# 2024 inventory tagging rubric (Wave 1 / calibration)

You are tagging rows from the **2024** federal AI use-case inventory with the
IFP analytical schema. The same schema is already applied to every 2025 row
via `use_case_tags`; your output enables apples-to-apples cross-year analysis.

## Output contract

Write a single CSV file. Each input row → one output row. Columns:

**Required:**

- `use_case_id_2024` — copy from input
- `tagged_by_agent` — your assigned agent letter (e.g. `agentA`, `agentB`, …)

**Required (judgement):**

- `entry_type` — one of: `generic_use_pattern` | `product_deployment` | `product_feature` | `custom_system` | `bespoke_application`
- `is_generative_ai` — `1` if the use case involves a generative model (LLM, diffusion, generative CV), else `0`
- `ai_sophistication` — one of: `general_llm` | `coding_assistant` | `agentic` | `classical_ml` | `computer_vision` | `nlp_specific` | `predictive_analytics`
- `deployment_scope` — one of: `enterprise_wide` | `department` | `bureau` | `office` | `team` | `pilot`
- `confidence` — `low` | `medium` | `high`
- `reasoning` — one sentence explaining the tags, citing specific narrative phrases

**Useful (set when clear):**

- `is_general_llm_access` (0/1) — agency-wide access to a general-purpose chatbot (ChatGPT, Copilot Chat, Claude, Gemini, Bedrock)
- `is_coding_tool` (0/1) — coding assistant (GitHub Copilot, Cursor, Codex, similar)
- `is_cots_commercial` (0/1) — purchased commercial product (vs. in-house build)
- `tool_product_name` / `tool_vendor` — parsed from `commercial_ai` when clear
- `is_microsoft_copilot` / `is_openai` / `is_anthropic` / `is_google` / `is_github_copilot` / `is_aws_ai` (0/1) — vendor flags
- `is_enterprise_wide` (0/1) — convenience flag, set to 1 iff `deployment_scope='enterprise_wide'`
- `architecture_type` — one of: `inference_only` | `rag_pipeline` | `fine_tuned` | `custom_trained` | `agentic_workflow` | `unknown`
- `has_model_training` (0/1) — agency trains/fine-tunes a model
- `use_type` — `mission_critical` | `administrative` | `it_operations` | `cybersecurity` | `research`
- `is_public_facing` (0/1)

Omit any column you cannot determine — empty/blank means "not asserted" and is preferred over guessing.

## How to read a 2024 row

The 2024 inventory has no `ai_classification` column. Infer from the narrative.
Read these columns together:

- `use_case_name` — title
- `purpose_benefits` — what problem it solves / why it exists
- `outputs` — what the system produces
- `commercial_ai` — vendor + product (conflated — often reads "Microsoft Copilot", "AWS Bedrock + RAG", or "None of the above")
- `dev_method` — built in-house / acquired / hybrid
- `dev_stage` — lifecycle stage (Operation and Maintenance, Initiated, Retired, …)
- `bureau` — sub-agency
- `lineage_status` — `continued` / `renamed` / `split` / `retired_2024` (the 2024↔2025 link outcome — DO NOT use this to look up 2025 tags)

## Rules

1. **NO reading any 2025 table or 2025 source CSV.** The point of Wave 1 is
   to capture 2024 as agencies filed it, not as it would look in hindsight.
2. **`generic_use_pattern` vs `product_deployment`** — if the entry is "an
   agency-wide pattern of using LLMs to do X" rather than a specific named
   system, use `generic_use_pattern`. If the entry is one named product
   (e.g. "Microsoft 365 Copilot for HR drafting"), use `product_deployment`.
3. **`custom_system` vs `bespoke_application`** — in-house ML built from
   scratch is `custom_system`; in-house wrapping/orchestration of a
   third-party model (RAG over Bedrock, fine-tune on top of OpenAI) is
   `bespoke_application`.
4. **`product_feature`** — when the entry is one capability of a broader
   product (e.g. "Salesforce Einstein Lead Scoring" inside a Salesforce
   deployment). Set `is_product_capability_entry=1`.
5. **Vendor flags** — `is_microsoft_copilot` covers M365 Copilot, Copilot
   Chat, Copilot for Security; `is_openai` is direct OpenAI API or ChatGPT
   Enterprise; `is_anthropic` is Claude (via Bedrock or direct);
   `is_google` is Vertex/Gemini/Duet; `is_aws_ai` is Bedrock,
   SageMaker, Comprehend, Rekognition, Textract.
6. **Confidence**:
   - `high` — narrative explicitly names the product/vendor/scope
   - `medium` — narrative strongly implies it
   - `low` — narrative is ambiguous; you're making a best guess
7. **`reasoning`** — one sentence, must quote 2–6 words from the narrative
   that drove the tag. Example: "Names 'Microsoft 365 Copilot' and
   'deployed agency-wide' → enterprise_wide LLM deployment."

## Important agency patterns (from 2025 tagging experience)

- **NLRB/USITC/PBGC**: many entries that are each a different capability of
  Microsoft Copilot — tag as `generic_use_pattern` +
  `is_product_capability_entry=1`.
- **HHS/DHS**: many bureaus (CDC, FDA, CBP, …) — scope often `bureau`,
  set `scope_detail` to the bureau name.
- **DOE/NASA**: mix of national-lab custom builds and COTS — `custom_system`
  or `bespoke_application` is common.
- **VA/DOJ**: large portfolios, mostly bureau-level deployments with some
  COTS wraps.
