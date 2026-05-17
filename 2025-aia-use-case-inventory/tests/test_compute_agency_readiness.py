"""Tests for compute_agency_readiness (Federal AI Readiness Scorecard).

Builds an in-memory DB with three known agencies, applies migrations
m004–m006, populates a minimal fixture, runs the compute, and asserts
the rubric does what the methodology page says it does.
"""
from __future__ import annotations

import sqlite3

import pytest

from migrations import (
    m004_omb_consolidated_provenance as m004,
    m005_consolidation_pattern as m005,
    m006_agency_readiness as m006,
)
from scripts import compute_agency_readiness as ar


# --- Schema bootstrap ------------------------------------------------------

def _bootstrap_minimum_schema(conn: sqlite3.Connection) -> None:
    """Recreate just enough of the production schema for the rubric to run."""
    conn.executescript(
        """
        CREATE TABLE agencies (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            abbreviation TEXT NOT NULL UNIQUE
        );
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            canonical_name TEXT NOT NULL UNIQUE,
            product_origin TEXT
        );
        CREATE TABLE use_cases (
            id INTEGER PRIMARY KEY,
            agency_id INTEGER NOT NULL,
            use_case_id TEXT,
            use_case_name TEXT,
            bureau_component TEXT,
            stage_of_development TEXT,
            is_high_impact TEXT,
            justification TEXT,
            topic_area TEXT,
            ai_classification TEXT,
            problem_statement TEXT,
            expected_benefits TEXT,
            system_outputs TEXT,
            vendor_name TEXT,
            development_type TEXT,
            has_ato TEXT,
            training_data_description TEXT,
            link_to_data TEXT,
            has_pii TEXT,
            pia_url TEXT,
            has_custom_code TEXT,
            hi_testing_conducted TEXT,
            hi_assessment_completed TEXT,
            template_id INTEGER
        );
        CREATE TABLE consolidated_use_cases (
            id INTEGER PRIMARY KEY,
            agency_id INTEGER NOT NULL,
            template_id INTEGER
        );
        CREATE TABLE use_case_tags (
            id INTEGER PRIMARY KEY,
            use_case_id INTEGER,
            consolidated_use_case_id INTEGER,
            is_frontier_model INTEGER,
            is_agentic_ai INTEGER,
            ai_sophistication TEXT,
            has_meaningful_risk_docs INTEGER
        );
        CREATE TABLE use_case_products (
            use_case_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            PRIMARY KEY (use_case_id, product_id)
        );
        CREATE TABLE fedramp_product_links (
            id INTEGER PRIMARY KEY,
            inventory_product_id INTEGER NOT NULL,
            fedramp_id TEXT NOT NULL
        );
        CREATE TABLE agency_ai_maturity (
            agency_id INTEGER PRIMARY KEY,
            pct_with_risk_docs REAL,
            pct_deployed REAL
        );
        """
    )


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    _bootstrap_minimum_schema(c)
    # m006 only depends on `agencies`; m004/m005 alter pre-existing tables
    # the production migrations expect. We re-apply m006 to keep this test
    # representative of the runtime migration ledger.
    m006.apply(c)
    yield c
    c.close()


# --- Test data -------------------------------------------------------------

