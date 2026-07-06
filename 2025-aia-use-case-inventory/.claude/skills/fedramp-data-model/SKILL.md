---
name: fedramp-data-model
description: Use when working with the FedRAMP side of the database or dashboard — the fedramp_* tables, authorization vs reuse semantics, the AI classifications (product-level vs service-level), the inventory↔FedRAMP crosswalk and link queue, the sleeping/spread/unlinked-AI coverage boards, or the `make fedramp` chain. Covers what a fedramp_authorizations row means, why reuse_count never reconciles with the ledger, the TWO distinct sleeping boards, the EFFECTIVE_FEDRAMP_LINKS_CTE parent walk every coverage query must use, which link rows survive relinking, and the different confidence enum trap. Triggered by: any query touching fedramp_% tables, editing load_fedramp.py / link_fedramp.py / scripts/*fedramp*, dashboard work under lib/db/fedramp/ or app/fedramp/, or interpreting ATO/reuse/sleeping numbers for an article.
---

# FedRAMP Data Model — Reference

The FedRAMP marketplace is mirrored into the inventory DB (from the sibling
`2025-fedramp/data/fedramp_marketplace.db`, read-only) and cross-walked to
the AI inventory. The semantics below are the ones agents re-derive every
session — read this instead. All counts as of snapshot 2026-06-12.

## The tables in one pass

| Table | Rows | What a row is |
|---|---|---|
| `fedramp_products` | 659 | A marketplace listing. **`fedramp_id` (TEXT) is FedRAMP's own stable id — safe to cite/hardcode.** Carries status, impact level, and marketplace `authorization_count`/`reuse_count` (see the reconciliation trap). |
| `fedramp_authorizations` | 3,385 | ONE agency's ATO event on ONE package. `ato_type`: `Initial` (523) = the agency did its own authorization; `Reuse` (2,726) = riding an existing one; NULL (136) = pre-2020 legacy. This column is THE original-vs-reuse signal. |
| `fedramp_agencies` (91) / `fedramp_assessors` (32) | | FedRAMP's own directories — a SEPARATE id namespace from inventory `agencies`, bridged only by `fedramp_agency_links`. |
| `fedramp_leveraged_systems` | 1,751 | CSO→CSO supply-chain edges (a SaaS running on GovCloud). **Nothing to do with agency reuse** — free-text `system_name`, fuzzy-resolved at query time, resolves ~half the time. |
| `fedramp_authorized_services` | 1,902 | The **"services in scope"** catalog — named sub-services inside each package (Bedrock inside AWS). Same thing as "authorized services" / "services-in-scope" in prose; there is no second table. |
| `fedramp_business_functions` (2,424) / `fedramp_service_models` (726) | | Multi-valued tags per package. |
| `fedramp_ai_classification` | 659 | Per-PRODUCT AI label: `core_ai` 46 / `ai_featured` 225 / `not_ai` 388. Single LLM pass + manual overrides only. |
| `fedramp_ai_service_classification` | 1,591 | Per-SERVICE-NAME AI label (keyed on the `service` string, shared across packages): `core_ai` 129 / `ai_featured` 122 / `not_ai` 1,340. Went through full QC + adjudication (rubric v2 after a systematic AI-overcall was caught) — **the more-verified of the two classifications; prefer it for article claims.** |
| `fedramp_product_links` | 132 | inventory `products.id` ↔ `fedramp_id`. `source`: `alias_match` (rebuilt every relink), `manual_csv`, `link_queue` (both survive relinks). |
| `fedramp_agency_links` | 50 | inventory `agencies.id` ↔ `fedramp_agencies.id` (45 alias_match self-healing + 5 manual_csv that do NOT self-heal — first suspect if agency links look wrong after a marketplace re-scrape). |
| `fedramp_link_queue` | ~823 | Ambiguous link candidates (`product`/`agency` × `pending/resolved/rejected`) — the `/fedramp/curate` workflow. |
| `fedramp_service_product_map` | 42 | Curated core-AI service name → inventory `product_canonical_name` crosswalk (string-keyed) with capability_category + evidence_tier. Backs the sleeping-services board exclusively. |
| `fedramp_snapshot` | 1 | Singleton snapshot metadata. |

`fedramp_link_evidence` does NOT exist (dropped by m021, was always empty) —
references to it are stale. `product_capability_labels` is a fifth sidecar
(not fedramp_-prefixed) the sleeping-services board depends on.

## Semantics agents keep re-deriving

- **Authorization vs reuse**: `ato_type` on `fedramp_authorizations`.
  Adoption-breadth queries deliberately DON'T filter it — a reuse ATO still
  means "this agency can use it," so boards count
  `COUNT(DISTINCT agency_id)` regardless.
- **`reuse_count` NEVER reconciles with the authorizations ledger** (AWS
  GovCloud: counter 1,175 vs 82 ledger rows). They're independently-sourced
  marketplace tallies; the ledger under-records reuse. Read counter-based
  numbers as upper bounds; never build a check or claim assuming they match.
- **TWO sleeping boards — don't conflate their counts**:
  - `/fedramp/coverage/sleeping` (product-level, `coverage.ts`): agencies
    holding an ATO on a product that OTHER agencies report AI use for, with
    no inventory row themselves (authorized_pairs MINUS using_pairs).
  - `/fedramp/coverage/sleeping-services` (service-level,
    `sleeping-services.ts`): same question inside packages (Azure OpenAI
    inside Azure), via `fedramp_service_product_map` +
    `product_capability_labels`; adds `similar_deployed` ("agency reports
    something in the same capability class") and time gates
    (`SLEEPING_INVENTORY_CUTOFF` 2025-12-31 — post-cutoff ATOs can't have
    produced a 2025 inventory row; `SLEEPING_ATO_DATE_FLOOR` filters junk
    dates).
- **"Unlinked AI"** (`classification.ts`): marketplace-AI products with ZERO
  inventory linkage — orthogonal to sleeping (which requires a link and a
  lead user).
- **"Spread"** (`spread.ts`): of authorized core-AI products, single-ATO vs
  multi-ATO; tracks the frontier trio (ChatGPT / Gemini for Government /
  Perplexity) by exact `cso` NAME, never id.
- **"Shelf inside the shelf"**: core-AI SERVICES in scope of packages
  agencies already hold ATOs for — measures **legal reach, not enablement**
  ("in scope of an authorization the agency already holds — not necessarily
  enabled or available to staff" — keep that caveat with any citation).
- **Every AI-filtered coverage number excludes the agency's full ATO
  portfolio** by construction (filtered through the product links). Mixing
  filtered and unfiltered styles is the classic way to 10× a gap number
  (DOJ: ~127 total ATOs, ~20 AI-linked — called out three times in
  `coverage.ts`). The marketplace explorer (`marketplace.ts`,
  `/fedramp/marketplace/*`) is the intentionally-unfiltered surface.

## The crosswalk — always use the CTE

`EFFECTIVE_FEDRAMP_LINKS_CTE` (`dashboard/lib/db/shared/sql-fragments.ts`)
walks `parent_product_id` up to 5 hops so coverage inherited from a parent
platform (Textract → AWS) is found, tagging `inherited_from_parent_id`.
**Any new "does this product have FedRAMP coverage" query must use it** — a
raw join on `fedramp_product_links` silently misses inherited coverage.

## `make fedramp` chain (order matters)

`load_fedramp.py` (mirror 9 tables wipe-and-reload from the sibling repo) →
`apply_fedramp_ai_classification.py` (CSV keyed by `fedramp_id`; **exits
non-zero below 100% coverage** — a fresh marketplace scrape with new
products fails until `classify_fedramp_ai.py` tops up the CSV) →
`apply_fedramp_service_classification.py` (same contract, keyed by service
string) → `apply_fedramp_service_product_map.py` (string-keyed; exit 1 enum/
consistency, exit 2 unresolved product or non-core_ai mapping) →
`apply_product_capability_labels.py` (exit 2 if any edged product lacks a
label — top up via the `audit/retag/product_capability_*` round) →
`link_fedramp.py --apply` (rebuilds ONLY `source='alias_match'` link rows;
manual/queue-sourced rows survive) → `promote_resolved_link_queue.py`
(queue rows marked resolved → links with `source='link_queue'`).

**Across plain `make fix`**: the fedramp mirror + classifications are
untouched, BUT because `build_lookups.py` reissues `products.id`, the fix
chain re-runs the link-recovery block (`rekey_fedramp_link_queue`,
`link_fedramp`, `promote_resolved_link_queue`,
`apply_fedramp_link_decisions`) — that ordering is load-bearing ("without
this step every full rebuild loses ~18 authorized-listing links").

## Curation workflow

`/fedramp/curate` (read-only browser, deliberately unlinked from nav) →
CSV export → hand-edit decisions → `scripts/import_fedramp_link_decisions.py
--apply` → resolved queue rows promoted with `decision_notes` carrying the
chosen `fedramp_id` (regex `(?:FR|F1)\d+` or `accept_N`).

## Dashboard module map — `dashboard/lib/db/fedramp/`

`marketplace.ts` (unfiltered explorer) · `links.ts` (crosswalk queries,
leveraged-systems walk, per-use-case coverage state) · `coverage.ts`
(AI-filtered hub + vendors/fit/agencies/unused + product-level sleeping) ·
`classification.ts` (product-level AI labels, unlinked-AI) · `spread.ts`
(spread, shelf-inside-shelf, frontier trio) · `sleeping-services.ts`
(service-level sleeping) · `queue.ts` (curate/queue reads).

## Traps

1. **Confidence enum differs from the inventory edges**:
   `fedramp_product_links`/`fedramp_agency_links` use
   `('strong','weak','manual')` — NOT the `('strong','inferred')` of
   `use_case_products`. Don't cross-apply the repo's usual translation rule.
2. Product-level vs service-level classification rigor differs (see table)
   — prefer service-level for citations.
3. `fedramp_agencies.id`/`fedramp_assessors.id` are copied verbatim from the
   sibling snapshot — stable within a snapshot, not across re-scrapes;
   `manual_csv` agency links are the non-self-healing exposure.
4. `fedramp_product_links.id`/`fedramp_link_queue.id` are ordinary
   AUTOINCREMENT — resolve by `canonical_name`/`fedramp_id`/`service`
   string, never a stored integer id.
5. "Services in scope" = "authorized services" = `fedramp_authorized_services`
   — one table, several prose names; don't hunt for a second one.

Cross-refs: inventory side + rebuild rules → `inventory-db-model`;
classification/QC round mechanics → `adjudication-rounds`; publishing
FedRAMP numbers with caveats → `publish-and-repin`.
