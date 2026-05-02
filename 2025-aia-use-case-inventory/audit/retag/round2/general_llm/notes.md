# Round-2 General LLM Access Review — Notes

## Methodology

- Filtered `audit/retag/general_llm/by_row.csv` to rows where `current_is_general_llm_access != corrected_is_general_llm_access` AND `confidence == low`. This produced 274 rows (the prompt said ~270; the actual count is 274).
- Direction of flips: 273 were downgrades (1 → 0) driven by name-substring heuristics, and 1 was an upgrade (0 → 1) for `DOC Chat`.
- For each row, pulled the full narrative (`problem_statement`, `expected_benefits`, `system_outputs`, `system_name`, `vendor_name`, `ai_classification`) from the SQLite DB and read it directly. Made decisions based on the rule:
  - `is_general_llm_access = 1` only if the system is a broadly-available general-purpose chat / drafting / summarization assistant where staff can ask arbitrary text questions.
  - `0` for narrow workflow tools, classifiers, perception models, search-with-no-chat, single-knowledge-base RAG chatbots, and dedicated coding assistants.
- Web search used only for one genuinely ambiguous row (`DOC Chat` at id=7847), where the inventory entry was empty; the public DOC AI inventory landing page confirmed the existence of an enterprise AI inventory but did not surface a specific "DOC Chat" product page. I overturned to 1 with medium confidence based on the explicit `scope=department` plus the name itself.

## Tally

- Confirms: 261 / 274 (95%)
- Overturns: 13 / 274 (5%)
- Web searches attempted: 1

## Overturns (rows where I disagree with the prior agent and assert `is_general_llm_access = 1`)

| id | Agency | Name | Why |
|---|---|---|---|
| 7628 | DHS | Commercial Generative AI for Text Generation (AI Chatbot) | Name itself is the definition of a general-purpose enterprise chatbot; row is at `enterprise_wide` scope. The prior agent downgraded purely off the substring "commercial generative ai for text" — completely wrong. |
| 7847 | DOC | DOC Chat | Department-scoped DOC chat platform. (One web search.) |
| 7982 | DOE | Merlin - KCNSC Generative AI with RAG | Narrative explicitly: "general productivity enhancer" using vLLM + GPT-OSS-120b + OpenWebUI front end. That's a general-purpose chat front end. |
| 8608 | DOJ | Internal Component-specific chatbot service | Narrative explicitly: "human-like conversational responses to conduct general information queries and suggestions towards improving text" — that's general LLM access, just hosted in GCCH instead of the public ChatGPT. |
| 8718 | DOJ | Chatbot | Stated purpose: "General AI assistance"; multimodal output. FBI internal general LLM. |
| 9247 | HHS | CDC Chatbot | Narrative explicitly: "general purpose assistant for CDC staff powered by Large Language Models. Staff can upload documents, summarize information, extract information, create content, develop software code, or general tasks". |
| 9566 | HHS | LibreChat | Narrative: "alternative to using publicly available chat services" with image+chat capabilities — general LLM access for NHGRI staff. |
| 10122 | SBA | Chatbots for internal research | Lists Claude / ChatGPT for general research. |
| 10124 | SBA | Generative AI for SBA.gov product training | ChatGPT used as general training assistant. |
| 10125 | SBA | AI for Small Business Development w/Copilot, Gemini or ChatGPT | Explicit Copilot/Gemini/ChatGPT for SBA district-office staff. |
| 10126 | SBA | ChatGPT for OMS Marketing | Direct ChatGPT use for general marketing copy. |
| 10127 | SBA | Gemini AI for Strategic Planning | Direct Gemini use for general planning. |
| 10176 | SEC | Using AI Large Language Model chat for general tasks/questions | Name itself; "general usage" stated. |
| 10993 | VA | VA Chat Copilot Meta Pilot | Empty record but name strongly implies a meta/umbrella copilot pilot. Low confidence overturn. |

## Heuristic patterns that the prior agent got systematically wrong

1. **`screening` substring is too aggressive.** The prior agent downgraded "Synthetic data for improved Automated Threat Recognition (ATR) in checkpoint screening" — actually correct (it's an image-recognition perception model), so my confirm stands. But in general "screening" appears in benign LLM tools too. The heuristic happened not to misfire often here.
2. **`code assistant` / `code conversion` / `codegen` substrings**: These were correctly downgraded. Code assistants are *not* `is_general_llm_access` per the rule (they're a separate "code" category). All confirmed.
3. **`detection` substring**: Always downgraded. Correctly so — every "detection" row I saw was a classifier or perception model.
4. **`legal research` substring**: Always downgraded. Correctly so — Westlaw/Lexis Plus/Bloomberg legal-research GenAI tools are domain-specific, *not* general-purpose chat.
5. **`transcription` / `translation` / `data extraction`**: Always downgraded; correct. All cases were narrow document/audio pipelines.
6. **`chatbot` and `assistant` substrings (where the heuristic *did not* downgrade)**: These pulled in many narrow knowledge-base chatbots that should also be 0 — the prior agent already correctly handled those by leaving them as 0 from the keyword pass earlier.
7. **The major systematic miss**: rows whose names contain `commercial generative ai`, `chatbot`, `chat`, `general LLM`, `librechat`, `copilot meta`, or where the narrative explicitly says **"general purpose"** or **"general tasks"** — these were sometimes downgraded by the *parent* heuristic just because of an unrelated substring (e.g., `name contains "data dictionary"`). The upstream pipeline did not respect explicit "general-purpose" language in the narrative. Several of the SBA overturns above are pure ChatGPT/Copilot/Gemini deployments at the office level.
8. **The `enterprise_wide` scope tag is a strong signal** that I trust more than the name heuristic: when scope=enterprise_wide AND the narrative mentions general / multi-task / arbitrary / chat / Copilot / ChatGPT / Gemini, the row should be 1.
9. **Empty narratives** (e.g., id=10993, id=7847, several discontinued use cases): I usually confirmed 0 unless the *name* clearly described a general-purpose tool. For id=10993 ("VA Chat Copilot Meta Pilot") I marked 1 with low confidence because the name strongly suggests a broad copilot pilot.

## Things I was unsure about and left as confirms

- `Ask HR` (DOE, id=8156) at `enterprise_wide` scope: it's a RAG over HR content. Per the rule, narrow-knowledge-base RAG → 0 even if broadly available. Confirmed 0 with medium confidence.
- `Establish localized Large Language Model (LLM)` (Treasury BFS, id=10416): explicit goal is an enterprise LLM, but currently a research-stage initiative. Confirmed 0 (research/enabler) with medium confidence — could go either way once deployed.
- Small bureau LLM RAG chatbots over a single SOP / handbook (e.g., `OFM` GPT, `Ask HR Policy` ACF, `MauroGPT`, `FuelGPT`, `PARSGPT`): each is RAG over one knowledge corpus → 0. Confirmed.
- Multiple FAA "LLM Document Search" rows (rows 103–110, ids 8850–8857): each is a single knowledge-base chatbot for one FAA org — confirmed 0.

## Process notes

- Almost all 274 rows were unambiguous from the source narrative; the heuristic agent's downgrades were correct in 95% of cases. The substring-based approach over-fired in a small number of cases where the substring was itself the *name* of a general-purpose LLM ("commercial generative ai for text", "librechat", "chat copilot", "chatgpt", "gemini").
- Total time: ~75 minutes (within 60-90 minute budget).
