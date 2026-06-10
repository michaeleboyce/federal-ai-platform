"""Re-derive the primary-product cache columns from the edge tables.

`use_cases.product_id` / `consolidated_use_cases.product_id` are caches of
each entry's primary product; the authoritative data is the edge tables
(`use_case_products`, `consolidated_use_case_products`). The two layers had
drifted on 341 + 3 rows (flagged by audit/checks/check_refactor_quality.py,
xfailed 2026-06-09). This recomputes the cache with the exact ordering the
check asserts: strong edges before inferred, then lowest product_id.

Runs in `make fix` after all product-link passes. Idempotent.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"


def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            uc = conn.execute(
                """
                UPDATE use_cases AS u SET product_id = (
                  SELECT ucp.product_id FROM use_case_products ucp
                   WHERE ucp.use_case_id = u.id
                   ORDER BY CASE ucp.confidence WHEN 'strong' THEN 0 ELSE 1 END,
                            ucp.product_id
                   LIMIT 1)
                WHERE COALESCE(u.product_id, -1) != COALESCE((
                  SELECT ucp.product_id FROM use_case_products ucp
                   WHERE ucp.use_case_id = u.id
                   ORDER BY CASE ucp.confidence WHEN 'strong' THEN 0 ELSE 1 END,
                            ucp.product_id
                   LIMIT 1), -1)
                """
            ).rowcount
            cons = conn.execute(
                """
                UPDATE consolidated_use_cases AS c SET product_id = (
                  SELECT cucp.product_id FROM consolidated_use_case_products cucp
                   WHERE cucp.consolidated_use_case_id = c.id
                   ORDER BY CASE cucp.confidence WHEN 'strong' THEN 0 ELSE 1 END,
                            cucp.product_id
                   LIMIT 1)
                WHERE COALESCE(c.product_id, -1) != COALESCE((
                  SELECT cucp.product_id FROM consolidated_use_case_products cucp
                   WHERE cucp.consolidated_use_case_id = c.id
                   ORDER BY CASE cucp.confidence WHEN 'strong' THEN 0 ELSE 1 END,
                            cucp.product_id
                   LIMIT 1), -1)
                """
            ).rowcount
        print(f"[primary-product cache] use_cases updated={uc} consolidated updated={cons}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
