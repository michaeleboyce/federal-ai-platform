# WS3 alias-coverage audit — notes

## Decision counts

| Decision | Count |
|---|---:|
| `add_alias` | 12 |
| `false_positive` | 17 |
| `unclear` | 2 |
| **Total** | **31** |

(31 decisions across 30 input products — Azure AI Foundry, Synapse, Exchange
Server each get both an `add_alias` and a paired `false_positive` explaining
the bare-name variant rejected.)

## Methodology

The input CSV's `sample_unlinked_mentions` column was empty for every row,
so I tested each candidate alias against the live `use_cases` table directly:

```sql
SELECT use_case_name, system_name FROM use_cases
WHERE LOWER(<field>) LIKE '%<bare-alias>%' LIMIT N;
```

For each bare-name candidate I asked four questions:
1. ≥4 chars? (filters "VS", "MS")
2. Common English word? (filters "Edge", "Project", "Discovery", "Exchange")
3. Collision with another product's alias_text? (checked
   `product_aliases` for case-insensitive matches)
4. Does word-boundary-checked substring matching produce false positives
   in the actual narrative? (the killer — caught "Sentinel" colliding
   with ESA Sentinel satellites + FTC Sentinel Network Services,
   "Outlook" with hurricane outlooks, "Foundry" with Palantir Foundry,
   "Dynamics" with Boston Dynamics)

## Surprising findings

- **"Microsoft 365" has zero aliases** — not even its own canonical name.
  Product 7767 (the Office productivity suite) was literally unfindable
  by the linker. Added as the most-impactful single recommendation.
- **The word-boundary check is doing real work.** Many bare names that
  *look* dangerous (Viva, Skype, OneDrive) are actually safe once you
  confirm in-the-wild use; their substring "hits" only appear inside
  longer alphanumeric runs ("survival" contains "viva") which the
  boundary check rejects.
- **"Sentinel" was the most surprising false positive.** FTC operates a
  "Sentinel Network Services" system used in 6 distinct AI use cases
  (chatbot, word cloud, graph analytics, etc.). NOAA/USGS reference
  the ESA Sentinel satellite constellation in remote-sensing use
  cases. Bare "Sentinel" would have polluted the Microsoft Sentinel
  product with ~25 false-positive edges.
- **"AI Foundry" vs "Foundry"** — Palantir Foundry is a known catalog
  product family (NIH IDAP is on Palantir). The 2-token "AI Foundry"
  is distinctive enough to capture Azure AI Foundry without colliding.
- **"Microsoft Search in Bing"** turned out riskier than expected — a
  row named "Microsoft Bing Service" exists (75868) and may or may not
  be the same product. Flagged as a follow-up rather than blindly
  aliasing "Bing".

## Catalog-level concerns flagged for reviewer

- Product 7768 `Microsoft 365 Apps for Enterprise` has its likely alias
  ("Microsoft 365 apps", case-insensitive) currently attached to the
  Copilot product (7763). Either reassign or accept the overlap as a
  Copilot-bundle reflection. Flagged `unclear`.
- The Microsoft Azure family is still very flat: `Microsoft Azure
  Platform` has only its canonical alias, and most child products
  (Synapse, Data Factory, Speech, AI Foundry) lack parent linkage.
  WS2's hierarchy-gap workstream should pick this up.

## What I did NOT touch

- Did not propose `Azure` as a bare alias for `Microsoft Azure
  Platform`. Per charter and confirmed via DB: there are ~10
  Azure-prefixed sub-products in catalog (Azure OpenAI, Azure AI
  Document Intelligence, Azure Speech, Azure Synapse Analytics, Azure
  Data Factory, Azure AI Translator, Azure AI Foundry, …). Bare
  "Azure" would shadow all of them via longest-match precedence.
- Did not propose `Copilot` (collides with M365 Copilot, GitHub
  Copilot, Copilot Studio, Copilot for Security).
- Did not propose `Defender`, `Teams`, or `Purview` — already aliased.

## Expected impact

Conservatively, 12 added aliases should pick up:
- ~5-10 additional `Microsoft 365` edges (currently the product has 6
  linked but zero alias coverage means it's only finding edges via the
  exact 13-char canonical match elsewhere)
- ~2-5 edges from each of the well-targeted sub-product aliases
  (`Power BI`, `PowerPoint`, `OneDrive`, `OneNote`, `Skype`, `SSMS`,
  `Synapse Analytics`, `AI Foundry`, `Azure Quantum Elements`,
  `Exchange Server`, `Viva`).

Estimated additional linkage: 30-60 use_case_products edges. Modest but
the highest-precision additions surfaced by this candidate list.
