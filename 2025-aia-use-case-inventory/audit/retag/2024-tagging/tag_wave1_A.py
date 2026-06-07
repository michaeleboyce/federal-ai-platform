"""Wave 1 Agent A: tag the 500 HHS+VA 2024 inventory rows.

Per-row signal extraction → emits one tag row per input row.
Reasoning sentences quote 2-6 words from the source narrative.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IN_PATH = ROOT / "inputs" / "A.csv"
OUT_PATH = ROOT / "wave1" / "A.csv"
AGENT = "wave1-A"

OUTPUT_COLS = [
    "use_case_id_2024",
    "tagged_by_agent",
    "entry_type",
    "is_generative_ai",
    "ai_sophistication",
    "deployment_scope",
    "confidence",
    "reasoning",
    "is_general_llm_access",
    "is_coding_tool",
    "is_cots_commercial",
    "tool_product_name",
    "tool_vendor",
    "is_microsoft_copilot",
    "is_openai",
    "is_anthropic",
    "is_google",
    "is_github_copilot",
    "is_aws_ai",
    "is_enterprise_wide",
    "architecture_type",
    "has_model_training",
    "use_type",
    "is_public_facing",
    "scope_detail",
]


# ---------- helpers ----------

WORD = re.compile(r"\w+(?:[-/]\w+)*")


def quote_phrase(text: str, pattern: re.Pattern, default: str | None = None) -> str | None:
    """Return a short quoted phrase from text matching pattern (2-6 words)."""
    m = pattern.search(text)
    if not m:
        return default
    snippet = m.group(0)
    words = snippet.split()
    if len(words) > 6:
        words = words[:6]
    return " ".join(words).strip().strip(".,;:()[]")


def find_quote(text: str, patterns: list[str], window: int = 5) -> str | None:
    """Find first matching pattern in text and return ~window-word snippet around it."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 20)
            chunk = text[start:end]
            words = chunk.split()
            # Find the matched word and take a centered window
            for i, w in enumerate(words):
                if re.search(pat, w, re.IGNORECASE):
                    lo = max(0, i - 1)
                    hi = min(len(words), i + window)
                    return " ".join(words[lo:hi]).strip().strip(".,;:()[]\"")
            return " ".join(words[:window]).strip().strip(".,;:()[]\"")
    return None


def first_sentence(text: str, max_words: int = 18) -> str:
    """Take a short clip near the start of the narrative for fallback reasoning."""
    text = text.strip()
    # Split on sentence boundary
    parts = re.split(r"(?<=[.!?])\s+", text)
    if parts:
        s = parts[0]
    else:
        s = text
    words = s.split()
    if len(words) > max_words:
        words = words[:max_words]
    return " ".join(words).strip().strip(".,;:()[]\"")


# ---------- vendor / signal detectors ----------

# Generative-AI signals
GEN_PATTERNS = [
    r"\bLLM[s]?\b",
    r"large language model",
    r"\bGPT-?[0-9]?\b",
    r"\bChatGPT\b",
    r"\bChat\s*CDC\b",
    r"\bgenerative\b",
    r"\bGen[\s-]?AI\b",
    r"\bgenAI\b",
    r"\bcopilot\b",
    r"\bBedrock\b",
    r"\bClaude\b",
    r"\bGemini\b",
    r"\bAzure OpenAI\b",
    r"\bOpenAI\b",
    r"retrieval[- ]augmented generation",
    r"\bRAG\b",
    r"\btext generation\b",
    r"\bsummariz",
    r"\bsummary\b",
    r"\bchatbot\b",
    r"\bvirtual assistant\b",
    r"\bdrafting\b",
    r"prompt[- ]engineer",
    r"foundation model",
    r"\bdiffusion\b",
    r"\bcode generation\b",
    r"\bDALL[- ]?E\b",
    r"\btranscrib(?:e|ing)\b.*\bsummariz",
]

COMPUTER_VISION_PATTERNS = [
    r"\bcomputer vision\b",
    r"\bimage classif",
    r"\bobject detect",
    r"\bsegmentation\b",
    r"\bX-?ray\b",
    r"\bMRI\b",
    r"\bCT scan\b",
    r"\bradiograph",
    r"\bmammograph",
    r"\bimaging\b",
    r"\bimage analysis\b",
    r"\bfacial recognition\b",
    r"\bOCR\b",
    r"optical character",
    r"\bsatellite image",
    r"\bremote sensing\b",
    r"\bvideo analysis\b",
    r"\bbioimaging\b",
    r"\bhistolog",
    r"\bdigital pathology\b",
    r"\bcell counting\b",
    r"\bpolyp detection\b",
]

