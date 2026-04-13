# Source
`DOL-2025-ai-inventory-consolidated.csv` / Department of Labor

# Counts
- Source rows: 14
- Loaded DB rows: 14
- Tagged rows: 14
- Untagged rows: 0

# Findings
- Row count matches exactly, and the raw CSV parses cleanly as a 2-column file with headers `Commercial Examples` and `AI Use Case`.
- The loaded rows preserve the source meaning overall. The use-case text and commercial example pairs line up with the raw file, including the long final row about augmented reality training and the acquisition policy Q&A row.
- Most tags are directionally reasonable, especially the obvious writing, coding, search, scheduling, and help-desk cases. `template_id` mappings also look broadly consistent for those standard OMB patterns.
- A few tags look weak or incomplete:
  - `id 407` (`Scheduling and managing social media posts using AI.`) has `product_capability = NULL` even though it is a scheduling workflow analogous to `id 405` and `id 414`.
  - `id 413` (`Managing or implementing security controls for information systems (e.g., cybersecurity) using AI.`) is tagged as `classical_ml` with `architecture_type = inference_only`, but the source is a general AI/security-controls use case and the specific product mapping is only partial (`Microsoft Defender` is captured, `Crowdstrike Falcon` is not).
  - `id 418` (`Answering federal regulatory and agency policy questions related to acquisition using a generative AI tool.`) is tagged `general_llm`, but `tool_product_name`/`cots_product_name` are blank, so the row is less specific than the source suggests.
  - `id 417` (`Using AI-enabled augmented reality to train inspectors...`) is left with no template or product-capability mapping even though the use case is clearly a training/inspection workflow; that is probably acceptable as a custom row, but it is still a sparse classification.

# Recommended follow-up
- No reparse is needed. The main follow-up is to review the sparse or partial tag mappings for rows 407, 413, 417, and 418 and decide whether they should be normalized to the nearest standard capability or left intentionally broad.
