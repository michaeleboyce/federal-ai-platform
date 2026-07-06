"""Add resolvable agency_id FK columns to the abbreviation-keyed tables.

Five tables carry a free-text agency abbreviation with no FK — and real
drift existed (case variants 'STATE'/'TREASURY' vs 'State'/'Treasury',
OMB's 'TREAS'). This adds a nullable `agency_id REFERENCES agencies(id)`
to each; scripts/backfill_agency_fks.py resolves it on every rebuild
(case-insensitive + alias map), and audit/checks/check_agency_fk_integrity
gates that only the documented exceptions stay unresolved:

  - column_mappings.agency_abbreviation: 'COTS'/'MULTI' loader artifacts
  - agency_ai_policy_documents.agency_abbr: 'EOP'/'OMB' (policy tracker
    covers entities that filed no inventory)

NOT NULL enforcement is deliberately deferred (rename-recreate on five
mid-chain tables isn't worth it; the check provides the guarantee).

Idempotent. Safe to re-run. Tolerant of minimal test fixtures.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "024_agency_fk_columns"

TABLES = (
    "column_mappings",
    "omb_consolidated_rows",
    "agency_ai_access_evidence",
    "agency_ai_policy_documents",
    "agency_ai_policy_compliance",
)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(
        r[1] == column for r in conn.execute(f"PRAGMA table_info({table})")
    )


def apply(conn: sqlite3.Connection) -> None:
    for table in TABLES:
        if not _table_exists(conn, table):
            continue
        if not _column_exists(conn, table, "agency_id"):
            conn.execute(
                f"ALTER TABLE {table} ADD COLUMN agency_id INTEGER "
                "REFERENCES agencies(id)"
            )
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table}_agency_id "
            f"ON {table}(agency_id)"
        )
