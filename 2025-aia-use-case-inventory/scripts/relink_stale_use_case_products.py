"""Repair dangling FK rows in use_case_products and consolidated_use_case_products.

Background: scripts/apply_linkage_pass_2026_05.py (the May 2026 4-agent labeling
pass + its July followup) accepted a `linking_use_case_ids` column of raw
integers and INSERTed them directly into the link tables. Between the labeling
pass and the apply step, `load_inventories.py` re-keyed every use_case via
DELETE+AUTOINCREMENT re-INSERT, so the integers landed dangling. SQLite's
declared FK is unenforced without `PRAGMA foreign_keys=ON`, so the writes
succeeded silently. Result on the current DB: 301 dangling rows in
use_case_products + 22 in consolidated_use_case_products. They render as
"phantom orphan products" on /products because `entry_product_edges` inner-joins
through use_cases and drops the dangling edges.

This script repairs the damage in three subcommands:

  remap          (Phase 1a) — try to remap dangling rows automatically using
                 the original input CSVs as a (old_id) → (agency, name)
                 lookup, then look up the current id by signature. Aborts if
                 any rows can't be resolved; writes the unresolved list to
                 audit/orphan_link_followup/unresolved.csv for follow-up.
  apply-resolved (Phase 1c) — read audit/orphan_link_followup/resolved.csv
                 (produced by an agent that did deeper recovery from the
                 agent recommendation JSONs + old DB backups) and UPDATE
                 those rows to point at the resolved new ids.
  quarantine     (Phase 1c) — create use_case_products_orphaned and
                 consolidated_use_case_products_orphaned tables, move any
                 remaining dangling rows into them, and write a Markdown
                 record at audit/orphan_link_followup/quarantined.md. After
                 this, the live link tables have zero dangles.
  verify         — print current dangling counts. Read-only.

Reuses `scripts/remap_linkage_pass_ids._build_old_id_to_signature` for the
signature lookup (extended here to also consume the linkage_pass_2026-05-
followup/inputs/ws*.csv files, which the original helper didn't know about).

All mutations are wrapped in BEGIN IMMEDIATE / COMMIT and require a manual
db backup before running (the plan docs the backup naming convention).
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
PRIMARY_INPUTS = ROOT / "audit" / "linkage_pass_2026-05" / "inputs"
FOLLOWUP_INPUTS = ROOT / "audit" / "linkage_pass_2026-05-followup" / "inputs"
OUT_DIR = ROOT / "audit" / "orphan_link_followup"


def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


def _read_signature_csv(
    path: Path,
    id_col: str,
    name_col: str,
    table_prefix: str,
) -> dict[int, tuple[str, str]]:
    out: dict[int, tuple[str, str]] = {}
    if not path.exists():
        return out
    with path.open() as f:
        for r in csv.DictReader(f):
            raw_id = r.get(id_col)
            try:
                uid = int(raw_id) if raw_id is not None else None
            except ValueError:
                continue
            if uid is None:
                continue
            out[uid] = (table_prefix + _norm(r.get("agency")), _norm(r.get(name_col)))
    return out


def build_old_id_to_signature() -> dict[int, tuple[str, str]]:
    """Union of original-pass and followup-pass (old_id → signature) maps."""
    out: dict[int, tuple[str, str]] = {}
    for fname in (
        "slice_a_named_vendor_individual.csv",
        "slice_b_mention_only_individual.csv",
        "slice_c_dark_sample.csv",
    ):
        out.update(
            _read_signature_csv(
                PRIMARY_INPUTS / fname, "use_case_id", "use_case_name", "__uc__"
            )
        )
    out.update(
        _read_signature_csv(
            PRIMARY_INPUTS / "slice_b_named_consolidated.csv",
            "consolidated_use_case_id",
            "ai_use_case",
            "__c__",
        )
    )
    out.update(
        _read_signature_csv(
            FOLLOWUP_INPUTS / "ws1_va_dark_individual.csv",
            "use_case_id",
            "use_case_name",
            "__uc__",
        )
    )
    out.update(
        _read_signature_csv(
            FOLLOWUP_INPUTS / "ws1_va_dark_consolidated.csv",
            "consolidated_use_case_id",
            "ai_use_case",
            "__c__",
        )
    )
    return out


def scan_backup_signatures(needed_ids: set[int]) -> dict[int, tuple[str, str]]:
    """Walk every data/*.backup-* DB and recover (old_id) → (agency, name)
    signatures for any `needed_ids` whose row still exists in that snapshot.

    Each backup may have either use_cases or consolidated_use_cases rows with
    a matching id; we collect both. First-match wins (backups are scanned in
    arbitrary order, but for our purposes each old_id should only correspond
    to one historical row across all snapshots — the slug is stable, the id
    was the snapshot value)."""
    out: dict[int, tuple[str, str]] = {}
    backups = sorted((ROOT / "data").glob("federal_ai_inventory_2025.db.backup-*"))
    for backup in backups:
        if not needed_ids:
            break
        try:
            conn = sqlite3.connect(f"file:{backup}?mode=ro", uri=True)
        except sqlite3.OperationalError:
            continue
        try:
            placeholders = ",".join("?" * min(len(needed_ids), 500))
            ids_list = list(needed_ids)
            # Batch in chunks of 500 to keep the IN-list reasonable
            for i in range(0, len(ids_list), 500):
                chunk = ids_list[i : i + 500]
                ph = ",".join("?" * len(chunk))
                try:
                    for row in conn.execute(
                        f"""
                        SELECT uc.id, a.abbreviation, uc.use_case_name
                          FROM use_cases uc JOIN agencies a ON a.id = uc.agency_id
                         WHERE uc.id IN ({ph})
                        """,
                        chunk,
                    ):
                        if row[0] not in out:
                            out[row[0]] = ("__uc__" + _norm(row[1]), _norm(row[2]))
                except sqlite3.OperationalError:
                    pass
                try:
                    for row in conn.execute(
                        f"""
                        SELECT c.id, a.abbreviation, c.ai_use_case
                          FROM consolidated_use_cases c JOIN agencies a ON a.id = c.agency_id
                         WHERE c.id IN ({ph})
                        """,
                        chunk,
                    ):
                        if row[0] not in out:
                            out[row[0]] = ("__c__" + _norm(row[1]), _norm(row[2]))
                except sqlite3.OperationalError:
                    pass
        finally:
            conn.close()
    return out


def build_signature_to_new_id(conn: sqlite3.Connection) -> dict[tuple[str, str], int]:
    out: dict[tuple[str, str], int] = {}
    for row in conn.execute(
        """
        SELECT uc.id, a.abbreviation, uc.use_case_name
          FROM use_cases uc JOIN agencies a ON a.id = uc.agency_id
        """
    ):
        out[("__uc__" + _norm(row[1]), _norm(row[2]))] = row[0]
    for row in conn.execute(
        """
        SELECT c.id, a.abbreviation, c.ai_use_case
          FROM consolidated_use_cases c JOIN agencies a ON a.id = c.agency_id
        """
    ):
        out[("__c__" + _norm(row[1]), _norm(row[2]))] = row[0]
    return out


def fetch_dangling(conn: sqlite3.Connection):
    ucp = list(
        conn.execute(
            """
            SELECT ucp.use_case_id, ucp.product_id, p.canonical_name,
                   ucp.evidence_text, ucp.confidence
              FROM use_case_products ucp
              JOIN products p ON p.id = ucp.product_id
             WHERE NOT EXISTS (SELECT 1 FROM use_cases uc WHERE uc.id = ucp.use_case_id)
             ORDER BY ucp.use_case_id, ucp.product_id
            """
        )
    )
    cup = list(
        conn.execute(
            """
            SELECT cup.consolidated_use_case_id, cup.product_id, p.canonical_name,
                   cup.evidence_text, cup.confidence
              FROM consolidated_use_case_products cup
              JOIN products p ON p.id = cup.product_id
             WHERE NOT EXISTS (SELECT 1 FROM consolidated_use_cases c WHERE c.id = cup.consolidated_use_case_id)
             ORDER BY cup.consolidated_use_case_id, cup.product_id
            """
        )
    )
    return ucp, cup


def cmd_verify(_: argparse.Namespace) -> int:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        ucp_dangling = conn.execute(
            "SELECT COUNT(*) FROM use_case_products ucp "
            "WHERE NOT EXISTS (SELECT 1 FROM use_cases uc WHERE uc.id = ucp.use_case_id)"
        ).fetchone()[0]
        cup_dangling = conn.execute(
            "SELECT COUNT(*) FROM consolidated_use_case_products cup "
            "WHERE NOT EXISTS (SELECT 1 FROM consolidated_use_cases c WHERE c.id = cup.consolidated_use_case_id)"
        ).fetchone()[0]
        reverse = conn.execute(
            "SELECT COUNT(*) FROM use_cases uc WHERE uc.product_id IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM products p WHERE p.id = uc.product_id)"
        ).fetchone()[0]
        products_zero = conn.execute(
            "SELECT COUNT(*) FROM products p "
            "WHERE NOT EXISTS (SELECT 1 FROM entry_product_edges e WHERE e.product_id = p.id)"
        ).fetchone()[0]
        # Quarantine tables (may not exist yet)
        ucp_q = cup_q = 0
        for tbl, var in (
            ("use_case_products_orphaned", "ucp_q"),
            ("consolidated_use_case_products_orphaned", "cup_q"),
        ):
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
                if var == "ucp_q":
                    ucp_q = count
                else:
                    cup_q = count
            except sqlite3.OperationalError:
                pass
    finally:
        conn.close()
    print(f"use_case_products dangling: {ucp_dangling}")
    print(f"consolidated_use_case_products dangling: {cup_dangling}")
    print(f"use_cases.product_id pointing at deleted product: {reverse}")
    print(f"products with 0 entries in entry_product_edges: {products_zero}")
    print(f"use_case_products_orphaned (quarantine): {ucp_q}")
    print(f"consolidated_use_case_products_orphaned (quarantine): {cup_q}")
    return 0


def _attempt_remap(
    old_id: int,
    expected_prefix: str,
    old_to_sig: dict[int, tuple[str, str]],
    sig_to_new: dict[tuple[str, str], int],
) -> int | None:
    sig = old_to_sig.get(old_id)
    if sig is None:
        return None
    if not sig[0].startswith(expected_prefix):
        # signature belongs to the wrong table — defensive
        return None
    return sig_to_new.get(sig)


def cmd_remap(args: argparse.Namespace) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        old_to_sig = build_old_id_to_signature()
        sig_to_new = build_signature_to_new_id(conn)
        ucp_rows, cup_rows = fetch_dangling(conn)
        print(
            f"input signatures: {len(old_to_sig)} old_ids loaded from primary+followup inputs"
        )
        print(
            f"db signatures: {len(sig_to_new)} (agency, name) entries in current use_cases+consolidated"
        )
        print(f"dangling: use_case_products={len(ucp_rows)} consolidated={len(cup_rows)}")

        if not args.no_scan_backups:
            needed: set[int] = set()
            for old_id, *_ in ucp_rows:
                if old_id not in old_to_sig:
                    needed.add(old_id)
            for old_id, *_ in cup_rows:
                if old_id not in old_to_sig:
                    needed.add(old_id)
            if needed:
                print(f"scanning DB backups for {len(needed)} missing signatures…")
                recovered = scan_backup_signatures(needed)
                old_to_sig.update(recovered)
                print(f"  recovered {len(recovered)} signatures from backups")

        ucp_updates: list[tuple[int, int, int]] = []  # (new_id, old_id, product_id)
        cup_updates: list[tuple[int, int, int]] = []
        # cross-table moves: rows in the wrong link table because apply script
        # confused use_case ids and consolidated ids. List of (old_id, new_id, product_id).
        ucp_to_cup_moves: list[tuple[int, int, int]] = []
        cup_to_ucp_moves: list[tuple[int, int, int]] = []
        unresolved: list[dict] = []

        for old_id, product_id, product_name, evidence, conf in ucp_rows:
            new_id = _attempt_remap(old_id, "__uc__", old_to_sig, sig_to_new)
            if new_id is not None:
                ucp_updates.append((new_id, old_id, product_id))
                continue
            # Cross-table fallback: maybe the id belonged to a consolidated row.
            cross_id = _attempt_remap(old_id, "__c__", old_to_sig, sig_to_new)
            if cross_id is not None:
                ucp_to_cup_moves.append((old_id, cross_id, product_id))
                continue
            suspected_slice = "primary" if old_id < 70000 else "followup"
            suspected_agency = ""
            sig = old_to_sig.get(old_id)
            if sig:
                suspected_agency = sig[0].removeprefix("__uc__").removeprefix("__c__")
            unresolved.append(
                {
                    "table": "use_case_products",
                    "old_use_case_id": old_id,
                    "product_id": product_id,
                    "product_canonical_name": product_name,
                    "evidence_text": evidence,
                    "confidence": conf,
                    "suspected_agency": suspected_agency,
                    "suspected_slice": suspected_slice,
                }
            )

        for old_id, product_id, product_name, evidence, conf in cup_rows:
            new_id = _attempt_remap(old_id, "__c__", old_to_sig, sig_to_new)
            if new_id is not None:
                cup_updates.append((new_id, old_id, product_id))
                continue
            cross_id = _attempt_remap(old_id, "__uc__", old_to_sig, sig_to_new)
            if cross_id is not None:
                cup_to_ucp_moves.append((old_id, cross_id, product_id))
                continue
            suspected_slice = "primary" if old_id < 70000 else "followup"
            suspected_agency = ""
            sig = old_to_sig.get(old_id)
            if sig:
                suspected_agency = sig[0].removeprefix("__uc__").removeprefix("__c__")
            unresolved.append(
                {
                    "table": "consolidated_use_case_products",
                    "old_use_case_id": old_id,
                    "product_id": product_id,
                    "product_canonical_name": product_name,
                    "evidence_text": evidence,
                    "confidence": conf,
                    "suspected_agency": suspected_agency,
                    "suspected_slice": suspected_slice,
                }
            )

        print(
            f"resolved automatically: ucp={len(ucp_updates)} cup={len(cup_updates)}"
        )
        if ucp_to_cup_moves or cup_to_ucp_moves:
            print(
                f"cross-table moves (misrouted by buggy apply): "
                f"ucp→cup={len(ucp_to_cup_moves)} cup→ucp={len(cup_to_ucp_moves)}"
            )
        print(f"unresolved: {len(unresolved)}")

        if args.dry_run:
            print("dry-run: no DB writes")
            _write_unresolved_csv(unresolved)
            return 0 if not unresolved else 1

        conn.execute("BEGIN IMMEDIATE")
        # Updates may collide with an existing (use_case_id, product_id) PK after
        # remap. INSERT OR IGNORE semantics: delete the dangling row if a live
        # row already exists at the target id; otherwise UPDATE.
        for new_id, old_id, product_id in ucp_updates:
            exists = conn.execute(
                "SELECT 1 FROM use_case_products WHERE use_case_id = ? AND product_id = ?",
                (new_id, product_id),
            ).fetchone()
            if exists:
                conn.execute(
                    "DELETE FROM use_case_products WHERE use_case_id = ? AND product_id = ?",
                    (old_id, product_id),
                )
            else:
                conn.execute(
                    "UPDATE use_case_products SET use_case_id = ? WHERE use_case_id = ? AND product_id = ?",
                    (new_id, old_id, product_id),
                )
        for new_id, old_id, product_id in cup_updates:
            exists = conn.execute(
                "SELECT 1 FROM consolidated_use_case_products "
                "WHERE consolidated_use_case_id = ? AND product_id = ?",
                (new_id, product_id),
            ).fetchone()
            if exists:
                conn.execute(
                    "DELETE FROM consolidated_use_case_products "
                    "WHERE consolidated_use_case_id = ? AND product_id = ?",
                    (old_id, product_id),
                )
            else:
                conn.execute(
                    "UPDATE consolidated_use_case_products SET consolidated_use_case_id = ? "
                    "WHERE consolidated_use_case_id = ? AND product_id = ?",
                    (new_id, old_id, product_id),
                )
        # Cross-table moves: remove from source, insert into target.
        for old_id, new_id, product_id in ucp_to_cup_moves:
            evidence_text, conf = conn.execute(
                "SELECT evidence_text, confidence FROM use_case_products "
                "WHERE use_case_id = ? AND product_id = ?",
                (old_id, product_id),
            ).fetchone() or (None, None)
            conn.execute(
                "DELETE FROM use_case_products WHERE use_case_id = ? AND product_id = ?",
                (old_id, product_id),
            )
            conn.execute(
                "INSERT OR IGNORE INTO consolidated_use_case_products "
                "(consolidated_use_case_id, product_id, evidence_text, confidence) "
                "VALUES (?, ?, ?, ?)",
                (new_id, product_id, evidence_text, conf),
            )
        for old_id, new_id, product_id in cup_to_ucp_moves:
            evidence_text, conf = conn.execute(
                "SELECT evidence_text, confidence FROM consolidated_use_case_products "
                "WHERE consolidated_use_case_id = ? AND product_id = ?",
                (old_id, product_id),
            ).fetchone() or (None, None)
            conn.execute(
                "DELETE FROM consolidated_use_case_products "
                "WHERE consolidated_use_case_id = ? AND product_id = ?",
                (old_id, product_id),
            )
            conn.execute(
                "INSERT OR IGNORE INTO use_case_products "
                "(use_case_id, product_id, evidence_text, confidence) "
                "VALUES (?, ?, ?, ?)",
                (new_id, product_id, evidence_text, conf),
            )
        conn.commit()

        if unresolved:
            _write_unresolved_csv(unresolved)
            print(
                f"\nABORT: {len(unresolved)} rows could not be remapped.\n"
                f"Wrote: {OUT_DIR / 'unresolved.csv'}\n"
                "Next: run an agent to recover the slug/use_case_name for each unresolved row,\n"
                "  then run `scripts/relink_stale_use_case_products.py apply-resolved`.",
                file=sys.stderr,
            )
            return 1
        print("all dangling rows resolved automatically.")
        return 0
    finally:
        conn.close()


def _write_unresolved_csv(unresolved: list[dict]) -> None:
    path = OUT_DIR / "unresolved.csv"
    fields = [
        "table",
        "old_use_case_id",
        "product_id",
        "product_canonical_name",
        "evidence_text",
        "confidence",
        "suspected_agency",
        "suspected_slice",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(unresolved)


def cmd_apply_resolved(args: argparse.Namespace) -> int:
    path = Path(args.resolved)
    if not path.exists():
        print(f"error: {path} not found", file=sys.stderr)
        return 1
    with path.open() as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("resolved.csv is empty; nothing to apply.")
        return 0
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        conn.execute("BEGIN IMMEDIATE")
        applied = 0
        skipped = 0
        for r in rows:
            tbl = r["table"]
            try:
                old_id = int(r["old_use_case_id"])
                product_id = int(r["product_id"])
                new_id_raw = r.get("resolved_use_case_id", "").strip()
            except (KeyError, ValueError):
                skipped += 1
                continue
            if not new_id_raw:
                skipped += 1
                continue
            try:
                new_id = int(new_id_raw)
            except ValueError:
                skipped += 1
                continue
            if tbl == "use_case_products":
                exists = conn.execute(
                    "SELECT 1 FROM use_case_products WHERE use_case_id = ? AND product_id = ?",
                    (new_id, product_id),
                ).fetchone()
                if exists:
                    conn.execute(
                        "DELETE FROM use_case_products WHERE use_case_id = ? AND product_id = ?",
                        (old_id, product_id),
                    )
                else:
                    conn.execute(
                        "UPDATE use_case_products SET use_case_id = ? WHERE use_case_id = ? AND product_id = ?",
                        (new_id, old_id, product_id),
                    )
                applied += 1
            elif tbl == "consolidated_use_case_products":
                exists = conn.execute(
                    "SELECT 1 FROM consolidated_use_case_products "
                    "WHERE consolidated_use_case_id = ? AND product_id = ?",
                    (new_id, product_id),
                ).fetchone()
                if exists:
                    conn.execute(
                        "DELETE FROM consolidated_use_case_products "
                        "WHERE consolidated_use_case_id = ? AND product_id = ?",
                        (old_id, product_id),
                    )
                else:
                    conn.execute(
                        "UPDATE consolidated_use_case_products SET consolidated_use_case_id = ? "
                        "WHERE consolidated_use_case_id = ? AND product_id = ?",
                        (new_id, old_id, product_id),
                    )
                applied += 1
            else:
                skipped += 1
        conn.commit()
        print(f"apply-resolved: applied={applied} skipped={skipped}")
        return 0
    finally:
        conn.close()


def cmd_quarantine(args: argparse.Namespace) -> int:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        conn.execute("BEGIN IMMEDIATE")
        # Create quarantine tables if missing.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS use_case_products_orphaned (
                original_use_case_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                evidence_text TEXT,
                confidence TEXT,
                quarantined_at TEXT NOT NULL,
                quarantine_reason TEXT,
                suspected_agency TEXT,
                PRIMARY KEY (original_use_case_id, product_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS consolidated_use_case_products_orphaned (
                original_consolidated_use_case_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                evidence_text TEXT,
                confidence TEXT,
                quarantined_at TEXT NOT NULL,
                quarantine_reason TEXT,
                suspected_agency TEXT,
                PRIMARY KEY (original_consolidated_use_case_id, product_id)
            )
            """
        )

        ucp_rows, cup_rows = fetch_dangling(conn)
        now = datetime.now(timezone.utc).isoformat()
        reason = args.reason or (
            "Dangling FK from May 2026 linkage_pass apply scripts; "
            "agent could not recover the original use_case mapping."
        )

        for old_id, product_id, _product_name, evidence, conf in ucp_rows:
            conn.execute(
                """
                INSERT OR IGNORE INTO use_case_products_orphaned
                       (original_use_case_id, product_id, evidence_text, confidence,
                        quarantined_at, quarantine_reason, suspected_agency)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (old_id, product_id, evidence, conf, now, reason, ""),
            )
            conn.execute(
                "DELETE FROM use_case_products WHERE use_case_id = ? AND product_id = ?",
                (old_id, product_id),
            )
        for old_id, product_id, _product_name, evidence, conf in cup_rows:
            conn.execute(
                """
                INSERT OR IGNORE INTO consolidated_use_case_products_orphaned
                       (original_consolidated_use_case_id, product_id, evidence_text,
                        confidence, quarantined_at, quarantine_reason, suspected_agency)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (old_id, product_id, evidence, conf, now, reason, ""),
            )
            conn.execute(
                "DELETE FROM consolidated_use_case_products "
                "WHERE consolidated_use_case_id = ? AND product_id = ?",
                (old_id, product_id),
            )
        conn.commit()
        _write_quarantine_markdown(ucp_rows, cup_rows, now, reason)
        print(
            f"quarantined: use_case_products={len(ucp_rows)} "
            f"consolidated_use_case_products={len(cup_rows)}"
        )
        return 0
    finally:
        conn.close()


def _write_quarantine_markdown(
    ucp_rows: list, cup_rows: list, when: str, reason: str
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "quarantined.md"
    lines: list[str] = []
    lines.append(f"# Quarantined dangling product links — {when}")
    lines.append("")
    lines.append(f"**Reason:** {reason}")
    lines.append("")
    lines.append(
        "These rows existed in `use_case_products` / "
        "`consolidated_use_case_products` but pointed at deleted parent rows. "
        "They've been moved into `use_case_products_orphaned` / "
        "`consolidated_use_case_products_orphaned` for audit retention and "
        "removed from the live link tables. The dashboard `/products` page no "
        "longer sees them."
    )
    lines.append("")
    lines.append("## use_case_products_orphaned")
    lines.append("")
    if ucp_rows:
        lines.append("| original_use_case_id | product_id | product | evidence | confidence |")
        lines.append("|---|---|---|---|---|")
        for old_id, product_id, name, evidence, conf in ucp_rows:
            lines.append(
                f"| {old_id} | {product_id} | {name} | {evidence} | {conf} |"
            )
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## consolidated_use_case_products_orphaned")
    lines.append("")
    if cup_rows:
        lines.append(
            "| original_consolidated_use_case_id | product_id | product | evidence | confidence |"
        )
        lines.append("|---|---|---|---|---|")
        for old_id, product_id, name, evidence, conf in cup_rows:
            lines.append(
                f"| {old_id} | {product_id} | {name} | {evidence} | {conf} |"
            )
    else:
        lines.append("(none)")
    lines.append("")
    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n\n")


def cmd_fix_reverse(_: argparse.Namespace) -> int:
    """Phase 1d helper: NULL out use_cases.product_id rows pointing at deleted products."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        conn.execute("BEGIN IMMEDIATE")
        rows = conn.execute(
            "SELECT id, product_id FROM use_cases "
            "WHERE product_id IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM products p WHERE p.id = use_cases.product_id)"
        ).fetchall()
        for uc_id, product_id in rows:
            conn.execute("UPDATE use_cases SET product_id = NULL WHERE id = ?", (uc_id,))
            print(f"  nulled use_cases.id={uc_id} (was pointing at product_id={product_id})")
        conn.commit()
        print(f"fix-reverse: cleared {len(rows)} dangling use_cases.product_id refs")
        return 0
    finally:
        conn.close()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("verify", help="Print current dangling counts (read-only)")
    sp.set_defaults(func=cmd_verify)

    sp = sub.add_parser("remap", help="Phase 1a: try automatic remap")
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument(
        "--no-scan-backups",
        action="store_true",
        help="Skip scanning data/*.backup-* for signature recovery",
    )
    sp.set_defaults(func=cmd_remap)

    sp = sub.add_parser("apply-resolved", help="Phase 1c: apply agent-recovered ids")
    sp.add_argument(
        "--resolved",
        default=str(OUT_DIR / "resolved.csv"),
        help="CSV with columns: table, old_use_case_id, product_id, resolved_use_case_id, ...",
    )
    sp.set_defaults(func=cmd_apply_resolved)

    sp = sub.add_parser(
        "quarantine", help="Phase 1c: move remaining dangling rows to *_orphaned tables"
    )
    sp.add_argument("--reason", default=None)
    sp.set_defaults(func=cmd_quarantine)

    sp = sub.add_parser(
        "fix-reverse", help="Phase 1d: NULL use_cases.product_id refs to deleted products"
    )
    sp.set_defaults(func=cmd_fix_reverse)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
