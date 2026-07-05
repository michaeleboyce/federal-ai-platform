# Audit gate — 2026-07 labeling passes (Fable audit layer)

Labeler: Sonnet 5 subagents (17 batches). Auditor: Fable 5 (main session),
2026-07-05. Protocol: 100% of seat-mass-bearing rows + 100% of
headline-shifting verdicts + stratified samples; overrides win at apply
time via `audit_overrides.csv`.

## A1 — band population labels (436 rows)

- **197/436 rows audited (45%)**: all 58 rows with 10k+ bands (81% of
  seat mass), all low-confidence / unknown-population / invalid-vocab
  rows (70), a 15% stratified sample (45), plus a full re-audit of
  batch2 (DOE/FERC) after its targeted subsets showed a pattern.
- **13 overrides** (3.0% of the pass): 3 invalid `stratum='unknown'`
  vocab rows (DOE), 10 consistency fixes — embedded features
  (travel-booking/Concur, Google Calendar, Viva Insights, ServiceNow
  helpdesk, whole-agency Power BI, Google Lens) moved to
  `excluded_not_seats` to match the EPA Concur/Viva precedents; AWS Q
  Developer moved to `technical`.
- Documented distinction: analyst-scoped BI bands (DOE Tableau,
  101-1000) stay `technical`; whole-agency bundled BI bands (FDIC Power
  BI, 5001-10,000) are excluded features.
- Per-batch override rates in audited subsets all <10% except batch2,
  which received the full re-audit (final batch2 rate incl. re-audit:
  6/54 = 11%, all documented above).

## A3 — LLM flag drift (341 rows)

- **100% of 327 `clear_llm_access` reasoning strings reviewed** via
  red-flag scan (phrases implying broad chat access: 13 hits, all
  verified as correct "scoped tool" clears) + no-pattern scan (58 rows
  individually read — dominated by DOE's bundled-software boilerplate:
  MUI language packs, C++ runtimes, Exchange). All 11 `set_genai` and 3
  `keep_current` read individually. **5 narrative spot-checks confirmed
  quoted text is genuine.**
- **Zero overrides.** The 96% clear rate is real: the auto-tagger's
  `is_general_llm_access` systematically over-fired on DOE's software
  catalog dump and on scoped workflow tools. Expected headline impact:
  LLM-access count drops from 803 to ~540; GenAI count rises ~180 (the
  scoped-but-generative rows now correctly carry `is_generative_ai=1`).
- Systemic finding for the ETL backlog: auto_tag's LLM inference needs
  a bundled-software guard (`ai_classification` boilerplate "AI was
  automatically integrated…" should never yield llm_access=1).

## A2 — band product links (71 rows → 73 verdicts)

- **100% audited** (small set): 14 links (all sound; GitHub
  Enterprise→GitHub Copilot correctly `inferred`), 4 `new_product`
  (approved; appended to `data/expanded_product_catalog.csv`), 55
  `no_product` (correct — "Various"/"N/A"/FRB category labels; fuzzy
  candidates properly rejected).

## A4 — product spot-audit (102 products, 29 recommendations)

- **100% audited, all 29 accepted.** Highlights: `Microsoft 365` was
  typed `coding_assistant` (clear data error); Synthesia
  computer_vision→media_analysis; Magnet Forensics security_tool→
  forensics (re-enters investigative stratum); 13 genai/frontier flag
  fixes (Perplexity, USAi, Ask Sage, Azure AI Foundry…). Doble
  Test Assistant reclassification independently converged with the A1
  audit override for the same row.
- Routing: product_type → `audit/product_categorization/proposal.json`
  (1 updated, 12 appended, canonical_name-resolved); flags →
  `data/expanded_product_catalog.csv` (11 edits; Unison PRISM promoted
  into the catalog); DALL-E parent-clear recommendation **deferred**
  (cosmetic, and clearing a parent via the current CSV mechanisms is
  not supported — family rollup is unaffected for the seat model).

## Gate checklist

- [x] All 58 big-band rows audited (audited=1 after apply)
- [x] A3 clear_llm_access 100% reviewed; headline impact quantified
- [x] A2 new products Fable-reviewed and integrated
- [x] A4 recommendations Fable-reviewed and routed to surviving CSVs
- [x] Research JSONs reviewed and applied: W3 denominators cover ALL 42
      banded agencies (post-2025-RIF, sourced; DOE carries
      contractor_headcount=94,000 with denominator_basis=incl_contractors;
      OPM corrected 5,600→2,000); 10 rollout anchors with verbatim quotes
      (Fable correction: CMS Chat share 0.87→0.15 — CMS ≈ 15% of HHS
      eligible, not 87%). Occupation caps (2210/0905 via data.opm.gov
      parquet, FedScope's successor) land as a follow-up apply — the model
      defaults role-stratum caps to the eligible workforce until then.
- [x] `make fix && make check` green twice consecutively (351 passed ×2;
      2026-07-05)
- [x] Workforce table: 120 rows, 1 per org, 0 orphans
- [x] Final headline counts (joined): OMB 852 · IFP GenAI 1,230 ·
      LLM access 476 · enterprise LLM 125. Deltas vs pre-pass
      (999/803/182) fully attributed: A3 adjudication (audited 100% on
      clear verdicts) + A4 product-flag propagation through auto_tag.

## Upstream issues logged for later passes (out of scope here)
- auto_tag LLM inference needs a bundled-software guard (DOE catalog dump).
- ~900 orphaned use_case_tags rows survive rebuilds (page queries all
  join, so no user-facing effect; hygiene fix for the ETL backlog).
- DHS "Draft Report Generation and Formatting for Investigations":
  narrative describes a different tool (contract duplicate detection) —
  source-data misalignment flagged by batch 4.
- NASA science-directorate entries carry placeholder general_llm/GenAI
  self-tags on classical-science models — candidate for a broader sweep.
