---
name: inventory-db-model
description: Use when working with the federal AI inventory SQLite database's STRUCTURE — its tables, views, relationships, invariants, and rebuild conventions (post the 2026-07 data-quality overhaul, migrations m019–m025). Covers the two-entry-type model, edge-based product linkage via entry_primary_products, the normalized enum columns, the maturity collapse (agency_ai_maturity is a VIEW), the agency FK layer, the omb_only completeness gate, migration authoring rules, and the loud-failure/re-baseline discipline. Triggered by: writing or reviewing a migration under `migrations/`, editing `db.py` / `Makefile` fix-chain ordering, adding a script that reads or writes `use_cases` / `consolidated_use_cases` / product edges / maturity, adding or re-baselining a check under `audit/checks/`, or debugging a `make fix` failure. For the MEANING of OMB source columns and their value vocabularies, use `omb-ai-use-case-inventory` instead.
---

# Federal AI Inventory — Database Model Reference

How the SQLite database (`data/federal_ai_inventory_2025.db`, ~60 MB, mirrored
into `dashboard/data/`) is structured, why it's structured that way, and the
rules that keep it coherent. State as of the 2026-07 data-quality overhaul
(migrations m001–m025; the overhaul was m019–m025 plus a loader fix and a
45-row OMB ingest — full record in `audit/omb_only_ingest/ADJUDICATION.md`).

This is a **structure** reference. For what an OMB column *means*, use the
`omb-ai-use-case-inventory` skill.

## The one-paragraph mental model

Two parallel **entry types** (narrative `use_cases`, checkbox-grid
`consolidated_use_cases`) are unified by views. Products link to entries only
through **edge tables**; a view derives each entry's primary product. All
maturity rows live in **one physical table** keyed by the org tree;
the legacy per-agency table is a compat view. Free-text OMB enums have
**normalized sibling columns** recomputed every rebuild. Everything
id-numbered rotates on every rebuild; everything durable is keyed by
**signature** (slug, canonical_name, row_hash). Completeness against OMB's
own consolidated file is **gated at zero**. Failures are loud by design.

## Entry types: two instruments, not one

