"""Add `agency_ai_policy_documents` and `agency_ai_policy_compliance` —
the two tables behind the dashboard's `/policy` section.

`agency_ai_policy_documents` is one row per published federal AI policy
document (agency-issued strategies / compliance plans / genAI policies /
governance charters / etc., plus the foundational executive orders and OMB
memoranda tagged `agency_type='White House / OMB'`). Columns mirror the
research tracker's `audit/research/ai_strategies/documents.csv`.

`agency_ai_policy_compliance` is one row per agency searched, capturing
search status + per-artifact years (M-25-21 AI Strategy, compliance plan,
genAI policy) + CAIO status. Columns mirror `coverage.csv`.

Both tables are idempotent (DDL guarded by existence checks) and intended to
be truncated-and-reloaded by `scripts/load_ai_policy_tracker.py`. There are
no foreign keys to `agencies` because the tracker covers two synthetic
"agencies" (EOP, OMB) that don't appear in the agencies table.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "012_ai_policy_tracker"


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
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
            (name,),
        ).fetchone()
        is not None
    )


def apply(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "agency_ai_policy_documents"):
        conn.execute(
            """
            CREATE TABLE agency_ai_policy_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agency_abbr TEXT NOT NULL,
                agency_name TEXT NOT NULL,
                agency_type TEXT NOT NULL,
                issuing_office TEXT,
                document_type TEXT NOT NULL,
                document_title TEXT NOT NULL,
                publication_year INTEGER NOT NULL,
                publication_date TEXT,
                pages INTEGER,
                issuing_memo TEXT,
                superseded INTEGER NOT NULL DEFAULT 0,
                is_public INTEGER NOT NULL DEFAULT 1,
                url TEXT NOT NULL,
                local_path TEXT,
                access_status TEXT NOT NULL,
                date_accessed TEXT NOT NULL,
                notes TEXT
            )
            """
        )

    for col, ddl_idx in (
        ("agency_abbr", "idx_agency_ai_policy_documents_agency_abbr"),
        ("agency_type", "idx_agency_ai_policy_documents_agency_type"),
        ("document_type", "idx_agency_ai_policy_documents_document_type"),
        ("publication_year", "idx_agency_ai_policy_documents_publication_year"),
    ):
        if not _index_exists(conn, ddl_idx):
            conn.execute(
                f"CREATE INDEX {ddl_idx} ON agency_ai_policy_documents ({col})"
            )

    if not _table_exists(conn, "agency_ai_policy_compliance"):
        conn.execute(
            """
            CREATE TABLE agency_ai_policy_compliance (
                agency_abbr TEXT PRIMARY KEY,
                agency_name TEXT NOT NULL,
                agency_type TEXT NOT NULL,
                searched INTEGER NOT NULL DEFAULT 1,
                date_searched TEXT NOT NULL,
                ai_landing_page_url TEXT,
                ai_strategy_year INTEGER,
                compliance_plan_year INTEGER,
                genai_policy_year INTEGER,
                caio_status TEXT,
                other_policy_count INTEGER NOT NULL DEFAULT 0,
                total_documents INTEGER NOT NULL DEFAULT 0,
                gaps TEXT,
                notes TEXT
            )
            """
        )

    conn.commit()
