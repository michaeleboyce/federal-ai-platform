# Source
`VA-2025-ai-inventory.csv` for Department of Veterans Affairs.

# Counts
- Source file has 367 data rows. The raw CSV also has 2 trailing blank rows, plus the title row and header row.
- Loaded DB row count is 367, so ingestion preserved the source row count.
- Parsing appears structurally sound: the file is a 14-column CSV, and the loaded rows line up with the source row structure.

# Findings
- The row count and basic CSV parsing look correct, but several tags are clearly off relative to the source text.
- `10654` `Lexis+` is tagged as `product_deployment` with `tool_product_name = Microsoft Teams`. The source describes the Lexis+ document analysis tool for legal research, so the product label is wrong.
- `10656` `Forescout: AI Behavioral Anomaly Detection w/ Automated Enforcement` is also tagged with `tool_product_name = Microsoft Teams` and `ai_sophistication = general_llm`, even though the source is a cybersecurity anomaly-detection/enforcement use case that reads like classical ML, not Teams or an LLM deployment.
- `10913` `Customer Sentiment` is tagged to `Custom In-House AI`, but the source says it is an NLP/LLM use case to proactively identify customer-service drops. That may still be custom, but the current product label is only weakly supported and should be rechecked.
- `10926` `Human-Centered Design (HCD) User Feedback Summary, Analysis, and Design` is tagged `agentic` / `agentic_workflow` and `Custom In-House AI`. The source does mention LLMs and custom agents, so the sophistication tag is plausible, but it is a better fit for an internal workflow/tooling use case than a product deployment.
- `10669` `Xtract WDS - OSLE` is tagged `computer_vision` / `inference_only`, which matches the source’s weapon-detection heat-map description more closely than the other outliers.

# Recommended follow-up
- Fix the obvious product-label leakage on `10654` and `10656`; both look like misassigned default product tags rather than source-backed labels.
- Recheck `10913` and `10926` against the tagging rules for when to assign `Custom In-House AI` versus leaving product fields blank.
- Spot-check the remaining VA rows for similar tag drift, especially among enterprise/internal tools where product names can be inherited incorrectly.