def _populate_fixture(conn: sqlite3.Connection) -> None:
    """Three agencies:
      1) HIGH — leader: 4 use cases, 2 bureaus, 1 frontier+agentic+custom,
         3 with ATO, 2 reporting fields fully filled, in maturity table
         with strong risk-docs + deployment percentages.
      2) MID — middle: 2 use cases, 1 bureau, 1 frontier, 1 ATO, partial
         reporting, modest maturity.
      3) LOW — laggard: 1 use case, no bureau, no frontier, no ATO, sparse
         reporting, missing from agency_ai_maturity.
      4) EMPTY — zero use cases at all.
    """
    conn.executescript(
        """
        INSERT INTO agencies VALUES
            (1, 'Department of High', 'HIGH'),
            (2, 'Mid Agency', 'MID'),
            (3, 'Low Agency', 'LOW'),
            (4, 'Empty Agency', 'EMPTY');

        INSERT INTO products (id, canonical_name) VALUES
            (10, 'Frontier LLM'),
            (11, 'Custom Tool');

        INSERT INTO fedramp_product_links (id, inventory_product_id, fedramp_id) VALUES
            (1, 10, 'FR0001');

        -- HIGH: 4 use cases (all fields filled), 2 bureaus, products on
        -- both FedRAMP-linked (id 10) and not (id 11).
        INSERT INTO use_cases (id, agency_id, bureau_component, stage_of_development,
            is_high_impact, justification, topic_area, ai_classification,
            problem_statement, expected_benefits, system_outputs, vendor_name,
            has_ato, training_data_description, link_to_data, has_custom_code)
        VALUES
            (101, 1, 'BureauA', 'Operation and Maintenance', 'Yes', 'because',
             'Mission', 'Generative AI', 'p', 'b', 'o', 'OpenAI', 'Yes', 'td', 'http://x', 'Yes'),
            (102, 1, 'BureauA', 'Initiated', 'No', 'j2',
             'Admin', 'Predictive', 'p2', 'b2', 'o2', 'Anthropic', 'Yes', 'td2', 'http://y', 'No'),
            (103, 1, 'BureauB', 'Operation and Maintenance', 'No', 'j3',
             'Cyber', 'Generative AI', 'p3', 'b3', 'o3', 'Microsoft', 'Yes', 'td3', 'http://z', 'No'),
            (104, 1, 'BureauB', 'Acquisition and/or Development', 'No', 'j4',
             'IT', 'CV', 'p4', 'b4', 'o4', 'AWS', 'No', 'td4', 'http://w', 'No');

        INSERT INTO use_case_products VALUES
            (101, 10), (102, 10), (103, 11), (104, 11);

        INSERT INTO use_case_tags (use_case_id, is_frontier_model, is_agentic_ai,
            ai_sophistication, has_meaningful_risk_docs)
        VALUES
            (101, 1, 1, 'agentic', 1),
            (102, 1, 0, 'general_llm', 1),
            (103, 0, 0, 'classical_ml', 0),
            (104, 0, 0, 'computer_vision', 0);

        INSERT INTO agency_ai_maturity (agency_id, pct_with_risk_docs, pct_deployed)
            VALUES (1, 80.0, 75.0);

        -- MID: 2 use cases.
        INSERT INTO use_cases (id, agency_id, bureau_component, stage_of_development,
            is_high_impact, justification, topic_area, ai_classification,
            problem_statement, expected_benefits, system_outputs, vendor_name,
            has_ato, training_data_description, link_to_data, has_custom_code)
        VALUES
            (201, 2, 'MidBureau', 'Initiated', 'No', '',
             'Admin', 'Generative AI', 'p', '', '', 'OpenAI', 'Yes', '', '', 'No'),
            (202, 2, 'MidBureau', NULL, NULL, NULL,
             NULL, NULL, NULL, NULL, NULL, NULL, 'No', NULL, NULL, NULL);

        INSERT INTO use_case_products VALUES (201, 10);

        INSERT INTO use_case_tags (use_case_id, is_frontier_model, is_agentic_ai,
            ai_sophistication, has_meaningful_risk_docs)
        VALUES
            (201, 1, 0, 'general_llm', 1),
            (202, 0, 0, NULL, 0);

        INSERT INTO agency_ai_maturity (agency_id, pct_with_risk_docs, pct_deployed)
            VALUES (2, 50.0, 40.0);

        -- LOW: 1 use case, no ATO, no frontier, no maturity row.
        INSERT INTO use_cases (id, agency_id, bureau_component, stage_of_development,
            is_high_impact, justification, topic_area, ai_classification,
            problem_statement, expected_benefits, system_outputs, vendor_name,
            has_ato, training_data_description, link_to_data, has_custom_code)
        VALUES
            (301, 3, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'No', NULL, NULL, NULL);

        INSERT INTO use_case_tags (use_case_id, is_frontier_model, is_agentic_ai,
            ai_sophistication, has_meaningful_risk_docs)
        VALUES (301, 0, 0, NULL, 0);

        -- EMPTY: no rows anywhere.
        """
    )


# --- Tests -----------------------------------------------------------------

def test_weights_sum_to_one():
    assert abs(sum(ar.WEIGHTS.values()) - 1.0) < 1e-9


def test_tier_band_assignment():
    # Exact-boundary checks against the published v1.1 tier bands.
    # A=70+, B=55+, C=35+, D=15+, F=<15.
    assert ar.assign_tier(70.0)[0] == "A"
    assert ar.assign_tier(69.9)[0] == "B"
    assert ar.assign_tier(55.0)[0] == "B"
    assert ar.assign_tier(54.9)[0] == "C"
    assert ar.assign_tier(35.0)[0] == "C"
    assert ar.assign_tier(34.9)[0] == "D"
    assert ar.assign_tier(15.0)[0] == "D"
    assert ar.assign_tier(14.9)[0] == "F"
    assert ar.assign_tier(0.0)[0] == "F"


