"""Automated first-pass tagging of all use cases.

Performs mechanical tagging (product/template matching, keyword-based flags) that
sub-agents can then review and refine.
"""

import json
import re
from difflib import SequenceMatcher

from db import get_connection

# Keywords for various categorizations
#
# LLM_KEYWORDS is the broad match set used elsewhere in the module for
# `is_generative_ai` heuristics. The LLM-inference function uses a *narrowed*
# set below so that generic words like "assistant" don't flip non-LLM rows
# (e.g. a classical-ML "scheduling assistant") into the LLM bucket.
LLM_KEYWORDS = [
    "copilot", "chatgpt", "claude", "gemini", "gpt-4", "gpt4", "llm",
    "large language model", "chatbot", "generative ai", "genai",
    "conversational ai", "assistant", "bard", "anthropic", "openai",
    "azure openai", "bedrock", "amazon q"
]

# Narrowed keyword set used ONLY by infer_llm_flag's blank-classification
# fallback. These are strong positive signals for generative LLM access.
# Deliberately excludes "assistant" (too generic), "bedrock" (Textract is on
# Bedrock too), "azure openai" (handled via product table).
LLM_FALLBACK_KEYWORDS = [
    "copilot", "chatgpt", "claude", "gemini", "gpt-4", "gpt4", "gpt-3",
    "gpt-5", "llm", "large language model", "chatbot", "generative ai",
    "genai", "bard", "anthropic", "openai", "amazon q", "draft ",
    "summarize", "summarization",
]

# Name/problem keywords that indicate a *non-LLM* task (extraction / routing /
# classical NLP / forecasting / transcription). When ai_classification is
# blank we treat these as strong negative signals.
EXTRACTION_ROUTING_BLACKLIST = [
    "extraction", "extract ", "routing", "sentiment",
    "topic model", "topic modeling", "anomaly detection",
    "forecasting", "forecast ", "transcription", "transcribe",
    "classification of", "classifier ", "ocr", "image recognition",
    "object detection", "face recognition", "speech recognition",
]

# Regex patterns against ai_classification source field.
_CLASSICAL_RE = re.compile(
    r"classical|predictive|computer vision|traditional ml|statistical",
    re.IGNORECASE,
)
_GENERATIVE_RE = re.compile(
    r"generative|large language|^\s*llm\b|\bllm\s",
    re.IGNORECASE,
)
# Named-LLM override: if source classification says "classical" but the row
# literally names a frontier LLM, treat as LLM.
_NAMED_LLM_RE = re.compile(
    r"chatgpt|copilot|\bllm\b|gpt-\d|gemini|\bclaude\b|anthropic|openai|"
    r"amazon q\b|azure openai|microsoft 365 copilot",
    re.IGNORECASE,
)

CODING_KEYWORDS = [
    "github copilot", "codewhisperer", "claude code", "coding assist",
    "code generation", "code completion", "code review", "ai coding",
    "programming assist", "developer tools", "code suggest",
]

AGENTIC_KEYWORDS = [
    "agent", "agentic", "autonomous", "multi-step", "workflow",
    "ai agent", "automated workflow",
]

RAG_KEYWORDS = [
    "retrieval", "rag ", "retrieval-augmented", "knowledge base",
    "document search", "knowledge retrieval", "vector", "embedding",
    "semantic search",
]

TRAINING_KEYWORDS = [
    "fine-tune", "fine tuned", "finetune", "trained on our", "trained on agency",
    "custom-trained", "custom trained", "training data set", "model training",
]

MISSION_KEYWORDS = [
    "mission", "public", "constituent", "citizen", "customer", "benefit processing",
    "application", "adjudication", "fraud", "enforcement",
]

ADMIN_KEYWORDS = [
    "administrative", "drafting", "email", "calendar", "scheduling",
    "travel", "expense", "hr", "human resources",
]

IT_OPS_KEYWORDS = [
    "it operations", "help desk", "ticket", "service desk", "monitoring",
    "alerting", "infrastructure",
]

