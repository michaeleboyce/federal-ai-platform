"""Wave 3 reconciliation for partition P2.

Per WAVE3_RUBRIC.md decision rules:

- drift_legitimate (often with material_divergence): keep the 2024 tag — the
  agency genuinely changed posture between cycles.
- material_divergence alone: choose whichever side the 2024 narrative
  supports.
- tagging_error_2024: adopt the proposed correction when present and
  consistent with the narrative.
- tagging_error_2025: keep the Wave 1 2024 tag (2025 row is fixed elsewhere).
- internal_inconsistency: re-derive a consistent tag set from narrative.
- misclassified_lifecycle: realign deployment_scope with dev_stage.
- tool_vendor_unverified: clear vendor fields unless narrative supports.

Output: audit/retag/2024-tagging/wave3/P2.csv (211 rows).
"""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


INPUT = Path("audit/retag/2024-tagging/wave3_inputs/P2.csv")
OUTPUT = Path("audit/retag/2024-tagging/wave3/P2.csv")

OUTPUT_COLS = [
    "use_case_id_2024",
    "tagged_by_agent",
    "confidence",
    "reasoning",
    "entry_type",
    "is_generative_ai",
    "ai_sophistication",
    "deployment_scope",
    "scope_detail",
    "is_enterprise_wide",
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
    "architecture_type",
    "use_type",
    "is_public_facing",
]

WAVE1_FIELDS = [
    "entry_type",
    "is_generative_ai",
    "ai_sophistication",
    "deployment_scope",
    "scope_detail",
    "is_enterprise_wide",
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
    "architecture_type",
    "use_type",
    "is_public_facing",
]

# Fields the Wave-2 agent can override on a per-row basis. Booleans + a few
# string fields. (No `proposed_ai_sophistication`-or-equivalents we haven't
# already listed.)
PROPOSED_FIELDS = {
    "entry_type": "proposed_entry_type",
    "is_generative_ai": "proposed_is_generative_ai",
    "ai_sophistication": "proposed_ai_sophistication",
    "deployment_scope": "proposed_deployment_scope",
    "scope_detail": "proposed_scope_detail",
    "is_enterprise_wide": "proposed_is_enterprise_wide",
    "is_general_llm_access": "proposed_is_general_llm_access",
    "is_coding_tool": "proposed_is_coding_tool",
    "is_cots_commercial": "proposed_is_cots_commercial",
    "tool_product_name": "proposed_tool_product_name",
    "tool_vendor": "proposed_tool_vendor",
    "is_microsoft_copilot": "proposed_is_microsoft_copilot",
    "is_openai": "proposed_is_openai",
    "is_anthropic": "proposed_is_anthropic",
    "is_google": "proposed_is_google",
    "is_github_copilot": "proposed_is_github_copilot",
    "is_aws_ai": "proposed_is_aws_ai",
    "architecture_type": "proposed_architecture_type",
    "use_type": "proposed_use_type",
    "is_public_facing": "proposed_is_public_facing",
}


def w1(row: dict, field: str) -> str:
    return (row.get(f"wave1_{field}") or "").strip()


def w25(row: dict, field: str) -> str:
    return (row.get(f"{field}_2025") or "").strip()


def proposed(row: dict, field: str) -> str:
    col = PROPOSED_FIELDS.get(field)
    if not col:
        return ""
    return (row.get(col) or "").strip()


def narrative(row: dict) -> str:
    return " ".join(
        (row.get(k) or "")
        for k in (
            "use_case_name",
            "purpose_benefits",
            "outputs",
            "commercial_ai",
            "dev_method",
            "dev_stage",
        )
    ).lower()


def has_generative_signal(text: str) -> bool:
    keys = [
        "generative",
        "llm",
        "large language model",
        "gpt",
        "chatgpt",
        "copilot",
        "claude",
        "gemini",
        "bedrock",
        "azure openai",
        "openai",
        "anthropic",
        "rag",
        "retrieval augmented",
        "retrieval-augmented",
        "transformer",
        "chatbot",
        "conversational ai",
        "summariz",
        "natural language generation",
        "foundation model",
        "agentic",
        "prompt",
    ]
    return any(k in text for k in keys)


