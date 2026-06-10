# Phase 5 — `/discrepancies` Page + Per-Case OMB ID Chip

## Context

Phase 4 shipped the dashboard data layer (`lib/discrepancies.ts` with 4 query functions; `UseCase` type extended with `omb_consolidated_*` columns; both deployed). Phase 5 builds the user-facing UI on top of that:

1. A summary + filterable table page at `/discrepancies` showing all 6 status buckets and every unresolved row.
2. A drill-down at `/discrepancies/[auditId]` rendering the OMB row vs DB row side-by-side, with drift fields highlighted.
3. An OMB-ID chip on the use-case detail page (`/use-cases/[slug]`) that surfaces both the agency-as-filed (IFP) and the OMB-assigned IDs, plus a "Not in OMB consolidated 2025" chip when the use case is missing from OMB's snapshot.

**Deferred to Phase 5b:** the `/discrepancies` link in `components/navigation.tsx`. The user has uncommitted WIP rewriting that file (splitting the LINKS array into PRIMARY + MORE). To avoid the deploy-bundles-WIP issues from Phases 3 and 4, I won't touch `navigation.tsx` until that rewrite lands. The page is reachable by direct URL in the meantime.

## Coordination guard (critical)

The dashboard repo is being actively edited. Phase 5 only touches files the user does NOT have WIP in (verified via `git diff` before each edit):

- ✅ `app/discrepancies/page.tsx` — new file, no conflict possible
- ✅ `app/discrepancies/[auditId]/page.tsx` — new file
- ✅ `components/discrepancy-table.tsx` — new file
- ✅ `components/discrepancy-side-by-side.tsx` — new file
- ✅ `app/use-cases/[slug]/page.tsx` — verified CLEAN at time of plan
- ❌ `components/navigation.tsx` — user has WIP, DEFERRED to Phase 5b

For commit/push: explicit `git add --` paths, `git status` immediately before commit, abort if anything unintended is staged.

## Files to create

| Path | Responsibility |
|---|---|
| `app/discrepancies/page.tsx` | Server component. Renders summary stats (6 status buckets + drift) and embeds the client-side `DiscrepancyTable`. |
| `app/discrepancies/[auditId]/page.tsx` | Server component. Async `params`, calls `getDiscrepancyDetail`, returns `notFound()` if missing. Renders side-by-side. |
| `components/discrepancy-table.tsx` | Client component. Filters by status, agency, search-by-name. Renders rows from `getDiscrepancyRows()` server-side; client only filters client-side over the prefetched list. |
| `components/discrepancy-side-by-side.tsx` | Server component. Iterates the 10 canonical fields and renders DB vs OMB cells; drift rows tinted amber. |

## Files to modify

| Path | Change |
|---|---|
| `app/use-cases/[slug]/page.tsx` | Add an OMB-ID chip near the existing `No. {data.use_case_id}` block (around line 127). Show `OMB: {omb_consolidated_id}` chip when present; show `Not in OMB consolidated 2025` chip when null. |

## Reused conventions

| From | Use |
|---|---|
| `components/editorial.tsx::Section` | `{ number, title, lede?, source?, children, className? }` — all sections get `source="omb-derived"` per the Section-source convention. |
| `components/editorial.tsx::MonoChip` | For ID chips. Use `size="xs"` for inline IDs. |
| `lib/discrepancies.ts` | All 4 query functions. |
| `lib/types.ts` | `UseCase.omb_consolidated_id` etc. (already extended in Phase 4). |
| `notFound()` from `next/navigation` | For 404 on bad audit IDs. |

## Status chip palette

Each `match_status` gets a tinted chip (Tailwind tones already used elsewhere in the dashboard):

| Status | Tone |
|---|---|
| `omb_only` | amber-50 / amber-900 (action: ingest) |
| `db_only` | rose-50 / rose-900 (action: investigate) |
| `suggested_rename` | violet-50 / violet-800 |
| `duplicate_in_omb` | orange-50 / orange-900 |
| `matched_fuzzy` | blue-50 / blue-800 |
| `matched_exact` | stone-100 / stone-700 (background, not actionable) |

## Execution steps

### Step 1: `app/discrepancies/page.tsx` (summary + table)

Server component. Imports `getDiscrepancySummary`, `getDiscrepancyRows`, `getDiscrepancyAgencies` from `@/lib/discrepancies`. Computes summary numbers, fetches all unresolved rows (default filter `unresolvedOnly: true`), passes both to the client `DiscrepancyTable`. Renders 7 summary stat cards in a grid + the table inside two `Section` components.

### Step 2: `components/discrepancy-table.tsx` (client component)

`"use client"`. Receives `rows: DiscrepancyRow[]` + `agencies: Array<{agency, n}>` as props. Uses `useState` for status filter, agency filter, name search; `useMemo` to apply filters. Renders an HTML `<table>` with status chips, agency monos, name, IFP id, OMB id, drift count, score, and a "View →" link to `/discrepancies/[audit_id]`.

### Step 3: `app/discrepancies/[auditId]/page.tsx` (drill-down)

