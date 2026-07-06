"""Automated first-pass tagging of all use cases.

Performs mechanical tagging (product/template matching, keyword-based flags) that
sub-agents can then review and refine.
"""

import json
import re
from difflib import SequenceMatcher

from db import get_connection
from product_resolution import (
    consolidated_search_text,
    extract_products,
    load_product_aliases as load_shared_product_aliases,
    load_products as load_shared_products,
    use_case_search_text,
)

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


# Map of case-folded variant -> canonical (titlecased) value.
# Only contains values where multiple casings exist in the source data;
# we deliberately avoid widening this beyond verified case-only duplicates.
_TOPIC_AREA_CASE_CANONICAL = {
    "administrative functions": "Administrative Functions",
}


def normalize_topic_area(raw):
    """Normalize a `topic_area` value at ingest time.

    Rules (deliberately conservative — see
    `audit/cleanup_pass/topic_area_normalization_log.md`):
      * `None` / blank-after-trim -> `None`
      * Em-dash (U+2013) -> ASCII hyphen
      * Collapse runs of whitespace to a single space; trim outer whitespace
      * Case-only duplicates collapse to the titlecased canonical
        (e.g. "Administrative functions" -> "Administrative Functions")
      * Genuinely distinct values (e.g. "Cybersecurity" vs.
        "Cybersecurity Operations") are NOT merged.

    Idempotent: `f(f(x)) == f(x)` for all inputs.
    """
    if raw is None:
        return None
    s = str(raw)
    # Em-dash (and en-dash variant) -> hyphen, before whitespace collapse so
    # surrounding spacing normalizes uniformly.
    s = s.replace("–", "-").replace("—", "-")
    # Collapse internal whitespace runs (incl. NBSP) to a single ASCII space,
    # then trim outer whitespace.
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return None
    canonical = _TOPIC_AREA_CASE_CANONICAL.get(s.lower())
    if canonical is not None:
        return canonical
    return s


_TEMPLATE_WHITESPACE_RE = re.compile(r"\s+")
_TEMPLATE_TRAILING_PUNCT_RE = re.compile(r"[.,;:\s]+$")


def normalize_template_text(s):
    """Aggressive normalization for template matching.

    Agencies file Appendix B with minor cosmetic drift (stray newlines,
    dropped trailing periods, "AI powered" vs. "AI-powered"). This
    normalization strips all that so exact-string template matches survive.
    """
    if s is None:
        return ""
    out = _TEMPLATE_WHITESPACE_RE.sub(" ", str(s)).strip()
    out = out.replace("AI powered", "AI-powered")
    out = _TEMPLATE_TRAILING_PUNCT_RE.sub("", out)
    return out.lower()


def load_product_aliases(conn):
    """Build a dict of lowered alias -> product_id."""
    return load_shared_product_aliases(conn)


def load_templates(conn):
    """Build list of (template_id, normalized_text, capability_category).

    Uses `normalize_template_text` so cosmetic drift in agency filings
    (stray newlines, dropped periods, hyphenation) still yields an exact
    normalized-string match at tag time.
    """
    return [
        (r["id"], normalize_template_text(r["template_text"]), r["capability_category"])
        for r in conn.execute(
            "SELECT id, template_text, capability_category FROM use_case_templates"
        )
    ]


def load_products(conn):
    """Build dict of product_id -> {name, vendor, type, is_genai, is_frontier}."""
    return load_shared_products(conn)


def match_product(text, aliases_dict, products_dict):
    """Try to match a product from vendor/description text. Returns product_id or None.

    Agent D (plan §D): uses the same word-boundary-aware extractor that
    populates ``use_case_products`` so the single FK and the join table stay
    consistent. Returns the first (highest-confidence / longest-alias) match.
    The old substring-only matcher produced false positives like "Custom" ->
    Custom In-House AI hitting inside the word "Customs".
    """
    if not text:
        return None
    matches = extract_products(text, aliases_dict)
    if not matches:
        return None
    return matches[0]["product_name"]  # value is product_id from DB aliases


