"""agency_id FK integrity on the abbreviation-keyed tables (m024).

The five tables below used to carry only a free-text agency abbreviation;
scripts/backfill_agency_fks.py now resolves agency_id on every rebuild.
These gates ensure (a) every abbreviation outside the documented exception
set resolves, and (b) resolved ids actually point at agencies rows.
"""

TARGETS = (
    ("column_mappings", "agency_abbreviation", {"COTS", "MULTI"}),
    ("omb_consolidated_rows", "agency_abbreviation", set()),
    ("agency_ai_access_evidence", "agency_abbreviation", set()),
    ("agency_ai_policy_documents", "agency_abbr", {"EOP", "OMB"}),
    ("agency_ai_policy_compliance", "agency_abbr", {"EOP", "OMB"}),
    # Pre-dates m024 (agency_id added by m011-era loader) but carries the
    # same abbreviation+id pair — hold it to the same integrity bar.
    ("use_case_year_links", "agency_abbreviation", set()),
)


def test_all_abbreviations_resolved(conn):
    problems = []
    for table, col, exceptions in TARGETS:
        rows = conn.execute(
            f"SELECT DISTINCT {col} FROM {table} "
            f"WHERE {col} IS NOT NULL AND agency_id IS NULL"
        ).fetchall()
        unexpected = [r[0] for r in rows if r[0] not in exceptions]
        if unexpected:
            problems.append(f"{table}: {unexpected}")
    assert not problems, (
        f"unresolved agency abbreviations outside exceptions: {problems}"
    )


def test_resolved_ids_point_at_agencies(conn):
    problems = []
    for table, _col, _exceptions in TARGETS:
        n = conn.execute(
            f"SELECT COUNT(*) FROM {table} t WHERE t.agency_id IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM agencies a WHERE a.id = t.agency_id)"
        ).fetchone()[0]
        if n:
            problems.append(f"{table}: {n} dangling")
    assert not problems, f"dangling agency_id values: {problems}"


def test_abbreviation_id_agreement(conn):
    """Where both abbreviation and id are set, they agree (case-insensitive,
    modulo the TREAS alias)."""
    n = conn.execute(
        """SELECT COUNT(*) FROM omb_consolidated_rows o
            JOIN agencies a ON a.id = o.agency_id
           WHERE UPPER(o.agency_abbreviation) != UPPER(a.abbreviation)
             AND NOT (o.agency_abbreviation = 'TREAS'
                      AND a.abbreviation = 'Treasury')"""
    ).fetchone()[0]
    assert n == 0, f"{n} omb_consolidated_rows abbreviation/id disagreements"