CYBER_KEYWORDS = [
    "cyber", "security", "threat", "malware", "anomaly detection",
    "intrusion", "phishing", "edr", "siem",
]

FRONTIER_LLMS = {
    "ChatGPT", "Claude", "Gemini", "Microsoft 365 Copilot", "Azure OpenAI",
    "Amazon Q", "AWS Bedrock", "OpenAI API",
}


def normalize(s):
    if s is None:
        return ""
    return str(s).lower().strip()


def load_product_aliases(conn):
    """Build a dict of lowered alias -> product_id."""
    d = {}
    for row in conn.execute("SELECT alias_text, product_id FROM product_aliases"):
        d[normalize(row["alias_text"])] = row["product_id"]
    return d


def load_templates(conn):
    """Build list of (template_id, lowered_text, capability_category)."""
    return [(r["id"], normalize(r["template_text"]), r["capability_category"])
            for r in conn.execute("SELECT id, template_text, capability_category FROM use_case_templates")]


def load_products(conn):
    """Build dict of product_id -> {name, vendor, type, is_genai, is_frontier}."""
    d = {}
    for r in conn.execute("SELECT id, canonical_name, vendor, product_type, is_generative_ai, is_frontier_llm FROM products"):
        d[r["id"]] = dict(r)
    return d


