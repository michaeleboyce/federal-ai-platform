"""Tests for compute_year_comparison (Phase 2 — 2024↔2025 aggregate rollup).

Builds an in-memory DB with a minimal schema (`agencies`, `use_cases`,
`use_cases_2024`), applies the m010 migration to create `year_comparison`,
seeds a small fixture with known 2024/2025 counts across a couple of stages
and dev methods, runs the compute, and asserts the tidy rollup is correct.
"""
from __future__ import annotations

import sqlite3

import pytest

import compute_year_comparison as cyc
from migrations import m010_year_comparison as m010


# --- Schema bootstrap ------------------------------------------------------

def _bootstrap_minimum_schema(conn: sqlite3.Connection) -> None:
    """Just enough of the production schema for the rollup to run."""
    conn.executescript(
        """
        CREATE TABLE agencies (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            abbreviation TEXT NOT NULL UNIQUE
        );
        CREATE TABLE use_cases (
            id INTEGER PRIMARY KEY,
            agency_id INTEGER NOT NULL,
            stage_of_development TEXT,
            development_type TEXT
        );
        CREATE TABLE use_cases_2024 (
            id INTEGER PRIMARY KEY,
            agency_id INTEGER NOT NULL,
            dev_stage TEXT,
            dev_method TEXT
        );
        """
    )


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    _bootstrap_minimum_schema(c)
    m010.apply(c)
    yield c
    c.close()


# --- Test data -------------------------------------------------------------

def _populate_fixture(conn: sqlite3.Connection) -> None:
    """Three agencies:
      A — in BOTH years: 3 use cases in 2024, 5 in 2025.
      B — 2024 only: 2 use cases in 2024, 0 in 2025 (retired agency).
      C — 2025 only: 0 in 2024, 4 in 2025 (new agency).

    Stages chosen to exercise the recode, including an off-enum 2024 value
    (`Planned`) that must land in Pre-deployment after the extended recode.
    """
    conn.executescript(
        """
        INSERT INTO agencies VALUES
            (1, 'Agency A', 'A'),
            (2, 'Agency B', 'B'),
            (3, 'Agency C', 'C');

        -- 2024: A has 3, B has 2 (total 5).
        INSERT INTO use_cases_2024 (id, agency_id, dev_stage, dev_method) VALUES
            (1, 1, 'Operation and Maintenance', 'Developed in-house.'),
            (2, 1, 'Initiated', 'Developed with contracting resources.'),
            (3, 1, 'Planned', NULL),
            (4, 2, 'Retired', 'Developed in-house.'),
            (5, 2, 'Operation and Maintenance',
             'Developed with both contracting and in-house resources.');

        -- 2025: A has 5, C has 4 (total 9).
        INSERT INTO use_cases (id, agency_id, stage_of_development,
            development_type) VALUES
            (101, 1, 'c) Deployed – actively used', 'b) Developed in-house'),
            (102, 1, 'a) Pre-deployment – in development', 'a) Purchased from a vendor'),
            (103, 1, 'b) Pilot – limited test', 'c) Developed with both contracting and in-house resources'),
            (104, 1, 'd) Retired – discontinued', NULL),
            (105, 1, 'Operation and Maintenance', 'N/A'),
            (201, 3, 'a) Pre-deployment', 'b) Developed in-house'),
            (202, 3, 'c) Deployed', 'a) Purchased from a vendor'),
            (203, 3, 'In Production', NULL),
            (204, 3, 'b) Pilot', 'Developed in-house');
        """
    )


def _rows_by_dim(conn, dimension):
    return conn.execute(
        "SELECT * FROM year_comparison WHERE dimension=?", (dimension,)
    ).fetchall()


# --- Stage bucketers -------------------------------------------------------

