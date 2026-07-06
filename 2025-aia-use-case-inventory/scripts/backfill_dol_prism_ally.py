"""Backfill the one row silently dropped by SKIP_FILES: DOL's Prism Ally.

The 2026-07 SKIP_FILES supersession audit
(audit/omb_only_ingest/skipfiles_coverage.md) verified 6 of the 7 skipped
per-agency consolidated files are true duplicates of the COTS aggregate.
The exception: DOL-2025-ai-inventory-consolidated.csv row 14 —

    "Answering federal regulatory and agency policy questions related to
     acquisition using a generative AI tool."  (product: Prism Ally, Unison)

— a DOL-specific addendum outside the fixed 20-item template, absent from
the COTS aggregate, DOL's narrative file, and OMB's consolidated file.
(The similarly non-template row 13, Hololens, IS covered — it appears in
DOL's narrative file as use_case_id DOL-08.)

We keep the file in SKIP_FILES (its other 13 rows are genuine duplicates;
un-skipping would cross-duplicate Hololens) and insert just this row into
consolidated_use_cases, agency resolved by abbreviation at write time.

Runs in `make fix` right after load_inventories.py. Idempotent: keyed by
deterministic slug.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db import get_connection  # noqa: E402
from load_inventories import _lookup_agency_id, slugify  # noqa: E402

USE_CASE = (
    "Answering federal regulatory and agency policy questions related to "
    "acquisition using a generative AI tool."
)
PRODUCT = "Prism Ally"
SOURCE_FILE = "DOL-2025-ai-inventory-consolidated.csv"


def main() -> int:
    conn = get_connection()
    try:
        agency_id = _lookup_agency_id(conn, "DOL")
        if agency_id is None:
            print("FATAL: DOL not found in agencies")
            return 1
        slug = slugify("DOL", USE_CASE)
        if conn.execute(
            "SELECT 1 FROM consolidated_use_cases WHERE slug = ?", (slug,)
        ).fetchone():
            print(f"[dol-prism-ally] already present ({slug}) — no-op")
            return 0
        with conn:
            conn.execute(
                """INSERT INTO consolidated_use_cases
                   (agency_id, source_file, slug, ai_use_case,
                    commercial_product, agency_uses, raw_json, source_format)
                   VALUES (?, ?, ?, ?, ?, 'Y', ?, 'dol_addendum_backfill')""",
                (
                    agency_id,
                    SOURCE_FILE,
                    slug,
                    USE_CASE,
                    PRODUCT,
                    json.dumps(
                        {
                            "AI Use Case": USE_CASE,
                            "Commercial Examples": PRODUCT,
                            "_backfill": "scripts/backfill_dol_prism_ally.py",
                            "_audit": "audit/omb_only_ingest/skipfiles_coverage.md",
                        }
                    ),
                ),
            )
        print(f"[dol-prism-ally] inserted ({slug})")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
