# Agent 5 — Regulators slice notes (SEC, FDIC, FRB, FHFA, OPM)

## Methodology

1. Filtered `audit/unmapped_bureaus.csv` to the five parents in scope (FTC handled by another agent, excluded).
2. Cross-referenced each unmapped string against the existing seed (`data/federal_hierarchy_seed.py`, lines 447-530).
3. Spot-checked use cases via SQLite to disambiguate ambiguous abbreviations (e.g., confirming OCOO/OGC/DBR/OCFO all belong to FHFA, not FDIC or FRB).
4. Ran web searches only for non-obvious entities (FDIC CIOO, SEC EBO, SEC FinHub, FRB Office of the Secretary). Standard offices like OCIO, OGC, OIG, OS, OHR were treated as obvious from agency org charts.

## Decision counts

- `add_to_seed`: 16 (incl. 1 synthetic add for FDIC/OCOM needed to resolve a multi-bureau split)
- `alias_existing`: 1 (FDIC "Legal Division" -> FDIC/OGC)
- `split_multi_bureau`: 3 (one FDIC two-way, one FDIC four-way, one SEC two-way)
- `generic_skip`: 1 (OPM "Human Resources")
- `unclear`: 0

## Patterns observed

- **Regulators heavily use bare abbreviations**: FHFA rows arrived as `OGC`, `OCOO`, `OCFO`, `DBR` with no expansion. Resolved via spot-checking the use cases (all clearly FHFA) and matching to FHFA's published org structure.
- **Parenthetical-abbreviation form**: SEC consistently formats as `Long Name (ABBR)` (EBO, OHR, FinHub, OCOO, OS). Aliases include both the parenthetical form and the bare abbreviation so future ingest variants match.
- **Misspelling preserved**: SEC FinHub row contains "Innocation" rather than "Innovation". Added the misspelled form as an alias so historical rows map without DB edits.
- **"Legal Division" at FDIC = OGC**: FDIC labels its OGC as "Legal Division" in some contexts. Recommend alias rather than a new node.
- **Multi-bureau strings use varied separators**: ` and ` (FDIC), `; ` (SEC), `, ` (FDIC four-way). Mapper integration needs all three split rules.
- **CIOO vs DIT at FDIC**: Distinct entities. DIT is already in seed; CIOO is the broader IT umbrella that contains DIT, OCISO, and the CDO Staff. Both should coexist as offices.

## Blocking ambiguity for integration

- For the FDIC four-way string, the constituent "Office of Communications" was not present as a standalone unmapped row but is needed to split. I added it as a synthetic `add_to_seed` (occurrence_count 0) so the integration agent can map all four constituents cleanly.
