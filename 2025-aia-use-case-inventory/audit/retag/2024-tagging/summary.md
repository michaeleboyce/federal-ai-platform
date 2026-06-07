# 2024 use-case tagging backfill — summary

This document records the multi-wave agent-driven tagging of the 2,133 rows
in `use_cases_2024` with the IFP analytical tag schema, completed on
2026-05-26. The plan-of-record is `docs/plans/2024-tagging/PLAN.md`. The
operational plan with checkpoints is at `~/.claude/plans/ok-make-a-proper-synthetic-gem.md`.

## Final state

`use_case_tags_2024_canonical` returns exactly **2,133 rows** — one
canonical tag per 2024 use case. Wave 1 is canonical for 1,500 rows;
Wave 3 reconciliation supersedes Wave 1 for 633 rows.

## Wave counts in `use_case_tags_2024`

| Wave | Rows | Notes |
|---|---|---|
| `0-calibration` | 300 | 50 rows × 6 agents — excluded from canonical view |
| `1` | 2,133 | One per use case, six agency-partitioned agents |
| `2a` | 567 | QA flags on matched 2024↔2025 pairs |
| `2b` | 66 | QA flags on retired_2024 rows |
| `3` | 633 | Reconciliation for everything Wave 2 flagged |
| **Total** | **3,699** | |

## Calibration agreement

All four headline metrics cleared the PLAN.md thresholds with significant
margin on a 50-row stratified sample tagged by all 6 agents:

| Field | Avg pairwise agreement | Threshold |
|---|---|---|
| `is_generative_ai` | 97.7% | 85% |
| `ai_sophistication` | 91.7% | 70% |
| `entry_type` | 88.5% | 70% |
| `deployment_scope` | 91.5% | 70% |

Lowest pairwise agreement on any field was 82% (`entry_type`, two pairs).
Full detail in `audit/retag/2024-tagging/calibration.md`. The same handful
of rows showed up as "genuinely ambiguous" in every agent's flagged list
(NOAA cyber, DOT TrAIN, FERC interconnection, DOT governance) —
consistent signal that the rubric is well-calibrated.

## Wave 2 flagging rates

| Partition | Input | Flagged | Rate |
|---|---|---|---|
| 2a continued | 1,139 | 430 | 38% |
| 2a renamed/split | 286 | 137 | 48% |
| 2b retired_2024 | 710 | 66 | 9% |

Wave 2a flag types (430+137 rows total):
- `material_divergence`: 427 (Wave 1 ≠ 2025 tag in a way that matters)
- `drift_legitimate`: 334 (genuine cross-year posture change)
- `tagging_error_2025`: 38 — routed to side queue (see below)
- `tagging_error_2024`: 15 (Wave 1 missed something)

Wave 2b flag types (66 rows):
- `internal_inconsistency`: 39 (Wave 1 tag self-contradictory)
- `misclassified_lifecycle`: 27 (scope vs `dev_stage` mismatch)
- `tool_vendor_unverified`: 1 (Wave 1 hallucinated a vendor)

## Wave 3 reconciliation

633 flagged rows (211 × 3 partitions) reconciled to a final canonical
tag. Decision distribution across all three partitions:

- **Kept Wave 1 tag**: ~330 rows (mostly `drift_legitimate` cases — the
  2024 reality stays even when 2025 evolved)
- **Adopted Wave 2 proposed correction**: ~60 rows (`tagging_error_2024`
  + clear `internal_inconsistency` resolutions)
- **Adopted 2025 reading**: ~30 rows (narrative supports the 2025 tag
  over the Wave 1 tag)
- **Lifecycle realignments**: ~25 rows (scope adjusted to match
  `dev_stage`)
- **Other narrative-grounded corrections**: ~10 rows

Confidence on Wave 3 rows: ~280 high / ~230 medium / ~10 low.

## Headline 2024 IFP-tag stats (canonical)

- **Generative AI use cases**: 520 / 2,133 (24%)
- **General LLM sophistication**: 511 (24%)
- **Classical ML sophistication**: 663 (31%)
- **Enterprise-wide deployment scope**: 58 (2.7%)
- **Microsoft Copilot deployments**: 22

### Per-agency top-10 (canonical)

| Agency | Total | GenAI | General LLM | Enterprise-wide |
|---|---|---|---|---|
| HHS | 271 | 109 | 106 | 1 |
| DOJ | 240 | 34 | 37 | 2 |
| VA | 229 | 39 | 35 | 0 |
| DHS | 183 | 29 | 29 | 0 |
| DOI | 180 | 22 | 22 | 0 |
| USAID | 137 | 21 | 21 | 0 |
| USDA | 89 | 4 | 5 | 0 |
| DOE | 79 | 25 | 26 | 0 |
| DOL | 70 | 13 | 11 | 0 |
| DOT | 66 | 17 | 17 | 3 |

