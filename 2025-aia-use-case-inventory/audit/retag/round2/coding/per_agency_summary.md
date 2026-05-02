# Per-agency `is_coding_tool=1` before/after — Round 2

Counts include both `use_cases` and `consolidated_use_cases` rows. "Before" = current DB state at start of round 2. "After" = state if all decisions in `resolved.csv` are applied.

| Agency | Before | After | Δ | Notes |
|--------|-------:|------:|--:|-------|
| CSOSA | 1 | 1 | 0 | Appendix B template entry |
| DHS | 5 | 5 | 0 | All custom/dev tools (CodeGen, OCFO Code Assist, Palantir AIP) |
| DOC | 8 | 9 | +1 | Gained 7657, 7678 from Slice A; lost 7802 broad-admin row |
| DOE | 12 | 8 | −4 | Lost generic M365/ChatGPT/Claude rollouts (8043, 8068, 8072, 8150) |
| DOI | 2 | 2 | 0 | ChatGPT for code optimization + GitHub Copilot |
| DOJ | 2 | 2 | 0 | GitHub Copilot + Legacy Code Modernization |
| DOL | 1 | 1 | 0 | Appendix B template entry |
| EAC | 1 | 1 | 0 | Appendix B template entry |
| ED | 13 | 13 | 0 | All 12 "Generative AI - Code Generation" entries + MS Copilot Tech Assistance (all explicit coding focus) |
| EPA | 1 | 0 | −1 | Esri ArcGIS AI Assistants demoted (GIS-analysis tool) |
| FCC | 1 | 1 | 0 | Appendix B template entry |
| FDIC | 1 | 1 | 0 | Appendix B template entry (GitHub Copilot, Appian) |
| HHS | 9 | 10 | +1 | Gained 9307 CSB MCP AI (IaC) |
| HUD | 1 | 1 | 0 | Appendix B template entry |
| NASA | 3 | 2 | −1 | Lost XMM-GPT (mission helpdesk RAG) |
| NLRB | 1 | 1 | 0 | Appendix B template entry (GitHub Copilot) |
| NSF | 1 | 1 | 0 | Amazon CodeWhisperer |
| OSC | 1 | 1 | 0 | Appendix B template entry |
| PBGC | 1 | 1 | 0 | Appendix B template entry |
| SBA | 4 | 3 | −1 | Lost Employee Work Prioritization AI Agent (generic Gemini) |
| SSA | 2 | 2 | 0 | AveriSource + Windsurf |
| State | 2 | 1 | −1 | Lost Databricks Code Assistant (mobile-plan billing analysis) |
| Treasury | 6 | 6 | 0 | Gained 10449; lost 10391 (data platform ops); kept IRS modernization rows |
| TVA | 1 | 1 | 0 | GitHub Copilot |
| USITC | 1 | 1 | 0 | Appendix B template entry (M365 Copilot) |
| USTDA | 1 | 1 | 0 | Appendix B template entry |
| VA | 2 | 2 | 0 | Ansible Lightspeed + VetsEZ |
| **Total** | **84** | **78** | **−6** | 10 demoted, 4 promoted |

## Net effect on article-level claims

- "Federal agencies tagging coding tools": **27 agencies before, 26 after** (EPA drops out — it had only the one Esri row).
- Concentration: **GitHub Copilot** remains the dominant named product (≈18 distinct use case rows across DHS, DOC, DOE, DOI, DOJ, FDIC, HHS, NLRB, SBA, TVA, plus consolidated entries). **Amazon Q Developer / CodeWhisperer** appears at DOC, NSF, SBA, FCC. **Gemini Code Assist** at DOC (twice). **Tabnine** at DOE (twice). **AveriSource, Windsurf** at SSA. **Ansible Lightspeed** at VA. **Pingwind AI DevOps** at HHS. **ServiceNow Now Assist for Creator** at HHS.
