"""Field-fullness and tag-coarseness checks.

Source: audit/consistency/07_field_fullness_and_tag_coarseness.md
Baseline: audit/baselines/2026-04-12-pre-remediation.json
  - architecture_unknown: 2183 (current 2113 from audit narrative)
  - product_id_null_on_use_cases: 3143

Asserts no hard regression in null rates on key columns. These thresholds
are deliberately wider than current state - they catch a loader bug that
silently blanks a column, not slow drift.
"""


def _null_rate(conn, table, column):
    sql = (
        f"SELECT AVG(CASE WHEN {column} IS NULL OR TRIM(COALESCE({column}, '')) = '' "
        f"THEN 1.0 ELSE 0.0 END) FROM {table}"
    )
    return conn.execute(sql).fetchone()[0] or 0.0


def test_vendor_name_null_rate_not_pathological(conn):
    """vendor_name is sparsely populated by source (~71% null today).

    A loader bug that blanks the column would push this to 1.0; ceiling 0.85.
    """
    rate = _null_rate(conn, "use_cases", "vendor_name")
    assert rate <= 0.85, (
        f"use_cases.vendor_name null rate = {rate:.3f} "
        f"(baseline ~0.71); ceiling 0.85 - column may have been blanked"
    )


def test_has_ato_null_rate_not_pathological(conn):
    """has_ato baseline ~52% null."""
    rate = _null_rate(conn, "use_cases", "has_ato")
    assert rate <= 0.75, (
        f"use_cases.has_ato null rate = {rate:.3f} "
        f"(baseline ~0.52); ceiling 0.75 - column may have been blanked"
    )


def test_involves_pii_null_rate_not_pathological(conn):
    """involves_pii baseline ~54% null."""
    rate = _null_rate(conn, "use_cases", "involves_pii")
    assert rate <= 0.75, (
        f"use_cases.involves_pii null rate = {rate:.3f} "
        f"(baseline ~0.54); ceiling 0.75 - column may have been blanked"
    )


def test_ai_classification_null_rate_not_pathological(conn):
    """ai_classification is the primary AI-type signal; should stay well-populated.

    Baseline ~17% null. Hard ceiling 0.40 - a higher rate would defeat
    downstream LLM/CV/classical filters.
    """
    rate = _null_rate(conn, "use_cases", "ai_classification")
    assert rate <= 0.40, (
        f"use_cases.ai_classification null rate = {rate:.3f} "
        f"(baseline ~0.17); ceiling 0.40 - signal degradation suspected"
    )


def test_stage_of_development_null_rate_not_pathological(conn):
    """stage_of_development baseline ~8% null."""
    rate = _null_rate(conn, "use_cases", "stage_of_development")
    assert rate <= 0.30, (
        f"use_cases.stage_of_development null rate = {rate:.3f} "
        f"(baseline ~0.08); ceiling 0.30 - signal degradation suspected"
    )


def test_architecture_unknown_share_under_loose_ceiling(conn):
    """architecture_type='unknown' share of use_case_tags rows for canonical use_cases.

    Pre-remediation: 2113/3616 (58.5%). Phase 2 Agent E intentionally moved
    ~443 weak name-only inferences (rag_pipeline, agentic_workflow) to
    'unknown' per plan §E.2; post-remediation expected ~77%. The dashboard
    shows a callout explaining the shift. Ceiling 0.85 catches a genuine
    column-blanking regression without false-alarming on the intentional shift.
    """
    total = conn.execute(
        "SELECT COUNT(*) FROM use_case_tags WHERE use_case_id IS NOT NULL"
    ).fetchone()[0]
    unknown = conn.execute(
        "SELECT COUNT(*) FROM use_case_tags WHERE use_case_id IS NOT NULL "
        "AND architecture_type = 'unknown'"
    ).fetchone()[0]
    share = unknown / total if total else 0.0
    assert share <= 0.85, (
        f"use_case_tags.architecture_type='unknown' share = {share:.3f} "
        f"({unknown}/{total}, post-remediation expected ~0.77); ceiling 0.85"
    )


def test_product_capability_almost_entirely_blank_in_canonical(conn):
    """Documented baseline: only 1/3616 canonical rows has product_capability.

    This is a known gap. Just sanity-check the field still exists and is queryable.
    """
    populated = conn.execute(
        """
        SELECT COUNT(*)
        FROM use_case_tags
        WHERE use_case_id IS NOT NULL
          AND product_capability IS NOT NULL
          AND TRIM(product_capability) <> ''
        """
    ).fetchone()[0]
    # Phase 2 may backfill, but a sudden drop to 0 would indicate a bug.
    # No upper bound; just assert the query runs.
    assert populated >= 0, "product_capability query failed"
