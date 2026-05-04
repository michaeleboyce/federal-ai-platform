"""Seed the products, product_aliases, and use_case_templates tables."""

from db import get_connection

# (canonical_name, vendor, product_type, is_genai, is_frontier_llm, parent, description, aliases)
PRODUCTS = [
    # Microsoft Copilot family
    # Bare "Copilot" alias intentionally omitted — it was matching GitHub Copilot,
    # Copilot for Security, Copilot Studio, Salesforce Copilot, etc. Aliases here
    # are Microsoft-specific shorthand. Longer-alias-first means "Microsoft Copilot
    # for Security" / "Microsoft Copilot Studio" still win over plain "Microsoft
    # Copilot" when both could match.
    ("Microsoft 365 Copilot", "Microsoft", "general_llm", 1, 1, None,
     "Microsoft's enterprise LLM assistant integrated with Office apps",
     ["M365 Copilot", "Microsoft M365 Copilot", "Microsoft M365 Copilot AI",
      "Microsoft Copilot for M365", "Microsoft 365 Copilot",
      "Copilot for Microsoft 365", "M365 CoPilot",
      "Microsoft 365 CoPilot", "M365 copilot", "Copilot Enterprise",
      "Microsoft Copilot Enterprise",
      # COTS-file shorthand (2025 OMB consolidated COTS file)
      "Microsoft Copilot", "Microsoft CoPilot", "Microsoft365 Copilot",
      "Copilot for MS 365", "Microsoft Copilot 365", "MS Copilot",
      "MS 365 Copilot", "Microsoft 365 Copilot GCC", "Microsoft Copilot GCC",
      "Microsoft 365 apps"]),
    ("Microsoft 365 Copilot Chat", "Microsoft", "general_llm", 1, 1, "Microsoft 365 Copilot",
     "The free in-app Copilot chat tier within Microsoft 365 (distinct from the paid M365 Copilot SKU)",
     ["M365 Copilot Chat", "Microsoft Copilot Chat", "Microsoft 365 Copilot Chat",
      "Copilot Chat"]),
    ("Microsoft Copilot for Security", "Microsoft", "security_tool", 1, 0, None,
     "Microsoft's GenAI-assisted security operations copilot",
     ["Copilot for Security", "Microsoft Copilot for Security",
      "Security Copilot", "Microsoft Security Copilot"]),
    ("Microsoft Copilot Studio", "Microsoft", "agent_platform", 1, 0, None,
     "Low-code platform for building custom copilots and agents",
     ["Copilot Studio", "Microsoft Copilot Studio", "Power Virtual Agents"]),
    ("GitHub Copilot", "Microsoft", "coding_assistant", 1, 0, "Microsoft 365 Copilot",
     "AI pair programmer for code generation",
     ["GitHub CoPilot", "GitHub Copilot", "Github Copilot", "GitHub copilot", "GH Copilot"]),
    ("Microsoft Teams", "Microsoft", "productivity", 0, 0, None,
     "Collaboration platform with AI features",
     ["Teams", "Microsoft Teams", "MS Teams", "Microsoft Teams Premium"]),
    ("Microsoft Defender", "Microsoft", "security_tool", 0, 0, None,
     "Endpoint security with ML-based threat detection",
     ["Microsoft Defender", "MS Defender", "Defender"]),
    ("Azure OpenAI", "Microsoft", "general_llm", 1, 1, None,
     "OpenAI models hosted on Azure",
     ["Azure OpenAI", "Azure OpenAI Service", "OpenAI on Azure"]),

    # OpenAI
    ("ChatGPT", "OpenAI", "general_llm", 1, 1, None,
     "OpenAI's conversational AI assistant",
     ["ChatGPT", "GPT-4", "GPT-4o", "OpenAI ChatGPT", "ChatGPT Enterprise", "ChatGPT Plus"]),
    ("OpenAI API", "OpenAI", "general_llm", 1, 1, None,
     "Direct OpenAI API access (non-Azure)",
     ["OpenAI", "OpenAI API"]),

    # Anthropic
    ("Claude", "Anthropic", "general_llm", 1, 1, None,
     "Anthropic's conversational AI",
     ["Claude", "Anthropic", "Anthropic Claude", "Claude.ai", "Claude 3", "Claude 3.5", "Claude Sonnet", "Claude Opus"]),
    ("Claude Code", "Anthropic", "coding_assistant", 1, 0, "Claude",
     "Anthropic's coding agent",
     ["Claude Code"]),

    # Google
    ("Gemini", "Google", "general_llm", 1, 1, None,
     "Google's conversational AI",
     ["Gemini", "Google Gemini", "Bard", "Gemini Pro", "Gemini 1.5", "Gemini 2",
      "Gemini for Google Workspace", "Gemini for Workspace",
      "Gemini Code Assist", "Gemini Advanced"]),
    ("NotebookLM", "Google", "general_llm", 1, 0, "Gemini",
     "Google's Gemini-powered research notebook for document Q&A and synthesis",
     ["NotebookLM", "Notebook LM", "Google NotebookLM"]),
    ("Google Lens", "Google", "computer_vision", 1, 0, None,
     "Google's image-recognition product",
     ["Google Lens"]),
    ("Google Workspace", "Google", "productivity", 0, 0, None,
     "Google's productivity suite",
     ["Google Workspace", "GSuite"]),

    # Amazon
    ("Amazon Q", "Amazon", "general_llm", 1, 1, None,
     "Amazon's enterprise AI assistant",
     ["AWS Q", "Amazon Q", "Q Developer", "Q Business"]),
    ("Amazon CodeWhisperer", "Amazon", "coding_assistant", 1, 0, None,
     "Amazon's AI coding assistant",
     ["CodeWhisperer", "Amazon CodeWhisperer", "AWS CodeWhisperer"]),
    ("AWS Transcribe", "Amazon", "nlp_specific", 0, 0, None,
     "Speech-to-text service",
     ["AWS Transcribe", "Amazon Transcribe"]),
    ("AWS Bedrock", "Amazon", "general_llm", 1, 1, None,
     "Amazon's managed foundation model service",
     ["Bedrock", "AWS Bedrock", "Amazon Bedrock"]),

    # Legal / research
    ("Westlaw AI", "Thomson Reuters", "legal_research", 1, 0, None,
     "Legal research with AI",
     ["Westlaw", "Thomson Reuters/Westlaw Drafting Assistant", "Westlaw AI", "Westlaw Precision",
      "Thomson Reuters Westlaw"]),
    ("Lexis+ AI", "LexisNexis", "legal_research", 1, 0, None,
     "Legal research AI",
     ["Lexis+ AI", "LexisNexis AI", "Lexis Advance"]),

    # ITSM/workflow
    ("ServiceNow Now Assist", "ServiceNow", "productivity", 1, 0, None,
     "ServiceNow's GenAI features",
     ["ServiceNow", "ServiceNow (Now Assist)", "Now Assist", "ServiceNow Now Assist"]),
    ("Grammarly", "Grammarly", "productivity", 0, 0, None,
     "Writing assistant",
     ["Grammarly", "Grammarly Business"]),

    # Meeting / admin
    ("Otter.ai", "Otter", "productivity", 1, 0, None,
     "Meeting transcription",
     ["Otter", "Otter.ai"]),
    ("Calendly", "Calendly", "productivity", 0, 0, None,
     "AI-enabled scheduling",
     ["Calendly"]),
    ("Reclaim.AI", "Reclaim", "productivity", 1, 0, None,
     "AI calendar management",
     ["Reclaim.AI", "Reclaim"]),
    ("SAP Concur", "SAP", "productivity", 0, 0, None,
     "Travel and expense",
     ["SAP Concur", "Concur"]),

    # News/monitoring
    ("Meltwater", "Meltwater", "productivity", 0, 0, None,
     "Media monitoring with AI",
     ["Meltwater"]),

    # Security
    ("Crowdstrike Falcon", "Crowdstrike", "security_tool", 0, 0, None,
     "Endpoint security with ML",
     ["Crowdstrike", "Crowdstrike Falcon", "Falcon"]),
    ("Splunk", "Splunk", "security_tool", 0, 0, None,
     "SIEM with ML analytics",
     ["Splunk"]),
    ("Zscaler", "Zscaler", "security_tool", 0, 0, None,
     "Cloud security platform",
     ["Zscaler"]),
    ("Palo Alto Networks", "Palo Alto Networks", "security_tool", 0, 0, None,
     "Network security",
     ["Palo Alto", "Palo Alto Networks"]),

    # Data/analytics platforms
    ("Databricks", "Databricks", "ml_platform", 1, 0, None,
     "ML platform",
     ["Databricks"]),
    ("Snowflake Cortex", "Snowflake", "ml_platform", 1, 0, None,
     "Snowflake's AI features",
     ["Snowflake Cortex", "Snowflake AI"]),

    # Specialized
    ("Esri ArcGIS AI", "Esri", "nlp_specific", 0, 0, None,
     "GIS with AI features",
     ["ArcGIS", "ESRI GIS AI", "Esri", "Esri ArcGIS"]),
    ("Adobe Firefly", "Adobe", "computer_vision", 1, 0, None,
     "Image generation",
     ["Adobe Firefly", "Firefly"]),
    ("Adobe Photoshop", "Adobe", "computer_vision", 1, 0, None,
     "Image editing with generative fill and other AI features",
     ["Adobe Photoshop", "Photoshop"]),

    # Agent D (plan §D.3): four missing products evidenced in data.
    ("AWS Textract", "Amazon", "computer_vision", 0, 0, None,
     "Amazon's document text-extraction / OCR service",
     ["AWS Textract", "Amazon Textract", "Textract"]),
    ("Airtable AI", "Airtable", "productivity", 1, 0, None,
     "Airtable's embedded AI (OpenAI-backed) for low-code databases",
     ["Airtable AI", "Airtable's AI", "Airtable"]),
    ("WellSaid Labs", "WellSaid Labs", "nlp_specific", 1, 0, None,
     "Synthetic voice / text-to-speech platform",
     ["WellSaid Labs", "Wellsaid Labs", "WellSaid", "Wellsaid"]),

    # ---- Products evidenced in 2025 OMB consolidated COTS file (May 2026 audit) ----
    # GenAI tools
    ("DALL-E", "OpenAI", "computer_vision", 1, 0, "ChatGPT",
     "OpenAI's image generation model",
     ["DALL-E", "DALLE", "DALL E", "Dall-E"]),
    ("Perplexity", "Perplexity AI", "general_llm", 1, 1, None,
     "Conversational answer engine",
     ["Perplexity", "Perplexity AI", "Perplexity.ai"]),
    ("Ask Sage", "Ask Sage", "general_llm", 1, 0, None,
     "GenAI platform authorized for federal/DoD use",
     ["AskSage", "Ask Sage", "ask-sage"]),
    ("Cursor", "Anysphere", "coding_assistant", 1, 0, None,
     "AI-native code editor",
     ["Cursor", "Cursor AI"]),
    ("Poolside", "Poolside", "coding_assistant", 1, 0, None,
     "AI coding assistant",
     ["Poolside", "poolside.ai"]),
    ("Synthesia", "Synthesia", "computer_vision", 1, 0, None,
     "AI video generation with avatars",
     ["Synthesia"]),
    ("Canva", "Canva", "productivity", 1, 0, None,
     "Design platform with generative AI features (Magic Studio)",
     ["Canva", "Canva Magic Studio"]),

    # Productivity / SaaS with AI
    ("Sprout Social", "Sprout Social", "productivity", 1, 0, None,
     "Social media management with AI",
     ["Sprout Social", "SproutSocial"]),
    ("FS Pro", "FS Pro", "productivity", 1, 0, None,
     "Foreign Service productivity tool used at the Department of State",
     ["FS Pro", "FSPro"]),
    ("Asana", "Asana", "productivity", 1, 0, None,
     "Work-management platform with Asana Intelligence (GenAI)",
     ["Asana", "Asana Intelligence"]),
    ("Monday.com", "monday.com", "productivity", 1, 0, None,
     "Work-OS with monday AI features",
     ["Monday.com", "monday.com", "Monday AI"]),
    ("Slack", "Salesforce", "productivity", 1, 0, None,
     "Team messaging with Slack AI",
     ["Slack", "Slack AI"]),
    ("Zoom", "Zoom", "productivity", 1, 0, None,
     "Video conferencing with Zoom AI Companion",
     ["Zoom", "Zoom AI", "Zoom AI Companion"]),
    ("BioRender", "BioRender", "productivity", 1, 0, None,
     "Scientific diagramming tool with AI assist",
     ["BioRender", "Biorender"]),

    # Data / analytics
    ("Alteryx", "Alteryx", "ml_platform", 1, 0, None,
     "Self-service analytics platform with embedded AI",
     ["Alteryx"]),
    ("Tableau", "Salesforce", "ml_platform", 1, 0, None,
     "Visualization platform with Tableau Pulse / Tableau GPT AI features",
     ["Tableau", "Tableau Pulse", "Tableau GPT", "Tableau Enterprise Visualization"]),
    ("Palantir AIP", "Palantir", "ml_platform", 1, 0, None,
     "Palantir's AI Platform",
     ["Palantir", "Palantir AIP", "AIP"]),

    # Security
    ("Microsoft Purview", "Microsoft", "security_tool", 0, 0, None,
     "Data governance and compliance with ML classification",
     ["Microsoft Purview", "Purview"]),
    ("SentinelOne", "SentinelOne", "security_tool", 0, 0, None,
     "Endpoint security with ML-based threat detection",
     ["SentinelOne", "Sentinel One"]),
    ("Wiz", "Wiz", "security_tool", 0, 0, None,
     "Cloud security with AI-driven risk prioritization",
     ["Wiz"]),
    ("Magnet Forensics", "Magnet Forensics", "security_tool", 1, 0, None,
     "Digital forensics platform with Magnet Copilot AI features",
     ["Magnet Forensics", "Magnet Copilot"]),
    # Consumer features (track as products with consumer_feature type so dashboards
    # can opt in/out of vendor-share charts that should focus on enterprise tools).
    ("Apple Face ID", "Apple", "consumer_feature", 0, 0, None,
     "Apple's on-device facial recognition for device unlock",
     ["Apple iPhone", "Apple Iphone", "iPhone Face ID", "Face ID"]),
    ("Apple Maps", "Apple", "consumer_feature", 0, 0, None,
     "Apple Maps with AI-powered routing",
     ["Apple Maps"]),
    ("Google Maps", "Google", "consumer_feature", 0, 0, None,
     "Google Maps with AI-powered routing",
     ["Google Maps"]),
    ("Google Pixel", "Google", "consumer_feature", 0, 0, None,
     "Google Pixel with on-device AI features (Face Unlock, Magic Eraser)",
     ["Google Pixel"]),

    # ---- Catalog expansion (May 2026) — 76 products surfaced by the
    # 3-agent review-queue pass over the 80 alias proposals.
    # See audit/review_queue_resolution/catalog_seed.py for the source
    # of truth and the agent's triage rationale.
    ('ARC Travel Intelligence', 'Airlines Reporting Corporation', 'investigative_data', 0, 0, None,
     "ARC's Travel Intelligence Program provides commercial air travel data analytics used for law-enforcement and investigative work.",
     ['Airlines Reporting Corporation Travel Intelligence Program', 'ARC Travel Intelligence Program', 'ARC TIP']),
    ('AWS Translate', 'Amazon Web Services', 'translation', 1, 0, None,
     "Amazon's neural machine translation service for translating text between languages.",
     ['AWS Translate', 'Amazon Translate']),
    ('Amazon Alexa', 'Amazon', 'nlp', 0, 0, None,
     "Amazon's voice assistant platform supporting custom skills and voice-driven applications.",
     ['Amazon Alexa', 'Alexa', 'Amazon Alexa Skill', 'Alexa Skill']),
    ('Amazon Connect', 'Amazon Web Services', 'nlp', 1, 0, None,
     'AWS cloud contact center with built-in AI for IVR, transcription, sentiment, and agent assist.',
     ['Amazon Connect', 'AWS Connect']),
    ('Aretec EDP', 'Aretec', 'data_analytics', 0, 0, None,
     'Aretec-built Enterprise Data Platform used at the SEC for analytics and ML workloads, distinct from NEAT.',
     ['Aretec EDP', 'EDP', 'SEC EDP', 'Enterprise Data Platform (Aretec)']),
    ('Aretec SEARCH', 'Aretec', 'search', 0, 0, None,
     'Aretec-built SEARCH platform used at the SEC for full-text and analytical search across regulatory filings; sibling to NEAT and EDP.',
     ['Aretec SEARCH', 'SEARCH', 'SEC SEARCH']),
    ('AttackIQ', 'AttackIQ', 'security_tool', 0, 0, None,
     'Breach-and-attack-simulation platform that uses ML to validate security controls against MITRE ATT&CK techniques.',
     ['AttackIQ']),
    ('Aware Biometrics', 'Aware', 'biometrics', 0, 0, None,
     "Aware's biometric platform providing facial, fingerprint, and multimodal recognition.",
     ['Aware', 'Aware Biometrics', 'Aware Inc']),
    ('Axon Evidence', 'Axon', 'forensics', 1, 0, None,
     'Digital evidence management platform (evidence.com) with AI-driven redaction, transcription, and video retention used by law enforcement.',
     ['Axon Evidence', 'Axon Evidence.com', 'Evidence.com', 'Axon Video Retention Solution (VRS)', 'Axon VRS', 'Axon Evidence Redaction', 'Axon Evidence Digital Evidence Management']),
    ('Axon FUSUS', 'Axon', 'physical_security', 0, 0, 'Axon Evidence',
     'Real-time crime center platform that integrates camera feeds, sensors, and analytics for law-enforcement situational awareness.',
     ['Axon FUSUS', 'FUSUS']),
    ('Azure Data Factory', 'Microsoft', 'data_analytics', 0, 0, None,
     'Microsoft Azure data integration service with embedded AI features such as anomaly detection and data-quality scoring.',
     ['Azure Data Factory', 'ADF']),
    ('BD Pyxis MedStation', 'Becton Dickinson', 'clinical_decision_support', 0, 0, None,
     'Automated medication-dispensing system with predictive analytics for inventory and diversion detection.',
     ['BD Pyxis', 'BD Pyxis MedStation', 'Pyxis MedStation']),
    ('Bloomberg Government', 'Bloomberg', 'investigative_data', 0, 0, None,
     'Bloomberg Government (BGOV) provides policy, regulatory, and procurement analytics for federal stakeholders.',
     ['Bloomberg Government', 'BGOV', 'Bloomberg Government (BGOV)']),
    ('BriefCatch', 'BriefCatch', 'legal_research', 1, 0, None,
     'AI-powered legal-writing editor that suggests style, citation, and clarity improvements to briefs and memoranda.',
     ['BriefCatch', 'Lawcatch BriefCatch']),
    ('Broadcom Code for Z', 'Broadcom', 'code_modernization', 1, 0, None,
     'Mainframe code-modernization tool providing AI-assisted analysis and refactoring of COBOL and z/OS applications.',
     ['Broadcom Code for Z', 'Code for Z']),
    ('Buzzsprout CoHost AI', 'Buzzsprout', 'media_analysis', 1, 0, None,
     "Buzzsprout's CoHost AI generates podcast titles, descriptions, transcripts, and chapter markers from uploaded audio.",
     ['CoHost AI', 'Buzzsprout CoHost', 'Buzzsprout CoHost AI']),
    ('CargoNet', 'Verisk', 'investigative_data', 0, 0, None,
     'Verisk CargoNet aggregates cargo theft incident data and applies analytics to predict and disrupt supply-chain crime.',
     ['CargoNet', 'Verisk CargoNet']),
    ('Cell Hawk', 'LeadsOnline', 'investigative_data', 0, 0, None,
     'LeadsOnline Cell Hawk parses and visualizes call detail records and tower data for investigations.',
     ['Cell Hawk', 'CellHawk', 'LeadsOnline Cell Hawk']),
    ('Cisco Identity Services Engine', 'Cisco', 'security_tool', 0, 0, None,
     'Cisco ISE network access control platform that uses ML for device profiling and posture assessment.',
     ['Cisco Identity Services Engine', 'Cisco ISE', 'Cisco Identify Services engine', 'ISE']),
    ('Cisco Secure Network Analytics', 'Cisco', 'security_tool', 0, 0, None,
     "Cisco's network detection-and-response platform (formerly Stealthwatch) using ML to surface anomalous network behavior.",
     ['Cisco Secure Network Analytics', 'Stealthwatch', 'Cisco Stealthwatch']),
    ('Cloudflare Turnstile', 'Cloudflare', 'security_tool', 0, 0, None,
     "Cloudflare's privacy-preserving bot detection and CAPTCHA-replacement service.",
     ['Cloudflare Turnstile', 'Turnstile']),
    ('CoCounsel', 'Thomson Reuters', 'legal_research', 1, 0, None,
     'Thomson Reuters CoCounsel is a generative AI legal assistant for research, document review, and drafting.',
     ['CoCounsel', 'Cocounsel AI', 'Thomson Reuters CoCounsel', 'Casetext CoCounsel']),
    ('Cofense PhishMe', 'Cofense', 'security_tool', 0, 0, None,
     "Cofense's phishing simulation and reporting platform with ML-based threat triage.",
     ['Cofense', 'Cofense PhishMe', 'PhishMe']),
    ('Conductor Conduit AI', 'Conductor', 'document_ai', 1, 0, None,
     "Conductor's Conduit AI platform for document review and litigation workflows.",
     ['Conduit AI', 'Conductor Conduit AI']),
    ('Critical Mention', 'Critical Mention', 'media_analysis', 0, 0, None,
     'Real-time broadcast and online media monitoring with transcription and sentiment analysis.',
     ['Critical Mention']),
    ('DeepEMhancer', 'Open source (CSIC)', 'scientific_ml', 0, 0, None,
     'Deep-learning post-processing tool that sharpens and denoises CryoEM density maps.',
     ['DeepEMhancer']),
    ('Descript', 'Descript', 'media_analysis', 1, 0, None,
     'AI-powered audio and video editor with transcription, voice cloning, and text-based editing.',
     ['Descript']),
    ('Dun & Bradstreet', 'Dun & Bradstreet', 'investigative_data', 0, 0, None,
     'Dun & Bradstreet business establishments and risk data with AI-driven anomaly and fraud-detection analytics.',
     ['Dun & Bradstreet', 'D&B', 'Dun & Bradstreet Business Establishments Data']),
    ('ELSAG ALPR', 'Leonardo', 'computer_vision', 0, 0, None,
     'Leonardo ELSAG license-plate-reader cameras and back-end analytics used by law enforcement.',
     ['ELSAG', 'ELSAG/Leonardo', 'ELSAG ALPR', 'Leonardo ELSAG']),
    ('Elastic Stack', 'Elastic', 'search', 0, 0, None,
     'Elastic Stack (Elasticsearch, Logstash, Kibana) for search, analytics, and observability with built-in ML jobs.',
     ['Elastic Stack', 'Elastic Stack Technology (ELK)', 'ELK', 'ELK Stack', 'Elasticsearch']),
    ('Elsa (FDA)', 'FDA (internal, vendor-supported)', 'general_llm', 1, 0, None,
     "FDA's Elsa is an internal generative AI assistant used by FDA staff for document drafting and search.",
     ['Elsa', 'Elsa GenAI Chat Tool', 'FDA Elsa']),
    ('EnerGPT', 'Unknown / DOE-targeted vendor', 'general_llm', 1, 0, None,
     'DOE-targeted generative AI assistant tuned for energy-domain queries; vendor not yet confirmed in inventory text.',
     ['EnerGPT']),
    ('Fiji ImageJ', 'Open source (NIH ImageJ / Fiji community)', 'scientific_ml', 0, 0, None,
     'Fiji is the bundled ImageJ distribution for scientific image analysis; widely used with ML plugins for microscopy.',
     ['FIJI', 'Fiji', 'Fiji ImageJ', 'ImageJ']),
    ('FirstTwo', 'FirstTwo', 'investigative_data', 0, 0, None,
     'Geospatial OSINT platform that aggregates address, person, and location data for investigative lookups.',
     ['FirstTwo', 'First Two', 'FirstTwo / First Two']),
    ('Flock Safety', 'Flock Safety', 'computer_vision', 0, 0, None,
     'Cloud-based license-plate-reader and camera network with AI vehicle and behavior analytics for law enforcement.',
     ['Flock Safety', 'Flock', 'Flock LPR']),
    ('Genetec Security Center', 'Genetec', 'physical_security', 0, 0, None,
     'Unified physical-security platform with video management, access control, and AI-driven video analytics.',
     ['Genetec', 'Genetec Security Center']),
    ('Griffeye Analyze', 'Griffeye', 'forensics', 0, 0, None,
     'Forensic media analysis platform used by law enforcement to triage CSAM and other illicit imagery with classifiers.',
     ['Griffeye', 'Griffeye Analyze']),
    ('Harvey', 'Harvey', 'legal_research', 1, 0, None,
     'Domain-specific generative AI legal assistant for law firms and legal departments.',
     ['Harvey', 'harvey.ai', 'Harvey AI']),
    ('Hootsuite', 'Hootsuite', 'social_listening', 1, 0, None,
     'Social media management platform with AI-assisted content generation and analytics.',
     ['Hootsuite']),
    ('IBM watsonx Code Assistant', 'IBM', 'coding_assistant', 1, 0, None,
     'IBM watsonx Code Assistant including the Code Assistant for Z mainframe modernization variant.',
     ['IBM watsonx Code Assistant', 'IBM WatsonX Code Assistant', 'watsonx Code Assistant', 'watsonx Code Assistant for Z']),
    ('ISO ClaimSearch', 'Verisk', 'investigative_data', 0, 0, None,
     'Verisk ISO ClaimSearch is the all-claims database with analytics used by NICB and insurers to detect fraud.',
     ['ISO ClaimSearch', 'National Insurance Crime Bureau ISO ClaimSearch', 'NICB ISO ClaimSearch']),
    ('Imaris', 'Oxford Instruments', 'scientific_ml', 0, 0, None,
     'Imaris microscopy image-analysis software with ML-based segmentation and tracking.',
     ['Imaris', 'Oxford Instruments Imaris']),
    ('LaserAI', 'LaserAI', 'document_ai', 1, 0, None,
     'Commercial systematic-review automation product that uses ML to screen and extract from scientific literature.',
     ['LaserAI', 'Laser AI']),
    ('Lenel OnGuard', 'LenelS2 (Honeywell)', 'physical_security', 0, 0, None,
     'Lenel OnGuard physical access control system with analytics for credential and intrusion events.',
     ['Lenel', 'Lenel OnGuard', 'OnGuard']),
    ('Lexis+ Protege', 'LexisNexis', 'legal_research', 1, 0, 'Lexis+ AI',
     'LexisNexis Protege is a personalized generative AI legal assistant; distinct from the broader Lexis+ AI platform.',
     ['Lexis Protege', 'Lexis+ Protege', 'Protege']),
    ('Litera TOA Builder', 'Litera', 'legal_research', 0, 0, None,
     'Litera (formerly Levit & James) Word plugin for automated table-of-authorities and legal document drafting.',
     ['Litera TOA Builder', 'Levit & James Word plugin', 'Levit & James', 'TOA Builder']),
    ('Lumivero NVivo', 'Lumivero', 'data_analytics', 1, 0, None,
     'NVivo qualitative data analysis tool with AI-assisted coding and theme detection.',
     ['NVivo', 'Lumivero NVivo', 'Lumivero, NVivo']),
    ('Mark43', 'Mark43', 'investigative_data', 1, 0, None,
     'Cloud-based public-safety records management and CAD platform with AI-assisted report writing.',
     ['Mark43', 'Mark43 Public Safety Records', 'Mark43 RMS']),
    ('Milestone XProtect', 'Milestone Systems', 'physical_security', 0, 0, None,
     'Milestone XProtect video management software with integrated AI analytics for object and event detection.',
     ['Milestone', 'Milestone XProtect', 'XProtect']),
    ('ModelAngelo', 'Open source (MRC LMB)', 'scientific_ml', 0, 0, None,
     'Deep-learning tool for automated atomic-model building from CryoEM density maps.',
     ['ModelAngelo', 'Model Angelo']),
    ('NetDocuments', 'NetDocuments', 'document_ai', 1, 0, None,
     'Cloud document and email management for legal/professional services with predictive filing and GenAI features.',
     ['NetDocuments']),
    ('Nlets LPR Pointer Index', 'Nlets', 'investigative_data', 0, 0, None,
     'Nlets-operated nationwide license-plate-reader pointer index that federates LPR hits across state and local systems.',
     ['Nlets Nationwide License Plate Reader Pointer Index', 'Nlets LPR Pointer Index', 'Nlets LPR']),
    ('Nuance Dragon', 'Nuance (Microsoft)', 'transcription', 0, 0, None,
     'Nuance Dragon professional speech recognition and dictation product family.',
     ['Dragon', 'Nuance Dragon', 'Dragon NaturallySpeaking', 'Dragon Professional']),
    ('OnCue Trial Presentation', 'OnCue Technology', 'legal_research', 0, 0, None,
     'Trial presentation software used by litigators to organize and display exhibits and transcripts in court.',
     ['OnCue', 'OnCue Technology', 'OnCue Trial Presentation']),
    ('PDRI Automatically-Scored Writing Assessment', 'PDRI', 'nlp_specific', 0, 0, None,
     "PDRI's commercial automatically-scored writing assessment used in federal hiring and selection.",
     ['PDRI AWA', 'Personnel Decisions Research Institutes, LLC (PDRI)', 'PDRI Automatically-Scored Writing Assessment']),
    ('Pearson Q-interactive', 'Pearson', 'clinical_decision_support', 0, 0, None,
     "Pearson's tablet-based platform for administering and scoring psychological and cognitive assessments.",
     ['Pearson Assessments', 'Pearson Q-interactive', 'Q-interactive']),
    ('Plexis Quantum Choice', 'Plexis', 'data_analytics', 0, 0, None,
     'Plexis Quantum Choice claims adjudication and benefits-administration platform with rules and ML.',
     ['Quantum Choice from Plexis', 'Plexis Quantum Choice', 'Quantum Choice']),
    ('ProLaw', 'Thomson Reuters', 'legal_research', 0, 0, None,
     'Thomson Reuters ProLaw legal practice management with integrated search and AI features.',
     ['ProLaw', 'Thomson Reuters ProLaw']),
    ('Ptolemy', 'Open source', 'scientific_ml', 0, 0, None,
     'Open-source CryoEM micrograph screening and triage tool using ML.',
     ['Ptolemy']),
    ('Qualtrics', 'Qualtrics', 'data_analytics', 1, 0, None,
     'Experience-management and survey platform with AI-driven sentiment, topic, and text analytics.',
     ['Qualtrics', 'Qualtrics XM']),
    ('RWS Trados', 'RWS', 'translation', 1, 0, None,
     'Trados is a leading computer-assisted translation suite with neural MT and translation-memory features.',
     ['RWS Trados', 'Trados', 'SDL Trados']),
    ('Rangeland Analysis Platform', 'University of Montana / NRCS', 'scientific_ml', 0, 0, None,
     'Public Rangeland Analysis Platform on Google Cloud providing remote-sensing-derived rangeland vegetation models.',
     ['Rangeland Analysis Platform', 'RAP']),
    ('Rank One Computing', 'Rank One Computing', 'biometrics', 0, 0, None,
     'Rank One Computing face recognition and biometric SDK used in identity and law-enforcement deployments.',
     ['Rank One Computing', 'Rank One', 'ROC']),
    ('Raytheon BBN M3S', 'Raytheon BBN', 'media_analysis', 0, 0, None,
     "Raytheon BBN's Multimedia Monitoring System (M3S) ingests and analyzes broadcast and online media for situational awareness.",
     ['Raytheon Multimedia Monitoring System (M3S)', 'M3S', 'Raytheon BBN M3S']),
    ('SAS Analytics', 'SAS', 'data_analytics', 0, 0, None,
     'SAS statistical analytics and ML platform used across federal agencies for classification and risk modeling.',
     ['SAS', 'SAS Analytics', 'SAS Viya', 'SAS Enterprise Miner']),
    ('ShotSpotter', 'SoundThinking', 'audio_analysis', 0, 0, None,
     'SoundThinking ShotSpotter acoustic gunshot detection and localization service for law enforcement.',
     ['ShotSpotter', 'SoundThinking ShotSpotter']),
    ('Smiths Detection TruNarc', 'Smiths Detection', 'forensics', 0, 0, None,
     'Handheld Raman-spectroscopy narcotics analyzer with onboard classification of controlled substances.',
     ['TruNarc', 'Smiths Detection TruNarc', 'TruNarc, Smiths Detection']),
    ('Spokeo', 'Spokeo', 'investigative_data', 0, 0, None,
     'Spokeo people-search service aggregating public records for investigative lookups.',
     ['Spokeo']),
    ('TLOxp', 'TransUnion', 'investigative_data', 0, 0, None,
     'TransUnion TLOxp investigative search platform that links person, asset, and association records for due diligence.',
     ['TLOxp', 'TLO', 'TransUnion TLOxp']),
    ('Techsmith Audiate', 'TechSmith', 'media_analysis', 1, 0, None,
     'TechSmith Audiate is a text-based audio editor with AI transcription and voice cleanup.',
     ['Audiate', 'Techsmith Audiate', 'TechSmith Audiate']),
    ('TekSynap SimplifAI', 'TekSynap', 'general_llm', 1, 0, None,
     "TekSynap's SimplifAI commercial generative AI platform sold to federal customers.",
     ['TekSynap SimplifAI', 'SimplifAI']),
    ('Topaz CryoEM', 'Open source', 'scientific_ml', 0, 0, None,
     'Topaz is a deep-learning-based particle-picking tool for CryoEM data.',
     ['Topaz', 'Topaz CryoEM', 'Topaz Picker']),
    ('Trunet Biometrics', 'Advanced Technologies Group', 'biometrics', 0, 0, None,
     'Advanced Technologies Group Trunet biometric capture and matching system.',
     ['Trunet', 'Trunet Systems', 'Trunet Biometrics']),
    ('Unison PRISM', 'Unison', 'supply_chain', 0, 0, None,
     'Unison PRISM federal procurement and acquisition platform with embedded analytics.',
     ['Unison', 'Unison PRISM', 'PRISM']),
    ('Verkada', 'Verkada', 'physical_security', 0, 0, None,
     'Cloud-managed video surveillance, access control, and sensor platform with on-camera AI analytics.',
     ['Verkada']),
    ('reCAPTCHA', 'Google', 'security_tool', 0, 0, None,
     'Google reCAPTCHA bot detection service that uses behavioral signals and risk scoring.',
     ['reCAPTCHA', 'Google reCAPTCHA']),
    # Catch-all categories
    ("Custom In-House AI", "In-House", "custom", 1, 0, None,
     "Agency-built custom AI systems",
     ["In-house", "Custom", "Developed in-house", "In-House"]),
]


