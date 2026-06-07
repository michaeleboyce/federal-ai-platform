"""Wave 2a QA pass for renamed / split lineage pairs.

Compares Wave-1 2024 tags vs the existing 2025 IFP tags. Emits a row only
when the pair is divergent enough to warrant Wave-3 review.

Output: audit/retag/2024-tagging/wave2a/renamed_split.csv
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IN_PATH = ROOT / "wave2a_inputs" / "renamed_split.csv"
OUT_PATH = ROOT / "wave2a" / "renamed_split.csv"

SCOPE_TIER = {
    "pilot": 0,
    "office": 1,
    "bureau": 2,
    "department": 3,
    "enterprise_wide": 4,
}

# Sophistication "ladders" — coarse families. nlp_specific is intentionally
# grouped with classical (it's often classical-NLP per OMB guidance), and
# coding_assistant with the LLM family. Cross-family means a real capability
# class change; within-family is calibration noise we don't surface.
SOPH_GROUPS = {
    "general_llm": "llm",
    "agentic": "llm",
    "coding_assistant": "llm",
    "nlp_specific": "classical",
    "computer_vision": "cv",
    "classical_ml": "classical",
    "predictive_analytics": "classical",
}


def scope_tier(s: str) -> int | None:
    return SCOPE_TIER.get((s or "").strip().lower())


def scope_shift(a: str, b: str) -> int:
    ta, tb = scope_tier(a), scope_tier(b)
    if ta is None or tb is None:
        return 0
    return abs(ta - tb)


def soph_family(s: str) -> str:
    return SOPH_GROUPS.get((s or "").strip().lower(), "")


def normalize(v: str) -> str:
    return (v or "").strip().lower()


def flag_row(r: dict) -> dict | None:
    flags = []
    notes = []
    confidence = "medium"

    g24 = normalize(r["is_generative_ai_2024"])
    g25 = normalize(r["is_generative_ai_2025"])
    e24 = normalize(r["entry_type_2024"])
    e25 = normalize(r["entry_type_2025"])
    s24 = normalize(r["ai_sophistication_2024"])
    s25 = normalize(r["ai_sophistication_2025"])
    sc24 = normalize(r["deployment_scope_2024"])
    sc25 = normalize(r["deployment_scope_2025"])
    llm24 = normalize(r["is_general_llm_access_2024"])
    llm25 = normalize(r["is_general_llm_access_2025"])

    name24 = (r.get("name_2024") or "").lower()
    name25 = (r.get("name_2025") or "").lower()
    text_blob = " ".join([
        r.get("purpose_benefits", "") or "",
        r.get("outputs", "") or "",
        r.get("problem_statement_2025", "") or "",
        r.get("expected_benefits_2025", "") or "",
        r.get("system_outputs_2025", "") or "",
    ]).lower()

    lineage = r["lineage_status"]

    # ---- material_divergence checks -----------------------------------------
    # 1. is_generative_ai mismatch.
    if g24 != g25:
        flags.append("material_divergence")
        notes.append(f"is_generative_ai 2024={g24} vs 2025={g25}")

    # 2. ai_sophistication mismatch — flag only LLM ↔ non-LLM swaps, which
    # are the most material capability-class changes (an LLM/agentic system
    # is qualitatively different from a classical/CV one). Swaps WITHIN the
    # non-LLM space (e.g., classical_ml↔computer_vision) are usually a
    # modality re-tag, not a capability change, and we don't surface them.
    if s24 != s25:
        f24, f25 = soph_family(s24), soph_family(s25)
        if f24 and f25 and f24 != f25 and (f24 == "llm" or f25 == "llm"):
            flags.append("material_divergence")
            notes.append(f"ai_sophistication LLM-class shift {s24}→{s25}")
        elif f24 == "llm" and f25 == "llm" and {s24, s25} == {"general_llm", "agentic"}:
            flags.append("material_divergence")
            notes.append(f"ai_sophistication {s24}→{s25} (LLM→agentic uplift)")

    # 3. entry_type mismatch — only flag the crispest boundary:
    # generic_use_pattern↔anything-else is real (umbrella vs concrete).
    # Other entry_type swaps (custom_system↔product_deployment) are very
    # often calibration noise / disclosure tweaks; we don't surface them
    # as material_divergence in renamed/split QA.
    if e24 != e25 and e24 and e25:
        if e24 == "generic_use_pattern" or e25 == "generic_use_pattern":
            flags.append("material_divergence")
            notes.append(f"entry_type {e24}→{e25}")

    # 4. deployment_scope shift by 2+ tiers.
    if scope_shift(sc24, sc25) >= 2:
        flags.append("material_divergence")
        notes.append(f"scope {sc24}→{sc25} (≥2 tiers)")

    # ---- drift_legitimate -----------------------------------------------------
    # Split umbrella → specific product is almost always drift_legitimate.
    if lineage == "split":
        if e24 == "generic_use_pattern" or "copilot" in name24 or "general" in name24:
            flags.append("drift_legitimate")
            notes.append("split: 2024 umbrella → 2025 specific deployment")

    # Pilot/office → bureau+ = legitimate rollout. Only attach drift_legitimate
    # when the scope shift is ≥2 tiers (otherwise it isn't notable enough to
    # surface for Wave-3 reconciliation).
    if scope_shift(sc24, sc25) >= 2 and scope_tier(sc24) is not None and scope_tier(sc25) is not None:
        if scope_tier(sc25) > scope_tier(sc24) and sc24 in {"pilot", "office"} and sc25 in {"bureau", "department", "enterprise_wide"}:
            flags.append("drift_legitimate")
            notes.append(f"scope rollout {sc24}→{sc25}")

    # general_llm → agentic transition often legitimate maturity.
    if s24 == "general_llm" and s25 == "agentic":
        flags.append("drift_legitimate")
        notes.append("general_llm→agentic = maturity uplift")

    # ---- tagging_error_2024 ---------------------------------------------------
    # Wave 1 said is_generative_ai=0 but text strongly suggests genAI and 2025
    # confirms it.
    if g24 == "0" and g25 == "1":
        gen_signals = [
            "generative ai", "generative-ai", "llm", "large language model",
            "chatgpt", "claude", "gemini", "copilot", "openai", "anthropic",
            "synthetic data", "text generation", "summariz", "chatbot",
        ]
        if any(sig in text_blob for sig in gen_signals):
            flags.append("tagging_error_2024")
            notes.append("2024 missed generative AI signals present in narrative")

    # Wave 1 picked classical_ml/predictive_analytics for what is clearly LLM.
    if s24 in {"classical_ml", "predictive_analytics"} and s25 in {"general_llm", "agentic", "nlp_specific"}:
        gen_signals = ["llm", "large language", "chatgpt", "claude", "gpt-", "copilot", "generative"]
        if any(sig in text_blob for sig in gen_signals) or llm25 == "1":
            flags.append("tagging_error_2024")
            notes.append(f"2024 tagged {s24}; narrative + 2025 indicate LLM-class")

    # ---- tagging_error_2025 ---------------------------------------------------
    # Wave 1 found gen-AI-zero with no LLM signal but 2025 marks general_llm=1
    # and the narrative is clearly a non-LLM classical system (e.g., CV-only).
    if llm25 == "1" and g24 == "0":
        cv_signals = ["facial recogn", "image classif", "computer vision", "object detection", "satellite imagery"]
        if any(sig in text_blob for sig in cv_signals) and "llm" not in text_blob and "chat" not in text_blob:
            flags.append("tagging_error_2025")
            notes.append("2025 marks general_llm but narrative is computer-vision")

    # ---- dedupe + finalize ---------------------------------------------------
    if not flags:
        return None
    flags = sorted(set(flags))

    # Confidence heuristic.
    if "tagging_error_2024" in flags or "tagging_error_2025" in flags:
        confidence = "medium"
    elif len(flags) >= 2:
        confidence = "high"
    else:
        confidence = "medium"

    out = {
        "use_case_id_2024": r["uc_2024_id"],
        "tagged_by_agent": "wave2a-renamed-split",
        "quality_flags_json": json.dumps(flags),
        "reasoning": "; ".join(notes)[:500],
        "confidence": confidence,
    }

    # Carry corrected tags when tagging_error_2024 — propose 2025 values.
    if "tagging_error_2024" in flags:
        out["entry_type"] = r["entry_type_2025"]
        out["is_generative_ai"] = r["is_generative_ai_2025"]
        out["ai_sophistication"] = r["ai_sophistication_2025"]
        out["deployment_scope"] = r["deployment_scope_2024"]  # scope can legitimately differ
        out["is_general_llm_access"] = r["is_general_llm_access_2025"]
        out["is_coding_tool"] = r["is_coding_tool_2025"]
        out["tool_product_name"] = r["tool_product_name_2025"]
        out["tool_vendor"] = r["tool_vendor_2025"]

    return out


def main():
    with IN_PATH.open() as f:
        rows = list(csv.DictReader(f))

    flagged = []
    for r in rows:
        out = flag_row(r)
        if out is not None:
            flagged.append(out)

    # Build column union.
    base_cols = ["use_case_id_2024", "tagged_by_agent", "quality_flags_json", "reasoning", "confidence"]
    extra_cols = [
        "entry_type", "is_generative_ai", "ai_sophistication", "deployment_scope",
        "is_general_llm_access", "is_coding_tool", "tool_product_name", "tool_vendor",
    ]
    cols = base_cols + extra_cols

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in flagged:
            w.writerow({c: row.get(c, "") for c in cols})

    # Quick breakdown for the report.
    from collections import Counter
    bk = Counter()
    for row in flagged:
        for fl in json.loads(row["quality_flags_json"]):
            bk[fl] += 1
    print(f"total input: {len(rows)}  flagged: {len(flagged)}")
    print("flag breakdown:", dict(bk))


if __name__ == "__main__":
    main()
