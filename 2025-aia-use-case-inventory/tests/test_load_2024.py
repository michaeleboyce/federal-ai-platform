"""Tests for load_2024.py — the 2024 inventory corpus loader.

Uses an in-memory DB, applies the m009 migration, seeds the agencies the
2024 CSV needs, and runs the loader against the real
`data/raw/2024_consolidated_ai_inventory_raw_v2.csv` (2,133 rows — fast).
"""
import json
import sqlite3

from migrations import m009_use_cases_2024 as m009
from column_maps_2024 import COLUMN_CROSSWALK_2024
import load_2024 as loader

# Every 2024 agency abbreviation (raw, as it appears in the CSV) -> full name.
# TREAS / STATE are the raw forms; normalize_agency maps them at load time.
AGENCIES_2024 = [
    "CFPB", "CFTC", "DHS", "DOC", "DOE", "DOI", "DOJ", "DOL", "DOT", "EAC",
    "ED", "EEOC", "EPA", "FDIC", "FERC", "FHFA", "FRB", "FTC", "GSA", "HHS",
    "HUD", "NARA", "NASA", "NCUA", "NSF", "NTSB", "OPM", "PBGC", "PRC", "PT",
    "SEC", "SSA", "Treasury", "TVA", "USAGM", "USAID", "USCCR", "USDA",
    "USTDA", "VA",
    # State is normalize_agency(STATE); seed under the normalized form.
    "State",
]


def _seed_db():
    """In-memory DB with the agencies table + the m009 use_cases_2024 table."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "CREATE TABLE agencies ("
        "id INTEGER PRIMARY KEY, abbreviation TEXT UNIQUE, full_name TEXT)"
    )
    for abbr in AGENCIES_2024:
        conn.execute(
            "INSERT INTO agencies(abbreviation, full_name) VALUES (?, ?)",
            (abbr, abbr),
        )
    m009.apply(conn)
    conn.commit()
    return conn


def test_loader_inserts_all_2024_rows():
    conn = _seed_db()
    loader.load(conn)
    n = conn.execute("SELECT COUNT(*) FROM use_cases_2024").fetchone()[0]
    assert n == 2133


def test_loader_reports_2133_loaded_zero_skipped():
    conn = _seed_db()
    stats = loader.load(conn)
    assert stats["inserted"] == 2133
    assert stats["skipped"] == 0
    assert stats["skipped_unknown_agencies"] == {}


def test_all_41_agencies_resolve():
    conn = _seed_db()
    loader.load(conn)
    n = conn.execute(
        "SELECT COUNT(DISTINCT agency_id) FROM use_cases_2024"
    ).fetchone()[0]
    assert n == 41


def test_cp1252_character_round_trips():
    """A curly apostrophe in a 2024 narrative survives cp1252 decoding."""
    conn = _seed_db()
    loader.load(conn)
    # The 2024 CSV uses U+2019 (right single quote) in narrative text.
    n = conn.execute(
        "SELECT COUNT(*) FROM use_cases_2024 WHERE raw_json LIKE ?",
        ("%’%",),
    ).fetchone()[0]
    assert n > 0
    # And no cp1252 mojibake artifact leaked through.
    bad = conn.execute(
        "SELECT COUNT(*) FROM use_cases_2024 WHERE raw_json LIKE ?",
        ("%â%",),
    ).fetchone()[0]
    assert bad == 0


def test_raw_json_has_all_62_field_keys():
    conn = _seed_db()
    loader.load(conn)
    expected_fields = {e["field"] for e in COLUMN_CROSSWALK_2024}
    assert len(expected_fields) == 62
    raw = conn.execute(
        "SELECT raw_json FROM use_cases_2024 ORDER BY id LIMIT 1"
    ).fetchone()["raw_json"]
    parsed = json.loads(raw)
    assert set(parsed.keys()) == expected_fields


def test_slug_uniqueness_holds_across_all_rows():
    conn = _seed_db()
    loader.load(conn)
    total, distinct = conn.execute(
        "SELECT COUNT(slug), COUNT(DISTINCT slug) FROM use_cases_2024"
    ).fetchone()
    assert total == 2133
    assert distinct == 2133


def test_native_columns_match_crosswalk_fields():
    """The use_cases_2024 table carries exactly the 62 crosswalk fields."""
    conn = _seed_db()
    cols = {
        r["name"]
        for r in conn.execute("PRAGMA table_info(use_cases_2024)")
    }
    for entry in COLUMN_CROSSWALK_2024:
        assert entry["field"] in cols


def test_values_stored_verbatim_no_recoding():
    """Stage-of-development values keep their native 2024 vocabulary."""
    conn = _seed_db()
    loader.load(conn)
    stages = {
        r["dev_stage"]
        for r in conn.execute(
            "SELECT DISTINCT dev_stage FROM use_cases_2024 "
            "WHERE dev_stage IS NOT NULL AND dev_stage != ''"
        )
    }
    # Native 2024 SDLC vocabulary present; 2025 recoded values absent.
    assert any("Operation" in s or "Implementation" in s for s in stages)
    assert not any(s.startswith("c) Deployed") for s in stages)


def test_loader_is_idempotent_on_rerun():
    conn = _seed_db()
    loader.load(conn)
    n1 = conn.execute("SELECT COUNT(*) FROM use_cases_2024").fetchone()[0]
    loader.load(conn)
    n2 = conn.execute("SELECT COUNT(*) FROM use_cases_2024").fetchone()[0]
    assert n1 == n2 == 2133
