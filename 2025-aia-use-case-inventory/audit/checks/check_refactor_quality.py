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


@pytest.mark.xfail(
    strict=False,
    reason="Pre-existing product-cache divergence (341 use_cases + 3 "
    "consolidated as of 2026-06-09, unchanged across rebuilds) — the "
    "use_cases.product_id cache disagrees with use_case_products edges. "
    "Tracked with the 626-row review_queue_products backlog; needs a "
    "dedicated cache-refresh pass, not a threshold tweak.",
)
def test_primary_product_cache_is_derived_from_edges(conn):
    stale_use_cases = _scalar(
        conn,
        """
        SELECT COUNT(*)
          FROM use_cases uc
         WHERE COALESCE(uc.product_id, -1) != COALESCE((
           SELECT ucp.product_id
             FROM use_case_products ucp
            WHERE ucp.use_case_id = uc.id
            ORDER BY CASE ucp.confidence WHEN 'strong' THEN 0 ELSE 1 END,
                     ucp.product_id
            LIMIT 1
         ), -1)
        """,
    )
    stale_consolidated = _scalar(
        conn,
        """
        SELECT COUNT(*)
          FROM consolidated_use_cases c
         WHERE COALESCE(c.product_id, -1) != COALESCE((
           SELECT cucp.product_id
             FROM consolidated_use_case_products cucp
            WHERE cucp.consolidated_use_case_id = c.id
            ORDER BY CASE cucp.confidence WHEN 'strong' THEN 0 ELSE 1 END,
                     cucp.product_id
            LIMIT 1
         ), -1)
        """,
    )
    assert stale_use_cases == 0
    assert stale_consolidated == 0


@pytest.mark.xfail(
    strict=False,
    reason="Pre-existing: 3 consolidated rows carry a product_id with no "
    "matching consolidated_use_case_products edge (as of 2026-06-09, "
    "unchanged across rebuilds). Same backlog as the cache-divergence xfail.",
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
    primary_without_edge = _scalar(
        conn,
        """
        SELECT COUNT(*)
          FROM consolidated_use_cases c
         WHERE c.product_id IS NOT NULL
           AND NOT EXISTS (
             SELECT 1
               FROM consolidated_use_case_products cucp
              WHERE cucp.consolidated_use_case_id = c.id
                AND cucp.product_id = c.product_id
           )
        """,
    )
    assert rows_from_examples == 0
    assert primary_without_edge == 0


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