NLP_PATTERNS = [
    r"\bnatural language processing\b",
    r"\bNLP\b",
    r"\bnamed entity\b",
    r"\bentity extraction\b",
    r"\bsentiment\b",
    r"\btopic modeling\b",
    r"\btext mining\b",
    r"\btext classif",
    r"\bspeech[- ]to[- ]text\b",
    r"\bspeech recognition\b",
    r"\btranscrib",
    r"\btranslation\b",
    r"\bautocod",
]

PREDICTIVE_PATTERNS = [
    r"\bpredict",
    r"\bforecast",
    r"\brisk model",
    r"\brisk score\b",
    r"\bsurviv",
    r"\bmortalit",
    r"\breadmission\b",
    r"\bsuicide risk\b",
    r"\bopioid risk\b",
]

CLASSICAL_ML_PATTERNS = [
    r"\bmachine learning\b",
    r"\brandom forest\b",
    r"\bxgboost\b",
    r"\bgradient boost",
    r"\bregression\b",
    r"\bclassif",
    r"\bclustering\b",
    r"\banomaly detect",
    r"\boutlier",
    r"\bdecision tree",
    r"\bsupport vector",
    r"\bsupervised learning\b",
    r"\bunsupervised learning\b",
]

AGENTIC_PATTERNS = [
    r"\bagent(?:ic)?\b",
    r"\bautonomous\b",
    r"\bmulti[- ]agent\b",
    r"\borchestrat",
]

CODING_PATTERNS = [
    r"github\s*copilot",
    r"\bcoding assistant\b",
    r"\bcode completion\b",
    r"\bcursor\b(?!\s*pad)",
    r"\bcodex\b",
    r"developer productivity",
    r"\bsoftware development\b.*\bAI\b",
]

# Vendor detection (each returns label + flags)
VENDOR_REGEXES = [
    ("Microsoft 365 Copilot", "Microsoft",
     [r"microsoft\s*365\s*copilot", r"\bm365\s*copilot\b", r"office\s*copilot"], "ms_copilot"),
    ("Microsoft Copilot", "Microsoft",
     [r"\bcopilot\s*(?:chat|for security|studio)?\b"], "ms_copilot"),
    ("Azure OpenAI", "Microsoft/OpenAI",
     [r"azure\s*open\s*ai", r"\bazure ai\b"], "ms_openai"),
    ("ChatGPT", "OpenAI",
     [r"\bchatgpt\b", r"chatgpt\s*enterprise"], "openai"),
    ("GPT-4", "OpenAI", [r"\bgpt-?4\b"], "openai"),
    ("OpenAI", "OpenAI", [r"\bopenai\b"], "openai"),
    ("Claude", "Anthropic", [r"\bclaude\b"], "anthropic"),
    ("Gemini", "Google", [r"\bgemini\b"], "google"),
    ("Vertex AI", "Google", [r"vertex\s*ai"], "google"),
    ("GitHub Copilot", "GitHub/Microsoft", [r"github\s*copilot"], "github_copilot"),
    ("AWS Bedrock", "AWS", [r"\bbedrock\b"], "aws"),
    ("AWS SageMaker", "AWS", [r"sagemaker"], "aws"),
    ("Amazon Textract", "AWS", [r"textract"], "aws"),
    ("Amazon Comprehend", "AWS", [r"comprehend"], "aws"),
    ("Amazon Rekognition", "AWS", [r"rekognition"], "aws"),
]


def detect_vendor(text: str):
    """Return (product_name, vendor, flag_set) for the first vendor matched."""
    lower = text.lower()
    flags = set()
    product = None
    vendor = None
    for prod, ven, patterns, flag in VENDOR_REGEXES:
        for pat in patterns:
            if re.search(pat, lower):
                if product is None:
                    product = prod
                    vendor = ven
                flags.add(flag)
                break
    return product, vendor, flags


def has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


# ---------- topic_area → use_type ----------

USE_TYPE_BY_TOPIC = {
    "Health & Medical": "mission_critical",
    "Mission-Enabling (internal agency support)": "administrative",
    "Mission-Enabling": "administrative",
    "Government Services (includes Benefits and Service Delivery)": "mission_critical",
    "Diplomacy & Trade": "mission_critical",
    "Energy & the Environment": "mission_critical",
    "Education & Workforce": "mission_critical",
    "Science & Space": "research",
    "Transportation": "mission_critical",
    "Law & Justice": "mission_critical",
    "Emergency Management": "mission_critical",
}

