"""Check `use_case_tags_2024_canonical` for tag-logic invariant violations.

Runs 11 invariant rules against every canonical tag row and writes every
violation to `audit/retag/2024-tagging-verification/invariants.csv`.

Severity:
  impossible  — logically contradictory; must be fixed before dashboard use
  suspicious  — likely wrong but may have an edge-case explanation

Usage:
    python3 scripts/check_2024_tag_invariants.py
    python3 scripts/check_2024_tag_invariants.py --db path/to/alt.db
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
DEFAULT_OUT = (
    ROOT / "audit" / "retag" / "2024-tagging-verification" / "invariants.csv"
)

# Non-generative sophistication buckets — cannot coexist with is_generative_ai.
NON_GENAI_SOPHISTICATIONS = frozenset(
    {"classical_ml", "computer_vision", "predictive_analytics"}
)

OUTPUT_FIELDS = (
    "invariant_id",
    "severity",
    "description",
    "use_case_id_2024",
    "wave",
    "agency_abbreviation",
    "use_case_name",
    "entry_type",
    "is_generative_ai",
    "ai_sophistication",
    "deployment_scope",
    "is_enterprise_wide",
    "is_general_llm_access",
    "is_coding_tool",
    "is_cots_commercial",
    "is_microsoft_copilot",
    "is_openai",
    "is_anthropic",
    "is_github_copilot",
    "tool_product_name",
    "tool_vendor",
    "confidence",
)


@dataclass
class Violation:
    invariant_id: int
    severity: str
    description: str
    row: dict
    extra: dict = field(default_factory=dict)

    def to_csv_row(self) -> dict:
        d: dict = {
            "invariant_id": self.invariant_id,
            "severity": self.severity,
            "description": self.description,
        }
        for f in OUTPUT_FIELDS:
            if f in ("invariant_id", "severity", "description"):
                continue
            d[f] = self.row.get(f, "")
        d.update(self.extra)
        return d


def _i(v) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _s(v) -> str:
    return str(v).strip() if v is not None else ""


def check_row(row: dict) -> list[Violation]:
    violations: list[Violation] = []

    genai = _i(row.get("is_generative_ai"))
    sophistication = _s(row.get("ai_sophistication"))
    llm_access = _i(row.get("is_general_llm_access"))
    enterprise_wide = _i(row.get("is_enterprise_wide"))
    scope = _s(row.get("deployment_scope"))
    copilot = _i(row.get("is_microsoft_copilot"))
    openai = _i(row.get("is_openai"))
    anthropic = _i(row.get("is_anthropic"))
    github_copilot = _i(row.get("is_github_copilot"))
    coding = _i(row.get("is_coding_tool"))
    cots = _i(row.get("is_cots_commercial"))
    vendor = _s(row.get("tool_vendor")).lower()
    product = _s(row.get("tool_product_name"))
    entry = _s(row.get("entry_type"))
    confidence = _s(row.get("confidence"))

    # 1 — generative AI + non-generative sophistication (impossible)
    if genai == 1 and sophistication in NON_GENAI_SOPHISTICATIONS:
        violations.append(Violation(
            1, "impossible",
            f"is_generative_ai=1 but ai_sophistication='{sophistication}'",
            row,
        ))

    # 2 — general LLM access requires generative AI (impossible)
    if llm_access == 1 and genai != 1:
        violations.append(Violation(
            2, "impossible",
            f"is_general_llm_access=1 but is_generative_ai={genai}",
            row,
        ))

    # 3 — is_enterprise_wide ↔ deployment_scope='enterprise_wide' (impossible both ways)
    if enterprise_wide == 1 and scope != "enterprise_wide":
        violations.append(Violation(
            3, "impossible",
            f"is_enterprise_wide=1 but deployment_scope='{scope}'",
            row,
        ))
    if enterprise_wide != 1 and scope == "enterprise_wide":
        violations.append(Violation(
            3, "impossible",
            f"deployment_scope='enterprise_wide' but is_enterprise_wide={enterprise_wide}",
            row,
        ))

    # 4 — is_microsoft_copilot ⇒ vendor contains 'microsoft' (suspicious)
    if copilot == 1 and "microsoft" not in vendor:
        violations.append(Violation(
            4, "suspicious",
            f"is_microsoft_copilot=1 but tool_vendor='{_s(row.get('tool_vendor'))}'",
            row,
        ))

    # 5 — is_openai ⇒ vendor contains 'openai' or 'microsoft' (suspicious;
    #     microsoft/azure openai is a valid openai deployment channel)
    if openai == 1 and "openai" not in vendor and "microsoft" not in vendor:
        violations.append(Violation(
            5, "suspicious",
            f"is_openai=1 but tool_vendor='{_s(row.get('tool_vendor'))}'",
            row,
        ))

    # 6 — is_anthropic ⇒ vendor contains 'anthropic' (suspicious)
    if anthropic == 1 and "anthropic" not in vendor:
        violations.append(Violation(
            6, "suspicious",
            f"is_anthropic=1 but tool_vendor='{_s(row.get('tool_vendor'))}'",
            row,
        ))

    # 7 — is_github_copilot ⇒ is_coding_tool (impossible)
    if github_copilot == 1 and coding != 1:
        violations.append(Violation(
            7, "impossible",
            f"is_github_copilot=1 but is_coding_tool={coding}",
            row,
        ))

    # 8 — is_coding_tool + generic_use_pattern ⇒ sophistication should be
    #     coding_assistant or general_llm (suspicious if it's something else)
    if (
        coding == 1
        and entry == "generic_use_pattern"
        and sophistication
        and sophistication not in ("coding_assistant", "general_llm", "agentic")
    ):
        violations.append(Violation(
            8, "suspicious",
            f"is_coding_tool=1 + entry_type='generic_use_pattern' "
            f"but ai_sophistication='{sophistication}'",
            row,
        ))

    # 9 — entry_type='product_deployment' + no tool_product_name (suspicious)
    if entry == "product_deployment" and not product:
        violations.append(Violation(
            9, "suspicious",
            "entry_type='product_deployment' but tool_product_name is empty",
            row,
        ))

    # 10 — is_cots_commercial=1 + no tool_product_name (suspicious)
    if cots == 1 and not product:
        violations.append(Violation(
            10, "suspicious",
            "is_cots_commercial=1 but tool_product_name is empty",
            row,
        ))

    # 11 — confidence='high' + no entry_type (suspicious: high-confidence
    #      but missing the most basic classification)
    if confidence == "high" and not entry:
        violations.append(Violation(
            11, "suspicious",
            "confidence='high' but entry_type is empty",
            row,
        ))

    return violations


def run(conn: sqlite3.Connection, out_path: Path = DEFAULT_OUT) -> dict[str, int]:
    """Check all canonical rows, write violations CSV. Returns summary counts."""
    rows = conn.execute(
        """
        SELECT
            c.use_case_id_2024,
            c.wave,
            u.agency_abbreviation,
            u.use_case_name,
            c.entry_type,
            c.is_generative_ai,
            c.ai_sophistication,
            c.deployment_scope,
            c.is_enterprise_wide,
            c.is_general_llm_access,
            c.is_coding_tool,
            c.is_cots_commercial,
            c.tool_product_name,
            c.tool_vendor,
            c.is_microsoft_copilot,
            c.is_openai,
            c.is_anthropic,
            c.is_github_copilot,
            c.confidence
        FROM use_case_tags_2024_canonical c
        JOIN use_cases_2024 u ON u.id = c.use_case_id_2024
        ORDER BY c.use_case_id_2024
        """
    ).fetchall()

    all_violations: list[Violation] = []
    for r in rows:
        d = dict(r)
        all_violations.extend(check_row(d))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for v in all_violations:
            writer.writerow(v.to_csv_row())

    impossible = sum(1 for v in all_violations if v.severity == "impossible")
    suspicious = sum(1 for v in all_violations if v.severity == "suspicious")

    by_invariant: dict[int, int] = {}
    for v in all_violations:
        by_invariant[v.invariant_id] = by_invariant.get(v.invariant_id, 0) + 1

    return {
        "total_rows": len(rows),
        "total_violations": len(all_violations),
        "impossible": impossible,
        "suspicious": suspicious,
        "by_invariant": by_invariant,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        counts = run(conn, args.out)
    finally:
        conn.close()

    print(f"rows checked  : {counts['total_rows']}")
    print(f"violations    : {counts['total_violations']}")
    print(f"  impossible  : {counts['impossible']}")
    print(f"  suspicious  : {counts['suspicious']}")
    print()
    print("by invariant:")
    for inv_id, n in sorted(counts["by_invariant"].items()):
        print(f"  rule {inv_id:2d}: {n}")
    print()
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
