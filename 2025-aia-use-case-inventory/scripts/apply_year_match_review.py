"""Apply the multi-agent year-match adjudication pass.

Phase 4 (Stage 3, step 2) of the 2024 ↔ 2025 AI use case inventory
comparison project (see `docs/plans/2024-vs-2025-comparison/PLAN.md`).

Reads the committed `audit/year_match_review/integration/proposed_lineage.csv`
and overlays its decisions onto `use_case_year_links` — on top of the
deterministic matcher's freshly-rebuilt baseline. Runs every `make fix`
after `match_year_over_year.py`; idempotent (the matcher rebuilds the
baseline each run, this re-applies the same committed decisions).

Slug-keyed: `proposed_lineage.csv` keys on `use_cases_2024.slug` /
`use_cases.slug`; this script resolves slug → current id (ids are not
stable across `make fix`).

Decision effects (see CHARTER.md):
  - confirm_rename → the suggested_rename link → lineage_status='renamed',
    match_method='llm_review', llm_reasoning, resolved_at.
  - reject_rename  → delete the suggested_rename link; insert a
    retired_2024 row (the 2024 slug) + a new_2025 row (the 2025 slug).
  - recover_match  → delete the separate retired_2024 + new_2025 rows;
    insert one renamed link.
  - split          → replace the affected links with N split rows
    (same uc_2024_id, distinct uc_2025_id).
  - merge          → replace the affected links with N merged rows
    (distinct uc_2024_id, same uc_2025_id).

Tail steps (plan §4, §6):
  - Reconciliation invariant — every use_cases_2024 row appears as
    uc_2024_id in ≥1 link; every use_cases row as uc_2025_id in ≥1 link.
    (≥1, not ==1: split/merge are intentionally N:M.) Asserted.
  - Retired cross-check — flags inconsistencies (a new_2025 row already at
    Retired stage; a retired_2024 row whose 2024 filing was itself Retired)
    to integration/classification_flags.csv. Non-blocking.

Default: --apply (writes); the matcher already ran in `make fix` so this is
not a preview-then-commit step. Re-runnable any time.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# This script lives in scripts/ but imports repo-root modules — put the
# repo root on the path (the convention in scripts/populate_use_case_products.py).
sys.path.insert(0, str(ROOT))

from column_maps_2024 import DEV_STAGE_RECODE_2024  # noqa: E402
from compute_year_comparison import (  # noqa: E402
    STAGE_RETIRED,
    bucket_stage_2025,
)

DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
DEFAULT_PASS_DIR = ROOT / "audit" / "year_match_review"

_FINAL_STATUSES = (
    "continued", "renamed", "split", "merged", "retired_2024", "new_2025",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _slugs(value: str | None) -> list[str]:
    """Split a pipe-joined slug cell to a clean list."""
    if not value:
        return []
    return [s.strip() for s in value.split("|") if s.strip()]


# ── slug → id resolution ──────────────────────────────────────────────────

def _slug_index(conn: sqlite3.Connection) -> tuple[dict[str, int], dict[str, int]]:
    """Return ({2024_slug: id}, {2025_slug: id})."""
    idx_2024 = {
        r[0]: r[1]
        for r in conn.execute("SELECT slug, id FROM use_cases_2024 WHERE slug IS NOT NULL")
    }
    idx_2025 = {
        r[0]: r[1]
        for r in conn.execute("SELECT slug, id FROM use_cases WHERE slug IS NOT NULL")
    }
    return idx_2024, idx_2025


def _agency_of(conn: sqlite3.Connection, *, uc_2024_id: int | None,
               uc_2025_id: int | None) -> tuple[int | None, str | None]:
    """Resolve (agency_id, abbreviation) from whichever side row exists."""
    if uc_2025_id is not None:
        r = conn.execute(
            "SELECT a.id, a.abbreviation FROM use_cases u "
            "LEFT JOIN agencies a ON a.id = u.agency_id WHERE u.id=?",
            (uc_2025_id,),
        ).fetchone()
        if r:
            return r[0], r[1]
    if uc_2024_id is not None:
        r = conn.execute(
            "SELECT a.id, a.abbreviation FROM use_cases_2024 u "
            "LEFT JOIN agencies a ON a.id = u.agency_id WHERE u.id=?",
            (uc_2024_id,),
        ).fetchone()
        if r:
            return r[0], r[1]
    return None, None


def _insert_link(conn: sqlite3.Connection, run_at: str, *, uc_2024_id: int | None,
                 uc_2025_id: int | None, match_method: str, match_score: float | None,
                 lineage_status: str, llm_reasoning: str | None) -> int:
    """Insert one link row; return its rowid (so callers can stamp it)."""
    agency_id, abbr = _agency_of(conn, uc_2024_id=uc_2024_id, uc_2025_id=uc_2025_id)
    cur = conn.execute(
        """
        INSERT INTO use_case_year_links(
            run_at, uc_2024_id, uc_2025_id, agency_id, agency_abbreviation,
            match_method, match_score, lineage_status, drift_fields_json,
            llm_reasoning, first_seen, last_seen, resolved_at, resolution_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, NULL)
        """,
        (run_at, uc_2024_id, uc_2025_id, agency_id, abbr, match_method,
         match_score, lineage_status, llm_reasoning, run_at, run_at, run_at),
    )
    return cur.lastrowid


# ── decision application ──────────────────────────────────────────────────

def apply_decisions(conn: sqlite3.Connection, pass_dir: Path) -> dict[str, int]:
    """Overlay proposed_lineage.csv onto use_case_year_links.

    Returns a per-action count of decisions applied. A no-op (every count
    0) when proposed_lineage.csv is absent or empty.
    """
    csv_path = pass_dir / "integration" / "proposed_lineage.csv"
    decisions = _read_csv(csv_path)
    applied: dict[str, int] = defaultdict(int)
    if not decisions:
        print(f"  no decisions ({csv_path.name} absent or empty) — baseline left intact")
        return dict(applied)

    run_at = _now()
    idx_2024, idx_2025 = _slug_index(conn)
    cur = conn.cursor()
    skipped = 0
    superseded = {"retired_2024": 0, "new_2025": 0}

    # Apply ordering: reject_rename must run before recover_match. A
    # reject_rename sends its slugs back to residual (retired_2024 /
    # new_2025); a recover_match for a shared slug then re-links that
    # freed residual row. Process rejects first so the recover operates
    # on the freed slug. (The handlers are self-idempotent — delete-by-
    # slug then insert — so within-action order is irrelevant; only this
    # cross-action ordering matters.) Decisions with the same priority
    # keep proposed_lineage.csv's deterministic order via a stable sort.
    _APPLY_ORDER = {
        "reject_rename": 0,
        "confirm_rename": 1,
        "split": 1,
        "merge": 1,
        "recover_match": 2,
    }
    decisions = sorted(
        decisions, key=lambda d: _APPLY_ORDER.get((d.get("action") or "").strip(), 1)
    )

    for d in decisions:
        action = (d.get("action") or "").strip()
        reasoning = (d.get("reasoning") or "").strip() or None
        s2024 = _slugs(d.get("uc_2024_slugs"))
        s2025 = _slugs(d.get("uc_2025_slugs"))
        ids_2024 = [idx_2024[s] for s in s2024 if s in idx_2024]
        ids_2025 = [idx_2025[s] for s in s2025 if s in idx_2025]
        # A decision whose slugs no longer resolve (e.g. source row dropped
        # in a later refresh) is skipped, not fatal.
        if len(ids_2024) != len(s2024) or len(ids_2025) != len(s2025):
            skipped += 1
            continue

        if action == "confirm_rename":
            i24, i25 = ids_2024[0], ids_2025[0]
            # Idempotent: clear any prior result for this pair (the
            # suggested_rename link on run 1, the renamed link on re-runs)
            # then insert the canonical renamed row. A bare UPDATE would
            # miss the second run after the matcher status differs.
            cur.execute(
                "DELETE FROM use_case_year_links WHERE uc_2024_id=? AND uc_2025_id=?",
                (i24, i25),
            )
            # Also clear stray residuals for either endpoint (same hygiene
            # as recover_match). Post loader-fix, the matcher may no longer
            # propose this exact pair — it then emits a new_2025/-retired
            # residual for an endpoint, which must not survive the confirm.
            cur.execute(
                "DELETE FROM use_case_year_links "
                "WHERE uc_2024_id=? AND uc_2025_id IS NULL "
                "AND lineage_status='retired_2024'",
                (i24,),
            )
            cur.execute(
                "DELETE FROM use_case_year_links "
                "WHERE uc_2025_id=? AND uc_2024_id IS NULL "
                "AND lineage_status='new_2025'",
                (i25,),
            )
            link_id = _insert_link(
                conn, run_at, uc_2024_id=i24, uc_2025_id=i25,
                match_method="llm_review", match_score=None,
                lineage_status="renamed", llm_reasoning=reasoning,
            )
            cur.execute(
                "UPDATE use_case_year_links SET resolved_at=? WHERE id=?",
                (run_at, link_id),
            )
            applied["confirm_rename"] += 1

        elif action == "reject_rename":
            i24, i25 = ids_2024[0], ids_2025[0]
            # Idempotent: delete both the source (suggested_rename) link and
            # any prior TARGET rows (a retired_2024 for this 2024 id, a
            # new_2025 for this 2025 id) before re-inserting the fresh pair.
            cur.execute(
                "DELETE FROM use_case_year_links WHERE uc_2024_id=? AND uc_2025_id=?",
                (i24, i25),
            )
            cur.execute(
                "DELETE FROM use_case_year_links "
                "WHERE uc_2024_id=? AND uc_2025_id IS NULL "
                "AND lineage_status='retired_2024'",
                (i24,),
            )
            cur.execute(
                "DELETE FROM use_case_year_links "
                "WHERE uc_2025_id=? AND uc_2024_id IS NULL "
                "AND lineage_status='new_2025'",
                (i25,),
            )
            # 2026-07 guard: insert a residual only if the fresh baseline
            # hasn't already given the row a live PAIRED link. The loader
            # name-collision fix recovered 2025 twins for rows that were
            # invisible when these decisions were authored — a stale
            # "retired_2024"/"new_2025" verdict yields to the matcher's
            # exact-name link to the recovered twin. Counted and printed,
            # never silently dropped.
            if cur.execute(
                "SELECT 1 FROM use_case_year_links "
                "WHERE uc_2024_id=? AND uc_2025_id IS NOT NULL LIMIT 1",
                (i24,),
            ).fetchone() is None:
                _insert_link(conn, run_at, uc_2024_id=i24, uc_2025_id=None,
                             match_method="llm_review", match_score=None,
                             lineage_status="retired_2024",
                             llm_reasoning=reasoning)
            else:
                superseded["retired_2024"] += 1
            if cur.execute(
                "SELECT 1 FROM use_case_year_links "
                "WHERE uc_2025_id=? AND uc_2024_id IS NOT NULL LIMIT 1",
                (i25,),
            ).fetchone() is None:
                _insert_link(conn, run_at, uc_2024_id=None, uc_2025_id=i25,
                             match_method="llm_review", match_score=None,
                             lineage_status="new_2025",
                             llm_reasoning=reasoning)
            else:
                superseded["new_2025"] += 1
            applied["reject_rename"] += 1

        elif action == "recover_match":
            i24, i25 = ids_2024[0], ids_2025[0]
            # Idempotent: delete the separate retired_2024 + new_2025 rows
            # AND any prior renamed link for this pair (the TARGET of a
            # previous run) before re-inserting the single renamed link.
            cur.execute(
                "DELETE FROM use_case_year_links WHERE uc_2024_id=? AND uc_2025_id IS NULL",
                (i24,),
            )
            cur.execute(
                "DELETE FROM use_case_year_links WHERE uc_2025_id=? AND uc_2024_id IS NULL",
                (i25,),
            )
            cur.execute(
                "DELETE FROM use_case_year_links WHERE uc_2024_id=? AND uc_2025_id=?",
                (i24, i25),
            )
            _insert_link(conn, run_at, uc_2024_id=i24, uc_2025_id=i25,
                         match_method="llm_review", match_score=None,
                         lineage_status="renamed", llm_reasoning=reasoning)
            applied["recover_match"] += 1

        elif action == "split":
            i24 = ids_2024[0]
            # Drop the matcher's link for the 2024 row and every link that
            # currently claims one of the split-target 2025 rows (this also
            # clears the TARGET split rows from a prior run), then insert
            # N fresh split rows.
            cur.execute("DELETE FROM use_case_year_links WHERE uc_2024_id=?", (i24,))
            for i25 in ids_2025:
                cur.execute(
                    "DELETE FROM use_case_year_links WHERE uc_2025_id=?", (i25,)
                )
            for i25 in ids_2025:
                _insert_link(conn, run_at, uc_2024_id=i24, uc_2025_id=i25,
                             match_method="llm_review", match_score=None,
                             lineage_status="split", llm_reasoning=reasoning)
            applied["split"] += 1

        elif action == "merge":
            i25 = ids_2025[0]
            # Drop the matcher's link for the 2025 row and every link that
            # currently claims one of the merge-source 2024 rows (this also
            # clears the TARGET merged rows from a prior run), then insert
            # N fresh merged rows.
            cur.execute("DELETE FROM use_case_year_links WHERE uc_2025_id=?", (i25,))
            for i24 in ids_2024:
                cur.execute(
                    "DELETE FROM use_case_year_links WHERE uc_2024_id=?", (i24,)
                )
            for i24 in ids_2024:
                _insert_link(conn, run_at, uc_2024_id=i24, uc_2025_id=i25,
                             match_method="llm_review", match_score=None,
                             lineage_status="merged", llm_reasoning=reasoning)
            applied["merge"] += 1
        else:
            skipped += 1

    conn.commit()
    print(f"  applied {sum(applied.values())} decision(s); skipped {skipped}")
    for action in ("confirm_rename", "reject_rename", "recover_match",
                   "split", "merge"):
        if applied.get(action):
            print(f"    {action:<16}: {applied[action]}")
    if any(superseded.values()):
        print(
            "  residuals superseded by fresh baseline links "
            f"(recovered-twin precedence): {superseded}"
        )
    return dict(applied)


# ── orphan re-homing (plan §4) ────────────────────────────────────────────

def rehome_orphans(conn: sqlite3.Connection) -> dict[str, int]:
    """Guarantee the ≥1 reconciliation invariant by construction.

    Runs after every decision is applied and before assert_reconciliation.
    A decision handler can leave a row orphaned in an edge case — e.g. a
    `split` discards the matcher's suggested 2025 partner (a wrong-component
    row) so that row ends up in no link at all. Rather than patch each
    handler's bookkeeping, this final pass sweeps any 2024/2025 row that no
    link references and inserts a retired_2024 / new_2025 link for it.

    Idempotent: the matcher rebuilds the baseline each `make fix`, so a
    re-run sees the same orphan set (or none) and re-creates the same links.
    """
    run_at = _now()
    note = "re-homed orphan after Phase-4 apply"
    rehomed: dict[str, int] = defaultdict(int)

    orphan_2024 = [
        r[0] for r in conn.execute(
            "SELECT slug FROM use_cases_2024 WHERE slug IS NOT NULL "
            "AND slug NOT IN ("
            "  SELECT u.slug FROM use_case_year_links l "
            "  JOIN use_cases_2024 u ON u.id = l.uc_2024_id "
            "  WHERE l.uc_2024_id IS NOT NULL)"
        )
    ]
    orphan_2025 = [
        r[0] for r in conn.execute(
            "SELECT slug FROM use_cases WHERE slug IS NOT NULL "
            "AND slug NOT IN ("
            "  SELECT u.slug FROM use_case_year_links l "
            "  JOIN use_cases u ON u.id = l.uc_2025_id "
            "  WHERE l.uc_2025_id IS NOT NULL)"
        )
    ]

    idx_2024, idx_2025 = _slug_index(conn)
    for slug in orphan_2024:
        i24 = idx_2024.get(slug)
        if i24 is None:
            continue
        link_id = _insert_link(
            conn, run_at, uc_2024_id=i24, uc_2025_id=None,
            match_method="none", match_score=None,
            lineage_status="retired_2024", llm_reasoning=None,
        )
        # Stamp by the freshly-inserted row's id — a WHERE on uc_2024_id
        # could hit a different unstamped row sharing that id.
        conn.execute(
            "UPDATE use_case_year_links SET resolution_note=? WHERE id=?",
            (note, link_id),
        )
        rehomed["retired_2024"] += 1
    for slug in orphan_2025:
        i25 = idx_2025.get(slug)
        if i25 is None:
            continue
        link_id = _insert_link(
            conn, run_at, uc_2024_id=None, uc_2025_id=i25,
            match_method="none", match_score=None,
            lineage_status="new_2025", llm_reasoning=None,
        )
        conn.execute(
            "UPDATE use_case_year_links SET resolution_note=? WHERE id=?",
            (note, link_id),
        )
        rehomed["new_2025"] += 1

    conn.commit()
    total = sum(rehomed.values())
    if total:
        print(
            f"  re-homed {total} orphan(s): "
            f"{rehomed.get('retired_2024', 0)} retired_2024, "
            f"{rehomed.get('new_2025', 0)} new_2025"
        )
    else:
        print("  re-homed 0 orphans (every row already linked)")
    return dict(rehomed)


# ── reconciliation + retired cross-check (plan §4, §6) ────────────────────

def assert_reconciliation(conn: sqlite3.Connection) -> None:
    """Every use_cases_2024 row appears as uc_2024_id in ≥1 link; every
    use_cases row as uc_2025_id in ≥1 link. (≥1, not ==1 — split/merge
    are intentionally N:M.)

    Also asserts no use case carries a *duplicate* link in a 1:1 status:
      - in 'continued'/'renamed'/'retired_2024' a uc_2024_id appears once;
      - in 'continued'/'renamed'/'new_2025' a uc_2025_id appears once.
    (split is N 2025 rows for one 2024 id; merge the reverse — both are
    excluded from the relevant side.) This catches a non-idempotent
    decision handler that double-inserts the same 1:1 link.
    """
    n_2024 = conn.execute("SELECT COUNT(*) FROM use_cases_2024").fetchone()[0]
    n_2025 = conn.execute("SELECT COUNT(*) FROM use_cases").fetchone()[0]
    distinct_2024 = conn.execute(
        "SELECT COUNT(DISTINCT uc_2024_id) FROM use_case_year_links "
        "WHERE uc_2024_id IS NOT NULL"
    ).fetchone()[0]
    distinct_2025 = conn.execute(
        "SELECT COUNT(DISTINCT uc_2025_id) FROM use_case_year_links "
        "WHERE uc_2025_id IS NOT NULL"
    ).fetchone()[0]
    assert distinct_2024 == n_2024, (
        f"2024 reconciliation failed: {n_2024} use_cases_2024 rows, "
        f"{distinct_2024} distinct uc_2024_id in links"
    )
    assert distinct_2025 == n_2025, (
        f"2025 reconciliation failed: {n_2025} use_cases rows, "
        f"{distinct_2025} distinct uc_2025_id in links"
    )

    # 1:1 uniqueness — duplicate rows for the same use case in a 1:1 status
    # would slip past the COUNT(DISTINCT) checks above.
    dup_2024 = conn.execute(
        "SELECT uc_2024_id, COUNT(*) c FROM use_case_year_links "
        "WHERE uc_2024_id IS NOT NULL "
        "AND lineage_status IN ('continued', 'renamed', 'retired_2024') "
        "GROUP BY uc_2024_id HAVING c > 1"
    ).fetchall()
    assert not dup_2024, (
        f"1:1 uniqueness failed: {len(dup_2024)} uc_2024_id(s) with a "
        f"duplicate continued/renamed/retired_2024 link "
        f"(e.g. {tuple(dup_2024[0])})"
    )
    dup_2025 = conn.execute(
        "SELECT uc_2025_id, COUNT(*) c FROM use_case_year_links "
        "WHERE uc_2025_id IS NOT NULL "
        "AND lineage_status IN ('continued', 'renamed', 'new_2025') "
        "GROUP BY uc_2025_id HAVING c > 1"
    ).fetchall()
    assert not dup_2025, (
        f"1:1 uniqueness failed: {len(dup_2025)} uc_2025_id(s) with a "
        f"duplicate continued/renamed/new_2025 link "
        f"(e.g. {tuple(dup_2025[0])})"
    )

    print(
        f"  reconciliation OK: {n_2024}/{n_2024} 2024 rows linked, "
        f"{n_2025}/{n_2025} 2025 rows linked (≥1 each); "
        f"no duplicate 1:1 links."
    )


def _stage_2024_is_retired(raw: str | None) -> bool:
    """True when a raw 2024 dev_stage value recodes to the Retired bucket."""
    if not raw:
        return False
    entry = DEV_STAGE_RECODE_2024.get(" ".join(raw.split()))
    return bool(entry and entry["target"] == "d) Retired")


def retired_cross_check(conn: sqlite3.Connection, pass_dir: Path) -> int:
    """Flag classification inconsistencies to classification_flags.csv.

    Two checks (non-blocking — written for review, do not abort):
      - a new_2025 link whose 2025 row is itself at the Retired stage;
      - a retired_2024 link whose 2024 row was itself filed as Retired.
    Reuses compute_year_comparison.bucket_stage_2025 — does not reimplement.
    """
    flags: list[dict[str, str]] = []

    for r in conn.execute(
        """
        SELECT l.id, l.agency_abbreviation, u.slug, u.use_case_name,
               u.stage_of_development
        FROM use_case_year_links l
        JOIN use_cases u ON u.id = l.uc_2025_id
        WHERE l.lineage_status = 'new_2025'
        """
    ):
        if bucket_stage_2025(r[4]) == STAGE_RETIRED:
            flags.append({
                "flag": "new_2025_already_retired",
                "link_id": str(r[0]),
                "agency_abbreviation": r[1] or "",
                "slug": r[2] or "",
                "use_case_name": r[3] or "",
                "detail": f"2025 stage={r[4]!r} buckets as Retired",
            })

    for r in conn.execute(
        """
        SELECT l.id, l.agency_abbreviation, u.slug, u.use_case_name,
               u.dev_stage
        FROM use_case_year_links l
        JOIN use_cases_2024 u ON u.id = l.uc_2024_id
        WHERE l.lineage_status = 'retired_2024'
        """
    ):
        if _stage_2024_is_retired(r[4]):
            flags.append({
                "flag": "retired_2024_filed_retired",
                "link_id": str(r[0]),
                "agency_abbreviation": r[1] or "",
                "slug": r[2] or "",
                "use_case_name": r[3] or "",
                "detail": f"2024 dev_stage={r[4]!r} already Retired",
            })

    out = pass_dir / "integration" / "classification_flags.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["flag", "link_id", "agency_abbreviation", "slug",
            "use_case_name", "detail"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(flags)
    print(f"  retired cross-check: {len(flags)} flag(s) → {out.name}")
    return len(flags)


def _print_final_summary(conn: sqlite3.Connection, applied: dict[str, int],
                         n_flags: int) -> None:
    print()
    print("Final lineage_status rollup:")
    counts = {
        r[0]: r[1]
        for r in conn.execute(
            "SELECT lineage_status, COUNT(*) FROM use_case_year_links "
            "GROUP BY lineage_status"
        )
    }
    for status in _FINAL_STATUSES:
        print(f"  {status:<16}: {counts.get(status, 0)}")
    other = {k: v for k, v in counts.items() if k not in _FINAL_STATUSES}
    for status, n in sorted(other.items()):
        print(f"  {status:<16}: {n}  (unresolved — no final classification)")
    print(f"  agent-resolved decisions : {sum(applied.values())}")
    print(f"  classification flags     : {n_flags}")


def run(conn: sqlite3.Connection, pass_dir: Path) -> dict[str, int]:
    """Apply the pass end-to-end. Returns the per-action decision counts."""
    print("== Year-match review apply ==")
    applied = apply_decisions(conn, pass_dir)
    print("== Orphan re-homing ==")
    rehome_orphans(conn)
    print("== Reconciliation ==")
    assert_reconciliation(conn)
    print("== Retired cross-check ==")
    n_flags = retired_cross_check(conn, pass_dir)
    _print_final_summary(conn, applied, n_flags)
    return applied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH, help="SQLite DB path.")
    parser.add_argument(
        "--pass-dir", type=Path, default=DEFAULT_PASS_DIR,
        help="Audit-pass directory (parent of integration/).",
    )
    # Accepted for parity with the linkage-pass scripts; this step always
    # writes (the matcher already rebuilt the baseline in `make fix`).
    parser.add_argument("--apply", action="store_true",
                        help="No-op flag kept for CLI parity; this step always writes.")
    args = parser.parse_args(argv)

    if not args.db.exists():
        raise FileNotFoundError(args.db)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        run(conn, args.pass_dir.resolve())
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
