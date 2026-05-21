"""2024 (M-24-10) → 2025 (M-25-21) schema crosswalk and header resolver.

Phase 0 of the 2024 ↔ 2025 AI use case inventory comparison project. This is a
sibling to ``column_maps.py``: where that module maps *agency-filed 2025*
headers to the canonical M-25-21 DB schema, this one maps the *2024 consolidated
inventory* headers to a snake_case 2024 vocabulary and records — column by
column — whether each 2024 field can honestly be compared to its 2025
counterpart.

Design notes
------------
- **Static constants only.** The 2024 data dictionary
  (``docs/plans/2024-vs-2025-comparison/2024_data_dictionary.yaml``) was read
  *once during development* to author the constants below; this module does no
  runtime YAML parsing — it is committed as plain code, mirroring
  ``column_maps.py``.
- **The live CSV header is the authoritative vocabulary.** The crosswalk has one
  entry per column in
  ``data/raw/2024_consolidated_ai_inventory_raw_v2.csv`` (cp1252-encoded). That
  file ships **62 columns**, not the 54 quoted in some early planning notes: the
  62 include 10 "If Other/No, please explain." follow-up columns that the YAML
  models as ``*_question_type`` metadata. They are real CSV columns, so they are
  in the crosswalk (classified ``2024_only``) — nothing is silently dropped.
- The ``target_2025`` values are canonical 2025 DB column names from the
  ``use_cases`` table (see ``db.py`` / ``column_maps.CANONICAL_TO_DB``), or
  ``None`` where 2024 has no 2025 equivalent.

Comparability disposition (exactly one per column):
  - ``directly_comparable`` — same concept, same value space; compare as-is.
  - ``recoded``             — same concept, different value taxonomy; comparison
                              requires a (lossy) value recode.
  - ``2024_only``           — no 2025 equivalent; cannot be compared.

The 2025-only columns (no 2024 source) are not in this structure — they are
documented in ``docs/plans/2024-vs-2025-comparison/COMPARABILITY-MATRIX.md``.
"""

from __future__ import annotations

from difflib import SequenceMatcher

# Reuse the 2025 header normalizer so we never diverge from it.
from column_maps import normalize_header

# Disposition vocabulary.
DIRECTLY_COMPARABLE = "directly_comparable"
RECODED = "recoded"
YEAR_2024_ONLY = "2024_only"

COMPARABILITY_VALUES = frozenset({DIRECTLY_COMPARABLE, RECODED, YEAR_2024_ONLY})