# OMB standard use case templates
TEMPLATES = [
    ("Generating first drafts of documents, briefing, or communication materials using AI.",
     "document_drafting", "writing"),
    ("Summarizing the key points of a lengthy report using AI.",
     "document_summarization", "writing"),
    ("Searching for agency information using a knowledge retrieval system.",
     "knowledge_search", "search"),
    ("Using AI-assisted tools in word processors.",
     "word_processor_ai", "writing"),
    ("Generating code using AI.",
     "code_generation", "coding"),
    ("Improving the quality of written communications using AI tools.",
     "writing_improvement", "writing"),
    ("Managing and prioritizing internal service or help desk tickets using AI.",
     "help_desk", "it_operations"),
    ("Transcribing, summarizing, or other efforts that improve the accessibility of a virtual meeting or interview using AI.",
     "meeting_transcription", "meetings"),
    ("Prioritizing and categorizing incoming emails using AI.",
     "email_triage", "email"),
    ("Creating visual representations of data sets for reports or presentations using AI.",
     "data_visualization", "data_viz"),
    ("Finding and booking travel accommodations using AI-powered platforms.",
     "travel_booking", "travel"),
    ("Curating news articles and updates based on user preferences using AI.",
     "news_curation", "search"),
    ("Scheduling internal-to-government meetings or appointments or setting reminders using AI.",
     "scheduling", "meetings"),
    ("Logging and analyzing time spent on tasks using AI-powered time management tools.",
     "time_management", "productivity"),
    ("Managing or implementing security controls for information systems (e.g., cybersecurity) using AI.",
     "security_controls", "cybersecurity"),
    ("Scheduling and managing social media posts using AI.",
     "social_media_scheduling", "productivity"),
    ("Planning travel routes using AI-driven map applications.",
     "travel_routes", "travel"),
    ("Unlocking smartphones or other devices without the need for passwords or PINs using AI-based facial recognition technology.",
     "device_unlock", "security"),
    ("Editing images, videos, or other public affairs materials using AI.",
     "media_editing", "writing"),
    ("Identifying and cataloging items in a storage room using AI-driven image recognition.",
     "storage_cataloging", "operations"),
    # ---- Agency-specific extensions beyond OMB Appendix B (is_omb_standard=0).
    # Kept here so a fresh DB rebuild preserves them; downstream queries should
    # filter on `is_omb_standard` when presenting the canonical 20-item list.
    ("Using AI-enabled augmented reality to train inspectors to visually assess unsafe environments from a safe location, significantly reducing training time, costs, and staffing needs while maintaining inspection effectiveness.",
     "ar_inspector_training", "training", 0),
    ("Answering federal regulatory and agency policy questions related to acquisition using a generative AI tool.",
     "regulatory_qa", "knowledge", 0),
]


