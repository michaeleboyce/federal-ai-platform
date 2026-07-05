# Product band audit 2026-07 — spot-audit the products that carry seat mass

## Why

The stratified seat model maps products to population strata via
`products.product_type`, families via `parent_product_id`, and GenAI
status via `is_generative_ai`. Only the ~100 products that appear on
banded consolidated rows actually carry seat mass — this pass audits
exactly those, because a wrong `product_type` there silently moves
thousands of modeled seats between strata.

## Input

`inputs/products_on_banded_rows.csv` — one row per product with its
current catalog fields plus the banded rows it touches (`banded_rows`
count, `max_band`, `agencies`, `example_use_cases`) so the stakes of each
call are visible.

## What to check per product

1. `product_type` — is it right? (The type→stratum map: general_llm /
   productivity / document_ai / search / translation / transcription /
   itsm / agent_platform → general; coding_assistant / ml_platform /
   developer_tool / data_analytics / cloud_platform → technical;
   legal_research / ediscovery → legal; investigative_data / forensics →
   investigative; media_analysis / social_listening → comms;
   clinical_decision_support → clinical; security_tool / consumer_feature
   / computer_vision / biometrics → excluded from seats.)
2. `parent_canonical_name` — should this product roll up to a family
   parent it currently lacks (e.g., a "Microsoft 365" child), or is its
   current parent wrong?
3. `is_generative_ai` / `is_frontier_llm` — right for what the product is
   in 2025?
4. `vendor` — obviously wrong or missing?

Recommend a change ONLY where the current value is wrong — this is an
audit, not a re-cataloging. When correct, don't emit a row.

## Output

Write `recommendations.csv` to this directory:

canonical_name,field,current_value,proposed_value,confidence,reasoning

- field ∈ {product_type, parent_canonical_name, is_generative_ai,
  is_frontier_llm, vendor}
- one row per (product, field) you propose changing
- confidence ∈ {high, medium, low}
- reasoning: 1–2 sentences; cite the product's actual capability, and for
  parent changes name the family logic.

Also write `notes.md`: counts per field changed, products you were unsure
about, and anything surprising (e.g., a product whose banded usage
contradicts its catalog identity).

## Routing note (for the apply step, not the auditor)

Corrections are applied through the rebuild-surviving CSV homes — never
direct UPDATEs: product_type → `audit/product_categorization/proposal.json`;
parents → `data/product_hierarchy_edges.csv`; flags/vendor →
`data/expanded_product_catalog.csv` (promoting filings-seeded products
into the catalog where needed).
