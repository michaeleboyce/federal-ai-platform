# Source
`DOE-2025-ai-inventory.xlsx` (`use_cases`, Department of Energy)

# Counts
- Source row count in the context JSON: `340`
- Loaded DB row count: `340`
- Tagged DB rows: `340`
- Workbook structure is consistent with the ingest target: one section header row, one column-header row, then `340` data rows.

# Findings
- The row count matches, but the primary source identifier was not preserved. Every DOE row in `use_cases` has `use_case_id = NULL` even though the workbook’s first column contains values like `DOE-10`, `DOE-118`, and `DOE-347`. That makes the loaded rows harder to trace back to the source and suggests the ID column was dropped during parsing rather than mapped.
- The row text itself is largely preserved, including long descriptions and line breaks, so the parse appears to have captured the substantive content. One exception to watch is the first-column loss above, since that is the stable source key for audits and cross-checks.
- Tags are directionally mixed but mostly plausible for the DOE file. Product deployments are tagged as such for clear cases like `ServiceNow Predictive Intelligence` and `Microsoft 365 Copilot`, with `tool_product_name`/`tool_vendor` populated.
- Some vendor-backed rows still land in `custom_system` with no product-capability detail, which is a weak spot in the tagging. For example, `Network Security and Analysis` has vendor `Vectra` and `Purchased from a vendor` in the source, but the loaded tags still mark it as `custom_system` with blank `product_capability`. Similar patterns show up for `Adaptive Cyber-Physical Resilience for Building Control Systems` (`PassiveLogic`) and `APT Analytics` (`Microsoft`). That may be defensible for custom deployments, but the tags do not clearly explain the distinction.
- The tag set is very coarse for this source: `product_capability` is blank for all 340 rows and `architecture_type` is `unknown` for 211 rows. That is not necessarily a parsing error, but it limits the value of the labels and makes the tagging feel under-resolved for a DOE inventory with a lot of mixed vendor/custom use cases.

# Recommended follow-up
- Restore or map the workbook’s `Use Case ID` column into `use_case_id` so each row can be traced back to the source.
- Spot-check the vendor-backed rows tagged `custom_system` to confirm whether the labeling logic is intentionally distinguishing custom deployments from product deployments, or whether some should be relabeled.
- If the tagging pipeline supports it, populate `product_capability` or a comparable field for the obvious product cases so the DOE file is less dominated by blank or `unknown` labels.
