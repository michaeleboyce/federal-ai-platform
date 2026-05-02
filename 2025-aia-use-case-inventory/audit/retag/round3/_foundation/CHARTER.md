# Round-3 Charter — Sub-agency rollups

## Why this round

The round-1 `by_agency.md` rollups treat each cabinet department or
independent agency as a single tile. That hides the most important shape
of federal AI: it's bureau-level. CDC ≠ OASH within HHS. NASA Goddard ≠
the rest of NASA. PNNL ≠ NREL within DOE. The article needs to make these
distinctions, which means each topic rollup needs sub-agency rows under
the federated parents.

## Inputs you have

- `audit/retag/round3/_foundation/sub_agencies.json` — 96 sub-agencies
  meeting the use-case threshold. Each has the slug, parent agency,
  subtree counts, named tools, sample use cases, and a sub-agency-level
  maturity tier (computed from `org_ai_maturity`).
- `audit/retag/general_llm/by_agency.md` — round-1 + round-2 agency rollup
  with citations. Treat as authoritative for parent-agency-level claims.
- `audit/retag/coding/by_agency.md` — same, for coding tools.
- `audit/retag/data_analysis/by_agency.md` — same, for analytic platforms.
- The DB at `data/federal_ai_inventory_2025.db` — read-only; fall back to
  this only when the foundation pack lacks evidence.

## Rating scale (use the same scale your topic uses in round 1)

**General LLM:**
- **Enterprise** — sub-agency has a named, broadly-deployed FOUO/CUI LLM
  available to most/all of its workforce, OR is fully covered by the
  parent agency's enterprise rollout (e.g., FDA staff covered by HHS
  Anthropic Claude department-wide).
- **Broad** — significant deployment across the sub-agency but not
  agency-wide; or a federated mix of bureau-level systems.
- **Limited** — pilot, single-component, or narrow use only.
- **None reported** — no general LLM in the sub-agency's inventory or
  public materials.
- **Inherited** — sub-agency has no own deployment but the parent's
  agency-wide rollout (M365 Copilot, ChatGPT) covers staff. Use this
  sparingly — only when there's clear evidence the parent rollout
  reaches this bureau.

**Coding:**
- **Enterprise/Broad** — named coding-specific tool (GitHub Copilot,
  Amazon Q Developer, Gemini Code Assist, Tabnine, Cursor, Claude Code,
  AveriSource, etc.) deployed to most developers in this sub-agency.
- **Limited/Pilot** — coding tool in pilot or single-team use.
- **None reported** — no coding-specific tool in inventory or public
  materials.
- **APPLY THE GENERIC-LLM RULE**: M365 Copilot / ChatGPT / Claude /
  Gemini do NOT count as coding tools unless the sub-agency's narrative
  explicitly cites coding-specific work as the primary use.

**Data analysis:**
- **Strong** — sub-agency has a named analytic platform supporting AI/ML
  on agency data at scale, with broad analyst access.
- **Moderate** — one platform or limited rollout to specific teams.
- **Limited** — Power BI / Tableau / Excel only; no AI-on-data
  environment surfaced.
- **None reported** — nothing in inventory.

## Confidence

- **High** — ≥2 independent public sources or explicit subtree DB
  evidence (named system + use-case count + scope).
- **Medium** — DB subtree evidence + 1 weaker public source.
- **Low** — DB subtree evidence only, or single weak source.

## Decision rules

1. If the parent agency rollup is "Enterprise" with a department-wide
   deployment that explicitly names this sub-agency as covered, the sub-
   agency inherits that rating with confidence dropped one notch.
2. If the sub-agency has named systems in the foundation pack
   (`named_tools` list) that aren't covered by the parent's rollout, weight
   those toward an independent rating.
3. If the sub-agency's `subtree_enterprise_llm_count` is ≥3 OR
   subtree LLM count is ≥10, that's strong DB evidence for at least
   "Broad" on general_llm.
4. If `maturity_tier` from `org_ai_maturity` is "leading," the
   general_llm rating is at least "Broad" (the rubric requires
   has_enterprise_llm + has_coding + has_agentic + >50 use cases).
5. Don't overrate. If the foundation pack shows the sub-agency has 0
   coding tools and 0 named coding products, the coding rating is
   "None reported" or "Inherited" — never higher.
6. Web-search is for ambiguity only. Each search you run goes in
   `searches.csv` with the query, top URL, and conclusion. Most
   sub-agencies you can rate from the foundation pack alone.

## Output schema (CSV)

`sub_agency_rows.csv` columns:

```
parent_agency, sub_agency_slug, sub_agency_name, sub_agency_abbr, level,
subtree_use_cases, rating, key_systems, scope_or_users, confidence,
key_evidence, notes
```

- `parent_agency`: parent abbreviation (HHS, DHS, etc.)
- `sub_agency_slug`: e.g., `hhs-cdc`
- `key_systems`: pipe-separated list of named tools/systems for this
  sub-agency (or "—" for inherited)
- `scope_or_users`: rough estimate of who has access (e.g., "all FDA
  staff via HHS Anthropic deal", "GSFC researchers", "OFR division-only
  pilot")
- `key_evidence`: comma-separated list of either DB row IDs (`db_row_X`)
  or URLs

`searches.csv` columns:
`sub_agency_slug, topic, query, top_url, found_useful, conclusion`

`notes.md`: methodology, surprises, calls you weren't sure about, any
sub-agencies where the foundation pack misled you.

## Final summary (≤300 words at the end of your run)

- How many sub-agencies you rated, distribution of ratings.
- Top 5 sub-agencies that surprised you (positive or negative).
- Any sub-agencies where you'd recommend the parent rating be revised
  too (rare but happens — e.g., if NASA Goddard's posture is so
  different from the rest of NASA that the parent "Broad / Federated"
  needs a caveat).
