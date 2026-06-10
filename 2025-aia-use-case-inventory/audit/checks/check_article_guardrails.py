"""Machine-enforced article guardrails.

Source: audit/retag/TODO.md §3 "Things the article must NOT say" and the
verification work in audit/retag/2024-tagging-verification/. These checks
keep the published surfaces (fact sheet, dashboard) from citing fields the
audits showed to be unreliable, and pin the flagship corrections so a
rebuild regression is caught at `make check` time.

Runs under pytest (audit/checks/ is collected by `make check`).
"""
from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "federal_ai_inventory_2025.db"
DASHBOARD_LIB = ROOT / "dashboard" / "lib"
DASHBOARD_APP = ROOT / "dashboard" / "app"


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    yield c
    c.close()


def _grep(pattern: str, *paths: Path) -> list[str]:
    """ripgrep-style search; returns matching lines (empty when no match)."""
    existing = [str(p) for p in paths if p.exists()]
    if not existing:
        return []
    out = subprocess.run(
        ["grep", "-rn", pattern, *existing, "--include=*.ts", "--include=*.tsx"],
        capture_output=True,
        text=True,
    )
    return [line for line in out.stdout.splitlines() if line.strip()]


def test_has_enterprise_llm_matches_tag_signal(conn):
    """agency_ai_maturity.has_enterprise_llm was wrong in BOTH directions
    (Appendix-B checkbox false positives; State/VA/DOJ/DOT false negatives)
    until compute_maturity.py was re-derived from corrected tags on
    individually-reported rows only. The dashboard displays the field, so
    it must stay byte-equal to the tag-derived signal."""
    mismatches = conn.execute(
        """
        SELECT a.abbreviation, m.has_enterprise_llm, derived.v
          FROM agencies a
          JOIN agency_ai_maturity m ON m.agency_id = a.id
          JOIN (
            SELECT a2.id AS agency_id,
                   CASE WHEN EXISTS (
                     SELECT 1 FROM use_cases uc
                       JOIN use_case_tags t ON t.use_case_id = uc.id
                      WHERE uc.agency_id = a2.id
                        AND t.is_general_llm_access = 1
                        AND t.is_enterprise_wide = 1
                   ) THEN 1 ELSE 0 END AS v
              FROM agencies a2
          ) derived ON derived.agency_id = m.agency_id
         WHERE m.has_enterprise_llm != derived.v
        """
    ).fetchall()
    assert not mismatches, (
        "agency_ai_maturity.has_enterprise_llm diverges from the tag-derived "
        f"signal (re-run compute_maturity.py): {mismatches[:10]}"
    )


def test_statechat_is_enterprise_wide(conn):
    """Flagship web-verified correction (FedScoop: 45K active users). If a
    rebuild loses this, the apply chain is silently broken again."""
    row = conn.execute(
        """SELECT t.deployment_scope, t.is_enterprise_wide
             FROM use_cases u JOIN use_case_tags t ON t.use_case_id = u.id
            WHERE u.use_case_name LIKE '%StateChat%'"""
    ).fetchone()
    assert row == ("enterprise_wide", 1), f"StateChat scope regressed: {row!r}"


def test_doj_code_development_tagged_coding(conn):
    row = conn.execute(
        """SELECT t.is_coding_tool
             FROM use_cases u
             JOIN agencies a ON a.id = u.agency_id
             JOIN use_case_tags t ON t.use_case_id = u.id
            WHERE a.abbreviation = 'DOJ' AND u.use_case_name = 'Code Development'"""
    ).fetchone()
    assert row is not None and row[0] == 1, f"DOJ Code Development regressed: {row!r}"


def test_deployment_environment_mostly_unknown_stays_caveated(conn):
    """deployment_environment is only filled where an agent verified a
    platform (~85 rows). If this ever exceeds 20% of rows the caveat in the
    fact sheet ('NEVER cite environment shares of the whole corpus') needs
    rewriting — fail so a human reconsiders."""
    filled = conn.execute(
        """SELECT COUNT(*) FROM use_case_tags
            WHERE use_case_id IS NOT NULL
              AND deployment_environment IS NOT NULL
              AND deployment_environment NOT IN ('', 'unknown')"""
    ).fetchone()[0]
    total = conn.execute(
        "SELECT COUNT(*) FROM use_case_tags WHERE use_case_id IS NOT NULL"
    ).fetchone()[0]
    assert filled / total < 0.20, (
        f"deployment_environment now filled on {filled}/{total} rows — "
        "update the fact-sheet caveat before citing environment shares."
    )


def test_stage_normalized_populated(conn):
    """The normalized stage column (m016) must be populated post-rebuild —
    every deployed-vs-pilot claim rides on it."""
    nulls = conn.execute(
        "SELECT COUNT(*) FROM use_cases WHERE stage_normalized IS NULL"
    ).fetchone()[0]
    assert nulls == 0, (
        f"{nulls} rows missing stage_normalized — did "
        "scripts/normalize_use_case_fields.py run after the load?"
    )


def test_agentic_tag_within_sanity_band(conn):
    """Post-review agentic count should sit near the agencies' own 'Agentic
    AI' label count (~115), far below the pre-review keyword count (283).
    A bounce back above 200 means the keyword tagger overwrote the reviewed
    verdicts (ordering bug in make fix)."""
    ifp = conn.execute(
        """SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
            WHERE ai_sophistication = 'agentic' AND use_case_id IS NOT NULL"""
    ).fetchone()[0]
    assert ifp < 200, (
        f"ai_sophistication='agentic' on {ifp} rows — the agentic review "
        "verdicts (audit/retag/agentic_review/) are not being applied."
    )
