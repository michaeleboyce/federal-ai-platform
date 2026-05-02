# Federal AI Inventory 2025 — Key Findings

Generated from the SQLite database: `data/federal_ai_inventory_2025.db`

Total: **3,617 individual + 192 consolidated = 3,809 use case entries** across 44 agencies.

## Maturity Tier Distribution

| Tier | Count | Agencies |
|------|-------|----------|
| **Leading** (enterprise LLM + coding + agentic + >50 UC) | 7 | DHS, DOC, DOE, ED, FDIC, HHS, VA |
| **Progressing** (enterprise LLM + >20 UC) | 1 | GSA |
| **Early** (any GenAI + >5 UC) | 29 | CSOSA, DOI, DOJ, DOL, DOT, EAC, EPA, FCC, FERC, FHFA, FRB, FRTIB, FTC, HUD, NARA, NASA, NLRB, NSF, OSC, PBGC, SBA, SEC, SSA, State, TVA, Treasury, USDA, USITC, USTDA |
| **Minimal** (<5 UC or no GenAI) | 7 | CFTC, GPO, NCUA, NMB, NRC, NTSB, OPM |

## Enterprise LLM Access

### Agencies WITH enterprise LLM access (15)
CSOSA, DHS, DOC, DOE, EAC, ED, FCC, FDIC, FERC, GSA, HHS, NARA, NRC, USITC, VA

### CFO Act agencies WITHOUT enterprise LLM access in their inventory (14)
**USDA, HUD, DOI, DOJ, DOL, State, DOT, Treasury, EPA, NASA, NSF, OPM, SBA, SSA**

⚠️ Notable: **HHS does not show enterprise LLM access** in its 2025 inventory despite the 2023 CDC ChatGPT deployment referenced in the draft piece (1.2M chats, 41K hours saved). This may represent an inventory reporting gap rather than actual absence.

## Coding Assistant Deployment

**15 agencies deployed coding assistants** (at least 1 entry):

| Agency | Count | Top Tool |
|--------|-------|----------|
| ED | 13 | M365 Copilot + GSA USAi |
| DHS | 5 | Bespoke Azure OpenAI wrappers (CBP CodeGen, FEMA Code Assist GPT) |
| DOE | 5 | GitHub Copilot at PNNL/SLAC/WAPA + Tabnine |
| DOC | 4 | GitHub Copilot + Gemini Code Assist + Amazon Q Dev |
| HHS | 2 | Scattered; CMS OC GitHub Copilot POC |
| NASA, SBA, Treasury | 2 each | |
| DOL, FDIC, NLRB, NSF, SSA, TVA, VA | 1 each | |

**Zero coding assistants**: USDA, HUD, DOI, DOJ, State, DOT, EPA, GSA, NRC, OPM, NARA, FHFA, FRB, SEC, NCUA, FTC, FCC, CFTC, USITC, PBGC, FERC, NTSB, USTDA, EAC, GPO, FRTIB, OSC, CSOSA, NMB

## Top Products Deployed Government-Wide (by agency count)

| Product | Vendor | Agencies Using |
|---------|--------|----------------|
| **Microsoft Teams** | Microsoft | 16 |
| ServiceNow Now Assist | ServiceNow | 15 |
| ChatGPT | OpenAI | 14 |
| OpenAI API | OpenAI | 12 |
| Gemini | Google | 11 |
| Custom In-House AI | In-House | 10 |
| Salesforce Einstein | Salesforce | 8 |
| Amazon Q | Amazon | 7 |
| Crowdstrike Falcon | Crowdstrike | 7 |
| Databricks | Databricks | 7 |

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
- `use_cases` (3,617 individual, M-25-21 canonical schema)
- `consolidated_use_cases` (192 Appendix B/COTS entries)
- `products` (217 canonical products)
- `product_aliases` (367 observed name variants)
- `use_case_products` + `consolidated_use_case_products` (726 authoritative product attribution edges)
- `use_case_templates` (22 OMB/Appendix-style templates)
- `use_case_tags` (3,809 rows of analytical metadata)
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
SELECT COUNT(DISTINCT product_id) FROM entry_product_edges;
```
