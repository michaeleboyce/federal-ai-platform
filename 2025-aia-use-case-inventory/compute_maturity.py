"""Compute agency-level AI maturity scores from tagged use cases."""

from db import get_connection


def compute_maturity():
    conn = get_connection()
    try:
        # Clear existing
        conn.execute("DELETE FROM agency_ai_maturity")

        # 2024 per-agency individual-use-case counts, queried live from the
        # ingested 2024 corpus (`use_cases_2024`, Phase 1 of the 2024↔2025
        # comparison project). This replaces a hand-typed dict — the YoY
        # column is now self-maintaining and tracks the v2 rolling-update
        # additions automatically. Keyed by the agency PK (`agency_id`).
        counts_2024 = dict(
            conn.execute(
                "SELECT agency_id, COUNT(*) FROM use_cases_2024 GROUP BY agency_id"
            ).fetchall()
        )

        # Get all agencies with use cases
        agencies = conn.execute("""
            SELECT DISTINCT a.id, a.abbreviation, a.name
            FROM agencies a
            WHERE EXISTS (SELECT 1 FROM use_cases WHERE agency_id = a.id)
               OR EXISTS (SELECT 1 FROM consolidated_use_cases WHERE agency_id = a.id)
        """).fetchall()

        for agency in agencies:
            aid = agency["id"]
            abbr = agency["abbreviation"]

            # Total counts
            total_uc = conn.execute(
                "SELECT COUNT(*) FROM use_cases WHERE agency_id = ?", (aid,)
            ).fetchone()[0]
            total_cons = conn.execute(
                "SELECT COUNT(*) FROM consolidated_use_cases WHERE agency_id = ?", (aid,)
            ).fetchone()[0]

            # AI type counts (from tags)
            stats = conn.execute("""
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
            """, (aid, aid)).fetchone()

            genai_count = stats["genai"] or 0
            coding_count = stats["coding"] or 0
            general_llm_count = stats["general_llm"] or 0
            classical_count = stats["classical"] or 0
            agentic_count = stats["agentic"] or 0
            custom_count = stats["custom_sys"] or 0

            # Distinct products deployed. Product edges are authoritative;
            # product_id columns are only a compatibility cache.
            distinct_products = conn.execute("""
                SELECT COUNT(DISTINCT product_id)
                  FROM entry_product_edges
                 WHERE agency_id = ?
            """, (aid,)).fetchone()[0]

            org = conn.execute(
                """
                SELECT id FROM federal_organizations
                 WHERE legacy_agency_id = ? AND parent_id IS NULL
                 LIMIT 1
                """,
                (aid,),
            ).fetchone()
            organization_id = org["id"] if org else None

            # Binary capability flags (agency has at least one entry of each type)
            #
            # Individually-reported rows ONLY: an Appendix-B template checkbox
            # ("Microsoft Copilot ... Y") is not evidence of an enterprise
            # rollout — counting consolidated entries here produced the FCC/
            # PBGC/EAC/OSC false positives the 2026-04 retag audit flagged
            # (audit/retag/TODO.md §3). The false negatives (State, VA, DOJ,
            # DOT) are cured upstream by the web-verified scope corrections.
            has_enterprise_llm = conn.execute("""
                SELECT COUNT(*) FROM use_case_tags t
                JOIN use_cases uc ON uc.id = t.use_case_id
                WHERE uc.agency_id = ?
                  AND t.is_general_llm_access = 1 AND t.is_enterprise_wide = 1
            """, (aid,)).fetchone()[0] > 0

            has_coding = coding_count > 0
            has_agentic = agentic_count > 0
            has_custom = custom_count > 0

            # Percentages
            total_tagged = conn.execute("""
                SELECT COUNT(*) FROM use_case_tags t
                LEFT JOIN use_cases uc ON uc.id = t.use_case_id
                LEFT JOIN consolidated_use_cases c ON c.id = t.consolidated_use_case_id
                WHERE uc.agency_id = ? OR c.agency_id = ?
            """, (aid, aid)).fetchone()[0] or 1

            deployed_count = conn.execute("""
                SELECT COUNT(*) FROM use_cases uc
                WHERE uc.agency_id = ? AND (
                    LOWER(uc.stage_of_development) LIKE '%deployed%' OR
                    LOWER(uc.stage_of_development) LIKE '%operation and maintenance%' OR
                    LOWER(uc.stage_of_development) LIKE '%production%'
                )
            """, (aid,)).fetchone()[0]
            pct_deployed = (deployed_count / total_uc * 100) if total_uc else 0

            high_impact_count = conn.execute("""
                SELECT COUNT(*) FROM use_case_tags t
                JOIN use_cases uc ON uc.id = t.use_case_id
                WHERE uc.agency_id = ? AND t.high_impact_designation = 'high_impact'
            """, (aid,)).fetchone()[0]
            pct_high_impact = (high_impact_count / total_uc * 100) if total_uc else 0

            risk_docs_count = conn.execute("""
                SELECT COUNT(*) FROM use_case_tags t
                JOIN use_cases uc ON uc.id = t.use_case_id
                WHERE uc.agency_id = ? AND t.has_meaningful_risk_docs = 1
            """, (aid,)).fetchone()[0]
            pct_with_risk_docs = (risk_docs_count / total_uc * 100) if total_uc else 0

            # Year-over-year growth — compare like-with-like against the
            # 2024 baseline in `use_cases_2024`, which is individual-format
            # only (the consolidated / Appendix B checkbox format is new in
            # 2025). Including total_cons in the numerator produces phantom
            # growth for agencies that switched entirely to the consolidated
            # format (PBGC, EAC, USTDA all showed +400-900% with zero
            # individual use cases). Suppress YoY entirely when the agency
            # filed no individual rows in 2025 — they didn't shrink by 100%,
            # they changed filing formats, and either a negative or an
            # inflated positive number would mislead readers.
            omb_2024 = counts_2024.get(aid, 0)
            if omb_2024 > 0 and total_uc > 0:
                yoy = ((total_uc - omb_2024) / omb_2024) * 100
            else:
                yoy = None

            # Overall presence (used only for maturity tier; NOT for YoY).
            current_total = total_uc + total_cons

            # Maturity tier
            if has_enterprise_llm and has_coding and has_agentic and current_total > 50:
                tier = "leading"
            elif has_enterprise_llm and current_total > 20:
                tier = "progressing"
            elif genai_count > 0 and current_total > 5:
                tier = "early"
            elif current_total <= 5 or (genai_count == 0 and current_total > 0):
                tier = "minimal"
            else:
                tier = "none"

            conn.execute("""
                INSERT INTO agency_ai_maturity (
                    agency_id, organization_id, total_use_cases, total_consolidated_entries,
                    distinct_products_deployed,
                    generative_ai_count, coding_tool_count, general_llm_count,
                    classical_ml_count, agentic_ai_count, custom_system_count,
                    has_enterprise_llm, has_coding_assistants, has_agentic_ai, has_custom_ai,
                    pct_deployed, pct_high_impact, pct_with_risk_docs,
                    year_over_year_growth, maturity_tier
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                aid, organization_id, total_uc, total_cons, distinct_products,
                genai_count, coding_count, general_llm_count,
                classical_count, agentic_count, custom_count,
                int(has_enterprise_llm), int(has_coding), int(has_agentic), int(has_custom),
                pct_deployed, pct_high_impact, pct_with_risk_docs,
                yoy, tier,
            ))

        conn.commit()

        # Print summary
        print("\n=== Agency AI Maturity ===")
        results = conn.execute("""
            SELECT a.abbreviation, m.total_use_cases, m.total_consolidated_entries,
                   m.distinct_products_deployed, m.generative_ai_count, m.coding_tool_count,
                   m.has_enterprise_llm, m.has_coding_assistants, m.has_agentic_ai,
                   m.maturity_tier, m.year_over_year_growth
            FROM agency_ai_maturity m JOIN agencies a ON a.id = m.agency_id
            ORDER BY m.total_use_cases + m.total_consolidated_entries DESC
        """).fetchall()

        print(f"\n{'Agency':<10} {'UC':>5} {'Cons':>5} {'Prod':>5} {'GenAI':>6} {'Code':>5} {'ELLM':>5} {'CODE':>5} {'AGT':>4} {'Tier':<12} {'YoY':>6}")
        for r in results:
            yoy_str = f"{r['year_over_year_growth']:+.0f}%" if r['year_over_year_growth'] is not None else "n/a"
            print(f"{r['abbreviation']:<10} {r['total_use_cases']:>5} {r['total_consolidated_entries']:>5} "
                  f"{r['distinct_products_deployed']:>5} {r['generative_ai_count']:>6} {r['coding_tool_count']:>5} "
                  f"{r['has_enterprise_llm']:>5} {r['has_coding_assistants']:>5} {r['has_agentic_ai']:>4} "
                  f"{r['maturity_tier']:<12} {yoy_str:>6}")

        # Tier summary
        print("\n=== Maturity Tier Summary ===")
        tier_summary = conn.execute("""
            SELECT maturity_tier, COUNT(*) FROM agency_ai_maturity GROUP BY maturity_tier
            ORDER BY CASE maturity_tier
                WHEN 'leading' THEN 1 WHEN 'progressing' THEN 2
                WHEN 'early' THEN 3 WHEN 'minimal' THEN 4 WHEN 'none' THEN 5
            END
        """).fetchall()
        for t in tier_summary:
            print(f"  {t['maturity_tier']}: {t['COUNT(*)']}")

    finally:
        conn.close()


if __name__ == "__main__":
    compute_maturity()
