# Product Hierarchy Audit

Read-only review of `parent_product_id` relationships in `data/federal_ai_inventory_2025.db`.

## Executive Summary

The `products` table has 242 rows but only **5** parent→child edges. Most large vendor families (Microsoft, Google, Amazon, OpenAI, Palantir, IBM, Adobe, Apple, LexisNexis) currently have a flat structure even though obvious "platform / sub-product / feature" relationships exist.

**Recommendation:** add roughly **45–55 new parent-child edges** (high + medium confidence combined). Of the 5 existing edges, **3 are correct, 1 is borderline-defensible, and 1 should be removed (`GitHub Copilot → Microsoft 365 Copilot`)**. We also flag two duplicate rows (`NotebookLM` / `Google NotebookLM`; `Microsoft 365` / `Microsoft 365 Apps for Enterprise`) that should be merged before parenting; otherwise the hierarchy will encode the duplicates.

The dominant pattern that *should* be in the data, and currently is not, is **vendor-platform → sub-service** (e.g., `Microsoft Azure Platform` parents the entire `Azure …` family; `Google Vertex AI` parents nothing despite being a clear platform; `Amazon Q` parents nothing despite obvious Q-for-Business / Q-for-Developers SKUs).

We do **not** recommend modeling the cross-vendor "same model on multiple clouds" case (Claude on Bedrock vs. Claude on Vertex vs. Claude API) using `parent_product_id`. The current schema represents commercial SKUs / billing surfaces, not abstract models; encoding model-lineage there would conflate two different concepts. We argue this in the cross-vendor section below.

## Methodology

1. Queried `products` and `product_aliases` directly via sqlite3.
2. Grouped by `vendor`, then read every product name + alias for the vendors with ≥3 products plus a long tail of single-product vendors that share product-name prefixes.
3. Cross-referenced `use_case_products` so we could weight recommendations by how heavily each product is actually used (a heavily-used product makes a good "parent" because it absorbs traffic naturally).
4. For each vendor cluster we asked three questions: (a) is there a clear platform that the others sit inside? (b) are these distinct SKUs / billing units (peers)? (c) is the row a "feature surface" of an existing parent (real child)?
5. Treated FedRAMP authorization, separate licensing, and separate purchase as evidence the rows are **peers, not parent-child**, even when one has a vendor-level container brand.

## Audit of the 5 Existing Edges

| Edge (child → parent) | Verdict | Reasoning |
|---|---|---|
| `Microsoft 365 Copilot Chat` → `Microsoft 365 Copilot` | **KEEP** | Copilot Chat is the chat surface inside the M365 Copilot product. Same SKU family, same licensing, same FedRAMP authorization. Clean parent-child. |
| `GitHub Copilot` → `Microsoft 365 Copilot` | **REMOVE** | GitHub Copilot predates M365 Copilot, has separate GitHub Enterprise / GitHub Copilot Business / Copilot Enterprise SKUs, separate billing, separate FedRAMP scope, and a different underlying surface (IDE/CLI vs. M365 apps). They are Microsoft-owned siblings, not parent-child. Both should sit under a Microsoft container or, more accurately, just stay as peers (or both be parented to a top-level "Copilot family" if one is created). |
| `DALL-E` → `ChatGPT` | **CHANGE** to `DALL-E` → `OpenAI API` (or leave as ChatGPT-only feature). | DALL-E is exposed inside ChatGPT *and* via the OpenAI API. Modeling it strictly as a child of ChatGPT misses the API exposure. Lowest-friction fix: keep parent = `ChatGPT` since DALL-E is now embedded in the consumer/Enterprise surface and rarely procured separately, but flag for revisit. Confidence: medium. |
| `Claude Code` → `Claude` | **KEEP** | Claude Code is an Anthropic-shipped CLI/IDE coding agent that uses Claude as its underlying model. It is clearly a sub-product of the Claude family and is sold/licensed against the same Anthropic account. Clean parent-child. |
| `NotebookLM` → `Gemini` | **CHANGE** to `NotebookLM` → (no parent), or parent to a `Google AI` container. | NotebookLM is Gemini-powered but is a distinct product surface and has been since launch. Parenting it to Gemini conflates "uses Gemini as the model" with "is a sub-SKU of Gemini." If we keep it, we should be consistent and parent every Google product that uses Gemini under the model — which we explicitly recommend against (see cross-vendor section). Better: remove this edge, and let NotebookLM (the canonical row) live as a peer. Confidence to remove: medium. |

