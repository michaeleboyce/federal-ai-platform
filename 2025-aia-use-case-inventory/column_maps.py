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
    "Should this AI use case be withheld from public reporting?": "withheld_from_public",
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
    "If the data is required to be publicly disclosed as an open government data asset, provide a link to the entry on the Federal Data Catalog.": "federal_data_catalog_link",
    "Does this AI use case involve personally identifiable information (PII) that is maintained by the agency?": "involves_pii",
    "If publicly available, provide the link to the AI use case's associated Privacy Impact Assessment (PIA), if any.": "pia_link",
    "Which, if any, demographic variables does the AI use case explicitly use as model features?": "demographic_variables",
    "Does this project include custom-developed code?": "has_custom_code",
    "If the code is open source, provide the link for the publicly available source code.": "open_source_link",
    # Section 5
    "Has pre-deployment testing been conducted for this AI use case?": "pre_deployment_testing",
    "Has an AI impact assessment been completed for this AI use case?": "impact_assessment",
    "What are the potential impacts of using the AI for this particular use case and how were they identified?": "potential_impacts",
    "Has as independent review of the AI use case been conducted?": "independent_review",
    "Is there a process to conduct ongoing monitoring to identify any adverse impacts to the performance and security of the AI functionality, as well as to privacy, civil rights, and civil liberties?": "ongoing_monitoring",
    "Has the agency established sufficient and periodic training for operators of the AI to interpret and act on the its output and managed associated risks?": "operator_training",
    "Does this AI use case have an appropriate fail-safe that minimizes the risk of significant harm?": "has_fail_safe",
    "Is there an established appeal process in the event that an impacted individual would like to appeal or contest the AI system's outcome?": "appeal_process",
    "What steps has the agency taken to consult and incorporate feedback from end users of this AI use case and the public?": "end_user_feedback",
}

# Explicit renames for agencies with abbreviated column names
EXPLICIT_OVERRIDES = {
    # DOT uses "Indicator"/"Description" suffixes
    "Use Case Identifier": "use_case_id",
    "Public Reporting Indicator": "withheld_from_public",
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
    "Enterprise Data Inventory URL": "federal_data_catalog_link",
    "PII Indicator": "involves_pii",
    "PIA URL": "pia_link",
    "Demographic Variable Description": "demographic_variables",
    "Custom Code Indicator": "has_custom_code",
    "Open Source Code URL": "open_source_link",
    "Predeployment Testing Indicator": "pre_deployment_testing",
    "AI Impact Assessment Indicator": "impact_assessment",
    "Potential Impact Description": "potential_impacts",
    "Independent Review Indicator": "independent_review",
    "Ongoing Monitoring Indicator": "ongoing_monitoring",
    "Operator Training Indicator": "operator_training",
    "Fail Safe Indicator": "has_fail_safe",
    "Appeal Process Indicator": "appeal_process",
    "End User Feedback Description": "end_user_feedback",
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
    "Federal Data Catalog Link": "federal_data_catalog_link",
    "Public Open Source Link": "open_source_link",
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

# Columns indicating this is a consolidated/Appendix B format (COTS)
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


def fuzzy_match_canonical(header: str, threshold: float = 0.7) -> str | None:
    """Find the best canonical column match for a header."""
    if not header:
        return None

    # Try explicit overrides first (exact match)
    if header in EXPLICIT_OVERRIDES:
        return EXPLICIT_OVERRIDES[header]

    # Normalize and try to match canonical
    normalized = normalize_header(header)
    if not normalized:
        return None

    best_score = 0.0
    best_match = None
    for canonical, db_col in CANONICAL_TO_DB.items():
        score = SequenceMatcher(None, normalized, normalize_header(canonical)).ratio()
        if score > best_score:
            best_score = score
            best_match = db_col

    if best_score >= threshold:
        return best_match
    return None


def is_consolidated_format(headers: list[str]) -> bool:
    """Detect if a file is in consolidated/Appendix B COTS format."""
    header_set = {str(h).strip() for h in headers if h}
    # If 2+ consolidated columns match, treat as consolidated
    matches = sum(1 for col in CONSOLIDATED_COLUMNS if col in header_set)
    return matches >= 2


def map_consolidated_headers(headers: list[str]) -> dict[int, str]:
    """Map column indices to consolidated_use_cases DB columns."""
    mapping = {}
    for i, h in enumerate(headers):
        hs = str(h).strip() if h else ""
        if hs == "AI Use Case":
            mapping[i] = "ai_use_case"
        elif hs == "Commercial Examples":
            mapping[i] = "commercial_examples"
        elif hs in ("Agency Use (Y/N)?", "Agency Use(Y/N)?"):
            mapping[i] = "agency_uses"
        elif hs == "Name of Commercial Product or Service Used":
            mapping[i] = "commercial_product"
        elif hs == "Estimated # of Licenses/Users":
            mapping[i] = "estimated_licenses_users"
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
