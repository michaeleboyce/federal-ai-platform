"""Build inputs for the band_product_links_2026-07 linkage pass.

Targets banded `consolidated_use_cases` rows (estimated_licenses_users
non-empty) that have NO `consolidated_use_case_products` link. For each,
proposes up to 5 catalog candidates (alias substring hits first, then
difflib similarity on the product string) so the labeling agent starts
from the likely match rather than the whole 655-product catalog.

Also snapshots the full catalog to `inputs/catalog_snapshot.csv` (pattern:
audit/linkage_pass_2026-05) so agents can go beyond the candidates.

Keyed by `slug`. Writes
`audit/retag/band_product_links_2026-07/input_batch{1..N}.csv` + `input.csv`.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT_DIR = ROOT / "audit" / "retag" / "band_product_links_2026-07"

COLUMNS = [
    "slug",
    "agency",
    "bureau",
    "ai_use_case",
    "commercial_product",
    "commercial_examples",
    "band",
    "candidates",
]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def candidates_for(
    text: str,
    names: list[tuple[str, str]],  # (normalized, canonical_name)
) -> list[str]:
    """Alias/canonical substring hits first, then difflib top-ups, max 5."""
    ntext = _norm(text)
    hits: list[str] = []
    seen: set[str] = set()
    for norm_name, canonical in names:
        if len(norm_name) >= 4 and norm_name in ntext and canonical not in seen:
            hits.append(canonical)
            seen.add(canonical)
    if len(hits) < 5 and ntext:
        scored = sorted(
            (
                (difflib.SequenceMatcher(None, ntext, n).ratio(), c)
                for n, c in names
                if c not in seen
            ),
            reverse=True,
        )
        for score, canonical in scored[:10]:
            if score < 0.45 or len(hits) >= 5:
                break
            if canonical not in seen:
                hits.append(canonical)
                seen.add(canonical)
    return hits[:5]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--batches", type=int, default=2)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        # Catalog names: canonical + aliases, mapped back to canonical.
        names: list[tuple[str, str]] = []
        catalog_rows = conn.execute(
            """
            SELECT p.canonical_name, COALESCE(p.vendor,''),
                   COALESCE(p.product_type,''),
                   (SELECT p2.canonical_name FROM products p2
                     WHERE p2.id = p.parent_product_id)
              FROM products p ORDER BY p.canonical_name
            """
        ).fetchall()
        for canonical, _v, _t, _parent in catalog_rows:
            names.append((_norm(canonical), canonical))
        for alias, canonical in conn.execute(
            """
            SELECT pa.alias_text, p.canonical_name
              FROM product_aliases pa JOIN products p ON p.id = pa.product_id
            """
        ):
            names.append((_norm(alias), canonical))

        rows = conn.execute(
            """
            SELECT c.slug, a.abbreviation, COALESCE(fo.name,''),
                   c.ai_use_case,
                   COALESCE(c.commercial_product,''),
                   COALESCE(c.commercial_examples,''),
                   c.estimated_licenses_users
              FROM consolidated_use_cases c
              JOIN agencies a ON a.id = c.agency_id
              LEFT JOIN federal_organizations fo
                     ON fo.id = c.bureau_organization_id
             WHERE c.estimated_licenses_users IS NOT NULL
               AND c.estimated_licenses_users != ''
               AND NOT EXISTS (SELECT 1 FROM consolidated_use_case_products cp
                                WHERE cp.consolidated_use_case_id = c.id)
             ORDER BY a.abbreviation, c.slug
            """
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        raise SystemExit("No unlinked banded rows — already linked?")

    out_rows = []
    for slug, agency, bureau, use_case, product, examples, band in rows:
        cands = candidates_for(
            " ".join([product, examples, use_case]), names
        )
        out_rows.append(
            {
                "slug": slug,
                "agency": agency,
                "bureau": bureau,
                "ai_use_case": use_case,
                "commercial_product": product,
                "commercial_examples": examples,
                "band": band,
                "candidates": "; ".join(cands),
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "inputs").mkdir(exist_ok=True)
    with (OUT_DIR / "inputs" / "catalog_snapshot.csv").open(
        "w", newline=""
    ) as f:
        w = csv.writer(f)
        w.writerow(["canonical_name", "vendor", "product_type", "parent"])
        w.writerows(catalog_rows)

    def write(path: Path, rs: list[dict]) -> None:
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(rs)

    write(OUT_DIR / "input.csv", out_rows)
    per = (len(out_rows) + args.batches - 1) // args.batches
    for i in range(args.batches):
        chunk = out_rows[i * per : (i + 1) * per]
        if chunk:
            write(OUT_DIR / f"input_batch{i + 1}.csv", chunk)
            print(f"batch{i + 1}: {len(chunk)} rows")
    print(f"total: {len(out_rows)} unlinked banded rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
