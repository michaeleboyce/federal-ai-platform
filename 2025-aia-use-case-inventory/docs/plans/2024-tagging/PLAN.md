# Tagging the 2024 inventory with the IFP analytical schema

## Why

`use_case_tags` exists for every 2025 row, populated by `auto_tag.py` + per-agency
agent passes. Nothing comparable exists for `use_cases_2024` (2,133 rows). Without
it, every cross-year comparison that depends on IFP-derived signals (
`is_generative_ai`, `is_general_llm_access`, `is_enterprise_wide`,
`ai_sophistication`, `deployment_scope`, `entry_type`, …) is asymmetric: clean for
2025, heuristic/regex for 2024.

The `/experience` page and the year-over-year LLM-access narrative both need a
symmetric tag set. This plan produces it via a four-wave multi-agent pass that
keeps the 2024 tagging *independent* of 2025 outcomes so we can later audit
whether agencies' 2024 self-reports actually predicted what they filed in 2025.

## The shape of the output

New table `use_case_tags_2024`, schema mirroring `use_case_tags` minus the
2025-only product/template foreign keys. Columns are the same booleans and
enums:

```
use_case_id_2024            -- FK to use_cases_2024.id
entry_type                  -- generic_use_pattern / product_deployment / …
product_capability          -- drafting, coding, search, …
is_general_llm_access       -- 0/1
is_coding_tool              -- 0/1
is_cots_commercial          -- 0/1
tool_product_name           -- normalized
tool_vendor                 -- normalized
ai_sophistication           -- general_llm / coding_assistant / agentic / …
is_generative_ai            -- 0/1
is_frontier_model           -- 0/1
deployment_scope            -- enterprise_wide / department / bureau / …
scope_detail
is_enterprise_wide          -- 0/1
estimated_user_count        -- band string if recoverable
architecture_type           -- inference_only / rag_pipeline / fine_tuned / …
has_model_training          -- 0/1
is_microsoft_copilot, is_openai, is_anthropic,
is_google, is_github_copilot, is_aws_ai
use_type                    -- mission_critical / administrative / …
is_public_facing            -- 0/1

-- provenance / audit
wave                        -- 1 | 2a | 2b | 3
tagged_by_agent             -- agent name
reasoning                   -- free text
quality_flags_json          -- JSON array of flags raised in QA
confidence                  -- low/medium/high
created_at, updated_at
```

`auto_tag.py` already encodes the rule logic for 2025 rows. We can re-use the
heuristic seed for 2024 as a starting point, but the *binding* tags come from
the agent waves, not the regex pass.

## The two columns the 2024 schema lacks (and how we cope)

`use_cases_2024` doesn't have:

- A clean `ai_classification` column. 2024 used `commercial_ai` (the COTS product
  list) and free-text `purpose_benefits` / `outputs`. The "is this GenAI"
  judgment must come from narrative reading, not a column lookup.
- A separate `vendor_name`. The 2024 column is `commercial_ai` and conflates
  vendor + product + sometimes pipeline element.

Agents will read `use_case_name + purpose_benefits + outputs + commercial_ai +
dev_method + bureau` together and make the same judgments they make for 2025.

## The four waves

### Wave 1 — Blind tagging (5–6 agents, run in parallel)

Each agent gets a partition of `use_cases_2024` keyed by agency. Partition sizes
roughly equal (≈350–425 rows each):

| Agent | Agencies (approx) | Approx rows |
|---|---|---|
| A | HHS, VA | ~500 |
| B | DOJ, DOC, DOE | ~376 |
| C | DOT, DHS, Treasury, FRB | ~485 |
| D | USDA, DOI, USAID | ~406 |
| E | State, GSA, DOL, ED, EPA, SSA | ~290 |
| F | All remaining (smaller agencies) | ~76 |

The partition by agency, not random shuffle, lets each agent build a mental
model of "what an agency tends to file" — agencies are quite distinctive in
their phrasing (HHS subagencies use forward-slash bureau notation, DOE labs
each have a house style, etc.).

Instructions to each Wave-1 agent:

1. **No 2025 reading allowed.** Do not query `use_cases`, `use_case_tags`, or
   `use_case_year_links` for any reason. The point is to capture the 2024
   reality as agencies filed it, not as it would look in hindsight.
2. Read each row's name + narrative columns + commercial_ai. Apply the IFP tag
   schema (above) using the same rubric as `AGENT_TAGGING_GUIDE.md`.
3. Record every tag *and* a one-sentence reasoning. Default `confidence='medium'`;
   set `low` when the narrative is genuinely ambiguous, `high` when the row is
   unambiguous (e.g., a row explicitly named "Microsoft 365 Copilot for HR").
4. Insert into `use_case_tags_2024` with `wave='1'`. Do NOT update existing rows
   — each wave appends.

Each agent runs the full agency partition end-to-end, producing one tag row per
use case.

### Wave 2a — Matched-pair QA (2 agents, run after Wave 1)

For every `(uc_2024_id, uc_2025_id)` pair in `use_case_year_links` with
`lineage_status IN ('continued', 'renamed', 'split')` — that's ~1,425 rows —
compare Wave-1's tags against the 2025 IFP tags on the matched 2025 row.

Where they diverge, flag it:

- **Material divergence** = different `is_generative_ai`, different
  `ai_sophistication`, different `entry_type`, or `deployment_scope` shifting
  more than one tier (enterprise_wide ↔ bureau is material;
  bureau ↔ office is not).
