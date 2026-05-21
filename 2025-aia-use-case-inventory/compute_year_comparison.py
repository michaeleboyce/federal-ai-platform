"""Populate `year_comparison` — the 2024↔2025 YoY aggregate rollup.

Phase 2 ("Option A" milestone) of the 2024 ↔ 2025 AI use case inventory
comparison project (see `docs/plans/2024-vs-2025-comparison/PLAN.md`).

This compute script is the sibling of `compute_maturity.py`: it opens the DB
via `get_connection()`, wipes `year_comparison` (idempotent reload), recomputes
every dimension row, INSERTs, commits, and prints a summary.

Dimensions produced (one row per dimension×bucket cell — a tidy/long table):
  - `total`      — 1 row, `comparability='clean'`.
  - `agency`     — ~41 rows, `clean`; full-outer joined on `agency_id`.
  - `stage`      — ~5 rows, `lossy`; 2024 SDLC enum recoded, 2025 posture
                   enum bucketed with the same logic `compute_maturity.py`
                   uses for `pct_deployed`.
  - `dev_method` — ~4 rows, `lossy`; both years are sparse.

`impact` / `ai_classification` are excluded by design — the taxonomies are not
1:1 (see the Phase 0 COMPARABILITY-MATRIX).
"""
from __future__ import annotations

import re

from column_maps_2024 import DEV_STAGE_RECODE_2024
from db import get_connection
from omb_consolidated_match import _canonicalize_field

# --- Canonical bucket vocabularies -----------------------------------------

# 2025 M-25-21 posture stages (the 4 canonical buckets) plus `unknown`.
STAGE_PRE = "a) Pre-deployment"
STAGE_PILOT = "b) Pilot"
STAGE_DEPLOYED = "c) Deployed"
STAGE_RETIRED = "d) Retired"
STAGE_UNKNOWN = "unknown"

# dev_method buckets.
METHOD_IN_HOUSE = "in_house"
METHOD_CONTRACTED = "contracted"
METHOD_BOTH = "both"
METHOD_UNKNOWN = "unknown"

_WS_RE = re.compile(r"\s+")


def _collapse_ws(s: str | None) -> str:
    """Collapse runs of whitespace — the 2024 CSV has e.g. a double space in
    `Research or  Administrative Action Complete`."""
    if s is None:
        return ""
    return _WS_RE.sub(" ", s).strip()


# --- Stage bucketing -------------------------------------------------------

def bucket_stage_2024(raw: str | None) -> str:
    """Recode a raw 2024 `dev_stage` value to a canonical 2025 posture bucket.

    Uses the extended `DEV_STAGE_RECODE_2024` map (Phase 0, extended in Phase
    2 with the real-world off-enum values). Whitespace is collapsed before
    lookup so double-spaced CSV values still resolve. Empty / unrecognized
    values fall through to `unknown`.
    """
    key = _collapse_ws(raw)
    if not key:
        return STAGE_UNKNOWN
    entry = DEV_STAGE_RECODE_2024.get(key)
    return entry["target"] if entry else STAGE_UNKNOWN


def bucket_stage_2025(raw: str | None) -> str:
    """Bucket a raw 2025 `stage_of_development` value to a posture bucket.

    The 2025 strings are extremely messy (letter prefixes, mojibake apostrophes,
    long-form trailers, casing drift). They are first normalized with
    `_canonicalize_field` — the same canonicalizer the OMB consolidated match
    uses — then classified.

    The `Deployed` arm deliberately mirrors the `pct_deployed` logic in
    `compute_maturity.py` (deployed == matches 'deployed' OR 'operation and
    maintenance' OR 'production'); this reuses that bucketer rather than
    inventing a second one. Retired is checked first because the canonical
    2025 'Retired' description contains the substring 'discontinued' but the
    bare token is 'retired'; pilot before deployed because the 2025 'Pilot'
    long-form text itself contains the word 'deployed'.
    """
    c = _canonicalize_field(raw)
    if not c:
        return STAGE_UNKNOWN
    if "retired" in c or "discontinued" in c:
        return STAGE_RETIRED
    if "pilot" in c:
        return STAGE_PILOT
    # Deployed — same predicate as compute_maturity.py's pct_deployed.
    if "deployed" in c or "operation and maintenance" in c or "production" in c:
        return STAGE_DEPLOYED
    if "pre deployment" in c or "initiated" in c or "acquisition" in c \
            or "development" in c or "ideation" in c or "evaluat" in c \
            or "sandbox" in c:
        return STAGE_PRE
    return STAGE_UNKNOWN


