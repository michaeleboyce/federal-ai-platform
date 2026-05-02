#!/usr/bin/env python3
"""Classify unresolved product-vendor strings into mapping decisions.

Outputs:
  resolved.csv     - per-row decision
  proposed_new_products.csv - dedup of seed_new_alias
  searches.csv     - any web searches we attempted (this script does none directly)
  notes.md         - methodology + summary
"""
from __future__ import annotations
import csv
import os
import re
import sqlite3
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
DB = os.path.join(ROOT, "data", "federal_ai_inventory_2025.db")
QUEUE = os.path.join(ROOT, "audit", "review_queue_products_unresolved.csv")
OUT_DIR = os.path.join(ROOT, "audit", "retag", "round2", "products")
os.makedirs(OUT_DIR, exist_ok=True)

# ---- canonical product + alias lookup ----
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
products = {row["id"]: dict(row) for row in con.execute(
    "SELECT id, canonical_name, vendor, product_type FROM products")}
aliases = []  # list of (alias_lower, canonical_name, product_id)
for row in con.execute(
        "SELECT pa.alias_text, p.canonical_name, p.id "
        "FROM product_aliases pa JOIN products p ON p.id=pa.product_id"):
    aliases.append((row["alias_text"].lower(), row["canonical_name"], row["id"]))
# Also include canonical names themselves as aliases-of-self.
for pid, p in products.items():
    aliases.append((p["canonical_name"].lower(), p["canonical_name"], pid))
# Add additional runtime aliases (high confidence) so we map these to existing canonicals.
def _pid_for(name: str):
    for pid, p in products.items():
        if p["canonical_name"].lower() == name.lower():
            return pid
    return None

_runtime_aliases = [
    # MS Copilot family → M365 Copilot
    ("microsoft co-pilot", "Microsoft 365 Copilot"),
    ("microsoft copilot", "Microsoft 365 Copilot"),
    ("ms co-pilot", "Microsoft 365 Copilot"),
    ("ms copilot", "Microsoft 365 Copilot"),
    ("microsoft copilot pilot", "Microsoft 365 Copilot"),
    ("github co-pilot", "GitHub Copilot"),
    ("github co pilot", "GitHub Copilot"),
    # ChatGPT / OpenAI variants
    ("open ai", "ChatGPT"),
    ("openai chatgpt", "ChatGPT"),
    # Google
    ("google gemini", "Gemini"),
    ("notebooklm", "Google Agentspace"),
    ("google agentspace / notebooklm", "Google Agentspace"),
    # AWS
    ("amazon web services", "AWS Bedrock"),  # too generic; will handle specially below
    # Salesforce
    ("salesforce einstein", "Salesforce Einstein"),
    # Misc
    ("uipath", "UiPath Enterprise RPA"),
    ("uipath studio", "UiPath Enterprise RPA"),
    ("crowdstrike", "Crowdstrike Falcon"),
    ("skillsoft", "Skillsoft Percipio CAISY"),
    ("percipio", "Skillsoft Percipio CAISY"),
    ("skillsoft/percipio", "Skillsoft Percipio CAISY"),
    ("airship", "Airship AI Platform"),
    ("azure open ai", "Azure OpenAI"),
    ("azure openai", "Azure OpenAI"),
    ("hyperscience", "Hyperscience"),
    # Microsoft 365 family fallthrough
    ("hanford accreditation boundary (hab) microsoft co-pilot", "Microsoft 365 Copilot"),
    ("hanford accreditation boundary (hab) github co-pilot", "GitHub Copilot"),
    # RELX / Lexis variants
    ("relx (lexis)", "Lexis+ AI"),
    ("relx", "Lexis+ AI"),
    ("lexis protege", "Lexis+ AI"),
]
for alias_text, canon_name in _runtime_aliases:
    pid = _pid_for(canon_name)
    if pid is None:
        continue
    aliases.append((alias_text.lower(), canon_name, pid))

# Dedup, keep first occurrence
seen = set()
dedup = []
for a in aliases:
    if a[0] in seen:
        continue
    seen.add(a[0])
    dedup.append(a)
aliases = dedup
# Sort by length descending so longest match wins.
aliases.sort(key=lambda x: -len(x[0]))

# A subset of "too generic" aliases - require strong AI-product context to map.
# E.g., "Amazon Web Services" alone shouldn't map to AWS Bedrock unless Bedrock
# is named.
WEAK_ALIASES = {"amazon web services"}

# ---- previously-proposed new products to avoid double-seeding ----
prev_proposed = set()  # lowercase canonical names already proposed
for fn in ("proposed_aliases_seed_now.csv", "proposed_aliases_round2.csv"):
    path = os.path.join(ROOT, "audit", fn)
    if not os.path.exists(path):
        continue
    with open(path) as f:
        for r in csv.DictReader(f):
            for col in ("proposed_alias", "proposed_name"):
                v = r.get(col, "").strip()
                if v:
                    prev_proposed.add(v.lower())