Server component with `async function Page({ params }: { params: Promise<{ auditId: string }> })`. Parses the param to a number, calls `notFound()` if NaN or if `getDiscrepancyDetail` returns null. Renders header (use case name + agency + IFP ID + OMB ID + match score) and the `DiscrepancySideBySide` component.

### Step 4: `components/discrepancy-side-by-side.tsx`

Server component. Takes a `DiscrepancyDetail`. Iterates the 10 canonical fields (`stage_of_development`, `is_high_impact`, `is_withheld`, `topic_area`, `ai_classification`, `vendor_name`, `have_ato`, `has_pii`, `has_custom_code`, `bureau_component`). For each, renders a 3-column row: field label, DB value, OMB value. Highlights rows where the field is in the `drift` array.

### Step 5: Use-case detail OMB-ID chip

Edit `app/use-cases/[slug]/page.tsx` near line 127. Insert chip rendering AFTER the existing `{data.use_case_id && ...}` block:

```tsx
{data.omb_consolidated_id ? (
  <MonoChip
    size="xs"
    tone="muted"
    title="ID assigned by OMB in the 2025 consolidated file"
  >
    OMB: {data.omb_consolidated_id}
  </MonoChip>
) : data.omb_consolidated_source ? (
  <MonoChip size="xs" tone="muted" title="Matched to OMB but no ID was filed">
    OMB: (no ID)
  </MonoChip>
) : (
  <MonoChip
    size="xs"
    tone="stamp"
    title="This use case is not present in OMB's 2025 consolidated inventory"
  >
    Not in OMB 2025
  </MonoChip>
)}
```

### Step 6: Build + smoke-test

```bash
cd dashboard
npx tsc --noEmit                       # zero errors
npm run dev &                          # background
sleep 4
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/discrepancies
# expect 200
# pick any audit id from the table:
AUDIT_ID=$(npx tsx -e "import {getDiscrepancyRows} from './lib/discrepancies'; console.log(getDiscrepancyRows({status:['omb_only']})[0].audit_id)")
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:3000/discrepancies/$AUDIT_ID"
# expect 200
kill %1
```

If both endpoints return 200, proceed.

### Step 7: Visual verify with Playwright (per user preference for HTML changes)

```bash
npm run dev &
sleep 4
node -e "
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('http://localhost:3000/discrepancies');
  await p.screenshot({ path: '/tmp/discrepancies.png', fullPage: true });
  console.log('summary visible:', await p.locator('text=OMB-only').count());
  await p.locator('text=View →').first().click();
  await p.waitForLoadState('networkidle');
  await p.screenshot({ path: '/tmp/discrepancy-detail.png', fullPage: true });
  console.log('detail title:', await p.title());
  await b.close();
})();
"
kill %1
```

Inspect both screenshots. Confirm:
- Summary numbers match Phase 4 stats
- Filter dropdowns populate (Status / Agency / Search)
- Status chips have the right tones
- Detail page shows side-by-side with drift rows highlighted

Also visit `/use-cases/[some-matched-slug]` and verify the OMB-ID chip renders. Test a slug from the FRTIB/GPO/NMB/OPM agencies to confirm "Not in OMB 2025" chip shows for those.

### Step 8: Commit + push (WIP-guarded)

```bash
git status -- app/discrepancies components/discrepancy-table.tsx \
              components/discrepancy-side-by-side.tsx \
              app/use-cases/[slug]/page.tsx

git add -- app/discrepancies/page.tsx \
           "app/discrepancies/[auditId]/page.tsx" \
           components/discrepancy-table.tsx \
           components/discrepancy-side-by-side.tsx \
           "app/use-cases/[slug]/page.tsx"
git status --short  # confirm only the 5 paths above are staged
git commit -m "..."
git push origin main
```

Vercel auto-deploys.

## Verification

Phase 5 is complete when:

1. `tsc --noEmit` clean
2. `/discrepancies` returns 200 and renders summary + table
3. `/discrepancies/[id]` returns 200 for a valid audit id, 404 for an invalid one
4. The OMB-ID chip renders correctly on use-case detail pages (3 cases: matched-with-id, matched-no-id, not-in-omb)
5. Playwright screenshots look correct
6. Production build green via Vercel
7. Only my 5 files in the commit (no user WIP bundled)

## What this phase does NOT do

- No `/discrepancies` link in nav (deferred to Phase 5b after user's nav rewrite lands)
- No "resolve discrepancy" UI gesture (schema supports `resolved_at`/`resolution_note`; UI is future work)
- No bulk-action UI (mark N as resolved, etc.)
- No OMB ID rendering on cards/lists outside the use-case detail page
- No FRTIB/GPO/NMB/OPM auto-archive — those still display normally with the "Not in OMB 2025" chip

## Risks

- **`use-cases/[slug]/page.tsx` already imports `MonoChip`?** Check before adding the chip; if not imported, add to the import list.
- **The `[auditId]` segment must accept any int** — no parameter validation in the route definition; do it in code with `Number.isFinite`.
- **Drift highlighting must use the field name from the drift array, not a derived display name** — drift list uses raw column names like `have_ato` (the OMB-side name in our drift detection), but the display label might say "ATO". Pass the raw field name in `DiscrepancyDriftField.field` and look it up in the side-by-side component.
