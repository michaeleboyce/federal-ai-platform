# Retag Audit — Follow-Ups

Generated 2026-04-29 from a three-agent web-grounded retag of the 2025 federal AI inventory. Companion artifacts:

- `general_llm/by_agency.md` · `general_llm/by_row.csv` · `general_llm/notes.md`
- `coding/by_agency.md` · `coding/by_row.csv` · `coding/notes.md`
- `data_analysis/by_agency.md` · `data_analysis/by_row.csv` · `data_analysis/notes.md`

The DB was **not modified**; all corrections live in CSVs awaiting an apply pass.

## 1. Editorial review (do first)

- [ ] Read `general_llm/by_agency.md` end-to-end (113 rows, the "which agencies have a real FOUO LLM" rollup).
- [ ] Read `coding/by_agency.md` (80 rows).
- [ ] Read `data_analysis/by_agency.md` (53 rows).
- [ ] Decide which agencies the article will name and at what rating. Anchor each named agency to a `Key Evidence` URL or DB row id from the rollups.

## 2. Press / verification follow-ups before publishing

- [ ] **DOJ department-wide GitHub Copilot** — DB row 8713 lists it "Department wide" with GitHub + Microsoft, but no public announcement corroborates a real rollout. Send a press inquiry to JMD/OCIO; do not publish a "DOJ-wide Copilot" claim without confirmation.
- [ ] **VA OIG advisory (Jan 2026)** — VHA authorized VA GPT and M365 Copilot Chat for use with PHI without National Center for Patient Safety coordination. Cite alongside any VA-positive framing. Source: vaoig.gov preliminary advisory memorandum.
- [ ] **Anthropic federal ban (Feb 2026)** — disrupts HHS Claude dept-wide rollout, NASA GSFC pilot, several DOE lab pilots. Add an "as of <date>" qualifier to any HHS-Claude claim.
- [ ] **DHS commercial-AI revocation** — DHS cut off ChatGPT and other commercial AI to consolidate on DHSChat. Note as a counter-trend to OneGov-driven federal expansion. Source: FedScoop.
- [ ] **State StateChat in promotion-panel selection** — documented decision-impact use, worth at least one sentence.
- [ ] **DOI "Iris"** — referenced in earlier internal notes; not surfaced in DB or web. Either drop the reference or chase it with DOI directly.

## 3. Things the article must NOT say

- [ ] Do not cite `agency_ai_maturity.has_enterprise_llm` or its sibling counters. Both directions are wrong.
  - False positives: FCC, PBGC, EAC, OSC, CSOSA, USTDA, NLRB (driven solely by checking "Y" on the OMB Appendix B Microsoft Copilot template line).
  - False negatives: State, VA, DOJ, DOI, DOT (real enterprise LLMs that the maturity table missed).
- [ ] Do not credit GSA USAi.gov as a data-analysis environment. It is a chat / model-evaluation sandbox.
- [ ] Do not infer broad analyst access from a Palantir contract. DHS $1B BPA and USDA $300M NFSAP are operational case-management platforms with narrow power-user populations.
- [ ] Do not assert that a financial regulator (SEC, FRB, FDIC, NCUA, CFTC, CFPB) lacks an analytic platform. The 2025 inventory just doesn't surface their stack.
- [ ] Do not equate "checked Y on the OMB Appendix B 'Generating code using AI' template" with a managed coding-tool deployment. Eight of eleven Appendix-B-only filers checked Y; most are M365 Copilot's incidental code-chat feature.

## 4. Consolidated apply pass to the DB (after editorial review)

Write a single migration script that, in order:

- [ ] Apply LLM-flag corrections from `general_llm/by_row.csv` to `use_case_tags.is_general_llm_access` and `deployment_scope`. Highest-impact corrections:
  - State StateChat → `enterprise_wide`.
  - VA, DHS, DOT, GSA, OPM, NARA, FRTIB, HHS → confirm `is_enterprise_wide` set correctly per the rollup.
  - HHS narrow CDC/CMS chatbots (≈34 rows) → `is_general_llm_access=0`.
  - FCC/PBGC/EAC/OSC/CSOSA/USTDA/NLRB consolidated rows → leave Y (technically correct) but rate Limited, not Enterprise.
