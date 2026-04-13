"""Seed the products, product_aliases, and use_case_templates tables."""

from db import get_connection

# (canonical_name, vendor, product_type, is_genai, is_frontier_llm, parent, description, aliases)
PRODUCTS = [
    # Microsoft Copilot family
    # Agent D (plan §D.2): bare "Copilot" alias removed — it was matching
    # GitHub Copilot, Copilot for Security, Copilot Studio, Salesforce Copilot,
    # etc. Aliases here are specific to the M365 SKU.
    ("Microsoft 365 Copilot", "Microsoft", "general_llm", 1, 1, None,
     "Microsoft's enterprise LLM assistant integrated with Office apps",
     ["M365 Copilot", "Microsoft M365 Copilot", "Microsoft M365 Copilot AI",
      "Microsoft Copilot for M365", "Microsoft 365 Copilot",
      "Copilot for Microsoft 365", "M365 CoPilot",
      "Microsoft 365 CoPilot", "M365 copilot", "Copilot Enterprise",
      "Microsoft Copilot Enterprise"]),
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
     ["Gemini", "Google Gemini", "Bard", "Gemini Pro", "Gemini 1.5", "Gemini 2"]),
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
        # Clear
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
