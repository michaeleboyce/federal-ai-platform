#!/usr/bin/env python3
"""
Round-2 entry_type review for unresolved use cases.

Reads:  audit/review_queue_entry_type_unresolved.csv
DB:     data/federal_ai_inventory_2025.db (read-only)

Writes:
  audit/retag/round2/entry_type/resolved.csv
  audit/retag/round2/entry_type/searches.csv  (empty unless we record one)

Decision rules (default keep_current; only reclassify when clear):

1. vendor_name names a clear commercial vendor (Microsoft, Google, OpenAI,
   Anthropic, AWS/Amazon, Palantir, ServiceNow, Databricks, Snowflake, IBM,
   Salesforce, Oracle, SAP, Adobe, Splunk, ESRI, FLIR, Teledyne, Rapiscan,
   Smiths Detection, Leidos, Booz Allen, Deloitte, Accenture, etc.)
   AND no system_name -> product_deployment
2. vendor names a commercial LLM/cloud provider AND system_name is a
   distinctive agency-chosen name -> bespoke_application
3. development_type contains "in-house" / "Developed in-house" / "agency
   personnel" AND vendor_name is empty/N/A -> custom_system
4. development_type names contracting/vendor only AND system_name is missing
   -> product_deployment
5. Otherwise keep_current.

Confidence: high if rule fires with strong vendor signal; medium if mixed;
low if speculative (we then keep_current).
"""

import csv
import os
import re
import sqlite3
import sys

ROOT = "/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory"
INPUT_CSV = os.path.join(ROOT, "audit/review_queue_entry_type_unresolved.csv")
DB = os.path.join(ROOT, "data/federal_ai_inventory_2025.db")
OUT_DIR = os.path.join(ROOT, "audit/retag/round2/entry_type")
RESOLVED_CSV = os.path.join(OUT_DIR, "resolved.csv")
SEARCHES_CSV = os.path.join(OUT_DIR, "searches.csv")

# Product vendors: their main offering IS a product, so vendor_name often
# means the agency deployed that product (e.g., M365 Copilot, ChatGPT,
# ServiceNow, Databricks). Default => product_deployment unless agency
# clearly built a wrapper.
PRODUCT_VENDORS = [
    # Hyperscaler / LLM platform
    "microsoft", "openai", "anthropic", "google", "amazon web services", "aws",
    "azure openai",
    # Enterprise software / data platforms
    "ibm", "oracle", "salesforce", "sap", "adobe",
    "palantir", "servicenow", "databricks", "snowflake", "splunk", "elastic",
    "mongodb", "tableau", "qlik", "alteryx", "dataiku", "datarobot", "h2o.ai",
    # GIS / imagery
    "esri",
    # Detection hardware / niche product makers
    "flir", "teledyne", "rapiscan", "smiths detection", "thruwave",
    "axon", "motorola",
    # Coding
    "github", "gitlab", "jetbrains", "tabnine", "cursor",
    # Comms / collaboration
    "nuance", "verint", "genesys", "twilio", "zoom", "cisco", "vmware",
    "atlassian", "thomson reuters", "lexisnexis", "westlaw",
    "qualtrics", "medallia", "abbyy", "kofax", "uipath",
    "automation anywhere", "blue prism", "appian", "pega", "mulesoft",
    "informatica", "veritone", "clarifai", "primer.ai", "primer ai",
    "sas ", "sas institute", "mathworks", "matlab",
    "hugging face", "huggingface", "cohere", "stability ai",
    "perplexity", "scale ai", "labelbox",
    "carahsoft",  # reseller but typically reselling commercial products
]

# System integrators / consultancies: vendor_name here usually means a
# contractor BUILT something custom for the agency. Default => keep current
# label or bespoke_application if narrative implies vendor-built app on top
# of an LLM. Do NOT classify as product_deployment.
SYSTEM_INTEGRATORS = [
    "accenture", "deloitte", "booz allen", "kpmg", "pwc", "mckinsey",
    "ey ", "ernst & young", "leidos", "raytheon", "lockheed", "northrop",
    "general dynamics", "saic", "caci", "mantech", "peraton", "guidehouse",
    "cgi federal", "iron mountain",
    "shieldai", "shield ai", "anduril",  # often build custom systems
    "pluribus digital", "ad hoc", "nava", "truss",
]

