"""Integrate the 4-agent linkage pass into CSV-staged outputs.

Reads:
  audit/linkage_pass_2026-05/agent_a/recommendations.json
  audit/linkage_pass_2026-05/agent_b/recommendations.json
  audit/linkage_pass_2026-05/agent_c/recommendations.json
  audit/linkage_pass_2026-05/agent_d/hierarchy_proposals.json

Writes:
  audit/linkage_pass_2026-05/integration/proposed_links.csv
  audit/linkage_pass_2026-05/integration/proposed_new_products.csv
  audit/linkage_pass_2026-05/integration/proposed_aliases.csv
  audit/linkage_pass_2026-05/integration/proposed_hierarchy_edges.csv
  audit/linkage_pass_2026-05/integration/conflicts.csv
  audit/linkage_pass_2026-05/integration/summary.md

Dedupes:
  - `add_product` proposals are merged by case-folded canonical_name.
    Conflicts (same name, different vendor/product_type) are flagged
    rather than auto-merged.
  - `link` proposals are deduped on (entry_kind, entry_id, canonical_name).
  - `add_alias` proposals are deduped on (canonical_name, alias).
  - Hierarchy edges deduped on (child, parent).

No DB writes here. The apply script in Phase 4 consumes these CSVs.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def _resolve_inputs(pass_dir: Path) -> list[tuple[str, Path, str]]:
    """Auto-detect agent subdirectories. Each subdir holds either
    `recommendations.json` (link/add_product/alias decisions) or
    `hierarchy_proposals.json` (Agent D-style). Returns
    (agent_label, file_path, kind)."""
    out: list[tuple[str, Path, str]] = []
    for sub in sorted(pass_dir.iterdir()):
        if not sub.is_dir():
            continue
        if sub.name in {"inputs", "integration", "review"}:
            continue
        rec = sub / "recommendations.json"
        hier = sub / "hierarchy_proposals.json"
        if rec.exists():
            out.append((sub.name, rec, "decisions"))
        if hier.exists():
            out.append((sub.name, hier, "hierarchy"))
    return out


def _load(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        print(f"WARN: missing {path}")
        return []
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} did not contain a JSON array")
    return data


def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


def _entry_key(d: dict[str, Any]) -> tuple[str, int] | None:
    if d.get("use_case_id"):
        return ("use_case", int(d["use_case_id"]))
    if d.get("consolidated_use_case_id"):
        return ("consolidated", int(d["consolidated_use_case_id"]))
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pass-dir",
        type=Path,
        default=ROOT / "audit" / "linkage_pass_2026-05",
        help="Audit-pass directory (parent of agent subdirs and integration/).",
    )
    args = parser.parse_args()
    pass_dir = args.pass_dir.resolve()
    if not pass_dir.exists():
        raise FileNotFoundError(pass_dir)
    OUT = pass_dir / "integration"
    OUT.mkdir(parents=True, exist_ok=True)
    AGENT_INPUTS = _resolve_inputs(pass_dir)
    print(f"reading {len(AGENT_INPUTS)} agent file(s) from {pass_dir}")
    by_agent: dict[str, list[dict[str, Any]]] = {}
    for agent, path, _ in AGENT_INPUTS:
        by_agent[agent] = _load(path)

    links: dict[tuple, dict[str, Any]] = {}
    new_products: dict[str, dict[str, Any]] = {}
    aliases: dict[tuple[str, str], dict[str, Any]] = {}
    hierarchy: dict[tuple[str, str], dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    decisions_by_type: dict[str, int] = defaultdict(int)
    decisions_by_agent: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for agent, decisions in by_agent.items():
        for d in decisions:
            decision = (d.get("decision") or "").strip()
            decisions_by_type[decision] += 1
            decisions_by_agent[agent][decision] += 1

            if decision == "link":
                key = (
                    _entry_key(d),
                    _norm(d.get("canonical_name")),
                )
                if key[0] is None or not key[1]:
                    conflicts.append({
                        "agent": agent, "reason": "link missing entry_id or canonical_name",
                        "decision": json.dumps(d),
                    })
                    continue
                if key not in links:
                    links[key] = {**d, "_agent": agent}

            elif decision == "add_product":
                name_key = _norm(d.get("proposed_canonical_name"))
                if not name_key:
                    conflicts.append({
                        "agent": agent, "reason": "add_product missing proposed_canonical_name",
                        "decision": json.dumps(d),
                    })
                    continue
                if name_key in new_products:
                    existing = new_products[name_key]
                    same_vendor = _norm(existing.get("vendor")) == _norm(d.get("vendor"))
                    same_type = _norm(existing.get("product_type")) == _norm(d.get("product_type"))
                    if not (same_vendor and same_type):
                        conflicts.append({
                            "agent": agent,
                            "reason": f"add_product conflict on '{name_key}': vendor/type disagreement with {existing.get('_agent')}",
                            "decision": json.dumps({"new": d, "existing": existing}),
                        })
                        continue
                    # Merge use_case_ids that should link to this new product.
                    existing.setdefault("linking_use_case_ids", [])
                    new_ids = d.get("linking_use_case_ids") or []
                    if entry := _entry_key(d):
                        new_ids = [*new_ids, entry[1]] if entry not in [
                            ("use_case", i) for i in existing["linking_use_case_ids"]
                        ] else new_ids
                    existing["linking_use_case_ids"] = sorted(set(existing["linking_use_case_ids"]) | set(new_ids))
                else:
                    entry = _entry_key(d)
                    new_products[name_key] = {
                        **d,
                        "_agent": agent,
                        "linking_use_case_ids": sorted(set(
                            (d.get("linking_use_case_ids") or []) +
                            ([entry[1]] if entry and entry[0] == "use_case" else [])
                        )),
                        "linking_consolidated_ids": sorted(set(
                            (d.get("linking_consolidated_ids") or []) +
                            ([entry[1]] if entry and entry[0] == "consolidated" else [])
                        )),
                    }

            elif decision == "add_alias":
                key = (_norm(d.get("canonical_name")), _norm(d.get("proposed_alias")))
                if not key[0] or not key[1]:
                    conflicts.append({
                        "agent": agent, "reason": "add_alias missing canonical_name or proposed_alias",
                        "decision": json.dumps(d),
                    })
                    continue
                if key not in aliases:
                    aliases[key] = {**d, "_agent": agent}

            elif decision == "tighten_alias":
                # Record as alias change; the apply script handles tighten semantics.
                key = (_norm(d.get("canonical_name")), _norm(d.get("proposed_alias_replacement")))
                if not key[0]:
                    conflicts.append({
                        "agent": agent, "reason": "tighten_alias missing canonical_name",
                        "decision": json.dumps(d),
                    })
                    continue
                # Stored under same aliases dict but flagged via _kind.
                aliases.setdefault(key, {**d, "_agent": agent, "_kind": "tighten"})

            elif decision == "add_hierarchy_edge":
                key = (
                    _norm(d.get("child_canonical_name") or d.get("canonical_name")),
                    _norm(d.get("proposed_parent_canonical_name")),
                )
                if not key[0] or not key[1]:
                    conflicts.append({
                        "agent": agent, "reason": "add_hierarchy_edge missing child or parent",
                        "decision": json.dumps(d),
                    })
                    continue
                if key not in hierarchy:
                    hierarchy[key] = {**d, "_agent": agent}

            elif decision in {"false_positive", "unclear"}:
                # Recorded in summary; no CSV output.
                pass
            else:
                conflicts.append({
                    "agent": agent, "reason": f"unknown decision '{decision}'",
                    "decision": json.dumps(d),
                })

    # Also surface hierarchy edges that arrived embedded in `add_product` decisions.
    for name_key, d in new_products.items():
        parent = _norm(d.get("proposed_parent_canonical_name"))
        if parent:
            key = (name_key, parent)
            if key not in hierarchy:
                hierarchy[key] = {
                    "decision": "add_hierarchy_edge",
                    "child_canonical_name": d.get("proposed_canonical_name"),
                    "proposed_parent_canonical_name": d.get("proposed_parent_canonical_name"),
                    "confidence": d.get("confidence") or "medium",
                    "reasoning": f"derived from add_product by {d['_agent']}: {d.get('reasoning', '')}",
                    "_agent": d["_agent"],
                }

    # --- Write CSVs ---
    def write(path: Path, header: list[str], rows: list[dict[str, Any]]):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in header})
        print(f"wrote {len(rows):>4d} rows to {path.name}")

    write(
        OUT / "proposed_links.csv",
        ["entry_kind", "entry_id", "canonical_name", "evidence_quote", "confidence", "_agent"],
        [
            {
                "entry_kind": _entry_key(d)[0] if _entry_key(d) else "",
                "entry_id": _entry_key(d)[1] if _entry_key(d) else "",
                "canonical_name": d.get("canonical_name"),
                "evidence_quote": d.get("evidence_quote", "")[:300],
                "confidence": d.get("confidence") or "strong",
                "_agent": d["_agent"],
            }
            for d in links.values()
        ],
    )

    write(
        OUT / "proposed_new_products.csv",
        [
            "canonical_name", "vendor", "product_type", "is_generative_ai",
            "proposed_parent_canonical_name", "linking_use_case_ids",
            "linking_consolidated_ids", "confidence", "reasoning", "_agent",
        ],
        [
            {
                "canonical_name": d.get("proposed_canonical_name"),
                "vendor": d.get("vendor"),
                "product_type": d.get("product_type"),
                "is_generative_ai": d.get("is_generative_ai", 0),
                "proposed_parent_canonical_name": d.get("proposed_parent_canonical_name") or "",
                "linking_use_case_ids": ",".join(str(i) for i in d.get("linking_use_case_ids") or []),
                "linking_consolidated_ids": ",".join(str(i) for i in d.get("linking_consolidated_ids") or []),
                "confidence": d.get("confidence") or "medium",
                "reasoning": (d.get("reasoning") or "").replace("\n", " ")[:400],
                "_agent": d["_agent"],
            }
            for d in new_products.values()
        ],
    )

    write(
        OUT / "proposed_aliases.csv",
        ["canonical_name", "alias", "kind", "replaces", "evidence_quote", "_agent"],
        [
            {
                "canonical_name": d.get("canonical_name"),
                "alias": d.get("proposed_alias_replacement") or d.get("proposed_alias"),
                "kind": d.get("_kind") or "add",
                "replaces": (d.get("proposed_alias") or "") if d.get("_kind") == "tighten" else "",
                "evidence_quote": (d.get("evidence_quote") or "")[:300],
                "_agent": d["_agent"],
            }
            for d in aliases.values()
        ],
    )

    write(
        OUT / "proposed_hierarchy_edges.csv",
        ["child_canonical_name", "parent_canonical_name", "confidence", "reasoning", "_agent"],
        [
            {
                "child_canonical_name": d.get("child_canonical_name") or d.get("canonical_name"),
                "parent_canonical_name": d.get("proposed_parent_canonical_name"),
                "confidence": d.get("confidence") or "medium",
                "reasoning": (d.get("reasoning") or "").replace("\n", " ")[:300],
                "_agent": d["_agent"],
            }
            for d in hierarchy.values()
        ],
    )

    write(
        OUT / "conflicts.csv",
        ["agent", "reason", "decision"],
        conflicts,
    )

    # --- Summary ---
    summary = OUT / "summary.md"
    lines = [
        "# Linkage-pass integration summary",
        "",
        "## Decisions per agent",
        "",
        "| Agent | link | add_product | add_alias | tighten_alias | add_hierarchy_edge | false_positive | unclear | total |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for agent in ("agent_a", "agent_b", "agent_c", "agent_d"):
        d = decisions_by_agent[agent]
        total = sum(d.values())
        lines.append(
            f"| {agent} | {d.get('link', 0)} | {d.get('add_product', 0)} | "
            f"{d.get('add_alias', 0)} | {d.get('tighten_alias', 0)} | "
            f"{d.get('add_hierarchy_edge', 0)} | {d.get('false_positive', 0)} | "
            f"{d.get('unclear', 0)} | {total} |"
        )
    lines += [
        "",
        "## Integrated outputs",
        "",
        f"- proposed_links.csv          : {len(links)}",
        f"- proposed_new_products.csv   : {len(new_products)}",
        f"- proposed_aliases.csv        : {len(aliases)}",
        f"- proposed_hierarchy_edges.csv: {len(hierarchy)}",
        f"- conflicts.csv               : {len(conflicts)}",
        "",
    ]
    if conflicts:
        lines.append("⚠ Conflicts present — review `conflicts.csv` before applying.")
    summary.write_text("\n".join(lines))
    print(f"wrote summary to {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
