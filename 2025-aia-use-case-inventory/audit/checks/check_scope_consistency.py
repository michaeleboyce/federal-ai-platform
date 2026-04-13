"""Scope and maturity consistency checks.

Source: audit/consistency/06_scope_and_maturity_consistency.md
Baseline: audit/baselines/2026-04-12-pre-remediation.json
  - enterprise_wide_consolidated: 111
  - enterprise_wide_agency_uses_split: {Y: 75, N: 29, NULL: 7}
    -> N + NULL = 36

Tightened by Agent E (plan §E.5) after ``infer_scope()`` was rewritten to
require ``agency_uses='Y'`` OR explicit agency-wide phrasing for consolidated
rows. The 36 demotion candidates are now tagged 'unknown'; the residual
ceiling of 5 catches unexpected regressions from the new phrase list.
"""


def test_enterprise_wide_requires_evidence(conn):
    """consolidated rows tagged enterprise_wide but agency_uses != Y,
    and no explicit agency-wide wording in the description.

    Baseline 36. Post-Agent-E target: <=5.
    """
    n = conn.execute(
        """
        SELECT COUNT(*)
        FROM use_case_tags t
        JOIN consolidated_use_cases c ON c.id = t.consolidated_use_case_id
        WHERE t.deployment_scope = 'enterprise_wide'
          AND (c.agency_uses IS NULL OR c.agency_uses = 'N')
          AND LOWER(COALESCE(c.ai_use_case, '')) NOT LIKE '%agency-wide%'
          AND LOWER(COALESCE(c.ai_use_case, '')) NOT LIKE '%agency wide%'
          AND LOWER(COALESCE(c.ai_use_case, '')) NOT LIKE '%department-wide%'
          AND LOWER(COALESCE(c.ai_use_case, '')) NOT LIKE '%enterprise-wide%'
          AND LOWER(COALESCE(c.ai_use_case, '')) NOT LIKE '%all employees%'
          AND LOWER(COALESCE(c.ai_use_case, '')) NOT LIKE '%all staff%'
          AND LOWER(COALESCE(c.commercial_product, '')) NOT LIKE '%agency-wide%'
        """
    ).fetchone()[0]
    assert n <= 5, (
        f"Regressed: {n} unjustified enterprise_wide tags (baseline 36, target <=5)"
    )


def test_enterprise_wide_total_consolidated_under_loose_ceiling(conn):
    """Overall enterprise_wide population in consolidated rows.

    Baseline 111 of 192 consolidated rows (~58%). Audit: too high.
    Phase 2 will likely cut this; ceiling 130 catches accidental over-tagging.
    """
    n = conn.execute(
        """
        SELECT COUNT(*)
        FROM use_case_tags t
        JOIN consolidated_use_cases c ON c.id = t.consolidated_use_case_id
        WHERE t.deployment_scope = 'enterprise_wide'
        """
    ).fetchone()[0]
    assert n <= 130, (
        f"enterprise_wide consolidated rows = {n} "
        f"(baseline 111); ceiling 130 - over-tagging regression suspected"
    )


def test_enterprise_wide_use_cases_with_pre_deployment_under_loose_ceiling(conn):
    """canonical use_cases tagged enterprise_wide while still pre-deployment/pilot.

    Audit narrative reported 74 such rows; this is allowed (intent-tagging) but
    a sudden growth would be suspicious.
    """
    n = conn.execute(
        """
        SELECT COUNT(*)
        FROM use_case_tags t
        JOIN use_cases u ON u.id = t.use_case_id
        WHERE t.deployment_scope = 'enterprise_wide'
          AND LOWER(COALESCE(u.stage_of_development, '')) IN
              ('pre-deployment', 'pilot', 'planned', 'initiated', 'developmental')
        """
    ).fetchone()[0]
    assert n <= 120, (
        f"enterprise_wide canonical use_cases still in pre-deployment/pilot = {n} "
        f"(baseline ~74); ceiling 120 - tagging drift suspected"
    )
