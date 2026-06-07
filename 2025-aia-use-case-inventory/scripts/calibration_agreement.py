"""Compute pairwise inter-rater agreement on the calibration set tagged
by Wave-1 subagents (per `docs/plans/2024-tagging/PLAN.md` §Calibration).

Pulls every `wave='0-calibration'` row from `use_case_tags_2024` and
computes, for each ordered agent-pair (A,B):

    pct_agree[field] = (count of use_case_id where A and B agree) /
                       (count of use_case_id where both A and B tagged)

For `deployment_scope` we apply the PLAN.md "tier shift" collapse: the
6-level ladder (enterprise_wide > department > bureau > office > team >
pilot) is collapsed so that adjacent-tier disagreements (e.g. bureau vs
office) do not count as disagreement, only shifts of more than one tier
(e.g. enterprise_wide vs office) do.

Writes a Markdown report to `audit/retag/2024-tagging/calibration.md`
with agreement matrices, headline thresholds, and the 10 rows with the
most divergence across agents (for rubric refinement).
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
DEFAULT_OUT = ROOT / "audit" / "retag" / "2024-tagging" / "calibration.md"

# Fields evaluated for agreement, with their PLAN.md thresholds.
THRESHOLDS = {
    "is_generative_ai": 0.85,
    "ai_sophistication": 0.70,
    "entry_type": 0.70,
    "deployment_scope": 0.70,
}

# PLAN.md tier ladder for deployment_scope. Adjacent-tier disagreement
# collapses to "agreed"; shifts of >1 tier remain disagreements.
SCOPE_TIERS = {
    "enterprise_wide": 0,
    "department": 1,
    "bureau": 2,
    "office": 3,
    "team": 4,
    "pilot": 5,
}


def _normalize_value(field: str, raw):
    if raw is None:
        return None
    v = str(raw).strip()
    if not v:
        return None
    if field in ("is_generative_ai",):
        return 1 if v in ("1", "True", "true", "yes") else 0
    return v


def _values_agree(field: str, a, b) -> bool:
    if a is None or b is None:
        return False  # treat missing-from-one-agent as disagreement
    if field == "deployment_scope":
        ai = SCOPE_TIERS.get(a)
        bi = SCOPE_TIERS.get(b)
        if ai is None or bi is None:
            return a == b
        return abs(ai - bi) <= 1
    return a == b


def _fetch_calibration_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        f"""
        SELECT
            use_case_id_2024,
            tagged_by_agent,
            {", ".join(THRESHOLDS.keys())}
        FROM use_case_tags_2024
        WHERE wave = '0-calibration'
        """
    ).fetchall()


def compute_agreement(rows: Iterable[sqlite3.Row]) -> dict:
    """Returns nested dict: result[field][(agentA, agentB)] = (agree, total, pct)."""
    rows = list(rows)
    # Index: by_uc[use_case_id] = {agent: {field: value}}
    by_uc: dict[int, dict[str, dict[str, object]]] = defaultdict(dict)
    agents: set[str] = set()
    for r in rows:
        uc = r["use_case_id_2024"]
        agent = r["tagged_by_agent"]
        agents.add(agent)
        by_uc[uc][agent] = {
            f: _normalize_value(f, r[f]) for f in THRESHOLDS
        }

    agent_pairs = sorted(combinations(sorted(agents), 2))
    result: dict = {f: {} for f in THRESHOLDS}
    for field in THRESHOLDS:
        for a, b in agent_pairs:
            agree = 0
            total = 0
            for uc, by_agent in by_uc.items():
                if a not in by_agent or b not in by_agent:
                    continue
                total += 1
                if _values_agree(field, by_agent[a][field], by_agent[b][field]):
                    agree += 1
            pct = (agree / total) if total else 0.0
            result[field][(a, b)] = (agree, total, pct)

    # Per-row divergence count — useful for the "10 most-divergent rows"
    # block in the report.
    per_uc_divergence: list[tuple[int, int]] = []
    for uc, by_agent in by_uc.items():
        if len(by_agent) < 2:
            continue
        diverged_fields = 0
        for field in THRESHOLDS:
            values = {by_agent[a][field] for a in by_agent}
            if len(values) > 1:
                # Apply scope tier collapse even here
                if field == "deployment_scope":
                    tier_set = {SCOPE_TIERS.get(v) for v in values if v is not None}
                    if len(tier_set) >= 2 and (max(tier_set) - min(tier_set)) > 1:
                        diverged_fields += 1
                else:
                    diverged_fields += 1
        per_uc_divergence.append((uc, diverged_fields))
    per_uc_divergence.sort(key=lambda x: -x[1])
    return {
        "agents": sorted(agents),
        "n_rows": len(by_uc),
        "field_results": result,
        "top_divergent": per_uc_divergence[:10],
    }


def _format_report(agg: dict, conn: sqlite3.Connection) -> str:
    lines: list[str] = []
    lines.append("# 2024 tagging calibration — agreement report")
    lines.append("")
    lines.append(
        f"- Agents: {', '.join(agg['agents']) if agg['agents'] else '(none)'}"
    )
    lines.append(f"- Calibration rows tagged: {agg['n_rows']}")
    lines.append("")
    lines.append("## Headline agreement (per field, averaged across agent pairs)")
    lines.append("")
    lines.append("| Field | Avg pairwise agreement | Threshold | Pass? |")
    lines.append("|---|---|---|---|")
    for field, threshold in THRESHOLDS.items():
        pairs = agg["field_results"][field].values()
        if not pairs:
            avg = 0.0
        else:
            avg = sum(p[2] for p in pairs) / len(pairs)
        passing = "✅" if avg >= threshold else "❌"
        lines.append(
            f"| `{field}` | {avg:.1%} | {threshold:.0%} | {passing} |"
        )
    lines.append("")

    lines.append("## Per-pair agreement (each cell = agreed / total comparable)")
    lines.append("")
    for field in THRESHOLDS:
        lines.append(f"### `{field}`")
        lines.append("")
        lines.append("| Agent A | Agent B | Agreed | Total | Pct |")
        lines.append("|---|---|---|---|---|")
        for (a, b), (agree, total, pct) in sorted(
            agg["field_results"][field].items()
        ):
            lines.append(f"| {a} | {b} | {agree} | {total} | {pct:.1%} |")
        lines.append("")

    lines.append("## 10 most-divergent calibration rows")
    lines.append("")
    if not agg["top_divergent"]:
        lines.append("_(No divergent rows — every agent agreed on every field.)_")
    else:
        lines.append("| use_case_id_2024 | # diverged fields | agency | name |")
        lines.append("|---|---|---|---|")
        for uc, n in agg["top_divergent"]:
            r = conn.execute(
                "SELECT agency_abbreviation, use_case_name "
                "FROM use_cases_2024 WHERE id = ?",
                (uc,),
            ).fetchone()
            ag = r["agency_abbreviation"] if r else "?"
            nm = (r["use_case_name"] if r else "?") or ""
            nm = nm.replace("|", "\\|")[:80]
            lines.append(f"| {uc} | {n} | {ag} | {nm} |")
    lines.append("")
    lines.append(
        "_Generated by `scripts/calibration_agreement.py`. See "
        "`docs/plans/2024-tagging/PLAN.md` for thresholds._"
    )
    return "\n".join(lines) + "\n"


def write_report(
    conn: sqlite3.Connection, out_path: Path = DEFAULT_OUT
) -> dict:
    rows = _fetch_calibration_rows(conn)
    agg = compute_agreement(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_format_report(agg, conn))
    return agg


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        agg = write_report(conn, args.out)
    finally:
        conn.close()
    print(f"wrote {args.out}")
    print(f"agents={agg['agents']}, n_rows={agg['n_rows']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
