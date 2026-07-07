# Article fact sheet — 2025 Federal AI Use Case Inventory (IFP tags)

_Generated: 2026-07-07 by `scripts/build_article_factsheet.py`. Re-run after any `make fix`._

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

**561**

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

## 1b. Frontier-product penetration (named-product filings)

Agencies with ≥1 inventory entry linked to each frontier product, via
the curated products graph (`entry_product_edges`, both entry types).
Stage mix covers INDIVIDUAL entries only — Appendix-B consolidated
entries carry no stage. ⚠ Only ~35% of use cases name a linkable
product: these are floors ("agencies that filed named usage"), never
totals. Do NOT read column sums as adoption shares.

| product | agencies | entries (edges) | deployed | pilot | pre-dep | other/unk |
|---|---|---|---|---|---|---|
| Microsoft 365 Copilot | 41 | 211 | 23 | 10 | 3 | 0 |
| ChatGPT | 19 | 76 | 4 | 12 | 11 | 2 |
| GitHub Copilot | 19 | 29 | 3 | 3 | 1 | 4 |
| Gemini | 16 | 60 | 10 | 2 | 8 | 8 |
| Azure OpenAI | 15 | 49 | 17 | 12 | 7 | 4 |
| OpenAI API | 15 | 96 | 75 | 11 | 5 | 2 |
| Claude | 11 | 38 | 2 | 6 | 3 | 2 |
| AWS Bedrock | 9 | 13 | 2 | 1 | 4 | 0 |
| Microsoft 365 Copilot Chat | 9 | 17 | 5 | 1 | 0 | 0 |
| Perplexity | 6 | 26 | 0 | 4 | 1 | 0 |

- ⚠ Consolidated (Appendix-B) edges appear in `entries` but not in the
  stage columns; the stage columns sum to the individual-entry share.
- ⚠ Product names are canonical: `AWS Bedrock` (not "Amazon Bedrock"),
  `Claude` excludes `Claude Code` (separate product; see §2).

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

### 'Claude Code' mentions across the whole corpus (2025)

**1**

```sql
SELECT
  (SELECT COUNT(*) FROM use_cases WHERE lower(
     COALESCE(use_case_name,'') || ' ' || COALESCE(problem_statement,'') || ' ' ||
     COALESCE(expected_benefits,'') || ' ' || COALESCE(system_outputs,'') || ' ' ||
     COALESCE(system_name,'') || ' ' || COALESCE(vendor_name,'') || ' ' ||
     COALESCE(raw_json,'')) LIKE '%claude code%')
+ (SELECT COUNT(*) FROM consolidated_use_cases WHERE lower(
     COALESCE(ai_use_case,'') || ' ' || COALESCE(commercial_product,'') || ' ' ||
     COALESCE(commercial_examples,'') || ' ' || COALESCE(raw_json,'')) LIKE '%claude code%')
```
- ⚠ The single hit is DOI's Appendix-B 'Generating code using AI.' template row (commercial_product field) — a checkbox listing, not a managed deployment (guardrail 5). Pinned by check_article_guardrails.py; a source reload that moves it fails `make check`.
- ⚠ 11 individual use cases mention 'Claude' in any form — see claims_review_2026-07-06.md §1 for the list; date-stamp all Claude framings against the 2026-02-27 Anthropic cease-use directive (guardrail 6).

Coding-tool taxonomy of the individual filings (IFP-labeled, adjudicated 2026-07):

| coding_tool_type | n |
|---|---|
| chat_assistant | 25 |
| ide_autocomplete | 18 |
| code_analysis_tool | 14 |
| unclear | 9 |
| coding_agent | 4 |

### Deployed or piloted AGENTIC coding tools (2025)

**0**

```sql
SELECT a.abbreviation, u.use_case_name, u.stage_normalized
  FROM use_case_tags t
  JOIN use_cases u ON u.id = t.use_case_id
  JOIN agencies a ON a.id = u.agency_id
 WHERE t.coding_tool_type = 'coding_agent'
```
- ⚠ The 4 agent-class filings (SBA Developer Code Assistant AI [pre_deployment]; SBA Developer Code Assistant AI [pre_deployment]; SBA Multi-Agent Orchestration [pre_deployment]; SSA Coding Assistance [pre_deployment]) are ALL pre-deployment — zero live agentic coding tools in the 2025 inventory. Pair with the single Claude Code mention (above) for the 'next wave is missing' claim.
- ⚠ IFP-labeled taxonomy (closed vocab, Sonnet label -> Fable audit -> gate GREEN); 'unclear' rows (9) are thin narratives, not hidden agents — see the round's AUDIT_GATE.md.

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

