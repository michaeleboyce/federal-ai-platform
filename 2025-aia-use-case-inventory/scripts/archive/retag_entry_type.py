"""Surgical migration: recompute use_case_tags.entry_type for every row
using the Phase 2 Agent C corrected infer_entry_type() precedence.

Only the entry_type column is updated — no other tag columns are touched.
Consolidated-linked tag rows are re-evaluated with is_consolidated=True.
"""

from pathlib import Path
import sys

# Allow running as `python scripts/retag_entry_type.py` from repo root.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import sqlite3  # noqa: E402

from auto_tag import infer_entry_type, load_products  # noqa: E402

DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"


def _counts(conn):
    out = {}
    for r in conn.execute(
        "SELECT entry_type, COUNT(*) FROM use_case_tags GROUP BY entry_type"
    ):
        out[r[0]] = r[1]
    out["__vendor_populated_custom_system"] = conn.execute(
        """
        SELECT COUNT(*) FROM use_case_tags t
        JOIN use_cases u ON u.id = t.use_case_id
        WHERE t.entry_type = 'custom_system'
          AND u.vendor_name IS NOT NULL AND TRIM(u.vendor_name) <> ''
        """
    ).fetchone()[0]
    return out


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        before = _counts(conn)
        print("BEFORE:", before)

        products_dict = load_products(conn)

        # 1. Individual use-case-backed tag rows
        rows = conn.execute(
            """
            SELECT t.id AS tag_id,
                   t.entry_type AS current_entry_type,
                   u.id AS use_case_id,
                   u.product_id,
                   u.template_id,
                   u.use_case_name,
                   u.problem_statement,
                   u.development_type,
                   u.vendor_name
            FROM use_case_tags t
            JOIN use_cases u ON u.id = t.use_case_id
            WHERE t.use_case_id IS NOT NULL
            """
        ).fetchall()

        updates = 0
        for r in rows:
            row_dict = {k: (r[k] if r[k] is not None else "") for k in r.keys()}
            new_type = infer_entry_type(
                row_dict,
                r["product_id"],
                r["template_id"],
                False,
                products_dict,
            )
            if new_type != r["current_entry_type"]:
                conn.execute(
                    "UPDATE use_case_tags SET entry_type = ? WHERE id = ?",
                    (new_type, r["tag_id"]),
                )
                updates += 1

        # 2. Consolidated-backed tag rows — always generic_use_pattern
        cons_rows = conn.execute(
            """
            SELECT t.id AS tag_id, t.entry_type AS current_entry_type
            FROM use_case_tags t
            WHERE t.consolidated_use_case_id IS NOT NULL
            """
        ).fetchall()
        for r in cons_rows:
            if r["current_entry_type"] != "generic_use_pattern":
                conn.execute(
                    "UPDATE use_case_tags SET entry_type = ? WHERE id = ?",
                    ("generic_use_pattern", r["tag_id"]),
                )
                updates += 1

        conn.commit()
        after = _counts(conn)
        print(f"UPDATED {updates} rows")
        print("AFTER:", after)
    finally:
        conn.close()


if __name__ == "__main__":
    run()
