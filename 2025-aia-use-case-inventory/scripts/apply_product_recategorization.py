"""Apply IFP product-category assignments from the audit/product_categorization proposal.

`products.product_type` is an IFP-curated category (general_llm, security_tool,
productivity, etc.) — distinct from OMB's `ai_classification` field, which
lives on use_cases. The cleanup_products_taxonomy.py step backfills NULL
values to the literal string 'unclassified'; this script then upgrades those
'unclassified' rows (and any matching by canonical_name) to specific
categories per the curated proposal at audit/product_categorization/proposal.json.

Resolution order for each assignment row:
  1. Match by `id` if a product with that id exists.
  2. Fall back to canonical_name lookup (so the script survives DB re-keying
     between runs — products IDs are AUTOINCREMENT and shift when seeds change).

Idempotent: re-running produces no new changes.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
PROPOSAL_PATH = ROOT / "audit" / "product_categorization" / "proposal.json"


def main() -> int:
    if not PROPOSAL_PATH.exists():
        print(f"[recategorize] proposal not found at {PROPOSAL_PATH} — skipping")
        return 0

    proposal = json.loads(PROPOSAL_PATH.read_text())
    assignments = proposal.get("assignments", [])
    if not assignments:
        print("[recategorize] no assignments in proposal — skipping")
        return 0

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        # Build lookup: canonical_name → id and id → current product_type.
        rows = conn.execute(
            "SELECT id, canonical_name, product_type FROM products"
        ).fetchall()
        by_id = {r["id"]: dict(r) for r in rows}
        by_name = {r["canonical_name"].lower(): r["id"] for r in rows}

        applied = 0
        unchanged = 0
        skipped_missing = 0
        for a in assignments:
            target_id = a.get("id")
            name = a.get("canonical_name", "")
            category = a.get("category")
            if not category:
                continue

            product_id = None
            if target_id is not None and target_id in by_id:
                product_id = target_id
            elif name and name.lower() in by_name:
                product_id = by_name[name.lower()]

            if product_id is None:
                skipped_missing += 1
                continue

            current = by_id[product_id]["product_type"]
            if current == category:
                unchanged += 1
                continue

            conn.execute(
                "UPDATE products SET product_type = ? WHERE id = ?",
                (category, product_id),
            )
            applied += 1

        conn.commit()

        # Coverage report
        remaining_unclassified = conn.execute(
            """
            SELECT COUNT(*) FROM products
            WHERE product_type IS NULL
               OR LOWER(TRIM(product_type)) IN ('', 'unclassified')
            """
        ).fetchone()[0]

        print(
            "[recategorize] "
            f"applied={applied} unchanged={unchanged} "
            f"skipped_missing={skipped_missing} remaining_unclassified={remaining_unclassified}"
        )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
