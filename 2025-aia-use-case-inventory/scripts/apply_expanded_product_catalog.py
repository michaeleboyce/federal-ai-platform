"""Replay the checked-in expanded product catalog seed.

build_lookups.py intentionally seeds the older baseline catalog. This script
adds the round-2/taxonomy-expanded products and aliases from a reproducible CSV
so a fresh `make fix` does not depend on a hand-mutated DB snapshot.
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
SEED = ROOT / "data" / "expanded_product_catalog.csv"


def _bool_int(raw: str | None) -> int:
    return 1 if str(raw or "").strip() in {"1", "true", "True", "yes"} else 0


def main() -> int:
    if not SEED.exists():
        raise FileNotFoundError(SEED)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    stats = {
        "upserted_products": 0,
        "aliases_inserted": 0,
        "aliases_skipped_collision": 0,
        "parents_set": 0,
    }

    try:
        with conn:
            rows = list(csv.DictReader(SEED.open()))
            for row in rows:
                name = (row.get("canonical_name") or "").strip()
                if not name:
                    continue
                conn.execute(
                    """
                    INSERT INTO products
                        (canonical_name, vendor, product_type,
                         is_generative_ai, is_frontier_llm,
                         description, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(canonical_name) DO UPDATE SET
                        vendor = COALESCE(excluded.vendor, products.vendor),
                        product_type = COALESCE(excluded.product_type, products.product_type),
                        is_generative_ai = excluded.is_generative_ai,
                        is_frontier_llm = excluded.is_frontier_llm,
                        description = COALESCE(excluded.description, products.description),
                        notes = COALESCE(excluded.notes, products.notes)
                    """,
                    (
                        name,
                        (row.get("vendor") or "").strip() or None,
                        (row.get("product_type") or "").strip() or None,
                        _bool_int(row.get("is_generative_ai")),
                        _bool_int(row.get("is_frontier_llm")),
                        (row.get("description") or "").strip() or None,
                        (row.get("notes") or "").strip() or None,
                    ),
                )
                stats["upserted_products"] += 1

            for row in rows:
                name = (row.get("canonical_name") or "").strip()
                parent_name = (row.get("parent_canonical_name") or "").strip()
                if not name or not parent_name:
                    continue
                parent = conn.execute(
                    "SELECT id FROM products WHERE canonical_name = ?",
                    (parent_name,),
                ).fetchone()
                child = conn.execute(
                    "SELECT id FROM products WHERE canonical_name = ?",
                    (name,),
                ).fetchone()
                if not parent or not child:
                    continue
                stats["parents_set"] += conn.execute(
                    "UPDATE products SET parent_product_id = ? WHERE id = ?",
                    (parent["id"], child["id"]),
                ).rowcount

            for row in rows:
                name = (row.get("canonical_name") or "").strip()
                product = conn.execute(
                    "SELECT id FROM products WHERE canonical_name = ?",
                    (name,),
                ).fetchone()
                if not product:
                    continue
                aliases = {name}
                aliases.update(
                    a.strip()
                    for a in (row.get("aliases") or "").split("|")
                    if a.strip()
                )
                for alias in aliases:
                    existing = conn.execute(
                        "SELECT product_id FROM product_aliases WHERE alias_text = ?",
                        (alias,),
                    ).fetchone()
                    if existing:
                        if existing["product_id"] != product["id"]:
                            stats["aliases_skipped_collision"] += 1
                        continue
                    conn.execute(
                        "INSERT INTO product_aliases (product_id, alias_text) VALUES (?, ?)",
                        (product["id"], alias),
                    )
                    stats["aliases_inserted"] += 1
    finally:
        conn.close()

    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
