# Round-3 Coding Sub-Agency Audit — Methodology and Findings

## Method

I walked all 96 sub-agencies in `_foundation/sub_agencies.json`. For each I
read `subtree_coding_count`, `named_tools`, and the sample use cases.
For sub-agencies with `subtree_coding_count > 0` I queried the DB
(`use_case_tags.is_coding_tool = 1` joined to `use_cases` by descendant
`organization_id` / `bureau_organization_id`) to verify each tagged row
was actually a coding-specific deployment, not a false positive.

Cross-referenced parent-agency ratings in `audit/retag/coding/by_agency.md`
to apply charter decision rule 1 (Inherited when parent is enterprise and
covers the sub-agency).

Web searches were used sparingly (11 total) — almost all came back with
no useful new information, confirming the foundation-pack signal as the
right primary evidence.

## Generic-LLM rule application

The strict generic-LLM rule mattered most for these sub-agencies:

- **DOE labs (LANL, INL, LLNL, BNL, FNAL, NREL, ANL, NR, EE, NETL).** Many
  have ChatGPT Enterprise / M365 Copilot / Claude / Azure OpenAI / Amazon
  Q in `named_tools` and the underlying narratives mention "code
  generation" as one capability. Under the strict rule these are NOT
  coding tools — they're general-LLM access. Result: many DOE labs
  drop to "None reported" even though the foundation pack might
  superficially suggest coding capability.
- **DHS USCIS (Claude listed)** — Claude is general LLM, not coding.
- **NASA centers (ARC, JSC, LaRC, MSFC, JPL, GRC).** All have ChatGPT or
  Azure OpenAI in `named_tools` but no coding-specific deployment.
  Even GSFC's coding entries are custom internal builds, not generic-LLM
  reuse. JPL's absence is the most surprising.
- **DOE-LM** is the carveout case where I let a generic LLM (Gemini)
  count: the row's primary purpose is explicitly "scripting" — coding-
  specific work as primary purpose, per the charter's narrow exception.

## Surprises (top 5)

1. **NASA JPL has zero coding-tool entries.** JPL writes flight software
   for missions; the absence of any coding-assistant pilot in the 2025
   inventory is striking. Likely a reporting gap — recommend caveat in
   the article.
2. **NOAA is the strongest sub-agency coding shop.** Six coding use
   cases naming GitHub Copilot, Amazon Q Developer, and Gemini Code
   Assist — broader vendor mix than any other federal sub-agency.
3. **SSA OCIO is the only Windsurf customer in federal government.** Plus
   AveriSource and IBM watsonx Code Assistant — the most diverse coding
   stack at office level.
4. **VA's "Enterprise" rating is really va-oit's deal.** VHA (253 use
   cases) and VBA have zero own coding entries. The article should
   present the VA rating as OIT-centric, not VA-wide.
5. **HHS sprawl.** Five different HHS sub-agencies + offices each have
   their own coding pilot (NIH, CDC, FDA, CMS-OIT, CMS-OC, HRSA, AHRQ).
   None reach enterprise. HHS coding posture really is bureau-level.

## Where the parent rating may need a caveat

- **VA.** Round-1 calls VA "Enterprise/Broad," which is accurate, but it
  is OIT-bound. VHA's massive use-case inventory has no coding tools.
  Recommend the article phrase this as "VA OIT (~7000 staff)" rather
  than "VA-wide."
- **NASA.** Round-1 calls NASA "Limited/Pilot," fair given GSFC center-
  level pilots. The sub-agency rollup confirms only GSFC has coding
  entries; six other centers (including JPL) have zero. NASA's coding
  posture is essentially Goddard-only.
- **DOE.** Round-1's "Limited/Pilot (lab-scoped)" is exactly right.
  Sub-agency rollup: only 6 of 17 DOE labs/offices in the foundation
  pack have any coding-tool entry, and they use 4 different products
  (GitHub Copilot at PNNL/Hanford/SLAC, Tabnine at SRS, custom at
  ORNL, Gemini scripting at LM). This fragmentation is the headline.
- **DOJ.** All seven DOJ sub-agencies/offices except CIV have zero own
  coding entries. The "Department-wide GitHub Copilot" claim from
  inventory row 8713 is unverified publicly. If true, the inheritance
  is real; if not, several DOJ rows would drop to "None reported."
  This remains the largest single uncertainty in the federal coding
  picture.

## Recommendations for the article

1. **Lead with bureau-level fragmentation, not agency totals.** NOAA, VA
   OIT, SBA OCIO, SSA OCIO, IRS, GSFC are the real units of analysis.
2. **Call out the generic-LLM-≠-coding distinction explicitly.** Many
   labs and centers list M365 Copilot / ChatGPT and the casual reader
   would assume "they have coding tools." The strict rule excludes them,
   and that exclusion meaningfully changes the picture (especially for
   DOE labs and NASA centers).
3. **Flag the autocoder confusion.** BLS occupation autocoders, DOJ
   MACO/OTAC autocoders, FAA SDRS JASC code picker — none are coding
   tools despite the word "code." This trips up automated tagging.
4. **DOJ Department-wide claim needs reporter follow-up.** Inventory
   row says department-wide GitHub Copilot but no public corroboration.
   Either the largest under-reported deployment in federal government
   or an aspirational filing.
5. **Reporting gaps to flag:** NIST, NASA JPL, USDA NRE, FAA — all
   large dev shops with zero coding-tool entries. Likely reporting
   completeness issues rather than genuine absence.

## Counts

- Total sub-agencies rated: 96
- Enterprise/Broad: 4 (doc-noaa, sba-ocio, ssa-ocio, va-oit)
- Limited/Pilot: 27
- Inherited: 11 (mostly DOJ bureaus + VA non-OIT + FDIC DRR)
- None reported: 54
