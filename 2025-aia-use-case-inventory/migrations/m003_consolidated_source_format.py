"""Add source_format column to consolidated_use_cases.

The 2025 OMB consolidated COTS file is a 5-column aggregate (one Agency column,
no Commercial Examples) — distinct from the older 6-column per-agency form. We
record which variant produced each row so future loader changes can find/migrate
old data without guesswork.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "003_consolidated_source_format"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def apply(conn: sqlite3.Connection) -> None:
    if not _column_exists(conn, "consolidated_use_cases", "source_format"):
        conn.execute(
            "ALTER TABLE consolidated_use_cases ADD COLUMN source_format TEXT"
        )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_cuc_source_format "
        "ON consolidated_use_cases(source_format)"
    )
