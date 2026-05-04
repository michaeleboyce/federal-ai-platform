"""Column mapping definitions and fuzzy matcher to canonical M-25-21 schema."""

from difflib import SequenceMatcher

# Canonical 34 columns from OMB M-25-21 (from Treasury's full-compliance version)
# Maps canonical name -> DB column name
CANONICAL_TO_DB = {
    # Section 1
    "Use Case ID": "use_case_id",
    "Use Case Name": "use_case_name",
    "Bureau/Component": "bureau_component",
    "Email Address": "email_address",
    "Should this AI use case be withheld from public reporting?": "is_withheld",
    "Stage of Development": "stage_of_development",
    "Is the AI use case high-impact?": "is_high_impact",
    "Justification": "justification",
    "Use Case Topic Area": "topic_area",
    # Section 2
    "AI Classification": "ai_classification",
    "What problem is the AI intended to solve?": "problem_statement",
    "What are the expected benefits and positive outcomes from the AI for an agency's mission and/or the general public?": "expected_benefits",
    "Describe the AI system's outputs.": "system_outputs",
    "Date when AI use case became operational or the pilot's start date": "operational_date",
    # Section 3
    "Was the system involved in this use case purchased from a vendor or developed under contract(s) or in-house?": "development_type",
    "Vendor(s) Name": "vendor_name",
    "Does this AI use case have an associated Authorization to Operate (ATO)?": "has_ato",
    "System(s) Name": "system_name",
    "Describe any data used to train, fine-tune, and/or evaluate performance of the model(s) used in this use case.": "training_data_description",
    # Section 4
    "If the data is required to be publicly disclosed as an open government data asset, provide a link to the entry on the Federal Data Catalog.": "link_to_data",
    "Does this AI use case involve personally identifiable information (PII) that is maintained by the agency?": "has_pii",
    "If publicly available, provide the link to the AI use case's associated Privacy Impact Assessment (PIA), if any.": "pia_url",
    "Which, if any, demographic variables does the AI use case explicitly use as model features?": "demographic_features",
    "Does this project include custom-developed code?": "has_custom_code",
    "If the code is open source, provide the link for the publicly available source code.": "code_url",
    # Section 5
    "Has pre-deployment testing been conducted for this AI use case?": "hi_testing_conducted",
    "Has an AI impact assessment been completed for this AI use case?": "hi_assessment_completed",
    "What are the potential impacts of using the AI for this particular use case and how were they identified?": "hi_potential_impacts",
    "Has as independent review of the AI use case been conducted?": "hi_independent_review",
    "Is there a process to conduct ongoing monitoring to identify any adverse impacts to the performance and security of the AI functionality, as well as to privacy, civil rights, and civil liberties?": "hi_ongoing_monitoring",
    "Has the agency established sufficient and periodic training for operators of the AI to interpret and act on the its output and managed associated risks?": "hi_training_established",
    "Does this AI use case have an appropriate fail-safe that minimizes the risk of significant harm?": "hi_failsafe_presence",
    "Is there an established appeal process in the event that an impacted individual would like to appeal or contest the AI system's outcome?": "hi_appeal_process",
    "What steps has the agency taken to consult and incorporate feedback from end users of this AI use case and the public?": "hi_public_consultation",
}

