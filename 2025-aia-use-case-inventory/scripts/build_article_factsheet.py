"""Generate audit/article/fact_sheet.md — every number the IFP article can
cite, each with the exact SQL that produced it and the caveats that must
travel with it.

Story frame the sheet serves: the administration has broadly supported
chatbot/assistant adoption across agencies, while advanced capabilities —
coding assistance and serious data analytics — are still mostly pending.

Re-run after any `make fix`:
    python3 scripts/build_article_factsheet.py

The sheet is deterministic given the same DB except for the "Generated"
line; diff with that line excluded when checking reproducibility.
"""
from __future__ import annotations

import datetime as _dt
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT = ROOT / "audit" / "article" / "fact_sheet.md"

# Canonical column populated by scripts/normalize_use_case_fields.py (m016).
STAGE_BUCKET = "u.stage_normalized"

# 2024 dev_stage values are cleaner; bucket with the same intent.
STAGE_BUCKET_2024 = """
  CASE
    WHEN LOWER(COALESCE(u.dev_stage,'')) LIKE '%retire%' THEN 'retired'
    WHEN LOWER(COALESCE(u.dev_stage,'')) LIKE '%implementation%'
      OR LOWER(COALESCE(u.dev_stage,'')) LIKE '%assessment%' THEN 'pilot'
    WHEN LOWER(COALESCE(u.dev_stage,'')) LIKE '%operation%'
      OR LOWER(COALESCE(u.dev_stage,'')) LIKE '%production%'
      OR LOWER(COALESCE(u.dev_stage,'')) LIKE '%mission%' THEN 'deployed'
    WHEN TRIM(COALESCE(u.dev_stage,'')) = '' THEN 'unknown'
    ELSE 'pre_deployment'
  END
"""


