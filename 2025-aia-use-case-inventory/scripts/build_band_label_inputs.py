"""Build input slices for the band_labels_2026-07 population-labeling pass.

One row per banded `consolidated_use_cases` row (estimated_licenses_users
non-empty). Each row carries the context a labeling agent needs to decide
WHO the license band counts: the use-case narrative, the product string,
the canonical products already linked, the band, and the agency's workforce
size for plausibility checks.

Rows are keyed by the deterministic `slug` (unique, survives rebuilds) —
never numeric ids. Slices are agency-grouped so a labeler sees a whole
agency's filings together: agencies are packed greedily into N batches
balanced by row count.

Writes `audit/retag/band_labels_2026-07/input_batch{1..N}.csv` plus a
combined `input.csv`.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT_DIR = ROOT / "audit" / "retag" / "band_labels_2026-07"

COLUMNS = [
    "slug",
    "agency",
    "agency_name",
    "bureau",
    "ai_use_case",
    "commercial_product",
    "commercial_examples",
    "band",
    "band_upper",
    "linked_products",
    "linked_product_types",
    "agency_total_headcount",
]

BAND_UPPER = {
    "1-100": 100,
    "101-1000": 1000,
    "1001-5000": 5000,
    "5001-10,000": 10000,
    "10,000-50,000": 50000,
    "50,000+": 100000,
}


def fetch_rows(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT c.slug,
               a.abbreviation                    AS agency,
               a.name                            AS agency_name,
               COALESCE(fo.name, '')             AS bureau,
               c.ai_use_case,
               COALESCE(c.commercial_product, '')  AS commercial_product,
               COALESCE(c.commercial_examples, '') AS commercial_examples,
               c.estimated_licenses_users        AS band,
               (SELECT GROUP_CONCAT(p.canonical_name, '; ')
                  FROM consolidated_use_case_products cp
                  JOIN products p ON p.id = cp.product_id
                 WHERE cp.consolidated_use_case_id = c.id) AS linked_products,
               (SELECT GROUP_CONCAT(DISTINCT p.product_type)
                  FROM consolidated_use_case_products cp
                  JOIN products p ON p.id = cp.product_id
                 WHERE cp.consolidated_use_case_id = c.id) AS linked_product_types,
               (SELECT w.total_headcount
                  FROM agency_workforce_profile w
                 WHERE w.agency_id = c.agency_id AND w.level = 'agency'
                 LIMIT 1)                        AS agency_total_headcount
          FROM consolidated_use_cases c
          JOIN agencies a ON a.id = c.agency_id
          LEFT JOIN federal_organizations fo ON fo.id = c.bureau_organization_id
         WHERE c.estimated_licenses_users IS NOT NULL
           AND c.estimated_licenses_users != ''
         ORDER BY a.abbreviation, c.slug
        """
    ).fetchall()
    out = []
    for r in rows:
        d = dict(
            zip(
                [
                    "slug",
                    "agency",
                    "agency_name",
                    "bureau",
                    "ai_use_case",
                    "commercial_product",
                    "commercial_examples",
                    "band",
                    "linked_products",
                    "linked_product_types",
                    "agency_total_headcount",
                ],
                r,
            )
        )
        d["band_upper"] = BAND_UPPER.get(d["band"], 0)
        d["linked_products"] = d["linked_products"] or ""
        d["linked_product_types"] = d["linked_product_types"] or ""
        d["agency_total_headcount"] = d["agency_total_headcount"] or ""
        out.append(d)
    if not out:
        raise SystemExit("No banded rows found — wrong DB?")
    missing_slug = [d for d in out if not d["slug"]]
    if missing_slug:
        raise SystemExit(f"{len(missing_slug)} banded rows missing slug")
    return out


def pack_batches(rows: list[dict], n_batches: int) -> list[list[dict]]:
    """Greedy bin-packing by agency, largest agency first."""
    by_agency: dict[str, list[dict]] = {}
    for r in rows:
        by_agency.setdefault(r["agency"], []).append(r)
    batches: list[list[dict]] = [[] for _ in range(n_batches)]
    for _, agency_rows in sorted(
        by_agency.items(), key=lambda kv: -len(kv[1])
    ):
        smallest = min(batches, key=len)
        smallest.extend(agency_rows)
    return [b for b in batches if b]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--batches", type=int, default=8)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        rows = fetch_rows(conn)
    finally:
        conn.close()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def write(path: Path, rs: list[dict]) -> None:
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(rs)

    write(OUT_DIR / "input.csv", rows)
    batches = pack_batches(rows, args.batches)
    for i, batch in enumerate(batches, start=1):
        write(OUT_DIR / f"input_batch{i}.csv", batch)
        agencies = sorted({r["agency"] for r in batch})
        print(f"batch{i}: {len(batch)} rows — {', '.join(agencies)}")
    print(f"total: {len(rows)} rows across {len(batches)} batches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
