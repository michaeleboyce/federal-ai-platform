## Source
- `NARA-2025-ai-inventory.csv` for National Archives and Records Administration (NARA)
- Raw file contains 1 section/banner row plus 14 actual use-case rows.

## Counts
- Source context reports `row_count = 14`; the SQLite load also has `db_row_count = 14`.
- I confirmed the DB has 14 `use_cases` rows for this file, so the inventory count is aligned.
- The raw CSV parser sees 15 records total because the file starts with a non-data section banner before the actual use-case table. That does not appear to have been loaded as a use case.

## Findings
- The main structural issue is that the normalized `use_cases.use_case_id` column is `NULL` for all 14 loaded rows. The raw file has explicit IDs like `NARA - 0001` through `NARA - 0014`, so the source identifiers are only preserved inside `raw_json`, not as a queryable field.
- Tags are broadly directionally correct, but a few are coarse enough to deserve a second look. `9645` (`Automated Data Discovery and Classification Pilot`) is tagged `general_llm` / `is_general_llm_access=1`, even though the source description reads more like an internal classification pilot than a general chatbot-style access use case.
- `9639` (`Topic Summarizer and Entity Extraction using AI`) is also tagged `general_llm`, but the source text frames it as a summarization/extraction workflow; that may be fine, but it is less clearly an end-user LLM access case than the tag suggests.

## Recommended follow-up
- Populate the structured `use_case_id` field from the source IDs so rows can be joined and audited without parsing `raw_json`.
- Spot-check the rows tagged `general_llm` / `is_general_llm_access=1` against the source narratives to confirm the tag is intended for any workflow using an LLM internally, not only interactive LLM products.
