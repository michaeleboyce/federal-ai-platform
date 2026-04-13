# Source
- `SBA-2025-ai-inventory.xlsx` (`audit/source_contexts/SBA__use_cases__SBA-2025-ai-inventory.xlsx.json`)
- Source sheet: `All Use Cases`
- Workbook data rows: 34
- Loaded DB rows for this source: 34

# Counts
- Row count matches exactly: 34 source rows and 34 `use_cases` rows.
- No blank source rows were reported in the source context, and the workbook’s `All Use Cases` sheet has a clean 34-row data region.
- The DB also has 34 matching `use_case_tags` rows for this source.

# Findings
- Parsing looks structurally sound. The loaded rows preserve the source record count, and the row-level content appears to come through without obvious truncation or column shifts.
- Tagging is mostly directionally plausible, but there are some clear outliers where the DB tags do not match the source wording:
- `SBA-10 / Customer Response` is source-described as use of Perplexity to evaluate customer responses, but the tag set marks it as `entry_type=product_deployment` with `tool_product_name=Custom In-House AI` and `tool_vendor=In-House`. That is inconsistent with the workbook, which names a vendor product (`https://www.perplexity.ai/`) and describes a purchased tool.
- `SBA-24 / Secure IL5 AI` is source-described as the `Ask Sage Platform` from `Ask Sage, Inc.`, but the tag set marks `tool_product_name=Microsoft Teams` and `tool_vendor=Microsoft`. That looks like a cross-wired product label.
- `SBA-22 / General AI Use Case across the SBA for web and desktop` is a Perplexity vendor deployment, but it is tagged `entry_type=custom_system` with no product/vendor labels. The source text points to a commercial vendor product, so this should not read as a custom build.
- `SBA-23 / Email, Document, and Composing AI Editor` is a Grammarly deployment, but it is tagged `ai_sophistication=classical_ml` rather than a generative AI-style assistant. That may be arguable on implementation details, but the source description and outputs read more like an AI writing assistant than a plain classical ML classifier.
- The workbook also contains a few source-side oddities/typos that were preserved in the DB, such as `Tralking Point Generation` in the system name for `SBA-11`, which suggests the loader is copying text faithfully rather than normalizing it.

# Recommended follow-up
- Recheck the source-to-tag mapping for the Perplexity, Ask Sage, and Grammarly rows above.
- Confirm whether `Customer Response` and `General AI Use Case across the SBA for web and desktop` should be reclassified from custom-system-style tags to vendor product deployments.
- If the tagging rules intend to classify based on the agency’s use pattern rather than the named product, document that convention explicitly; otherwise these rows should be corrected to match the workbook text.
