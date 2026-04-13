# Source
`PBGC-2025-ai-inventory.csv` (`consolidated_use_cases`)

# Counts
- Source row count: `20` non-empty rows in the raw CSV, plus `21` blank trailing rows.
- DB row count: `20`.
- Parsing looks intact overall: the wrapped source text in row 539 stayed as one record, and the source/DB counts match.

# Findings
- The loaded rows mostly preserve the source meaning, and the high-level tags are directionally reasonable for a PBGC inventory that is dominated by administrative productivity use cases.
- The strongest mismatch is row `540` (`Managing or implementing security controls for information systems...`). The source lists `Zscaler` as the commercial product, but the loaded tag record points `tool_product_name` to `Microsoft Defender` and `tool_vendor` to `Microsoft`, so the product/vendor normalization is wrong for this row.
- There are a few softer but still notable product-label inconsistencies where the source names one Microsoft product and the tags normalize to a broader variant: row `528` has `Microsoft Teams Premium (with intelligent meeting recap)` in the source but `Microsoft Teams` in tags, and rows `532`, `534`, and `536` use `Microsoft Copilot` in the source but the tags normalize to `Microsoft 365 Copilot`. Those may be intentional aliasing, but they should be checked for consistency.
- Row `543` (`Planning travel routes using AI-driven map applications.`) is borderline as an AI inventory entry: the source product is `Native map applications on mobile devices`, the tag fields are mostly blank, and the row is labeled `classical_ml` with `inference_only`/`enterprise_wide` despite the source not naming a distinct AI product. This looks more like a weakly substantiated generic use pattern than a clear AI implementation.
- A few rows with blank commercial-product fields also remain broadly plausible, but the tagging is very generic (`classical_ml`, `enterprise_wide`, `inference_only`) and does not add much confidence beyond the source text itself.

# Recommended follow-up
- Verify row `540` against the source and remap the commercial product/vendor to `Zscaler` instead of `Microsoft Defender`.
- Spot-check the Microsoft rows (`528`, `532`, `534`, `536`) to confirm whether the canonical product label should stay normalized or match the source string more literally.
- Review whether row `543` should remain in the AI inventory at all, since the source evidence for an AI-specific product is thin.
