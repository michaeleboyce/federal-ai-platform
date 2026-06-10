#!/usr/bin/env python3
"""Apply the 2026-06 enterprise-scope corrections to the canonical DB.

Inputs: the reviewed decision CSVs under
    audit/retag/enterprise-scope-2026-06/
        decisions_slice1.csv            (2025 rows, DHS/DOE/DOI/DOJ)
        decisions_slice2.csv            (2025 rows, DOL..VA)
        decisions_sweep.csv             (2025 rows missed by the OCIO filter)
        decisions_2025_claims.csv       (2025 rows tagged enterprise — inverse check)
        decisions_2024_department.csv   (2024 rows tagged deployment_scope='department')

Background: the 2025 tagger recorded the OWNING office (OCIO/MGMT) as the
deployment scope for many agency-wide tools (SSA ASC, StateChat, DHS-Chat,
OPM ChatGPT...), and the 2024 tagger used a 'department' scope value that was
never mapped into is_enterprise_wide. Both defects distorted the
"agencies with enterprise-wide GenAI" comparison (reported 15 -> 12; actually
roughly flat at ~21 -> ~21). Every row below was individually reviewed
(per-row reasoning in the CSVs; web evidence where available).

Write rules:
  * 2025 rows: resolve use_cases by (agency abbreviation, use_case_name,
    bureau_component), falling back to (abbreviation, name) when unique.
    Update use_case_tags.deployment_scope and .is_enterprise_wide.
  * 2024 rows: resolve use_cases_2024 by (agency_abbreviation, use_case_name).
    Update ALL wave rows in use_case_tags_2024 whose deployment_scope is
    'department' for that use case, setting is_enterprise_wide per decision.
    deployment_scope is left as 'department' for upgrades (original 2024
    vocabulary preserved; the analysis layer keys off is_enterprise_wide),
    except explicit downgrades (GSA SOC row -> 'office').
  * Ids are NEVER taken from the CSVs (ref_id_unstable is ignored);
    signatures are re-resolved against the live DB at write time.
  * Idempotent: rows already matching the proposed state are skipped.
  * Ambiguous signatures (0 or >1 matches) are reported and NOT written.

Run:  python scripts/apply_enterprise_scope_corrections_2026_06.py [--dry-run]
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "federal_ai_inventory_2025.db"
DEC_DIR = ROOT / "audit" / "retag" / "enterprise-scope-2026-06"

CSV_2025 = [
    "decisions_slice1.csv",
    "decisions_slice2.csv",
    "decisions_sweep.csv",
    "decisions_2025_claims.csv",
]
CSV_2024 = "decisions_2024_department.csv"

VALID_SCOPES = {"enterprise_wide", "bureau", "office", "unknown", "department"}


def load_rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def apply_2025(conn: sqlite3.Connection, dry: bool) -> tuple[int, int, list[str]]:
    applied, skipped, problems = 0, 0, []
    for fname in CSV_2025:
        for row in load_rows(DEC_DIR / fname):
            agency = row["agency"].strip()
            name = row["use_case_name"].strip()
            bureau = (row.get("bureau_component") or "").strip()
            scope = row["proposed_scope"].strip()
            ew = int(row["proposed_is_enterprise_wide"])
            if scope not in VALID_SCOPES:
                problems.append(f"{fname}: bad scope {scope!r} for {agency}|{name}")
                continue
            # Resolve by full signature, then fall back to (agency, name).
            ids = [
                r[0]
                for r in conn.execute(
                    """SELECT u.id FROM use_cases u
                       JOIN agencies a ON a.id = u.agency_id
                       WHERE a.abbreviation = ? AND u.use_case_name = ?
                         AND coalesce(u.bureau_component,'') = ?""",
                    (agency, name, bureau),
                )
            ]
            if not ids:
                ids = [
                    r[0]
                    for r in conn.execute(
                        """SELECT u.id FROM use_cases u
                           JOIN agencies a ON a.id = u.agency_id
                           WHERE a.abbreviation = ? AND u.use_case_name = ?""",
                        (agency, name),
                    )
                ]
            if not ids:
                # Tolerate non-breaking-space vs space drift between the
                # filed name and the reviewed CSV (e.g. NSF's RPPR row).
                ids = [
                    r[0]
                    for r in conn.execute(
                        """SELECT u.id FROM use_cases u
                           JOIN agencies a ON a.id = u.agency_id
                           WHERE a.abbreviation = ?
                             AND replace(u.use_case_name, char(160), ' ') = ?""",
                        (agency, name),
                    )
                ]
            if len(ids) != 1:
                problems.append(
                    f"{fname}: {agency}|{name}|{bureau} resolved to {len(ids)} rows"
                )
                continue
            (uc_id,) = ids
            cur = conn.execute(
                "SELECT deployment_scope, is_enterprise_wide FROM use_case_tags WHERE use_case_id = ?",
                (uc_id,),
            ).fetchone()
            if cur is None:
                problems.append(f"{fname}: {agency}|{name} has no use_case_tags row")
                continue
            if cur[0] == scope and (cur[1] or 0) == ew:
                skipped += 1
                continue
            if not dry:
                conn.execute(
                    "UPDATE use_case_tags SET deployment_scope = ?, is_enterprise_wide = ? WHERE use_case_id = ?",
                    (scope, ew, uc_id),
                )
            applied += 1
    return applied, skipped, problems


def apply_2024(conn: sqlite3.Connection, dry: bool) -> tuple[int, int, list[str]]:
    applied, skipped, problems = 0, 0, []
    for row in load_rows(DEC_DIR / CSV_2024):
        agency = row["agency"].strip()
        name = row["use_case_name"].strip()
        scope = row["proposed_scope"].strip()
        ew = int(row["proposed_is_enterprise_wide"])
        bureau = (row.get("bureau") or "").strip()
        ids = [
            r[0]
            for r in conn.execute(
                """SELECT id FROM use_cases_2024
                   WHERE agency_abbreviation = ? AND use_case_name = ?
                     AND coalesce(bureau,'') = ?""",
                (agency, name, bureau),
            )
        ]
        if not ids:
            ids = [
                r[0]
                for r in conn.execute(
                    "SELECT id FROM use_cases_2024 WHERE agency_abbreviation = ? AND use_case_name = ?",
                    (agency, name),
                )
            ]
        if len(ids) != 1:
            problems.append(f"2024: {agency}|{name} resolved to {len(ids)} rows")
            continue
        (uc_id,) = ids
        # Preserve original 2024 vocabulary on upgrades; rewrite on downgrades.
        new_scope = "department" if scope == "enterprise_wide" else scope
        n = conn.execute(
            """SELECT count(*) FROM use_case_tags_2024
               WHERE use_case_id_2024 = ? AND deployment_scope = 'department'
                 AND (coalesce(is_enterprise_wide,0) != ? OR deployment_scope != ?)""",
            (uc_id, ew, new_scope),
        ).fetchone()[0]
        if n == 0:
            skipped += 1
            continue
        if not dry:
            conn.execute(
                """UPDATE use_case_tags_2024
                   SET is_enterprise_wide = ?, deployment_scope = ?
                   WHERE use_case_id_2024 = ? AND deployment_scope = 'department'""",
                (ew, new_scope, uc_id),
            )
        applied += n
    return applied, skipped, problems


def headline(conn: sqlite3.Connection) -> None:
    q24 = conn.execute(
        """SELECT count(DISTINCT u.agency_abbreviation)
           FROM use_cases_2024 u
           JOIN use_case_tags_2024_canonical t ON t.use_case_id_2024 = u.id
           WHERE t.is_generative_ai = 1 AND t.is_enterprise_wide = 1"""
    ).fetchone()[0]
    q25 = conn.execute(
        """SELECT count(DISTINCT a.abbreviation)
           FROM use_cases u
           JOIN use_case_tags t ON t.use_case_id = u.id
           JOIN agencies a ON a.id = u.agency_id
           WHERE t.is_generative_ai = 1 AND t.is_enterprise_wide = 1"""
    ).fetchone()[0]
    n24 = conn.execute(
        """SELECT count(*) FROM use_case_tags_2024_canonical
           WHERE is_generative_ai = 1 AND is_enterprise_wide = 1"""
    ).fetchone()[0]
    n25 = conn.execute(
        """SELECT count(*) FROM use_case_tags
           WHERE is_generative_ai = 1 AND is_enterprise_wide = 1 AND use_case_id IS NOT NULL"""
    ).fetchone()[0]
    print(f"  agencies w/ enterprise GenAI: 2024={q24}  2025={q25}")
    print(f"  enterprise GenAI use cases:   2024={n24}  2025={n25}")


def main() -> int:
    dry = "--dry-run" in sys.argv
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    print(f"{'DRY RUN — ' if dry else ''}applying enterprise-scope corrections to {DB.name}")
    print("before:")
    headline(conn)
    with conn:
        a25, s25, p25 = apply_2025(conn, dry)
        a24, s24, p24 = apply_2024(conn, dry)
    print(f"2025 tags: {a25} updated, {s25} already correct")
    print(f"2024 tag rows: {a24} updated, {s24} already correct")
    problems = p25 + p24
    if problems:
        print(f"\nUNRESOLVED ({len(problems)}) — NOT written:")
        for p in problems:
            print(f"  ! {p}")
    print("after:")
    headline(conn)
    conn.close()
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
