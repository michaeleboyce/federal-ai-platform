"""Build an 80-row stratified sample for the Phase B accuracy verification.

Samples from `use_case_tags_2024_canonical` with stratification targets:
  - confidence:      ~27 high, ~27 medium, ~26 low (oversamples low to catch errors)
  - wave:            proportional (wave=3 rows get slight preference within buckets)
  - lineage_status:  ~30 continued, ~15 renamed/split, ~35 retired_2024
  - agency:          at least 1 row from every top-15 agency

Each output row includes: 2024 narrative, canonical IFP tag, wave-1 reasoning
(for comparison), and wave-3 reasoning if the canonical tag came from wave 3.

Output: audit/retag/2024-tagging-verification/sample_input.csv

Usage:
    python3 scripts/build_verification_sample.py
    python3 scripts/build_verification_sample.py --n 80 --seed 20260528
"""
from __future__ import annotations

import argparse
import csv
import random
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
DEFAULT_OUT = (
    ROOT / "audit" / "retag" / "2024-tagging-verification" / "sample_input.csv"
)
DEFAULT_N = 80
DEFAULT_SEED = 20260528

# Top agencies by 2024 row count (DOD has 0 rows in use_cases_2024).
TOP_AGENCIES = {
    "HHS", "DOJ", "VA", "DHS", "DOI", "USAID", "USDA",
    "DOE", "DOL", "DOT", "DOC", "STATE", "EPA", "GSA",
}

# 2D cell targets: (confidence, lineage_category) → desired count.
# confidence totals: high=27, medium=27, low=26
# lineage totals:    continued=30, retired=35, renamed_split=15 (oversample retired)
CELL_TARGETS: dict[tuple[str, str], int] = {
    ("high",   "continued"):     10,
    ("high",   "retired"):       12,
    ("high",   "renamed_split"): 5,
    ("medium", "continued"):     10,
    ("medium", "retired"):       12,
    ("medium", "renamed_split"): 5,
    ("low",    "continued"):     10,
    ("low",    "retired"):       11,
    ("low",    "renamed_split"): 5,
}

