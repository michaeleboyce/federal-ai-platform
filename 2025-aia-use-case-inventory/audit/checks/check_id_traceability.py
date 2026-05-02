"""use_case_id traceability and provenance regression checks.

Source: Phase 1 Agent A — Ingest Surgeon.
Baseline (pre-remediation): 2,567 NULL use_case_ids out of 3,616 rows;
~2,007 recoverable from raw_json after the column_maps.py header normalization
fix.

After remediation:
  * id_provenance is one of {'source', 'backfilled_from_raw_json',
    'source_missing'} on every row.
  * No row may have NULL use_case_id AND NULL id_provenance — that combination
    means the backfill script never touched the row.
  * The vast majority of recoverable IDs are stamped either 'source' or
    'backfilled_from_raw_json'. Newer loaders can capture IDs directly, so the
    exact mix is allowed to change.
  * Every populated use_case_id is unique within its agency.
"""


def _scalar(conn, sql):
    return conn.execute(sql).fetchone()[0]


def test_use_case_id_coverage(conn):
    """At least 95% of the original recoverable IDs are populated and stamped."""
    baseline = 2007  # recoverable from raw_json per pre-remediation audit
    populated = _scalar(
        conn,
        "SELECT COUNT(*) FROM use_cases "
        "WHERE use_case_id IS NOT NULL AND use_case_id != '' "
        "AND id_provenance IN ('source', 'backfilled_from_raw_json')",
    )
    assert populated >= int(baseline * 0.95), (
        f"Expected >= 95% of {baseline} recoverable IDs populated, got {populated}"
    )


def test_no_unaccounted_nulls(conn):
    """Every NULL-use_case_id row must carry an id_provenance stamp."""
    unaccounted = _scalar(
        conn,
        "SELECT COUNT(*) FROM use_cases "
        "WHERE use_case_id IS NULL AND id_provenance IS NULL",
    )
    assert unaccounted == 0, (
        f"{unaccounted} rows have NULL use_case_id with no id_provenance"
    )


def test_provenance_values_are_in_enum(conn):
    """id_provenance must only contain the three allowed values (or NULL for
    rows that have a populated use_case_id and somehow weren't restamped — we
    assert that case is empty too)."""
    bad = _scalar(
        conn,
        "SELECT COUNT(*) FROM use_cases "
        "WHERE id_provenance IS NOT NULL "
        "AND id_provenance NOT IN ('source', 'backfilled_from_raw_json', 'source_missing')",
    )
    assert bad == 0, f"{bad} rows have an unrecognized id_provenance value"


def test_source_provenance_matches_populated_ids(conn):
    """Every populated use_case_id should be stamped 'source' or
    'backfilled_from_raw_json' — never NULL or 'source_missing'."""
    bad = _scalar(
        conn,
        "SELECT COUNT(*) FROM use_cases "
        "WHERE use_case_id IS NOT NULL AND use_case_id != '' "
        "AND (id_provenance IS NULL OR id_provenance = 'source_missing')",
    )
    assert bad == 0, (
        f"{bad} populated use_case_id rows have wrong/missing id_provenance"
    )


def test_use_case_id_unique_within_agency(conn):
    """Within a single agency, use_case_id should be unique. Cross-agency
    collisions are fine (Treasury and GPO both use plain integers)."""
    dups = conn.execute(
        "SELECT agency_id, use_case_id, COUNT(*) AS n "
        "FROM use_cases "
        "WHERE use_case_id IS NOT NULL AND use_case_id != '' "
        "GROUP BY agency_id, use_case_id HAVING n > 1"
    ).fetchall()
    assert not dups, (
        f"{len(dups)} (agency_id, use_case_id) collisions: "
        f"{[(d[0], d[1], d[2]) for d in dups[:5]]}"
    )
