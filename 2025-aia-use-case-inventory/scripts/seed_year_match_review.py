"""Seed the Phase-4 year-match adjudication pass.

Phase 4 (Stage 2 input) of the 2024 ↔ 2025 AI use case inventory
comparison project (see `docs/plans/2024-vs-2025-comparison/PLAN.md`).

Emits per-agency-batch review slices to `audit/year_match_review/inputs/`.
Each slice is the working set for one dispatched adjudication agent: every
`suggested_rename` pair plus the agency's `retired_2024` and `new_2025`
residual, so the agent can confirm/reject renames AND detect split/merge
and matcher-missed pairs.

Mirrors `scripts/seed_linkage_pass_inputs.py` — a one-off, orchestrator-
driven step (NOT a `make` step). Idempotent: regenerates the slices each
run.

Slug-keyed, not id-keyed. `use_cases` / `use_cases_2024` row ids are NOT
stable across `make fix`; the slices, the agent recommendations, and the
committed `integration/proposed_lineage.csv` all key on
`(slug, agency_abbreviation)`. The apply script resolves slug → current id.

Output layout — for each batch `audit/year_match_review/inputs/`:
  - `batch_<N>_<slug>.json` — one JSON object per batch, holding three
    lists (`suggested_rename`, `retired_2024`, `new_2025`).
  - `_manifest.csv` — batch → agency assignment + per-batch row counts.

Batching: agencies are bin-packed into ~6-8 balanced batches by total
ambiguous-row load (suggested_rename pairs + retired_2024 + new_2025), so
each dispatched agent gets roughly equal work.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "audit" / "year_match_review" / "inputs"
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"

# Target batch count — agents dispatched in Stage 2, one per batch.
DEFAULT_BATCHES = 7


def _narrative_2024(row: dict) -> str:
    """2024 narrative text: purpose_benefits + outputs (matcher convention)."""
    parts = [row.get("purpose_benefits"), row.get("outputs")]
    return " ".join(p for p in parts if p)


def _narrative_2025(row: dict) -> str:
    """2025 narrative: problem_statement + expected_benefits + system_outputs."""
    parts = [
        row.get("problem_statement"),
        row.get("expected_benefits"),
        row.get("system_outputs"),
    ]
    return " ".join(p for p in parts if p)


def _load_suggested(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    """{agency_abbreviation: [pair_dict, ...]} for every suggested_rename link."""
    by_agency: dict[str, list[dict]] = {}
    for r in conn.execute(
        """
        SELECT l.agency_abbreviation,
               l.match_score        AS name_score,
               u24.slug             AS uc_2024_slug,
               u24.use_case_name    AS uc_2024_name,
               u24.purpose_benefits AS purpose_benefits,
               u24.outputs          AS outputs,
               u25.slug             AS uc_2025_slug,
               u25.use_case_name    AS uc_2025_name,
               u25.problem_statement AS problem_statement,
               u25.expected_benefits AS expected_benefits,
               u25.system_outputs   AS system_outputs
        FROM use_case_year_links l
        JOIN use_cases_2024 u24 ON u24.id = l.uc_2024_id
        JOIN use_cases u25 ON u25.id = l.uc_2025_id
        WHERE l.lineage_status = 'suggested_rename'
        """
    ):
        d = dict(r)
        abbr = d.get("agency_abbreviation") or "_UNKNOWN"
        by_agency.setdefault(abbr, []).append({
            "uc_2024_slug": d["uc_2024_slug"],
            "uc_2024_name": d["uc_2024_name"] or "",
            "uc_2024_narrative": _narrative_2024(d),
            "uc_2025_slug": d["uc_2025_slug"],
            "uc_2025_name": d["uc_2025_name"] or "",
            "uc_2025_narrative": _narrative_2025(d),
            "name_score": round(d["name_score"], 4) if d["name_score"] is not None else None,
        })
    return by_agency


def _load_retired(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    """{agency_abbreviation: [row_dict, ...]} for every retired_2024 link."""
    by_agency: dict[str, list[dict]] = {}
    for r in conn.execute(
        """
        SELECT l.agency_abbreviation,
               u24.slug             AS slug,
               u24.use_case_name    AS use_case_name,
               u24.purpose_benefits AS purpose_benefits,
               u24.outputs          AS outputs
        FROM use_case_year_links l
        JOIN use_cases_2024 u24 ON u24.id = l.uc_2024_id
        WHERE l.lineage_status = 'retired_2024'
        """
    ):
        d = dict(r)
        abbr = d.get("agency_abbreviation") or "_UNKNOWN"
        by_agency.setdefault(abbr, []).append({
            "slug": d["slug"],
            "use_case_name": d["use_case_name"] or "",
            "narrative": _narrative_2024(d),
        })
    return by_agency


def _load_new(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    """{agency_abbreviation: [row_dict, ...]} for every new_2025 link."""
    by_agency: dict[str, list[dict]] = {}
    for r in conn.execute(
        """
        SELECT l.agency_abbreviation,
               u25.slug              AS slug,
               u25.use_case_name     AS use_case_name,
               u25.problem_statement AS problem_statement,
               u25.expected_benefits AS expected_benefits,
               u25.system_outputs    AS system_outputs
        FROM use_case_year_links l
        JOIN use_cases u25 ON u25.id = l.uc_2025_id
        WHERE l.lineage_status = 'new_2025'
        """
    ):
        d = dict(r)
        abbr = d.get("agency_abbreviation") or "_UNKNOWN"
        by_agency.setdefault(abbr, []).append({
            "slug": d["slug"],
            "use_case_name": d["use_case_name"] or "",
            "narrative": _narrative_2025(d),
        })
    return by_agency


def _balance_batches(
    agency_load: dict[str, int], n_batches: int
) -> list[list[str]]:
    """Greedy bin-pack agencies into `n_batches` lists by total row load.

    Largest-first longest-processing-time heuristic: assign each agency to
    the currently-lightest batch. Deterministic (ties broken by agency
    name) so re-runs produce identical batches.
    """
    n_batches = max(1, min(n_batches, len(agency_load) or 1))
    batches: list[list[str]] = [[] for _ in range(n_batches)]
    loads = [0] * n_batches
    # Largest load first; agency name as a stable tiebreaker.
    ordered = sorted(agency_load.items(), key=lambda kv: (-kv[1], kv[0]))
    for abbr, load in ordered:
        i = min(range(n_batches), key=lambda j: (loads[j], j))
        batches[i].append(abbr)
        loads[i] += load
    return [b for b in batches if b]


def seed(
    conn: sqlite3.Connection, out_dir: Path, n_batches: int = DEFAULT_BATCHES
) -> list[dict]:
    """Build the review slices. Returns the per-batch manifest rows."""
    suggested = _load_suggested(conn)
    retired = _load_retired(conn)
    new = _load_new(conn)

    agencies = sorted(set(suggested) | set(retired) | set(new))
    # Ambiguous-row load drives the balancing: the suggested_rename queue is
    # the core work; retired/new are context the agent scans for recoveries.
    agency_load = {
        a: len(suggested.get(a, [])) + len(retired.get(a, [])) + len(new.get(a, []))
        for a in agencies
    }
    batches = _balance_batches(agency_load, n_batches)

    out_dir.mkdir(parents=True, exist_ok=True)
    # Wipe stale slices so a re-run with fewer batches doesn't leave orphans.
    for stale in out_dir.glob("batch_*.json"):
        stale.unlink()

    manifest: list[dict] = []
    for idx, batch_agencies in enumerate(batches, start=1):
        slug = "_".join(batch_agencies[:3]).lower()
        if len(batch_agencies) > 3:
            slug = f"{slug}_plus{len(batch_agencies) - 3}"
        slug = slug or f"batch{idx}"
        # Every row carries its agency_abbreviation so a multi-agency batch
        # is unambiguous to the dispatched agent.
        payload = {
            "batch": idx,
            "agencies": batch_agencies,
            "suggested_rename": [
                {**row, "agency_abbreviation": a}
                for a in batch_agencies for row in suggested.get(a, [])
            ],
            "retired_2024": [
                {**row, "agency_abbreviation": a}
                for a in batch_agencies for row in retired.get(a, [])
            ],
            "new_2025": [
                {**row, "agency_abbreviation": a}
                for a in batch_agencies for row in new.get(a, [])
            ],
        }
        fname = f"batch_{idx}_{slug}.json"
        (out_dir / fname).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False)
        )
        manifest.append({
            "batch": idx,
            "file": fname,
            "agencies": ";".join(batch_agencies),
            "n_agencies": len(batch_agencies),
            "suggested_rename": len(payload["suggested_rename"]),
            "retired_2024": len(payload["retired_2024"]),
            "new_2025": len(payload["new_2025"]),
            "total_rows": (
                len(payload["suggested_rename"])
                + len(payload["retired_2024"])
                + len(payload["new_2025"])
            ),
        })

    manifest_path = out_dir / "_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as fh:
        cols = [
            "batch", "file", "agencies", "n_agencies", "suggested_rename",
            "retired_2024", "new_2025", "total_rows",
        ]
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(manifest)
    return manifest


def _print_summary(manifest: list[dict], out_dir: Path) -> None:
    print(f"Seeded {len(manifest)} review batch(es) to {out_dir}")
    header = (
        f"  {'batch':<6}{'agencies':<10}{'suggested':>11}"
        f"{'retired':>10}{'new':>8}{'total':>8}"
    )
    print(header)
    for m in manifest:
        print(
            f"  {m['batch']:<6}{m['n_agencies']:<10}{m['suggested_rename']:>11}"
            f"{m['retired_2024']:>10}{m['new_2025']:>8}{m['total_rows']:>8}"
        )
    tot_sug = sum(m["suggested_rename"] for m in manifest)
    tot_ret = sum(m["retired_2024"] for m in manifest)
    tot_new = sum(m["new_2025"] for m in manifest)
    print("  " + "-" * (len(header) - 2))
    print(
        f"  {'TOTAL':<6}{'':<10}{tot_sug:>11}{tot_ret:>10}"
        f"{tot_new:>8}{tot_sug + tot_ret + tot_new:>8}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir", type=Path, default=DEFAULT_OUT,
        help="Directory for the review slices.",
    )
    parser.add_argument(
        "--db", type=Path, default=DB_PATH, help="SQLite DB path.",
    )
    parser.add_argument(
        "--batches", type=int, default=DEFAULT_BATCHES,
        help="Target number of agency batches (one dispatched agent each).",
    )
    args = parser.parse_args(argv)

    if not args.db.exists():
        raise FileNotFoundError(args.db)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        manifest = seed(conn, args.out_dir.resolve(), args.batches)
    finally:
        conn.close()
    _print_summary(manifest, args.out_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
