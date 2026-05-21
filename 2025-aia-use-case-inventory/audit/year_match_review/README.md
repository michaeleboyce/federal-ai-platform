# Year-match review — Phase 4

Multi-agent adjudication pass that resolves the ambiguous residual of the
2024 ↔ 2025 AI use case inventory matcher and assigns every link its final
`lineage_status`. Phase 4 of the 2024↔2025 comparison project (see
`docs/plans/2024-vs-2025-comparison/PLAN.md`).

The deterministic matcher (`match_year_over_year.py`, Phase 3) leaves
`continued` / `renamed` confidently linked but queues **411
`suggested_rename`** pairs and cannot express split/merge or recover its
own misses. This pass mirrors `audit/linkage_pass_2026-05/` — a
seed → dispatched-agents → integrate → apply pipeline.

## Pipeline order

1. **`scripts/seed_year_match_review.py`** — one-off, orchestrator-driven.
   Emits per-agency-batch review slices to `inputs/batch_*.json` +
   `inputs/_manifest.csv`. Idempotent (regenerated each run).
2. **~6-8 Claude Code adjudication agents in parallel** — one per
   agency-batch. Each reads its `inputs/batch_<N>_<slug>.json`, queries the
   DB for context, and writes `agent_<slice>/recommendations.json` +
   `notes.md`. Decision schema is in `CHARTER.md`.
3. **`scripts/integrate_year_match_review.py`** — reads every
   `agent_*/recommendations.json`, validates the schema, dedupes, flags
   conflicting decisions on a slug to `integration/conflicts.csv`, and
   writes the single **`integration/proposed_lineage.csv`** — the
   committed, replayable source of record.
4. **`scripts/apply_year_match_review.py`** — reads
   `integration/proposed_lineage.csv`, resolves slugs → current ids,
   overlays the decisions onto `use_case_year_links` (on top of the
   matcher's freshly-rebuilt baseline). Folds in the final-classification
   + retired cross-check tail. Idempotent — runs every `make fix`.
5. **`compute_year_lineage_drift.py`** — deterministic. Computes
   field-level drift over the 21 directly-comparable column pairs for every
   1:1 `continued` / `renamed` link and writes `drift_fields_json`.

Steps 4 and 5 are wired into `Makefile fix` after `match_year_over_year.py`
so future rebuilds replay this pass. Steps 1-3 are orchestrator-driven,
not `make` steps (same convention as the linkage-pass scripts).

## Decision actions

`confirm_rename`, `reject_rename`, `recover_match`, `split`, `merge` —
see `CHARTER.md` for each action's meaning and DB effect.

## Slug-keyed, not id-keyed

`use_cases` / `use_cases_2024` row ids are wiped-and-reloaded every
`make fix`, so they are not stable. The seed slices, the agent
recommendations, and the committed `proposed_lineage.csv` all key on
`(slug, agency_abbreviation)`. The apply script resolves slug → current id
on each run.

## Reconciliation invariant

After apply, every `use_cases_2024` row appears as `uc_2024_id` in **≥1**
link and every `use_cases` row as `uc_2025_id` in **≥1** link. (Phase 3's
`==1` relaxes to `≥1` because split/merge are intentionally N:M.) The
apply script asserts this.

## Files

```
audit/year_match_review/
├── CHARTER.md                ← agent decision schema
├── README.md                 ← you are here
├── inputs/
│   ├── _manifest.csv          batch → agency assignment + row counts
│   └── batch_<N>_<slug>.json  per-batch agent working set
├── agent_<slice>/{recommendations.json, notes.md}   (Stage 2 output)
└── integration/
    ├── proposed_lineage.csv          committed source of record
    ├── conflicts.csv                 conflicting decisions on a slug
    ├── classification_flags.csv      retired cross-check flags (non-blocking)
    └── summary.md
```

## Replay safety

`proposed_lineage.csv` is committed to the repo and replayed idempotently
by `apply_year_match_review.py` on every `make fix`, on top of the
deterministic matcher's freshly-rebuilt baseline. With no agent output yet
(empty/absent `agent_*/` and no `proposed_lineage.csv`), the integrate /
apply / drift scripts run as clean no-ops — the matcher baseline is left
intact.
