# OMB-alignment slice charter

You are one of three parallel slice agents for the OMB-alignment task. The
foundation phase has already shipped these prerequisites:

1. **DB migration applied.** 15 columns on `use_cases` have been renamed to
   their OMB-canonical names. The DB at
   `data/federal_ai_inventory_2025.db` already has the new names. The
   dashboard's local copy at `dashboard/data/federal_ai_inventory_2025.db`
   has NOT been synced — production keeps working off the old schema until
   integration ships.
2. **`Section` component extended** in `dashboard/components/editorial.tsx`
   with a new `source?: "omb" | "derived" | "omb-derived" | "mixed"` prop
   and a new exported `SourceLegend` component. Both are ready to use.
3. **DB backup** at `data/federal_ai_inventory_2025.db.pre-omb-align.bak`.

Your job is to update everything in your slice's file set so the codebase
matches the new schema and (for the dashboard slice) renders the OMB-vs-IFP
labels.

## The 15 column renames (all already applied to the parent DB)

| Old name | New (OMB canonical) |
|---|---|
| `withheld_from_public` | `is_withheld` |
| `involves_pii` | `has_pii` |
| `federal_data_catalog_link` | `link_to_data` |
| `pia_link` | `pia_url` |
| `demographic_variables` | `demographic_features` |
| `open_source_link` | `code_url` |
| `pre_deployment_testing` | `hi_testing_conducted` |
| `impact_assessment` | `hi_assessment_completed` |
| `potential_impacts` | `hi_potential_impacts` |
| `independent_review` | `hi_independent_review` |
| `ongoing_monitoring` | `hi_ongoing_monitoring` |
| `operator_training` | `hi_training_established` |
| `has_fail_safe` | `hi_failsafe_presence` |
| `appeal_process` | `hi_appeal_process` |
| `end_user_feedback` | `hi_public_consultation` |

## Columns intentionally NOT renamed (leave as-is)

- `stage_of_development` — 49 refs across dashboard CASE-statement normalization + audit docs; deferred
- `development_type` — 66 refs; deferred
- `system_name` — 82 refs; deferred (large audit-doc surface area)
- `training_data_description` — 37 refs incl. test fixtures; deferred
- `has_ato` — 33 refs incl. dashboard ATO availability matrix; deferred
- `bureau_component` — heavily referenced; deferred
- `use_case_id` — would conflict with primary key `id`; not renamed

If you encounter a reference to one of these columns, leave it alone.

## Source-label vocabulary (dashboard slice only)

`Section` now takes an optional `source` prop:

| `source` value | Meaning |
|---|---|
| `"omb"` | Section displays only OMB-filed fields |
| `"derived"` | Section displays only IFP-added fields (tags, evidence, products, hierarchy) |
| `"omb-derived"` | Counts/rollups whose inputs are OMB but whose computation is IFP |
| `"mixed"` | Section displays both kinds (use sparingly; prefer per-Row labeling) |

## File-ownership boundaries — DO NOT CROSS THESE LINES

- **Slice A (dashboard)** owns `dashboard/**` exclusively. Don't touch any
  Python file or any docs file outside `dashboard/`.
- **Slice B (Python ETL)** owns the parent project's Python — `db.py`,
  `auto_tag.py`, `load_inventories.py`, `compute_maturity.py`,
  `build_lookups.py`, `scripts/*.py`, `tests/*.py`. Don't touch anything
  under `dashboard/`.
- **Slice C (docs/skill)** owns
  `.claude/skills/omb-ai-use-case-inventory/**`,
  `AGENT_TAGGING_GUIDE.md`, `KEY_FINDINGS.md`, and adds a new
  `audit/omb_alignment/MIGRATION_REPORT.md`. Don't touch any Python or
  TypeScript source.

If you find a file that doesn't fit your slice but needs an update, flag
it in your final summary instead of editing it.

## Conventions

- Use ripgrep / `grep -rn` to find references rather than guessing. The
  exact list of references per column is in `audit/omb_alignment/` if
  needed, but a fresh grep is more reliable.
- For Slice A: never write a `Section` without a `source` prop. If a
  section truly straddles, use `"mixed"`.
- For Slice B: after updating a file, run `python -c "import <module>"`
  on it as a quick smoke test where applicable.
- For Slice C: cross-reference the schema doc (`reference/columns.md`) so
  the renamed columns reflect identity mapping in the crosswalk.

## Final-summary contract

Each slice agent writes a brief summary to its TaskUpdate and returns
≤300 words covering:
- Files modified
- Anything you couldn't change and why (rare)
- Any test runs / typechecks you ran
- Any cross-slice issue you noticed (so integration can pick it up)
