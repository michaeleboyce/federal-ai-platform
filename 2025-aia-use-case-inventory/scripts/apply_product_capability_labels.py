"""Apply data/product_capability_labels.csv to product_capability_labels.

Per-product AI capability categories from the product_capability_2026_07
LLM labeling pass (audit/retag/product_capability_2026_07/). Backs the
sleeping-services board's "nothing similar deployed" test.

CSV is EXPLODED: one row per (canonical_name, category) pair; products with
no capability carry a single `none` row. Keyed by canonical_name (durable
across `make fix` id rotations); the dashboard joins on canonical_name.

Idempotent wipe-and-reload. Dry-run by default; pass --apply to write.

If the canonical CSV does not exist yet the script warns and exits 0 so the
Makefile `fedramp` target stays green until the labeling pass lands (same
contract as apply_band_labels.py).

Exit codes:
  1 - invalid enums, `none` co-occurring with a real category for the same
      product, or intra-product gen_ai inconsistency
  2 - coverage gate: a product with >=1 entry_product_edges row has no label
      (new products from a retag pass — top up via the labeling pass)

Labels whose canonical_name no longer resolves to a live product are warned
and skipped (post-merge rename).
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
CSV_PATH = ROOT / "data" / "product_capability_labels.csv"

VALID_CATEGORIES = {
    "genai_platform", "assistant", "ml_lowcode", "ml_platform",
    "doc_processing", "speech", "translation", "vision", "nlp",
    "search", "chatbot", "none",
}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_SOURCES = {"llm", "qc_confirmed", "qc_corrected", "adjudicated", "manual_override"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS product_capability_labels (
    canonical_name TEXT NOT NULL,
    category   TEXT NOT NULL CHECK (category IN
        ('genai_platform','assistant','ml_lowcode','ml_platform','doc_processing',
         'speech','translation','vision','nlp','search','chatbot','none')),
    gen_ai     INTEGER NOT NULL CHECK (gen_ai IN (0,1)),
    confidence TEXT NOT NULL CHECK (confidence IN ('high','medium','low')),
    reasoning  TEXT NOT NULL,
    model      TEXT NOT NULL,
    labeled_at TEXT NOT NULL,
    source     TEXT NOT NULL DEFAULT 'llm'
               CHECK (source IN ('llm','qc_confirmed','qc_corrected',
                                 'adjudicated','manual_override')),
    PRIMARY KEY (canonical_name, category)
);
CREATE INDEX IF NOT EXISTS idx_pcl_category
    ON product_capability_labels(category);
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write the DB (default: dry run)")
    args = ap.parse_args()

    if not CSV_PATH.exists():
        print(f"warn: {CSV_PATH.name} not present yet; skipping "
              "(labeling pass product_capability_2026_07 has not landed)")
        return

    with CSV_PATH.open() as f:
        rows = list(csv.DictReader(f))

    bad = [
        r for r in rows
        if r["category"] not in VALID_CATEGORIES
        or r["confidence"] not in VALID_CONFIDENCE
        or (r.get("source") or "llm") not in VALID_SOURCES
        or r["gen_ai"] not in {"0", "1"}
        or not r["reasoning"].strip()
        or not r["canonical_name"].strip()
    ]
    if bad:
        print(f"{len(bad)} invalid CSV rows, e.g. {bad[0]['canonical_name']!r}; aborting")
        sys.exit(1)

    by_product: dict[str, list[dict]] = {}
    for r in rows:
        by_product.setdefault(r["canonical_name"], []).append(r)
    for name, rs in by_product.items():
        cats = {r["category"] for r in rs}
        if "none" in cats and len(cats) > 1:
            print(f"'none' co-occurs with categories for {name!r}; aborting")
            sys.exit(1)
        if len({r["gen_ai"] for r in rs}) > 1:
            print(f"inconsistent gen_ai within {name!r}; aborting")
            sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        live = {
            r["canonical_name"]
            for r in conn.execute(
                """SELECT DISTINCT p.canonical_name
                     FROM products p
                     JOIN entry_product_edges e ON e.product_id = p.id"""
            )
        }
        labeled = set(by_product)
        all_products = _all_products(conn)
        keep = [r for r in rows if r["canonical_name"] in live
                or r["canonical_name"] in all_products]
        for name in sorted(labeled - {r["canonical_name"] for r in keep}):
            print(f"warn: skipping label for unknown product {name!r} (renamed/merged?)")

        if args.apply:
            with conn:
                conn.execute("DELETE FROM product_capability_labels")
                conn.executemany(
                    """
                    INSERT INTO product_capability_labels (
                        canonical_name, category, gen_ai, confidence,
                        reasoning, model, labeled_at, source
                    ) VALUES (?,?,?,?,?,?,?,?)
                    """,
                    [
                        (
                            r["canonical_name"], r["category"], int(r["gen_ai"]),
                            r["confidence"], r["reasoning"], r["model"],
                            r["labeled_at"], r.get("source") or "llm",
                        )
                        for r in keep
                    ],
                )
            n = conn.execute(
                "SELECT COUNT(*) FROM product_capability_labels"
            ).fetchone()[0]
            print(f"applied: {n} rows")
        else:
            print(f"dry run: would load {len(keep)} rows (use --apply)")

        kept_products = {r["canonical_name"] for r in keep}
        cats: dict[str, int] = {}
        for r in keep:
            cats[r["category"]] = cats.get(r["category"], 0) + 1
        print(f"coverage: {len(kept_products & live)}/{len(live)} edged products")
        for c in sorted(cats):
            print(f"  {c:<15} {cats[c]}")

        missing = sorted(live - kept_products)
        if missing:
            print(f"ERROR: {len(missing)} edged products unlabeled, e.g. {missing[:5]}")
            print("top up via the product_capability_2026_07 labeling pass")
            sys.exit(2)
    finally:
        conn.close()


def _all_products(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute("SELECT canonical_name FROM products")}


if __name__ == "__main__":
    main()
