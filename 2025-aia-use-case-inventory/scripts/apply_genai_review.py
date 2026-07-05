"""Apply the 2026-07 genai_review verdicts to use_case_tags.is_generative_ai.

Adjudicates every 2025 row where the keyword-derived `is_generative_ai`
flag disagreed with the agency's own filed classification (see
audit/retag/genai_review_2026-07/INSTRUCTIONS.md for the decision rule
and cohorts). Each verdicts_*.csv row sets the flag to 1 (verdict=genai)
or 0 (verdict=not_genai).

Invariant repair (mirrors apply_2024_tag_corrections.py): when a verdict
flips a row TO genai=1 while its ai_sophistication is a bucket that
cannot coexist with generative AI ({classical_ml, computer_vision,
predictive_analytics}), the sophistication is bumped to 'general_llm'
and the repair is counted in the stats.

Ordering note: this runs in the `make fix` chain BEFORE
scripts/apply_llm_flag_drift.py, which enforces
is_general_llm_access=1 ⇒ is_generative_ai=1 and keeps the last word on
that contradiction. A not_genai verdict on an llm_access=1 row is
counted under `overridden_later` so the tension is visible in the log.

Rows are keyed by (agency, use_case_name) signature — never numeric ids —
and resolved against the live DB via scripts/uc_signature.py, so this
pass survives `make fix` id rotation. Unresolved rows hard-fail above 2%.

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
PASS_DIR = ROOT / "audit" / "retag" / "genai_review_2026-07"

NON_GENAI_SOPHISTICATIONS = frozenset(
    {"classical_ml", "computer_vision", "predictive_analytics"}
)
VALID_VERDICTS = {"genai", "not_genai"}


def _verdict_rows(directory: Path) -> list[dict]:
    rows: list[dict] = []
    for f in sorted(directory.glob("verdicts_*.csv")):
        with open(f) as fh:
            rows.extend(csv.DictReader(fh))
    return rows


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


def apply_genai_review(
    conn: sqlite3.Connection, res: Resolver, apply: bool
) -> dict:
    stats = {
        "set_1": 0,
        "set_0": 0,
        "unchanged": 0,
        "soph_repaired": 0,
        "overridden_later": 0,
        "invalid": 0,
    }
    for row in _verdict_rows(PASS_DIR):
        verdict = (row.get("verdict") or "").strip().lower()
        if verdict not in VALID_VERDICTS:
            stats["invalid"] += 1
            continue
        target = 1 if verdict == "genai" else 0
        for uc_id in res.uc(None, row["agency"], row["use_case_name"]):
            cur = conn.execute(
                """SELECT COALESCE(is_generative_ai,0),
                          COALESCE(ai_sophistication,''),
                          COALESCE(is_general_llm_access,0)
                     FROM use_case_tags WHERE use_case_id = ?""",
                (uc_id,),
            ).fetchone()
            if cur is None:
                continue
            cur_genai, cur_soph, cur_llm = cur
            if target == 0 and cur_llm == 1:
                # apply_llm_flag_drift.py will re-assert genai=1 downstream.
                stats["overridden_later"] += 1
            if cur_genai == target:
                stats["unchanged"] += 1
            else:
                if apply:
                    conn.execute(
                        "UPDATE use_case_tags SET is_generative_ai = ? WHERE use_case_id = ?",
                        (target, uc_id),
                    )
                stats["set_1" if target == 1 else "set_0"] += 1
            if target == 1 and cur_soph in NON_GENAI_SOPHISTICATIONS:
                if apply:
                    conn.execute(
                        "UPDATE use_case_tags SET ai_sophistication = 'general_llm' WHERE use_case_id = ?",
                        (uc_id,),
                    )
                stats["soph_repaired"] += 1
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
            print("[genai_review] WARNING: no verdict files yet — skipped")
            return 0
        res = Resolver(conn)
        with conn:
            stats = apply_genai_review(conn, res, args.apply)
        mode = "APPLIED" if args.apply else "DRY-RUN"
        print(f"[genai_review] {mode} {stats} | {_coverage(PASS_DIR, verdicts)}")
        res.check("apply_genai_review")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
