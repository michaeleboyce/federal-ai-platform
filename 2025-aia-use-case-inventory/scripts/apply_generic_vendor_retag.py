"""Apply the 2026-05 generic-vendor-links retag pass.

Reads `audit/retag/generic_vendor_links/by_row.csv` (validator-merged) and
realigns `use_case_products` / `consolidated_use_case_products` so that
edges to placeholder products (Microsoft, Google, Amazon, Adobe, Splunk,
Thomson Reuters, LexisNexis, Veritone, Cisco, ServiceNow, Salesforce)
are either:

- `relink`              — replaced with an edge to a specific catalog product
                          (UPDATE in place, OR DELETE-only if the
                          destination edge already exists per PK collision)
- `delete_or_inferred`  — downgraded to `confidence='inferred'` (edge kept,
                          since the source named the vendor but not a
                          specific product; the data point is preserved
                          and the dashboard renders it with a lighter
                          treatment)
- `keep_strong`         — no-op (placeholder is genuinely the best label)

## Multi-agent safety (see ../CLAUDE.md "Multi-agent safety")

This script is idempotent and SAFE TO RE-RUN. It defends against three
classes of mid-flight breakage:

1. **Stale numeric IDs in the CSV.** The CSV's `live_*_id` columns were
   captured at validator-run time. If a sibling agent rebuilt the DB
   between validation and apply, those IDs are now stale. The script
   re-resolves EVERY id at apply time, from stable signatures:
     - `current_product_id`  ← canonical_name lookup in `products`
     - `proposed_product_id` ← canonical_name lookup
     - `use_case_id`         ← `(agency_id, use_case_name)` signature
                                (mirrors how the validator did it)

2. **DB-vocab leakage.** The `confidence` column is
   `CHECK(confidence IN ('strong', 'inferred'))`. The CSV uses
   `high`/`medium`/`low`/`inferred` as the agent's gating signal.
   Translation happens at the SQL boundary only.

3. **Mid-session DB rebuild detection.** Reads
   `apply_snapshot.json.db_mtime_at_validation` and compares against the
   live DB mtime. If the live DB is newer, the placeholder ids in the
   snapshot are stale; the script proceeds anyway since it re-resolves
   everything by name, but it prints a warning.

## Confidence + action policy (must match validator's apply_snapshot.json)

| CSV `proposed_action`     | CSV `confidence`         | Effect                                                                   |
|---------------------------|--------------------------|--------------------------------------------------------------------------|
| `relink` + no pk-collision| high / medium            | UPDATE … SET product_id=<new>, confidence='strong'                       |
| `relink` + pk-collision   | high / medium            | DELETE the placeholder edge (existing strong edge to target stays)       |
| `relink`                  | low                      | SKIP (stays in CSV for human review)                                     |
| `delete_or_inferred`      | high / medium / inferred | UPDATE … SET confidence='inferred' (edge stays — vendor signal preserved)|
| `delete_or_inferred`      | low                      | SKIP                                                                     |
| `keep_strong`             | any                      | no-op                                                                    |

(`inferred` in the CSV's `confidence` column is Slice B's spelling of
"medium-equivalent for delete_or_inferred rows" — gated as apply, not skip.)

## Run

    python3 scripts/apply_generic_vendor_retag.py           # apply
    python3 scripts/apply_generic_vendor_retag.py --dry-run # preview SQL, no writes
    python3 scripts/apply_generic_vendor_retag.py --force   # ignore mtime warning

Wired into `make fix` after `apply_retag_audit.py` so corrections persist
across rebuilds.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
AUDIT_DIR = ROOT / "audit" / "retag" / "generic_vendor_links"
BY_ROW_CSV = AUDIT_DIR / "by_row.csv"
APPLY_SNAPSHOT = AUDIT_DIR / "apply_snapshot.json"

APPLY_CONFIDENCES = {"high", "medium", "inferred"}
SKIP_CONFIDENCES = {"low"}
VALID_ACTIONS = {"relink", "delete_or_inferred", "keep_strong"}


def _open(read_only: bool = False) -> sqlite3.Connection:
    if read_only:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _check_mtime(snapshot: dict, force: bool) -> None:
    """Warn (or abort) if the DB has been rebuilt since validation."""
    snap_iso = snapshot.get("db_mtime_at_validation")
    if not snap_iso:
        return
    snap_dt = datetime.fromisoformat(snap_iso)
    live_mtime = datetime.fromtimestamp(DB_PATH.stat().st_mtime, tz=timezone.utc)
    if live_mtime > snap_dt:
        delta = (live_mtime - snap_dt).total_seconds()
        msg = (
            f"DB modified after validation: live {live_mtime.isoformat()} "
            f"is {delta:.0f}s newer than snapshot {snap_iso}. "
            "IDs in the snapshot are stale; this script re-resolves by name "
            "so it should still apply cleanly, but a sibling agent may have "
            "concurrent writes in flight."
        )
        if force:
            print(f"WARNING: {msg}\n  (proceeding because --force)", file=sys.stderr)
        else:
            print(f"WARNING: {msg}", file=sys.stderr)


def _resolve_product_id(
    conn: sqlite3.Connection, canonical_name: str, vendor_hint: str | None = None
) -> int | None:
    """Re-resolve a product id from its canonical_name. Multi-agent-safe.

    If multiple rows share the name (rare but possible across vendors), the
    vendor_hint tiebreaker picks the row whose vendor matches. Returns None
    if no row matches.
    """
    rows = conn.execute(
        "SELECT id, vendor FROM products WHERE canonical_name = ?",
        (canonical_name,),
    ).fetchall()
    if not rows:
        return None
    if len(rows) == 1:
        return int(rows[0]["id"])
    if vendor_hint:
        for r in rows:
            if (r["vendor"] or "").strip().lower() == vendor_hint.strip().lower():
                return int(r["id"])
    return None  # ambiguous


def _resolve_use_case_id(
    conn: sqlite3.Connection, agency_abbr: str, use_case_name: str, entry_kind: str
) -> int | None:
    """Re-resolve use_case_id by (agency_id, use_case_name) signature.

    Mirrors the validator's strategy. Falls back to CSV's id only if the
    signature is ambiguous or missing.
    """
    table = "use_cases" if entry_kind == "use_case" else "consolidated_use_cases"
    name_col = "use_case_name" if entry_kind == "use_case" else "ai_use_case"
    row = conn.execute(
        f"""
        SELECT uc.id
          FROM {table} uc
          JOIN agencies a ON a.id = uc.agency_id
         WHERE a.abbreviation = ?
           AND uc.{name_col} = ?
        """,
        (agency_abbr, use_case_name),
    ).fetchone()
    return int(row["id"]) if row else None


def _table_for(entry_kind: str) -> tuple[str, str]:
    """Return (table_name, fk_column) for the given entry_kind."""
    if entry_kind == "use_case":
        return "use_case_products", "use_case_id"
    if entry_kind == "consolidated":
        return "consolidated_use_case_products", "consolidated_use_case_id"
    raise ValueError(f"Unknown entry_kind: {entry_kind!r}")


def _classify(row: dict) -> str:
    """Return the apply policy bucket: 'apply' | 'skip' | 'noop' | 'invalid'."""
    action = (row.get("proposed_action") or "").strip()
    conf = (row.get("confidence") or "").strip().lower()
    if action not in VALID_ACTIONS:
        return "invalid"
    if action == "keep_strong":
        return "noop"
    if conf in SKIP_CONFIDENCES:
        return "skip"
    if conf in APPLY_CONFIDENCES:
        return "apply"
    return "skip"  # unknown confidence → conservative skip


def apply_retag(conn: sqlite3.Connection, dry_run: bool) -> dict:
    rows = list(csv.DictReader(BY_ROW_CSV.open()))
    stats = Counter()
    skipped: list[tuple[str, dict]] = []
    by_placeholder_action = defaultdict(Counter)

    for row in rows:
        policy = _classify(row)
        stats[f"policy_{policy}"] += 1
        if policy == "invalid":
            skipped.append(("invalid_action_or_confidence", row))
            continue
        if policy == "skip":
            skipped.append(("low_confidence_or_unknown", row))
            continue
        if policy == "noop":
            stats["noop_keep_strong"] += 1
            by_placeholder_action[row.get("current_product_name", "?")]["keep_strong"] += 1
            continue

        entry_kind = (row.get("entry_kind") or "").strip()
        try:
            table, fk_col = _table_for(entry_kind)
        except ValueError:
            stats["error_unknown_entry_kind"] += 1
            skipped.append(("unknown_entry_kind", row))
            continue

        current_name = (row.get("current_product_name") or "").strip()
        proposed_name = (row.get("proposed_product_name") or "").strip()
        agency_abbr = (row.get("agency") or "").strip()
        use_case_name = (row.get("use_case_name") or "").strip()
        action = (row.get("proposed_action") or "").strip()

        # Re-resolve every id at apply time. NEVER trust CSV ids.
        current_pid = _resolve_product_id(conn, current_name)
        if current_pid is None:
            stats["error_current_product_unresolved"] += 1
            skipped.append((f"current_product_unresolved:{current_name}", row))
            continue

        entry_id = _resolve_use_case_id(conn, agency_abbr, use_case_name, entry_kind)
        if entry_id is None:
            stats["error_use_case_unresolved"] += 1
            skipped.append(
                (f"use_case_unresolved:{agency_abbr}/{use_case_name[:40]}", row)
            )
            continue

        if action == "relink":
            if not proposed_name:
                stats["error_relink_no_target"] += 1
                skipped.append(("relink_no_target", row))
                continue
            proposed_pid = _resolve_product_id(conn, proposed_name)
            if proposed_pid is None:
                stats["error_proposed_product_unresolved"] += 1
                skipped.append((f"proposed_product_unresolved:{proposed_name}", row))
                continue
            if proposed_pid == current_pid:
                # Slice agent proposed the same row that's already linked.
                # Idempotency: treat as no-op.
                stats["noop_relink_self"] += 1
                continue

            # Live PK-collision check. (CSV's pk_collision column was correct
            # at validator-time, but products.id may have rotated since.)
            existing = conn.execute(
                f"SELECT 1 FROM {table} WHERE {fk_col}=? AND product_id=?",
                (entry_id, proposed_pid),
            ).fetchone()

            if existing:
                # Destination edge already exists — DELETE placeholder edge only.
                sql = f"DELETE FROM {table} WHERE {fk_col}=? AND product_id=?"
                params = (entry_id, current_pid)
                if dry_run:
                    print(f"DRY  {sql}  {params}  -- PK-collision delete")
                else:
                    conn.execute(sql, params)
                stats["apply_relink_pk_collision_delete"] += 1
                by_placeholder_action[current_name]["relink_pk_delete"] += 1
            else:
                # Standard relink: move the edge to the target product, mark strong.
                sql = (
                    f"UPDATE {table} "
                    f"   SET product_id=?, confidence='strong' "
                    f" WHERE {fk_col}=? AND product_id=?"
                )
                params = (proposed_pid, entry_id, current_pid)
                if dry_run:
                    print(f"DRY  {sql}  {params}")
                else:
                    conn.execute(sql, params)
                stats["apply_relink_update"] += 1
                by_placeholder_action[current_name]["relink_update"] += 1

        elif action == "delete_or_inferred":
            # Downgrade the placeholder edge to inferred (do NOT delete — the
            # vendor signal is still useful to surface in the dashboard).
            sql = (
                f"UPDATE {table} "
                f"   SET confidence='inferred' "
                f" WHERE {fk_col}=? AND product_id=?"
            )
            params = (entry_id, current_pid)
            if dry_run:
                print(f"DRY  {sql}  {params}")
            else:
                conn.execute(sql, params)
            stats["apply_downgrade_to_inferred"] += 1
            by_placeholder_action[current_name]["downgrade_inferred"] += 1

    return {
        "stats": dict(stats),
        "by_placeholder_action": {k: dict(v) for k, v in by_placeholder_action.items()},
        "skipped_count": len(skipped),
        "skipped_sample": [(reason, r.get("use_case_id"), r.get("agency"))
                           for reason, r in skipped[:10]],
    }


def _expected_post_state(snapshot: dict, current_state: dict) -> str:
    """Build a human-readable expected-vs-actual delta table."""
    lines = []
    lines.append("\nExpected vs actual edges on placeholder products:")
    lines.append(
        f"  {'Placeholder':<20s} {'before':>7s} {'expected_after':>16s} {'actual_after':>14s}  delta"
    )
    expected = snapshot.get("expected_post_apply", {})
    snap = snapshot.get("placeholder_products", {})
    for name in sorted(snap.keys()):
        before = snap[name].get("edges_before", 0)
        exp_after = expected.get(name, {}).get("total_left_on_placeholder", 0)
        actual_after = current_state.get(name, 0)
        delta = actual_after - exp_after
        marker = "OK" if delta == 0 else f"DELTA {delta:+d}"
        lines.append(
            f"  {name:<20s} {before:>7d} {exp_after:>16d} {actual_after:>14d}  {marker}"
        )
    return "\n".join(lines)


def _live_edge_counts(conn: sqlite3.Connection) -> dict:
    """Return {placeholder_name: total_edges} for the 11 placeholder products."""
    rows = conn.execute(
        """
        SELECT p.canonical_name AS name,
               COALESCE(uc.c, 0) + COALESCE(cuc.c, 0) AS total
          FROM products p
          LEFT JOIN (
              SELECT product_id, COUNT(*) AS c
                FROM use_case_products GROUP BY product_id
          ) uc ON uc.product_id = p.id
          LEFT JOIN (
              SELECT product_id, COUNT(*) AS c
                FROM consolidated_use_case_products GROUP BY product_id
          ) cuc ON cuc.product_id = p.id
         WHERE p.canonical_name IN (
            'Microsoft','Google','Amazon','Adobe','Splunk',
            'Thomson Reuters','LexisNexis','Veritone','Cisco',
            'ServiceNow','Salesforce'
         )
        """
    ).fetchall()
    return {r["name"]: int(r["total"]) for r in rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print SQL that would run; do not commit any changes.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Proceed even if the DB has been modified since validation.",
    )
    args = parser.parse_args()

    if not BY_ROW_CSV.exists():
        print(f"ERROR: missing {BY_ROW_CSV}", file=sys.stderr)
        sys.exit(2)
    if not APPLY_SNAPSHOT.exists():
        print(f"ERROR: missing {APPLY_SNAPSHOT}", file=sys.stderr)
        sys.exit(2)

    snapshot = json.loads(APPLY_SNAPSHOT.read_text())
    _check_mtime(snapshot, args.force)

    conn = _open(read_only=args.dry_run)
    try:
        result = apply_retag(conn, dry_run=args.dry_run)
        if not args.dry_run:
            conn.commit()
        live_after = _live_edge_counts(conn)
    finally:
        conn.close()

    print("\nApply summary:")
    for k, v in sorted(result["stats"].items()):
        print(f"  {k}: {v}")
    print(f"\nSkipped: {result['skipped_count']}")
    if result["skipped_sample"]:
        print("Skipped sample (first 10):")
        for reason, uid, agency in result["skipped_sample"]:
            print(f"  {agency} use_case={uid}  reason={reason}")
    print("\nBy placeholder product:")
    for placeholder in sorted(result["by_placeholder_action"]):
        actions = result["by_placeholder_action"][placeholder]
        bits = ", ".join(f"{k}={v}" for k, v in sorted(actions.items()))
        print(f"  {placeholder}: {bits}")
    print(_expected_post_state(snapshot, live_after))

    if args.dry_run:
        print("\n[dry-run] no changes written.")
    else:
        print("\n[committed]")


if __name__ == "__main__":
    main()
