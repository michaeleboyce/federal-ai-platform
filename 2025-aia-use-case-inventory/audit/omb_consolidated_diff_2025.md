# OMB Consolidated 2025 ↔ IFP DB Discrepancy Report

_Generated 2026-07-06 10:45_

Source file: `data/raw/2025_individually_reported_AI_use_cases.xlsx`


## Headline counts

| Status | Count |
|---|---:|
| matched_exact | 3524 |
| matched_fuzzy | 25 |
| suggested_rename | 5 |
| omb_only | 0 |
| db_only | 45 |
| duplicate_in_omb | 12 |

## OMB-only — 0 use cases new in OMB file

These use cases appear in the OMB consolidated file but NOT in our DB. Net-new agencies (EAC, FCA, FCC, NEA, NIGC, OSC, OSHRC, PBGC, STB) are entirely listed here.

| Agency | OMB ID | Bureau | Name |
|---|---|---|---|

## DB-only — 45 use cases missing from OMB file

These use cases are in our DB but NOT in the OMB consolidated file. Includes the 4 dropped agencies (FRTIB, GPO, NMB, OPM) plus agency-specific rows that OMB excluded from consolidation.

| Agency | DB ID | Bureau | Name |
|---|---|---|---|
| ED | ED-0009 | Federal Student Aid | Azure AI Internal General Q&A |
| ED | ED-0008 | Federal Student Aid | Comment Categorization |
| ED | ED-0007 | Federal Student Aid | Customer Service Support |
| ED | ED-0011 | Office of the Chief Information Officer | Department-wide implementation of GSA USAi |
| ED | ED-0020 | Institute of Education Sciences | Generative AI - Code Generation |
| ED | ED-0035 | Office of Career, Technical, and Adult E | Generative AI - Text Generation |
| ED | ED-0004 | Office of Migrant Education, Office of E | Grammarly AI Writing Assistant |
| ED | ED-0006 | Office of Postsecondary Education | Legislation Comment Categorization |
| FRTIB | FRTIB-001 | Agency Wide | AVA |
| FRTIB | FRTIB-006 | Agency Wide | Adobe Firefly |
| FRTIB | FRTIB-003 | Agency Wide | Contact Center AI |
| FRTIB | FRTIB-002 | Agency Wide | Fraud Detection Platform |
| FRTIB | FRTIB-004 | Agency Wide | Microsoft CoPilot |
| FRTIB | FRTIB-005 | Agency Wide | Sumtotal Chatbot |
| GPO | 1 |  | Audio Transcription |
| GPO | 7 |  | Cognitive Services search engine (GPO Intranet site) |
| GPO | 8 |  | DevOps |
| GPO | 10 |  | Document Summarization and Text to Podcast Conversion |
| GPO | 5 |  | Internet Browser |
| GPO | 6 |  | Machine Learning (IT Ops) |
| GPO | 9 |  | PII Scanning |
| GPO | 4 |  | Spelling grammar and plagiarism check |
| GPO | 2 |  | Threat Detection |
| GPO | 3 |  | Threat Detection (Cloud-based) |
| NMB | NMB-0004 |  | AI-Powered Proofreading and Editing |
| NMB | NMB-0003 |  | Automated Document Creation |
| NMB | NMB-0001 |  | Document Summarization |
| NMB | NMB-0002 |  | Meeting Transcript Analysis |
| NSF | AII-32 | OLPA | Alt text Generator for Images in NSF's Media Hub |
| NSF | AII-56 | BIO/IOS | Comparison of proposal similarities at different levels of NSF organization |
| NSF | AII-27 | SBE/NCSES | Data Access Alternatives: Artificial Intelligence Supported Interfaces |
| NSF | AII-74 | OIA | ETAP HelpDesk incidents content analysis |
| NSF | AII-26 | TIP-ITE-ENGINES | Enhancing TIP Awards: Efficient Tagging for the 10 Key Technology Areas (KTA) |
| NSF | AII-33 | OIA/EAC | Exploring the use of BERTopic Modeling for a portfolio analysis |
| NSF | AII-30 | OGC | FOIA processing |
| NSF | AII-53 | OIA | M365 AI Builder pre-built GPT for Summarization |
| NSF | AII-48 | OCIO | NSF AI-Ready RPPR Data |
| NSF | AII-72 | BIO/IOS | Open access LLM |
| NSF | AII-49 | TIP & OCIO | TIP MS Copilot Pilot |
| OPM |  | OCIO | Anthropic Claude |
| OPM |  | OCIO | Microsoft Copilot |
| OPM |  | OCIO | OPM Rexi Chatbot |
| OPM |  | OCIO | OpenAI ChatGPT |
| OPM |  | Human Resources | USA Class |
| SBA | SBA-34 | OCIO: Office of the Chief Information Of | Developer Code Assistant AI |

