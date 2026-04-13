# Check
`product_mapping_and_alias_quality`

# Method
- Compared every nonblank `cots_product_name` and `tool_product_name` in `use_case_tags` against the normalized product catalog (`products.canonical_name`) plus alias table (`product_aliases.alias_text`).
- Reviewed the remaining unmatched strings for compound labels, internal labels, and implementation notes that should not be treated as clean single-product aliases.
- Checked `product_deployment` and `product_feature` rows with blank product fields to find obvious product rows that lost their product label.

# Findings
- Coverage is decent but not complete: `cots_product_name` has `639` populated rows, of which `58` (`9.1%`) do not match any canonical product or alias; `tool_product_name` has `592` populated rows, of which `24` (`4.1%`) do not match.
- The catalog does not have alias collisions across different canonical products. The issue is missing coverage and over-broad canonicalization, not conflicting aliases.
- `Microsoft 365 Copilot` is acting as an overly broad bucket. `6` rows whose source text explicitly names `Microsoft Copilot for Security`, `Copilot Studio`, or `MS Copilot - Security & Privacy` were collapsed into that one product.
- `ServiceNow Now Assist` is also too coarse for several rows. `10` rows with source names like `ServiceNow Virtual Agent`, `ServiceNow Predictive Intelligence`, and `ServiceNow AI Search` were normalized to that same canonical product.
- There are `5` blank-product rows inside the explicit product-use categories (`product_deployment` / `product_feature`). These are the only clear blank-product misses in the audit and they are concentrated in DOJ, FERC, GPO, and SEC.
- Alias coverage is uneven: `AWS Textract`, `Adobe Photoshop`, `Airtable AI`, and `Wellsaid Labs` currently have no aliases even though they appear as product strings in the inventory. That is a catalog gap rather than a collision, but it reduces recall.

# Examples
- Composite or implementation-note strings that should not be treated as clean single-product aliases:
  - `FTC` `id=1710`: `Amazon Connect / Lex`
  - `FTC` `id=1711`: `AWS (Textract + Bedrock)`
  - `GSA` `id=1750`: `Elastic ML + SageMaker`
  - `NSF` `id=2683`: `Wellsaid Labs / ElevenLabs`
  - `DHS` `id=193`: `DHSChat (Azure OpenAI)`
  - `State` `id=2884`: `Microsoft Azure (custom bot)`
  - `SEC` `id=2775`: `SEARCH (internal LLM)`
- Over-broad canonical mappings:
  - `DOE` `id=513`: `Microsoft Copilot for Security` -> `Microsoft 365 Copilot`
  - `DOE` `id=516`, `id=740`, `id=790` and `ED` `id=1549` / `USDA` `id=3170`: `Copilot Studio` / `MS Copilot - Security & Privacy` -> `Microsoft 365 Copilot`
  - `DOE` `id=502`, `id=510`, `id=520`, `id=561`, `id=562`, `id=770`, `GSA` `id=1754`, `HHS` `id=1923`: `Virtual Agent`, `Predictive Intelligence`, and `AI Search` -> `ServiceNow Now Assist`
- Blank product fields on obvious product rows:
  - `DOJ` `id=1220`: `Lexis Nexis (People Search)`
  - `FERC` `id=1637`: `AI Enabled Assistant Legal Research`
  - `GPO` `id=1719` and `id=1721`: `Machine Learning (IT Ops)` and `DevOps`
  - `SEC` `id=2752`: `Mobile Phone Artificial Intelligence Features`
- A likely false-positive aliasing case:
  - `FCC` `id=3672`: generic time-management text was mapped to `Amazon Q Developer`, which looks more like a product-name match than a true product fit.

# Recommended follow-up
- Split internal platform labels from vendor products where a row names multiple systems or embeds implementation notes, instead of forcing them into a single canonical product.
- Tighten the `Microsoft 365 Copilot` and `ServiceNow Now Assist` alias rules so feature-level names do not get flattened into a broader canonical product unless that is intentional.
- Add aliases for straightforward missing products where the inventory uses clear single-product names, especially `AWS Textract`, `Adobe Photoshop`, `Airtable AI`, and `Wellsaid Labs`.
- Fill the `5` blank product fields in explicit product-use rows, or document why they are non-product features and should stay blank.
