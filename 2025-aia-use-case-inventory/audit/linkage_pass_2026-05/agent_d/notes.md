# Agent D — hierarchy edge proposals

## Summary

| Parent family | Edges proposed | Confidence mix |
|---|---:|---|
| Microsoft Azure Platform | 2 | high, high |
| Palantir Federal Cloud Service | 2 | medium, medium |
| LexisNexis | 1 | medium |
| LexisNexis Risk Solutions | 1 | high |
| IBM Watson | 1 | medium |
| **Total** | **7** | 3 high / 4 medium / 0 low |

All seven proposals are appends; none conflict with the existing `remove`
rows in `data/product_hierarchy_edges.csv` (GitHub Copilot, NotebookLM).
No proposed chain exceeds depth 3 (e.g., `idiCORE -> LexisNexis Risk
Solutions -> LexisNexis` is depth 3), well under the 5-hop cap.

## Methodology

Walked the full 316-row snapshot, treating any product whose
`parent_canonical_name` is empty as a candidate. Filtered to products
where:

1. The candidate parent already exists in the catalog AND is itself
   either a clear platform/family root or already used as a parent.
2. The child is a real technical sub-product, component, or
   subscription-bundled feature of that parent (not just same brand).
3. There is precedent in the existing 41-edge CSV for the same family.

## Catalog observations (not edges, but flagged)

These are catalog-level oddities I noticed but did NOT act on — they're
out of scope for hierarchy edges:

1. **`Microsoft 365` (5323) has product_type `coding_assistant`**, as
   does `Microsoft 365 Apps for Enterprise` (5324). M365 itself is a
   productivity suite; this looks like inherited mis-typing. Worth a
   separate catalog cleanup pass.
2. **`Microsoft 365 Copilot` (4981) `product_type` is `general_llm` /
   `is_frontier_llm=1`**. M365 Copilot is a UX layer on top of GPT-4;
   classifying the wrapper as a frontier LLM is arguable.
3. **`Snowflake Cortex`, `Microsoft 365 Apps for Enterprise`, and
   `Microsoft HoloLens`** all have `edge_count=0`. They may be
   over-specified — i.e. nothing actually links to them yet. Not a
   hierarchy issue, just dead-weight catalog entries worth reviewing.
4. **`Adobe Creative Cloud Suite` `product_type` is `productivity`**
   while its children Photoshop and Firefly are `computer_vision`. Not
   wrong, just inconsistent typing across the family.
5. **No AWS-platform root**: AWS Bedrock, Amazon Q, AWS Kendra,
   Rekognition, Textract, Transcribe, Translate, Lex, and Amazon
   Connect all sit as top-level entries with no shared AWS-platform
   parent (cf. the explicit Microsoft Azure Platform root). If a future
   pass wants to mirror the Azure pattern, an `Amazon Web Services`
   parent could be created and these reparented under it. I did NOT
   propose this here because it requires adding a new catalog row,
   which is out of scope for the `add_hierarchy_edge` decision type.
6. **No Thomson Reuters parent**: Westlaw AI, CoCounsel, ProLaw, and
   Thomson Reuters CLEAR could all be parented under a "Thomson
   Reuters" platform row if one existed. Same out-of-scope reason as
   #5.
7. **Microsoft Dynamics 365 and Microsoft Edge / Skype / ScreenSketch**
   are Microsoft products NOT bundled in M365 SKUs. Deliberately left
   unparented.
8. **NotebookLM and GitHub Copilot** were skipped per the explicit
   `remove` precedents in the existing CSV.

## What I did not propose and why

- `Google Translate`, `Google Lens`, `Google Chrome Generative AI`,
  `reCAPTCHA`, `Google Maps`, `Google Pixel`, `AlphaFold` — all
  Google-brand but technically separate product lines from GCP and
  Workspace; no platform inheritance.
- `Microsoft Edge`, `Microsoft Skype`, `Microsoft ScreenSketch`,
  `Microsoft Dynamics 365`, `Microsoft HoloLens`, `SQL Server
  Management Studio`, `Nuance Dragon` — separately licensed / not part
  of M365 or Azure inheritance.
- All AWS services — no AWS-platform root to attach to.
- `Slack`, `Tableau` — Salesforce-owned but acquired-brand product
  lines, parenting under Salesforce Einstein would be wrong.
