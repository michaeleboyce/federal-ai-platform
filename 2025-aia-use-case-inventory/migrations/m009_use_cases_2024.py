"""Add `use_cases_2024` — the raw 2024 (M-24-10) AI use case inventory corpus.

Phase 1 of the 2024 ↔ 2025 AI use case inventory comparison project (see
`docs/plans/2024-vs-2025-comparison/PLAN.md`). This table holds the 2,133 use
cases from the official OMB 2024 consolidated inventory in their **native
M-24-10 shape** — columns keep their 2024 names; they are NOT remapped to the
2025 canonical schema. That cross-year mapping is comparison-layer metadata
(`column_maps_2024.COLUMN_CROSSWALK_2024`) consumed by later phases, not a
property of this raw corpus.

The 62 data columns are generated directly from `COLUMN_CROSSWALK_2024` so the
table can never drift from the Phase 0 crosswalk. All columns are `TEXT`,
matching the existing `use_cases` convention. `raw_json` preserves every cell
losslessly (keyed by crosswalk `field` name — the 2024 CSV repeats the literal
`"If Other, please explain."` header ten times, so field names, not raw
headers, are the unique key).

Populated by `load_2024.py` from
`data/raw/2024_consolidated_ai_inventory_raw_v2.csv` (cp1252-encoded).

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

from column_maps_2024 import COLUMN_CROSSWALK_2024

MIGRATION_ID = "009_use_cases_2024"


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
    if not _table_exists(conn, "use_cases_2024"):
        # 62 native-2024 data columns, all TEXT, named by the crosswalk
        # `field` value and in CSV order. Generated from COLUMN_CROSSWALK_2024
        # so the DDL can never drift from the Phase 0 crosswalk.
        data_cols = ",\n                ".join(
            f"{e['field']} TEXT" for e in COLUMN_CROSSWALK_2024
        )
        conn.execute(
            f"""
            CREATE TABLE use_cases_2024 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agency_id INTEGER NOT NULL REFERENCES agencies(id),
                source_file TEXT NOT NULL,
                slug TEXT UNIQUE,
                {data_cols},
                raw_json TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
    if not _index_exists(conn, "idx_use_cases_2024_agency"):
        conn.execute(
            "CREATE INDEX idx_use_cases_2024_agency "
            "ON use_cases_2024(agency_id)"
        )
