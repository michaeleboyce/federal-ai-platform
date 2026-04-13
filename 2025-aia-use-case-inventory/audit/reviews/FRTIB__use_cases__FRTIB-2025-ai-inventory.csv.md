# Source
- `FRTIB-2025-ai-inventory.csv` (Federal Retirement Thrift Investment Board)
- Raw file row count: 6
- Loaded DB row count: 6

# Counts
- The source and DB row counts match exactly.
- The CSV header parsed cleanly, including the long questionnaire fields and the UTF-8 apostrophe/dash variants.

# Findings
- The loader appears to have dropped the source use-case IDs. The CSV has explicit IDs `FRTIB-001` through `FRTIB-006`, but the loaded `use_cases.use_case_id` values are blank for all 6 rows. The rows were instead assigned internal IDs `9093` to `9098` and slugs like `frtib-ava-0`.
- The row meanings otherwise look preserved: the six names, vendors, classifications, and operational dates in the DB match the raw CSV, and the vendor-purchased / COTS framing is consistent across the file.
- The tags look directionally correct overall. `Microsoft CoPilot` and `Adobe Firefly` are tagged as `product_deployment` with matching product/vendor labels, while the other four rows are tagged as `custom_system`, which fits the source’s use-case framing even though the underlying vendor is still listed.

# Recommended follow-up
- Populate `use_cases.use_case_id` from the source `Use Case ID` column for this file so the original agency identifiers are preserved alongside the internal DB IDs.
- If the ingest pipeline is expected to retain source IDs everywhere, spot-check whether other 2025 agency CSVs have the same blank `use_case_id` pattern.