# Vendors most typical of bespoke_application (LLM/cloud APIs / model-as-a-
# service providers underneath custom apps)
LLM_API_VENDORS = [
    "microsoft", "openai", "anthropic", "google", "aws", "amazon web services",
    "azure openai", "azure", "bedrock", "vertex", "cohere", "hugging face",
    "ibm",  # Watson APIs frequently wrapped by agency apps
    "cisco",  # rare here; defensive
]

# Use-case-name signals indicating an agency-built wrapper application.
# Triggers lean to bespoke_application instead of product_deployment.
CUSTOM_APP_NAME_SIGNALS_RX = re.compile(
    r"\b(chatbot|chat-bot|gpt|assistant|wrapper)\b", re.IGNORECASE)
# Acronym detector: 3-5 uppercase letters as standalone token (e.g. LISA, C3PO,
# AAXI, ARMOR). Only valid as a "custom name" signal if not a known vendor token.
ACRONYM_RX = re.compile(r"\b([A-Z][A-Z0-9]{2,5})\b")
KNOWN_ACRONYMS_NOT_CUSTOM = {
    "AWS", "AI", "ML", "NIST", "OMB", "HHS", "DHS", "DOJ", "DOE", "DOI", "ED",
    "EPA", "FTC", "DOL", "USDA", "DOD", "VA", "NASA", "NSF", "GAO", "FBI",
    "CBP", "ICE", "USCIS", "TSA", "FEMA", "USCG", "USSS",
    "API", "PII", "HIPAA", "FOIA", "SaaS",
    "GPT",  # too generic
    "RAG", "LLM", "OCR", "NLP", "CNN", "RNN",
    "M365", "O365", "GCP", "USA", "DC", "USC", "CFR",
    "PDF", "CSV", "JSON",
}

# Phrases in development_type that signal in-house build
INHOUSE_PHRASES = [
    "developed in-house",
    "developed by agency personnel",
    "in-house resources",  # ambiguous if "both contracting and in-house"
    "a) developed in-house",
    "agency-developed",
]

CONTRACTOR_ONLY_PHRASES = [
    "developed by contractor",
    "b) developed by contractor",
    "contracted out",
    "purchased",
    "off-the-shelf",
    "commercial off-the-shelf",
    "cots",
]

MIXED_PHRASES = [
    "both contracting and in-house",
    "c) developed with both",
]


def first_match(text, needles):
    if not text:
        return None
    t = text.lower()
    for n in needles:
        if n in t:
            return n
    return None


