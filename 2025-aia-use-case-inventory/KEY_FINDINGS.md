# Federal AI Inventory 2025 — Key Findings

Generated from the SQLite database: `data/federal_ai_inventory_2025.db`

Total: **3,616 individual + 192 consolidated = 3,808 use case entries** across 44 agencies.

## Maturity Tier Distribution

| Tier | Count | Agencies |
|------|-------|----------|
| **Leading** (enterprise LLM + coding + agentic + >50 UC) | 8 | VA, DOE, DOJ, DOI, DHS, DOT, State, TVA |
| **Progressing** (enterprise LLM + >20 UC) | 5 | ED, FDIC, GSA, SSA, HUD |
| **Early** (any GenAI + >5 UC) | 25 | HHS, NASA, Treasury, DOC, USDA, DOL, SEC, SBA, etc. |
| **Minimal** (<5 UC or no GenAI) | 6 | OPM, NRC, NTSB, NMB, NCUA, CFTC |

## Enterprise LLM Access

### Agencies WITH enterprise LLM access (13)
VA, DOE, DOJ, DOI, DHS, ED, DOT, State, GSA, SSA, HUD, OPM, NRC

### CFO Act agencies WITHOUT enterprise LLM access in their inventory (8)
**HHS, NASA, DOC, USDA, Treasury, DOL, SBA, EPA, NSF**

⚠️ Notable: **HHS does not show enterprise LLM access** in its 2025 inventory despite the 2023 CDC ChatGPT deployment referenced in the draft piece (1.2M chats, 41K hours saved). This may represent an inventory reporting gap rather than actual absence.

## Coding Assistant Deployment

**29 agencies deployed coding assistants** (at least 1 entry):

| Agency | Count | Top Tool |
|--------|-------|----------|
| ED | 13 | M365 Copilot + GSA USAi |
| DOC | 12 | GitHub Copilot + Gemini Code Assist + Amazon Q Dev |
| Treasury | 8 | Multiple bureau-level deployments |
| DOE | 7 | GitHub Copilot at PNNL/SLAC/WAPA + Tabnine |
| DHS | 7 | Bespoke Azure OpenAI wrappers (CBP CodeGen, FEMA Code Assist GPT) |
| HHS | 5 | Scattered; CMS OC GitHub Copilot POC |
| NASA | 4 | Pilot studies |
| DOJ, SBA, SSA | 3 each | |
| State, SEC, FTC, FCC, DOI | 2 each | |
| 14 other agencies | 1 each | Usually M365 Copilot "generate code" template |

**Zero coding assistants**: USDA, FRB, FHFA, EPA, NARA, GPO, FERC, FRTIB, OPM, NRC, NTSB, NMB, NCUA, CFTC

## Top Products Deployed Government-Wide (by agency count)

| Product | Vendor | Agencies Using |
|---------|--------|----------------|
| **Microsoft 365 Copilot** | Microsoft | 18 |
| ServiceNow Now Assist | ServiceNow | 12 |
| ChatGPT | OpenAI | 11 |
| Azure OpenAI | Microsoft | 11 |
| Microsoft Teams | Microsoft | 9 |
| Gemini | Google | 8 |
| **GitHub Copilot** | Microsoft | 8 |
| Databricks | Databricks | 7 |
| Microsoft Defender | Microsoft | 7 |
| Esri ArcGIS AI | Esri | 6 |

## Year-over-Year Growth (2024 → 2025)

**Largest increases:**
- NASA: +2261% (18 → 425)
- PBGC: +900%, EAC: +900%
- HUD: +417%, USTDA: +400%
- DOE: +330%, DOC: +291%

**Declines:**
- NCUA: -81%, FRB: -24%, DOL: -21%, CFTC: -25%, FHFA: -11%

## Notable Deployment Patterns

### Federated (bureau-siloed) deployment
- **DHS**: Each component runs its own LLM chat (DHSChat, ChatCBP, CISAChat, ICE AI Assistant, USCIS PAiTH) atop Azure OpenAI
- **DOE**: Every national lab procured its own ChatGPT/Claude/Copilot separately — no DOE-wide deployment
- **Treasury**: OCC built 3 custom platforms (OCC.Chat, InfoAssist, DocChat) with 21+ sub-apps

### Enterprise-wide (centralized) deployment
- **State Dept**: StateChat (45-50K of 80K employees) on OpenAI via Palantir Foundry
- **DHS**: DHSChat (~19K employees) on Azure OpenAI
- **ED**: Two enterprise platforms (M365 Copilot + GSA USAi) fragmented into 65 line items
- **DOT**: Enterprise Personal Productivity Assistant + "Ask Dottie"
- **DOJ**: DOJ-wide M365 Copilot + GitHub Copilot

### Heavy custom/research (no broad LLM)
- **NASA**: 422/425 custom research systems (no enterprise LLM surfaced)
- **USDA**: 85% custom ML (Forest Service, NRCS scientific work)
- **FRB**: Nearly all classical ML/non-generative NLP

### Unique patterns
- **GSA**: Builds products OTHER agencies consume (USAi.gov) — most AI-forward
- **NARA**: Enterprise Google Gemini rollout + custom NLP/semantic search
- **FTC**: Aggressive bespoke Azure OpenAI + Sentinel platform (consumer protection)

## Database Schema

Tables:
- `agencies` (60 agencies tracked, 44 with data)
- `use_cases` (3,616 individual, M-25-21 canonical schema)
- `consolidated_use_cases` (192 Appendix B/COTS entries)
- `products` (36 canonical products)
- `product_aliases` (~120 observed name variants)
- `use_case_templates` (20 OMB standard templates)
- `use_case_tags` (3,808 rows of analytical metadata)
- `agency_ai_maturity` (44 agency scores)
- `column_mappings` (documents per-agency schema mappings)

## Key Queries for the Piece

```sql
-- How many CFO Act agencies have enterprise LLM access?
SELECT COUNT(*) FROM agency_ai_maturity m
JOIN agencies a ON a.id = m.agency_id
WHERE a.agency_type = 'CFO_ACT' AND m.has_enterprise_llm = 1;

-- Which agencies have ZERO coding tools in their inventory?
SELECT a.abbreviation FROM agency_ai_maturity m
JOIN agencies a ON a.id = m.agency_id
WHERE m.coding_tool_count = 0 AND m.total_use_cases > 0;

-- Total distinct products deployed across all agencies (deduped)
SELECT COUNT(DISTINCT product_id) FROM use_cases WHERE product_id IS NOT NULL;
```
