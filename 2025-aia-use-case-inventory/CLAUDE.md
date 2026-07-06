# Routing for AI agents

**The active project is the dashboard at `dashboard/` (relative to this directory).** It's a separate git repo (`michaeleboyce/use-case-inventory` on GitHub) deployed to **https://use-case-inventory.vercel.app**.

If the user asks for any work that isn't explicitly about the python ETL, retag rules, hierarchy seeds, or audit work, **`cd dashboard/` first** and read its `CLAUDE.md` and `AGENTS.md`. That is where almost everything happens.

## What's at this level

This directory is the **python ETL + audit + data-pipeline workspace**. Its job is to build and maintain `data/federal_ai_inventory_2025.db` — the SQLite database the dashboard reads from. Touch this when the **source data** needs to change; touch the dashboard for **everything else**.

| Path | What it is | Touch when |
|---|---|---|
| `dashboard/` | The deployed Next.js app (separate repo). | Almost always — features, bugfixes, UI, deploys. |
| `data/federal_ai_inventory_2025.db` | The canonical SQLite DB. Read by the dashboard. | Only via `make fix` (rebuilds from sources). |
| `data/raw/` | Per-agency 2025 inventory CSVs/XLSXs from OMB. | Re-running ETL with refreshed source data. |
| `data/federal_hierarchy_seed.py` | Hand-curated federal organizations tree (departments, sub-agencies, offices). | Adding a missing bureau / sub-agency. |
| `auto_tag.py`, `scripts/compute_org_maturity.py`, `load_*.py`, `build_lookups.py` | The ETL chain orchestrated by `make fix`. | Changing tag rules, maturity rubric, ingestion. |
| `scripts/` | One-off migrations, retag passes, hierarchy backfill, audit-apply scripts. | Specific named tasks (each script has a docstring). |
| `audit/` | Audit findings, retag rollups (`audit/retag/`), unmapped-bureau research, the article-grade by_agency.md files. | Audit / retag work. |
| `migrations/` | Additive schema migrations. | Schema changes. |
| `tests/` + `audit/checks/` | pytest suite (~413 checks: unit tests + build-gating DB invariants). | After ETL changes: `python3 -m pytest tests/ audit/checks/ -q`. |

## The `.claude/skills/` directory

Project-scoped Claude skills live at `.claude/skills/<name>/SKILL.md`. Currently:

- **`omb-ai-use-case-inventory`** — Reference for the OMB M-25-21 inventory schema (36 columns, valid values, recoding maps, conditional-required clauses, DB column crosswalk). Auto-triggers when an agent works with the schema, source CSVs, or any retag / load / backfill script.
- **`inventory-db-model`** — Reference for the DATABASE's own structure post the 2026-07 overhaul (m019–m025): two entry types, edge-only product linkage via `entry_primary_products`, normalized enum columns, the `agency_ai_maturity` compat view, agency FK layer, the omb_only==0 completeness gate, migration/rebuild conventions, and the re-baselining discipline. Auto-triggers on migration authoring, fix-chain edits, check re-baselining, or any script touching the core tables.

Both skills are **mirrored into `dashboard/.claude/skills/`** (the dashboard is its own repo, so its sessions load their own copies). When you edit a skill, `cp` it to the other location in the same change — the copies must stay identical.

## When you DO need to touch this directory

1. **Source data changed** (a new agency inventory dropped, OMB published a fresher consolidated file). Re-run `make fix` and sync the rebuilt DB into `dashboard/data/`.
2. **Tag rules need correction** (a retag audit found systemic issues). Modify `auto_tag.py` or write a follow-up script under `scripts/`. Run `make fix`.
3. **Hierarchy seed needs a new bureau / sub-agency.** Edit `data/federal_hierarchy_seed.py`. Re-run `python scripts/seed_federal_hierarchy.py && python scripts/backfill_bureau_orgs.py && python scripts/compute_org_maturity.py`. Sync DB to dashboard.
4. **Audit work** (bureau research, retag rounds, evidence verification). Outputs go under `audit/`.

