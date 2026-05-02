# Agent 3 (DOT, DOJ, ED, DOL) — Methodology & Patterns

## Approach
1. Filtered `unmapped_bureaus.csv` to the four parents.
2. Cross-referenced each candidate against the existing seed (`data/federal_hierarchy_seed.py`) to detect already-present entries before proposing additions.
3. Ran ≤2 web searches per cluster of related bureaus, batching where possible (e.g., one search covered all six DOJ codes).
4. For multi-bureau strings, listed every constituent. Where a constituent was missing from the seed, proposed it as its own `add_to_seed` entry so the splitter has a target to attach to.

## Patterns observed

### DOT — heavy multi-bureau strings
DOT use cases routinely list 3–5 contributors in `bureau_component`, almost always anchored on **CAIO** (Chief AI Officer) plus modal admins. The recurring "OST-R / OST-M / OST-P" pattern reflects the three Assistant Secretary offices under OST (Research/Tech, Administration, Transportation Policy). These should be added as `office`-level peers of the existing OST entry. **OIE** could not be resolved authoritatively in 2 searches and is flagged `unclear`.

### DOJ — slash-prefixed strings
DOJ uses `"Department of Justice / <ABBR>"` as the bureau string. All six new abbreviations resolved to real components per the DOJ FOIA Attachment B reference. Note that **OPR** (Office of Professional Responsibility) and **PRAO** (Professional Responsibility Advisory Office) are explicitly distinct components — both should be added separately. **USTP** is the same component already in seed as `UST` (U.S. Trustee Program) → alias only.

### ED — senior-leadership offices
The unmapped ED entries are all real top-level offices that the seed simply omitted (Under Secretary, Deputy Secretary, Communications & Outreach, Educational Technology). Two are sub-offices of existing seed entries: **GMPD** and **CAM** sit under **OFO**; **OME** sits under **OESE**. Used `parent_path` accordingly.

### DOL — pipe-delimited multi-bureau, plus CEO collaborations
"OWCP||VETS||WHD" and "EBSA || OHR" use a different delimiter (`||`) than DOT's comma — integration code should accept both. The "CEO - WB" / "CEO-ILAB" pattern is a Chief Evaluation Office collaboration with another bureau; both halves needed to be added (CEO, WB, ILAB).

## Blocking ambiguity
- **DOT OIE**: marked `unclear`. Sample use case IDs 8811, 8842 may help a human disambiguate.

## Counts (for integration step)
- `add_to_seed`: 23 (5 ED, 6 DOJ minus 1 alias = 5, 5 DOT new offices + HASS COE = 6, 4 DOL new offices)
- `alias_existing`: 1 (DOJ USTP → UST)
- `split_multi_bureau`: 13 (9 DOT + 1 ED + 2 DOL pipe + 2 DOL CEO-X)
- `unclear`: 1 (DOT OIE)
- `generic_skip`: 0
