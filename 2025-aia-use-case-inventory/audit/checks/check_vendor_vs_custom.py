"""Vendor-product vs custom-system tagging consistency checks.

Source: audit/consistency/04_vendor_product_vs_custom_system.md
Baseline: audit/baselines/2026-04-12-pre-remediation.json
  - custom_system_with_vendor_name: 750 (pre-Phase-2)

Phase 2 Agent C tightened the ceilings after reclassifying vendor-backed
rows from custom_system to product_deployment / bespoke_application.
"""


def test_custom_system_with_vendor_name_under_tight_ceiling(conn):
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
    assert n <= 50, (
        f"custom_system rows with vendor_name populated = {n} "
        f"(baseline 750); ceiling 50 - vendor/custom tagging regression."
    )


def test_custom_system_with_purchased_from_vendor_under_tight_ceiling(conn):
    """custom_system rows whose source development_type says vendor purchase.

    Audit narrative reported 452 such rows pre-Phase-2. Target <=25.
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
    assert n <= 25, (
        f"custom_system rows with development_type='Purchased from a vendor' = {n} "
        f"(baseline ~452); ceiling 25 - tagging regression suspected"
    )