# Cybersecurity narrative override
CYBER_PATTERNS = [
    r"cybersecurity\b",
    r"\bSOC\b",
    r"\bSIEM\b",
    r"\bphishing\b",
    r"\bmalware\b",
    r"\bintrusion\b",
    r"\bthreat detect",
    r"\bvulnerability\b",
]
IT_OPS_PATTERNS = [
    r"\bIT operations\b",
    r"\bhelpdesk\b",
    r"\bservice desk\b",
    r"\bIT support\b",
    r"\binfrastructure monitoring\b",
    r"\bDevOps\b",
    r"\bincident management\b",
]


# ---------- main tagging ----------

def tag_row(row: dict) -> dict:
    name = row.get("use_case_name", "") or ""
    purpose = row.get("purpose_benefits", "") or ""
    outputs = row.get("outputs", "") or ""
    commercial_ai = row.get("commercial_ai", "") or ""
    dev_method = row.get("dev_method", "") or ""
    dev_stage = row.get("dev_stage", "") or ""
    topic = row.get("topic_area", "") or ""
    bureau = row.get("bureau", "") or ""
    agency = row.get("agency_abbreviation", "") or ""

    full = f"{name}\n{purpose}\n{outputs}\n{commercial_ai}"
    full_l = full.lower()

    out = {c: "" for c in OUTPUT_COLS}
    out["use_case_id_2024"] = row["id"]
    out["tagged_by_agent"] = AGENT

    # ----- vendor detection -----
    product, vendor, vflags = detect_vendor(full)
    if product:
        out["tool_product_name"] = product
        out["tool_vendor"] = vendor
    out["is_microsoft_copilot"] = "1" if "ms_copilot" in vflags else ""
    out["is_openai"] = "1" if ("openai" in vflags or "ms_openai" in vflags) else ""
    out["is_anthropic"] = "1" if "anthropic" in vflags else ""
    out["is_google"] = "1" if "google" in vflags else ""
    out["is_github_copilot"] = "1" if "github_copilot" in vflags else ""
    out["is_aws_ai"] = "1" if "aws" in vflags else ""

    # ----- generative AI -----
    is_gen = has_any(full, GEN_PATTERNS)

    # ----- sophistication -----
    soph = None
    if has_any(full, CODING_PATTERNS) or "github_copilot" in vflags:
        soph = "coding_assistant"
    elif has_any(full, AGENTIC_PATTERNS) and is_gen:
        soph = "agentic"
    elif is_gen:
        soph = "general_llm"
    elif has_any(full, COMPUTER_VISION_PATTERNS):
        soph = "computer_vision"
    elif has_any(full, NLP_PATTERNS):
        soph = "nlp_specific"
    elif has_any(full, PREDICTIVE_PATTERNS):
        soph = "predictive_analytics"
    elif has_any(full, CLASSICAL_ML_PATTERNS):
        soph = "classical_ml"
    else:
        # Fallback: most VHA FDA-cleared imaging devices = computer_vision; medical = classical_ml
        if "FDA-cleared medical device" in purpose:
            # Default to classical_ml unless name suggests imaging
            if re.search(r"(?i)imaging|radiolog|dose|x-?ray|mammo|MRI|CT|ultrasound|fundus|retina|pathology|optical|tomograph|ECG|EKG", name):
                soph = "computer_vision"
            else:
                soph = "classical_ml"
        else:
            soph = "classical_ml"

    out["ai_sophistication"] = soph
    out["is_generative_ai"] = "1" if is_gen else "0"

    # ----- entry_type -----
    # Defaults; refined below
    dev_method_l = dev_method.lower()
    contracted = "contract" in dev_method_l
    in_house = "in-house" in dev_method_l
    hybrid = contracted and in_house

    # FDA-cleared medical device pattern is essentially a product deployment of a vendor device
    fda_device = "FDA-cleared medical device" in purpose

    if product and ("copilot" in product.lower() or product in ("ChatGPT", "Azure OpenAI", "GitHub Copilot")):
        # Specific named generative product
        entry_type = "product_deployment"
    elif fda_device:
        entry_type = "product_deployment"
    elif is_gen and (re.search(r"\bRAG\b", full, re.IGNORECASE) or "retrieval-augmented" in full_l or "retrieval augmented" in full_l):
        # In-house wrapper around a foundation model with RAG
        entry_type = "bespoke_application"
    elif is_gen and contracted and not in_house:
        # Contracted LLM solution but no specific product named
        entry_type = "bespoke_application"
    elif is_gen and in_house:
        entry_type = "bespoke_application"
    elif in_house and not contracted:
        entry_type = "custom_system"
    elif contracted and not in_house and not is_gen:
        # Acquired classical/CV/NLP solution
        entry_type = "product_deployment"
    elif hybrid:
        entry_type = "bespoke_application"
    else:
        # Unknown dev_method
        if is_gen:
            entry_type = "bespoke_application"
        else:
            entry_type = "custom_system"

    # Override: clearly generic patterns (no named system, agency-wide LLM access)
    if is_gen and re.search(r"(?i)(agency[- ]wide|enterprise[- ]wide|all employees|general[- ]purpose chatbot)", full) and not product:
        entry_type = "generic_use_pattern"

    out["entry_type"] = entry_type

    # ----- deployment_scope -----
    # Strong signal in narrative
    scope = None
    if re.search(r"(?i)(enterprise[- ]wide|agency[- ]wide|department[- ]wide|all employees|HHS[- ]wide|VA[- ]wide)", full):
        scope = "enterprise_wide"
    elif re.search(r"(?i)\bpilot\b", full) or dev_stage in ("Initiated",):
        scope = "pilot"
    elif bureau and bureau not in (agency, ""):
        # Bureau-scoped if a sub-bureau named
        scope = "bureau"
    else:
        scope = "department"

    # Office override: "Office of X" mentioned in narrative + small scale
    if scope in ("bureau", "department") and re.search(r"(?i)office of\b", purpose) and dev_stage != "Operation and Maintenance":
        # Only override to office if clearly scoped to that office
        if re.search(r"(?i)used by .{0,30}office of|within the .{0,30}office of|the .{0,40}office of\b", purpose):
            scope = "office"

    # VHA: huge scope, set as bureau (bureau is VHA itself)
    out["deployment_scope"] = scope
    out["is_enterprise_wide"] = "1" if scope == "enterprise_wide" else "0"
    if bureau and bureau not in (agency, "HHS", "VA"):
        # Strip the "XYZ: long name" prefix for scope_detail
        sd = bureau.split(":")[0].strip() if ":" in bureau else bureau
        out["scope_detail"] = sd
    elif bureau:
        out["scope_detail"] = bureau

    # ----- is_general_llm_access -----
    if is_gen and re.search(r"(?i)(general[- ]purpose chatbot|enterprise chatbot|GenAI chatbot|broad access|all employees|agency[- ]wide.*chatbot|chatbot.*agency[- ]wide)", full):
        out["is_general_llm_access"] = "1"
    elif is_gen and "ms_copilot" in vflags and re.search(r"(?i)(agency|enterprise|all staff|employees)", full):
        out["is_general_llm_access"] = "1"

    # ----- is_coding_tool -----
    if soph == "coding_assistant":
        out["is_coding_tool"] = "1"

    # ----- is_cots_commercial -----
    if contracted and not in_house:
        out["is_cots_commercial"] = "1"
    elif fda_device:
        out["is_cots_commercial"] = "1"
    elif in_house and not contracted:
        out["is_cots_commercial"] = "0"

    # ----- architecture_type -----
    if re.search(r"(?i)\bRAG\b|retrieval[- ]augmented", full):
        out["architecture_type"] = "rag_pipeline"
    elif re.search(r"(?i)fine[- ]tun(?:e|ing|ed)", full):
        out["architecture_type"] = "fine_tuned"
    elif re.search(r"(?i)agent(?:ic)? workflow|multi[- ]agent", full):
        out["architecture_type"] = "agentic_workflow"
    elif soph in ("classical_ml", "computer_vision", "nlp_specific", "predictive_analytics") and in_house:
        out["architecture_type"] = "custom_trained"
    elif is_gen and not product:
        out["architecture_type"] = "inference_only"
    elif product:
        out["architecture_type"] = "inference_only"
    else:
        out["architecture_type"] = "unknown"

    # ----- has_model_training -----
    if re.search(r"(?i)(train(?:ed|ing) (?:a |our |the |custom |our own )?model|fine[- ]tun|model training|train the model)", full):
        out["has_model_training"] = "1"
    elif soph in ("classical_ml", "computer_vision", "predictive_analytics") and in_house:
        out["has_model_training"] = "1"
    else:
        out["has_model_training"] = "0"

    # ----- use_type -----
    use_type = USE_TYPE_BY_TOPIC.get(topic, None)
    if has_any(full, CYBER_PATTERNS):
        use_type = "cybersecurity"
    elif has_any(full, IT_OPS_PATTERNS):
        use_type = "it_operations"
    elif use_type is None:
        use_type = "administrative"
    out["use_type"] = use_type

    # ----- is_public_facing -----
    if re.search(r"(?i)(public[- ]facing|publicly available|to the public|veterans? facing|patient[- ]facing|beneficiar(?:y|ies)[- ]facing|external users?|website chatbot|public website)", full):
        out["is_public_facing"] = "1"
    elif re.search(r"(?i)(internal[- ]facing|internal use|staff[- ]facing|employee[- ]facing|internal to)", full):
        out["is_public_facing"] = "0"

    # ----- confidence -----
    # high: explicit product or vendor named, or FDA-device boilerplate (very clear what it is)
    # medium: clear domain signal (CV/NLP/ML) but no product
    # low: ambiguous text or very thin description
    text_len = len(purpose) + len(outputs)
    if product or "FDA-cleared medical device" in purpose:
        conf = "high"
    elif text_len < 120:
        conf = "low"
    elif is_gen and (re.search(r"\bLLM\b|GPT|RAG|copilot", full, re.IGNORECASE)):
        conf = "high"
    elif soph in ("computer_vision", "nlp_specific", "predictive_analytics") and text_len > 200:
        conf = "medium"
    else:
        conf = "medium"
    out["confidence"] = conf

    # ----- reasoning -----
    # Build a sentence that quotes 2-6 words from narrative
    quote = None
    # Prefer a quote that drove the chosen sophistication
    if is_gen:
        quote = find_quote(full, [r"LLM", r"large language model", r"GPT-?[0-9]?", r"ChatGPT",
                                   r"generative", r"Gen[\s-]?AI", r"copilot", r"Bedrock",
                                   r"Claude", r"Gemini", r"RAG", r"retrieval[- ]augmented",
                                   r"chatbot", r"summariz", r"prompt"])
    elif soph == "computer_vision":
        quote = find_quote(full, [r"computer vision", r"image", r"X-?ray", r"MRI", r"CT scan",
                                   r"radiograph", r"mammograph", r"imaging", r"segmentation",
                                   r"object detect", r"OCR"])
    elif soph == "nlp_specific":
        quote = find_quote(full, [r"natural language", r"NLP", r"sentiment", r"topic model",
                                   r"entity extract", r"transcrib", r"translation",
                                   r"speech recognition"])
    elif soph == "predictive_analytics":
        quote = find_quote(full, [r"predict", r"forecast", r"risk model", r"risk score",
                                   r"mortalit", r"readmission", r"suicide risk"])
    elif soph == "classical_ml":
        quote = find_quote(full, [r"machine learning", r"random forest", r"classif",
                                   r"clustering", r"anomaly detect", r"regression"])

    if not quote:
        quote = first_sentence(purpose or outputs or name, max_words=12)

    quote = quote.strip().strip("\"'")
    if len(quote) > 90:
        quote = quote[:90].rsplit(" ", 1)[0]

    # Compose reasoning sentence
    parts = []
    if "FDA-cleared medical device" in purpose:
        parts.append(f"FDA-cleared medical device for VHA imaging/clinical use; '{quote}'.")
    else:
        if entry_type == "generic_use_pattern":
            parts.append(f"Agency-wide pattern: '{quote}' → {soph}.")
        elif entry_type == "product_deployment":
            parts.append(f"Named product deployment: '{quote}' → {soph}.")
        elif entry_type == "bespoke_application":
            parts.append(f"In-house wrapper/RAG over foundation model: '{quote}' → {soph}.")
        elif entry_type == "custom_system":
            parts.append(f"In-house {soph} system: '{quote}'.")
        else:
            parts.append(f"{entry_type}: '{quote}' → {soph}.")

    out["reasoning"] = parts[0]

    return out


def main():
    with IN_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    tagged = [tag_row(r) for r in rows]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLS)
        writer.writeheader()
        writer.writerows(tagged)

    print(f"Wrote {len(tagged)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
