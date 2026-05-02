"""Refresh round-3 sub-agency CSVs against a regenerated foundation.

Behavior:
  - For each sub-agency present in the existing CSV: keep the agent's editorial
    rating + key_systems + scope_or_users + confidence + key_evidence + notes;
    refresh `subtree_use_cases` from the latest foundation JSON.
  - For each sub-agency NEW in the foundation (intermediate parents added by
    the unmapped-research integration): emit a deterministic-rule row using
    the same logic as scripts/draft_round3_ratings.py.
  - For each sub-agency GONE from the foundation (not expected): drop.

Idempotent. Run after a foundation refresh.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.draft_round3_ratings import (  # noqa: E402
    rate_general_llm, rate_coding, rate_data_analysis, parse_parent_ratings,
)

FOUNDATION = ROOT / "audit" / "retag" / "round3" / "_foundation" / "sub_agencies.json"
PARENT_LLM = ROOT / "audit" / "retag" / "general_llm" / "by_agency.md"
PARENT_CODING = ROOT / "audit" / "retag" / "coding" / "by_agency.md"
PARENT_DATA = ROOT / "audit" / "retag" / "data_analysis" / "by_agency.md"

CSV_HEADER = [
    "parent_agency", "sub_agency_slug", "sub_agency_name", "sub_agency_abbr",
    "level", "subtree_use_cases", "rating", "key_systems", "scope_or_users",
    "confidence", "key_evidence", "notes",
]


def refresh_topic(topic: str, rater) -> dict:
    csv_path = ROOT / "audit" / "retag" / "round3" / topic / "sub_agency_rows.csv"
    parent_md = {
        "general_llm": PARENT_LLM,
        "coding": PARENT_CODING,
        "data_analysis": PARENT_DATA,
    }[topic]
    parent_ratings = parse_parent_ratings(parent_md.read_text() if parent_md.exists() else "")

    foundation = json.loads(FOUNDATION.read_text())
    foundation_by_slug = {e["slug"]: e for e in foundation}

    existing = {r["sub_agency_slug"]: r for r in csv.DictReader(open(csv_path))}

    out_rows: list[list] = []
    stats = {"refreshed": 0, "added_deterministic": 0, "dropped_missing": 0}

    for entry in foundation:
        slug = entry["slug"]
        if slug in existing:
            row = existing[slug]
            row["subtree_use_cases"] = str(entry["subtree_use_cases"])
            stats["refreshed"] += 1
            out_rows.append([row.get(c, "") for c in CSV_HEADER])
        else:
            decision = rater(entry, parent_ratings)
            row_list = [
                entry.get("parent_agency") or "",
                slug,
                entry.get("name") or "",
                entry.get("abbreviation") or "",
                entry.get("level") or "",
                entry.get("subtree_use_cases") or 0,
                decision["rating"],
                decision["key_systems"],
                decision["scope_or_users"],
                decision["confidence"],
                decision["key_evidence"] + "; deterministic_rule_post_unmapped_integration",
                decision["notes"],
            ]
            out_rows.append(row_list)
            stats["added_deterministic"] += 1

    # Sub-agencies in old CSV but no longer in foundation — keep them in the
    # output (don't drop) since they may still be referenced elsewhere; mark
    # them as such by setting subtree_use_cases to original value.
    for slug, row in existing.items():
        if slug not in foundation_by_slug:
            stats["dropped_missing"] += 1
            # Don't include them — the foundation is now authoritative

    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)
        for row in out_rows:
            w.writerow(row)
    print(f"[refresh] {topic:>14}: {stats}")
    return stats


def main() -> int:
    refresh_topic("general_llm", rate_general_llm)
    refresh_topic("coding", rate_coding)
    refresh_topic("data_analysis", rate_data_analysis)
    return 0


if __name__ == "__main__":
    sys.exit(main())