# Explicit renames for agencies with abbreviated column names
EXPLICIT_OVERRIDES = {
    # DOT uses "Indicator"/"Description" suffixes
    "Use Case Identifier": "use_case_id",
    "Public Reporting Indicator": "is_withheld",
    "Development Stage": "stage_of_development",
    "High Impact Indicator": "is_high_impact",
    "High Impact Justification": "justification",
    "Problem Description": "problem_statement",
    "Benefit Description": "expected_benefits",
    "Output Description": "system_outputs",
    "Operation Date": "operational_date",
    "Contractor Indicator": "development_type",
    "Vendor Name": "vendor_name",
    "ATO Indicator": "has_ato",
    "System Name": "system_name",
    "Training Data Description": "training_data_description",
    "Enterprise Data Inventory URL": "link_to_data",
    "PII Indicator": "has_pii",
    "PIA URL": "pia_url",
    "Demographic Variable Description": "demographic_features",
    "Custom Code Indicator": "has_custom_code",
    "Open Source Code URL": "code_url",
    "Predeployment Testing Indicator": "hi_testing_conducted",
    "AI Impact Assessment Indicator": "hi_assessment_completed",
    "Potential Impact Description": "hi_potential_impacts",
    "Independent Review Indicator": "hi_independent_review",
    "Ongoing Monitoring Indicator": "hi_ongoing_monitoring",
    "Operator Training Indicator": "hi_training_established",
    "Fail Safe Indicator": "hi_failsafe_presence",
    "Appeal Process Indicator": "hi_appeal_process",
    "End User Feedback Description": "hi_public_consultation",
    # VA uses custom names
    "VA Admin or Staff Office": "bureau_component",
    "High-Impact Status": "is_high_impact",
    "Problem to be Solved": "problem_statement",
    "Expected Benefits": "expected_benefits",
    "AI System Outputs": "system_outputs",
    "AI Tech Classification": "ai_classification",
    "Topic Area": "topic_area",
    "Custom-Developed Code?": "has_custom_code",
    "Development Type": "development_type",
    "Federal Data Catalog Link": "link_to_data",
    "Public Open Source Link": "code_url",
    # CFTC minimal schema
    "Bureau": "bureau_component",
    "What is the intended purpose and expected benefits of the AI?": "expected_benefits",
    # DOJ minimal schema
    "Contact Name": None,  # no canonical field
    "Contact Email Address": "email_address",
    "Bureau/Component/Division/Branch": "bureau_component",
    "Is the AI use case found in Appendix B's list of general commercial AI products and services?": None,
    "What is the intended purpose and expected benefits of the AI?": "expected_benefits",
    "Is the AI use case rights-impacting, safety-impacting, both, or neither?": "is_high_impact",
    # DOC simple schema
    "Description": "problem_statement",
    "Agency": None,  # redundant with agency table
    # NSF simple schema
    "Summary of Use Case": "problem_statement",
    "Stage of System Development Life Cycle": "stage_of_development",
    "Date Implemented": "operational_date",
    "Bureau / Department": "bureau_component",
    # OPM custom schema
    "Tool/Application Name": "use_case_name",
    "Sponsoring Office": "bureau_component",
    "Deployment Phase": "stage_of_development",
    "First Production Use": "operational_date",
    "Risk Classification": "is_high_impact",
    "Compliance Documentation": "has_ato",
    # TVA/GPO/NMB custom headers
    "Use Case Topic Area": "topic_area",
    "Intended Purpose and Expected Benefits": "expected_benefits",
    "Impact Classification": "is_high_impact",
    "AI Use Case Name": "use_case_name",
    "Summary of Use Case": "problem_statement",
    "AI Technique": "ai_classification",
    "AI Tool": "vendor_name",
    "Intended Purpose": "problem_statement",
    "ID": "use_case_id",
    "Use Case": "use_case_name",
}

# Columns indicating this is a consolidated/Appendix B format (COTS).
# Two known variants exist: the original 6-column form (with "Commercial Examples")
# and the 2025 OMB aggregate form (5 columns, no "Commercial Examples", with an
# "Agency" column instead so a single file can carry many agencies). Detection
# below is normalized + N>=2 marker columns, so either variant matches.
CONSOLIDATED_COLUMNS = {
    "AI Use Case",
    "Commercial Examples",
    "Agency Use (Y/N)?",
    "Agency Use(Y/N)?",
    "Name of Commercial Product or Service Used",
    "Estimated # of Licenses/Users",
}


def normalize_header(h: str) -> str:
    """Normalize a header string for fuzzy matching."""
    if h is None:
        return ""
    return " ".join(str(h).replace("\n", " ").replace("\u2013", "-").replace("\u0092", "'").replace("\u0096", "-").split()).strip().lower()


# Pre-computed normalized lookup tables. Built once at import time so per-header
# matching is O(1) on the exact-match paths instead of repeatedly normalizing
# every override/canonical key for each header.
_NORMALIZED_OVERRIDES: dict[str, str | None] = {}
_NORMALIZED_CANONICAL: dict[str, str] = {}


def _build_normalized_lookups() -> None:
    """Populate the normalized lookup dicts from EXPLICIT_OVERRIDES and CANONICAL_TO_DB."""
    _NORMALIZED_OVERRIDES.clear()
    _NORMALIZED_CANONICAL.clear()
    for k, v in EXPLICIT_OVERRIDES.items():
        nk = normalize_header(k)
        if nk and nk not in _NORMALIZED_OVERRIDES:
            _NORMALIZED_OVERRIDES[nk] = v
    for k, v in CANONICAL_TO_DB.items():
        nk = normalize_header(k)
        if nk and nk not in _NORMALIZED_CANONICAL:
            _NORMALIZED_CANONICAL[nk] = v