# --- dev_method bucketing --------------------------------------------------

def bucket_dev_method(raw: str | None) -> str:
    """Normalize a raw dev-method value (either year) to a canonical bucket.

    Both years describe the same three-way concept (in-house / contracted /
    both) in free-text-ish enums with heavy drift and high missingness. The
    value is canonicalized, then classified by substring. Empty / N/A /
    'not reported' → `unknown`.
    """
    c = _canonicalize_field(raw)
    if not c or c in ("n/a", "na", "none"):
        return METHOD_UNKNOWN
    if "not reported" in c or "will be updated" in c:
        return METHOD_UNKNOWN
    has_inhouse = "in house" in c or "inhouse" in c
    has_contract = (
        "contract" in c
        or "vendor" in c
        or "purchased" in c
        or "external" in c
    )
    if "both" in c or "combination" in c or (has_inhouse and has_contract):
        return METHOD_BOTH
    if has_inhouse:
        return METHOD_IN_HOUSE
    if has_contract:
        return METHOD_CONTRACTED
    return METHOD_UNKNOWN


# --- Row builders ----------------------------------------------------------

def _pct_change(count_2024: int, count_2025: int) -> float | None:
    """YoY pct change; None when the 2024 side is 0 (no meaningful base)."""
    if count_2024 == 0:
        return None
    return ((count_2025 - count_2024) / count_2024) * 100


def _total_row(conn) -> dict:
    c24 = conn.execute("SELECT COUNT(*) FROM use_cases_2024").fetchone()[0]
    c25 = conn.execute("SELECT COUNT(*) FROM use_cases").fetchone()[0]
    return {
        "dimension": "total",
        "bucket": None,
        "agency_id": None,
        "count_2024": c24,
        "count_2025": c25,
        "delta": c25 - c24,
        "pct_change": _pct_change(c24, c25),
        "comparability": "clean",
        "notes": (
            "Overall individual-use-case counts. Not strictly apples-to-apples: "
            "2025 split COTS into a separate consolidated appendix (excluded "
            "here) while 2024 did not, and the agency set changed (41→36)."
        ),
    }


def _agency_rows(conn) -> list[dict]:
    """Per-agency rows — full-outer join of the two years on agency_id."""
    c24 = dict(
        conn.execute(
            "SELECT agency_id, COUNT(*) FROM use_cases_2024 GROUP BY agency_id"
        ).fetchall()
    )
    c25 = dict(
        conn.execute(
            "SELECT agency_id, COUNT(*) FROM use_cases GROUP BY agency_id"
        ).fetchall()
    )
    abbrevs = dict(
        conn.execute("SELECT id, abbreviation FROM agencies").fetchall()
    )
    rows: list[dict] = []
    for aid in sorted(set(c24) | set(c25)):
        n24 = c24.get(aid, 0)
        n25 = c25.get(aid, 0)
        rows.append({
            "dimension": "agency",
            "bucket": abbrevs.get(aid),
            "agency_id": aid,
            "count_2024": n24,
            "count_2025": n25,
            "delta": n25 - n24,
            "pct_change": _pct_change(n24, n25),
            "comparability": "clean",
            "notes": None,
        })
    return rows


def _stage_rows(conn) -> list[dict]:
    """Development-stage mix rows — recoded, so `lossy`."""
    buckets = [STAGE_PRE, STAGE_PILOT, STAGE_DEPLOYED, STAGE_RETIRED,
               STAGE_UNKNOWN]
    c24 = {b: 0 for b in buckets}
    c25 = {b: 0 for b in buckets}
    for (raw,) in conn.execute("SELECT dev_stage FROM use_cases_2024"):
        c24[bucket_stage_2024(raw)] += 1
    for (raw,) in conn.execute("SELECT stage_of_development FROM use_cases"):
        c25[bucket_stage_2025(raw)] += 1
    note = (
        "Stage mix is lossy: the 2024 5-value SDLC taxonomy (Initiated / "
        "Acquisition / Implementation / Operation / Retired) was recoded to "
        "the 2025 4-value posture taxonomy (Pre-deployment / Pilot / Deployed "
        "/ Retired). 2024 has no clean Pilot analogue. Unmapped/empty values "
        "fall in the 'unknown' bucket."
    )
    rows: list[dict] = []
    for b in buckets:
        rows.append({
            "dimension": "stage",
            "bucket": b,
            "agency_id": None,
            "count_2024": c24[b],
            "count_2025": c25[b],
            "delta": c25[b] - c24[b],
            "pct_change": _pct_change(c24[b], c25[b]),
            "comparability": "lossy",
            "notes": note,
        })
    return rows