def match_template(text, templates):
    """Match against OMB templates. Returns template_id or None.

    Tries exact match on normalized text first (fast path, covers cosmetic
    drift like trailing punctuation), then falls back to SequenceMatcher at
    the 0.75 threshold for genuinely paraphrased filings.
    """
    if not text:
        return None
    norm = normalize_template_text(text)

    # Fast path: exact normalized match.
    for (tid, ttext, _cat) in templates:
        if norm == ttext:
            return tid

    # Fallback: fuzzy.
    best_id = None
    best_score = 0.0
    for (tid, ttext, _cat) in templates:
        score = SequenceMatcher(None, norm, ttext).ratio()
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


# Phrases that indicate an explicit agency-wide / department-wide deployment.
# These are the ONLY description signals that should promote a row to
# enterprise_wide (beyond the authoritative consolidated `agency_uses = 'Y'`).
ENTERPRISE_WIDE_PHRASES = [
    "agency-wide", "agency wide",
    "department-wide", "department wide",
    "enterprise-wide", "enterprise wide",
    "all employees", "all staff",
    "organization-wide", "organization wide",
    "government-wide",
]

# Phrases in training_data_description that constitute explicit RAG evidence.
# Plan §E.2: require product-type OR explicit phrase.
RAG_PHRASES = [
    "vector database", "vector db", "vector store",
    "embedding", "embeddings",
    "retrieval-augmented", "retrieval augmented",
]

# Phrases that constitute explicit agentic-workflow evidence.
AGENTIC_PHRASES = [
    "agentic workflow", "multi-step agent", "multi step agent",
    "tool use", "tool-use", "tool calling", "tool-calling",
    "autonomous agent",
]


def infer_architecture(row, products_dict=None, product_id=None):
    """Classify architecture type with evidence-gated RAG/agentic inference.

    Plan §E.2 — rag_pipeline / agentic_workflow now require EITHER:
      * A matched product whose ``product_type`` is ``rag_platform`` /
        ``agent_platform``, OR
      * An explicit phrase in ``training_data_description`` (vector db,
        embedding, retrieval-augmented for RAG; agentic/tool-use phrasing
        for agentic).

    Name-only keyword matches are dropped — they produced 443 false positives
    (279 rag_pipeline + 164 agentic_workflow) on this dataset.

    Returns ``(architecture_type, has_model_training)``.
    """
    train_desc = normalize(row.get("training_data_description", ""))
    problem = normalize(
        (row.get("problem_statement", "") or "")
        + " "
        + (row.get("use_case_name", "") or "")
    )
    dev = normalize(row.get("development_type", ""))

    # Fine-tuning remains explicit by nature — TRAINING_KEYWORDS are strong
    # phrases ("fine-tune", "trained on our", etc.) in training_data_description.
    if keyword_any(train_desc, TRAINING_KEYWORDS):
        return "fine_tuned", 1

    # Product-type evidence for RAG / agent platforms.
    product_type = ""
    if product_id and products_dict:
        product_type = (products_dict.get(product_id, {}) or {}).get(
            "product_type", ""
        ) or ""
        product_type = product_type.lower()

    if product_type == "rag_platform":
        return "rag_pipeline", 0
    if product_type == "agent_platform":
        return "agentic_workflow", 0

    # Explicit phrase evidence in training_data_description.
    if any(phrase in train_desc for phrase in RAG_PHRASES):
        return "rag_pipeline", 0
    if any(phrase in train_desc for phrase in AGENTIC_PHRASES) or any(
        phrase in problem for phrase in AGENTIC_PHRASES
    ):
        return "agentic_workflow", 0

    # Custom-trained: in-house development with substantive training desc.
    if "in-house" in dev and train_desc and len(train_desc) > 50:
        return "custom_trained", 1

    # Fallback: if a product matched, call it inference_only; else unknown
    # (preserves uncertainty — plan §E Section 5 intent).
    if product_id:
        return "inference_only", 0
    return "unknown", 0


