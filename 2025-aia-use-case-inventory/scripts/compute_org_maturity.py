"""Compute sub-agency maturity tiers for orgs with at least N use cases
(via the effective org subtree: bureau_organization_id, falling back to
organization_id for top-level-only mappings).

Mirrors the rubric in compute_maturity.py but groups by federal_organizations
instead of agencies. Only emits rows for sub_agency / office levels — top-level
departments and independents are already covered by agency_ai_maturity.

Idempotent: clears and rewrites org_ai_maturity each run.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"

MIN_USE_CASES = 5  # threshold from the plan

INSERT_SQL = """
INSERT INTO org_ai_maturity (
    organization_id, total_use_cases, distinct_products_deployed,
    generative_ai_count, coding_tool_count, general_llm_count,
    classical_ml_count, agentic_ai_count, custom_system_count,
    has_enterprise_llm, has_coding_assistants, has_agentic_ai, has_custom_ai,
    pct_deployed, pct_high_impact, pct_with_risk_docs,
    maturity_tier
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def main() -> int:
    conn = _open()
    try:
        with conn:
            conn.execute("DELETE FROM org_ai_maturity")

            # All sub-orgs (sub_agency, office, component) with hierarchy_path
            sub_orgs = conn.execute(
                """
                SELECT id, name, abbreviation, hierarchy_path, level
                  FROM federal_organizations
                 WHERE level IN ('sub_agency','office','component')
                   AND hierarchy_path IS NOT NULL
                """
            ).fetchall()

            written = 0
            tier_counts: dict[str, int] = {}

            for org in sub_orgs:
                path = org["hierarchy_path"]

                # Use cases attached anywhere in this org's subtree
                stats = conn.execute(
                    """
                    SELECT
                        COUNT(*) AS total,
                        SUM(CASE WHEN t.is_generative_ai = 1 THEN 1 ELSE 0 END) AS genai,
                        SUM(CASE WHEN t.is_coding_tool = 1 THEN 1 ELSE 0 END) AS coding,
                        SUM(CASE WHEN t.is_general_llm_access = 1 THEN 1 ELSE 0 END) AS general_llm,
                        SUM(CASE WHEN t.ai_sophistication = 'classical_ml' THEN 1 ELSE 0 END) AS classical,
                        SUM(CASE WHEN t.ai_sophistication = 'agentic' THEN 1 ELSE 0 END) AS agentic,
                        SUM(CASE WHEN t.entry_type = 'custom_system' THEN 1 ELSE 0 END) AS custom_sys,
                        SUM(CASE WHEN t.is_general_llm_access = 1
                                  AND t.deployment_scope IN ('enterprise_wide','department')
                                 THEN 1 ELSE 0 END) AS enterprise_llm
                      FROM use_cases uc
                      JOIN federal_organizations fo
                        ON fo.id = COALESCE(uc.bureau_organization_id, uc.organization_id)
                      LEFT JOIN use_case_tags t ON t.use_case_id = uc.id
                     WHERE fo.hierarchy_path LIKE ? || '%'
                    """,
                    (path,),
                ).fetchone()

                total = stats["total"] or 0
                if total < MIN_USE_CASES:
                    continue

                genai = stats["genai"] or 0
                coding = stats["coding"] or 0
                general_llm = stats["general_llm"] or 0
                classical = stats["classical"] or 0
                agentic = stats["agentic"] or 0
                custom = stats["custom_sys"] or 0
                has_enterprise_llm = (stats["enterprise_llm"] or 0) > 0

                distinct_products = conn.execute(
                    """
                    SELECT COUNT(DISTINCT epe.product_id)
                      FROM entry_product_edges epe
                      JOIN federal_organizations fo
                        ON fo.id = COALESCE(epe.bureau_organization_id, epe.organization_id)
                     WHERE fo.hierarchy_path LIKE ? || '%'
                    """,
                    (path,),
                ).fetchone()[0]

                deployed = conn.execute(
                    """
                    SELECT COUNT(*)
                      FROM use_cases uc
                      JOIN federal_organizations fo
                        ON fo.id = COALESCE(uc.bureau_organization_id, uc.organization_id)
                     WHERE fo.hierarchy_path LIKE ? || '%'
                       AND (
                            LOWER(uc.stage_of_development) LIKE '%deployed%'
                         OR LOWER(uc.stage_of_development) LIKE '%operation and maintenance%'
                         OR LOWER(uc.stage_of_development) LIKE '%production%'
                       )
                    """,
                    (path,),
                ).fetchone()[0]
                pct_deployed = (deployed / total * 100) if total else 0.0

                high_impact = conn.execute(
                    """
                    SELECT COUNT(*)
                      FROM use_case_tags t
                      JOIN use_cases uc ON uc.id = t.use_case_id
                      JOIN federal_organizations fo
                        ON fo.id = COALESCE(uc.bureau_organization_id, uc.organization_id)
                     WHERE fo.hierarchy_path LIKE ? || '%'
                       AND t.high_impact_designation = 'high_impact'
                    """,
                    (path,),
                ).fetchone()[0]
                pct_high_impact = (high_impact / total * 100) if total else 0.0

                risk_docs = conn.execute(
                    """
                    SELECT COUNT(*)
                      FROM use_case_tags t
                      JOIN use_cases uc ON uc.id = t.use_case_id
                      JOIN federal_organizations fo
                        ON fo.id = COALESCE(uc.bureau_organization_id, uc.organization_id)
                     WHERE fo.hierarchy_path LIKE ? || '%'
                       AND t.has_meaningful_risk_docs = 1
                    """,
                    (path,),
                ).fetchone()[0]
                pct_with_risk_docs = (risk_docs / total * 100) if total else 0.0

                # Tier rubric — same thresholds as compute_maturity.py
                if has_enterprise_llm and coding > 0 and agentic > 0 and total > 50:
                    tier = "leading"
                elif has_enterprise_llm and total > 20:
                    tier = "progressing"
                elif genai > 0 and total > 5:
                    tier = "early"
                elif total <= 5 or (genai == 0 and total > 0):
                    tier = "minimal"
                else:
                    tier = "none"

                conn.execute(
                    INSERT_SQL,
                    (
                        org["id"], total, distinct_products,
                        genai, coding, general_llm,
                        classical, agentic, custom,
                        int(has_enterprise_llm), int(coding > 0),
                        int(agentic > 0), int(custom > 0),
                        pct_deployed, pct_high_impact, pct_with_risk_docs,
                        tier,
                    ),
                )
                written += 1
                tier_counts[tier] = tier_counts.get(tier, 0) + 1

        print(f"[org-maturity] wrote {written} sub-org maturity rows")
        for t in ("leading", "progressing", "early", "minimal", "none"):
            if t in tier_counts:
                print(f"  {t}: {tier_counts[t]}")

        # Show top 15 by total use cases
        rows = conn.execute(
            """
            SELECT fo.slug, fo.name, fo.abbreviation, m.total_use_cases,
                   m.has_enterprise_llm, m.coding_tool_count,
                   m.agentic_ai_count, m.maturity_tier
              FROM org_ai_maturity m
              JOIN federal_organizations fo ON fo.id = m.organization_id
             ORDER BY m.total_use_cases DESC
             LIMIT 15
            """
        ).fetchall()
        print("\nTop 15 sub-orgs by use-case count:")
        for r in rows:
            print(
                f"  {r['slug']:<28} {r['abbreviation'] or '—':<8} "
                f"uc={r['total_use_cases']:>4} ELLM={r['has_enterprise_llm']} "
                f"code={r['coding_tool_count']:>3} agt={r['agentic_ai_count']:>3} "
                f"tier={r['maturity_tier']}"
            )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
