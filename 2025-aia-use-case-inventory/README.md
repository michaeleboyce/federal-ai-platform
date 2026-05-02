# 2025 Federal AI Use Case Inventory

A normalized, tagged, and queryable dataset of what U.S. federal agencies reported under OMB Memorandum M-25-21 for the 2025 AI use case reporting cycle — plus an editorial Next.js dashboard that explores it.

## What's here

```
2025-aia-use-case-inventory/
├── data/
│   ├── raw/                              Source CSVs and XLSXs from 44 agencies
│   └── federal_ai_inventory_2025.db      Built SQLite database (not checked in)
├── dashboard/                            Next.js 16 app — editorial data-journalism view
├── scripts/                              Python helpers (schema comparison, etc.)
├── reference/                            Draft article + source material
├── agency-inventory-tracker.csv          Master tracker — 60 agencies
├── db.py                                 SQLite schema + connection
├── load_agencies.py                      Step 2 — tracker → agencies table
├── column_maps.py                        Step 3 — per-agency fuzzy column mapping
├── load_inventories.py                   Step 4 — CSV/XLSX → use_cases + consolidated_use_cases
├── build_lookups.py                      Step 4.5 — seed products, aliases, templates
├── auto_tag.py                           Step 5a — first-pass automated tagging
├── compute_maturity.py                   Step 7 — agency maturity scoring
├── KEY_FINDINGS.md                       Summary report for the piece
├── AGENT_TAGGING_GUIDE.md                Per-agency sub-agent tagging rubric
├── MANUAL-DOWNLOADS-NEEDED.md            Source URLs that required manual browser download
└── schema-comparison-report.csv          Per-agency M-25-21 compliance snapshot
```

## Reproducing the database

```bash
# Seed schema + lookup tables
make fix                    # rebuild schema, data, tags, product edges, maturity, and audit/db_snapshot.md
```

Per-agency refinement and cross-reference review were performed by sub-agents; see `AGENT_TAGGING_GUIDE.md` for the rubric and `KEY_FINDINGS.md` for results.

## Running the dashboard

```bash
cd dashboard
npm install
npm run dev          # localhost:3000
```

Reads directly from `../data/federal_ai_inventory_2025.db` via `better-sqlite3` in Server Components. See `dashboard/README.md` and `dashboard/EDITORIAL_STYLE_GUIDE.md`.

## Headline numbers (2025 cycle)

- **3,809** use case entries — 3,617 individual + 192 consolidated
- **44** agencies with published data (60 tracked total)
- **217** canonical AI products cross-referenced with 367 observed aliases
- **726** product attribution edges across 637 inventory entries
- **22** OMB/Appendix-style standard templates
- **7** agencies classified "leading" on AI maturity
- **15** agencies show enterprise-wide LLM access in their inventory
- **15** agencies report any coding assistant deployment

Volatile count blocks are generated from the database in `audit/db_snapshot.md`.
