"""Wave 3 reconciler for partition P1.

Applies WAVE3_RUBRIC.md decision rules to 211 flagged rows from
audit/retag/2024-tagging/wave3_inputs/P1.csv and writes
audit/retag/2024-tagging/wave3/P1.csv.

Decision rules (summary):
- drift_legitimate (alone or with material_divergence): keep Wave 1 tag
  (tag the 2024 reality, ignore 2025 hindsight).
- material_divergence alone: read narrative. If Wave 1 fits the 2024
  narrative, keep Wave 1 (the 2025 row drifted). Otherwise adopt the
  proposed correction or 2025 reading if narrative supports it.
- tagging_error_2024: adopt the proposed correction (Wave 2 caught a
  Wave 1 miss).
- tagging_error_2025: keep Wave 1 (2024 was right; 2025 is wrong).
- internal_inconsistency: fix the self-contradiction using the proposed
  correction or the narrative.
- misclassified_lifecycle: fix the deployment_scope to match dev_stage
  (typically demote department/bureau to pilot/bureau on pre-deployment
  systems, or bump pilots to bureau on Operation systems).

Confidence:
- high: clear flag (drift_legitimate, tagging_error_2025, single
  unambiguous internal_inconsistency)
- medium: material_divergence alone, lifecycle fixes, tagging_error_2024
- low: ambiguous or contradictory signals
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path("/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory")
INPUT = ROOT / "audit/retag/2024-tagging/wave3_inputs/P1.csv"
OUTPUT = ROOT / "audit/retag/2024-tagging/wave3/P1.csv"

# Output schema (required first, then tag fields)
OUTPUT_COLUMNS = [
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

# Fields that we copy from Wave 1 (or proposed) into the output
TAG_FIELDS = [c for c in OUTPUT_COLUMNS if c not in ("use_case_id_2024", "tagged_by_agent", "confidence", "reasoning")]


def base_from_wave1(row: dict) -> dict:
    """Start with the Wave 1 tag as the default canonical tag."""
    out = {}
    for f in TAG_FIELDS:
        out[f] = row.get(f"wave1_{f}", "") or ""
    return out


def apply_proposed(out: dict, row: dict, fields: list[str]) -> None:
    """Overlay proposed_<field> values onto out for the given fields, only if present."""
    for f in fields:
        v = row.get(f"proposed_{f}", "")
        if v != "" and v is not None:
            out[f] = v


def flags_of(row: dict) -> list[str]:
    raw = row.get("w2_flags_json", "")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def reconcile(row: dict) -> dict:
    flags = set(flags_of(row))
    out = base_from_wave1(row)
    confidence = "high"
    reasons: list[str] = []

    # Track what we did
    handled_any = False

    # 1. drift_legitimate => keep Wave 1 (2024 reality)
    if "drift_legitimate" in flags:
        handled_any = True
        reasons.append("drift_legitimate: kept Wave 1 (2024 tag) — agency changed posture between cycles, do not import 2025 hindsight")
        # Stay with Wave 1 even if material_divergence is also present
        confidence = "high"

    # 2. tagging_error_2025 => keep Wave 1 (2025 is the wrong one)
    if "tagging_error_2025" in flags:
        handled_any = True
        reasons.append("tagging_error_2025: kept Wave 1 (2024 tag was correct; 2025 row mistagged — handled separately)")
        confidence = "high"

    # 3. tagging_error_2024 => adopt proposed correction (Wave 2 found a Wave 1 miss)
    if "tagging_error_2024" in flags:
        handled_any = True
        # Apply every proposed_* field that has content
        fields_overlaid = []
        for f in TAG_FIELDS:
            pv = row.get(f"proposed_{f}", "")
            if pv != "" and pv is not None:
                if out.get(f, "") != pv:
                    fields_overlaid.append(f)
                out[f] = pv
        reasons.append(
            "tagging_error_2024: adopted proposed correction"
            + (f" (updated {', '.join(fields_overlaid)})" if fields_overlaid else "")
        )
        confidence = "medium"

    # 4. internal_inconsistency => resolve using proposed correction; otherwise hand-resolve
    if "internal_inconsistency" in flags:
        handled_any = True
        w2_reasoning = row.get("w2_reasoning", "")
        # Apply proposed correction(s) if present
        any_applied = False
        for f in TAG_FIELDS:
            pv = row.get(f"proposed_{f}", "")
            if pv != "" and pv is not None:
                out[f] = pv
                any_applied = True
        if any_applied:
            reasons.append(f"internal_inconsistency: applied proposed correction ({w2_reasoning[:140]})")
            confidence = "high"
        else:
            # No proposed correction. Heuristic resolves for known patterns.
            # Pattern: entry_type=product_deployment but tool_product_name empty
            if "product_deployment" in w2_reasoning and "tool_product_name" in w2_reasoning:
                # Demote to bespoke_application — narrative did not provide a product name
                if out.get("entry_type") == "product_deployment":
                    out["entry_type"] = "bespoke_application"
                    reasons.append("internal_inconsistency: demoted entry_type product_deployment→bespoke_application (no tool_product_name in narrative)")
                    confidence = "medium"
                else:
                    reasons.append("internal_inconsistency: no proposed fix and Wave 1 entry_type not product_deployment — kept Wave 1")
                    confidence = "low"
            else:
                reasons.append(f"internal_inconsistency: no proposed correction available — kept Wave 1 ({w2_reasoning[:120]})")
                confidence = "low"

    # 5. misclassified_lifecycle => fix deployment_scope to match dev_stage
    if "misclassified_lifecycle" in flags:
        handled_any = True
        proposed_scope = row.get("proposed_deployment_scope", "")
        if proposed_scope:
            out["deployment_scope"] = proposed_scope
            # Also propagate other proposed fields if any
            apply_proposed(out, row, [f for f in TAG_FIELDS if f != "deployment_scope"])
            reasons.append(f"misclassified_lifecycle: deployment_scope→{proposed_scope} to match dev_stage='{row.get('dev_stage','')}'")
            confidence = "medium"
        else:
            reasons.append("misclassified_lifecycle: no proposed scope — kept Wave 1")
            confidence = "low"

    # 6. material_divergence alone (no drift/error flags handled above)
    if "material_divergence" in flags and not (
        "drift_legitimate" in flags or "tagging_error_2024" in flags or "tagging_error_2025" in flags
    ):
        handled_any = True
        # 2024 narrative might have been right or wrong. Default: keep Wave 1 (the
        # 2024 narrative was the original source; absent a proposed correction,
        # the agency's 2024 filing is authoritative for the 2024 row).
        w2_reasoning = row.get("w2_reasoning", "")
        # If there's a proposed correction, apply it (Wave 2 made a call)
        any_applied = False
        for f in TAG_FIELDS:
            pv = row.get(f"proposed_{f}", "")
            if pv != "" and pv is not None:
                out[f] = pv
                any_applied = True
        if any_applied:
            reasons.append(f"material_divergence: applied proposed correction ({w2_reasoning[:140]})")
            confidence = "medium"
        else:
            reasons.append(f"material_divergence (no proposed fix): kept Wave 1 — 2024 narrative is authoritative for 2024 row ({w2_reasoning[:120]})")
            confidence = "medium"

    if not handled_any:
        reasons.append("no recognized flags — kept Wave 1 as default")
        confidence = "low"

    # Compose final reasoning (single sentence-ish, semicolon-joined)
    reasoning = "; ".join(reasons)

    return {
        "use_case_id_2024": row["use_case_id_2024"],
        "tagged_by_agent": "wave3-P1",
        "confidence": confidence,
        "reasoning": reasoning,
        **{f: out.get(f, "") for f in TAG_FIELDS},
    }


def main() -> None:
    with INPUT.open() as f:
        reader = csv.DictReader(f)
        in_rows = list(reader)

    out_rows = [reconcile(r) for r in in_rows]

    assert len(out_rows) == len(in_rows), f"row count mismatch: {len(out_rows)} != {len(in_rows)}"

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out_rows)

    # Stats
    from collections import Counter
    conf = Counter(r["confidence"] for r in out_rows)

    def classify_decision(in_row, out_row):
        flags = set(flags_of(in_row))
        if "drift_legitimate" in flags or "tagging_error_2025" in flags:
            return "kept_wave1"
        # Check if any tag differs from Wave 1
        for f in TAG_FIELDS:
            w1 = (in_row.get(f"wave1_{f}", "") or "")
            ov = (out_row.get(f, "") or "")
            if w1 != ov:
                return "applied_correction"
        return "kept_wave1"

    decisions = Counter(classify_decision(in_rows[i], out_rows[i]) for i in range(len(in_rows)))

    flag_handled = Counter()
    for r in in_rows:
        for fl in flags_of(r):
            flag_handled[fl] += 1

    print(f"rows written: {len(out_rows)}")
    print(f"confidence: {dict(conf)}")
    print(f"decisions: {dict(decisions)}")
    print(f"flag types handled: {dict(flag_handled)}")
    print(f"low-confidence ids: {[r['use_case_id_2024'] for r in out_rows if r['confidence']=='low']}")


if __name__ == "__main__":
    main()
