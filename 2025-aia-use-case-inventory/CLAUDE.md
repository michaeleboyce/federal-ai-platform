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
| `auto_tag.py`, `compute_maturity.py`, `load_*.py`, `build_lookups.py` | The ETL chain orchestrated by `make fix`. | Changing tag rules, maturity rubric, ingestion. |
| `scripts/` | One-off migrations, retag passes, hierarchy backfill, audit-apply scripts. | Specific named tasks (each script has a docstring). |
| `audit/` | Audit findings, retag rollups (`audit/retag/`), unmapped-bureau research, the article-grade by_agency.md files. | Audit / retag work. |
| `migrations/` | Additive schema migrations. | Schema changes. |
| `tests/` | pytest suite (52 tests). | After ETL changes. |

## The `.claude/skills/` directory

Project-scoped Claude skills live at `.claude/skills/<name>/SKILL.md`. Currently:

- **`omb-ai-use-case-inventory`** — Reference for the OMB M-25-21 inventory schema (36 columns, valid values, recoding maps, conditional-required clauses, DB column crosswalk). Auto-triggers when an agent works with the schema, source CSVs, or any retag / load / backfill script.

## When you DO need to touch this directory

1. **Source data changed** (a new agency inventory dropped, OMB published a fresher consolidated file). Re-run `make fix` and sync the rebuilt DB into `dashboard/data/`.
2. **Tag rules need correction** (a retag audit found systemic issues). Modify `auto_tag.py` or write a follow-up script under `scripts/`. Run `make fix`.
3. **Hierarchy seed needs a new bureau / sub-agency.** Edit `data/federal_hierarchy_seed.py`. Re-run `python scripts/seed_federal_hierarchy.py && python scripts/backfill_bureau_orgs.py && python scripts/compute_org_maturity.py`. Sync DB to dashboard.
4. **Audit work** (bureau research, retag rounds, evidence verification). Outputs go under `audit/`.

After any of those, sync the rebuilt DB into the dashboard:
```
cp data/federal_ai_inventory_2025.db dashboard/data/federal_ai_inventory_2025.db
cd dashboard && pytest tests/ -q && npm run build
```

## When NOT to touch this directory

If the user asks for anything UI-shaped — a page change, a component, a route, a chart, a new section, a deploy fix — **`cd dashboard/` first**. Don't modify python files for those tasks.

## How the deploy works (so you don't get confused)

The dashboard at `dashboard/` is its own git repo. It deploys via Vercel autoamtically on push to `main`. The SQLite DB is shipped INSIDE the dashboard repo's `data/` directory at build time — that's why we sync the rebuilt DB after any ETL change.

The OUTER monorepo (where this directory lives) does NOT deploy anywhere. There's a stale Vercel project named "federal-ai-platform" that used to deploy this monorepo's root, but it's intentionally short-circuited via `vercel.json` at the parent. Don't try to deploy from here.
