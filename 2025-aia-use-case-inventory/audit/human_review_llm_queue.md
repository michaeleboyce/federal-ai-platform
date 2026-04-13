# LLM Queue Review

## Check
Reconciled `review_queue_llm` (250 rows) against the live DB state. The queue
has already been scored by the LLM pass: every row carries `llm_label`,
`llm_confidence`, and `llm_reasoning`. The unresolved rows are exported to
[review_queue_llm_unresolved.csv](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/review_queue_llm_unresolved.csv)
via `scripts/export_review_queue_llm_unresolved.py`.

## DB-derived counts (authoritative)
| Bucket | Count | Meaning |
|---|---|---|
| Total queue rows | 250 | All rows where `review_queue_llm.use_case_id` is set. |
| Already auto-applied | 218 | `applied = 1`. Of these: **190 agree** (heuristic == LLM label) and **28 high-confidence flips** (LLM overrode heuristic at `llm_confidence = high`). |
| Still unresolved | 32 | `applied = 0`. Breakdown: 11 low-confidence, 21 medium-confidence disagreements. |

Confidence distribution across the full queue: 182 high, 57 medium, 11 low.

## What "still unresolved" means here
For the 32 unresolved rows, the canonical
`use_case_tags.is_general_llm_access` value **retains the heuristic label**
pending human review. The LLM's proposed label and its one-line reasoning are
preserved in `review_queue_llm.llm_label` and `review_queue_llm.llm_reasoning`
for reference but are **not** currently reflected in the canonical tags.

Unresolved breakdown by agreement direction:
| Confidence | Heuristic -> LLM | Count |
|---|---|---|
| low  | 0 -> 0 (agree, held for review) | 9  |
| low  | 1 -> 0 (flip to non-LLM)         | 2  |
| medium | 0 -> 1 (flip to LLM)           | 20 |
| medium | 1 -> 0 (flip to non-LLM)       | 1  |

Agency concentration of unresolved rows (top 5): HHS 9, NASA 4, VA 3,
Treasury 2, SEC 2. See the CSV for per-row details.

## Method
Used the tag guidance in [AGENT_TAGGING_GUIDE.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/AGENT_TAGGING_GUIDE.md),
the LLM precedence fixtures in [tests/test_llm_tagging.py](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/tests/test_llm_tagging.py),
and the current heuristic logic in [auto_tag.py](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/auto_tag.py).
Applied the same conservative rule family as the tests:
- `Classical/Predictive Machine Learning`, `Computer Vision`, and
  non-generative `NLP` default to non-LLM unless the row explicitly names a
  frontier model or chatbot.
- Named LLMs and chat products such as `ChatGPT`, `Copilot`, `Claude`,
  `Gemini`, `LLM`, `GenAI`, `GPT`, `Azure OpenAI`, and `Amazon Q` count as
  positive evidence.
- Blank `ai_classification` with no explicit model/product signal stays
  unresolved rather than being inferred.

## Recommended follow-up
Treat the 32 unresolved rows as a single human-review workstream. The
medium-confidence `0 -> 1` cluster (20 rows) is the highest-signal queue and
is concentrated in HHS, NASA, and VA. The low-confidence rows should be
reviewed second.

## Operational note on idempotence
`scripts/retag_llm.py` remains the authoritative pass for
`is_general_llm_access`. As of this audit, `auto_tag.py` has been corrected
so that its `is_llm` computation matches `infer_llm_flag` exactly (the
previous `coding_assistant`/`agentic` bump was removed; see the comment in
`auto_tag.py` near the `is_llm =` block). The `Makefile` `fix` target now
also invokes `scripts/retag_llm.py` after `auto_tag.py` as a belt-and-
suspenders safeguard, so canonical LLM false positives stay below the
`audit/checks/check_llm_flags.py` ceilings even if a future change to
`auto_tag.py` re-broadens the rule.
