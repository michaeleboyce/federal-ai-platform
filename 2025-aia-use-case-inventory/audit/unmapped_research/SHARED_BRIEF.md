# Shared brief — unmapped-bureau research agents

## Why this exists

The current federal-organizations seed maps 94.8% of use cases to a sub-agency.
The remaining 122 distinct `bureau_component` strings sit in
`audit/unmapped_bureaus.csv`. Most are real entities the seed missed; some are
multi-bureau strings or generic "N/A" values that shouldn't be added. Your job
is to research the ones in your slice, confirm what they are, decide where
they belong in the hierarchy, and emit a structured proposed-addition file.

## Where to look

- `audit/unmapped_bureaus.csv` — full unmapped list. Columns:
  `agency, bureau_component, occurrence_count, sample_use_case_ids`. Filter to
  the parent agencies in your slice.
- `data/federal_hierarchy_seed.py` — the existing seed tree (Python literal).
  Read it to see what's already there for your parents and to learn the data
  shape your additions need to match.
- `data/federal_ai_inventory_2025.db` (read-only). Useful for spot-checking
  what a use case actually is:
  ```
  SELECT u.use_case_name, u.problem_statement, u.system_name, u.vendor_name
    FROM use_cases u JOIN agencies a ON a.id = u.agency_id
   WHERE a.abbreviation = ? AND u.bureau_component = ?
   LIMIT 5;
  ```

## Decision rules

For each unmapped bureau, choose ONE of:

1. **`add_to_seed`** — real org missing from the seed. Provide the new node and
   where it attaches in the hierarchy (parent path).
2. **`alias_existing`** — same as an existing seed entry under a different
   name; provide the existing canonical slug + the alias to add.
3. **`split_multi_bureau`** — the string names two or more bureaus. List them
   separately if all already exist; otherwise mark for human review.
4. **`generic_skip`** — uninformative ("N/A", "Human Resources" without a
   parent qualifier, internal shared-services org codes that aren't analyst-
   facing). Don't add.
5. **`unclear`** — couldn't confirm via web search; flag for human review.

## Web search

Use search to confirm each candidate. Good queries:
- `"<bureau name>" "<parent agency>" .gov`
- `<parent agency> "<bureau abbreviation>" sub-agency`
- For office codes: `<agency> org chart "<code>"`

Aim for ≤2 searches per bureau. Record every search.

## Hierarchy levels

Use the same enum as the seed: `department` | `independent` | `sub_agency` |
`office` | `component`. If a bureau is a directorate, division, or major
office (e.g., NSF directorates BIO/ENG/CISE), use `sub_agency`. If it's a
narrower office under a sub_agency (e.g., NSF/BIO/IOS), use `office`. You may
introduce intermediate levels when the existing parent path is too shallow —
for example, if NSF's BIO directorate isn't in the seed, you'd add BIO as a
sub_agency under NSF and IOS as an office under NSF/BIO.

## Output schema

Write three files into your output directory:

1. **`proposed_additions.json`** — JSON array. One entry per unmapped bureau
   you handled (any decision type). Schema:
   ```json
   {
     "agency": "DHS",
     "bureau_component": "CWMD",
     "occurrence_count": 1,
     "decision": "add_to_seed | alias_existing | split_multi_bureau | generic_skip | unclear",
     "parent_path": ["DHS"],
     "name": "Countering Weapons of Mass Destruction Office",
     "abbreviation": "CWMD",
     "level": "sub_agency",
     "aliases": ["CWMD"],
     "evidence_url": "https://...",
     "evidence_quote": "...",
     "notes": "..."
   }
   ```
   - `parent_path` is an array of abbreviations from root to immediate parent
     (e.g., `["NSF"]` for an NSF directorate, `["NSF", "BIO"]` for an office
     under BIO). Top-level agencies use a single-element array.
   - For `alias_existing`: leave name/level/parent_path empty, set `aliases` to
     the new alias(es) and `notes` to the existing slug to attach to.
   - For `split_multi_bureau`: set `notes` listing the constituent bureaus.
   - For `generic_skip` / `unclear`: just decision + agency + bureau_component
     + notes (everything else can be empty).

2. **`searches.csv`** — every web search you ran. Columns: `agency,
   bureau_component, query, top_url, found_useful, conclusion`.

3. **`notes.md`** — short methodology note + any patterns you saw (e.g.,
   "TVA's bureau strings are program names, not formal sub-agencies — those
   should mostly be office level"). ≤300 words.

## Constraints

- Do NOT modify the DB. Do NOT modify the seed file directly. Do NOT modify
  `audit/unmapped_bureaus.csv`. Output files only.
- Do NOT enter plan mode. Your harness mode is `acceptEdits`. Write the
  deliverable files directly.
- Time budget: ~45 minutes per agent.
- Final reply ≤200 words: count of decisions by category and any blocking
  ambiguities the integration step needs to resolve.
