"""Extend org_ai_maturity with the two agency-level columns.

Prepares the maturity collapse (m023): `org_ai_maturity` becomes the
single physical maturity table, holding BOTH the per-agency rows
(computed by the agency pass in scripts/compute_org_maturity.py, keyed
by the agency's legacy-linked organization) and the sub-org rows (the
existing MIN_USE_CASES>=5 pass). The two columns below existed only on
`agency_ai_maturity`:

  - total_consolidated_entries: Appendix-B/COTS row count (agency-level
    concept; NULL on sub-org rows)
  - year_over_year_growth: 2024→2025 individual-filings growth (agency-
    level concept, suppressed for format-switch agencies; NULL on
    sub-org rows)

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "022_org_maturity_agency_columns"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(
        r[1] == column for r in conn.execute(f"PRAGMA table_info({table})")
    )


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def apply(conn: sqlite3.Connection) -> None:
    # Tolerant of minimal test fixtures where earlier migrations are ledger-
    # marked but never ran (tests/test_migration_m004.py); on any real DB
    # m001 has created org_ai_maturity before this runs.
    if not _table_exists(conn, "org_ai_maturity"):
        return
    for col, decl in (
        ("total_consolidated_entries", "INTEGER"),
        ("year_over_year_growth", "REAL"),
    ):
        if not _column_exists(conn, "org_ai_maturity", col):
            conn.execute(
                f"ALTER TABLE org_ai_maturity ADD COLUMN {col} {decl}"
            )
