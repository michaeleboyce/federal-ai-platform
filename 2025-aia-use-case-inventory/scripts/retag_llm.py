"""Surgical retag pass for use_case_tags.is_general_llm_access.

Applies the rewritten auto_tag.infer_llm_flag to every row and UPDATEs only
the is_general_llm_access column. No other tag column is touched.

Prints before/after counts for:
  - total rows with is_general_llm_access=1
  - canonical false positives (classical/predictive/CV ai_classification)
  - blank-classification LLM-tagged rows

Usage:
    python scripts/retag_llm.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Allow `python scripts/retag_llm.py` from repo root.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from auto_tag import (  # noqa: E402
    infer_llm_flag,
    load_products,
    load_product_aliases,
    match_product,
    normalize,
)

DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"

# SQL used for canonical false-positive count and blank-classification LLM
# count. Must match audit/checks/check_llm_flags.py.
CANONICAL_FP_SQL = """
    SELECT COUNT(*) FROM use_cases u
    JOIN use_case_tags t ON t.use_case_id = u.id
    WHERE t.is_general_llm_access = 1
      AND (u.ai_classification LIKE '%Classical%'
           OR u.ai_classification LIKE '%Predictive%'
           OR u.ai_classification LIKE '%Computer Vision%')
"""

BLANK_CLASS_SQL = """
    SELECT COUNT(*) FROM use_cases u
    JOIN use_case_tags t ON t.use_case_id = u.id
    WHERE t.is_general_llm_access = 1
      AND (u.ai_classification IS NULL OR TRIM(u.ai_classification) = '')
"""

TOTAL_LLM_SQL = """
    SELECT COUNT(*) FROM use_case_tags WHERE is_general_llm_access = 1
"""


def snapshot(conn):
    return {
        "total_llm": conn.execute(TOTAL_LLM_SQL).fetchone()[0],
        "canonical_fp": conn.execute(CANONICAL_FP_SQL).fetchone()[0],
        "blank_class_llm": conn.execute(BLANK_CLASS_SQL).fetchone()[0],
    }


def print_snapshot(label, snap):
    print(f"[{label}]")
    print(f"  total is_general_llm_access=1 : {snap['total_llm']}")
    print(f"  canonical false positives      : {snap['canonical_fp']}")
    print(f"  blank-classification LLM-tagged: {snap['blank_class_llm']}")


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        before = snapshot(conn)
        print_snapshot("BEFORE", before)

        aliases_dict = load_product_aliases(conn)
        products_dict = load_products(conn)

        # Walk every tag row with a matching use_case; recompute flag.
        # Primary product via the m020 view (the scalar u.product_id cache
        # was dropped by m025); same strong-first ordering auto_tag used.
        rows = conn.execute(
            """
            SELECT t.id as tag_id, t.use_case_id, t.is_general_llm_access,
                   u.ai_classification, u.vendor_name, u.use_case_name,
                   u.problem_statement, u.development_type, u.system_name,
                   epp.product_id AS product_id
            FROM use_case_tags t
            JOIN use_cases u ON u.id = t.use_case_id
            LEFT JOIN entry_primary_products epp
              ON epp.entry_kind = 'use_case' AND epp.entry_id = u.id
            """
        ).fetchall()

        updated = 0
        flips_to_0 = 0
        flips_to_1 = 0

        for r in rows:
            row_dict = {
                "ai_classification": r["ai_classification"] or "",
                "vendor_name": r["vendor_name"] or "",
                "use_case_name": r["use_case_name"] or "",
                "problem_statement": r["problem_statement"] or "",
                "development_type": r["development_type"] or "",
            }

            # Recompute product_id the same way auto_tag does, in case the
            # DB row doesn't have it persisted (fallback to stored value).
            product_id = r["product_id"]
            if product_id is None:
                search_text = " ".join([
                    r["use_case_name"] or "",
                    r["vendor_name"] or "",
                    r["system_name"] or "",
                    r["problem_statement"] or "",
                ])
                product_id = match_product(search_text, aliases_dict, products_dict)

            new_flag = infer_llm_flag(row_dict, product_id, products_dict)
            old_flag = r["is_general_llm_access"]

            if new_flag != old_flag:
                conn.execute(
                    "UPDATE use_case_tags SET is_general_llm_access = ? WHERE id = ?",
                    (new_flag, r["tag_id"]),
                )
                updated += 1
                if new_flag == 0:
                    flips_to_0 += 1
                else:
                    flips_to_1 += 1

        conn.commit()
        print(f"[FLIPS] total={updated}  -> 0: {flips_to_0}  -> 1: {flips_to_1}")

        after = snapshot(conn)
        print_snapshot("AFTER", after)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
