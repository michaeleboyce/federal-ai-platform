# Source
NLRB `NLRB-2025-ai-inventory.csv`

# Counts
- Source rows: 7
- Loaded DB rows: 7
- Parsed rows missing from DB: 0
- DB rows missing required fields: 0
- Tagged rows: 7

# Findings
- Row count and parsing look correct. The CSV has 7 non-empty data rows, and the database loaded all 7 with no blank rows or dropped records.
- The main issue is normalization of the `commercial_product` field. Rows 499-501 list `CoPilot, Westlaw`, but the DB collapses all three to `Microsoft 365 Copilot` only. That is directionally plausible for the Copilot portion, but it drops the Westlaw signal from the source and makes the loaded product attribution incomplete.
- Row 505 is also mixed-source in the CSV (`CoPilot, ServiceNow`) and was normalized to `ServiceNow Now Assist`. That is likely the right dominant product, but the source wording still suggests a dual-product usage pattern that should be preserved somewhere in the record or tags.
- The tags are broadly directionally correct for the file: most rows are generic enterprise LLM / administrative use, the coding row is tagged as `coding_assistant`, and the help desk row is tagged as `it_operations`. The product/capability tags still look a bit over-generalized for the Westlaw rows, which read more like legal drafting/summarization use cases than plain Microsoft 365 Copilot usage.
- No header or schema parsing problems are visible in the raw CSV.

# Recommended follow-up
- Preserve mixed product names explicitly when the source lists multiple tools, especially for `CoPilot, Westlaw` and `CoPilot, ServiceNow`.
- Review whether the three Westlaw-linked rows should carry a Westlaw-related product tag or secondary label instead of being normalized entirely to Microsoft 365 Copilot.
