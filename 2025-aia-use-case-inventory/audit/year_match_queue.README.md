# `year_match_queue.csv` — 2024↔2025 deterministic-match review queue

`year_match_queue.csv` is **matcher output**, regenerated on every run of
`match_year_over_year.py` (and therefore on every `make fix`). Do not edit it
by hand — changes are overwritten.

## What it is

Phase 3 of the 2024 ↔ 2025 AI use case inventory comparison project (see
`docs/plans/2024-vs-2025-comparison/PLAN.md`) links each 2024 use case to its
2025 counterpart using three deterministic stages — exact name, fuzzy name
(score ≥ 0.85), and narrative similarity (token-set Jaccard ≥ 0.50).

This file is the **ambiguous residual**: every link the matcher assigned
`lineage_status = suggested_rename` — a 2024 row paired with the best
remaining 2025 candidate whose *name* score landed in the band
`[0.40, 0.85)`. Too weak to auto-confirm as a rename, too strong to call the
2024 use case retired. These are exactly the pairs that need semantic
judgment.

## What consumes it

**Phase 4** (`review_year_match_llm.py`, not yet built): a per-row LLM
micro-agent reads each pair, decides link / no-link / split / merge, and
persists its reasoning into `use_case_year_links.llm_reasoning`. Until then
these rows sit in `use_case_year_links` with `lineage_status = suggested_rename`
and `resolved_at IS NULL`.

## Columns

| column | meaning |
|---|---|
| `agency_abbreviation` | agency the pair belongs to (matching is strictly per-agency) |
| `uc_2024_id` | `use_cases_2024.id` of the 2024 row |
| `uc_2024_name` | its `use_case_name` |
| `uc_2025_id` | `use_cases.id` of the candidate 2025 row |
| `uc_2025_name` | its `use_case_name` |
| `name_score` | difflib name-similarity score, in `[0.40, 0.85)` |
| `narrative_score` | token-set Jaccard over the narrative paragraphs (informational) |
| `lineage_status` | always `suggested_rename` for rows in this file |

The CSV row count equals the `suggested_rename` count in
`use_case_year_links` — that invariant is checked in
`tests/test_match_year_over_year.py`.
