"""Deterministic round-3 sub-agency rating draft.

Applies the CHARTER decision rules to each entry in
audit/retag/round3/_foundation/sub_agencies.json and emits three CSV files:

  audit/retag/round3/general_llm/sub_agency_rows.csv
  audit/retag/round3/coding/sub_agency_rows.csv
  audit/retag/round3/data_analysis/sub_agency_rows.csv

These are first-cut ratings derived ONLY from the foundation pack — no web
search. Used as a fallback when slice agents are blocked, or as a starting
point for human/agent review of surprising rows.

Each row carries a `notes` column flagging the rule that fired and any
follow-up needed (e.g., "verify parent cascade", "named tool not in canonical
list").
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
FOUNDATION = ROOT / "audit" / "retag" / "round3" / "_foundation" / "sub_agencies.json"
PARENT_LLM = ROOT / "audit" / "retag" / "general_llm" / "by_agency.md"
PARENT_CODING = ROOT / "audit" / "retag" / "coding" / "by_agency.md"
PARENT_DATA = ROOT / "audit" / "retag" / "data_analysis" / "by_agency.md"

OUT = {
    "general_llm": ROOT / "audit" / "retag" / "round3" / "general_llm" / "sub_agency_rows.csv",
    "coding": ROOT / "audit" / "retag" / "round3" / "coding" / "sub_agency_rows.csv",
    "data_analysis": ROOT / "audit" / "retag" / "round3" / "data_analysis" / "sub_agency_rows.csv",
}

CSV_HEADER = [
    "parent_agency", "sub_agency_slug", "sub_agency_name", "sub_agency_abbr",
    "level", "subtree_use_cases", "rating", "key_systems", "scope_or_users",
    "confidence", "key_evidence", "notes",
]

# Coding-specific tool tokens (lowercase substring match)
CODING_TOOL_TOKENS = (
    "github copilot", "claude code", "amazon q developer", "amazon codewhisperer",
    "codewhisperer", "gemini code assist", "tabnine", "cursor", "codeium",
    "windsurf", "watsonx code", "averisource", "pingwind", "ansible lightspeed",
    "code llama", "starcoder", "ai pair programming", "ide assistant",
)
# Tokens that look code-related but are autocoders / not real coding tools
NON_CODING_HINTS = (
    "autocoder", "auto-coder", "auto coder", "icd-10", "occupation code",
    "offense code", "soc code", "naics", "med-coder", "medcoder",
)
# Generic LLMs — code generation in these is INCIDENTAL, not a coding tool
GENERIC_LLM_TOKENS = (
    "m365 copilot", "microsoft 365 copilot", "ms copilot", "microsoft copilot",
    "chatgpt", "gpt-4", "gpt 4", "claude (", "claude for government",
    "gemini for government", "gemini for workspace", "azure openai",
    "aws bedrock", "amazon bedrock",
)
# Analytic-platform tokens worth highlighting
PLATFORM_TOKENS = (
    "databricks", "sagemaker", "bedrock", "vertex ai", "azure ml",
    "azure machine learning", "fabric", "snowflake", "palantir", "foundry",
    "domino", "jupyterhub", "biowulf", "hecc", "pleiades", "aitken", "athena",
    "frontier", "mosaic", "edav", "atap", "nccs", "vinci",
    "cdw", "irs cdw", "raas", "atlas", "stridepoint",
)


def parse_parent_ratings(md_text: str) -> dict[str, str]:
    """Extract parent-agency ratings from a by_agency.md markdown table.

    Returns {abbr_uppercase: rating_lowercase} for table rows. Forgiving
    parser — pulls the first markdown table cell as the agency name (which
    may contain a bold marker) and the second cell as the rating.
    """
    out: dict[str, str] = {}
    table_re = re.compile(r"^\|\s*\*?\*?([A-Za-z][A-Za-z &/.+\-()' ]+?)\*?\*?\s*\|\s*([^|]+?)\s*\|")
    for line in md_text.splitlines():
        m = table_re.match(line.strip())
        if not m:
            continue
        agency_label = m.group(1).strip()
        rating = m.group(2).strip()
        # Skip header rows (rating column would say "Rating" or contain dashes)
        if rating.lower() in {"rating", "---", "----", "-----"} or rating.startswith("---"):
            continue
        # Capture by abbreviation when the cell is just an abbreviation
        # (typical pattern in our rollups).
        out[agency_label.upper()] = rating
    return out


def has_token(text: str, tokens: Iterable[str]) -> bool:
    if not text:
        return False
    t = text.lower()
    return any(tok in t for tok in tokens)


def join_text(entry: dict) -> str:
    parts = [entry.get("name") or "", " | ".join(entry.get("named_tools") or [])]
    for s in entry.get("sample_use_cases") or []:
        parts.append(s.get("name") or "")
        parts.append(s.get("system_name") or "")
        parts.append(s.get("vendor_name") or "")
    return " | ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Per-topic rating logic
# ---------------------------------------------------------------------------

def rate_general_llm(entry: dict, parent_ratings: dict[str, str]) -> dict:
    parent_rating = parent_ratings.get((entry.get("parent_agency") or "").upper(), "")
    parent_lower = parent_rating.lower()
    enterprise_llm = entry.get("subtree_enterprise_llm_count", 0)
    llm = entry.get("subtree_llm_count", 0)
    tier = entry.get("maturity_tier") or ""

    note_parts = []
    confidence = "low"

    if enterprise_llm >= 3 or llm >= 10:
        rating = "Broad"
        confidence = "medium"
        note_parts.append(f"subtree_llm_count={llm}, enterprise={enterprise_llm}")
    elif tier == "leading":
        rating = "Broad"
        confidence = "medium"
        note_parts.append("maturity_tier=leading")
    elif "enterprise" in parent_lower or "broad" in parent_lower:
        rating = "Inherited"
        confidence = "low"
        note_parts.append(f"parent rated {parent_rating!r}; cascade")
    elif llm > 0 or enterprise_llm > 0:
        rating = "Limited"
        confidence = "low"
        note_parts.append(f"some LLM activity in subtree (llm={llm})")
    else:
        rating = "None reported"
        confidence = "medium"
        note_parts.append("no LLM-tagged use cases in subtree")

    return {
        "rating": rating,
        "confidence": confidence,
        "key_systems": "—",
        "scope_or_users": f"{entry.get('subtree_use_cases', 0)} subtree use cases",
        "key_evidence": f"foundation:{entry.get('slug')}",
        "notes": "; ".join(note_parts),
    }


def rate_coding(entry: dict, parent_ratings: dict[str, str]) -> dict:
    parent_rating = parent_ratings.get((entry.get("parent_agency") or "").upper(), "")
    parent_lower = parent_rating.lower()
    coding = entry.get("subtree_coding_count", 0)
    text = join_text(entry)

    has_real_coding_tool = has_token(text, CODING_TOOL_TOKENS)
    has_autocoder_only = has_token(text, NON_CODING_HINTS) and not has_real_coding_tool
    only_generic_llm = (
        coding > 0
        and has_token(text, GENERIC_LLM_TOKENS)
        and not has_real_coding_tool
    )

    note_parts = []
    confidence = "low"

    if has_autocoder_only:
        rating = "None reported"
        confidence = "medium"
        note_parts.append("autocoder hits only — not a coding tool per CHARTER")
    elif has_real_coding_tool:
        rating = "Limited/Pilot" if coding < 3 else "Enterprise/Broad"
        confidence = "medium" if coding >= 3 else "low"
        note_parts.append(f"named coding tool present; subtree_coding_count={coding}")
    elif only_generic_llm:
        rating = "None reported"
        confidence = "medium"
        note_parts.append("generic-LLM only; CHARTER excludes")
    elif coding > 0:
        rating = "Limited/Pilot"
        confidence = "low"
        note_parts.append(f"subtree_coding_count={coding} but no named coding-specific tool surfaced")
    elif "enterprise" in parent_lower or "broad" in parent_lower:
        rating = "Inherited"
        confidence = "low"
        note_parts.append(f"parent rated {parent_rating!r}; cascade for staff developers")
    else:
        rating = "None reported"
        confidence = "medium"
        note_parts.append("no coding-tagged use cases")

    return {
        "rating": rating,
        "confidence": confidence,
        "key_systems": "—",
        "scope_or_users": f"{entry.get('subtree_use_cases', 0)} subtree use cases",
        "key_evidence": f"foundation:{entry.get('slug')}",
        "notes": "; ".join(note_parts),
    }


def rate_data_analysis(entry: dict, parent_ratings: dict[str, str]) -> dict:
    parent_rating = parent_ratings.get((entry.get("parent_agency") or "").upper(), "")
    parent_lower = parent_rating.lower()
    env_count = entry.get("subtree_env_count", 0)
    text = join_text(entry)

    has_named_platform = has_token(text, PLATFORM_TOKENS)

    note_parts = []
    confidence = "low"

    if env_count >= 5 and has_named_platform:
        rating = "Strong"
        confidence = "medium"
        note_parts.append(f"env_count={env_count} + named platform")
    elif has_named_platform and env_count >= 1:
        rating = "Moderate"
        confidence = "medium"
        note_parts.append(f"named platform + env_count={env_count}")
    elif "strong" in parent_lower:
        rating = "Moderate"
        confidence = "low"
        note_parts.append(f"parent {parent_rating!r}; floor at Moderate")
    elif env_count >= 3:
        rating = "Moderate"
        confidence = "low"
        note_parts.append(f"env_count={env_count} signal but platform unnamed")
    elif env_count >= 1:
        rating = "Limited"
        confidence = "low"
        note_parts.append(f"env_count={env_count}")
    else:
        rating = "Limited" if "moderate" in parent_lower or "strong" in parent_lower else "None reported"
        confidence = "low"
        note_parts.append("no platform/env signal in subtree")

    return {
        "rating": rating,
        "confidence": confidence,
        "key_systems": "—",
        "scope_or_users": f"{entry.get('subtree_use_cases', 0)} subtree use cases",
        "key_evidence": f"foundation:{entry.get('slug')}",
        "notes": "; ".join(note_parts),
    }


# ---------------------------------------------------------------------------
def main() -> int:
    entries = json.loads(FOUNDATION.read_text())
    parent_llm_md = PARENT_LLM.read_text() if PARENT_LLM.exists() else ""
    parent_coding_md = PARENT_CODING.read_text() if PARENT_CODING.exists() else ""
    parent_data_md = PARENT_DATA.read_text() if PARENT_DATA.exists() else ""

    parent_llm = parse_parent_ratings(parent_llm_md)
    parent_coding = parse_parent_ratings(parent_coding_md)
    parent_data = parse_parent_ratings(parent_data_md)

    raters = {
        "general_llm": (rate_general_llm, parent_llm),
        "coding": (rate_coding, parent_coding),
        "data_analysis": (rate_data_analysis, parent_data),
    }

    summary: dict[str, dict[str, int]] = {k: {} for k in raters}

    for topic, (rater, parent_map) in raters.items():
        out_path = OUT[topic]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(CSV_HEADER)
            for e in entries:
                rating_dict = rater(e, parent_map)
                row = [
                    e.get("parent_agency") or "",
                    e.get("slug") or "",
                    e.get("name") or "",
                    e.get("abbreviation") or "",
                    e.get("level") or "",
                    e.get("subtree_use_cases") or 0,
                    rating_dict["rating"],
                    rating_dict["key_systems"],
                    rating_dict["scope_or_users"],
                    rating_dict["confidence"],
                    rating_dict["key_evidence"],
                    rating_dict["notes"],
                ]
                w.writerow(row)
                summary[topic][rating_dict["rating"]] = (
                    summary[topic].get(rating_dict["rating"], 0) + 1
                )
        print(f"[draft] {topic:>14} → {out_path.relative_to(ROOT)}")

    print("\n=== Rating distributions (deterministic draft) ===")
    for topic, dist in summary.items():
        print(f"  {topic}:")
        for rating, n in sorted(dist.items(), key=lambda kv: -kv[1]):
            print(f"    {rating:>20}  {n:>3}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
