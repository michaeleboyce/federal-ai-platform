"""Compute ALL maturity rows into org_ai_maturity (single physical table).

Two passes, one table:

1. AGENCY pass — one row per agency with any 2025 entry, keyed by the
   agency's legacy-linked organization (federal_organizations.
   legacy_agency_id, bijective). This is the exact per-agency computation
   that used to live in compute_maturity.py / agency_ai_maturity,
   including the two agency-only columns (total_consolidated_entries,
   year_over_year_growth — m022) and the individual-rows-only
   has_enterprise_llm rule (see the inline note; audit/retag/TODO.md §3).
   The `agency_ai_maturity` compatibility VIEW (m023) exposes these rows
   under the legacy name/shape for every existing reader.

2. SUB-ORG pass — sub_agency/office/component orgs with >= MIN_USE_CASES
   use cases in their subtree (unchanged logic). Orgs already written by
   the agency pass are skipped (organization_id is UNIQUE).

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

AGENCY_INSERT_SQL = """
INSERT INTO org_ai_maturity (
    organization_id, total_use_cases, total_consolidated_entries,
    distinct_products_deployed,
    generative_ai_count, coding_tool_count, general_llm_count,
    classical_ml_count, agentic_ai_count, custom_system_count,
    has_enterprise_llm, has_coding_assistants, has_agentic_ai, has_custom_ai,
    pct_deployed, pct_high_impact, pct_with_risk_docs,
    year_over_year_growth, maturity_tier
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _tier(has_enterprise_llm: bool, coding: int, agentic: int,
          genai: int, current_total: int) -> str:
    """Shared maturity-tier rubric (identical thresholds in both passes)."""
    if has_enterprise_llm and coding > 0 and agentic > 0 and current_total > 50:
        return "leading"
    if has_enterprise_llm and current_total > 20:
        return "progressing"
    if genai > 0 and current_total > 5:
        return "early"
    if current_total <= 5 or (genai == 0 and current_total > 0):
        return "minimal"
    return "none"


def compute_agency_rows(conn: sqlite3.Connection) -> int:
    """The former compute_maturity.py per-agency computation, written into
    org_ai_maturity keyed by each agency's legacy-linked organization."""
    counts_2024 = dict(
        conn.execute(
            "SELECT agency_id, COUNT(*) FROM use_cases_2024 GROUP BY agency_id"
        ).fetchall()
    )
    agencies = conn.execute(
        """
        SELECT DISTINCT a.id, a.abbreviation
          FROM agencies a
         WHERE EXISTS (SELECT 1 FROM use_cases WHERE agency_id = a.id)
            OR EXISTS (SELECT 1 FROM consolidated_use_cases WHERE agency_id = a.id)
        """
    ).fetchall()

    written = 0
    skipped_no_org = []
    for agency in agencies:
        aid = agency["id"]
        org = conn.execute(
            "SELECT id FROM federal_organizations WHERE legacy_agency_id = ? "
            "ORDER BY (parent_id IS NULL) DESC LIMIT 1",
            (aid,),
        ).fetchone()
        if org is None:
            skipped_no_org.append(agency["abbreviation"])
            continue
        organization_id = org["id"]

        total_uc = conn.execute(
            "SELECT COUNT(*) FROM use_cases WHERE agency_id = ?", (aid,)
        ).fetchone()[0]
        total_cons = conn.execute(
            "SELECT COUNT(*) FROM consolidated_use_cases WHERE agency_id = ?",
            (aid,),
        ).fetchone()[0]

        stats = conn.execute(
            """
            SELECT
                SUM(CASE WHEN t.is_generative_ai = 1 THEN 1 ELSE 0 END) as genai,
                SUM(CASE WHEN t.is_coding_tool = 1 THEN 1 ELSE 0 END) as coding,
                SUM(CASE WHEN t.is_general_llm_access = 1 THEN 1 ELSE 0 END) as general_llm,
                SUM(CASE WHEN t.ai_sophistication = 'classical_ml' THEN 1 ELSE 0 END) as classical,
                SUM(CASE WHEN t.ai_sophistication = 'agentic' THEN 1 ELSE 0 END) as agentic,
                SUM(CASE WHEN t.entry_type = 'custom_system' THEN 1 ELSE 0 END) as custom_sys
            FROM use_case_tags t
            LEFT JOIN use_cases uc ON uc.id = t.use_case_id
            LEFT JOIN consolidated_use_cases c ON c.id = t.consolidated_use_case_id
            WHERE uc.agency_id = ? OR c.agency_id = ?
            """,
            (aid, aid),
        ).fetchone()
        genai = stats["genai"] or 0
        coding = stats["coding"] or 0
        general_llm = stats["general_llm"] or 0
        classical = stats["classical"] or 0
        agentic = stats["agentic"] or 0
        custom = stats["custom_sys"] or 0

        distinct_products = conn.execute(
            "SELECT COUNT(DISTINCT product_id) FROM entry_product_edges "
            "WHERE agency_id = ?",
            (aid,),
        ).fetchone()[0]

        # Individually-reported rows ONLY: an Appendix-B template checkbox
        # is not evidence of an enterprise rollout — counting consolidated
        # entries here produced the FCC/PBGC/EAC/OSC false positives the
        # 2026-04 retag audit flagged (audit/retag/TODO.md §3). Field is
        # retained for view compatibility; scheduled for retirement in
        # favor of enterprise_genai_tier_rollup / agency_readiness.
        has_enterprise_llm = conn.execute(
            """
            SELECT COUNT(*) FROM use_case_tags t
            JOIN use_cases uc ON uc.id = t.use_case_id
            WHERE uc.agency_id = ?
              AND t.is_general_llm_access = 1 AND t.is_enterprise_wide = 1
            """,
            (aid,),
        ).fetchone()[0] > 0

        deployed = conn.execute(
            "SELECT COUNT(*) FROM use_cases "
            "WHERE agency_id = ? AND stage_normalized = 'deployed'",
            (aid,),
        ).fetchone()[0]
        pct_deployed = (deployed / total_uc * 100) if total_uc else 0

        high_impact = conn.execute(
            """
            SELECT COUNT(*) FROM use_case_tags t
            JOIN use_cases uc ON uc.id = t.use_case_id
            WHERE uc.agency_id = ? AND t.high_impact_designation = 'high_impact'
            """,
            (aid,),
        ).fetchone()[0]
        pct_high_impact = (high_impact / total_uc * 100) if total_uc else 0

        risk_docs = conn.execute(
            """
            SELECT COUNT(*) FROM use_case_tags t
            JOIN use_cases uc ON uc.id = t.use_case_id
            WHERE uc.agency_id = ? AND t.has_meaningful_risk_docs = 1
            """,
            (aid,),
        ).fetchone()[0]
        pct_with_risk_docs = (risk_docs / total_uc * 100) if total_uc else 0

        # YoY vs the 2024 individual-format corpus; suppressed when the
        # agency filed no individual 2025 rows (format switch, not shrink).
        omb_2024 = counts_2024.get(aid, 0)
        if omb_2024 > 0 and total_uc > 0:
            yoy = ((total_uc - omb_2024) / omb_2024) * 100
        else:
            yoy = None

        current_total = total_uc + total_cons
        tier = _tier(has_enterprise_llm, coding, agentic, genai, current_total)

        conn.execute(
            AGENCY_INSERT_SQL,
            (
                organization_id, total_uc, total_cons, distinct_products,
                genai, coding, general_llm, classical, agentic, custom,
                int(has_enterprise_llm), int(coding > 0), int(agentic > 0),
                int(custom > 0),
                pct_deployed, pct_high_impact, pct_with_risk_docs,
                yoy, tier,
            ),
        )
        written += 1

    if skipped_no_org:
        # Every agency with data must have a legacy-linked org (the
        # bijection check enforces it) — fail loudly, not silently.
        raise SystemExit(
            f"FATAL: {len(skipped_no_org)} agencies have inventory data but "
            f"no legacy-linked federal_organizations row: {skipped_no_org} — "
            "add them to data/federal_hierarchy_seed.py / "
            "scripts/seed_federal_hierarchy.py SPECIAL_LEGACY_LINKS"
        )
    return written


def main() -> int:
    conn = _open()
    try:
        with conn:
            conn.execute("DELETE FROM org_ai_maturity")

            agency_rows = compute_agency_rows(conn)
            agency_org_ids = {
                r[0]
                for r in conn.execute(
                    "SELECT organization_id FROM org_ai_maturity"
                )
            }

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
                if org["id"] in agency_org_ids:
                    # Already written by the agency pass (e.g. VA-OIG's
                    # office node carries a legacy_agency_id).
                    continue
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
                       AND uc.stage_normalized = 'deployed'
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

                tier = _tier(has_enterprise_llm, coding, agentic, genai, total)

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

        print(
            f"[org-maturity] wrote {agency_rows} agency rows + "
            f"{written} sub-org rows"
        )
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
