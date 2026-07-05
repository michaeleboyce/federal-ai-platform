# Product capability labeling — product_capability_2026_07

## Purpose

Label every canonical inventory product that has at least one use-case edge
with the AI **capability categories** it provides. These labels back the
sleeping-services board's "nothing similar deployed" test: when agency X
holds an ATO with (say) a translation service in scope and reports no
product labeled `translation`, the board can honestly claim a capability
void rather than merely a missing name.

## Input / output

Input: `input_batch<N>.csv` — one row per product:
`canonical_name, vendor, product_type, is_generative_ai_hint,
is_frontier_llm_hint, parent_product, description, edge_count,
agency_count, sample_use_snippets`

Output: `labels_batch<N>.csv` — one row per product:
`canonical_name, categories, gen_ai, confidence, reasoning`

- `canonical_name` — copied EXACTLY from the input (it is the join key).
- `categories` — pipe-delimited, 1..N values from the closed vocabulary
  below, **or exactly `none`**. Never mix `none` with a category.
- `gen_ai` — `1` if the product produces novel text/image/code/audio via
  generative models, or is a gen-AI platform/assistant; else `0`.
- `confidence` — `high` | `medium` | `low`.
- `reasoning` — one sentence; required.

## Closed vocabulary (11 categories + none)

| Category | Definition | Boundary rules |
|---|---|---|
| `genai_platform` | Hosts, serves, or fine-tunes generative models, or is a general-purpose LLM chat/API surface (Azure OpenAI, Bedrock, Claude, Gemini, Ask Sage, h2oGPTe, AI Foundry). | The model/platform itself, not a product that merely embeds one → that's `assistant`. |
| `assistant` | An AI copilot/agent embedded in a workflow product (M365 Copilot, Amazon Q, Salesforce Einstein/Agentforce, GitHub Copilot, Databricks Assistant). | If the product's core is the assistant experience, label it here even though a genai_platform powers it. |
| `ml_lowcode` | Low/no-code ML builders for business users (Microsoft AI Builder, Power Platform AI features). | Full data-science platforms → `ml_platform`. |
| `ml_platform` | Train/deploy/manage ML models; data-science platforms (SageMaker, Vertex AI, Azure ML, Databricks, Dataiku, H2O, MLflow, Palantir AIP/Foundry, C3 AI). | |
| `doc_processing` | OCR / intelligent document processing / forms extraction (Textract, Azure Document Intelligence, Hyperscience, ABBYY, Kofax/Tungsten). | Document *search* → `search`; document *generation* → gen_ai flag on whatever category fits. |
| `speech` | Speech-to-text, text-to-speech, voice analytics (Transcribe, Azure Speech, Polly, Dragon/Nuance, Whisper). | |
| `translation` | Machine translation between human languages (Amazon/Azure/Google Translate, Systran, Lilt). | |
| `vision` | Image/video analysis: object detection, recognition, classification, biometrics (Rekognition, Cloud Vision, facial recognition, medical imaging AI). | |
| `nlp` | Text analytics short of generation: entity extraction, sentiment, classification, summarization-as-analysis (Comprehend, Azure Text Analytics). | If it's a chat surface → `genai_platform`/`assistant`. |
| `search` | AI-powered enterprise/semantic search and retrieval (Kendra, Vertex AI Search, Elastic w/ ML). | |
| `chatbot` | Conversational front-ends / virtual agents / contact-center bots (Lex, Dialogflow, Kore.ai, bot frameworks). | A general LLM chat UI is `genai_platform`, not `chatbot`; `chatbot` is the task-specific dialog-flow product class. |
| `none` | Real product, but none of the above capabilities (RPA-only, GIS, cybersecurity analytics without the above, plain BI dashboards, robotics hardware). | Prefer a category when the product genuinely provides one; `none` is not a dumping ground for "hard to say" — use `low` confidence instead. |

## Multi-label guidance

Label ALL categories the product genuinely provides, not just the primary
one. Databricks = `ml_platform|assistant` (platform + Assistant). Gemini =
`genai_platform|assistant`. A document-AI suite with OCR + translation =
`doc_processing|translation`. Do NOT cascade implied capabilities: an LLM
platform can translate, but only label `translation` when translation is a
productized capability the agency would buy it for.

## Worked hard cases

- **Microsoft 365 Copilot** → `assistant`, gen_ai=1. (Embedded copilot; not
  the platform.)
- **Palantir AIP** → `ml_platform|genai_platform`, gen_ai=1. (Ops platform
  with first-class LLM orchestration.) Palantir Foundry alone →
  `ml_platform`, gen_ai=0.
- **Databricks** → `ml_platform|assistant`, gen_ai=1 (Assistant/Genie).
- **CrowdStrike Falcon** → `none`, gen_ai=0 unless the specific product IS
  Charlotte AI (then `assistant`, gen_ai=1). Security analytics ML alone
  does not qualify for a category.
- **Apple Face ID** → `vision`, gen_ai=0. (On-device biometric — still the
  vision capability class.)
- **Custom agency systems** (e.g. "USCIS Text Analytics") → label by the
  capability the name/snippets describe: `nlp`. Being custom-built does not
  exclude a product.
- **ChatGPT / Claude / Gemini consumer or API** → `genai_platform`, gen_ai=1.

## Hints discipline

`is_generative_ai_hint` / `is_frontier_llm_hint` come from an earlier ETL
pass — treat them as weak priors, not answers. If the hint conflicts with
what the name/description/snippets tell you, follow your judgment and say
so in `reasoning`.

## Confidence

- `high` — recognizable commercial product or unambiguous description.
- `medium` — inferred from name + snippets with reasonable certainty.
- `low` — genuinely ambiguous; the QC pass reviews 100% of these.
