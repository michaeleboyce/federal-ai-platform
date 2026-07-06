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


# Full-row scan fragments shared by the Claude Code pin below. raw_json
# carries every source column verbatim, so text-columns + raw_json is a
# complete scan of what the agency filed. Hand-synced with the §2 query in
# scripts/build_article_factsheet.py — change both together.
_UC_BLOB = """lower(
     COALESCE(use_case_name,'') || ' ' || COALESCE(problem_statement,'') || ' ' ||
     COALESCE(expected_benefits,'') || ' ' || COALESCE(system_outputs,'') || ' ' ||
     COALESCE(system_name,'') || ' ' || COALESCE(vendor_name,'') || ' ' ||
     COALESCE(raw_json,''))"""
_CUC_BLOB = """lower(
     COALESCE(ai_use_case,'') || ' ' || COALESCE(commercial_product,'') || ' ' ||
     COALESCE(commercial_examples,'') || ' ' || COALESCE(raw_json,''))"""


def test_claude_code_appears_exactly_once(conn):
    """Flagship article claim (claims_review_2026-07-06.md §1): 'Claude Code'
    appears EXACTLY once across both entry types — DOI's Appendix-B
    'Generating code using AI.' template row, in the commercial_product
    listing. The article leans on this number; a source reload or retag that
    changes it must fail loudly so the prose gets re-verified, not silently
    stranded. Resolved by signature (agency + template line + product text),
    never by rowid — ids rotate on every rebuild."""
    n_uc = conn.execute(
        f"SELECT COUNT(*) FROM use_cases WHERE {_UC_BLOB} LIKE '%claude code%'"
    ).fetchone()[0]
    n_cuc = conn.execute(
        f"SELECT COUNT(*) FROM consolidated_use_cases WHERE {_CUC_BLOB} LIKE '%claude code%'"
    ).fetchone()[0]
    assert (n_uc, n_cuc) == (0, 1), (
        f"'Claude Code' corpus count moved: {n_uc} individual + {n_cuc} "
        "consolidated (pinned 0 + 1). Re-verify the article's single-mention "
        "claim and update claims_review + fact_sheet §2 together."
    )
    sig = conn.execute(
        """SELECT a.abbreviation, c.ai_use_case
             FROM consolidated_use_cases c JOIN agencies a ON a.id = c.agency_id
            WHERE lower(
                  COALESCE(c.ai_use_case,'') || ' ' ||
                  COALESCE(c.commercial_product,'') || ' ' ||
                  COALESCE(c.commercial_examples,'') || ' ' ||
                  COALESCE(c.raw_json,'')) LIKE '%claude code%'"""
    ).fetchone()
    assert sig is not None and sig[0] == "DOI" and sig[1].startswith(
        "Generating code"
    ), (
        f"The single 'Claude Code' hit moved to {sig!r} — expected DOI's "
        "'Generating code using AI.' Appendix-B row. Update the article "
        "claim before re-pinning."
    )


def test_frontier_penetration_bands(conn):
    """Fact-sheet §1b headline rows (2026-07-06 baseline: M365 Copilot 41
    agencies / ChatGPT 19 — via entry_product_edges over the explicit
    canonical-name list, NOT is_frontier_llm). Bands absorb legitimate
    link-pass growth; a trip means either a product-links regression or
    the article's penetration table needs re-citing. Re-baseline only in
    the same commit as the linkage change that moves it."""
    def agencies_for(name: str) -> int:
        return conn.execute(
            """SELECT COUNT(DISTINCT e.agency_id)
                 FROM entry_product_edges e JOIN products p ON p.id = e.product_id
                WHERE p.canonical_name = ?""",
            (name,),
        ).fetchone()[0]

    m365 = agencies_for("Microsoft 365 Copilot")
    chatgpt = agencies_for("ChatGPT")
    assert 36 <= m365 <= 46, (
        f"M365 Copilot penetration moved to {m365} agencies (pinned 41±5) — "
        "update fact_sheet §1b and the article table together."
    )
    assert 15 <= chatgpt <= 24, (
        f"ChatGPT penetration moved to {chatgpt} agencies (pinned 19±4/5) — "
        "update fact_sheet §1b and the article table together."
    )
