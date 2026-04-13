# Source
`ED-2025-ai-inventory.xlsx` (`use_cases`)

# Counts
- Source context says 77 data rows; SQLite also has 77 `use_cases` rows for this file.
- The workbook itself has 79 physical rows in `All Use Cases`, which is consistent with 1 title row + 1 header row + 77 data rows.

# Findings
- The ingest preserved the row count, but the normalized `use_case_id` column is empty for all 77 loaded rows. The raw source IDs are only retained inside `raw_json`, so the DB does not expose the source's `ED-####` identifiers for downstream joins or audits.
- One clear tag mismatch: `ED-0003` / `CAISY - Artificial Intelligence System Skillsoft Percipio Assessment for the Department Use` is a vendor-purchased Skillsoft product in the sheet (`a) Purchased from a vendor`), but it is tagged as `entry_type=custom_system` with `ai_sophistication=classical_ml` and no product linkage. That combination does not match the source description well enough and should likely be a product/COTS record instead.
- The rest of the ED rows look directionally plausible at a glance: the Microsoft Copilot cluster is consistently tagged as `product_deployment`, and the OpenAI / Google Distributed Cloud generative AI entries mostly line up with their source text.

# Recommended follow-up
- Populate the normalized `use_case_id` field from the source IDs, or document that `raw_json` is the only place they are preserved.
- Recheck the CAISY row against the tagging rules and update its entry type/product linkage if the vendor-purchased interpretation is intentional.
