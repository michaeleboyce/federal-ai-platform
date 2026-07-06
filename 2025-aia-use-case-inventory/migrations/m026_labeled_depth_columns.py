"""Add `integration_depth` and `coding_tool_type` to use_case_tags.

Two adjudicated labeling rounds (2026-07) measure what the OMB M-25-21
inventory format does not collect:

  integration_depth — how deeply a pilot/deployed use case is wired into
    agency work, labeled over the ~1,573 stage_normalized IN
    ('pilot','deployed') individual rows. NULL = outside the labeled
    population (pre-deployment/retired/unknown rows), which is distinct
    from 'unclear' (labeled but the narrative doesn't say).
    Vocabulary: standalone_chat | workflow_embedded | system_integrated |
    agentic_workflow | unclear

  coding_tool_type — taxonomy of the is_coding_tool=1 individual filings
    (which of them are actually coding AGENTS vs chat/autocomplete).
    NULL = not a coding-tagged row.
    Vocabulary: chat_assistant | ide_autocomplete | coding_agent |
    code_analysis_tool | not_coding | unclear

Values are re-applied after every rebuild by
scripts/apply_integration_depth.py and scripts/apply_coding_taxonomy.py
(signature-keyed; wired into the `make fix` chain after auto_tag.py),
from the adjudicated rounds under audit/retag/integration_depth_2026-07/
and audit/retag/coding_taxonomy_2026-07/.

Distinct from `architecture_type` (technical build: rag_pipeline,
fine_tuned, ...), which stays untouched and keeps its corpus-level
"mostly unknown" guardrail.

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "026_labeled_depth_columns"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(
        r[1] == column for r in conn.execute(f"PRAGMA table_info({table})")
    )


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        is not None
    )


def apply(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "use_case_tags"):
        return  # minimal test fixture without the tags table
    if not _column_exists(conn, "use_case_tags", "integration_depth"):
        conn.execute("ALTER TABLE use_case_tags ADD COLUMN integration_depth TEXT")
    if not _column_exists(conn, "use_case_tags", "coding_tool_type"):
        conn.execute("ALTER TABLE use_case_tags ADD COLUMN coding_tool_type TEXT")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_tags_integration_depth "
        "ON use_case_tags(integration_depth)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_tags_coding_tool_type "
        "ON use_case_tags(coding_tool_type)"
    )
