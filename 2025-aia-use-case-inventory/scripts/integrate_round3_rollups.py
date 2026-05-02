"""Merge round-3 sub-agency rows into the three article-grade by_agency.md
rollups.

Reads:
  audit/retag/round3/<topic>/sub_agency_rows.csv  (× 3)
  audit/retag/<topic>/by_agency.md                (× 3, current)

Writes:
  audit/retag/<topic>/by_agency.md  — appends a "Sub-agency rollup" section
                                       that groups sub-agencies by parent and
                                       renders a markdown table per parent
                                       (only for parents with >= 3 sub-agencies
                                       in scope; smaller parents get a footnote)
  audit/retag/round3/SUB_AGENCY_FINDINGS.md — editorial cross-topic summary

The append is idempotent: if a "Sub-agency rollup (round-3)" header already
exists, everything below it is replaced.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECTION_HEADER = "## Sub-agency rollup (round-3)"
TOPICS = [
    ("general_llm", "general-purpose LLM", {"Enterprise": 0, "Broad": 1, "Limited": 2, "None reported": 3, "Inherited": 4}),
    ("coding", "AI coding tools", {"Enterprise/Broad": 0, "Limited/Pilot": 1, "Inherited": 2, "None reported": 3}),
    ("data_analysis", "AI data-analysis platforms", {"Strong": 0, "Moderate": 1, "Limited": 2, "None reported": 3}),
]

# Order in which we display parent-agency sections. Drives editorial flow.
PARENT_ORDER = [
    "HHS", "DHS", "DOE", "NASA", "DOJ", "DOC", "Treasury", "VA", "DOI", "USDA",
    "State", "DOL", "SEC", "DOT", "ED", "VA", "SSA", "SBA", "FDIC", "FRB", "FHFA", "FTC", "TVA",
]

# Only render a per-parent table for parents with this many or more sub-agencies
TABLE_MIN = 3


def md_escape(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


def render_topic_section(topic: str, label: str, rating_order: dict) -> str:
    csv_path = ROOT / "audit" / "retag" / "round3" / topic / "sub_agency_rows.csv"
    rows = list(csv.DictReader(open(csv_path)))

    # Group by parent
    by_parent: dict[str, list[dict]] = {}
    for r in rows:
        by_parent.setdefault(r["parent_agency"], []).append(r)

    # Sort each group by rating then by use-case count desc
    for p, lst in by_parent.items():
        lst.sort(key=lambda r: (rating_order.get(r["rating"], 99), -int(r["subtree_use_cases"] or 0)))

    out: list[str] = []
    out.append(SECTION_HEADER)
    out.append("")
    out.append(
        f"Sub-agency view for {label}, derived from per-bureau use-case counts and "
        f"the round-3 review (96 sub-agencies, see `audit/retag/round3/{topic}/`). "
        "Cabinet departments and independent agencies are kept at the parent table "
        "above; the rows below are bureaus, labs, centers, and offices within them. "
        "Sub-agencies with <5 use cases are excluded as below the data-quality "
        "threshold."
    )
    out.append("")

    # Render parents in PARENT_ORDER, then any leftovers alphabetically
    seen = set()
    parent_list = [p for p in PARENT_ORDER if p in by_parent and p not in seen and not seen.add(p)]
    parent_list += sorted(p for p in by_parent if p not in parent_list)

    big_parents = [p for p in parent_list if len(by_parent[p]) >= TABLE_MIN]
    small_parents = [p for p in parent_list if len(by_parent[p]) < TABLE_MIN]

    for parent in big_parents:
        rows_p = by_parent[parent]
        out.append(f"### Within {parent} ({len(rows_p)} sub-agencies)")
        out.append("")
        out.append("| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |")
        out.append("|---|---|---|---|---|---|---|")
        for r in rows_p:
            slug = r["sub_agency_slug"]
            name = r["sub_agency_name"]
            abbr = r["sub_agency_abbr"]
            link_label = abbr if abbr and abbr != name else name
            cell_name = f"[{md_escape(name)} ({link_label})](/agencies/{slug})" if abbr else f"[{md_escape(name)}](/agencies/{slug})"
            out.append(
                "| "
                + " | ".join([
                    cell_name,
                    md_escape(r["rating"]),
                    md_escape(r["key_systems"]),
                    md_escape(r["scope_or_users"]),
                    md_escape(r["confidence"]),
                    md_escape(r["key_evidence"]),
                    md_escape(r["notes"])[:240],
                ])
                + " |"
            )
        out.append("")

    if small_parents:
        out.append(f"### Smaller parent agencies ({len(small_parents)})")
        out.append("")
        out.append("Parent agencies with fewer than 3 in-scope sub-agencies are summarized inline:")
        out.append("")
        for parent in small_parents:
            for r in by_parent[parent]:
                out.append(
                    f"- **{parent} → {r['sub_agency_name']} ({r['sub_agency_abbr']})** — "
                    f"{r['rating']} ({r['confidence']}). {md_escape(r['notes'])[:200]}"
                )
        out.append("")

    out.append(f"_Source: `audit/retag/round3/{topic}/sub_agency_rows.csv` (96 rows). "
               f"Methodology in `audit/retag/round3/{topic}/notes.md`._")
    out.append("")
    return "\n".join(out)


def upsert_section(md_path: Path, new_section: str) -> None:
    text = md_path.read_text() if md_path.exists() else ""
    # Replace existing section if present, else append
    pattern = re.compile(r"\n*---\n*" + re.escape(SECTION_HEADER) + r".*", re.S)
    if pattern.search(text):
        text = pattern.sub("\n\n---\n\n" + new_section.rstrip() + "\n", text)
    else:
        text = text.rstrip() + "\n\n---\n\n" + new_section.rstrip() + "\n"
    md_path.write_text(text)


def main() -> int:
    for topic, label, order in TOPICS:
        section = render_topic_section(topic, label, order)
        target = ROOT / "audit" / "retag" / topic / "by_agency.md"
        upsert_section(target, section)
        print(f"[integrate] {topic} → {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    main()
