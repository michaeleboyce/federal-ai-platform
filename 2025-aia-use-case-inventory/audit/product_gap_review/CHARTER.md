# Product-gap review charter

You are one of three parallel agents reviewing potential undercoverage in
the use_case_products linking. The audit script
`scripts/audit_undercovered_products.py` found products WITH some links
where free-text searching their canonical name + aliases turns up
ADDITIONAL use cases that aren't currently linked. Your job: judge each
gap and recommend a fix.

## Inputs you have

- `audit/undercovered_products_audit.csv` — the full audit (27 products,
  217 gap rows). Filter to your slice's products.
- `data/federal_ai_inventory_2025.db` (read-only) — query
  `use_cases` for the actual narrative text per gap row, plus the
  `product_aliases` table to see what's currently registered.
- `data/expanded_product_catalog.csv` — the canonical product catalog
  with current alias lists per product.

## Decision rubric per gap row

For each gap (a use case appearing in free-text but not in
`use_case_products`), categorize it as:

| Decision | Meaning |
|---|---|
| `link` | Real product use; should be added to `use_case_products`. Provide use_case_id. |
| `add_alias` | The matching text reveals a new alias that's missing from the product catalog. Provide the alias and (optionally) the use_case_ids that would link via it. |
| `false_positive` | Substring/word-boundary noise; the use case mentions the product name in passing or coincidentally (e.g., "Microsoft Teams" appearing in a transcription pipeline that ISN'T deploying Teams as the AI). Don't link. |
| `tighten_alias` | The product's existing alias is too greedy and producing many false positives. Recommend a more specific replacement (e.g., require co-occurrence with vendor name). |
| `unclear` | Can't tell from the narrative. Flag for human review. |

## Decision principles

1. **Read the use case's actual narrative** before deciding. The audit row
   gives you `sample_gap_uc_ids`; pull the full text from the DB:
   ```sql
   SELECT u.id, a.abbreviation, u.use_case_name, u.system_name, u.vendor_name,
          u.problem_statement, u.expected_benefits, u.system_outputs
     FROM use_cases u JOIN agencies a ON a.id = u.agency_id
    WHERE u.id IN (...);
   ```
2. **A real link requires the product to be the AI tool the use case
   deploys**, not just a passing reference. "We use Microsoft Teams to
   notify users when our model finishes" is NOT a Teams link; "We
   deployed Microsoft 365 Copilot's Teams integration to summarize
   meetings" IS.
3. **An alias is risky if it's a common phrase**. "GPT" alone matches too
   much; "ChatGPT" or "OpenAI GPT-4" is safer. Never add aliases shorter
   than 4 characters or that are common English words.
4. **Vendor co-occurrence is a strong signal**. If the gap text mentions
   "NEC" alongside the alias, it's much more likely a real NEC product
   deployment than a coincidental mention.

## Output schema

Write `recommendations.json` to your output directory as a JSON array.
Per gap row:

```json
{
  "product_id": 1432,
  "canonical_name": "NEC NeoFace",
  "use_case_id": 12345,
  "use_case_agency": "DHS",
  "decision": "link | add_alias | false_positive | tighten_alias | unclear",
  "evidence_quote": "...short verbatim phrase that justifies the decision...",
  "proposed_alias": "...if decision is add_alias...",
  "proposed_alias_replacement": "...if decision is tighten_alias...",
  "notes": "..."
}
```

Also write `notes.md` with a short summary: count of decisions per type,
patterns you saw, products that need catalog-level rework, anything you
flagged as unclear.

## File-ownership boundaries

Each agent owns its own subdirectory under `audit/product_gap_review/`.
Do NOT modify the DB, the catalog, or any other agent's output. Don't
modify dashboard code or python ETL. Output JSON + notes only;
integration applies the changes.

## Final-summary contract

Final reply ≤300 words: count of `link` / `add_alias` / `false_positive`
/ `tighten_alias` / `unclear` decisions, the most surprising findings,
and any products that should be globally re-engineered (e.g., "NEC
NeoFace's alias coverage needs rebuilding from scratch").

Time budget per agent: 45–75 minutes.
