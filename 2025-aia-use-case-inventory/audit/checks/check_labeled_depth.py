"""Machine-enforced pins for the 2026-07 labeled-depth rounds (m026 columns).

coding_tool_type (audit/retag/coding_taxonomy_2026-07/, gate GREEN
2026-07-06): 70 labeled = chat_assistant 25 + ide_autocomplete 18 +
code_analysis_tool 14 + unclear 9 + coding_agent 4 (post-audit-override).
integration_depth pins land with that round's apply (same-commit rule).

Bands exist because is_coding_tool has ~2-row rebuild jitter from
auto_tag heuristics. If a band trips after an intentional relabel or a
source-data refresh, re-baseline in the SAME commit and re-verify the
article claims that cite these numbers (fact_sheet §2/§3b).

Runs under pytest (audit/checks/ is collected by `make check`).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "federal_ai_inventory_2025.db"


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    yield c
    c.close()


def test_coding_taxonomy_labeled_band(conn):
    """Every is_coding_tool row should carry a coding_tool_type after
    scripts/apply_coding_taxonomy.py runs in the fix chain. Baseline
    2026-07-06: 70 labeled, 0 unlabeled. Small bands absorb auto_tag
    jitter adding/removing a coding row between relabels."""
    labeled = conn.execute(
        """SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
            WHERE coding_tool_type IS NOT NULL AND use_case_id IS NOT NULL"""
    ).fetchone()[0]
    unlabeled = conn.execute(
        """SELECT COUNT(*) FROM use_case_tags
            WHERE is_coding_tool = 1 AND use_case_id IS NOT NULL
              AND coding_tool_type IS NULL"""
    ).fetchone()[0]
    assert 65 <= labeled <= 75, (
        f"coding_tool_type labeled count {labeled} outside 70±5 — did "
        "apply_coding_taxonomy.py drop out of the fix chain?"
    )
    assert unlabeled <= 5, (
        f"{unlabeled} coding-tagged rows lack a coding_tool_type — auto_tag "
        "added coding rows the taxonomy round hasn't labeled; run a top-up "
        "batch (audit/retag/coding_taxonomy_2026-07/)."
    )


def test_no_deployed_agentic_coding_tool(conn):
    """FLAGSHIP article claim (fact_sheet §2): ZERO deployed or piloted
    agentic coding tools in the 2025 inventory — the 4 coding_agent
    filings (SBA x3, SSA Windsurf) are all pre_deployment as of
    2026-07-06. A source-data refresh that changes this must fail loudly
    so the article's 'the next wave is missing' claim gets re-verified,
    not silently stranded."""
    rows = conn.execute(
        """SELECT COALESCE(u.stage_normalized,'unknown'), COUNT(*)
             FROM use_case_tags t JOIN use_cases u ON u.id = t.use_case_id
            WHERE t.coding_tool_type = 'coding_agent'
            GROUP BY 1"""
    ).fetchall()
    total = sum(n for _, n in rows)
    live = sum(n for s, n in rows if s in ("deployed", "pilot"))
    assert 2 <= total <= 8, (
        f"coding_agent count {total} outside 4±4 band — re-verify the "
        "taxonomy round before citing."
    )
    assert live == 0, (
        f"{live} coding_agent rows now deployed/pilot ({rows}) — the "
        "article's 'zero live agentic coding tools' claim no longer holds; "
        "update fact_sheet §2 and the draft together."
    )


def test_integration_depth_coverage_band(conn):
    """integration_depth round (gate GREEN 2026-07-06): 1,572 of 1,573
    pilot+deployed rows labeled (the one gap is a DOI row with a blank
    use_case_name — signature unresolvable). Bands absorb stage jitter on
    reload; a big trip means apply_integration_depth.py dropped out of the
    fix chain."""
    labeled = conn.execute(
        """SELECT COUNT(DISTINCT t.use_case_id)
             FROM use_case_tags t JOIN use_cases u ON u.id = t.use_case_id
            WHERE t.integration_depth IS NOT NULL
              AND u.stage_normalized IN ('pilot','deployed')"""
    ).fetchone()[0]
    unlabeled = conn.execute(
        """SELECT COUNT(*)
             FROM use_case_tags t JOIN use_cases u ON u.id = t.use_case_id
            WHERE u.stage_normalized IN ('pilot','deployed')
              AND t.integration_depth IS NULL"""
    ).fetchone()[0]
    assert 1500 <= labeled <= 1650, (
        f"integration_depth labeled P+D count {labeled} outside 1572±band — "
        "did apply_integration_depth.py drop out of the fix chain?"
    )
    assert unlabeled <= 25, (
        f"{unlabeled} pilot/deployed rows lack integration_depth — stage "
        "drift added rows the round hasn't labeled; run a top-up batch "
        "(audit/retag/integration_depth_2026-07/)."
    )


def test_genai_integration_contrast_bands(conn):
    """FLAGSHIP article claim (fact_sheet §3b): operating GenAI is mostly
    uncoupled (baseline 2026-07-06: ~42% standalone_chat, ~14%
    system_integrated of 481 GenAI P+D rows) while the integrated estate
    is pre-GenAI (classical standalone share ~2%). Wide bands — this
    gates the DIRECTION of the contrast, not the decimals; a trip means
    re-verify §3b and the draft's integration claims together."""
    def share(genai: int, depth: str) -> float:
        num, den = conn.execute(
            """SELECT
                 COUNT(DISTINCT CASE WHEN t.integration_depth = ? THEN t.use_case_id END),
                 COUNT(DISTINCT t.use_case_id)
                 FROM use_case_tags t JOIN use_cases u ON u.id = t.use_case_id
                WHERE t.integration_depth IS NOT NULL
                  AND u.stage_normalized IN ('pilot','deployed')
                  AND COALESCE(t.is_generative_ai,0) = ?""",
            (depth, genai),
        ).fetchone()
        return num / den if den else 0.0

    genai_standalone = share(1, "standalone_chat")
    genai_integrated = share(1, "system_integrated")
    classical_standalone = share(0, "standalone_chat")
    assert 0.25 <= genai_standalone <= 0.60, (
        f"GenAI standalone_chat share {genai_standalone:.0%} outside the "
        "42%-baseline band — re-verify fact_sheet §3b."
    )
    assert genai_integrated <= 0.30, (
        f"GenAI system_integrated share {genai_integrated:.0%} above 30% — "
        "the 'GenAI is mostly uncoupled' claim needs re-verification."
    )
    assert classical_standalone <= 0.10, (
        f"non-GenAI standalone_chat share {classical_standalone:.0%} above "
        "10% — the 'integrated estate is pre-GenAI' contrast weakened."
    )
