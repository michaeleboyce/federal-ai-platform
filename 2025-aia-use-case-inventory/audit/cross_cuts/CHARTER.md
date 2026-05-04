# Cross-cuts UX charter

You are one of three parallel agents strengthening cross-cut browsing,
click-through, and tag-driven navigation in the dashboard. Foundation
work is already done — the shared utilities below exist and type-check.
Your job is to use them.

## Foundation already in place (read-only for you, do not modify)

### `dashboard/lib/urls.ts`
- New type `CrossCutDimension = "entry_type" | "sophistication" | "scope" | "use_type" | "high_impact" | "topic_area"`.
- New helper `tagFilterUrl(key: CrossCutDimension, value: string, agencyId?: number): string` — returns a `/use-cases?<param>=<value>` URL, optionally narrowed to one agency. Use for every "click a tag value" affordance.
- Existing helpers `buildUseCasesUrl`, `agencyUseCasesUrl`, `productUseCasesUrl` unchanged.

### `dashboard/lib/db.ts`
- New `getCrossCutSummary(dim: CrossCutKey): CrossCutValueRow[]` — for each distinct value of the dimension, returns count + top 3 agencies + top 3 products. `CrossCutKey` is `CrossCutDimension | "vendor"` (vendor only valid here, no `tagFilterUrl` for it because vendor isn't a use-case-tag column — link to `/use-cases?vendor=...` via the existing single-value `vendor` filter or to `/products?vendor=...`).
- New `getCrossCutHeatmap(dim, agencyLimit=15)` — returns `{agencies, values, cells}` for the value × agency grid. `agencies` is the top-15 by total count; `cells` only contains non-zero combinations.
- New `getPeerUseCases(useCaseId, limit=6): PeerUseCaseRow[]` — fully implemented. Returns up to 6 peers that share ≥3 tag dimensions with the seed (sophistication, scope, use_type, high_impact, entry_type, topic_area), excluding self and same-agency, ranked by shared-dimensions desc then operational_date desc.

### `dashboard/components/editorial.tsx`
- New `<TagChip dimension={d} value={v} agencyId?={id} label?={...} tone?={...} size?={...} />` — wraps `MonoChip` with the right href. Use everywhere a tag value would otherwise be static text. Has built-in label maps for entry_type, sophistication, scope; falls back to titleCase. Override with the `label` prop.

### Use-cases filter API
- `topic_area` is now a working filter param (multi-select, OR semantics). Sidebar already has the facet group. URL: `/use-cases?topic_area=Health%20%26%20Medical,Science`.

## Charter per slice

### Slice A — Make tag chips clickable across detail pages + table
Owns these files only:
- `dashboard/app/use-cases/[slug]/page.tsx`
- `dashboard/app/agencies/[slug]/page.tsx`
- `dashboard/app/products/[id]/page.tsx`
- `dashboard/components/use-case-table.tsx`

Job:
1. Replace static-text tag renderings in the use case detail sidebar (around lines 135–183) with `<TagChip>`. Pull dimension from the field name: `entry_type` tag → `dimension="entry_type"`, `ai_sophistication` → `"sophistication"`, `deployment_scope` → `"scope"`, `use_type` → `"use_type"`, `high_impact_designation` → `"high_impact"`, `topic_area` (on `uc.topic_area`) → `"topic_area"`. Don't pass agencyId here — the reader is on a use case detail and likely wants global peers, not same-agency peers.
2. On `/agencies/[slug]/page.tsx`, do the same in the sidebar tag rendering. **Pass agencyId** — when a reader is on an agency page and clicks a tag chip, they want peers within that agency, not the global list. (BreakdownChips below the donut charts already do this; don't touch those.)
3. On `/products/[id]/page.tsx` sidebar attribute chips: only the ones that map to a filter param become clickable. `is_generative_ai=1` → `<MonoChip href={buildUseCasesUrl({isGenAI:true, productIds:[productId]})}>`. `is_frontier_llm=1` is not a filter param — leave as static. `product_origin` is not a filter param — leave as static.
4. In `dashboard/components/use-case-table.tsx`: tag cells (entry_type, sophistication, high_impact) become `<TagChip>`. Add `topic_area` as an optional column rendered to the right of high_impact, also as a `<TagChip>`. Don't break the existing column layout — verify with `npm run build` and a dev-server load of `/use-cases`.

Do NOT touch any file outside the four above. Slice B owns navigation and the new browse pages; Slice C owns the use case detail page's "Use cases like this" Section.

Wait — Slice C also touches `dashboard/app/use-cases/[slug]/page.tsx`. Coordinate by making your edits to the **sidebar tag rendering only** (lines 135–183 today). Do not insert new top-level Sections; that's Slice C's job.

Verify when done: `npx tsc --noEmit` from `dashboard/` clean. Spot-check one URL per file you touched to confirm the chips render and link correctly.

### Slice B — `/browse/[dimension]` pages with list + heatmap tabs
Owns these files only:
- `dashboard/app/browse/[dimension]/page.tsx` (NEW)
- `dashboard/components/cross-cut-list.tsx` (NEW)
- `dashboard/components/cross-cut-heatmap.tsx` (NEW)
- `dashboard/components/navigation.tsx`
- `dashboard/app/page.tsx`

Job:
1. Create `app/browse/[dimension]/page.tsx` (server component):
   - Valid dimensions: `sophistication`, `high-impact`, `topic-area`, `vendor`. Map URL slug → CrossCutKey: `high-impact` → `high_impact`, `topic-area` → `topic_area`, others identity.
   - Read `?view=list|heatmap` (default `list`).
   - Call `getCrossCutSummary(dim)` for list view; `getCrossCutHeatmap(dim, 15)` for heatmap view.
   - Editorial header: page title "Browse · {Dimension}", lede "Every reported AI use case, sliced by …".
   - Tab strip immediately below — two `<Link>` tabs that toggle `?view=`. Style with the existing mono uppercase eyebrow rule.
   - Render `<CrossCutList>` or `<CrossCutHeatmap>` per the active view.
   - 404 (`notFound()`) on unknown dimension slugs.
2. `components/cross-cut-list.tsx` (client OK or server — server is fine):
   - Per value, render a card with: value title, count (tabular-nums), one-line "Top: {agency1} · {agency2} · {agency3}", one-line "Products: {p1} · {p2} · {p3}", and a "View all →" `<Link>` to `tagFilterUrl(dim, value)` (or `buildUseCasesUrl({vendor: value})` for the vendor dim — vendor isn't a CrossCutDimension, so use the single-value vendor filter directly).
3. `components/cross-cut-heatmap.tsx`:
   - Render an HTML `<table>`. Rows = values, columns = top-15 agencies. Cell content: count tier glyph (■ for ≥10, · for 1–9, blank for 0) plus `title=` with the exact count and value × agency. Cell `<a href>` routes to `/use-cases?<dim_param>=<value>&agency_ids=<id>`.
   - For dim=vendor: route to `/use-cases?vendor=<value>&agency_ids=<id>`.
   - Mobile: degrade to a stacked list (one block per value, listing top-3 agencies inline). Use a CSS class to switch.
4. `components/navigation.tsx`: add a "Browse" item in the top nav that opens a small dropdown listing the 4 dimensions. Match the existing nav-link styling.
5. `app/page.tsx`: add a "Cross-cuts" row above the existing stat-cards block. Four small cards each linking to one of the 4 `/browse/[dim]` pages, with a one-line description ("Browse by sophistication tier", etc.).

Do NOT touch files outside the five above. Specifically, do not modify the use-cases filter UI (Slice A's earlier topic_area work is done) or use case detail pages (Slice C territory).

Verify when done: `npx tsc --noEmit` clean; `npm run build` succeeds; load each `/browse/[dim]` URL with `?view=list` and `?view=heatmap`; click a heatmap cell and confirm it lands on a correctly-filtered `/use-cases`.

### Slice C — "Use cases like this" panel
Owns these files only:
- `dashboard/app/use-cases/[slug]/page.tsx`

Job:
- Add a new `<Section number="VII.5" title="Use cases like this" source="derived">` (or whatever the next available section number is — read the file first to see what's there) between the existing Section VII "Related" and Section VIII or FedRAMP block.
- Call `getPeerUseCases(useCase.id, 6)` from the foundation.
- Render up to 6 rows. Each row: agency abbreviation chip (link to `/agencies/[slug]`) · use case name (link to `/use-cases/[peer.slug]`) · subtle right-aligned mono line "{sophistication} · {scope} · {stage}". Empty state: render nothing (no Section) if the peer list is empty.
- Coordinate with Slice A: A is editing the SIDEBAR tag rendering (lines ~135–183). You are inserting a NEW Section in the main column. Different regions of the same file — should not conflict, but if you both edit the file, manually inspect the diff before committing.

Do NOT touch any other file. Do NOT modify the data layer (foundation already implemented `getPeerUseCases` end-to-end — just call it and render).

Verify when done: `npx tsc --noEmit` clean; load three different use cases (one general_llm, one agentic, one classical_ml); confirm 6 distinct entries from different agencies appear and the dimensions visibly overlap.

## Common rules
- All work in the dashboard repo at `2025-aia-use-case-inventory/dashboard/`. Do not modify python ETL or the parent monorepo.
- `npx tsc --noEmit` must be clean after your slice.
- Do not run `git commit` or `git push` — integration handles that.
- Time budget per slice: 30–60 minutes.

## Final-summary contract
Final reply ≤300 words: list the files you modified with one-line summaries, anything you skipped, and any questions for the integrator.
