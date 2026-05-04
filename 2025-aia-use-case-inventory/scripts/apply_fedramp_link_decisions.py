"""Apply hand-curated FedRAMP-product links from a CSV.

CSV columns: canonical_name, fedramp_id, confidence, source, notes
Lines starting with `#` are treated as comments and skipped (in addition to
the standard CSV-DictReader-skips-blank-lines behavior).

Resolves canonical_name to current products.id via canonical_name first,
then aliases. Validates fedramp_id exists in fedramp_products. Idempotent
via INSERT OR IGNORE on UNIQUE(inventory_product_id, fedramp_id, source).

Replaces the broken inventory_id-based lookup in import_fedramp_link_decisions.py
for this curation cycle. The older script can stay for historical CSVs.

Usage:
    python3 scripts/apply_fedramp_link_decisions.py            # dry-run
    python3 scripts/apply_fedramp_link_decisions.py --apply
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
CSV_PATH = ROOT / "data" / "fedramp_link_decisions.csv"


def _resolve(conn: sqlite3.Connection, name: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM products WHERE LOWER(canonical_name) = LOWER(?)", (name,)
    ).fetchone()
    if row:
        return row[0]
    row = conn.execute(
        "SELECT product_id FROM product_aliases WHERE LOWER(alias_text) = LOWER(?)", (name,)
    ).fetchone()
    return row[0] if row else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    inserts, skipped_no_product, skipped_no_fedramp, skipped_existing = [], [], [], []

    with CSV_PATH.open() as f:
        # Filter out comment lines BEFORE handing to DictReader so '# foo' rows
        # are not parsed as data rows whose canonical_name starts with '#'.
        non_comment = (line for line in f if not line.lstrip().startswith("#"))
        reader = csv.DictReader(non_comment)
        rows = list(reader)

    if args.apply:
        conn.execute("BEGIN")
    try:
        for row in rows:
            name = row["canonical_name"].strip()
            fr_id = row["fedramp_id"].strip()
            confidence = row["confidence"].strip() or "manual"
            source = row["source"].strip() or "manual_csv"
            notes = row["notes"].strip()

            pid = _resolve(conn, name)
            if pid is None:
                skipped_no_product.append((name, fr_id))
                continue
            ok = conn.execute(
                "SELECT 1 FROM fedramp_products WHERE fedramp_id = ?", (fr_id,)
            ).fetchone() is not None
            if not ok:
                skipped_no_fedramp.append((name, fr_id))
                continue
            already = conn.execute(
                "SELECT 1 FROM fedramp_product_links "
                "WHERE inventory_product_id = ? AND fedramp_id = ? AND source = ?",
                (pid, fr_id, source),
            ).fetchone() is not None
            if already:
                skipped_existing.append((name, fr_id))
                continue
            inserts.append((name, pid, fr_id, confidence, source))
            if args.apply:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO fedramp_product_links
                        (inventory_product_id, fedramp_id, confidence, source, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (pid, fr_id, confidence, source, notes),
                )
        if args.apply:
            conn.commit()
    except Exception:
        if args.apply:
            conn.rollback()
        raise

    print(f"csv rows: {len(rows)}")
    print(f"  inserts:                 {len(inserts)}")
    print(f"  skipped (no product):    {len(skipped_no_product)}")
    print(f"  skipped (no fedramp_id): {len(skipped_no_fedramp)}")
    print(f"  skipped (already):       {len(skipped_existing)}")

    if inserts:
        print("\nInserts:")
        for name, pid, fr_id, conf, src in inserts:
            print(f"  pid={pid:<5} fedramp_id={fr_id:<14} src={src:<11} {name!r}")

    if skipped_no_product:
        print("\nSkipped (no product):")
        for name, fr_id in skipped_no_product:
            print(f"  {name!r}  (intended fedramp_id={fr_id})")
    if skipped_no_fedramp:
        print("\nSkipped (fedramp_id not in fedramp_products):")
        for name, fr_id in skipped_no_fedramp:
            print(f"  {name!r}  bad_id={fr_id!r}")

    post = conn.execute("SELECT COUNT(*) FROM fedramp_product_links").fetchone()[0]
    print(f"\nfedramp_product_links total rows: {post}")

    if not args.apply:
        print("\n(dry-run; pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