TAG_FIELDS: tuple[str, ...] = (
    "entry_type",
    "is_generative_ai",
    "ai_sophistication",
    "deployment_scope",
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

OUTPUT_COLS = (
    "use_case_id_2024",
    "agency_abbreviation",
    "bureau",
    "use_case_name",
    "purpose_benefits",
    "outputs",
    "commercial_ai",
    "dev_method",
    "dev_stage",
    "lineage_status",
    "canonical_wave",
    *TAG_FIELDS,
    "confidence",
    "canonical_reasoning",
    "wave1_is_generative_ai",
    "wave1_ai_sophistication",
    "wave1_deployment_scope",
    "wave1_entry_type",
    "wave1_reasoning",
    "wave3_reasoning",
)


def _fetch_candidates(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        f"""
        SELECT
            c.use_case_id_2024,
            c.wave         AS canonical_wave,
            c.confidence,
            c.reasoning    AS canonical_reasoning,
            { ", ".join(f"c.{f}" for f in TAG_FIELDS) },
            u.agency_abbreviation,
            u.bureau,
            u.use_case_name,
            u.purpose_benefits,
            u.outputs,
            u.commercial_ai,
            u.dev_method,
            u.dev_stage,
            COALESCE(GROUP_CONCAT(DISTINCT l.lineage_status), '') AS lineage_status
        FROM use_case_tags_2024_canonical c
        JOIN use_cases_2024 u ON u.id = c.use_case_id_2024
        LEFT JOIN use_case_year_links l ON l.uc_2024_id = c.use_case_id_2024
        GROUP BY c.use_case_id_2024
        ORDER BY c.use_case_id_2024
        """
    ).fetchall()
    return [dict(r) for r in rows]


def _fetch_wave1_tags(conn: sqlite3.Connection, ids: set[int]) -> dict[int, dict]:
    if not ids:
        return {}
    ph = ",".join(["?"] * len(ids))
    rows = conn.execute(
        f"SELECT use_case_id_2024, is_generative_ai, ai_sophistication, "
        f"deployment_scope, entry_type, reasoning "
        f"FROM use_case_tags_2024 WHERE wave='1' AND use_case_id_2024 IN ({ph})",
        list(ids),
    ).fetchall()
    return {r["use_case_id_2024"]: dict(r) for r in rows}


def _fetch_wave3_reasonings(conn: sqlite3.Connection, ids: set[int]) -> dict[int, str]:
    if not ids:
        return {}
    ph = ",".join(["?"] * len(ids))
    rows = conn.execute(
        f"SELECT use_case_id_2024, reasoning "
        f"FROM use_case_tags_2024 WHERE wave='3' AND use_case_id_2024 IN ({ph})",
        list(ids),
    ).fetchall()
    return {r["use_case_id_2024"]: r["reasoning"] or "" for r in rows}


def _lineage_pref(status: str) -> int:
    for i, s in enumerate(LINEAGE_PREF_ORDER):
        if s in status:
            return i
    return len(LINEAGE_PREF_ORDER)


def _norm_lineage(status: str) -> str:
    s = status.lower()
    if "retired" in s:
        return "retired"
    if "renamed" in s or "split" in s:
        return "renamed_split"
    if "continued" in s:
        return "continued"
    return "continued"  # default: treat blank as continued


def sample(candidates: list[dict], n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)

    # Group into 2D cells (confidence × lineage_category).
    cells: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in candidates:
        conf = (r.get("confidence") or "").strip() or "medium"
        lineage = _norm_lineage(r.get("lineage_status") or "")
        cells[(conf, lineage)].append(r)

    selected: list[dict] = []
    seen_ids: set[int] = set()
    agency_seen: set[str] = set()

    for (conf, lineage), target in CELL_TARGETS.items():
        bucket = list(cells.get((conf, lineage), []))
        rng.shuffle(bucket)
        # Within the shuffled bucket, prefer top-agency rows first.
        bucket.sort(key=lambda r: (
            0 if r.get("agency_abbreviation") in TOP_AGENCIES else 1,
        ))
        taken = 0
        for r in bucket:
            if taken >= target:
                break
            if r["use_case_id_2024"] in seen_ids:
                continue
            selected.append(r)
            seen_ids.add(r["use_case_id_2024"])
            agency_seen.add(r.get("agency_abbreviation") or "")
            taken += 1

    # Ensure every top agency has ≥1 row — fill gaps from any remaining rows.
    missing_agencies = TOP_AGENCIES - agency_seen
    if missing_agencies:
        remaining = [r for r in candidates if r["use_case_id_2024"] not in seen_ids]
        rng.shuffle(remaining)
        for r in remaining:
            ag = r.get("agency_abbreviation") or ""
            if ag in missing_agencies:
                selected.append(r)
                seen_ids.add(r["use_case_id_2024"])
                missing_agencies.discard(ag)
            if not missing_agencies:
                break

    return sorted(selected, key=lambda r: r["use_case_id_2024"])


def build(
    conn: sqlite3.Connection,
    out_path: Path = DEFAULT_OUT,
    n: int = DEFAULT_N,
    seed: int = DEFAULT_SEED,
) -> int:
    candidates = _fetch_candidates(conn)
    picked = sample(candidates, n, seed)

    ids = {r["use_case_id_2024"] for r in picked}
    w1 = _fetch_wave1_tags(conn, ids)
    w3_reasonings = _fetch_wave3_reasonings(conn, ids)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLS)
        writer.writeheader()
        for r in picked:
            uid = r["use_case_id_2024"]
            w1r = w1.get(uid, {})
            row = {k: r.get(k, "") for k in OUTPUT_COLS}
            row["wave1_is_generative_ai"] = w1r.get("is_generative_ai", "")
            row["wave1_ai_sophistication"] = w1r.get("ai_sophistication", "")
            row["wave1_deployment_scope"] = w1r.get("deployment_scope", "")
            row["wave1_entry_type"] = w1r.get("entry_type", "")
            row["wave1_reasoning"] = w1r.get("reasoning", "")
            row["wave3_reasoning"] = w3_reasonings.get(uid, "")
            writer.writerow(row)

    return len(picked)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--n", type=int, default=DEFAULT_N)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        n = build(conn, args.out, args.n, args.seed)
    finally:
        conn.close()
    print(f"wrote {n} rows to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
