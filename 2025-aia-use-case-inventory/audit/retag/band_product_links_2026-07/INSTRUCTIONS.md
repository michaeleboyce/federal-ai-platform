# Band product links 2026-07 — link the unlinked banded rows

## What this is

~71 banded `consolidated_use_cases` rows (rows carrying a license band)
have no `consolidated_use_case_products` link, so the seat model can't
see which tool family they belong to. This pass links each one to the
canonical product catalog — or explicitly concludes it can't be linked.

`input_batch<N>.csv` has one row per unlinked banded row with the
product string as filed, the use-case narrative, the band, and up to 5
`candidates` from the catalog (alias substring hits + fuzzy matches).
`inputs/catalog_snapshot.csv` is the full 655-product catalog — the
candidates are a head start, not a constraint.

## Verdicts

- `link` — an existing catalog product matches. Put its EXACT
  `canonical_name` (from the snapshot) in `product_canonical_name`.
  Multi-product strings ("Azure OpenAI, Microsoft365 Copilot, Qlik"):
  emit ONE OUTPUT ROW PER PRODUCT (same slug repeated) — the link table
  is many-to-many.
- `new_product` — a real, identifiable product that isn't in the catalog.
  Name it the way the catalog would (vendor prefix where the catalog does:
  "Adobe Firefly", not "firefly"), and fill the new-product columns.
- `no_product` — the row names no identifiable product ("various AI
  tools", "AI-powered features"). Say why.

## Confidence vocabulary

`confidence` ∈ {strong, inferred} — this matches the DB CHECK constraint.
`strong` = the product name appears verbatim (or as a known alias) in the
row. `inferred` = you're reading through a description ("our office suite
copilot" → M365 Copilot at a Microsoft shop).

## Output

Write `links_<your-batch>.csv` to this directory with EXACTLY these
columns, keyed by `slug`:

slug,agency,ai_use_case,verdict,product_canonical_name,confidence,evidence_text,reasoning,new_vendor,new_product_type,new_is_generative_ai,new_parent_canonical_name

- `evidence_text`: the verbatim phrase from the row that names the product.
- The four `new_*` columns are filled ONLY for `new_product` verdicts
  (product_type must be one of the existing types in the catalog snapshot;
  parent only if the catalog has an obvious family parent).
- Every input row appears at least once; `link` rows may repeat a slug
  (one per product); `new_product`/`no_product` rows appear exactly once.

Optional web search to identify an ambiguous product name; put the URL in
reasoning.