def fuzzy_match_canonical(header: str, threshold: float = 0.7) -> str | None:
    """Find the best canonical column match for a header.

    Normalization (strip whitespace, collapse newlines/repeated spaces, lowercase)
    is applied to BOTH the input header and the override/canonical key sets BEFORE
    matching. This is required so that header variants such as
    ``"Use Case ID\\n\\n[Agency Abbrev.] - [#]"`` (which several agencies use)
    still resolve to the canonical ``use_case_id`` column. Doing the override
    lookup against the raw, un-normalized header was silently dropping ~2,000
    use_case_id values during ingest.

    Match order:
      1. Normalized exact match against EXPLICIT_OVERRIDES.
      2. Normalized exact match against CANONICAL_TO_DB.
      3. Prefix match: header begins with an override/canonical key followed by
         whitespace (handles "Use Case ID [Agency Abbrev.] - [#]" style suffixes).
      4. Fuzzy SequenceMatcher ratio against canonical names (>= threshold).
    """
    if not header:
        return None

    if not _NORMALIZED_OVERRIDES:
        _build_normalized_lookups()

    normalized = normalize_header(header)
    if not normalized:
        return None

    # 1. Normalized exact match in EXPLICIT_OVERRIDES.
    if normalized in _NORMALIZED_OVERRIDES:
        return _NORMALIZED_OVERRIDES[normalized]

    # 2. Normalized exact match in CANONICAL_TO_DB.
    if normalized in _NORMALIZED_CANONICAL:
        return _NORMALIZED_CANONICAL[normalized]

    # 3. Prefix-match, longest key first so "use case id" beats "use case".
    #    Catches "use case id [agency abbrev.] - [#]" and friends where the
    #    agency tacks an annotation on the end of the canonical name.
    prefix_candidates = sorted(
        list(_NORMALIZED_OVERRIDES.items()) + list(_NORMALIZED_CANONICAL.items()),
        key=lambda kv: len(kv[0]),
        reverse=True,
    )
    for nk, db_col in prefix_candidates:
        if nk and normalized.startswith(nk + " "):
            return db_col

    # 4. Fall back to fuzzy ratio against canonical names.
    best_score = 0.0
    best_match = None
    for nk, db_col in _NORMALIZED_CANONICAL.items():
        score = SequenceMatcher(None, normalized, nk).ratio()
        if score > best_score:
            best_score = score
            best_match = db_col

    if best_score >= threshold:
        return best_match
    return None


# Public alias used by tests and external callers.
def map_header_to_canonical(header: str) -> str | None:
    """Map a raw header string to its canonical DB column, or None."""
    return fuzzy_match_canonical(header)


def is_consolidated_format(headers: list[str]) -> bool:
    """Detect if a file is in consolidated/Appendix B COTS format.

    Match against normalized headers so curly-quote / `?` / whitespace variants
    don't silently drop. N >= 2 marker columns is sufficient.
    """
    normalized = {normalize_header(h) for h in headers if h}
    canonical_normalized = {normalize_header(c) for c in CONSOLIDATED_COLUMNS}
    matches = len(normalized & canonical_normalized)
    return matches >= 2


# Normalized-header → consolidated DB column. Routing through normalize_header
# at lookup time means we tolerate `?` vs no-`?`, double spaces, curly quotes,
# and the en-dash/em-dash variants OMB occasionally publishes.
_CONSOLIDATED_HEADER_MAP = {
    normalize_header("AI Use Case"): "ai_use_case",
    normalize_header("Commercial Examples"): "commercial_examples",
    normalize_header("Agency Use (Y/N)?"): "agency_uses",
    normalize_header("Agency Use(Y/N)?"): "agency_uses",
    normalize_header("Agency Use (Y/N)"): "agency_uses",
    normalize_header("Name of Commercial Product or Service Used"): "commercial_product",
    normalize_header("Estimated # of Licenses/Users"): "estimated_licenses_users",
    # 2025 aggregate form: a single file with many agencies; agency is a column.
    normalize_header("Agency"): "agency_name",
}


def map_consolidated_headers(headers: list[str]) -> dict[int, str]:
    """Map column indices to consolidated_use_cases DB columns."""
    mapping = {}
    for i, h in enumerate(headers):
        if not h:
            continue
        nk = normalize_header(str(h))
        db_col = _CONSOLIDATED_HEADER_MAP.get(nk)
        if db_col:
            mapping[i] = db_col
    return mapping


