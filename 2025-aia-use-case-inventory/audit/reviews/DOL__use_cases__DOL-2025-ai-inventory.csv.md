# Source
DOL-2025-ai-inventory.csv (`Department of Labor`)

# Counts
- Source rows: 41
- Loaded DB rows: 41
- Row count match: yes
- Parsed `use_case_id` values in DB: 0 non-empty / 41 blank

# Findings
- The row count matches exactly, so the file was ingested at the right cardinality, but the primary identifier column did not survive parsing. In the source, the first column contains values like `DOL-02`, `DOL-03`, `DOL-19`, etc., while the loaded `use_cases.use_case_id` field is blank for every row. That makes row-level reconciliation much harder and suggests the first column/header mapping was lost during import.
- A few tags look directionally too generic for the source text. `Language Translation` is tagged `general_llm` / `is_generative_ai=1`, but the source describes translation using natural language processing models and gives no clear evidence of an LLM-based implementation. `Automatic Document Processing` is also tagged `general_llm`, even though the source says it is form extraction / processing with Azure Form Recognizer. These read more like NLP or document extraction workloads than general LLM use cases.
- The inverse problem appears in some of the BLS autocoder rows: `OEWS Occupation Autocoder`, `Scanner Data Product Classification`, `QCEW NAICS Autocoder`, and `Computer-Assisted Review: ORS Autocoder` are tagged as classical ML / custom-trained, which matches the source well. That contrast makes the over-broad LLM tagging on the translation/document-processing rows stand out more clearly.

# Recommended follow-up
- Fix the CSV-to-DB mapping so the source `Use Case ID` column populates `use_cases.use_case_id`, then rerun the import or backfill the missing identifiers.
- Recheck the `Language Translation` and `Automatic Document Processing` tag assignments against the source descriptions and downgrade them from `general_llm` if no LLM implementation is actually documented.
- Spot-check a few multiline rows in the raw file against the loaded text to confirm the parser is preserving line breaks and commas without shifting columns.