# ---- service-contractor / consulting vendors (non-products) ----
SERVICE_CONTRACTORS = {
    # large consulting & systems integrators
    "deloitte", "accenture", "booz allen", "booz allen hamilton", "bah",
    "leidos", "saic", "mantech", "mantech international", "northrop grumman",
    "lockheed", "lockheed martin", "raytheon", "general dynamics", "gdit",
    "gd it", "ibm consulting", "kpmg", "pwc", "ernst & young", "ey",
    "mckinsey", "bcg", "boston consulting", "guidehouse", "ca technologies",
    "ca tech", "navteca", "cgi federal", "cgi", "perspecta", "peraton",
    "macro solutions", "maximus", "iqvia", "deloitte consulting",
    "niyamit", "elder research", "devtech", "elder research inc",
    "bates white", "candidate solutions", "canda solutions", "pluribus digital",
    "metroibr", "inadev", "aneesh technologies", "24x7", "ellumen",
    "rohde & schwarz", "jhu apl", "johns hopkins apl", "applied physics laboratory",
    "sandia national laboratories", "sandia",
    "lmi consulting", "lmi", "ideation",  # ideation also a product
    "microhealth", "pdri", "sentar", "sentar inc", "sti",
    "highlight technologies", "highlight tech", "synergy", "saic and dv united",
    "dv united", "ais ", "the regulatory group", "trg",
    "pinnacle solutions", "engility", "csra", "dxc", "dxc technology",
    "csc", "computer sciences corp", "tata consultancy", "tcs",
    "infosys", "wipro", "hcl", "cognizant", "capgemini", "atos",
    "oracle consulting",
    "buchanan & edwards", "buchanan and edwards", "be llc",
    "abeyon", "abacus technology", "abacus", "vincere group",
    "carahsoft", "presidio", "mantech", "salient crgt", "salient",
    "noblis", "mitre", "the mitre corporation", "rand", "rand corp",
    "anser", "ida", "institute for defense analyses", "idemia",  # idemia is product family but treat case by case
    "general dynamics information technology",
    "icf", "icf international", "tetra tech", "tetratech",
    "battelle", "manhattan strategy group", "manhattan strategy",
    "westat", "abt associates", "abt global", "rti international",
    "rti", "mathematica", "ssa global", "agilex",
    "high tide technologies", "high tide tech", "high tide",
    "novetta", "verisign", "preferred systems solutions", "pss",
    "gemini industries", "centurum", "ase", "ase tech",
    "open source", "opensource", "open-source",
    "in-house", "in house", "internal", "n/a", "na ", "none",
    "redacted", "law enforcement sensitive", "les",
    "not available", "not specified", "unknown", "tbd", "pending",
    "us digital corps", "usds", "tts", "18f", "gsa",  # could also be product context
    "dhs", "doj", "dod", "dot", "treasury", "hhs",
    "tysons technology", "tysons tech",
    "valiant", "valiant solutions", "softrams",
    "octo consulting", "octo",
    "definitive logic", "definitive", "elasticsearch",  # last is a product but base ES
    "concept solutions", "concept plus",
    "preferred systems",
    "innotion", "blue water federal", "blue water",
    "navarro research", "navarro", "akima", "akimaglobal",
    "pernix", "pernix federal", "rivet",
    "metaphase", "metaphase consulting", "exygy",
    "ca-tech",
    "wildfire.org",
    "trax international", "trax",
    "stinger ghaffarian technologies", "sgt", "sgt inc",
    "ethink", "ethink edutech", "etr", "etr associates",
    "agile six", "agile-six", "agilesix",
    "ad hoc", "ad hoc llc", "adhoc",
    "nava", "nava pbc", "truss", "truss works",
    "esri",  # esri is also a product family; handled in aliases
}

# strings that indicate AI service provider was redacted / unknown
REDACTED_HINTS = (
    "redacted for cybersecurity",
    "ai service provider",
    "law enforcement sensitive",
    "not available",
    "not specified",
    "unknown vendor",
    "internal use only",
    "not applicable",
    "n/a n/a",
    "n/a  ",
    "n/a ",
)

