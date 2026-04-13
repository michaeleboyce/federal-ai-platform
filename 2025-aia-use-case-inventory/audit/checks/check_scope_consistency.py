"""Scope and maturity consistency checks.

Source: audit/consistency/06_scope_and_maturity_consistency.md
Baseline: audit/baselines/2026-04-12-pre-remediation.json
  - enterprise_wide_consolidated: 111
  - enterprise_wide_agency_uses_split: {Y: 75, N: 29, NULL: 7}
    -> N + NULL = 36

THIS IS A BASELINE-LOOSE SCAFFOLD.

Phase 2 Agent E owns this check and will tighten the threshold from <=40
down to <=5 once enterprise_wide tagging is restricted to rows with
explicit agency-wide wording or supporting user/license signal.
"""


def test_enterprise_wide_consolidated_with_no_agency_use_under_loose_ceiling(conn):
    """consolidated rows tagged enterprise_wide but agency_uses != Y.

    Baseline 36 (N=29 + NULL=7). Phase 2 target: <=5.
    """
    n = conn.execute(
        """
        SELECT COUNT(*)
        FROM use_case_tags t
        JOIN consolidated_use_cases c ON c.id = t.consolidated_use_case_id
        WHERE t.deployment_scope = 'enterprise_wide'
          AND (c.agency_uses IS NULL OR c.agency_uses = 'N')
        """
    ).fetchone()[0]
    assert n <= 40, (
        f"enterprise_wide consolidated rows with agency_uses IN (N, NULL) = {n} "
        f"(baseline 36); ceiling 40 - scope tagging regression suspected. "
        f"Phase 2 Agent E will tighten this to <=5."
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