## Suggested renames — 5 (score 0.40–0.85)

OMB row name fuzzy-matches a DB row name within the same agency, but below the auto-link threshold. Most are OMB expanding acronyms (e.g., NSF) or rephrasing. Human review recommended; no auto-link performed.

| Agency | Score | OMB name | DB name |
|---|---:|---|---|
| NSF | 0.83 | Comparison of proposal similarities at different levels of N | Comparison of proposal similarities at different levels of N |
| NSF | 0.78 | Enhancing Technology, Innovation and Partnerships (TIP) Awar | Enhancing TIP Awards: Efficient Tagging for the 10 Key Techn |
| NSF | 0.64 | Microsoft 365 (M365) AI Builder pre-built Generative Pre-tra | M365 AI Builder pre-built GPT for Summarization |
| NSF | 0.52 | NSF AI-Ready Research Performance Progress Reports (RPPR) Da | NSF AI-Ready RPPR Data |
| NSF | 0.43 | Technology, Innovation and Partnerships (TIP) Microsoft (MS) | TIP MS Copilot Pilot |

## Duplicates in OMB file — 8 groups

Same `(agency, bureau, name)` triple appearing twice or more in the OMB consolidated file. The first occurrence is matched against the DB; subsequent occurrences are flagged here.

| Agency | Name | Extra occurrences |
|---|---|---:|
| Treasury | Research / Discovery on GenAI Product for IT | 4 |
| ED | Generative AI - Information Summarization | 2 |
| DOJ | Creating and Maintaining IT Security Packages for Authorizations | 1 |
| ED | Generative AI - Code Generation | 1 |
| ED | Generative AI - Text Generation | 1 |
| HHS | Chatbot | 1 |
| PBGC | Legislative and Regulatory Analysis / Automation (Actuarial/Financial) | 1 |
| SBA | Developer Code Assistant AI | 1 |

## Field drift on matched pairs — 746 pairs affected

Pairs where OMB's value differs from our DB's value on at least one of the 11 canonical fields after normalization (letter prefix, case, curly quotes).

### Drift count by field

| Field | Pairs |
|---|---:|
| have_ato | 438 |
| has_pii | 397 |
| has_custom_code | 391 |
| vendor_name | 241 |
| stage_of_development | 223 |
| contracting_usage | 190 |
| topic_area | 136 |
| is_high_impact | 115 |
| is_withheld | 111 |
| ai_classification | 74 |
| bureau_component | 16 |

### High-impact reclassifications

