"""Row-count and ingest-integrity regression checks.

Source: audit/consistency/02_row_count_and_ingest_integrity.md
Baseline: audit/baselines/2026-04-12-pre-remediation.json

Asserts that core table row counts stay within +/- a small tolerance of the
2026-04-12 pre-remediation snapshot. Tolerances are wide enough to absorb
benign re-ingest churn but narrow enough that any structural change in the
loader (silent dedup, accidental drop, double-load) trips the test.
"""


def _count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_use_cases_total_matches_baseline(conn):
    n = _count(conn, "use_cases")
    # Baseline 3616; allow +/- 50 for ingest refreshes.
    assert 3566 <= n <= 3666, (
        f"use_cases count {n} diverged from baseline 3616 (+/- 50 tolerance)"
    )


def test_consolidated_use_cases_total_matches_baseline(conn):
    n = _count(conn, "consolidated_use_cases")
    # Baseline 192; allow +/- 20.
    assert 172 <= n <= 212, (
        f"consolidated_use_cases count {n} diverged from baseline 192 (+/- 20 tolerance)"
    )


def test_agencies_total_matches_baseline(conn):
    n = _count(conn, "agencies")
    # Baseline 60; allow +/- 5.
    assert 55 <= n <= 65, (
        f"agencies count {n} diverged from baseline 60 (+/- 5 tolerance)"
    )


def test_use_case_tags_total_matches_baseline(conn):
    n = _count(conn, "use_case_tags")
    # Baseline 3808; allow +/- 100.
    assert 3708 <= n <= 3908, (
        f"use_case_tags count {n} diverged from baseline 3808 (+/- 100 tolerance)"
    )


def test_products_total_matches_baseline(conn):
    n = _count(conn, "products")
    # Pre-remediation baseline 45; Phase 2 Agent D narrowed overbroad Copilot
    # aliases (which had collapsed distinct SKUs) and added 6 new products,
    # netting 39 canonical products. Threshold 35 catches a real catalog
    # regression without false-alarming on the intentional narrowing.
    assert n >= 35, (
        f"products count {n} below 35 (post-remediation expected ~39) "
        f"- catalog regression suspected"
    )


def test_product_aliases_total_matches_baseline(conn):
    n = _count(conn, "product_aliases")
    # Baseline 136; allow growth (Phase 2 Agent D adds aliases) but flag big drop.
    assert n >= 120, (
        f"product_aliases count {n} below baseline 136 - alias regression suspected"
    )


def test_no_duplicate_use_case_slugs(conn):
    """Slugs are UNIQUE-constrained; a violation would surface here as count > distinct."""
    total = _count(conn, "use_cases")
    distinct = conn.execute("SELECT COUNT(DISTINCT slug) FROM use_cases").fetchone()[0]
    assert total == distinct, (
        f"use_cases has {total} rows but only {distinct} distinct slugs - dup detected"
    )
