"""Hard checks for the refactor/data-quality contract."""

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent.parent
SNAPSHOT = ROOT / "audit" / "db_snapshot.md"
ROUND2_PRODUCTS = ROOT / "audit" / "retag" / "round2" / "products" / "proposed_new_products.csv"
EXPANDED_PRODUCTS = ROOT / "data" / "expanded_product_catalog.csv"


def _scalar(conn, sql: str, params=()):
    return conn.execute(sql, params).fetchone()[0]


def test_shared_views_exist(conn):
    rows = conn.execute(
        """
        SELECT name
          FROM sqlite_master
         WHERE type = 'view'
           AND name IN ('inventory_entries', 'entry_product_edges', 'agency_rollups')
        """
    ).fetchall()
    assert {r["name"] for r in rows} == {
        "inventory_entries",
        "entry_product_edges",
        "agency_rollups",
    }


def test_reporting_agency_count_comes_from_loaded_inventory(conn):
    loaded = _scalar(conn, "SELECT COUNT(DISTINCT agency_id) FROM inventory_entries")
    maturity = _scalar(conn, "SELECT COUNT(*) FROM agency_ai_maturity")
    found_2024_only_with_rows = _scalar(
        conn,
        """
        SELECT COUNT(DISTINCT a.id)
          FROM agencies a
          JOIN inventory_entries ie ON ie.agency_id = a.id
         WHERE a.status = 'FOUND_2024_ONLY'
        """,
    )
    assert loaded == maturity
    assert found_2024_only_with_rows == 0


def test_primary_product_view_is_derived_from_edges(conn):
    """The m025 drop retired the scalar cache columns; the m020
    entry_primary_products view is now the only primary-product surface.
    Assert it exists, is edge-consistent (one row per entry with >=1 edge),
    and the legacy columns are really gone."""
    view_rows = _scalar(conn, "SELECT COUNT(*) FROM entry_primary_products")
    entries_with_edges = _scalar(
        conn,
        """SELECT
             (SELECT COUNT(DISTINCT use_case_id) FROM use_case_products) +
             (SELECT COUNT(DISTINCT consolidated_use_case_id)
                FROM consolidated_use_case_products)""",
    )
    assert view_rows == entries_with_edges, (
        f"entry_primary_products has {view_rows} rows; expected one per "
        f"entry with edges ({entries_with_edges})"
    )
    uc_cols = {r[1] for r in conn.execute("PRAGMA table_info(use_cases)")}
    c_cols = {
        r[1] for r in conn.execute("PRAGMA table_info(consolidated_use_cases)")
    }
    assert "product_id" not in uc_cols and "template_id" not in uc_cols, (
        "legacy scalar columns survive on use_cases — m025 did not apply"
    )
    assert "product_id" not in c_cols, (
        "legacy scalar product_id survives on consolidated_use_cases"
    )
    assert "template_id" in c_cols, (
        "consolidated_use_cases.template_id must be KEPT (live column)"
    )


def test_consolidated_examples_do_not_create_product_evidence(conn):
    rows_from_examples = _scalar(
        conn,
        """
        SELECT COUNT(*)
          FROM consolidated_use_case_products
         WHERE LOWER(COALESCE(evidence_text, '')) LIKE '%commercial_examples%'
        """,
    )
    # (The primary-without-edge invariant is structural since m025: the
    # entry_primary_products view derives FROM the edges, so a primary
    # without an edge cannot exist.)
    assert rows_from_examples == 0


def test_agency_maturity_matches_shared_rollups(conn):
    drift = conn.execute(
        """
        SELECT a.abbreviation,
               m.total_use_cases,
               ar.total_use_cases AS rolled_total_use_cases,
               m.total_consolidated_entries,
               ar.total_consolidated_entries AS rolled_total_consolidated,
               m.distinct_products_deployed,
               ar.distinct_products_deployed AS rolled_distinct_products
          FROM agency_ai_maturity m
          JOIN agencies a ON a.id = m.agency_id
          JOIN agency_rollups ar ON ar.agency_id = m.agency_id
         WHERE m.total_use_cases != ar.total_use_cases
            OR m.total_consolidated_entries != ar.total_consolidated_entries
            OR m.distinct_products_deployed != ar.distinct_products_deployed
        """
    ).fetchall()
    assert drift == []


def test_product_catalog_is_reproducible_and_typed(conn):
    blank_types = _scalar(
        conn,
        "SELECT COUNT(*) FROM products WHERE product_type IS NULL OR TRIM(product_type) = ''",
    )
    total_products = _scalar(conn, "SELECT COUNT(*) FROM products")
    assert blank_types == 0
    assert ROUND2_PRODUCTS.exists()
    assert EXPANDED_PRODUCTS.exists()
    assert total_products >= 200


def test_generated_db_snapshot_matches_current_counts(conn):
    assert SNAPSHOT.exists(), "run scripts/generate_db_snapshot.py to refresh audit/db_snapshot.md"
    text = SNAPSHOT.read_text()
    expected = {
        "tracked_agencies": _scalar(conn, "SELECT COUNT(*) FROM agencies"),
        "loaded_agencies": _scalar(conn, "SELECT COUNT(DISTINCT agency_id) FROM inventory_entries"),
        "individual_entries": _scalar(conn, "SELECT COUNT(*) FROM use_cases"),
        "consolidated_entries": _scalar(conn, "SELECT COUNT(*) FROM consolidated_use_cases"),
        "canonical_products": _scalar(conn, "SELECT COUNT(*) FROM products"),
        "product_edges": _scalar(conn, "SELECT COUNT(*) FROM entry_product_edges"),
        "pending_product_reviews": _scalar(
            conn,
            "SELECT COUNT(*) FROM review_queue_products WHERE COALESCE(llm_reviewed, 0) = 0",
        ),
    }
    for key, value in expected.items():
        assert f"{key}: {value}" in text
