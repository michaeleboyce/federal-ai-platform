"""Guard against drift between the two independent YoY computations.

The dashboard shows year-over-year growth from TWO separately-computed
sources: `agency_ai_maturity.year_over_year_growth` (analytics Fig. 02 /
Fig. 05) and `year_comparison.pct_change` where dimension='agency'
(/compare-years § III). They are built by different scripts and agree
only by construction — this test makes the agreement an invariant so a
future rebuild can't silently ship two different growth numbers for the
same agency.

Known, accepted asymmetry: agencies with zero 2025 use cases (full
attrition, pct_change = -100) have no maturity row at all, so they are
absent from the analytics chart — the chart's caption discloses this.
The test therefore only compares agencies present in BOTH sources.
"""
from __future__ import annotations

import pytest

TOLERANCE = 0.51  # pct-points; both sides round to 0.1 in different places


def test_yoy_growth_sources_agree(conn):
    rows = conn.execute(
        """
        SELECT a.abbreviation,
               y.pct_change,
               m.year_over_year_growth
          FROM year_comparison y
          JOIN agencies a ON a.id = y.agency_id
          JOIN agency_ai_maturity m ON m.agency_id = y.agency_id
         WHERE y.dimension = 'agency'
           AND y.pct_change IS NOT NULL
           AND m.year_over_year_growth IS NOT NULL
        """
    ).fetchall()
    assert rows, "no overlapping agencies between year_comparison and agency_ai_maturity"
    mismatches = [
        (r["abbreviation"], r["pct_change"], r["year_over_year_growth"])
        for r in rows
        if abs(r["pct_change"] - r["year_over_year_growth"]) > TOLERANCE
    ]
    assert not mismatches, (
        "year_comparison.pct_change and agency_ai_maturity.year_over_year_growth "
        f"disagree for: {mismatches}"
    )


def test_full_attrition_agencies_have_no_maturity_row(conn):
    """Documents (and pins) the asymmetry the analytics caption discloses:
    -100% agencies appear only in year_comparison."""
    rows = conn.execute(
        """
        SELECT a.abbreviation
          FROM year_comparison y
          JOIN agencies a ON a.id = y.agency_id
          JOIN agency_ai_maturity m ON m.agency_id = y.agency_id
         WHERE y.dimension = 'agency'
           AND y.pct_change = -100
           AND m.year_over_year_growth IS NOT NULL
        """
    ).fetchall()
    assert not [r["abbreviation"] for r in rows], (
        "full-attrition agencies unexpectedly gained maturity growth rows — "
        "update the analytics Fig. 02 caption if this is intentional"
    )
