# Batch 5 adjudication notes — VA, DHS, GSA, FRB, FTC, FRTIB, USTDA, PRC

## Decision counts

| Action | Count |
|---|---|
| `confirm_rename` | 18 |
| `reject_rename` | 59 |
| `split` | 1 |
| `merge` | 0 |
| `recover_match` | 0 |
| **Total** | **78** |

All 78 `suggested_rename` pairs were adjudicated. The single `split`
replaces one of those pairs (SR51), so 77 confirm/reject + 1 split = 78
decisions, each touching exactly one SR-side 2024 slug. No duplicate
slugs across decisions.

## Headline finding: the matcher's `suggested_rename` queue was mostly wrong

59 of 78 pairs (76%) are `reject_rename`. The mid-confidence fuzzy band
for this batch is dominated by **acronym-shape and generic-noun
collisions** — pairs the matcher linked on shared tokens like
"Service", "Services", "Analysis", "Assessment", "Chatbot", "Cyber",
"Sentiment Analysis", "Large Language Model", "Facial Recognition" while
the underlying systems are unrelated. Examples:

- `dhs-traveler-verification-service-tvs` (biometric entry/exit) →
  `dhs-document-translation-service-dts` (Azure translation) — matched
  purely on "...Service (xyz)".
- `dhs-cyber-incident-reporting` → `dhs-traveler-entity-resolution`;
  `dhs-cyber-vulnerability-reporting` → `dhs-land-border-integration`.
- `va-github-copilot` → `va-image-quality-control-tool`.
- `va-zio-patch-heart-monitor` → `va-continuous-glucose-monitoring-summary`
  (both 14-day monitors, different organ/condition).

A recurring DHS pattern: 2024 retired/inactive **CISA cyber** use cases
were fuzzy-matched to **2025 HSI/CBP investigation** use cases. These
are different DHS components and different missions — all rejected.

## The one split

**SR51 — `dhs-facial-recognition-service` → 3 HSI 2025 rows.** The 2024
HSI Innovation Lab / RAVEn Facial Recognition Service (covering child
exploitation, war criminals, human-rights atrocities) was re-filed in
2025 as three HSI component-level use cases:
`dhs-facial-recognition-for-national-security-investigations`,
`...-for-investigations-of-transnational-criminal-organizations`, and
`...-for-investigations-of-child-sexual-exploitation-and-abuse`. The
matcher's suggested 2025 partner
(`dhs-facial-recognition-for-national-security-and-transnational-criminal-organization`)
is a separate **USBP / Border Patrol** facial-recognition row — wrong
component — so the suggested pair is discarded by the split. The USBP
2025 row is left undecided and keeps its `new_2025` status.

## Confirmed renames worth noting

Most `confirm_rename` decisions are high-confidence FDA-device or
named-product carryovers where the 2025 filing only cleaned up the name
(GE Logiq E10, Avicenna ICH→CINA, QVCAD, Philips EPIQ/Affiniti, LINQ II,
Volpara, PCSIP). A few are program-level renames with rewritten
narratives but the same problem+outputs (Genesys→AI-Enhanced Call
Center, VET-HOME→VA VoiceBot, FEMA OCFO GPT→Executive Summary GPT,
ML Translation Initiative→Mobile Language Translation Services).

## No recover / merge

- **Recover:** FRB has 13 `retired_2024` rows but only **1**
  `new_2025` row (`frb-oasis-semantic-search`). I checked it against the
  FRB retired rows — Oasis Semantic Search is generic document retrieval
  and does not bilaterally match `frb-document-organization-tool` or any
  other retired FRB row strongly enough to recover. USTDA (4 retired, 0
  new) and PRC (1 retired, 0 new) have no `new_2025` rows at all, so no
  recover is possible. The USTDA retired rows are commercial security
  tools (Lookout, Qualys, CrowdStrike, Exiger DDIQ) genuinely dropped.
- **Merge:** No ≥2-to-1 consolidation found with real bilateral
  narrative evidence in the VA/DHS/GSA residuals.

## Low-confidence / unresolved

- **SR70 GSA `gsa-survey-comment-ham-spam-tester` →
  `gsa-public-comments-analysis`** — flagged **low confidence**
  `confirm_rename`. Both are AI-assisted comment processing, but the
  2024 input is USA.gov *survey* comments and the 2025 input is
  *regulatory-docket* public comments (regulations.gov). Could
  reasonably be a `reject_rename`; integrators may want to re-check.
- A cluster of DHS pairs (`autonomous-maritime-awareness` /
  `global-maritime-intelligence`; `advanced-analytic-enabled-forensic-investigation`
  / `mobile-device-forensics`; `cyber-threat-intelligence-feed-correlation`
  / `dark-web-threat-intelligence`; `svip-language-translator` /
  `real-time-language-translation-services`; `climate-change-assessment-tool`
  / `dhs-asset-assessment-tool`) share a broad domain but differ on
  component and specific system. All rejected at **medium** confidence —
  defensible either way but the bilateral "same system" evidence is
  absent.
