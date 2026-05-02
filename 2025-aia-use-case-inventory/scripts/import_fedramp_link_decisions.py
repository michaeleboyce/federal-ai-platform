"""Apply curator decisions from a FedRAMP link-queue CSV.

Reads a CSV produced by `scripts/export_fedramp_link_queue.py` (or by the
dashboard's `/api/fedramp-queue-export` route — same shape) and writes
manual links into `fedramp_product_links` / `fedramp_agency_links`, marking
the queue row resolved or rejected.

Decision values per row:

    accept_N            (N=1..5) Accept candidate N from the row.
    reject              No FedRAMP match; mark the queue row rejected.
    custom:<fedramp_id> Use a hand-typed FedRAMP ID (must already exist in
                        fedramp_products / fedramp_agencies).
    <blank>             Skip this row silently — leaves it pending.

For accept_N / custom: a row is written to the appropriate link table with
`confidence='manual'`, `source='manual_csv'`, `notes=<decision_notes>`. The
queue row's `status` flips to `'resolved'`. For `reject`, only `status`
changes (to `'rejected'`).

Defaults to dry-run; pass `--apply` to write. The whole import is wrapped in
a single transaction — if any row errors out in apply mode, the entire
import rolls back and you get a report of the failures.

Usage (run from `2025-aia-use-case-inventory/`):

    # Dry-run (default — print summary, change nothing)
    python scripts/import_fedramp_link_decisions.py decisions.csv

    # Apply
    python scripts/import_fedramp_link_decisions.py decisions.csv --apply
"""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data" / "federal_ai_inventory_2025.db"

MAX_CANDIDATES = 5
ACCEPT_RE = re.compile(r"^accept_([1-5])$")
CUSTOM_RE = re.compile(r"^custom:(.+)$")


@dataclass
class RowError:
    queue_id: str
    decision: str
    message: str


def _resolve_decision(
    decision: str,
    candidates: list[dict],
) -> tuple[str, str | None]:
    """Map a decision string to (action, fedramp_id).

    action ∈ {'accept', 'reject', 'skip'}; fedramp_id is set only for accept.
    Raises ValueError on a malformed / out-of-range decision.
    """
    decision = (decision or "").strip()
    if not decision:
        return "skip", None
    if decision == "reject":
        return "reject", None
    m = ACCEPT_RE.match(decision)
    if m:
        n = int(m.group(1))
        if n < 1 or n > MAX_CANDIDATES:
            raise ValueError(f"accept_{n} out of range (1..{MAX_CANDIDATES})")
        if n > len(candidates):
            raise ValueError(
                f"accept_{n} but row has only {len(candidates)} candidate(s)"
            )
        fid = candidates[n - 1].get("fedramp_id")
        if not fid:
            raise ValueError(f"accept_{n} but candidate {n} has no fedramp_id")
        return "accept", str(fid)
    m = CUSTOM_RE.match(decision)
    if m:
        return "accept", m.group(1).strip()
    raise ValueError(
        f"unrecognized decision '{decision}' "
        f"(expected accept_1..accept_{MAX_CANDIDATES} | reject | custom:<id> | blank)"
    )


def _row_candidates(row: dict[str, str]) -> list[dict]:
    """Reconstruct the candidates list from the wide CSV columns."""
    out: list[dict] = []
    for i in range(1, MAX_CANDIDATES + 1):
        fid = (row.get(f"candidate_{i}_fedramp_id") or "").strip()
        if not fid:
            continue
        c = {"fedramp_id": fid}
        for k in ("csp", "cso"):
            v = (row.get(f"candidate_{i}_{k}") or "").strip()
            if v:
                c[k] = v
        score_raw = (row.get(f"candidate_{i}_score") or "").strip()
        if score_raw:
            try:
                c["score"] = float(score_raw)
            except ValueError:
                pass
        out.append(c)
    return out


def _validate_fedramp_id(
    conn: sqlite3.Connection, link_kind: str, fedramp_id: str
) -> bool:
    if link_kind == "product":
        cur = conn.execute(
            "SELECT 1 FROM fedramp_products WHERE fedramp_id = ?", (fedramp_id,)
        )
    else:
        # Agencies use the integer id (no `fedramp_id` column).
        cur = conn.execute(
            "SELECT 1 FROM fedramp_agencies WHERE id = ?", (fedramp_id,)
        )
    return cur.fetchone() is not None