def test_bucket_stage_2024_canonical_and_offenum():
    assert cyc.bucket_stage_2024("Operation and Maintenance") == cyc.STAGE_DEPLOYED
    assert cyc.bucket_stage_2024("Initiated") == cyc.STAGE_PRE
    assert cyc.bucket_stage_2024("Retired") == cyc.STAGE_RETIRED
    assert cyc.bucket_stage_2024("Implementation and Assessment") == cyc.STAGE_PILOT
    # Off-enum values added in the Phase 2 recode extension.
    assert cyc.bucket_stage_2024("Planned") == cyc.STAGE_PRE
    assert cyc.bucket_stage_2024("Ideation") == cyc.STAGE_PRE
    assert cyc.bucket_stage_2024("In production") == cyc.STAGE_DEPLOYED
    assert cyc.bucket_stage_2024("In mission") == cyc.STAGE_DEPLOYED
    # Double-space CSV variant must still resolve.
    assert (
        cyc.bucket_stage_2024("Research or  Administrative Action Complete")
        == cyc.STAGE_RETIRED
    )
    # Empty / unrecognized → unknown.
    assert cyc.bucket_stage_2024("") == cyc.STAGE_UNKNOWN
    assert cyc.bucket_stage_2024(None) == cyc.STAGE_UNKNOWN
    assert cyc.bucket_stage_2024("Some Weird Value") == cyc.STAGE_UNKNOWN


def test_bucket_stage_2025_messy_strings():
    assert cyc.bucket_stage_2025("c)  Deployed – actively used") == cyc.STAGE_DEPLOYED
    assert cyc.bucket_stage_2025("a) Pre-deployment – in dev") == cyc.STAGE_PRE
    # Pilot long-form text contains 'deployed' — must still bucket as Pilot.
    assert (
        cyc.bucket_stage_2025("b)  Pilot  The use case has been deployed in a test")
        == cyc.STAGE_PILOT
    )
    assert cyc.bucket_stage_2025("d) Retired – discontinued") == cyc.STAGE_RETIRED
    assert cyc.bucket_stage_2025("Operation and Maintenance") == cyc.STAGE_DEPLOYED
    assert cyc.bucket_stage_2025("In Production") == cyc.STAGE_DEPLOYED
    assert cyc.bucket_stage_2025("") == cyc.STAGE_UNKNOWN
    assert cyc.bucket_stage_2025(None) == cyc.STAGE_UNKNOWN


def test_bucket_dev_method():
    assert cyc.bucket_dev_method("Developed in-house.") == cyc.METHOD_IN_HOUSE
    assert cyc.bucket_dev_method("b) Developed in-house") == cyc.METHOD_IN_HOUSE
    assert (
        cyc.bucket_dev_method("Developed with contracting resources.")
        == cyc.METHOD_CONTRACTED
    )
    assert cyc.bucket_dev_method("a) Purchased from a vendor") == cyc.METHOD_CONTRACTED
    assert (
        cyc.bucket_dev_method("Developed with both contracting and in-house resources.")
        == cyc.METHOD_BOTH
    )
    assert cyc.bucket_dev_method("N/A") == cyc.METHOD_UNKNOWN
    assert cyc.bucket_dev_method("") == cyc.METHOD_UNKNOWN
    assert cyc.bucket_dev_method(None) == cyc.METHOD_UNKNOWN


# --- Total dimension -------------------------------------------------------

def test_total_row(conn):
    _populate_fixture(conn)
    cyc.compute_year_comparison(conn)
    total = _rows_by_dim(conn, "total")
    assert len(total) == 1
    row = total[0]
    assert row["count_2024"] == 5
    assert row["count_2025"] == 9
    assert row["delta"] == 4
    assert row["pct_change"] == pytest.approx(80.0)
    assert row["bucket"] is None
    assert row["comparability"] == "clean"


# --- Agency dimension ------------------------------------------------------

def test_agency_rows(conn):
    _populate_fixture(conn)
    cyc.compute_year_comparison(conn)
    rows = {r["bucket"]: r for r in _rows_by_dim(conn, "agency")}
    assert set(rows) == {"A", "B", "C"}

    # A — present both years.
    assert rows["A"]["count_2024"] == 3
    assert rows["A"]["count_2025"] == 5
    assert rows["A"]["delta"] == 2
    assert rows["A"]["pct_change"] == pytest.approx(66.6667, abs=0.01)
    assert rows["A"]["agency_id"] == 1
    assert rows["A"]["comparability"] == "clean"

    # B — 2024 only → 0 on the 2025 side, pct_change present (count_2024 > 0).
    assert rows["B"]["count_2024"] == 2
    assert rows["B"]["count_2025"] == 0
    assert rows["B"]["delta"] == -2
    assert rows["B"]["pct_change"] == pytest.approx(-100.0)

    # C — 2025 only → 0 on the 2024 side, pct_change NULL (count_2024 == 0).
    assert rows["C"]["count_2024"] == 0
    assert rows["C"]["count_2025"] == 4
    assert rows["C"]["delta"] == 4
    assert rows["C"]["pct_change"] is None


