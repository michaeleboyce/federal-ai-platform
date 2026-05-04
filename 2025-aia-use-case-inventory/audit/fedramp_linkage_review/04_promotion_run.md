# FedRAMP Linkage Fix — Run Report

Plan: `~/.claude/plans/virtual-sniffing-peacock.md`
Date: 2026-05-03

## Summary

| Metric | Before | After |
|---|---:|---:|
| Products | 242 | 240 |
| Hierarchy edges | 5 | 36 |
| `fedramp_product_links` | 0 | 64 |
| Distinct linked products (direct) | 0 | 59 |
| Products with link via parent inheritance (CTE) | 0 | 32 |
| **Total covered (direct + inherited)** | **0** | **91 / 235 commercial** |
| `fedramp_leveraged_systems` | 0 | 1762 |

## Backups

- `data/federal_ai_inventory_2025.db.backup-20260503-224113` — pre-Phase-1
- `data/federal_ai_inventory_2025.db.backup-20260503-225859-pre-recovery` — pre-recovery (after external `make fix` rebuild)

## Phase results

### Phase 1 — Duplicate merge

Merged via `scripts/merge_duplicate_products.py` (canonical-name lookup; survives ID rebuilds):
- `Google NotebookLM` → `NotebookLM` (no dependents lost)
- `Azure AI Vision / Document Intelligence` → `Azure AI Document Intelligence` (1 use_case_product, 1 entry_product_edges, 2 aliases repointed)

The third audit-flagged pair (`Microsoft 365` vs `Microsoft 365 Apps for Enterprise`) was kept distinct — different SKUs. The latter was instead made a child of the former in Phase 5.

### Phase 2 — Queue re-key

`scripts/rekey_fedramp_link_queue.py`: 192/192 product queue rows resolved via canonical_name + alias join. `fedramp_link_queue.inventory_id` re-keyed from stale 85–305 to current product IDs.

Skipped the audit's "alias gap-fill" sub-step: agency→product alias additions wouldn't help the FedRAMP linkage matcher (it operates on FedRAMP CSO/CSP text, not product aliases). Wrong rejections handled directly via Phase 7 hand-link CSV instead.

### Phase 3 — Promote strong-signal queue decisions

`scripts/promote_resolved_link_queue.py`:
- Scanned 84 resolved product queue rows
- 19 promoted (8 via `FR\d+`/`F1\d+` regex, 11 via `accept_N` JSON pick)
- 65 deferred (inheritance narratives — no per-row fedramp_id; covered in Phase 6 by parent links)
- All inserts: `confidence='manual'`, `source='link_queue'`, notes verbatim

### Phase 4 — Pipeline integration

Added `python3 scripts/promote_resolved_link_queue.py --apply` to `Makefile`'s `fedramp` target after `link_fedramp.py --apply`. Future queue resolutions auto-materialize; idempotent on re-run (verified — second run skipped all 19 as already-present).

### Phase 5 — Hierarchy + leveraged_systems

`scripts/apply_product_hierarchy_edges.py` from `data/product_hierarchy_edges.csv`:
- 33 edges added (Microsoft Azure platform/M365/Power Platform/Purview, Google GCP/Vertex/Workspace, AWS Q rebrand, Adobe CC, IBM Watson, LexisNexis, Veritone, Visual Studio)
- 2 edges removed (`GitHub Copilot → M365 Copilot`, `NotebookLM → Gemini`)
- Final hierarchy: 5 → 36 edges; max chain depth 3 (Google Cloud Platform → Vertex AI → Agentspace), well under dashboard's 5-hop CTE cap

`load_fedramp.py` extended to mirror `product_leveraged_systems` from the FedRAMP marketplace DB into a new `fedramp_leveraged_systems` table (1762 rows of CSO→CSO supply-chain dependency edges).

### Phase 6 — Inheritance narratives reconciled via parent links

Instead of writing 41 direct child links, linked the parent products that the narratives reference. The dashboard's existing 5-hop inheritance CTE then propagates coverage to all children. Parent links added (within Phase 7's CSV):

| Parent | FedRAMP CSO | Children covered |
|---|---|---|
| Microsoft Azure Platform | Azure Government (High) | 7 (Azure OpenAI, Foundry, Doc Intel, Speech, etc.) |
| Microsoft Power Platform | M365 GCC | 3 (Copilot Studio, AI Builder, Power BI) |
| Adobe Creative Cloud Suite | Adobe CC for Enterprise (Li-SaaS) | 2 (Photoshop, Firefly) |
| Google Cloud Platform | Google Services (GCP) High | 2+ (Vertex AI → Agentspace; Cloud Vision) |
| Google Workspace | Google Workspace (High) | NotebookLM-adjacent narratives |
| IBM Watson | IBM Cloud for Government (High) | 2 (ARGOS, CoreDF) |
| Veritone | Veritone iDEMS Government (Moderate) | 1 (Illuminate) |