# ---------------------------------------------------------------------------
# The crosswalk.
#
# One entry per 2024 CSV column, in CSV column order. Each entry is a dict:
#   csv_header     — exact 2024 CSV header string (authoritative).
#   field          — snake_case 2024 column name (YAML semantic stem, numeric
#                    prefix dropped).
#   target_2025    — canonical 2025 DB column it maps to, or None.
#   comparability  — one of COMPARABILITY_VALUES.
#   notes          — short rationale for the disposition.
#
# Classification reasoning is captured per row in `notes`; see
# COMPARABILITY-MATRIX.md for the human-readable table.
# ---------------------------------------------------------------------------
COLUMN_CROSSWALK_2024: list[dict] = [
    # --- Section 1: Use Case Identifiers --------------------------------------
    {
        "csv_header": "Use Case Name",
        "field": "use_case_name",
        "target_2025": "use_case_name",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Title of the AI use case; same concept both years.",
    },
    {
        "csv_header": "Agency",
        "field": "agency",
        "target_2025": "agency_name",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Agency full name; OMB adds this during consolidation both years.",
    },
    {
        "csv_header": "Agency Abbreviation",
        "field": "agency_abbreviation",
        "target_2025": "agency_abbreviation",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Agency abbreviation; OMB-added consolidation column both years.",
    },
    {
        "csv_header": "Bureau",
        "field": "bureau",
        "target_2025": "bureau_component",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Sub-agency organization; free text, messy both years but same concept.",
    },
    {
        "csv_header": "Use Case Topic Area",
        "field": "topic_area",
        "target_2025": "topic_area",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Topic area; the enum drifted year to year but the concept is shared "
        "and the dashboard already collapses topic aliases.",
    },
    {
        "csv_header": "Other (Use Case Topic Area)",
        "field": "topic_area_other",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Free-text 'Other' detail for topic_area (YAML 8_question_type); "
        "metadata, no 2025 equivalent.",
    },
    {
        "csv_header": "Is the AI use case found in the below list of general "
        "commercial AI products and services?",
        "field": "commercial_ai",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "2024 COTS self-identification (YAML 10_commercial_ai). 2025 split "
        "COTS into a separate Appendix B inventory entirely; not a comparable "
        "row-level field.",
    },
    {
        "csv_header": "What is the intended purpose and expected benefits of the AI?",
        "field": "purpose_benefits",
        "target_2025": "expected_benefits",
        "comparability": RECODED,
        "notes": "2024 combines problem + benefits in one field; M-25-21 splits it "
        "into problem_statement + expected_benefits. Mapped to expected_benefits; "
        "splitting one field into two is lossy.",
    },
    {
        "csv_header": "Describe the AI system’s outputs.",
        "field": "outputs",
        "target_2025": "system_outputs",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Free-text description of system outputs; same concept both years.",
    },
    {
        "csv_header": "Stage of Development",
        "field": "dev_stage",
        "target_2025": "stage_of_development",
        "comparability": RECODED,
        "notes": "2024 uses the 5-value SDLC enum (Initiated / Acquisition / "
        "Implementation / Operation / Retired); 2025 uses the 4-value M-25-21 enum "
        "(Pre-deployment / Pilot / Deployed / Retired). Different taxonomies — "
        "see DEV_STAGE_RECODE_2024.",
    },
    {
        "csv_header": "Is the AI use case rights-impacting, safety-impacting, "
        "both, or neither?",
        "field": "impact_type",
        "target_2025": "is_high_impact",
        "comparability": RECODED,
        "notes": "2024 rights/safety/both/neither taxonomy does NOT map 1:1 to "
        "M-25-21 high-impact tiers — see IMPACT_TYPE_RECODE_2024 (lossy).",
    },
    # --- Section 2: Use Case Summary -----------------------------------------
    {
        "csv_header": "Date Initiated",
        "field": "date_initiated",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "M-25-21 collapsed four date fields into one operational_date; "
        "initiation date has no 2025 home.",
    },
    {
        "csv_header": "Date when Acquisition and/or Development began",
        "field": "date_acq_dev_began",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "M-25-21 collapsed four date fields into one; acq/dev-start date "
        "has no 2025 home.",
    },
    {
        "csv_header": "Date Implemented",
        "field": "date_implemented",
        "target_2025": "operational_date",
        "comparability": RECODED,
        "notes": "2024 'Date Implemented' is the closest analogue to 2025 "
        "operational_date, but 2025 conflates pilot-start and deployment dates — "
        "the mapping is approximate.",
    },
    {
        "csv_header": "Date Retired",
        "field": "date_retired",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "2025 expresses retirement via the 'Retired' development stage, "
        "not a date; no comparable date column.",
    },
    {
        "csv_header": "Was the AI system involved in this use case developed "
        "(or is it to be developed) under contract(s) or in-house? ",
        "field": "dev_method",
        "target_2025": "development_type",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Contracting vs in-house vs both; same three-way concept and "
        "value space both years.",
    },
    {
        "csv_header": "Provide the Procurement Instrument Identifier(s) (PIID) "
        "of the contract(s) used.",
        "field": "contract_piids",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "M-25-21 dropped the PIID column entirely; no 2025 equivalent.",
    },
    {
        "csv_header": "Is this AI use case supporting a High-Impact Service "
        "Provider (HISP) public-facing service?",
        "field": "hisp_support",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "HISP block; M-25-21 dropped HISP reporting entirely.",
    },
    {
        "csv_header": "Which HISP is the AI use case supporting?",
        "field": "hisp_name",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "HISP block; M-25-21 dropped HISP reporting entirely.",
    },
    {
        "csv_header": "Which public-facing service is the AI use case supporting?",
        "field": "public_service",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "HISP block (public-facing-service identification); M-25-21 dropped "
        "HISP reporting entirely.",
    },
    {
        "csv_header": "Does this AI use case disseminate information to the public?",
        "field": "public_info",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Information-dissemination question (YAML 27_public_info); M-25-21 "
        "has no equivalent.",
    },
    {
        "csv_header": "How is the agency ensuring compliance with Information "
        "Quality Act guidelines, if applicable?",
        "field": "iqa_compliance",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Information Quality Act compliance; M-25-21 dropped it.",
    },
    {
        "csv_header": "Does this AI use case involve personally identifiable "
        "information (PII) that is maintained by the agency?",
        "field": "contains_pii",
        "target_2025": "has_pii",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "PII Yes/No; same concept and value space both years.",
    },
    {
        "csv_header": "Has the Senior Agency Official for Privacy (SAOP) "
        "assessed the privacy risks associated with this AI use case?",
        "field": "saop_review",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "SAOP privacy-risk review (YAML 30_saop_review); M-25-21 replaced "
        "this with the optional pia_url link — not a comparable Yes/No field.",
    },
    {
        "csv_header": "Do you have access to an enterprise data catalog or "
        "agency-wide data repository that enables you to identify whether or not "
        "the necessary datasets exist and are ready to develop your use case?",
        "field": "data_catalog",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Agency-readiness/infrastructure question (YAML 31_data_catalog); "
        "M-25-21 dropped the readiness block.",
    },
    {
        "csv_header": "If Other, please explain.",
        "field": "data_catalog_other",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Free-text 'Other' detail for data_catalog (YAML 31_question_type); "
        "metadata, no 2025 equivalent.",
    },
    {
        "csv_header": "Describe any agency-owned data used to train, fine-tune, "
        "and/or evaluate performance of the model(s) used in this use case.",
        "field": "agency_data",
        "target_2025": "training_data_description",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Free-text training-data description; same concept both years "
        "(2024 scopes to agency-owned data; 2025 is broader but compatible).",
    },
    {
        "csv_header": "Is there available documentation for the model training "
        "and evaluation data that demonstrates the degree to which it is "
        "appropriate to be used in analysis or for making predictions?",
        "field": "data_docs",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Training-data documentation-maturity scale (YAML 34_data_docs); "
        "M-25-21 dropped it.",
    },
    {
        "csv_header": "Which, if any, demographic variables does the AI use case "
        "explicitly use as model features?",
        "field": "demo_features",
        "target_2025": "demographic_features",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Demographic model features; multi-select, same concept and "
        "near-identical value lists both years.",
    },
    {
        "csv_header": "If Other, please explain.",
        "field": "demo_features_other",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Free-text 'Other' detail for demo_features (YAML "
        "35_question_type); metadata, no 2025 equivalent.",
    },
    {
        "csv_header": "Does this project include custom-developed code?",
        "field": "custom_code",
        "target_2025": "has_custom_code",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Custom-code Yes/No; same concept and value space both years.",
    },
    {
        "csv_header": "Does the agency have access to the code associated with "
        "the AI use case?",
        "field": "code_access",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Code-access tri-state (YAML 38_code_access); M-25-21 dropped it — "
        "2025 keeps only the optional code_url link.",
    },
    {
        "csv_header": "If the code is open-source, provide the link for the "
        "publicly available source code.",
        "field": "code_link",
        "target_2025": "code_url",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Optional link to public source code; same concept both years.",
    },
    {
        "csv_header": "Does this AI use case have an associated Authority to "
        "Operate (ATO) for an AI system?",
        "field": "has_ato",
        "target_2025": "has_ato",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "ATO Yes/No; same concept and value space both years.",
    },
    {
        "csv_header": "System Name",
        "field": "system_name",
        "target_2025": "system_name",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "ATO system name; free text, same concept both years.",
    },
    {
        "csv_header": "How long have you waited for the necessary developer "
        "tools to implement the AI use case? ",
        "field": "dev_tools_wait",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Agency-readiness block (YAML 42_dev_tools_wait); M-25-21 dropped "
        "the readiness/infrastructure questions.",
    },
    {
        "csv_header": "For this AI use case, is the required IT infrastructure "
        "provisioned via a centralized intake form or process inside the agency?",
        "field": "infra_provisioned",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Agency-readiness block (YAML 43_infra_provisioned); M-25-21 "
        "dropped the readiness/infrastructure questions.",
    },
    {
        "csv_header": "If Other, please explain.",
        "field": "infra_provisioned_other",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Free-text 'Other' detail for infra_provisioned (YAML "
        "43_question_type); metadata, no 2025 equivalent.",
    },
    {
        "csv_header": "Do you have a process in place to request access to "
        "computing resources for model training and development of the AI "
        "involved in this use case?",
        "field": "compute_request",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Agency-readiness block (YAML 45_compute_request); M-25-21 dropped "
        "the readiness/infrastructure questions.",
    },
    {
        "csv_header": "If Other, please explain.",
        "field": "compute_request_other",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Free-text 'Other' detail for compute_request (YAML "
        "45_question_type); metadata, no 2025 equivalent.",
    },
    {
        "csv_header": "Has communication regarding the provisioning of your "
        "requested resources been timely?",
        "field": "timely_resources",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Agency-readiness block (YAML 47_timely_resources); M-25-21 dropped "
        "the readiness/infrastructure questions.",
    },
    {
        "csv_header": "If Other, please explain.",
        "field": "timely_resources_other",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Free-text 'Other' detail for timely_resources (YAML "
        "47_question_type); metadata, no 2025 equivalent.",
    },
    {
        "csv_header": "How are existing data science tools, libraries, data "
        "products, and internally-developed AI infrastructure being re-used for "
        "the current AI use case?",
        "field": "existing_reuse",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Agency-readiness block (YAML 49_existing_reuse); M-25-21 dropped "
        "the readiness/infrastructure questions.",
    },
    {
        "csv_header": "Has information regarding the AI use case, including "
        "performance metrics and intended use of the model, been made available "
        "for review and feedback within the agency?",
        "field": "internal_review",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Internal-documentation-availability scale (YAML 50_internal_review); "
        "M-25-21 dropped it.",
    },
    {
        "csv_header": "Has your agency requested an extension to implement the "
        "minimum risk management practices for this AI use case?",
        "field": "extension_request",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "M-24-10 risk-practice extension request (YAML 51_extension_request); "
        "M-25-21 has no equivalent gating field.",
    },
    {
        "csv_header": "Has an AI impact assessment been conducted for this AI "
        "use case?",
        "field": "impact_assessment",
        "target_2025": "hi_assessment_completed",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "AI impact assessment status; same concept and near-identical "
        "value list (Yes / Planned-or-in-progress / No / CAIO waived) both years.",
    },
    {
        "csv_header": "Has the AI use case been tested in operational or "
        "real-world environments to understand the performance and impact it may "
        "have on affected individuals or communities?",
        "field": "real_world_testing",
        "target_2025": "hi_testing_conducted",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Pre-deployment/real-world testing; same concept and value space "
        "both years.",
    },
    {
        "csv_header": "What are the key risks from using the AI for this "
        "particular use case and how were they identified?",
        "field": "key_risks",
        "target_2025": "hi_potential_impacts",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Free-text identification of foreseeable risks/impacts; same "
        "concept both years (2024 'key risks' == 2025 'potential impacts').",
    },
    {
        "csv_header": "Has an independent evaluation of the AI use case been "
        "conducted?",
        "field": "independent_eval",
        "target_2025": "hi_independent_review",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Independent evaluation/review status; same concept and value "
        "space both years.",
    },
    {
        "csv_header": "Is there a process to monitor performance of the AI "
        "system’s functionality and changes to its impact on rights or safety "
        "as part of the post-deployment plan for the AI use case?",
        "field": "monitor_postdeploy",
        "target_2025": "hi_ongoing_monitoring",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Post-deployment ongoing monitoring; same concept both years.",
    },
    {
        "csv_header": "For this particular use case, can the AI carry out a "
        "decision or action without direct human involvement that could result "
        "in a significant impact on rights or safety?",
        "field": "autonomous_impact",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Autonomy/human-involvement question (YAML 57_autonomous_impact); "
        "M-25-21 dropped it.",
    },
    {
        "csv_header": "If Other, please explain.",
        "field": "autonomous_impact_other",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Free-text 'Other' detail for autonomous_impact (YAML "
        "57_question_type); metadata, no 2025 equivalent.",
    },
    {
        "csv_header": "How is the agency providing reasonable and timely notice "
        "regarding the use of AI when people interact with an AI-enabled service "
        "as a result of this AI use case?",
        "field": "ai_notice",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "AI-notice mechanism (YAML 59_ai_notice); M-25-21 dropped it.",
    },
    {
        "csv_header": "If Other, please explain.",
        "field": "ai_notice_other",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Free-text 'Other' detail for ai_notice (YAML 59_question_type); "
        "metadata, no 2025 equivalent.",
    },
    {
        "csv_header": "Is the AI used to significantly influence or inform "
        "decisions or actions that could have an adverse or negative impact on "
        "specific individuals or groups?",
        "field": "adverse_impact",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Adverse-decision-influence question (YAML 61_adverse_impact); "
        "M-25-21 dropped it.",
    },
    {
        "csv_header": "What steps has the agency taken to detect and mitigate "
        "significant disparities in the model’s performance across demographic "
        "groups for this AI use case?",
        "field": "disparity_mitigation",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Demographic-disparity detection/mitigation (YAML "
        "62_disparity_mitigation); M-25-21 dropped this free-text field.",
    },
    {
        "csv_header": "What steps has the agency taken to consult and "
        "incorporate feedback from groups affected by this AI use case?",
        "field": "stakeholder_consult",
        "target_2025": "hi_public_consultation",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Public/affected-group consultation; same concept both years "
        "(2024 63_stakeholder_consult == 2025 hi_public_consultation).",
    },
    {
        "csv_header": "If Other, please explain.",
        "field": "stakeholder_consult_other",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Free-text 'Other' detail for stakeholder_consult (YAML "
        "63_question_type); metadata, no 2025 equivalent.",
    },
    {
        "csv_header": "Is there an established fallback and escalation process "
        "for this AI use case in the event that an impacted individual or group "
        "would like to appeal or contest the AI system’s outcome?",
        "field": "appeal_process",
        "target_2025": "hi_appeal_process",
        "comparability": DIRECTLY_COMPARABLE,
        "notes": "Appeal/contest process; same concept and value space both years.",
    },
    {
        "csv_header": "If No, please explain.",
        "field": "no_appeal_reason",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Free-text 'If No' detail for appeal_process (YAML "
        "66_no_appeal_reason); metadata, no 2025 equivalent.",
    },
    {
        "csv_header": "Where practicable and consistent with applicable law and "
        "governmentwide policy, is there an established mechanism for individuals "
        "to opt-out from the AI functionality in favor of a human alternative?",
        "field": "opt_out",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Opt-out mechanism (YAML 67_opt_out); M-25-21 dropped it — note "
        "2025 has no fail-safe-presence source from 2024 either.",
    },
    {
        "csv_header": "If Other, please explain.",
        "field": "opt_out_other",
        "target_2025": None,
        "comparability": YEAR_2024_ONLY,
        "notes": "Free-text 'Other' detail for opt_out (YAML 67_question_type); "
        "metadata, no 2025 equivalent.",
    },
]


# ---------------------------------------------------------------------------
# Value recode maps.
#
# These are the first Python recode-map data structures in the project (prior
# recoding was markdown reference + hand-coded rules in load_inventories.py).
# Each is a dict; the impact map carries an explicit `lossy` marker so
# downstream code can never silently treat a recoded value as an exact match.
# ---------------------------------------------------------------------------

# 2024 17_impact_type -> 2025 is_high_impact.
#
# The taxonomies do NOT map 1:1: 2024 asks rights/safety/both/neither; 2025
# asks a) High-impact / b) Presumed-high-impact-but-determined-not /
# c) Not high-impact. A 2024 use case flagged rights/safety/both would today
# very likely be reported as high-impact, and "neither" maps cleanly to "not
# high-impact" — but there is no 2024 analogue of the 2025 "b) presumed but
# determined not" middle tier, so EVERY recode here is lossy.
#
# Each value maps to a dict: {"target": <2025 canonical>, "lossy": bool}.
IMPACT_TYPE_RECODE_2024: dict[str, dict] = {
    "Rights-Impacting": {"target": "a) High-impact", "lossy": True},
    "Safety-Impacting": {"target": "a) High-impact", "lossy": True},
    "Both": {"target": "a) High-impact", "lossy": True},
    "Neither": {"target": "c) Not high-impact", "lossy": True},
}

# Every IMPACT_TYPE_RECODE_2024 enum value the YAML defines, for test coverage.
IMPACT_TYPE_ENUM_2024: tuple[str, ...] = (
    "Rights-Impacting",
    "Safety-Impacting",
    "Both",
    "Neither",
)

# 2024 16_dev_stage -> 2025 stage_of_development.
#
# The enums genuinely differ. 2024 uses the 5-value SDLC vocabulary
# (Initiated / Acquisition and/or Development / Implementation and Assessment /
# Operation and Maintenance / Retired); M-25-21 uses the 4-value posture
# vocabulary (a) Pre-deployment / b) Pilot / c) Deployed / d) Retired). The
# mapping below is best-effort: 2024 has no clean "Pilot" analogue, so
# "Implementation and Assessment" is mapped to Pilot (the assessment phase is
# the closest pre-full-deployment state) — this is the lossy edge.
#
# Beyond the five canonical SDLC values, the live 2024 consolidated CSV also
# carries ~50 off-enum rows that agencies filed using assorted ad-hoc stage
# labels (`Planned`, `Ideation`, `In production`, `In mission`, `Research or
# Administrative Action Complete`). These are recoded here too so the stage
# rollup classifies them instead of dumping them in `unknown`; every off-enum
# recode is `lossy: True` because the agency's intent has to be inferred.
# Genuinely empty / unrecognized values are left unmapped — the rollup buckets
# those as `unknown`.
#
# Each value maps to a dict: {"target": <2025 canonical>, "lossy": bool}.
DEV_STAGE_RECODE_2024: dict[str, dict] = {
    "Initiated": {"target": "a) Pre-deployment", "lossy": False},
    "Acquisition and/or Development": {"target": "a) Pre-deployment", "lossy": True},
    "Implementation and Assessment": {"target": "b) Pilot", "lossy": True},
    "Operation and Maintenance": {"target": "c) Deployed", "lossy": False},
    "Retired": {"target": "d) Retired", "lossy": False},
    # Off-enum real-world variants found in the v2 consolidated CSV.
    "Planned": {"target": "a) Pre-deployment", "lossy": True},
    "Ideation": {"target": "a) Pre-deployment", "lossy": True},
    "In production": {"target": "c) Deployed", "lossy": True},
    "In mission": {"target": "c) Deployed", "lossy": True},
    "Research or Administrative Action Complete": {
        "target": "d) Retired",
        "lossy": True,
    },
}

# Every DEV_STAGE_RECODE_2024 enum value the YAML defines, for test coverage.
DEV_STAGE_ENUM_2024: tuple[str, ...] = (
    "Initiated",
    "Acquisition and/or Development",
    "Implementation and Assessment",
    "Operation and Maintenance",
    "Retired",
)


# ---------------------------------------------------------------------------
# Header resolution.
#
# Mirrors column_maps.fuzzy_match_canonical / map_canonical_headers: a
# normalize -> exact -> fuzzy pipeline. Built once at import time so per-header
# resolution is O(1) on the exact path.
# ---------------------------------------------------------------------------

# Normalized-CSV-header -> field name. Built from COLUMN_CROSSWALK_2024.
#
# NOTE: the 2024 CSV intentionally repeats the literal header
# "If Other, please explain." (and once "If No, please explain.") for ten
# follow-up columns. Those collide under exact-normalized lookup, so header
# resolution falls back to CSV column ORDINAL for ambiguous headers — see
# map_2024_headers. This dict is therefore only the unambiguous exact-match
# layer.
_NORMALIZED_HEADER_TO_FIELD: dict[str, str] = {}
_AMBIGUOUS_NORMALIZED_HEADERS: set[str] = set()


def _build_header_lookup() -> None:
    """Populate the normalized-header lookup, recording duplicate headers."""
    _NORMALIZED_HEADER_TO_FIELD.clear()
    _AMBIGUOUS_NORMALIZED_HEADERS.clear()
    seen: dict[str, int] = {}
    for entry in COLUMN_CROSSWALK_2024:
        nk = normalize_header(entry["csv_header"])
        seen[nk] = seen.get(nk, 0) + 1
    for entry in COLUMN_CROSSWALK_2024:
        nk = normalize_header(entry["csv_header"])
        if seen[nk] > 1:
            _AMBIGUOUS_NORMALIZED_HEADERS.add(nk)
        elif nk not in _NORMALIZED_HEADER_TO_FIELD:
            _NORMALIZED_HEADER_TO_FIELD[nk] = entry["field"]


# The crosswalk is in CSV order, so the i-th entry's field is the field for
# CSV column i. This positional list is the authority for ambiguous headers.
_FIELDS_BY_POSITION: list[str] = [e["field"] for e in COLUMN_CROSSWALK_2024]


def resolve_2024_header(header: str, threshold: float = 0.7) -> str | None:
    """Resolve a single 2024 CSV header to its snake_case field name.

    Match order (mirrors column_maps.fuzzy_match_canonical):
      1. Normalized exact match against the unambiguous crosswalk headers.
      2. Fuzzy SequenceMatcher ratio against the unambiguous crosswalk headers
         (>= threshold).

    Ambiguous repeated headers (the ten "If Other/No, please explain."
    columns) are NOT resolvable by text alone — they return None here and must
    be resolved positionally by map_2024_headers. Callers wanting per-column
    resolution should use map_2024_headers, not this function.
    """
    if not header:
        return None
    if not _NORMALIZED_HEADER_TO_FIELD and not _AMBIGUOUS_NORMALIZED_HEADERS:
        _build_header_lookup()

    normalized = normalize_header(header)
    if not normalized:
        return None

    # Repeated headers can only be resolved by position.
    if normalized in _AMBIGUOUS_NORMALIZED_HEADERS:
        return None

    # 1. Normalized exact match.
    if normalized in _NORMALIZED_HEADER_TO_FIELD:
        return _NORMALIZED_HEADER_TO_FIELD[normalized]

    # 2. Fuzzy ratio fallback against the unambiguous headers.
    best_score = 0.0
    best_match: str | None = None
    for nk, field in _NORMALIZED_HEADER_TO_FIELD.items():
        score = SequenceMatcher(None, normalized, nk).ratio()
        if score > best_score:
            best_score = score
            best_match = field

    if best_score >= threshold:
        return best_match
    return None


def map_2024_headers(headers: list[str]) -> dict[int, str]:
    """Map 2024 CSV column indices to snake_case field names.

    Given the 2024 CSV header row, return ``{column_index: field_name}``.
    Mirrors ``column_maps.map_canonical_headers`` but is ORDINAL-AWARE: the
    2024 inventory repeats the literal "If Other, please explain." header ten
    times, so text matching alone cannot disambiguate. When the supplied header
    row has exactly the expected column count and every header position agrees
    (by normalized text) with the crosswalk, resolution is purely positional —
    every column resolves, nothing is silently dropped.

    Resolution per column index ``i``:
      1. If the row length matches the crosswalk and the i-th header's
         normalized text equals the i-th crosswalk header's normalized text,
         use the i-th crosswalk field (positional — handles duplicates).
      2. Otherwise fall back to ``resolve_2024_header`` (exact + fuzzy) for
         unambiguous headers.
    """
    if not _NORMALIZED_HEADER_TO_FIELD and not _AMBIGUOUS_NORMALIZED_HEADERS:
        _build_header_lookup()

    mapping: dict[int, str] = {}
    positional_ok = len(headers) == len(COLUMN_CROSSWALK_2024)

    for i, h in enumerate(headers):
        if h is None or not str(h).strip():
            continue
        # 1. Positional resolution when the header layout matches the crosswalk.
        if positional_ok:
            expected = normalize_header(COLUMN_CROSSWALK_2024[i]["csv_header"])
            if normalize_header(h) == expected:
                mapping[i] = _FIELDS_BY_POSITION[i]
                continue
        # 2. Text-based fallback for unambiguous headers.
        field = resolve_2024_header(str(h))
        if field:
            mapping[i] = field

    return mapping


def comparability_counts() -> dict[str, int]:
    """Return the count of crosswalk entries per comparability disposition."""
    counts = {v: 0 for v in COMPARABILITY_VALUES}
    for entry in COLUMN_CROSSWALK_2024:
        counts[entry["comparability"]] += 1
    return counts
