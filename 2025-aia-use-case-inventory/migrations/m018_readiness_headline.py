"""Add the 1-row `readiness_headline` table + a use_case_tags uniqueness guard.

Part of readiness rubric v1.2. Previously the dashboard re-derived the
headline stats (internal-build %, production rate, FedRAMP coverage) in
TypeScript from raw tables, while scripts/compute_agency_readiness.py
derived them in Python — the two implementations drifted (the TS side
counted OMB Pilot rows as "deployed" via a substring match). The scorer now
persists its stats here and the dashboard only reads.

Also enforces one tags row per individual use case: the audit found a
single duplicate use_case_tags row; it is removed (keeping the lowest id)
and a partial unique index prevents recurrence. Consolidated-side tag rows
(use_case_id IS NULL) are untouched.

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "018_readiness_headline"

# Keep in sync with scripts/compute_agency_readiness.py:_HEADLINE_DDL
# (duplicated there so the script is self-sufficient on older snapshots).
HEADLINE_DDL = """
CREATE TABLE IF NOT EXISTS readiness_headline (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    rubric_version TEXT NOT NULL,
    internal_build_pct REAL NOT NULL,
    purchased_pct REAL NOT NULL,
    unreported_pct REAL NOT NULL,
    production_rate_pct REAL NOT NULL,
    production_rate_all_pct REAL NOT NULL,
    fedramp_linked_pct REAL NOT NULL,
    fedramp_floor_pct REAL NOT NULL,
    frontier_ready_agency_count INTEGER NOT NULL,
    total_agencies_scored INTEGER NOT NULL,
    total_units INTEGER NOT NULL,
    total_use_cases INTEGER NOT NULL,
    hi_no_risk_docs_pct REAL NOT NULL,
    hi_no_risk_docs_high_impact_pct REAL NOT NULL,
    fedramp_link_row_count INTEGER NOT NULL DEFAULT 0,
    computed_at TEXT NOT NULL
)
"""


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def apply(conn: sqlite3.Connection) -> None:
    conn.execute(HEADLINE_DDL)

    # De-dupe use_case_tags on use_case_id (keep lowest rowid), then guard.
    # Skipped on snapshots that predate the tags table (ledger-runner tests
    # apply every migration to a minimal DB).
    if not _table_exists(conn, "use_case_tags"):
        return
    conn.execute(
        """
        DELETE FROM use_case_tags
         WHERE use_case_id IS NOT NULL
           AND id NOT IN (
             SELECT MIN(id) FROM use_case_tags
              WHERE use_case_id IS NOT NULL
              GROUP BY use_case_id
           )
        """
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_use_case_tags_uc_unique "
        "ON use_case_tags(use_case_id) WHERE use_case_id IS NOT NULL"
    )