# Specific high-confidence candidate-product detections (regex/word-pattern → canonical_name, vendor, product_type)
# These detect substrings that strongly imply a non-canonical product.
NEW_PRODUCT_PATTERNS = [
    # (regex, proposed_name, vendor, product_type)
    # ---- Microsoft / Azure family extras ----
    (r"\bmicrosoft\s+sentinel\b", "Microsoft Sentinel", "Microsoft", "security_tool"),
    (r"\bms\s+sentinel\b", "Microsoft Sentinel", "Microsoft", "security_tool"),
    (r"\bhololens\b", "Microsoft HoloLens", "Microsoft", "computer_vision"),
    (r"\bazure\s+ml\b|\bazure\s+machine\s+learning\b", "Azure Machine Learning", "Microsoft", "ml_platform"),
    (r"\bazure\s+cognitive\s+search\b", "Azure Cognitive Search", "Microsoft", "search"),
    (r"\bazure\s+cognitive\s+services\b", "Azure Cognitive Services", "Microsoft", "general_llm"),
    (r"\bazure\s+speech\b", "Azure Speech", "Microsoft", "transcription"),
    (r"\bazure\s+translator\b", "Azure Translator", "Microsoft", "translation"),
    (r"\bazure\s+platform\b", "Microsoft Azure Platform", "Microsoft", "cloud_platform"),
    (r"\bazure\s+automatic\s+document\s+processing\b", "Azure AI Document Intelligence", "Microsoft", "document_ai"),
    (r"\bazure\s+audio\s+transcription\b|\bazure\s+speech\s+to\s+text\b", "Azure Speech", "Microsoft", "transcription"),
    # ---- Veritone ----
    (r"\bveritone\s+illuminate\b", "Veritone Illuminate", "Veritone", "media_analysis"),
    (r"\bveritone\b", "Veritone", "Veritone", "media_analysis"),
    (r"\bsystran\s+translate\b", "Systran Translate", "Systran", "translation"),
    (r"\bsystran\b", "Systran Translate", "Systran", "translation"),
    (r"\bchainalysis\b", "Chainalysis", "Chainalysis", "blockchain_analytics"),
    (r"\btrm\s+labs\b", "TRM Labs Blockchain Analysis Platform", "TRM Labs", "blockchain_analytics"),
    (r"\bclear\s+(background|service|web|application)\b", "Thomson Reuters CLEAR", "Thomson Reuters", "data_analytics"),
    (r"\bthomson reuters clear\b", "Thomson Reuters CLEAR", "Thomson Reuters", "data_analytics"),
    (r"\bultralytics\b", "Ultralytics YOLO", "Ultralytics", "computer_vision"),
    (r"\bcryodgrn\b", "cryoDRGN", "Open Source", "scientific_ml"),
    (r"\baivia\b", "Leica Aivia", "Leica", "computer_vision"),
    (r"\bidemia\b.*\bcat[- ]?2\b", "IDEMIA CAT-2/AutoCAT", "IDEMIA", "biometrics"),
    (r"\bidemia\b.*\bautocat\b", "IDEMIA CAT-2/AutoCAT", "IDEMIA", "biometrics"),
    (r"\bidemia\b", "IDEMIA Biometric Platform", "IDEMIA", "biometrics"),
    (r"\bbi\s+isap\s+iv\b", "BI SmartLINK", "BI Incorporated", "biometrics"),
    (r"\bsmartlink\b", "BI SmartLINK", "BI Incorporated", "biometrics"),
    (r"\bargos\b.*\bibm\b|\bibm\b.*\bargos\b", "IBM ARGOS", "IBM", "nlp"),
    (r"\bdataminr\b", "Dataminr First Alert", "Dataminr", "social_listening"),
    (r"\bairship\s+outpost\b", "Airship Outpost", "Airship AI Holdings", "computer_vision"),
    (r"\bservicenow\s+vulnerability\s+response\b", "ServiceNow Vulnerability Response", "ServiceNow", "security_tool"),
    (r"\baltana\b", "Altana Atlas", "Altana", "supply_chain"),
    (r"\bquantaero\b", "Quantaero Marine Wildlife AI", "Quantaero", "computer_vision"),
    (r"\binvariant\s+corporation\b.*\bacoustic\b", "Invariant Acoustic Signature AI", "Invariant Corporation", "audio_analysis"),
    (r"\bpest\b", "PEST (Parameter Estimation)", "Open Source", "scientific_ml"),
    (r"\bazure\s+ai\s+foundry\b", "Azure AI Foundry", "Microsoft", "general_llm"),
    (r"\bazure\s+document\s+intelligence\b|\bazure\s+ai\s+document\s+intelligence\b", "Azure AI Document Intelligence", "Microsoft", "document_ai"),
    (r"\busai\b", "USAi (GSA)", "GSA", "general_llm"),
    (r"\bedav\b", "EDAV (CDC)", "CDC", "data_analytics"),
    (r"\bvegspec\b", "VegSpec", "USDA NRCS", "scientific_ml"),
    (r"\batlas\s+turbo\b|\badvanced platform for technical learning\b", "ATLAS (Forest Service)", "USDA Forest Service", "data_analytics"),
    (r"\bvao\s+ally\b|\bvirtual acquisition office\b", "VAO Ally", "GSA", "agent_platform"),
    (r"\bgrants\.gov\b", "Grants.gov AI Tools", "HHS", "data_analytics"),
    (r"\bcleartrac\b", "ClearTrac", "Unknown", "data_analytics"),
    (r"\bspeechmatics\b", "Speechmatics", "Speechmatics", "transcription"),
    (r"\bdeepgram\b", "Deepgram", "Deepgram", "transcription"),
    (r"\bassemblyai\b", "AssemblyAI", "AssemblyAI", "transcription"),
    (r"\bwindsurf\b", "Windsurf", "Codeium", "coding_assistant"),
    (r"\bcursor\b(?!\s+for\b)", "Cursor", "Anysphere", "coding_assistant"),
    (r"\bcodeium\b", "Codeium", "Codeium", "coding_assistant"),
    (r"\bperplexity\b", "Perplexity", "Perplexity AI", "general_llm"),
    (r"\bmistral\b", "Mistral", "Mistral AI", "general_llm"),
    (r"\bllama\b", "Llama", "Meta", "general_llm"),
    (r"\bhuggingface\b|\bhugging\s+face\b", "Hugging Face", "Hugging Face", "ml_platform"),
    (r"\bnvidia\s+nemo\b", "NVIDIA NeMo", "NVIDIA", "ml_platform"),
    (r"\bnvidia\b.*\bnim\b", "NVIDIA NIM", "NVIDIA", "ml_platform"),
    (r"\bsambanova\b", "SambaNova", "SambaNova", "ml_platform"),
    (r"\bcohere\b", "Cohere", "Cohere", "general_llm"),
    (r"\baveris(o|ou)rce\b", "AveriSource", "AveriSource", "code_modernization"),
    (r"\bpingwind\b", "Pingwind AI DevOps", "Pingwind", "devops"),
    (r"\bdocusign\b.*\binsight\b|\bdocusign\s+iam\b|\bdocusign\s+ai\b", "DocuSign Insight", "DocuSign", "document_ai"),
    (r"\bnotebooklm\b", "Google NotebookLM", "Google", "general_llm"),
    (r"\babbyy\b", "ABBYY FineReader", "ABBYY", "document_ai"),
    (r"\bdatabricks\s+mosaic\b|\bmosaic\s+ai\b", "Databricks Mosaic AI", "Databricks", "ml_platform"),
    (r"\bsnorkel\b", "Snorkel AI", "Snorkel AI", "ml_platform"),
    (r"\bscale\s+ai\b", "Scale AI", "Scale AI", "ml_platform"),
    (r"\bappian\b", "Appian AI", "Appian", "agent_platform"),
    (r"\bpegasystems\b|\bpega\s+ai\b", "Pega AI", "Pegasystems", "agent_platform"),
    (r"\bblue\s*prism\b", "Blue Prism", "Blue Prism", "rpa"),
    (r"\bautomation\s+anywhere\b", "Automation Anywhere", "Automation Anywhere", "rpa"),
    (r"\bdatarobot\b", "DataRobot", "DataRobot", "ml_platform"),
    (r"\bh2o\.ai\b|\bh2o ai\b", "H2O.ai", "H2O.ai", "ml_platform"),
    (r"\bh2o-3\b|\bh2o3\b", "H2O.ai", "H2O.ai", "ml_platform"),
    (r"\bgensim\b", "Gensim", "Open Source", "nlp"),
    (r"\bspacy\b", "spaCy", "Open Source", "nlp"),
    (r"\bpytorch\b", "PyTorch", "Meta/Open Source", "ml_framework"),
    (r"\btensorflow\b", "TensorFlow", "Google/Open Source", "ml_framework"),
    (r"\bscikit-?learn\b|\bsklearn\b", "scikit-learn", "Open Source", "ml_framework"),
    (r"\bxgboost\b", "XGBoost", "Open Source", "ml_framework"),
    (r"\bclear[- ]?trac\b", "ClearTrac", "Unknown", "data_analytics"),
    (r"\bpalantir\s+foundry\b", "Palantir Foundry", "Palantir", "data_analytics"),
    (r"\bpalantir\s+gotham\b", "Palantir Gotham", "Palantir", "data_analytics"),
    (r"\bpalantir\s+aip\b", "Palantir AIP", "Palantir", "general_llm"),
    (r"\bsalesforce\s+einstein\s+gpt\b|\beinstein\s+gpt\b", "Salesforce Einstein GPT", "Salesforce", "general_llm"),
    (r"\baws\s+sagemaker\b|\bamazon\s+sagemaker\b|\bsagemaker\b", "AWS SageMaker", "Amazon", "ml_platform"),
    (r"\baws\s+comprehend\b|\bamazon\s+comprehend\b", "AWS Comprehend", "Amazon", "nlp"),
    (r"\baws\s+rekognition\b|\bamazon\s+rekognition\b|\brekognition\b", "AWS Rekognition", "Amazon", "computer_vision"),
    (r"\baws\s+polly\b|\bamazon\s+polly\b", "AWS Polly", "Amazon", "speech_synthesis"),
    (r"\baws\s+forecast\b|\bamazon\s+forecast\b", "AWS Forecast", "Amazon", "ml_platform"),
    (r"\baws\s+kendra\b|\bamazon\s+kendra\b|\bkendra\b", "AWS Kendra", "Amazon", "search"),
    (r"\bgoogle\s+document\s+ai\b|\bdocument\s+ai\b(?!\s+v|\s+powershell)", "Google Document AI", "Google", "document_ai"),
    (r"\bgemma\b", "Gemma", "Google", "general_llm"),
    (r"\bgoogle\s+colab\b", "Google Colab", "Google", "ml_platform"),
    (r"\baws\s+ground\s+truth\b|\bsagemaker\s+ground\s+truth\b", "AWS SageMaker Ground Truth", "Amazon", "ml_platform"),
    (r"\bclaude\s+enterprise\b", "Claude", "Anthropic", "general_llm"),
    (r"\baws\s+q\s+developer\b|\bamazon\s+q\s+developer\b", "Amazon Q", "Amazon", "general_llm"),
    (r"\bgithub\s+advanced\s+security\b", "GitHub Advanced Security", "GitHub", "security_tool"),
    (r"\bsemgrep\b", "Semgrep", "Semgrep", "security_tool"),
    (r"\bsnyk\b", "Snyk", "Snyk", "security_tool"),
    (r"\bsonarqube\b|\bsonar\s+cloud\b", "SonarQube", "SonarSource", "security_tool"),
    (r"\bjira\b", "Atlassian Jira", "Atlassian", "productivity"),
    (r"\bconfluence\b", "Atlassian Confluence", "Atlassian", "productivity"),
    (r"\bzoom\s+ai\b|\bzoom\s+companion\b", "Zoom AI Companion", "Zoom", "productivity"),
    (r"\bwebex\s+ai\b", "Webex AI", "Cisco", "productivity"),
    (r"\bcisco\s+ai\b", "Cisco AI", "Cisco", "security_tool"),
    (r"\bdarktrace\b", "Darktrace", "Darktrace", "security_tool"),
    (r"\bsentinelone\b|\bsentinel\s+one\b", "SentinelOne", "SentinelOne", "security_tool"),
    (r"\belastic\s+(security|machine learning|ml)\b", "Elastic Security", "Elastic", "security_tool"),
    # ---- Federal / Agency platforms ----
    (r"\bask\s+sage\b", "Ask Sage", "Ask Sage Inc.", "general_llm"),
    (r"\bcredal\b", "Credal", "Credal", "agent_platform"),
    (r"\bnvivo\b|\blumivero\b", "NVivo", "Lumivero", "qualitative_analysis"),
    (r"\bqualtrics\b", "Qualtrics", "Qualtrics", "survey_analytics"),
    (r"\bonereach\b", "OneReach.ai", "OneReach.ai", "agent_platform"),
    (r"\bamazon\s+connect\b", "Amazon Connect", "Amazon", "contact_center"),
    (r"\brelativity\s+(active\s+learning|federal|cloud)\b|\brelativity\s+ediscovery\b|\brelativity\b", "Relativity", "Relativity", "ediscovery"),
    (r"\bkiteworks\b", "Kiteworks", "Kiteworks", "security_tool"),
    (r"\bknowbe4\b", "KnowBe4 PhishER", "KnowBe4", "security_tool"),
    (r"\bphisher\b", "KnowBe4 PhishER", "KnowBe4", "security_tool"),
    (r"\bcitrix\b", "Citrix", "Citrix", "virtualization"),
    (r"\bflowmon\b", "Flowmon", "Progress Flowmon", "security_tool"),
    (r"\btesseract\b", "Tesseract OCR", "Open Source", "document_ai"),
    (r"\bdeepmind\b.*\balphafold\b|\balphafold\b", "AlphaFold", "Google DeepMind", "scientific_ml"),
    (r"\bcryosparc\b", "CryoSPARC", "Structura Biotechnology", "scientific_ml"),
    (r"\bpangolin\b.*\blineage\b|\bpangolin\b", "Pangolin Lineage", "COG-UK", "scientific_ml"),
    (r"\bcogito\b|\bexpert\.?ai\b|\bexpert\s+ai\b", "Expert.ai Cogito", "expert.ai", "nlp"),
    (r"\bdynatrace\b", "Dynatrace", "Dynatrace", "security_tool"),
    (r"\bid\.me\b", "ID.me", "ID.me", "identity_verification"),
    (r"\binformatica\b", "Informatica", "Informatica", "data_catalog"),
    # Hyperscience handled as canonical alias.
    (r"\bbmc\s+helix\b", "BMC Helix ITSM", "BMC", "itsm"),
    (r"\bwhooster\b", "Whooster", "Whooster", "data_analytics"),
    (r"\bcryolo\b", "crYOLO", "Open Source", "scientific_ml"),
    (r"\bcoleridge\b.*\bdemocratizing\s+data\b|\bdemocratizing\s+data\b", "Democratizing Data", "Coleridge Institute", "data_analytics"),
    (r"\bsimplyfile\b", "SimplyFile", "TechHit", "productivity"),
    (r"\bfoiaxpress\b", "FOIAXpress AI", "OPEXUS", "document_ai"),
    (r"\bgoogle\s+translate\b", "Google Translate", "Google", "translation"),
    (r"\buptodate\b", "UpToDate", "Wolters Kluwer", "clinical_decision_support"),
    (r"\bexiger\b.*\bddiq\b|\bddiq\b", "Exiger DDIQ", "Exiger", "supply_chain"),
    (r"\bcommonlook\b", "Commonlook Online", "Commonlook", "document_ai"),
    (r"\bnvivo\b", "NVivo", "Lumivero", "qualitative_analysis"),
    (r"\bjustia\b", "Justia", "Justia", "legal_research"),
    (r"\bblueprint\s+technologies\b|\bblueprintai\b", "Blueprint AI", "Blueprint Technologies", "data_analytics"),
    (r"\binnodata\b", "Innodata", "Innodata", "ml_platform"),
    (r"\babbyy\s+finereader\b", "ABBYY FineReader", "ABBYY", "document_ai"),
    (r"\bablespace\b|\bable\s+space\b", "AbleSpace", "AbleSpace", "data_analytics"),
    (r"\bappenate\b", "Appenate", "Appenate", "agent_platform"),
    (r"\bcomet\b\s+ml|\bcomet\.ml\b", "Comet ML", "Comet", "ml_platform"),
    (r"\bweights\s+&?\s*biases\b|\bwandb\b", "Weights & Biases", "Weights & Biases", "ml_platform"),
    (r"\blangchain\b", "LangChain", "LangChain", "ml_framework"),
    (r"\bllamaindex\b|\bllama\s+index\b", "LlamaIndex", "LlamaIndex", "ml_framework"),
    (r"\bopensearch\b", "OpenSearch", "Open Source", "search"),
    (r"\belasticsearch\b\s+(ml|machine learning)", "Elasticsearch ML", "Elastic", "ml_platform"),
    (r"\bh2o\.?gpte\b|\bh2ogpte\b", "H2O GPTe", "H2O.ai", "general_llm"),
    (r"\bemerald\s+innovations\b", "Emerald Innovations", "Emerald Innovations", "scientific_ml"),
    (r"\bmindpetal\b", "Mindpetal AIARA", "Mindpetal", "agent_platform"),
    (r"\bskyward\b.*\b(claw|cedar)\b", "Skyward CEDAR/CLAW", "Skyward IT Solutions", "agent_platform"),
    # (Skillsoft / Percipio handled as runtime alias to canonical Skillsoft Percipio CAISY)
    (r"\bspyglassgpt\b", "SpyglassGPT", "Unknown", "general_llm"),
    (r"\bcohesity\b", "Cohesity", "Cohesity", "security_tool"),
    (r"\bflashpoint\b", "Flashpoint", "Flashpoint", "social_listening"),
    (r"\blexis\s+protege\b", "Lexis+ AI", "LexisNexis", "legal_research"),
    (r"\baccrete\b.*\bargus\b|\bargus\s+ai\b", "ACCRETE ARGUS", "ACCRETE AI Government", "supply_chain"),
    (r"\bgaia\s+ai\b", "GAIA AI", "GAIA AI", "computer_vision"),
    (r"\bprocuresight\b", "ProcureSight", "ProcureSight", "data_analytics"),
    (r"\bglobalcomm\b.*\bvideo\s+surveillance\b", "GlobalComm Video Surveillance", "GlobalComm", "computer_vision"),
    (r"\bnanci\b", "NanCI", "NIH", "agent_platform"),
    (r"\blexical\s+intelligence\b", "Lexical Intelligence", "Lexical Intelligence, LLC", "nlp"),
    (r"\baretec\b.*\bneat\b|\baretec\s+neat\b", "Aretec NEAT", "Aretec Inc", "data_analytics"),
    (r"\bredcastle\b", "RedCastle Forest Health", "RedCastle Resources", "computer_vision"),
    (r"\bdigital\s+science\s+dimensions\b|\bdimensions\s+for\s+nih\b", "Digital Science Dimensions", "Digital Science", "data_analytics"),
    (r"\bshabash\b.*\bmerops\b|\bmerops\b", "Shabash Merops", "Shabash", "nlp"),
    (r"\btrigent\b.*\bplates\b|\bplates,?\s+foodtrak\b|\bplates\b.*\bfoodtrak\b", "PLATES/FoodTrak", "Trigent Solutions", "document_ai"),
    (r"\bicatalyst\b", "iCatalyst RPA", "iCatalyst Inc", "rpa"),
    (r"\bsumtotal\b", "SumTotal", "SumTotal", "training"),
    (r"\bbarnacle\b.*\bnanci\b", "NanCI", "NIH/Barnacle", "agent_platform"),
    (r"\bibm\s+coredf\b|\bcoredf\b", "IBM CoreDF", "IBM", "document_ai"),
    (r"\bquantomvision\b", "QuantomVision", "Unknown", "training"),
    (r"\belsa\s+\(?foia\b|\belsa\b\s+fred|\bfred\b.*\bfoia\b", "FOIA REDACTION (FRED)", "Unknown", "document_ai"),
    (r"\bprecise\s+mlaas\b", "Precise MLaaS", "Precise Software", "ml_platform"),
    (r"\bpalantir\s+foundry\b", "Palantir Foundry", "Palantir", "data_analytics"),
    (r"\bpalantir\s+gotham\b", "Palantir Gotham", "Palantir", "data_analytics"),
    (r"\baip\s+assist\b|\bpalantir\s+aip\b", "Palantir AIP", "Palantir", "general_llm"),
    (r"\beinstein\s+gpt\b|\bsalesforce\s+einstein\s+gpt\b", "Salesforce Einstein GPT", "Salesforce", "general_llm"),
]