def classify(row, db_row):
    """Return (decision, final_entry_type, reason_code, confidence, evidence_quote, notes)."""
    current = row["heuristic_label"] or "custom_system"
    vendor = (db_row.get("vendor_name") or "").strip()
    dev = (db_row.get("development_type") or "").strip()
    system_name = (db_row.get("system_name") or "").strip()
    use_name = (db_row.get("use_case_name") or "").strip()
    problem = (db_row.get("problem_statement") or "")[:600]
    outputs = (db_row.get("system_outputs") or "")[:300]
    training = (db_row.get("training_data_description") or "")[:300]
    is_cots = db_row.get("is_cots_commercial")
    cots_name = (db_row.get("cots_product_name") or "").strip()
    cots_vendor = (db_row.get("cots_vendor") or "").strip()

    blob = " ".join([use_name, system_name, problem, outputs, training,
                     vendor, cots_name, cots_vendor]).lower()

    vendor_norm = vendor.lower().strip()
    vendor_is_blank = vendor_norm in {"", "n/a", "na", "none", "not applicable"}

    # Multi-vendor / open-source signal: vendor field that lists multiple
    # parties (commas/semicolons) AND mentions open-source or python libs
    # is closer to bespoke research than to a single product deployment.
    multi_vendor_research = (
        not vendor_is_blank
        and ("open-source" in vendor_norm
             or "python libraries" in vendor_norm
             or "multiple" in vendor_norm)
        and ("," in vendor or ";" in vendor)
    )

    # Treat "Redacted ..." system_name as effectively absent. Also treat
    # registry-style identifiers (R&D User, CS-CAR-###, Multiple, the literal
    # vendor name itself, ATO/Cyber plan identifiers) as not-a-custom-name.
    sys_lower = system_name.lower()
    registry_patterns = [
        "r&d user", "redacted", "multiple", "cs-car", "ato",
        "cybersecurity system security plan",
        "cybersecurity cloud service",
        "interim authorization to test",
        "cybersecurity authorization", "system security plan",
    ]
    looks_like_registry = (
        any(p in sys_lower for p in registry_patterns)
        or sys_lower == vendor_norm
        or sys_lower in {"aws", "azure", "gcp", "google cloud platform"}
    )
    system_is_real = (
        bool(system_name)
        and not sys_lower.startswith("redacted")
        and not looks_like_registry
    )

    inhouse_hit = first_match(dev, INHOUSE_PHRASES)
    contractor_hit = first_match(dev, CONTRACTOR_ONLY_PHRASES)
    mixed_hit = first_match(dev, MIXED_PHRASES)

    # Identify vendor type
    product_vendor_hit = None
    sys_integrator_hit = None
    if not vendor_is_blank:
        product_vendor_hit = first_match(vendor, PRODUCT_VENDORS)
        sys_integrator_hit = first_match(vendor, SYSTEM_INTEGRATORS)

    # Also check narrative blob for explicit product references
    blob_vendor_hit = first_match(blob, [
        "microsoft 365 copilot", "m365 copilot", "copilot for microsoft",
        "azure openai", "azure ai", "amazon bedrock", "aws bedrock",
        "google gemini", "vertex ai", "openai api", "chatgpt enterprise",
        "github copilot", "servicenow now assist", "now assist",
        "palantir", "databricks", "snowflake cortex",
    ])

    llm_api_hit = None
    if not vendor_is_blank:
        llm_api_hit = first_match(vendor, LLM_API_VENDORS)
    if not llm_api_hit:
        llm_api_hit = first_match(blob, LLM_API_VENDORS)

    # Detect custom-app signals in use_case_name
    use_case_name_signal = bool(CUSTOM_APP_NAME_SIGNALS_RX.search(use_name))
    # Acronym in use_case_name not in the noise set
    custom_acronym = None
    for m in ACRONYM_RX.findall(use_name):
        if m not in KNOWN_ACRONYMS_NOT_CUSTOM:
            custom_acronym = m
            break
    has_custom_app_name = use_case_name_signal or bool(custom_acronym)

    # ---- Decision ladder ----

    # Rule 0: multi-vendor research with open-source signal => keep_current
    # (almost certainly bespoke_application research code, not a product deploy)
    if multi_vendor_research:
        return ("keep_current", current,
                "multi_vendor_research", "low",
                f"vendor='{vendor}' lists multiple parties + open source; "
                f"likely research wrapper, not a product deployment", "")

    # Rule A: explicit named commercial product in narrative
    if blob_vendor_hit:
        # Custom agency-built wrapper signals: real distinctive system_name OR
        # custom acronym/chatbot/assistant in use_case_name
        wrapper_signal = (
            (system_is_real and blob_vendor_hit not in sys_lower
             and not any(k in sys_lower for k in
                         ["copilot", "chatgpt", "bedrock", "vertex",
                          "now assist", "azure", "openai api"]))
            or has_custom_app_name
        )
        if wrapper_signal:
            sig = system_name if system_is_real else \
                  f"use_case_name='{use_name}'"
            if current == "bespoke_application":
                return ("keep_current", current,
                        "bespoke_wrap_on_vendor_api", "medium",
                        f"narrative names {blob_vendor_hit}; "
                        f"custom signal: {sig}", "")
            return ("reclassify", "bespoke_application",
                    "bespoke_wrap_on_vendor_api", "medium",
                    f"narrative names {blob_vendor_hit}; "
                    f"custom signal: {sig}", "")
        return ("reclassify", "product_deployment",
                "clear_vendor_named", "high",
                f"narrative names commercial product: {blob_vendor_hit}",
                "")

    # Rule B-1: vendor is a system integrator => typically bespoke_application
    # (contractor built a custom system for the agency)
    if sys_integrator_hit and not product_vendor_hit:
        # If LLM provider also named in narrative, definitely bespoke_application
        if llm_api_hit:
            if current == "bespoke_application":
                return ("keep_current", current,
                        "integrator_with_llm_api", "medium",
                        f"vendor='{vendor}' is integrator; LLM api "
                        f"({llm_api_hit}) in narrative", "")
            return ("reclassify", "bespoke_application",
                    "integrator_with_llm_api", "medium",
                    f"vendor='{vendor}' is integrator; LLM api "
                    f"({llm_api_hit}) in narrative", "")
        # No LLM api; integrator built something - likely bespoke_application
        if current == "bespoke_application":
            return ("keep_current", current,
                    "integrator_built", "low",
                    f"vendor='{vendor}' is system integrator", "")
        # If currently custom_system, lean to bespoke_application
        if current == "custom_system":
            return ("reclassify", "bespoke_application",
                    "integrator_built", "medium",
                    f"vendor='{vendor}' is integrator -> not in-house build",
                    "")
        return ("keep_current", current,
                "integrator_built", "low",
                f"vendor='{vendor}' is integrator", "")

    # Rule B-2: vendor is a known commercial product vendor
    if product_vendor_hit:
        # Bespoke signals: real system_name OR custom use_case_name AND
        # vendor is an LLM/cloud API provider
        bespoke_signal = (
            llm_api_hit
            and ((system_is_real and sys_lower != vendor_norm
                  and len(system_name) > 3)
                 or has_custom_app_name)
        )
        if bespoke_signal:
            sig = system_name if system_is_real else \
                  f"use_case_name='{use_name}'"
            if current == "bespoke_application":
                return ("keep_current", current,
                        "bespoke_wrap_on_vendor_api", "medium",
                        f"vendor='{vendor}' (LLM/cloud API); "
                        f"custom signal: {sig}", "")
            return ("reclassify", "bespoke_application",
                    "bespoke_wrap_on_vendor_api", "medium",
                    f"vendor='{vendor}' (LLM/cloud API); "
                    f"custom signal: {sig}", "")
        return ("reclassify", "product_deployment",
                "clear_vendor_named", "high",
                f"vendor_name='{vendor}' identifies a commercial product "
                f"vendor ({product_vendor_hit})",
                "")

    # Rule C: development_type explicitly in-house, vendor blank => custom_system
    if inhouse_hit and vendor_is_blank and not mixed_hit:
        if current == "custom_system":
            return ("keep_current", current,
                    "development_type_inhouse", "high",
                    f"development_type='{dev}'", "")
        return ("reclassify", "custom_system",
                "development_type_inhouse", "high",
                f"development_type='{dev}'; vendor blank", "")

    # Rule D: contractor-only build, no commercial vendor named => keep_current
    # (could be bespoke_application by a contractor or product_deployment of a
    #  niche product; without more evidence we don't reclassify)
    if contractor_hit and vendor_is_blank:
        return ("keep_current", current,
                "ambiguous_contractor_no_vendor", "low",
                f"development_type='{dev}'; vendor blank", "")

    # Rule E: vendor populated but unrecognized — likely a niche contractor
    # building a custom system for the agency. Without a brand we can identify,
    # treat as bespoke_application only if system has a named system identifier;
    # otherwise keep_current.
    if not vendor_is_blank and not (product_vendor_hit or sys_integrator_hit):
        # Heuristic: vendor + system_name + outputs implies a delivered product
        if system_name:
            return ("keep_current", current,
                    "vendor_unrecognized_with_system_name", "low",
                    f"vendor='{vendor}', system_name='{system_name}', "
                    f"insufficient signal to reclassify", "")
        return ("keep_current", current,
                "vendor_unrecognized_no_system_name", "low",
                f"vendor='{vendor}'; ambiguous", "")

    # Rule F: mixed development_type w/ no vendor — keep_current
    if mixed_hit:
        return ("keep_current", current,
                "mixed_dev_no_vendor", "low",
                f"development_type='{dev}'; ambiguous", "")

    # Rule G: blank dev + blank vendor — pure narrative, keep_current
    return ("keep_current", current,
            "no_clear_signals", "low",
            "vendor and development_type both blank/unhelpful", "")


