# Article fact sheet — 2025 Federal AI Use Case Inventory (IFP tags)

_Generated: 2026-06-09 by `scripts/build_article_factsheet.py`. Re-run after any `make fix`._

Every number below is produced by the SQL shown with it, against
`data/federal_ai_inventory_2025.db`. Caveats marked ⚠ MUST travel with
the number into the article. See §Guardrails for claims the data
cannot support.

## 0. Scale

### Individually reported 2025 use cases

**3549**

```sql
SELECT COUNT(*) FROM use_cases
```
- ⚠ Excludes the 900 Appendix-B consolidated template entries (counted separately).

### 2024 use cases (M-24-10 corpus)

**2133**

```sql
SELECT COUNT(*) FROM use_cases_2024
```

## 1. Pillar — chatbots / assistants arrived broadly

### GenAI by OMB's own classification (2025)

**852**

```sql
SELECT COUNT(*) FROM use_cases
 WHERE ai_classification LIKE '%Generative%'
```
- ⚠ OMB's `ai_classification` field as filed by agencies; 600+ rows left it blank.

### GenAI by IFP tag (2025)

**969**

```sql
SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE is_generative_ai = 1 AND use_case_id IS NOT NULL
```

### GenAI by IFP tag (2024)

**527**

```sql
SELECT COUNT(*) FROM use_case_tags_2024_canonical
 WHERE is_generative_ai = 1
```
- ⚠ 2024 tags are agent-tagged + verified (93.9% sampled accuracy on this flag).

### General-purpose LLM access entries (2025)

**803**

```sql
SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE is_general_llm_access = 1 AND use_case_id IS NOT NULL
```
- ⚠ Definition: staff can submit arbitrary prompts, internal-work approved, broadly available — not single-workflow integrations. Low-confidence heuristic flips were re-adjudicated row-by-row in audit/retag/general_llm_round3/.

### Agencies with enterprise-wide GenAI: 15 (2024) → 21 (2025)

**15 → 21**

```sql
SELECT COUNT(DISTINCT u.agency_id)
  FROM use_cases u JOIN use_case_tags t ON t.use_case_id = u.id
 WHERE t.is_generative_ai = 1 AND t.is_enterprise_wide = 1;
-- 2024:
SELECT COUNT(DISTINCT u.agency_id)
  FROM use_cases_2024 u
  JOIN use_case_tags_2024_canonical t ON t.use_case_id_2024 = u.id
 WHERE t.is_generative_ai = 1 AND t.is_enterprise_wide = 1
```
- ⚠ The 2025 figure includes the web-verified scope corrections (StateChat, VA GPT, DHSChat, Ask Dottie...) restored by apply_retag_audit.py. Earlier drafts said 15→12; that was an artifact of the corrections not being applied — do not reuse it.
- ⚠ Tag-row counts (not agency counts) concentrate heavily in HHS; always pair a row count with the agency count.

Enterprise-wide GenAI agencies (2025): DHS, DOC, DOE, DOJ, DOT, ED, FERC, FRTIB, FTC, GSA, HHS, HUD, NARA, NASA, NRC, NTSB, OPM, SEC, SSA, State, VA

## 2. Pillar — coding assistance: present but mostly pre-deployment

### Coding-assistant use cases, individual filings (2025)

**57**

```sql
SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE is_coding_tool = 1 AND use_case_id IS NOT NULL
```
- ⚠ Row-by-row audited (audit/retag/coding/, round2). Excludes Appendix-B template checkboxes — see Guardrails.

### Coding-related Appendix-B template entries (2025)

**19**

```sql
SELECT COUNT(DISTINCT consolidated_use_case_id) FROM use_case_tags
 WHERE is_coding_tool = 1 AND consolidated_use_case_id IS NOT NULL
```
- ⚠ These are agencies checking the 'Generating code using AI' template line — mostly M365 Copilot's incidental code-chat. NOT managed coding-tool deployments.

### Coding-assistant use cases (2024)

**31**

```sql
SELECT COUNT(*) FROM use_case_tags_2024_canonical
 WHERE is_coding_tool = 1
```

Stage mix of 2025 individual coding filings:

| stage | n |
|---|---|
| pre_deployment | 21 |
| deployed | 14 |
| unknown | 10 |
| pilot | 9 |
| retired | 3 |

Named coding deployments by agency (2025 individual filings):

| agency | n | examples |
|---|---|---|
| HHS | 10 | Microsoft Teams,(unnamed),ServiceNow Now Assist,GitHub Copilot,Tableau,OpenAI API,Palantir |
| DOC | 9 | GitHub Copilot,(unnamed),Gemini,Amazon Q,unspecified |
| DOE | 7 | GitHub Copilot,Microsoft Teams,unspecified,Gemini,Tabnine |
| Treasury | 6 | unspecified,Microsoft Teams,(unnamed) |
| DHS | 6 | Custom GenAI coding assistant,Custom code-generation tool,(unnamed),OpenAI API,Palantir AI |
| SSA | 3 | AveriSource Platform,Windsurf,IBM watsonx Code Assistant |
| VA | 2 | Microsoft Teams |
| SBA | 2 | Amazon Q,AWS Bedrock |
| NASA | 2 | Custom LLM (planned),Custom (VS plugin) |
| ED | 2 | OpenAI API,Microsoft 365 Copilot |
| DOJ | 2 | GitHub Copilot,unspecified |
| DOI | 2 | ChatGPT,GitHub Copilot |
| TVA | 1 | GitHub Copilot |
| State | 1 | unspecified |
| NSF | 1 | Amazon CodeWhisperer |
| DOT | 1 | (unnamed) |

