# 2025 OMB Consolidated COTS File — Coverage Audit

**Source file**: `2025_consolidated_COTS_AI_use_cases.xlsx` (901 rows × 5 columns; OMB-published Appendix B aggregate)
**Loaded as**: `data/raw/cots-2025-ai-inventory-consolidated.xlsx`
**Pipeline date**: 2026-05-03

## What the file is

The 2025 OMB consolidated COTS file is the Appendix B "do you use any of these AI capabilities?" survey aggregated across 45 small/independent and CFO-Act agencies. Each agency answered Y/N to each of the 20 OMB-defined capability templates and, if Y, named the commercial products used.

| Metric | Value |
|---|---|
| Agencies | 45 |
| OMB capability templates | 20 |
| Total rows | 900 (45 × 20) |
| Y rows (agency uses this capability) | 468 |
| N rows | 416 |
| Blank | 16 |
| Compound product strings (Y rows) | 172 |

Schema (5 columns): `Agency`, `AI Use Case`, `Agency Use (Y/N)?`, `Name of Commercial Product or Service Used`, `Estimated # of Licenses/Users`. **No `Commercial Examples` column** — distinct from the older 6-column per-agency variant.

## Before vs after

|  | Before | After |
|---|---:|---:|
| `consolidated_use_cases` rows | 192 | **900** |
| Distinct agencies in `consolidated_use_cases` | 11 | **45** |
| `consolidated_use_case_products` edges | ~150 | **596** |
| Total `products` | 217 | **242** |
| Microsoft 365 Copilot mentions | scattered | **178** edges |
| Product-extraction coverage by mention volume | 36% exact, 9% substring, 55% unmatched | **61% exact, 6% substring, 31% unmatched** |

## Top remaining unmatched (deliberate)

These are intentional non-matches, not gaps:

- **`Various` (24), `N/A` (16), `Response`, `WebApps`, `External- Chatbots`, `Internal Gov Cloud- Chatbots`** — non-product placeholders. `product_resolution.NON_PRODUCT_PLACEHOLDERS` lists them; they produce 0 product edges, which is correct.
- **`NIPRGPT` (4), `CamoGPT` (4), `Ask Hamilton` (4), `AcqBot` (3), `OpenWebUI` (3), `xAI gov` (2)** — agency-built systems, not commercial products. Per `audit/human_review_products.md` these are `leave_unmapped`. `auto_tag.infer_entry_type` classifies them as `custom_system` / `bespoke_application` instead.
- **Bare `Copilot` (15), `CoPilot` (11)** — too ambiguous between Microsoft 365 Copilot, GitHub Copilot, Copilot for Security, Copilot Studio, Salesforce Copilot. Build_lookups.py:7-10 documents this. The compound-string review queue is the right route for these — an LLM/curator can disambiguate per-context.
- **`Apple Iphone` (1, lowercase variant), `Apple iPhone` (19)** — both now map to `Apple Face ID` via aliases.

## Agency-name normalization

Five existing top-level orgs got new aliases to absorb OMB's 2025 spellings, plus one VA sub-agency (VA-OIG) became its own agency entry:

| OMB spelling in COTS file | Resolves to |
|---|---|
| Department of Treasury | Department of the Treasury |
| Federal Reserve Board of Governors | Federal Reserve Board |
| Export-Import Bank of the U.S. | Export-Import Bank |
| United States International Trade Commission | U.S. International Trade Commission |
| United States Election Assistance Commission | Election Assistance Commission |
| United States Office of Special Counsel | U.S. Office of Special Counsel |
| Department of Veteran Affairs-OIG | (new agency: VA-OIG) |

Seven net-new agencies seeded (filed only via the COTS aggregate, no per-agency inventory): AbilityOne Commission, Farm Credit Administration, Udall Foundation, National Endowment for the Arts, National Indian Gaming Commission, OSHRC, Surface Transportation Board.

## Product taxonomy expansion

**Microsoft Copilot family — folded, not split.** All 13 spelling variants of Microsoft 365 Copilot now alias to the single canonical `Microsoft 365 Copilot` product. `Microsoft 365 Copilot Chat` is a separate child product (`parent_product_id` → Microsoft 365 Copilot) for the in-app chat tier that several agencies (OPM, SSA, VA) explicitly distinguish.

**New canonical products** (25 added): NotebookLM, Perplexity, Ask Sage, Cursor, Poolside, Synthesia, Canva, DALL-E, Sprout Social, FS Pro, Asana, Monday.com, Slack, Zoom, BioRender, Alteryx, Tableau, Palantir AIP, Microsoft Purview, SentinelOne, Wiz, Magnet Forensics, Google Lens, Google Pixel.

**Consumer features** (4 added with `product_type=consumer_feature` so vendor-share charts can opt out): Apple Face ID, Apple Maps, Google Maps, Google Pixel.

**Substring fix:** Added `Gemini for Google Workspace` as an explicit alias of Gemini (length-sorted, so it now wins over `Google Workspace` in greedy-longest-first matching).

## Per-agency files superseded

The COTS aggregate file is the canonical source for these 45 agencies' Appendix B filings. The 11 per-agency consolidated files that previously fed `consolidated_use_cases` are now in `load_inventories.SKIP_FILES`:

CSOSA, DOL-consolidated, EAC, FCC, FDIC-consolidated, HUD-consolidated, NLRB, OSC, PBGC, USITC, USTDA.

Each agency's *canonical* M-25-21 inventory file (where one exists, e.g. DOL-2025-ai-inventory.csv, FDIC-2025-ai-inventory.csv, HUD-2025-ai-inventory.xlsx) continues to load normally.

## Idempotency

`make fix` is destructive (full DELETE + reload), so re-running produces identical row counts. The `consolidated_use_cases.slug` UNIQUE constraint plus deterministic `slugify(agency_abbr, primary_key)` plus `INSERT OR IGNORE` defend against accidental duplicate rows if the loader is invoked outside `make fix`.

## What changed (file index)

| File | Change |
|---|---|
| `data/federal_hierarchy_seed.py` | +7 new top-level orgs; aliases on 5 existing + VA-OIG sub-org |
| `agency-inventory-tracker.csv` | +8 rows (7 new + VA-OIG) |
| `column_maps.py` | `is_consolidated_format` uses normalized headers; `map_consolidated_headers` routes through `normalize_header`; added `Agency` column mapping |
| `load_inventories.py` | Multi-agency-per-file branch; per-row agency resolution from seed-tree alias index; deterministic slug; INSERT OR IGNORE; SKIP_FILES expanded |
| `migrations/m003_consolidated_source_format.py` | New: adds `source_format` column to `consolidated_use_cases` |
| `build_lookups.py` | Microsoft Copilot family aliases; `Microsoft 365 Copilot Chat` child; 25 new products + 4 consumer features; `Gemini for Google Workspace` alias |
| `product_resolution.py` | `NON_PRODUCT_PLACEHOLDERS` stop-list short-circuit |
| `data/raw/cots-2025-ai-inventory-consolidated.xlsx` | New: the OMB file |
| `dashboard/.claude/skills/omb-ai-use-case-inventory/` | New: skill copy so dashboard agents see schema reference |