def main():
    # Read input csv
    with open(INPUT_CSV, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    ids = [int(r["use_case_id"]) for r in rows]

    # Pull DB rows for all IDs
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    placeholders = ",".join("?" * len(ids))
    query = f"""
        SELECT u.id AS use_case_id, u.use_case_name, u.development_type,
               u.vendor_name, u.system_name, u.problem_statement,
               u.system_outputs, u.training_data_description,
               t.entry_type AS current_entry_type,
               t.is_cots_commercial, t.cots_product_name, t.cots_vendor
        FROM use_cases u
        LEFT JOIN use_case_tags t ON t.use_case_id = u.id
        WHERE u.id IN ({placeholders})
    """
    cur = conn.execute(query, ids)
    db_lookup = {row["use_case_id"]: dict(row) for row in cur.fetchall()}
    conn.close()

    # Output
    os.makedirs(OUT_DIR, exist_ok=True)
    out_fields = [
        "use_case_id", "agency", "use_case_name",
        "current_entry_type", "final_entry_type",
        "decision", "reason_code", "confidence",
        "search_attempted", "search_query",
        "evidence_quote", "notes",
    ]

    n_reclassify = 0
    n_keep = 0
    by_target = {}
    by_agency_reclass = {}

    with open(RESOLVED_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        w.writeheader()
        for r in rows:
            uid = int(r["use_case_id"])
            db_row = db_lookup.get(uid, {})
            current = db_row.get("current_entry_type") or r["heuristic_label"]
            decision, final, reason, conf, evidence, notes = classify(r, db_row)
            # Reconcile decision with actual DB state: if final == current,
            # this is keep_current regardless of what the rule fired.
            if final == current and decision == "reclassify":
                decision = "keep_current"
                if not notes:
                    notes = "rule fired but already matched current entry_type"
            if decision == "reclassify":
                n_reclassify += 1
                by_target[final] = by_target.get(final, 0) + 1
                by_agency_reclass[r["agency"]] = (
                    by_agency_reclass.get(r["agency"], 0) + 1)
            else:
                n_keep += 1
            w.writerow({
                "use_case_id": uid,
                "agency": r["agency"],
                "use_case_name": r["use_case_name"],
                "current_entry_type": current,
                "final_entry_type": final,
                "decision": decision,
                "reason_code": reason,
                "confidence": conf,
                "search_attempted": "no",
                "search_query": "",
                "evidence_quote": evidence,
                "notes": notes,
            })

    # Empty searches.csv (we did no live web searches; record schema only)
    with open(SEARCHES_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["use_case_id", "system_name", "vendor_name",
                    "search_query", "result_summary", "outcome"])

    print(f"Wrote {RESOLVED_CSV}")
    print(f"reclassify={n_reclassify}, keep_current={n_keep}, total={len(rows)}")
    print("By target entry_type:", by_target)
    print("Top reclassify agencies:",
          sorted(by_agency_reclass.items(), key=lambda x: -x[1])[:8])


if __name__ == "__main__":
    main()
