# Linkage-pass charter — May 2026

You are one of four parallel labeling agents (A/B/C/D) working through the
unlinked corpus of the Federal AI Use Case Inventory. Your job: triage your
slice and emit `recommendations.json` so the integration script can stage
catalog additions, hierarchy edges, aliases, and `use_case_products` edges.

This pass extends `audit/product_gap_review/CHARTER.md` (the prior 3-agent
audit). Read that file first if you haven't seen the pattern.

## Why this pass exists

The catalog covers only 23% of individual use cases (832 / 3,549) and 41%
of consolidated entries (369 / 900). Two distinct gaps:

- **Catalog gaps** — real commercial products named verbatim in
  `vendor_name + use_case_name + system_name` but missing from `products`
  entirely (e.g., Abridge). The linker can't link to something that
  doesn't exist.
- **Linker recall gaps** — products that *are* in the catalog but where
  the filing names a sub-product the linker doesn't alias (e.g., "Adobe
  Premiere" → no edge to `Adobe Creative Cloud Suite`).

## Slice ownership (do NOT cross slices)

| Agent | Slice | Rows | Input CSV |
|---|---|---:|---|
| A | Named-vendor individual use_cases | 279 | `inputs/slice_a_named_vendor_individual.csv` |
| B | Mention-only individual + named consolidated | 144 | `inputs/slice_b_*.csv` (two files) |
| C | Dark-sample individual (random 200) | 200 | `inputs/slice_c_dark_sample.csv` |
| D | Existing-catalog hierarchy review | 316 | `inputs/existing_catalog_snapshot.csv` |

Each agent writes ONLY to its own subdirectory under
`audit/linkage_pass_2026-05/agent_{a,b,c,d}/`. Do not touch the DB, the
catalog CSVs, or other agents' output.

## Inputs available to every agent

- `data/federal_ai_inventory_2025.db` (READ-ONLY). Query `use_cases`,
  `consolidated_use_cases`, `products`, `product_aliases`,
  `use_case_products`, `consolidated_use_case_products`, `agencies`.
