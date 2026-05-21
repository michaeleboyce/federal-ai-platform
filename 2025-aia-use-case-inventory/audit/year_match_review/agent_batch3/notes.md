# Batch 3 — DOE, DOL, TVA, USAGM, NMB, FHFA — adjudication notes

## Decision counts

| Action | Count |
|---|---|
| `confirm_rename` | 0 |
| `reject_rename` | 29 |
| `recover_match` | 0 |
| `split` | 0 |
| `merge` | 0 |
| **Total** | **29** |

All 29 `suggested_rename` pairs were rejected. No splits, merges, or recoveries
were emitted.

## Headline finding: every suggested_rename pair is a false positive

This batch's `suggested_rename` queue contained **zero genuine renames**. The
deterministic matcher paired rows almost entirely on shared brand names or
single keywords while the narratives describe unrelated systems:

- **DOE (9 pairs):** classic keyword collisions —
  "CrowdStrike"↔"Crickets", "Coupa"↔"CoPilot",
  DAMaL ES&H text-mining tools paired against nuclear-safety and
  geophysical-inversion tools. Two pairs (`...-fusion-energy`,
  `...-advanced-manufacturing`) paired a *specific* 2024 tool against a
  *generic ORNL portfolio rollup* — the 2025 ORNL rows are a family of
  ~10 program-level entries with identical boilerplate narratives
  ("accelerate scientific discovery ... prediction and classification"),
  not renames of any individual 2024 use case.
- **DOL (9 pairs):** the matcher paired retired COTS-tool inventory rows
  (Periscope, Dragon, ABBYY FineReader, Autodesk, Webex, Adobe Acrobat,
  Westlaw) against unrelated 2025 BLS/EBSA/MSHA custom use cases. DOL
  evidently rewrote its inventory wholesale between years.
- **TVA (11 pairs):** every 2024 row is a cybersecurity use case; every
  2025 partner is a non-security use case carrying the near-identical
  generic narrative "Increased efficiency and productivity". TVA's 2025
  filing dropped almost all its detailed 2024 cyber narratives and refiled
  a different, generically-described portfolio. No bilateral evidence
  exists for any of these pairs.

## Recoveries deliberately NOT emitted (one-slug-one-decision constraint)

Two genuine cross-year matches were identified but could not be emitted as
`recover_match` because the 2024 slug already appears in a `suggested_rename`
pair (the CHARTER forbids a slug appearing in two decisions, and
`recover_match` requires a `retired_2024` slug, not a `suggested_rename`
slug). Flagging both for the integration step:

1. **DOE Position Description Tool → SmartPD Creator.**
   `doe-position-description-tool` (2024, "streamline the creation of
   position descriptions ... for hiring federal employees") is genuinely
   continued by the new-2025 row `doe-smartpd-creator` ("improves the speed
   and accuracy for DOE employees to create position descriptions ...
   time to hire reduced"). The matcher instead mis-paired the 2024 tool
   with `doe-scripting`, which we rejected. After the reject is applied,
   `doe-position-description-tool` lands back in `retired_2024` and
   `doe-smartpd-creator` remains in `new_2025` — an integrator could then
   link them as `renamed`. **Recommend a follow-up recover_match:
   doe-position-description-tool ↔ doe-smartpd-creator.**

2. **DOL Data Ingestion of Payroll Forms → Form Recognition model.**
   The 2024 `suggested_rename` row `dol-data-ingestion-of-payroll-forms`
   ("custom ML model to extract data from complex forms ... JSON
   key/value pairs") is near-verbatim identical to the `retired_2024` row
   `dol-form-recognition-model-for-benefits-forms` ("custom ML model to
   extract data from complex forms ... JSON key/value pairs"). These are
   the **same use case duplicated within the 2024 inventory**, not a
   cross-year match — so no decision applies here, but it is a 2024-side
   data-quality issue worth noting.

## Other data-quality observations (no decision)

- `dol-ai-course-design-assistant` and `dol-ai-course-design-assistant-2`
  are exact-duplicate rows within the 2024 `retired_2024` list.
- `tva-advanced-threat-protection` and `tva-advanced-threat-protection-2`
  are exact-duplicate 2024 rows (identical names and narratives), each
  separately mis-paired by the matcher.
- The DOE 2025 expansion is genuine: ~200 new national-lab (ORNL, BNL,
  SRNS, INL, Pantex, etc.) use cases. Per the CHARTER's skepticism note,
  none of these were treated as recoveries — they are bona fide new
  filings, and no `retired_2024` DOE rows were present in this slice to
  match against anyway.
- USAGM, NMB, FHFA: no `suggested_rename` pairs in this batch. Their
  `retired_2024` / `new_2025` rows (USAGM CMS/media GenAI use cases, NMB
  document-summarization use cases, FHFA Microsoft 365 / iOS productivity
  rows) showed no genuine cross-year matches — the USAGM and NMB 2025 rows
  are net-new filings and the FHFA retired rows have no 2025 counterpart.

## Low-confidence flags

Four DOE rejects were marked `medium` confidence rather than `high`
because the paired use cases share a real thematic domain (autonomous
real-time control; "data infrastructure"; fusion energy; advanced
manufacturing). In each case the narratives still describe distinct
systems/facilities/outputs, so `reject_rename` stands — but these are the
pairs most worth a second look if integration review re-samples:
`doe-fast-ai-...`↔`doe-autonomous-real-time-guiding-of-bcp-film-synthesis`,
`doe-scmc-aws-data-infrastructure`↔`doe-doe-ai-data-infrastructure-system`,
`doe-tritium-accountancy-...`↔`doe-ornl-ai-for-fusion-energy`,
`doe-in-situ-monitoring-...`↔`doe-ornl-ai-for-advanced-manufacturing`.
One DOL reject (`dol-dol-intranet-website-chatbot-assistant`↔
`dol-generative-ai-assistanti-ai-center`) was also `medium`: the 2025 AI
Center could plausibly be a successor platform, but the scope expansion
(narrow procurement Q&A → broad GenAI platform) makes it a new use case.
