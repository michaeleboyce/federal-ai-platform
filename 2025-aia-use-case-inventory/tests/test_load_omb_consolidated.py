"""Loader tests using the fixture XLSX + an in-memory DB."""
import json
import sqlite3
from pathlib import Path

from migrations import m004_omb_consolidated_provenance as m004
from migrations import m005_consolidation_pattern as m005
import load_omb_consolidated as loader

FIXTURE = Path(__file__).parent / "fixtures" / "omb_consolidated_sample.xlsx"


def _seed_db():
    """In-memory DB with the subset of schema the loader queries."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute(
        "CREATE TABLE agencies ("
        "id INTEGER PRIMARY KEY, abbreviation TEXT UNIQUE, full_name TEXT)"
    )
    conn.execute(
        """
        CREATE TABLE use_cases (
            id INTEGER PRIMARY KEY,
            agency_id INTEGER,
            use_case_id TEXT,
            use_case_name TEXT NOT NULL,
            stage_of_development TEXT,
            is_high_impact TEXT,
            is_withheld TEXT,
            topic_area TEXT,
            ai_classification TEXT,
            contracting_usage TEXT,
            development_type TEXT,
            vendor_name TEXT,
            has_ato TEXT,
            has_pii TEXT,
            has_custom_code TEXT,
            bureau_component TEXT
        )
        """
    )
    m004.apply(conn)
    m005.apply(conn)

    # Seed agencies the fixture references.
    for abbr, name in [
        ("DOJ", "Department of Justice"),
        ("NSF", "National Science Foundation"),
        ("DHS", "Department of Homeland Security"),
        ("DOE", "Department of Energy"),
        ("ED", "Department of Education"),
        ("State", "Department of State"),
        ("PBGC", "Pension Benefit Guaranty Corp"),
        ("FRTIB", "FRTIB"),
    ]:
        conn.execute(
            "INSERT INTO agencies(abbreviation, full_name) VALUES (?, ?)",
            (abbr, name),
        )

    # Seed DB use_cases. Bureau "Test Bureau" matches the fixture's default
    # bureau so the (agency, bureau, name) match key collides as expected.
    seeds = [
        ("DOJ", "DOJ-0001", "Test Veritone System", "Test Bureau"),
        # Slight rename — should fuzzy-match Test Veritone Audio Sys (~0.90).
        ("DOJ", "DOJ-LEGACY", "Test Veritone Audio System", "Test Bureau"),
        # NSF acronym base form — should land in suggested_rename for the
        # acronym-expanded OMB row.
        ("NSF", "AII-49", "TIP MS Copilot Pilot", "Test Bureau"),
        # Drift target — DB stage is Pilot/NotHighImpact; OMB row has
        # Deployed/HighImpact, so detect_drift returns 2 fields.
        ("DOE", "DOE-555", "Drift Test Case", "Test Bureau"),
        ("ED", "ED-0001", "Aidan Chat-bot", "Test Bureau"),
        ("State", "DOS - 1473", "AI Input in Translation", "Test Bureau"),
        # FRTIB row not in OMB file at all → db_only.
        ("FRTIB", "FRTIB-001", "Sumtotal Chatbot", "Test Bureau"),
    ]
    for abbr, uid, name, bureau in seeds:
        agency_id = conn.execute(
            "SELECT id FROM agencies WHERE abbreviation=?", (abbr,)
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO use_cases(agency_id, use_case_id, use_case_name, "
            "stage_of_development, is_high_impact, bureau_component) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (agency_id, uid, name, "b) Pilot", "c) Not high-impact", bureau),
        )
    conn.commit()
    return conn


def test_loader_inserts_all_omb_rows():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    n = conn.execute("SELECT COUNT(*) FROM omb_consolidated_rows").fetchone()[0]
    assert n == 10  # 10 data rows in the fixture


def test_loader_marks_exact_match():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    row = conn.execute("""
        SELECT a.match_status, a.match_score
        FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id = a.omb_row_id
        WHERE o.use_case_name = 'Test Veritone System'
    """).fetchone()
    assert row["match_status"] == "matched_exact"
    assert row["match_score"] == 1.0


def test_loader_marks_fuzzy_or_rename_for_nsf_acronym():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    row = conn.execute("""
        SELECT a.match_status FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id = a.omb_row_id
        WHERE o.agency_abbreviation = 'NSF'
    """).fetchone()
    assert row["match_status"] in ("matched_fuzzy", "suggested_rename")


def test_loader_records_drift_for_doe_case():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    drift_json = conn.execute("""
        SELECT a.drift_fields_json FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id = a.omb_row_id
        WHERE o.use_case_name = 'Drift Test Case'
    """).fetchone()["drift_fields_json"]
    drift = json.loads(drift_json)
    assert "stage_of_development" in drift
    assert "is_high_impact" in drift


def test_loader_marks_db_only_for_frtib():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    rows = conn.execute(
        "SELECT match_status FROM omb_match_audit "
        "WHERE agency_abbreviation='FRTIB'"
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["match_status"] == "db_only"


def test_loader_marks_omb_only_at_dhs_for_unknown_name():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    row = conn.execute("""
        SELECT a.match_status FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id = a.omb_row_id
        WHERE o.use_case_name = 'Brand New DHS Use Case'
    """).fetchone()
    assert row["match_status"] == "omb_only"


def test_loader_detects_pbgc_duplicate():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    rows = conn.execute("""
        SELECT match_status FROM omb_match_audit
        WHERE use_case_name = 'Legislative and Regulatory Analysis'
    """).fetchall()
    statuses = [r["match_status"] for r in rows]
    assert "duplicate_in_omb" in statuses


def test_loader_populates_use_case_omb_consolidated_id_for_matches():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    omb_id = conn.execute(
        "SELECT omb_consolidated_id FROM use_cases "
        "WHERE use_case_name='Test Veritone System'"
    ).fetchone()["omb_consolidated_id"]
    assert omb_id == "DOJ-0001"


def test_loader_handles_state_to_state_normalization():
    """OMB 'STATE' agency must match DB 'State' agency rows."""
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    row = conn.execute("""
        SELECT a.match_status FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id = a.omb_row_id
        WHERE o.use_case_name = 'AI Input in Translation'
    """).fetchone()
    assert row["match_status"] == "matched_exact"


def test_loader_is_idempotent_on_rerun():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    n1 = conn.execute("SELECT COUNT(*) FROM omb_consolidated_rows").fetchone()[0]
    n_audit_1 = conn.execute("SELECT COUNT(*) FROM omb_match_audit").fetchone()[0]
    loader.load(conn, FIXTURE)
    n2 = conn.execute("SELECT COUNT(*) FROM omb_consolidated_rows").fetchone()[0]
    n_audit_2 = conn.execute("SELECT COUNT(*) FROM omb_match_audit").fetchone()[0]
    assert n1 == n2
    assert n_audit_1 == n_audit_2