## Per-Vendor Proposed Hierarchy

### Microsoft (40 products)

The single biggest cluster. There are really four sub-families inside Microsoft:

```
Microsoft Azure Platform (2910)
├── Azure OpenAI (2843)
├── Azure AI Foundry (2942)
├── Azure AI Document Intelligence (2945)
├── Azure AI Vision / Document Intelligence (3013)   [duplicate of 2945? merge candidate]
├── Azure Speech (2943)
├── Microsoft Azure Authoring Tools (3106)
├── Microsoft Azure PowerShell (3108)
└── Microsoft Azure Quantum Elements (3109)

Microsoft 365 (3102)   [or merge 3102 + 3103 + Microsoft 365 Apps for Enterprise into one row first]
├── Microsoft 365 Apps for Enterprise (3103)         [duplicate; merge then drop]
├── Microsoft Teams (2841)
├── Microsoft Outlook (3120)
├── Microsoft OneDrive (3118)
├── Microsoft OneNote (3119)
├── Microsoft PowerPoint (3123)
├── Microsoft Exchange Server (3116)                  [server SKU, looser fit]
├── Microsoft Project (3124)
├── Microsoft Skype (3129)                            [legacy, but Microsoft ships it as M365-adjacent]
└── Microsoft 365 Copilot (2836)
    └── Microsoft 365 Copilot Chat (2837)             [existing edge - KEEP]

Microsoft Power Platform (3122)
├── Microsoft AI Builder (3105)
├── Microsoft Copilot Studio (2839)                  [Copilot Studio = renamed Power Virtual Agents, lives in Power Platform]
└── Microsoft Power BI (3121)

Microsoft Security family   (no parent in DB; recommend NOT inventing a parent — these are peers)
├── Microsoft Defender (2842)
├── Microsoft Sentinel (2914)
├── Microsoft Purview (2894)
│   └── Microsoft Purview eDiscovery (3125)
└── Microsoft Copilot for Security (2838)            [peer of M365 Copilot, NOT child]

Standalone / loose
- GitHub Copilot (2840)              [Microsoft-owned but fully separate product]
- Microsoft Edge (3115)              [browser; standalone]
- Microsoft HoloLens (2944)          [hardware]
- Microsoft Discovery (3113)
- Microsoft Dynamics 365 (3114)      [own product line; could parent ScreenSketch / Search in Bing if we wanted]
- Microsoft Search in Bing (3127)
- Microsoft ScreenSketch (3126)
- Visual Studio (3197)
- Visual Studio Enterprise (3198)    → child of Visual Studio
- SQL Server Management Studio (3176)
```

Notable choices:
- `Microsoft Copilot for Security` is a **peer** of M365 Copilot, not a child. Different SKU, different audience, separate FedRAMP scope. Recommend leaving it parentless or only sibling-grouping it.
- `Microsoft Copilot Studio` belongs under `Microsoft Power Platform`, not under M365 Copilot. It's the rebranded Power Virtual Agents product.
- `Azure OpenAI` is **not** a child of `Microsoft 365 Copilot`. It is a child of `Microsoft Azure Platform`. This is the most common modeling mistake in inventories of this kind.

### Google (13 products + 1 duplicate)

```
Google Cloud Platform (3062)
├── Google Vertex AI (3066)
│   └── Google Agentspace (3060)        [Agentspace ships on Vertex]
└── Google Cloud Vision (3063)

Google Workspace (2851)
├── Gemini (2848)                       [Gemini-for-Workspace surface ships inside; canonical row covers consumer/API too — borderline]
└── Google Chrome Generative AI (3061)  [arguably Workspace-adjacent, also standalone consumer]

Standalone
- NotebookLM (2849)                     [canonical; remove parent edge to Gemini]
- Google NotebookLM (2980)              [DUPLICATE of 2849; merge & drop]
- Google Translate (2919)
- Google Lens (2850)
- Google Maps (2900)
- Google Pixel (2901)                   [hardware]
```

