# Source
- `DOJ-2025-ai-inventory.xlsx` (`use_cases`, DOJ)
- Raw sheet: `Reportable AI Use Cases`
- Audit scope reviewed against `data/federal_ai_inventory_2025.db` and the source context JSON for DOJ.

# Counts
- Source rows: 314
- Loaded DB rows: 314
- Tagged DB rows: 314
- Untagged rows: 0
- Parsing looks structurally complete: the source workbook has 314 populated reportable rows, and the DB row count matches.

# Findings
- The main parsing/count path is correct, but there are clear tag-quality issues in a small set of rows where the source meaning is not preserved.
- `8454` (`Unmanned Aerial Systems (UAS)`) is tagged `ai_sophistication=general_llm`, but the source record’s AI classification is `Computer Vision`. That tag is directionally wrong and should not be treated as an LLM use case.
- `8484` (`Thomson Reuters Vigilant Vehicle Manager`) is also tagged `ai_sophistication=general_llm`, while the source describes the use case as `Computer Vision`. Same issue: the tag overstates the model type.
- `8487` / `8488` / `8489` (`R`, `Stata`, `Matlab`) are tagged `ai_sophistication=classical_ml`, which is plausible, but the source classification is `Generative AI` in the DB payload. That combination looks internally inconsistent and should be rechecked against the raw workbook because the loaded labels are mixing legacy analytics tools with a generative-AI source classification.
- Broader tag distribution is otherwise plausible for DOJ: most entries are `custom_system`, with a smaller `product_deployment` slice and a few `bespoke_application` rows. The strongest concern is not row loss, but incorrect sophistication labeling on representative rows.

# Recommended follow-up
- Recheck the tagger/mapping rules for product and legacy-analytics entries, especially where the source AI classification is computer vision or generic analytics rather than LLM-based.
- Spot-audit the remaining `general_llm` rows that are not obviously chatbot/copilot-style tools to confirm they are not over-tagged.
- If the tagger is using the DB `ai_classification` field as a proxy, add a normalization rule so computer-vision and classic predictive rows do not drift into `general_llm`.
