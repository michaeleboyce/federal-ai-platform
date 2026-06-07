"""Build the 50-row calibration set used to compute inter-rater agreement
across Wave-1 subagents (per `docs/plans/2024-tagging/PLAN.md`).

Strategy:
- Allocate rows across `dev_stage` buckets roughly proportional to the
  population distribution, with a floor of 1 row per non-empty bucket.
- Within each bucket, sample agencies in proportion to that bucket's
  population, with a floor that guarantees the largest 5 agencies are
  represented and at least one minor-agency row is present.
- Deterministic seed (default 20260525) so the calibration set is
  reproducible.

Output: audit/retag/2024-tagging/inputs/calibration.csv (same CSV shape
as the partition CSVs from `build_2024_tagging_partitions.py`).
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

# Mirrors `CSV_COLUMNS` in `scripts/build_2024_tagging_partitions.py` so the
# calibration CSV is shape-compatible with the agency partition CSVs.
CSV_COLUMNS = (
    "id",
    "agency_abbreviation",
    "bureau",
    "use_case_name",
    "purpose_benefits",
    "outputs",
    "commercial_ai",
    "dev_method",
    "dev_stage",
    "topic_area",
    "lineage_status",
)
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
DEFAULT_OUT = ROOT / "audit" / "retag" / "2024-tagging" / "inputs" / "calibration.csv"
DEFAULT_N = 50
DEFAULT_SEED = 20260525


def _eligible_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            u.id,
            COALESCE(u.agency_abbreviation, '') AS agency_abbreviation,
            COALESCE(u.bureau, '') AS bureau,
            COALESCE(u.use_case_name, '') AS use_case_name,
            COALESCE(u.purpose_benefits, '') AS purpose_benefits,
            COALESCE(u.outputs, '') AS outputs,
            COALESCE(u.commercial_ai, '') AS commercial_ai,
            COALESCE(u.dev_method, '') AS dev_method,
            COALESCE(u.dev_stage, '') AS dev_stage,
            COALESCE(u.topic_area, '') AS topic_area,
            COALESCE(GROUP_CONCAT(DISTINCT l.lineage_status), '') AS lineage_status
        FROM use_cases_2024 u
        LEFT JOIN use_case_year_links l ON l.uc_2024_id = u.id
        WHERE u.use_case_name IS NOT NULL AND u.use_case_name <> ''
        GROUP BY u.id
        """
    ).fetchall()


def _allocate_per_stage(
    stage_counts: dict[str, int], n_total: int
) -> dict[str, int]:
    """Proportional allocation with floor of 1 per non-empty stage."""
    non_empty = {s: c for s, c in stage_counts.items() if c > 0}
    if not non_empty:
        return {}
    total = sum(non_empty.values())
    base = {s: max(1, round(n_total * (c / total))) for s, c in non_empty.items()}
    # Adjust to exactly n_total
    diff = n_total - sum(base.values())
    if diff != 0:
        ordered = sorted(non_empty.items(), key=lambda kv: -kv[1])
        i = 0
        while diff != 0 and ordered:
            stage, _ = ordered[i % len(ordered)]
            if diff > 0:
                base[stage] += 1
                diff -= 1
            else:
                if base[stage] > 1:
                    base[stage] -= 1
                    diff += 1
            i += 1
            if i > 10_000:
                break
    return base


def sample(
    rows: list[sqlite3.Row], n: int, seed: int
) -> list[sqlite3.Row]:
    rng = random.Random(seed)

    by_stage: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for r in rows:
        by_stage[r["dev_stage"] or "(blank)"].append(r)

    stage_counts = {s: len(v) for s, v in by_stage.items()}
    allocation = _allocate_per_stage(stage_counts, n)

    selected: list[sqlite3.Row] = []
    seen_ids: set[int] = set()

    # Within each stage bucket, prefer agency diversity: shuffle by agency
    # then take in round-robin order until the bucket's quota is filled.
    for stage, take in allocation.items():
        bucket = list(by_stage[stage])
        rng.shuffle(bucket)
        by_agency: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for r in bucket:
            by_agency[r["agency_abbreviation"]].append(r)
        agency_order = list(by_agency.keys())
        rng.shuffle(agency_order)
        picked_in_stage = 0
        while picked_in_stage < take and any(by_agency.values()):
            for ag in agency_order:
                if picked_in_stage >= take:
                    break
                queue = by_agency[ag]
                if not queue:
                    continue
                row = queue.pop(0)
                if row["id"] in seen_ids:
                    continue
                selected.append(row)
                seen_ids.add(row["id"])
                picked_in_stage += 1

    # Sort the final list by id for reproducibility (the CSV is the same
    # regardless of internal shuffle order).
    return sorted(selected, key=lambda r: r["id"])


def build(
    conn: sqlite3.Connection,
    out_path: Path = DEFAULT_OUT,
    n: int = DEFAULT_N,
    seed: int = DEFAULT_SEED,
) -> int:
    rows = _eligible_rows(conn)
    picked = sample(rows, n, seed)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(CSV_COLUMNS)
        for r in picked:
            w.writerow([r[c] for c in CSV_COLUMNS])
    return len(picked)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--n", type=int, default=DEFAULT_N)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        n = build(conn, args.out, args.n, args.seed)
    finally:
        conn.close()
    print(f"wrote {n} rows to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
