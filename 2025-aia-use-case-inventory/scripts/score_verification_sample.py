"""Score the Phase B verification agent's raw verdicts.

Reads `audit/retag/2024-tagging-verification/sample_audit_raw.csv` (produced
by the verification agent), aggregates accuracy per dimension, checks against
pass thresholds, and writes a Markdown summary to
`audit/retag/2024-tagging-verification/sample_audit.md`.

Usage:
    python3 scripts/score_verification_sample.py
    python3 scripts/score_verification_sample.py --raw path/to/raw.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAW = (
    ROOT / "audit" / "retag" / "2024-tagging-verification" / "sample_audit_raw.csv"
)
DEFAULT_OUT = (
    ROOT / "audit" / "retag" / "2024-tagging-verification" / "sample_audit.md"
)
DEFAULT_INPUT = (
    ROOT / "audit" / "retag" / "2024-tagging-verification" / "sample_input.csv"
)

# Pass thresholds (fraction of rows that must be 'correct').
# off_by_one / debatable / off_by_one_tier do NOT count as errors.
THRESHOLDS = {
    "is_generative_ai": 0.85,
    "ai_sophistication": 0.75,
    "deployment_scope": 0.75,
    "entry_type": 0.75,
}

# Verdict columns and their "partial credit" values (don't count as error).
VERDICT_COLS = {
    "verdict_is_generative_ai": set(),
    "verdict_ai_sophistication": {"off_by_one"},
    "verdict_deployment_scope": {"off_by_one_tier"},
    "verdict_entry_type": {"debatable"},
    "verdict_tool": {"na"},  # no threshold for tool
}

# Maps verdict column → friendly dimension name
DIM_NAMES = {
    "verdict_is_generative_ai": "is_generative_ai",
    "verdict_ai_sophistication": "ai_sophistication",
    "verdict_deployment_scope": "deployment_scope",
    "verdict_entry_type": "entry_type",
    "verdict_tool": "tool",
}


def _pct(n: int, d: int) -> str:
    return f"{n/d:.1%}" if d else "n/a"


def score(raw_rows: list[dict]) -> dict:
    n = len(raw_rows)
    results = {}

    for vcol, partial_values in VERDICT_COLS.items():
        dim = DIM_NAMES[vcol]
        counts: Counter = Counter()
        for r in raw_rows:
            v = (r.get(vcol) or "").strip().lower()
            counts[v] += 1

        correct = counts.get("correct", 0)
        incorrect = counts.get("incorrect", 0) + counts.get("hallucinated", 0) + counts.get("missing", 0)
        partial = sum(counts[pv] for pv in partial_values)
        na_count = counts.get("na", 0)
        evaluated = n - na_count

        # Adjusted accuracy: partial-credit rows (off_by_one, debatable) are
        # excluded from the denominator per the plan — they count neither for
        # nor against the pass rate.  Threshold is applied to adj_accuracy.
        adj_evaluated = evaluated - partial
        results[dim] = {
            "correct": correct,
            "incorrect": incorrect,
            "partial": partial,
            "na": na_count,
            "evaluated": evaluated,
            "adj_evaluated": adj_evaluated,
            "counts": dict(counts),
            "accuracy": correct / evaluated if evaluated else None,
            "adj_accuracy": correct / adj_evaluated if adj_evaluated else None,
        }

    # Per-confidence breakdown for is_generative_ai.
    by_conf: dict[str, Counter] = defaultdict(Counter)
    for r in raw_rows:
        conf = (r.get("confidence") or "").strip()
        v = (r.get("verdict_is_generative_ai") or "").strip().lower()
        by_conf[conf][v] += 1

    # Per-wave breakdown.
    by_wave: dict[str, Counter] = defaultdict(Counter)
    for r in raw_rows:
        wave = (r.get("canonical_wave") or "").strip()
        v = (r.get("verdict_is_generative_ai") or "").strip().lower()
        by_wave[wave][v] += 1

    return {
        "n": n,
        "dims": results,
        "by_conf": dict(by_conf),
        "by_wave": dict(by_wave),
    }


def _format_report(agg: dict, raw_rows: list[dict]) -> str:
    n = agg["n"]
    lines: list[str] = []

    lines += [
        "# Phase B verification — accuracy report",
        "",
        f"Sample: {n} rows from `use_case_tags_2024_canonical`.",
        "Auditor: `phase-b-auditor` (independent verification agent).",
        "",
        "## Headline accuracy",
        "",
        "| Dimension | Correct | Partial | Incorrect | Strict acc | Adj acc | Threshold | Pass? |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for vcol, partial_values in VERDICT_COLS.items():
        dim = DIM_NAMES[vcol]
        r = agg["dims"][dim]
        threshold = THRESHOLDS.get(dim)
        adj_acc = r["adj_accuracy"]
        if threshold is None:
            pass_flag = "—"
            thr_str = "—"
        else:
            pass_flag = "✅" if (adj_acc is not None and adj_acc >= threshold) else "❌"
            thr_str = f"{threshold:.0%}"
        strict_str = f"{r['accuracy']:.1%}" if r["accuracy"] is not None else "n/a"
        adj_str = f"{adj_acc:.1%}" if adj_acc is not None else "n/a"
        partial_label = "/".join(sorted(partial_values)) if partial_values else "—"
        lines.append(
            f"| `{dim}` | {r['correct']} | {r['partial']} ({partial_label}) | "
            f"{r['incorrect']} | {strict_str} | {adj_str} | {thr_str} | {pass_flag} |"
        )
    lines.append("")

    lines += [
        "## is_generative_ai by confidence tier",
        "",
        "| Confidence | Correct | Incorrect | Rows | Accuracy |",
        "|---|---|---|---|---|",
    ]
    for conf in ("high", "medium", "low"):
        c = agg["by_conf"].get(conf, Counter())
        tot = sum(c.values())
        acc = _pct(c.get("correct", 0), tot)
        lines.append(
            f"| {conf} | {c.get('correct', 0)} | {c.get('incorrect', 0)} | {tot} | {acc} |"
        )
    lines.append("")

    lines += [
        "## is_generative_ai by canonical wave",
        "",
        "| Wave | Correct | Incorrect | Rows | Accuracy |",
        "|---|---|---|---|---|",
    ]
    for wave in ("1", "3"):
        c = agg["by_wave"].get(wave, Counter())
        tot = sum(c.values())
        acc = _pct(c.get("correct", 0), tot)
        lines.append(
            f"| {wave} | {c.get('correct', 0)} | {c.get('incorrect', 0)} | {tot} | {acc} |"
        )
    lines.append("")

    # Errors — list incorrect rows
    lines += ["## Incorrect rows"]
    incorrect_rows = [
        r for r in raw_rows
        if any(
            (r.get(vc) or "").strip().lower() == "incorrect"
            for vc in VERDICT_COLS
        )
        or (r.get("verdict_tool") or "").strip().lower() == "hallucinated"
    ]
    if not incorrect_rows:
        lines += ["", "_(No incorrect verdicts.)_", ""]
    else:
        lines += [
            "",
            "| use_case_id | agency | name | genai | soph | scope | entry | tool | notes |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for r in sorted(incorrect_rows, key=lambda x: x.get("use_case_id_2024", "")):
            nm = (r.get("use_case_name") or "")[:40].replace("|", "\\|")
            notes = (r.get("notes") or "")[:60].replace("|", "\\|")
            lines.append(
                f"| {r.get('use_case_id_2024','')} | {r.get('agency_abbreviation','')} | "
                f"{nm} | {r.get('verdict_is_generative_ai','')} | "
                f"{r.get('verdict_ai_sophistication','')} | "
                f"{r.get('verdict_deployment_scope','')} | "
                f"{r.get('verdict_entry_type','')} | "
                f"{r.get('verdict_tool','')} | {notes} |"
            )
        lines.append("")

    lines += [
        "_Generated by `scripts/score_verification_sample.py`._",
    ]
    return "\n".join(lines) + "\n"


def run(raw_path: Path, out_path: Path, input_path: Path) -> dict:
    if not raw_path.exists():
        raise FileNotFoundError(f"raw verdicts file not found: {raw_path}")

    # Load sample_input.csv to join back canonical_wave and confidence.
    meta: dict[str, dict] = {}
    if input_path.exists():
        for r in csv.DictReader(input_path.open(newline="")):
            meta[r["use_case_id_2024"]] = {
                "canonical_wave": r.get("canonical_wave", ""),
                "confidence": r.get("confidence", ""),
                "agency_abbreviation": r.get("agency_abbreviation", ""),
                "use_case_name": r.get("use_case_name", ""),
            }

    raw_rows = list(csv.DictReader(raw_path.open(newline="")))
    # Enrich with sample metadata.
    for r in raw_rows:
        uid = r.get("use_case_id_2024", "")
        m = meta.get(uid, {})
        r.setdefault("canonical_wave", m.get("canonical_wave", ""))
        r.setdefault("confidence", m.get("confidence", ""))
        r.setdefault("agency_abbreviation", r.get("agency_abbreviation") or m.get("agency_abbreviation", ""))
        r.setdefault("use_case_name", r.get("use_case_name") or m.get("use_case_name", ""))

    agg = score(raw_rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_format_report(agg, raw_rows))
    return agg


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    agg = run(args.raw, args.out, args.input)
    n = agg["n"]
    print(f"scored {n} rows")
    for dim, r in agg["dims"].items():
        adj_acc = r["adj_accuracy"]
        strict_str = f"{r['accuracy']:.1%}" if r["accuracy"] is not None else "n/a"
        adj_str = f"{adj_acc:.1%}" if adj_acc is not None else "n/a"
        threshold = THRESHOLDS.get(dim)
        pass_str = ""
        if threshold is not None and adj_acc is not None:
            pass_str = " ✅" if adj_acc >= threshold else " ❌"
        print(f"  {dim}: {r['correct']}/{r['adj_evaluated']} adj-correct ({adj_str}){pass_str}  [strict: {strict_str}]")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
