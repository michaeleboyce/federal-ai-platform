# Review-queue resolution — agent charter

## What this is

`review_queue_products` holds 598 unattributed product mentions from the 2025 federal AI inventory. Each row is either:

- **`compound_string`** (55 rows) — a single source field listed multiple products, like `"Adobe Firefly, Microsoft M365 Copilot AI, FS Pro"`. The heuristic populator matched 0–3 of them; the queue captures the original text so a human/LLM can audit + add the missing edges.
- **`unmatched_vendor_text`** (543 rows) — a vendor / system / problem-statement field where no canonical product alias matched. Either a vague vendor ("Microsoft", "Various"), an agency-internal system name ("USCIS Electronic Immigration System"), or a product we genuinely don't have in the catalog.

## Your task

For your slice (`queue.json`), produce `recommendations.json` with one record per input row. Each record's `decision` is one of:

| decision | meaning |
|---|---|
| `link` | This row evidences use of a specific canonical product. Provide `canonical_name` (must exist in `product_catalog.json`). Multi-product rows can produce multiple `link` records — one per product found. |
| `add_alias` | The text contains a clear product name that's NOT in the catalog yet but probably should be. Provide `canonical_name` proposal + `alias_text` (the variant string seen). The applier will queue this for catalog expansion. |
| `agency_internal_system` | The text refers to an agency-built system, not a commercial product. e.g. "USCIS Electronic Immigration System (ELIS)". The use case still gets tagged via `auto_tag.infer_entry_type` as `custom_system` — no product edge needed. |
| `false_positive` | The "vendor" text is non-product noise: "Various", "N/A", contractor company names that aren't AI vendors, etc. Skip without action. |
| `unclear` | Genuinely ambiguous — not enough context to decide. |

## Your slice

Read `queue.json` from your slice directory. Each row carries:

```json
{
  "id": 13756,                     // review_queue_products.id
  "reason": "compound_string",
  "agency": "DHS",
  "scope": "use_case",             // or "consolidated"
  "entry_id": 50513,
  "entry_name": "API Security Vulnerability Technology",
  "system_name": "...",
  "vendor_text": "...",
  "source_text": "Discover, ingest, and analyze APIs ...",
  "heuristic_product_names": ["Apigee", "Akamai"]
}
```

`source_text` is the haystack the heuristic matcher searched. It often runs together fields (vendor + system + problem statement). Read it for context but be careful: a long paragraph may name many things, only some of which are AI products in this row.

## Output

Write to `recommendations.json` in your slice directory:

```json
[
  {
    "id": 13756,
    "decision": "link",
    "canonical_name": "Apigee",
    "evidence_quote": "Apigee for API analysis",
    "confidence": "high",
    "rationale": "Source text explicitly names Apigee as the AI-driven API analytics tool."
  },
  {
    "id": 13756,
    "decision": "link",
    "canonical_name": "Akamai",
    "evidence_quote": "Akamai security intelligence",
    "confidence": "high",
    "rationale": "Akamai's security platform is the second component of the system."
  },
  {
    "id": 13802,
    "decision": "agency_internal_system",
    "evidence_quote": "SCOUT LLM helps staff create content",
    "rationale": "SCOUT is DOC's internal LLM wrapper, not a commercial product. Use case should be tagged as custom_system via auto_tag."
  },
  {
    "id": 14001,
    "decision": "false_positive",
    "rationale": "Source text says 'Various' — agency declined to name a specific product."
  }
]
```

Notes on shape:
- One row's review can produce **multiple records** (compound strings → multiple `link` decisions).
- `canonical_name` must EXACTLY match a row in `product_catalog.json`. Misspellings break the applier.
- `evidence_quote` should be a contiguous substring of `source_text` ≤ 80 chars.
- `confidence`: `"high"` when explicit name match, `"medium"` when inferred from context, `"low"` when guessing.

## Rubric — how to decide

1. **Does the heuristic matcher's guess look right?** If `heuristic_product_names` already has the right product, that row already has a link — DON'T duplicate it. Only emit `link` for products NOT in the heuristic list.

2. **Is the text naming a real commercial vendor?** Cross-reference against `product_catalog.json` (240 products). If you see "Microsoft Copilot Chat" or "Azure OpenAI", that's a `link`. If you see "Optum AI Lab" and it's not in the catalog, that's `add_alias` (with the proposed canonical name) OR `agency_internal_system`.

3. **Is it an agency-built system?** Names like "USCIS ELIS", "DHS GenAI Platform", "FEMA Decision Support" — these are NOT commercial products. Use `agency_internal_system`.

4. **Is it noise?** "Various", "N/A", "TBD", `[REDACTED]`, contractor names that aren't AI vendors (e.g., "Aneesh Technologies"), generic categories ("LLM", "AI") — `false_positive`.

5. **When in doubt, `unclear`**. Better to skip a hard call than poison the data.

## Cost budget

- ~200 rows per agent. Most are obvious; spend most time on the 30–50 ambiguous ones.
- Don't web-search unless the vendor is genuinely unfamiliar AND not in the catalog. The 240-product catalog covers ~95% of cases.
- Total agent budget: ~5–8 minutes per slice. Be disciplined.

## Final report

End your run with a brief summary (under 200 words):
- Counts by decision type.
- Top 5 newly-proposed canonical names (for `add_alias`).
- Anything systemic you noticed worth flagging (e.g., "70 rows are all the same DOJ ELIS variant — probably a load-time data quality issue").
