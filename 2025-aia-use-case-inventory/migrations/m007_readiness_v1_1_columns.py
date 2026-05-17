"""Swap agency_readiness columns from v1.0 (compliance-leaning) to v1.1 (capacity-first).

v1.0 dimensions:
  adoption_breadth, frontier_capability, procurement_hygiene,
  reporting_quality, governance_documentation

v1.1 dimensions:
  internal_capacity, frontier_capability, procurement_hygiene,
  risk_relevant_governance, adoption_breadth

The rubric was rejected pre-launch (the IFP audience challenged the
compliance bias of "did you fill out the form?" as a state-capacity
signal). v1.1 replaces it with direct capability measures.

Pre-launch — no data needs preserving. This migration just drops the
old table if its columns are the v1.0 set and lets m006's apply()
re-create it with the v1.1 schema on the next make fix.

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "007_readiness_v1_1_columns"


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        is not None
    )


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(
        r[1] == column for r in conn.execute(f"PRAGMA table_info({table})")
    )


def apply(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "agency_readiness"):
        return
    if _column_exists(conn, "agency_readiness", "internal_capacity"):
        return  # already v1.1
    conn.execute("DROP TABLE agency_readiness")
    # Recreate with v1.1 schema. (m006.apply also handles this if called
    # again, but we inline the DDL here so the migration is self-contained.)
    conn.execute(
        """
        CREATE TABLE agency_readiness (
            agency_id INTEGER PRIMARY KEY REFERENCES agencies(id),
            internal_capacity REAL,
            frontier_capability REAL,
            procurement_hygiene REAL,
            risk_relevant_governance REAL,
            adoption_breadth REAL,
            composite_score REAL,
            tier TEXT,
            tier_label TEXT,
            rank INTEGER,
            headline_inputs_json TEXT,
            computed_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_agency_readiness_rank "
        "ON agency_readiness(rank)"
    )
