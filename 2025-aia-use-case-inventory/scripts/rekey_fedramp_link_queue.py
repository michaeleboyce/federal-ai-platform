"""Re-key the fedramp_link_queue.inventory_id column to current products.id.

Background: the queue's inventory_id values were captured against an older
products-table generation (range 85-305) and never updated when the table
was rebuilt (current ids start at 3206). The columns are still useful for
audit and downstream tooling if re-keyed.

Resolution strategy per row, in order:
    1. Exact case-insensitive match on products.canonical_name
    2. Exact case-insensitive match on product_aliases.alias_text
    3. Leave inventory_id unchanged; log as unresolved

Idempotent: re-running on already-rekeyed rows leaves them unchanged.

Usage:
    python3 scripts/rekey_fedramp_link_queue.py            # dry-run
    python3 scripts/rekey_fedramp_link_queue.py --apply
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"


def _resolve(conn: sqlite3.Connection, source_text: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM products WHERE LOWER(canonical_name) = LOWER(?)",
        (source_text,),
    ).fetchone()
    if row is not None:
        return row[0]
    row = conn.execute(
        "SELECT product_id FROM product_aliases WHERE LOWER(alias_text) = LOWER(?)",
        (source_text,),
    ).fetchone()
    if row is not None:
        return row[0]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, inventory_id, source_text FROM fedramp_link_queue WHERE link_kind='product'"
    ).fetchall()

    updated, unchanged, unresolved = 0, 0, []
    if args.apply:
        conn.execute("BEGIN")
    try:
        for qid, old_inv_id, source_text in rows:
            new_id = _resolve(conn, source_text)
            if new_id is None:
                unresolved.append((qid, old_inv_id, source_text))
                continue
            if new_id == old_inv_id:
                unchanged += 1
                continue
            if args.apply:
                conn.execute(
                    "UPDATE fedramp_link_queue SET inventory_id = ?, updated_at = datetime('now') WHERE id = ?",
                    (new_id, qid),
                )
            updated += 1
        if args.apply:
            conn.commit()
    except Exception:
        if args.apply:
            conn.rollback()
        raise

    print(f"queue rows scanned: {len(rows)}")
    print(f"  updated:    {updated}")
    print(f"  unchanged:  {unchanged}")
    print(f"  unresolved: {len(unresolved)}")
    if unresolved:
        print("\nUnresolved (canonical_name + alias both miss):")
        for qid, old, src in unresolved:
            print(f"  q{qid:>4}  old_inv_id={old:>4}  source_text={src!r}")

    if not args.apply:
        print("\n(dry-run; pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
