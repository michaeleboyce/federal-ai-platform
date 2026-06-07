"""Wave 2a continued QA: compare 2024 Wave-1 tags vs 2025 IFP tags for 1,139
matched 'continued' lineage pairs. Emit a row only when at least one
divergence flag applies.

Flags emitted:
  - material_divergence: differ on is_generative_ai, ai_sophistication,
    entry_type, OR deployment_scope shifts by more than one tier
    (bureau<->office NOT material; bureau<->enterprise_wide IS).
  - drift_legitimate: scope expanded from a small pilot/team/office to
    bureau or enterprise_wide (paired with material_divergence).
  - tagging_error_2024: re-reading the 2024 narrative reveals Wave 1
    miscoded a field.
  - tagging_error_2025: the 2025 row's tag is the wrong one given the
    matched narrative; 2024 looks correct.
"""

import csv
import json
import os

INPUT = "audit/retag/2024-tagging/wave2a_inputs/continued.csv"
OUTPUT = "audit/retag/2024-tagging/wave2a/continued.csv"

# entry_type equivalence: Wave-1 sometimes used legacy 'custom_system' /
# 'bespoke_application' interchangeably. Per the OMB schema:
#   custom_system / bespoke_application — both refer to agency-developed
#   bespoke applications. The 2025 IFP tagger consolidated some of these.
# We treat the pair {custom_system, bespoke_application} as semantically
# equivalent for material_divergence purposes UNLESS the narrative
# clearly indicates otherwise. They are still surfaced as a soft signal
# only when paired with another divergence.
ENTRY_TYPE_EQUIV = {
    frozenset({"custom_system", "bespoke_application"}),
}

# ai_sophistication: 'predictive_analytics' was a Wave-1 category that
# the 2025 IFP tagger collapsed into 'classical_ml'. Treat as equivalent.
SOPHISTICATION_EQUIV = {
    # predictive_analytics was a Wave-1 only label; IFP collapses to classical_ml.
    frozenset({"predictive_analytics", "classical_ml"}),
    # The meaningful boundary is between the "classical" cluster
    # {classical_ml, nlp_specific, computer_vision, predictive_analytics}
    # and the "genai" cluster {general_llm, agentic, coding_assistant}.
    # Reshuffling within the classical cluster is taxonomy noise
    # (sentiment-classification could land in nlp_specific OR classical_ml
    # depending on tagger judgement); collapse to equivalent.
    frozenset({"nlp_specific", "classical_ml"}),
    frozenset({"nlp_specific", "predictive_analytics"}),
    frozenset({"nlp_specific", "computer_vision"}),
    frozenset({"computer_vision", "classical_ml"}),
    frozenset({"computer_vision", "predictive_analytics"}),
}

CLASSICAL_CLUSTER = {"classical_ml", "nlp_specific", "computer_vision", "predictive_analytics"}
GENAI_CLUSTER = {"general_llm", "agentic", "coding_assistant"}

# entry_type: 'generic_use_pattern' (Wave-1) vs 'custom_system' or
# 'product_deployment' (2025) is a real category disagreement we keep.
# But product_deployment vs custom_system is often just "did the agency
# wrap a commercial API or build from scratch" — when both years agree
# on the OTHER dimensions (genai, soph, scope), this alone isn't worth
# flagging. We require entry_type divergence to be paired with another
# divergence; we don't flag it standalone.

# deployment_scope tier ordering (higher index = broader).
SCOPE_TIERS = {
    "pilot": 0,
    "team": 0,
    "office": 1,
    "bureau": 2,
    "department": 3,
    "enterprise_wide": 4,
    "unknown": -1,  # treat unknown as a non-comparable
}


def entry_type_equivalent(a: str, b: str) -> bool:
    if a == b:
        return True
    return frozenset({a, b}) in ENTRY_TYPE_EQUIV


def sophistication_equivalent(a: str, b: str) -> bool:
    if a == b:
        return True
    return frozenset({a, b}) in SOPHISTICATION_EQUIV


def scope_delta(a: str, b: str) -> int | None:
    """Return absolute tier delta. None if either side is unknown/missing."""
    ta = SCOPE_TIERS.get(a, -1)
    tb = SCOPE_TIERS.get(b, -1)
    if ta < 0 or tb < 0:
        return None
    return abs(ta - tb)


