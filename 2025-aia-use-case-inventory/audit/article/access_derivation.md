# Derivation — the person-weighted AI-access statistic

_Generated 2026-07-06 by `scripts/build_access_derivation.py`;
re-run after any rebuild touching `agency_workforce_profile` or
`agency_ai_access_evidence`. Every input row carries its own source
columns in the DB; the table below shows them._

## The two denominators — do not conflate

1. **~2.31M** — OPM FedScope total federal non-postal civilian workforce
   (Sept 2024). ONLY legitimate use: sizing the coverage blind spot
   (DoD's 772,549 civilians ≈ one-third filed no 2025 inventory).
   Never the base for an access claim: it includes agencies the data
   cannot assess and makes no eligibility adjustment.
2. **The eligible base (below)** — the correct denominator for every
   person-weighted access claim, and the one matching the mandate's own
   scope ("employees whose work could benefit"): covered-agency
   headcount x per-agency `ai_eligible_share` (sourced rationale per
   row: excludes frontline/field staff without government computing).

## The chain

| Step | Value | Source |
|---|---|---|
| Covered agencies with workforce profiles | 56 | `agency_workforce_profile` level='agency' |
| Total covered civilian headcount | 1,508,837 | per-row FedScope/agency sources (as-of dates in table) |
| AI-eligible after per-agency eligibility share | 747,141 | `ai_eligible_share` x headcount, summed |
| Eligible at agencies WITH an access assessment | 715,548 (22 agencies) | `agency_ai_access_evidence` best share per agency |
| — of whom, estimated WITH access to a general-purpose tool | 282,422 (~38% of all eligible) | share x eligible, summed |
| Eligible at the 34 UNASSESSED agencies | 31,594 (~4%) | unmeasured, NOT zero |

**Headline form:** of the ~747K AI-eligible civilian employees at
covered agencies, public evidence supports general-purpose AI access for
roughly 282,422 (~38%); the remainder work where broad access
is not publicly evidenced. Attribute to IFP estimates.

## Method caveats (travel with any citation)

- **Simplified max-share model**: this doc takes each agency's single
  most-available assessed share. The dashboard's seat model
  (`dashboard/lib/db/experience/seat-model.ts`) is the authoritative
  estimator (per-tool union with independence assumption, stratum caps,
  FedScope ceilings) and will differ modestly.
- Access shares mix corroborated (press/official) and IFP-assessed
  (`searched_no_source`) rows — the Status column below distinguishes.
- The 2026-07-05 `/experience` page audit left open defects; derive
  numbers from the DB (this doc), not from the live page.
- DoD and the intelligence community are absent from the base entirely
  (no inventory, no workforce profile row).

## Per-agency derivation

| Agency | Headcount | As of | Eligible share | Eligible | Access share | Tier | Status/conf | Tool |
|---|---|---|---|---|---|---|---|---|
| VA | 451,100 | 2025-12 | 38% | 171,418 | 69% | all | corroborated/high | VA GPT |
| Treasury | 89,900 | 2025-12 | 90% | 80,910 | 5% | pilot | corroborated/medium | ChatGPT Enterprise |
| DHS | 271,927 | 2025-09-30 | 27% | 73,420 | 29% | all | corroborated/medium | DHSChat |
| HHS | 72,000 | 2026-04-17 | 78% | 56,160 | 50% | all | corroborated/high | ChatGPT (OpenAI) |
| USDA | 90,078 | 2025-06-14 | 56% | 50,444 | 10% | partial | corroborated/low | Microsoft Copilot / OpenAI models / Grok (optional generative AI tools) |
| State | 77,000 | 2024-09-30 | 61% | 46,970 | 100% | all | corroborated/high | StateChat (adoption/usage metrics) |
| DOC | 42,100 | 2025-12 | 96% | 40,416 | 5% | unknown | searched_no_source/low | General-purpose generative AI (USAi / Microsoft Copilot / Azure OpenAI) |
| DOI | 58,884 | 2026-05 | 60% | 35,330 | 10% | partial | corroborated/medium | Department-wide generative AI platform (no confirmed agency-wide tool) |
| DOJ | 115,000 | 2024-09-30 | 30% | 34,500 | 1% | latent | searched_no_source/low | Microsoft 365 Copilot Chat (M365 license entitlement) |
| DOT | 54,139 | 2025 | 51% | 27,611 | 57% | most | corroborated/medium | Google Gemini (department-wide via Google Workspace migration) |
| SSA | 58,000 | 2024-09-30 | 45% | 26,100 | 50% | all | corroborated/medium | Agency Support Companion (ASC) |
| NASA | 14,000 | 2025-07 | 98% | 13,720 | 46% | partial | corroborated/medium | ChatGSFC (Goddard-built LibreChat AI assistant) |
| DOL | 15,000 | 2024-09-30 | 80% | 12,000 | 5% | unknown | corroborated/medium | Generative AI Assistant / AI Center (OpenAI GPT-4o, GPT-4o mini via Azure) |
| EPA | 12,198 | 2025-09 | 96% | 11,710 | 10% | partial | corroborated/medium | Secure GenAI chatbot (“govchat” / Azure OpenAI internal platform) |
| DOE | 16,000 | 2025-04 | 62% | 9,920 | 81% | all | corroborated/high | Joulix (DOE enterprise AI productivity suite) |
| GSA | 8,323 | 2025-05-30 | 97% | 8,073 | 70% | most | corroborated/high | Agency-wide generative AI usage (multiple tools) |
| HUD | 7,700 | 2025-10 | 85% | 6,545 | 0% | pilot | corroborated/high | Microsoft Copilot |
| FDIC | 5,000 | 2026-01-01 | 99% | 4,950 | — | no assessment | — | — |
| SEC | 4,200 | 2025-05-06 | 99% | 4,158 | — | no assessment | — | — |
| TVA | 10,635 | 2025-09-30 | 35% | 3,722 | — | no assessment | — | — |
| FRB | 3,291 | 2025 | 85% | 2,797 | — | no assessment | — | — |
| NRC | 3,000 | 2024-09-30 | 85% | 2,550 | 5% | unknown | corroborated/medium | SimplifAI (internal generative AI chatbot) |
| NARA | 3,000 | 2024-09-30 | 85% | 2,550 | — | no assessment | — | — |
| SBA | 3,600 | 2025-05-30 | 70% | 2,520 | 0% | none | corroborated/medium | Microsoft Copilot / Perplexity / Gemini / Grammarly |
| ED | 2,453 | 2025-12 | 85% | 2,085 | 5% | unknown | searched_no_source/low | GSA USAi / Azure OpenAI / AWS Bedrock (department-wide implementation per inventory) |
| OPM | 2,000 | 2025-07-21 | 85% | 1,700 | 100% | all | corroborated/high | Microsoft 365 Copilot Chat and OpenAI ChatGPT (GPT-5) |
| EEOC | 2,000 | 2024-09-30 | 85% | 1,700 | — | no assessment | — | — |
| NSF | 1,700 | 2024-09-30 | 85% | 1,445 | 0% | pilot | corroborated/medium | Microsoft 365 Copilot (TIP pilot) |
| FERC | 1,500 | 2025 | 85% | 1,275 | — | no assessment | — | — |
| FCC | 1,404 | 2026 | 85% | 1,193 | — | no assessment | — | — |
| NLRB | 1,200 | 2024-09-30 | 85% | 1,020 | — | no assessment | — | — |
| FTC | 1,183 | 2025 | 85% | 1,006 | — | no assessment | — | — |
| NCUA | 1,255 | 2024-12-17 | 80% | 1,004 | — | no assessment | — | — |
| CFPB | 1,174 | 2026-03-31 | 85% | 998 | — | no assessment | — | — |
| PBGC | 970 | 2024-09-30 | 85% | 824 | — | no assessment | — | — |
| FHFA | 800 | 2024-09-30 | 85% | 680 | — | no assessment | — | — |
| CFTC | 700 | 2024-09-30 | 85% | 595 | — | no assessment | — | — |
| CSOSA | 1,096 | 2025 | 45% | 493 | — | no assessment | — | — |
| USITC | 430 | 2025-01 | 85% | 366 | — | no assessment | — | — |
| EXIM | 350 | 2026-02 | 85% | 298 | — | no assessment | — | — |
| FCA | 340 | 2025 | 80% | 272 | — | no assessment | — | — |
| NTSB | 455 | 2024-03 | 55% | 250 | — | no assessment | — | — |
| FRTIB | 270 | 2024-09-30 | 85% | 230 | — | no assessment | — | — |
| MSPB | 200 | 2024-09-30 | 85% | 170 | — | no assessment | — | — |
| USAID | 232 | 2026-03-20 | 65% | 151 | — | no assessment | — | — |
| NEA | 167 | 2024-09 | 85% | 142 | — | no assessment | — | — |
| STB | 152 | 2024 | 85% | 129 | — | no assessment | — | — |
| NIGC | 140 | 2025 | 85% | 119 | — | no assessment | — | — |
| OSC | 135 | 2024-03 | 85% | 115 | — | no assessment | — | — |
| FLRA | 116 | 2025 | 85% | 99 | — | no assessment | — | — |
| EAC | 83 | 2025 | 82% | 68 | — | no assessment | — | — |
| USTDA | 73 | 2024 | 85% | 62 | — | no assessment | — | — |
| OSHRC | 63 | 2024-03 | 88% | 55 | — | no assessment | — | — |
| NEH | 60 | 2025-06-10 | 85% | 51 | — | no assessment | — | — |
| AbilityOne | 37 | 2025-10-01 | 85% | 31 | — | no assessment | — | — |
| Udall | 24 | 2025-09-30 | 85% | 20 | — | no assessment | — | — |

_Eligibility rationales, headcount source URLs/titles, and verbatim
evidence quotes are on the underlying rows (`agency_workforce_profile`,
`agency_ai_access_evidence`) — cite from there when a per-agency claim
needs its primary source._
