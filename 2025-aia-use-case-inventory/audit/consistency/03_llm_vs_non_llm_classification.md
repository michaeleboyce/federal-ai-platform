# Check
`llm_vs_non_llm_classification`

# Method
Joined `use_cases` to `use_case_tags` and reviewed rows where any of `is_generative_ai`, `is_general_llm_access`, or `ai_sophistication = 'general_llm'` is set. I then checked whether the source `ai_classification` and source narrative looked like a non-LLM workflow, with emphasis on classical/predictive ML, NLP text analytics, search/retrieval, and computer-vision use cases.

# Findings
- The flagging is not random, but it is too broad for non-LLM workflows. In `use_cases`, 1,434 rows carry at least one LLM-related flag, and a strict text pass found 143 rows where the LLM flags look inconsistent with the source classification and wording.
- The strongest false-positive cluster is classical/predictive ML: 63 suspicious rows. These are mostly scoring, classification, anomaly detection, maintenance, or forecasting workflows, not generative systems.
- NLP rows also show over-tagging: 50 suspicious rows. Many descriptions read like text analytics, extraction, routing, or sentiment analysis rather than generation.
- Computer-vision rows contribute another 30 suspicious rows. Several are facial recognition, object detection, image classification, or video analytics items that do not read as LLM use cases.
- Search/lookup rows are mixed. A separate slice produced 66 rows with LLM flags and search/lookup/retrieval wording but no explicit generative/LLM language; some are legitimate semantic-search assistants, but others look like ordinary retrieval tooling.
- The consolidated inventory is materially cleaner. It has 96 LLM-flagged rows, and most of those map to obvious products such as Copilot, ChatGPT, Claude, Gemini, or Azure/OpenAI. I did not see the same concentration of false positives there.

# Examples
- `7433` `API Security Vulnerability Technology` - `Classical/Predictive Machine Learning`; `general_llm`; narrative: “Discover, ingest, and analyze APIs to create and run thousands of custom attack scenarios...” This reads like security analytics, not an LLM workflow.
- `7963` `ServiceNow Predictive Intelligence` - `Classical/Predictive Machine Learning`; `general_llm`; narrative: “Reduce error rate of categorization of incidents in ServiceNow.” This is incident classification, not generative AI.
- `8014` `ServiceNow Classification Prediction` - `Classical/Predictive Machine Learning`; `general_llm`; narrative: “Inconsistencies in classification values determined by human technicians.” Again, predictive classification rather than LLM use.
- `8532` `LexisNexis (AI assisted legal research)` - `Classical/Predictive Machine Learning`; `general_llm`; narrative: “Addresses manual process of conducting legal research.” This looks like research/retrieval support, not a generative system.
- `9154` `ServiceNow Generic Ticket Classification` - `Classical/Predictive Machine Learning`; `general_llm`; narrative: “Used to automatically route generic tickets to the correct group.” This is ticket routing/classification.
- `9397` `Renamed: FAR-based Facility Signal Detection Tool` - `Natural Language Processing (NLP)`; `general_llm`; narrative: “Need for proactive detection of quality signals in post-market surveillance reports using statistical process control and topic modeling...” Topic modeling is not the same as a general LLM use case.
- `10913` `Customer Sentiment` - `Natural Language Processing: AI that processes, interprets, and shares information in human language.`; `general_llm`; narrative: “Proactively identify drops in customer service as perceived by the customer.” This is sentiment analysis, not obviously generative AI.
- `7419` `Anomaly Detection COV Structure` - `Computer Vision`; `general_llm`; narrative: “The Anomaly Detection Algorithm (ADA) models are intended to solve...” This is computer-vision anomaly detection, not LLM.
- `7535` `I-765 - USCIS Facial Recognition through IDENT (1:1 Face Recognition/Validation)` - `Computer Vision`; `general_llm`; narrative: “Using the Automated Biometric Identification System (IDENT) makes this process nearly instant...” Biometric matching is not an LLM use case.
- `7544` `Customs Broker License Exam - Proctor Support` - `Computer Vision`; `general_llm`; narrative: “Detect potential cheating during the Customs Broker License Exam.” This is proctoring/vision monitoring.
- `7807` `SWFSC Publications Search` - `general_llm`; no explicit generative language in the source text. This reads like publications search rather than an LLM use case.
- `7853` `TM Word and Image Search Tool (TWIST)` - `general_llm`; narrative: “Provide the capability for external customers to perform clearance searches prior to filing...” This is search/retrieval tooling, not obviously generative AI.

# Recommended follow-up
- Re-tag the clear classical/predictive and computer-vision false positives first; those are the least ambiguous.
- For NLP rows, separate text analytics/search/routing from actual generative and chat-based systems before carrying forward `general_llm` or `is_generative_ai`.
- Review the LLM flag derivation logic against source `ai_classification` values such as `Classical/Predictive Machine Learning`, `Natural Language Processing`, and `Computer Vision` so that generic analytics and perception workflows do not inherit LLM labels by default.