def main() -> None:
    with open(INPUT, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    out_rows: list[dict] = []
    counts = {
        "material_divergence": 0,
        "drift_legitimate": 0,
        "tagging_error_2024": 0,
        "tagging_error_2025": 0,
    }

    for row in rows:
        uc_2024 = row["uc_2024_id"]

        et24 = row.get("entry_type_2024", "")
        et25 = row.get("entry_type_2025", "")
        ga24 = row.get("is_generative_ai_2024", "")
        ga25 = row.get("is_generative_ai_2025", "")
        so24 = row.get("ai_sophistication_2024", "")
        so25 = row.get("ai_sophistication_2025", "")
        ds24 = row.get("deployment_scope_2024", "")
        ds25 = row.get("deployment_scope_2025", "")

        flags: list[str] = []
        reasons: list[str] = []
        material_reasons: list[str] = []
        drift_reasons: list[str] = []

        # is_generative_ai mismatch is always material (binary, no ambiguity).
        genai_diff = bool(ga24) and bool(ga25) and ga24 != ga25

        # ai_sophistication mismatch (after equivalence collapse). Only
        # considered material if it crosses the classical/genai cluster
        # boundary AND that crossing isn't already encoded by genai_diff.
        soph_diff = (
            bool(so24)
            and bool(so25)
            and not sophistication_equivalent(so24, so25)
        )
        soph_xcluster = (
            soph_diff
            and so24 in (CLASSICAL_CLUSTER | GENAI_CLUSTER)
            and so25 in (CLASSICAL_CLUSTER | GENAI_CLUSTER)
            and (
                (so24 in CLASSICAL_CLUSTER) != (so25 in CLASSICAL_CLUSTER)
            )
        )

        # entry_type mismatch (after equivalence collapse). NOT material
        # on its own — only annotated alongside another divergence.
        et_diff = (
            bool(et24)
            and bool(et25)
            and not entry_type_equivalent(et24, et25)
        )

        # deployment_scope: delta > 1 tier.
        delta = scope_delta(ds24, ds25)
        scope_any = delta is not None and delta > 1
        # Scope GREW (narrow -> broad). Any tier increase >1 is textbook
        # drift_legitimate (pilot/office -> bureau, bureau -> enterprise).
        # Treat as drift, not material divergence.
        t24 = SCOPE_TIERS.get(ds24, -1)
        t25 = SCOPE_TIERS.get(ds25, -1)
        scope_grew_legit = scope_any and t25 > t24
        # broad->narrow (enterprise_wide->bureau, etc) — the more
        # suspicious direction, worth surfacing as material.
        scope_shrunk = scope_any and t25 < t24

        if genai_diff:
            material_reasons.append(
                f"is_generative_ai 2024={ga24} vs 2025={ga25}"
            )
        # cross-cluster soph shift not already implied by genai_diff
        if soph_xcluster and not genai_diff:
            material_reasons.append(
                f"ai_sophistication crossed cluster {so24}->{so25}"
            )
        if scope_shrunk:
            material_reasons.append(
                f"deployment_scope NARROWED {ds24}->{ds25} ({delta} tiers)"
            )
        # bureau<->department type shifts that are still >1 tier (e.g.,
        # bureau->enterprise) but not narrow->broad/legit growth.
        if scope_any and not scope_grew_legit and not scope_shrunk:
            material_reasons.append(
                f"deployment_scope shifted {ds24}->{ds25} ({delta} tiers)"
            )

        if material_reasons:
            flags.append("material_divergence")
            reasons.extend(material_reasons)
            if et_diff:
                reasons.append(
                    f"entry_type also shifted {et24}->{et25}"
                )

        # ---- drift_legitimate (standalone-eligible) ----
        if scope_grew_legit:
            drift_reasons.append(
                f"scope grew narrow->broad ({ds24}->{ds25}); likely real rollout"
            )

        # GenAI gained between cycles: a 2024 non-genai use case that the
        # agency layered an LLM onto in 2025 is real drift, not a tagging
        # error. Pair drift_legitimate with material_divergence.
        if genai_diff and ga24 == "0" and ga25 == "1":
            drift_reasons.append(
                "agency added generative AI between cycles"
            )

        if drift_reasons:
            flags.append("drift_legitimate")
            reasons.extend(drift_reasons)

        # ---- tagging_error_2024 (re-read the narrative) ----
        # Heuristic: 2024 said non-genai but the narrative or vendor name
        # clearly references an LLM/ChatGPT/Copilot/Claude/Gemini AND 2025
        # also says genai=1 — Wave 1 missed it.
        narrative = " ".join(
            (
                row.get("purpose_benefits", "") or "",
                row.get("outputs", "") or "",
                row.get("name_2024", "") or "",
            )
        ).lower()
        llm_markers = (
            "chatgpt",
            "gpt-4",
            "gpt 4",
            "large language model",
            "llm ",
            " llm.",
            "copilot",
            "claude",
            "gemini",
            "generative ai",
            "generative artificial intelligence",
            "foundation model",
        )
        looks_llm = any(m in narrative for m in llm_markers)
        if ga24 == "0" and ga25 == "1" and looks_llm:
            flags.append("tagging_error_2024")
            reasons.append(
                "narrative mentions LLM/genai marker; Wave 1 missed it"
            )

        # ---- tagging_error_2025 ----
        # Heuristic: 2024 said genai=1 and the narrative supports that
        # (genai marker present), but 2025 says genai=0. The 2025 tag is
        # likely the wrong one. (Reverse of above.)
        if ga24 == "1" and ga25 == "0" and looks_llm:
            flags.append("tagging_error_2025")
            reasons.append(
                "narrative mentions genai marker; 2025 tag of 0 likely wrong"
            )

        # Coding tool inconsistency: 2025 says it's a coding tool but
        # 2024 didn't — usually drift or 2024 error. We don't flag this
        # alone unless it pairs with sophistication/genai divergence
        # already flagged.

        if not flags:
            continue

        # Dedup flags preserving order.
        seen = set()
        deduped = []
        for fl in flags:
            if fl not in seen:
                seen.add(fl)
                deduped.append(fl)

        # Confidence calibration.
        if "tagging_error_2024" in deduped or "tagging_error_2025" in deduped:
            confidence = "medium"
        elif "drift_legitimate" in deduped:
            confidence = "medium"
        elif scope_any and not (genai_diff or soph_diff or et_diff):
            # Pure scope shift, no other divergence — lower confidence.
            confidence = "low"
        else:
            confidence = "medium"

        for fl in deduped:
            counts[fl] = counts.get(fl, 0) + 1

        out = {
            "use_case_id_2024": uc_2024,
            "tagged_by_agent": "wave2a-continued",
            "quality_flags_json": json.dumps(deduped),
            "reasoning": "; ".join(reasons)[:500],
            "confidence": confidence,
        }

        # If we propose a 2024 correction, include corrected fields.
        if "tagging_error_2024" in deduped:
            # Adopt 2025's reading as the proposed fix (it agrees with
            # narrative evidence).
            out["entry_type"] = et25
            out["is_generative_ai"] = ga25
            out["ai_sophistication"] = so25
            out["deployment_scope"] = ds24  # keep 2024 scope
            out["is_general_llm_access"] = row.get("is_general_llm_access_2025", "")
            out["is_coding_tool"] = row.get("is_coding_tool_2025", "")
            out["tool_product_name"] = row.get("tool_product_name_2025", "")
            out["tool_vendor"] = row.get("tool_vendor_2025", "")

        out_rows.append(out)

    fieldnames = [
        "use_case_id_2024",
        "tagged_by_agent",
        "quality_flags_json",
        "reasoning",
        "confidence",
        "entry_type",
        "is_generative_ai",
        "ai_sophistication",
        "deployment_scope",
        "is_general_llm_access",
        "is_coding_tool",
        "tool_product_name",
        "tool_vendor",
    ]

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in out_rows:
            w.writerow(r)

    print(f"flagged_rows={len(out_rows)}")
    print("flag_counts:", counts)


if __name__ == "__main__":
    main()