### Phase 7 — Hand-linked orphans (39 rows)

`data/fedramp_link_decisions.csv` applied via `scripts/apply_fedramp_link_decisions.py`. All 39 resolved (canonical-name lookup, valid fedramp_id). Sections:

- 7 parent-product links (above)
- 16 standalone-product links from inheritance narratives (Splunk, Snowflake Cortex, UiPath, Articulate, Cellebrite, KnowBe4, BMC Helix, Skillsoft Percipio, Everlaw, Appian, H2O, Alation, OpenText x2, Sentinel, Dynamics 365)
- 6 wrong-rejection fixes (ChatGPT, OpenAI API, Gemini, GitHub Copilot, Altana, Exiger)
- 10 never-queued targets (Grok, Slack, Zoom, ServiceNow x2, Salesforce, Crowdstrike, Wiz, Asana, Perplexity)

### Phase 8 — Re-tier multi-candidate decisions

Added 6 High-tier counterparts alongside the Moderate links Phase 3 promoted (kept Moderate too — some agencies authorize at Moderate):

- Zscaler: + ZIA-Government High
- Palo Alto Networks: + GCS-HIGH
- Citrix: + Citrix for Government - High
- Microsoft 365: + M365 GCC-High (alongside MSO365MT Moderate)
- Palantir Federal Cloud Service: + PFCS - High
- Plus a baseline Moderate link for Zscaler (which was missing entirely)

### Phase 9 — Tests, sync, build

- pytest (this repo): **71/72 passing (1 pre-existing failure)** — `test_name_match_score_fuzzy_threshold` fails on main without my changes too, unrelated to linkage.
- DB synced: `cp data/federal_ai_inventory_2025.db dashboard/data/federal_ai_inventory_2025.db` (the dashboard's `prebuild` script also auto-syncs).
- `npm run build` (dashboard): succeeded; built 240 static product pages and all FedRAMP routes.

## Mid-run incident — external `make fix` rebuilt the products table

Between Phase 7's dry-run and apply, an external process (a Makefile-modifier change pulled in `apply_product_gap_review.py` and `make fix` ran) rebuilt the `products` table with new IDs (3206-3574 → 3576-3944). This wiped Phase 1's merges, Phase 2's rekey, Phase 3's 19 link_queue rows (orphaned-then-cleaned), and Phase 5's hierarchy edges.

Recovery (all scripts use canonical-name lookup so they're rebuild-safe):
1. Re-ran `merge_duplicate_products.py` (after refactoring it to look up by name instead of hardcoded IDs)
2. Re-ran `rekey_fedramp_link_queue.py`
3. Re-ran `apply_product_hierarchy_edges.py`
4. Re-ran `promote_resolved_link_queue.py` — recovered the 19 lost link_queue rows
5. `apply_fedramp_link_decisions.py` re-applied (skipped 45 already-present)

End state matches the original target. **Lesson:** all linkage and hierarchy scripts MUST resolve products via canonical_name (not raw IDs) to survive the inevitable rebuilds. This is now baked into every script in this PR.

## Files added/modified

**New:**
- `scripts/merge_duplicate_products.py`
- `scripts/rekey_fedramp_link_queue.py`
- `scripts/promote_resolved_link_queue.py`
- `scripts/apply_product_hierarchy_edges.py`
- `scripts/apply_fedramp_link_decisions.py`
- `data/product_hierarchy_edges.csv`
- `data/fedramp_link_decisions.csv`
- `audit/fedramp_linkage_review/04_promotion_run.md` (this file)

**Modified:**
- `Makefile` (added `promote_resolved_link_queue.py --apply` to `fedramp` target)
- `load_fedramp.py` (added `fedramp_leveraged_systems` mirror)
- `data/federal_ai_inventory_2025.db` (the actual data changes)

**Synced:**
- `dashboard/data/federal_ai_inventory_2025.db`

## What's left

Per the plan's "Deferred" section:

1. **`business_function` and `service_model` ingest** — useful as filter facets on `/fedramp/marketplace/products`. Spin out as a separate plan.
2. **Dashboard panel for `leveraged_systems`** — data is in the DB; UI is a follow-up. The supply-chain visualization on `/fedramp/marketplace/products/[id]` would be the answer to the user's "services within a product" design question (1762 dependency edges available to render).
3. **Re-key the 65 deferred queue rows' decision_notes** to point at the new product IDs (currently they have only stale narrative). Low priority.
4. The remaining ~144 commercial products without coverage — most are correctly unlinked (no FedRAMP presence: Anthropic Claude, most coding assistants, many AI-specific tools). A handful may merit a follow-up review pass.