| Agency | Use case | DB | OMB |
|---|---|---|---|
| DOE | Copilot Studio | c) Not high-impact | a) High-impact |
| DOE | Copilot for Microsoft 365 | c) Not high-impact | a) High-impact |
| ED | Aidan Chat-bot | c) Not high-impact |  |
| ED | CAISY - Artificial Intelligence System Skillsoft Percipio As | c) Not high-impact |  |
| ED | Generative AI - Capability Evaluation | c) Not high-impact |  |
| ED | Generative AI - Capability Evaluation | c) Not high-impact |  |
| ED | Generative AI - Capability Evaluation | c) Not high-impact |  |
| ED | Generative AI - Capability Evaluation | c) Not high-impact |  |
| ED | Generative AI - Capability Evaluation | c) Not high-impact |  |
| ED | Generative AI - Code Generation | c) Not high-impact |  |
| ED | Generative AI - Code Generation | c) Not high-impact |  |
| ED | Generative AI - Code Generation | c) Not high-impact |  |
| ED | Generative AI - Code Generation | c) Not high-impact |  |
| ED | Generative AI - Code Generation | c) Not high-impact |  |
| ED | Generative AI - Code Generation | c) Not high-impact |  |
| ED | Generative AI - Code Generation | c) Not high-impact |  |
| ED | Generative AI - Code Generation | c) Not high-impact |  |
| ED | Generative AI - Code Generation | c) Not high-impact |  |
| ED | Generative AI - Code Generation | c) Not high-impact |  |
| ED | Generative AI - Code Generation | c) Not high-impact |  |
| ED | Generative AI - Data Manipulation | c) Not high-impact |  |
| ED | Generative AI - Design Generation | c) Not high-impact |  |
| ED | Generative AI - Idea Suggestion | c) Not high-impact |  |
| ED | Generative AI - Idea Suggestion | c) Not high-impact |  |
| ED | Generative AI - Idea Suggestion | c) Not high-impact |  |
| ED | Generative AI - Idea Suggestion | c) Not high-impact |  |
| ED | Generative AI - Image Generation | c) Not high-impact |  |
| ED | Generative AI - Information Summarization | c) Not high-impact |  |
| ED | Generative AI - Information Summarization | c) Not high-impact |  |
| ED | Generative AI - Information Summarization | c) Not high-impact |  |
| ED | Generative AI - Information Summarization | c) Not high-impact |  |
| ED | Generative AI - Information Summarization | c) Not high-impact |  |
| ED | Generative AI - Information Summarization | c) Not high-impact |  |
| ED | Generative AI - Information Summarization | c) Not high-impact |  |
| ED | Generative AI - Mock Data Generation | c) Not high-impact |  |
| ED | Generative AI - System Testing | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI - Text Generation | c) Not high-impact |  |
| ED | Generative AI and Foundation Model Integration | c) Not high-impact |  |
| ED | IPAC RPA Bot | c) Not high-impact |  |
| ED | Speech to Text Meeting Transcription | c) Not high-impact |  |
| NCUA | Risk Indicator Model | c) Not high-impact | a) High-impact |
| NCUA | Supervisory Stress Testing | c) Not high-impact | a) High-impact |
| TVA | AI-Enhanced Search | Neither |  |
| TVA | AWS Q | Neither |  |
| TVA | AWS Transcribe | Neither |  |
| TVA | Advanced Network Anomaly Detection | Neither |  |
| TVA | Amazon Connect | Neither |  |
| TVA | ArcGIS | Neither |  |
| TVA | Arkio | Neither |  |
| TVA | Azure FEWS CUA | Neither |  |
| TVA | Azure Nuclear Permitting Solution | Neither |  |
| TVA | Bill of Material | Neither |  |
| TVA | CAP Automation | Neither |  |
| TVA | CAP Enhancement | Neither |  |
| TVA | CESAFCAAllocator | Neither |  |
| TVA | CESASolarModel | Neither |  |
| TVA | COBIT and ATAD Prediction | Neither |  |
| TVA | CR intelligent search | Neither |  |
| TVA | ChatSPP | Neither |  |
| TVA | Cisco ML | Neither |  |
| TVA | Cold-Weather Heat Pump Model | Neither |  |
| TVA | Copilot | Neither |  |
| TVA | Data Services Business Context Definition | Neither |  |
| TVA | Datum | Neither |  |
| TVA | EE/DR Smart Thermostat Impact Model | Neither |  |
| TVA | ESRI GIS AI | Neither |  |
| TVA | EnergyRightDERPortfolioEvaluation | Neither |  |
| TVA | EnergyRightPSPImpactsForecasting | Neither |  |
| TVA | Enscape | Neither |  |
| TVA | Environmental Documentation | Neither |  |
| TVA | Extreme Load Analysis | Neither |  |
| TVA | GET | Neither |  |
| TVA | GET Enhancement | Neither |  |
| TVA | GMET | Neither |  |
| TVA | GMET Enhancement | Neither |  |
| TVA | GMET Multivariate analysis | Neither |  |
| TVA | Generation Project Funding Estimates | Neither |  |
| TVA | Github Copilot | Neither |  |
| TVA | Heliviewer | Neither |  |
| TVA | ICI camera | Neither |  |
| TVA | Land Management Records | Neither |  |
| TVA | Load Forecasting | Neither |  |
| TVA | Materials Intelligent Catalog Assistant | Neither |  |
| TVA | Materials tracking | Neither |  |
| TVA | Natural Reader | Neither |  |
| TVA | Network Anomaly Detection | Neither |  |
| TVA | Non-NPG CAP | Neither |  |
| TVA | Optiwatt EV Load Model | Neither |  |
| TVA | Perimeter Defense | Neither |  |
| TVA | Prism Models for MDM | Neither |  |
| TVA | River Forecast | Neither |  |
| TVA | SEEQ AI | Neither |  |
| TVA | Specification Intelligence | Neither |  |
| TVA | Standard EE/BE Measure Impact Models | Neither |  |
| TVA | TVA Today AI | Neither |  |
| TVA | Talkwalker | Neither |  |
| TVA | Thinklabs | Neither |  |
| TVA | Trade Chat | Neither |  |
| TVA | Transmission analytics | Neither |  |
| TVA | Vegetation Management | Neither |  |
| TVA | Westlaw | Neither |  |

