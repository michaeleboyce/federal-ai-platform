# Source
TVA `use_cases` inventory: `TVA-2025-ai-inventory.csv`.

# Counts
- Source rows: 59
- Loaded DB rows: 59
- Unmatched / untagged rows: 0
- Raw parse check: 59 non-empty data rows, 0 blank rows, 5-column header preserved cleanly

# Findings
- The file loaded cleanly with no row-count drift or obvious parsing problems. The CSV header is simple and consistent, and the DB row count matches the source exactly.
- Tags are directionally reasonable overall. The mix of `custom_system` rows dominates, with a small set of product deployments for Copilot, GitHub Copilot, Westlaw, AWS Q, AWS Transcribe, and ArcGIS. That distribution fits the source text better than a generic LLM-heavy inventory would.
- One row looks worth manual verification: `10329 | Copilot`. The source only says `Information Technology` and `Increased efficiency and productivity`, but the DB marks it as `product_deployment` with `deployment_scope=enterprise_wide`. That is plausible, but the source text does not itself justify enterprise-wide scope, so this looks like the most likely overreach in the tag set.
- The ArcGIS/ESRI rows are also somewhat coarse in labeling. The source describes GIS efficiency and insight use cases, while the DB normalizes them to `Esri ArcGIS` / `Esri ArcGIS AI` with `ai_sophistication=classical_ml`. That is directionally defensible, but the product linkage is broader than the source wording.

# Recommended follow-up
- Verify row `10329` against the original inventory record to confirm whether the deployment is truly enterprise-wide or just an IT-managed bureau deployment.
- Spot-check the ArcGIS-linked rows to confirm the product normalization is intentional and not collapsing distinct GIS capabilities into one product label.
