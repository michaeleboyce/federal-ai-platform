# Article fact sheet — 2025 Federal AI Use Case Inventory (IFP tags)

_Generated: 2026-07-06 by `scripts/build_article_factsheet.py`. Re-run after any `make fix`._

Every number below is produced by the SQL shown with it, against
`data/federal_ai_inventory_2025.db`. Caveats marked ⚠ MUST travel with
the number into the article. See §Guardrails for claims the data
cannot support.

## 0. Scale

### Individually reported 2025 use cases

**3660**

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

**933**

```sql
SELECT COUNT(*) FROM use_cases
 WHERE ai_classification LIKE '%Generative%'
```
- ⚠ OMB's `ai_classification` field as filed by agencies; 600+ rows left it blank.

### GenAI by IFP tag (2025)

**1005**

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

**559**

```sql
SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE is_general_llm_access = 1 AND use_case_id IS NOT NULL
```
- ⚠ Definition: staff can submit arbitrary prompts, internal-work approved, broadly available — not single-workflow integrations. Low-confidence heuristic flips were re-adjudicated row-by-row in audit/retag/general_llm_round3/.

### Agencies with enterprise-wide GenAI: 21 (2024) → 24 (2025)

**21 → 24**

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

Enterprise-wide GenAI agencies (2025): DHS, DOC, DOE, DOJ, DOT, EAC, ED, FDIC, FERC, FRTIB, FTC, GSA, HHS, HUD, NARA, NASA, NEA, NRC, OPM, OSC, OSHRC, SSA, State, VA

## 2. Pillar — coding assistance: present but mostly pre-deployment

### Coding-assistant use cases, individual filings (2025)

**70**

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
| deployed | 26 |
| pre_deployment | 22 |
| unknown | 10 |
| pilot | 9 |
| retired | 3 |

Named coding deployments by agency (2025 individual filings):

| agency | n | examples |
|---|---|---|
| ED | 13 | OpenAI API,Microsoft 365 Copilot |
| HHS | 10 | Microsoft Teams,(unnamed),ServiceNow Now Assist,GitHub Copilot,Tableau,OpenAI API,Palantir |
| DOC | 9 | GitHub Copilot,(unnamed),Gemini,Amazon Q,unspecified |
| DOE | 8 | GitHub Copilot,Microsoft Teams,unspecified,Gemini,Tabnine |
| Treasury | 6 | unspecified,Microsoft Teams,(unnamed) |
| DHS | 6 | Custom GenAI coding assistant,Custom code-generation tool,(unnamed),OpenAI API,Palantir AI |
| SSA | 3 | AveriSource Platform,Windsurf,IBM watsonx Code Assistant |
| SBA | 3 | Amazon Q,GitHub Copilot,AWS Bedrock |
| VA | 2 | Microsoft Teams |
| NASA | 2 | Custom LLM (planned),Custom (VS plugin) |
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

**2606**

```sql
SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE (architecture_type IS NULL OR architecture_type IN ('','unknown'))
   AND use_case_id IS NOT NULL
```
- ⚠ Do not cite architecture_type distributions as corpus-level facts.

## 4. Agentic AI

### Agentic by IFP tag (2025, post-review)

**66**

```sql
SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
 WHERE ai_sophistication = 'agentic' AND use_case_id IS NOT NULL
```
- ⚠ Keyword over-tagging was re-adjudicated row-by-row in audit/retag/agentic_review/ — cite this number only after that apply pass has run (check the directory exists and scripts/apply_agentic_review.py ran in make fix).

### Agentic by OMB's own classification (2025)

**117**

```sql
SELECT COUNT(*) FROM use_cases
 WHERE ai_classification LIKE '%Agentic%'
```
- ⚠ Agencies' own label. Use as the conservative anchor.

## 5. Cross-year capacity (2024 → 2025)

### Deployed GenAI use cases: 200 (2024) → 311 (2025)

**200 → 311**

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

**699**

```sql
SELECT COUNT(DISTINCT l.uc_2025_id)
  FROM use_case_year_links l
  JOIN use_case_tags t ON t.use_case_id = l.uc_2025_id
 WHERE l.lineage_status = 'new_2025' AND t.is_generative_ai = 1
```

### Live-in-2024 GenAI filings absent from the 2025 inventory

**93**

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

## 7. FedRAMP — authorization vs adoption

_Added 2026-07-05 (hand-verified; every figure re-run against the live DB
that day). Marketplace snapshot: **2026-06-12**; the 20x trio's fedramp.gov
listings were additionally re-checked live 2026-07-03. Numbers pinned by
`audit/checks/check_fedramp_fact_sheet.py` — a snapshot refresh that moves
them fails `make check` until this section is updated._

### Beat 1 — the shelf is stocked, nothing moves