### Stage drift

| Agency | Use case | DB | OMB |
|---|---|---|---|
| CFTC | Anomaly Detection for Data Quality | Operation and Maintenance | c) Deployed – The use case is  |
| CFTC | MPD Entity Risk Modeling | Initiated | b) Pilot – The use case has be |
| CFTC | Stress Testing Scenarios with Deep Learning | Acquisition and/or Development | a) Pre-deployment – The use ca |
| ED | Aidan Chat-bot | c)  Deployed – The use case is |  |
| ED | CAISY - Artificial Intelligence System Skillsoft Percipio As | c)  Deployed – The use case is |  |
| ED | Generative AI - Capability Evaluation | c)  Deployed – The use case is |  |
| ED | Generative AI - Capability Evaluation | c)  Deployed – The use case is |  |
| ED | Generative AI - Capability Evaluation | c)  Deployed – The use case is |  |
| ED | Generative AI - Capability Evaluation | c)  Deployed – The use case is |  |
| ED | Generative AI - Capability Evaluation | c)  Deployed – The use case is |  |
| ED | Generative AI - Code Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Code Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Code Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Code Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Code Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Code Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Code Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Code Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Code Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Code Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Code Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Data Manipulation | c)  Deployed – The use case is |  |
| ED | Generative AI - Design Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Idea Suggestion | c)  Deployed – The use case is |  |
| ED | Generative AI - Idea Suggestion | c)  Deployed – The use case is |  |
| ED | Generative AI - Idea Suggestion | c)  Deployed – The use case is |  |
| ED | Generative AI - Idea Suggestion | c)  Deployed – The use case is |  |
| ED | Generative AI - Image Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Information Summarization | c)  Deployed – The use case is |  |
| ED | Generative AI - Information Summarization | c)  Deployed – The use case is |  |
| ED | Generative AI - Information Summarization | c)  Deployed – The use case is |  |
| ED | Generative AI - Information Summarization | c)  Deployed – The use case is |  |
| ED | Generative AI - Information Summarization | c)  Deployed – The use case is |  |
| ED | Generative AI - Information Summarization | c)  Deployed – The use case is |  |
| ED | Generative AI - Information Summarization | c)  Deployed – The use case is |  |
| ED | Generative AI - Mock Data Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - System Testing | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI - Text Generation | c)  Deployed – The use case is |  |
| ED | Generative AI and Foundation Model Integration | c)  Deployed – The use case is |  |
| ED | IPAC RPA Bot | c)  Deployed – The use case is |  |
| ED | Speech to Text Meeting Transcription | c)  Deployed – The use case is |  |
| EPA | AI Assistants in Esri Tools | b)  b)  Pilot  The use case h | b) Pilot – The use case has be |
| EPA | FFEO TSCA investigation into privatized military housing pro | a) a) Pre-deployment  The use | a) Pre-deployment – The use ca |
| GSA | AI in Public Experience (PX) Contact Center Services Blanket | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | AI-Powered Visibility for Supply and Vendor Risk Resilience | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | ASSIST Auto Copy and Summarize | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | ASSIST ECF Autoclassification and Summary | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | ASSIST Global Search and Inference | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Acquisition Analytics | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | Category Taxonomy Refinement Using NLP | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | ChatOGC | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Content Management Analysis System Pilot | b)  Pilot - The use case has b | b) Pilot – The use case has be |
| GSA | Cybersecurity Chatbot | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Elastic Machine Learning Threat Detection (Phase 1) | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | Elastic Machine Learning Threat Detection (Phase 2) | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | Enterprise Chatbot (GSAi) | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | Enterprise Management Program Management Office Chatbot | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Expedited Transfer of Program of Requirements into Test Fit  | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | FAS Catalog Platform - Image Recognition for Product Photos | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | FAS Catalog Platform - Virtual Assistant | b)  Pilot - The use case has b | b) Pilot – The use case has be |
| GSA | FAS Vision Agentforce | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Gemini for Google Workspace | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | GovCXAnalyzer | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | Improve ASSIST Application Help | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | LaborMatch IQ - Efficient Services Pricing Market Research | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Leasing Desk Guide Bot | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | Leveraging Retrieval Augmented Generation (RAG) AI to Power  | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Login.gov: artificial intelligence technology used for detec | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | Lot Description Generation | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Marketplace: AI Supported Bookings & Space Stacking | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | National Computerized Maintenance Management System (NCMMS)  | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | No-Code Text and Sentiment Analysis with XM Discover | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | OCFO Chatbot | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Office of Civil Rights (OCR) Case Crawler | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | PBS AI Chatbot Domain Enhancements | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | PPMS - Decode Image to Generate Property Description | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Portfolio Analysis LLM | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | Pricing Policy Chatbot | b)  Pilot - The use case has b | b) Pilot – The use case has be |
| GSA | Public Comments Analysis | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | RPA Cloud Connection | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | ReDux Toolkit | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | SINSpector: Using Generative AI to Enforce Scope and Complia | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | ServiceNow Generic Ticket Classification | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | ServiceNow Virtual Agent (Curie) | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | Similar Auction Items Recommendations | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Slack AI | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Software Supply Chain Security Research | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Solicitation Review Tool (SRT) | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | Solicitation Review Tool - Section 508 | a) Pre-deployment - The use ca | a) Pre-deployment – The use ca |
| GSA | Strategic Atlas | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | Tier 1 Use Cases | c)  Deployed - The use case is | c) Deployed – The use case is  |
| GSA | USAi.gov | c)  Deployed - The use case is | c) Deployed – The use case is  |
| NSF | AI voice over | Deployed | b) Pilot – The use case has be |
| NSF | Hand-written text extraction using Textract for the Public E | Deployed | b) Pilot – The use case has be |
| State | Live Consular AI Language Augmentation (LCALA) - Visa Interv | d) Retired  The use case was  | b) Pilot – The use case has be |
| Treasury | 1040X AI Transcription | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | AI Application and Agent Management POC | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | AI Assisted Business Process Mapping | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | AI Contract Document Toolbox | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | AI Use Case Review and Evaluation Workflow | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | AI Voiceover Generation for eLearning Development | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | AI for Schema Development - Online Adaptive Forms | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | AI-Augmented Software Modernization and Insight | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | AI-Driven Predictive Maintenance for Mint Manufacturing Equi | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | AI-Enabled Automated Visual Inspection for Mint Product Qual | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | AI-Powered Enterprise Standard Portfolio (ESP) for End-to-En | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | AI-assisted Procurement POC | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Accounts Management “Balance Due” Call Transcript Classifica | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Advanced Anomaly & Changepoint Detection | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Answering Employee Questions with Natural Language Processin | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Application to AI services integration POC | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Ask-CFO Research Aide | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | AskBEP AI ChatBot | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Automated Document Processing | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | ChatOFR AI Chatbot | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | CoCounsel tool used in the legal office | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | DATA Act Bot for Procurement Data Matching | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Digitalization AI Agent | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Employee Resource Center (ERC) Chatbot | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Employee Retention Credit Text Clustering | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Employee Task Organization | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Enterprise Systems Testing Generative Pre-Trained Transforme | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Establish localized Large Language Model (LLM) | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | F1023 Hybrid NLP and ML Pipeline | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | FORMS AI | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | FRB AI Code Translation POC | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Form 4546 IDR Question-Answering Automation | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Form 990N Machine Learning Model | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Forms Conversion | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Framework Analysis | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | GenAI Procurement Tool | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | GenAI Productivity Tool | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | GenAI Productivity Tool Pilot | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | GenAI Productivity Tool with Web Grounding Pilot | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | GenAI for Data Platform Operations | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | GenAI for Low Code Platform | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Handbook Highlights | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | IDV Model | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | IRS IaaP Accelerator ( AI-Powered Infrastructure as a Produc | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Identity Verification | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Ink and Paper Consumption Forecast (IPCF) | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Integrate Word Processor AI for Digitalization | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Integrated Data Retrieval System Modernization | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Integrated Financial Management Information System (IFMIS) | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Internal Revenue Manual Research Aid (IRMA) | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Inventory Replenishment Forecast | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Joint Committee on Taxation Review Research Aide | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Knowledge Retrieval Chatbot POC | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Large Language Model (LLM) Chatbot for Proof of Concept | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Large Language Model (LLM) Coding for Proof of Concept | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Legislative Analysis Tool | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Line-Item Consolidation for Form 1120 | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Local GenAI Pilot | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Local LLMs Evaluation | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Machine Translation | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Meeting Minute Summarization | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Modular Code Assistant (Explain & Refactor Small Methods) fo | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | NCCBR Data Validation Pilot | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Narrative Summary and Thematic Analysis | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Newsletter Content Support | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | OCC Guidance Summarization | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | OCC Writing Style Adherence | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | OCC.Chat | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | OCC.DocChat | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | OCC.InfoAssist | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Open source Python library and models for NLP | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Operational Support Bots | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Pilot a suite of Fiscal Service Gen AI solutions | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Policy Development Editorial Assistant | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Procurement Data Transparency, Reporting, & Decision Trackin | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Procurement Intelligence | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Procurement Research | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Programmatic Access to LLMs via API | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Public Chatbot | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Public Information Analysis | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Qualitative Text Classification for Analysis | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Regulation Statutory and Common Name Indexing | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Regulation Summarization | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Regulatory Reform Tool | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Regulatory Rule Analysis | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Reporting Requirement Analysis | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Requirements Elaboration Tool | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Research / Discovery on GenAI Product for HR | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Research / Discovery on GenAI Product for IT | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Research Suitability | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Resource Assignment Optimization | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Resume Ranking Engine | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Rulemaking Comment Analytics | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | SBSE - Payments Topics Chatbot | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Safeguards | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Sandbox for Large Language Model Research | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Software Code Generation | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Statistical Information Services Customer Correspondence Ana | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Sub-Asset Maintenance Model | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Survey Analysis | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Synthetic Data Engine | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | TP360 IRM Research Companion | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Tax Disclosure Text Clustering | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Taxpayer Services Chatbot | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Ticket Management Generative AI Pilot | Deployed - The use case is bei | c) Deployed – The use case is  |
| Treasury | Training Content Generation | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Treasury Readability | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | USAspending Natural Language Search Initiative | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Using AI to analyze Taxpayer Burden Survey open-ended respon | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Using Text Summarization for Open-Ended Survey Responses | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Vendor Risk Analytics | Pilot - The use case has been  | b) Pilot – The use case has be |
| Treasury | Visualization Alt-Text Generation | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | Zero Paper AI Routing for Digitalization | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
| Treasury | eDiscovery Software | Pre-Deployment - The use case  | a) Pre-deployment – The use ca |
