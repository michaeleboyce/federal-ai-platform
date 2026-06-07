"""Load agent-produced tag CSVs into `use_case_tags_2024`.

Inputs: one or more CSV files (or a directory of CSVs) produced by Wave
0-calibration / 1 / 2a / 2b / 3 subagents. Each row corresponds to one
tag of one use case by one agent.

Idempotent on `(use_case_id_2024, wave, tagged_by_agent)`: re-running an
agent's CSV updates that agent's existing row instead of duplicating.

Usage:
    python3 scripts/load_2024_tags.py --wave 1 audit/retag/2024-tagging/wave1/
    python3 scripts/load_2024_tags.py --wave 0-calibration path/to/dir
    python3 scripts/load_2024_tags.py --wave 1 --check path/to/dir   # dry-run

See `docs/plans/2024-tagging/PLAN.md` and `migrations/m014_use_case_tags_2024.py`.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"

VALID_WAVES = {"0-calibration", "1", "2a", "2b", "3"}

# Columns that map straight into use_case_tags_2024 (excluding id /
# created_at / updated_at which the DB manages, and excluding
# use_case_id_2024 / wave / tagged_by_agent which are unique-key columns).
TAG_TEXT_COLUMNS = (
    "entry_type",
    "product_capability",
    "tool_product_name",
    "tool_vendor",
    "ai_sophistication",
    "deployment_scope",
    "scope_detail",
    "estimated_user_count",
    "architecture_type",
    "cots_product_name",
    "cots_vendor",
    "use_type",
    "high_impact_designation",
    "deployment_environment",
    "reasoning",
    "quality_flags_json",
    "confidence",
)

TAG_INT_COLUMNS = (
    "is_product_capability_entry",
    "is_general_llm_access",
    "is_coding_tool",
    "is_cots_commercial",
    "is_generative_ai",
    "is_frontier_model",
    "is_enterprise_wide",
    "has_model_training",
    "is_microsoft_copilot",
    "is_openai",
    "is_anthropic",
    "is_google",
    "is_github_copilot",
    "is_aws_ai",
    "is_public_facing",
    "has_meaningful_risk_docs",
    "has_ato_or_fedramp",
)

REQUIRED_COLUMNS = ("use_case_id_2024", "tagged_by_agent")

# Enum constraints. Empty / None is always allowed (the field is then
# treated as unknown). Mirrors the comments on `use_case_tags` in db.py.
ENUM_VALUES = {
    "entry_type": {
        "generic_use_pattern",
        "product_deployment",
        "product_feature",
        "custom_system",
        "bespoke_application",
    },
    "ai_sophistication": {
        "general_llm",
        "coding_assistant",
        "agentic",
        "classical_ml",
        "computer_vision",
        "nlp_specific",
        "predictive_analytics",
    },
    "deployment_scope": {
        "enterprise_wide",
        "department",
        "bureau",
        "office",
        "team",
        "pilot",
    },
    "architecture_type": {
        "inference_only",
        "rag_pipeline",
        "fine_tuned",
        "custom_trained",
        "agentic_workflow",
        "unknown",
    },
    "use_type": {
        "mission_critical",
        "administrative",
        "it_operations",
        "cybersecurity",
        "research",
    },
    "confidence": {"low", "medium", "high"},
}


def _to_int(v) -> int | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    sl = s.lower()
    if sl in ("true", "yes", "y"):
        return 1
    if sl in ("false", "no", "n"):
        return 0
    try:
        return int(s)
    except ValueError:
        raise ValueError(f"expected int/bool, got {v!r}")


def _opt(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _csv_paths(input_path: Path) -> list[Path]:
    if input_path.is_dir():
        return sorted(input_path.glob("*.csv"))
    return [input_path]


def _validate_row(row: dict, wave: str, line_no: int, source: Path) -> None:
    for col in REQUIRED_COLUMNS:
        if not (row.get(col) or "").strip():
            raise ValueError(
                f"{source}:{line_no}: missing required column {col!r}"
            )
    for col, allowed in ENUM_VALUES.items():
        v = (row.get(col) or "").strip()
        if v and v not in allowed:
            raise ValueError(
                f"{source}:{line_no}: invalid {col}={v!r}; "
                f"allowed: {sorted(allowed)}"
            )


def load(
    conn: sqlite3.Connection,
    wave: str,
    csv_paths: list[Path],
) -> int:
    """Upsert tag rows from CSVs. Returns number of rows written."""
    if wave not in VALID_WAVES:
        raise ValueError(f"invalid wave {wave!r}; expected one of {sorted(VALID_WAVES)}")

    valid_ids = {
        r[0] for r in conn.execute("SELECT id FROM use_cases_2024").fetchall()
    }

    n_written = 0
    for path in csv_paths:
        with path.open(newline="") as f:
            reader = csv.DictReader(f)
            for line_no, row in enumerate(reader, start=2):
                _validate_row(row, wave, line_no, path)
                use_case_id = _to_int(row["use_case_id_2024"])
                if use_case_id not in valid_ids:
                    raise ValueError(
                        f"{path}:{line_no}: unknown use_case_id_2024={use_case_id}"
                    )
                agent = row["tagged_by_agent"].strip()

                cols = ["use_case_id_2024", "wave", "tagged_by_agent"]
                vals: list = [use_case_id, wave, agent]
                for c in TAG_TEXT_COLUMNS:
                    cols.append(c)
                    vals.append(_opt(row.get(c, "")))
                for c in TAG_INT_COLUMNS:
                    cols.append(c)
                    vals.append(_to_int(row.get(c, "")))
                cols.append("updated_at")
                vals.append("datetime('now')")  # placeholder; replaced below

                # Build INSERT ... ON CONFLICT DO UPDATE so re-runs of the
                # same agent's CSV refresh that agent's row rather than
                # duplicate-key-error.
                placeholders = ",".join(["?"] * (len(cols) - 1)) + ",datetime('now')"
                update_cols = [c for c in cols if c not in (
                    "use_case_id_2024", "wave", "tagged_by_agent"
                )]
                update_set = ",".join(
                    f"{c}=excluded.{c}" if c != "updated_at"
                    else "updated_at=datetime('now')"
                    for c in update_cols
                )
                sql = (
                    f"INSERT INTO use_case_tags_2024 ({','.join(cols)}) "
                    f"VALUES ({placeholders}) "
                    f"ON CONFLICT(use_case_id_2024, wave, tagged_by_agent) "
                    f"DO UPDATE SET {update_set}"
                )
                # Drop the trailing 'updated_at' placeholder value; the SQL
                # uses datetime('now') literal for it.
                conn.execute(sql, vals[:-1])
                n_written += 1
    return n_written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wave", required=True, choices=sorted(VALID_WAVES))
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--check", action="store_true", help="dry-run; rollback")
    ap.add_argument("input", type=Path, help="CSV file or directory of CSVs")
    args = ap.parse_args()

    csv_paths = _csv_paths(args.input)
    if not csv_paths:
        print(f"no CSVs found at {args.input}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        n = load(conn, args.wave, csv_paths)
        if args.check:
            conn.rollback()
            print(f"[check] would write {n} rows (wave {args.wave})")
        else:
            conn.commit()
            print(f"wrote {n} rows (wave {args.wave})")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
