# Wave 3 reconciliation rubric

Wave 2 flagged 633 use cases (out of 2,133) for reconciliation. You produce
a final, canonical tag for each one. After Wave 3, the
`use_case_tags_2024_canonical` view will pick *your* row over the Wave 1 row.

## Your input

Each row in the input CSV contains, for one use case:

- **2024 narrative** — `use_case_name, purpose_benefits, outputs,
  commercial_ai, dev_method, dev_stage, agency_abbreviation, bureau`
- **Wave 1 tag** — `wave1_<field>` for every IFP tag (the current canonical)
- **Wave 2 flag(s)** — `w2_flags_json` (JSON array), `w2_reasoning`,
  `w2_tagged_by` (which Wave 2 agent(s) flagged it)
- **Proposed corrections** (from Wave 2 agents) — `proposed_<field>` (often empty)
- **2025 mirror** — `name_2025, problem_statement_2025, expected_benefits_2025,
  system_outputs_2025, vendor_name_2025, ai_classification_2025,
  system_name_2025`, plus the 2025 IFP tags as `<field>_2025`
- **`lineage_status`** — `continued | renamed | split | retired_2024`

## Your output

One row per input row. CSV format. Columns:

- Required: `use_case_id_2024, tagged_by_agent, confidence, reasoning`
- The reconciled tag fields: `entry_type, is_generative_ai, ai_sophistication,
  deployment_scope, scope_detail, is_enterprise_wide, is_general_llm_access,
  is_coding_tool, is_cots_commercial, tool_product_name, tool_vendor,
  is_microsoft_copilot, is_openai, is_anthropic, is_google, is_github_copilot,
  is_aws_ai, architecture_type, use_type, is_public_facing` — set every field
  you're confident about (omit / blank fields you can't determine)
- `tagged_by_agent`: `wave3-P1` / `wave3-P2` / `wave3-P3` (your partition)
- `reasoning`: one sentence explaining your reconciliation decision

## Decision rules

The Wave 2 flags tell you what kind of decision you need to make.

### `material_divergence` + `drift_legitimate` (often together)
Both years are correctly tagged for their own year — the agency genuinely
changed posture. **Your job: tag the 2024 reality**, NOT the 2025 reality.
Example: 2024 says `is_generative_ai=0, classical_ml, pilot`; 2025 says
`is_generative_ai=1, general_llm, enterprise_wide`. You output the 2024
tag. Your `reasoning`: "drift_legitimate — kept 2024 tag (classical pilot)
as filed."

### `material_divergence` alone (no drift)
One of the years is wrong. Read the 2024 narrative carefully — if the
narrative supports the 2024 tag, keep it; if it supports the 2025 tag,
adopt the 2025 tag for the 2024 row (the agency mislabeled in 2024, and
2025 caught it). Your `reasoning`: "2024 narrative says X, so I adopt
the 2025 reading of Y."

### `tagging_error_2024`
Wave 2 thinks Wave 1 missed something. Read the narrative and the
proposed correction. If you agree, output the corrected tag. If you
disagree, output the Wave 1 tag and explain why.

### `tagging_error_2025`
Wave 2 thinks the 2025 IFP tag is wrong; Wave 1 (2024) was right. Output
the Wave 1 tag (or a refinement). The row is also in the
`tagging_error_2025` side queue for separate 2025 remediation — you don't
need to fix 2025 here.

### `internal_inconsistency` (Wave 2b only)
The Wave 1 tag is self-contradictory. Resolve it by re-reading the
narrative and producing a consistent tag set.

### `misclassified_lifecycle` (Wave 2b only)
The Wave 1 `deployment_scope` doesn't match `dev_stage`. Common case:
narrative says "pilot of 3 users" but Wave 1 tagged `bureau`. Fix the
scope. **Special interest**: if `dev_stage` says "Operation and
Maintenance" or "In production" AND `lineage_status='retired_2024'`,
this is a silently-dropped live system — make sure your tag reflects
the deployed-then-killed reality (`use_type=mission_critical` maybe,
or `is_public_facing=1` if it was).

### `tool_vendor_unverified` (Wave 2b only)
Wave 1 invented a vendor name. Clear the `tool_product_name` and
`tool_vendor` fields unless the narrative explicitly supports them.

## Special handling

- **Multiple Wave 2 flags on the same row**: address every flag in your
  reasoning. They're additive.
- **`split` rows** (one 2024 → multiple 2025): you'll see one row per
  source 2024 use case in Wave 3 (we don't repeat the source row). Tag
  the 2024 reality; the 2025 children get their own tags via 2025's
  pipeline.
- **`retired_2024` rows**: no 2025 to compare to. Lean on the Wave 1
  reasoning + the narrative + the Wave 2 flag.
- **Confidence**:
  - `high` — narrative + Wave 2 flag agree clearly
  - `medium` — narrative is reasonably clear
  - `low` — narrative is genuinely thin; Wave 1 + Wave 2 also disagreed

## Output mechanics

- Use the Python `csv` module.
- `mkdir -p audit/retag/2024-tagging/wave3/` before writing.
- Filename: `<partition>.csv` (e.g., `P1.csv`).
- `tagged_by_agent` must be set on every row.
- Expected: exactly one row per input row (no skipping — every flagged
  row needs a reconciliation).
