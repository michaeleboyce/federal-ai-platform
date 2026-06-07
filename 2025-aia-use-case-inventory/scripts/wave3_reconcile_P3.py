"""Wave 3 reconciliation for partition P3 (211 rows).

Decision rules per audit/retag/2024-tagging/WAVE3_RUBRIC.md.
"""
from __future__ import annotations
import csv, json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "audit/retag/2024-tagging/wave3_inputs/P3.csv"
OUT_DIR = ROOT / "audit/retag/2024-tagging/wave3"
OUT_PATH = OUT_DIR / "P3.csv"

TAG_FIELDS = [
    "entry_type", "is_generative_ai", "ai_sophistication",
    "deployment_scope", "scope_detail", "is_enterprise_wide",
    "is_general_llm_access", "is_coding_tool", "is_cots_commercial",
    "tool_product_name", "tool_vendor",
    "is_microsoft_copilot", "is_openai", "is_anthropic", "is_google",
    "is_github_copilot", "is_aws_ai",
    "architecture_type", "use_type", "is_public_facing",
]
OUT_FIELDS = ["use_case_id_2024", "tagged_by_agent", "confidence", "reasoning"] + TAG_FIELDS

GENAI_RE = re.compile(
    r"\b(generative ai|gen[- ]?ai|llm|large language|gpt[- ]?\d?|chatgpt|copilot|"
    r"claude|gemini|bedrock|azure openai|openai|anthropic|"
    r"summariz|summarise|draft(ing|s)? (a |an |the |text|response|email|memo)|"
    r"natural language generation|chatbot|conversational ai|prompt|"
    r"text generation|code generation)\b",
    re.IGNORECASE,
)
CODING_RE = re.compile(r"\b(code|coding|developer productivity|software development|copilot)\b", re.IGNORECASE)
CHAT_RE = re.compile(r"\bchat( ?bot)?\b|\bconversational\b|\bvirtual (assistant|agent)\b", re.IGNORECASE)

def narrative_text(r):
    return " ".join([
        r.get("use_case_name", ""), r.get("purpose_benefits", ""),
        r.get("outputs", ""), r.get("commercial_ai", ""), r.get("dev_method", ""),
    ])

def has_genai_markers(r) -> bool:
    txt = narrative_text(r)
    if GENAI_RE.search(txt):
        return True
    return False

def from_wave1(r) -> dict:
    return {f: r.get(f"wave1_{f}", "") for f in TAG_FIELDS}

def from_2025(r) -> dict:
    """Map 2025 mirror fields into the tag schema (only those that map cleanly)."""
    out = {}
    for f in TAG_FIELDS:
        key2025 = f"{f}_2025"
        if key2025 in r:
            out[f] = r.get(key2025, "")
    # tool_product_name / tool_vendor 2025 mirrors are tool_product_name_2025 / tool_vendor_2025
    if not out.get("tool_product_name") and r.get("tool_product_name_2025"):
        out["tool_product_name"] = r["tool_product_name_2025"]
    if not out.get("tool_vendor") and r.get("tool_vendor_2025"):
        out["tool_vendor"] = r["tool_vendor_2025"]
    return out

def apply_proposed(base: dict, r: dict) -> dict:
    """Overlay any non-empty proposed_* fields onto base."""
    out = dict(base)
    for f in TAG_FIELDS:
        p = r.get(f"proposed_{f}", "")
        if p != "" and p is not None:
            out[f] = p
    return out

def scope_from_dev_stage(dev_stage: str, current: str) -> str:
    ds = (dev_stage or "").strip().lower()
    if ds in ("planned",):
        return "planned"
    if ds in ("initiated", "acquisition and/or development", "implementation and assessment"):
        # Pre-deployment — pilot/limited is appropriate
        if current in ("department", "bureau", "enterprise_wide"):
            return "pilot"
        return current or "pilot"
    return current

