# AUDIT GATE — product_capability_2026_07

**Status: GREEN** (labeled, QC-audited, applied — 2026-07-05)

## Population and flow

- 609 canonical products with ≥1 `entry_product_edges` row (built by
  `scripts/build_product_capability_inputs.py`, 5 vendor-grouped batches).
- First pass: 5 labeler agents, one per batch (`labels_batch{1..5}.csv`),
  609/609 rows, zero vocabulary violations on mechanical validation.
- QC pass: 288 rows (47%) re-judged by 3 independent judge agents
  (`qc_input_batch{1..3}.csv` → `qc_results_batch{1..3}.csv`). Strata:
  100% of rows labeled `genai_platform` or `assistant` (99), 100% of
  `low`-confidence rows (178), deterministic 10% sample of the rest
  (md5-ordered, no RNG).

## QC outcome

- 279 confirmed (`source=qc_confirmed`), 9 corrected (`source=qc_corrected`),
  321 not sampled (`source=llm`). Correction rate 3.1%.
- Systematic first-pass error identified by judge 2: thin custom GenAI
  applications over-assigned `genai_platform`; the platform label is
  reserved for products that ARE the LLM surface. 3 of 9 corrections
  (INL ×2, ORR) fix this; future top-ups should heed the boundary rule in
  INSTRUCTIONS.md.
- Other corrections: Elsa (FDA) assistant→genai_platform for consistency
  with peer agency chat surfaces; Google Distributed Cloud none→
  genai_platform (hosts OpenAI models); GrantSolutions Helpdesk
  assistant→chatbot; MediaViz gen_ai 1→0; Palantir CMA ml_platform→none
  (app-on-platform double-count); Whooster search→none (skip-trace lookup,
  not semantic search).

## Applied

- Merged to `data/product_capability_labels.csv` (exploded; 642 rows,
  609 products), applied via `scripts/apply_product_capability_labels.py
  --apply`. Coverage gate: 609/609 edged products.
- Invariants: `tests/test_apply_product_capability_labels.py` +
  `audit/checks/check_sleeping_services.py` all green.
- Tripwire cross-check: sleeping-pair replica = 599 pairs (matches the
  2026-07-05 prototype exactly); LLM-vs-regex similar-deployed
  disagreement 25.9% (bound: 30%; the LLM labels are intentionally
  broader than the prototype name-regex).

## Category distribution (products, multi-label)

none 197 · vision 144 · nlp 62 · assistant 56 · genai_platform 43 ·
chatbot 32 · speech 32 · search 26 · doc_processing 24 · ml_platform 15 ·
translation 9 · ml_lowcode 2

## Known limitations

- The closed vocabulary has no slot for scientific/predictive ML
  (AlphaFold, hydrology forecasts), entity-resolution/investigative data
  products, or generative video (Synthesia, Vyond) — these sit in `none`
  (or nearest class) by design; revisit if a capability-void analysis
  wants those classes.
- `gen_ai` hints from the earlier ETL pass were overridden in both
  directions where evidence contradicted them; reasoning strings note it.
