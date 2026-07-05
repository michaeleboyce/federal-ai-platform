"""Band-row population labels, occupational caps, and workforce v2 columns.

Backs the stratified-overlap seat model on the dashboard's /experience page.

The license bands on `consolidated_use_cases.estimated_licenses_users` are
row-level (task-level) facts: the same user population repeats across task
rows, and banded rows link to multiple products. Summing bands therefore
never yields a defensible seat total (several agencies' sums are 10-25x
their headcount). The model instead needs, per banded row, WHO the band
counts — labeled by the band_labels_2026-07 pass and stored here.

1. `consolidated_band_labels` — one row per banded consolidated use case.
   A separate table (not columns on `consolidated_use_cases`) because
   `load_omb_consolidated.py` wipes that table every rebuild; labels are
   re-applied from `audit/retag/band_labels_2026-07/` CSVs by
   `scripts/apply_band_labels.py`, resolving by the deterministic `slug`.

2. `agency_occupation_counts` — FedScope occupational-series headcounts
   (2210 IT, 0905 attorneys, ...) used as caps for role strata in the
   seat model. Seeded by `scripts/apply_agency_workforce.py` from the
   `occupations` payload in `audit/research/agency_workforce/*.json`.

3. `agency_workforce_profile` gains `contractor_headcount` and
   `denominator_basis` so agencies whose filed bands clearly include
   on-site contractors (DOE's ~100k lab contractors) can carry an
   honest, sourced denominator.

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "017_band_labels_and_workforce_v2"


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


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def apply(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "consolidated_band_labels"):
        conn.execute(
            """
            CREATE TABLE consolidated_band_labels (
                consolidated_use_case_id INTEGER PRIMARY KEY
                    REFERENCES consolidated_use_cases(id)
                    ON DELETE CASCADE ON UPDATE CASCADE,
                slug          TEXT NOT NULL UNIQUE,
                unit_counted  TEXT NOT NULL CHECK(unit_counted IN
                    ('employees','employees_and_contractors',
                     'devices_endpoints','public_users',
                     'applicants_cases','unknown')),
                population    TEXT NOT NULL,
                org_scope     TEXT NOT NULL CHECK(org_scope IN
                    ('enterprise','component','unknown')),
                stratum       TEXT NOT NULL CHECK(stratum IN
                    ('general','technical','legal','investigative',
                     'comms','clinical','excluded_not_seats')),
                confidence    TEXT NOT NULL CHECK(confidence IN
                    ('high','medium','low')),
                reasoning     TEXT,
                labeler       TEXT NOT NULL,
                audited       INTEGER NOT NULL DEFAULT 0,
                audit_verdict TEXT CHECK(audit_verdict IN
                    ('agree','override','escalated')
                    OR audit_verdict IS NULL),
                audit_reasoning TEXT,
                captured_at   TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
    if not _index_exists(conn, "idx_cbl_stratum"):
        conn.execute(
            "CREATE INDEX idx_cbl_stratum "
            "ON consolidated_band_labels(stratum)"
        )
    if not _index_exists(conn, "idx_cbl_unit"):
        conn.execute(
            "CREATE INDEX idx_cbl_unit "
            "ON consolidated_band_labels(unit_counted)"
        )

    if not _table_exists(conn, "agency_occupation_counts"):
        conn.execute(
            """
            CREATE TABLE agency_occupation_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agency_id         INTEGER REFERENCES agencies(id),
                organization_slug TEXT NOT NULL,
                occ_series        TEXT NOT NULL,
                occ_label         TEXT NOT NULL,
                stratum           TEXT NOT NULL CHECK(stratum IN
                    ('general','technical','legal','investigative',
                     'comms','clinical')),
                headcount         INTEGER NOT NULL,
                as_of             TEXT NOT NULL,
                source_url        TEXT NOT NULL,
                source_title      TEXT,
                notes             TEXT,
                captured_at       TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(organization_slug, occ_series, as_of)
            )
            """
        )
    if not _index_exists(conn, "idx_aoc_agency"):
        conn.execute(
            "CREATE INDEX idx_aoc_agency "
            "ON agency_occupation_counts(agency_id)"
        )

    if not _column_exists(
        conn, "agency_workforce_profile", "contractor_headcount"
    ):
        conn.execute(
            "ALTER TABLE agency_workforce_profile "
            "ADD COLUMN contractor_headcount INTEGER"
        )
    if not _column_exists(
        conn, "agency_workforce_profile", "denominator_basis"
    ):
        conn.execute(
            "ALTER TABLE agency_workforce_profile "
            "ADD COLUMN denominator_basis TEXT"
        )
