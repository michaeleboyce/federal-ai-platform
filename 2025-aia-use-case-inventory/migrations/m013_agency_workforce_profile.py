"""Add `agency_workforce_profile` + share-of-eligible columns on
`agency_ai_access_evidence`.

Backs the headcount-derived seat estimate on the dashboard's /experience
page. Today's "Est. seats" is a sum of license-band midpoints from the
consolidated inventory; we want a parallel estimate grounded in workforce
size × AI-eligible share × measured rollout. The two estimates are
displayed side-by-side — neither replaces the other.

Populated by `scripts/apply_agency_workforce.py` from per-agent JSON files
under `audit/research/agency_workforce/`. Calibration priors live in
`audit/research/agency_workforce/priors.json`.

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "013_agency_workforce_profile"


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        is not None
    )


def _index_exists(conn: sqlite3.Connection, name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
            (name,),
        ).fetchone()
        is not None
    )


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def apply(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "agency_workforce_profile"):
        conn.execute(
            """
            CREATE TABLE agency_workforce_profile (
                organization_id        INTEGER PRIMARY KEY
                                       REFERENCES federal_organizations(id),
                agency_id              INTEGER REFERENCES agencies(id),
                level                  TEXT NOT NULL,
                total_headcount        INTEGER,
                headcount_as_of        TEXT,
                headcount_source_url   TEXT,
                headcount_source_title TEXT,
                headcount_quote        TEXT,
                ai_eligible_share      REAL,
                ai_eligible_rationale  TEXT,
                ai_eligible_source_url TEXT,
                confidence             TEXT,
                wave                   TEXT,
                tagged_by_agent        TEXT,
                notes                  TEXT,
                captured_at            TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at             TEXT
            )
            """
        )
    if not _index_exists(conn, "idx_awp_agency"):
        conn.execute(
            "CREATE INDEX idx_awp_agency "
            "ON agency_workforce_profile(agency_id)"
        )
    if not _index_exists(conn, "idx_awp_level"):
        conn.execute(
            "CREATE INDEX idx_awp_level "
            "ON agency_workforce_profile(level)"
        )

    # Extensions to agency_ai_access_evidence so Wave 2 can record
    # per-(agency, tool) share estimates and a deterministic mapping to
    # the dashboard's MatrixProductKey buckets.
    if not _column_exists(
        conn, "agency_ai_access_evidence", "estimated_share_of_eligible"
    ):
        conn.execute(
            "ALTER TABLE agency_ai_access_evidence "
            "ADD COLUMN estimated_share_of_eligible REAL"
        )
    if not _column_exists(
        conn, "agency_ai_access_evidence", "share_rationale"
    ):
        conn.execute(
            "ALTER TABLE agency_ai_access_evidence "
            "ADD COLUMN share_rationale TEXT"
        )
    if not _column_exists(
        conn, "agency_ai_access_evidence", "matrix_product_key"
    ):
        conn.execute(
            "ALTER TABLE agency_ai_access_evidence "
            "ADD COLUMN matrix_product_key TEXT"
        )