def main() -> int:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    q = lambda sql, *p: conn.execute(sql, p).fetchall()  # noqa: E731
    q1 = lambda sql, *p: conn.execute(sql, p).fetchone()[0]  # noqa: E731

    lines: list[str] = []
    w = lines.append

    def fact(label: str, value, sql: str, caveats: list[str] | None = None):
        w(f"### {label}\n")
        w(f"**{value}**\n")
        w("```sql")
        w(sql.strip())
        w("```")
        for c in caveats or []:
            w(f"- ⚠ {c}")
        w("")

    today = _dt.date.today().isoformat()
    w("# Article fact sheet — 2025 Federal AI Use Case Inventory (IFP tags)")
    w("")
    w(f"_Generated: {today} by `scripts/build_article_factsheet.py`. Re-run after any `make fix`._")
    w("")
    w("Every number below is produced by the SQL shown with it, against")
    w("`data/federal_ai_inventory_2025.db`. Caveats marked ⚠ MUST travel with")
    w("the number into the article. See §Guardrails for claims the data")
    w("cannot support.")
    w("")

    # ------------------------------------------------------------------ scale
    w("## 0. Scale")
    w("")
    fact(
        "Individually reported 2025 use cases",
        q1("SELECT COUNT(*) FROM use_cases"),
        "SELECT COUNT(*) FROM use_cases",
        ["Excludes the 900 Appendix-B consolidated template entries (counted separately)."],
    )
    fact(
        "2024 use cases (M-24-10 corpus)",
        q1("SELECT COUNT(*) FROM use_cases_2024"),
        "SELECT COUNT(*) FROM use_cases_2024",
    )

    # --------------------------------------------------------------- pillar 1
    w("## 1. Pillar — chatbots / assistants arrived broadly")
    w("")
    sql_omb = """SELECT COUNT(*) FROM use_cases
 WHERE ai_classification LIKE '%Generative%'"""
    fact("GenAI by OMB's own classification (2025)", q1(sql_omb), sql_omb,
         ["OMB's `ai_classification` field as filed by agencies; 600+ rows left it blank."])

    sql_ifp = """SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE is_generative_ai = 1 AND use_case_id IS NOT NULL"""
    fact("GenAI by IFP tag (2025)", q1(sql_ifp), sql_ifp)

    sql_2024_genai = """SELECT COUNT(*) FROM use_case_tags_2024_canonical
 WHERE is_generative_ai = 1"""
    fact("GenAI by IFP tag (2024)", q1(sql_2024_genai), sql_2024_genai,
         ["2024 tags are agent-tagged + verified (93.9% sampled accuracy on this flag)."])

    sql_llm = """SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE is_general_llm_access = 1 AND use_case_id IS NOT NULL"""
    fact("General-purpose LLM access entries (2025)", q1(sql_llm), sql_llm,
         ["Definition: staff can submit arbitrary prompts, internal-work approved, "
          "broadly available — not single-workflow integrations. "
          "Low-confidence heuristic flips were re-adjudicated row-by-row in "
          "audit/retag/general_llm_round3/."])

    sql_ew = """SELECT COUNT(DISTINCT u.agency_id)
  FROM use_cases u JOIN use_case_tags t ON t.use_case_id = u.id
 WHERE t.is_generative_ai = 1 AND t.is_enterprise_wide = 1"""
    ew_2025 = q1(sql_ew)
    sql_ew24 = """SELECT COUNT(DISTINCT u.agency_id)
  FROM use_cases_2024 u
  JOIN use_case_tags_2024_canonical t ON t.use_case_id_2024 = u.id
 WHERE t.is_generative_ai = 1 AND t.is_enterprise_wide = 1"""
    ew_2024 = q1(sql_ew24)
    fact(
        f"Agencies with enterprise-wide GenAI: {ew_2024} (2024) → {ew_2025} (2025)",
        f"{ew_2024} → {ew_2025}",
        sql_ew + ";\n-- 2024:\n" + sql_ew24,
        ["The 2025 figure includes the web-verified scope corrections "
         "(StateChat, VA GPT, DHSChat, Ask Dottie...) restored by "
         "apply_retag_audit.py. Earlier drafts said 15→12; that was an "
         "artifact of the corrections not being applied — do not reuse it.",
         "Tag-row counts (not agency counts) concentrate heavily in HHS; "
         "always pair a row count with the agency count."],
    )

    rows = q(f"""SELECT a.abbreviation
  FROM use_cases u
  JOIN agencies a ON a.id = u.agency_id
  JOIN use_case_tags t ON t.use_case_id = u.id
 WHERE t.is_generative_ai = 1 AND t.is_enterprise_wide = 1
 GROUP BY a.abbreviation ORDER BY a.abbreviation""")
    w(f"Enterprise-wide GenAI agencies (2025): {', '.join(r[0] for r in rows)}")
    w("")

    # ------------------------------------------------ pillar 1b: penetration
    # Explicit canonical-name list, NOT products.is_frontier_llm (that flag
    # excludes GitHub Copilot/Perplexity and includes Amazon Q/USAi/Ask
    # Sage). Names resolve at query time — product ids rotate per rebuild.
    w("## 1b. Frontier-product penetration (named-product filings)")
    w("")
    w("Agencies with ≥1 inventory entry linked to each frontier product, via")
    w("the curated products graph (`entry_product_edges`, both entry types).")
    w("Stage mix covers INDIVIDUAL entries only — Appendix-B consolidated")
    w("entries carry no stage. ⚠ Only ~35% of use cases name a linkable")
    w("product: these are floors (\"agencies that filed named usage\"), never")
    w("totals. Do NOT read column sums as adoption shares.")
    w("")
    frontier = (
        "Microsoft 365 Copilot", "Microsoft 365 Copilot Chat", "ChatGPT",
        "OpenAI API", "Azure OpenAI", "Claude", "Gemini", "GitHub Copilot",
        "AWS Bedrock", "Perplexity",
    )
    ph = ",".join("?" for _ in frontier)
    w("| product | agencies | entries (edges) | deployed | pilot | pre-dep | other/unk |")
    w("|---|---|---|---|---|---|---|")
    for r in q(
        f"""SELECT p.canonical_name,
               COUNT(DISTINCT e.agency_id)                    AS agencies,
               COUNT(*)                                       AS edges,
               SUM(CASE WHEN u.stage_normalized='deployed' THEN 1 ELSE 0 END),
               SUM(CASE WHEN u.stage_normalized='pilot' THEN 1 ELSE 0 END),
               SUM(CASE WHEN u.stage_normalized='pre_deployment' THEN 1 ELSE 0 END),
               SUM(CASE WHEN e.entry_kind='use_case'
                         AND COALESCE(u.stage_normalized,'')
                             NOT IN ('deployed','pilot','pre_deployment')
                        THEN 1 ELSE 0 END)
          FROM entry_product_edges e
          JOIN products p ON p.id = e.product_id
          LEFT JOIN use_cases u
            ON e.entry_kind = 'use_case' AND u.id = e.entry_id
         WHERE p.canonical_name IN ({ph})
         GROUP BY p.canonical_name
         ORDER BY agencies DESC, p.canonical_name""",
        *frontier,
    ):
        w(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} |")
    w("")
    w("- ⚠ Consolidated (Appendix-B) edges appear in `entries` but not in the")
    w("  stage columns; the stage columns sum to the individual-entry share.")
    w("- ⚠ Product names are canonical: `AWS Bedrock` (not \"Amazon Bedrock\"),")
    w("  `Claude` excludes `Claude Code` (separate product; see §2).")
    w("")

    # --------------------------------------------------------------- pillar 2
    w("## 2. Pillar — coding assistance: present but mostly pre-deployment")
    w("")
    sql_coding = """SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE is_coding_tool = 1 AND use_case_id IS NOT NULL"""
    fact("Coding-assistant use cases, individual filings (2025)", q1(sql_coding), sql_coding,
         ["Row-by-row audited (audit/retag/coding/, round2). Excludes Appendix-B "
          "template checkboxes — see Guardrails."])

    sql_coding_cons = """SELECT COUNT(DISTINCT consolidated_use_case_id) FROM use_case_tags
 WHERE is_coding_tool = 1 AND consolidated_use_case_id IS NOT NULL"""
    fact("Coding-related Appendix-B template entries (2025)", q1(sql_coding_cons), sql_coding_cons,
         ["These are agencies checking the 'Generating code using AI' template "
          "line — mostly M365 Copilot's incidental code-chat. NOT managed "
          "coding-tool deployments."])

    # Flagship article claim, pinned by audit/checks/check_article_guardrails
    # .py::test_claude_code_appears_exactly_once. raw_json carries every
    # source column verbatim, so scanning it + the narrative columns is a
    # full-row scan.
    sql_claude_code = """SELECT
  (SELECT COUNT(*) FROM use_cases WHERE lower(
     COALESCE(use_case_name,'') || ' ' || COALESCE(problem_statement,'') || ' ' ||
     COALESCE(expected_benefits,'') || ' ' || COALESCE(system_outputs,'') || ' ' ||
     COALESCE(system_name,'') || ' ' || COALESCE(vendor_name,'') || ' ' ||
     COALESCE(raw_json,'')) LIKE '%claude code%')
+ (SELECT COUNT(*) FROM consolidated_use_cases WHERE lower(
     COALESCE(ai_use_case,'') || ' ' || COALESCE(commercial_product,'') || ' ' ||
     COALESCE(commercial_examples,'') || ' ' || COALESCE(raw_json,'')) LIKE '%claude code%')"""
    n_claude_any = q1("""SELECT COUNT(*) FROM use_cases WHERE lower(
     COALESCE(use_case_name,'') || ' ' || COALESCE(problem_statement,'') || ' ' ||
     COALESCE(expected_benefits,'') || ' ' || COALESCE(system_outputs,'') || ' ' ||
     COALESCE(system_name,'') || ' ' || COALESCE(vendor_name,'')) LIKE '%claude%'""")
    fact("'Claude Code' mentions across the whole corpus (2025)",
         q1(sql_claude_code), sql_claude_code,
         ["The single hit is DOI's Appendix-B 'Generating code using AI.' "
          "template row (commercial_product field) — a checkbox listing, not "
          "a managed deployment (guardrail 5). Pinned by "
          "check_article_guardrails.py; a source reload that moves it fails "
          "`make check`.",
          f"{n_claude_any} individual use cases mention 'Claude' in any form "
          "— see claims_review_2026-07-06.md §1 for the list; date-stamp all "
          "Claude framings against the 2026-02-27 Anthropic cease-use "
          "directive (guardrail 6)."])

    # 2026-07 coding taxonomy round (Sonnet-labeled, Fable-audited, gate
    # GREEN — audit/retag/coding_taxonomy_2026-07/AUDIT_GATE.md). Pinned by
    # audit/checks/check_labeled_depth.py.
    w("Coding-tool taxonomy of the individual filings (IFP-labeled, adjudicated 2026-07):")
    w("")
    w("| coding_tool_type | n |")
    w("|---|---|")
    for r in q("""SELECT coding_tool_type, COUNT(DISTINCT use_case_id)
  FROM use_case_tags
 WHERE coding_tool_type IS NOT NULL AND use_case_id IS NOT NULL
 GROUP BY 1 ORDER BY 2 DESC"""):
        w(f"| {r[0]} | {r[1]} |")
    w("")
    n_agent_live = q1("""SELECT COUNT(*)
  FROM use_case_tags t JOIN use_cases u ON u.id = t.use_case_id
 WHERE t.coding_tool_type = 'coding_agent'
   AND u.stage_normalized IN ('deployed','pilot')""")
    sql_agent = """SELECT a.abbreviation, u.use_case_name, u.stage_normalized
  FROM use_case_tags t
  JOIN use_cases u ON u.id = t.use_case_id
  JOIN agencies a ON a.id = u.agency_id
 WHERE t.coding_tool_type = 'coding_agent'"""
    agent_rows = q(sql_agent)
    fact(
        "Deployed or piloted AGENTIC coding tools (2025)",
        n_agent_live,
        sql_agent,
        [
            "The "
            + str(len(agent_rows))
            + " agent-class filings ("
            + "; ".join(f"{r[0]} {r[1]} [{r[2]}]" for r in agent_rows)
            + ") are ALL pre-deployment — zero live agentic coding tools in "
            "the 2025 inventory. Pair with the single Claude Code mention "
            "(above) for the 'next wave is missing' claim.",
            "IFP-labeled taxonomy (closed vocab, Sonnet label -> Fable audit "
            "-> gate GREEN); 'unclear' rows (9) are thin narratives, not "
            "hidden agents — see the round's AUDIT_GATE.md.",
        ],
    )

    sql_coding24 = """SELECT COUNT(*) FROM use_case_tags_2024_canonical
 WHERE is_coding_tool = 1"""
    fact("Coding-assistant use cases (2024)", q1(sql_coding24), sql_coding24)

    w("Stage mix of 2025 individual coding filings:")
    w("")
    w("| stage | n |")
    w("|---|---|")
    for r in q(f"""SELECT {STAGE_BUCKET} s, COUNT(DISTINCT u.id)
  FROM use_cases u JOIN use_case_tags t ON t.use_case_id = u.id
 WHERE t.is_coding_tool = 1
 GROUP BY s ORDER BY 2 DESC"""):
        w(f"| {r[0]} | {r[1]} |")
    w("")
    w("Named coding deployments by agency (2025 individual filings):")
    w("")
    w("| agency | n | examples |")
    w("|---|---|---|")
    for r in q(f"""SELECT a.abbreviation, COUNT(DISTINCT u.id),
       GROUP_CONCAT(DISTINCT COALESCE(NULLIF(t.tool_product_name,''),'(unnamed)'))
  FROM use_cases u
  JOIN agencies a ON a.id = u.agency_id
  JOIN use_case_tags t ON t.use_case_id = u.id
 WHERE t.is_coding_tool = 1
 GROUP BY a.abbreviation ORDER BY 2 DESC"""):
        tools = (r[2] or "")[:90]
        w(f"| {r[0]} | {r[1]} | {tools} |")
    w("")

    # --------------------------------------------------------------- pillar 3
    w("## 3. Pillar — advanced data analytics: federated and opaque")
    w("")
    w("The inventory format cannot answer 'can an analyst use AI on real")
    w("agency data?' from row counts — platforms appear inconsistently in")
    w("system_name/vendor/narrative. The citable artifact is the per-agency")
    w("Strong/Moderate/Limited rating table in")
    w("`audit/retag/data_analysis/by_agency.md` (web-corroborated, with")
    w("evidence URLs). DB-side supporting facts:")
    w("")
    sql_env = """SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE deployment_environment IS NOT NULL AND deployment_environment != ''
   AND deployment_environment != 'unknown' AND use_case_id IS NOT NULL"""
    fact("Rows with a known deployment environment", q1(sql_env), sql_env,
         ["deployment_environment was 'unknown' on ~100% of rows before the "
          "audit backfill; it is only filled where an agent verified a "
          "platform. NEVER cite environment shares of the whole corpus."])
    sql_arch = """SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE (architecture_type IS NULL OR architecture_type IN ('','unknown'))
   AND use_case_id IS NOT NULL"""
    fact("Rows with UNKNOWN architecture_type", q1(sql_arch), sql_arch,
         ["Do not cite architecture_type distributions as corpus-level facts."])

    # -------------------------------------------- pillar 3b: integration depth
    # 2026-07 integration-depth round (Sonnet-labeled, Fable-audited, gate
    # GREEN — audit/retag/integration_depth_2026-07/AUDIT_GATE.md; 22.5%
    # audited, 26 overrides). Pinned by audit/checks/check_labeled_depth.py.
    w("## 3b. Integration depth — measured (IFP-labeled, adjudicated 2026-07)")
    w("")
    w("How deeply each PILOT or DEPLOYED individual use case is wired into")
    w("agency work, labeled over the narratives (the measurement the OMB")
    w("format does not collect). Ladder: standalone_chat < workflow_embedded")
    w("< system_integrated < agentic_workflow.")
    w("")
    w("| integration_depth | all P+D | GenAI | non-GenAI |")
    w("|---|---|---|---|")
    depth_rows = q("""SELECT t.integration_depth,
       COUNT(DISTINCT t.use_case_id),
       COUNT(DISTINCT CASE WHEN t.is_generative_ai=1 THEN t.use_case_id END),
       COUNT(DISTINCT CASE WHEN COALESCE(t.is_generative_ai,0)=0 THEN t.use_case_id END)
  FROM use_case_tags t JOIN use_cases u ON u.id = t.use_case_id
 WHERE t.integration_depth IS NOT NULL
   AND u.stage_normalized IN ('pilot','deployed')
 GROUP BY 1
 ORDER BY CASE t.integration_depth
   WHEN 'standalone_chat' THEN 1 WHEN 'workflow_embedded' THEN 2
   WHEN 'system_integrated' THEN 3 WHEN 'agentic_workflow' THEN 4 ELSE 5 END""")
    for r in depth_rows:
        w(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |")
    tot = sum(r[1] for r in depth_rows)
    genai_tot = sum(r[2] for r in depth_rows)
    d = {r[0]: r for r in depth_rows}
    w("")
    w(f"**{tot}** labeled pilot/deployed rows ({genai_tot} GenAI). Headlines:")
    ga_stand = d.get("standalone_chat", (0, 0, 0, 0))
    ga_sys = d.get("system_integrated", (0, 0, 0, 0))
    ga_agent = d.get("agentic_workflow", (0, 0, 0, 0))
    w(f"- GenAI in operation is mostly UNcoupled: {ga_stand[2]}/{genai_tot} "
      f"(~{ga_stand[2]/genai_tot:.0%}) standalone chat vs {ga_sys[2]}/{genai_tot} "
      f"(~{ga_sys[2]/genai_tot:.0%}) integrated with agency systems.")
    w(f"- The integrated AI estate is pre-GenAI: {ga_sys[3]} of {ga_sys[1]} "
      "system_integrated rows are classical/predictive systems.")
    w(f"- Agentic workflows in live operation: {ga_agent[1]} total "
      f"({ga_agent[1]/tot:.1%}), of which GenAI-based: {ga_agent[2]} "
      "(HHS 'Deep Research for Public Health', pilot).")
    w("")
    w("- ⚠ IFP-labeled adjudicated round (Sonnet label → Fable audit → gate")
    w("  GREEN; 100% of low-confidence + 100% of agentic verdicts audited).")
    w("  Labels reflect what narratives DESCRIBE as operating — floors, not")
    w("  ground truth about undescribed couplings.")
    w("- ⚠ One DOI row with a blank use_case_name is unlabeled (signature")
    w("  unresolvable); population is otherwise 1,573/1,573 covered.")
    w("- ⚠ integration_depth='agentic_workflow' (behavior-based) is NOT the")
    w("  same axis as ai_sophistication='agentic' (66, capability-based) —")
    w("  overlap is partial by design; do not conflate the two counts.")
    w("")

    # --------------------------------------------------------------- agentic
    w("## 4. Agentic AI")
    w("")
    sql_agentic = """SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE ai_sophistication = 'agentic' AND use_case_id IS NOT NULL"""
    sql_agentic_omb = """SELECT COUNT(*) FROM use_cases
 WHERE ai_classification LIKE '%Agentic%'"""
    fact("Agentic by IFP tag (2025, post-review)", q1(sql_agentic), sql_agentic,
         ["Keyword over-tagging was re-adjudicated row-by-row in "
          "audit/retag/agentic_review/ — cite this number only after that "
          "apply pass has run (check the directory exists and "
          "scripts/apply_agentic_review.py ran in make fix)."])
    fact("Agentic by OMB's own classification (2025)", q1(sql_agentic_omb), sql_agentic_omb,
         ["Agencies' own label. Use as the conservative anchor."])

    # ------------------------------------------------------------ cross-year
    w("## 5. Cross-year capacity (2024 → 2025)")
    w("")
    sql_dep_genai = f"""SELECT COUNT(DISTINCT u.id)
  FROM use_cases u JOIN use_case_tags t ON t.use_case_id = u.id
 WHERE t.is_generative_ai = 1 AND {STAGE_BUCKET} = 'deployed'"""
    sql_dep_genai24 = f"""SELECT COUNT(DISTINCT u.id)
  FROM use_cases_2024 u
  JOIN use_case_tags_2024_canonical t ON t.use_case_id_2024 = u.id
 WHERE t.is_generative_ai = 1 AND {STAGE_BUCKET_2024} = 'deployed'"""
    dep25, dep24 = q1(sql_dep_genai), q1(sql_dep_genai24)
    fact(f"Deployed GenAI use cases: {dep24} (2024) → {dep25} (2025)",
         f"{dep24} → {dep25}", sql_dep_genai24 + ";\n-- 2025:\n" + sql_dep_genai,
         ["Stage buckets normalize ~40 free-text variants; see the CASE in this script."])

    sql_new = """SELECT COUNT(DISTINCT l.uc_2025_id)
  FROM use_case_year_links l
  JOIN use_case_tags t ON t.use_case_id = l.uc_2025_id
 WHERE l.lineage_status = 'new_2025' AND t.is_generative_ai = 1"""
    fact("Net-new GenAI capabilities introduced in 2025", q1(sql_new), sql_new)

    sql_dropped = """SELECT COUNT(DISTINCT l.uc_2024_id)
  FROM use_case_year_links l
  JOIN use_case_tags_2024_canonical t ON t.use_case_id_2024 = l.uc_2024_id
  JOIN use_cases_2024 u ON u.id = l.uc_2024_id
 WHERE l.lineage_status = 'retired_2024' AND t.is_generative_ai = 1
   AND (LOWER(COALESCE(u.dev_stage,'')) LIKE '%operation%'
        OR LOWER(COALESCE(u.dev_stage,'')) LIKE '%implementation%')"""
    fact("Live-in-2024 GenAI filings absent from the 2025 inventory", q1(sql_dropped), sql_dropped,
         ["'Silently dropped' = no Retired trace in 2025. Several agencies "
          "(ED above all) filed many task-level entries under one repeated "
          "name; cite the distinct-name count from /compare-years/silently-dropped, "
          "not raw filings."])

    # ------------------------------------- pillar 5b: bureau-level divergence
    w("## 5b. Bureau-level divergence — enterprise access is decided below the department")
    w("")
    w("Within-department spread of bureau-scored maturity (`org_ai_maturity`")
    w("rows at sub_agency/office level, ≥5 use cases to be scored; one-hop")
    w("parent rollup). The unit of adoption choice is the bureau: HHS is a")
    w("federation where nearly every scored operating division independently")
    w("meets enterprise-LLM; DOJ's bureaus uniformly do not; DOE is bimodal")
    w("across its labs.")
    w("")
    w("| dept | bureaus scored | w/ enterprise LLM | w/ coding assistants | enterprise-LLM bureaus |")
    w("|---|---|---|---|---|")
    for r in q(
        """SELECT parent.abbreviation,
                  COUNT(*),
                  SUM(m.has_enterprise_llm),
                  SUM(m.has_coding_assistants),
                  COALESCE(GROUP_CONCAT(CASE WHEN m.has_enterprise_llm=1
                                             THEN fo.abbreviation END), '—')
             FROM org_ai_maturity m
             JOIN federal_organizations fo ON fo.id = m.organization_id
             JOIN federal_organizations parent ON parent.id = fo.parent_id
            WHERE fo.level IN ('sub_agency','office')
            GROUP BY parent.abbreviation
           HAVING COUNT(*) >= 3
            ORDER BY COUNT(*) DESC"""
    ):
        w(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |")
    w("")
    w("- ⚠ Scored-bureau counts are floors — bureaus under 5 filed use cases")
    w("  aren't scored; absence from the table is not evidence of absence.")
    w("- ⚠ For SPECIFIC bureau capability claims (VA/OIT triple-strong; HHS")
    w("  8-of-11 opdivs independently Enterprise; Treasury OCC.Chat; DOJ's")
    w("  dept-wide Copilot being pre-deployment/uncorroborated), cite the")
    w("  round-3 web-corroborated ratings: `audit/retag/round3/")
    w("  SUB_AGENCY_FINDINGS.md` + `<topic>/sub_agency_rows.csv` (96")
    w("  sub-agencies × 3 topics, evidence quotes + URLs) — not this table.")
    w("- ⚠ Bureau workforce shares: `agency_workforce_profile` level='bureau'")
    w("  (64 rows) — needed before converting bureau counts to people-terms.")
    w("")

    # ------------------------------------------------------------ guardrails
    w("## 6. Guardrails — claims the data cannot support")
    w("")
    w("(Enforced where machine-checkable by `audit/checks/`; full list in")
    w("`audit/retag/TODO.md` §3.)")
    w("")
    w("1. `agency_ai_maturity.has_enterprise_llm` — RESOLVED 2026-07-06: cured")
    w("   upstream (individual-rows-only rule, scope corrections, omb_only")
    w("   ingest; audit/retag/TODO.md §3). Safe to cite as \"enterprise-wide")
    w("   general-LLM access, individually-filed evidence\". One definitional")
    w("   split remains: PBGC has enterprise general-LLM access but no")
    w("   GenAI-flagged enterprise row; FERC the reverse.")
    w("2. Do NOT credit GSA USAi.gov as a data-analysis environment — it is a")
    w("   chat/model-evaluation sandbox.")
    w("3. Do NOT infer broad analyst access from a Palantir contract (DHS $1B")
    w("   BPA, USDA $300M are narrow operational platforms).")
    w("4. Do NOT assert a financial regulator (SEC, FRB, FDIC, NCUA, CFTC)")
    w("   lacks an analytic platform — the inventory just doesn't surface it.")
    w("5. Do NOT equate an Appendix-B 'Generating code using AI' checkbox with")
    w("   a managed coding-tool deployment.")
    w("6. Press-verification still owed before naming: DOJ-wide GitHub Copilot")
    w("   (no public corroboration), VA OIG Jan-2026 PHI advisory (cite with")
    w("   any VA-positive framing), Anthropic federal ban Feb-2026 (date-stamp")
    w("   HHS Claude claims), DHS commercial-AI revocation (counter-trend),")
    w("   the 'DHS/DoW have adopted Claude Code' anecdote (no public source;")
    w("   DoD/DoW filed no 2025 individual inventory, so the data cannot")
    w("   corroborate or refute it), and the 'decade compressed into two")
    w("   years' adoption-speed comparison (needs an external historical")
    w("   baseline — cloud/PC/email federal adoption curves).")
    w("")

    # Preserve hand-authored trailing sections (## 7. onward — the FedRAMP
    # beats added in 6216de3 are not machine-generated; regenerating the
    # sheet must never destroy them).
    preserved = ""
    if OUT.exists():
        current = OUT.read_text()
        marker = current.find("\n## 7.")
        if marker != -1:
            preserved = current[marker:]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + preserved)
    n_lines = len(lines) + preserved.count("\n")
    suffix = " (+ preserved hand-authored §7+)" if preserved else ""
    print(f"wrote {OUT} ({n_lines} lines{suffix})")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