### Silently-dropped live GenAI systems

The 2024-tagging pass surfaced 15+ rows where the agency filed a system
in 2024 with `dev_stage='Operation and Maintenance'` (or similar) AND the
system is `retired_2024` (absent from 2025) AND we tagged it
`is_generative_ai=1`. These are *live GenAI systems that the agency
quietly dropped* between cycles — high-signal for the dashboard.

Examples in the canonical view:

- DOI/OCIO **DOIChatGPT** (production-stage AI chatbot — disappeared)
- DHS/USCIS **Large Language Models for an Officer Training Tool**
- DOJ **FOIA.gov Virtual Assistant**, **Evidence.com - Axon**
- DOI/NPS **Adobe Firefly** images, NPS acquisition workload tool
- USPTO **Enriched Citation**

(Full list available via the SQL in this file's appendix.)

## tagging_error_2025 side queue

38 rows where Wave 2 judged that the 2025 IFP tag is wrong (not the 2024
tag). Exported to `audit/retag/2024-vs-2025-divergence/queue.csv` for a
separate manual remediation pass. Out of scope for this plan's
deliverables.

## Schema

- **Migration**: `migrations/m014_use_case_tags_2024.py` (applied as
  `014_use_case_tags_2024`)
- **Table**: `use_case_tags_2024` — mirrors `use_case_tags` minus 2025-only
  FKs, with provenance columns (`wave`, `tagged_by_agent`, `reasoning`,
  `quality_flags_json`, `confidence`)
- **View**: `use_case_tags_2024_canonical` — picks the latest non-calibration
  wave per use case (Wave 3 > 2a/2b > 1)
- **Unique key**: `(use_case_id_2024, wave, tagged_by_agent)` — the
  loader upserts on this key, so re-running an agent's CSV refreshes
  that agent's row instead of duplicating

## Reproducibility

The full pipeline is scripts:
- `scripts/build_2024_tagging_partitions.py` — agency partition CSVs
- `scripts/build_2024_calibration_set.py` — stratified-sample calibration CSV
- `scripts/build_wave2_inputs.py` — Wave 2 QA inputs (2024 + 2025 joined)
- `scripts/build_wave3_inputs.py` — Wave 3 reconciliation inputs from flagged Wave 2
- `scripts/load_2024_tags.py` — CSV → DB loader, idempotent on unique key
- `scripts/calibration_agreement.py` — pairwise agreement math
- `scripts/resolve_2024_tag_ids.py` — re-resolve ids by slug after parallel-agent rebuilds

Agent CSVs are preserved under `audit/retag/2024-tagging/`:
- `calibration/[A-F].csv` — calibration outputs
- `wave1/[A-F].csv` — Wave 1 outputs
- `wave2a/{continued,renamed_split}.csv` — Wave 2a flagged outputs
- `wave2b/retired.csv` — Wave 2b flagged outputs
- `wave3/{P1,P2,P3}.csv` — Wave 3 reconciled outputs

## Caveats and follow-ups

1. **2024 `commercial_ai` is task-categorical, not vendor-named.** All 6
   Wave 1 agents independently flagged that the OMB 2024 schema for this
   column is a checkbox of AI *tasks* ("Searching for information using
   AI", "Summarizing the key points…"), not a vendor product list. Vendor
   parsing leaned heavily on narrative free-text. Roughly 90% of rows
   have no parseable vendor.
2. **2 silently-dropped LLM clusters worth deeper look**: DOI/OCIO
   DOIChatGPT (3 production rows, all retired_2024) and HHS HHSGPT
   (Operation and Maintenance stage, retired).
3. **The tagging_error_2025 side queue (38 rows)** is a separate
   workstream — most are HHS/CDC and DOC entries where 2024 narrative
   clearly says GenAI but 2025 IFP tagging dropped to non-GenAI.
4. **Future Wave-2 refinement candidate**: the `entry_type` boundary
   (custom_system vs bespoke_application vs product_deployment) had the
   most divergence in calibration. Future passes should refine the
   rubric on this specifically.

## Mid-run incident — parallel-agent ID rotation

During execution, two parallel agents' work briefly intersected with
this pipeline:

1. A pre-existing m015 migration appeared mid-run and was applied along
   with m014 by the migration runner (no harm — m015 only touches link
   tables, orthogonal to this work).
2. After Wave 1 was loaded, a parallel "generic_vendor_retag" wiped all
   Wave 1 rows from `use_case_tags_2024`. Recovery: re-ran the loader
   against the saved Wave 1 CSVs. Pattern documented in CLAUDE.md §
   Multi-agent safety.

The `scripts/resolve_2024_tag_ids.py` helper (id remapping by `slug`)
was written for this scenario and used once when `use_cases_2024.id`
rotated between calibration CSV generation and the calibration load.
