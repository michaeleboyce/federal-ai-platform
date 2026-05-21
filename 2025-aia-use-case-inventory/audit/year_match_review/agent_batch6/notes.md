# Batch 6 adjudication notes — DOI, Treasury, ED, NCUA, NARA, CFPB, OPM, PBGC

## Decision counts

| Action | Count |
|---|---|
| `confirm_rename` | 6 |
| `reject_rename` | 95 |
| `recover_match` | 0 |
| `split` | 0 |
| `merge` | 0 |
| **Total** | **101** |

All 101 `suggested_rename` pairs adjudicated. No split/merge/recover decisions
were made — see reasoning below.

## Headline finding: the `suggested_rename` queue for this batch is almost entirely noise

Of 101 queued pairs, only **6 are genuine** (all DOI). The other 95 are
fuzzy-matcher artifacts: the deterministic matcher paired use cases on
shared generic vocabulary ("machine learning", "deep learning",
"prediction", "voicebot", "Copilot", "pipeline", "digitalization") despite
fully disjoint narratives. Name overlap alone was worthless here.

## DOI (62 pairs → 6 confirm, 56 reject)

The 6 confirms are all high-confidence genuine continuations:

- SR 28 `doi-predictions-of-pfas-concentrations-in-groundwater` → `doi-pfas-groundwater-model`
- SR 30 prairie dog colony mapping (Theodore Roosevelt NP) — stamped `[2024 INV#WO0000000109308]`
- SR 33 Flow Photo Explorer — stamped `[2024 INV#WO0000000109196]`
- SR 39 tephra classification — stamped `[2024 INV#WO0000000109095]`
- SR 48 CriticalMAAS (USGS-DARPA) — stamped `[2024 INV#WO0000000108419; ...96527]`

**Most surprising DOI finding — the `[2024 INV#...]` stamp is a trap if used naively.**
DOI's 2025 filing carries `[2024 INV#...]` stamps on many use cases, which
the charter flagged as strong continuation evidence. It IS — but the
deterministic matcher repeatedly paired a stamped 2025 row with the WRONG
2024 row (a fuzzy name match), while the stamp itself points to a
*different* 2024 use case entirely. Examples rejected for this reason:
SR 3, 5, 8, 12, 31, 44, 51, 54, 60. In each case the stamped 2025 row is a
real continuation of *some* 2024 row — just not the one the matcher
queued. Those true links presumably already exist or belong to other
slices; I did not invent `recover_match` decisions for them because the
correct 2024 partner was not in this batch's queue with bilateral
narrative evidence in front of me.

Notable near-misses rejected at medium confidence (defensible either way):
- SR 22 crack mapping (technology search → automated workflow) — same
  problem/bureau; rejected because it reads as two distinct project phases
  rather than one renamed use case.
- SR 15 migratory-bird thermal-imagery surveys — same USFWS program, but
  the 2025 row carries an INV# stamp (DOI-67) for a distinct 2024 row.

## Treasury (31 pairs → 1 confirm, 30 reject)

Only **SR 72** confirmed: `treas-integrate-google-doc-ai-for-digitalization`
→ `treasury-integrate-word-processor-ai-for-digitalization` — both are the
IRS Digital Enablement Platform (DEP); the vendor name was generalized.

The single most striking pattern: IRS filed ~10 named "voicebot" use cases
in 2024 (AUR, 1040, WMR/WMAR, EIP, OTP, AdvCTC, ACS, Financial Relief,
etc.). In 2025 these voicebots largely disappeared from the queue and the
matcher paired each one with a completely unrelated 2025 use case (anomaly
detection, inventory forecasting, identity verification, ink/paper
forecasting). All rejected. The 2024 voicebots appear to have been retired
or consolidated outside this queue.

Medium-confidence rejects worth a second look by integration:
SR 73 (LLM code-dev demo → enterprise LLM), SR 83 (tech-debt remedy → AI
software modernization), SR 85 (Copilot for Power Platform → GenAI for low-
code), SR 88 (customer-experience analytics → SOI correspondence
analytics), SR 91 (microfilm digitization → digitalization AI agent). Each
shares a theme but describes a different system/office; rejected to avoid
over-broad links.

## ED (8 pairs → 0 confirm, 8 reject)

ED filed **51** identically-named "Generative AI Usage" rows in 2024 (DB
confirmed) and only 36 total use cases in 2025, restructured into named
"Generative AI - X" categories plus distinct named tools (Aidan, Grammarly,
MS Copilot suite, RAG chatbots).

This is a genuine restructure, but **not a `split`**: a `split` per the
charter is ONE 2024 slug → ≥2 2025 slugs. Here it is many-to-many — 51
interchangeable 2024 duplicate rows mapping onto ~13 named 2025 categories.
The 8 queued pairs are arbitrary fuzzy pairings; in 6 of 8 the 2024
narrative content (code snippets, web-design images) directly contradicts
the 2025 category (image generation, code generation, mock data). The
2024 rows are functionally interchangeable, so no defensible 1:1 lineage
exists for any specific pair. All 8 rejected — the 51 2024 rows correctly
retire; the named 2025 rows are correctly new.

## NCUA, NARA, CFPB, OPM, PBGC

These agencies had **no `suggested_rename` pairs** in the queue — only
`retired_2024` and/or `new_2025` residual rows. I scanned them for
`recover_match` (a missed 1:1 between a retired 2024 row and a new 2025
row):

- **NCUA** (13 retired, 0 new in slice): the 2024 rows (Native Editor,
  Image Creator, Language Translator, Coding, etc.) have no NCUA 2025 rows
  in this slice to recover against. No decision.
- **NARA** (2 retired, 7 new): the 2 retired 2024 rows (NDC declassification
  pilot, custom AI model) and the 7 new 2025 rows (Gemini, Kendra search,
  Amelia Earhart search, Archives.gov search, etc.) describe different
  systems. The closest pair — `nara-ai-pilot-for-national-declassification-center`
  vs `nara-amelia-earhart-ai-search` — both touch declassification, but the
  2025 row is a narrow Presidential-directive POC for Earhart records, not
  a continuation of the general NDC declassification pilot. No bilateral
  evidence strong enough to recover; no decision.
- **CFPB** (4 retired, 0 new in slice): no 2025 partners available. No decision.
- **OPM** (0 retired, 3 new): only new rows (ChatGPT, Claude, Rexi). No decision.
- **PBGC** (2 retired, 0 new in slice): no 2025 partners. No decision.

## Pairs I could not confidently resolve

None left unresolved — every pair received a decision. The lowest-
confidence calls (flagged `medium` in `recommendations.json`) where a
reviewer could reasonably disagree: DOI SR 13, 14, 15, 18, 22, 24, 26, 27,
49, 59; Treasury SR 65, 73, 83, 85, 88, 91; ED SR 93, 95, 96. All were
rejected; for ED in particular the rejection is structural (interchangeable
duplicate 2024 rows) rather than a narrative-mismatch judgment.
