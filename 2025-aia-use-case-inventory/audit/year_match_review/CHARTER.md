# Year-match review charter — Phase 4

You are one of ~6-8 parallel adjudication agents resolving the 2024 ↔ 2025
AI use case inventory lineage. Your job: triage your agency-batch slice and
emit `recommendations.json` so the integration script can stage the final
use-case-level lineage.

This pass mirrors `audit/linkage_pass_2026-05/CHARTER.md` (the prior
4-agent linkage pass). Read that file first if you haven't seen the
seed → agents → integrate → apply pattern.

## Why this pass exists

`match_year_over_year.py` (Phase 3) is a deterministic matcher. It linked
1,139 use cases as `continued` and 237 as `renamed` with confidence, but
left **411 `suggested_rename`** pairs in an ambiguous mid-confidence band
plus **346 `retired_2024`** and **1,762 `new_2025`** residual rows. The
deterministic matcher is also strictly 1:1 — it cannot express split or
merge, and it cannot recover a genuine match it scored below threshold.

Phase 4 resolves that residual:

- **Confirm or reject the 411 `suggested_rename` pairs** — is each one
  genuinely the same use case across years, or two unrelated use cases the
  fuzzy matcher paired by name overlap?
- **Detect split / merge** — one 2024 use case that became multiple 2025
  use cases (split), or multiple 2024 use cases consolidated into one 2025
  use case (merge). These are N:M and the deterministic matcher cannot see
  them.
- **Recover matcher misses** — a `retired_2024` row and a `new_2025` row
  that are actually the same use case, missed because the 2025 filing
  rewrote the name and narrative enough to fall below threshold.

## Scope note

You resolve the 411-row `suggested_rename` queue and detect split/merge +
missed matches from each agency's residual. You do **not** row-by-row
re-verify all 1,762 `new_2025` rows — Phase 3's QA already sampled those
and found them genuine. The `retired_2024` / `new_2025` lists are in your
slice as **context** so split/merge and recoveries are visible; a residual
row with no decision keeps its Phase-3 classification.

## Slice ownership (do NOT cross slices)

Each agent owns one agency batch. The batch → agency assignment and
per-batch row counts are in `inputs/_manifest.csv`; your working set is
`inputs/batch_<N>_<slug>.json`. Write ONLY to your own
`agent_<slice>/` subdirectory. Do not touch the DB or other agents'
output.

## Inputs available to every agent

- `data/federal_ai_inventory_2025.db` (READ-ONLY). Query `use_cases`,
  `use_cases_2024`, `use_case_year_links`, `agencies`.
- Your slice's `inputs/batch_<N>_<slug>.json`. It holds, for every agency
  in your batch:
  - `suggested_rename` — every queued pair: the 2024 + 2025 `slug`, names,
    narratives, and `name_score`.
  - `retired_2024` — every retired 2024 row: `slug`, name, narrative.
  - `new_2025` — every new 2025 row: `slug`, name, narrative.

Everything is keyed on **`slug`** (`use_cases.slug`,
`use_cases_2024.slug`) plus `agency_abbreviation` — NOT row id. Row ids are
not stable across `make fix`; the apply script resolves slug → current id.

## Decision schema

Per decision, write one object to `recommendations.json`. Decision
`action` ∈:

| Action | Meaning | DB effect (applied by `apply_year_match_review.py`) |
|---|---|---|
| `confirm_rename` | A `suggested_rename` pair is genuinely the same use case. | The link → `lineage_status='renamed'`, `match_method='llm_review'`. |
| `reject_rename` | The pair is two unrelated use cases. | The link is deleted; the 2024 slug → a fresh `retired_2024` row, the 2025 slug → a fresh `new_2025` row. |
| `recover_match` | A `retired_2024` slug and a `new_2025` slug that the matcher MISSED are actually the same use case. | The separate `retired_2024` + `new_2025` rows are deleted; one `renamed` link is inserted. |
| `split` | One 2024 use case became multiple 2025 use cases. | The affected links are replaced with N `split` rows — same `uc_2024_id`, distinct `uc_2025_id`. |
| `merge` | Multiple 2024 use cases were consolidated into one 2025 use case. | The affected links are replaced with N `merged` rows — distinct `uc_2024_id`, same `uc_2025_id`. |

Any row with no decision keeps its Phase-3 classification.

### Decision principles

1. **Read the actual narratives before deciding.** Name overlap alone is
   weak — agencies systematically rewrote use-case names under M-25-21.
   Two use cases with similar names but disjoint narratives are NOT the
   same use case (`reject_rename`); two with rewritten names but the same
   problem + outputs ARE (`confirm_rename`).
2. **`recover_match` requires real bilateral evidence.** A `retired_2024`
   and a `new_2025` row are the same use case only if the narratives
   describe the same system / problem / outputs. Do not recover on a
   single shared keyword.
3. **`split` / `merge` need ≥2 rows on one side.** A split is one 2024
   slug → ≥2 distinct 2025 slugs; a merge is ≥2 distinct 2024 slugs → one
   2025 slug. List every slug on both sides.
4. **One slug, one decision.** A given 2024 or 2025 slug must appear in at
   most one decision. The integration script flags conflicting decisions
   on a slug to `integration/conflicts.csv`.
5. **`confidence`** — `high` / `medium` / `low`. **`reasoning`** — 1-2
   sentences citing the narrative evidence (the persisted-reasoning
   convention; it lands in `use_case_year_links.llm_reasoning`).

## Output schema

`agent_<slice>/recommendations.json` is a JSON array of decision objects:

```json
[
  {
    "action": "confirm_rename",
    "agency_abbreviation": "VA",
    "uc_2024_slugs": ["va-clinical-note-summarizer"],
    "uc_2025_slugs": ["va-ambient-clinical-documentation"],
    "confidence": "high",
    "reasoning": "Both describe ambient transcription of clinician-patient encounters into draft notes; the 2025 filing renamed it and expanded the narrative."
  },
  {
    "action": "split",
    "agency_abbreviation": "DOI",
    "uc_2024_slugs": ["doi-wildlife-imagery-classifier"],
    "uc_2025_slugs": ["doi-bird-species-id", "doi-marine-mammal-id"],
    "confidence": "medium",
    "reasoning": "The single 2024 imagery classifier was filed in 2025 as two separate species-specific use cases."
  }
]
```

Field rules:
- `uc_2024_slugs` / `uc_2025_slugs` are always **lists** (length 1 for
  `confirm_rename` / `reject_rename`; one side has ≥2 for `split` /
  `merge`; both length 1 for `recover_match`).
- `confirm_rename` / `reject_rename` — both lists length 1 (the existing
  `suggested_rename` pair).
- `recover_match` — both lists length 1 (the retired + new pair to link).
- `split` — `uc_2024_slugs` length 1, `uc_2025_slugs` length ≥2.
- `merge` — `uc_2024_slugs` length ≥2, `uc_2025_slugs` length 1.

Also write `agent_<slice>/notes.md`: count per `action`, surprising
findings (notable splits/merges, recoveries), and anything you flagged
low-confidence.

## Final-summary contract

Final reply ≤300 words: count of decisions by `action`, the most
surprising findings (notable splits/merges + recoveries), and any pairs
you could not confidently resolve.
