"""Load `audit/research/ai_strategies/{documents,coverage}.csv` into the two
`agency_ai_policy_*` tables (created by migration m012). Idempotent
wipe-and-reload: both tables are TRUNCATEd before each run.

Usage:
    python3 scripts/load_ai_policy_tracker.py            # defaults to repo paths
    python3 scripts/load_ai_policy_tracker.py --check    # dry-run, prints counts

Wired into the Makefile `fix` chain after `scripts/run_migrations.py`.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV_DIR = ROOT / "audit" / "research" / "ai_strategies"
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"


def _to_int(v: str) -> int | None:
    v = (v or "").strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return None


def _to_bool(v: str) -> int:
    return 1 if (v or "").strip().lower() == "yes" else 0


def _opt(v: str) -> str | None:
    v = (v or "").strip()
    return v if v else None


def load(conn: sqlite3.Connection, csv_dir: Path = DEFAULT_CSV_DIR) -> tuple[int, int]:
    """Truncate-and-reload both tables. Returns (n_documents, n_compliance)."""
    docs_path = csv_dir / "documents.csv"
    cov_path = csv_dir / "coverage.csv"
    if not docs_path.exists():
        raise FileNotFoundError(docs_path)
    if not cov_path.exists():
        raise FileNotFoundError(cov_path)

    conn.execute("DELETE FROM agency_ai_policy_documents")
    conn.execute("DELETE FROM agency_ai_policy_compliance")

    n_docs = 0
    with docs_path.open(newline="") as f:
        for row in csv.DictReader(f):
            year = _to_int(row["publication_year"])
            if year is None:
                # The tracker invariant is "every row has publication_year";
                # treat a violation as a hard error so loader runs surface it.
                raise ValueError(
                    f"documents.csv row missing publication_year: {row['document_title']!r}"
                )
            conn.execute(
                """
                INSERT INTO agency_ai_policy_documents (
                    agency_abbr, agency_name, agency_type, issuing_office,
                    document_type, document_title, publication_year,
                    publication_date, pages, issuing_memo, superseded,
                    is_public, url, local_path, access_status, date_accessed,
                    notes
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    row["agency_abbr"].strip(),
                    row["agency_name"].strip(),
                    row["agency_type"].strip(),
                    _opt(row.get("issuing_office", "")),
                    row["document_type"].strip(),
                    row["document_title"].strip(),
                    year,
                    _opt(row.get("publication_date", "")),
                    _to_int(row.get("pages", "")),
                    _opt(row.get("issuing_memo", "")),
                    _to_bool(row.get("superseded", "")),
                    _to_bool(row.get("is_public", "yes")),
                    row["url"].strip(),
                    _opt(row.get("local_path", "")),
                    row["access_status"].strip(),
                    row["date_accessed"].strip(),
                    _opt(row.get("notes", "")),
                ),
            )
            n_docs += 1

    n_cov = 0
    with cov_path.open(newline="") as f:
        for row in csv.DictReader(f):
            conn.execute(
                """
                INSERT INTO agency_ai_policy_compliance (
                    agency_abbr, agency_name, agency_type, searched,
                    date_searched, ai_landing_page_url, ai_strategy_year,
                    compliance_plan_year, genai_policy_year, caio_status,
                    other_policy_count, total_documents, gaps, notes
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    row["agency_abbr"].strip(),
                    row["agency_name"].strip(),
                    row["agency_type"].strip(),
                    _to_bool(row.get("searched", "yes")),
                    row["date_searched"].strip(),
                    _opt(row.get("ai_landing_page_url", "")),
                    _to_int(row.get("ai_strategy_year", "")),
                    _to_int(row.get("compliance_plan_year", "")),
                    _to_int(row.get("genai_policy_year", "")),
                    _opt(row.get("caio_status", "")),
                    _to_int(row.get("other_policy_count", "0")) or 0,
                    _to_int(row.get("total_documents", "0")) or 0,
                    _opt(row.get("gaps", "")),
                    _opt(row.get("notes", "")),
                ),
            )
            n_cov += 1

    conn.commit()
    return n_docs, n_cov


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--csv-dir", type=Path, default=DEFAULT_CSV_DIR)
    ap.add_argument("--check", action="store_true", help="dry-run; rollback")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        n_docs, n_cov = load(conn, args.csv_dir)
        if args.check:
            conn.rollback()
            print(f"[check] would load {n_docs} documents, {n_cov} agencies")
        else:
            print(f"loaded {n_docs} documents, {n_cov} agencies")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
