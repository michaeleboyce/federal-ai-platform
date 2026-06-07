"""Wave 2b QA pass: scan 710 retired_2024 use cases and flag any whose
Wave-1 tags are internally inconsistent, lifecycle-mismatched, or whose
named vendor/product lacks supporting evidence.

Input:  audit/retag/2024-tagging/wave2b_inputs/retired.csv
Output: audit/retag/2024-tagging/wave2b/retired.csv

Only rows with at least one flag are emitted.
"""
from __future__ import annotations

import csv
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_PATH = os.path.join(ROOT, "audit/retag/2024-tagging/wave2b_inputs/retired.csv")
OUT_PATH = os.path.join(ROOT, "audit/retag/2024-tagging/wave2b/retired.csv")

# -------- helpers --------

LLM_TOKENS = [
    r"\bllm\b",
    r"\blarge language model",
    r"\bchatgpt\b",
    r"\bgpt-?[34]",
    r"\bgpt-?4o",
    r"\bgenerative ai\b",
    r"\bgenerative model",
    r"\bgenai\b",
    r"\bfoundation model",
    r"\bchatbot\b",
    r"\brag pipeline\b",
    r"\bretrieval[- ]augmented",
    r"\bfine[- ]tun",
    r"\bgemini\b",
    r"\bclaude\b",
    r"\bcopilot\b",
    r"\bbedrock\b",
    r"\btransformer\b",
    r"\bllama\b",
    r"\bmistral\b",
    r"\bhhsgpt\b",
]

VENDOR_NAMES = [
    "microsoft", "copilot", "openai", "chatgpt", "anthropic", "claude",
    "google", "gemini", "vertex", "github", "aws", "bedrock", "sagemaker",
    "azure", "amazon", "meta", "llama", "mistral", "hugging", "cohere",
    "nuance", "dragon", "otter", "zoom", "adobe", "grammarly", "salesforce",
    "oracle", "sap", "servicenow", "ibm", "watson", "palantir", "databricks",
    "snowflake", "splunk", "tableau", "power bi", "alteryx", "axon",
    "lexisnexis", "thomson reuters", "esri", "autodesk", "abbyy",
]


def narrative_text(r: dict) -> str:
    return " ".join(
        [
            r.get("use_case_name", "") or "",
            r.get("purpose_benefits", "") or "",
            r.get("outputs", "") or "",
            r.get("commercial_ai", "") or "",
            r.get("dev_method", "") or "",
        ]
    ).lower()


def has_llm_signal(text: str) -> bool:
    return any(re.search(p, text) for p in LLM_TOKENS)


def names_a_vendor(text: str, tool_name: str | None) -> bool:
    if tool_name:
        if tool_name.lower() in text:
            return True
    return any(v in text for v in VENDOR_NAMES)


