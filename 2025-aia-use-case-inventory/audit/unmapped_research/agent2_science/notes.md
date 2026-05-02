# Agent 2 (Science slice: NSF, DOE, USDA, EPA) — methodology and patterns

## Methodology

For each unmapped row I (1) consulted the existing seed to see what was
already mapped under the parent agency, (2) ran a single confirming web
search per distinct entity (≤2 searches per row), and (3) mapped to one of
the five decision types in the shared brief. I biased toward `add_to_seed`
when the entity has its own .gov landing page and a clear parent path.

## Slice-specific patterns

**NSF (`DIR/DIV` convention).** The unmapped strings follow a strict
directorate/division-or-office pattern (e.g., `BIO/IOS`, `ENG/CBET`,
`SBE/NCSES`, `EDU/DRL`, `OIA/EAC`). The seed had only three NSF children
(OIA, OCIO, OIRM), so I introduced six intermediate directorates as
`sub_agency` nodes (BIO, ENG, CISE, EDU, SBE, TIP) before attaching the
narrower offices/divisions as `office` under them. I did NOT add MPS, GEO,
EHR (renamed EDU), OISE — they did not appear in the unmapped slice and the
seed prefers minimalism. EDU carries `EHR` as alias since the directorate
was renamed in 2023. CISE/OAD = directorate front office (Office of the
Assistant Director); kept as `office` under CISE.

**DOE HQ codes.** The DOE unmapped values use a `<CODE> HQ - <Name> (<CODE>)`
template. Most resolve to genuine DOE offices that report to a Deputy
Secretary or Under Secretary — added as `sub_agency` (EHSS, PM, GDO, HC,
SWPA, SEPA). The single exception is `IM-60`, which is an internal sub-unit
within OCIO/IM (Deputy CIO for Enterprise Operations & Shared Services) —
not analyst-facing per the brief, so `generic_skip`. PA (Public Affairs) is
a small HQ comms shop, marked `office` rather than `sub_agency`.

**USDA mission areas.** The compound string
"Research, Education and Economics; Farm Production and Conservation" maps
cleanly to two existing seed entries (REE and FPAC) via `split_multi_bureau`.
"Food, Nutrition, and Consumer Services" (FNCS) is a mission-area umbrella
over the existing FNS — added as `sub_agency`; integrator may want to
re-parent FNS under FNCS. Departmental Administration (DA) added as
`sub_agency` to provide a parent for OSSP and OHS staff offices.

**EPA.** `Region 8` and `Region 1` are real geographic regional offices —
added as `sub_agency` (`R8`, `R1`). Recommend integrator backfill R2–R10
for symmetry. `AO` is the canonical EPA abbreviation for the existing
"Office of the Administrator" (which the seed records under abbreviation
`OFA`); resolved as `alias_existing` and flagged that the canonical
abbreviation should likely flip from OFA to AO.

## Synthetic intermediate rows

Six entries with `bureau_component` of the form `__directorate_X__` and
`occurrence_count: 0` are synthetic: they are the parent directorates that
must exist before the child unmapped rows can attach. The integrator should
treat these as plain `add_to_seed` actions and ignore the synthetic
bureau_component string.
