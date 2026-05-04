# Phase 4 — Dashboard Data Layer for `/discrepancies`

## Context

Phase 3 populated the DB:
- `omb_consolidated_rows`: 3,611 rows (mirror of OMB's XLSX)
- `omb_match_audit`: 3,668 rows across the 6 status buckets
- `use_cases.omb_consolidated_id` / `_source` / `_first_seen` / `_last_seen`: populated for 3,492 matched rows

The DB is already synced to `dashboard/data/federal_ai_inventory_2025.db` and deployed (Phase 3 commit `6190ccb` on the dashboard repo). The dashboard does not yet read these tables — Phase 4 adds the TypeScript types and server-side query layer that Phase 5's `/discrepancies` page will consume.

This phase is **dashboard-only** and **read-only at the data layer** (no schema changes, no script changes, no XLSX work). It produces:

1. New TypeScript types in `dashboard/lib/types.ts` for the discrepancy domain.
2. A new query-layer module `dashboard/lib/discrepancies.ts` with four exported functions.
3. Extension of the existing `UseCase` interface with the four `omb_consolidated_*` columns (so Phase 5's per-case OMB-ID chip can read them off the existing `getUseCaseBySlug` result).

No page work, no nav changes, no chip rendering — those land in Phase 5.

## Coordination caveat

The dashboard repo is being actively edited (per commits `4baa334` `f926e7d` while I was working on Phase 3). To avoid the bundling-WIP-into-deploy issue from Phase 3, I will:

- Touch ONLY `dashboard/lib/types.ts` (existing) and `dashboard/lib/discrepancies.ts` (new) in this phase.
- Use `git add -- lib/types.ts lib/discrepancies.ts` (explicit paths, not `git add .` or `git add -A`).
- Run `git status` immediately before `git commit` and abort if anything else is staged.

## Files to create

| Path | Responsibility |
|---|---|
| `dashboard/lib/discrepancies.ts` | Server-side queries: `getDiscrepancySummary()`, `getDiscrepancyRows(filter)`, `getDiscrepancyDetail(auditId)`, `getDiscrepancyAgencies()`. Uses `rawDb()` from `lib/db.ts` (existing convention from `lib/hierarchy-db.ts`). |

## Files to modify

| Path | Change |
|---|---|
| `dashboard/lib/types.ts` | (1) Append 4 nullable `omb_consolidated_*` fields to existing `UseCase` interface (lines 57–116). (2) Append a new section at end of file with `DiscrepancyStatus`, `DiscrepancyRow`, `DiscrepancyDetail`, `DiscrepancyDriftField`, `DiscrepancyFilter`, `DiscrepancySummary` types. |

No other files are touched in Phase 4.

## Reused conventions (don't reimplement)

| From | Use |
|---|---|
| `dashboard/lib/db.ts::rawDb()` | Public accessor for the better-sqlite3 connection (lazy-initialized, read-only, WAL mode). Used by `lib/hierarchy-db.ts`; same pattern here. |
| `dashboard/lib/types.ts::UseCase` | Extended in place — don't fork. |
| Prepared-statement generic typing `prepare<ParamTuple, RowShape>(...)` | The convention throughout `lib/db.ts`. Match it. |

## Public surface of `lib/discrepancies.ts`

```typescript
import type {
  DiscrepancyDetail,
  DiscrepancyFilter,
  DiscrepancyRow,
  DiscrepancySummary,
} from "./types";

/** Top-level counts by match_status + drift count. ~6 SQL rows. */
export function getDiscrepancySummary(): DiscrepancySummary;

/** Filtered list for the table. Each row joins audit, use_cases, and the OMB
 * mirror so the table can render IFP ID, OMB ID, drift count, score, and
 * agency without N+1 follow-ups. */
export function getDiscrepancyRows(filter?: DiscrepancyFilter): DiscrepancyRow[];

/** Per-audit-id detail: status, score, both DB and OMB row dicts of the 11
 * canonical fields, plus the parsed drift list. Returns null if not found. */
export function getDiscrepancyDetail(auditId: number): DiscrepancyDetail | null;

/** Distinct agency abbreviations with at least one non-matched discrepancy.
 * Powers the dropdown filter on the discrepancy page. */
export function getDiscrepancyAgencies(): Array<{ agency: string; n: number }>;
```

## Type additions (concrete)

Appended to the bottom of `dashboard/lib/types.ts`:

```typescript
// ─── OMB consolidated discrepancy types ────────────────────────────────────

export type DiscrepancyStatus =
  | "matched_exact"
  | "matched_fuzzy"
  | "suggested_rename"
  | "omb_only"
  | "db_only"
  | "duplicate_in_omb";

export interface DiscrepancySummary {
  matched_exact: number;
  matched_fuzzy: number;
  suggested_rename: number;
  omb_only: number;
  db_only: number;
  duplicate_in_omb: number;
  total_with_drift: number;
  total_pairs_compared: number;
}

export interface DiscrepancyRow {
  audit_id: number;
  match_status: DiscrepancyStatus;
  match_score: number | null;
  agency_abbreviation: string | null;
  use_case_name: string | null;
  db_use_case_id: number | null;        // FK into use_cases.id
  db_use_case_id_text: string | null;   // agency-as-filed string id
  db_use_case_slug: string | null;      // for linking to /use-cases/[slug]
  omb_row_id: number | null;
  omb_use_case_id: string | null;       // OMB-assigned ID (may be null/empty)
  drift_field_count: number;
  resolved_at: string | null;
}

export interface DiscrepancyDriftField {
  field: string;
  db_value: string | null;
  omb_value: string | null;
}

export interface DiscrepancyDetail {
  audit: DiscrepancyRow;
  drift: DiscrepancyDriftField[];
  db_row: Record<string, string | null> | null;
  omb_row: Record<string, string | null> | null;
}

export interface DiscrepancyFilter {
  status?: DiscrepancyStatus[];
  agency?: string;
  hasDrift?: boolean;
  unresolvedOnly?: boolean;
}
```

And in the existing `UseCase` interface, add four lines just after line 115 (`raw_json: string | null;`):

```typescript
  // OMB consolidated provenance (m004; populated by load_omb_consolidated.py).
  // Null when the use case wasn't matched to any OMB row, or when OMB filed
  // an empty Use Case ID column (true for ED, GSA, HHS, SSA, STATE, TVA).
  omb_consolidated_id: string | null;
  omb_consolidated_source: string | null;
  omb_consolidated_first_seen: string | null;
  omb_consolidated_last_seen: string | null;
```

These ride for free in every existing `getUseCaseBy*` call because the SELECT uses `uc.*`.

## Execution steps

### Step 1: Extend `UseCase` interface

Read `dashboard/lib/types.ts` lines 57–116 to confirm the current shape. Insert the 4 new `omb_consolidated_*` fields just before the closing `}` of the interface (after `created_at`).

Verify with:
```bash
cd dashboard && npx tsc --noEmit lib/types.ts
```
Expected: no TypeScript errors.

### Step 2: Append discrepancy types

Append the entire `// ─── OMB consolidated discrepancy types ───` block (above) to the end of `dashboard/lib/types.ts`.

### Step 3: Implement `lib/discrepancies.ts`

Create the file. Skeleton:

```typescript
/**
 * Server-side queries for the /discrepancies page.
 *
 * Reads `omb_match_audit` (one row per OMB↔DB match attempt) and joins
 * to `use_cases` and `omb_consolidated_rows` to surface a flat row shape
 * for the dashboard. All functions are read-only and synchronous via
 * better-sqlite3 prepared statements.
 *
 * Pattern adapted from lib/hierarchy-db.ts: imports rawDb() from ./db,
 * defines small helper SELECTs, returns plain typed objects.
 */
import { rawDb } from "./db";
import type {
  DiscrepancyDetail,
  DiscrepancyDriftField,
  DiscrepancyFilter,
  DiscrepancyRow,
  DiscrepancyStatus,
  DiscrepancySummary,
} from "./types";

export function getDiscrepancySummary(): DiscrepancySummary { ... }
export function getDiscrepancyRows(filter?: DiscrepancyFilter): DiscrepancyRow[] { ... }
export function getDiscrepancyDetail(auditId: number): DiscrepancyDetail | null { ... }
export function getDiscrepancyAgencies(): Array<{ agency: string; n: number }> { ... }
```

Implementation details:

- **`getDiscrepancySummary`**: one `GROUP BY match_status` query for the 6 buckets, plus one `COUNT(*) WHERE drift_fields_json IS NOT NULL AND drift_fields_json != '{}'` for the total-with-drift number. `total_pairs_compared` = `matched_exact + matched_fuzzy`.

- **`getDiscrepancyRows`**: one parameterized SELECT with a dynamic WHERE clause assembled from `filter`. Use `json_each(a.drift_fields_json)` for `drift_field_count` (SQLite does not have `json_object_keys`). Order by status priority (omb_only first, db_only second, suggested_rename third, duplicate fourth, fuzzy fifth, exact last) so the most actionable rows float to the top. Default cap at 5,000 rows (the full audit table is ~3,668 — no pagination needed).

- **`getDiscrepancyDetail`**: one SELECT with all 11 canonical fields aliased as `db_<field>` and `omb_<field>`. Parse `drift_fields_json` into the `DiscrepancyDriftField[]` shape. Return `null` if the audit row doesn't exist.

- **`getDiscrepancyAgencies`**: `SELECT agency_abbreviation AS agency, COUNT(*) AS n FROM omb_match_audit WHERE match_status != 'matched_exact' GROUP BY agency_abbreviation ORDER BY n DESC`. Powers the dropdown filter.

Field list to alias in `getDiscrepancyDetail` (matches `omb_consolidated_match.DRIFT_FIELDS_DEFAULT` minus the few OMB-only fields we don't surface): `stage_of_development`, `is_high_impact`, `is_withheld`, `topic_area`, `ai_classification`, `vendor_name`, `have_ato`, `has_pii`, `has_custom_code`, `bureau_component`. Note: DB column for `have_ato` is **`has_ato`** (intentional divergence); SELECT it as `uc.has_ato AS db_have_ato`.

### Step 4: Type-check + smoke-test

```bash
cd dashboard
npx tsc --noEmit
```
Expected: zero errors.

```bash
npx tsx -e "
  import { getDiscrepancySummary, getDiscrepancyRows, getDiscrepancyAgencies } from './lib/discrepancies';
  console.log('summary:', getDiscrepancySummary());
  console.log('first 3 rows:', getDiscrepancyRows({ status: ['omb_only'] }).slice(0, 3));
  console.log('agencies:', getDiscrepancyAgencies().slice(0, 5));
"
```
Expected: summary numbers match Phase 3 stats (3467/25/39/68/57/12); first 3 omb_only rows from largest agencies (PBGC, ED, etc.); agencies array sorted by n.

### Step 5: Build verification

```bash
cd dashboard && npm run build 2>&1 | tail -20
```
Expected: build succeeds. (The new module isn't imported by any page yet — this just confirms the types compile cleanly across the project.)

### Step 6: Commit (carefully)

Run `git status` first. **Abort if anything other than `lib/types.ts`, `lib/discrepancies.ts` is staged.** Then:

```bash
cd dashboard
git add -- lib/types.ts lib/discrepancies.ts
git status   # human-eyeball — confirm only these two paths are staged
git commit -F /tmp/phase4-msg.txt
git push origin main
```

The push triggers Vercel auto-deploy. The deployed dashboard will have the types and query layer compiled in but no page consuming them (Phase 5).

## Critical files referenced

| Path | Why |
|---|---|
| `dashboard/lib/db.ts:128` | `rawDb()` export to import in `discrepancies.ts` |
| `dashboard/lib/types.ts:57-116` | `UseCase` interface to extend |
| `dashboard/lib/hierarchy-db.ts:1-25` | Reference pattern for a sibling query module |
| `dashboard/data/federal_ai_inventory_2025.db` | Live DB; already has the populated tables |

## Verification

Phase 4 is complete when:

1. `npx tsc --noEmit` passes from `dashboard/`.
2. `npm run build` succeeds.
3. The smoke-test script (Step 4) prints the expected summary numbers (matched_exact=3467, etc.).
4. Only two files (`lib/types.ts`, `lib/discrepancies.ts`) are in the Phase 4 commit.
5. Push succeeds and Vercel builds green (no runtime change to user-facing pages — the new module is unused).

## What this phase does NOT do

- No `/discrepancies` page (Phase 5).
- No nav link (Phase 5).
- No use-case-detail-page chip (Phase 5).
- No tests (TypeScript projects in this repo don't ship unit tests at the lib layer; the smoke-test in Step 4 is the verification).
- No Python or DB changes.
- No touching of unrelated dashboard files (the user's parallel WIP).

## Risks / things to watch

- **`getDiscrepancyDetail` field aliasing.** The DB column for `have_ato` is `has_ato` (intentional divergence per the omb-ai-use-case-inventory skill), but the OMB-side mirror table has `have_ato`. The aliases in the SELECT need to map both correctly: `uc.has_ato AS db_have_ato`, `o.have_ato AS omb_have_ato`. Easy to mix up. Test this by spot-checking one detail row.
- **WIP coordination.** If the user pushes commits between my last `git status` check and `git push`, my push could be rejected (non-fast-forward). Recovery: `git pull --rebase` and re-push. Safer than `--force-with-lease`.
- **`drift_field_count` SQL.** SQLite has `json_each` but not `json_array_length` for keys. The COUNT subquery `(SELECT COUNT(*) FROM json_each(a.drift_fields_json))` returns the number of TOP-LEVEL JSON keys when given `'{"a":1, "b":2}'` — that's 2. Good. But for `'{}'` it returns 0. Good. For NULL it errors — guard with `CASE WHEN drift_fields_json IS NULL OR drift_fields_json='{}' THEN 0 ELSE (subquery) END`.