- **Drift** = same use case, agencies legitimately changed posture (e.g., 2024
  pilot → 2025 enterprise rollout). Tag both as `drift_legitimate`.
- **Tagging error** = Wave-1 agent missed something a re-reading would catch.
  Tag `tagging_error_2024`.
- **2025 tag is the wrong one** = Wave-1 was right, 2025 should be corrected.
  Tag `tagging_error_2025` and route to a separate small queue for 2025
  remediation.

Append findings to `use_case_tags_2024` with `wave='2a'`, with a
`quality_flags_json` array describing the divergence. **Do not overwrite Wave-1
rows yet** — Wave 3 will reconcile.

Agents:
- QA-1: lineage_status='continued' pairs (~1,139 rows)
- QA-2: lineage_status IN ('renamed', 'split') pairs (~286 rows)

### Wave 2b — Unmatched-2024 QA (1 agent)

For every `uc_2024_id` where `lineage_status='retired_2024'` (~710 rows), there
is no 2025 row to compare against. These need a different sanity check:

- Is the Wave-1 tag *internally consistent*? (A row with
  `is_generative_ai=1, ai_sophistication='classical_ml'` is impossible.)
- Did the agency file this as "Retired" in 2024's `dev_stage` (legitimately
  aged off), or was it active-then-dropped (silently dropped — see
  `/compare-years/silently-dropped`)?
- Re-confirm `tool_product_name` and `tool_vendor` for any commercial-AI row,
  since these don't have a 2025 mirror to compare against.

Append findings with `wave='2b'` and `quality_flags_json`.

### Wave 3 — Reconciliation relabel (3–4 agents)

For every row flagged in Wave 2a or 2b, produce a final canonical tag. Each
Wave-3 agent gets a partition of *flagged rows*, not agencies, because the
reconciliation logic is the same regardless of agency.

Wave-3 agents read:
- The Wave-1 tag + reasoning
- The Wave-2 flag(s)
- The original row narrative
- For 2a-flagged rows: the matched 2025 row + 2025 tags
- For 2b-flagged rows: just the 2024 narrative

…and produce a `wave='3'` row that supersedes Wave 1 for that use case. The
final canonical tag for any 2024 row is: the latest `wave` row in
`use_case_tags_2024`.

Rows that pass Wave 2 unflagged keep their Wave-1 tag as canonical.

After Wave 3, write a view `use_case_tags_2024_canonical` that picks the latest
wave per `use_case_id_2024`.

## Tagging-error-2025 side channel

The small subset of Wave-2a divergences flagged as `tagging_error_2025` (where
the 2024 agent's reading is more defensible than the existing 2025 tag) feeds a
separate remediation queue: `audit/retag/2024-vs-2025-divergence/queue.csv`.
This isn't part of the 2024 tagging plan's deliverables — it's a side benefit
of running the comparison and should be triaged manually.

## Calibration before Wave 1 launches

Before partitioning the work, run a calibration pass:

1. Pick 50 use cases from 2024 stratified across agencies + dev_stage buckets.
2. Have ALL Wave-1 agents (5–6 of them) tag the *same* 50 rows independently.
3. Compute pairwise inter-rater agreement on `is_generative_ai`,
   `ai_sophistication`, `entry_type`, `deployment_scope`. Target >85% pairwise
   agreement on `is_generative_ai`; >70% on the others.
4. If agreement is too low, refine the rubric and re-calibrate before
   partitioning.

Calibration rows are tagged with `wave='0-calibration'` and excluded from
canonical view selection.

## Outputs

When the plan finishes:

- `use_case_tags_2024` populated with ~2,200–2,500 rows (1 wave-1 per use case,
  plus wave-2 flags and wave-3 reconciliations as needed).
- `use_case_tags_2024_canonical` view (or materialized table) with one row per
  2024 use case = the final tag.
- An `audit/retag/2024-tagging/summary.md` documenting:
  - Wave-1 calibration agreement scores
  - Counts at each wave
  - The 25 most-flagged-and-reconciled examples (for the article footnotes)
  - The `tagging_error_2025` side queue contents (count + examples)
- A migration (`migrations/m013_use_case_tags_2024.sql`) creating the table and
  view.

## What this unblocks

Once `use_case_tags_2024_canonical` exists:

- `/experience` page can show "GenAI use cases 2024 vs 2025 by IFP definition"
  with matched-methodology bars, not heuristic 2024 + tagged 2025.
- The `/compare-years` page gets a "definition lens" toggle that's honest across
  both cycles.
- We can answer: how many 2024 use cases that were *actually* enterprise-wide
  LLM access continued vs. retired in 2025? Currently impossible to ask.

## Ordering / parallelism

```
Calibration (sequential, all agents on same 50 rows)
       ↓
Wave 1   (6 agents in parallel, ~2-4 hours each)
       ↓
Wave 2a + Wave 2b   (3 agents in parallel)
       ↓
Wave 3   (3-4 agents in parallel on flagged subset)
       ↓
Materialize canonical view + audit summary
```

Total wall-clock: roughly one working day if launched well-supervised.

## Out of scope for this plan

- Tagging the consolidated Appendix-B rows (`consolidated_use_cases`). They have
  their own schema and license-band column; tag them separately if needed.
- Re-tagging 2025 rows. The `tagging_error_2025` queue gets routed to a manual
  pass, not folded back into a 2025 wave.
- Building the comparable 2024 `products` and `product_aliases` rows. The
  `tool_product_name` and `tool_vendor` columns in `use_case_tags_2024` are
  free-text strings; FK-linking to canonical products is a follow-on.