def lifecycle_in_production(stage: str) -> bool:
    s = (stage or "").lower()
    return any(
        k in s
        for k in (
            "operation",
            "production",
            "deployed",
            "implemented",
            "operational",
            "released",
        )
    )


def lifecycle_pilot(stage: str) -> bool:
    s = (stage or "").lower()
    return any(k in s for k in ("pilot", "prototype", "proof of concept", "poc", "test"))


def reconcile(row: dict) -> dict:
    try:
        flags = json.loads(row.get("w2_flags_json") or "[]")
    except json.JSONDecodeError:
        flags = []
    flagset = set(flags)
    nar = narrative(row)
    out = {
        "use_case_id_2024": row["use_case_id_2024"],
        "tagged_by_agent": "wave3-P2",
    }

    # Default: start from Wave 1 tag, then mutate based on rules.
    tag: dict[str, str] = {f: w1(row, f) for f in WAVE1_FIELDS}

    confidence = "medium"
    reasons: list[str] = []

    drift = "drift_legitimate" in flagset
    div = "material_divergence" in flagset
    err24 = "tagging_error_2024" in flagset
    err25 = "tagging_error_2025" in flagset
    internal = "internal_inconsistency" in flagset
    lifecycle = "misclassified_lifecycle" in flagset
    vendor_unverified = "tool_vendor_unverified" in flagset

    # ------------------------------------------------------------------
    # tagging_error_2024 — accept proposed corrections when offered
    # ------------------------------------------------------------------
    if err24:
        applied = []
        for field, pcol in PROPOSED_FIELDS.items():
            pval = (row.get(pcol) or "").strip()
            if pval:
                tag[field] = pval
                applied.append(field)
        if applied:
            reasons.append(
                "tagging_error_2024 — adopted proposed correction for "
                + ",".join(applied)
            )
            confidence = "high"
        else:
            reasons.append("tagging_error_2024 — kept Wave 1 (no proposed override)")

    # ------------------------------------------------------------------
    # drift_legitimate — keep 2024 tag (the rubric's headline rule)
    # ------------------------------------------------------------------
    if drift:
        # Do not pull from 2025. Wave 1 reflects the 2024 reality.
        reasons.append("drift_legitimate — kept 2024 tag as filed")
        confidence = "high"

    # ------------------------------------------------------------------
    # material_divergence (without drift, without an err24 override)
    # ------------------------------------------------------------------
    if div and not drift and not err24:
        # Adopt 2025 reading only if the 2024 narrative actually supports
        # it. Headline check: is_generative_ai.
        if w1(row, "is_generative_ai") != w25(row, "is_generative_ai"):
            if has_generative_signal(nar):
                # 2024 narrative talks about generative AI → 2025 reading
                # of genAI=1 is correct.
                for field in (
                    "is_generative_ai",
                    "ai_sophistication",
                    "architecture_type",
                    "entry_type",
                ):
                    if w25(row, field):
                        tag[field] = w25(row, field)
                reasons.append(
                    "material_divergence — 2024 narrative shows generative AI signals, adopted 2025 reading"
                )
                confidence = "medium"
            else:
                reasons.append(
                    "material_divergence — 2024 narrative shows no generative AI signals, kept Wave 1"
                )
                confidence = "medium"
        else:
            # divergence is on a non-genAI axis — keep Wave 1 unless
            # proposed correction exists (handled above)
            reasons.append("material_divergence — kept Wave 1 (no proposal, genAI agrees)")

    # ------------------------------------------------------------------
    # tagging_error_2025 — Wave 1 was right; 2025 is wrong (fixed elsewhere)
    # ------------------------------------------------------------------
    if err25:
        reasons.append("tagging_error_2025 — kept Wave 1 (2025 fix is out of scope)")
        confidence = "high"

    # ------------------------------------------------------------------
    # internal_inconsistency — try to derive a consistent tag set
    # ------------------------------------------------------------------
    if internal:
        # Most common case: is_generative_ai vs ai_sophistication mismatch.
        gen = tag.get("is_generative_ai", "")
        soph = (tag.get("ai_sophistication") or "").lower()
        gen_sophs = {"general_llm", "agentic", "rag", "fine_tuned_llm"}
        if gen == "1" and soph and soph not in gen_sophs and soph != "nlp_specific":
            # Narrative-driven decision: if narrative shows LLM signals,
            # promote sophistication; else demote is_generative_ai.
            if has_generative_signal(nar):
                tag["ai_sophistication"] = "general_llm"
                reasons.append(
                    "internal_inconsistency — promoted ai_sophistication to general_llm to match is_generative_ai=1"
                )
            else:
                tag["is_generative_ai"] = "0"
                reasons.append(
                    "internal_inconsistency — set is_generative_ai=0 (narrative lacks LLM signals)"
                )
            confidence = "medium"
        elif gen == "0" and soph in gen_sophs:
            # Reverse case.
            if has_generative_signal(nar):
                tag["is_generative_ai"] = "1"
                reasons.append(
                    "internal_inconsistency — set is_generative_ai=1 to match generative sophistication"
                )
            else:
                tag["ai_sophistication"] = "classical_ml"
                reasons.append(
                    "internal_inconsistency — demoted ai_sophistication to classical_ml (narrative lacks LLM signals)"
                )
            confidence = "medium"
        else:
            # Generic case: prefer 2025 reading when it exists
            for field in ("is_generative_ai", "ai_sophistication", "architecture_type"):
                if w25(row, field):
                    tag[field] = w25(row, field)
            reasons.append(
                "internal_inconsistency — adopted 2025 reading on the inconsistent fields"
            )
            confidence = "medium"

    # ------------------------------------------------------------------
    # misclassified_lifecycle — align deployment_scope with dev_stage
    # ------------------------------------------------------------------
    if lifecycle:
        stage = row.get("dev_stage") or ""
        scope = tag.get("deployment_scope", "")
        if lifecycle_pilot(stage) and scope in ("bureau", "enterprise_wide", "agency_wide"):
            tag["deployment_scope"] = "pilot"
            reasons.append(
                f"misclassified_lifecycle — narrative dev_stage='{stage}' indicates pilot; corrected scope"
            )
            confidence = "medium"
        elif lifecycle_in_production(stage) and scope in ("pilot", "prototype", ""):
            # If retired_2024 + in production = silently-dropped live system.
            if (row.get("lineage_status") or "") == "retired_2024":
                tag["use_type"] = tag.get("use_type") or "mission_critical"
                tag["deployment_scope"] = scope if scope and scope != "pilot" else "bureau"
                reasons.append(
                    "misclassified_lifecycle — silently-dropped deployed system (retired_2024 + Operation/Maintenance); marked mission_critical"
                )
                confidence = "high"
            else:
                tag["deployment_scope"] = "bureau"
                reasons.append(
                    f"misclassified_lifecycle — narrative dev_stage='{stage}' is in-production; raised scope from pilot"
                )
                confidence = "medium"
        else:
            reasons.append("misclassified_lifecycle — kept Wave 1 (no clean dev_stage signal)")

    # ------------------------------------------------------------------
    # tool_vendor_unverified — clear vendor fields unless narrative supports
    # ------------------------------------------------------------------
    if vendor_unverified:
        prod = (tag.get("tool_product_name") or "").lower()
        vend = (tag.get("tool_vendor") or "").lower()
        keep_prod = bool(prod) and prod in nar
        keep_vend = bool(vend) and vend in nar
        if not keep_prod:
            tag["tool_product_name"] = ""
        if not keep_vend:
            tag["tool_vendor"] = ""
        reasons.append(
            "tool_vendor_unverified — cleared vendor/product fields not supported by narrative"
        )
        confidence = "high"

    # If we somehow got no specific rule (shouldn't happen — every row has a flag)
    if not reasons:
        reasons.append("kept Wave 1 (no actionable flag)")

    out["confidence"] = confidence
    out["reasoning"] = "; ".join(reasons)
    for field in WAVE1_FIELDS:
        out[field] = tag.get(field, "")
    return out


def main() -> None:
    with INPUT.open(newline="") as f:
        rows = list(csv.DictReader(f))

    outputs = [reconcile(r) for r in rows]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLS)
        writer.writeheader()
        for row in outputs:
            writer.writerow({k: row.get(k, "") for k in OUTPUT_COLS})

    assert len(outputs) == len(rows) == 211, f"expected 211, got {len(outputs)}"
    print(f"wrote {len(outputs)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
