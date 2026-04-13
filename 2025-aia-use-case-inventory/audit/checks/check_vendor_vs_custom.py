"""Vendor-product vs custom-system tagging consistency checks.

Source: audit/consistency/04_vendor_product_vs_custom_system.md
Baseline: audit/baselines/2026-04-12-pre-remediation.json
  - custom_system_with_vendor_name: 750

THIS IS A BASELINE-LOOSE SCAFFOLD.

Phase 2 Agent C owns this check and will tighten the threshold from <=800
down to <=50 once vendor-backed rows are re-classified to product_deployment.
For now we lock the ceiling at the current value plus a small headroom
buffer so a regression is detectable but pre-Phase-2 state still passes.
"""


def test_custom_system_with_vendor_name_under_loose_ceiling(conn):
    """custom_system rows that name a vendor (i.e. likely product_deployment).

    Baseline 750. Phase 2 target <=50.
    """
    n = conn.execute(
        """
        SELECT COUNT(*)
        FROM use_cases u
        JOIN use_case_tags t ON t.use_case_id = u.id
        WHERE t.entry_type = 'custom_system'
          AND u.vendor_name IS NOT NULL
          AND TRIM(u.vendor_name) <> ''
        """
    ).fetchone()[0]
    assert n <= 800, (
        f"custom_system rows with vendor_name populated = {n} "
        f"(baseline 750); ceiling 800 - tagging regression suspected. "
        f"Phase 2 Agent C will tighten this to <=50."
    )


def test_custom_system_with_purchased_from_vendor_under_loose_ceiling(conn):
    """custom_system rows whose source development_type says vendor purchase.

    Audit narrative reported 452 such rows. Loose ceiling 500.
    """
    n = conn.execute(
        """
        SELECT COUNT(*)
        FROM use_cases u
        JOIN use_case_tags t ON t.use_case_id = u.id
        WHERE t.entry_type = 'custom_system'
          AND u.development_type LIKE '%urchased%vendor%'
        """
    ).fetchone()[0]
    assert n <= 500, (
        f"custom_system rows with development_type='Purchased from a vendor' = {n} "
        f"(baseline ~452); ceiling 500 - tagging regression suspected"
    )
