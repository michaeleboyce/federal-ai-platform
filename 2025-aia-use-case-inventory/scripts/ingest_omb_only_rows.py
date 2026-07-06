"""Ingest adjudicated `omb_only` rows from OMB's consolidated file.

`omb_match_audit.match_status='omb_only'` marks use cases present in OMB's
authoritative consolidated file (mirrored into `omb_consolidated_rows`) but
missing from the per-agency source sweep that builds `use_cases` — the
inventory's one systematic completeness gap. Each such row was human/agent
adjudicated in audit/omb_only_ingest/decisions.csv with a verdict:

  ingest             — a genuine miss; insert into use_cases (this script)
  duplicate_of:<slug> — already present under a different name; mark audit
  withheld_variant   — a withheld/blank shell not worth a use_cases row
  documented_skip    — intentionally not ingested; reason in notes

Runs in `make fix` immediately after load_omb_consolidated.py (which wipes
and rebuilds the mirror + audit each time) and BEFORE
scripts/normalize_use_case_fields.py / build_lookups.py / auto_tag.py, so
ingested rows are normalized, slugged, and tagged exactly like loader rows.

Rows are resolved by `row_hash` (stable content hash) — NEVER by id, which
rotates every rebuild. Missing agencies (OMB includes small agencies that
never published a per-agency file) are created first, resolved by
abbreviation.

Idempotent: the loader wipe already removes prior ingested rows each
rebuild; the delete-by-provenance below additionally makes standalone
re-runs safe. Hard-fails if >2% of decisions no longer resolve by
row_hash (OMB republished the file → re-adjudicate).
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db import get_connection  # noqa: E402
from load_inventories import _lookup_agency_id, slugify  # noqa: E402

DECISIONS_CSV = ROOT / "audit" / "omb_only_ingest" / "decisions.csv"
PROVENANCE = "omb_consolidated_ingest"

# Agencies that appear in OMB's consolidated file but never published a
# per-agency inventory file. Created on demand; abbreviation is the stable
# key. federal_organizations seed entries are added separately in
# data/federal_hierarchy_seed.py (Slice A wires the legacy link).
NEW_AGENCIES = {
    "NIGC": ("National Indian Gaming Commission", "Independent Agency"),
    "NEA": ("National Endowment for the Arts", "Independent Agency"),
    "STB": ("Surface Transportation Board", "Independent Agency"),
    "OSHRC": (
        "Occupational Safety and Health Review Commission",
        "Independent Agency",
    ),
    "FCA": ("Farm Credit Administration", "Independent Agency"),
}

# omb_consolidated_rows column -> use_cases column (identical names omitted
# from comment; the three renames are the OMB-consolidation artifacts).
COLUMN_MAP = {
    "use_case_id_omb": "use_case_id",
    "use_case_name": "use_case_name",
    "bureau_component": "bureau_component",
    "email_address": "email_address",
    "is_withheld": "is_withheld",
    "stage_of_development": "stage_of_development",
    "is_high_impact": "is_high_impact",
    "hi_justification": "justification",
    "topic_area": "topic_area",
    "ai_classification": "ai_classification",
    "problem_statement": "problem_statement",
    "expected_benefits": "expected_benefits",
    "system_outputs": "system_outputs",
    "operational_date": "operational_date",
    "contracting_usage": "development_type",
    "vendor_name": "vendor_name",
    "have_ato": "has_ato",
    "system_name_ato": "system_name",
    "training_data_description": "training_data_description",
    "link_to_data": "link_to_data",
    "has_pii": "has_pii",
    "pia_url": "pia_url",
    "demographic_features": "demographic_features",
    "has_custom_code": "has_custom_code",
    "code_url": "code_url",
    "hi_testing_conducted": "hi_testing_conducted",
    "hi_assessment_completed": "hi_assessment_completed",
    "hi_potential_impacts": "hi_potential_impacts",
    "hi_independent_review": "hi_independent_review",
    "hi_ongoing_monitoring": "hi_ongoing_monitoring",
    "hi_training_established": "hi_training_established",
    "hi_failsafe_presence": "hi_failsafe_presence",
    "hi_appeal_process": "hi_appeal_process",
    "hi_public_consultation": "hi_public_consultation",
}

# Verdict -> omb_match_audit.match_status once handled. documented_skip rows
# intentionally KEEP status 'omb_only'; check_loader_integrity asserts the
# residual omb_only count equals the documented_skip count exactly.
VERDICT_STATUS = {
    "ingest": "ingested",
    "withheld_variant": "withheld_variant",
}


def load_decisions() -> list[dict]:
    if not DECISIONS_CSV.exists():
        return []
    with DECISIONS_CSV.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if (r.get("verdict") or "").strip()]


def main() -> int:
    decisions = load_decisions()
    if not decisions:
        print("[ingest_omb_only] no decisions.csv (or empty) — clean no-op")
        return 0

    conn = get_connection()
    today = date.today().isoformat()
    try:
        # Idempotency key: omb_consolidated_source. (id_provenance is
        # restamped to 'source' by backfill_use_case_id.py later in the
        # chain, so it can't identify ingested rows on re-runs.)
        conn.execute(
            "DELETE FROM use_cases WHERE omb_consolidated_source = 'omb_only_ingest'"
        )

        unresolved: list[str] = []
        ingested = 0
        marked = 0
        with conn:
            for d in decisions:
                row_hash = d["row_hash"].strip()
                verdict = d["verdict"].strip()
                omb = conn.execute(
                    "SELECT * FROM omb_consolidated_rows WHERE row_hash = ?",
                    (row_hash,),
                ).fetchone()
                if omb is None:
                    unresolved.append(f"{d.get('agency_abbreviation')}:{row_hash[:12]}")
                    continue

                abbr = (omb["agency_abbreviation"] or "").strip().upper()
                if verdict == "ingest":
                    agency_id = _lookup_agency_id(conn, abbr)
                    if agency_id is None and abbr in NEW_AGENCIES:
                        name, agency_type = NEW_AGENCIES[abbr]
                        conn.execute(
                            """INSERT INTO agencies
                               (name, abbreviation, agency_type, inventory_year,
                                status, notes)
                               VALUES (?, ?, ?, 2025, 'no_per_agency_file',
                                'Created by ingest_omb_only_rows.py: appears only in
                                 OMB consolidated file')""",
                            (name, abbr, agency_type),
                        )
                        agency_id = _lookup_agency_id(conn, abbr)
                    if agency_id is None:
                        unresolved.append(f"{abbr}:{row_hash[:12]} (no agency)")
                        continue

                    slug = slugify(abbr, omb["use_case_name"] or omb["use_case_id_omb"] or row_hash[:12])
                    if conn.execute(
                        "SELECT 1 FROM use_cases WHERE slug = ?", (slug,)
                    ).fetchone():
                        unresolved.append(f"{abbr}:{row_hash[:12]} (slug collision {slug})")
                        continue

                    cols = ["agency_id", "source_file", "slug", "id_provenance",
                            "omb_consolidated_id", "omb_consolidated_source",
                            "omb_consolidated_first_seen", "omb_consolidated_last_seen",
                            "raw_json"]
                    vals = [agency_id, omb["ingest_source_file"], slug, PROVENANCE,
                            omb["id"], "omb_only_ingest", today, today,
                            omb["raw_json"] or json.dumps(dict(zip(omb.keys(), tuple(omb))))]
                    for src, dst in COLUMN_MAP.items():
                        cols.append(dst)
                        vals.append(omb[src])
                    conn.execute(
                        f"INSERT INTO use_cases ({','.join(cols)}) "
                        f"VALUES ({','.join('?' * len(cols))})",
                        vals,
                    )
                    new_id = conn.execute(
                        "SELECT id FROM use_cases WHERE slug = ?", (slug,)
                    ).fetchone()[0]
                    conn.execute(
                        """UPDATE omb_match_audit
                           SET match_status='ingested', match_method='ingested',
                               use_case_id_db=?, resolved_at=?,
                               resolution_note=?
                         WHERE omb_row_id=? AND match_status='omb_only'""",
                        (new_id, today, d.get("notes") or "ingested from OMB consolidated file", omb["id"]),
                    )
                    ingested += 1

                elif verdict.startswith("duplicate_of:"):
                    target_slug = verdict.split(":", 1)[1].strip()
                    target = conn.execute(
                        "SELECT id FROM use_cases WHERE slug = ?", (target_slug,)
                    ).fetchone()
                    if target is None:
                        unresolved.append(f"{abbr}:{row_hash[:12]} (dup target {target_slug} missing)")
                        continue
                    conn.execute(
                        """UPDATE omb_match_audit
                           SET match_status='matched_manual', match_method='adjudicated_duplicate',
                               use_case_id_db=?, resolved_at=?, resolution_note=?
                         WHERE omb_row_id=? AND match_status='omb_only'""",
                        (target[0], today, d.get("notes") or f"duplicate of {target_slug}", omb["id"]),
                    )
                    marked += 1

                elif verdict in VERDICT_STATUS:
                    conn.execute(
                        """UPDATE omb_match_audit
                           SET match_status=?, resolved_at=?, resolution_note=?
                         WHERE omb_row_id=? AND match_status='omb_only'""",
                        (VERDICT_STATUS[verdict], today, d.get("notes") or verdict, omb["id"]),
                    )
                    marked += 1

                elif verdict == "documented_skip":
                    conn.execute(
                        """UPDATE omb_match_audit
                           SET resolution_note=?
                         WHERE omb_row_id=? AND match_status='omb_only'""",
                        (d.get("notes") or "documented skip", omb["id"]),
                    )
                    marked += 1
                else:
                    unresolved.append(f"{abbr}:{row_hash[:12]} (unknown verdict {verdict!r})")

        residual = conn.execute(
            "SELECT COUNT(*) FROM omb_match_audit WHERE match_status='omb_only'"
        ).fetchone()[0]
        print(
            f"[ingest_omb_only] decisions={len(decisions)} ingested={ingested} "
            f"marked={marked} unresolved={len(unresolved)} residual_omb_only={residual}"
        )
        if unresolved:
            for u in unresolved:
                print(f"  UNRESOLVED: {u}")
        if len(unresolved) / len(decisions) > 0.02:
            print(
                "FATAL: >2% of adjudication decisions failed to resolve by "
                "row_hash — OMB likely republished the file; re-adjudicate."
            )
            return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