- [ ] Apply coding-tool corrections from `coding/by_row.csv` to `use_case_tags.is_coding_tool` and `tool_product_name`. Largest gains: DOJ row 8713; DOC NOAA/BEA/USPTO; DOE all 9+ labs; HHS CMS/FDA/HRSA/NIH; DOI BTFA; SSA AveriSource; Treasury IRS/BFS/OCC.
- [ ] Apply autocoder de-tagging from `coding/by_row.csv` (DHS LIGER/PAiTH, DOL/DOJ/HHS classifiers — these are NOT coding tools despite "code" in the name).
- [ ] Backfill `deployment_environment` from `data_analysis/by_row.csv` (currently 100% "unknown" — fill where the rollup names a platform/network).
- [ ] **Merge in pre-existing unresolved review queues** so we don't lose prior work:
  - `audit/review_queue_products_unresolved.csv` (~821 rows)
  - `audit/review_queue_scope_unresolved.csv` (~166 rows)
  - `audit/review_queue_entry_type_unresolved.csv` (~236 rows)
  - `audit/proposed_aliases_seed_now.csv` and friends
- [ ] **Fix the `make fix` drift bug** (see `audit/human_review_llm_drift.md`). `Makefile:fix` runs `auto_tag.py` which silently regresses LLM corrections. Either chain `scripts/retag_llm.py` after `auto_tag.py` in the Makefile, OR change `auto_tag.py` to defer to `is_general_llm_access` already set by the LLM pass. Without this, the next rebuild undoes everything.
- [ ] Re-run `python compute_maturity.py` so `agency_ai_maturity` reflects the corrected tags.
- [ ] Re-run the dashboard build and spot-check that maturity-tier rankings now match `general_llm/by_agency.md`.

## 5. Known gaps the apply pass cannot fix

- [ ] Source IDs lost on 2,007 of 3,616 rows during normalization (per `audit/consistency/01_id_traceability.md`). Backfill from `raw_json` is a separate, prerequisite cleanup if traceability matters for citation.
- [ ] DoD, USAID, ODNI, CFPB, EEOC, GAO, EXIM, FLRA, MSPB, NEH, PRC, Presidio Trust, USAGM, USCCR, CPSC have no 2025 individual inventory in our dataset. Article framing must acknowledge this — "federal civilian agencies" without DoD is roughly a 60%-of-headcount asterisk.
- [ ] HHS public download returned 403 during audit; the 447 HHS rows in the DB are loaded but not externally re-verified at the file level.
- [ ] Financial regulators' analytic-platform stack is invisible to this inventory format.

## 6. Optional next-round work

- [x] **Subagency-level rollup for HHS, DHS, DOE, DOC, Treasury, DOJ — done in round-3.** See `audit/retag/round3/SUB_AGENCY_FINDINGS.md` for the editorial summary and `audit/retag/round3/<topic>/sub_agency_rows.csv` (96 rows × 3 topics) for the per-row evidence. Sub-agency tables now appended to all three `by_agency.md` rollups under a "Sub-agency rollup (round-3)" heading. Headline: VA/OIT is the only triple-strong sub-agency; HHS is a federation of 8 independently-Enterprise bureaus; NASA/GSFC carries the agency; DOE is bimodal across labs.
- [ ] Cross-check 2024 → 2025 deltas on the named-platform list to find systems that quietly disappeared (e.g., State CodeGen retired).
- [ ] Vendor-side corroboration for high-stakes claims (Databricks, Snowflake, Palantir, Anthropic public-sector pages).

## 5. Data lineage (added 2026-06-09, post-restore)

Raw agency files (`data/raw/*.{csv,xlsx}`) → `load_inventories.py` /
`load_2024.py` (verbatim columns + raw_json; 2024 tags survive reloads via
slug re-attachment) → `scripts/normalize_use_case_fields.py` (m016:
`stage_normalized`, `ai_classification_normalized` — the only derived
recodes of OMB-filed fields) → `auto_tag.py` keyword first pass →
`scripts/retag_llm.py` + `apply_retag_audit.py` + `apply_round2_audit.py`
+ `apply_capability_reviews.py` (row-by-row audited corrections; ALL
signature-keyed via `scripts/uc_signature.py` + the
`id_snapshot_2026-04.csv` old-id map; hard-fail on >2% unresolved) →
`compute_maturity.py` (capability flags now tag-derived, individually
reported rows only).

Citable numbers: regenerate `audit/article/fact_sheet.md` via
`scripts/build_article_factsheet.py` after every `make fix`. Guardrails
enforced by `audit/checks/check_article_guardrails.py`.

The §4 consolidated apply pass below is COMPLETE as of 2026-06-09 (the
original apply scripts had silently no-op'd on rotated ids; see
`scripts/apply_retag_audit.py` docstring for the post-mortem).