**46 core-AI FedRAMP listings · 35 fully authorized · 26 of 35 never
spread past one agency ATO · 10 of 48 ATO'd pairs corroborated**

```sql
SELECT COUNT(*) FROM fedramp_ai_classification WHERE category='core_ai';
-- authorized + single-ATO: see check_fedramp_fact_sheet.py (distinct
-- agency_id per product; ≤1 = never spread)
```
- ⚠ "Corroborated" = the ATO-holding agency's own 2025 inventory names the
  product in ≥1 use case. Only ~35% of use cases name a linkable product,
  so write "no reported use", never "unused".
- Dashboard: /fedramp/coverage/spread §I–II.

### Beat 1b — unlinked-AI split

**203 marketplace AI products absent from every inventory = 156 fully
authorized + 47 Ready / In-Process**

- ⚠ Never cite "203 authorized" — 47 of them have not completed
  authorization (guardrail 8).
- Dashboard: /fedramp/coverage/unlinked-ai.

### Beat 2 — the 20x zeros

**ChatGPT Enterprise (Moderate, auth 2026-01-09) · Gemini for Government
(Low, 2026-01-21) · Perplexity Enterprise (Low, 2026-02-01) — each: one
program-level authorization, zero recorded agency reuses**

```sql
SELECT cso, status, auth_date, reuse_count FROM fedramp_products
 WHERE cso IN ('ChatGPT Enterprise and API Platform',
               'Gemini for Government',
               'Perplexity Enterprise and API Platform');
```
- ⚠ The 2025 inventories closed before these authorizations landed — their
  inventory absence is mechanical. The meaningful zero is the reuse ledger
  months after authorization (guardrail 11: date-stamp).
- Dashboard: /fedramp/coverage/spread §III.

### Beat 3 — adoption routed around the ledger

**OneGov: ChatGPT Enterprise $1/agency (announced 2025-08-07) · Google
stack $0.47/agency (2025-08-21) · Perplexity $0.25/agency/18mo
(2025-11-19) · USAi: 15 agencies + waitlist (2026-04), cost-recovery from
FY2027 · Anthropic: presidential cease-use directive 2026-02-27; GSA
removed it from USAi and terminated MAS listings**

- Sources: GSA newsroom releases, ExecutiveGov, Nextgov/FCW, FedScoop —
  full citations in `audit/article/fedramp_section_draft.md` footnotes
  (all URLs fetch-verified 2026-07-03/05).

### Beat 3b — the shelf inside the shelf (services in scope)

**1,591 unique in-scope services labeled (129 core_ai · 122 ai_featured ·
1,340 not_ai) · 129 core-AI services inside 34 authorized packages ·
46 agencies hold an ATO on ≥1 core-AI-bearing package · Amazon Bedrock in
scope at Moderate (AWS US East/West) AND High (AWS GovCloud)**

```sql
SELECT COUNT(*), SUM(category='core_ai') FROM fedramp_ai_service_classification;
SELECT COUNT(DISTINCT al.inventory_agency_id)
  FROM fedramp_authorized_services s
  JOIN fedramp_ai_service_classification c
    ON c.service = s.service AND c.category = 'core_ai'
  JOIN fedramp_authorizations a ON a.fedramp_id = s.fedramp_id
  JOIN fedramp_agency_links al ON al.fedramp_agency_id = a.agency_id;
```
- ⚠ Every core_ai and ai_featured label was adversarially reviewed by a
  frontier-model QC pass (`source` column ≠ 'llm'); label provenance is
  row-level auditable in `data/fedramp_service_classification.csv`.
- ⚠ Formulation: FedRAMP publishes scope down to the service but tracks
  adoption only at the package. Do NOT write "FedRAMP can't see services".
- Dashboard: /fedramp/coverage/spread §IV (#services).

### Beat 4 — capability in reach vs staff access (the payoff)

**Core-AI services in scope of packages the agency holds an ATO for,
against IFP's web-corroborated staff-access estimate:**

| Agency | Services in reach | IFP access tier (share) |
|---|---|---|
| HHS | 110 | all (~50%) |
| DOE | 99 | all (~81%) |
| Treasury | 98 | pilot (~5%) |
| State | 93 | all (~95–100%) |
| DOJ | 63 | latent (IFP assessment ~1%, not press-corroborated) |
| HUD | 41 | pilot (~0.15%) |
| SBA | 41 | none (0%) |
| VA | 31 | (see §1 enterprise list) |

- ⚠ Guardrail 7 applies to every row: "in scope of a package the agency
  holds an ATO for" — never "enabled" or "available to staff". The gap
  between the columns is the claim; causality is not.
- ⚠ DOJ's ~1% share is an IFP assessment with status `searched_no_source`
  — cite the tier, attribute the share to IFP explicitly.
- Dashboard: /fedramp/coverage/agencies §II + per-agency drills.
