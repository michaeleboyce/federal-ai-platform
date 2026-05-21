"""Compute field-level drift for the 2024↔2025 use-case lineage.

Phase 4 (Stage 3, step 3) of the 2024 ↔ 2025 AI use case inventory
comparison project (see `docs/plans/2024-vs-2025-comparison/PLAN.md`).

Deterministic — no agents. For every **1:1 `continued` / `renamed`** link
in `use_case_year_links`, build two aligned dicts from the 21
`directly_comparable` field pairs in `column_maps_2024.COLUMN_CROSSWALK_2024`
(each entry's `field` is a 2024 column, `target_2025` a 2025 column), pass
them to `omb_consolidated_match.detect_drift`, and write the result to
`use_case_year_links.drift_fields_json`.

The two `recoded` columns are ALSO compared, after recoding the 2024 value:
  - `dev_stage` → `stage_of_development` via `DEV_STAGE_RECODE_2024`
  - `impact_type` → `is_high_impact` via `IMPACT_TYPE_RECODE_2024`
Any drift entry produced from a recoded column is flagged `lossy: true` —
the recode is lossy, so a "drift" there may be an artifact of the recode.

Drift is skipped for `split` / `merged` links (N:M — field drift is
ill-defined) and for `retired_2024` / `new_2025` (no counterpart row).

Idempotent: every eligible link's `drift_fields_json` is recomputed; links
that are not 1:1 continued/renamed have it cleared to NULL. Runs in
`make fix` after `apply_year_match_review.py`.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from column_maps_2024 import (
    COLUMN_CROSSWALK_2024,
    DEV_STAGE_RECODE_2024,
    DIRECTLY_COMPARABLE,
    IMPACT_TYPE_RECODE_2024,
)
from omb_consolidated_match import detect_drift

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"

# The 21 directly-comparable (2024 field, 2025 target) pairs.
DIRECT_PAIRS: list[tuple[str, str]] = [
    (e["field"], e["target_2025"])
    for e in COLUMN_CROSSWALK_2024
    if e["comparability"] == DIRECTLY_COMPARABLE and e["target_2025"]
]

# The recoded pairs, each with its recode map. The 2024 value is recoded
# to the 2025 vocabulary before comparison; any resulting drift is `lossy`.
RECODED_PAIRS: list[tuple[str, str, dict]] = [
    ("dev_stage", "stage_of_development", DEV_STAGE_RECODE_2024),
    ("impact_type", "is_high_impact", IMPACT_TYPE_RECODE_2024),
]

# 2024 columns to SELECT from use_cases_2024.
_FIELDS_2024 = sorted(
    {f for f, _ in DIRECT_PAIRS} | {f for f, _, _ in RECODED_PAIRS}
)
# 2025 targets to SELECT from use_cases (joined with agencies for the two
# agency-* targets which live on the agencies table, not use_cases).
_AGENCY_TARGETS = {"agency_name", "agency_abbreviation"}
_TARGETS_2025 = sorted(
    {t for _, t in DIRECT_PAIRS} | {t for _, t, _ in RECODED_PAIRS}
)


# SELECT-alias prefixes — several columns (`system_name`, `topic_area`,
# `has_ato`, `agency_abbreviation`) exist in BOTH use_cases_2024 and
# use_cases, so the SELECT must alias them distinctly or the row dict
# collides (one side silently overwrites the other).
_P2024 = "c2024_"
_P2025 = "c2025_"


def _select_2024_expr(alias: str) -> str:
    return ", ".join(f"{alias}.{f} AS {_P2024}{f}" for f in _FIELDS_2024)


def _select_2025_expr(uc_alias: str, agency_alias: str) -> str:
    """SELECT list for the 2025 row. `agency_name` / `agency_abbreviation`
    come from the joined `agencies` table; everything else from use_cases."""
    parts: list[str] = []
    for t in _TARGETS_2025:
        if t == "agency_name":
            parts.append(f"{agency_alias}.name AS {_P2025}agency_name")
        elif t == "agency_abbreviation":
            parts.append(f"{agency_alias}.abbreviation AS {_P2025}agency_abbreviation")
        else:
            parts.append(f"{uc_alias}.{t} AS {_P2025}{t}")
    return ", ".join(parts)


def _recode_2024(value: str | None, recode_map: dict) -> str | None:
    """Recode a raw 2024 value to its 2025-vocabulary target, or None."""
    if value is None:
        return None
    entry = recode_map.get(" ".join(value.split()))
    return entry["target"] if entry else None


def _drift_for_link(row_2024: dict, row_2025: dict) -> dict:
    """Build the drift dict for one 1:1 link.

    Directly-comparable pairs go through `detect_drift` as-is. Recoded
    pairs are compared after recoding the 2024 value; any recoded-pair
    drift entry carries `lossy: true`.
    """
    # Directly-comparable: align the two dicts on a shared key per pair.
    db_aligned: dict[str, str | None] = {}
    omb_aligned: dict[str, str | None] = {}
    for f24, t25 in DIRECT_PAIRS:
        db_aligned[f24] = row_2024.get(f24)
        omb_aligned[f24] = row_2025.get(t25)
    direct = detect_drift(db_aligned, omb_aligned, fields=[f for f, _ in DIRECT_PAIRS])

    out: dict[str, dict] = {}
    for f24, change in direct.items():
        out[f24] = {
            "v2024": change["db"],
            "v2025": change["omb"],
            "lossy": False,
        }

    # Recoded pairs: recode the 2024 value, then compare.
    for f24, t25, recode_map in RECODED_PAIRS:
        raw_2024 = row_2024.get(f24)
        recoded_2024 = _recode_2024(raw_2024, recode_map)
        v2025 = row_2025.get(t25)
        rd = detect_drift(
            {f24: recoded_2024}, {f24: v2025}, fields=[f24]
        )
        if rd:
            out[f24] = {
                "v2024": raw_2024,
                "v2024_recoded": recoded_2024,
                "v2025": v2025,
                "lossy": True,
            }
    return out


def compute(conn: sqlite3.Connection) -> dict[str, int]:
    """Recompute `drift_fields_json` for every link. Returns a small stat
    dict: {eligible, with_drift, cleared}."""
    cur = conn.cursor()
    # Clear drift for every non-eligible link (idempotent reset).
    cur.execute(
        "UPDATE use_case_year_links SET drift_fields_json = NULL "
        "WHERE lineage_status NOT IN ('continued', 'renamed') "
        "   OR uc_2024_id IS NULL OR uc_2025_id IS NULL"
    )
    cleared = cur.rowcount

    # The 2024 SELECT list aliases columns off `u` (use_cases_2024); the
    # 2025 list off `u25` (use_cases) and `a` (agencies).
    sel_2024 = _select_2024_expr("u")
    sel_2025 = _select_2025_expr("u25", "a")
    rows = list(conn.execute(
        f"""
        SELECT l.id AS link_id, {sel_2024}, {sel_2025}
        FROM use_case_year_links l
        JOIN use_cases_2024 u ON u.id = l.uc_2024_id
        JOIN use_cases u25 ON u25.id = l.uc_2025_id
        LEFT JOIN agencies a ON a.id = u25.agency_id
        WHERE l.lineage_status IN ('continued', 'renamed')
          AND l.uc_2024_id IS NOT NULL AND l.uc_2025_id IS NOT NULL
        """
    ))

    eligible = 0
    with_drift = 0
    for r in rows:
        d = dict(r)
        link_id = d["link_id"]
        row_2024 = {f: d.get(f"{_P2024}{f}") for f in _FIELDS_2024}
        row_2025 = {t: d.get(f"{_P2025}{t}") for t in _TARGETS_2025}
        drift = _drift_for_link(row_2024, row_2025)
        eligible += 1
        payload = json.dumps(drift, ensure_ascii=False) if drift else json.dumps({})
        if drift:
            with_drift += 1
        cur.execute(
            "UPDATE use_case_year_links SET drift_fields_json=? WHERE id=?",
            (payload, link_id),
        )
    conn.commit()
    return {"eligible": eligible, "with_drift": with_drift, "cleared": cleared}


def _print_summary(stats: dict[str, int]) -> None:
    print("Year-lineage drift summary:")
    print(f"  eligible 1:1 continued/renamed links : {stats['eligible']}")
    print(f"  links with ≥1 drifted field          : {stats['with_drift']}")
    print(f"  non-eligible links cleared to NULL   : {stats['cleared']}")
    if stats["eligible"]:
        pct = stats["with_drift"] / stats["eligible"]
        print(f"  drift coverage                       : {pct:.1%} of eligible")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH, help="SQLite DB path.")
    args = parser.parse_args(argv)
    if not args.db.exists():
        raise FileNotFoundError(args.db)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        stats = compute(conn)
    finally:
        conn.close()
    _print_summary(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
