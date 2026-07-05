"""Apply the llm_flag_drift_2026-07 verdicts to use_case_tags.

Adjudication of every row that carried the contradiction
`is_general_llm_access = 1 AND is_generative_ai = 0` (a general-purpose
chat LLM is by definition generative AI). Verdicts live at
audit/retag/llm_flag_drift_2026-07/verdicts_*.csv with an optional
`audit_overrides.csv` layer (the Fable audit — overrides win). Sets BOTH
final flags per row.

Rows are keyed by (agency, use_case_name) signature — never numeric ids —
and resolved against the live DB via scripts/uc_signature.py::Resolver,
so this pass survives `make fix` id rotation. Unresolved rows hard-fail
above 2%. Idempotent; wired into `make fix` after
apply_capability_reviews.py (which re-broadens the same flags upstream).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uc_signature import Resolver, _norm  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from db import get_connection  # noqa: E402

PASS_DIR = _ROOT / "audit" / "retag" / "llm_flag_drift_2026-07"
VALID_VERDICTS = {"set_genai", "clear_llm_access", "keep_current"}


def load_verdicts() -> tuple[dict[tuple[str, str], dict], list[str]]:
    """Verdicts by normalized signature, audit overrides applied."""
    errors: list[str] = []
    verdicts: dict[tuple[str, str], dict] = {}
    files = sorted(PASS_DIR.glob("verdicts_*.csv"))
    if not files:
        return {}, [f"no verdicts_*.csv under {PASS_DIR}"]

    def ingest(row: dict, src: str, is_override: bool) -> None:
        sig = (_norm(row.get("agency")), _norm(row.get("use_case_name")))
        if not sig[0] or not sig[1]:
            errors.append(f"{src}: row missing agency/use_case_name")
            return
        if row.get("verdict") not in VALID_VERDICTS:
            errors.append(
                f"{src}: {row.get('use_case_name')!r} bad verdict "
                f"{row.get('verdict')!r}"
            )
            return
        for field in ("final_is_general_llm_access", "final_is_generative_ai"):
            if (row.get(field) or "").strip() not in {"0", "1"}:
                errors.append(
                    f"{src}: {row.get('use_case_name')!r} bad {field}"
                    f"={row.get(field)!r}"
                )
                return
        if not is_override and sig in verdicts:
            errors.append(f"{src}: duplicate signature {sig}")
            return
        verdicts[sig] = row

    for path in files:
        with path.open() as f:
            for row in csv.DictReader(f):
                ingest(row, path.name, is_override=False)
    overrides = PASS_DIR / "audit_overrides.csv"
    if overrides.exists():
        with overrides.open() as f:
            for row in csv.DictReader(f):
                if (row.get("audit_verdict") or "override") == "agree":
                    continue
                ingest(row, "audit_overrides.csv", is_override=True)
    return verdicts, errors


def main() -> int:
    if not sorted(PASS_DIR.glob("verdicts_*.csv")):
        print(
            f"WARNING: no verdicts_*.csv under {PASS_DIR} yet — skipping "
            f"(batches land incrementally)."
        )
        return 0
    verdicts, errors = load_verdicts()
    if errors:
        print("VALIDATION ERRORS — nothing written:")
        for e in errors:
            print(f"  - {e}")
        return 1

    # Coverage vs the frozen input.
    with (PASS_DIR / "input.csv").open() as f:
        input_sigs = {
            (_norm(r["agency"]), _norm(r["use_case_name"]))
            for r in csv.DictReader(f)
        }
    missing = input_sigs - set(verdicts)
    print(
        f"{len(input_sigs) - len(missing)}/{len(input_sigs)} input rows "
        f"covered"
        + (f" — {len(missing)} STILL PENDING" if missing else "")
    )

    conn = get_connection()
    try:
        res = Resolver(conn)
        stats = {"set_genai": 0, "clear_llm_access": 0, "keep_current": 0,
                 "rows_updated": 0}
        with conn:
            for (agency, name), row in verdicts.items():
                uc_ids = res.uc(None, row["agency"], row["use_case_name"])
                for uc_id in uc_ids:
                    conn.execute(
                        """
                        UPDATE use_case_tags
                           SET is_general_llm_access = ?,
                               is_generative_ai      = ?
                         WHERE use_case_id = ?
                        """,
                        (
                            int(row["final_is_general_llm_access"]),
                            int(row["final_is_generative_ai"]),
                            uc_id,
                        ),
                    )
                    stats["rows_updated"] += 1
                if uc_ids:
                    stats[row["verdict"]] += 1
        res.check("llm_flag_drift_2026-07")
        print(
            f"Applied: {stats['set_genai']} set_genai, "
            f"{stats['clear_llm_access']} clear_llm_access, "
            f"{stats['keep_current']} keep_current "
            f"({stats['rows_updated']} tag rows updated)."
        )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
