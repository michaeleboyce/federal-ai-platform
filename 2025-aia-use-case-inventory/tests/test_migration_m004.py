"""Migration m004 adds OMB-consolidated provenance columns + tables."""
import sqlite3

from migrations import m004_omb_consolidated_provenance as m


def _bootstrap_use_cases(conn: sqlite3.Connection) -> None:
    """Minimal use_cases table — m004 only adds columns; it doesn't read them."""
    conn.execute("CREATE TABLE use_cases (id INTEGER PRIMARY KEY, use_case_id TEXT)")


def test_migration_id_is_set():
    assert m.MIGRATION_ID == "004_omb_consolidated_provenance"


def test_adds_four_omb_columns_to_use_cases():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(use_cases)")}
    assert "omb_consolidated_id" in cols
    assert "omb_consolidated_source" in cols
    assert "omb_consolidated_first_seen" in cols
    assert "omb_consolidated_last_seen" in cols


def test_creates_omb_consolidated_rows_table_with_36_omb_columns():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(omb_consolidated_rows)")}
    for c in ["id", "ingest_source_file", "ingest_run_at", "row_hash",
              "row_index_in_file", "raw_json"]:
        assert c in cols, f"missing metadata column {c}"
    for c in ["agency_abbreviation", "agency_name", "use_case_id_omb",
              "use_case_name", "bureau_component", "is_withheld",
              "stage_of_development", "is_high_impact", "ai_classification",
              "vendor_name", "have_ato", "has_pii", "has_custom_code",
              "hi_testing_conducted", "hi_public_consultation"]:
        assert c in cols, f"missing OMB column {c}"


def test_omb_consolidated_rows_has_unique_index_on_file_plus_idx():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    indexes = {
        r[1]: r[2]
        for r in conn.execute("PRAGMA index_list(omb_consolidated_rows)")
    }
    assert "uq_omb_rows_file_idx" in indexes
    assert indexes["uq_omb_rows_file_idx"] == 1, "must be UNIQUE"


def test_creates_omb_match_audit_table():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(omb_match_audit)")}
    expected = {
        "id", "ingest_run_at", "omb_row_id", "use_case_id_db",
        "agency_abbreviation", "use_case_name", "match_method", "match_score",
        "match_status", "drift_fields_json", "first_seen", "last_seen",
        "resolved_at", "resolution_note",
    }
    assert expected <= cols, f"missing audit columns: {expected - cols}"


def test_match_status_index_exists():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    indexes = {r[1] for r in conn.execute("PRAGMA index_list(omb_match_audit)")}
    assert any("status" in name for name in indexes)


def test_is_idempotent_when_applied_twice():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    m.apply(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(use_cases)")}
    assert "omb_consolidated_id" in cols


def test_ledger_runner_picks_up_m004():
    """End-to-end: scripts/run_migrations auto-discovers m004 and applies it
    exactly once. Re-running is a no-op (m004 absent from second-call result).
    """
    from scripts import run_migrations as runner

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    _bootstrap_use_cases(conn)
    conn.execute(
        "CREATE TABLE schema_migrations ("
        "migration_id TEXT PRIMARY KEY, applied_at TEXT NOT NULL "
        "DEFAULT (datetime('now')))"
    )
    for prior in ("001_additive_inventory_schema", "002_rename_to_omb_canonical",
                  "003_consolidated_source_format"):
        conn.execute(
            "INSERT INTO schema_migrations(migration_id, applied_at) VALUES (?, ?)",
            (prior, "2026-05-03"),
        )

    applied = runner.apply_migrations(conn)
    assert "004_omb_consolidated_provenance" in applied
    applied2 = runner.apply_migrations(conn)
    assert "004_omb_consolidated_provenance" not in applied2
