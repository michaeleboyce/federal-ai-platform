"""Apply the integration_depth_2026-07 verdicts to use_case_tags.integration_depth.

Labels how deeply each pilot/deployed individually-reported use case is
wired into agency work, in the closed vocabulary {standalone_chat,
workflow_embedded, system_integrated, agentic_workflow, unclear} (see the
round's INSTRUCTIONS.md). This measures what the OMB M-25-21 format does
not collect; NULL on a row means "outside the labeled population"
(pre-deployment / retired / unknown stage at label time), which is
distinct from 'unclear' (labeled, but the narrative doesn't say).

Fable audit overrides (audit_overrides*.csv, rows with override_verdict
set) take precedence over labeler verdicts.

Rows are keyed by (agency, use_case_name) signature — never numeric ids —
resolved via scripts/uc_signature.py; unresolved rows hard-fail above 2%.
Idempotent: recomputes every labeled row's value on each run (the fix
chain re-runs it after auto_tag.py rebuilds the tags).

Default: dry-run. Pass --apply to write (the Makefile does).
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uc_signature import Resolver, _norm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
PASS_DIR = ROOT / "audit" / "retag" / "integration_depth_2026-07"

VALID_VERDICTS = {
    "standalone_chat",
    "workflow_embedded",
    "system_integrated",
    "agentic_workflow",
    "unclear",
}


def _verdict_rows(directory: Path) -> list[dict]:
    rows: list[dict] = []
    for f in sorted(directory.glob("verdicts_*.csv")):
        with open(f) as fh:
            rows.extend(csv.DictReader(fh))
    return rows


def _override_map(directory: Path) -> dict[tuple[str, str], str]:
    """(norm_agency, norm_name) -> override verdict, from the Fable audit.

    Globs audit_overrides*.csv so per-batch audit files (written
    concurrently by the audit agents) and a single merged file both work.
    """
    out: dict[tuple[str, str], str] = {}
    for path in sorted(directory.glob("audit_overrides*.csv")):
        with open(path) as fh:
            for row in csv.DictReader(fh):
                override = (row.get("override_verdict") or "").strip().lower()
                if override:
                    out[(_norm(row["agency"]), _norm(row["use_case_name"]))] = override
    return out


def _coverage(directory: Path, verdicts: list[dict]) -> str:
    input_keys = {
        (_norm(r["agency"]), _norm(r["use_case_name"]))
        for r in csv.DictReader(open(directory / "input.csv"))
    }
    seen = {(_norm(r["agency"]), _norm(r["use_case_name"])) for r in verdicts}
    missing = len(input_keys - seen)
    extra = len(seen - input_keys)
    msg = f"{len(input_keys) - missing}/{len(input_keys)} input rows covered"
    if missing:
        msg += f" — {missing} STILL PENDING (re-run the missing review batches)"
    if extra:
        msg += f" — {extra} verdict signatures NOT IN INPUT (check for edited names)"
    return msg


def apply_integration_depth(
    conn: sqlite3.Connection, res: Resolver, apply: bool
) -> dict:
    stats = {"set": 0, "unchanged": 0, "overridden": 0, "invalid": 0}
    overrides = _override_map(PASS_DIR)
    for row in _verdict_rows(PASS_DIR):
        key = (_norm(row["agency"]), _norm(row["use_case_name"]))
        verdict = (row.get("verdict") or "").strip().lower()
        if key in overrides:
            verdict = overrides[key]
            stats["overridden"] += 1
        if verdict not in VALID_VERDICTS:
            stats["invalid"] += 1
            continue
        for uc_id in res.uc(None, row["agency"], row["use_case_name"]):
            cur = conn.execute(
                "SELECT integration_depth FROM use_case_tags WHERE use_case_id = ?",
                (uc_id,),
            ).fetchone()
            if cur is None:
                continue
            if cur[0] == verdict:
                stats["unchanged"] += 1
            else:
                if apply:
                    conn.execute(
                        "UPDATE use_case_tags SET integration_depth = ? WHERE use_case_id = ?",
                        (verdict, uc_id),
                    )
                stats["set"] += 1
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    ap.add_argument("--db", default=str(DB_PATH))
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        verdicts = _verdict_rows(PASS_DIR)
        if not verdicts:
            print("[integration_depth] WARNING: no verdict files yet — skipped")
            return 0
        res = Resolver(conn)
        with conn:
            stats = apply_integration_depth(conn, res, args.apply)
        mode = "APPLIED" if args.apply else "DRY-RUN"
        print(f"[integration_depth] {mode} {stats} | {_coverage(PASS_DIR, verdicts)}")
        res.check("apply_integration_depth")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
