# Routing for AI agents

**The active project is the dashboard at `2025-aia-use-case-inventory/dashboard/`.** It is a separate git repo (`michaeleboyce/use-case-inventory` on GitHub) deployed to **https://use-case-inventory.vercel.app**. Commits to it go to the `use-case-inventory` repo's `main` branch.

If the user asks for work that isn't explicitly about the python ETL or the FedRAMP browser, **`cd` into `2025-aia-use-case-inventory/dashboard/` first**. Read its `CLAUDE.md` and `AGENTS.md` for project-specific conventions. That's where almost everything happens.

## What's at this level (the outer monorepo)

This directory is a checkout of `michaeleboyce/federal-ai-platform` on the `use-case-inventory` branch. It is a container for three sub-projects:

| Subdirectory | What it is | Active? | Touch when... |
|---|---|---|---|
| `2025-aia-use-case-inventory/dashboard/` | The live Next.js dashboard (separate repo). | **Yes — this is the project.** | Almost always. |
| `2025-aia-use-case-inventory/` (excluding `dashboard/`) | Python ETL + audit work that builds `data/federal_ai_inventory_2025.db` (the SQLite DB the dashboard reads). | Periodically | Source data needs reloading, retag rules change, hierarchy seeds need editing, audit work. |
| `2025-fedramp/` | FedRAMP marketplace ingest (separate sub-project). | Periodically | FedRAMP-specific tasks. |
| `original-inventory/` | Archive — older AI-inventory + FedRAMP browser experiments. | No | Don't touch. |

## What about the Vercel project named "federal-ai-platform"?

That Vercel project is a stale deploy linked to this repo's root from when the dashboard used to live here. It no longer builds anything (intentionally short-circuited via `vercel.json` at this root). **Do not try to "fix" it.** See `DEPRECATED.md` and `README.md` for context.

The actual deployed dashboard lives elsewhere — see top of this file.

## Common task → which directory

| Task | Where to work |
|---|---|
| "Add a feature to the dashboard" | `2025-aia-use-case-inventory/dashboard/` |
| "Update a page / component / route" | `2025-aia-use-case-inventory/dashboard/` |
| "Fix a deployment issue" | `2025-aia-use-case-inventory/dashboard/` (then `vercel deploy --prod` from there) |
| "Update the source SQLite DB" | `2025-aia-use-case-inventory/` (then `make fix`, then sync the DB into `dashboard/data/`) |
| "Add a retag rule, hierarchy seed change, audit pass" | `2025-aia-use-case-inventory/` |
| "Edit FedRAMP marketplace ingest" | `2025-fedramp/` |
| Anything else | Default to `2025-aia-use-case-inventory/dashboard/`. |

## Don't confuse with the sibling repo

There is also `~/Documents/Programming/ifp/federal-ai-platform/` (a separate top-level checkout) that is the **FedRAMP browser app** — a totally different Next.js project that happens to share the GitHub repo name with this monorepo (it's the same repo's `main` branch, but a different working tree). Nothing in this monorepo's `use-case-inventory` branch deploys to `federal-ai-platform.vercel.app`; that's served from the sibling checkout's `main` branch. Don't conflate them.