# --- Stage dimension -------------------------------------------------------

def test_stage_rows(conn):
    _populate_fixture(conn)
    cyc.compute_year_comparison(conn)
    rows = {r["bucket"]: r for r in _rows_by_dim(conn, "stage")}
    # All 5 canonical stage buckets present.
    assert set(rows) == {
        cyc.STAGE_PRE, cyc.STAGE_PILOT, cyc.STAGE_DEPLOYED,
        cyc.STAGE_RETIRED, cyc.STAGE_UNKNOWN,
    }
    for r in rows.values():
        assert r["comparability"] == "lossy"

    # 2024 stages: OM(deployed), Initiated(pre), Planned(pre), Retired, OM.
    #   pre=2, deployed=2, retired=1.
    assert rows[cyc.STAGE_PRE]["count_2024"] == 2
    assert rows[cyc.STAGE_DEPLOYED]["count_2024"] == 2
    assert rows[cyc.STAGE_RETIRED]["count_2024"] == 1
    assert rows[cyc.STAGE_PILOT]["count_2024"] == 0

    # 2025 stages: Deployed, Pre, Pilot, Retired, OM(deployed),
    #   Pre, Deployed, In Production(deployed), Pilot.
    #   pre=2, pilot=2, deployed=4, retired=1.
    assert rows[cyc.STAGE_PRE]["count_2025"] == 2
    assert rows[cyc.STAGE_PILOT]["count_2025"] == 2
    assert rows[cyc.STAGE_DEPLOYED]["count_2025"] == 4
    assert rows[cyc.STAGE_RETIRED]["count_2025"] == 1

    # The off-enum 2024 'Planned' value landed in Pre-deployment, not unknown.
    assert rows[cyc.STAGE_UNKNOWN]["count_2024"] == 0


# --- dev_method dimension --------------------------------------------------

def test_dev_method_rows(conn):
    _populate_fixture(conn)
    cyc.compute_year_comparison(conn)
    rows = {r["bucket"]: r for r in _rows_by_dim(conn, "dev_method")}
    assert set(rows) == {
        cyc.METHOD_IN_HOUSE, cyc.METHOD_CONTRACTED,
        cyc.METHOD_BOTH, cyc.METHOD_UNKNOWN,
    }
    for r in rows.values():
        assert r["comparability"] == "lossy"

    # 2024: in-house, contracted, NULL, in-house, both.
    assert rows[cyc.METHOD_IN_HOUSE]["count_2024"] == 2
    assert rows[cyc.METHOD_CONTRACTED]["count_2024"] == 1
    assert rows[cyc.METHOD_BOTH]["count_2024"] == 1
    assert rows[cyc.METHOD_UNKNOWN]["count_2024"] == 1


# --- Idempotency -----------------------------------------------------------

def test_idempotent(conn):
    _populate_fixture(conn)
    cyc.compute_year_comparison(conn)
    n1 = conn.execute("SELECT COUNT(*) FROM year_comparison").fetchone()[0]
    cyc.compute_year_comparison(conn)
    n2 = conn.execute("SELECT COUNT(*) FROM year_comparison").fetchone()[0]
    assert n1 == n2
    # total(1) + agency(3) + stage(5) + dev_method(4) = 13.
    assert n1 == 13


def test_migration_m010_idempotent():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE agencies (id INTEGER PRIMARY KEY)")
    m010.apply(c)
    m010.apply(c)
    tables = {
        r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert "year_comparison" in tables
    indexes = {
        r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
    }
    assert "idx_year_comparison_dimension" in indexes
    c.close()