def map_canonical_headers(headers: list[str]) -> dict[int, str]:
    """Map column indices to use_cases DB columns via fuzzy match + overrides."""
    mapping = {}
    for i, h in enumerate(headers):
        if not h:
            continue
        db_col = fuzzy_match_canonical(str(h).strip())
        if db_col:
            mapping[i] = db_col
    return mapping


# 2025 OMB consolidated INDIVIDUALLY-REPORTED inventory.
#
# Source: data/raw/2025_individually_reported_AI_use_cases.xlsx
# Sheet: 'Consolidated Inventory' — header row 2, data starts row 3.
# 36 columns total = 34 OMB schema columns + 2 OMB-added agency columns
# (Agency Abbreviation, Agency Name) at the front.
#
# Position-locked: the file's two `Does this AI use case ...` headers (PII
# and ATO) collide on prefix match alone, so we trust column ORDINAL over
# header substring. If OMB ever reorders columns we fail loudly via the
# verification check (see map_omb_consolidated_headers below).
OMB_CONSOLIDATED_COLUMNS = [
    ("agency abbreviation",                   "agency_abbreviation"),
    ("agency name",                           "agency_name"),
    ("use case id",                           "use_case_id_omb"),
    ("use case name",                         "use_case_name"),
    ("bureau/component",                      "bureau_component"),
    ("email address",                         "email_address"),
    ("should this ai use case be withheld",   "is_withheld"),
    ("stage of development",                  "stage_of_development"),
    ("is the ai use case high-impact",        "is_high_impact"),
    ("justification",                         "hi_justification"),
    ("use case topic area",                   "topic_area"),
    ("ai classification",                     "ai_classification"),
    ("what problem is the ai intended to solve", "problem_statement"),
    ("what are the expected benefits",        "expected_benefits"),
    ("describe the ai system",                "system_outputs"),
    ("date when ai use case became operational", "operational_date"),
    ("was the system involved in this use case purchased", "contracting_usage"),
    ("vendor(s) name",                        "vendor_name"),
    ("does this ai use case have an associated authorization to operate", "have_ato"),
    ("system(s) name",                        "system_name_ato"),
    ("describe any data used to",             "training_data_description"),
    ("if the data is required to be",         "link_to_data"),
    ("does this ai use case",                 "has_pii"),
    ("if publicly available, provide",        "pia_url"),
    ("which, if any, demographic",            "demographic_features"),
    ("does this project include",             "has_custom_code"),
    ("if the code is open source",            "code_url"),
    ("has pre-deployment testing",            "hi_testing_conducted"),
    ("has an ai impact assessment",           "hi_assessment_completed"),
    ("what are the potential",                "hi_potential_impacts"),
    ("has as independent review",             "hi_independent_review"),
    ("is there a process to conduct",         "hi_ongoing_monitoring"),
    ("has the agency established sufficient and periodic", "hi_training_established"),
    ("does this ai use case have an appropriate fail-safe", "hi_failsafe_presence"),
    ("is there an established appeal process", "hi_appeal_process"),
    ("what steps has the agency taken to consult", "hi_public_consultation"),
]
assert len(OMB_CONSOLIDATED_COLUMNS) == 36, "OMB_CONSOLIDATED_COLUMNS must be exactly 36"


def map_omb_consolidated_headers(headers: list[str | None]) -> list[str | None]:
    """Position-locked header map for the OMB consolidated XLSX.

    Returns a list of canonical keys aligned with the input headers by
    INDEX. Header text is checked for sanity (the documented prefix must
    appear) but the canonical key comes from position. This guards against
    OMB silently reordering columns: if the 1st header doesn't contain
    'agency abbreviation', the 4th doesn't contain 'use case name', etc.,
    the function raises ValueError.
    """
    if len(headers) < len(OMB_CONSOLIDATED_COLUMNS):
        raise ValueError(
            f"OMB consolidated file has {len(headers)} columns; "
            f"expected at least {len(OMB_CONSOLIDATED_COLUMNS)}"
        )
    out: list[str | None] = [None] * len(headers)
    for i, (expected_prefix, canonical) in enumerate(OMB_CONSOLIDATED_COLUMNS):
        h = headers[i]
        h_norm = " ".join(str(h or "").lower().split())
        if expected_prefix not in h_norm:
            raise ValueError(
                f"OMB consolidated header position {i} expected prefix "
                f"{expected_prefix!r} in header; got {h_norm[:80]!r}"
            )
        out[i] = canonical
    return out
