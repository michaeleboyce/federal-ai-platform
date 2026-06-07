"""wave1-D tagging script for partition D (USDA + DOI + USAID).

Reads audit/retag/2024-tagging/inputs/D.csv and writes
audit/retag/2024-tagging/wave1/D.csv.

NO 2025 source reads. Tags derived only from the 2024 narrative columns.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "audit/retag/2024-tagging/inputs/D.csv"
OUTPUT = ROOT / "audit/retag/2024-tagging/wave1/D.csv"

OUT_COLS = [
    "use_case_id_2024", "tagged_by_agent", "entry_type", "is_generative_ai",
    "ai_sophistication", "deployment_scope", "confidence", "reasoning",
    "is_general_llm_access", "is_coding_tool", "is_cots_commercial",
    "tool_product_name", "tool_vendor", "is_microsoft_copilot", "is_openai",
    "is_anthropic", "is_google", "is_github_copilot", "is_aws_ai",
    "is_enterprise_wide", "architecture_type", "has_model_training",
    "use_type", "is_public_facing", "scope_detail",
]


def first_phrase(text, patterns, max_words=6):
    """Find the first matching phrase in text and return up to max_words words."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            words = m.group(0).split()
            return " ".join(words[:max_words])
    return None


def short_quote(text, max_words=6):
    """Pick a short opening phrase from text (fallback)."""
    if not text:
        return ""
    words = re.findall(r"\S+", text)[:max_words]
    return " ".join(words)


