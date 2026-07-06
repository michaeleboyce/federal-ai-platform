"""Loader-integrity gates.

These checks make the failure modes of load_inventories.py loud. The
loader itself now exits non-zero on per-file exceptions and unresolved
COTS agency names (hardened 2026-07); these DB-side checks catch anything
that slips through a partial rebuild or a hand-edit, and gate the OMB
completeness gap so it can only shrink.

Bounds marked PHASE0 were set from the 2026-07 Phase-0 baseline of the
data-quality overhaul; the omb_only bound tightens to the documented-skip
count exactly once the Phase-2 ingest lands.
"""


def test_every_use_case_has_resolvable_agency(conn):
    """agency_id is NOT NULL and resolves to agencies.id on every row."""
    n = conn.execute(
        """SELECT COUNT(*) FROM use_cases u
            WHERE u.agency_id IS NULL
               OR NOT EXISTS (SELECT 1 FROM agencies a WHERE a.id = u.agency_id)"""
    ).fetchone()[0]
    assert n == 0, f"{n} use_cases rows with NULL/dangling agency_id"


def test_every_consolidated_has_resolvable_agency(conn):
    n = conn.execute(
        """SELECT COUNT(*) FROM consolidated_use_cases c
            WHERE c.agency_id IS NULL
               OR NOT EXISTS (SELECT 1 FROM agencies a WHERE a.id = c.agency_id)"""
    ).fetchone()[0]
    assert n == 0, f"{n} consolidated rows with NULL/dangling agency_id"


def test_no_nameless_idless_rows(conn):
    """The loader drops rows with neither a name nor a use_case_id; none
    should survive into the DB."""
    n = conn.execute(
        """SELECT COUNT(*) FROM use_cases
            WHERE TRIM(COALESCE(use_case_name, '')) = ''
              AND TRIM(COALESCE(use_case_id, '')) = ''"""
    ).fetchone()[0]
    assert n == 0, f"{n} use_cases rows with blank name AND blank use_case_id"


def test_omb_only_gap_bounded(conn):
    """Rows in OMB's authoritative consolidated file that our per-agency
    sweep lacks. PHASE0 baseline: 68. This bound may only be lowered:
    the Phase-2 ingest sets it to the count of documented_skip verdicts in
    audit/omb_only_ingest/decisions.csv."""
    n = conn.execute(
        "SELECT COUNT(*) FROM omb_match_audit WHERE match_status = 'omb_only'"
    ).fetchone()[0]
    assert n <= 68, (
        f"omb_only = {n} (bound 68) — OMB's inventory now has MORE rows we "
        "lack than at baseline; the source sweep regressed or OMB published "
        "an update that needs a new adjudication round"
    )
