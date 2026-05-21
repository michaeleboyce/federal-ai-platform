"""Add `agency_ai_access_evidence` — researched public evidence of how widely
each agency has deployed general-purpose AI tools.

The OMB inventory carries an `estimated licenses/users` field, but it is a
coarse bucket and absent for most rows. This table holds a separate,
citable research layer: per-agency, per-tool findings backed by a verbatim
quote and a source URL (agency press releases, memos, GAO/OMB documents,
and reputable trade press). Rows with `status='searched_no_source'`
record a researched dead end so the gap itself is persisted and never
re-researched.

Populated by `scripts/apply_ai_access_evidence.py` from per-agent JSON
files under `audit/research/ai_access/`.

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "008_agency_ai_access_evidence"


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


def apply(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "agency_ai_access_evidence"):
        conn.execute(
            """
            CREATE TABLE agency_ai_access_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agency_id INTEGER REFERENCES agencies(id),
                agency_abbreviation TEXT NOT NULL,
                tool_name TEXT,
                finding TEXT NOT NULL,
                estimated_users TEXT,
                coverage_assessment TEXT,   -- all | most | partial | pilot | unknown | none
                exact_quote TEXT,           -- verbatim; NULL when no source
                source_url TEXT,            -- NULL when no source
                source_title TEXT,
                source_date TEXT,
                source_type TEXT,           -- official | press | inventory_field | none
                confidence TEXT,            -- high | medium | low
                status TEXT NOT NULL,       -- corroborated | searched_no_source
                notes TEXT,
                captured_at TEXT NOT NULL,
                captured_by TEXT
            )
            """
        )
    if not _index_exists(conn, "idx_ai_access_evidence_agency"):
        conn.execute(
            "CREATE INDEX idx_ai_access_evidence_agency "
            "ON agency_ai_access_evidence(agency_abbreviation)"
        )
