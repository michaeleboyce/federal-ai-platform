# Phase 0 baseline — captured 2026-05-03

`pytest tests/ audit/checks/ -q` reported **83/90 tests passing (7 pre-existing failures)**.

Full output captured at `/tmp/phase0-pytest-baseline.txt` at the time of capture.

This baseline is the comparison target for Phase 6's final test pass: any new failure
introduced by the OMB ingest implementation must be a *new* failure, not one of these.

## Pre-existing failures (7)

All seven are in `audit/checks/` (not `tests/`) and are baseline-drift assertions from
prior data-pipeline work (COTS ingest, hierarchy backfill, retag rounds). None block
Phase 1 because none touch `test_load_inventories.py`, `test_db.py`, or any `*omb*`
test file (verified: those files do not exist yet).

| Test | Failure | Likely cause |
|---|---|---|
| `audit/checks/check_refactor_quality.py::test_primary_product_cache_is_derived_from_edges` | cache-derivation invariant violated | drifted after product-catalog cleanup |
| `audit/checks/check_refactor_quality.py::test_generated_db_snapshot_matches_current_counts` | snapshot MD missing `canonical_products: 240` | snapshot hasn't been regenerated since latest catalog change |
| `audit/checks/check_row_count.py::test_use_cases_total_matches_baseline` | `use_cases count 3549 diverged from baseline 3616 (±50)` | baseline was set when the source data had 3,616 rows; current 3,549 is the post-cleanup state |
| `audit/checks/check_row_count.py::test_consolidated_use_cases_total_matches_baseline` | `consolidated_use_cases count 900 vs baseline 192 (±20)` | the COTS file ingest (commit `303fc6a`) added 45 agencies × 20 templates = 900 consolidated rows; baseline was pre-COTS |
| `audit/checks/check_row_count.py::test_agencies_total_matches_baseline` | `agencies count 68 vs baseline 60 (±5)` | hierarchy seed expanded the agency table |
| `audit/checks/check_row_count.py::test_use_case_tags_total_matches_baseline` | `use_case_tags count 4449 vs baseline 3808 (±100)` | retag passes added tags |
| `audit/checks/check_scope_consistency.py::test_enterprise_wide_total_consolidated_under_loose_ceiling` | `enterprise_wide consolidated rows = 468 vs ceiling 130` | scope-tagging change after the COTS ingest pushed enterprise_wide tagging way up |

## Critical-area sweep (verification step F4 from the Phase 0 plan)

Confirmed by `ls tests/ | grep -iE "load_inv|test_db|omb"` returning **no results** — there
are no test files in any of the areas the OMB ingest will touch, so none of the 7
pre-existing failures sit in our path.

## Implication for Phase 6 verification

Phase 6 should target **83 passing / 7 failing as the floor**. New OMB-ingest tests
(Phase 1: `test_migration_m004.py`, Phase 2: `test_omb_consolidated_match.py`,
Phase 3: `test_load_omb_consolidated.py`) should all pass and bring the total to
**~108 passing / 7 failing** assuming no regression. The 7 pre-existing failures
should NOT be addressed by this work — they're separate data-baseline questions that
need their own triage pass.

If after Phase 6 the row-count baselines drift further (likely, since `omb_consolidated_rows`
adds ~3,611 rows to a new table — which doesn't affect the existing `use_cases` /
`consolidated_use_cases` / `agencies` / `use_case_tags` baselines, so they should be unchanged),
that's a *separate* baseline update and is out of scope for this plan.
