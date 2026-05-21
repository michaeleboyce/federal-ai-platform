# Batch 4 — year-match review notes (DOC, USDA, SEC, FDIC, EEOC, PT, EAC, NTSB)

## Decision counts

| Action | Count |
|---|---|
| `confirm_rename` | 6 |
| `reject_rename` | 33 |
| `recover_match` | 0 |
| `split` | 0 |
| `merge` | 0 |
| **Total** | **39** |

All 39 decisions correspond exactly to the 39 `suggested_rename` pairs. No
split / merge / recover were issued (rationale below).

## Headline finding: the `suggested_rename` queue for this batch is almost all noise

33 of 39 (85%) suggested_rename pairs were **rejected**. The deterministic
matcher's mid-confidence band for these eight agencies is dominated by
cross-bureau false pairings — it paired use cases on a single shared token
("chat", "search", "automate", "analysis", "mitigation", "detection",
"create", "research", "water", "cloud") across completely different bureaus
and problem domains. Examples:

- BEA cybersecurity tool → NOAA wildfire nowcasting model (SR1)
- NOAA CoralNet computer vision → NTIA grants/environmental-assessment pilot (SR3)
- USPTO Enriched Citation system → NOAA precipitation forecasting (SR13)
- USPTO DesignVision image search → NOAA VIAME marine toolkit (SR15)
- APHIS email-spam classifier → Forest Service feral-ungulate camera traps (SR22)

This is the expected behavior of fuzzy name matching once obvious matches are
already consumed as `continued` / `renamed` upstream — the residual is the
hard tail.

## The 6 confirmed renames (all genuine, name-driven rewrites)

- **SR5** `LightningCast: AI for lightning prediction` → `LightningCast: A
  lightning nowcasting model` (NOAA). Same model, "prediction" → "nowcasting".
- **SR9** `AI Rain Rate estimation` → `AI based Precipitation estimation`
  (NOAA). Same satellite precipitation-estimation task generalized; both
  narratives empty so judged on name + bureau + domain — `medium` confidence.
- **SR12** `AI retrieval for TM design coding and image search` → `TM Word
  and Image Search Tool (TWIST)` (USPTO). Both the Clarivate TMVision
  trademark image-search use case.
- **SR17** `Patents - Skill Group Matching` → `Pre-Exam Application: Skill
  Group Matching` (USPTO). Identical function, reframed under pre-exam.
- **SR29** `Public Filing Disclosure Review` → `Disclosure Review Chatbot`
  (SEC). Same disclosure-review Q&A problem recast as the DREAM chatbot —
  `medium` confidence (the 2025 row is more chatbot-specific).
- **SR31** `Invoice and Contract Data Extraction` → `Data Extraction from
  Contract PDF Files` (FDIC). Same contract-PDF extraction-to-spreadsheet
  use case, scope narrowed to date fields.

## No split issued despite DOC/NOAA refactor

DOC/NOAA did refactor heavily — 169 `new_2025` DOC rows, many granular NOAA
computer-vision rows. The 2024 CoralNet use case (SR3) has a near-duplicate
sibling in `retired_2024` (`...-machine-vision-p-2`), and 2025 contains
`doc-using-coralnet-to-develop-subtrate-detection-models-for-auv-imagery`
plus a dozen marine image-classification rows (VIAME reef fish, zooplankton,
groundfish, marine mammals). A `split` of the 2024 CoralNet row into those
2025 rows is *plausible* but the 2024 narratives are too thin ("Computer
vision for coral reef monitoring", "FCNN") to establish the required
bilateral evidence that the same 2024 use case became those specific 2025
rows — they read as independently filed new projects. Per CHARTER principle
2/3 I did not assert a split on keyword overlap alone. Flagged here for the
integration team if richer 2024 source data is available.

## Candidate recover_match NOT issued — flagged for integration

`fdic-deposit-insurance-determination` (2024) and `fdic-provisional-holds-model`
(new 2025) both describe estimating/managing provisional holds on large
(>$250M) failed-bank deposit accounts, in the same Division of Resolutions &
Receiverships. This looked like a genuine matcher miss. However, the 2024
slug is already the subject of `suggested_rename` SR36 (paired with OIG
forensics), which I **reject**. Per CHARTER principle 4 (one slug, one
decision) I could not also emit a `recover_match` on the same 2024 slug, so
SR36 is recorded as `reject_rename` (sending the 2024 slug back to
`retired_2024`). **Recommendation for the integration step:** after SR36 is
applied, consider a follow-up `recover_match`
`fdic-deposit-insurance-determination` → `fdic-provisional-holds-model`
(low/medium confidence).

## Pairs flagged low/medium confidence

- **SR7** (radiative transfer) — rejected `medium`. The 2024 CRTM emulator
  likely has a true 2025 descendant
  (`doc-ai-based-radiative-transfer-emulator-for-data-assimilation-and-remote-sensing`),
  not the hybrid-framework row the matcher chose. Not recovered (the better
  partner would need its own decision and the SR pairing was clearly wrong).
- **SR9** confirm — `medium` only because both narratives are empty.
- **SR29** confirm — `medium`; the 2025 row is notably more chatbot-specific.
- Several USDA/SEC/FDIC rejects marked `medium` where the two use cases share
  a genuine functional theme (comment analysis, research summarization,
  report generation) but differ in bureau, inputs, and outputs.

## Agencies with no suggested_rename rows

EEOC, PT, EAC, NTSB had **zero** `suggested_rename` pairs. Their
`retired_2024` rows (EEOC's 8 generic capability rows, PT's 5
capability-category rows, EAC's 2) and NTSB's 2 `new_2025` rows showed no
defensible bilateral recovery — EEOC/PT 2024 rows are vague
capability-bucket entries with near-identical boilerplate narratives, and
the NTSB 2025 rows (Dataminr, FOIAXpress) are clearly new products. No
decisions issued for these four agencies.
