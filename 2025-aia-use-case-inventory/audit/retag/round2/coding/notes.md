# Round 2 coding-tool retag — methodology and impact

## Editorial rule applied

A row gets `is_coding_tool=1` iff:

1. The product is a **coding-specific developer tool** (GitHub Copilot, Claude Code, Codex, Amazon Q Developer / CodeWhisperer, Gemini Code Assist, Tabnine, Cursor, Codeium, Windsurf, JetBrains AI, IBM watsonx Code Assistant, Replit Ghostwriter, AveriSource, Pingwind AI DevOps, ServiceNow Now Assist for Creator, Ansible Lightspeed, etc.); **OR**
2. The product is a generic LLM (M365 Copilot, ChatGPT, Claude, Gemini, Bing Chat, Perplexity, Azure OpenAI, AWS Bedrock) **and** the use case description names coding as the primary purpose (refactoring, code translation, COBOL/Java modernization, scripting, IDE-integrated dev work). Incidental "...also generates code snippets" mentions are not enough.

Demote when:

- Generic LLM/chatbot deployed for general staff use with code as one capability among many.
- Title contains "code" but narrative is about classifying offense codes, ICD codes, search queries, etc. (autocoder).
- Low-code/no-code RPA platforms without a developer-assistant component (Power Automate, Copilot Studio).

## Method

1. Pulled all `is_coding_tool=1` rows in `use_case_tags` (73 use_cases-side, 10 consolidated-side).
2. Walked the 15 low-confidence rows from `audit/retag/coding/by_row.csv`.
3. Read `use_case_name`, `problem_statement`, `expected_benefits`, `system_outputs`, `vendor_name`, `system_name` for every borderline row.
4. Two web searches attempted (see `searches.csv`); both resolved against keeping the tag.
5. Did **not** modify the database.

## Impact

| Metric | Count |
|--------|-------|
| Rows currently tagged `is_coding_tool=1` (use_cases + consolidated) | 84 |
| Rows surviving the new rule | 78 |
| Demoted (1 → 0) | 10 |
| Newly promoted from low-confidence Slice A queue (0 → 1) | 4 |
| Net change to `is_coding_tool=1` population | −6 |

## Demotions (10)

| ID | Agency | Use case | Why demoted |
|----|--------|----------|-------------|
| 7802 | DOC | Administrative Tools — meeting/document mgmt + broad code generation | Mixed admin entry; code is one of many capabilities |
| 8043 | DOE | Microsoft CoPilot | Generic M365 Copilot; "writing/coding/research/analysis" boilerplate |
| 8068 | DOE | Claude Anthropic Enterprise | Generic Claude rollout; code listed alongside research/analysis |
| 8072 | DOE | ChatGPT | Generic ChatGPT enterprise rollout |
| 8150 | DOE | Anthropic Claude | Same generic Claude boilerplate |
| 8955 | EPA | AI Assistants in Esri Tools | GIS-analysis assistant; code is one output among tool-use suggestions |
| 10053 | NASA | XMM-GPT | Mission-domain RAG helpdesk; coding is secondary to documentation Q&A |
| 10135 | SBA | Employee Work Prioritization AI Agent | Generic Gemini multi-task assistant |
| 10283 | State | Databricks Code Assistant | Despite product label, narrative is mobile-plan billing analysis |
| 10391 | Treasury | GenAI for Data Platform Operations | Generic platform listing code among many tasks; outputs generic |

## Promotions from Slice A (4)

| ID | Agency | Use case | Why promoted |
|----|--------|----------|--------------|
| 7657 | DOC | Statistical package syntax development and debugging | Title explicit (SAS/R/Stata coding) |
| 7678 | DOC | Scientific Code Development Assistance | Title explicit |
| 9307 | HHS | CSB MCP AI | Output explicitly "infrastructure code generation" (IaC is coding) |
| 10449 | Treasury | Modernization Accelerator — Legacy Applications Code Conversion | Title unambiguous code conversion |

## Slice A rows held at 0 (confirm_drop)

- 8709 DOJ Data Call Code Assist Tool — generates search query terms, not code.
- 9349 HHS T-MSIS Prima — code is one of four output categories; mixed-purpose.
- 9852 NASA Code Assistant Pilot Study — narrative is graph link prediction; title misleading.
- 10396 Treasury LLM Coding for POC — narrative is FAQ chatbot/case deflection.
- 11008 VA BlackBox Code research — retired, no narrative.
- 8027 DOE EnerGPT Canvas — general content tool; code among many outputs.
- 7917 DOE Copilot Studio — citizen-developer / low-code platform, not a developer assistant.

## Agencies most affected

- **DOE**: −4 (M365 Copilot, two Claude rollouts, ChatGPT). Largest single-agency drop. DOE has many lab-level entries that are generic LLM rollouts where staff describe coding as one of several uses; under the strict rule these don't count.
- **NASA**: −1 (XMM-GPT, a mission-specific RAG helpdesk).
- **EPA, SBA, State**: −1 each. Each lost one row that was a generic-purpose LLM or domain analysis tool labeled as a "code assistant".
- **DOC**: net +1 (gained two Slice-A coding-titled rows; lost the broad-admin entry).
- **HHS**: net +1 (gained the CDC infrastructure-as-code row).
- **Treasury**: net 0 (gained the IRS modernization-accelerator title row; lost a generic data-platform row).

## Where the new rule felt aggressive

Three cases where the editorial team should sanity-check:

1. **DOE Claude/ChatGPT enterprise rollouts (8068, 8072, 8150)** — these are big-deployment rows where staff *do* use the tool to write code, but the inventory narrative is a copy-paste boilerplate that says "writing, coding, research, analysis." The rule demotes them because nothing in the description establishes coding as the primary purpose. Reasonable, but the actual user mix likely includes substantial coding work that won't be visible in the article-level claim.
2. **DOE Microsoft Copilot (8043)** — same boilerplate. Microsoft explicitly markets M365 Copilot's developer features; with no narrative-level commitment to coding, demoting feels right under the new rule but understates real usage.
3. **EPA Esri AI Assistants (8955)** — outputs include "code, analysis, suggested tool use." If editors prefer a broader definition that includes domain-tool AI assistants that emit Python/Arcade snippets, this should be re-promoted.

## Recommended editorial framing

The article-level claim should now read along the lines of: "78 federal AI use cases describe coding-specific work" rather than the prior 84. Articles can safely call out: GitHub Copilot, Amazon Q Developer / CodeWhisperer, Gemini Code Assist, Tabnine, Windsurf, AveriSource, Ansible Lightspeed, ServiceNow Now Assist for Creator, Pingwind AI DevOps as the named coding-specific products in the federal inventory. Generic-LLM-for-coding rows (the 12 ED entries, 10 consolidated "Generating code using AI" Appendix B rows, and a handful of agency POCs) are still in the count because their narratives explicitly commit to coding work, but should be characterized as "general-purpose LLMs being applied specifically to code-generation tasks" rather than dedicated developer products.
