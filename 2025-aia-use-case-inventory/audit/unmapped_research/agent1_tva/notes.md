# Agent 1 — TVA / NCUA / CFTC / FTC / EPA notes

## Methodology

Filtered `audit/unmapped_bureaus.csv` to the five agencies in this slice (30
distinct bureau strings). For each, I (1) spot-checked the use cases in the DB
to see what the bureau actually does, (2) ran 1–2 web searches per bureau, and
(3) consulted the existing seed (`data/federal_hierarchy_seed.py`) to decide
whether to add, alias, split, or skip.

## TVA-specific patterns

- TVA's bureau strings are a mix of formal corporate groups (Supply Chain,
  Economic Development, Innovation & Research) and lower-level program/team
  names (Right of Way, Transmission System Support, GIS, MDM). I modeled the
  former as `sub_agency` and the latter as `office` or `component`.
- TVA's Power Operations (`PO`, already in the seed) is the right parent for
  the operational fleet groups. Per Don Moul's COO scope, PO covers:
  Generation (coal/gas/hydro), Nuclear, Transmission & Power Supply, and
  Generation Projects & Fleet Services/Strategy. I attached all of those as
  offices under `["TVA","PO"]`.
- River Management, Safety & Shared Services, Supply Chain, Enterprise
  Planning, Enterprise Analytics & Innovation, Innovation & Research, and
  Economic Development are TVA-wide — added as `sub_agency` directly under TVA.
- "External Communications" → aliased to existing TVA/ER (External Relations).
- "Riverfleet Management Services" and "River Management" are likely the same
  org under different names; I added both with cross-aliases and flagged for
  the integrator to reconcile.

## Multi-bureau FTC strings

`BC/BCP/OGC` and `BE/BC/OCIO` are slash-delimited multi-bureau strings.
Decision = `split_multi_bureau`. Two new FTC children need adding to the seed:
**OGC** (Office of General Counsel) and **BE** (Bureau of Economics). After
that, the integrator should map each composite string to its first/lead bureau.

## EPA

Only AO, Region 1, and Region 8 are unmapped. AO is just a different
abbreviation for the existing OFA node — added as alias. Regions are not in
the seed at all; added R1 and R8 as `sub_agency`. Integrator may want to
backfill R2–R10 for completeness.

## CFTC

CFTC has no children in seed today. Added the three operating divisions
present in this slice (DOD, DCR, MPD) as `sub_agency`. Other CFTC divisions
(DMO, DOE, OGC, OCDO) exist but didn't appear in the unmapped list.

## NCUA

Only `N/A` appeared — `generic_skip`.

## Decision counts

- add_to_seed: 25 (TVA: 19, EPA: 2, CFTC: 3, FTC: 0 in this round — see split note)
- alias_existing: 2 (TVA External Communications → ER; EPA AO → OFA)
- split_multi_bureau: 2 (FTC BC/BCP/OGC, FTC BE/BC/OCIO)
- generic_skip: 1 (NCUA N/A)
- unclear: 0

## Open questions for integration step

1. River Management vs. Riverfleet Management Services — likely the same
   organization. Recommend integrator merge into one canonical node.
2. Workforce Development — placed at TVA top level; could equally attach
   under Economic Development (where the Workforce Invest program lives).
3. FTC BE and OGC need to be added to the seed before the multi-bureau
   strings can be mapped to a primary bureau.
