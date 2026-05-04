# Cleanup-pass charter

You are one of three parallel agents executing the dashboard cleanup
plan at `~/.claude/plans/please-make-a-full-peaceful-fairy.md`.
Foundation work has confirmed two real bugs and three safe paths;
your slice owns one piece. Read this charter first.

## Foundation findings (already verified — trust these numbers)

- `use_case_tags.architecture_type` rows: 3,549 with `use_case_id`
  set, 900 with `consolidated_use_case_id` set, 0 orphans. So
  `getArchitectureDistribution` (which queries `use_case_tags`
  directly, no entry-table join) correctly spans both kinds — Slice A
  should NOT change it.
- GitHub Copilot agency count: current `getAnalyticsInsights.github_copilot_agencies`
  joins only `use_cases` and returns **4**. Truth, including
  consolidated, is **18**. This is the real Fig. 01 "Coding" insight
  card bug Slice A must fix.
- Reporting-agency total: 55 (status IN 'FOUND_2025','FOUND_2024_ONLY').

## File-ownership boundaries

Each agent owns the files listed below. Do NOT modify any other file.
Do NOT git commit or push — integration owns that.

### Slice A — `/analytics` audit + fix
Owns:
- `dashboard/lib/db.ts` — analytics-related helpers only.
- `dashboard/app/analytics/page.tsx` — caption / label edits only.

Deliverables:
1. Fix `getAnalyticsInsights.github_copilot_agencies` to include
   `consolidated_use_cases` via UNION (foundation confirmed: should
   return 18, not 4). Mirror the pattern from
   `getEntryTypeMixByAgency` (recently fixed, in same file).
2. Spot-check the other 7 helpers listed in the plan (getYoYGrowthData,
   getProductAgencyMatrix, getMaturityScatterData,
   getArchitectureDistribution, getLLMVendorShare,
   getCodingToolAgencies, getEnterpriseLLMAgencies). For each, run a
   quick SQL query against `data/federal_ai_inventory_2025.db` and
   confirm the helper's output matches. Report any mismatches.
3. Clarify Fig. 09 caption ("Enterprise LLM distribution",
   `app/analytics/page.tsx` ~line 477): the "general-LLM entries"
   value is entries-per-agency, not agencies. Make that explicit.
4. Add a one-line comment on any helper you fix, naming the bug
   pattern (analogous to the comment recently added on
   `getEntryTypeMixByAgency`).

Verify: `npx tsc --noEmit` clean; `npm run build` clean. Report ≤300 words.

### Slice B — `topic_area` normalization at ingest time
Owns (in the parent ETL repo at
`/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/`,
NOT the dashboard):
- `auto_tag.py` — add `normalize_topic_area()` near the existing
  `normalize()` at line 11.
- `load_inventories.py` ~line 353 — apply the normalizer before
  insert.
- `scripts/normalize_topic_areas_inplace.py` (NEW) — one-shot
  migration that re-normalizes existing rows in
  `data/federal_ai_inventory_2025.db`.
- `audit/cleanup_pass/topic_area_normalization_log.md` (NEW) —
  before/after distinct counts and the merge rules.

Merge rules (do NOT widen):
- Case-fold-then-prefer-titlecase: "Administrative Functions" wins
  over "Administrative functions".
- Em-dash (`–`) and double-space normalized to single hyphen + single
  space within the `Other` family ("Other – Economic & Financial",
  "Other - Applied Mathematical Sciences", etc.).
- Trim outer whitespace; leave inner punctuation alone.
- DO NOT merge "Cybersecurity" with "Cybersecurity Operations" or
  "Information Technology" with "IT Operations & Infrastructure
  Management" — those are genuinely distinct values.

Job:
1. Run a SQL spot to enumerate every distinct topic_area + its case-
   normalized form. Identify all merge candidates.
2. Implement `normalize_topic_area(raw: str | None) -> str | None`.
   Idempotent.
3. Wire it into `load_inventories.py`.
4. Run the in-place migration (UPDATE use_cases SET topic_area = ...)
   so the live DB reflects the normalization without a full `make fix`.
5. Confirm via SQL: distinct count drops from current 33 → expected
   value (write the actual number in the log).
6. `pytest tests/ -q` from parent repo: 52/52 should pass.

Report ≤300 words.

### Slice C — IFP marker on use-case-card + IFP footnote on capability-flags
Owns:
- `dashboard/components/use-case-card.tsx` — replace plain-text
  `entry_type` and `ai_sophistication` (lines ~99–110) with
  `<TagChip dimension={...} value={...} showProvenance={false} />`.
  `showProvenance={false}` keeps it compact for grid views (the
  enclosing context already conveys provenance). Keep the binary
  flag icons (Code2, Sparkles, ShieldCheck) untouched.
- `dashboard/components/capability-flags.tsx` — add a single one-line
  "IFP-derived from agency_ai_maturity rollups" mono-style footnote
  near the section header (~line 17), using existing editorial
  primitives. No structural changes to the ✓/✗/? rows.

Job: read each file first to confirm exact line numbers; make
minimal, surgical changes.

Verify: `npx tsc --noEmit` clean. Report ≤300 words.

## Common rules

- Dashboard work happens in `2025-aia-use-case-inventory/dashboard/`.
- Python ETL work happens in the parent dir (Slice B only).
- `npx tsc --noEmit` must be clean after your slice.
- Do NOT git commit or push.
- Time budget: 30–60 min per slice.
