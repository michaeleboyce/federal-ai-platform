# Linkage Pass — May 2026

4-agent labeling pass + 2-reviewer verification of the product-linkage gap
in `data/federal_ai_inventory_2025.db`. Source-of-record CSVs under
`integration/` are applied by `scripts/apply_linkage_pass_2026_05.py` and
replayed in the `make fix` recovery section.

## Headline outcome

| Metric | Before | After | Δ |
|---|---:|---:|---:|
| products | 316 | 536 | **+220** |
| products with parent_product_id | 42 | 78 | **+36** |
| use_case_products edges | 962 | 1,164 | **+202** |
| consolidated_use_case_products edges | 605 | 627 | **+22** |
| individual use_cases with ≥1 link | 832 (23.4%) | 1,032 (29.1%) | **+200** |
| consolidated entries with ≥1 link | 369 (41.0%) | 386 (42.9%) | +17 |

## Per-agent breakdown

| Agent | Slice | Input rows | Decisions | Key outputs |
|---|---|---:|---:|---|
| A | Named-vendor individual use_cases | 272 | 272 | 174 add_product, 69 link, 8 false_positive, 21 unclear |
| B | Mention-only individual + named consolidated | 130 | 152 | 37 add_product, 39 link, 6 add_alias, 49 false_positive, 21 unclear |
| C | Dark-sample individual (random 200) | 200 | 200 | 12 add_product, 3 link, 1 add_alias, 2 false_positive, 182 unclear |
| D | Existing-catalog hierarchy review | 316 | 7 | 7 add_hierarchy_edge |

Aggregate integration (post-dedup, post-fixup): 220 new products, 38
hierarchy edges, 7 aliases, 220 links (after stale-ID remap).

## Pipeline order

1. `scripts/seed_linkage_pass_inputs.py` — one-off; emits `inputs/*.csv`.
2. Four Claude Code subagents in parallel; each writes
   `agent_{a,b,c,d}/recommendations.json` + `notes.md`.
3. `scripts/integrate_linkage_pass.py` — dedupes, splits to 4 CSVs under
   `integration/`. Zero conflicts on first run.
4. `scripts/remap_linkage_pass_ids.py` — fixes stale use_case_ids when
   the DB was re-keyed between Phase 0 and Phase 4 (resolves 602 IDs).
5. Two Claude Code reviewer subagents in parallel — `validity_findings.md`
   (mechanical correctness) and `coverage_findings.md` (semantic
   defensibility, 98% per-agent score).
6. `scripts/fixup_linkage_pass_validity.py` — applies Reviewer V's 52
   FAIL fixes (5 umbrella parents, 4 missing catalog targets, product_type
   correction, 3 mal-formed link drops).
7. `scripts/apply_linkage_pass_2026_05.py [--apply]` — dry-run by default;
   `--apply` writes to DB and appends to canonical CSVs. Idempotent.
8. Added to `Makefile fix` after `apply_product_gap_review.py` so future
   rebuilds replay this pass.

## Calibration verdict — dark sample

Agent C found 16 actionable rows of 200 sampled (8%). Extrapolating to the
2,347-row "dark" population (individual use_cases with blank/generic
vendor_name AND no catalog vendor mention in name/system): **~190
additional links hide in the long tail**, with 50% concentrated in **VA
medical-imaging** vendors (Siemens MAGNETOM, Canon Aquilion, Hologic,
Planmeca, Verathon, Cortechs). A targeted VA-medical second pass is the
highest-ROI follow-up.

## Hierarchy edges Agent D missed

Reviewer C flagged that Agent D was conservative (7 explicit edges); the
integration script harvested 31 more from `proposed_parent_canonical_name`
fields embedded in A/B/C's `add_product` proposals. Total: 38 edges. Still
missing per Reviewer C: an AWS umbrella parent for the 9 AWS sub-services,
Google Workspace/Maps/Translate parenting, Microsoft 365 / Power Platform
top-level parenting. Future pass.

## Files

```
audit/linkage_pass_2026-05/
├── CHARTER.md
├── README.md                                  ← you are here
├── inputs/
│   ├── slice_a_named_vendor_individual.csv    272
│   ├── slice_b_mention_only_individual.csv     77
│   ├── slice_b_named_consolidated.csv          53
│   ├── slice_c_dark_sample.csv                200
│   └── existing_catalog_snapshot.csv          316
├── agent_a/{recommendations.json, notes.md}
├── agent_b/{recommendations.json, notes.md}
├── agent_c/{recommendations.json, notes.md}
├── agent_d/{hierarchy_proposals.json, notes.md}
├── integration/
│   ├── proposed_links.csv                     220 (after fixup)
│   ├── proposed_new_products.csv              223 (after fixup; 220 applied)
│   ├── proposed_aliases.csv                     7
│   ├── proposed_hierarchy_edges.csv            38
│   ├── conflicts.csv                            0
│   └── summary.md
└── review/
    ├── validity_findings.md                   (52 FAIL → 0 after fixup)
    └── coverage_findings.md                   (GREEN LIGHT)
```

## Replay safety

All linkage decisions are keyed on `canonical_name`. The catalog CSV
(`data/expanded_product_catalog.csv`) and hierarchy CSV
(`data/product_hierarchy_edges.csv`) are the source of truth and survive
`build_lookups.py` re-keys. `apply_linkage_pass_2026_05.py` is idempotent
and runs in the `make fix` recovery chain.
