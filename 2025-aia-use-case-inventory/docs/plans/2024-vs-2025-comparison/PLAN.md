# 2024 ↔ 2025 AI Use Case Inventory Comparison — Plan

Status: **scoping complete, ready to execute.** Created 2026-05-20, consolidated 2026-05-21.

## Context

The dashboard is built on the 2025 federal AI use case inventory. We want to compare it against the
2024 inventory to show what changed year over year — which use cases are new, retired, continued,
or scaled, and how agency adoption shifted.

The 2024 corpus has been acquired (see below). This plan covers ingesting it and building the
comparison, in six independently-shippable phases.

## The two datasets

| | 2024 (M-24-10) | 2025 (M-25-21) |
|---|---|---|
| File | `data/raw/2024_consolidated_ai_inventory_raw_v2.csv` | per-agency files + COTS appendix |
| Rows | 2,133 individual use cases | 3,549 in `use_cases` + 900 in `consolidated_use_cases` (COTS) |
| Agencies | 41 | 36 |
| Columns | 62 (54 distinct headers — 10 repeated `"If Other, please explain."`-type) | 36 |
| Encoding | **cp1252** | UTF-8-SIG |
| Use case ID | **none — no ID column at all** | `id` (2025-minted) |

The 2024 file is the official OMB consolidated inventory, **v2** (committed 2025-01-23 with 376
rolling-update additions from ED/DOJ/DOT/NCUA; v1 was the 2024-12-18 initial drop). Source:
[`ombegov/2024-Federal-AI-Use-Case-Inventory`](https://github.com/ombegov/2024-Federal-AI-Use-Case-Inventory).
The official 2024 data dictionary is saved alongside this plan as `2024_data_dictionary.yaml`.

## What already exists in the repo

- **`getYoYGrowthData()`** (`dashboard/lib/db/analytics/distributions.ts:11`) reads a precomputed
  `agency_ai_maturity.year_over_year_growth` column.
- That column is computed in **`compute_maturity.py`** from a **hardcoded dict `OMB_2024_COUNTS`**
  (`compute_maturity.py:6`) — per-agency *total counts* from the 2024 inventory. Aggregate only;
  nothing use-case-level. This plan replaces that hardcoded dict with a real ingested source.

## The core problem: there is no join key

2024 has no IDs; 2025's IDs were minted in 2025. **Nothing links a 2024 row to a 2025 row.** Every
cross-year link must be *inferred* from `(agency, use_case_name, narrative text)`. Agencies that
re-filed under M-25-21 often rewrote their use-case names, so name matching alone is weak —
narrative-text similarity and an LLM review pass are required. The matching layer, not the ingest,
is where the real work is.

## Architecture: two new tables, no schema cramming

Do **not** merge 2024 into the `use_cases` table with a year flag — the schemas barely overlap
(62 vs 36 columns → ~60% nulls) and columns that *look* shared carry different taxonomies per year.
Instead mirror the codebase's existing "two row sets + an audit table" pattern
(`use_cases` ↔ `consolidated_use_cases` ↔ `omb_match_audit`):

- **`use_cases_2024`** — raw 2024 corpus in native M-24-10 shape, lossless `raw_json`.
- **`use_case_year_links`** — the lineage table, schema cloned from `omb_match_audit`. Nullable on
  both `uc_2024_id` and `uc_2025_id`, so it naturally expresses retired (1:0), new (0:1),
  continued (1:1), and split/merge (N:M):

```
use_case_year_links(
  id, run_at,
  uc_2024_id  INTEGER REFERENCES use_cases_2024(id),
  uc_2025_id  INTEGER REFERENCES use_cases(id),
  agency_abbreviation TEXT,
  match_method   TEXT,   -- exact_name | fuzzy_name | narrative | llm_review | manual
  match_score    REAL,
  lineage_status TEXT,   -- continued | renamed | new_2025 | retired_2024 | split | merged
  drift_fields_json TEXT,
  llm_reasoning  TEXT,
  first_seen, last_seen, resolved_at, resolution_note
)
```

## Honest-comparison caveats (surface these in any UI)

1. **The naive +66% headline (2,133 → 3,549) is not apples-to-apples.** 2025 split COTS use cases
   into a separate 900-row appendix; 2024 did not. Counting methodology changed.
2. **Impact is not comparable as a tier.** 2024's rights/safety/both/neither taxonomy ≠ 2025's
   high-impact tiers.
3. **AI type cannot be compared.** 2024 has no `ai_classification` column.
4. **Agency set changed** — 41 → 36. USAID filed 137 use cases in 2024 and is gone in 2025 (agency
   dismantled). Total-count delta is partly composition change, not growth.
5. **2024 stage values are messy** (cp1252 mojibake, letter prefixes) — canonicalize before any
   stage comparison; `_canonicalize_field` in `omb_consolidated_match.py` already does this.

---

# Execution — six phases

```
Phase 0  Crosswalk            ─┐
Phase 1  Ingest raw 2024       ├─ "Option A" — honest aggregate comparison. ~3 days.
Phase 2  Aggregate comparison ─┘   ◄── DECISION GATE: see real numbers, then commit to B or stop
Phase 3  Deterministic match  ─┐
Phase 4  LLM adjudication      ├─ "Option B" — use-case-level lineage. ~2 weeks.
Phase 5  Dashboard surface    ─┘
```

Phases 0–2 are a complete, valuable deliverable on their own. Each phase ends green (`make fix`
passes, tests pass) and is one reviewable PR. After a DB-changing phase, sync the DB into
`dashboard/data/`.

## Phase 0 — Schema crosswalk & comparability audit

**Goal:** know exactly which of the 62 2024 columns can be compared to 2025, before writing a loader.

**Deliverables**
- `column_maps_2024.py` — new module, sibling to `column_maps.py`. Maps each 2024 header →
  snake_case column, tags each with `comparability`:
  `directly_comparable | recoded | 2024_only | 2025_only`.
- Recode tables for the `recoded` columns (impact taxonomy, stage-value drift).
- `COMPARABILITY-MATRIX.md` (this folder) — human-readable table of all 62 columns and dispositions.
- `tests/test_column_maps_2024.py` — every 2024 header accounted for; recode maps unit-tested.

**Inputs:** `2024_data_dictionary.yaml`, the live CSV header, the `omb-ai-use-case-inventory` skill.
**Reuses:** structure + fuzzy-matcher pattern of `column_maps.py`.
**Verification:** `pytest tests/test_column_maps_2024.py`; no 2024 column silently dropped.
**Shippable independently:** yes (pure module, no DB change). **Effort:** ~1 day.

## Phase 1 — Ingest the raw 2024 corpus

**Goal:** the 2,133 2024 use cases queryable in the DB, lossless.

**Deliverables**
- `migrations/m008_use_cases_2024.py` — additive migration creating `use_cases_2024` (M-24-10 shape
  per the crosswalk + `agency_id` FK, `slug`, `raw_json`, `created_at`; indexes on `agency_id`,
  `slug`).
- `load_2024.py` — loader: cp1252 decoding, `agency_id` resolution (reuse `normalize_agency`),
  `slug` generation, `raw_json` preservation. Idempotent (clear-and-reload).
- `Makefile` — new `load_2024.py` step after `load_inventories.py`.
- `tests/test_load_2024.py` — row count = 2,133; encoding sanity; all 41 agencies resolve.

**Watch:** 41 agencies in 2024 vs 36 in 2025 — some (e.g. USAID) won't be in `agencies`. Recommend
seeding the missing ones so per-agency queries don't silently drop rows.

**Reuses:** `load_inventories.py` patterns; `omb_consolidated_match.normalize_agency`; `raw_json`
convention.
**Verification:** `make fix` green; `COUNT(*) FROM use_cases_2024` = 2,133; spot-check 5 rows.
**Shippable independently:** yes. **Effort:** ~1 day.

## Phase 2 — Real aggregate comparison ("Option A" complete)

**Goal:** trustworthy year-over-year *aggregates*; the hardcoded baseline gone.

**Deliverables**
- `compute_maturity.py` — replace the hardcoded `OMB_2024_COUNTS` dict with
  `SELECT agency, COUNT(*) FROM use_cases_2024 GROUP BY agency`. YoY column becomes self-maintaining.
- YoY aggregate rollups over **comparable dimensions only** (per Phase 0): total counts, per-agency
  counts, stage mix, contract-vs-in-house. Small `year_comparison` rollup table or query-layer
  computation — decide based on dashboard needs.
- Caveat metadata: each aggregate flagged clean vs lossy (impact, AI type are not aggregatable YoY).

**Reuses:** `compute_maturity.py` aggregation patterns; `_canonicalize_field` for stage
normalization.
**Verification:** YoY numbers reconcile by hand for 3 agencies; `make fix` green.
**Shippable independently:** yes — **the Option A milestone. Decision gate here.** **Effort:** ~0.5–1 day.

## Phase 3 — Lineage table & deterministic matching

**Goal:** every 2024 row linked to its 2025 counterpart where a confident match exists; rest queued.

**Deliverables**
- `migrations/m009_use_case_year_links.py` — the `use_case_year_links` table.
- `match_year_over_year.py` — per-agency matcher, three deterministic stages: (1) exact name
  (`normalize_name` equality), (2) fuzzy name (difflib ≥ 0.85), (3) narrative similarity
  (problem-statement + benefits + system-outputs) for residuals. Confident matches →
  `use_case_year_links`; ambiguous → review queue.
- `audit/year_match_queue/` — review-queue CSVs for the residual.
- `Makefile` — `match_year_over_year.py` step after the OMB consolidated match.
- `tests/test_match_year_over_year.py` — synthetic pairs: exact, rename, retired, new.

**Reuses:** `omb_consolidated_match.py` end-to-end — `normalize_agency`, `normalize_name`,
`name_match_score`, `classify_match`, `detect_drift`.
**Verification:** match-rate report; manual spot-check of 20 fuzzy matches across the top-5 agencies.
**Shippable independently:** yes (partial lineage is useful; queue is explicit). **Effort:** ~3–5 days.

## Phase 4 — LLM adjudication, split/merge, final classification

**Goal:** resolve the ambiguous residual; assign every link a final `lineage_status` and drift.

**Deliverables**
- `review_year_match_llm.py` — per-row LLM micro-agent over the Phase 3 queue. Decides
  link / no-link / split / merge; **persists reasoning** to `use_case_year_links.llm_reasoning`.
  Batched per-agency (parallelizable — multi-agent if desired).
- Split/merge resolution — N:M links written; `lineage_status` set to `split` / `merged`.
- Final classification — `continued | renamed | new_2025 | retired_2024 | split | merged` for every
  row; `retired_2024` cross-checked against 2025's own `Retired` stage.
- `drift_fields_json` — via `detect_drift` over **directly-comparable columns only**; recoded-column
  drift flagged lossy.
- `tests/test_year_lineage_classification.py`.

**Reuses:** the established regex/fuzzy-then-LLM-review pattern (LLM adjudicates the residual,
reasoning persisted for audit); `detect_drift`.
**Verification:** counts reconcile — 2024 total = continued + renamed + retired + merged-inputs;
2025 total = continued + renamed + new + split-outputs. Manual review of all `split`/`merged`.
**Shippable independently:** yes. **Effort:** ~3–5 days.

## Phase 5 — Dashboard comparison surface

**Goal:** the comparison visible and honestly framed in the dashboard.

**Deliverables**
- New `/compare-years` route (or extend the existing YoY chart — decide during the phase). Two
  confidence tiers: **aggregate rollups always** (counts, stage mix, agency growth); **use-case
  lineage where confident** (continued / new / retired lists, per-agency).
- Caveat surfacing — the caveats above rendered in-UI via the existing `Section` `source`-chip
  vocabulary.
- `lib/db/` query module + colocated `_view-model.ts` (per current dashboard conventions).
- DB sync into `dashboard/data/`.

**Reuses:** dashboard view-model + `lib/db` entity-module conventions; existing YoY chart; the
`Section` provenance-chip system.
**Verification:** `npm run typecheck && npm run build`; click-through; numbers match ETL rollups.
**Shippable independently:** yes — the user-facing payoff. **Effort:** ~2–3 days.

---

## Sequencing & effort

- Strict order 0 → 1 → 2; **decision gate after 2** (look at real numbers, commit to 3+ or stop).
- Strict order 3 → 4 → 5. Phase 4's LLM review batches are per-agency and parallelizable.
- Each phase: one PR, `make fix` green, sync DB to dashboard if the DB changed.

| | Phases | Effort |
|---|---|---|
| Option A — aggregate comparison | 0–2 | ~3 days |
| Option B — use-case lineage | 3–5 | ~+2 weeks |
| Full | 0–5 | ~2.5–3 weeks |

## Migration numbering

Next free migration numbers are **m008** (`use_cases_2024`) and **m009** (`use_case_year_links`) —
`m006`/`m007` already exist.
