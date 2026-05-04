"""Generate offline-readable markdown report of OMB-vs-IFP discrepancies.

Reads `omb_match_audit` and writes `audit/omb_consolidated_diff_2025.md`.
Complements the live `/discrepancies` dashboard page — useful for review
in PRs, linking from issues, and checked-in snapshots.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT_PATH = ROOT / "audit" / "omb_consolidated_diff_2025.md"


def main() -> int:
    if not DB_PATH.exists():
        print(f"DB not found at {DB_PATH}", file=sys.stderr)
        return 1
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rollup = {
        r["match_status"]: r["n"]
        for r in conn.execute(
            "SELECT match_status, COUNT(*) AS n FROM omb_match_audit "
            "GROUP BY match_status"
        )
    }

    omb_only = conn.execute(
        """
        SELECT a.agency_abbreviation, o.use_case_id_omb, o.use_case_name,
               o.bureau_component
        FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id = a.omb_row_id
        WHERE a.match_status = 'omb_only'
        ORDER BY a.agency_abbreviation, o.use_case_name
        """
    ).fetchall()

    db_only = conn.execute(
        """
        SELECT a.agency_abbreviation, uc.use_case_id, uc.use_case_name,
               uc.bureau_component
        FROM omb_match_audit a
        JOIN use_cases uc ON uc.id = a.use_case_id_db
        WHERE a.match_status = 'db_only'
        ORDER BY a.agency_abbreviation, uc.use_case_name
        """
    ).fetchall()

    drifts = conn.execute(
        """
        SELECT a.agency_abbreviation, uc.use_case_name, a.drift_fields_json
        FROM omb_match_audit a
        JOIN use_cases uc ON uc.id = a.use_case_id_db
        WHERE a.match_status IN ('matched_exact', 'matched_fuzzy')
          AND a.drift_fields_json IS NOT NULL AND a.drift_fields_json != '{}'
        ORDER BY a.agency_abbreviation, uc.use_case_name
        """
    ).fetchall()

    suggested = conn.execute(
        """
        SELECT a.agency_abbreviation, o.use_case_name AS omb_name,
               uc.use_case_name AS db_name, a.match_score
        FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id = a.omb_row_id
        JOIN use_cases uc ON uc.id = a.use_case_id_db
        WHERE a.match_status = 'suggested_rename'
        ORDER BY a.match_score DESC
        """
    ).fetchall()

    duplicates = conn.execute(
        """
        SELECT a.agency_abbreviation, a.use_case_name, COUNT(*) AS n
        FROM omb_match_audit a
        WHERE a.match_status = 'duplicate_in_omb'
        GROUP BY a.agency_abbreviation, a.use_case_name
        ORDER BY n DESC
        """
    ).fetchall()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out: list[str] = []
    out.append("# OMB Consolidated 2025 ↔ IFP DB Discrepancy Report\n")
    out.append(f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M %Z').strip()}_\n")
    out.append(
        "Source file: "
        "`data/raw/2025_individually_reported_AI_use_cases.xlsx`\n"
    )

    out.append("\n## Headline counts\n")
    out.append("| Status | Count |\n|---|---:|")
    for k in [
        "matched_exact", "matched_fuzzy", "suggested_rename",
        "omb_only", "db_only", "duplicate_in_omb",
    ]:
        out.append(f"| {k} | {rollup.get(k, 0)} |")

    out.append(f"\n## OMB-only — {len(omb_only)} use cases new in OMB file\n")
    out.append(
        "These use cases appear in the OMB consolidated file but NOT in our "
        "DB. Net-new agencies (EAC, FCA, FCC, NEA, NIGC, OSC, OSHRC, PBGC, "
        "STB) are entirely listed here.\n"
    )
    out.append("| Agency | OMB ID | Bureau | Name |\n|---|---|---|---|")
    for r in omb_only:
        nm = (r["use_case_name"] or "")[:80]
        bu = (r["bureau_component"] or "")[:40]
        oid = r["use_case_id_omb"] or ""
        out.append(f"| {r['agency_abbreviation']} | {oid} | {bu} | {nm} |")

    out.append(f"\n## DB-only — {len(db_only)} use cases missing from OMB file\n")
    out.append(
        "These use cases are in our DB but NOT in the OMB consolidated file. "
        "Includes the 4 dropped agencies (FRTIB, GPO, NMB, OPM) plus "
        "agency-specific rows that OMB excluded from consolidation.\n"
    )
    out.append("| Agency | DB ID | Bureau | Name |\n|---|---|---|---|")
    for r in db_only:
        nm = (r["use_case_name"] or "")[:80]
        bu = (r["bureau_component"] or "")[:40]
        out.append(f"| {r['agency_abbreviation']} | {r['use_case_id'] or ''} | {bu} | {nm} |")

    out.append(f"\n## Suggested renames — {len(suggested)} (score 0.40–0.85)\n")
    out.append(
        "OMB row name fuzzy-matches a DB row name within the same agency, "
        "but below the auto-link threshold. Most are OMB expanding acronyms "
        "(e.g., NSF) or rephrasing. Human review recommended; no auto-link "
        "performed.\n"
    )
    out.append("| Agency | Score | OMB name | DB name |\n|---|---:|---|---|")
    for r in suggested:
        out.append(
            f"| {r['agency_abbreviation']} | {r['match_score']:.2f} | "
            f"{(r['omb_name'] or '')[:60]} | {(r['db_name'] or '')[:60]} |"
        )

    out.append(f"\n## Duplicates in OMB file — {len(duplicates)} groups\n")
    out.append(
        "Same `(agency, bureau, name)` triple appearing twice or more in "
        "the OMB consolidated file. The first occurrence is matched against "
        "the DB; subsequent occurrences are flagged here.\n"
    )
    out.append("| Agency | Name | Extra occurrences |\n|---|---|---:|")
    for r in duplicates:
        nm = (r["use_case_name"] or "")[:80]
        out.append(f"| {r['agency_abbreviation']} | {nm} | {r['n']} |")

    drift_field_counts: dict[str, int] = {}
    drift_total = 0
    for r in drifts:
        drift_total += 1
        for f in json.loads(r["drift_fields_json"]):
            drift_field_counts[f] = drift_field_counts.get(f, 0) + 1
    out.append(f"\n## Field drift on matched pairs — {drift_total} pairs affected\n")
    out.append(
        "Pairs where OMB's value differs from our DB's value on at least "
        "one of the 11 canonical fields after normalization (letter prefix, "
        "case, curly quotes).\n"
    )
    out.append("### Drift count by field\n")
    out.append("| Field | Pairs |\n|---|---:|")
    for f in sorted(drift_field_counts, key=lambda k: -drift_field_counts[k]):
        out.append(f"| {f} | {drift_field_counts[f]} |")

    def _pair_cell(d: dict, field: str) -> tuple[str, str]:
        sub = d.get(field) or {}
        return (
            (sub.get("db") or "")[:30].replace("\n", " "),
            (sub.get("omb") or "")[:30].replace("\n", " "),
        )

    out.append("\n### High-impact reclassifications\n")
    out.append("| Agency | Use case | DB | OMB |\n|---|---|---|---|")
    for r in drifts:
        d = json.loads(r["drift_fields_json"])
        if "is_high_impact" in d:
            db_v, omb_v = _pair_cell(d, "is_high_impact")
            out.append(
                f"| {r['agency_abbreviation']} | "
                f"{(r['use_case_name'] or '')[:60]} | {db_v} | {omb_v} |"
            )

    out.append("\n### Stage drift\n")
    out.append("| Agency | Use case | DB | OMB |\n|---|---|---|---|")
    for r in drifts:
        d = json.loads(r["drift_fields_json"])
        if "stage_of_development" in d:
            db_v, omb_v = _pair_cell(d, "stage_of_development")
            out.append(
                f"| {r['agency_abbreviation']} | "
                f"{(r['use_case_name'] or '')[:60]} | {db_v} | {omb_v} |"
            )

    OUT_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(out)} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
