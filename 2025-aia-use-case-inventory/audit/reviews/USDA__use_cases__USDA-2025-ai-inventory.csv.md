# Source
`USDA-2025-ai-inventory.csv` (`use_cases`)

# Counts
- Source rows: `162`
- Loaded DB rows: `162`
- Untagged rows: `0`
- Row count and record preservation look correct overall; I did not find evidence of dropped or duplicated rows.

# Findings
- The CSV header is parsed cleanly into 32 columns, and the DB row count matches the source row count exactly. The main risk here is not row loss, but label quality on a subset of rows.
- Most tags are directionally reasonable for USDA’s inventory mix, especially for classic ML, computer vision, and general chatbot/LLM entries.
- A small set of rows look mislabeled or at least worth manual review:
  - `USDA-144` (`Recreation site chatbot`) is classified in the source as `Natural Language Processing (NLP)`, but the DB tags it as `ai_sophistication = general_llm` with `architecture_type = custom_trained`. The source text describes a text dataset for estimating recreation use, which reads like NLP/classical analytics rather than a general LLM.
  - `USDA-090` (`IOL Focus Group and Survey Sensemaking`) is also source-classified as `Natural Language Processing (NLP)`, but the DB again tags it as `general_llm` and `inference_only`. That seems too generative for the source description.
  - `USDA-014` (`Ecosystem Management Decision Support System (EMDS)`) has a suspicious product linkage: the DB records `tool_product_name = Esri ArcGIS AI` / `tool_vendor = Esri`, while the source vendor is `Mountain View Business Group Services` and the system name is `Ecosystem Management Decision Support System`. The source does mention ArcGIS and QGIS tools, but the current product label looks broader than the source warrants.
  - `USDA-162` (`Fire Containment Suitability (FireCON)`) is a classic predictive modeling entry in the source, but the DB links it to `Microsoft Teams`. That looks like an incidental collaboration tool rather than the AI system itself.
- A few other rows in the USDA file appear to be tagged as `general_llm` or `agentic` even when the source language is more cautious or non-generative. These may be acceptable if the downstream taxonomy intentionally normalizes chatbot-like uses into those buckets, but the reviewer should treat them as the highest-risk area for over-classification.

# Recommended follow-up
- Spot-check the NLP-labeled USDA rows (`USDA-090`, `USDA-144`, and similar entries) against the source text and confirm whether they should remain `general_llm` or be retagged to `nlp_specific` / `classical_ml`.
- Verify the product linkage logic for rows like `USDA-014` and `USDA-162` so the tag table only attaches a product when the source clearly names one.
- If the current taxonomy is intentionally broad, document that rule in the audit notes so future reviewers do not flag these same rows repeatedly.
