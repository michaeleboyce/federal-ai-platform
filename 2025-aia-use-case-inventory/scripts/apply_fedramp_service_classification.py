"""Apply data/fedramp_service_classification.csv to fedramp_ai_service_classification.

Idempotent wipe-and-reload keyed by the stable service-name string (survives
`make fix` id rotations; nothing in the fix/load pipeline drops this table).
Table DDL lives here per the fedramp_* sidecar convention (see
apply_fedramp_ai_classification.py) so the apply step is self-healing on a
from-scratch DB.

Dry-run by default; pass --apply to write. Exits non-zero (2) if coverage is
below 100% of the distinct services in the fedramp_authorized_services mirror
— a fresh marketplace snapshot arrived with unlabeled services; top up via
scripts/classify_fedramp_services.py.

Wired into the Makefile `fedramp` target after the product-level apply.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
CSV_PATH = ROOT / "data" / "fedramp_service_classification.csv"

VALID_CATEGORIES = {"core_ai", "ai_featured", "not_ai"}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_SOURCES = {"llm", "qc_confirmed", "qc_corrected", "adjudicated", "manual_override"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS fedramp_ai_service_classification (
    service       TEXT PRIMARY KEY,
    category      TEXT NOT NULL CHECK (category IN ('core_ai','ai_featured','not_ai')),
    confidence    TEXT NOT NULL CHECK (confidence IN ('high','medium','low')),
    reasoning     TEXT NOT NULL,
    signals       TEXT,
    model         TEXT NOT NULL,
    input_hash    TEXT NOT NULL,
    classified_at TEXT NOT NULL,
    source        TEXT NOT NULL DEFAULT 'llm'
                  CHECK (source IN ('llm','qc_confirmed','qc_corrected',
                                    'adjudicated','manual_override'))
);
CREATE INDEX IF NOT EXISTS idx_fasc_category
    ON fedramp_ai_service_classification(category);
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write the DB (default: dry run)")
    args = ap.parse_args()

    if not CSV_PATH.exists():
        print(f"missing {CSV_PATH}; run scripts/classify_fedramp_services.py first")
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
        print(f"{len(bad)} invalid CSV rows, e.g. {bad[0]['service']!r}; aborting")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        live = {
            r["service"]
            for r in conn.execute(
                "SELECT DISTINCT service FROM fedramp_authorized_services"
            )
        }
        keep = [r for r in rows if r["service"] in live]
        orphans = [r["service"] for r in rows if r["service"] not in live]
        for svc in orphans:
            print(f"warn: skipping orphan service {svc!r} (not in current snapshot)")

        if args.apply:
            with conn:
                conn.execute("DELETE FROM fedramp_ai_service_classification")
                conn.executemany(
                    """
                    INSERT INTO fedramp_ai_service_classification (
                        service, category, confidence, reasoning, signals,
                        model, input_hash, classified_at, source
                    ) VALUES (?,?,?,?,?,?,?,?,?)
                    """,
                    [
                        (
                            r["service"], r["category"], r["confidence"],
                            r["reasoning"], r["signals"] or None, r["model"],
                            r["input_hash"], r["classified_at"],
                            r.get("source") or "llm",
                        )
                        for r in keep
                    ],
                )
            n = conn.execute(
                "SELECT COUNT(*) FROM fedramp_ai_service_classification"
            ).fetchone()[0]
            print(f"applied: {n} rows")
        else:
            print(f"dry run: would load {len(keep)} rows (use --apply)")

        cats: dict[str, int] = {}
        for r in keep:
            cats[r["category"]] = cats.get(r["category"], 0) + 1
        print(f"coverage: {len(keep)}/{len(live)} distinct services")
        for c in sorted(cats):
            print(f"  {c:<12} {cats[c]}")

        if len(keep) < len(live):
            missing = sorted(live - {r["service"] for r in keep})
            print(f"ERROR: {len(missing)} unlabeled services, e.g. {missing[:5]}")
            print("re-run scripts/classify_fedramp_services.py for the new snapshot rows")
            sys.exit(2)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
