# Uncertain rows — recommended human review before apply

These rows are flagged either because validation surfaced a concrete error/warning, or because
their proposed action carries some interpretive risk. The apply script will:

- **Block** (skip) any row with `validation_status` starting with `error_` until resolved.
- **Apply with reduced confidence** any row with `warning_` validation status.
- **Apply normally** medium-confidence relinks (gated by the standard apply policy), but they
  are listed here so a human can audit a sample first.

Total flagged: **206** items.

| Category | use_case_id | entry | agency | use-case | what is uncertain | proposed action |
|---|---|---|---|---|---|---|
| `warning_pk_collision` | 129046 | use_case | DOE | Microsoft 365 Copilot (Productivity Suite) | validation flag | relink → Microsoft 365 Copilot (high) |
| `warning_pk_collision` | 129049 | use_case | DOE | Microsoft Power Platform capability that provides AI to auto | validation flag | relink → Microsoft Power Platform (high) |
| `warning_pk_collision` | 129054 | use_case | DOE | Microsoft Copilot for Security | validation flag | relink → Microsoft Copilot for Security (high) |
| `warning_pk_collision` | 129057 | use_case | DOE | Copilot Studio | validation flag | relink → Microsoft Copilot Studio (high) |
| `warning_pk_collision` | 129062 | use_case | DOE | Copilot for Microsoft 365 | validation flag | relink → Microsoft 365 Copilot (high) |
| `warning_pk_collision` | 129069 | use_case | DOE | Hanford Search | validation flag | relink → Azure OpenAI (high) |
| `warning_pk_collision` | 129071 | use_case | DOE | Hanford Popfon Search | validation flag | relink → Azure OpenAI (high) |
| `warning_pk_collision` | 129081 | use_case | DOE | Hanford  Service Ticket Lookup | validation flag | relink → Azure OpenAI (high) |
| `warning_pk_collision` | 129084 | use_case | DOE | Hanford Procedure Search | validation flag | relink → Azure OpenAI (high) |
| `warning_pk_collision` | 129103 | use_case | DOE | Microsoft Bing Service | validation flag | relink → Microsoft Search in Bing (high) |
| `warning_pk_collision` | 129105 | use_case | DOE | Microsoft Azure Quantum Elements | validation flag | relink → Microsoft Azure Quantum Elements (high) |
| `warning_pk_collision` | 129111 | use_case | DOE | Visual Studio Enterprise | validation flag | relink → Visual Studio Enterprise (high) |
| `warning_pk_collision` | 129117 | use_case | DOE | Microsoft OneNote | validation flag | relink → Microsoft OneNote (high) |
| `warning_pk_collision` | 129126 | use_case | DOE | AI Builder Document Scraping | validation flag | relink → Microsoft AI Builder (high) |
| `warning_pk_collision` | 129127 | use_case | DOE | Microsoft Azure Authoring Tools | validation flag | relink → Microsoft Azure Authoring Tools (high) |
| `warning_pk_collision` | 129146 | use_case | DOE | Microsoft Project | validation flag | relink → Microsoft Project (high) |
| `warning_pk_collision` | 129167 | use_case | DOE | Microsoft Copilot | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 129172 | use_case | DOE | GitHub Copilot | validation flag | relink → GitHub Copilot (high) |
| `warning_pk_collision` | 129186 | use_case | DOE | Microsoft Teams | validation flag | relink → Microsoft Teams (high) |
| `warning_pk_collision` | 129190 | use_case | DOE | Microsoft Search in Bing | validation flag | relink → Microsoft Search in Bing (high) |
| `warning_pk_collision` | 129191 | use_case | DOE | Microsoft Copilot (Pilot) | validation flag | relink → Microsoft 365 Copilot (high) |
| `warning_pk_collision` | 129194 | use_case | DOE | Microsoft Teams Classic | validation flag | relink → Microsoft Teams (high) |
| `warning_pk_collision` | 129220 | use_case | DOE | Visual Studio Community | validation flag | relink → Visual Studio (high) |
| `warning_pk_collision` | 129223 | use_case | DOE | Microsoft OneDrive | validation flag | relink → Microsoft OneDrive (high) |
| `warning_pk_collision` | 129234 | use_case | DOE | Microsoft Discovery | validation flag | relink → Microsoft Discovery (high) |
| `warning_pk_collision` | 129239 | use_case | DOE | Microsoft 365 | validation flag | relink → Microsoft 365 (high) |
| `warning_pk_collision` | 129258 | use_case | DOE | Microsoft OneDrive MUI | validation flag | relink → Microsoft OneDrive (high) |
| `warning_pk_collision` | 129271 | use_case | DOE | Microsoft AI Builder | validation flag | relink → Microsoft AI Builder (high) |
| `warning_pk_collision` | 129273 | use_case | DOE | Microsoft 365 Apps for Enterprise | validation flag | relink → Microsoft 365 Apps for Enterprise (high) |
| `warning_pk_collision` | 129277 | use_case | DOE | Microsoft Outlook MUI | validation flag | relink → Microsoft Outlook (high) |
| `warning_pk_collision` | 129283 | use_case | DOE | Microsoft Edge | validation flag | relink → Microsoft Edge (high) |
| `warning_pk_collision` | 129296 | use_case | DOE | SQL Server Management Studio | validation flag | relink → SQL Server Management Studio (high) |
| `warning_pk_collision` | 129297 | use_case | DOE | Microsoft Exchange Server | validation flag | relink → Microsoft Exchange Server (high) |
| `warning_pk_collision` | 129307 | use_case | DOE | Microsoft Skype App | validation flag | relink → Microsoft Skype (high) |
| `warning_pk_collision` | 129320 | use_case | DOE | CoPilot | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 129321 | use_case | DOE | Microsoft OneNote MUI | validation flag | relink → Microsoft OneNote (high) |
| `warning_pk_collision` | 129324 | use_case | DOE | Microsoft Copilot Studio | validation flag | relink → Microsoft Copilot Studio (high) |
| `warning_pk_collision` | 129327 | use_case | DOE | Microsoft PowerPoint MUI | validation flag | relink → Microsoft PowerPoint (high) |
| `warning_pk_collision` | 129331 | use_case | DOE | Microsoft Power BI Desktop | validation flag | relink → Microsoft Power BI (high) |
| `warning_pk_collision` | 129332 | use_case | DOE | Microsoft Azure PowerShell | validation flag | relink → Microsoft Azure PowerShell (high) |
| `warning_pk_collision` | 129365 | use_case | DOI | USGS Azure OpenAI ChatGPT [2024 INV#WO0000000154392] | validation flag | relink → Azure OpenAI (high) |
| `warning_pk_collision` | 129567 | use_case | DOI | Microsoft eDiscovery Attorney-Client Privilege Detection | validation flag | relink → Microsoft Purview eDiscovery (high) |
| `warning_pk_collision` | 129584 | use_case | DOI | Non-Generative AI use for Trust Information Analysis and Rep | validation flag | relink → Azure AI Document Intelligence (high) |
| `warning_pk_collision` | 129585 | use_case | DOI | Integration of AI, specifically CoPilot for GitHub,  for BTF | validation flag | relink → GitHub Copilot (high) |
| `warning_pk_collision` | 129591 | use_case | DOJ | Azure Data Factory | validation flag | relink → Azure Data Factory (high) |
| `warning_pk_collision` | 129592 | use_case | DOJ | Azure Zen 2 Storage | validation flag | relink → Microsoft Azure Platform (high) |
| `warning_pk_collision` | 129631 | use_case | DOJ | Azure Platform/Tools - Network Routing | validation flag | relink → Microsoft Azure Platform (high) |
| `warning_pk_collision` | 129808 | use_case | DOJ | Knowledge retrieval and synthesis (Azure OpenAI Services) | validation flag | relink → Azure OpenAI (high) |
| `warning_pk_collision` | 129848 | use_case | DOJ | Azure AI Foundry Platform | validation flag | relink → Azure AI Foundry (high) |
| `warning_pk_collision` | 130019 | use_case | ED | MS Copilot - Document Creation & Editing | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130020 | use_case | ED | MS Copilot - Summarization | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130021 | use_case | ED | MS Copilot - Data Analysis & Insights | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130022 | use_case | ED | MS Copilot - Process & Workflow Automation | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130023 | use_case | ED | MS Copilot - Compliance & Risk Management | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130024 | use_case | ED | MS Copilot - Collaboration & Communication | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130025 | use_case | ED | MS Copilot - Research & Knowledge Management | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130026 | use_case | ED | MS Copilot - Training & Education | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130027 | use_case | ED | MS Copilot - Project & Task Management | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130028 | use_case | ED | MS Copilot - Content Organization & Archiving | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130029 | use_case | ED | MS Copilot - Grant & Program Management | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130030 | use_case | ED | MS Copilot - Security & Privacy | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130031 | use_case | ED | MS Copilot - Business Process Improvement | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130032 | use_case | ED | MS Copilot - Technical Assistance & Code Generation | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130033 | use_case | ED | MS Copilot - Creative & Productive Work Enhancement | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 130070 | use_case | FDIC | AI Assisted Data Collection | validation flag | relink → Microsoft Power Platform (high) |
| `warning_pk_collision` | 130176 | use_case | FRTIB | Microsoft CoPilot | validation flag | relink → Microsoft 365 Copilot (high) |
| `warning_pk_collision` | 130188 | use_case | FTC | Microsoft 365 Copilot | validation flag | relink → Microsoft 365 Copilot (high) |
| `warning_pk_collision` | 130278 | use_case | HHS | Acquisition support: co-drafting acquisition packages | validation flag | relink → Microsoft 365 Copilot Chat (high) |
| `warning_pk_collision` | 130279 | use_case | HHS | Acquisition support: assisting reviews and co-drafting techn | validation flag | relink → Microsoft 365 Copilot Chat (high) |
| `warning_pk_collision` | 130679 | use_case | HHS | Enhancing the RCDC with Generative AI | validation flag | relink → Azure OpenAI (high) |
| `warning_pk_collision` | 130706 | use_case | HUD | Microsoft Copilot | validation flag | relink → Microsoft 365 Copilot (high) |
| `warning_pk_collision` | 131025 | use_case | NASA | Intelligent Chatbot for Science using Microsoft Copilot | validation flag | relink → Microsoft 365 Copilot (medium) |
| `warning_pk_collision` | 131158 | use_case | NRC | Support routine administrative tasks and enhancing communica | validation flag | relink → Microsoft 365 Copilot Chat (high) |
| `warning_pk_collision` | 131177 | use_case | NSF | TIP MS Copilot Pilot | validation flag | relink → Microsoft 365 Copilot (high) |
| `warning_pk_collision` | 131193 | use_case | SBA | Meeting Minutes Summary Tool | validation flag | relink → Microsoft Teams (high) |
| `warning_pk_collision` | 131210 | use_case | SBA | Security Team Productivity Enhancement | validation flag | relink → Microsoft Copilot for Security (high) |
| `warning_pk_collision` | 131300 | use_case | SSA | Speech to Text Video Transcription | validation flag | relink → Azure Speech (high) |
| `warning_pk_collision` | 131316 | use_case | SSA | General Use Chatbot | validation flag | relink → Microsoft 365 Copilot Chat (high) |
| `warning_pk_collision` | 131645 | use_case | USDA | Axon+ Copilot Studio Chatbot | validation flag | relink → Microsoft Copilot Studio (high) |
| `warning_pk_collision` | 132081 | use_case | VA | Microsoft Power Automate and AI | validation flag | relink → Microsoft Power Platform (high) |
| `warning_pk_collision` | 26075 | consolidated | HHS | Generating first drafts of documents, briefing, or communica | validation flag | relink → Microsoft 365 Copilot Chat (high) |
| `warning_pk_collision` | 26079 | consolidated | HHS | Using AI-assisted tools in word processors. | validation flag | relink → Microsoft 365 Copilot (high) |
| `warning_pk_collision` | 26235 | consolidated | VA | Generating first drafts of documents, briefing, or communica | validation flag | relink → Microsoft 365 Copilot Chat (high) |
| `warning_pk_collision` | 128976 | use_case | DOC | LLM support for NIST research (Google Vertex) | validation flag | relink → Google Vertex AI (high) |
| `warning_pk_collision` | 129151 | use_case | DOE | Google Chrome Generative AI | validation flag | relink → Google Chrome Generative AI (high) |
| `warning_pk_collision` | 129176 | use_case | DOE | Google Agentspace / NotebookLM | validation flag | relink → Google Agentspace (high) |
| `warning_pk_collision` | 129363 | use_case | DOI | Google Cloud Vision [2024 INV#WO0000000154445] | validation flag | relink → Google Cloud Vision (high) |
| `warning_pk_collision` | 129364 | use_case | DOI | Google Vertex AI Document workbench [2024 INV#WO000000015439 | validation flag | relink → Google Vertex AI (high) |
| `warning_pk_collision` | 129703 | use_case | DOJ | Google Translate | validation flag | relink → Google Translate (high) |
| `warning_pk_collision` | 129711 | use_case | DOJ | reCAPTCHA | validation flag | relink → reCAPTCHA (high) |
| `warning_pk_collision` | 129995 | use_case | DOT | Conversational Multi-modal Chatbot (Google Gemini) | validation flag | relink → Gemini (high) |
| `warning_pk_collision` | 129996 | use_case | DOT | Report Sumarization (Google NotebookLM) | validation flag | relink → NotebookLM (high) |
| `warning_pk_collision` | 130613 | use_case | HHS | Alphafold | validation flag | relink → AlphaFold (high) |
| `warning_pk_collision` | 130634 | use_case | HHS | Protein Modeling with AlphaFold | validation flag | relink → AlphaFold (high) |
| `warning_pk_collision` | 130711 | use_case | NARA | Generative AI Solutions for Workplace Productivity (aka Gemi | validation flag | relink → Gemini (high) |
| `warning_pk_collision` | 131041 | use_case | NASA | JSC SMA NT Paper WAD Data Extraction | validation flag | relink → Gemini (high) |
| `warning_pk_collision` | 131160 | use_case | NRC | Testing industry leading generative AI foundational large la | validation flag | relink → Gemini (high) |
| `warning_pk_collision` | 131214 | use_case | SBA | Employee Work Prioritization AI Agent | validation flag | relink → Gemini (high) |
| `warning_pk_collision` | 131638 | use_case | USDA | IOL Focus Group and Survey Sensemaking | validation flag | relink → NotebookLM (high) |
| `warning_pk_collision` | 131667 | use_case | USDA | Digital Soil Mapping | validation flag | relink → Google Earth Engine (high) |
| `warning_pk_collision` | 128968 | use_case | DOC | Amazon Q Developer Pilot | validation flag | relink → Amazon Q (high) |
| `warning_pk_collision` | 129092 | use_case | DOE | LANL AI Portal | validation flag | relink → Amazon Web Services (high) |
| `warning_pk_collision` | 129769 | use_case | DOJ | Voicemail Transcription, Translation and Summarization | validation flag | relink → AWS Transcribe (medium) |
| `warning_pk_collision` | 129906 | use_case | DOL | PII Redaction | validation flag | relink → Amazon Comprehend (high) |
| `warning_pk_collision` | 129907 | use_case | DOL | Workforce Recruitment Program (WRP) Website Chatbot Assistan | validation flag | relink → AWS Lex (high) |
| `warning_pk_collision` | 130191 | use_case | FTC | IVR Automated Voice Assistant | validation flag | relink → AWS Lex (medium) |
| `warning_pk_collision` | 131118 | use_case | NASA | GLOBE Program - Image processing | validation flag | relink → AWS Rekognition (high) |
| `warning_pk_collision` | 131219 | use_case | SBA | Developer Code Assistant AI | validation flag | relink → Amazon Q (high) |
| `warning_pk_collision` | 26077 | consolidated | HHS | Summarizing the key points of a lengthy report using AI. | validation flag | relink → Gemini (high) |
| `warning_pk_collision` | 26080 | consolidated | HHS | Generating code using AI. | validation flag | relink → Amazon Q (high) |
| `warning_pk_collision` | 26740 | consolidated | SBA | Generating code using AI. | validation flag | relink → Amazon Q (high) |
| `warning_pk_collision` | 129612 | use_case | DOJ | Thomson Reuters CLEAR | validation flag | relink → Thomson Reuters CLEAR (high) |
| `warning_pk_collision` | 129628 | use_case | DOJ | Thomson Reuters CLEAR - License Plate Recognition | validation flag | relink → Thomson Reuters CLEAR (high) |
| `warning_pk_collision` | 129669 | use_case | DOJ | Westlaw (AI assisted legal research) | validation flag | relink → Westlaw AI (high) |
| `warning_pk_collision` | 129791 | use_case | DOJ | ProLaw | validation flag | relink → ProLaw (high) |
| `warning_pk_collision` | 129838 | use_case | DOJ | Cocounsel AI | validation flag | relink → CoCounsel (high) |
| `warning_pk_collision` | 130077 | use_case | FDIC | Generative Artificial Intelligence (AI) for Legal Research | validation flag | relink → Westlaw AI (high) |
| `warning_pk_collision` | 130118 | use_case | FERC | AI Enabled Assistant Legal Research | validation flag | relink → Westlaw AI (medium) |
| `warning_pk_collision` | 129586 | use_case | DOJ | Adobe Suite Applications | validation flag | relink → Adobe Creative Cloud Suite (medium) |
| `warning_pk_collision` | 129874 | use_case | DOJ | Adobe Premiere | validation flag | relink → Adobe Premiere Pro (high) |
| `warning_pk_collision` | 129875 | use_case | DOJ | Adobe Photoshop | validation flag | relink → Adobe Photoshop (high) |
| `warning_pk_collision` | 130178 | use_case | FRTIB | Adobe Firefly | validation flag | relink → Adobe Firefly (high) |
| `warning_pk_collision` | 131317 | use_case | SSA | Training Audio and Video Generation | validation flag | relink → Adobe Firefly (high) |
| `warning_pk_collision` | 132085 | use_case | VA | Adobe Creative Cloud | validation flag | relink → Adobe Creative Cloud Suite (high) |
| `warning_pk_collision` | 26053 | consolidated | DOE | Editing images, videos, or other public affairs materials us | validation flag | relink → Adobe Creative Cloud Suite (high) |
| `warning_pk_collision` | 26353 | consolidated | FDIC | Editing images, videos, or other public affairs materials us | validation flag | relink → Adobe Photoshop (medium) |
| `warning_pk_collision` | 26633 | consolidated | NTSB | Editing images, videos, or other public affairs materials us | validation flag | relink → Adobe Creative Cloud Suite (high) |
| `warning_pk_collision` | 26713 | consolidated | SEC | Editing images, videos, or other public affairs materials us | validation flag | relink → Adobe Firefly (high) |
| `warning_pk_collision` | 129619 | use_case | DOJ | Veritone Illuminate | validation flag | relink → Veritone Illuminate (high) |
| `warning_pk_collision` | 130128 | use_case | FHFA | Security and network monitoring using Cisco Identify Service | validation flag | relink → Cisco Identity Services Engine (high) |
| `multi_product_vendor` | 130112 | use_case | FDIC | OIG computer forensics investigation tools. | vendor_name lists multiple products: "Adobe, Auto Split, Microsoft, Scan Writer, Social Discovery" | delete_or_inferred →  (high) |
| `multi_product_vendor` | 130278 | use_case | HHS | Acquisition support: co-drafting acquisition packages | vendor_name lists multiple products: "Credal, Ask Sage, Microsoft" | relink → Microsoft 365 Copilot Chat (high) |
| `multi_product_vendor` | 130279 | use_case | HHS | Acquisition support: assisting reviews and co-drafting techn | vendor_name lists multiple products: "Credal, Ask Sage, Microsoft" | relink → Microsoft 365 Copilot Chat (high) |
| `multi_product_vendor` | 130640 | use_case | HHS | Notebooks Hub | vendor_name lists multiple products: "Axle Informatics, Microsoft, OpenAI" | relink → Azure OpenAI (high) |
| `multi_product_vendor` | 130641 | use_case | HHS | Ask Aithena | vendor_name lists multiple products: "Axle Informatics, Microsoft, OpenAI" | relink → Azure OpenAI (high) |
| `multi_product_vendor` | 131335 | use_case | State | Data.State Analytics and AI Funhouse | vendor_name lists multiple products: "Microsoft, Databricks, ZenPoint" | relink → Azure OpenAI (high) |
| `multi_product_vendor` | 26075 | consolidated | HHS | Generating first drafts of documents, briefing, or communica | vendor_name lists multiple products: "Microsoft 365 Copilot Chat, Microsoft 365 Copilot, AWS, ChatGPT, Gemini, xAI gov, CHIRP, Claude, EndNote, Microsoft Azure, Synthesia, Zotero, Credal + Claude and GPT API" | relink → Microsoft 365 Copilot Chat (high) |
| `multi_product_vendor` | 26079 | consolidated | HHS | Using AI-assisted tools in word processors. | vendor_name lists multiple products: "Microsoft Word, Microsoft 365 Copilot, Grammarly, ChatGPT, Gemini, Signals ELN" | relink → Microsoft 365 Copilot (high) |
| `multi_product_vendor` | 26235 | consolidated | VA | Generating first drafts of documents, briefing, or communica | vendor_name lists multiple products: "Power Automate AI Builder, Microsoft Dynamics D365 CoPilot, Microsoft Copilot Chat" | relink → Microsoft 365 Copilot Chat (high) |
| `multi_product_vendor` | 26340 | consolidated | FCC | Generating code using AI. | vendor_name lists multiple products: "Microsoft Copilot, 
AWS Q Developer, 
Microsoft Azure Open AI" | relink → Azure OpenAI (high) |
| `multi_product_vendor` | 26353 | consolidated | FDIC | Editing images, videos, or other public affairs materials us | vendor_name lists multiple products: "Photoshop, Adobe Premier, Microsoft Paint Limited Copilot" | relink → Microsoft 365 Copilot (medium) |
| `multi_product_vendor` | 26520 | consolidated | NASA | Generating code using AI. | vendor_name lists multiple products: "Azure, Alteryx, Microsoft Power Suite, Windsurf" | relink → Microsoft Azure Platform (high) |
| `cross_vendor_babel_street` | 129604 | use_case | DOJ | LexisNexis Babel Street | cross-vendor Babel Street row, flagged by slice C | delete_or_inferred →  (medium) |
| `medium_relink` | 129167 | use_case | DOE | Microsoft Copilot | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 129320 | use_case | DOE | CoPilot | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130019 | use_case | ED | MS Copilot - Document Creation & Editing | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130020 | use_case | ED | MS Copilot - Summarization | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130021 | use_case | ED | MS Copilot - Data Analysis & Insights | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130022 | use_case | ED | MS Copilot - Process & Workflow Automation | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130023 | use_case | ED | MS Copilot - Compliance & Risk Management | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130024 | use_case | ED | MS Copilot - Collaboration & Communication | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130025 | use_case | ED | MS Copilot - Research & Knowledge Management | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130026 | use_case | ED | MS Copilot - Training & Education | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130027 | use_case | ED | MS Copilot - Project & Task Management | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130028 | use_case | ED | MS Copilot - Content Organization & Archiving | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130029 | use_case | ED | MS Copilot - Grant & Program Management | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130030 | use_case | ED | MS Copilot - Security & Privacy | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130031 | use_case | ED | MS Copilot - Business Process Improvement | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130032 | use_case | ED | MS Copilot - Technical Assistance & Code Generation | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130033 | use_case | ED | MS Copilot - Creative & Productive Work Enhancement | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 130130 | use_case | FHFA | Analytics, Indexing, and Anomaly Detection for Data Manageme | medium-confidence relink — verify proposal | relink → SQL Server Management Studio (medium) |
| `medium_relink` | 130392 | use_case | HHS | Federal Select Agents Program (FSAP) Customer Agent | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 131025 | use_case | NASA | Intelligent Chatbot for Science using Microsoft Copilot | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 131194 | use_case | SBA | Business Development | medium-confidence relink — verify proposal | relink → Azure OpenAI (medium) |
| `medium_relink` | 26353 | consolidated | FDIC | Editing images, videos, or other public affairs materials us | medium-confidence relink — verify proposal | relink → Microsoft 365 Copilot (medium) |
| `medium_relink` | 128810 | use_case | DOC | Google Public Sector NLP, Classification, Text Mining | medium-confidence relink — verify proposal | relink → Google Cloud Platform (medium) |
| `medium_relink` | 129416 | use_case | DOI | Machine Learning Image Classification of Wetlands and Soil m | medium-confidence relink — verify proposal | relink → Google Earth Engine (medium) |
| `medium_relink` | 130009 | use_case | ED | Generative AI - Text Generation | medium-confidence relink — verify proposal | relink → Google Cloud Platform (medium) |
| `medium_relink` | 130010 | use_case | ED | Generative AI - Code Generation | medium-confidence relink — verify proposal | relink → Google Cloud Platform (medium) |
| `medium_relink` | 130011 | use_case | ED | Generative AI - Idea Suggestion | medium-confidence relink — verify proposal | relink → Google Cloud Platform (medium) |
| `medium_relink` | 130012 | use_case | ED | Generative AI - Information Summarization | medium-confidence relink — verify proposal | relink → Google Cloud Platform (medium) |
| `medium_relink` | 130013 | use_case | ED | Generative AI - Design Generation | medium-confidence relink — verify proposal | relink → Google Cloud Platform (medium) |
| `medium_relink` | 130014 | use_case | ED | Generative AI - Data Manipulation | medium-confidence relink — verify proposal | relink → Google Cloud Platform (medium) |
| `medium_relink` | 130015 | use_case | ED | Generative AI - Mock Data Generation | medium-confidence relink — verify proposal | relink → Google Cloud Platform (medium) |
| `medium_relink` | 130016 | use_case | ED | Generative AI - System Testing | medium-confidence relink — verify proposal | relink → Google Cloud Platform (medium) |
| `medium_relink` | 130017 | use_case | ED | Generative AI - Capability Evaluation | medium-confidence relink — verify proposal | relink → Google Cloud Platform (medium) |
| `medium_relink` | 130018 | use_case | ED | Generative AI - Image Generation | medium-confidence relink — verify proposal | relink → Google Cloud Platform (medium) |
| `medium_relink` | 131596 | use_case | USDA | Rangeland Analysis Platform | medium-confidence relink — verify proposal | relink → Google Earth Engine (medium) |
| `medium_relink` | 129047 | use_case | DOE | NLCOO AI for Lessons Learned tool | medium-confidence relink — verify proposal | relink → Amazon Web Services (medium) |
| `medium_relink` | 129769 | use_case | DOJ | Voicemail Transcription, Translation and Summarization | medium-confidence relink — verify proposal | relink → AWS Transcribe (medium) |
| `medium_relink` | 130191 | use_case | FTC | IVR Automated Voice Assistant | medium-confidence relink — verify proposal | relink → AWS Lex (medium) |
| `medium_relink` | 130118 | use_case | FERC | AI Enabled Assistant Legal Research | medium-confidence relink — verify proposal | relink → Westlaw AI (medium) |
| `medium_relink` | 129586 | use_case | DOJ | Adobe Suite Applications | medium-confidence relink — verify proposal | relink → Adobe Creative Cloud Suite (medium) |
| `medium_relink` | 26353 | consolidated | FDIC | Editing images, videos, or other public affairs materials us | medium-confidence relink — verify proposal | relink → Adobe Photoshop (medium) |
| `keep_strong` | 129629 | use_case | DOJ | Veritone | kept as strong on bare-vendor — verify source is truly generic | keep_strong →  (high) |
| `keep_strong` | 130187 | use_case | FTC | Relativity Integrated Veritone | kept as strong on bare-vendor — verify source is truly generic | keep_strong →  (medium) |
| `keep_strong` | 129037 | use_case | DOE | AI techniques for identification of suitable delivery parkin | kept as strong on bare-vendor — verify source is truly generic | keep_strong →  (high) |
| `keep_strong` | 131412 | use_case | TVA | Cisco ML | kept as strong on bare-vendor — verify source is truly generic | keep_strong →  (medium) |
| `inferred_vocab_b` | 128713 | use_case | DHS | GenAI for Document Summarization and Content Generation | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 130053 | use_case | EPA | Semantic search of qualitative data | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 130280 | use_case | HHS | AHRQ Search | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 130582 | use_case | HHS | NanCI: Connecting Scientists | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 130609 | use_case | HHS | NIH Grants Virtual Assistant | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 130758 | use_case | NASA | HyperMapping with Hyperspectral Precise Pointing Optical Sen | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 130938 | use_case | NASA | Development of real-time high-resolution air quality maps th | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 131132 | use_case | NASA | XMM-GPT | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 131182 | use_case | NSF | Open access LLM | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 131270 | use_case | SEC | Enhancing Analysis of SEC Web Engagement Trends Using AI | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 131331 | use_case | State | DS-5528 Promissory Note Automation | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 131687 | use_case | USDA | Forest Plan review and planning support | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 131688 | use_case | USDA | TreeSearch | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 131689 | use_case | USDA | Infosec Chatbot | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 131995 | use_case | VA | App feedback model for NLP tasks | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 26281 | consolidated | EPA | Searching for agency information using a knowledge retrieval | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 26645 | consolidated | NTSB | Curating news articles and updates based on user preferences | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |
| `inferred_vocab_b` | 26717 | consolidated | SEC | Summarizing the key points of a lengthy report using AI. | slice_b used DB-vocab "inferred" for confidence; treated as medium-equivalent for gating | delete_or_inferred → Google (inferred) |

## Spot-check sample (10 random high-confidence relinks)

| use_case_id | agency | proposed | result | evidence preview |
|---|---|---|---|---|
| 129630 | DOJ | Amazon Web Services | pass | AWS/cloud.gov -  Network Routing... |
| 129626 | DOJ | Microsoft Azure Platform | pass | ding (LUIS) services which is developed using the Microsoft Azure Software As A ... |
| 128722 | DHS | Azure OpenAI | pass | Leverages Azure Commercial OpenAI within the FEMA system boundary, currently lev... |
| 130640 | HHS | Azure OpenAI | pass | Axle Informatics, Microsoft, OpenAI... |
| 130117 | FERC | Microsoft Azure Platform | pass | Microsoft Azure Commercial... |
| 130113 | FERC | Microsoft Azure Platform | pass | Microsoft Azure Commercial... |
| 129735 | DOJ | Azure Speech | pass | Speech to Text Managed Service - Voice Transcription to Text... |
| 129178 | DOE | Azure OpenAI | pass | neral purpose chatbot using government instances of popular Open AI models.... |
| 129059 | DOE | Gemini | pass | Google's Gemini familiy of models.... |
| 129136 | DOE | Azure AI Document Intelligence | pass | Azure Document Intelligence... |

**Spot-check verdict: 10/10 pass.**