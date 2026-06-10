"""Add `stage_normalized` and `ai_classification_normalized` to use_cases.

`stage_of_development` arrives from agencies as ~40 free-text variants of
the four M-25-21 stages; `ai_classification` as 31 variants of the seven
canonical categories (with/without definition suffixes, plus free text).
Every "deployed vs pilot" or "GenAI by OMB's own label" claim depends on
collapsing these correctly, and until now each consumer (dashboard SQL
fragments, fedramp coverage, fact-sheet scripts) re-implemented its own
LIKE chains.

This migration adds the two canonical columns; the values are recomputed
on every rebuild by `scripts/normalize_use_case_fields.py` (the loader
wipes and re-inserts rows, so a once-only backfill would go stale).

Vocabulary:
  stage_normalized: pre_deployment | pilot | deployed | retired | unknown
  ai_classification_normalized: Generative AI | Classical/Predictive
    Machine Learning | Computer Vision | Natural Language Processing |
    Agentic AI | Reinforcement Learning | Other | Unspecified

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "016_normalized_columns"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(
        r[1] == column for r in conn.execute(f"PRAGMA table_info({table})")
    )


def apply(conn: sqlite3.Connection) -> None:
    if not _column_exists(conn, "use_cases", "stage_normalized"):
        conn.execute("ALTER TABLE use_cases ADD COLUMN stage_normalized TEXT")
    if not _column_exists(conn, "use_cases", "ai_classification_normalized"):
        conn.execute(
            "ALTER TABLE use_cases ADD COLUMN ai_classification_normalized TEXT"
        )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_use_cases_stage_norm "
        "ON use_cases(stage_normalized)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_use_cases_ai_class_norm "
        "ON use_cases(ai_classification_normalized)"
    )
