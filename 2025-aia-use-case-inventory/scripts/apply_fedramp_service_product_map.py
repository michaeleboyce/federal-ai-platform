"""Apply data/fedramp_service_product_map.csv to fedramp_service_product_map.

The curated crosswalk between FedRAMP in-scope AI services (rows of
fedramp_authorized_services classified core_ai) and their counterparts in the
inventory products graph. Backs the sleeping-services coverage board: a
service is only analyzable for lead-user / sleeping-holder gaps when it maps
to a canonical product that use cases can reference.

Keyed by the stable service-name string and product canonical_name — never
products.id — so the table survives `make fix` id rotations with no recovery
wiring (same convention as fedramp_ai_service_classification). The dashboard
resolves canonical_name -> products.id at query time.

Idempotent wipe-and-reload. Dry-run by default; pass --apply to write.

Exit codes:
  1 - invalid enum values, or rows sharing a product that disagree on
      capability_category / evidence_tier (gen_ai MAY disagree across service
      variants of one product, e.g. Vertex AI Search vs Vertex ML Metadata;
      consumers aggregate MAX(gen_ai) per product)
  2 - a product_canonical_name no longer resolves via products/product_aliases
      (the mapped product left the catalog; fix the CSV), or a mapped service
      is present in fedramp_ai_service_classification with category != core_ai
      (crosswalk/classification disagreement)

Orphan services absent from the current fedramp_authorized_services snapshot
are warned and skipped, matching the classification apply.

Wired into the Makefile `fedramp` target after the service-classification apply.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
CSV_PATH = ROOT / "data" / "fedramp_service_product_map.csv"

VALID_CONFIDENCE = {"strong", "inferred"}
VALID_CATEGORIES = {
    "genai_platform", "assistant", "ml_lowcode", "ml_platform",
    "doc_processing", "speech", "translation", "vision", "nlp",
    "search", "chatbot",
}
VALID_TIERS = {"named_offering", "catalog"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS fedramp_service_product_map (
    service                TEXT PRIMARY KEY,
    product_canonical_name TEXT NOT NULL,
    confidence             TEXT NOT NULL CHECK (confidence IN ('strong','inferred')),
    capability_category    TEXT NOT NULL CHECK (capability_category IN
        ('genai_platform','assistant','ml_lowcode','ml_platform','doc_processing',
         'speech','translation','vision','nlp','search','chatbot')),
    gen_ai                 INTEGER NOT NULL CHECK (gen_ai IN (0,1)),
    evidence_tier          TEXT NOT NULL CHECK (evidence_tier IN ('named_offering','catalog')),
    notes                  TEXT
);
CREATE INDEX IF NOT EXISTS idx_fspm_product
    ON fedramp_service_product_map(product_canonical_name);
"""


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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write the DB (default: dry run)")
    args = ap.parse_args()

    if not CSV_PATH.exists():
        print(f"missing {CSV_PATH}")
        sys.exit(1)

    with CSV_PATH.open() as f:
        rows = list(csv.DictReader(f))

    bad = [
        r for r in rows
        if r["confidence"] not in VALID_CONFIDENCE
        or r["capability_category"] not in VALID_CATEGORIES
        or r["gen_ai"] not in {"0", "1"}
        or r["evidence_tier"] not in VALID_TIERS
        or not r["service"].strip()
        or not r["product_canonical_name"].strip()
    ]
    if bad:
        print(f"{len(bad)} invalid CSV rows, e.g. {bad[0]['service']!r}; aborting")
        sys.exit(1)

    # Per-product consistency: category and tier must agree across a product's
    # service variants (gen_ai may not — MAX-aggregated by consumers).
    per_product: dict[str, set[tuple[str, str]]] = {}
    for r in rows:
        per_product.setdefault(r["product_canonical_name"], set()).add(
            (r["capability_category"], r["evidence_tier"])
        )
    inconsistent = {p: v for p, v in per_product.items() if len(v) > 1}
    if inconsistent:
        for p, v in inconsistent.items():
            print(f"inconsistent category/tier for product {p!r}: {sorted(v)}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)

        unresolved = sorted({
            r["product_canonical_name"] for r in rows
            if _resolve(conn, r["product_canonical_name"]) is None
        })
        if unresolved:
            print(f"ERROR: {len(unresolved)} unresolvable products: {unresolved}")
            print("the mapped product left the catalog; fix the CSV")
            sys.exit(2)

        non_core = [
            r["service"] for r in rows
            if conn.execute(
                """SELECT 1 FROM fedramp_ai_service_classification
                    WHERE service = ? AND category != 'core_ai'""",
                (r["service"],),
            ).fetchone()
        ]
        if non_core:
            print(f"ERROR: mapped services not classified core_ai: {non_core}")
            sys.exit(2)

        live = {
            r["service"]
            for r in conn.execute(
                "SELECT DISTINCT service FROM fedramp_authorized_services"
            )
        }
        keep = [r for r in rows if r["service"] in live]
        for r in rows:
            if r["service"] not in live:
                print(f"warn: skipping orphan service {r['service']!r} (not in current snapshot)")

        if args.apply:
            with conn:
                conn.execute("DELETE FROM fedramp_service_product_map")
                conn.executemany(
                    """
                    INSERT INTO fedramp_service_product_map (
                        service, product_canonical_name, confidence,
                        capability_category, gen_ai, evidence_tier, notes
                    ) VALUES (?,?,?,?,?,?,?)
                    """,
                    [
                        (
                            r["service"], r["product_canonical_name"],
                            r["confidence"], r["capability_category"],
                            int(r["gen_ai"]), r["evidence_tier"],
                            r["notes"] or None,
                        )
                        for r in keep
                    ],
                )
            n = conn.execute(
                "SELECT COUNT(*) FROM fedramp_service_product_map"
            ).fetchone()[0]
            print(f"applied: {n} rows")
        else:
            print(f"dry run: would load {len(keep)} rows (use --apply)")

        products = {r["product_canonical_name"] for r in keep}
        tiers: dict[str, int] = {}
        for r in keep:
            tiers[r["evidence_tier"]] = tiers.get(r["evidence_tier"], 0) + 1
        print(f"coverage: {len(keep)} services -> {len(products)} products")
        for t in sorted(tiers):
            print(f"  {t:<15} {tiers[t]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