def tag_row(row):
    """Return dict with all OUT_COLS for one input row."""
    agency = row.get("agency_abbreviation", "")
    bureau = row.get("bureau", "")
    name = row.get("use_case_name", "")
    purpose = row.get("purpose_benefits", "")
    outputs = row.get("outputs", "")
    commercial_ai = row.get("commercial_ai", "") or ""
    dev_method = row.get("dev_method", "") or ""
    dev_stage = row.get("dev_stage", "") or ""

    blob = f"{name} {purpose} {outputs}".lower()
    name_lower = name.lower()

    tags = {c: "" for c in OUT_COLS}
    tags["use_case_id_2024"] = row["id"]
    tags["tagged_by_agent"] = "wave1-D"

    # ---- vendor / product detection ----
    is_ms_copilot = 0
    is_openai = 0
    is_anthropic = 0
    is_google = 0
    is_github_copilot = 0
    is_aws_ai = 0
    is_coding_tool = 0
    is_general_llm_access = 0
    is_cots_commercial = 0
    tool_product_name = ""
    tool_vendor = ""

    if re.search(r"github copilot|gh copilot", blob):
        is_github_copilot = 1
        is_coding_tool = 1
        is_cots_commercial = 1
        tool_product_name = "GitHub Copilot"
        tool_vendor = "GitHub/Microsoft"
    if re.search(r"\bm365 copilot|microsoft 365 copilot|copilot for microsoft 365|copilot chat|copilot for security|\bcopilot\b", blob) \
            and not re.search(r"github copilot", blob):
        # Disambiguate: only set MS copilot if "copilot" appears and not solely github
        if re.search(r"microsoft|m365|365|office", blob) or "copilot" in blob:
            is_ms_copilot = 1
            is_cots_commercial = 1
            if not tool_product_name:
                tool_product_name = "Microsoft 365 Copilot"
                tool_vendor = "Microsoft"
    if re.search(r"\bchatgpt|openai|\bgpt-?[345]|azure openai", blob):
        is_openai = 1
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "Azure OpenAI" if "azure" in blob else "ChatGPT/OpenAI"
            tool_vendor = "OpenAI/Microsoft" if "azure" in blob else "OpenAI"
    if re.search(r"\bclaude\b|anthropic", blob):
        is_anthropic = 1
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "Claude"
            tool_vendor = "Anthropic"
    if re.search(r"\bgemini\b|vertex ai|google duet|\bbard\b|google ai", blob):
        is_google = 1
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "Gemini/Vertex"
            tool_vendor = "Google"
    if re.search(r"\bbedrock|sagemaker|amazon comprehend|amazon rekognition|amazon textract|aws ai", blob):
        is_aws_ai = 1
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "AWS AI"
            tool_vendor = "AWS"

    if re.search(r"\besri|arcgis", blob):
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "ArcGIS/Esri"
            tool_vendor = "Esri"
    if re.search(r"salesforce|einstein", blob):
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "Salesforce Einstein"
            tool_vendor = "Salesforce"
    if re.search(r"\bservicenow\b", blob):
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "ServiceNow"
            tool_vendor = "ServiceNow"
    if re.search(r"\badobe\b|firefly|acrobat ai", blob):
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "Adobe (Firefly/Acrobat AI)"
            tool_vendor = "Adobe"
    if re.search(r"power automate|microsoft power platform|power bi", blob):
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "MS Power Platform"
            tool_vendor = "Microsoft"
    if re.search(r"alteryx", blob):
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "Alteryx"
            tool_vendor = "Alteryx"
    if re.search(r"caseguard", blob):
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "CaseGuard Studio"
            tool_vendor = "CaseGuard"
    if re.search(r"\bdatabricks\b|databricks ai", blob):
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "Databricks"
            tool_vendor = "Databricks"
    if re.search(r"\bgrammarly\b|writer\.com", blob):
        is_cots_commercial = 1
        if not tool_product_name:
            tool_product_name = "Grammarly/Writer"
            tool_vendor = "Grammarly"

    # general LLM access flag — agency-wide chat to LLM
    if re.search(r"(chat\s?gpt|chatbot|chat with|llm).*(secure|agency|user|deploy|access)", blob) \
            or re.search(r"(doichatgpt|chat gpt|chat-gpt)", blob):
        is_general_llm_access = 1
        is_cots_commercial = 1 if is_cots_commercial or is_openai or is_ms_copilot else 0

    # ---- generative AI detection ----
    # Strong/explicit signals (high confidence gen)
    strong_gen = [
        r"\bgenerative\b", r"large language model", r"\bllm\b", r"chatgpt", r"\bgpt-?[345]",
        r"\bgemini\b", r"\bclaude\b", r"openai", r"bedrock",
        r"copilot", r"chat\s?bot", r"chat\s?gpt",
        r"diffusion", r"stable diffusion", r"image generation",
        r"retrieval[- ]augmented", r"\brag\b",
        r"prompt engineer", r"foundation model", r"firefly",
        r"ai[- ]assist(ed|ant) (writing|drafting)",
        r"caption generation", r"transcription using ai", r"speech.*generat",
    ]
    # Weaker signals — only count as gen if combined with other context
    weak_gen = [
        r"\bsummariz[ae]", r"summarization", r"text generation", r"natural language generation",
        r"drafting (documents?|content|memos|emails)", r"\bdraft\b.*document",
        r"automate.*writing", r"generate.*(text|report|summary|content|caption|response)",
        r"ai[- ]?(generated|powered) (text|content|caption|summary)",
    ]
    is_gen = 0
    for p in strong_gen:
        if re.search(p, blob):
            is_gen = 1
            break
    if not is_gen:
        for p in weak_gen:
            if re.search(p, blob):
                is_gen = 1
                break
    # Mention of "AI chatbot" name with LLM context
    if re.search(r"ai chat", blob) and re.search(r"language model|llm|chat with", blob):
        is_gen = 1

    # ---- ai_sophistication ----
    soph = "classical_ml"  # default
    if is_gen:
        if is_coding_tool:
            soph = "coding_assistant"
        elif re.search(r"agentic|autonomous agent|multi[- ]agent", blob):
            soph = "agentic"
        else:
            soph = "general_llm"
    else:
        # Non-generative paths
        cv_signals = [
            r"satellite imag", r"aerial imag", r"remote sens", r"computer vision",
            r"image classif", r"object detect", r"image segment", r"\blandsat\b",
            r"\bsentinel-?2\b", r"naip imagery", r"\blidar\b", r"orthoimagery",
            r"camera trap", r"trail camera", r"underwater video", r"sonar imag",
            r"image recogni", r"photo identif", r"deep learning.*imag",
            r"convolutional neural", r"\bcnn\b", r"u-?net", r"\byolo\b",
            r"video.*redact", r"audio.*redact", r"video analyt", r"facial recogn",
            r"\baerial\b.*classif", r"\bdrone\b", r"\buav\b", r"unmanned aerial",
            r"detect.*(species|wildlife|tree|land cover|crop|field|building|object)",
            r"image.*segment", r"\bimagery\b", r"photo.*analy", r"raster",
            r"land[ -]?cover", r"\bndvi\b", r"\bdem\b model",
            r"scanned document", r"\bocr\b", r"optical character",
            r"image-based", r"blood smear", r"cell count.*image", r"counting.*cells",
            r"video.*analy", r"image.*analy", r"detect.*image", r"image.*detect",
        ]
        nlp_signals = [
            r"topic model", r"sentiment analy", r"named entity", r"text classif",
            r"text mining", r"text analyt", r"text extract", r"document classif",
            r"natural language process", r"\bnlp\b", r"keyword extract",
            r"document summariz", r"language model(?! free)", r"word embedding",
            r"document tag", r"automated indexing", r"thesaurus", r"controlled vocabulary",
            r"information extract", r"semantic search", r"document parsing",
            r"entity extraction", r"text categor", r"\btf[- ]?idf\b",
            r"document(s)? (review|process|analy|extract|classif|tag)",
            r"public comment", r"narrative.*analy", r"survey response",
            r"\bcomments?\b.*(process|analy|classif|cluster|categor)",
            r"\bemail\b.*(classif|categor|route|analy)",
            r"speech (to|recogni|transcrib)", r"\btranscrib", r"transcript",
            r"extract.*(from|data).*document", r"document.*extract",
            r"scrap(e|ing).*document", r"parse.*document", r"chatlog",
            r"text-based", r"\btext\b.*(matching|search|categor)",
            r"\bsearch\b.*(document|text)", r"language understanding",
            r"\bclassif(y|ication)\b.*\b(text|document|email|comment|narrative|article|complaint)",
            r"\b(extract|parse)\b.*\b(text|content|metadata|fields?|forms?)\b",
            r"automated.*coding",
        ]
        predictive_signals = [
            r"predict(ing|ion|ive|s)?", r"forecast", r"risk score", r"risk model",
            r"early warning", r"anomaly detect", r"time series", r"trend analy",
            r"probability of", r"likelihood", r"propensity", r"churn",
            r"survival analy", r"hazard model",
            r"estimat(e|ing|ion|es)",
            r"simulat(e|ing|ion|or)",
            r"recommend(ation|er)", r"scoring (model|algorithm)", r"classif(y|ication).*risk",
            r"detect(ion)?.*fraud", r"fraud detect",
            r"\bdetect\b.*(earthquake|landslide|outbreak|disease|abnormal|anomal)",
            r"model.*(stream|water|temperature|nutrient|salinity|flow|crop|yield|species|population|abundance|wildfire|fire|drought|flood|climate)",
            r"\bmodel development", r"machine learning model.*to (estimat|predict|forecast|model|simulat)",
            r"reinforcement learning", r"\boptimiz(e|ing|ation)\b.*(operation|control|schedul|resource)",
            r"\bassess(ment)?\b.*(risk|impact|effect|condition)",
            r"automated (decision|scoring|review|triage)",
        ]
        # Decide based on most-specific match
        cv_hit = any(re.search(p, blob) for p in cv_signals)
        nlp_hit = any(re.search(p, blob) for p in nlp_signals)
        pred_hit = any(re.search(p, blob) for p in predictive_signals)

        # Prioritize: CV > NLP > predictive > classical
        # but if a row mentions both imagery and text, choose by which is dominant
        if cv_hit and not nlp_hit:
            soph = "computer_vision"
        elif nlp_hit and not cv_hit:
            soph = "nlp_specific"
        elif cv_hit and nlp_hit:
            # both — choose by which appears in name/outputs (likely primary)
            primary = (name + " " + outputs).lower()
            if re.search(r"imag|video|photo|satellit|aerial|lidar|sonar|camera|redact|landsat|map|gis", primary):
                soph = "computer_vision"
            else:
                soph = "nlp_specific"
        elif pred_hit:
            soph = "predictive_analytics"
        else:
            soph = "classical_ml"

    # ---- entry_type ----
    in_house = "in-house" in dev_method.lower()
    contracting = "contract" in dev_method.lower()

    if is_general_llm_access or (is_gen and (is_ms_copilot or (is_openai and "chatgpt" in blob))):
        # Wrapping a 3rd party LLM
        if "doichatgpt" in blob or re.search(r"customized.*govchat|azure openai", blob):
            entry_type = "bespoke_application"
        elif is_ms_copilot and not in_house:
            entry_type = "product_deployment"
        else:
            entry_type = "generic_use_pattern"
    elif is_cots_commercial and not in_house and tool_product_name:
        # Off-the-shelf commercial product, not wrapped in-house
        entry_type = "product_deployment"
    elif is_cots_commercial and tool_product_name and re.search(r"\b(adobe|alteryx|caseguard|grammarly|esri|arcgis|salesforce|servicenow|databricks|power automate|power bi)\b", blob):
        # Even if marked in-house, products like Adobe/Alteryx are clearly the COTS tool
        entry_type = "product_deployment"
    elif in_house and is_gen and (is_openai or is_aws_ai or is_anthropic or is_google):
        entry_type = "bespoke_application"
    elif in_house:
        entry_type = "custom_system"
    elif contracting:
        # in-house developed with contractors — still custom
        entry_type = "custom_system"
    else:
        entry_type = "custom_system"

    # ---- deployment_scope ----
    # USGS / NRCS / FS / APHIS / NASS etc. → bureau
    # USAID/<country> or USAID/<bureau> → office or bureau
    # OCIO/department-wide LLM chat → department or enterprise_wide
    scope = "bureau"
    scope_detail = bureau or ""
    if agency == "DOI" and bureau in ("OCIO",) and re.search(r"doichatgpt|doi users|doi-wide|department", blob):
        scope = "department"
    elif agency == "DOI" and bureau.startswith("OS - Office of the Secretary"):
        scope = "department"
    elif agency == "USAID":
        if re.search(r"^USAID/(Colombia|India|Pakistan|Kenya|Mozambique|Nigeria|Bangladesh|Cambodia|Philippines|Indonesia|Senegal|Tanzania|Ghana|Ethiopia|Uganda|Zambia|Egypt|Liberia|Malawi|Rwanda|Madagascar|Burma|Nepal|DRC|Mali|Honduras|Guatemala)$", bureau):
            scope = "office"
        elif bureau.startswith("USAID/Bureau for"):
            scope = "bureau"
        else:
            scope = "office"
    elif agency == "USDA":
        scope = "bureau"
    elif agency == "DOI":
        scope = "bureau"

    # Pilot detection — only when the narrative explicitly says it's a pilot/PoC,
    # not just because dev_stage is "Initiated". Many Initiated projects are
    # full bureau efforts that haven't shipped yet.
    if re.search(r"\bpilot\b|proof of concept|\bpoc\b|prototyp(e|ing)|exploratory|feasibility study", blob):
        scope = "pilot"

    is_enterprise_wide = 1 if scope == "enterprise_wide" else 0

    # ---- architecture_type ----
    if is_gen:
        if re.search(r"retrieval[- ]augmented|\brag\b|knowledge base|document retrieval|vector (search|store|db)", blob):
            arch = "rag_pipeline"
        elif re.search(r"fine[- ]?tun", blob):
            arch = "fine_tuned"
        elif re.search(r"agentic|autonomous agent|multi[- ]agent", blob):
            arch = "agentic_workflow"
        elif is_general_llm_access or is_ms_copilot or (is_openai and "azure" in blob):
            arch = "inference_only"
        else:
            arch = "inference_only"
    else:
        if in_house or contracting:
            arch = "custom_trained"
        else:
            arch = "unknown"

    has_training = 0
    if arch in ("custom_trained", "fine_tuned"):
        has_training = 1
    if not is_gen and (in_house or contracting):
        has_training = 1

    # ---- use_type ----
    blob_use = blob
    if re.search(r"cyber|threat detect|intrusion|malware|phishing|security operations|soc\b", blob_use):
        use_type = "cybersecurity"
    elif re.search(r"\bhr\b|human resources|hiring|recruit|onboarding|travel|procurement|finance|accounting|budget|invoice|contract management|financial|expense|payroll|administrative|paperwork|memo", blob_use):
        use_type = "administrative"
    elif re.search(r"\bIT\b|service desk|help desk|tickets?|incident|software develop|system administ", blob_use):
        use_type = "it_operations"
    elif re.search(r"research|pilot study|experiment|investigat", blob_use) and agency in ("USDA",) and "research" in bureau.lower():
        use_type = "research"
    elif agency == "USDA" and bureau.startswith("ARS"):
        use_type = "research"
    elif agency == "DOI" and bureau == "USGS":
        use_type = "research"
    else:
        use_type = "mission_critical"

    # ---- public-facing ----
    is_public = 0
    if re.search(r"public[- ]facing|external user|citizens|public access|public users|public website", blob):
        is_public = 1
    if "doichatgpt api management development environment" in blob and "public facing" in blob:
        is_public = 1

    # ---- confidence ----
    if is_cots_commercial and tool_product_name:
        confidence = "high"
    elif is_gen and (is_openai or is_anthropic or is_ms_copilot):
        confidence = "high"
    elif soph in ("computer_vision", "nlp_specific", "predictive_analytics") and (in_house or contracting):
        confidence = "high"
    elif soph == "classical_ml" and not (in_house or contracting):
        confidence = "low"
    else:
        confidence = "medium"

    # ---- reasoning ----
    # Find a 2–6 word quoted phrase from the narrative that motivates the tag.
    txt = (purpose + " " + outputs).strip()
    # Prefer specific signals that drive the soph classification
    quote_candidates = []
    if is_gen:
        for p in [r"\b(large language model|llm|chatgpt|gpt[- ]?[345]|claude|gemini|copilot|chatbot|generative ai|firefly|openai|azure openai|bedrock|prompt engineer|rag|retrieval[- ]augmented|fine[- ]tun(e|ing)|foundation model|generative images?|summarization)\b"]:
            m = re.search(p, txt, re.IGNORECASE)
            if m:
                quote_candidates.append(m.group(0))
                break
    if soph == "computer_vision":
        for p in [r"\b(satellite imagery|aerial imag\w*|remote sensing|computer vision|image classif\w*|object detect\w*|image segment\w*|landsat|sentinel-?2|lidar|orthoimagery|deep learning|imagery|video analy\w*|camera trap|cnn|drone|naip|raster|ocr|optical character)\b"]:
            m = re.search(p, txt, re.IGNORECASE)
            if m:
                quote_candidates.append(m.group(0))
                break
    if soph == "nlp_specific":
        for p in [r"\b(topic model\w*|sentiment|natural language process\w*|nlp|text classif\w*|text extract\w*|text mining|named entity|public comment|document(s)? (process\w+|extract\w+|classif\w+|tag\w+|analy\w+)|automated indexing|thesaurus|controlled vocabulary|transcrib\w*|transcript|email classif\w*)\b"]:
            m = re.search(p, txt, re.IGNORECASE)
            if m:
                quote_candidates.append(m.group(0))
                break
    if soph == "predictive_analytics":
        for p in [r"\b(predict\w+|forecast\w*|risk score|early warning|anomaly|estimat\w+|simulat\w+|model develop\w*|recommend\w+|fraud detect\w+|time series|trend|likelihood|hazard|reinforcement learning)\b"]:
            m = re.search(p, txt, re.IGNORECASE)
            if m:
                quote_candidates.append(m.group(0))
                break
    if not quote_candidates:
        # generic fallback: any 'AI/ML' phrase
        for p in [r'"[^"]{4,40}"', r"\b(machine learning|artificial intelligence|deep learning|ai/ml|ai model|ai system|ai tool)\b"]:
            m = re.search(p, txt, re.IGNORECASE)
            if m:
                quote_candidates.append(m.group(0).strip('"'))
                break
    if not quote_candidates:
        # final fallback: opening phrase from name
        quote_candidates.append(short_quote(name, 5))

    quote = quote_candidates[0].strip().strip('"')
    quote = quote[:60]

    # Build per-row reasoning sentence
    if is_gen:
        if is_general_llm_access:
            tail = "indicates LLM/chatbot deployment."
        elif is_ms_copilot:
            tail = "indicates Microsoft Copilot use."
        elif is_openai or is_anthropic or is_google or is_aws_ai:
            tail = f"indicates commercial LLM ({tool_vendor or 'cloud'}) {('wrap' if in_house or contracting else 'use')}."
        else:
            tail = "indicates generative-AI use."
    else:
        if soph == "computer_vision":
            tail = "→ imagery/CV model."
        elif soph == "nlp_specific":
            tail = "→ text/NLP processing."
        elif soph == "predictive_analytics":
            tail = "→ predictive/forecasting model."
        else:
            tail = "→ classical ML model."

    # Add scope/development context where relevant
    extra = []
    if scope == "department":
        extra.append("department scope")
    elif scope == "pilot":
        extra.append("pilot/prototype")
    elif scope == "office":
        extra.append("office scope")
    if entry_type == "product_deployment" and tool_product_name:
        extra.append(f"{tool_product_name} deployment")
    elif entry_type == "bespoke_application":
        extra.append("in-house wrap on third-party model")
    elif in_house:
        extra.append("in-house build")
    elif contracting:
        extra.append("contracted build")

    extra_s = "; " + ", ".join(extra) if extra else ""
    reasoning = f'"{quote}" {tail}{extra_s}'

    if len(reasoning) > 240:
        reasoning = reasoning[:237] + "..."

    # Fill tags
    tags["entry_type"] = entry_type
    tags["is_generative_ai"] = str(is_gen)
    tags["ai_sophistication"] = soph
    tags["deployment_scope"] = scope
    tags["confidence"] = confidence
    tags["reasoning"] = reasoning
    tags["is_general_llm_access"] = str(is_general_llm_access) if is_general_llm_access else ""
    tags["is_coding_tool"] = str(is_coding_tool) if is_coding_tool else ""
    tags["is_cots_commercial"] = str(is_cots_commercial)
    tags["tool_product_name"] = tool_product_name
    tags["tool_vendor"] = tool_vendor
    tags["is_microsoft_copilot"] = str(is_ms_copilot) if is_ms_copilot else ""
    tags["is_openai"] = str(is_openai) if is_openai else ""
    tags["is_anthropic"] = str(is_anthropic) if is_anthropic else ""
    tags["is_google"] = str(is_google) if is_google else ""
    tags["is_github_copilot"] = str(is_github_copilot) if is_github_copilot else ""
    tags["is_aws_ai"] = str(is_aws_ai) if is_aws_ai else ""
    tags["is_enterprise_wide"] = str(is_enterprise_wide)
    tags["architecture_type"] = arch
    tags["has_model_training"] = str(has_training)
    tags["use_type"] = use_type
    tags["is_public_facing"] = str(is_public)
    tags["scope_detail"] = scope_detail

    return tags


def main():
    rows_in = []
    with open(INPUT, newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            rows_in.append(row)

    rows_out = []
    for row in rows_in:
        rows_out.append(tag_row(row))

    with open(OUTPUT, "w", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=OUT_COLS)
        wtr.writeheader()
        for r in rows_out:
            wtr.writerow(r)

    print(f"Wrote {len(rows_out)} rows to {OUTPUT}")
    print(f"Input rows: {len(rows_in)}")
    assert len(rows_in) == len(rows_out) == 406, "row count mismatch"


if __name__ == "__main__":
    main()
