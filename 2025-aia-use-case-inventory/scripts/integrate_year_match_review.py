"""Integrate the multi-agent year-match adjudication pass.

Phase 4 (Stage 3, step 1) of the 2024 ↔ 2025 AI use case inventory
comparison project (see `docs/plans/2024-vs-2025-comparison/PLAN.md`).

Reads every `audit/year_match_review/agent_*/recommendations.json`,
validates the decision schema, dedupes, flags conflicting decisions on a
slug, and writes the single committed source of record:

  audit/year_match_review/integration/proposed_lineage.csv
  audit/year_match_review/integration/conflicts.csv
  audit/year_match_review/integration/summary.md

`proposed_lineage.csv` columns:
  action, agency_abbreviation, uc_2024_slugs, uc_2025_slugs,
  confidence, reasoning

`uc_2024_slugs` / `uc_2025_slugs` are pipe-joined slug lists (a single
slug on the 1:1 actions, ≥2 on one side for split/merge).

Conflict rule: a slug must not receive conflicting decisions. Any 2024 or
2025 slug appearing in more than one decision is flagged to
`conflicts.csv` and ALL of its decisions are dropped from
`proposed_lineage.csv` so the apply step never sees an ambiguous slug.

Mirrors `scripts/integrate_linkage_pass.py` — no DB writes here; the apply
script consumes `proposed_lineage.csv`. Runs cleanly as a no-op when no
`agent_*/` directories exist yet (writes empty CSVs).
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PASS_DIR = ROOT / "audit" / "year_match_review"

# The valid decision actions and the slug-count shape each requires.
#   (min_2024, max_2024 | None, min_2025, max_2025 | None)
_ACTION_SHAPE: dict[str, tuple[int, int | None, int, int | None]] = {
    "confirm_rename": (1, 1, 1, 1),
    "reject_rename": (1, 1, 1, 1),
    "recover_match": (1, 1, 1, 1),
    "split": (1, 1, 2, None),
    "merge": (2, None, 1, 1),
}

_PROPOSED_COLUMNS = [
    "action", "agency_abbreviation", "uc_2024_slugs", "uc_2025_slugs",
    "confidence", "reasoning",
]

# A "definitive" decision asserts a final lineage for its slug(s): a rename
# (confirm/recover) or an N:M re-link (split/merge). `reject_rename` is NOT
# definitive — it only sends both slugs back to residual (retired_2024 /
# new_2025), from which a later `recover_match` can legitimately re-link
# one of them. See the supersede rule in conflict detection below.
_DEFINITIVE_ACTIONS = frozenset(
    {"confirm_rename", "recover_match", "split", "merge"}
)


def _resolve_inputs(pass_dir: Path) -> list[tuple[str, Path]]:
    """Auto-detect agent subdirectories holding `recommendations.json`.

    Returns (agent_label, file_path). Skips the non-agent subdirectories
    (`inputs`, `integration`, `review`). Returns [] when none exist yet —
    the script then writes empty integration CSVs (a clean no-op).
    """
    out: list[tuple[str, Path]] = []
    if not pass_dir.exists():
        return out
    for sub in sorted(pass_dir.iterdir()):
        if not sub.is_dir() or sub.name in {"inputs", "integration", "review"}:
            continue
        rec = sub / "recommendations.json"
        if rec.exists():
            out.append((sub.name, rec))
    return out


def _load(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        print(f"WARN: missing {path}")
        return []
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} did not contain a JSON array")
    return data


def _as_slug_list(value: Any) -> list[str]:
    """Coerce a decision's slug field to a clean list of non-empty slugs.

    Accepts a JSON list (the schema) or a single string / pipe-joined
    string (tolerated for hand-authored input)."""
    if value is None:
        return []
    if isinstance(value, str):
        parts = value.split("|") if "|" in value else [value]
    elif isinstance(value, (list, tuple)):
        parts = list(value)
    else:
        parts = [value]
    return [str(p).strip() for p in parts if str(p).strip()]


def _validate(d: dict[str, Any]) -> tuple[str, list[str], list[str]] | str:
    """Validate one decision. Returns (action, slugs_2024, slugs_2025) on
    success, or an error-reason string on failure."""
    action = str(d.get("action") or "").strip()
    if action not in _ACTION_SHAPE:
        return f"unknown action '{action}'"
    s2024 = _as_slug_list(d.get("uc_2024_slugs"))
    s2025 = _as_slug_list(d.get("uc_2025_slugs"))
    lo24, hi24, lo25, hi25 = _ACTION_SHAPE[action]
    if not (lo24 <= len(s2024) and (hi24 is None or len(s2024) <= hi24)):
        return f"{action}: uc_2024_slugs count {len(s2024)} out of range"
    if not (lo25 <= len(s2025) and (hi25 is None or len(s2025) <= hi25)):
        return f"{action}: uc_2025_slugs count {len(s2025)} out of range"
    if len(set(s2024)) != len(s2024) or len(set(s2025)) != len(s2025):
        return f"{action}: duplicate slug within one decision"
    return (action, s2024, s2025)


def integrate(pass_dir: Path) -> dict[str, Any]:
    """Read agent JSONs, validate, dedupe, write the integration CSVs.

    Returns a small result dict for the summary / tests:
      {proposed: [...], conflicts: [...], by_action: {...}}
    """
    out_dir = pass_dir / "integration"
    out_dir.mkdir(parents=True, exist_ok=True)
    agent_inputs = _resolve_inputs(pass_dir)
    print(f"reading {len(agent_inputs)} agent file(s) from {pass_dir}")

    # Stage 1: collect every valid decision, tag with its agent.
    decisions: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    by_action: dict[str, int] = defaultdict(int)
    by_agent: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for agent, path in agent_inputs:
        for d in _load(path):
            result = _validate(d)
            if isinstance(result, str):
                conflicts.append({
                    "agent": agent, "reason": result, "decision": json.dumps(d),
                })
                continue
            action, s2024, s2025 = result
            by_action[action] += 1
            by_agent[agent][action] += 1
            decisions.append({
                "_agent": agent,
                "action": action,
                "agency_abbreviation": str(d.get("agency_abbreviation") or "").strip(),
                "uc_2024_slugs": s2024,
                "uc_2025_slugs": s2025,
                "confidence": str(d.get("confidence") or "").strip() or "medium",
                "reasoning": str(d.get("reasoning") or "").replace("\n", " ").strip(),
            })

    # Stage 2: conflict detection — every 2024 / 2025 slug must appear in
    # at most one *definitive* decision.
    #
    # Supersede rule: a `recover_match` / `confirm_rename` (and `split` /
    # `merge`) supersedes a `reject_rename` that shares a slug. This is NOT
    # a conflict — the reject correctly rejected a *different* pair and
    # sent the slug to residual; the definitive decision then legitimately
    # re-links that freed slug. The apply step orders reject_rename before
    # recover_match so the recover operates on the freed slug. Both
    # decisions are kept; only the definitive one's lineage is final.
    #
    # A genuine conflict — flagged, all touching decisions dropped — is
    # still: (a) ≥2 *definitive* decisions on one slug (e.g. two confirms,
    # two recovers, a confirm + a recover), or (b) ≥2 reject_rename on one
    # slug. Those are truly ambiguous and the apply step must not see them.
    slug_users_2024: dict[str, list[int]] = defaultdict(list)
    slug_users_2025: dict[str, list[int]] = defaultdict(list)
    for i, dec in enumerate(decisions):
        for s in dec["uc_2024_slugs"]:
            slug_users_2024[s].append(i)
        for s in dec["uc_2025_slugs"]:
            slug_users_2025[s].append(i)

    conflicted_idx: set[int] = set()

    def _flag_conflicts(slug_users: dict[str, list[int]], side: str) -> None:
        for slug, users in slug_users.items():
            if len(users) < 2:
                continue
            n_definitive = sum(
                1 for i in users
                if decisions[i]["action"] in _DEFINITIVE_ACTIONS
            )
            n_reject = sum(
                1 for i in users
                if decisions[i]["action"] == "reject_rename"
            )
            # Supersede case: exactly one definitive decision alongside
            # exactly one reject → not a conflict, both decisions are kept
            # (all 5 actions are either definitive or reject_rename, so for
            # len(users) >= 2 this is the only non-conflicting shape).
            if n_definitive <= 1 and n_reject <= 1:
                continue
            conflicted_idx.update(users)
            conflicts.append({
                "agent": ";".join(sorted({decisions[i]["_agent"] for i in users})),
                "reason": f"{side} slug '{slug}' claimed by "
                          f"{n_definitive} definitive + {n_reject} reject decision(s)",
                "decision": json.dumps([decisions[i]["action"] for i in users]),
            })

    _flag_conflicts(slug_users_2024, "2024")
    _flag_conflicts(slug_users_2025, "2025")

    proposed = [
        {
            "action": dec["action"],
            "agency_abbreviation": dec["agency_abbreviation"],
            "uc_2024_slugs": "|".join(dec["uc_2024_slugs"]),
            "uc_2025_slugs": "|".join(dec["uc_2025_slugs"]),
            "confidence": dec["confidence"],
            "reasoning": dec["reasoning"][:600],
        }
        for i, dec in enumerate(decisions)
        if i not in conflicted_idx
    ]
    # Deterministic order so the committed CSV diffs cleanly.
    proposed.sort(key=lambda r: (r["agency_abbreviation"], r["action"],
                                 r["uc_2024_slugs"], r["uc_2025_slugs"]))

    def _write(path: Path, header: list[str], rows: list[dict[str, Any]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in header})
        print(f"wrote {len(rows):>4d} rows to {path.name}")

    _write(out_dir / "proposed_lineage.csv", _PROPOSED_COLUMNS, proposed)
    _write(out_dir / "conflicts.csv", ["agent", "reason", "decision"], conflicts)

    # --- summary.md ---
    lines = [
        "# Year-match review integration summary",
        "",
        "## Decisions per agent",
        "",
        "| Agent | confirm_rename | reject_rename | recover_match | split | merge | total |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for agent in sorted(by_agent):
        d = by_agent[agent]
        total = sum(d.values())
        lines.append(
            f"| {agent} | {d.get('confirm_rename', 0)} | "
            f"{d.get('reject_rename', 0)} | {d.get('recover_match', 0)} | "
            f"{d.get('split', 0)} | {d.get('merge', 0)} | {total} |"
        )
    lines += [
        "",
        "## Integrated output",
        "",
        f"- proposed_lineage.csv : {len(proposed)} decisions",
        f"- conflicts.csv        : {len(conflicts)}",
        "",
    ]
    if conflicts:
        lines.append("⚠ Conflicts present — review `conflicts.csv` before applying.")
    (out_dir / "summary.md").write_text("\n".join(lines))
    print(f"wrote summary to {out_dir / 'summary.md'}")

    return {
        "proposed": proposed,
        "conflicts": conflicts,
        "by_action": dict(by_action),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pass-dir", type=Path, default=DEFAULT_PASS_DIR,
        help="Audit-pass directory (parent of agent subdirs and integration/).",
    )
    args = parser.parse_args(argv)
    integrate(args.pass_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
