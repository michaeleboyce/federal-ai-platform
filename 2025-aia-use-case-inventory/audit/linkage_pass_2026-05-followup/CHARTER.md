# Linkage-pass follow-up charter — May 2026 (2nd sprint)

You are one of three parallel labeling agents (WS1 / WS2 / WS3) working a
focused follow-up to the prior linkage pass. Read
`audit/linkage_pass_2026-05/CHARTER.md` first — the schema and rubric
carry forward; this charter just lists the differences.

## Why this pass

The first pass closed coverage from 23.4% → 30.4%. Reviewer C surfaced
three follow-ups that didn't fit:

- **WS1**: ~50% of the 16 dark-sample hits were VA medical-imaging
  vendors. VA has 323 dark-unlinked individual rows + ~30-40 unlinked
  consolidated rows. Sweep specifically there.
- **WS2**: existing catalog has parent-less products in major vendor
  families (Microsoft, Google, AWS, Adobe). Agent D was conservative;
  this is a broader sweep with explicit umbrella-product propose
  authority.
- **WS3**: bare-name aliases on parent products are thin (Microsoft
  Azure Platform has only 1 alias). Add `Vertex AI`, `Azure`, etc.
  cautiously, with collision checking against the full alias set.

A separate code change (WS4 — not your concern) is adjusting the
production linker scan to include `expected_benefits` and fixing a
non-word-boundary bug in the seed candidate-matcher. That's running in
parallel with your work.

## Slice ownership

| Agent | Slice | Input file(s) |
|---|---|---|
| WS1 | VA dark sweep (individual + consolidated) | `inputs/ws1_va_dark_individual.csv` + `inputs/ws1_va_dark_consolidated.csv` |
| WS2 | Catalog hierarchy gaps | `inputs/ws2_hierarchy_gap_candidates.csv` |
| WS3 | Alias coverage audit | `inputs/ws3_alias_coverage_candidates.csv` |

Each agent writes ONLY to its own subdirectory under
`audit/linkage_pass_2026-05-followup/ws{1_va,2_hierarchy,3_aliases}/`.

## Decision schema

Identical to the prior CHARTER. The only addition is that WS3 will emit
a higher proportion of `false_positive` decisions for proposed aliases
that are too generic — that's expected behavior, not a quality problem.

## WS1-specific guidance

- VA's dark population skews toward medical imaging. Look for vendors
  not already in the catalog (the prior pass added Cortechs, Siemens
  MAGNETOM, Hologic 3D Quorum, Canon Aquilion ONE AiCE, Verathon,
  Planmeca — those are baseline; find the **long tail**).
- Watch for VA-internal AI tools (VA GPT, VA Clinical AI Agent). When
  proposing those as `add_product`, set `vendor = "U.S. Department of
  Veterans Affairs"` and consider whether `product_origin` should be
  `agency_internal_platform` (note this in `reasoning` — apply script
  will pick it up).
- Ambient scribe deployments (Abridge, Suki, Nuance DAX) are likely in
  unrelated rows where the vendor field is blank. Use the dev_type
  field — `"Purchased from a vendor"` rows whose narrative mentions
  "ambient", "scribe", "clinician documentation" should get more
  research time.
- Most rows will still be `unclear` — accept that.

## WS2-specific guidance

- Check `data/product_hierarchy_edges.csv` first to see what's already
  parented (and what's explicitly `action=remove` — don't re-propose
  those).
- When proposing an umbrella parent that doesn't exist in catalog
  (e.g., the prior pass found no `Amazon Web Services` top-level row),
  emit `add_product` for the umbrella + `add_hierarchy_edge` rows for
  each child.
- Max depth ≤ 5. Be conservative — if you're not sure, leave parent
  unset.

## WS3-specific guidance

- The input CSV gives you 30 candidate products + sample unlinked use
  cases that mention the product name. For each, decide per proposed
  bare alias:
  - `add_alias` only if all four hold:
    1. ≥4 characters
    2. Not a common English word
    3. No collision with another catalog product's alias_text
    4. Distinctive enough that boundary-checked substring matching
       won't produce false positives in real narrative
  - `false_positive` if the bare name is greedy ("AI Builder" alone,
    "Maps" alone, "Translate" alone — too dangerous).
  - `unclear` if you can't tell.
- The production linker already applies word-boundary checks
  (`product_resolution.py:88-95`), so aliases that read as
  "would match too much" intuitively may actually be safe in practice
  — but err conservative.

## Time budget

WS1: 60–75 min (largest batch). WS2: 30 min. WS3: 30 min. Final reply
each ≤300 words.
