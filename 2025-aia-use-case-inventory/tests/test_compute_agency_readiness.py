"""Tests for compute_agency_readiness (Federal AI Readiness Scorecard v1.2).

Builds an in-memory DB with known agencies, applies migrations, populates a
minimal fixture, runs the compute, and asserts the rubric does what the
methodology page says it does — including the v1.2 corrections:

  - "deployed" uses the canonical stage bucket (pilots are NOT deployed)
  - effective-unit dedup (atomized near-identical filings score once)
  - in-house cross-check (pure in-house claim + commercial vendor = no credit)
  - governance shrinkage toward the pooled federal rate (K=5)
  - tightened oversight predicate (real PIA URLs; case-insensitive hi_*)
  - readiness_headline persistence
"""
from __future__ import annotations

import sqlite3

import pytest

from migrations import (
    m006_agency_readiness as m006,
    m018_readiness_headline as m018,
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
            stage_normalized TEXT,
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
    m006.apply(c)
    m018.apply(c)
    yield c
    c.close()


# --- Test data -------------------------------------------------------------

def _populate_fixture(conn: sqlite3.Connection) -> None:
    """Four agencies:
      1) HIGH — leader: 4 use cases, 2 bureaus, 1 frontier+agentic+custom,
         3 with ATO, in maturity table with strong percentages.
      2) MID — middle: 2 use cases, 1 bureau, 1 frontier, 1 ATO.
      3) LOW — laggard: 1 sparse use case.
      4) EMPTY — zero use cases at all.
    Problem statements are all short (<25 chars) so every row is its own
    effective unit — dedup behavior is exercised by dedicated tests below.
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


# --- Rubric constant tests --------------------------------------------------

def test_weights_sum_to_one():
    assert abs(sum(ar.WEIGHTS.values()) - 1.0) < 1e-9


def test_rubric_version_is_1_2():
    assert ar.RUBRIC_VERSION == "1.2"


def test_tier_band_assignment():
    # Exact-boundary checks against the published tier bands.
    # A=70+, B=55+, C=35+, D=15+, F=<15. (Unchanged in v1.2.)
    assert ar.assign_tier(70.0)[0] == "A"
    assert ar.assign_tier(69.9)[0] == "B"
    assert ar.assign_tier(55.0)[0] == "B"
    assert ar.assign_tier(54.9)[0] == "C"
    assert ar.assign_tier(35.0)[0] == "C"
    assert ar.assign_tier(34.9)[0] == "D"
    assert ar.assign_tier(15.0)[0] == "D"
    assert ar.assign_tier(14.9)[0] == "F"
    assert ar.assign_tier(0.0)[0] == "F"


# --- Stage bucketing (the v1.1 pilot-as-deployed bug) ------------------------

def test_stage_bucket_pilot_label_is_not_deployed():
    """The OMB Pilot label contains the word 'deployed' — the v1.1 substring
    match counted 423 pilots as deployed. The canonical bucket must not."""
    pilot = ("b)  Pilot – The use case has been deployed in a limited test "
             "or pilot capacity.")
    assert ar._stage_bucket(None, pilot) == "pilot"
    assert ar._stage_bucket(None, "c)  Deployed – The use case is being actively authorized") == "deployed"
    assert ar._stage_bucket(None, "Operation and Maintenance") == "deployed"
    assert ar._stage_bucket(None, "In Production") == "deployed"
    assert ar._stage_bucket(None, "d) Retired – reported in prior year") == "retired"
    # stage_normalized wins when present:
    assert ar._stage_bucket("deployed", pilot) == "deployed"


def test_pilot_rows_do_not_count_as_deployed_end_to_end(conn):
    _populate_fixture(conn)
    # Add a pilot row to LOW whose label text contains "deployed".
    conn.execute(
        """INSERT INTO use_cases (id, agency_id, stage_of_development,
               has_ato, problem_statement)
           VALUES (302, 3, 'b)  Pilot  The use case has been deployed in a limited test or pilot capacity.',
                   'No', 'pp')"""
    )
    result = ar.compute_agency_readiness(conn)
    low = next(r for r in result["rows"] if r["abbreviation"] == "LOW")
    import json as _json
    inputs = _json.loads(low["headline_inputs_json"])
    assert inputs["internal_capacity"]["deployed"] == 0


def test_retired_rows_excluded_from_production_denominator(conn):
    _populate_fixture(conn)
    baseline = ar.compute_agency_readiness(conn)["headline"]
    # Adding a retired row must not depress the (active-denominator) rate.
    conn.execute(
        """INSERT INTO use_cases (id, agency_id, stage_of_development,
               has_ato, problem_statement)
           VALUES (303, 3, 'd) Retired  discontinued', 'No', 'rr')"""
    )
    after = ar.compute_agency_readiness(conn)["headline"]
    assert after["production_rate_pct"] == baseline["production_rate_pct"]
    assert after["production_rate_all_pct"] < baseline["production_rate_all_pct"]


# --- Effective-unit dedup -----------------------------------------------------

LONG_PS = "Ease the access to information and generate materials for staff"


def test_atomized_filings_dedup_to_one_unit(conn):
    """Three rows sharing a long identical problem statement + vendor +
    dev type collapse to ONE effective unit; short statements stay
    row-unique."""
    _populate_fixture(conn)
    for i in (401, 402, 403):
        conn.execute(
            """INSERT INTO use_cases (id, agency_id, stage_of_development,
                   problem_statement, vendor_name, development_type, has_ato)
               VALUES (?, 3, 'Deployed', ?, 'OpenAI', 'b) Developed in-house', 'No')""",
            (i, LONG_PS),
        )
        conn.execute(
            "INSERT INTO use_case_tags (use_case_id, is_frontier_model) VALUES (?, 1)",
            (i,),
        )
    units = ar._load_units(conn)
    low_units = units[3]
    # 1 pre-existing sparse row + 1 deduped group = 2 units (not 4)
    assert len(low_units) == 2
    group = next(u for u in low_units if u.member_count == 3)
    assert group.frontier is True
    assert group.deployed is True


def test_dedup_ignores_short_problem_statements(conn):
    _populate_fixture(conn)
    # HIGH's four rows all have short statements → 4 distinct units.
    units = ar._load_units(conn)
    assert len(units[1]) == 4


# --- In-house cross-check ------------------------------------------------------

def test_pure_inhouse_claim_with_commercial_vendor_gets_no_credit(conn):
    """The ED pattern: dev_type 'b) Developed in-house' + vendor 'OpenAI &
    Google Distributed Cloud' + no custom code is a mislabeled commercial
    buy, not internal capacity."""
    _populate_fixture(conn)
    conn.execute(
        """INSERT INTO use_cases (id, agency_id, problem_statement,
               development_type, vendor_name, has_custom_code, has_ato)
           VALUES (401, 3, 'x', 'b) Developed in-house',
                   'OpenAI & Google Distributed Cloud', 'No', 'No')"""
    )
    units = ar._load_units(conn)
    assert all(not u.inhouse for u in units[3])


def test_pure_inhouse_claim_with_placeholder_vendor_keeps_credit(conn):
    _populate_fixture(conn)
    conn.execute(
        """INSERT INTO use_cases (id, agency_id, problem_statement,
               development_type, vendor_name, has_custom_code, has_ato)
           VALUES (402, 3, 'x', 'Developed in-house', 'N/A', 'No', 'No')"""
    )
    units = ar._load_units(conn)
    assert any(u.inhouse for u in units[3])


def test_hybrid_inhouse_claim_keeps_credit_despite_vendor(conn):
    _populate_fixture(conn)
    conn.execute(
        """INSERT INTO use_cases (id, agency_id, problem_statement,
               development_type, vendor_name, has_custom_code, has_ato)
           VALUES (403, 3, 'x',
                   'c) Developed with both contracting and in-house resources',
                   'Accenture', 'No', 'No')"""
    )
    units = ar._load_units(conn)
    assert any(u.inhouse for u in units[3])


# --- Governance: shrinkage + tightened predicate --------------------------------

def test_governance_shrinkage_small_n_defers_to_prior(conn):
    """Agency A: 1/1 overseen. Agency B: 0/3 overseen. Pooled p0 = 1/4.
    A must NOT score 100 — with K=5: (1 + 5*0.25) / (1 + 5) = 37.5.
    B: (0 + 1.25) / 8 = 15.625 (→ 15.62 under Python banker's rounding)."""
    conn.executescript(
        """
        INSERT INTO agencies VALUES (1, 'A', 'A'), (2, 'B', 'B');
        INSERT INTO use_cases (id, agency_id, is_high_impact, has_ato, problem_statement)
        VALUES (1, 1, 'a) High-impact', 'Yes', 'x');
        """
    )
    for i in (2, 3, 4):
        conn.execute(
            """INSERT INTO use_cases (id, agency_id, is_high_impact, has_ato,
                   problem_statement) VALUES (?, 2, 'a) High-impact', 'No', ?)""",
            (i, f"y{i}"),
        )
    scores, raw = ar.compute_risk_relevant_governance(conn)
    assert scores[1] == pytest.approx(37.5, abs=0.01)
    assert scores[2] == pytest.approx(15.62, abs=0.01)
    assert raw[1]["raw_score"] == pytest.approx(100.0)
    assert raw[1]["prior_rate"] == pytest.approx(0.25)
    assert raw[1]["shrinkage_k"] == 5


def test_governance_zero_risky_still_scores_zero(conn):
    """LOW has 1 use case with no PII, no high-impact flag → no risky units
    → risk_relevant_governance is 0 by design (we don't reward absence of
    risk exposure). Unchanged in v1.2."""
    _populate_fixture(conn)
    result = ar.compute_agency_readiness(conn)
    low = next(r for r in result["rows"] if r["abbreviation"] == "LOW")
    assert low["risk_relevant_governance"] == 0


def test_junk_pia_url_is_not_an_oversight_signal(conn):
    """84% of non-blank pia_url values are placeholder text. Only a real
    URL counts (v1.2)."""
    conn.executescript(
        """
        INSERT INTO agencies VALUES (1, 'A', 'A'), (2, 'B', 'B');
        -- A: risky, junk PIA, no ATO, no hi_* → NOT overseen
        INSERT INTO use_cases (id, agency_id, is_high_impact, has_ato, pia_url,
            problem_statement) VALUES (1, 1, 'a) High-impact', 'No', 'N/A', 'x');
        -- B: risky, real PIA → overseen
        INSERT INTO use_cases (id, agency_id, is_high_impact, has_ato, pia_url,
            problem_statement)
        VALUES (2, 2, 'a) High-impact', 'No', 'https://agency.gov/pia.pdf', 'y');
        """
    )
    _, raw = ar.compute_risk_relevant_governance(conn)
    assert raw[1]["risky_with_oversight"] == 0
    assert raw[2]["risky_with_oversight"] == 1


def test_uppercase_na_hi_fields_do_not_count_as_filled(conn):
    """v1.1 compared hi_* values case-sensitively, so a literal 'N/A'
    counted as a filled Section-5 field."""
    conn.executescript(
        """
        INSERT INTO agencies VALUES (1, 'A', 'A');
        INSERT INTO use_cases (id, agency_id, is_high_impact, has_ato, pia_url,
            hi_testing_conducted, hi_assessment_completed, problem_statement)
        VALUES (1, 1, 'a) High-impact', 'No', NULL, 'N/A', 'Not Applicable', 'x');
        """
    )
    _, raw = ar.compute_risk_relevant_governance(conn)
    assert raw[1]["risky_with_oversight"] == 0


# --- Full pipeline ------------------------------------------------------------

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


def test_high_agency_has_strong_subscores(conn):
    _populate_fixture(conn)
    result = ar.compute_agency_readiness(conn)
    high = next(r for r in result["rows"] if r["abbreviation"] == "HIGH")

    # HIGH has 3/4 with ATO and 2 products, 1 FedRAMP-linked.
    # share_ato = 0.75, share_fedramp = 0.5 → procurement = 62.5
    assert high["procurement_hygiene"] == pytest.approx(62.5, abs=0.01)

    # Internal capacity sub-shares (4 units, all active):
    #   custom_code='Yes' on 101 only → 1/4
    #   inhouse dev: none → 0/4
    #   deployed ('Operation and Maintenance'): 101 + 103 → 2/4 active
    #   internal_platform products: 0 → 0/4
    # composite = (0.25 + 0 + 0.5 + 0) / 4 * 100 = 18.75
    assert high["internal_capacity"] == pytest.approx(18.75, abs=0.01)

    # Risk-relevant governance: the fixture's only risky unit federal-wide
    # is 101 (overseen via ATO), so p0 = 1.0 and shrinkage is a no-op:
    # (1 + 5*1.0) / (1 + 5) = 100.
    assert high["risk_relevant_governance"] == pytest.approx(100.0, abs=0.01)


def test_idempotent(conn):
    _populate_fixture(conn)
    ar.compute_agency_readiness(conn)
    n1 = conn.execute("SELECT COUNT(*) FROM agency_readiness").fetchone()[0]
    h1 = conn.execute("SELECT COUNT(*) FROM readiness_headline").fetchone()[0]
    ar.compute_agency_readiness(conn)
    n2 = conn.execute("SELECT COUNT(*) FROM agency_readiness").fetchone()[0]
    h2 = conn.execute("SELECT COUNT(*) FROM readiness_headline").fetchone()[0]
    assert n1 == n2 == 4
    assert h1 == h2 == 1


# --- Headline stats -------------------------------------------------------------

def test_headline_stats_present_and_persisted(conn):
    _populate_fixture(conn)
    result = ar.compute_agency_readiness(conn)
    h = result["headline"]

    # Three-way build split over 7 units: only 101 is internal (custom).
    assert h["internal_build_pct"] == pytest.approx(14.3, abs=0.1)
    assert h["purchased_pct"] == pytest.approx(0.0, abs=0.1)
    assert h["internal_build_pct"] + h["purchased_pct"] + h["unreported_pct"] == pytest.approx(100.0, abs=0.2)

    # Production rate: 2 deployed of 7 active units = 28.6%.
    assert h["production_rate_pct"] == pytest.approx(28.6, abs=0.5)

    # FedRAMP: units with a product link = 101,102,103,104,201 (5);
    # FedRAMP-linked (product 10) = 101,102,201 (3) → 60% / floor 3/7=42.9%.
    assert h["fedramp_linked_pct"] == pytest.approx(60.0, abs=0.1)
    assert h["fedramp_floor_pct"] == pytest.approx(42.9, abs=0.1)
    # Back-compat alias:
    assert h["fedramp_coverage_pct"] == h["fedramp_linked_pct"]

    # Compliance baseline: 3 of 7 rows have meaningful risk docs → 57.1%.
    assert h["hi_no_risk_docs_pct"] == pytest.approx(57.1, abs=0.5)
    # High-impact-only variant: 101 is the only high-impact row and it has
    # risk docs → 0% missing.
    assert h["hi_no_risk_docs_high_impact_pct"] == pytest.approx(0.0, abs=0.1)

    assert "frontier_ready_agency_count" in h

    # Persisted 1-row table matches the returned dict.
    row = conn.execute("SELECT * FROM readiness_headline").fetchone()
    assert row["rubric_version"] == ar.RUBRIC_VERSION
    assert row["production_rate_pct"] == pytest.approx(h["production_rate_pct"])
    assert row["internal_build_pct"] == pytest.approx(h["internal_build_pct"])
    assert row["total_units"] == 7


# --- Migrations ------------------------------------------------------------------

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


def test_migration_m018_dedupes_tags_and_guards():
    # Fresh connection WITHOUT m018 applied, so we can seed a duplicate
    # first and verify the migration cleans it up.
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    _bootstrap_minimum_schema(c)
    c.executescript(
        """
        INSERT INTO agencies VALUES (1, 'A', 'A');
        INSERT INTO use_case_tags (id, use_case_id, is_frontier_model) VALUES
            (1, 500, 0), (2, 500, 1), (3, 501, 0);
        """
    )
    m018.apply(c)
    n = c.execute(
        "SELECT COUNT(*) FROM use_case_tags WHERE use_case_id = 500"
    ).fetchone()[0]
    assert n == 1
    # Guard prevents re-introducing a duplicate.
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO use_case_tags (use_case_id) VALUES (501)")
    # Idempotent.
    m018.apply(c)
    assert "readiness_headline" in {
        r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    c.close()
