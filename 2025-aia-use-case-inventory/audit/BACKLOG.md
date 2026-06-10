# Data-quality backlog — single source of truth for what remains

_Last updated: 2026-06-10. Update this file whenever a queue's state
changes; future agents should trust this over scattered TODO sections._

## How to verify the current state

```bash
make fix && python3 -m pytest tests/ audit/checks/ -q   # must be green
python3 scripts/build_article_factsheet.py              # citable numbers
```

## Done (do not redo)

| Item | Where the receipts live |
|---|---|
| 2026-04 retag audit applied (was silently no-op'ing on stale ids) | `scripts/apply_retag_audit.py` docstring (post-mortem), `scripts/uc_signature.py` |
| 553-verdict capability re-reviews (LLM access 1,055→803; agentic 283→59) | `audit/retag/general_llm_round3/`, `audit/retag/agentic_review/` |
| Enterprise-scope corrections, both years (15→12 artifact resolved to 21→24) | `audit/retag/enterprise-scope-2026-06/` |
| Evidence persistence: sources + quotes written onto use cases | `scripts/persist_capability_evidence.py` → `use_case_external_evidence` (790+ rows) |
| Primary-product cache re-derived from edges every rebuild | `scripts/refresh_primary_product_cache.py`; `check_refactor_quality` un-xfailed |
| stage / ai_classification normalization (m016) | `scripts/normalize_use_case_fields.py` |
| 2024 tag backfill + verification (93.9–100% across 4 dims) | `audit/retag/2024-tagging-verification/verification_report.md` |
| Article guardrails enforced as tests | `audit/checks/check_article_guardrails.py` |

## In flight (2026-06-10)

- **review_queue_products (626 rows)** — five reviewer batches writing
  `audit/product_queue_review_2026-06/verdicts_batch{1..5}.csv`; applied by
  `scripts/apply_product_queue_review.py` (signature-keyed, in `make fix`).
  When complete, `audit/db_snapshot.md` `pending_product_reviews` should
  drop toward 0 and stay there across rebuilds.
- **2024-vs-2025 divergence queue (38 rows)** — reviewer writing
  `audit/retag/2024-vs-2025-divergence/resolutions.csv`; applied by
  `scripts/apply_divergence_resolutions.py`.

## Remaining — needs a human (cannot be done by agents)

1. **Press verification before publishing** (also baked into
   `audit/article/fact_sheet.md` §Guardrails):
   - DOJ department-wide GitHub Copilot — no public corroboration; press
     inquiry to JMD/OCIO before any "DOJ-wide Copilot" claim.
   - VA OIG Jan-2026 advisory (VA GPT/Copilot PHI) — cite with any
     VA-positive framing.
   - Anthropic federal ban (Feb 2026) — date-stamp HHS Claude claims.
   - DHS commercial-AI revocation — counter-trend framing.
2. **DOI "Iris"** — referenced in old notes, never found in DB or web;
   drop the reference or ask DOI directly.

## Remaining — agent-sized, lower priority

- 31 `data_analysis` shorthand rows skipped by evidence persistence
  (agent-abbreviated names like "Elastic ML Threat Detection" vs the DB's
  full names); their evidence lives in `audit/retag/data_analysis/by_agency.md`.
  Optional: hand-map them in `persist_capability_evidence.py`.
- `topic_area` blank on ~560 rows — display-level "Unspecified" only;
  never invent values.
- Dashboard `/use-cases` stage facet still filters on raw
  `stage_of_development` variants (UX nit; data layer normalized via m016).

## Standing rules (read before touching anything)

- Never trust numeric ids from CSVs — resolve by (agency, use_case_name)
  via `scripts/uc_signature.py`; apply scripts must hard-fail >2–5%
  unresolved (see CLAUDE.md "Multi-agent safety").
- Cite numbers only from `audit/article/fact_sheet.md` (regenerate after
  every `make fix`); the "must NOT say" list there is enforced by
  `audit/checks/check_article_guardrails.py`.
- After tag/scope changes, re-run `compute_maturity.py` +
  `scripts/compute_agency_readiness.py` (the guardrail check catches the
  drift if you forget) and sync the DB into `dashboard/data/` before any
  dashboard push.