# Internal-system / agency-acronym indicators (heuristic)
# When source_text starts with an obvious agency program name like "Custom",
# "Internal", "Agency Built", treat as agency_internal_system_name (no product).
INTERNAL_SYSTEM_HINTS = (
    "custom in-house", "custom in house", "developed in-house", "in-house developed",
    "custom built", "custom-built", "internally developed", "internally-developed",
    "agency-built", "agency built", "in-house solution", "agency internal",
    "bls internal", "internal system",
)


def find_canonical(text: str):
    """Return list of (canonical_name, alias_match, product_id) found in text. Longest match preferred."""
    t = text.lower()
    found = []
    used_spans = []
    for alias, canon, pid in aliases:
        # avoid trivially short / generic aliases
        if len(alias) < 3:
            continue
        if alias in WEAK_ALIASES:
            continue
        # word-boundary match
        # use simple substring with word boundaries when alphanumeric
        # build regex
        try:
            pattern = re.compile(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])")
        except re.error:
            continue
        for m in pattern.finditer(t):
            span = (m.start(), m.end())
            # skip if overlaps an already-found longer match
            if any(s[0] <= span[0] < s[1] or s[0] < span[1] <= s[1] for s in used_spans):
                continue
            used_spans.append(span)
            found.append((canon, alias, pid))
    return found