Notes:
- Gemini under Google Workspace is borderline. The Gemini *row* covers the underlying model + the consumer Gemini app + API + Workspace surface, so it's overloaded. We'd recommend leaving it parentless rather than picking one parent that's wrong for the others.
- `Google Cloud Platform` parenting `Vertex AI` is high confidence; Vertex is a GCP service.
- The duplicate (`NotebookLM` 2849 vs `Google NotebookLM` 2980) needs a data fix before any hierarchy is set, otherwise the parent-child structure will encode the duplication.

### Amazon / AWS (8 products)

```
AWS Bedrock (2855)                       [no parent]

Amazon Q (2852)                          [no parent in DB; the canonical row absorbs Q-for-Business / Q-for-Developers per aliases]

Standalone AWS services (each a peer; could optionally parent under a synthetic "AWS" row, but we don't recommend creating one)
- AWS Kendra (2925)
- AWS Lex (3007)
- AWS Rekognition (2969)
- AWS Textract (2874)
- AWS Transcribe (2854)
- Amazon CodeWhisperer (2853)            [merged into Amazon Q Developer in 2024 — candidate to make child of Amazon Q]
```

Notes:
- The `products` table does not have an `AWS` umbrella row. We do **not** recommend creating one — it would be a synthetic concept with no SKU. Parents should map to real procurable platforms.
- `Amazon CodeWhisperer` was officially folded into `Amazon Q Developer` in 2024. If the dashboard intends to keep CodeWhisperer as a row for historical use cases, it should be a child of `Amazon Q`.
- `AWS Bedrock` deliberately has no parent. It is its own SKU and is not a child of "AWS" because there is no "AWS" row.

### OpenAI (3 products)

```
OpenAI API (2845)
└── (no children — DALL-E currently parented to ChatGPT)

ChatGPT (2844)
└── DALL-E (2877)                        [existing edge; questionable but defensible — see audit table]
```

Notes:
- ChatGPT and OpenAI API are peers (both use the same underlying models but are different commercial surfaces — Enterprise/Team/Edu vs. pay-as-you-go API). Do not parent one to the other.
- DALL-E parent is debatable. Slight preference: keep current edge (under ChatGPT) since DALL-E is now consumed primarily through ChatGPT in the federal procurement context.

### Anthropic (2 products)

```
Claude (2846)
└── Claude Code (2847)                   [existing edge - KEEP]
```

Clean. No additional structure needed unless Anthropic ships further sub-products that show up in inventory.

### Palantir (4 products)

```
Palantir Federal Cloud Service (3144)    [the platform / cloud environment]
└── Palantir AIP (2893)                  [AI surface that runs on Foundry / FedCloud]

Palantir Decision and Analytics Platform (DNA-P) (3143)   [bespoke gov platform]
└── Palantir Case Management & Analytics (CMA) (3142)     [bespoke gov module]
```

Notes:
- Palantir's federal product naming is messy (DNA-P and CMA appear to be agency-branded deployments). Confidence on the second tree is **low**; would benefit from an analyst-level review.
- `Palantir AIP` heavy use (23 use cases) — making it a child of FedCloud is correct conceptually but won't change much in the dashboard. Optional.

### IBM (3 products)

```
IBM Watson (3077)
├── IBM ARGOS (2930)                     [Watson NLP-derived; medium confidence]
└── IBM CoreDF (2957)                    [Watson document AI; medium confidence]
```

Confidence is medium because IBM has rebranded Watson several times and ARGOS / CoreDF appear to be agency-specific deployments. If we're not sure they're Watson-derived, leave as peers.

### Adobe (3 products)

```
Adobe Creative Cloud Suite (2986)
├── Adobe Photoshop (2873)
└── Adobe Firefly (2872)                  [Firefly ships inside Creative Cloud apps but is also a separate API]
```

