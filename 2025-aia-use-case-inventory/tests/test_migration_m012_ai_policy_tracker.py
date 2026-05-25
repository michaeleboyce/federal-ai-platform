"""Tests for migrations/m012_ai_policy_tracker.py — creates the two
agency_ai_policy_* tables and their indexes. Idempotent."""
import sqlite3

from migrations import m012_ai_policy_tracker as m012


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    return c


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _indexes(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA index_list({table})").fetchall()]


def test_creates_agency_ai_policy_documents_with_expected_columns():
    conn = _conn()
    m012.apply(conn)
    cols = _columns(conn, "agency_ai_policy_documents")
    assert "id" in cols
    assert "agency_abbr" in cols
    assert "agency_name" in cols
    assert "agency_type" in cols
    assert "issuing_office" in cols
    assert "document_type" in cols
    assert "document_title" in cols
    assert "publication_year" in cols
    assert "publication_date" in cols
    assert "pages" in cols
    assert "issuing_memo" in cols
    assert "superseded" in cols
    assert "is_public" in cols
    assert "url" in cols
    assert "local_path" in cols
    assert "access_status" in cols
    assert "date_accessed" in cols
    assert "notes" in cols


def test_creates_agency_ai_policy_compliance_with_expected_columns():
    conn = _conn()
    m012.apply(conn)
    cols = _columns(conn, "agency_ai_policy_compliance")
    assert "agency_abbr" in cols
    assert "agency_name" in cols
    assert "agency_type" in cols
    assert "searched" in cols
    assert "date_searched" in cols
    assert "ai_landing_page_url" in cols
    assert "ai_strategy_year" in cols
    assert "compliance_plan_year" in cols
    assert "genai_policy_year" in cols
    assert "caio_status" in cols
    assert "other_policy_count" in cols
    assert "total_documents" in cols
    assert "gaps" in cols
    assert "notes" in cols


def test_creates_expected_indexes_on_documents():
    conn = _conn()
    m012.apply(conn)
    idx = _indexes(conn, "agency_ai_policy_documents")
    expected = {
        "idx_agency_ai_policy_documents_agency_abbr",
        "idx_agency_ai_policy_documents_agency_type",
        "idx_agency_ai_policy_documents_document_type",
        "idx_agency_ai_policy_documents_publication_year",
    }
    assert expected.issubset(set(idx))


def test_compliance_table_has_agency_abbr_as_primary_key():
    conn = _conn()
    m012.apply(conn)
    rows = conn.execute("PRAGMA table_info(agency_ai_policy_compliance)").fetchall()
    pk_col = next(r["name"] for r in rows if r["pk"] == 1)
    assert pk_col == "agency_abbr"


def test_apply_is_idempotent():
    conn = _conn()
    m012.apply(conn)
    m012.apply(conn)  # second run must not raise
    cols = _columns(conn, "agency_ai_policy_documents")
    assert "id" in cols
