# Source
`SEC-2025-ai-inventory.csv` for the SEC (`use_cases` table).

# Counts
- Source rows: 60
- Loaded DB rows: 60
- Parsed row count matches the source, so there is no row-loss issue.

# Findings
- The structured `use_case_id` column is empty for all 60 loaded rows, even though the CSV contains IDs such as `SEC-1`, `SEC-19`, and `SEC-68`. The original identifiers are only preserved inside `raw_json`, which makes the normalized table harder to trace back to the source.
- The row-level tags are mostly directionally correct. Examples that line up well include `SEC-6` / `Training Conversation Tool` as `product_deployment` with `SkillSoft`, `SEC-64` / `Natural language search on images through FlashPoint` as `product_deployment` with `computer_vision`, and `SEC-67` / `Tracing digital asset transactions...` as a vendor-backed deployed product.
- Coverage is uneven in the derived tags, especially `deployment_environment` (`unknown` for all 60 rows) and `product_capability` (blank for all rows). That is not necessarily wrong, but it means the tag layer is fairly thin compared with the source detail.

# Recommended follow-up
- Preserve the SEC source identifier in the structured `use_case_id` field on reload or backfill it from `raw_json` so joins and audits can reference the original SEC numbering directly.
- If the downstream workflow expects richer normalization, consider whether `deployment_environment` and `product_capability` can be populated for at least the vendor-backed or clearly scoped rows.
