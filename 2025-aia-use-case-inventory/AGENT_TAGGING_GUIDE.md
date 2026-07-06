# Agent Tagging Guide

You are refining analytical tags for a specific federal agency's AI use cases in a SQLite database.

**Database:** `/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/data/federal_ai_inventory_2025.db`

**Your target agency:** {AGENCY_ABBR}

## Analytical Goal

These tags support a piece on whether federal agencies provide meaningful AI access (especially general LLM and coding tools) in controlled environments. Key questions we need to answer:

- Is this entry really a separate use case or just a capability of a product the agency uses?
- Does this agency deploy general-purpose LLMs (ChatGPT, Copilot, Claude, Gemini) broadly?
- Does this agency deploy coding assistants (GitHub Copilot, Claude Code, CodeWhisperer)?
- Is the AI available enterprise-wide or just to a single bureau/office?
- Is it a real custom system, or just wrapping a commercial product?

## Workflow

1. Run: `sqlite3 data/federal_ai_inventory_2025.db`
2. Query the data for your agency:
   ```sql
   SELECT uc.id, uc.use_case_name, uc.bureau_component, uc.vendor_name, uc.system_name,
          uc.ai_classification, uc.problem_statement, uc.development_type,
          uc.training_data_description, uc.has_custom_code,
          t.entry_type, t.is_general_llm_access, t.is_coding_tool,
          t.deployment_scope, t.scope_detail, t.architecture_type,
          t.ai_sophistication,
          epp.product_name AS product_name
   FROM use_cases uc
   JOIN use_case_tags t ON t.use_case_id = uc.id
   JOIN agencies a ON a.id = uc.agency_id
   LEFT JOIN entry_primary_products epp
          ON epp.entry_kind = 'use_case' AND epp.entry_id = uc.id
   WHERE a.abbreviation = '{AGENCY_ABBR}';
   ```
3. Also check consolidated_use_cases the same way if applicable.
4. Review the auto-tagged values. For each use case, consider whether the classification is correct.
5. Write UPDATE statements to fix incorrect tags.

## Fields to Review