## 3b. Integration depth — measured (IFP-labeled, adjudicated 2026-07)

How deeply each PILOT or DEPLOYED individual use case is wired into
agency work, labeled over the narratives (the measurement the OMB
format does not collect). Ladder: standalone_chat < workflow_embedded
< system_integrated < agentic_workflow.

| integration_depth | all P+D | GenAI | non-GenAI |
|---|---|---|---|
| standalone_chat | 227 | 202 | 25 |
| workflow_embedded | 703 | 197 | 506 |
| system_integrated | 564 | 66 | 498 |
| agentic_workflow | 14 | 1 | 13 |
| unclear | 64 | 12 | 52 |

**1572** labeled pilot/deployed rows (478 GenAI). Headlines:
- GenAI in operation is mostly UNcoupled: 202/478 (~42%) standalone chat vs 66/478 (~14%) integrated with agency systems.
- The integrated AI estate is pre-GenAI: 498 of 564 system_integrated rows are classical/predictive systems.
- Agentic workflows in live operation: 14 total (0.9%), of which GenAI-based: 1 (HHS 'Deep Research for Public Health', pilot).

- ⚠ IFP-labeled adjudicated round (Sonnet label → Fable audit → gate
  GREEN; 100% of low-confidence + 100% of agentic verdicts audited).
  Labels reflect what narratives DESCRIBE as operating — floors, not
  ground truth about undescribed couplings.
- ⚠ One DOI row with a blank use_case_name is unlabeled (signature
  unresolvable); population is otherwise 1,573/1,573 covered.
- ⚠ integration_depth='agentic_workflow' (behavior-based) is NOT the
  same axis as ai_sophistication='agentic' (66, capability-based) —
  overlap is partial by design; do not conflate the two counts.

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

## 5b. Bureau-level divergence — enterprise access is decided below the department

Within-department spread of bureau-scored maturity (`org_ai_maturity`
rows at sub_agency/office level, ≥5 use cases to be scored; one-hop
parent rollup). The unit of adoption choice is the bureau: HHS is a
federation where nearly every scored operating division independently
meets enterprise-LLM; DOJ's bureaus uniformly do not; DOE is bimodal
across its labs.

| dept | bureaus scored | w/ enterprise LLM | w/ coding assistants | enterprise-LLM bureaus |
|---|---|---|---|---|
| DOE | 18 | 2 | 6 | IM-50,SRS |
| DOJ | 14 | 0 | 1 | — |
| NASA | 8 | 2 | 1 | GSFC,ARC |
| HHS | 8 | 8 | 6 | ASFR,CDC,CMS,FDA,NIH,ACF,HRSA,AHRQ |
| VA | 7 | 1 | 2 | OIT |
| DOI | 7 | 0 | 1 | — |
| DOC | 7 | 1 | 3 | OS |
| DHS | 7 | 1 | 3 | MGMT |
| USDA | 6 | 0 | 0 | — |
| FDIC | 6 | 0 | 0 | — |
| Treasury | 5 | 0 | 3 | — |
| State | 5 | 1 | 1 | DT |
| ED | 5 | 5 | 5 | OCIO,OPE,OSERS,OFO,FSA |
| CMS | 5 | 4 | 3 | CCIIO,OIT,OC,CCSQ |
| SEC | 4 | 0 | 0 | — |
| DOL | 4 | 0 | 0 | — |
| TVA | 3 | 0 | 1 | — |
| FDA | 3 | 1 | 0 | CDER |
| EPA | 3 | 0 | 0 | — |

- ⚠ Scored-bureau counts are floors — bureaus under 5 filed use cases
  aren't scored; absence from the table is not evidence of absence.
- ⚠ For SPECIFIC bureau capability claims (VA/OIT triple-strong; HHS
  8-of-11 opdivs independently Enterprise; Treasury OCC.Chat; DOJ's
  dept-wide Copilot being pre-deployment/uncorroborated), cite the
  round-3 web-corroborated ratings: `audit/retag/round3/
  SUB_AGENCY_FINDINGS.md` + `<topic>/sub_agency_rows.csv` (96
  sub-agencies × 3 topics, evidence quotes + URLs) — not this table.
