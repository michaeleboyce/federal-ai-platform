# Source
HUD `HUD-2025-ai-inventory-consolidated.xlsx` (`Sheet1`), 20 data rows after the header.

# Counts
- Source row count: 20
- Loaded DB row count: 20
- Parsed row order appears intact: DB ids `479-498` map one-for-one to the 20 source rows.

# Findings
- The load count matches the source exactly, and the row text/sequence is preserved without obvious splitting or dropped rows.
- Most tags are directionally reasonable for a generic-use inventory, but the file is heavily normalized into `generic_use_pattern` / `administrative`, which is fine here.
- One concrete tag mismatch: row `490` (`Generating code using AI.`) is tagged `is_microsoft_copilot=1` even though the source examples only mention `Poolside, GitHub Copilot` and the product column is blank. `is_github_copilot=1` fits; the Microsoft Copilot flag does not.
- A few rows look under-tagged at the capability level. For example, row `483` (`Editing images, videos, or other public affairs materials using AI.`) has no `product_capability`, and row `493` (`Managing or implementing security controls...`) is also left blank even though both clearly map to known operational categories.
- The `classical_ml` label is applied broadly, including several rows that read like modern generative-AI workflows (`485-491`), but the source’s commercial examples are mixed and the labels are not obviously wrong enough to call this a hard error.

# Recommended follow-up
- Drop the `is_microsoft_copilot` flag for row `490`, or confirm there is a source basis outside the spreadsheet.
- Review the blank `product_capability` tags on rows `483`, `493`, `496`, `497`, and `498` to see whether they should be assigned a more specific capability label.
