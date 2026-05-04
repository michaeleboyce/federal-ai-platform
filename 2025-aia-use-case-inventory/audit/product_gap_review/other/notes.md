# Product-gap review — "other" slice (18 products, 28 gap rows)

## Decision tally

| Decision | Count |
|---|---|
| `link` | 9 |
| `add_alias` | 0 |
| `false_positive` | 17 |
| `tighten_alias` | 1 |
| `unclear` | 2 |
| **Total** | **29** |

(UC 46558 Andesite appears under both Splunk and Sentinel as separate
`false_positive` rows since each product has its own gap row in the audit.
The 9 `link` rows cover 8 distinct use cases — Westlaw has one and one
borderline `unclear` row counted separately.)

## Important note on stale audit IDs

The `audit/undercovered_products_audit.csv` was generated against an older
DB snapshot. Both `use_cases.id` and `products.id` have been re-keyed
since:

| Product (audit pid → current pid) | Was | Now |
|---|---|---|
| Microsoft 365 1401 | 3 linked | 3102, still 3 linked (different IDs) |
| Westlaw AI 1177 | 8 linked | 2856, 8 linked |
| ServiceNow Now Assist 1179 | 34 linked | 2858, 32 linked |
| Databricks 1190 | 8 linked | 2869, 8 linked |
| Microsoft Power Platform 1421 | 3 linked | 3122, 3 linked |
| Salesforce Einstein 1460 | 13 linked | 3161, 12 linked |
| Visual Studio 1496 | 2 linked | 3197, 2 linked |
| Microsoft Copilot Studio 1162 | 5 linked | 2839, 4 linked |
| Splunk 1187 | 4 linked | 2866, 4 linked |
| Esri ArcGIS AI 1192 | 13 linked | 2871, 13 linked |
| Adobe Photoshop 1194 | 2 linked | 2873, 2 linked |
| Microsoft Sentinel 1210 | 4 linked | 2914, 4 linked |
| Relativity 1214 | 5 linked | 2918, 5 linked |
| AWS Rekognition 1268 | 1 linked | 2969, 1 linked |
| Hyperscience 1373 | 3 linked | 3074, 3 linked |
| Microsoft AI Builder 1404 | 2 linked | 3105, 2 linked |
| Microsoft Power BI 1420 | 1 linked | 3121, 1 linked |
| Skillsoft Percipio CAISY 1468 | 1 linked | 3169, 1 linked |

Many of the original audit's gap rows (Westlaw/ServiceNow/Databricks/etc.)
have been resolved by subsequent ETL runs that hit the same use cases I'd
recommend. I re-ran the gap analysis against the **current** DB and used
that as the authoritative gap list, then mapped each original audit
sample back to the current `use_cases.id` by name + agency.

## Patterns observed

### 1. Microsoft 365 (3102) is a phantom — its single alias is greedy
Every "Microsoft 365 Copilot" mention triggers a phantom gap on the
non-AI Microsoft 365 bundle (3102). 5 of 5 gap rows are this collision.
Recommend either:
- **Drop the standalone "Microsoft 365" alias from product 3102**
  (let it be populated only by exact-system_name matches), or
- Restrict the alias to "Microsoft 365" AND NOT containing "copilot".

This same pattern likely affects other base-bundle products that share a
prefix with their AI-enabled SKU (Visual Studio vs Visual Studio
Enterprise, Power Platform vs Power Automate/Power BI, etc.).

### 2. SIEMs and CRMs are *data sources* in many use cases, not the AI
ServiceNow, Splunk, Microsoft Sentinel, Salesforce, Relativity all show
up in narratives as "the AI consumes/feeds/integrates with X" rather
than "we deployed X's AI features." Six of my 16 false_positives are
this pattern. populate_use_case_products may need a heuristic that
looks for verbs like "deployed/built using/runs on" near the product
name vs "integrates with/data from/written to" — though that's
probably too noisy to do in regex.