def match_product(text, aliases_dict, products_dict):
    """Try to match a product from vendor/description text. Returns product_id or None."""
    if not text:
        return None
    text_lower = normalize(text)
    # Try longest aliases first for better matching
    sorted_aliases = sorted(aliases_dict.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        if alias and alias in text_lower:
            return aliases_dict[alias]
    return None


def match_template(text, templates):
    """Fuzzy match against OMB templates. Returns template_id or None."""
    if not text:
        return None
    text_lower = normalize(text)
    best_id = None
    best_score = 0.0
    for (tid, ttext, _cat) in templates:
        score = SequenceMatcher(None, text_lower, ttext).ratio()
        if score > best_score:
            best_score = score
            best_id = tid
    return best_id if best_score >= 0.75 else None


def keyword_any(text, keywords):
    if not text:
        return 0
    t = normalize(text)
    return 1 if any(kw in t for kw in keywords) else 0


def infer_entry_type(row, product_id, template_id, is_consolidated, products_dict):
    """Determine what this entry represents.

    Precedence (Phase 2 Agent C — plan §C.2):
      1. Consolidated rows -> generic_use_pattern.
      2. Template match with no tool-ish noun in the name -> generic_use_pattern.
      3. development_type starts with "a)" (purchased) OR vendor populated
         with blank development_type -> product_deployment
         (product_feature if the matched product has a parent).
      4. development_type contains "in-house" AND vendor blank -> custom_system.
      5. Any mix of in-house + (vendor OR product) -> bespoke_application.
      6. Default: product_deployment if vendor populated, else custom_system.
    """
    if is_consolidated:
        # Consolidated format is inherently about generic use patterns
        return "generic_use_pattern"

    name = normalize(row.get("use_case_name", ""))
    development = normalize(row.get("development_type", ""))
    vendor = normalize(row.get("vendor_name", ""))

    def _product_deployment_label():
        if product_id:
            prod = products_dict.get(product_id, {}) if products_dict else {}
            if prod.get("parent_product_id") is not None:
                return "product_feature"
        return "product_deployment"

    # 2. Template match without a tool-ish noun in the name -> generic pattern
    if template_id and not any(
        c in name for c in ["tool", "system", "assistant", "platform"]
    ):
        return "generic_use_pattern"

    purchased = development.startswith("a)") or "purchased from a vendor" in development
    in_house = "in-house" in development or development.startswith("b)")
    both = "both" in development or development.startswith("c)")

    # 3. Purchased from a vendor OR vendor populated with blank development_type
    if purchased or (vendor and not development):
        return _product_deployment_label()

    # 4. Strictly in-house with no vendor -> custom_system
    if in_house and not both and not vendor:
        return "custom_system"

    # 5. Any mix of in-house + vendor/product -> bespoke_application
    if (in_house or both) and (vendor or product_id):
        return "bespoke_application"

    # 5b. Product matched but no explicit development signal -> product_deployment
    if product_id and not in_house and not both:
        return _product_deployment_label()

    # 6. Safe default: product_deployment if vendor populated, else custom_system
    if vendor:
        return _product_deployment_label()
    return "custom_system"


def _g(row, key, default=""):
    """Safely get a value from row dict, coercing None to default."""
    v = row.get(key)
    return v if v else default


def infer_llm_flag(row, product_id, products_dict):
    """Decide whether this row should be tagged ``is_general_llm_access=1``.

    Pure function — takes only the row dict plus the products context so the
    test suite can exercise it without a DB.

    Precedence (see Agent B plan §B.2):
      1. ai_classification regex-matches classical/predictive/CV/traditional ML
         -> 0, UNLESS the row is clearly a named-LLM product deployment
         (vendor product_type='general_llm', or name/problem names a frontier
         model). The override keeps a mis-classified source row from being
         dropped.
      2. ai_classification regex-matches generative/large language/llm -> 1.
      3. ai_classification blank/unknown -> fallback in order:
         3a. product_id resolves to products.product_type='general_llm' -> 1.
         3b. Name+problem text hits EXTRACTION_ROUTING_BLACKLIST -> 0.
         3c. Name+problem text hits LLM_FALLBACK_KEYWORDS -> 1.
         3d. Otherwise -> 0.
    """
    ai_class = normalize(_g(row, "ai_classification"))
    name_prob = normalize(
        _g(row, "use_case_name") + " " + _g(row, "problem_statement")
    )
    vendor = normalize(_g(row, "vendor_name"))

    prod = products_dict.get(product_id, {}) if product_id else {}
    product_is_general_llm = prod.get("product_type") == "general_llm"

    # Rule 1: strong non-LLM source signal.
    if ai_class and _CLASSICAL_RE.search(ai_class):
        # Override: named LLM product wins over a misclassified source field.
        if product_is_general_llm:
            return 1
        if _NAMED_LLM_RE.search(name_prob) or _NAMED_LLM_RE.search(vendor):
            return 1
        return 0

    # Rule 2: strong LLM source signal.
    if ai_class and _GENERATIVE_RE.search(ai_class):
        return 1

    # Rule 3: fallback when source classification is blank/unknown.
    # 3a: product is a general_llm.
    if product_is_general_llm:
        return 1
    # 3b: extraction / routing / classical-NLP negative signal.
    if any(kw in name_prob for kw in EXTRACTION_ROUTING_BLACKLIST):
        return 0
    # 3c: narrowed LLM keyword list.
    haystack = name_prob + " " + vendor
    if any(kw in haystack for kw in LLM_FALLBACK_KEYWORDS):
        return 1
    # 3d: default negative.
    return 0


def infer_ai_sophistication(row, product_id, products_dict):
    """Classify sophistication level."""
    ai_class = normalize(_g(row, "ai_classification"))
    name_prob = normalize(_g(row, "use_case_name") + " " + _g(row, "problem_statement"))

    if product_id:
        prod = products_dict.get(product_id, {})
        ptype = prod.get("product_type", "")
        if ptype == "coding_assistant":
            return "coding_assistant"
        if ptype == "general_llm":
            return "general_llm"

    if "agentic" in ai_class or keyword_any(name_prob, AGENTIC_KEYWORDS):
        return "agentic"
    if "generative" in ai_class or keyword_any(name_prob, LLM_KEYWORDS):
        return "general_llm"
    if "computer vision" in ai_class or "image" in name_prob:
        return "computer_vision"
    if "natural language processing" in ai_class or "nlp" in ai_class:
        return "nlp_specific"
    if "classical" in ai_class or "predictive" in ai_class or "machine learning" in ai_class:
        return "classical_ml"
    return "classical_ml"  # default


def infer_architecture(row, product_id, products_dict):
    """Classify architecture type."""
    train_desc = normalize(row.get("training_data_description", ""))
    custom_code = normalize(row.get("has_custom_code", ""))
    problem = normalize(row.get("problem_statement", "") + " " + row.get("use_case_name", ""))
    dev = normalize(row.get("development_type", ""))

    if keyword_any(train_desc + " " + problem, TRAINING_KEYWORDS):
        return "fine_tuned", 1
    if keyword_any(problem + " " + train_desc, RAG_KEYWORDS):
        return "rag_pipeline", 0
    if keyword_any(problem, AGENTIC_KEYWORDS):
        return "agentic_workflow", 0
    if "in-house" in dev and train_desc and len(train_desc) > 50:
        return "custom_trained", 1
    if product_id:
        return "inference_only", 0
    return "unknown", 0


def infer_scope(row, bureau, agency_abbr, licenses_users=None):
    """Classify deployment scope."""
    b = normalize(bureau)
    # For consolidated entries, rely on license count
    if licenses_users:
        lc = normalize(licenses_users)
        if "10000" in lc or "100000" in lc or "1001-" in lc or "5001-" in lc:
            return "enterprise_wide", None
        if "1-100" in lc or "101-1000" in lc:
            return "bureau", None

    if not b:
        return "unknown", None

    # If bureau matches agency name, it's enterprise-wide
    if normalize(agency_abbr) in b or b == normalize(agency_abbr).lower():
        return "enterprise_wide", None

    if "enterprise" in b or "agency-wide" in b or "department-wide" in b:
        return "enterprise_wide", None

    # Known large bureaus like CDC within HHS
    known_bureaus = ["cdc", "cms", "fda", "nih", "cbp", "ice", "tsa", "fema",
                     "uscis", "fbi", "dea", "atf", "irs", "fsa", "bop"]
    if any(kb in b for kb in known_bureaus):
        return "bureau", bureau

    # If has "office" in name, likely an office scope
    if "office" in b or "division" in b:
        return "office", bureau

    return "bureau", bureau


def infer_use_type(row):
    """Classify mission type."""
    name_prob = normalize(row.get("use_case_name", "") + " " + row.get("problem_statement", ""))
    topic = normalize(row.get("topic_area", ""))

    if keyword_any(topic, ["cyber", "security"]) or keyword_any(name_prob, CYBER_KEYWORDS):
        return "cybersecurity"
    if keyword_any(topic, ["it", "information technology"]) or keyword_any(name_prob, IT_OPS_KEYWORDS):
        return "it_operations"
    if keyword_any(topic, ["administrative"]) or keyword_any(name_prob, ADMIN_KEYWORDS):
        return "administrative"
    if keyword_any(topic, ["research"]) or "research" in name_prob:
        return "research"
    if keyword_any(name_prob, MISSION_KEYWORDS) or keyword_any(topic, ["service delivery", "benefits"]):
        return "mission_critical"
    return "administrative"


def has_risk_docs(row):
    """Check if Section 5 is meaningfully filled."""
    fields = [
        "pre_deployment_testing", "impact_assessment", "potential_impacts",
        "independent_review", "ongoing_monitoring", "operator_training",
        "has_fail_safe", "appeal_process", "end_user_feedback"
    ]
    filled = 0
    for f in fields:
        v = normalize(row.get(f, ""))
        if v and v not in ("", "n/a", "na", "none", "not applicable", "-"):
            filled += 1
    return 1 if filled >= 3 else 0


def vendor_flags(product_id, products_dict):
    """Return dict of vendor boolean flags."""
    if not product_id:
        return {k: 0 for k in ["is_microsoft_copilot", "is_openai", "is_anthropic",
                               "is_google", "is_github_copilot", "is_aws_ai"]}
    prod = products_dict.get(product_id, {})
    name = prod.get("canonical_name", "")
    vendor = prod.get("vendor", "")
    return {
        "is_microsoft_copilot": 1 if "copilot" in name.lower() and "microsoft" == vendor.lower() else 0,
        "is_openai": 1 if vendor == "OpenAI" else 0,
        "is_anthropic": 1 if vendor == "Anthropic" else 0,
        "is_google": 1 if vendor == "Google" else 0,
        "is_github_copilot": 1 if name == "GitHub Copilot" else 0,
        "is_aws_ai": 1 if vendor == "Amazon" else 0,
    }


def tag_use_case(row, agency_abbr, aliases_dict, templates, products_dict, is_consolidated=False):
    """Generate all tags for a single row. Returns dict of tag values."""
    if is_consolidated:
        search_text = " ".join([
            row.get("ai_use_case", "") or "",
            row.get("commercial_product", "") or "",
            row.get("commercial_examples", "") or "",
        ])
        name_prob = (row.get("ai_use_case", "") or "")
    else:
        search_text = " ".join([
            row.get("use_case_name", "") or "",
            row.get("vendor_name", "") or "",
            row.get("system_name", "") or "",
            row.get("problem_statement", "") or "",
        ])
        name_prob = (row.get("use_case_name", "") or "") + " " + (row.get("problem_statement", "") or "")

    product_id = match_product(search_text, aliases_dict, products_dict)
    template_id = match_template(name_prob, templates)

    entry_type = infer_entry_type(row, product_id, template_id, is_consolidated, products_dict)

    prod = products_dict.get(product_id, {}) if product_id else {}
    ai_soph = infer_ai_sophistication(row, product_id, products_dict)
    arch, has_train = infer_architecture(row, product_id, products_dict)

    if is_consolidated:
        scope, scope_detail = infer_scope(
            row, "", agency_abbr, licenses_users=row.get("estimated_licenses_users")
        )
    else:
        scope, scope_detail = infer_scope(row, row.get("bureau_component", ""), agency_abbr)

    # is_general_llm_access is computed by the dedicated inference function so
    # the precedence rules (source ai_classification as strong signal, product
    # fallback for blank classification, extraction/routing blacklist) stay
    # testable in isolation. See Agent B plan §B.2. Consolidated rows piggy-
    # back on ai_sophistication since they lack an ai_classification column.
    if is_consolidated:
        is_llm = 1 if ai_soph in ("general_llm", "coding_assistant", "agentic") else 0
    else:
        is_llm = infer_llm_flag(row, product_id, products_dict)
        # Coding assistants and agentic are still LLM-tier tools.
        if not is_llm and ai_soph in ("coding_assistant", "agentic"):
            is_llm = 1
    is_coding = 1 if ai_soph == "coding_assistant" or keyword_any(search_text, CODING_KEYWORDS) else 0
    is_genai = 1 if prod.get("is_generative_ai") or keyword_any(search_text, LLM_KEYWORDS + AGENTIC_KEYWORDS) else 0
    is_frontier = 1 if prod.get("canonical_name") in FRONTIER_LLMS else 0

    # Development type
    if is_consolidated:
        is_cots = 1  # Consolidated format is by definition COTS
    else:
        dev = normalize(row.get("development_type", ""))
        is_cots = 1 if "vendor" in dev else (0 if "in-house" in dev and "both" not in dev else 1 if product_id else 0)

    # High impact
    if is_consolidated:
        high_impact = None
    else:
        hi = normalize(row.get("is_high_impact", ""))
        if "a)" in hi or hi == "high-impact" or "high-impact" in hi and "not" not in hi:
            high_impact = "high_impact"
        elif "not high-impact" in hi or "c)" in hi:
            high_impact = "not_high_impact"
        elif "presumed" in hi or "b)" in hi:
            high_impact = "presumed_not_high_impact"
        else:
            high_impact = None

    # Enterprise wide
    is_enterprise = 1 if scope == "enterprise_wide" else 0

    # ATO check
    has_ato_text = normalize(row.get("has_ato", ""))
    has_ato_flag = 1 if "yes" in has_ato_text else 0

    # Product capability (if generic_use_pattern, use template category)
    product_capability = None
    if entry_type == "generic_use_pattern" and template_id:
        tmpl_cat = next((cat for (tid, _, cat) in templates if tid == template_id), None)
        product_capability = tmpl_cat

    is_capability_entry = 1 if entry_type == "generic_use_pattern" else 0

    vflags = vendor_flags(product_id, products_dict)

    tags = {
        "entry_type": entry_type,
        "is_product_capability_entry": is_capability_entry,
        "product_capability": product_capability,
        "product_id": product_id,
        "template_id": template_id,
        "is_general_llm_access": is_llm,
        "is_coding_tool": is_coding,
        "is_cots_commercial": is_cots,
        "tool_product_name": prod.get("canonical_name"),
        "tool_vendor": prod.get("vendor"),
        "ai_sophistication": ai_soph,
        "is_generative_ai": is_genai,
        "is_frontier_model": is_frontier,
        "deployment_scope": scope,
        "scope_detail": scope_detail,
        "is_enterprise_wide": is_enterprise,
        "estimated_user_count": row.get("estimated_licenses_users") if is_consolidated else None,
        "architecture_type": arch,
        "has_model_training": has_train,
        "cots_product_name": prod.get("canonical_name"),
        "cots_vendor": prod.get("vendor"),
        "use_type": infer_use_type(row) if not is_consolidated else "administrative",
        "is_public_facing": 0,  # conservative default
        "has_meaningful_risk_docs": has_risk_docs(row) if not is_consolidated else 0,
        "high_impact_designation": high_impact,
        "deployment_environment": "unknown",
        "has_ato_or_fedramp": has_ato_flag,
        **vflags,
    }
    return tags


def run():
    conn = get_connection()
    try:
        # Clear existing tags
        conn.execute("DELETE FROM use_case_tags")
        conn.commit()

        aliases_dict = load_product_aliases(conn)
        templates = load_templates(conn)
        products_dict = load_products(conn)

        # Tag individual use cases
        rows = conn.execute("""
            SELECT uc.*, a.abbreviation as agency_abbr
            FROM use_cases uc JOIN agencies a ON a.id = uc.agency_id
        """).fetchall()

        individual_count = 0
        # Keys that live on use_cases table, not use_case_tags
        TAG_EXCLUDE = {"product_id", "template_id"}

        for r in rows:
            row_dict = {k: (v if v is not None else "") for k, v in dict(r).items()}
            tags = tag_use_case(row_dict, row_dict["agency_abbr"], aliases_dict, templates, products_dict, is_consolidated=False)
            tag_fields = {k: v for k, v in tags.items() if k not in TAG_EXCLUDE}
            cols = ["use_case_id"] + list(tag_fields.keys())
            placeholders = ",".join(["?"] * len(cols))
            values = [r["id"]] + list(tag_fields.values())
            conn.execute(
                f"INSERT INTO use_case_tags ({','.join(cols)}) VALUES ({placeholders})",
                values,
            )
            # Update source table with product_id and template_id
            conn.execute(
                "UPDATE use_cases SET product_id = ?, template_id = ? WHERE id = ?",
                (tags["product_id"], tags["template_id"], r["id"]),
            )
            individual_count += 1

        # Tag consolidated use cases
        cons_rows = conn.execute("""
            SELECT c.*, a.abbreviation as agency_abbr
            FROM consolidated_use_cases c JOIN agencies a ON a.id = c.agency_id
        """).fetchall()

        consolidated_count = 0
        for r in cons_rows:
            row_dict = {k: (v if v is not None else "") for k, v in dict(r).items()}
            tags = tag_use_case(row_dict, row_dict["agency_abbr"], aliases_dict, templates, products_dict, is_consolidated=True)
            tag_fields = {k: v for k, v in tags.items() if k not in TAG_EXCLUDE}
            cols = ["consolidated_use_case_id"] + list(tag_fields.keys())
            placeholders = ",".join(["?"] * len(cols))
            values = [r["id"]] + list(tag_fields.values())
            conn.execute(
                f"INSERT INTO use_case_tags ({','.join(cols)}) VALUES ({placeholders})",
                values,
            )
            conn.execute(
                "UPDATE consolidated_use_cases SET product_id = ?, template_id = ? WHERE id = ?",
                (tags["product_id"], tags["template_id"], r["id"]),
            )
            consolidated_count += 1

        conn.commit()
        print(f"Auto-tagged {individual_count} individual + {consolidated_count} consolidated = {individual_count + consolidated_count} use cases")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
