"""Product-mapping and alias-quality checks.

Source: audit/consistency/05_product_mapping_and_alias_quality.md
Baseline: audit/baselines/2026-04-12-pre-remediation.json
  - product_id_null_on_use_cases: 3143

THIS IS A BASELINE-LOOSE SCAFFOLD.

Phase 2 Agent D owns this check and will tighten the thresholds once
alias coverage is expanded and over-broad canonical buckets are split
(Microsoft 365 Copilot, ServiceNow Now Assist).
"""


def test_product_deployment_rows_have_product_link(conn):
    """product_deployment / product_feature entries should have linkage in
    ``use_case_products`` (Agent D's join table) OR ``use_cases.product_id``.

    Agent D's heuristic pass resolves every row whose vendor text contains a
    canonical alias. The remaining orphans have vendor text like bare
    "Microsoft", "Google", "N/A", or consulting-firm names ("Leidos", "SAIC")
    that don't evidence a specific AI product — those are queued in
    ``review_queue_products`` for the coordinator's LLM review pass.

    After heuristic pass: ~600 orphans (up from 545 baseline because the
    stricter word-boundary matcher eliminated "Custom" false-positives from
    inside "Customs"). After LLM pass: expected ≤20.

    Ceiling 650 reflects the solvable-by-alias-only state. The LLM pass will
    tighten this further — see ``audit/review_queue_products_unresolved.csv``.
    """
    n = conn.execute(
        """
        SELECT COUNT(*)
        FROM use_case_tags t
        WHERE t.entry_type IN ('product_deployment', 'product_feature')
          AND t.use_case_id IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM use_case_products ucp
            WHERE ucp.use_case_id = t.use_case_id
          )
          AND NOT EXISTS (
            SELECT 1 FROM use_cases u
            WHERE u.id = t.use_case_id AND u.product_id IS NOT NULL
          )
        """
    ).fetchone()[0]
    assert n <= 650, (
        f"product_deployment/product_feature rows with no product linkage = {n} "
        f"(baseline 545; heuristic-only ceiling 650). Post-LLM target: ≤20."
    )


def test_cots_named_rows_mostly_resolve_to_products(conn):
    """Rows that name a COTS product should mostly resolve to products.product_id.

    Audit narrative: cots_product_name has 639 populated rows, 58 unmatched
    (9.1%). Current strict match: 61 unresolved. Phase 2 target: <=15.
    """
    n = conn.execute(
        """
        SELECT COUNT(*)
        FROM use_case_tags t
        LEFT JOIN use_cases u ON u.id = t.use_case_id
        LEFT JOIN consolidated_use_cases c ON c.id = t.consolidated_use_case_id
        WHERE t.cots_product_name IS NOT NULL
          AND TRIM(t.cots_product_name) <> ''
          AND COALESCE(u.product_id, c.product_id) IS NULL
        """
    ).fetchone()[0]
    assert n <= 100, (
        f"cots_product_name populated but no product_id linked: {n} "
        f"(baseline ~58, current 61); ceiling 100 - alias coverage regression suspected"
    )


def test_tool_named_rows_mostly_resolve_to_products(conn):
    """Rows that name a tool/product should mostly resolve to products.product_id.

    Audit narrative: tool_product_name has 592 populated rows, 24 unmatched
    (4.1%). Current strict match: 35 unresolved. Phase 2 target: <=10.
    """
    n = conn.execute(
        """
        SELECT COUNT(*)
        FROM use_case_tags t
        LEFT JOIN use_cases u ON u.id = t.use_case_id
        LEFT JOIN consolidated_use_cases c ON c.id = t.consolidated_use_case_id
        WHERE t.tool_product_name IS NOT NULL
          AND TRIM(t.tool_product_name) <> ''
          AND COALESCE(u.product_id, c.product_id) IS NULL
        """
    ).fetchone()[0]
    assert n <= 80, (
        f"tool_product_name populated but no product_id linked: {n} "
        f"(baseline ~24, current 35); ceiling 80 - alias coverage regression suspected"
    )


def test_no_alias_collisions_across_canonical_products(conn):
    """An alias_text should map to at most one canonical product."""
    rows = conn.execute(
        """
        SELECT alias_text, COUNT(DISTINCT product_id) AS n
        FROM product_aliases
        GROUP BY LOWER(TRIM(alias_text))
        HAVING n > 1
        """
    ).fetchall()
    assert rows == [], (
        f"product_aliases has {len(rows)} alias_text values mapped to multiple products: "
        f"{[(r[0], r[1]) for r in rows[:5]]}"
    )
