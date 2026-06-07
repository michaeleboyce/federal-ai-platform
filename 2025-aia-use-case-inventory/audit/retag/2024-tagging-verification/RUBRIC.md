# Phase B verification rubric

You are an **independent accuracy auditor**. You will check whether the
IFP tag assigned to each 2024 federal AI use case in the sample matches
what the original source narrative says.

You are NOT one of the Wave 1–3 agents. You have NOT seen the wave rubrics
used to produce the tags you are auditing. Your job is to read each row and
make your own judgment.

## Your input

`audit/retag/2024-tagging-verification/sample_input.csv` — 82 rows, one
per use case. Each row has:

- **2024 narrative**: `use_case_name`, `purpose_benefits`, `outputs`,
  `commercial_ai`, `dev_method`, `dev_stage` — the raw OMB-reported text
- **Canonical IFP tag**: `entry_type`, `is_generative_ai`, `ai_sophistication`,
  `deployment_scope`, `is_enterprise_wide`, `is_general_llm_access`,
  `is_coding_tool`, `is_cots_commercial`, `tool_product_name`,
  `tool_vendor`, `is_microsoft_copilot`, `is_openai`, `is_anthropic`,
  `is_github_copilot`, `use_type`, `confidence`
- **canonical_wave**: `1` or `3` — where the canonical tag came from
- **canonical_reasoning**: the tagging agent's stated reason
- **wave1_* fields**: Wave 1's reading (if canonical is wave 3, these
  differ from the canonical tag)
- **wave3_reasoning**: Wave 3 reconciliation reasoning (when applicable)
- **lineage_status**: `continued | renamed | renamed_split | retired_2024`

## Your output

One row per input row. CSV file:
`audit/retag/2024-tagging-verification/sample_audit_raw.csv`

### Output columns

Required: `use_case_id_2024, agency_abbreviation, use_case_name`

Per-dimension verdicts (one column each):

| Column | Allowed values |
|---|---|
| `verdict_is_generative_ai` | `correct` / `incorrect` |
| `verdict_ai_sophistication` | `correct` / `off_by_one` / `incorrect` |
| `verdict_deployment_scope` | `correct` / `off_by_one_tier` / `incorrect` |
| `verdict_entry_type` | `correct` / `debatable` / `incorrect` |
| `verdict_tool` | `correct` / `hallucinated` / `missing` / `na` |

Plus:
- `notes`: free text — mention anything surprising, ambiguous, or flagworthy
- `auditor_confidence`: `high` / `medium` / `low` (your confidence in YOUR
  verdict, not the original tag's confidence)

### Verdict definitions

**`verdict_is_generative_ai`**:
- `correct` — your reading matches `is_generative_ai`
- `incorrect` — the narrative clearly does not support the assigned value
  (e.g., purely statistical model tagged as generative, or GPT-4 usage
  tagged as non-generative)

**`verdict_ai_sophistication`**:
- `correct` — matches
- `off_by_one` — adjacent category (e.g., tagged `general_llm` but should
  probably be `agentic`; or `classical_ml` but should be `nlp_specific`)
- `incorrect` — clearly wrong category (e.g., `computer_vision` when
  the narrative is about document summarization)

Valid sophistication values: `general_llm` | `coding_assistant` | `agentic`
| `classical_ml` | `computer_vision` | `nlp_specific` | `predictive_analytics`

**`verdict_deployment_scope`**:
Tier ladder: enterprise_wide > department > bureau > office > team > pilot
- `correct` — matches the narrative's described breadth
- `off_by_one_tier` — one step off (e.g., bureau vs office)
- `incorrect` — multiple steps off (e.g., enterprise_wide when it's a
  team-level pilot)

**`verdict_entry_type`**:
- `correct` — clearly matches
- `debatable` — reasonable tagging choice but another value could also fit
- `incorrect` — clearly wrong (e.g., `product_deployment` for a fully
  in-house custom model)

Valid entry_type values: `generic_use_pattern` | `product_deployment`
| `product_feature` | `custom_system` | `bespoke_application`

**`verdict_tool`**:
- `correct` — `tool_product_name` and `tool_vendor` are blank (and narrative
  names no specific product), OR the named product/vendor appears in the
  narrative text
- `hallucinated` — product/vendor names appear in the tag but NOT in the
  narrative text at all
- `missing` — narrative clearly names a specific commercial product but
  `tool_product_name` is blank
- `na` — the use case is a custom/bespoke system where no commercial
  product is expected

## Important context

**The 2024 `commercial_ai` column is NOT a vendor field.** It contains
OMB checkbox phrases like "Searching for information using AI",
"Summarizing the key points of a document" — NOT product names. Tagging
agents had to infer vendor names from `purpose_benefits`, `outputs`, and
`use_case_name` free text. Roughly 90% of rows have no parseable vendor.
So `verdict_tool=missing` should only fire when the vendor is clearly
named in the narrative text.

**`off_by_one` and `off_by_one_tier` count as partial credit.** For
accuracy scoring purposes, these are NOT errors — they represent the
inherent ambiguity of adjacent categories. Mark them for information but
they don't reduce the pass/fail accuracy count.

## Output mechanics

- Use the Python `csv` module.
- `mkdir -p audit/retag/2024-tagging-verification/` before writing.
- `tagged_by_agent` column: set to `phase-b-auditor`.
- Every input row must produce exactly one output row (no skipping).
- Read the input from `audit/retag/2024-tagging-verification/sample_input.csv`.

## Pass thresholds

Per the verification plan:
- `is_generative_ai`: >85% `correct` (excluding `off_by_one` — there's no
  off-by-one for binary fields)
- `ai_sophistication`: >75% `correct` (off_by_one doesn't count as error)
- `deployment_scope`: >75% `correct` (off_by_one_tier doesn't count as error)
- `entry_type`: >75% `correct` (debatable doesn't count as error)
- `tool`: N/A (no pass threshold; just report rates)