def infer_scope(row, is_consolidated=False, bureau=None, agency_abbr=None):
    """Classify deployment scope with evidence-gated enterprise_wide inference.

    Plan §E.1 — for consolidated rows, default to ``'unknown'``. Only promote
    to ``enterprise_wide`` when:
      * ``agency_uses == 'Y'`` (the authoritative consolidated source flag), OR
      * Description / name contains an explicit agency-wide phrase.

    The ``estimated_licenses_users`` substring block is DROPPED entirely —
    that field is self-reported free text and cannot support the plan's
    "strong user-count evidence" criterion.

    For non-consolidated rows, require explicit bureau/agency wording; if no
    bureau info is available, return ``'unknown'`` (never default to
    ``enterprise_wide``).

    Returns a tuple ``(scope, scope_detail)`` when ``bureau`` or
    ``agency_abbr`` are supplied (production call sites in ``tag_use_case``).
    When called with only ``is_consolidated`` (unit tests per plan §E.4),
    returns just the scope string.
    """
    # Description text for phrase scanning — consolidated rows use
    # ``ai_use_case``; canonical rows use ``problem_statement``; tests use
    # ``description``. Scan all of them.
    description = normalize(
        (row.get("description", "") or "")
        + " "
        + (row.get("ai_use_case", "") or "")
        + " "
        + (row.get("problem_statement", "") or "")
        + " "
        + (row.get("use_case_name", "") or "")
    )

    if is_consolidated:
        agency_uses = (row.get("agency_uses") or "").strip().upper()
        if agency_uses == "Y":
            scope, detail = "enterprise_wide", None
        elif any(phrase in description for phrase in ENTERPRISE_WIDE_PHRASES):
            scope, detail = "enterprise_wide", None
        else:
            scope, detail = "unknown", None
        if bureau is None and agency_abbr is None:
            return scope
        return scope, detail

    # Non-consolidated rows: require explicit evidence to promote.
    b = normalize(bureau)
    a = normalize(agency_abbr)

    if any(phrase in description for phrase in ENTERPRISE_WIDE_PHRASES):
        scope, detail = "enterprise_wide", None
    elif not b:
        scope, detail = "unknown", None
    elif a and (a in b or b == a):
        scope, detail = "enterprise_wide", None
    elif "enterprise" in b or "agency-wide" in b or "department-wide" in b:
        scope, detail = "enterprise_wide", None
    else:
        known_bureaus = [
            "cdc", "cms", "fda", "nih", "cbp", "ice", "tsa", "fema",
            "uscis", "fbi", "dea", "atf", "irs", "fsa", "bop",
        ]
        if any(kb in b for kb in known_bureaus):
            scope, detail = "bureau", bureau
        elif "office" in b or "division" in b:
            scope, detail = "office", bureau
        else:
            scope, detail = "bureau", bureau

    if bureau is None and agency_abbr is None:
        return scope
    return scope, detail


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
        "hi_testing_conducted", "hi_assessment_completed", "hi_potential_impacts",
        "hi_independent_review", "hi_ongoing_monitoring", "hi_training_established",
        "hi_failsafe_presence", "hi_appeal_process", "hi_public_consultation"
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
        search_text = consolidated_search_text(row)
        name_prob = (row.get("ai_use_case", "") or "")
    else:
        search_text = use_case_search_text(row)
        name_prob = (row.get("use_case_name", "") or "") + " " + (row.get("problem_statement", "") or "")

    product_id = match_product(search_text, aliases_dict, products_dict)
    template_id = match_template(name_prob, templates)

    entry_type = infer_entry_type(row, product_id, template_id, is_consolidated, products_dict)

    prod = products_dict.get(product_id, {}) if product_id else {}
    ai_soph = infer_ai_sophistication(row, product_id, products_dict)
    arch, has_train = infer_architecture(row, products_dict, product_id)

    if is_consolidated:
        scope, scope_detail = infer_scope(
            row, is_consolidated=True, bureau="", agency_abbr=agency_abbr
        )
    else:
        scope, scope_detail = infer_scope(
            row,
            is_consolidated=False,
            bureau=row.get("bureau_component", ""),
            agency_abbr=agency_abbr,
        )

    # is_general_llm_access is computed by the dedicated inference function so
    # the precedence rules (source ai_classification as strong signal, product
    # fallback for blank classification, extraction/routing blacklist) stay
    # testable in isolation. See Agent B plan §B.2.
    #
    # IMPORTANT: Agent B deliberately narrowed is_general_llm_access so that
    # "coding assistant" and "agentic" ai_sophistication tiers do NOT auto-
    # promote a row to is_llm=1 for non-consolidated rows. That broader rule
    # reintroduces ~70 canonical false positives (Classical / Predictive /
    # Computer Vision rows getting flagged as LLM). The source of truth for
    # this flag is `infer_llm_flag()`; `scripts/retag_llm.py` applies the same
    # function to every row. Do NOT add a fallback here that bumps
    # coding_assistant/agentic to is_llm=1 without also updating
    # infer_llm_flag, retag_llm.py, and the tests in tests/test_llm_tagging.py.
    #
    # Consolidated rows piggy-back on ai_sophistication since they lack an
    # ai_classification column; the broader tiers are acceptable there because
    # consolidated rows are already agency roll-ups, not per-system data.
    if is_consolidated:
        is_llm = 1 if ai_soph in ("general_llm", "coding_assistant", "agentic") else 0
    else:
        is_llm = infer_llm_flag(row, product_id, products_dict)
    is_coding = 1 if ai_soph == "coding_assistant" or keyword_any(search_text, CODING_KEYWORDS) else 0
    # LLM_KEYWORDS only — AGENTIC_KEYWORDS ("agent", "autonomous", "workflow")
    # over-fire on classical autonomy and RPA (2026-07 genai review: the
    # pre-2023 GenAI tail was almost entirely these false positives). Agentic
    # sophistication detection still uses AGENTIC_KEYWORDS above; reviewed
    # rows are overlaid by scripts/apply_genai_review.py either way.
    is_genai = 1 if prod.get("is_generative_ai") or keyword_any(search_text, LLM_KEYWORDS) else 0
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
        # Clear existing tags + the Agent D join table so this run is a clean
        # rebuild (idempotent).
        conn.execute("DELETE FROM use_case_tags")
        conn.execute("DELETE FROM use_case_products")
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
            # Agent D (plan §D.4): populate use_case_products with ALL matches
            # evidenced by the combined vendor/system/name/problem text. The
            # single-FK use_cases.product_id still gets the first (highest-
            # confidence) match for back-compat with existing dashboard code.
            ucp_text = use_case_search_text(row_dict)
            for m in extract_products(ucp_text, aliases_dict):
                pid = m["product_name"]  # product_id (values from DB aliases)
                evidence = m.get("evidence") or m.get("alias") or ""
                confidence = "strong" if len(evidence) >= 5 else "inferred"
                conn.execute(
                    """
                    INSERT OR IGNORE INTO use_case_products
                        (use_case_id, product_id, evidence_text, confidence)
                    VALUES (?, ?, ?, ?)
                    """,
                    (r["id"], pid, evidence, confidence),
                )
            # (The scalar use_cases.product_id/template_id cache columns were
            # dropped by m025 — the edge insert above is the only linkage;
            # primary product resolves via the entry_primary_products view.)
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
            # template_id is a live consolidated-only column (m025 kept it);
            # the scalar product_id cache was dropped.
            conn.execute(
                "UPDATE consolidated_use_cases SET template_id = ? WHERE id = ?",
                (tags["template_id"], r["id"]),
            )
            consolidated_count += 1

        conn.commit()
        print(f"Auto-tagged {individual_count} individual + {consolidated_count} consolidated = {individual_count + consolidated_count} use cases")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