def detect_new_products(text: str):
    t = text.lower()
    hits = []
    for pat, name, vendor, ptype in NEW_PRODUCT_PATTERNS:
        if re.search(pat, t):
            hits.append((name, vendor, ptype))
    return hits


def is_redacted_or_na(text: str) -> bool:
    t = text.lower().strip()
    if not t:
        return True
    for h in REDACTED_HINTS:
        if t.startswith(h) or h in t[:80]:
            return True
    # leading "n/a" checks
    if t.startswith("n/a") or t.startswith("not available") or t.startswith("not specified"):
        return True
    return False


def looks_like_service_contractor_only(text: str) -> bool:
    """True if text leads only with consulting firm names and no recognizable product."""
    t = text.lower()
    # take first 120 chars for vendor scan
    head = t[:200]
    matches = 0
    for sc in SERVICE_CONTRACTORS:
        if sc in head:
            matches += 1
    return matches >= 1


def classify(row, uc_ctx):
    src = row["source_text"]
    src_low = src.lower()

    # 0. Detect "multi-vendor list" pattern → not a single mappable product.
    multi_provider = bool(re.search(
        r"(openai|anthropic|google|meta|mistral|cohere)[,;]?\s+(and\s+)?"
        r"(openai|anthropic|google|meta|mistral|cohere)",
        src_low))

    # 1. Try canonical/alias match
    canon_hits = find_canonical(src)
    new_hits = detect_new_products(src)
    if multi_provider and canon_hits:
        # A multi-vendor passage that didn't name a specific product canonically:
        # if all hits are weak (just vendor names like Claude/Anthropic) and no
        # strong product alias was found (>=8 chars), drop them.
        if all(len(h[1]) <= 10 for h in canon_hits):
            canon_hits = []

    if canon_hits:
        # Prefer longest alias hit
        canon_hits.sort(key=lambda x: -len(x[1]))
        canon = canon_hits[0][0]
        # If we ALSO see a non-canonical-looking new product, still pick canon.
        return {
            "decision": "map_to_existing",
            "mapped_canonical_product": canon,
            "proposed_new_product_name": "",
            "proposed_vendor": "",
            "confidence": "high" if len(canon_hits[0][1]) >= 6 else "medium",
            "search_attempted": "no",
            "search_query": "",
            "evidence_url": f"db_row_{row['use_case_id']}",
            "notes": f"alias match: {canon_hits[0][1]!r}",
        }

    # 2. Try new product pattern detection
    if new_hits:
        # Take first hit
        name, vendor, ptype = new_hits[0]
        # skip if already proposed (duplicate seed)
        already = name.lower() in prev_proposed
        return {
            "decision": "seed_new_alias",
            "mapped_canonical_product": "",
            "proposed_new_product_name": name,
            "proposed_vendor": vendor,
            "confidence": "high",
            "search_attempted": "no",
            "search_query": "",
            "evidence_url": f"db_row_{row['use_case_id']}",
            "notes": ("already proposed in earlier round" if already else "pattern match")
                     + f"; product_type={ptype}",
            "_proposed_type": ptype,
        }

    # 3. Redacted / N/A / unknown
    if is_redacted_or_na(src):
        return {
            "decision": "service_contractor_only",
            "mapped_canonical_product": "",
            "proposed_new_product_name": "",
            "proposed_vendor": "",
            "confidence": "high",
            "search_attempted": "no",
            "search_query": "",
            "evidence_url": f"db_row_{row['use_case_id']}",
            "notes": "no product name; redacted/N/A/internal-only string",
        }

    # 4. Service contractor only (Deloitte, Booz, etc.)
    if looks_like_service_contractor_only(src):
        return {
            "decision": "service_contractor_only",
            "mapped_canonical_product": "",
            "proposed_new_product_name": "",
            "proposed_vendor": "",
            "confidence": "medium",
            "search_attempted": "no",
            "search_query": "",
            "evidence_url": f"db_row_{row['use_case_id']}",
            "notes": "leading contractor names; no recognizable product",
        }

    # 5. Internal system
    for h in INTERNAL_SYSTEM_HINTS:
        if h in src_low:
            return {
                "decision": "agency_internal_system_name",
                "mapped_canonical_product": "",
                "proposed_new_product_name": "",
                "proposed_vendor": "",
                "confidence": "medium",
                "search_attempted": "no",
                "search_query": "",
                "evidence_url": f"db_row_{row['use_case_id']}",
                "notes": "agency-built / in-house language",
            }

    # 6. Big-tech vendor with no specific product named → agency-internal system
    head_low = src_low[:60]
    big_tech_solo = (
        head_low.startswith("microsoft ") or head_low.startswith("microsoft\n")
        or head_low.startswith("amazon ") or head_low.startswith("aws ")
        or head_low.startswith("amazon web services")
        or head_low.startswith("google ") or head_low.startswith("google\n")
        or head_low.startswith("palantir ") or head_low.startswith("palantir\n")
        or head_low.startswith("cisco ") or head_low.startswith("cisco\n")
    )
    if big_tech_solo:
        return {
            "decision": "agency_internal_system_name",
            "mapped_canonical_product": "",
            "proposed_new_product_name": "",
            "proposed_vendor": "",
            "confidence": "low",
            "search_attempted": "no",
            "search_query": "",
            "evidence_url": f"db_row_{row['use_case_id']}",
            "notes": "Big-tech vendor named but no specific AI product identified; treating as agency program",
        }

    # 7. Sentinel (FDA) / FAERS / agency program nouns → internal
    internal_program_acronyms = (
        " sentinel ", " faers", " ardis", " altemis", " mappri", " edav", " cder ",
        " nextgen ", " edp ", " pfcs ", " rcra ", " ernie", " infovip",
    )
    padded = " " + src_low + " "
    if any(a in padded for a in internal_program_acronyms):
        return {
            "decision": "agency_internal_system_name",
            "mapped_canonical_product": "",
            "proposed_new_product_name": "",
            "proposed_vendor": "",
            "confidence": "medium",
            "search_attempted": "no",
            "search_query": "",
            "evidence_url": f"db_row_{row['use_case_id']}",
            "notes": "agency program/system acronym; vendor is contractor without product name",
        }

    # 8. "Contractor teams" prefix → service contractor only
    if src_low.startswith("contractor teams") or "third party vendor" in src_low[:40]:
        return {
            "decision": "service_contractor_only",
            "mapped_canonical_product": "",
            "proposed_new_product_name": "",
            "proposed_vendor": "",
            "confidence": "medium",
            "search_attempted": "no",
            "search_query": "",
            "evidence_url": f"db_row_{row['use_case_id']}",
            "notes": "generic 'contractor teams'/'third party vendor' wording; no product",
        }

    # 9. Ambiguous fallback
    return {
        "decision": "ambiguous",
        "mapped_canonical_product": "",
        "proposed_new_product_name": "",
        "proposed_vendor": "",
        "confidence": "low",
        "search_attempted": "no",
        "search_query": "",
        "evidence_url": f"db_row_{row['use_case_id']}",
        "notes": "no canonical alias + no recognized new product + not clearly contractor/internal",
    }


