"""Build Wave 2 QA input CSVs from Wave 1 tags + matched 2025 row tags.

Wave 2a inputs (matched-pair QA against 2025 mirror):
- `continued.csv` — 1,139 rows where `use_case_year_links.lineage_status='continued'`
- `renamed_split.csv` — 286 rows where `lineage_status IN ('renamed','split')`

Wave 2b inputs (unmatched-2024 sanity):
- `retired.csv` — 710 rows where `lineage_status='retired_2024'`

Per `docs/plans/2024-tagging/PLAN.md` §Wave 2:
- 2a agents compare the 2024 Wave-1 tags against the corresponding 2025
  `use_case_tags` row and emit `quality_flags_json` describing the
  divergence (`drift_legitimate` | `tagging_error_2024` | `tagging_error_2025`
  | `material_divergence`).
- 2b agents check internal consistency of the Wave-1 tag (no 2025 to
  compare against) and re-confirm `tool_product_name` / `tool_vendor`.

The CSVs include the 2024 narrative, the 2024 Wave-1 tags, AND (for 2a)
the matched 2025 row + its tags. This is the ONE place where 2024 tagging
work is explicitly allowed to see the 2025 mirror.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
DEFAULT_OUT = ROOT / "audit" / "retag" / "2024-tagging"

# Fields from use_case_tags_2024 (Wave 1) included in Wave 2 input CSVs.
WAVE1_TAG_FIELDS = (
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
    "confidence",
    "reasoning",
)

# Fields from the matched 2025 use_case_tags row (only used in Wave 2a).
# Same shape so the agent can compare side-by-side.
TAGS_2025_FIELDS = (
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
)


def _wave1_canonical_rows(conn: sqlite3.Connection) -> dict[int, dict]:
    """Return {use_case_id_2024 -> dict of Wave-1 tag fields}.

    Wave 1 has exactly one row per use case (each agent tagged their
    partition), so this is straightforward.
    """
    cols = ", ".join(WAVE1_TAG_FIELDS)
    rows = conn.execute(
        f"SELECT use_case_id_2024, tagged_by_agent, {cols} "
        f"FROM use_case_tags_2024 WHERE wave='1'"
    ).fetchall()
    return {
        r["use_case_id_2024"]: dict(r)
        for r in rows
    }


def _build_2a(conn: sqlite3.Connection, lineage_filter: str) -> list[dict]:
    """Emit one row per (2024 uc, 2025 uc) pair matching `lineage_filter`.

    `lineage_filter` is a SQL fragment such as `"lineage_status='continued'"`
    or `"lineage_status IN ('renamed','split')"`.
    """
    wave1 = _wave1_canonical_rows(conn)

    sql = f"""
        SELECT
            l.uc_2024_id, l.uc_2025_id, l.lineage_status,
            u24.agency_abbreviation, u24.bureau,
            u24.use_case_name AS name_2024,
            u24.purpose_benefits, u24.outputs,
            u24.commercial_ai, u24.dev_method, u24.dev_stage,
            u25.use_case_name AS name_2025,
            u25.problem_statement AS problem_statement_2025,
            u25.expected_benefits AS expected_benefits_2025,
            u25.system_outputs AS system_outputs_2025,
            u25.ai_classification AS ai_classification_2025,
            u25.vendor_name AS vendor_name_2025,
            u25.system_name AS system_name_2025,
            u25.bureau_component AS bureau_2025,
            { ", ".join(f"t25.{f} AS {f}_2025" for f in TAGS_2025_FIELDS) }
        FROM use_case_year_links l
        JOIN use_cases_2024 u24 ON u24.id = l.uc_2024_id
        JOIN use_cases u25 ON u25.id = l.uc_2025_id
        LEFT JOIN use_case_tags t25 ON t25.use_case_id = u25.id
        WHERE {lineage_filter}
        ORDER BY l.uc_2024_id
    """
    rows = conn.execute(sql).fetchall()
    out: list[dict] = []
    for r in rows:
        d = dict(r)
        # Splice in Wave 1 tag fields with `_2024` suffix
        w1 = wave1.get(d["uc_2024_id"], {})
        for f in WAVE1_TAG_FIELDS:
            d[f"{f}_2024"] = w1.get(f)
        d["tagged_by_agent_2024"] = w1.get("tagged_by_agent")
        out.append(d)
    return out


def _build_2b(conn: sqlite3.Connection) -> list[dict]:
    """Emit one row per retired_2024 use case (no 2025 to compare against)."""
    wave1 = _wave1_canonical_rows(conn)
    rows = conn.execute(
        """
        SELECT
            l.uc_2024_id,
            u.agency_abbreviation, u.bureau,
            u.use_case_name, u.purpose_benefits, u.outputs,
            u.commercial_ai, u.dev_method, u.dev_stage
        FROM use_case_year_links l
        JOIN use_cases_2024 u ON u.id = l.uc_2024_id
        WHERE l.lineage_status='retired_2024'
        ORDER BY l.uc_2024_id
        """
    ).fetchall()
    out: list[dict] = []
    for r in rows:
        d = dict(r)
        w1 = wave1.get(d["uc_2024_id"], {})
        for f in WAVE1_TAG_FIELDS:
            d[f"{f}_2024"] = w1.get(f)
        d["tagged_by_agent_2024"] = w1.get("tagged_by_agent")
        out.append(d)
    return out


def _write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        # Write header-only file so the loader/agent don't error on missing.
        with path.open("w", newline="") as f:
            f.write("")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def build(conn: sqlite3.Connection, out_dir: Path = DEFAULT_OUT) -> dict[str, int]:
    counts: dict[str, int] = {}

    continued = _build_2a(conn, "l.lineage_status='continued'")
    _write_csv(continued, out_dir / "wave2a_inputs" / "continued.csv")
    counts["wave2a/continued"] = len(continued)

    renamed_split = _build_2a(conn, "l.lineage_status IN ('renamed','split')")
    _write_csv(renamed_split, out_dir / "wave2a_inputs" / "renamed_split.csv")
    counts["wave2a/renamed_split"] = len(renamed_split)

    retired = _build_2b(conn)
    _write_csv(retired, out_dir / "wave2b_inputs" / "retired.csv")
    counts["wave2b/retired"] = len(retired)

    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        counts = build(conn, args.out)
    finally:
        conn.close()

    for k, v in counts.items():
        print(f"  {k}: {v} rows")
    print(f"total: {sum(counts.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