### `entry_type` (most important)
- `generic_use_pattern`: Describes a task pattern (from OMB's Appendix B template), e.g. "Generating first drafts of documents using AI"
- `product_deployment`: Specific product being deployed, e.g. "Microsoft 365 Copilot for HR"
- `product_feature`: A sub-feature of a larger platform, e.g. "GitHub Copilot" (within Microsoft family)
- `custom_system`: Custom-built agency system, no COTS parent (e.g. TVA's GMET, NASA custom models)
- `bespoke_application`: Custom app built ON a commercial product (e.g. "DOJ Case Summarizer built on Azure OpenAI")

### `deployment_scope`
- `enterprise_wide`: Available to whole agency (bureau_component matches agency name or says "Agency-wide")
- `department`: Entire department (e.g. "HHS" as bureau when agency is HHS)
- `bureau`: A specific bureau (e.g. CDC within HHS, CBP within DHS)
- `office`: A smaller office/division
- `team`: Single team
- `pilot`: Pilot project
- Fill `scope_detail` with the specific bureau/office name if not enterprise_wide

### `architecture_type`
- `inference_only`: Just using a pre-trained COTS product (most Copilot use cases)
- `rag_pipeline`: Has knowledge retrieval / document search / embeddings
- `fine_tuned`: Model was fine-tuned on agency data
- `custom_trained`: Model trained from scratch on agency data
- `agentic_workflow`: Multi-step autonomous agent
- `unknown`: Can't determine

### `ai_sophistication`
- `general_llm`: Conversational AI/chatbot
- `coding_assistant`: Code generation/completion
- `agentic`: Autonomous multi-step agents
- `classical_ml`: Traditional ML (not generative)
- `computer_vision`: Image/video analysis
- `nlp_specific`: Non-generative NLP (entity extraction, classification)
- `predictive_analytics`: Forecasting/prediction models

### Product linkage (edge tables — there is NO scalar `product_id`)
The former `use_cases.product_id` / `consolidated_use_cases.product_id`
columns were dropped (m025). Product links live ONLY in the edge tables:
```sql
INSERT OR IGNORE INTO use_case_products
    (use_case_id, product_id, evidence_text, confidence)  -- confidence: 'strong' | 'inferred' ONLY
VALUES (?, ?, ?, ?);
```
"The" primary product for an entry comes from the `entry_primary_products`
view. Query `SELECT * FROM products` to see the catalog; check
`product_aliases` for common-name mapping and add new aliases with
`INSERT INTO product_aliases (product_id, alias_text) VALUES (?, ?);`.
Resolve product ids by `canonical_name` at write time — ids rotate every
rebuild. See the `inventory-db-model` skill for the full model and the
`adjudication-rounds` skill for the labeling-round process this guide's
criteria plug into.

### `is_product_capability_entry`
Set to 1 if this is "just one feature of a bigger product deployment" (e.g. one of 7 NLRB Copilot entries where each is a different use pattern but all using the same Copilot license).

### Vendor boolean flags
- `is_microsoft_copilot`, `is_openai`, `is_anthropic`, `is_google`, `is_github_copilot`, `is_aws_ai`
- Should match the linked product_id's vendor.

## Important Patterns to Watch For

- **NLRB/USITC/PBGC pattern**: 7-20 entries that are ALL "just different capabilities of Microsoft Copilot" - each should have `entry_type='generic_use_pattern'`, `is_product_capability_entry=1`, linked to M365 Copilot.
- **HHS/DHS pattern**: Many entries from different bureaus (CDC, FDA, CBP, etc.) - scope should be `bureau` with scope_detail filled.
- **DOE/NASA pattern**: Mix of custom systems, national labs' research AI, and COTS - most are `custom_system` or `bespoke_application`.
- **VA/DOJ pattern**: Large inventories mostly bureau-level deployments with some COTS wraps.

## Deliverable

After reviewing:
1. Execute UPDATE statements for corrections
2. Report:
   - Total use cases reviewed
   - Number of tag corrections made
   - Key insights about this agency's AI deployment pattern
   - Any new product aliases added
   - Flag anything ambiguous for human review

---

## Addendum: Tagging 2024 rows (`use_cases_2024`)

The 2024 inventory uses a different source schema than 2025. When tagging
2024 rows (Wave 1 of the multi-wave plan in
`docs/plans/2024-tagging/PLAN.md`), keep these differences in mind:

- **No `ai_classification` column.** 2024 has no clean "generative AI vs
  classical ML" signal. Infer GenAI vs not from narrative:
  `use_case_name + purpose_benefits + outputs + commercial_ai +
  dev_method + bureau`.
- **`commercial_ai` conflates vendor + product + sometimes pipeline.**
  E.g. it may read "Microsoft Copilot", "ChatGPT Enterprise via Azure",
  "AWS Bedrock + custom RAG". Parse it into `tool_vendor` and
  `tool_product_name`. When unclear, leave both blank and set
  `confidence='low'`.
- **`dev_stage` is the 2024 analogue of stage/lifecycle.** Treat
  `Operation and Maintenance`, `Implementation and Assessment`, and
  `In production` as deployed; `Initiated`, `Acquisition/Development`,
  `Planned`, `Ideation`, `Research/Admin` as not yet deployed;
  `Retired` as off.
- **Do NOT read any 2025 table during Wave 1.** No `use_cases`, no
  `use_case_tags`, no `use_case_year_links`. The point of Wave 1 is to
  capture how agencies filed 2024, not how the 2025 mirror looks. The
  comparison happens in Wave 2.
- **Output format**: write a CSV with columns matching
  `scripts/load_2024_tags.py`'s contract (any subset of
  `entry_type, ai_sophistication, deployment_scope, …` plus the
  required `use_case_id_2024, tagged_by_agent`, plus `reasoning` and
  `confidence`). Do not write to the DB directly.