def main() -> int:
    with open(IN_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    out_rows = []

    for r in rows:
        flags = []
        notes = []
        corrections = {}

        ucid = r["uc_2024_id"]
        agency = r["agency_abbreviation"]
        name = r["use_case_name"]
        soph = r.get("ai_sophistication_2024", "")
        is_gen = r.get("is_generative_ai_2024", "")
        entry_type = r.get("entry_type_2024", "")
        scope = r.get("deployment_scope_2024", "")
        stage = r.get("dev_stage", "")
        tpn = (r.get("tool_product_name_2024", "") or "").strip()
        tvn = (r.get("tool_vendor_2024", "") or "").strip()
        comm_ai = (r.get("commercial_ai", "") or "").strip()
        is_cots = r.get("is_cots_commercial_2024", "")
        ms_cop = r.get("is_microsoft_copilot_2024", "") == "1"
        is_ew = r.get("is_enterprise_wide_2024", "") == "1"
        narr = narrative_text(r)

        # 1. internal_inconsistency: genai=1 but sophistication is non-generative
        if is_gen == "1" and soph in ("classical_ml", "predictive_analytics",
                                       "computer_vision", "nlp_specific"):
            flags.append("internal_inconsistency")
            notes.append(
                f"is_generative_ai=1 but ai_sophistication='{soph}' (non-generative class)"
            )
            # If narrative does NOT actually describe a generative model, the
            # right correction is is_generative_ai=0 (keep sophistication).
            if not has_llm_signal(narr):
                corrections["is_generative_ai"] = "0"
            else:
                # narrative does indicate LLM/generative — fix sophistication
                corrections["ai_sophistication"] = "general_llm"

        # 2. internal_inconsistency: genai=0 but sophistication=general_llm/coding/agentic
        if is_gen == "0" and soph in ("general_llm", "coding_assistant", "agentic"):
            flags.append("internal_inconsistency")
            notes.append(
                f"is_generative_ai=0 but ai_sophistication='{soph}' (a generative class)"
            )
            corrections["is_generative_ai"] = "1"

        # 3. internal_inconsistency: ms_copilot=1 but is_cots_commercial=0
        if ms_cop and is_cots == "0":
            flags.append("internal_inconsistency")
            notes.append("is_microsoft_copilot=1 but is_cots_commercial=0")
            corrections["is_cots_commercial"] = "1"

        # 4. internal_inconsistency: is_general_llm_access=1 but is_generative_ai=0
        if r.get("is_general_llm_access_2024", "") == "1" and is_gen == "0":
            flags.append("internal_inconsistency")
            notes.append("is_general_llm_access=1 but is_generative_ai=0")
            corrections["is_generative_ai"] = "1"

        # 5. internal_inconsistency: is_coding_tool=1 but is_generative_ai=0
        if r.get("is_coding_tool_2024", "") == "1" and is_gen == "0":
            flags.append("internal_inconsistency")
            notes.append("is_coding_tool=1 but is_generative_ai=0")
            corrections["is_generative_ai"] = "1"

        # 6. internal_inconsistency: is_enterprise_wide=1 but scope != enterprise_wide
        if is_ew and scope != "enterprise_wide":
            flags.append("internal_inconsistency")
            notes.append(
                f"is_enterprise_wide=1 but deployment_scope='{scope}'"
            )

        # 7. internal_inconsistency: product_deployment but empty tool_product_name
        if entry_type == "product_deployment" and not tpn:
            flags.append("internal_inconsistency")
            notes.append(
                "entry_type=product_deployment but tool_product_name is empty"
            )
            # Suggest a corrected entry_type only if the narrative also doesn't
            # name an actual product (otherwise the right fix is to add tpn).
            comm_low = comm_ai.lower()
            if not comm_low or "none of the above" in comm_low:
                corrections["entry_type"] = "custom_system" if r.get(
                    "dev_method", "").lower().startswith("developed in-house"
                ) else "bespoke_application"

        # 8. tool_vendor_unverified: Wave 1 named a tool but commercial_ai=
        # "None of the above" and narrative names no vendor.
        if tpn:
            comm_low = comm_ai.lower()
            if (not comm_low or "none of the above" in comm_low) and not names_a_vendor(narr, tpn):
                flags.append("tool_vendor_unverified")
                notes.append(
                    f"tool_product_name='{tpn}' but commercial_ai='{comm_ai}' and narrative names no vendor"
                )
                # Clear the unverifiable vendor fields
                corrections["tool_product_name"] = ""
                corrections["tool_vendor"] = ""
                corrections["is_cots_commercial"] = "0"

        # 9. misclassified_lifecycle: dev_stage=O&M but scope=pilot — a
        # production system can't simultaneously be a pilot. retired_2024
        # already says they dropped it; this combo means Wave 1 mis-scoped.
        if stage == "Operation and Maintenance" and scope == "pilot":
            flags.append("misclassified_lifecycle")
            notes.append(
                "dev_stage='Operation and Maintenance' but deployment_scope='pilot' — silently dropped live system"
            )
            corrections["deployment_scope"] = "office"

        # 10. misclassified_lifecycle: O&M (live system) tagged classical_ml
        # but narrative explicitly describes an LLM / generative system →
        # Wave 1 missed that this was a deployed-then-retired LLM use.
        if stage == "Operation and Maintenance" and soph in (
            "classical_ml", "predictive_analytics"
        ):
            if has_llm_signal(narr) and is_gen == "0":
                flags.append("misclassified_lifecycle")
                notes.append(
                    f"O&M with sophistication='{soph}' but narrative describes an LLM/generative system"
                )
                corrections["is_generative_ai"] = "1"
                corrections["ai_sophistication"] = "general_llm"

        # 11. misclassified_lifecycle: Implementation and Assessment + pilot
        # scope is internally OK, but I&A + enterprise_wide is suspicious —
        # generally agencies don't list a not-yet-assessed system as fully
        # rolled-out. Flag only if also retired.
        if stage == "Implementation and Assessment" and scope == "enterprise_wide":
            flags.append("misclassified_lifecycle")
            notes.append(
                "dev_stage='Implementation and Assessment' but deployment_scope='enterprise_wide' — implausible combo on a dropped system"
            )

        # 12. misclassified_lifecycle: pre-deployment stages (Initiated,
        # Acquisition and/or Development, Planned) but tagged with broad
        # rollout scope (enterprise_wide / department). A system that was
        # never operationalized can't have been rolled out broadly.
        if stage in ("Initiated", "Acquisition and/or Development", "Planned") and scope in (
            "enterprise_wide", "department"
        ):
            flags.append("misclassified_lifecycle")
            notes.append(
                f"dev_stage='{stage}' (pre-deployment) but deployment_scope='{scope}' — pre-deployment system can't be broadly rolled out"
            )
            corrections["deployment_scope"] = "bureau" if scope == "department" else "bureau"

        # 13. misclassified_lifecycle: dev_stage='Retired' (agency-acknowledged
        # retirement) but Wave 1 tagged scope=enterprise_wide. The combination
        # is plausible (a former enterprise system did get pulled), but flag
        # if the narrative is short/thin so the call should be re-verified.
        if stage == "Retired" and scope == "enterprise_wide":
            narr_len = len((r.get("purpose_benefits") or "") + (r.get("outputs") or ""))
            if narr_len < 200:
                flags.append("misclassified_lifecycle")
                notes.append(
                    "dev_stage='Retired' and scope='enterprise_wide' on a thin narrative — verify scope"
                )

        if not flags:
            continue

        # confidence: high when the flag is structural (impossible combo);
        # medium when narrative-judgment based; low when only weakly inferred.
        confidence = "high"
        if "tool_vendor_unverified" in flags or "misclassified_lifecycle" in flags:
            confidence = "medium"
        # If the only flag is internal_inconsistency from category 7 (PD with
        # empty tool name) and we don't have a clean correction, soften.
        if flags == ["internal_inconsistency"] and "entry_type=product_deployment" in " ".join(notes) and "entry_type" not in corrections:
            confidence = "low"

        out = {
            "use_case_id_2024": ucid,
            "tagged_by_agent": "wave2b-retired",
            "quality_flags_json": json.dumps(sorted(set(flags))),
            "reasoning": "; ".join(notes),
            "confidence": confidence,
        }
        # carry corrected tag fields when we proposed any
        for k, v in corrections.items():
            out[k] = v

        out_rows.append(out)

    # union of all keys, with the required ones first
    required_cols = [
        "use_case_id_2024",
        "tagged_by_agent",
        "quality_flags_json",
        "reasoning",
        "confidence",
    ]
    extra_cols = [
        "entry_type",
        "is_generative_ai",
        "ai_sophistication",
        "deployment_scope",
        "is_general_llm_access",
        "is_coding_tool",
        "is_cots_commercial",
        "tool_product_name",
        "tool_vendor",
    ]
    fieldnames = required_cols + extra_cols

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in out_rows:
            w.writerow(row)

    # quick summary
    from collections import Counter
    flag_counter = Counter()
    for r in out_rows:
        for fl in json.loads(r["quality_flags_json"]):
            flag_counter[fl] += 1
    print(f"Total flagged: {len(out_rows)} / {len(rows)}")
    for fl, n in flag_counter.most_common():
        print(f"  {fl}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
