"""Classify every continued/renamed/split 2024-2025 pair by post-Wave-3 alignment.

For each pair in use_case_year_links with lineage_status IN
('continued','renamed','split'), compares the canonical 2024 tag
(use_case_tags_2024_canonical) with the 2025 tag (use_case_tags) on four
key fields: is_generative_ai, ai_sophistication, deployment_scope,
entry_type.

Classification:
  aligned             — canonical 2024 ≈ 2025 on all four fields
  expected_drift      — canonical 2024 tag came from wave=3 (Wave 3 explicitly
                        chose the 2024 reality, so divergence is intentional)
  persistent_disagreement
                      — wave=1 canonical row (Wave 2 didn't flag this pair),
                        but the tags still differ on ≥1 key field
  error_2025_queue    — in audit/retag/2024-vs-2025-divergence/queue.csv
                        (Wave 2 flagged this as a possible 2025 tagging error)
  tags_2025_missing   — 2025 row exists but has no use_case_tags row

Output: audit/retag/2024-tagging-verification/cross_year_residuals.csv

Usage:
    python3 scripts/cross_year_residual_audit.py
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
DEFAULT_OUT = (
    ROOT / "audit" / "retag" / "2024-tagging-verification" / "cross_year_residuals.csv"
)
ERROR_2025_QUEUE = ROOT / "audit" / "retag" / "2024-vs-2025-divergence" / "queue.csv"

KEY_FIELDS = ("is_generative_ai", "ai_sophistication", "deployment_scope", "entry_type")

OUTPUT_COLS = (
    "uc_2024_id",
    "uc_2025_id",
    "lineage_status",
    "agency_abbreviation",
    "name_2024",
    "name_2025",
    "canonical_wave",
    "category",
    "diverged_fields",
    *[f"tag2024_{f}" for f in KEY_FIELDS],
    *[f"tag2025_{f}" for f in KEY_FIELDS],
)


def _load_error_2025_ids() -> set[int]:
    if not ERROR_2025_QUEUE.exists():
        return set()
    ids: set[int] = set()
    for r in csv.DictReader(ERROR_2025_QUEUE.open(newline="")):
        try:
            ids.add(int(r["use_case_id_2024"]))
        except (KeyError, ValueError):
            pass
    return ids


def _fields_diverge(tag24: dict, tag25: dict) -> list[str]:
    diverged = []
    for f in KEY_FIELDS:
        v24 = str(tag24.get(f) or "").strip()
        v25 = str(tag25.get(f) or "").strip()
        if v24 != v25:
            diverged.append(f)
    return diverged


def run(conn: sqlite3.Connection, out_path: Path = DEFAULT_OUT) -> dict[str, int]:
    error_2025_ids = _load_error_2025_ids()

    # Fetch all continued/renamed/split pairs with 2024 + 2025 tags.
    rows = conn.execute(
        f"""
        SELECT
            l.uc_2024_id,
            l.uc_2025_id,
            l.lineage_status,
            u24.agency_abbreviation,
            u24.use_case_name AS name_2024,
            u25.use_case_name AS name_2025,
            c.wave AS canonical_wave,
            { ", ".join(f"c.{f} AS tag2024_{f}" for f in KEY_FIELDS) },
            { ", ".join(f"t25.{f} AS tag2025_{f}" for f in KEY_FIELDS) },
            t25.id IS NOT NULL AS has_2025_tag
        FROM use_case_year_links l
        JOIN use_cases_2024 u24 ON u24.id = l.uc_2024_id
        JOIN use_cases u25 ON u25.id = l.uc_2025_id
        JOIN use_case_tags_2024_canonical c ON c.use_case_id_2024 = l.uc_2024_id
        LEFT JOIN use_case_tags t25 ON t25.use_case_id = l.uc_2025_id
        WHERE l.lineage_status IN ('continued','renamed','split')
        ORDER BY l.uc_2024_id, l.uc_2025_id
        """
    ).fetchall()

    out_rows: list[dict] = []
    counts: dict[str, int] = {
        "aligned": 0,
        "expected_drift": 0,
        "persistent_disagreement": 0,
        "error_2025_queue": 0,
        "tags_2025_missing": 0,
    }

    for r in rows:
        d = dict(r)
        uc24 = d["uc_2024_id"]

        tag24 = {f: d[f"tag2024_{f}"] for f in KEY_FIELDS}
        tag25 = {f: d[f"tag2025_{f}"] for f in KEY_FIELDS}

        if not d["has_2025_tag"]:
            category = "tags_2025_missing"
            diverged = []
        elif uc24 in error_2025_ids:
            category = "error_2025_queue"
            diverged = _fields_diverge(tag24, tag25)
        else:
            diverged = _fields_diverge(tag24, tag25)
            if not diverged:
                category = "aligned"
            elif d["canonical_wave"] == "3":
                # Wave 3 explicitly chose the 2024 reality — divergence is intentional.
                category = "expected_drift"
            else:
                # wave=1 canonical + still diverges from 2025 = Wave 2 may have missed it.
                category = "persistent_disagreement"

        counts[category] += 1
        out_rows.append({
            "uc_2024_id": uc24,
            "uc_2025_id": d["uc_2025_id"],
            "lineage_status": d["lineage_status"],
            "agency_abbreviation": d["agency_abbreviation"],
            "name_2024": d["name_2024"],
            "name_2025": d["name_2025"],
            "canonical_wave": d["canonical_wave"],
            "category": category,
            "diverged_fields": "|".join(diverged),
            **{f"tag2024_{f}": d[f"tag2024_{f}"] for f in KEY_FIELDS},
            **{f"tag2025_{f}": d[f"tag2025_{f}"] for f in KEY_FIELDS},
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLS)
        writer.writeheader()
        for row in out_rows:
            writer.writerow({k: row.get(k, "") for k in OUTPUT_COLS})

    counts["total"] = len(out_rows)
    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        counts = run(conn, args.out)
    finally:
        conn.close()

    total = counts.pop("total", sum(counts.values()))
    print(f"total pairs: {total}")
    for cat, n in sorted(counts.items()):
        print(f"  {cat}: {n}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
