# Product-queue review — resolve the 626 flagged vendor/product strings

## What this is

`review_queue_products` holds inventory rows whose vendor/product text the
heuristic matcher could not attribute: `compound_string` (several products
mashed into one cell) and `unmatched_vendor_text` (no catalog hit). Every
row needs a human-grade verdict so the product-attribution layer is
complete and future agents know nothing here is silently unresolved.

`input.csv`: one row per queue entry with the source text and the use
case's context columns. `catalog.txt`: the 644 canonical products
(`canonical_name | vendor`) you may map to.

## Decisions (one per input row)

- `map_to_existing` — the text names a product in catalog.txt. Put the
  EXACT canonical_name in `mapped_products`. For compound strings naming
  several catalog products, list them separated by ` ;; `.
- `propose_new` — a real commercial product missing from the catalog. Put
  `Name (Vendor)` in `proposed_new`; if also mapping some catalog
  products, fill both columns.
- `agency_internal_system` — a government-built system, not a commercial
  product (e.g. "LIGER", bespoke bureau tools).
- `false_positive` — the text is not a product at all (narrative prose,
  "N/A", org names, contract language).
- `unclear` — genuinely undecidable from the text; say why.

Rules:
- Generic platform mentions (plain "Microsoft", "AWS", "Google" with no
  product) are `false_positive` — vendor-only edges were deliberately
  removed in the 2026-05 generic-vendor retag; do not reintroduce them.
- M365 component names (Teams, Word, Outlook...) map to their specific
  catalog entries where present, NOT to "Microsoft 365" umbrella.
- Quote the deciding fragment of source_text in `reasoning`.

## Output

`verdicts_<batch>.csv` in this directory, EXACTLY these columns:

agency,use_case_name,source_text,decision,mapped_products,proposed_new,confidence,reasoning

- `agency`, `use_case_name`, `source_text` copied VERBATIM from input
  (they are the join keys — never alter, truncate, or re-wrap them).
- decision ∈ {map_to_existing, propose_new, agency_internal_system,
  false_positive, unclear}; confidence ∈ {high, medium, low}.
- Every assigned input row appears exactly once.