- `data/expanded_product_catalog.csv` — current canonical catalog with
  alias lists per product (controlled vocabulary for `product_type` is
  whatever appears in this CSV's `product_type` column).
- Your slice's input CSV under `inputs/`.

## Decision rubric

Per row, write one decision object to `recommendations.json`:

| Decision | Meaning |
|---|---|
| `link` | Real product use; add an edge `use_case → existing product`. Provide `use_case_id` (or `consolidated_use_case_id`) + `product_id` + `canonical_name`. |
| `add_product` | Real product not in catalog. Provide proposed canonical_name, vendor, product_type, is_generative_ai, and (optional) proposed_parent_canonical_name. Also list use_case_ids that should link to it. |
| `add_alias` | Existing product needs a new alias to cover this row. Provide product_id, canonical_name, proposed_alias. May also list use_case_ids that would link via it. |
| `tighten_alias` | An existing alias is too greedy. Provide product_id, the alias to replace, and a more specific replacement. |
| `false_positive` | The row mentions a vendor/product in passing but doesn't deploy it as the AI tool. |
| `unclear` | Cannot tell from the narrative. Flag for human review. |
| `add_hierarchy_edge` | **(Agent D only)** Existing child product should be parented to an existing parent. Provide child_canonical_name + parent_canonical_name. |

### Decision principles

1. **Read the use case's actual narrative before deciding.** The input CSV
   gives you the verbatim source fields, but for context pull more from
   the DB:
   ```sql
   SELECT u.id, a.abbreviation, u.use_case_name, u.system_name,
          u.vendor_name, u.problem_statement, u.expected_benefits,
          u.system_outputs, u.development_type
     FROM use_cases u JOIN agencies a ON a.id = u.agency_id
    WHERE u.id IN (...);
   ```
   For consolidated rows:
   ```sql
   SELECT c.id, a.abbreviation, c.ai_use_case, c.commercial_product,
          c.commercial_examples, c.agency_uses
     FROM consolidated_use_cases c
     JOIN agencies a ON a.id = c.agency_id
    WHERE c.id IN (...);
   ```
2. **A `link` requires the product to be the AI tool the use case
   deploys, not a passing reference.** "We use Teams to notify users
   when our model finishes" is NOT a Teams link.
3. **`add_product` requires real evidence the product exists.** If the
   row names a vendor + a system, the system is a real commercial
   product, AND the development_type ∈ {"Purchased from a vendor", "COTS"},
   you can propose. If only a vendor name appears with no product name,
   it's `unclear`, not `add_product`.
4. **Required fields when `decision="add_product"`:**
   - `proposed_canonical_name` — distinctive product name (e.g.,
     "Abridge Ambient Scribe", "Polaris Alpha"). Title-case, no
     trailing punctuation.
   - `vendor` — exact vendor name (e.g., "Abridge").
   - `product_type` — must be from the controlled vocabulary in
     `data/expanded_product_catalog.csv` (e.g., `transcription`,
     `general_llm`, `clinical_decision_support`,
     `physical_security`, `legal_research`).
   - `is_generative_ai` — `0` or `1`.
   - `proposed_parent_canonical_name` — OPTIONAL, only if the product is
     a sub-product of an existing catalog row (e.g., "Adobe Premiere" →
     "Adobe Creative Cloud Suite").
   - `confidence` — `high` / `medium` / `low`.
   - `reasoning` — 1–2 sentences why this is a real product, drawing on
     the row's text.
5. **Aliases must be ≥4 chars and not common English words.** Never
   "AI", "the", "Web", or anything that would match unrelated rows.
   Vendor co-occurrence is a strong signal ("Microsoft Power Automate"
   is safer than "Power Automate" alone).
6. **Hierarchy edges (Agent D)**: never create a cycle. Max chain depth
   ≤ 5 (the dashboard CTE caps at 5 hops). When in doubt, leave parent
   unset.

## Output schema

```json
{
  "use_case_id": 60824,
  "consolidated_use_case_id": null,
  "use_case_agency": "VA",
  "decision": "add_product",
  "product_id": null,
  "canonical_name": null,
  "proposed_canonical_name": "Abridge Ambient Scribe",
  "vendor": "Abridge",
  "product_type": "transcription",
  "is_generative_ai": 1,
  "proposed_parent_canonical_name": null,
  "proposed_alias": null,
  "proposed_alias_replacement": null,
  "evidence_quote": "...verbatim phrase from the source text, ≤120 chars...",
  "confidence": "high",
  "reasoning": "VA's use case explicitly names Abridge as vendor and Abridge Ambient Scribe as system_name; dev_type='Purchased from a vendor'.",
  "notes": ""
}
```

For `link`: populate `use_case_id`, `product_id`, `canonical_name`,
`evidence_quote`. Leave proposed_* fields null.

For `add_alias`: populate `product_id`, `canonical_name`,
`proposed_alias`, `evidence_quote`. Optionally `use_case_id`(s) that
would link via the alias.

For `false_positive` / `unclear`: populate `use_case_id` (or
`consolidated_use_case_id`) + `evidence_quote` (or empty) + `reasoning`.

For Agent D `add_hierarchy_edge`: populate `canonical_name` (child),
`proposed_parent_canonical_name`, `confidence`, `reasoning`.

Also write `notes.md` with: count per decision type, surprising
findings, products that need catalog-level rework, what you flagged as
unclear.

## Time budget

45–75 minutes per agent. Time on the named-vendor and named-consolidated
slices should be the most productive; the dark sample will be heavy on
`unclear` / `false_positive` and that's fine — the point is to estimate
the addressable rate of the broader 2,347-row dark population.

## Final-summary contract

Final reply ≤300 words: count of decisions by type, the most surprising
findings, and any products that need catalog-level engineering attention.
