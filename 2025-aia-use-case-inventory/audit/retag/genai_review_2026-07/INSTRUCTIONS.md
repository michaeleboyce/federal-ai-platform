# GenAI-flag review — is `is_generative_ai` right on this row?

## What this is

The 2025 heuristic tagger set `is_generative_ai` from keyword matches
(`LLM_KEYWORDS + AGENTIC_KEYWORDS` in `auto_tag.py`) — and bare words like
"autonomous", "agent", "workflow", "chatbot", "assistant" over-fire. A
2020 border-surveillance tower (agency-declared Classical ML) and a 2019
intent-based FAQ chatbot are currently flagged generative. Meanwhile some
rows the agency itself filed as "Generative AI" never got the flag. The
2024-cycle tags were LLM-judged row by row; this pass brings the 2025
flag to the same standard.

`input.csv` (and `input_batch{N}.csv` slices) has one row per use case
where the IFP flag disagrees with the agency's own `ai_classification`,
with the narrative fields, the current flags, and `fired_keywords` — the
exact tagger keyword(s) that matched, so you can see why the heuristic
fired. The `cohort` column says which direction the disagreement runs:

- `over_contradict` — flag=1, agency declared Classical/Predictive ML,
  Computer Vision, NLP, Other, or Reinforcement Learning.
- `over_unspecified` — flag=1, agency declared nothing.
- `under_declared` — flag=0, agency declared Generative AI or Agentic AI.

## Decision rule

**genai** (`is_generative_ai` should be 1): the system uses a model to
**produce novel content** — text, code, images, audio, video, or
synthetic data. This includes:
- LLM chat, drafting, coding assistants, summarization, Q&A over
  documents (RAG), translation by neural models;
- speech synthesis / text-to-speech, image or audio generation;
- template-free natural-language generation of narratives or reports;
- synthetic-data generation.
Strong genai signals: `is_general_llm_access=1` (a general chat LLM is
generative by definition); the agency's own classification says
Generative AI or Agentic AI; a named genai product (Copilot, ChatGPT,
Claude, Gemini, etc.) in the narrative.

**not_genai** (`is_generative_ai` should be 0):
- detection / classification / scoring pipelines (imagery, fraud,
  wildlife, medical findings) — even if "automated";
- classical autonomy and control (rovers, collision avoidance, spacecraft
  or schedule optimization) — "autonomous" in aerospace ≠ generative;
- intent-based / scripted chatbots that select canned answers rather
  than generating text (typical for pre-2022 chatbots — check the date);
- RPA / deterministic workflow automation, OCR, extraction, routing,
  transcription-only, forecasting, sentiment scoring.

Weighting: the agency's own `ai_classification` is a strong signal in
BOTH directions but not conclusive — agencies under-declare (a row that
names ChatGPT but is filed as "NLP" is still genai) and occasionally
over-declare (a row filed "Generative AI" whose narrative describes a
pure classifier: trust the narrative, mark not_genai, confidence=low or
medium, and say why). When `fired_keywords` shows only agentic words
("agent", "autonomous", "workflow", "multi-step") and the narrative shows
no content generation, that is the known over-fire pattern → not_genai.
When the narrative is too thin to tell, follow the agency's declared
classification; if that is 'Unspecified', keep the flag only if the name
or product is unambiguous, else not_genai with confidence=low.

Edge cases seen in spot checks (decide from the narrative, these are not
pre-verdicts): CBP Translate (neural MT → genai despite NLP declaration);
HUD Ginnie Mae narrative reports (rule-coded NLG — if the narrative says
coded rules / templates, that is borderline; template-free generation →
genai, pure mail-merge → not_genai); DOE text-to-speech (genai);
early FAQ chatbots (usually not_genai).

## Output

Write `verdicts_<your-batch>.csv` to this directory with EXACTLY these
columns (signature-keyed; do NOT invent numeric ids):

agency,use_case_name,verdict,confidence,reasoning

- verdict ∈ {genai, not_genai}
- confidence ∈ {high, medium, low}
- reasoning: 1–2 sentences quoting the deciding narrative phrase.

Every input row must appear exactly once in your output. Copy
`agency` and `use_case_name` byte-for-byte from the input — they are the
join key.