High confidence on Photoshop. Medium on Firefly (it's also a standalone API/SKU).

### Apple (3 products)

```
Apple Intelligence (2998)                  [no children — Face ID and Maps predate AI branding]

Standalone
- Apple Face ID (2898)                     [biometric feature; not part of "Apple Intelligence"]
- Apple Maps (2899)                        [consumer feature]
```

We recommend **no** edges here. Apple's three rows are not a family — they're separate consumer features that happen to share a vendor.

### LexisNexis (4 products)

```
LexisNexis (3094)                          [umbrella row]
├── Lexis+ AI (2857)                       [the AI legal research product]
├── LexisNexis Risk Solutions (3095)       [different business unit, but same vendor row]
└── NexisXplore (3134)                     [Nexis-branded, intel/news search]
```

Confidence: medium. Lexis+ AI under LexisNexis is high confidence; Risk Solutions is technically a separate business unit (RELX) and could be left parentless. NexisXplore is high confidence.

### Salesforce (3 products)

```
(no good single parent — Salesforce is a vendor, not a product row)

Salesforce Einstein (3161)                 [the AI layer across Salesforce CRM]
Tableau (2892)                              [Salesforce-owned, separate product]
Slack (2888)                                [Salesforce-owned, separate product]
```

We recommend **no** edges. Salesforce/Tableau/Slack are sibling acquisitions; parenting them creates noise. Einstein is the AI layer of Sales Cloud / Service Cloud — but those CRM clouds aren't in `products`.

### ServiceNow (2 products)

```
ServiceNow Now Assist (2858)
ServiceNow IT Operations Management (ITOM) Predictive AIOps (3164)
```

Peers. Both AI products, but Now Assist (the conversational AI) and ITOM Predictive AIOps (the AIOps SKU) are different product lines. No edge.

### OpenText (2 products)

```
OpenText Axcelerate (3138)                 [eDiscovery]
OpenText Decisiv (3139)                    [legal knowledge mgmt]
```

Peers. Different product lines. No edge.

### Veritone (2 products)

```
Veritone (2905)                            [the aiWARE platform / company-level row]
└── Veritone Illuminate (2937)             [specific product on Veritone platform]
```

High confidence.

### Thomson Reuters (2 products)

```
Thomson Reuters CLEAR (2904)               [investigative search]
Westlaw AI (2856)                          [legal research]
```

Peers. Different product lines. No edge.

### GSA (2 products)

```
USAi (GSA) (2912)                          [AI platform]
VAO Ally (2921)                            [agentic assistant]
```

USAi is a platform; VAO Ally is a specific agent. Could parent VAO Ally → USAi if VAO Ally is built on USAi infrastructure. Confidence: low without confirmation. Recommend leaving as peers absent evidence.

## Cross-Vendor / Multi-Deployment Models

The richest temptation, and the one we recommend resisting, is to model frontier models that ship across multiple clouds (Claude on Bedrock vs. Claude on Vertex vs. Claude API; Llama on Bedrock vs. Llama on Vertex vs. Llama via Hugging Face; GPT-4 via Azure OpenAI vs. via OpenAI API) as `model → deployment-surface` parent-child relationships.

Arguments for using `parent_product_id` for this:
- Reflects the reality that the same model is being purchased through different surfaces.
- Lets the dashboard roll up usage to "how much Claude is the federal government running."
- Helps audit whose model is actually doing work even when the contract is with a cloud provider.

Arguments against (we agree with these):
1. **Conflates two different concepts.** The current schema models **commercial SKUs** (procurable units). A model like Claude is *not* a SKU; it's an underlying capability that some SKUs deliver. Mixing these breaks the meaning of the field.
2. **Multi-parent problem.** Claude-on-Bedrock has two natural parents (`AWS Bedrock` and `Claude`). The schema only supports one `parent_product_id`. Whichever you pick is wrong half the time.
3. **The DB doesn't have separate rows for the deployment surfaces.** There is one `Claude` row, not "Claude on Bedrock" + "Claude via API" + "Claude on Vertex." So there's nothing to parent. The right way to surface this — if needed — is **tags** (e.g., `delivered_via=bedrock`) on `use_cases`, or a separate `model_deployments` table. Not `parent_product_id`.
4. **The 5 existing edges all model "is-a-sub-SKU-of," not "uses-the-model-of."** Adding model-of edges would mix two semantics in one field, which makes downstream queries ambiguous.

**Recommendation:** keep `parent_product_id` strictly for **same-vendor sub-SKU / sub-feature** relationships. If model-lineage is desired later, add a separate `underlying_model_id` column or a join table.

## Full Proposed-Edges Table

Edges to ADD (high confidence first):

| Child | Proposed Parent | Confidence | Reasoning |
|---|---|---|---|
| Azure OpenAI (2843) | Microsoft Azure Platform (2910) | High | Azure service, billed through Azure. |
| Azure AI Foundry (2942) | Microsoft Azure Platform (2910) | High | Azure service. |
| Azure AI Document Intelligence (2945) | Microsoft Azure Platform (2910) | High | Azure service. |
| Azure Speech (2943) | Microsoft Azure Platform (2910) | High | Azure service. |
| Microsoft Azure Authoring Tools (3106) | Microsoft Azure Platform (2910) | High | Azure service. |
| Microsoft Azure PowerShell (3108) | Microsoft Azure Platform (2910) | High | Azure service. |
| Microsoft Azure Quantum Elements (3109) | Microsoft Azure Platform (2910) | High | Azure service. |
| Azure AI Vision / Document Intelligence (3013) | Microsoft Azure Platform (2910) | High | Azure service (also a duplicate of 2945; resolve before adding edge). |
| Microsoft 365 Copilot (2836) | Microsoft 365 (3102) | High | Copilot is licensed on top of M365. (Resolve 3102/3103 dup first.) |
| Microsoft Teams (2841) | Microsoft 365 (3102) | High | Bundled in M365. |
| Microsoft Outlook (3120) | Microsoft 365 (3102) | High | Bundled in M365. |
| Microsoft OneDrive (3118) | Microsoft 365 (3102) | High | Bundled in M365. |
| Microsoft OneNote (3119) | Microsoft 365 (3102) | High | Bundled in M365. |
| Microsoft PowerPoint (3123) | Microsoft 365 (3102) | High | Bundled in M365. |
| Microsoft Project (3124) | Microsoft 365 (3102) | Med | Some plans bundle, some don't. |
| Microsoft Exchange Server (3116) | Microsoft 365 (3102) | Med | Server SKU is separate; M365 includes Exchange Online. Loose fit. |
| Microsoft 365 Apps for Enterprise (3103) | Microsoft 365 (3102) | High | (Or merge as duplicate.) |
| Microsoft Copilot Studio (2839) | Microsoft Power Platform (3122) | High | Copilot Studio = rebranded Power Virtual Agents. |
| Microsoft AI Builder (3105) | Microsoft Power Platform (3122) | High | Power Platform component. |
| Microsoft Power BI (3121) | Microsoft Power Platform (3122) | High | Power Platform component. |
| Microsoft Purview eDiscovery (3125) | Microsoft Purview (2894) | High | Sub-product of Purview. |
| Visual Studio Enterprise (3198) | Visual Studio (3197) | High | Tier of Visual Studio. |
| Google Vertex AI (3066) | Google Cloud Platform (3062) | High | GCP service. |
| Google Cloud Vision (3063) | Google Cloud Platform (3062) | High | GCP service. |
| Google Agentspace (3060) | Google Vertex AI (3066) | Med | Agentspace is built on Vertex; could alternatively parent to GCP directly. |
| Google Chrome Generative AI (3061) | Google Workspace (2851) | Low | Tenuous — Chrome is consumer, but Gen-AI features are tied to Workspace tenant in enterprise. Could leave parentless. |
| Amazon CodeWhisperer (2853) | Amazon Q (2852) | High | CodeWhisperer was rebranded as Amazon Q Developer in 2024. |
| Palantir AIP (2893) | Palantir Federal Cloud Service (3144) | Med | AIP runs on Foundry / FedCloud in federal context. |
| Palantir Case Management & Analytics (CMA) (3142) | Palantir Decision and Analytics Platform (DNA-P) (3143) | Low | Names suggest CMA is a module of DNA-P, but both look like agency-branded names. |
| IBM ARGOS (2930) | IBM Watson (3077) | Med | NLP product in Watson family; verify. |
| IBM CoreDF (2957) | IBM Watson (3077) | Med | Document AI in Watson family; verify. |
| Adobe Photoshop (2873) | Adobe Creative Cloud Suite (2986) | High | Photoshop is the core CC app. |
| Adobe Firefly (2872) | Adobe Creative Cloud Suite (2986) | Med | Ships inside CC apps; also standalone API. |
| Lexis+ AI (2857) | LexisNexis (3094) | High | Lexis+ AI is the LexisNexis AI legal research product. |
| NexisXplore (3134) | LexisNexis (3094) | High | Nexis-branded product. |
| LexisNexis Risk Solutions (3095) | LexisNexis (3094) | Low | Technically a separate RELX business unit; only edge if dashboard treats LexisNexis as company-level. |
| Veritone Illuminate (2937) | Veritone (2905) | High | Illuminate is a Veritone product on aiWARE. |

Total proposed adds: **~35 high + medium confidence**, plus ~5 low-confidence-but-defensible edges.

## Edges to REMOVE or RECONSIDER

| Existing Edge | Action | Reasoning |
|---|---|---|
| `GitHub Copilot` (2840) → `Microsoft 365 Copilot` (2836) | **REMOVE** | Different SKUs, different platforms, different licensing. Microsoft-owned siblings, not parent-child. |
| `NotebookLM` (2849) → `Gemini` (2848) | **REMOVE** | "Uses Gemini as the model" is not the same as "is a sub-SKU of Gemini." Removing this edge keeps the semantics of `parent_product_id` clean. |
| `DALL-E` (2877) → `ChatGPT` (2844) | **KEEP, REVISIT** | DALL-E is also exposed via the OpenAI API. Defensible to keep since federal procurement of DALL-E in 2025 happens almost entirely through ChatGPT Enterprise. |

## Other Data-Quality Findings (out of scope for hierarchy, but blocking)

These should be resolved **before** any large-scale hierarchy backfill, otherwise the parent edges will lock in the duplicates:

1. **Duplicate row:** `NotebookLM` (id 2849) and `Google NotebookLM` (id 2980). Merge — 2849 has the aliases and the use-case links; 2980 is empty.
2. **Duplicate row pair:** `Microsoft 365` (id 3102) and `Microsoft 365 Apps for Enterprise` (id 3103). Likely should be one row with the other as alias. (`Microsoft 365 Apps for Enterprise` is the formal name of the desktop-apps SKU within M365.)
3. **Likely duplicate:** `Azure AI Document Intelligence` (id 2945) and `Azure AI Vision / Document Intelligence` (id 3013). These appear to be the same Azure service; the second was likely a load-time variant.
4. **Vendor ambiguity:** `Slack` and `Tableau` are vendored to `Salesforce`. Correct factually, but it means vendor-clustering treats them as Salesforce siblings. Worth a comment in `auto_tag.py` to avoid future re-vendoring.

## Recommendations

1. **Fix the 5 existing edges first** (remove 1, change 1 to "no parent," keep 3). This is a 5-row UPDATE and clears semantic confusion before adding mass.
2. **Resolve the four duplicates** above. They are blockers for hierarchy work, not because edges can't be added with them in place but because adding edges will then need to be redone after dedup.
3. **Add the high-confidence edges** (~25 edges, all same-vendor sub-SKU / platform-component). Low risk.
4. **Treat medium-confidence edges as a review queue** for an analyst pass; do not bulk-apply.
5. **Do not** introduce cross-vendor model-lineage edges via `parent_product_id`. If model rollups are desired later, add a separate column or join table — see cross-vendor section.
6. **Consider documenting the semantics of `parent_product_id`** in a short comment in `data/federal_hierarchy_seed.py` or wherever products are seeded: "same-vendor sub-SKU / sub-feature only; not 'uses-the-model-of.'" This will prevent future audits from re-asking this question.
7. **Long-tail vendors with one product** (the 60+ single-product vendors) need no hierarchy work. Skip.