- ⚠ Bureau workforce shares: `agency_workforce_profile` level='bureau'
  (64 rows) — needed before converting bureau counts to people-terms.

## 6. Guardrails — claims the data cannot support

(Enforced where machine-checkable by `audit/checks/`; full list in
`audit/retag/TODO.md` §3.)

1. `agency_ai_maturity.has_enterprise_llm` — RESOLVED 2026-07-06: cured
   upstream (individual-rows-only rule, scope corrections, omb_only
   ingest; audit/retag/TODO.md §3). Safe to cite as "enterprise-wide
   general-LLM access, individually-filed evidence". One definitional
   split remains: PBGC has enterprise general-LLM access but no
   GenAI-flagged enterprise row; FERC the reverse.
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
   HHS Claude claims), DHS commercial-AI revocation (counter-trend),
   the 'DHS/DoW have adopted Claude Code' anecdote (no public source;
   DoD/DoW filed no 2025 individual inventory, so the data cannot
   corroborate or refute it), and the 'decade compressed into two
   years' adoption-speed comparison (needs an external historical
   baseline — cloud/PC/email federal adoption curves).
7. Do NOT cite self-reported time-savings/efficiency figures as
   measured outcomes — anywhere. Applies to comparators (UK 26 min,
   DWP 19 min, Australia 1 hr) AND to agencies the article praises
   (VA 2-3 hrs/week, CDC 41K hours/527% ROI): all survey/self-
   assessment data. METR's RCT perception gap (19% slower measured,
   20% faster believed) is the reason. Label (SR) or drop. See
   claims_review_2026-07-07.md §3 and fact_sheet §8 Beat 3.

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

## 8. Comparators — what fast adopters actually did

_Added 2026-07-07 (hand-authored; every claim survived 3-vote adversarial
verification in the 2026-07-06/07 deep-research pass — votes, verbatim
sources, and access dates in `research_2026-07-07/verified_findings.md`;
required phrasings and the do-not-use list in
`claims_review_2026-07-07.md`). Metric types are marked: (SR)
self-reported survey · (T) telemetry · (RCT) randomized trial · (V)
vendor/company-reported._

### Beat 1 — fast access without depth (the thesis, replicated abroad)

**Australia: licenses live ~6.5 weeks after the announcement — and only
~⅓ of participants used Copilot daily.** The DTA's whole-of-government
trial (Jan–Jun 2024, 5,765+ evaluated licenses, ~60 agencies) chose
Copilot explicitly because it nested "within existing whole-of-government
contracting arrangements" (their OneGov). Use concentrated in
summarisation/rewriting; the evaluation attributes low engagement to
capability, perceived benefit, and convenience — non-access factors. All
outcomes (SR). UK GDS's 20K-employee cross-government trial: 26 min/day
(SR, survey midpoints, top-capped); strong at drafting/summarising, weak
on judgment-heavy work; a separate UK evaluation found "no robust
evidence that time savings are leading to improved productivity."

- ⚠ Phrase UK as "centrally coordinated trial with ≥1,000-licence
  per-organisation commitments" — NOT central platform/procurement.

### Beat 2 — what the depth cases added (mechanisms, not access)

**Singapore: ~80% of 150,000 public officers have used the central Pair
Chat (Nov 2025); 20,000+ self-service AIBots built by officers; a
MANDATORY AI-literacy course for all officers (Oct 2025); a cross-agency
usage leaderboard "driving playful competition."** Enterprise cases:
Accenture rolling M365 Copilot to ~743K of ~780K staff with 89%
monthly-active in a measured 200K tranche (V/T); Moderna's CEO-set
target of 100% adoption-and-proficiency in six months with a champions
cohort, office hours, and incentives (V).

- ⚠ Singapore's 80% = ever-used among 150K officers (weekly-active is
  far smaller — "near-universal reach with a smaller committed-daily
  core"); our 38% = evidenced-access among 747K eligible. Directional
  contrast only — never one chart axis.
