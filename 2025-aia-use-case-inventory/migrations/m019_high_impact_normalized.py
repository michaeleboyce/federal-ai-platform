"""Add `high_impact_normalized` to use_cases.

`is_high_impact` arrives from agencies as ~11 free-text variants of what
M-25-21 defines as a three-choice field (High-impact / Presumed high-impact
but determined not high-impact / Not high-impact): list prefixes ("a)",
"c)"), bare labels, plus non-canonical strays ("Neither", "No",
"Low-impact", "Medium-impact"). This is the same drift m016 fixed for
stage_of_development and ai_classification; until now high-impact had no
normalized column at all.

Vocabulary:
  high_impact_normalized:
    high_impact | presumed_not_high_impact | not_high_impact | unknown

Editorial note: "Neither", "No", "Low-impact", and "Medium-impact" are not
canonical M-25-21 choices. We fold them into `not_high_impact` — the filer
affirmatively said the case is not high-impact, just not in OMB's words.
The raw `is_high_impact` column is retained and rendered "as filed" in the
dashboard, so no information is destroyed by this mapping.

Values are recomputed on every rebuild by
`scripts/normalize_use_case_fields.py` (the loader wipes and re-inserts
rows, so a once-only backfill would go stale).

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "019_high_impact_normalized"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(
        r[1] == column for r in conn.execute(f"PRAGMA table_info({table})")
    )


def apply(conn: sqlite3.Connection) -> None:
    if not _column_exists(conn, "use_cases", "high_impact_normalized"):
        conn.execute(
            "ALTER TABLE use_cases ADD COLUMN high_impact_normalized TEXT"
        )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_use_cases_high_impact_norm "
        "ON use_cases(high_impact_normalized)"
    )
