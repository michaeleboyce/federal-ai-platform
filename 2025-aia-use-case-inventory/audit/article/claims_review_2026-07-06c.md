# Claims review — 2026-07-06 (c): measured-evidence wave

Third same-day wave (a = morning claim verification, b = scout research).
This one records the NEW MEASUREMENTS built today — two adjudicated
labeling rounds plus two fact-base tables — and where each is pinned.
All numbers as of the 2026-07-06 rebuild (make fix green twice).

## 1. Integration depth — the OMB-missing measurement, now measured

Round: `audit/retag/integration_depth_2026-07/` (gate GREEN; 1,573
pilot+deployed rows; 14 Sonnet batches; Fable audit 22.5% incl. 100% of
low-confidence and 100% of agentic verdicts; 5 batches relabeled under
amendments; 26 overrides). Citable facts (fact_sheet §3b; pinned by
`check_labeled_depth.py`):

- Of 1,572 labeled live rows: workflow_embedded 703 · system_integrated
  564 · standalone_chat 227 · unclear 64 · agentic_workflow 14.
- **The contrast**: operating GenAI is mostly uncoupled — 42% standalone
  chat, 14% system-integrated (of 478 GenAI rows) — while the integrated
  estate is pre-GenAI (498/564 system_integrated rows are classical).
- **Exactly one live GenAI agentic workflow** government-wide: HHS
  "Deep Research for Public Health" (pilot).
  - **AMENDED 2026-07-10**: now TWO. User adjudication flipped HHS
    "AI Agent Orchestrator POC" (pilot) to `is_generative_ai=1`
    (LLM-driven orchestration of data-science workflows; override in
    `audit/retag/llm_flag_drift_2026-07/audit_overrides.csv`). GenAI
    P+D total 478 → 479; agentic_workflow split now 2 GenAI / 12
    non-GenAI. Do not cite "exactly one" — say "two, both HHS pilots".
- ⚠ IFP-labeled; narratives-as-described (floors); one DOI blank-name
  row unlabeled; don't conflate with `ai_sophistication='agentic'` (66).

Reform-section framing this unlocks: IFP measured in a day, from OMB's
own filings, what the inventory format doesn't ask — the working
prototype of the integration reporting item the article recommends.

## 2. Coding-tool taxonomy — the "next wave" quantified

Round: `audit/retag/coding_taxonomy_2026-07/` (gate GREEN; 70 rows;
batch 1 relabeled after a 22% systemic override rate on 'unclear'
over-use — the audit-rerun loop working as designed). Citable
(fact_sheet §2; pinned):

- 70 coding filings = chat_assistant 25 · ide_autocomplete 18 ·
  code_analysis_tool 14 · unclear 9 · coding_agent 4.
- **All 4 agent-class filings are pre-deployment** (SBA ×3, SSA
  Windsurf): **zero deployed or piloted agentic coding tools in the
  entire 2025 inventory.** Pair with the single Claude Code mention.

## 3. Frontier-product penetration (fact_sheet §1b; pinned)

M365 Copilot 41 agencies · ChatGPT 19 · GitHub Copilot 19 · Gemini 16 ·
Azure OpenAI 15 · OpenAI API 15 · Claude 11 · AWS Bedrock 9 · M365
Copilot Chat 9 · Perplexity 6. ⚠ Floors (only ~35% of rows name a
linkable product); stage mix individual-entries-only.

## 4. Bureau-level divergence (fact_sheet §5b)

HHS 8/8 scored opdivs independently enterprise-LLM · DOJ 0/14 · DOE
2/18 (bimodal labs) · VA only OIT · ED 5/5. For specific bureau claims
cite the round-3 web-corroborated ratings, not the maturity table.

## 5. Access-stat derivation (access_derivation.md)

747,141 AI-eligible of 1,508,837 covered headcount (56 agencies);
~282K (~38%) with evidenced access; unassessed agencies hold only ~4%
of the eligible base. The 2.31M FedScope total is ONLY for the DoD
blind-spot share (~⅓).
