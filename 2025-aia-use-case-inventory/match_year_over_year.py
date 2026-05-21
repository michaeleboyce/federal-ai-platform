"""Deterministic 2024 ↔ 2025 AI use case matcher.

Phase 3 of the 2024 ↔ 2025 AI use case inventory comparison project (see
`docs/plans/2024-vs-2025-comparison/PLAN.md`). Links each 2024 use case
(`use_cases_2024`) to its 2025 counterpart (`use_cases`) where a confident
deterministic match exists; queues the ambiguous residual for Phase 4.

There is no join key — 2024 has no IDs. Every link is *inferred* from
`(agency, use_case_name, narrative text)`. Matching is strictly
**per-agency**: the script loops the union of agency_ids and never compares
rows across agencies.

Three deterministic stages, greedy, with a `matched_2025_ids` set that
prevents any 2025 row being claimed twice (mirrors `matched_db_ids` in
`load_omb_consolidated.py`):

  1. exact name  — normalize_name equality          → continued
  2. fuzzy name  — max(name_match_score,
                   name_containment_score) >= 0.85   → renamed
  3. narrative   — narrative_match_score >= 0.50     → renamed

The fuzzy stage combines difflib's character-ratio with a token-
containment signal because 2025 systematically lengthened titles
(expanded acronyms, appended qualifiers, stamped `[2024 INV#...]`
provenance tags). difflib's ratio penalizes that length asymmetry, so a
2024 name that is a clean token-subset of its 2025 counterpart would be
missed by the ratio alone.

Residual classification:
  - an unmatched 2024 row whose best remaining name score is in
    [0.40, 0.85) is paired greedily with that candidate → suggested_rename
    (a Phase-4 review candidate; consumes the 2025 row).
  - an unmatched 2024 row with no candidate >= 0.40    → retired_2024.
  - any 2025 row still unmatched after all stages       → new_2025.

`drift_fields_json` and `llm_reasoning` stay NULL — they're Phase 4.

Idempotent: prior links are snapshotted by `(uc_2024_id, uc_2025_id)` to
preserve `first_seen` / `resolved_at` / `resolution_note`, then the table
is wiped and rebuilt — the same wipe-and-reload pattern as
`load_omb_consolidated.py`.

Also writes `audit/year_match_queue.csv` — the flat export of all
`suggested_rename` rows, consumed by Phase 4.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from omb_consolidated_match import (
    FUZZY_MATCH_THRESHOLD,
    NARRATIVE_MATCH_THRESHOLD,
    SUGGESTED_RENAME_THRESHOLD,
    name_containment_score,
    name_match_score,
    narrative_match_score,
    normalize_name,
)

ROOT = Path(__file__).resolve().parent
QUEUE_CSV = ROOT / "audit" / "year_match_queue.csv"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _name_score(a: str | None, b: str | None) -> float:
    """Best of difflib character-ratio and token-containment.

    The fuzzy stage scores names with `max(name_match_score,
    name_containment_score)`: the ratio catches near-identical strings
    (minor edits), the containment signal catches the systematic 2025
    pattern where the 2024 name is a clean token-subset of a lengthened
    2025 title. `name_containment_score` is internally guarded, so it
    returns 0.0 for generic stubs and never inflates a non-match.
    """
    return max(name_match_score(a, b), name_containment_score(a, b))


def _narrative_2024(row: dict) -> str:
    """2024 narrative text: purpose_benefits + outputs.

    2024's `purpose_benefits` conflates the problem and the expected
    benefits into one field — there is no separate problem statement.
    """
    parts = [row.get("purpose_benefits"), row.get("outputs")]
    return " ".join(p for p in parts if p)


def _narrative_2025(row: dict) -> str:
    """2025 narrative text: problem_statement + expected_benefits + system_outputs.

    Concatenating both `problem_statement` and `expected_benefits` is the
    intended asymmetric comparison against 2024's conflated
    `purpose_benefits` (see `_narrative_2024`).
    """
    parts = [
        row.get("problem_statement"),
        row.get("expected_benefits"),
        row.get("system_outputs"),
    ]
    return " ".join(p for p in parts if p)


def _load_2024(conn: sqlite3.Connection) -> dict[int, list[dict]]:
    """Return {agency_id: [row_dict, ...]} for use_cases_2024.

    LEFT JOIN — not an inner JOIN — so a row with a NULL or orphan
    `agency_id` is still loaded (it lands under that key, which the matcher
    treats as its own isolated agency group, so the row reconciles as
    retired_2024 rather than silently vanishing).
    """
    by_agency: dict[int, list[dict]] = {}
    for r in conn.execute(
        """
        SELECT uc.id, uc.agency_id, uc.use_case_name,
               uc.purpose_benefits, uc.outputs,
               a.abbreviation AS agency_abbreviation
        FROM use_cases_2024 uc
        LEFT JOIN agencies a ON a.id = uc.agency_id
        """
    ):
        d = dict(r) if isinstance(r, sqlite3.Row) else dict(
            zip(
                ["id", "agency_id", "use_case_name", "purpose_benefits",
                 "outputs", "agency_abbreviation"],
                r,
            )
        )
        d["narrative"] = _narrative_2024(d)
        by_agency.setdefault(d["agency_id"], []).append(d)
    return by_agency


def _load_2025(conn: sqlite3.Connection) -> dict[int, list[dict]]:
    """Return {agency_id: [row_dict, ...]} for use_cases.

    LEFT JOIN — see `_load_2024`: a NULL/orphan `agency_id` row is still
    loaded so it reconciles as new_2025 instead of being silently dropped.
    """
    by_agency: dict[int, list[dict]] = {}
    for r in conn.execute(
        """
        SELECT uc.id, uc.agency_id, uc.use_case_name,
               uc.problem_statement, uc.expected_benefits, uc.system_outputs,
               a.abbreviation AS agency_abbreviation
        FROM use_cases uc
        LEFT JOIN agencies a ON a.id = uc.agency_id
        """
    ):
        d = dict(r) if isinstance(r, sqlite3.Row) else dict(
            zip(
                ["id", "agency_id", "use_case_name", "problem_statement",
                 "expected_benefits", "system_outputs", "agency_abbreviation"],
                r,
            )
        )
        d["narrative"] = _narrative_2025(d)
        by_agency.setdefault(d["agency_id"], []).append(d)
    return by_agency


def _snapshot_prior(conn: sqlite3.Connection) -> dict[tuple, dict]:
    """Snapshot prior links keyed by (uc_2024_id, uc_2025_id).

    Preserves first_seen / resolved_at / resolution_note across the
    wipe-and-reload so a re-run doesn't reset provenance.
    """
    prior: dict[tuple, dict] = {}
    for r in conn.execute(
        "SELECT uc_2024_id, uc_2025_id, first_seen, resolved_at, "
        "resolution_note FROM use_case_year_links"
    ):
        if isinstance(r, sqlite3.Row):
            key = (r["uc_2024_id"], r["uc_2025_id"])
            prior[key] = dict(r)
        else:
            uc24, uc25, first_seen, resolved_at, resolution_note = r
            prior[(uc24, uc25)] = {
                "first_seen": first_seen,
                "resolved_at": resolved_at,
                "resolution_note": resolution_note,
            }
    return prior


def _insert_link(
    conn: sqlite3.Connection,
    run_at: str,
    prior: dict[tuple, dict],
    *,
    uc_2024_id: int | None,
    uc_2025_id: int | None,
    agency_id: int | None,
    agency_abbreviation: str | None,
    match_method: str,
    match_score: float | None,
    lineage_status: str,
) -> None:
    prior_row = prior.get((uc_2024_id, uc_2025_id))
    first_seen = (
        prior_row["first_seen"] if prior_row and prior_row["first_seen"] else run_at
    )
    resolved_at = prior_row["resolved_at"] if prior_row else None
    resolution_note = prior_row["resolution_note"] if prior_row else None
    conn.execute(
        """
        INSERT INTO use_case_year_links(
            run_at, uc_2024_id, uc_2025_id, agency_id, agency_abbreviation,
            match_method, match_score, lineage_status, drift_fields_json,
            llm_reasoning, first_seen, last_seen, resolved_at, resolution_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?)
        """,
        (
            run_at, uc_2024_id, uc_2025_id, agency_id, agency_abbreviation,
            match_method, match_score, lineage_status,
            first_seen, run_at, resolved_at, resolution_note,
        ),
    )


def _match_agency(
    rows_2024: list[dict], rows_2025: list[dict]
) -> list[dict]:
    """Run the three deterministic stages for one agency.

    Returns a list of link descriptors (plain dicts) — no DB writes here,
    so the matching policy stays unit-testable in isolation. Every input
    2024 row and every input 2025 row appears in exactly one descriptor.
    """
    links: list[dict] = []
    matched_2025_ids: set[int] = set()
    # The 2025 rows that are still claimable, kept as a list so stages can
    # rescan it cheaply; membership pruned via matched_2025_ids.
    unmatched_2024 = list(rows_2024)

    def _available_2025() -> list[dict]:
        return [r for r in rows_2025 if r["id"] not in matched_2025_ids]

    # ── Stage 1: exact name ────────────────────────────────────────────
    # Index available 2025 rows by normalized name; first-claim wins so a
    # 2025 row is never handed to two 2024 rows.
    exact_index: dict[str, list[dict]] = {}
    for r in rows_2025:
        exact_index.setdefault(normalize_name(r["use_case_name"]), []).append(r)
    still_2024: list[dict] = []
    for a in unmatched_2024:
        norm = normalize_name(a["use_case_name"])
        candidate = None
        for r in exact_index.get(norm, []):
            if r["id"] not in matched_2025_ids:
                candidate = r
                break
        if candidate is not None and norm:
            matched_2025_ids.add(candidate["id"])
            links.append({
                "uc_2024": a, "uc_2025": candidate,
                "match_method": "exact_name", "match_score": 1.0,
                "lineage_status": "continued",
            })
        else:
            still_2024.append(a)
    unmatched_2024 = still_2024

    # ── Stage 2: fuzzy name (>= FUZZY_MATCH_THRESHOLD) ─────────────────
    # Score names with max(character-ratio, token-containment) — see
    # `_name_score`: containment catches the 2025 length-asymmetry pattern
    # difflib's ratio penalizes.
    still_2024 = []
    for a in unmatched_2024:
        best_score, best = 0.0, None
        for r in _available_2025():
            s = _name_score(a["use_case_name"], r["use_case_name"])
            if s > best_score:
                best_score, best = s, r
        if best is not None and best_score >= FUZZY_MATCH_THRESHOLD:
            matched_2025_ids.add(best["id"])
            links.append({
                "uc_2024": a, "uc_2025": best,
                "match_method": "fuzzy_name", "match_score": best_score,
                "lineage_status": "renamed",
            })
        else:
            still_2024.append(a)
    unmatched_2024 = still_2024

    # ── Stage 3: narrative (>= NARRATIVE_MATCH_THRESHOLD) ──────────────
    still_2024 = []
    for a in unmatched_2024:
        best_score, best = 0.0, None
        for r in _available_2025():
            s = narrative_match_score(a["narrative"], r["narrative"])
            if s > best_score:
                best_score, best = s, r
        if best is not None and best_score >= NARRATIVE_MATCH_THRESHOLD:
            matched_2025_ids.add(best["id"])
            links.append({
                "uc_2024": a, "uc_2025": best,
                "match_method": "narrative", "match_score": best_score,
                "lineage_status": "renamed",
            })
        else:
            still_2024.append(a)
    unmatched_2024 = still_2024

    # ── Residual: suggested_rename vs retired_2024 ─────────────────────
    # For each still-unmatched 2024 row, find its best remaining 2025
    # candidate by NAME score. If that score lands in the suggested-rename
    # band [0.40, 0.85) the pair is queued for Phase 4 (both ids set, the
    # 2025 row is consumed). Below 0.40 → retired_2024.
    for a in unmatched_2024:
        best_score, best = 0.0, None
        # Recompute the best NAME candidate over what is *still* free —
        # stage 3 may have consumed earlier picks. Use the same combined
        # name score (`_name_score`) as the fuzzy stage so a containment-
        # strong pair lands in the suggested-rename band consistently.
        for r in _available_2025():
            s = _name_score(a["use_case_name"], r["use_case_name"])
            if s > best_score:
                best_score, best = s, r
        if (
            best is not None
            and SUGGESTED_RENAME_THRESHOLD <= best_score < FUZZY_MATCH_THRESHOLD
        ):
            matched_2025_ids.add(best["id"])
            narr = narrative_match_score(a["narrative"], best["narrative"])
            links.append({
                "uc_2024": a, "uc_2025": best,
                "match_method": "fuzzy_name", "match_score": best_score,
                "lineage_status": "suggested_rename",
                "narrative_score": narr,
            })
        else:
            links.append({
                "uc_2024": a, "uc_2025": None,
                "match_method": "none", "match_score": None,
                "lineage_status": "retired_2024",
            })

    # ── Leftover 2025 rows → new_2025 ──────────────────────────────────
    for r in rows_2025:
        if r["id"] not in matched_2025_ids:
            links.append({
                "uc_2024": None, "uc_2025": r,
                "match_method": "none", "match_score": None,
                "lineage_status": "new_2025",
            })

    return links


def match(conn: sqlite3.Connection) -> dict[str, int]:
    """Run the matcher over the whole DB. Returns the status rollup."""
    run_at = _now()
    prior = _snapshot_prior(conn)
    conn.execute("DELETE FROM use_case_year_links")

    rows_2024 = _load_2024(conn)
    rows_2025 = _load_2025(conn)
    # Sort with a None-safe key: a NULL/orphan agency_id sorts last as its
    # own isolated group rather than crashing the int comparison.
    agency_ids = sorted(
        set(rows_2024) | set(rows_2025),
        key=lambda x: (x is None, x),
    )

    # Resolve agency_id -> abbreviation once (covers agencies present in
    # only one of the two corpora).
    abbr_by_agency: dict[int, str | None] = {}
    for r in conn.execute("SELECT id, abbreviation FROM agencies"):
        abbr_by_agency[r[0]] = r[1]

    rollup: dict[str, int] = {}
    queue_rows: list[dict] = []
    per_agency: list[tuple[str, dict[str, int]]] = []

    for agency_id in agency_ids:
        a2024 = rows_2024.get(agency_id, [])
        a2025 = rows_2025.get(agency_id, [])
        abbr = abbr_by_agency.get(agency_id)
        links = _match_agency(a2024, a2025)

        agency_counts: dict[str, int] = {}
        for link in links:
            status = link["lineage_status"]
            uc24 = link["uc_2024"]
            uc25 = link["uc_2025"]
            _insert_link(
                conn, run_at, prior,
                uc_2024_id=uc24["id"] if uc24 else None,
                uc_2025_id=uc25["id"] if uc25 else None,
                agency_id=agency_id,
                agency_abbreviation=abbr,
                match_method=link["match_method"],
                match_score=link["match_score"],
                lineage_status=status,
            )
            rollup[status] = rollup.get(status, 0) + 1
            agency_counts[status] = agency_counts.get(status, 0) + 1
            if status == "suggested_rename":
                queue_rows.append({
                    "agency_abbreviation": abbr or "",
                    "uc_2024_id": uc24["id"],
                    "uc_2024_name": uc24["use_case_name"] or "",
                    "uc_2025_id": uc25["id"],
                    "uc_2025_name": uc25["use_case_name"] or "",
                    "name_score": round(link["match_score"], 4),
                    "narrative_score": round(link.get("narrative_score", 0.0), 4),
                    "lineage_status": status,
                })
        per_agency.append((abbr or f"agency#{agency_id}", agency_counts))

    conn.commit()
    _write_queue(queue_rows)
    _print_summary(per_agency, rollup)
    _assert_reconciliation(conn)
    return rollup


_QUEUE_COLUMNS = [
    "agency_abbreviation", "uc_2024_id", "uc_2024_name",
    "uc_2025_id", "uc_2025_name", "name_score", "narrative_score",
    "lineage_status",
]


def _write_queue(queue_rows: list[dict]) -> None:
    QUEUE_CSV.parent.mkdir(parents=True, exist_ok=True)
    queue_rows = sorted(
        queue_rows, key=lambda r: (r["agency_abbreviation"], r["uc_2024_id"])
    )
    with QUEUE_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_QUEUE_COLUMNS)
        writer.writeheader()
        writer.writerows(queue_rows)


_STATUS_ORDER = [
    "continued", "renamed", "suggested_rename", "retired_2024", "new_2025",
]


def _print_summary(
    per_agency: list[tuple[str, dict[str, int]]], rollup: dict[str, int]
) -> None:
    print("Year-over-year match summary (per agency):")
    header = f"  {'agency':<10}" + "".join(f"{s:>17}" for s in _STATUS_ORDER)
    print(header)
    for abbr, counts in sorted(per_agency):
        line = f"  {abbr:<10}" + "".join(
            f"{counts.get(s, 0):>17}" for s in _STATUS_ORDER
        )
        print(line)
    print("  " + "-" * (len(header) - 2))
    total_line = f"  {'TOTAL':<10}" + "".join(
        f"{rollup.get(s, 0):>17}" for s in _STATUS_ORDER
    )
    print(total_line)
    total_links = sum(rollup.values())
    matched = rollup.get("continued", 0) + rollup.get("renamed", 0)
    if total_links:
        print(
            f"  match rate (continued+renamed / all links): "
            f"{matched}/{total_links} = {matched / total_links:.1%}"
        )


def _assert_reconciliation(conn: sqlite3.Connection) -> None:
    """Every 2024 row appears as uc_2024_id exactly once; every 2025 row
    appears as uc_2025_id exactly once."""
    n_2024 = conn.execute("SELECT COUNT(*) FROM use_cases_2024").fetchone()[0]
    n_2025 = conn.execute("SELECT COUNT(*) FROM use_cases").fetchone()[0]

    linked_2024 = conn.execute(
        "SELECT COUNT(*) FROM use_case_year_links WHERE uc_2024_id IS NOT NULL"
    ).fetchone()[0]
    distinct_2024 = conn.execute(
        "SELECT COUNT(DISTINCT uc_2024_id) FROM use_case_year_links "
        "WHERE uc_2024_id IS NOT NULL"
    ).fetchone()[0]
    linked_2025 = conn.execute(
        "SELECT COUNT(*) FROM use_case_year_links WHERE uc_2025_id IS NOT NULL"
    ).fetchone()[0]
    distinct_2025 = conn.execute(
        "SELECT COUNT(DISTINCT uc_2025_id) FROM use_case_year_links "
        "WHERE uc_2025_id IS NOT NULL"
    ).fetchone()[0]

    assert linked_2024 == distinct_2024 == n_2024, (
        f"2024 reconciliation failed: {n_2024} use_cases_2024 rows, "
        f"{linked_2024} link rows with uc_2024_id, "
        f"{distinct_2024} distinct uc_2024_id"
    )
    assert linked_2025 == distinct_2025 == n_2025, (
        f"2025 reconciliation failed: {n_2025} use_cases rows, "
        f"{linked_2025} link rows with uc_2025_id, "
        f"{distinct_2025} distinct uc_2025_id"
    )
    print(
        f"  reconciliation OK: {n_2024}/{n_2024} 2024 rows linked, "
        f"{n_2025}/{n_2025} 2025 rows linked."
    )


def main(argv: list[str] | None = None) -> int:
    from db import get_connection
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    match(conn)
    print(f"Wrote {QUEUE_CSV.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
