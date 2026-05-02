# Unmapped-research integration report

- Sources: agent1_tva, agent2_science, agent3_civil, agent4_health, agent5_regulators
- Total proposed entries: 142

## Decision counts

- `add_to_seed`: 108 processed → **106 new nodes added**, 2 aliases applied to existing nodes
- `alias_existing`: 7 processed → 0 successful
- `split_multi_bureau`: 23 (handled by backfill multi-split, not by seed)
- `generic_skip`: 3 ignored by design
- `unclear`: 1 flagged for human review

## Duplicate-abbreviation merges

These entries had a sibling with the same abbreviation already in the parent. Aliases from the new entry were promoted onto the existing node.

- EPA > EPA > R8
- EPA > EPA > R1

## Skipped (parent path not found)

- TVA | bureau_component=`External Communications` | parent_path=`` | alias target not found
- EPA | bureau_component=`AO` | parent_path=`` | alias target not found
- EPA | bureau_component=`AO` | parent_path=`` | alias target not found
- DOJ | bureau_component=`Department of Justice / USTP` | parent_path=`` | alias target not found
- Treasury | bureau_component=`United States Mint (USM)` | parent_path=`` | alias target not found
- VA | bureau_component=`Office of the Deputy Secretary of VA` | parent_path=`` | alias target not found
- FDIC | bureau_component=`Legal Division` | parent_path=`` | alias target not found

## Unclear (needs human review)

- DOT > `OIE` (occurrence_count=0): OIE inside DOT multi-bureau strings. Likely 'Office of Intelligence, Security, and Emergency Response' or 'Office of Investment and Innovation' but no authoritative source confirmed in 2 searches. Flag for human review.

## Multi-bureau splits (backfill handles)

- FTC > `BC/BCP/OGC` → Multi-bureau string. BC + BCP already in seed. Need to add OGC (Office of General Counsel) under FTC. Integrator should map this string to the lead bureau (likely BC since it's listed first) and add OGC to seed for future.
- FTC > `BE/BC/OCIO` → Multi-bureau string. BC and OCIO already in seed. Need to add Bureau of Economics (BE) under FTC. Integrator: add BE then map this string to BE (lead bureau).
- NSF > `TIP & OCIO` → Compound string: TIP (Directorate for Technology, Innovation and Partnerships) AND OCIO (already in seed). Split into two: (1) TIP - directorate, must be added as sub_agency under NSF (see TIP additions). (2) OCIO - already in seed under NSF as office.
- USDA > `Research, Education and Economics; Farm Production and Conservation` → Compound string naming TWO mission areas; both already in seed: 'Research, Education, and Economics' (REE) and 'Farm Production and Conservation' (FPAC). No new entries needed; integrator should map the use case to both or to whichever is primary.
- DOT > `CAIO, NETT` → Constituents: CAIO (in seed), NETT (in seed). Both already in DOT seed; split into two attributions.
- DOT > `CAIO, HASS, Volpe` → Constituents: CAIO (in seed), HASS (NEW: Highly Automated Systems Safety Center of Excellence; needs add_to_seed under DOT as office with abbr 'HASS COE'), Volpe (in seed). After HASS COE is added, this string can be split.
- DOT > `CAIO, Volpe, OST-R` → Constituents: CAIO (in seed), Volpe (in seed), OST-R (NEW: Office of the Assistant Secretary for Research and Technology, office under DOT).
- DOT > `OIE, CAIO, OST-R, OCIO` → Constituents: OIE (UNCLEAR - DOT 'Office of Intelligence and Security' or similar; flag for review), CAIO (in seed), OST-R (NEW), OCIO (NEW: DOT Office of the Chief Information Officer).
- DOT > `CAIO, FAA, OST-R, Volpe, OCIO` → Constituents: CAIO, FAA, Volpe (all in seed); OST-R, OCIO (NEW).
- DOT > `CAIO, OST-M, OCIO, OIE` → Constituents: CAIO (in seed); OST-M, OCIO, OIE (NEW). OIE remains UNCLEAR.
- DOT > `CAIO, OCIO, OST-P, OST-M, NETT` → Constituents: CAIO, NETT (in seed); OCIO, OST-P, OST-M (NEW).
- DOT > `CAIO, OST-M, FHWA, OCIO` → Constituents: CAIO, FHWA (in seed); OST-M, OCIO (NEW).
- DOT > `CAIO, OST-R, OCIO` → Constituents: CAIO (in seed); OST-R, OCIO (NEW).
- DOT > `CAIO, OST-P, OCIO, OST-R` → Constituents: CAIO (in seed); OST-P, OST-R, OCIO (NEW).
- ED > `Office of Migrant Education, Office of Elementary and Secondary Education` → Constituents: OME (NEW: Office of Migrant Education, office under ED/OESE) and OESE (in seed).
- DOL > `OWCP||VETS||WHD` → Constituents: OWCP, VETS, WHD - all already in DOL seed.
- DOL > `EBSA || OHR` → Constituents: EBSA, OHR - both already in DOL seed.
- DOL > `CEO - WB` → Constituents: CEO (NEW: Chief Evaluation Office, office under DOL/OASP) and WB (NEW: Women's Bureau, sub_agency under DOL). Both not in seed.
- DOL > `CEO-ILAB` → Constituents: CEO (NEW: Chief Evaluation Office) and ILAB (NEW: Bureau of International Labor Affairs, sub_agency under DOL). Both not in seed.
- FDIC > `Division of Administration and Office of Inspector General` → Multi-bureau string. Both constituents already in seed: FDIC/DOA (Division of Administration) and FDIC/OIG. Mapper should split on ' and '.
- FDIC > `Legal Division and Office of Inspector General` → Multi-bureau string. Constituents: FDIC Legal Division (alias for OGC) and FDIC/OIG. After Legal Division alias is added (separate entry), this can be split.
- FDIC > `Office of Communications, Division of Complex Institution Supervision & Resolution, Legal Division, Division of Risk Management Supervision` → Four-way multi-bureau string. Constituents: Office of Communications (NOT in seed -- see separate add_to_seed entry below for OCOM), CISR (in seed), Legal Division (alias for OGC), RMS (in seed). Split on commas after adding OCOM.
- SEC > `Division of Enforcement (ENF); Division of Economic and Risk Analysis (DERA)` → Multi-bureau string. Both constituents in seed: SEC/ENF and SEC/DERA. Mapper should split on '; '.