def test_full_pipeline_three_agencies(conn):
    _populate_fixture(conn)
    result = ar.compute_agency_readiness(conn)

    rows = {r["abbreviation"]: r for r in result["rows"]}
    assert set(rows) == {"HIGH", "MID", "LOW", "EMPTY"}

    # HIGH should out-rank everyone.
    assert rows["HIGH"]["rank"] == 1
    assert rows["HIGH"]["composite_score"] > rows["MID"]["composite_score"]
    assert rows["MID"]["composite_score"] > rows["LOW"]["composite_score"]

    # EMPTY (no use cases, no maturity row) scores 0 across all dimensions.
    empty = rows["EMPTY"]
    assert empty["adoption_breadth"] == 0
    assert empty["frontier_capability"] == 0
    assert empty["procurement_hygiene"] == 0
    assert empty["internal_capacity"] == 0
    assert empty["risk_relevant_governance"] == 0
    assert empty["composite_score"] == 0
    assert empty["tier"] == "F"


def test_risk_relevant_governance_zero_for_no_risky_cases(conn):
    """LOW has 1 use case with no PII, no high-impact flag → no risky cases
    in the denominator → risk_relevant_governance is 0 by design (we don't
    reward absence of risk exposure).
    """
    _populate_fixture(conn)
    result = ar.compute_agency_readiness(conn)
    low = next(r for r in result["rows"] if r["abbreviation"] == "LOW")
    assert low["risk_relevant_governance"] == 0


def test_high_agency_has_strong_subscores(conn):
    _populate_fixture(conn)
    result = ar.compute_agency_readiness(conn)
    high = next(r for r in result["rows"] if r["abbreviation"] == "HIGH")

    # HIGH has 3/4 with ATO and 2/4 products FedRAMP-linked.
    # share_ato = 0.75, share_fedramp = 0.5 → procurement = 62.5
    assert high["procurement_hygiene"] == pytest.approx(62.5, abs=0.01)

    # Internal capacity sub-shares (out of 4 use cases):
    #   custom_code='Yes' on 101 only → 1/4
    #   inhouse dev: none → 0/4
    #   deployed stage ('Operation and Maintenance'): 101 + 103 → 2/4
    #   internal_platform products: 0 → 0/4
    # composite = (0.25 + 0 + 0.5 + 0) / 4 * 100 = 18.75
    assert high["internal_capacity"] == pytest.approx(18.75, abs=0.01)

    # Risk-relevant governance:
    #   Risky cases: 101 (is_high_impact='Yes'). No PII anywhere in fixture.
    #   101 has has_ato='Yes' → oversight signal present
    #   → 1/1 = 100
    assert high["risk_relevant_governance"] == pytest.approx(100.0, abs=0.01)


def test_idempotent(conn):
    _populate_fixture(conn)
    ar.compute_agency_readiness(conn)
    n1 = conn.execute("SELECT COUNT(*) FROM agency_readiness").fetchone()[0]
    ar.compute_agency_readiness(conn)
    n2 = conn.execute("SELECT COUNT(*) FROM agency_readiness").fetchone()[0]
    assert n1 == n2 == 4


def test_headline_stats_present(conn):
    _populate_fixture(conn)
    result = ar.compute_agency_readiness(conn)
    h = result["headline"]
    # Capacity-first headlines (the v1.1 hero candidates):
    assert "internal_build_pct" in h
    assert "production_rate_pct" in h
    assert "fedramp_coverage_pct" in h
    assert "frontier_ready_agency_count" in h
    # Compliance baseline preserved as a caveat-only stat:
    assert "hi_no_risk_docs_pct" in h
    # HIGH has 2/4 with meaningful risk docs, MID 1/2, LOW 0/1.
    # Total risk_docs = 3, total use cases = 7. So 1 - 3/7 = 0.5714 → 57.1%
    assert h["hi_no_risk_docs_pct"] == pytest.approx(57.1, abs=0.5)
    # Production rate: HIGH has 2/4 deployed, MID/LOW have 0 deployed,
    # EMPTY has 0 use cases. Total deployed = 2/7 = 28.6%.
    assert h["production_rate_pct"] == pytest.approx(28.6, abs=0.5)


def test_migration_m006_idempotent():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE agencies (id INTEGER PRIMARY KEY)")
    m006.apply(c)
    m006.apply(c)
    tables = {
        r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert "agency_readiness" in tables
    indexes = {
        r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
    }
    assert "idx_agency_readiness_rank" in indexes
