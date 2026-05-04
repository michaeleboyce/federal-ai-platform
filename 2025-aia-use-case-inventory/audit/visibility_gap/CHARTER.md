# Visibility-gap drill charter

You are one of two parallel agents drilling into the LLM-vendor
visibility gap surfaced as Insight Card G on /analytics:

- 1,203 general-LLM-access entries total
- 431 (36%) name no vendor and no product (even after fallback to
  use_cases.vendor_name and use_cases.system_name)

Foundation already verified the per-agency breakdown:

| Agency | Unspec | Total | Pct  |
|--------|------:|------:|-----:|
| HHS    | 87    | 167   | 52%  |
| VA     | 65    | 70    | 92%  |
| NASA   | 43    | 50    | 86%  |
| DOJ    | 42    | 87    | 48%  |
| DHS    | 41    | 66    | 62%  |
| DOC    | 23    | 31    | 74%  |
| GSA    | 19    | 22    | 86%  |
| DOT    | 18    | 21    | 85%  |
| DOE    | 18    | 151   | 11%  |
| USDA   | 18    | 32    | 56%  |
| SEC    | 14    | 25    | 56%  |
| DOI    | 14    | 20    | 70%  |

Top 6 agencies = 301 of 431 (70%) of the gap.

## Slice ownership

### Slice A — Code (data + UI)
Owns:
- `dashboard/lib/db/analytics.ts` — add `getLLMVendorVisibilityByAgency()` returning `Array<{agency_id, abbreviation, name, total, unspecified, share}>` sorted by `unspecified` desc. Mirror the SQL bucketing used in `getLLMVendorShare` and `getAnalyticsInsights` (the WITH tagged CTE that falls back through cots_vendor → tool_vendor → use_cases.vendor_name → '').
- `dashboard/app/analytics/page.tsx` — render a compact horizontal bar list ("Visibility-gap contributors") immediately under Fig. 07 (LLM vendor donut). Show top 10 agencies. Each row: agency abbr, unspecified count, share-percent, and a stacked bar (named vs unspecified). Click-through agency abbr to `/agencies/<abbr>`.
- (optional) `dashboard/components/charts/visibility-gap-list.tsx` (NEW) if you prefer to factor out the bar list rather than inline it.

Constraints:
- Do NOT touch the donut itself. The list is a complement.
- Keep it short — 10 rows max, mono editorial style matching the rest of the page.
- `npx tsc --noEmit` clean.

Verify by loading `/analytics` and confirming VA shows 92%, NASA 86%, etc.

### Slice B — Spot research + audit log
Owns (in the parent ETL repo, NOT the dashboard):
- `audit/visibility_gap/findings.md` (NEW) — the spot-research output.
- (optional) `data/federal_ai_inventory_2025.db` — apply UPDATEs to fill in vendor info where you can confidently identify it from external sources. Idempotent UPDATE statements only; back up first.

Job:
1. For each of the top 4 agencies by absolute unspecified count (HHS, VA, NASA, DOJ), pull a sample of 5–10 unspecified general-LLM use cases from the DB. Read their use_case_name, problem_statement, expected_benefits, system_outputs.
2. Identify patterns:
   - Are these duplicates of one platform (like CDC's EDAV pattern at HHS)?
   - Do narratives mention ChatGPT, Claude, Gemini, Copilot, or other tools that the agency just didn't put in vendor_name / system_name?
   - Are these requests for "general LLM access" with no specific tool yet selected?
3. For VA specifically (92% unspecified — the most extreme), do a deeper read. What's the actual VA platform? Web search if needed (cite the source).
4. Write `audit/visibility_gap/findings.md` with:
   - One section per agency (HHS, VA, NASA, DOJ — stretch: DHS, DOC).
   - Sample use case IDs you read.
   - The pattern you identified.
   - Any vendors you can confidently attribute (with a confidence note).
5. **Optional but high-value:** if you find a clear pattern (e.g., "all 65 VA entries point to a single platform built on X"), write a targeted UPDATE script under `scripts/recover_visibility_gap_<agency>.py` that fills in vendor / system_name on those rows. Idempotent.

Time budget: 30–60 minutes.

## Common rules
- Dashboard work in `dashboard/`; ETL/audit work in the parent.
- Do NOT git commit. Integration owns that.
- Report ≤300 words.