- ⚠ Ownership (verified 2026-07-07): Pair Chat = Open Government
  Products (core team ~8 people, inside the ~200-person OGP, inside
  ~3,000-person GovTech); AIBots = GovTech DSAID/LaunchPad — two
  different teams; never attribute both to OGP. The USAi contrast is
  INSTITUTIONAL (standing build agency, central-funded free over
  pan-gov SSO, no sunset) vs PRODUCT (opt-in, 15 agencies, FCSF
  cost-recovery from FY2027). Never anchor it in dollars: no government
  publishes LLM-platform running costs, USAi has no disclosed line item
  (the ~$71M FCSF request is the whole portfolio), and Singapore's
  S$70M LLM programme is SEA-LION R&D, not Pair opex. See
  `research_2026-07-07/ogp_funding_verification.md`.
- ⚠ Do NOT use: Singapore default-on browser provisioning (refuted 0-3);
  any Accenture rollout timeline (refuted 1-2); Accenture's "97%/15x"
  marketing stat; Moderna's 120-conversations/user/week without
  "vendor-reported, unaudited."
- ⚠ The mandate's own text already requires "appropriate training for"
  — Singapore's mandatory course is the enforced version of a clause
  the US mandate already contains.

### Beat 3 — the evidence-quality warning (applies to OUR numbers too)

**METR RCT (early 2025): experienced developers 19% SLOWER with AI while
believing they were 20% faster** — a ~39-point perception gap that
discounts every self-reported time-savings figure in this space,
including the VA 2-3 hrs/week and CDC 41K-hours numbers the prior draft
cites favorably. The telemetry counterweight is modest-positive:
GitHub/Accenture RCT +8.69% PRs, +15% merge rate (T/RCT, 2-1 vote,
vendor-published, Management Science corroboration).

**Coding claim, verified 2026-07-07 (the blanket "no government has
published coding data" is REFUTED — use this instead):** no government
has published sustained, production-scale data for autonomous coding
AGENTS; the published government evidence is time-boxed ASSISTANT
trials — UK GDS/DSIT (Nov 2024–Feb 2025: ~1,900 licences, 50+ orgs,
~418 daily actives and 15.8% code-line acceptance by telemetry; 56
min/day saved self-reported) and Singapore GovTech (70-developer pilot,
22% acceptance). The §2 zero-live-agents census remains the only
agent-level whole-government measurement anywhere.

- ⚠ Do NOT cite Australia's DTA trial as coding evidence (it was M365
  Copilot office productivity — the #1 conflation risk). VA's published
  "~100K users / 2–3 hrs" metric is VA GPT (chat), NOT its Copilot
  deployment, which has no published telemetry.

- ⚠ Cite METR as a date-stamped early-2025 finding + methodological
  warning, not as AI's current effect (their 2026-02 follow-up: tools
  likely better now, weak evidence on magnitude).
- ⚠ One standard for self-reported numbers: label them (SR) everywhere
  — comparators AND the agencies we praise — or drop them.
- Dashboard: /figures/adoption-comparators (mechanism matrix +
  evidence-quality panel; in progress).

### Beat 4 — US states: four distinct mechanisms, verified 2026-07-07

**PA (central-platform pilot → expansion): 175 pilot employees / 14
agencies → 3,000+ users / 35 agencies + 6,500 in training (Apr 2026).
NJ (training-first, state-BUILT LibreChat assistant): ~20,000 cumulative
users / 1M+ prompts (Feb 2026), ~$1/user/month vs ~$20 commercial;
training adopted by 25 states. Utah (enterprise Gemini rollout with a
mandatory-training gate): 257 pilot → ~15–16K with access, ~10K active
in ~7 months. CA (RFI2 procurement sandbox): strong mechanism, thin
published outcomes.** Sources + full caveats:
`research_2026-07-07/states_verification.md`.

- ⚠ PA's famous "95 minutes/day" is verbatim "users ESTIMATED" — an
  exit-survey self-estimate from 136 non-representative volunteers,
  GROSS of the paired "35 min/day SPENT using ChatGPT" stat the
  citations always drop. Citable only as (SR), ideally with the 35-min
  pairing.
- ⚠ CA's circulating "1.5% / 10,000 more calls" is initial-analysis +
  projection, not a published measured outcome; CDTFA's primary sources
  publish no number.
- ⚠ NJ's DOL-35%/ANCHOR-50% and PA's Apr-2026 operational stats
  (400K documents, +65% chatbot) are state-reported with methodology
  unstated — do not cite without a further pass.
- ⚠ The strongest measured state numbers everywhere are ADOPTION counts,
  never impact: state ROI claims are all self-reported.