def main():
    # Pull use-case context
    uc_ctx = {}
    cur = con.execute(
        "SELECT id, use_case_name, problem_statement, system_name, system_outputs, vendor_name, "
        "development_type FROM use_cases")
    for row in cur:
        uc_ctx[row["id"]] = dict(row)

    rows = []
    with open(QUEUE) as f:
        rows = list(csv.DictReader(f))

    out_rows = []
    proposed = defaultdict(lambda: {"vendor": "", "type": "", "occurrences": 0, "samples": []})
    decision_counts = Counter()

    for row in rows:
        uc_id = int(row["use_case_id"])
        ctx = uc_ctx.get(uc_id, {})
        result = classify(row, ctx)
        decision_counts[result["decision"]] += 1
        out_rows.append({
            "queue_id": row["queue_id"],
            "use_case_id": row["use_case_id"],
            "source_text": row["source_text"],
            "decision": result["decision"],
            "mapped_canonical_product": result["mapped_canonical_product"],
            "proposed_new_product_name": result["proposed_new_product_name"],
            "proposed_vendor": result["proposed_vendor"],
            "confidence": result["confidence"],
            "search_attempted": result["search_attempted"],
            "search_query": result["search_query"],
            "evidence_url": result["evidence_url"],
            "notes": result["notes"],
        })
        if result["decision"] == "seed_new_alias" and result["proposed_new_product_name"]:
            key = result["proposed_new_product_name"]
            proposed[key]["vendor"] = result["proposed_vendor"]
            proposed[key]["type"] = result.get("_proposed_type", "")
            proposed[key]["occurrences"] += 1
            if len(proposed[key]["samples"]) < 5:
                proposed[key]["samples"].append(str(row["use_case_id"]))

    # write resolved.csv
    out_path = os.path.join(OUT_DIR, "resolved.csv")
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "queue_id", "use_case_id", "source_text", "decision",
            "mapped_canonical_product", "proposed_new_product_name", "proposed_vendor",
            "confidence", "search_attempted", "search_query", "evidence_url", "notes",
        ])
        w.writeheader()
        for r in out_rows:
            w.writerow(r)

    # write proposed_new_products.csv
    pnp_path = os.path.join(OUT_DIR, "proposed_new_products.csv")
    with open(pnp_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "canonical_name", "vendor", "product_type", "occurrences", "sample_use_case_ids",
            "already_proposed_earlier",
        ])
        w.writeheader()
        for name, data in sorted(proposed.items(), key=lambda x: -x[1]["occurrences"]):
            w.writerow({
                "canonical_name": name,
                "vendor": data["vendor"],
                "product_type": data["type"],
                "occurrences": data["occurrences"],
                "sample_use_case_ids": "|".join(data["samples"]),
                "already_proposed_earlier": "yes" if name.lower() in prev_proposed else "no",
            })

    # write empty searches.csv (we did no live searches; classification was pattern-driven)
    sp = os.path.join(OUT_DIR, "searches.csv")
    with open(sp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["query", "context_queue_id", "result_url", "result_summary", "decision_impact"])
        # No live searches performed; rules-based.

    # print summary stats
    total = sum(decision_counts.values())
    print(f"Total classified: {total}")
    for k, v in decision_counts.most_common():
        print(f"  {k}: {v} ({v/total*100:.1f}%)")
    print(f"\nUnique proposed new products: {len(proposed)}")
    print("Top 15 proposed:")
    for name, data in sorted(proposed.items(), key=lambda x: -x[1]["occurrences"])[:15]:
        flag = "*" if name.lower() in prev_proposed else ""
        print(f"  {data['occurrences']:3d}  {name}{flag}  [{data['vendor']}]")


if __name__ == "__main__":
    main()
