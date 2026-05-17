"""Add `consolidated_into_omb_id` to omb_match_audit for upstream-consolidation pattern.

Phase-5 discrepancies-page upgrade adds a 7th match status
(`consolidated_upstream`) for DB rows that aren't matched 1:1 against any
OMB row but appear to have been deliberately rolled up by OMB into a
generic category row at the same agency (the ED MS-Copilot/Generative-AI
pattern). To make that traceable, we persist the OMB aggregator row's id
alongside each upstream-consolidated audit row.

`match_status` is plain TEXT with no CHECK constraint — see
`PRAGMA table_info(omb_match_audit)` — so widening the status enum needs
no DDL beyond the new pointer column.

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "005_consolidation_pattern"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(
        r[1] == column for r in conn.execute(f"PRAGMA table_info({table})")
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
    if not _column_exists(conn, "omb_match_audit", "consolidated_into_omb_id"):
        # SQLite ALTER TABLE ADD COLUMN can't add a foreign-key constraint
        # after the fact in a portable way, but it CAN store the integer.
        # The semantic FK is to omb_consolidated_rows.id; we document it
        # here and rely on application code to keep it valid.
        conn.execute(
            "ALTER TABLE omb_match_audit ADD COLUMN consolidated_into_omb_id INTEGER"
        )
    if not _index_exists(conn, "idx_omb_match_audit_consolidated"):
        conn.execute(
            "CREATE INDEX idx_omb_match_audit_consolidated "
            "ON omb_match_audit(consolidated_into_omb_id)"
        )
