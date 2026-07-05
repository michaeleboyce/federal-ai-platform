"""Build the input for the product_band_audit_2026-07 spot-audit.

One row per canonical product that appears on at least one banded
`consolidated_use_cases` row. These products drive the seat model's
stratum mapping, so their `product_type`, family (`parent_product_id`),
and `is_generative_ai` flags carry real weight — the input shows the
reviewer every banded row a product touches, with band sizes, so the
stakes are visible.

Writes `audit/product_band_audit_2026-07/inputs/products_on_banded_rows.csv`.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT_DIR = ROOT / "audit" / "product_band_audit_2026-07"

COLUMNS = [
    "canonical_name",
    "vendor",
    "product_type",
    "parent_canonical_name",
    "is_generative_ai",
    "is_frontier_llm",
    "banded_rows",
    "max_band",
    "agencies",
    "example_use_cases",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        rows = conn.execute(
            """
            WITH banded AS (
              SELECT c.id, c.agency_id, c.ai_use_case,
                     c.estimated_licenses_users AS band,
                     CASE c.estimated_licenses_users
                       WHEN '1-100' THEN 1 WHEN '101-1000' THEN 2
                       WHEN '1001-5000' THEN 3 WHEN '5001-10,000' THEN 4
                       WHEN '10,000-50,000' THEN 5 WHEN '50,000+' THEN 6
                       ELSE 0 END AS band_rank
                FROM consolidated_use_cases c
               WHERE c.estimated_licenses_users IS NOT NULL
                 AND c.estimated_licenses_users != ''
            )
            SELECT p.canonical_name,
                   COALESCE(p.vendor, ''),
                   COALESCE(p.product_type, ''),
                   COALESCE((SELECT p2.canonical_name FROM products p2
                              WHERE p2.id = p.parent_product_id), ''),
                   COALESCE(p.is_generative_ai, 0),
                   COALESCE(p.is_frontier_llm, 0),
                   COUNT(DISTINCT b.id),
                   (SELECT b2.band FROM banded b2
                     JOIN consolidated_use_case_products cp2
                       ON cp2.consolidated_use_case_id = b2.id
                    WHERE cp2.product_id = p.id
                    ORDER BY b2.band_rank DESC LIMIT 1),
                   (SELECT GROUP_CONCAT(DISTINCT a.abbreviation)
                      FROM banded b3
                      JOIN consolidated_use_case_products cp3
                        ON cp3.consolidated_use_case_id = b3.id
                      JOIN agencies a ON a.id = b3.agency_id
                     WHERE cp3.product_id = p.id),
                   (SELECT GROUP_CONCAT(substr(b4.ai_use_case, 1, 80), ' || ')
                      FROM (SELECT b4i.ai_use_case, cp4.product_id
                              FROM banded b4i
                              JOIN consolidated_use_case_products cp4
                                ON cp4.consolidated_use_case_id = b4i.id
                             ORDER BY b4i.band_rank DESC LIMIT 3) b4
                     WHERE b4.product_id = p.id)
              FROM products p
              JOIN consolidated_use_case_products cp ON cp.product_id = p.id
              JOIN banded b ON b.id = cp.consolidated_use_case_id
             GROUP BY p.id
             ORDER BY COUNT(DISTINCT b.id) DESC, p.canonical_name
            """
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        raise SystemExit("No products on banded rows — wrong DB?")

    (OUT_DIR / "inputs").mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "inputs" / "products_on_banded_rows.csv"
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(rows)
    print(f"{len(rows)} products → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
