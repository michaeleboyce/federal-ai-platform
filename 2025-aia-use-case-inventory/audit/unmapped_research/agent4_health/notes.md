# Agent 4 (HHS / SSA / HUD / VA / SBA / Treasury) — research notes

## Methodology

Filtered `audit/unmapped_bureaus.csv` to the six parents in scope (19 rows).
Cross-referenced each row against `data/federal_hierarchy_seed.py` and the
distinct `bureau_component` values already on use-case rows in the DB. Used
two confirmatory web searches (ASTP/ONC and SBA Office of Advocacy) for the
two highest-impact "is this really its own thing" calls; relied on prior
knowledge of the federal hierarchy for standard CFO/CHCO/communications
offices and bureau strings whose mapping is unambiguous.

## Patterns observed

- **HHS uses `HHS/<segment>` as a flat namespace.** Every HHS row strips the
  leading `HHS/` and treats the next segment as the canonical sub-agency
  abbreviation. The seed already covers most of these (CMS, FDA, AHRQ, etc.);
  the three new ones — `ASTP`, `OCIO`, `OCR` — slot directly under HHS at
  sub_agency / office level. ASTP is the renamed ONC and is the HHS-wide AI
  policy office; worth adding ONC as an alias since older inventories use it.
  HHS OCR shares its abbreviation with ED OCR — disambiguated by parent path.

- **SSA's OCIO is fractal.** Bureau strings follow
  `Chief Information Officer, <subdivision>` (e.g., Disability Information
  Systems, Digital Customer Solutions, System Operations and Hardware
  Engineering). The cleanest fix is to introduce an `office`-level layer
  under `SSA/OCIO` for each subdivision, rather than aliasing them all to
  OCIO and losing the distinction in the data. Bare "Human Resources" on SSA
  rows means SSA OHR — canonicalized as such. "Law and Policy, Disability
  Policy" mirrors the OCIO pattern for the Office of Disability Policy under
  ORDP.

- **HUD's seed was extremely shallow** — only OCIO and OIG. Added Ginnie Mae
  (semi-independent corp, sub_agency), Office of Housing (largest program
  office, runs FHA, sub_agency), plus the standard OCFO/OPA/OCHCO offices.

- **VA and Treasury were single-row alias fixes.** VA's "Office of the
  Deputy Secretary of VA" is the same as the existing ODS entry — alias.
  Treasury's "United States Mint (USM)" is the existing Mint sub_agency —
  alias. Treasury's "General Counsel" is its own OGC office and is added.

- **SBA bureau strings use `CODE: Full Name` format.** Three of the four
  unmapped SBA rows are standard CFO/Advocacy/OCPL offices. Office of
  Advocacy gets sub_agency level because it is statutorily independent
  within SBA and led by a presidentially appointed Chief Counsel.

## Constraints / open questions

- For `add_to_seed` decisions where I relied on prior knowledge rather than
  a fresh search, I'm confident but the integration step may want to spot
  check the SSA/OCIO sub-org names against the latest SSA org chart — those
  have been reorganized periodically.
- All decisions in this slice are `add_to_seed` (17) or `alias_existing` (2).
  No `generic_skip`, `split_multi_bureau`, or `unclear`.
