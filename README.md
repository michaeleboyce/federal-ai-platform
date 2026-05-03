# ⚠️ DEPRECATED MONOREPO — read this first

**This repository (`federal-ai-platform` on GitHub) is a deprecated container.**
**The live application has moved.** Do not deploy anything from this repo's root.

## Where the live application is

The Federal AI Use Case Inventory dashboard now lives in its own repo and
deploys from there:

- **Source:** https://github.com/michaeleboyce/use-case-inventory
- **Production:** https://use-case-inventory.vercel.app
- **Local checkout:** `2025-aia-use-case-inventory/dashboard/` (a separate
  git submodule; commits go to the `use-case-inventory` repo above)

When you make changes to the dashboard, commit + push from
`2025-aia-use-case-inventory/dashboard/`, **not** from this outer repo.

## What this repo still contains

| Path | Status | What it is |
|---|---|---|
| `2025-aia-use-case-inventory/` | Active | Python ETL, audit work, hierarchy seeds, the SQLite source DB. The dashboard subdirectory inside it has its own git remote (see above). |
| `2025-fedramp/` | Active | FedRAMP marketplace ingest scripts (separate sub-project). |
| `original-inventory/` | Archive | Older AI-inventory + FedRAMP browser experiments. |

Commits to `2025-aia-use-case-inventory/` (excluding the `dashboard/`
submodule) **do** land in this repo. They're for the data pipeline, not the
deployed dashboard.

## Why the Vercel project for this repo fails

The `federal-ai-platform` Vercel project was set up months ago when the
dashboard lived at the root of this repo. The dashboard has since moved to
its own repo. The Vercel project is now stale — every commit triggers a
"No Next.js version detected" failure because there's no Next.js app at
this repo's root anymore.

The included `vercel.json` short-circuits the build with `exit 0` so the
failure stops being noisy. **Do not "fix" this Vercel project** — the
correct fix is to delete the stale project from the Vercel dashboard, but
that's left to a human decision.

If you're an AI agent and you see this file: **stop**. The live deploy is
the `use-case-inventory` repo. This monorepo is data + scripts only.
