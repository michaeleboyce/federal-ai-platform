"""Add `agency_readiness` table for the published Federal AI Readiness scorecard.

The IFP-facing readiness scorecard layers a documented 5-dimension rubric on
top of the existing inventory + maturity data. This migration only creates
the substrate; population happens in `scripts/compute_agency_readiness.py`.

Existing tables (`agency_ai_maturity`, `use_cases`, `use_case_tags`,
`fedramp_product_links`, etc.) are untouched — the readiness scorecard reads
from them and writes a single normalized row per agency.

Idempotent. Safe to re-run.

NOTE: Rubric constants live in `scripts/compute_agency_readiness.py` and
MUST stay in sync with `dashboard/lib/readiness-rubric.ts`.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "006_agency_readiness"


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _index_exists(conn: sqlite3.Connection, name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
            (name,),
        ).fetchone()
        is not None
    )


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(
        r[1] == column for r in conn.execute(f"PRAGMA table_info({table})")
    )


def apply(conn: sqlite3.Connection) -> None:
    # If the table exists from the v1.0 rubric (compliance-leaning columns),
    # drop and recreate. Pre-launch — no production data to migrate. This
    # keeps the schema clean of dead columns.
    if _table_exists(conn, "agency_readiness") and not _column_exists(
        conn, "agency_readiness", "internal_capacity"
    ):
        conn.execute("DROP TABLE agency_readiness")

    if not _table_exists(conn, "agency_readiness"):
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
    if not _index_exists(conn, "idx_agency_readiness_rank"):
        conn.execute(
            "CREATE INDEX idx_agency_readiness_rank ON agency_readiness(rank)"
        )
