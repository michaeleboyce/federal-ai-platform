"""Clean up the products table to distinguish commercial products from
agency-internal platforms, and remove redundant single-mention entries
that are really just system_name aliases.

Three changes:
  1. Add `products.product_origin` column (commercial | agency_internal_platform).
  2. Backfill `use_case_products` links for round-2 seeded products from
     proposed_new_products.csv (the round-2 apply pass forgot to do this).
  3. Tag known agency-internal platforms (EDAV, ATLAS, USAi, VAO Ally,
     SpyglassGPT) as `agency_internal_platform`.
  4. Delete redundant single-mention agency-internal entries (NanCI,
     VegSpec, FOIA REDACTION (FRED), Grants.gov AI Tools) and clean up
     their aliases + use_case_products rows.

Idempotent.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
SEEDS_CSV = ROOT / "audit" / "retag" / "round2" / "products" / "proposed_new_products.csv"

sys.path.insert(0, str(ROOT))
from product_resolution import sync_primary_product_cache  # noqa: E402

AGENCY_INTERNAL_PLATFORMS = {
    "EDAV (CDC)",
    "ATLAS (Forest Service)",
    "USAi (GSA)",
    "VAO Ally",
    "SpyglassGPT",
}

REDUNDANT_DELETIONS = {
    "NanCI",
    "VegSpec",
    "FOIA REDACTION (FRED)",
    "Grants.gov AI Tools",
}


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")  # legacy join tables lack FK CASCADE
    return conn


def add_product_origin_column(conn) -> bool:
    """Add product_origin column with default 'commercial' if missing."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(products)").fetchall()}
    if "product_origin" in cols:
        return False
    conn.execute(
        "ALTER TABLE products ADD COLUMN product_origin TEXT NOT NULL DEFAULT 'commercial'"
    )
    return True


def backfill_seeded_links(conn) -> dict:
    """For each round-2 seeded product, link the use cases listed in
    sample_use_case_ids if not already linked.
    """
    stats = {"linked": 0, "skipped_missing_product": 0, "skipped_already_linked": 0}
    if not SEEDS_CSV.exists():
        return stats
    with open(SEEDS_CSV) as f:
        for row in csv.DictReader(f):
            name = (row["canonical_name"] or "").strip()
            sample_ids = (row.get("sample_use_case_ids") or "").strip()
            if not name or not sample_ids:
                continue
            prod = conn.execute(
                "SELECT id FROM products WHERE canonical_name = ?", (name,)
            ).fetchone()
            if prod is None:
                stats["skipped_missing_product"] += 1
                continue
            for raw in sample_ids.split("|"):
                try:
                    uc_id = int(raw)
                except ValueError:
                    continue
                # Confirm the use case still exists (not deleted upstream).
                if not conn.execute(
                    "SELECT 1 FROM use_cases WHERE id = ?", (uc_id,)
                ).fetchone():
                    continue
                existed = conn.execute(
                    "SELECT 1 FROM use_case_products WHERE use_case_id = ? AND product_id = ?",
                    (uc_id, prod["id"]),
                ).fetchone()
                if existed:
                    stats["skipped_already_linked"] += 1
                    continue
                conn.execute(
                    """
                    INSERT INTO use_case_products
                        (use_case_id, product_id, evidence_text, confidence)
                    VALUES (?, ?, ?, 'inferred')
                    """,
                    (uc_id, prod["id"], "round2_seeded_product_backfill"),
                )
                stats["linked"] += 1
    return stats


def tag_agency_internal(conn) -> dict:
    stats = {"tagged": 0, "missing": 0}
    for name in AGENCY_INTERNAL_PLATFORMS:
        updated = conn.execute(
            "UPDATE products SET product_origin = 'agency_internal_platform' WHERE canonical_name = ?",
            (name,),
        ).rowcount
        if updated:
            stats["tagged"] += updated
        else:
            stats["missing"] += 1
    return stats


def normalize_missing_product_types(conn) -> int:
    """Use an explicit bucket instead of leaving product_type blank."""
    return conn.execute(
        """
        UPDATE products
           SET product_type = 'unclassified'
         WHERE product_type IS NULL OR TRIM(product_type) = ''
        """
    ).rowcount


def delete_redundant(conn) -> dict:
    stats = {"deleted_products": 0, "deleted_aliases": 0, "deleted_links": 0,
             "deleted_use_case_pointers": 0, "missing": 0}
    for name in REDUNDANT_DELETIONS:
        prod = conn.execute(
            "SELECT id FROM products WHERE canonical_name = ?", (name,)
        ).fetchone()
        if prod is None:
            stats["missing"] += 1
            continue
        pid = prod["id"]
        stats["deleted_aliases"] += conn.execute(
            "DELETE FROM product_aliases WHERE product_id = ?", (pid,)
        ).rowcount
        stats["deleted_links"] += conn.execute(
            "DELETE FROM use_case_products WHERE product_id = ?", (pid,)
        ).rowcount
        # (Scalar product_id cache columns dropped by m025 — deleting the
        # edge rows above fully unlinks the product.)
        stats["deleted_products"] += conn.execute(
            "DELETE FROM products WHERE id = ?", (pid,)
        ).rowcount
    return stats


def main() -> int:
    conn = _open()
    try:
        with conn:
            added = add_product_origin_column(conn)
            backfill = backfill_seeded_links(conn)
            tagged = tag_agency_internal(conn)
            product_types_normalized = normalize_missing_product_types(conn)
            deleted = delete_redundant(conn)
            cache = sync_primary_product_cache(conn)
        print(f"[schema] product_origin column added: {added}")
        print(f"[backfill seed links]    {backfill}")
        print(f"[tag agency-internal]    {tagged}")
        print(f"[normalize product_type] {product_types_normalized}")
        print(f"[delete redundant]       {deleted}")
        print(f"[primary cache sync]     {cache}")

        rows = conn.execute(
            """
            SELECT product_origin, COUNT(*) AS n
            FROM products GROUP BY product_origin ORDER BY n DESC
            """
        ).fetchall()
        print("\nFinal products.product_origin distribution:")
        for r in rows:
            print(f"  {r['product_origin']:>30}  {r['n']:>5}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
