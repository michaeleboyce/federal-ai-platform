"""Apply the 3-agent product-gap-review recommendations.

Reads recommendations.json from audit/product_gap_review/{noisy,llms,other}/.

Per-decision behavior:
  link             -> INSERT OR IGNORE into use_case_products. Re-resolves
                      product_id by canonical_name and use_case_id by
                      (agency, evidence quote substring) when the recorded
                      ID has gone stale (DB re-keyed between runs).
  tighten_alias    -> Apply the noted alias change. Currently:
                      * Drop bare 'OpenAI' alias from product 'OpenAI API'
                        (was matching every Azure OpenAI deployment).
                      * Drop bare 'Microsoft 365' alias from 'Microsoft 365'
                        (was producing phantom M365 Copilot bundle gaps).
                      * The three NOISY tighten_alias recommendations
                        (NEC NeoFace, MS Teams, Custom In-House AI) are
                        deferred — they require populate_use_case_products
                        rework, not just alias edits.
  add_alias        -> none from any agent.
  false_positive   -> noop (just record).
  unclear          -> noop (flag in summary).

Idempotent.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
REVIEW_DIR = ROOT / "audit" / "product_gap_review"
RECOVERIES_PATH = REVIEW_DIR / "_use_case_name_recoveries.json"


def _load_recoveries() -> dict[int, tuple[str, str]]:
    """Return stale_uc_id → (agency_abbr, use_case_name) for tier-3 lookup.

    Backfills the use_case_name strings the gap-review recommendations were
    keyed against, recovered from older committed DB snapshots in the
    dashboard repo's git history (the recommendations.json files only stored
    use_case_id + agency, which goes stale every time make-fix re-keys the
    AUTOINCREMENT ids).
    """
    if not RECOVERIES_PATH.exists():
        return {}
    try:
        data = json.loads(RECOVERIES_PATH.read_text())
    except json.JSONDecodeError:
        return {}
    out: dict[int, tuple[str, str]] = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        sid = row.get("stale_uc_id")
        agency = row.get("agency_abbr")
        name = row.get("use_case_name")
        if isinstance(sid, int) and isinstance(agency, str) and isinstance(name, str):
            out[sid] = (agency, name)
    return out

# Tighten-alias actions we WILL apply (skipping the noisy slice's structural
# rework recommendations — those are larger refactors).
ALIAS_DROPS = [
    {"product_canonical": "OpenAI API", "drop_alias": "OpenAI"},
    {"product_canonical": "Microsoft 365", "drop_alias": "Microsoft 365"},
]


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def resolve_product_id(conn, canonical_name: str, fallback_id: int | None) -> int | None:
    """Look up product by canonical name; fall back to the recorded id if it
    still resolves to the same product."""
    row = conn.execute(
        "SELECT id, canonical_name FROM products WHERE canonical_name = ?",
        (canonical_name,),
    ).fetchone()
    if row:
        return row["id"]
    if fallback_id:
        row = conn.execute(
            "SELECT id, canonical_name FROM products WHERE id = ?",
            (fallback_id,),
        ).fetchone()
        if row and row["canonical_name"] == canonical_name:
            return row["id"]
    return None


def resolve_use_case_id(
    conn,
    recorded_id: int,
    agency_abbr: str,
    evidence: str,
    recoveries: dict[int, tuple[str, str]] | None = None,
) -> int | None:
    """Try recorded id, then evidence substring, then a curated name recovery.

    Tier 1: direct id match (recorded_id + agency_abbr).
    Tier 2: agency_abbr + evidence-quote substring across the narrative
            columns. Returns the match only if exactly one row is found.
    Tier 3: if `recoveries` carries the original use_case_name for this
            stale id, look up by exact (agency_abbr, use_case_name).
            (agency, name) is verified unique across all 3,549 use cases.
    """
    row = conn.execute(
        "SELECT u.id FROM use_cases u JOIN agencies a ON a.id = u.agency_id "
        "WHERE u.id = ? AND a.abbreviation = ?",
        (recorded_id, agency_abbr),
    ).fetchone()
    if row:
        return row["id"]
    # Tier 2: evidence-quote substring against narrative columns.
    needle = evidence[:60].strip()
    if needle:
        rows = conn.execute(
            """
            SELECT u.id FROM use_cases u JOIN agencies a ON a.id = u.agency_id
             WHERE a.abbreviation = ?
               AND (
                    LOWER(COALESCE(u.problem_statement,'')) LIKE ?
                 OR LOWER(COALESCE(u.expected_benefits,'')) LIKE ?
                 OR LOWER(COALESCE(u.system_outputs,'')) LIKE ?
                 OR LOWER(COALESCE(u.use_case_name,'')) LIKE ?
                 OR LOWER(COALESCE(u.system_name,'')) LIKE ?
               )
             LIMIT 5
            """,
            (
                agency_abbr,
                f"%{needle.lower()}%",
                f"%{needle.lower()}%",
                f"%{needle.lower()}%",
                f"%{needle.lower()}%",
                f"%{needle.lower()}%",
            ),
        ).fetchall()
        if len(rows) == 1:
            return rows[0]["id"]
    # Tier 3: curated recovery map.
    if recoveries and recorded_id in recoveries:
        rec_agency, rec_name = recoveries[recorded_id]
        if rec_agency == agency_abbr:
            row = conn.execute(
                "SELECT u.id FROM use_cases u JOIN agencies a ON a.id = u.agency_id "
                "WHERE a.abbreviation = ? AND u.use_case_name = ?",
                (rec_agency, rec_name),
            ).fetchone()
            if row:
                return row["id"]
    return None  # ambiguous or no match


def apply_links(conn) -> dict:
    stats = {"linked": 0, "skipped_no_product": 0, "skipped_no_uc": 0, "already_linked": 0}
    skipped_uc: list[dict] = []
    recoveries = _load_recoveries()
    for slice_dir in REVIEW_DIR.iterdir():
        if not slice_dir.is_dir():
            continue
        rec_path = slice_dir / "recommendations.json"
        if not rec_path.exists():
            continue
        with open(rec_path) as f:
            recs = json.load(f)
        for r in recs:
            if r["decision"] != "link":
                continue
            pid = resolve_product_id(conn, r["canonical_name"], r.get("product_id"))
            if pid is None:
                stats["skipped_no_product"] += 1
                continue
            uid = resolve_use_case_id(
                conn,
                int(r.get("use_case_id") or 0),
                r.get("use_case_agency", ""),
                r.get("evidence_quote", ""),
                recoveries=recoveries,
            )
            if uid is None:
                stats["skipped_no_uc"] += 1
                skipped_uc.append({
                    "slice": slice_dir.name,
                    "product": r["canonical_name"],
                    "agency": r.get("use_case_agency"),
                    "stale_uc_id": r.get("use_case_id"),
                    "evidence_quote": (r.get("evidence_quote") or "")[:80],
                })
                continue
            existed = conn.execute(
                "SELECT 1 FROM use_case_products WHERE use_case_id = ? AND product_id = ?",
                (uid, pid),
            ).fetchone()
            if existed:
                stats["already_linked"] += 1
                continue
            conn.execute(
                """
                INSERT INTO use_case_products
                    (use_case_id, product_id, evidence_text, confidence)
                VALUES (?, ?, ?, 'inferred')
                """,
                (uid, pid, (r.get("evidence_quote") or "")[:500]),
            )
            stats["linked"] += 1
    # Always overwrite the skip CSV so it reflects the current run — when
    # everything resolves, the file is truncated to header-only rather than
    # left with stale rows from a previous run.
    out = REVIEW_DIR / "_skipped_unresolvable_links.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["slice", "product", "agency", "stale_uc_id", "evidence_quote"],
        )
        w.writeheader()
        w.writerows(skipped_uc)
    print(f"  wrote {out.relative_to(ROOT)} ({len(skipped_uc)} unresolvable)")
    return stats


def apply_tighten(conn) -> dict:
    stats = {"aliases_dropped": 0, "aliases_not_found": 0}
    for action in ALIAS_DROPS:
        pid = resolve_product_id(conn, action["product_canonical"], None)
        if pid is None:
            stats["aliases_not_found"] += 1
            continue
        n = conn.execute(
            "DELETE FROM product_aliases WHERE product_id = ? AND alias_text = ?",
            (pid, action["drop_alias"]),
        ).rowcount
        if n > 0:
            stats["aliases_dropped"] += n
        else:
            stats["aliases_not_found"] += 1
    return stats


def main() -> int:
    conn = _open()
    try:
        with conn:
            link_stats = apply_links(conn)
            tighten_stats = apply_tighten(conn)
        print(f"[links]      {link_stats}")
        print(f"[tighten]    {tighten_stats}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
