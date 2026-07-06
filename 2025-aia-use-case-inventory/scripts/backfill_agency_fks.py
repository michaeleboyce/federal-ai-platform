"""Resolve agency_id on every abbreviation-keyed table (m024 columns).

Runs in `make fix` after all the loads that wipe/rewrite these tables.
Resolution is case-insensitive with an explicit alias map for source
spelling variants. Unresolvable abbreviations outside the documented
exception set fail the build — silent drift is the bug class this
whole pass exists to kill (see audit/checks/check_agency_fk_integrity).

Idempotent: recomputes agency_id wholesale each run.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db import get_connection  # noqa: E402

# (table, abbreviation column)
TARGETS = (
    ("column_mappings", "agency_abbreviation"),
    ("omb_consolidated_rows", "agency_abbreviation"),
    ("agency_ai_access_evidence", "agency_abbreviation"),
    ("agency_ai_policy_documents", "agency_abbr"),
    ("agency_ai_policy_compliance", "agency_abbr"),
)

# Source spelling -> agencies.abbreviation
ALIASES = {
    "TREAS": "Treasury",
}

# Abbreviations that legitimately resolve to no agency. Anything else
# unresolved is a build failure.
DOCUMENTED_EXCEPTIONS = {
    "column_mappings": {"COTS", "MULTI"},   # loader artifacts, not agencies
    "agency_ai_policy_documents": {"EOP", "OMB"},   # policy tracker covers
    "agency_ai_policy_compliance": {"EOP", "OMB"},  # non-inventory entities
}


def main() -> int:
    conn = get_connection()
    try:
        abbr_to_id = {
            r["abbreviation"].upper(): r["id"]
            for r in conn.execute("SELECT id, abbreviation FROM agencies")
        }
        for alias, canonical in ALIASES.items():
            target = abbr_to_id.get(canonical.upper())
            if target is not None:
                abbr_to_id[alias.upper()] = target

        failures = []
        with conn:
            for table, col in TARGETS:
                distinct = [
                    r[0]
                    for r in conn.execute(
                        f"SELECT DISTINCT {col} FROM {table} "
                        f"WHERE {col} IS NOT NULL"
                    )
                ]
                resolved = 0
                for abbr in distinct:
                    agency_id = abbr_to_id.get(abbr.strip().upper())
                    if agency_id is None:
                        if abbr not in DOCUMENTED_EXCEPTIONS.get(table, set()):
                            failures.append(f"{table}.{col} = {abbr!r}")
                        conn.execute(
                            f"UPDATE {table} SET agency_id = NULL "
                            f"WHERE {col} = ?",
                            (abbr,),
                        )
                        continue
                    conn.execute(
                        f"UPDATE {table} SET agency_id = ? WHERE {col} = ?",
                        (agency_id, abbr),
                    )
                    resolved += 1
                print(
                    f"[agency-fks] {table}: {resolved}/{len(distinct)} "
                    "distinct abbreviations resolved"
                )
        if failures:
            print(
                "FATAL: unresolvable agency abbreviations outside the "
                f"documented exception set: {failures} — add an ALIASES "
                "entry (spelling variant) or a DOCUMENTED_EXCEPTIONS entry "
                "(genuinely extra-inventory entity)"
            )
            return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