## 3. Pillar — advanced data analytics: federated and opaque

The inventory format cannot answer 'can an analyst use AI on real
agency data?' from row counts — platforms appear inconsistently in
system_name/vendor/narrative. The citable artifact is the per-agency
Strong/Moderate/Limited rating table in
`audit/retag/data_analysis/by_agency.md` (web-corroborated, with
evidence URLs). DB-side supporting facts:

### Rows with a known deployment environment

**85**

```sql
SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE deployment_environment IS NOT NULL AND deployment_environment != ''
   AND deployment_environment != 'unknown' AND use_case_id IS NOT NULL
```
- ⚠ deployment_environment was 'unknown' on ~100% of rows before the audit backfill; it is only filled where an agent verified a platform. NEVER cite environment shares of the whole corpus.

### Rows with UNKNOWN architecture_type

**2440**

```sql
SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE (architecture_type IS NULL OR architecture_type IN ('','unknown'))
   AND use_case_id IS NOT NULL
```
- ⚠ Do not cite architecture_type distributions as corpus-level facts.

## 4. Agentic AI

### Agentic by IFP tag (2025, post-review)

**59**

```sql
SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE ai_sophistication = 'agentic' AND use_case_id IS NOT NULL
```
- ⚠ Keyword over-tagging was re-adjudicated row-by-row in audit/retag/agentic_review/ — cite this number only after that apply pass has run (check the directory exists and scripts/apply_agentic_review.py ran in make fix).

### Agentic by OMB's own classification (2025)

**115**

```sql
SELECT COUNT(*) FROM use_cases
 WHERE ai_classification LIKE '%Agentic%'
```
- ⚠ Agencies' own label. Use as the conservative anchor.

## 5. Cross-year capacity (2024 → 2025)

### Deployed GenAI use cases: 200 (2024) → 322 (2025)

**200 → 322**

```sql
SELECT COUNT(DISTINCT u.id)
  FROM use_cases_2024 u
  JOIN use_case_tags_2024_canonical t ON t.use_case_id_2024 = u.id
 WHERE t.is_generative_ai = 1 AND 
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
 = 'deployed';
-- 2025:
SELECT COUNT(DISTINCT u.id)
  FROM use_cases u JOIN use_case_tags t ON t.use_case_id = u.id
 WHERE t.is_generative_ai = 1 AND u.stage_normalized = 'deployed'
```
- ⚠ Stage buckets normalize ~40 free-text variants; see the CASE in this script.

### Net-new GenAI capabilities introduced in 2025

**643**

```sql
SELECT COUNT(DISTINCT l.uc_2025_id)
  FROM use_case_year_links l
  JOIN use_case_tags t ON t.use_case_id = l.uc_2025_id
 WHERE l.lineage_status = 'new_2025' AND t.is_generative_ai = 1
```

### Live-in-2024 GenAI filings absent from the 2025 inventory

**144**

```sql
SELECT COUNT(DISTINCT l.uc_2024_id)
  FROM use_case_year_links l
  JOIN use_case_tags_2024_canonical t ON t.use_case_id_2024 = l.uc_2024_id
  JOIN use_cases_2024 u ON u.id = l.uc_2024_id
 WHERE l.lineage_status = 'retired_2024' AND t.is_generative_ai = 1
   AND (LOWER(COALESCE(u.dev_stage,'')) LIKE '%operation%'
        OR LOWER(COALESCE(u.dev_stage,'')) LIKE '%implementation%')
```
- ⚠ 'Silently dropped' = no Retired trace in 2025. Several agencies (ED above all) filed many task-level entries under one repeated name; cite the distinct-name count from /compare-years/silently-dropped, not raw filings.

## 6. Guardrails — claims the data cannot support

(Enforced where machine-checkable by `audit/checks/`; full list in
`audit/retag/TODO.md` §3.)

1. Do NOT cite `agency_ai_maturity.has_enterprise_llm` — wrong in both
   directions (false positives from Appendix-B checkboxes; false
   negatives for State, VA, DOJ, DOI, DOT).
2. Do NOT credit GSA USAi.gov as a data-analysis environment — it is a
   chat/model-evaluation sandbox.
3. Do NOT infer broad analyst access from a Palantir contract (DHS $1B
   BPA, USDA $300M are narrow operational platforms).
4. Do NOT assert a financial regulator (SEC, FRB, FDIC, NCUA, CFTC)
   lacks an analytic platform — the inventory just doesn't surface it.
5. Do NOT equate an Appendix-B 'Generating code using AI' checkbox with
   a managed coding-tool deployment.
6. Press-verification still owed before naming: DOJ-wide GitHub Copilot
   (no public corroboration), VA OIG Jan-2026 PHI advisory (cite with
   any VA-positive framing), Anthropic federal ban Feb-2026 (date-stamp
   HHS Claude claims), DHS commercial-AI revocation (counter-trend).
