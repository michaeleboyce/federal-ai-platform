"""Add OMB-consolidated-file provenance to use_cases + new tables.

The 2025 OMB consolidated `2025_individually_reported_AI_use_cases.xlsx`
introduces a parallel ID space (OMB-side) and a normalized snapshot of
each agency's filings, distinct from the per-agency raw files we ingest
via `load_inventories.py`. This migration adds the substrate:

  1. Four columns on `use_cases` for the OMB-side ID + ingest provenance.
     `use_case_id` (existing) stays IFP-canonical (agency-as-filed).
     `omb_consolidated_id` carries OMB's renumbering, which is sometimes
     blank (ED, GSA, HHS, SSA, STATE, TVA), sometimes a bare integer
     (EPA, NSF, TREAS), and sometimes the canonical AGENCY-N form.

  2. `omb_consolidated_rows` — a row-for-row mirror of the OMB file
     keeping all 36 OMB columns verbatim plus ingest metadata. Lets us
     re-audit drift in future rounds without re-parsing the XLSX.

  3. `omb_match_audit` — one row per match attempt (status enum, drift
     JSON, first_seen/last_seen, human-resolution fields). This drives
     the `/discrepancies` dashboard page.

Idempotent. Each DDL is guarded by an existence check so a crash mid-run
followed by re-application doesn't error out.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "004_omb_consolidated_provenance"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(
        r[1] == column for r in conn.execute(f"PRAGMA table_info({table})")
    )


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


USE_CASES_NEW_COLUMNS = [
    ("omb_consolidated_id", "TEXT"),
    ("omb_consolidated_source", "TEXT"),
    ("omb_consolidated_first_seen", "TEXT"),
    ("omb_consolidated_last_seen", "TEXT"),
]


def apply(conn: sqlite3.Connection) -> None:
    for col, ddl in USE_CASES_NEW_COLUMNS:
        if not _column_exists(conn, "use_cases", col):
            conn.execute(f"ALTER TABLE use_cases ADD COLUMN {col} {ddl}")

    if not _table_exists(conn, "omb_consolidated_rows"):
        conn.execute(
            """
            CREATE TABLE omb_consolidated_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingest_source_file TEXT NOT NULL,
                ingest_run_at TEXT NOT NULL,
                row_hash TEXT NOT NULL,
                row_index_in_file INTEGER NOT NULL,
                agency_abbreviation TEXT,
                agency_name TEXT,
                use_case_id_omb TEXT,
                use_case_name TEXT,
                bureau_component TEXT,
                email_address TEXT,
                is_withheld TEXT,
                stage_of_development TEXT,
                is_high_impact TEXT,
                hi_justification TEXT,
                topic_area TEXT,
                ai_classification TEXT,
                problem_statement TEXT,
                expected_benefits TEXT,
                system_outputs TEXT,
                operational_date TEXT,
                contracting_usage TEXT,
                vendor_name TEXT,
                have_ato TEXT,
                system_name_ato TEXT,
                training_data_description TEXT,
                link_to_data TEXT,
                has_pii TEXT,
                pia_url TEXT,
                demographic_features TEXT,
                has_custom_code TEXT,
                code_url TEXT,
                hi_testing_conducted TEXT,
                hi_assessment_completed TEXT,
                hi_potential_impacts TEXT,
                hi_independent_review TEXT,
                hi_ongoing_monitoring TEXT,
                hi_training_established TEXT,
                hi_failsafe_presence TEXT,
                hi_appeal_process TEXT,
                hi_public_consultation TEXT,
                raw_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE UNIQUE INDEX uq_omb_rows_file_idx "
            "ON omb_consolidated_rows(ingest_source_file, row_index_in_file)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_rows_agency "
            "ON omb_consolidated_rows(agency_abbreviation)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_rows_name "
            "ON omb_consolidated_rows(use_case_name)"
        )

    if not _table_exists(conn, "omb_match_audit"):
        conn.execute(
            """
            CREATE TABLE omb_match_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingest_run_at TEXT NOT NULL,
                omb_row_id INTEGER REFERENCES omb_consolidated_rows(id),
                use_case_id_db INTEGER REFERENCES use_cases(id),
                agency_abbreviation TEXT,
                use_case_name TEXT,
                match_method TEXT,
                match_score REAL,
                match_status TEXT NOT NULL,
                drift_fields_json TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                resolved_at TEXT,
                resolution_note TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX idx_omb_audit_status ON omb_match_audit(match_status)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_audit_agency "
            "ON omb_match_audit(agency_abbreviation)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_audit_db ON omb_match_audit(use_case_id_db)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_audit_omb ON omb_match_audit(omb_row_id)"
        )