After any of those, sync the rebuilt DB into the dashboard:
```
cp data/federal_ai_inventory_2025.db dashboard/data/federal_ai_inventory_2025.db
cd dashboard && npm test && npm run build
```
(The dashboard's test suite is vitest via `npm test` — it has no pytest.)

## Two meanings of "consolidated" — don't conflate

- **`consolidated_use_cases`** (900 rows) — a *parallel entry type*: the
  COTS/Appendix-B product-capability grid from
  `cots-2025-ai-inventory-consolidated.xlsx`. NOT a rollup of `use_cases`;
  unified with it only through the `inventory_entries` /
  `entry_product_edges` views.
- **`omb_consolidated_rows`** (+ `omb_match_audit`) — a *mirror* of OMB's
  government-wide consolidated file of individually-reported use cases
  (`2025_individually_reported_AI_use_cases.xlsx`), loaded by
  `load_omb_consolidated.py` purely to reconcile against `use_cases`
  (match statuses: matched_exact / omb_only / db_only / …).

If a task says "consolidated", determine which of the two it means first.

## Multi-agent safety: re-resolve IDs before EVERY write, commit, or push

This workspace is often touched by multiple agents on the same branch in
parallel. `products.id`, `use_cases.id`, and `consolidated_use_cases.id`
are NOT stable across `make fix` runs or even across partial rebuilds
(`load_inventories.py` does `DELETE … ; INSERT … AUTOINCREMENT`, so the
sequence rotates). A foreground agent's prior `SELECT id WHERE
canonical_name=…` reading may have become stale by the time it gets
back to writing.

**Hard rules — non-negotiable:**

1. **Before any DB write** (UPDATE / INSERT / DELETE on `products`,
   `use_cases`, `consolidated_use_cases`, `use_case_products`,
   `consolidated_use_case_products`, `entry_product_edges`, etc.),
   re-resolve every id in your working set immediately before the
   write transaction, in the same connection. Treat any id you read
   more than a few seconds ago as suspect. NEVER trust an id read
   from a CSV, an LLM proposal, or a sibling agent's report — only
   trust ids you just SELECTed by stable signature (canonical_name,
   slug, `(agency_id, source_file, use_case_name)`, etc.).

2. **Before any `git commit` or `git push`** that includes a DB or a
   DB-derived artifact, re-run the relevant `pytest tests/ -q`
   subset and a `sqlite3 …` sanity query for the entities you
   touched. CSVs under `audit/retag/` that embed ids: verify a
   representative sample still resolves before you commit them.

3. **`use_case_products.confidence` / `consolidated_use_case_products.confidence`**
   are `CHECK(confidence IN ('strong', 'inferred'))`. Any other
   value silently violates the constraint and SQLite (without
   `PRAGMA foreign_keys=ON`) will drop the row. If your CSV/agent
   pipeline uses `high`/`medium`/`low` as a gating signal, translate
   to `strong` / `inferred` AT THE WRITE BOUNDARY, never before.
   See `scripts/apply_linkage_pass_2026_05.py` (post `400badb`) for
   the reference pattern.

4. **Stale-id resolution helpers** live in
   `scripts/relink_stale_use_case_products.py`:
   - `build_old_id_to_signature()` — read pre-rebuild ids → signature
   - `build_signature_to_new_id(conn)` — read live DB ids by signature
   - `scan_backup_signatures(needed)` — fall back to backups
   Any apply script that consumes a CSV with ids in it MUST use these
   or an equivalent re-resolution before writing.

5. **If you discover a sibling agent has rebuilt the DB while you
   were working** (telltale: a fresh `data/federal_ai_inventory_2025.db.backup-*`
   file appeared, or `select max(id) from products` jumps by hundreds
   from what you last saw), STOP, refresh your snapshot, and re-do any
   id-bearing work. Do not assume your in-memory understanding is
   still valid.

The cost of an extra `SELECT … WHERE canonical_name=?` is microseconds.
The cost of a silently-dangling FK row that survives a `make fix` and
ships to the dashboard is hours of forensic work later.

## When NOT to touch this directory

If the user asks for anything UI-shaped — a page change, a component, a route, a chart, a new section, a deploy fix — **`cd dashboard/` first**. Don't modify python files for those tasks.

## How the deploy works (so you don't get confused)

The dashboard at `dashboard/` is its own git repo. It deploys via Vercel autoamtically on push to `main`. The SQLite DB is shipped INSIDE the dashboard repo's `data/` directory at build time — that's why we sync the rebuilt DB after any ETL change.

The OUTER monorepo (where this directory lives) does NOT deploy anywhere. There's a stale Vercel project named "federal-ai-platform" that used to deploy this monorepo's root, but it's intentionally short-circuited via `vercel.json` at the parent. Don't try to deploy from here.