def _queue_row_meta(
    conn: sqlite3.Connection, queue_id: int
) -> tuple[str, int] | None:
    """Return (link_kind, inventory_id) from the queue table or None."""
    cur = conn.execute(
        "SELECT link_kind, inventory_id FROM fedramp_link_queue WHERE id = ?",
        (queue_id,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return (r[0], r[1])


def _insert_product_link(
    conn: sqlite3.Connection,
    inventory_id: int,
    fedramp_id: str,
    notes: str,
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO fedramp_product_links (
            inventory_product_id, fedramp_id, confidence, source, score, notes
        ) VALUES (?, ?, 'manual', 'manual_csv', NULL, ?)
        """,
        (inventory_id, fedramp_id, notes or None),
    )


def _insert_agency_link(
    conn: sqlite3.Connection,
    inventory_id: int,
    fedramp_agency_id: str,
    notes: str,
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO fedramp_agency_links (
            inventory_agency_id, fedramp_agency_id, confidence, source, score, notes
        ) VALUES (?, ?, 'manual', 'manual_csv', NULL, ?)
        """,
        (inventory_id, int(fedramp_agency_id), notes or None),
    )


def _mark_queue(
    conn: sqlite3.Connection, queue_id: int, status: str, notes: str
) -> None:
    conn.execute(
        """
        UPDATE fedramp_link_queue
           SET status = ?,
               decision_notes = ?,
               updated_at = datetime('now')
         WHERE id = ?
        """,
        (status, notes or None, queue_id),
    )


def run(csv_path: Path, *, apply: bool) -> int:
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")
    if not DB.exists():
        raise SystemExit(f"DB not found at {DB}")

    counts = Counter()
    errors: list[RowError] = []

    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with csv_path.open("r", newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            required = {"queue_id", "decision"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise SystemExit(
                    f"CSV missing required columns: {sorted(missing)}"
                )

            for row in reader:
                queue_id_raw = (row.get("queue_id") or "").strip()
                decision_raw = (row.get("decision") or "").strip()
                notes = (row.get("decision_notes") or "").strip()

                if not queue_id_raw:
                    continue  # blank/separator row
                try:
                    queue_id = int(queue_id_raw)
                except ValueError:
                    errors.append(
                        RowError(queue_id_raw, decision_raw, "queue_id not an integer")
                    )
                    continue

                meta = _queue_row_meta(conn, queue_id)
                if meta is None:
                    errors.append(
                        RowError(queue_id_raw, decision_raw, "queue_id not found")
                    )
                    continue
                link_kind, inventory_id = meta

                candidates = _row_candidates(row)
                try:
                    action, fedramp_id = _resolve_decision(decision_raw, candidates)
                except ValueError as e:
                    errors.append(RowError(queue_id_raw, decision_raw, str(e)))
                    continue

                if action == "skip":
                    counts["skipped"] += 1
                    continue

                if action == "reject":
                    if apply:
                        _mark_queue(conn, queue_id, "rejected", notes)
                    counts["rejected"] += 1
                    continue

                # action == 'accept'
                assert fedramp_id is not None
                if not _validate_fedramp_id(conn, link_kind, fedramp_id):
                    errors.append(
                        RowError(
                            queue_id_raw,
                            decision_raw,
                            f"fedramp_id '{fedramp_id}' not found in "
                            f"fedramp_{'products' if link_kind == 'product' else 'agencies'}",
                        )
                    )
                    continue

                if apply:
                    if link_kind == "product":
                        _insert_product_link(conn, inventory_id, fedramp_id, notes)
                    else:
                        _insert_agency_link(conn, inventory_id, fedramp_id, notes)
                    _mark_queue(conn, queue_id, "resolved", notes)
                counts["accepted"] += 1

        if apply:
            if errors:
                conn.rollback()
            else:
                conn.commit()
    finally:
        conn.close()

    # Report.
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"\n=== fedramp link decisions ({mode}) ===")
    print(f"  accepted: {counts['accepted']}")
    print(f"  rejected: {counts['rejected']}")
    print(f"  skipped:  {counts['skipped']}")
    print(f"  errors:   {len(errors)}")
    if errors:
        print("\nFirst 10 errors:")
        for e in errors[:10]:
            print(f"  queue_id={e.queue_id} decision='{e.decision}': {e.message}")
        if apply:
            print("\nROLLED BACK — fix the errors above and re-run with --apply.")
    elif apply:
        print("\nWrote changes and committed.")
    else:
        print("\nDry-run only — pass --apply to write.")

    return 1 if errors and apply else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv", help="Path to the decisions CSV.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes (default: dry-run).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run even if --apply is set (for safety in scripts).",
    )
    args = parser.parse_args()
    apply = args.apply and not args.dry_run
    sys.exit(run(Path(args.csv), apply=apply))


if __name__ == "__main__":
    main()