def _dev_method_rows(conn) -> list[dict]:
    """Contract-vs-in-house mix rows — sparse both years, so `lossy`."""
    buckets = [METHOD_IN_HOUSE, METHOD_CONTRACTED, METHOD_BOTH, METHOD_UNKNOWN]
    c24 = {b: 0 for b in buckets}
    c25 = {b: 0 for b in buckets}
    for (raw,) in conn.execute("SELECT dev_method FROM use_cases_2024"):
        c24[bucket_dev_method(raw)] += 1
    for (raw,) in conn.execute("SELECT development_type FROM use_cases"):
        c25[bucket_dev_method(raw)] += 1
    total_24 = sum(c24.values()) or 1
    total_25 = sum(c25.values()) or 1
    miss_24 = c24[METHOD_UNKNOWN] / total_24 * 100
    miss_25 = c25[METHOD_UNKNOWN] / total_25 * 100
    note = (
        "Development-method mix is lossy: the field is sparse in both years "
        f"({miss_24:.0f}% of 2024 rows and {miss_25:.0f}% of 2025 rows fall in "
        "the 'unknown' bucket — empty, N/A, or 'not reported'), so the mix is "
        "low-confidence."
    )
    rows: list[dict] = []
    for b in buckets:
        rows.append({
            "dimension": "dev_method",
            "bucket": b,
            "agency_id": None,
            "count_2024": c24[b],
            "count_2025": c25[b],
            "delta": c25[b] - c24[b],
            "pct_change": _pct_change(c24[b], c25[b]),
            "comparability": "lossy",
            "notes": note,
        })
    return rows


# --- Driver ----------------------------------------------------------------

def compute_year_comparison(conn=None):
    """Recompute `year_comparison`. Idempotent (wipe-and-reload)."""
    own = conn is None
    if conn is None:
        conn = get_connection()
    try:
        conn.execute("DELETE FROM year_comparison")

        rows: list[dict] = [_total_row(conn)]
        rows.extend(_agency_rows(conn))
        rows.extend(_stage_rows(conn))
        rows.extend(_dev_method_rows(conn))

        conn.executemany(
            """
            INSERT INTO year_comparison (
                dimension, bucket, agency_id, count_2024, count_2025,
                delta, pct_change, comparability, notes
            ) VALUES (
                :dimension, :bucket, :agency_id, :count_2024, :count_2025,
                :delta, :pct_change, :comparability, :notes
            )
            """,
            rows,
        )
        conn.commit()

        # Summary.
        print("\n=== Year Comparison (year_comparison) ===")
        for dim, n in conn.execute(
            "SELECT dimension, COUNT(*) FROM year_comparison "
            "GROUP BY dimension ORDER BY dimension"
        ):
            print(f"  {dim}: {n} rows")

        total = conn.execute(
            "SELECT count_2024, count_2025, delta, pct_change "
            "FROM year_comparison WHERE dimension='total'"
        ).fetchone()
        pct = f"{total['pct_change']:+.1f}%" if total["pct_change"] is not None else "n/a"
        print(
            f"\n  TOTAL: 2024={total['count_2024']}  2025={total['count_2025']}  "
            f"delta={total['delta']:+d}  ({pct})"
        )

        print("\n  Top 5 agencies by delta:")
        for r in conn.execute(
            "SELECT bucket, count_2024, count_2025, delta FROM year_comparison "
            "WHERE dimension='agency' ORDER BY delta DESC LIMIT 5"
        ):
            print(
                f"    {r['bucket']:<10} 2024={r['count_2024']:>4}  "
                f"2025={r['count_2025']:>4}  delta={r['delta']:+d}"
            )

        return rows
    finally:
        if own:
            conn.close()


if __name__ == "__main__":
    compute_year_comparison()
