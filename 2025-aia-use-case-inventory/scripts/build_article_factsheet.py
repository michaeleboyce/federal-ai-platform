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

    # ------------------------------------------------------------ guardrails
    w("## 6. Guardrails — claims the data cannot support")
    w("")
    w("(Enforced where machine-checkable by `audit/checks/`; full list in")
    w("`audit/retag/TODO.md` §3.)")
    w("")
    w("1. Do NOT cite `agency_ai_maturity.has_enterprise_llm` — wrong in both")
    w("   directions (false positives from Appendix-B checkboxes; false")
    w("   negatives for State, VA, DOJ, DOI, DOT).")
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
    w("   HHS Claude claims), DHS commercial-AI revocation (counter-trend).")
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
