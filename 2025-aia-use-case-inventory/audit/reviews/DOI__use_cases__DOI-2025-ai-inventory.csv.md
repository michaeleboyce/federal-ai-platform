# Source
- File: `DOI-2025-ai-inventory.csv`
- Agency: `DOI` / Department of the Interior
- Raw file encoding: `latin-1`

# Counts
- Raw CSV has `249` physical rows, but the first row is a section banner and the second row is the header, leaving `246` data rows.
- Loaded SQLite rows match the source count exactly: `246` `use_cases` rows for this file.
- The loader appears to have skipped the non-data banner/header rows correctly.

# Findings
- The `Use Case ID` field was not preserved in the database. All `246` loaded DOI rows have a blank `use_case_id`, even though the raw CSV contains IDs such as `DOI-0270`, `DOI-0010`, and `DOI-0001`.
- Tagging is directionally good on many rows, but there are clear mismatches on some vendor/product cases.
- Example: `DOI-0002` / `Non-Generative AI use for Trust Information Analysis and Reporting Tool` is described in the source as `Computer Vision` and purchased from `Microsoft Azure`, but the loaded tag row marks it as `custom_system` with `ai_sophistication = general_llm` and `is_generative_ai = 1`. That is not consistent with the source.
- Example: vendor-backed rows are often not labeled as product deployments. Among DOI rows with `development_type = Purchased from a vendor`, only `4` are tagged `product_deployment`, while `11` are tagged `custom_system`. That split looks too aggressive toward custom-built labeling for a source with multiple clear vendor products.
- Example: `DOI-0001` / `Integration of AI, specifically CoPilot for GitHub...` is tagged more plausibly as `product_deployment` / `coding_assistant`, but it also shows the overall labeling approach is selective rather than consistently driven by the source's development-type field.

# Recommended follow-up
- Restore `use_case_id` from the source CSV during load, since it is present and useful for traceability.
- Recheck the product/custom split for DOI vendor rows, especially cases where the source explicitly names a commercial product or vendor.
- Spot-audit other rows with `ai_classification = Computer Vision` or `Purchased from a vendor` to confirm the `general_llm`/`custom_system` pattern is not broader than the examples above.
