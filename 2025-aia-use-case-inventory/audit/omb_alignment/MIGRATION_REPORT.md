# OMB-Alignment Migration Report

**Date:** 2026-04-29
**Migration:** `migrations/m002_rename_to_omb_canonical.py`
**DB backup:** `data/federal_ai_inventory_2025.db.pre-omb-align.bak`

This report documents the April 2026 OMB-alignment pass that renamed 15
columns on `use_cases` to match the canonical OMB M-25-21 column names,
along with the dashboard's new OMB-vs-IFP source labeling.

## What landed: the 15 renamed columns

| OMB canonical name (now DB column) | Previous DB column |
|---|---|
| `is_withheld` | `withheld_from_public` |
| `has_pii` | `involves_pii` |
| `link_to_data` | `federal_data_catalog_link` |
| `pia_url` | `pia_link` |
| `demographic_features` | `demographic_variables` |
| `code_url` | `open_source_link` |
| `hi_testing_conducted` | `pre_deployment_testing` |
| `hi_assessment_completed` | `impact_assessment` |
| `hi_potential_impacts` | `potential_impacts` |
| `hi_independent_review` | `independent_review` |
| `hi_ongoing_monitoring` | `ongoing_monitoring` |
| `hi_training_established` | `operator_training` |
| `hi_failsafe_presence` | `has_fail_safe` |
| `hi_appeal_process` | `appeal_process` |
| `hi_public_consultation` | `end_user_feedback` |

After the migration, all 15 OMB columns map to identically-named DB columns.
The skill's crosswalk in `.claude/skills/omb-ai-use-case-inventory/SKILL.md`
and the per-field reference in `reference/columns.md` have been updated to
reflect the new identity mappings.

## What was deferred and why

Seven columns were intentionally not renamed. The cost of updating call
sites in dashboard SQL, audit docs, and tests outweighed the benefit of
canonical naming. Each retained divergence is now flagged in SKILL.md and
reference/columns.md so future agents understand the gap is intentional.

| OMB column | Retained DB name | Rationale |
|---|---|---|
| `id` | `use_case_id` | Renaming would conflict with the table's primary key column `id`. |
| `agency_bureau` | `bureau_component` | Heavily referenced; deferred. |
| `development_stage` | `stage_of_development` | 49 refs across dashboard CASE-statement normalization + audit docs. |
| `contracting_usage` | `development_type` | 66 refs. |
| `have_ato` | `has_ato` | 33 refs incl. the dashboard ATO availability matrix. |
| `system_name_ato` | `system_name` | 82 refs across audit docs; largest deferred surface area. |
| `data_description` | `training_data_description` | 37 refs incl. test fixtures. |

## Before/after column-name samples

```sql
-- Before
SELECT use_case_id, withheld_from_public, involves_pii, pia_link
FROM use_cases
WHERE pre_deployment_testing IS NOT NULL;

-- After
SELECT use_case_id, is_withheld, has_pii, pia_url
FROM use_cases
WHERE hi_testing_conducted IS NOT NULL;
```

Note that `use_case_id` is unchanged (intentional divergence).

## Dashboard OMB-vs-IFP labeling

Concurrent with the column migration, the dashboard's `Section` component
in `dashboard/components/editorial.tsx` was extended to accept a `source`
prop and a new `SourceLegend` component was added. Every `Section` rendered
by the dashboard is now labeled with one of four chips so readers can
distinguish OMB-filed data from IFP-derived analysis:

| `source` value | Chip text | Meaning |
|---|---|---|
| `"omb"` | `OMB` | OMB-filed fields only |
| `"derived"` | `IFP` | IFP-added fields only (tags, evidence, products, hierarchy) |
| `"omb-derived"` | `OMB → IFP` | Rollups whose inputs are OMB but computation is IFP |
| `"mixed"` | `OMB + IFP` | Both kinds (use sparingly; prefer per-row labeling) |

See SKILL.md "Dashboard OMB-vs-IFP labeling" for the full chip vocabulary
and authoring conventions.

## Cross-references

- Migration script: `migrations/m002_rename_to_omb_canonical.py`
- Skill reference: `.claude/skills/omb-ai-use-case-inventory/SKILL.md`
- Per-field reference: `.claude/skills/omb-ai-use-case-inventory/reference/columns.md`
- Charter for this work: `audit/omb_alignment/CHARTER.md`
- Dashboard Section + SourceLegend: `dashboard/components/editorial.tsx`

## Rollback

If something goes wrong, the pre-migration DB is preserved at
`data/federal_ai_inventory_2025.db.pre-omb-align.bak`. The dashboard's
local DB copy at `dashboard/data/federal_ai_inventory_2025.db` was NOT
synced during this migration; production keeps working off the old schema
until integration ships.
