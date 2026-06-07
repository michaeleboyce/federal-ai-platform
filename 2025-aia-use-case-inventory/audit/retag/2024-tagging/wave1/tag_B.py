"""
wave1-B tagger for 2024 federal AI use-case inventory partition B (DOJ/DOC/DOE, 376 rows).

Constraints (HARD):
  * No reading of any 2025 source data.
  * Tags derived solely from input narrative columns.

Strategy:
  * Per-row narrative is the source of truth.
  * The reasoning column quotes 2-6 contiguous words drawn from the row's
    actual purpose_benefits / outputs / use_case_name text.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / "retag/2024-tagging/inputs/B.csv"
OUTDIR = Path(__file__).resolve().parent
OUT = OUTDIR / "B.csv"
AGENT = "wave1-B"

OUT_COLS = [
    "use_case_id_2024", "tagged_by_agent",
    "entry_type", "is_generative_ai", "ai_sophistication", "deployment_scope",
    "confidence", "reasoning",
    "is_general_llm_access", "is_coding_tool", "is_cots_commercial",
    "tool_product_name", "tool_vendor",
    "is_microsoft_copilot", "is_openai", "is_anthropic", "is_google",
    "is_github_copilot", "is_aws_ai",
    "is_enterprise_wide", "architecture_type", "has_model_training",
    "use_type", "is_public_facing", "scope_detail",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_quote(narrative, patterns, max_words=6):
    """Find the first regex pattern that matches narrative; return a
    quoted snippet (2-6 words) containing the match."""
    for pat in patterns:
        m = re.search(pat, narrative, re.IGNORECASE)
        if m:
            start = max(0, m.start())
            end = min(len(narrative), m.end())
            # Expand to word boundaries
            while start > 0 and narrative[start - 1].isalnum():
                start -= 1
            while end < len(narrative) and narrative[end].isalnum():
                end += 1
            snip = narrative[start:end]
            # Trim to <= 6 words
            words = snip.split()
            if len(words) > max_words:
                snip = " ".join(words[:max_words])
            snip = snip.strip(" .,;:\n\t-")
            if 1 <= len(snip.split()) <= max_words and len(snip) > 1:
                return snip
    return None


def first_clause(text, max_words=8):
    """Return the first short clause from a narrative."""
    if not text:
        return ""
    # Strip "Purpose:" / "Expected benefits:" preambles
    t = re.sub(r"^(Purpose|Expected benefits|Outputs?):\s*", "", text.strip(), flags=re.IGNORECASE)
    first = re.split(r"[.\n]", t, maxsplit=1)[0]
    words = first.split()
    if len(words) > max_words:
        first = " ".join(words[:max_words])
    return first.strip()


def bureau_short(bureau):
    if not bureau:
        return ""
    b = bureau.strip()
    if " - " in b:
        return b.split(" - ", 1)[0].strip()
    if " -" in b:
        return b.split(" -", 1)[0].strip()
    return b


# ---------------------------------------------------------------------------
# Per-row tagging
# ---------------------------------------------------------------------------

GEN_REGEX = [
    r"\bgenerative\s*ai\b", r"\bgen\s*ai\b", r"\bllm\b", r"large language model",
    r"\bchatgpt\b", r"\bopenai\b", r"azure\s*openai", r"\bclaude\b", r"\banthropic\b",
    r"\bgemini\b", r"\bcopilot\b", r"\bbedrock\b", r"\brag\b", r"retrieval[- ]augmented",
    r"foundation model", r"transformer[- ]based", r"transformer model",
    r"\bgpt\b", r"\bgpt-?\d", r"api gpt",
    r"chatbot", r"chat\s*bot", r"virtual assistant", r"\bcaisy\b",
    r"text generation", r"natural language generation", r"\bnlg\b",
    r"fine[- ]tun", r"image generation", r"generate\s+(images|text|content|code|graphs)",
    r"summari[zs]e", r"summari[zs]ation", r"draft.*(text|email|response|document|memo)",
    r"code (assistant|generation|completion)", r"github copilot", r"codium", r"codex",
    r"\baifreebox\b", r"grammarly",
]

# Stronger -> weaker order for sophistication
CV_REGEX = [
    r"computer vision", r"image (recognition|classification|detection|search|segmentation|labeling|annotation)",
    r"object (detection|recognition|tracking)", r"facial recognition", r"license plate",
    r"video (analytics|redact|recognition|editing)", r"bounding box",
    r"geospatial.*(map|imagery|model)", r"remote sens", r"satellite imagery", r"aerial imagery",
    r"sentinel-?2", r"land cover", r"crop type", r"x-?ray", r"radiograph",
    r"lidar", r"point cloud", r"\bocr\b", r"optical character recognition",
    r"photo (edit|enhance|classifi)", r"ocean image", r"image build",
    r"acoustic.*classif", r"sound classif", r"audio event",
    r"cloud (detection|mask)", r"\bcoralnet\b", r"\bfathomnet\b",
    r"redact (video|facial|image)", r"redact.*facial", r"redact.*image",
    r"audio and video", r"identify (objects|faces)",
]

NLP_REGEX = [
    r"natural language processing", r"\bnlp\b", r"topic modeling", r"sentiment analysis",
    r"named entity", r"text classifi", r"text analytics", r"text mining",
    r"transcrib", r"speech[- ]to[- ]text", r"voice[- ]to[- ]text", r"speech recognition",
    r"machine translation", r"\btranslation\b", r"language detection",
    r"document classifi", r"information extraction", r"entity extraction",
    r"keyword extraction", r"\btagging\b.*(text|web|document)",
    r"redact.*text", r"de-?identif", r"autosuggest", r"auto[- ]?classifi.*email",
    r"email.*auto.*classifi", r"document code", r"document label",
    r"name (screening|validation|matching)", r"autocoding", r"auto[- ]coding",
    r"\bsearch (relevance|ranking|tool|assistant)\b", r"patent search", r"trademark search",
]

PREDICTIVE_REGEX = [
    r"forecast", r"predictive", r"predict\b", r"prediction",
    r"anomaly detection", r"risk (score|model|assessment|identification|stratif)",
    r"fraud (detect|identif)", r"machine learning model", r"supervised", r"unsupervised",
    r"random forest", r"gradient boost", r"xgboost", r"regression", r"clustering",
    r"recommender", r"recommendation engine", r"neural network", r"deep learning",
    r"statistical model", r"estimat", r"classifi(er|cation|y)",
    r"\bml\s+(model|pipeline|algorithm)\b", r"machine learning",
    r"survival model", r"time series",
    r"screening (tool|model)", r"identify individuals", r"behavioral analysis",
    r"link.*analysis", r"network analysis", r"pattern (recognition|analysis)",
    r"entity (resolution|matching)", r"identity resolution",
]


CODING_REGEX = [
    r"github copilot", r"\bcopilot\b.*\bcode\b", r"code (assistant|generation|completion|modernization|review)",
    r"writing/reviewing code", r"writing or reviewing code", r"\bcodium\b", r"\bcodex\b",
    r"developer (assistant|productivity)", r"software (development|engineering) assistant",
]


def detect_sophistication(blob, is_gen, name):
    if any(re.search(p, blob, re.IGNORECASE) for p in CODING_REGEX):
        return "coding_assistant"
    if re.search(r"\bagentic\b|autonomous agent|multi[- ]agent system|agent[- ]based workflow", blob, re.IGNORECASE):
        return "agentic"
    if is_gen:
        return "general_llm"
    if any(re.search(p, blob, re.IGNORECASE) for p in CV_REGEX):
        return "computer_vision"
    if any(re.search(p, blob, re.IGNORECASE) for p in NLP_REGEX):
        return "nlp_specific"
    if any(re.search(p, blob, re.IGNORECASE) for p in PREDICTIVE_REGEX):
        return "predictive_analytics"
    return "classical_ml"


def detect_vendors(blob, name):
    bl = blob.lower()
    nl = name.lower()

    # GitHub Copilot
    gh_copilot = bool(re.search(r"github\s*copilot|gh\s+copilot", bl))

    # Microsoft Copilot family (excluding GH Copilot)
    ms_copilot = False
    if "copilot" in bl and not gh_copilot:
        # If "copilot" without github reference, treat as MS family
        if re.search(r"microsoft|m365|microsoft 365|copilot for security|copilot chat|productivity suite|office 365|ms\s*copilot|ms365", bl):
            ms_copilot = True
        elif re.search(r"\bcopilot\b", nl) and "github" not in nl:
            ms_copilot = True
        elif re.search(r"\bcopilot\b", bl) and "github" not in bl:
            ms_copilot = True

    openai = bool(re.search(r"\bopenai\b|\bchatgpt\b|azure\s*openai|\bgpt-?\d\b", bl))
    anthropic = bool(re.search(r"\banthropic\b|\bclaude\b", bl))
    google = bool(re.search(r"\bgemini\b|vertex ai|google\s+vertex|duet\s+ai|google earth engine|\bbard\b", bl))

    # AWS — exclude "JAWS" (screen reader)
    aws = False
    if "jaws" not in bl:
        if re.search(r"\baws\b|\bbedrock\b|sagemaker|rekognition|textract|amazon\s+comprehend|amazon\s+transcribe|amazon\s+translate|amazon\s+polly", bl):
            aws = True

    return {
        "github_copilot": gh_copilot,
        "ms_copilot": ms_copilot,
        "openai": openai,
        "anthropic": anthropic,
        "google": google,
        "aws": aws,
        "lexis": bool(re.search(r"lexis\s*nexis|lexisnexis|\blexis\b", bl)),
        "westlaw": "westlaw" in bl,
        "axon": "axon" in bl or "evidence.com" in bl,
        "clarivate": "clarivate" in bl,
        "salesforce": "salesforce" in bl,
        "databricks": "databricks" in bl,
        "palantir": "palantir" in bl,
        "veritone": "veritone" in bl,
        "sas": bool(re.search(r"\bsas\b\s+(institute|product|software|forecasting|enterprise|viya)", bl)) or "sas (forecasting" in bl,
        "flock": ("flock lpr" in bl) or ("flock" in bl and "license plate" in bl),
        "cellhawk": "cellhawk" in bl or "cell hawk" in bl,
        "skillsoft": "skillsoft" in bl or "percipio" in bl,
        "smiths_detection": "smiths detection" in bl,
        "thomson_reuters": "thomson reuters" in bl,
        "meta": bool(re.search(r"\bmeta\s*ai\b|metaai", bl)),
    }


def detect_tool(vendors, blob, name):
    bl = blob.lower()
    if vendors["github_copilot"]:
        return ("GitHub Copilot", "GitHub")
    if vendors["ms_copilot"]:
        if "copilot for security" in bl:
            return ("Microsoft Copilot for Security", "Microsoft")
        if "m365 copilot" in bl or "microsoft 365 copilot" in bl or "productivity suite" in bl:
            return ("Microsoft 365 Copilot", "Microsoft")
        return ("Microsoft Copilot", "Microsoft")
    if vendors["openai"]:
        if "azure openai" in bl:
            return ("Azure OpenAI", "Microsoft")
        if "chatgpt enterprise" in bl:
            return ("ChatGPT Enterprise", "OpenAI")
        if "chatgpt" in bl:
            return ("ChatGPT", "OpenAI")
        return ("OpenAI", "OpenAI")
    if vendors["anthropic"]:
        return ("Claude", "Anthropic")
    if vendors["google"]:
        if "gemini" in bl:
            return ("Gemini", "Google")
        if "vertex" in bl:
            return ("Vertex AI", "Google")
        if "google earth engine" in bl:
            return ("Google Earth Engine", "Google")
        return ("Google AI", "Google")
    if vendors["aws"]:
        for needle, prod in [
            ("bedrock", "AWS Bedrock"),
            ("sagemaker", "AWS SageMaker"),
            ("rekognition", "AWS Rekognition"),
            ("textract", "AWS Textract"),
            ("comprehend", "AWS Comprehend"),
            ("transcribe", "AWS Transcribe"),
            ("translate", "AWS Translate"),
        ]:
            if needle in bl:
                return (prod, "AWS")
        return ("AWS AI", "AWS")
    if vendors["lexis"]:
        return ("LexisNexis", "LexisNexis")
    if vendors["westlaw"]:
        return ("Westlaw", "Thomson Reuters")
    if vendors["axon"]:
        return ("Axon Evidence.com" if "evidence.com" in bl else "Axon", "Axon")
    if vendors["clarivate"]:
        return ("Clarivate", "Clarivate")
    if vendors["salesforce"]:
        return ("Salesforce", "Salesforce")
    if vendors["databricks"]:
        return ("Databricks", "Databricks")
    if vendors["palantir"]:
        return ("Palantir", "Palantir")
    if vendors["veritone"]:
        return ("Veritone", "Veritone")
    if vendors["sas"]:
        return ("SAS", "SAS")
    if vendors["flock"]:
        return ("Flock LPR", "Flock Safety")
    if vendors["cellhawk"]:
        return ("CellHawk", "Hawk Analytics")
    if vendors["skillsoft"]:
        return ("Percipio Skillsoft", "Skillsoft")
    if vendors["smiths_detection"]:
        return ("Smiths Detection", "Smiths Detection")
    if vendors["meta"]:
        return ("Meta AI", "Meta")
    return ("", "")


def detect_use_type(blob, bureau, agency):
    bl = blob.lower()
    bureau_l = bureau.lower()

    if re.search(r"cyber|security operation|incident response|\bsoc\b|threat detect|intrusion|\bsiem\b|malware|phishing|vulnerab|penetration test|red team", bl):
        return "cybersecurity"

    if re.search(r"code (modernization|generation|completion|review|assistance)|developer (productivity|assistant)|software development|writing.*code|reviewing.*code|legacy code", bl):
        return "it_operations"

    if re.search(
        r"investigat|criminal|law enforcement|intelligence analysis|border|immigration|"
        r"drug seizure|narcotic|weapons|trafficking|forensic|evidence|redact.*(video|foia)|"
        r"license plate|facial recognition|surveillance|inmate|prison|bureau of prisons|"
        r"patent|trademark|tax (lien|return|enforcement)|fraud detect|asset forfeiture|"
        r"subpoena|litigation|court (case|filing)|clemency|pardon|civil rights|antitrust|"
        r"spectrum allocation|trade enforcement|census frame|weather forecast|ocean|atmospher|"
        r"energy production|grid|nuclear (safety|security)|environmental (remediation|monitoring)|"
        r"health and safety|aviation safety|emergency response|firearm|gang|cartel|wiretap",
        bl,
    ):
        return "mission_critical"

    if re.search(
        r"national lab|laboratory research|scientif|experiment|physics|particle (detector|tracking)|"
        r"climate (model|research)|molecul|genom|materials science|fusion|plasma|"
        r"high.energy physics|cosmology|astronomy|biology research",
        bl,
    ) or re.search(r"\bnrel\b|\bornl\b|\bpnnl\b|\blanl\b|\banl\b|\bllnl\b|\bbnl\b|\bsnl\b|\bslac\b|\bfnal\b|\bpppl\b|\binl\b", bureau_l):
        return "research"

    if re.search(
        r"draft.*(email|memo|response|document)|summari[zs]e (meeting|document|report)|"
        r"training material|presentation|chart and graph|graphs and chart|"
        r"human resources|onboarding|policy drafting|productivity suite|"
        r"office productivity|administrative task|workflow automation|customer service",
        bl,
    ):
        return "administrative"

    bureau_low = bureau.lower()
    # Bureau-based defaults
    if agency == "DOE":
        return "research"
    if "census" in bureau_low:
        return "mission_critical"
    if "uspto" in bureau_low:
        return "mission_critical"
    if "noaa" in bureau_low:
        return "mission_critical"
    if "nist" in bureau_low:
        return "research"
    if "bea" in bureau_low or "bureau of economic analysis" in bureau_low:
        return "mission_critical"
    if "bea" == bureau_low or bureau_low.startswith("bea "):
        return "mission_critical"
    if "telecommunications" in bureau_low or "ntia" in bureau_low or "firstnet" in bureau_low:
        return "mission_critical"
    if "international trade" in bureau_low or "ita" == bureau_low:
        return "mission_critical"
    # DOJ defaults — most DOJ bureaus are mission_critical (investigative/legal)
    if agency == "DOJ":
        return "mission_critical"
    return ""


def detect_scope(blob, bureau, dev_stage, name):
    bl = blob.lower()
    nl = name.lower()
    if re.search(r"agency[- ]?wide|enterprise[- ]?wide|department[- ]?wide|across the (entire )?(department|agency)|all employees|all staff|all users", bl):
        return "enterprise_wide"
    if "department-wide" in bureau.lower() or "department wide" in bureau.lower():
        return "department"
    if re.search(r"\bpilot\b|\bprototype\b|proof of concept|\bpoc\b|test environment|sandbox", bl):
        return "pilot"
    if "prototype" in nl or "pilot" in nl:
        return "pilot"
    if dev_stage.strip().lower() == "initiated":
        return "pilot"
    if re.search(r"\bteam\b|small group of users", bl):
        return "team"
    if re.search(r"^office of |division|branch", bureau.lower()):
        return "office"
    return "bureau"


def detect_entry_type(blob, dev_method, vendors, tool_product, is_gen, sophistication, commercial_ai):
    bl = blob.lower()
    cots = any([
        vendors["github_copilot"], vendors["ms_copilot"], vendors["openai"], vendors["anthropic"],
        vendors["google"], vendors["lexis"], vendors["westlaw"], vendors["axon"],
        vendors["clarivate"], vendors["salesforce"], vendors["databricks"], vendors["palantir"],
        vendors["veritone"], vendors["sas"], vendors["flock"], vendors["cellhawk"],
        vendors["skillsoft"], vendors["smiths_detection"], vendors["meta"],
    ])

    in_house = "in-house" in dev_method.lower() and "contracting" not in dev_method.lower()
    contracting_only = ("contracting" in dev_method.lower()) and "in-house" not in dev_method.lower()

    # AWS Bedrock/SageMaker custom build = bespoke_application
    aws_custom = vendors["aws"] and re.search(r"bedrock|sagemaker|retrieval[- ]augmented|\brag\b|fine[- ]tun", bl)

    if cots and not aws_custom:
        return ("product_deployment", 1)
    if aws_custom:
        return ("bespoke_application", 1 if vendors["aws"] else 0)
    if in_house and is_gen:
        return ("bespoke_application", 0)
    if in_house:
        return ("custom_system", 0)
    if contracting_only:
        # Contractor-built specifically for the agency = custom_system
        return ("custom_system", 0)

    # Hybrid dev: 'Developed with both contracting and in-house resources.'
    if "both contracting and in-house" in dev_method.lower():
        if is_gen:
            return ("bespoke_application", 0)
        return ("custom_system", 0)

    # dev_method blank: rely on narrative / commercial_ai
    if commercial_ai.strip().lower() not in ("none of the above.", "none of the above", ""):
        return ("generic_use_pattern", 0)
    if cots:
        return ("product_deployment", 1)
    return ("custom_system", 0)


def is_generative(blob):
    return any(re.search(p, blob, re.IGNORECASE) for p in GEN_REGEX)


def is_coding_tool_check(blob, vendors):
    return vendors["github_copilot"] or any(re.search(p, blob, re.IGNORECASE) for p in CODING_REGEX)


def detect_arch(blob, is_gen, vendors, has_training_flag):
    bl = blob.lower()
    if re.search(r"retrieval[- ]augmented|\brag\b", bl):
        return "rag_pipeline"
    if re.search(r"fine[- ]tun", bl):
        return "fine_tuned"
    if re.search(r"\bagentic\b|autonomous agent|multi[- ]agent", bl):
        return "agentic_workflow"
    if has_training_flag == 1 and not is_gen:
        return "custom_trained"
    if is_gen and any([vendors["github_copilot"], vendors["ms_copilot"], vendors["openai"], vendors["anthropic"], vendors["google"]]):
        return "inference_only"
    if is_gen:
        return "unknown"
    return ""


def detect_training(blob, dev_method, is_gen, sophistication, entry_type):
    bl = blob.lower()
    if re.search(r"trained (a|the|our|on)|model training|training data|train(ing)? (a|our|the) model|custom[- ]trained|built from scratch|fine[- ]tun", bl):
        return 1
    if entry_type == "custom_system" and sophistication in ("classical_ml", "predictive_analytics", "computer_vision", "nlp_specific"):
        return 1
    if entry_type == "product_deployment":
        return 0
    return ""


def detect_public_facing(blob):
    bl = blob.lower()
    if re.search(r"public[- ]facing|provided to the public|public web|public chatbot|external users|publicly available chatbot|consumer[- ]facing", bl):
        return 1
    return 0


def build_reasoning(name, purpose, outputs, blob, is_gen, sophistication, scope, entry_type,
                    tool_product, bureau_sd, has_training, vendors):
    """Construct a one-sentence reasoning that quotes 2-6 words from the actual narrative."""

    # 1) Try to find a sophistication-grounding quote from the row's narrative
    soph_patterns = {
        "coding_assistant": [r"code (modernization|generation|completion|assistant|review)", r"writing.*code", r"reviewing.*code", r"github copilot", r"code assistant", r"\bcodium\b", r"\bcodex\b"],
        "agentic": [r"\bagentic\b", r"autonomous agent", r"multi[- ]agent"],
        "general_llm": [r"\bllm\b", r"large language model", r"generative ai", r"gen[- ]?ai", r"\bchatgpt\b", r"\bcopilot\b", r"\bgemini\b", r"\bclaude\b", r"summari[zs]e", r"chatbot", r"transformer[- ]based", r"retrieval[- ]augmented", r"\brag\b", r"draft.*text", r"foundation model"],
        "computer_vision": [r"computer vision", r"object (detection|recognition)", r"facial recognition", r"license plate", r"image (recognition|classification)", r"bounding box", r"geospatial", r"satellite imagery", r"sentinel-?2", r"land cover", r"\bocr\b"],
        "nlp_specific": [r"natural language processing", r"\bnlp\b", r"topic modeling", r"sentiment analysis", r"transcrib", r"translation", r"language detection", r"named entity", r"text classifi", r"information extraction", r"keyword extraction"],
        "predictive_analytics": [r"forecast", r"predict", r"anomaly detection", r"risk (score|model|assessment)", r"fraud (detect|identif)", r"machine learning", r"recommender", r"neural network", r"deep learning", r"regression", r"clustering"],
        "classical_ml": [r"machine learning", r"\bml\b", r"\bai\b", r"algorithm", r"model"],
    }

    quote = find_quote(blob, soph_patterns.get(sophistication, []))
    if not quote and tool_product and tool_product.lower() in blob.lower():
        quote = tool_product
    if not quote:
        # Fall back to first content phrase of purpose/outputs/name
        for src in (purpose, outputs, name):
            fc = first_clause(src, max_words=6)
            if fc and len(fc.split()) >= 2:
                quote = fc
                break
    if not quote:
        quote = (name or "use case")[:50]

    # 2) Build descriptor
    soph_descr = {
        "coding_assistant": "coding assistant",
        "agentic": "agentic workflow",
        "general_llm": "generative LLM use",
        "computer_vision": "computer-vision task",
        "nlp_specific": "classical NLP task",
        "predictive_analytics": "predictive ML model",
        "classical_ml": "classical ML pipeline",
    }[sophistication]

    scope_descr = {
        "enterprise_wide": "agency-wide deployment",
        "department": "department-wide deployment",
        "bureau": f"{bureau_sd}-scoped" if bureau_sd else "bureau-scoped",
        "office": f"office within {bureau_sd}" if bureau_sd else "office-level",
        "team": "team-level use",
        "pilot": "pilot/initiated stage",
    }[scope]

    sentence = f"Says '{quote}' — {soph_descr}, {scope_descr}."
    # Hard cap length
    if len(sentence) > 230:
        sentence = sentence[:227] + "..."
    return sentence


# ---------------------------------------------------------------------------
# Main per-row pipeline
# ---------------------------------------------------------------------------

def tag_row(row):
    name = (row.get("use_case_name") or "").strip()
    purpose = (row.get("purpose_benefits") or "").strip()
    outputs = (row.get("outputs") or "").strip()
    commercial = (row.get("commercial_ai") or "").strip()
    dev_method = (row.get("dev_method") or "").strip()
    dev_stage = (row.get("dev_stage") or "").strip()
    bureau = (row.get("bureau") or "").strip()
    agency = (row.get("agency_abbreviation") or "").strip()

    blob = "\n".join(s for s in [name, purpose, outputs, commercial] if s)

    vendors = detect_vendors(blob, name)
    tool_product, tool_vendor = detect_tool(vendors, blob, name)

    is_gen = is_generative(blob)
    # Vendor-driven gen overrides
    if vendors["lexis"] or vendors["westlaw"]:
        # AI-assisted legal research = generative summarization
        if re.search(r"ai[- ]assisted legal research|summari|legal research|case (briefing|search)|retrieval of court", blob, re.IGNORECASE):
            is_gen = True
    if vendors["clarivate"] or "skillsoft" in blob.lower() or "percipio" in blob.lower():
        if re.search(r"chatbot|generative|customize learning|interactive (tool|chatbot)|tailored", blob, re.IGNORECASE):
            is_gen = True
    if "virtual agent" in blob.lower() or "chatbot" in blob.lower() or "service ticket" in blob.lower():
        is_gen = True
    # "Data summaries" or "summaries and recommendations" = gen
    if re.search(r"data summari[zs]|summari[zs]e (and|with)|summaries and recommendations|provides? summaries", blob, re.IGNORECASE):
        is_gen = True
    if re.search(r"generation of (graphs|charts|images|content|text|reports)|generate (a |an )?(graph|chart|image|report|response|narrative)", blob, re.IGNORECASE):
        is_gen = True

    sophistication = detect_sophistication(blob, is_gen, name)
    is_coding = is_coding_tool_check(blob, vendors)

    # Refine: if classified as general_llm but no clear gen signal, downgrade
    # (covers cases where narrative purely says "ML")
    if sophistication == "general_llm" and not is_gen:
        sophistication = "classical_ml"

    # If is_gen but vendor and "code" present, flag coding_assistant
    if is_coding:
        sophistication = "coding_assistant"

    scope = detect_scope(blob, bureau, dev_stage, name)
    use_type = detect_use_type(blob, bureau, agency)

    entry_type, is_cots = detect_entry_type(blob, dev_method, vendors, tool_product, is_gen, sophistication, commercial)

    has_training = detect_training(blob, dev_method, is_gen, sophistication, entry_type)
    arch = detect_arch(blob, is_gen, vendors, has_training)
    public = detect_public_facing(blob)

    # Confidence
    confidence = "medium"
    if tool_product and is_cots:
        confidence = "high"
    elif sophistication in ("computer_vision", "nlp_specific", "predictive_analytics", "classical_ml") and entry_type == "custom_system":
        # Often clear in DOE/Census/NIST research
        if re.search(r"\bnrel\b|\bornl\b|\bpnnl\b|\blanl\b|\banl\b|\bllnl\b|\bslac\b|\bfnal\b|\bpppl\b|\binl\b|census|nist|noaa|uspto", bureau.lower()):
            confidence = "high"
    if entry_type == "generic_use_pattern":
        confidence = "low"
    if len(purpose) < 50 and len(outputs) < 30:
        confidence = "low"
    if is_gen and tool_product == "":
        confidence = "medium"  # leave at medium; we inferred genAI but no clear product
    # Very short / vague descriptions = low
    if len(blob) < 80:
        confidence = "low"

    bureau_sd = bureau_short(bureau)
    reasoning = build_reasoning(name, purpose, outputs, blob, is_gen, sophistication, scope,
                                entry_type, tool_product, bureau_sd, has_training, vendors)

    # General-LLM-access flag: only when narrative explicitly indicates broad chat access
    is_general_llm_access = 0
    if (sophistication == "general_llm"
        and (vendors["ms_copilot"] or vendors["openai"] or vendors["anthropic"] or vendors["google"])
        and re.search(r"all (employees|staff|users)|agency[- ]wide|department[- ]wide|chatbot.*all|provide.*staff.*(chat|llm|chatgpt)|chat with an llm", blob, re.IGNORECASE)):
        is_general_llm_access = 1

    out = {c: "" for c in OUT_COLS}
    out["use_case_id_2024"] = row.get("id", "")
    out["tagged_by_agent"] = AGENT
    out["entry_type"] = entry_type
    out["is_generative_ai"] = 1 if is_gen else 0
    out["ai_sophistication"] = sophistication
    out["deployment_scope"] = scope
    out["confidence"] = confidence
    out["reasoning"] = reasoning
    out["is_general_llm_access"] = is_general_llm_access
    out["is_coding_tool"] = 1 if is_coding else 0
    out["is_cots_commercial"] = is_cots
    out["tool_product_name"] = tool_product
    out["tool_vendor"] = tool_vendor
    out["is_microsoft_copilot"] = 1 if vendors["ms_copilot"] else 0
    out["is_openai"] = 1 if vendors["openai"] else 0
    out["is_anthropic"] = 1 if vendors["anthropic"] else 0
    out["is_google"] = 1 if vendors["google"] else 0
    out["is_github_copilot"] = 1 if vendors["github_copilot"] else 0
    out["is_aws_ai"] = 1 if vendors["aws"] else 0
    out["is_enterprise_wide"] = 1 if scope == "enterprise_wide" else 0
    out["architecture_type"] = arch
    out["has_model_training"] = has_training if has_training != "" else ""
    out["use_type"] = use_type
    out["is_public_facing"] = public
    out["scope_detail"] = bureau_sd
    return out


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    with open(INPUT, newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 376, f"Expected 376 rows, got {len(rows)}"

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()
        for row in rows:
            w.writerow(tag_row(row))

    with open(OUT) as f:
        out_rows = list(csv.DictReader(f))
    assert len(out_rows) == 376, f"Output row count mismatch: {len(out_rows)}"
    print(f"Wrote {len(out_rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
