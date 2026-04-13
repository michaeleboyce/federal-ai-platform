# Source
- `DOT-2025-ai-inventory.csv` (`Department of Transportation`)

# Counts
- Source rows: `70`
- Loaded DB rows: `70`
- Parsed header cleanly: `34` columns, no blank rows, no obvious split/shift errors in the import.

# Findings
- The load is row-complete, and the raw CSV structure looks intact, but several source labels are directionally weak or misleading for tagging.
- `DOT-1000035` (`Predictive Analytics Using Autonomous Track Geometry Measurement System (ATGMS) Data`) is a clear example of a non-LLM predictive ML use case, yet the loaded tag is `ai_sophistication = general_llm`. That is a substantive misread of the source meaning.
- The source contains multiple obvious AI/LLM use cases whose `AI Classification` is set to `Other`, including `DOT-1000052` (`Tech Ops LLM Document Search`), `DOT-1000060` (`Remote Maintenance Monitoring (RMM) Analyzer Copilot`), and `DOT-1000072` (`Case and Document Management Copilot`). The tags recover some of this via `bespoke_application` or `product_deployment` plus `general_llm`, but the source classification itself is not reliable and should not be treated as authoritative without manual normalization.
- The product-linked rows are mostly tagged in the expected direction: `DOT-1000215` (`Google Gemini`) and `DOT-1000216` (`Google NotebookLM`) correctly land as product deployments / general LLM use, and `DOT-1000052` is also linked to `Azure OpenAI`. The remaining issue is that the tags are sometimes more precise than the source field they inherit from.
- One additional mixed case is `DOT-1000007` (`Enterprise "Ask Dottie" ChatBot Capability`): the source describes an enterprise-wide LLM chatbot, but its source classification is `Natural Language Processing (NLP)`. That is understandable as a loose umbrella label, but it blurs a generative/chatbot use case into a non-generative bucket.

# Recommended follow-up
- Normalize the source `AI Classification` labels for obvious ML/LLM rows before relying on them for downstream analysis.
- Correct the tag on `DOT-1000035` so the sophistication bucket reflects predictive ML rather than general LLM.
- Spot-check other `Other` classifications in this file against the free-text descriptions, especially rows whose names include `LLM`, `Copilot`, `ChatBot`, or `Gemini`.
