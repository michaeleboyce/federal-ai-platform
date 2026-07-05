"""Build input slices for the genai_review_2026-07 adjudication pass.

Targets every 2025 `use_case_tags` row where the IFP `is_generative_ai`
flag DISAGREES with the agency's own filed classification
(`use_cases.ai_classification_normalized`), in three cohorts:

  over_contradict   is_generative_ai=1, agency declared Classical/
                    Predictive ML, Computer Vision, NLP, Other, or RL.
  over_unspecified  is_generative_ai=1, agency declared nothing
                    (normalized 'Unspecified').
  under_declared    is_generative_ai=0, agency declared Generative AI
                    or Agentic AI.

Why: the 2025 flag is keyword-derived (`auto_tag.py` — LLM_KEYWORDS +
AGENTIC_KEYWORDS, where bare "autonomous"/"agent"/"workflow"/"chatbot"
over-fire), while the 2024 tags were LLM-judged per row. This pass brings
the 2025 side to the same standard. See INSTRUCTIONS.md in the output
directory for the decision rule.

Signature-keyed by (agency, use_case_name) — never numeric ids — with the
same narrative columns as audit/retag/llm_flag_drift_2026-07/input.csv,
plus `fired_keywords`: which tagger keyword(s) actually matched the row's
search text, so reviewers can see *why* the heuristic fired.

Writes `audit/retag/genai_review_2026-07/input_batch{1..N}.csv` plus a
combined `input.csv`.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from auto_tag import AGENTIC_KEYWORDS, LLM_KEYWORDS  # noqa: E402
from product_resolution import use_case_search_text  # noqa: E402

DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT_DIR = ROOT / "audit" / "retag" / "genai_review_2026-07"

OVER_CONTRADICT_CLASSES = (
    "Classical/Predictive Machine Learning",
    "Computer Vision",
    "Natural Language Processing",
    "Other",
    "Reinforcement Learning",
)
UNDER_DECLARED_CLASSES = ("Generative AI", "Agentic AI")

COLUMNS = [
    "agency",
    "use_case_name",
    "cohort",
    "bureau_component",
    "current_is_generative_ai",
    "is_general_llm_access",
    "ai_sophistication",
    "ai_classification",
    "ai_classification_normalized",
    "stage_normalized",
    "operational_date",
    "tool_product_name",
    "system_name",
    "vendor_name",
    "problem_statement",
    "expected_benefits",
    "system_outputs",
    "fired_keywords",
]

# Raw-row keys use_case_search_text() reads, fetched alongside the output
# columns so fired_keywords reflects the tagger's actual haystack.
SEARCH_TEXT_KEYS = (
    "vendor_name",
    "system_name",
    "use_case_name",
    "problem_statement",
    "expected_benefits",
    "system_outputs",
)


def fired_keywords(row: dict) -> str:
    text = use_case_search_text({k: row.get(k) for k in SEARCH_TEXT_KEYS}).lower()
    hits = [kw for kw in LLM_KEYWORDS + AGENTIC_KEYWORDS if kw in text]
    return "; ".join(dict.fromkeys(hits))


def fetch_rows(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    placeholders_over = ",".join("?" for _ in OVER_CONTRADICT_CLASSES)
    placeholders_under = ",".join("?" for _ in UNDER_DECLARED_CLASSES)
    raw = conn.execute(
        f"""
        SELECT a.abbreviation                          AS agency,
               uc.use_case_name,
               CASE
                 WHEN COALESCE(t.is_generative_ai,0)=1
                  AND uc.ai_classification_normalized IN ({placeholders_over})
                   THEN 'over_contradict'
                 WHEN COALESCE(t.is_generative_ai,0)=1
                  AND uc.ai_classification_normalized = 'Unspecified'
                   THEN 'over_unspecified'
                 ELSE 'under_declared'
               END                                     AS cohort,
               COALESCE(uc.bureau_component, '')       AS bureau_component,
               COALESCE(t.is_generative_ai, 0)         AS current_is_generative_ai,
               COALESCE(t.is_general_llm_access, 0)    AS is_general_llm_access,
               COALESCE(t.ai_sophistication, '')       AS ai_sophistication,
               COALESCE(uc.ai_classification, '')      AS ai_classification,
               COALESCE(uc.ai_classification_normalized, '') AS ai_classification_normalized,
               COALESCE(uc.stage_normalized, '')       AS stage_normalized,
               COALESCE(uc.operational_date, '')       AS operational_date,
               COALESCE(t.tool_product_name, '')       AS tool_product_name,
               COALESCE(uc.system_name, '')            AS system_name,
               COALESCE(uc.vendor_name, '')            AS vendor_name,
               COALESCE(uc.problem_statement, '')      AS problem_statement,
               COALESCE(uc.expected_benefits, '')      AS expected_benefits,
               COALESCE(uc.system_outputs, '')         AS system_outputs
          FROM use_cases uc
          JOIN use_case_tags t ON t.use_case_id = uc.id
          JOIN agencies a ON a.id = uc.agency_id
         WHERE (COALESCE(t.is_generative_ai,0)=1
                AND uc.ai_classification_normalized IN ({placeholders_over}, 'Unspecified'))
            OR (COALESCE(t.is_generative_ai,0)=0
                AND uc.ai_classification_normalized IN ({placeholders_under}))
         ORDER BY a.abbreviation, uc.use_case_name
        """,
        (*OVER_CONTRADICT_CLASSES, *OVER_CONTRADICT_CLASSES, *UNDER_DECLARED_CLASSES),
    ).fetchall()
    if not raw:
        raise SystemExit("No disagreement rows found — already adjudicated?")
    rows = []
    for r in raw:
        d = dict(r)
        d["fired_keywords"] = fired_keywords(d)
        rows.append({k: d[k] for k in COLUMNS})
    return rows


def pack_batches(rows: list[dict], n_batches: int) -> list[list[dict]]:
    by_agency: dict[str, list[dict]] = {}
    for r in rows:
        by_agency.setdefault(r["agency"], []).append(r)
    batches: list[list[dict]] = [[] for _ in range(n_batches)]
    for _, agency_rows in sorted(by_agency.items(), key=lambda kv: -len(kv[1])):
        smallest = min(batches, key=len)
        smallest.extend(agency_rows)
    return [b for b in batches if b]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--batches", type=int, default=14)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        rows = fetch_rows(conn)
    finally:
        conn.close()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def write(path: Path, rs: list[dict]) -> None:
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(rs)

    write(OUT_DIR / "input.csv", rows)
    for i, batch in enumerate(pack_batches(rows, args.batches), start=1):
        write(OUT_DIR / f"input_batch{i}.csv", batch)
        agencies = sorted({r["agency"] for r in batch})
        print(f"batch{i}: {len(batch)} rows — {', '.join(agencies)}")
    cohorts: dict[str, int] = {}
    for r in rows:
        cohorts[r["cohort"]] = cohorts.get(r["cohort"], 0) + 1
    print(f"total: {len(rows)} rows — {cohorts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