### 3. "Copilot" / "Microsoft Copilot" is overloaded
M365 Copilot, Microsoft Copilot Studio, Microsoft Copilot for Security,
Microsoft Copilot Chat, GitHub Copilot — all share "Copilot." The
Copilot Studio gap (UC 43988) was a M365 Copilot use case that
mentioned "agentic orchestration for Copilot Studio" downstream.
Already linked correctly to M365 Copilot. The catalog should use the
strictest possible aliases for each Copilot variant; "Copilot" alone
should never be an alias.

### 4. ArcGIS as basemap vs ArcGIS AI
DHS UC 43421 mentions "physical location on an ArcGIS map" — basemap
display, no AI. The ArcGIS alias list ('ArcGIS', 'ESRI GIS AI', 'Esri',
'Esri ArcGIS', 'Esri ArcGIS AI') is loose; "ArcGIS" alone catches every
GIS-display reference. Could tighten to require co-occurrence with
"AI Assistant", "GeoAI", "spatial ML" — though current false-positive
rate is low (1 of 14).

## Real `link` recommendations (8)

1. **UC 44901 (FDIC) → Westlaw AI** — explicit Thomson Reuters/Westlaw GenAI
2. **UC 43454 (DHS) → Databricks** — "databricks dashboard"
3. **UC 44782 (DOT) → Databricks** — "AI/ML tools on Databricks platform"
4. **UC 46828 (VA) → Microsoft Power Platform** — "Microsoft Power Platform AI modeling" / Power Automate
5. **UC 44410 (DOJ) → Adobe Photoshop** — "AI capabilities in applications like Photoshop"
6. **UC 45426 (HHS) → AWS Rekognition** — "passed to the AWS Rekognition service"
7. **UC 46706 (VA) → Hyperscience** — "The Hyperscience platform (OCR, NLP, ML)"
8. **UC 45174 (HHS) → Microsoft AI Builder** — "OCR model built using Microsoft AI Builder"
9. **UC 45533 (HUD) → Skillsoft Percipio CAISY** — vendor literally Skillsoft Percipio; UC IS CAISY

(That's 9 — Westlaw counted once; tally above of 8 omits the borderline 44680.)

## Catalog-level rework recommendations

1. **Microsoft 365 (3102)**: drop or tighten the standalone alias.
   The bundle-vs-AI collision is the entire gap on this product.
2. **Visual Studio (3197) vs Visual Studio Enterprise (3198)**: decide
   whether these should be merged or whether 3197 is the parent. Right
   now both exist; the audit treats 3197 as canonical but the only
   use case is on 3198. Consider also adding **Visual Studio Code** as
   a separate product since Ansible Lightspeed and other plugins
   reference VS Code specifically.
3. **Skillsoft Percipio CAISY (3169)**: add `CAISY` as a standalone
   alias. The literal HUD CAISY use case is currently unlinked,
   apparently because the existing alias `SKILLSOFT PERCIPIO/CAISY`
   (with slash) is not a substring of the use case name "CAISY -
   Workforce Training Conversation Simulator." Adding `CAISY` (alone)
   would fix it. Risk: low — CAISY is a trademarked name with no
   common-English collision.
4. **Power Platform family**: clarify the parent/child relationship
   between Microsoft Power Platform (3122), Microsoft AI Builder
   (3105), Microsoft Power BI (3121), and any Power Automate entry.
   Use cases that build on AI Builder or Power Automate often also
   warrant a parent link; today they only link to the leaf.

## Unclear flags (2 — for human review)

- **UC 44680 (DOJ) "AI-powered Legal Research"**: narrative is generic;
  no vendor named. DOJ is plausible Westlaw user but the text doesn't
  justify the link. Human should check with DOJ directly.
- **UC 46893 (VA) "National Training Team | Schools NLP FAQ
  Dashboard"**: narrative is empty (problem/benefits/outputs all
  blank). Very likely the same situation as sibling UC 46713 (Power BI
  is dashboard, not AI), but cannot judge from text. Maybe pull the
  raw_json to recover.
