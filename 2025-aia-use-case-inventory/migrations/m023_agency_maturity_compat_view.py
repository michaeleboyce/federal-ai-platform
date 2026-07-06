"""Collapse the dual maturity tables: agency_ai_maturity becomes a view.

Before: two physical tables computed by two scripts with subtly divergent
logic — `agency_ai_maturity` (55 rows, keyed by agencies.id, written by
compute_maturity.py) and `org_ai_maturity` (133 sub-org rows, written by
scripts/compute_org_maturity.py). After: `org_ai_maturity` is the single
physical table; the agency pass in compute_org_maturity.py writes the
per-agency rows into it (keyed by each agency's legacy-linked
organization, carrying the m022 columns), and `agency_ai_maturity` is a
compatibility VIEW with the exact legacy name and column shape, so all
dashboard readers keep working unmodified.

The view maps organization → agency via federal_organizations.
legacy_agency_id (bijective per audit/checks/check_org_agency_bijection).
Note it intentionally exposes rows for ANY legacy-linked org regardless of
level — VA-OIG's agencies row maps to an office-level node.

`has_enterprise_llm` is retained in the view for dashboard compatibility
until Slice D retires its renders; it is scheduled for removal from the
view afterwards (known-wrong field, superseded by
enterprise_genai_tier_rollup / agency_readiness — audit/retag/TODO.md §3).

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "023_agency_maturity_compat_view"

VIEW_SQL = """
CREATE VIEW agency_ai_maturity AS
SELECT
    m.id,
    fo.legacy_agency_id AS agency_id,
    m.total_use_cases,
    m.total_consolidated_entries,
    m.distinct_products_deployed,
    m.generative_ai_count,
    m.coding_tool_count,
    m.general_llm_count,
    m.classical_ml_count,
    m.agentic_ai_count,
    m.custom_system_count,
    m.has_enterprise_llm,
    m.has_coding_assistants,
    m.has_agentic_ai,
    m.has_custom_ai,
    m.pct_deployed,
    m.pct_high_impact,
    m.pct_with_risk_docs,
    m.year_over_year_growth,
    m.maturity_tier,
    m.notes,
    m.updated_at,
    m.organization_id
FROM org_ai_maturity m
JOIN federal_organizations fo ON fo.id = m.organization_id
WHERE fo.legacy_agency_id IS NOT NULL;
"""


def apply(conn: sqlite3.Connection) -> None:
    # Dropping the TABLE is safe because its contents are recomputed on
    # every `make fix`; nothing is lost. The drop must be type-aware:
    # SQLite's DROP TABLE errors on a view (and vice versa).
    row = conn.execute(
        "SELECT type FROM sqlite_master WHERE name = 'agency_ai_maturity'"
    ).fetchone()
    if row is not None:
        conn.execute(f"DROP {row[0].upper()} agency_ai_maturity")
    conn.executescript(VIEW_SQL)