| | `use_cases` (3,660) | `consolidated_use_cases` (901) |
|---|---|---|
| What it is | Individually-reported narrative filings (M-25-21's 34 columns) | Appendix-B COTS checkbox grid (20 template lines × 45 agencies) + 1 DOL addendum |
| Loaded from | ~37 per-agency files + 45 rows ingested from OMB's consolidated file | `cots-2025-ai-inventory-consolidated.xlsx` + `scripts/backfill_dol_prism_ally.py` |
| Templates | NEVER (concept doesn't apply; the old `template_id` column was 0-populated and dropped by m025) | `template_id` → `use_case_templates` (live, 901/901) |
| Tag row | exactly one in `use_case_tags` (via `use_case_id`) | exactly one (via `consolidated_use_case_id`, XOR CHECK) |

**"Consolidated" means two unrelated things** — don't conflate:
- `consolidated_use_cases` = the Appendix-B entry type above.
- `omb_consolidated_rows` (+ `omb_match_audit`) = a mirror of **OMB's**
  government-wide consolidated file of individually-reported rows, used to
  reconcile completeness (see the gate below).

Unifying views: `inventory_entries` (both kinds, 4,561), `entry_product_edges`
(both kinds' product links), `agency_rollups` (per-agency counts).

## Product linkage: edges only

- Authoritative: `use_case_products` / `consolidated_use_case_products`
  (composite PK, `ON DELETE CASCADE`, `confidence CHECK IN
  ('strong','inferred')` — translate any high/medium/low pipeline signal AT
  THE WRITE BOUNDARY, never store it).
- **`entry_primary_products`** (m020 view): one row per entry with ≥1 edge —
  `(entry_kind, entry_id, product_id, product_name)` — ordered strong-before-
  inferred, then lowest product_id. This is THE way to get "the" product for
  an entry. The dashboard's `USE_CASE_SELECT` joins it.
- **There is no scalar product cache.** `use_cases.product_id`,
  `use_cases.template_id`, `consolidated_use_cases.product_id` were dropped
  (m025) along with the whole refresh subsystem. If you're writing a script
  that wants an entry's product: JOIN the view. If you're resurrecting an old
  script from `scripts/archive/`, it may still reference these columns — fix
  it or leave it archived.
- Product catalog (`products`, `product_aliases`) is hand-coded in
  `build_lookups.py` and **destructively reseeded every rebuild** — product
  ids rotate; every downstream link pass re-resolves by `canonical_name`.

## Normalized enum columns (never compute from raw)

`use_cases` carries free-text OMB fields AND canonical siblings, recomputed by
`scripts/normalize_use_case_fields.py` on every rebuild (it hard-fails when
non-blank values don't bucket — >5% stage, >1% high-impact):

| Raw (keep for display "as filed") | Normalized (compute/filter on this) | Vocabulary |
|---|---|---|
| `stage_of_development` (~47 variants) | `stage_normalized` | pre_deployment, pilot, deployed, retired, unknown |
| `ai_classification` (~19 variants) | `ai_classification_normalized` | Generative AI, Classical/Predictive ML, CV, NLP, Agentic AI, RL, Other, Unspecified |
| `is_high_impact` (~11 variants) | `high_impact_normalized` | high_impact, presumed_not_high_impact, not_high_impact, unknown (note: Neither/Low/Medium → not_high_impact is a documented editorial fold, m019) |

Dashboard rule: facets/filters/sorts read normalized; detail pages show
normalized + raw "(as filed)" side by side. Never add a new consumer of the
raw columns.

## Maturity: one table, one view

- `org_ai_maturity` is the ONLY physical maturity table. Two passes in
  `scripts/compute_org_maturity.py`: an **agency pass** (one row per
  agency-with-data, keyed by the agency's legacy-linked org, carrying
  `total_consolidated_entries` + `year_over_year_growth`) and a **sub-org
  pass** (≥5 use cases; skips orgs the agency pass already claimed —
  `organization_id` is UNIQUE).
- **`agency_ai_maturity` is a VIEW** (m023) with the legacy name/shape,
  mapped through `federal_organizations.legacy_agency_id`. You cannot
  INSERT/DELETE it — writers target `org_ai_maturity`.
- `has_enterprise_llm` is retained and **currently accurate** (it was cured
  upstream in 2026-07: individual-rows-only rule + scope corrections + the
  omb_only ingest; see `audit/retag/TODO.md` §3). Definition: agency has ≥1
  individually-filed row with `is_general_llm_access=1 AND
  is_enterprise_wide=1`. Cite it as "enterprise-wide general-LLM access,
  individually-filed evidence"; for delivery *kind*, use
  `enterprise_genai_tier_rollup`; for composite readiness, `agency_readiness`.

## Agency identity: two tables, one bridge, FKs everywhere

- `federal_organizations` (hierarchy tree, ~470 nodes) is **canonical for
  identity/hierarchy**; `agencies` (68) remains the physical ingest/FK table
  (it carries source-tracking columns). Bridge:
  `federal_organizations.legacy_agency_id` — **bijective for all 68**,
  enforced by `audit/checks/check_org_agency_bijection.py`. Two links are
  special-cased in `scripts/seed_federal_hierarchy.py` `SPECIAL_LEGACY_LINKS`
  (Peace Corps abbreviation mismatch; VA-OIG maps to an *office-level* node).
- Every abbreviation-keyed side table (`column_mappings`,
  `omb_consolidated_rows`, `agency_ai_access_evidence`,
  `agency_ai_policy_{documents,compliance}`, `use_case_year_links`) carries a
  resolved `agency_id` (m024), backfilled every rebuild by
  `scripts/backfill_agency_fks.py` (case-insensitive + `TREAS→Treasury`
  alias). Documented non-agency exceptions: `COTS`/`MULTI` (loader
  artifacts), `EOP`/`OMB` (policy tracker covers non-filers). Anything else
  unresolved **fails the build**.

## Completeness gate: omb_only == 0

`load_omb_consolidated.py` mirrors OMB's consolidated file and matches every
row against `use_cases` into `omb_match_audit`. After the 2026-07 pass the
`omb_only` status (OMB has it, we don't) is **exactly 0 and gated there**
(`audit/checks/check_loader_integrity.py`). If it trips: OMB republished with
new rows → run a new adjudication round (process documented in
`audit/omb_only_ingest/ADJUDICATION.md`); verdicts go in `decisions.csv`,
consumed by `scripts/ingest_omb_only_rows.py` (row_hash-keyed, idempotent,
runs in the fix chain after the OMB load and BEFORE normalize).

The loader itself (`load_inventories.py`) also fails the build on: any
per-file load exception, any unresolved COTS agency name, or row-skips beyond
a small bound. Its dedup rule: a row is a duplicate only if `use_case_id` AND
`bureau_component` both match an already-loaded row; same-NAME rows from
different bureaus get `-2`/`-3` slug tails (first occurrence always keeps the
plain slug — slug stability is what keeps signature-keyed correction CSVs
valid). Never "simplify" this back to name-only dedup: that bug silently
dropped 66 real filings.

## Rebuild + migration conventions

- **`make fix` is the only way to build the DB.** Wipe-and-reload: ids in
  `products`, `use_cases`, `consolidated_use_cases` ROTATE EVERY RUN. Durable
  keys are slug / canonical_name / row_hash / `(agency, use_case_id,
  bureau)`. Re-resolve ids immediately before every write (see the repo
  CLAUDE.md hard rules). The chain must be idempotent: two consecutive runs
  produce identical counts.
- **Schema is defined twice**: `db.py` `SCHEMA_SQL` (fresh DBs) + additive
  ledger migrations `migrations/m0NN_*.py` (`MIGRATION_ID`, `_column_exists`
  guards, tolerant of minimal test fixtures — see m022/m024 for the
  `_table_exists` pattern). Normalized columns and views live ONLY in
  migrations (`init_schema()` runs the ledger, so fresh DBs get them).
- **Dropping columns in SQLite** (m025 is the template): drop covering
  indexes first; drop EVERY view that references the column *or any dropped
  view* (ALTER revalidates the whole schema — `agency_rollups` failing
  because `inventory_entries` was gone is the classic trap); drop columns;
  recreate views UNCONDITIONALLY (a partially-failed run leaves views missing
  with columns intact).
- **Ordering invariants in the fix chain** (comments in the Makefile mark
  them): OMB ingest after `load_omb_consolidated`, before normalize;
  `normalize_use_case_fields` before anything reading `stage_normalized`;
  every tag-correction script after `auto_tag.py`; `compute_org_maturity`
  after hierarchy seed/backfill and again after the product-link passes;
  `backfill_agency_fks` after all abbreviation-writing loads;
  `compute_agency_readiness` last.

## Gates and re-baselining discipline

`pytest tests/ audit/checks/ -q` (413 checks) validates the committed DB.
Count gates and their authority:

- Row bands (`check_row_count.py`): use_cases 3660±50, consolidated 901±20,
  tags 4561±100 — tags must equal use_cases + consolidated exactly.
- Tag-drift bands (`check_llm_flags.py`): general-LLM distinct 559±50 / total
  789±50, agentic (`ai_sophistication='agentic'`) 66±10. The ± exists because
  `auto_tag` heuristics have ~2-row rebuild jitter. The distinct-LLM and
  agentic queries are hand-synced copies of the fact-sheet queries — change
  both together.
- Integrity gates: loader integrity, org/agency bijection, agency FK
  resolution, refactor-quality (view-is-edge-derived + dropped columns stay
  dropped), id traceability (DOJ-0160 is an allowlisted source-data id reuse).

**Re-baselining rule**: bands may only move in the same commit as the data
change that moves them, with the delta arithmetic written into the test
comment (e.g. "3660 = 3549 + 66 recovered + 45 ingested"). A band tripping on
an unrelated commit is a regression, full stop.

After any rebuild that will be shipped: `cp data/federal_ai_inventory_2025.db
dashboard/data/` (verify by shasum), `cd dashboard && npm test && npm run
build` — and remember the Next build passes with broken SQL; dynamic routes
(use-case detail pages) only fail at runtime, so smoke them against a dev
server. Regenerate `audit/article/fact_sheet.md`
(`scripts/build_article_factsheet.py` — it preserves the hand-authored `## 7.`
FedRAMP section) and re-pin any hardcoded dashboard copy (`/stories` stat
tiles are static strings by design).

## Deliberately unresolved (don't "fix" casually)

- `agencies` as physical FK target (full re-point to `federal_organizations`
  is a separate future project).
- Nullable `agency_id` on the m024 tables (NOT NULL would need
  rename-recreate on six mid-chain tables; the check provides the guarantee).
- The wide sparse `use_cases` table + per-row `raw_json` (faithful landing
  shape for a sparse source; don't normalize away).
- The hand-coded product catalog in `build_lookups.py` (externalizing it is
  known follow-up work).
- The 111 rows added in 2026-07 carry heuristic-only capability tags — a
  capability mini-review is flagged in ADJUDICATION.md.
