"""Add `year_comparison` — the precomputed 2024↔2025 YoY aggregate rollup.

Phase 2 of the 2024 ↔ 2025 AI use case inventory comparison project (see
`docs/plans/2024-vs-2025-comparison/PLAN.md`). This is the "Option A"
hand-off table: a tidy/long rollup of the year-over-year aggregates that are
*honestly* comparable, one row per dimension×bucket cell, each carrying a
`clean` / `lossy` comparability flag.

Dimensions populated by `compute_year_comparison.py`:
  - `total`      — overall count of `use_cases_2024` vs `use_cases` (clean).
  - `agency`     — per-agency counts, full-outer joined on `agency_id` (clean).
  - `stage`      — development-stage mix; 2024 SDLC enum recoded to the 2025
                   posture enum, so the comparison is `lossy`.
  - `dev_method` — in-house vs contracted mix; both years are sparse, so the
                   comparison is `lossy` (missingness recorded in `notes`).

`impact` and `ai_classification` are deliberately NOT dimensions here — the
2024/2025 impact taxonomies are not 1:1 and 2024 has no AI-type column (see
the Phase 0 COMPARABILITY-MATRIX).

The tidy/long shape keeps the table flexible for whatever the Phase 5
dashboard charts. No UI surface consumes it until then.

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "010_year_comparison"


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
    if not _table_exists(conn, "year_comparison"):
        conn.execute(
            """
            CREATE TABLE year_comparison (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                dimension     TEXT NOT NULL,
                bucket        TEXT,
                agency_id     INTEGER REFERENCES agencies(id),
                count_2024    INTEGER NOT NULL DEFAULT 0,
                count_2025    INTEGER NOT NULL DEFAULT 0,
                delta         INTEGER NOT NULL DEFAULT 0,
                pct_change    REAL,
                comparability TEXT NOT NULL,
                notes         TEXT,
                computed_at   TEXT DEFAULT (datetime('now'))
            )
            """
        )
    if not _index_exists(conn, "idx_year_comparison_dimension"):
        conn.execute(
            "CREATE INDEX idx_year_comparison_dimension "
            "ON year_comparison(dimension)"
        )
