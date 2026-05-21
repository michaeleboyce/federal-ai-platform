"""Add `use_case_year_links` — the 2024↔2025 use-case lineage table.

Phase 3 of the 2024 ↔ 2025 AI use case inventory comparison project (see
`docs/plans/2024-vs-2025-comparison/PLAN.md`). This is "Option B" — the
use-case-level lineage layer.

The 2024 corpus (`use_cases_2024`) has no IDs; nothing structurally links a
2024 row to its 2025 counterpart in `use_cases`. `match_year_over_year.py`
infers every link deterministically (exact name → fuzzy name → narrative
similarity), strictly within an agency, and records one row here per link.

The table mirrors `omb_match_audit` (defined in m004) — the project's proven
"two row sets + a match/audit table" pattern (`use_cases` ↔
`consolidated_use_cases` ↔ `omb_match_audit`). Nullable on BOTH `uc_2024_id`
and `uc_2025_id` so it naturally expresses:
  - 1:1  continued / renamed / suggested_rename (both ids set)
  - 1:0  retired_2024  (uc_2025_id NULL)
  - 0:1  new_2025      (uc_2024_id NULL)
(N:M split/merge is Phase 4.)

`drift_fields_json` and `llm_reasoning` columns exist but stay NULL until
Phase 4 (LLM adjudication + drift computation).

Idempotent. Each DDL is guarded by an existence check so a crash mid-run
followed by re-application doesn't error out.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "011_use_case_year_links"


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
    if not _table_exists(conn, "use_case_year_links"):
        conn.execute(
            """
            CREATE TABLE use_case_year_links (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at              TEXT NOT NULL,
                uc_2024_id          INTEGER REFERENCES use_cases_2024(id),
                uc_2025_id          INTEGER REFERENCES use_cases(id),
                agency_id           INTEGER REFERENCES agencies(id),
                agency_abbreviation TEXT,
                match_method        TEXT,
                match_score         REAL,
                lineage_status      TEXT NOT NULL,
                drift_fields_json   TEXT,
                llm_reasoning       TEXT,
                first_seen          TEXT NOT NULL,
                last_seen           TEXT NOT NULL,
                resolved_at         TEXT,
                resolution_note     TEXT
            )
            """
        )
    if not _index_exists(conn, "idx_ucyl_2024"):
        conn.execute(
            "CREATE INDEX idx_ucyl_2024 ON use_case_year_links(uc_2024_id)"
        )
    if not _index_exists(conn, "idx_ucyl_2025"):
        conn.execute(
            "CREATE INDEX idx_ucyl_2025 ON use_case_year_links(uc_2025_id)"
        )
    if not _index_exists(conn, "idx_ucyl_agency"):
        conn.execute(
            "CREATE INDEX idx_ucyl_agency ON use_case_year_links(agency_id)"
        )
    if not _index_exists(conn, "idx_ucyl_status"):
        conn.execute(
            "CREATE INDEX idx_ucyl_status ON use_case_year_links(lineage_status)"
        )