def reconcile(r: dict) -> dict:
    flags = set(json.loads(r["w2_flags_json"]) if r["w2_flags_json"] else [])
    flag_list = sorted(flags)
    out_tags = from_wave1(r)
    confidence = "medium"
    reasoning_parts: list[str] = []

    # tool_vendor_unverified — clear unless narrative supports
    if "tool_vendor_unverified" in flags:
        prod = (out_tags.get("tool_product_name") or "").strip()
        vendor = (out_tags.get("tool_vendor") or "").strip()
        narr = narrative_text(r)
        if prod and prod.lower() not in narr.lower():
            out_tags["tool_product_name"] = ""
        if vendor and vendor.lower() not in narr.lower():
            out_tags["tool_vendor"] = ""
            # Reset vendor brand flags that were inferred from vendor name
            if (out_tags.get("is_microsoft_copilot") or "") in ("1", 1) and "microsoft" not in narr.lower():
                out_tags["is_microsoft_copilot"] = "0"
            if (out_tags.get("is_openai") or "") in ("1", 1) and not re.search(r"openai|gpt", narr, re.I):
                out_tags["is_openai"] = "0"
            if (out_tags.get("is_anthropic") or "") in ("1", 1) and "anthropic" not in narr.lower() and "claude" not in narr.lower():
                out_tags["is_anthropic"] = "0"
            if (out_tags.get("is_google") or "") in ("1", 1) and "google" not in narr.lower() and "gemini" not in narr.lower():
                out_tags["is_google"] = "0"
            if (out_tags.get("is_github_copilot") or "") in ("1", 1) and "github" not in narr.lower() and "copilot" not in narr.lower():
                out_tags["is_github_copilot"] = "0"
            if (out_tags.get("is_aws_ai") or "") in ("1", 1) and "aws" not in narr.lower() and "amazon" not in narr.lower() and "bedrock" not in narr.lower():
                out_tags["is_aws_ai"] = "0"
            # Also clear cots if it was inferred only from the (now-cleared) vendor
            if (r.get("commercial_ai") or "").strip().lower() == "none of the above.":
                if (out_tags.get("is_cots_commercial") or "") in ("1", 1):
                    out_tags["is_cots_commercial"] = "0"
        reasoning_parts.append(f"tool_vendor_unverified — cleared product/vendor not supported by narrative")
        confidence = "high"

    # misclassified_lifecycle — fix scope based on dev_stage
    if "misclassified_lifecycle" in flags:
        proposed_scope = (r.get("proposed_deployment_scope") or "").strip()
        ds = (r.get("dev_stage") or "").strip()
        cur_scope = out_tags.get("deployment_scope", "")
        if proposed_scope:
            out_tags["deployment_scope"] = proposed_scope
            new_scope = proposed_scope
        else:
            new_scope = scope_from_dev_stage(ds, cur_scope)
            out_tags["deployment_scope"] = new_scope
        # retired_2024 + O&M = silently dropped live system; preserve deployed semantics
        if r.get("lineage_status") == "retired_2024" and "operation" in ds.lower():
            # Keep as deployed scope (don't downgrade to pilot) — these were live
            if cur_scope and cur_scope not in ("pilot", "planned"):
                out_tags["deployment_scope"] = cur_scope
            reasoning_parts.append(
                f"misclassified_lifecycle — retired_2024 + O&M; preserved deployed scope ({out_tags['deployment_scope']})"
            )
        else:
            reasoning_parts.append(
                f"misclassified_lifecycle — dev_stage='{ds}'; scope {cur_scope}→{out_tags['deployment_scope']}"
            )
        confidence = "high"

    # internal_inconsistency — re-resolve from narrative
    if "internal_inconsistency" in flags:
        w2 = r.get("w2_reasoning", "").lower()
        # Common pattern: entry_type=product_deployment but tool_product_name empty
        if "entry_type=product_deployment" in w2 and not (out_tags.get("tool_product_name") or "").strip():
            # Demote entry_type to a less-specific category
            if (r.get("commercial_ai") or "").strip().lower() != "none of the above.":
                # commercial_ai is set → it really is a product; entry_type ok, but product unknown
                out_tags["entry_type"] = "generic_use_pattern"
            else:
                out_tags["entry_type"] = "bespoke_application"
            reasoning_parts.append("internal_inconsistency — entry_type=product_deployment lacks tool name; downgraded entry_type")
        elif "is_generative_ai=1" in w2 and "soph" in w2 and "classical" in w2:
            # gen_ai=1 but soph=classical → narrative will decide
            if has_genai_markers(r):
                out_tags["is_generative_ai"] = "1"
                if (out_tags.get("ai_sophistication") or "") in ("", "classical_ml"):
                    out_tags["ai_sophistication"] = "general_llm"
                reasoning_parts.append("internal_inconsistency — narrative confirms genAI; soph→general_llm")
            else:
                out_tags["is_generative_ai"] = "0"
                reasoning_parts.append("internal_inconsistency — no genAI markers; gen_ai→0")
        else:
            # Generic: try the proposed if present, else flip the obvious one
            proposed_overlay = apply_proposed(out_tags, r)
            if proposed_overlay != out_tags:
                out_tags = proposed_overlay
                reasoning_parts.append("internal_inconsistency — applied proposed correction")
            else:
                reasoning_parts.append("internal_inconsistency — kept wave1 tag (no clear proposed fix)")
                confidence = "low"
        confidence = "high" if confidence != "low" else confidence

    # tagging_error_2024 — adopt proposed corrections from Wave 2
    if "tagging_error_2024" in flags:
        out_tags = apply_proposed(out_tags, r)
        # If proposed didn't fill the relevant field, pull from 2025 mirror
        # (Wave 2 flagged that 2024 was wrong and 2025 matches narrative)
        w2 = r.get("w2_reasoning", "").lower()
        m2025 = from_2025(r)
        # Apply 2025 mirror selectively for fields w2 reasoning mentions
        for fld_kw, fld in [
            ("ai_sophistication", "ai_sophistication"),
            ("is_generative_ai", "is_generative_ai"),
            ("entry_type", "entry_type"),
            ("architecture_type", "architecture_type"),
            ("deployment_scope", "deployment_scope"),
            ("use_type", "use_type"),
            ("is_cots_commercial", "is_cots_commercial"),
        ]:
            if fld_kw in w2 and (r.get(f"proposed_{fld}") or "") == "" and (m2025.get(fld) or "") != "":
                out_tags[fld] = m2025[fld]
        reasoning_parts.append("tagging_error_2024 — adopted Wave 2 corrections (and 2025 mirror where Wave 2 cited)")
        confidence = "high"

    # tagging_error_2025 — keep Wave 1; nothing to do beyond noting it
    if "tagging_error_2025" in flags and "tagging_error_2024" not in flags:
        reasoning_parts.append("tagging_error_2025 — kept wave1 2024 tag; 2025 fix is out-of-scope here")
        if not flags - {"tagging_error_2025"}:
            confidence = "high"

    # drift_legitimate — keep Wave 1 2024 tag as-filed
    if "drift_legitimate" in flags:
        # Override any earlier material_divergence-based decisions
        # by re-anchoring to wave1 (don't undo lifecycle/inconsistency fixes)
        if "misclassified_lifecycle" not in flags and "internal_inconsistency" not in flags and "tagging_error_2024" not in flags:
            out_tags = from_wave1(r)
        reasoning_parts.append("drift_legitimate — kept 2024 tag as filed (agency changed posture in 2025)")
        confidence = "high"

    # material_divergence (alone — no other flag handled it)
    if "material_divergence" in flags and "drift_legitimate" not in flags \
            and "tagging_error_2024" not in flags \
            and "tagging_error_2025" not in flags:
        w2 = r.get("w2_reasoning", "").lower()
        m2025 = from_2025(r)
        narr_has_genai = has_genai_markers(r)
        decision_made = False

        # is_generative_ai divergence
        if "is_generative_ai" in w2:
            w1_gen = (r.get("wave1_is_generative_ai") or "").strip()
            m25_gen = (r.get("is_generative_ai_2025") or "").strip()
            if narr_has_genai:
                out_tags["is_generative_ai"] = "1"
                if (out_tags.get("ai_sophistication") or "") in ("", "classical_ml", "nlp_specific"):
                    # Only upgrade if narrative truly LLM-ish
                    if re.search(r"\b(llm|gpt|chatgpt|copilot|claude|gemini|generative)\b", narrative_text(r), re.I):
                        out_tags["ai_sophistication"] = "general_llm"
                reasoning_parts.append("material_divergence (gen_ai) — narrative shows generative markers; adopted gen_ai=1")
            else:
                # No GenAI markers → narrative supports non-generative
                out_tags["is_generative_ai"] = "0"
                if (out_tags.get("ai_sophistication") or "") == "general_llm":
                    # Downgrade sophistication too
                    out_tags["ai_sophistication"] = m2025.get("ai_sophistication") or "nlp_specific"
                reasoning_parts.append("material_divergence (gen_ai) — narrative lacks GenAI markers; adopted gen_ai=0")
            decision_made = True

        # ai_sophistication cluster shift
        if "ai_sophistication" in w2 and "is_generative_ai" not in w2:
            if narr_has_genai or re.search(r"\b(llm|gpt|chatgpt|generative|copilot)\b", narrative_text(r), re.I):
                # Narrative supports LLM-class → adopt 2025 reading
                if m2025.get("ai_sophistication"):
                    out_tags["ai_sophistication"] = m2025["ai_sophistication"]
                if (r.get("is_generative_ai_2025") or "") == "1":
                    out_tags["is_generative_ai"] = "1"
                reasoning_parts.append("material_divergence (soph) — narrative supports LLM-class; adopted 2025 sophistication")
            else:
                # Narrative does not support LLM-class → keep wave1
                reasoning_parts.append("material_divergence (soph) — narrative does not support LLM-class; kept wave1 sophistication")
            decision_made = True

        # entry_type / architecture / deployment_scope drift without drift flag
        if "scope" in w2 and "scope grew" in w2 and "is_generative_ai" not in w2 and "ai_sophistication" not in w2:
            # Wave 2 thinks the rollout is real
            if m2025.get("deployment_scope"):
                out_tags["deployment_scope"] = m2025["deployment_scope"]
                reasoning_parts.append("material_divergence (scope) — adopted 2025 broader scope")
                decision_made = True

        if not decision_made:
            # Default: keep wave1, note we kept it
            reasoning_parts.append("material_divergence — narrative thin; kept wave1 tag")
            confidence = "low"
        else:
            confidence = "medium"

    if not reasoning_parts:
        reasoning_parts.append("no actionable flag handled — kept wave1")
        confidence = "low"

    return {
        "use_case_id_2024": r["use_case_id_2024"],
        "tagged_by_agent": "wave3-P3",
        "confidence": confidence,
        "reasoning": "; ".join(reasoning_parts),
        **{f: (out_tags.get(f) or "") for f in TAG_FIELDS},
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(IN_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 211, f"expected 211 input rows, got {len(rows)}"
    out_rows = [reconcile(r) for r in rows]
    assert len(out_rows) == 211
    with open(OUT_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        w.writeheader()
        for o in out_rows:
            w.writerow(o)
    print(f"Wrote {len(out_rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
