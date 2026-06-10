"""Apply the 2026-06 capability review verdicts to use_case_tags.

Two review waves, both adjudicated row-by-row by per-agency micro-agents
(see the INSTRUCTIONS.md in each directory for the decision rules):

  audit/retag/general_llm_round3/verdicts_*.csv
      Final word on the 270 low-confidence `is_general_llm_access` flips
      the 2026-04 audit proposed but never applied. Sets the flag to
      `final_is_general_llm_access` per row.

  audit/retag/agentic_review/verdicts_*.csv
      Adjudication of every `ai_sophistication='agentic'` row (the keyword
      tagger over-fired on "autonomous"/"automated"). Sets
      `ai_sophistication` to `final_ai_sophistication` per row. The
      is_generative_ai flag is deliberately NOT touched here — it was not
      in scope for the agentic review.

Rows are keyed by (agency, use_case_name) signature — never numeric ids —
and resolved against the live DB via scripts/uc_signature.py, so this pass
survives `make fix` id rotation. Unresolved rows hard-fail above 2%.

Coverage: applies whatever verdict batches exist and prints input-coverage
per wave; a wave with no verdict files at all is skipped with a warning
(batches can land incrementally). Idempotent.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uc_signature import Resolver, _norm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
LLM3 = ROOT / "audit" / "retag" / "general_llm_round3"
AGENTIC = ROOT / "audit" / "retag" / "agentic_review"

SOPHISTICATION_VALUES = {
    "agentic", "general_llm", "coding_assistant", "classical_ml",
    "computer_vision", "nlp_specific", "predictive_analytics",
}


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
    return f"{len(input_keys) - missing}/{len(input_keys)} input rows covered" + (
        f" — {missing} STILL PENDING (re-run the missing review batches)" if missing else ""
    )


def apply_general_llm_round3(conn: sqlite3.Connection, res: Resolver) -> dict:
    stats = {"set_1": 0, "set_0": 0, "invalid": 0}
    for row in _verdict_rows(LLM3):
        final = (row.get("final_is_general_llm_access") or "").strip()
        if final not in {"0", "1"}:
            stats["invalid"] += 1
            continue
        for uc_id in res.uc(None, row["agency"], row["use_case_name"]):
            conn.execute(
                "UPDATE use_case_tags SET is_general_llm_access = ? WHERE use_case_id = ?",
                (int(final), uc_id),
            )
            stats["set_1" if final == "1" else "set_0"] += 1
    return stats


def apply_agentic_review(conn: sqlite3.Connection, res: Resolver) -> dict:
    stats = {"kept_agentic": 0, "reclassified": 0, "invalid": 0}
    for row in _verdict_rows(AGENTIC):
        final = (row.get("final_ai_sophistication") or "").strip()
        if final not in SOPHISTICATION_VALUES:
            stats["invalid"] += 1
            continue
        for uc_id in res.uc(None, row["agency"], row["use_case_name"]):
            conn.execute(
                "UPDATE use_case_tags SET ai_sophistication = ? WHERE use_case_id = ?",
                (final, uc_id),
            )
            stats["kept_agentic" if final == "agentic" else "reclassified"] += 1
    return stats


def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        res = Resolver(conn)
        with conn:
            for label, directory, fn in (
                ("general_llm_round3", LLM3, apply_general_llm_round3),
                ("agentic_review", AGENTIC, apply_agentic_review),
            ):
                verdicts = _verdict_rows(directory)
                if not verdicts:
                    print(f"[{label}] WARNING: no verdict files yet — skipped")
                    continue
                stats = fn(conn, res)
                print(f"[{label}] {stats} | {_coverage(directory, verdicts)}")
        res.check("apply_capability_reviews")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