def seed_products():
    conn = get_connection()
    try:
        # Clear — null references first so FKs don't block the re-seed.
        conn.execute("UPDATE use_cases SET product_id = NULL")
        conn.execute("UPDATE consolidated_use_cases SET product_id = NULL")
        conn.execute("DELETE FROM use_case_products")
        conn.execute("DELETE FROM consolidated_use_case_products")
        conn.execute("DELETE FROM fedramp_product_links")
        conn.execute("DELETE FROM product_aliases")
        conn.execute("DELETE FROM products")

        # First pass: insert products without parent (so parent IDs can be resolved)
        name_to_id = {}
        for (name, vendor, ptype, is_genai, is_frontier, parent, desc, _aliases) in PRODUCTS:
            cur = conn.execute(
                """INSERT INTO products (canonical_name, vendor, product_type, is_generative_ai, is_frontier_llm, description)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (name, vendor, ptype, is_genai, is_frontier, desc),
            )
            name_to_id[name] = cur.lastrowid

        # Second pass: set parent_product_id
        for (name, _vendor, _ptype, _g, _f, parent, _desc, _aliases) in PRODUCTS:
            if parent:
                conn.execute(
                    "UPDATE products SET parent_product_id = ? WHERE id = ?",
                    (name_to_id[parent], name_to_id[name]),
                )

        # Third pass: aliases
        alias_count = 0
        for (name, _v, _p, _g, _f, _par, _d, aliases) in PRODUCTS:
            pid = name_to_id[name]
            for a in aliases:
                try:
                    conn.execute(
                        "INSERT INTO product_aliases (product_id, alias_text) VALUES (?, ?)",
                        (pid, a),
                    )
                    alias_count += 1
                except Exception as e:
                    print(f"Dup alias skipped: {a} -> {e}")

        conn.commit()
        print(f"Seeded {len(PRODUCTS)} products with {alias_count} aliases")
    finally:
        conn.close()


def seed_templates():
    conn = get_connection()
    try:
        conn.execute("DELETE FROM use_case_templates")
        for row in TEMPLATES:
            # Row is (text, short, category) for OMB-standard templates or
            # (text, short, category, is_omb_standard) for agency extensions.
            if len(row) == 4:
                text, short, category, is_std = row
            else:
                text, short, category = row
                is_std = 1
            conn.execute(
                "INSERT INTO use_case_templates (template_text, short_name, capability_category, is_omb_standard) VALUES (?, ?, ?, ?)",
                (text, short, category, is_std),
            )
        conn.commit()
        print(f"Seeded {len(TEMPLATES)} use case templates")
    finally:
        conn.close()


if __name__ == "__main__":
    seed_products()
    seed_templates()
