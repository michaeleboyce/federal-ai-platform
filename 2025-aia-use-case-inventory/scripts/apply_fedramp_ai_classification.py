"""Apply data/fedramp_ai_classification.csv to the fedramp_ai_classification table.

Idempotent wipe-and-reload keyed by the stable fedramp_id (survives `make fix`
product-id rotations; nothing in the fix/load pipeline drops this table). The
table DDL lives here, repo-convention for fedramp_* sidecar tables (see
link_fedramp.py LINK_SCHEMA) so the apply step is self-healing on a
from-scratch DB.

Dry-run by default; pass --apply to write. Exits non-zero if coverage is
below 100% of the current fedramp_products mirror (a fresh marketplace
snapshot arrives unclassified — re-run scripts/classify_fedramp_ai.py).

Wired into the Makefile `fedramp` target after load_fedramp.py.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
CSV_PATH = ROOT / "data" / "fedramp_ai_classification.csv"

VALID_CATEGORIES = {"core_ai", "ai_featured", "not_ai"}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_SOURCES = {"llm", "manual_override"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS fedramp_ai_classification (
    fedramp_id    TEXT PRIMARY KEY,
    category      TEXT NOT NULL CHECK (category IN ('core_ai','ai_featured','not_ai')),
    confidence    TEXT NOT NULL CHECK (confidence IN ('high','medium','low')),
    reasoning     TEXT NOT NULL,
    signals       TEXT,
    model         TEXT NOT NULL,
    input_hash    TEXT NOT NULL,
    classified_at TEXT NOT NULL,
    source        TEXT NOT NULL DEFAULT 'llm'
                  CHECK (source IN ('llm','manual_override'))
);
CREATE INDEX IF NOT EXISTS idx_fac_category
    ON fedramp_ai_classification(category);
"""

KEYWORDS = (
    "artificial intelligence", "machine learning", "generative ai",
    "large language model",
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write the DB (default: dry run)")
    args = ap.parse_args()

    if not CSV_PATH.exists():
        print(f"missing {CSV_PATH}; run scripts/classify_fedramp_ai.py first")
        sys.exit(1)

    with CSV_PATH.open() as f:
        rows = list(csv.DictReader(f))

    # Validate enums at the write boundary (CHECK constraints silently drop
    # rows when foreign_keys pragma is off — never trust upstream values).
    bad = [
        r for r in rows
        if r["category"] not in VALID_CATEGORIES
        or r["confidence"] not in VALID_CONFIDENCE
        or (r.get("source") or "llm") not in VALID_SOURCES
        or not r["reasoning"].strip()
    ]
    if bad:
        print(f"{len(bad)} invalid CSV rows, e.g. {bad[0]['fedramp_id']}; aborting")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        live = {
            r["fedramp_id"]: r["service_desc"] or ""
            for r in conn.execute(
                "SELECT fedramp_id, service_desc FROM fedramp_products"
            )
        }
        keep = [r for r in rows if r["fedramp_id"] in live]
        orphans = [r["fedramp_id"] for r in rows if r["fedramp_id"] not in live]
        for fid in orphans:
            print(f"warn: skipping orphan fedramp_id {fid} (not in current snapshot)")

        if args.apply:
            with conn:
                conn.execute("DELETE FROM fedramp_ai_classification")
                conn.executemany(
                    """
                    INSERT INTO fedramp_ai_classification (
                        fedramp_id, category, confidence, reasoning, signals,
                        model, input_hash, classified_at, source
                    ) VALUES (?,?,?,?,?,?,?,?,?)
                    """,
                    [
                        (
                            r["fedramp_id"], r["category"], r["confidence"],
                            r["reasoning"], r["signals"] or None, r["model"],
                            r["input_hash"], r["classified_at"],
                            r.get("source") or "llm",
                        )
                        for r in keep
                    ],
                )
            n = conn.execute(
                "SELECT COUNT(*) FROM fedramp_ai_classification"
            ).fetchone()[0]
            print(f"applied: {n} rows")
        else:
            print(f"dry run: would load {len(keep)} rows (use --apply)")

        # Coverage + calibration report
        cats: dict[str, int] = {}
        for r in keep:
            cats[r["category"]] = cats.get(r["category"], 0) + 1
        print(f"coverage: {len(keep)}/{len(live)} fedramp_products")
        for c in sorted(cats):
            print(f"  {c:<12} {cats[c]}")

        by_id = {r["fedramp_id"]: r for r in keep}
        kw_not_ai = [
            fid for fid, desc in live.items()
            if any(k in desc.lower() for k in KEYWORDS)
            and by_id.get(fid, {}).get("category") == "not_ai"
        ]
        no_kw_core = [
            fid for fid, desc in live.items()
            if not any(k in desc.lower() for k in KEYWORDS)
            and by_id.get(fid, {}).get("category") == "core_ai"
        ]
        print(f"calibration: keyword-positive but not_ai: {len(kw_not_ai)}; "
              f"keyword-negative but core_ai: {len(no_kw_core)}")

        if len(keep) < len(live):
            missing = sorted(set(live) - set(by_id))
            print(f"ERROR: {len(missing)} unclassified products, e.g. {missing[:5]}")
            print("re-run scripts/classify_fedramp_ai.py for the new snapshot rows")
            sys.exit(2)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
