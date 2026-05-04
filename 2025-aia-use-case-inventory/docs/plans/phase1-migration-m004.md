# Phase 1 — Migration `m004_omb_consolidated_provenance`

## Context

Phase 0 captured the test baseline (83/90 passing, 7 unrelated audit failures) and confirmed the dashboard surface area. Phase 1 adds the schema scaffolding the rest of the OMB-consolidated ingest will sit on:

1. **Four new columns on `use_cases`** that record OMB's parallel ID space and ingest timestamps. These let a use case carry both its agency-as-filed ID (the existing `use_case_id`, IFP-canonical) and its OMB-assigned ID (`omb_consolidated_id`, OMB-canonical) without one displacing the other.
2. **Two new tables** — `omb_consolidated_rows` (a row-for-row mirror of the OMB consolidated XLSX) and `omb_match_audit` (one row per matched/unmatched/drifted pair, the substrate the `/discrepancies` dashboard page reads from).

This phase is intentionally narrow: schema only, no ingest, no UI. After Phase 1 lands, the DB has empty new tables and four new NULL columns, ready for Phase 2 (match policy) and Phase 3 (loader).

## What I learned from Phase 0 that changes the original plan

The original plan in `2026-05-03-omb-consolidated-ingest.md` had a Phase 1 step "Verify the run-migrations runner picks up m004" that hand-waved the wiring. Reading `scripts/run_migrations.py` shows the runner **auto-discovers** any module under `migrations/` whose name starts with `m` via `pkgutil.iter_modules`, sorts by `MIGRATION_ID`, and tracks application via a `schema_migrations` ledger. That means:

- **No manual wiring needed.** Dropping `m004_omb_consolidated_provenance.py` into `migrations/` is sufficient.
- **The ledger handles re-run skipping.** My `apply()` only needs to be idempotent at the DDL level for the case where a prior run crashed mid-transaction (the runner wraps each `apply()` in `with conn:` so partial commits shouldn't happen, but defensive idempotency is cheap and matches m001–m003 patterns).
- **No need to run the migration manually with a hand-rolled `sqlite3.connect`.** Use `python3 scripts/run_migrations.py`.

## Files to create

| Path | Responsibility |
|---|---|
| `migrations/m004_omb_consolidated_provenance.py` | Adds 4 columns to `use_cases`, creates `omb_consolidated_rows` (mirror) + `omb_match_audit` (audit) + indexes. Idempotent. |
| `tests/test_migration_m004.py` | pytest suite verifying the four columns, both tables, and idempotency on second invocation. |

No files modified. No other moving parts.

## Execution steps

### Step 1: Write the failing test

Create `tests/test_migration_m004.py`:

```python
"""Migration m004 adds OMB-consolidated provenance columns + tables."""
import sqlite3

from migrations import m004_omb_consolidated_provenance as m


def _bootstrap_use_cases(conn: sqlite3.Connection) -> None:
    """Minimal use_cases table — m004 only adds columns; it doesn't read them."""
    conn.execute("CREATE TABLE use_cases (id INTEGER PRIMARY KEY, use_case_id TEXT)")


def test_migration_id_is_set():
    assert m.MIGRATION_ID == "004_omb_consolidated_provenance"


def test_adds_four_omb_columns_to_use_cases():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(use_cases)")}
    assert "omb_consolidated_id" in cols
    assert "omb_consolidated_source" in cols
    assert "omb_consolidated_first_seen" in cols
    assert "omb_consolidated_last_seen" in cols


def test_creates_omb_consolidated_rows_table_with_36_omb_columns():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(omb_consolidated_rows)")}
    # Ingest metadata
    for c in ["id", "ingest_source_file", "ingest_run_at", "row_hash",
              "row_index_in_file", "raw_json"]:
        assert c in cols, f"missing metadata column {c}"
    # 36 OMB columns (spot-check — full list verified by counting)
    for c in ["agency_abbreviation", "agency_name", "use_case_id_omb",
              "use_case_name", "bureau_component", "is_withheld",
              "stage_of_development", "is_high_impact", "ai_classification",
              "vendor_name", "have_ato", "has_pii", "has_custom_code",
              "hi_testing_conducted", "hi_public_consultation"]:
        assert c in cols, f"missing OMB column {c}"


def test_omb_consolidated_rows_has_unique_index_on_file_plus_idx():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    indexes = {
        r[1]: r[2]  # name -> unique flag
        for r in conn.execute("PRAGMA index_list(omb_consolidated_rows)")
    }
    assert "uq_omb_rows_file_idx" in indexes
    assert indexes["uq_omb_rows_file_idx"] == 1, "must be UNIQUE"


def test_creates_omb_match_audit_table():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(omb_match_audit)")}
    expected = {
        "id", "ingest_run_at", "omb_row_id", "use_case_id_db",
        "agency_abbreviation", "use_case_name", "match_method", "match_score",
        "match_status", "drift_fields_json", "first_seen", "last_seen",
        "resolved_at", "resolution_note",
    }
    assert expected <= cols, f"missing audit columns: {expected - cols}"


def test_match_status_index_exists():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    indexes = {r[1] for r in conn.execute("PRAGMA index_list(omb_match_audit)")}
    # Status filtering drives the dashboard page; index it.
    assert any("status" in name for name in indexes)


def test_is_idempotent_when_applied_twice():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    m.apply(conn)  # must not raise
    cols = {r[1] for r in conn.execute("PRAGMA table_info(use_cases)")}
    assert "omb_consolidated_id" in cols


def test_ledger_runner_picks_up_m004():
    """End-to-end: scripts/run_migrations auto-discovers m004 and applies it
    exactly once. Re-running is a no-op (returns []).
    """
    from scripts import run_migrations as runner

    conn = sqlite3.connect(":memory:")
    # Pre-create use_cases so m001 isn't required for m004's ALTER TABLE step.
    _bootstrap_use_cases(conn)
    # Insert other migrations' ledger rows so only m004 is "pending"
    conn.execute(
        "CREATE TABLE schema_migrations (migration_id TEXT PRIMARY KEY, applied_at TEXT)"
    )
    for prior in ("001_additive_inventory_schema", "002_rename_to_omb_canonical",
                  "003_consolidated_source_format"):
        conn.execute(
            "INSERT INTO schema_migrations(migration_id, applied_at) VALUES (?, ?)",
            (prior, "2026-05-03"),
        )

    applied = runner.apply_migrations(conn)
    assert "004_omb_consolidated_provenance" in applied
    # Second invocation: empty list (already in ledger)
    applied2 = runner.apply_migrations(conn)
    assert "004_omb_consolidated_provenance" not in applied2
```

### Step 2: Run test, verify ImportError

```bash
cd /Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory
pytest tests/test_migration_m004.py -v
```

Expected: `ModuleNotFoundError: No module named 'migrations.m004_omb_consolidated_provenance'`. All tests collect-fail or error at import.

### Step 3: Implement the migration

Create `migrations/m004_omb_consolidated_provenance.py`:

```python
"""Add OMB-consolidated-file provenance to use_cases + new tables.

The 2025 OMB consolidated `2025_individually_reported_AI_use_cases.xlsx`
introduces a parallel ID space (OMB-side) and a normalized snapshot of
each agency's filings, distinct from the per-agency raw files we ingest
via `load_inventories.py`. This migration adds the substrate:

  1. Four columns on `use_cases` for the OMB-side ID + ingest provenance.
     `use_case_id` (existing) stays IFP-canonical (agency-as-filed).
     `omb_consolidated_id` carries OMB's renumbering, which is sometimes
     blank (ED, GSA, HHS, SSA, STATE, TVA), sometimes a bare integer
     (EPA, NSF, TREAS), and sometimes the canonical AGENCY-N form.

  2. `omb_consolidated_rows` — a row-for-row mirror of the OMB file
     keeping all 36 OMB columns verbatim plus ingest metadata. Lets us
     re-audit drift in future rounds without re-parsing the XLSX.

  3. `omb_match_audit` — one row per match attempt (status enum, drift
     JSON, first_seen/last_seen, human-resolution fields). This drives
     the `/discrepancies` dashboard page.

Idempotent. Each DDL is guarded by an existence check so a crash mid-run
followed by re-application doesn't error out (the runner already wraps
this in a transaction; the guards are belt-and-suspenders).
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "004_omb_consolidated_provenance"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(
        r[1] == column for r in conn.execute(f"PRAGMA table_info({table})")
    )


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


# (column_name, ddl_type)
USE_CASES_NEW_COLUMNS = [
    ("omb_consolidated_id", "TEXT"),
    ("omb_consolidated_source", "TEXT"),
    ("omb_consolidated_first_seen", "TEXT"),
    ("omb_consolidated_last_seen", "TEXT"),
]


def apply(conn: sqlite3.Connection) -> None:
    # 1. Add four provenance columns to use_cases.
    for col, ddl in USE_CASES_NEW_COLUMNS:
        if not _column_exists(conn, "use_cases", col):
            conn.execute(f"ALTER TABLE use_cases ADD COLUMN {col} {ddl}")

    # 2. Mirror table — one row per OMB file row. row_hash is sha256 of the
    # canonical serialization (used by the loader for change detection on
    # re-ingest).
    if not _table_exists(conn, "omb_consolidated_rows"):
        conn.execute(
            """
            CREATE TABLE omb_consolidated_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingest_source_file TEXT NOT NULL,
                ingest_run_at TEXT NOT NULL,
                row_hash TEXT NOT NULL,
                row_index_in_file INTEGER NOT NULL,
                -- 36 OMB columns (verbatim from the consolidated XLSX)
                agency_abbreviation TEXT,
                agency_name TEXT,
                use_case_id_omb TEXT,
                use_case_name TEXT,
                bureau_component TEXT,
                email_address TEXT,
                is_withheld TEXT,
                stage_of_development TEXT,
                is_high_impact TEXT,
                hi_justification TEXT,
                topic_area TEXT,
                ai_classification TEXT,
                problem_statement TEXT,
                expected_benefits TEXT,
                system_outputs TEXT,
                operational_date TEXT,
                contracting_usage TEXT,
                vendor_name TEXT,
                have_ato TEXT,
                system_name_ato TEXT,
                training_data_description TEXT,
                link_to_data TEXT,
                has_pii TEXT,
                pia_url TEXT,
                demographic_features TEXT,
                has_custom_code TEXT,
                code_url TEXT,
                hi_testing_conducted TEXT,
                hi_assessment_completed TEXT,
                hi_potential_impacts TEXT,
                hi_independent_review TEXT,
                hi_ongoing_monitoring TEXT,
                hi_training_established TEXT,
                hi_failsafe_presence TEXT,
                hi_appeal_process TEXT,
                hi_public_consultation TEXT,
                raw_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE UNIQUE INDEX uq_omb_rows_file_idx "
            "ON omb_consolidated_rows(ingest_source_file, row_index_in_file)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_rows_agency "
            "ON omb_consolidated_rows(agency_abbreviation)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_rows_name "
            "ON omb_consolidated_rows(use_case_name)"
        )

    # 3. Audit table — one row per match attempt. match_status one of:
    #    'matched_exact' | 'matched_fuzzy' | 'suggested_rename' |
    #    'omb_only' | 'db_only' | 'duplicate_in_omb'.
    if not _table_exists(conn, "omb_match_audit"):
        conn.execute(
            """
            CREATE TABLE omb_match_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingest_run_at TEXT NOT NULL,
                omb_row_id INTEGER REFERENCES omb_consolidated_rows(id),
                use_case_id_db INTEGER REFERENCES use_cases(id),
                agency_abbreviation TEXT,
                use_case_name TEXT,
                match_method TEXT,
                match_score REAL,
                match_status TEXT NOT NULL,
                drift_fields_json TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                resolved_at TEXT,
                resolution_note TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX idx_omb_audit_status ON omb_match_audit(match_status)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_audit_agency "
            "ON omb_match_audit(agency_abbreviation)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_audit_db ON omb_match_audit(use_case_id_db)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_audit_omb ON omb_match_audit(omb_row_id)"
        )
```

### Step 4: Run tests, expect PASS

```bash
pytest tests/test_migration_m004.py -v
```

Expected: 8 tests pass. If `test_ledger_runner_picks_up_m004` fails with a foreign-key error from the `use_case_id_db REFERENCES use_cases(id)` clause, it means the `:memory:` DB enforced FK on a CREATE-ledger row — unlikely but possible. Fix by adding `conn.execute("PRAGMA foreign_keys = OFF")` before the test seeding (the live runner enables FK; the test doesn't need it for schema verification).

### Step 5: Apply against the live DB with safety backup

```bash
cp data/federal_ai_inventory_2025.db data/federal_ai_inventory_2025.db.pre-m004.bak
python3 scripts/run_migrations.py
```

Expected stdout:
```
Applied migrations:
  004_omb_consolidated_provenance
```

Verify:
```bash
sqlite3 data/federal_ai_inventory_2025.db "
  SELECT migration_id, applied_at FROM schema_migrations ORDER BY migration_id;
"
sqlite3 data/federal_ai_inventory_2025.db ".tables" | tr ' ' '\n' | grep -E '^omb_'
sqlite3 data/federal_ai_inventory_2025.db "
  SELECT COUNT(*) FROM pragma_table_info('use_cases')
  WHERE name LIKE 'omb_consolidated_%';
"
```

Expected:
- Ledger lists `001_…`, `002_…`, `003_…`, **`004_omb_consolidated_provenance`**, each with a timestamp.
- `.tables` includes `omb_consolidated_rows` and `omb_match_audit`.
- The `pragma_table_info` count returns **4**.

### Step 6: Re-run the runner, confirm no-op

```bash
python3 scripts/run_migrations.py
```

Expected: `No pending migrations.`

### Step 7: Run the full test suite, confirm baseline preserved

```bash
pytest tests/ audit/checks/ -q | tail -10
```

Expected: **91/98 passing (7 pre-existing failures)** — that is, +8 from the new m004 tests, no new failures, the same 7 baseline-drift failures from `audit/checks/` carried forward.

If the count is anything other than +8 from baseline, stop and investigate before committing.

### Step 8: Commit

```bash
git add migrations/m004_omb_consolidated_provenance.py tests/test_migration_m004.py
git status   # human-eyeball: only the two new files staged
git commit -m "$(cat <<'EOF'
feat(schema): add OMB consolidated provenance columns + tables (m004)

Adds 4 columns to use_cases (omb_consolidated_id, _source, _first_seen,
_last_seen) for OMB's parallel ID space, plus two new tables:

  - omb_consolidated_rows: row-for-row mirror of OMB's consolidated XLSX
    with all 36 OMB columns + ingest metadata.
  - omb_match_audit: one row per match attempt with status enum, drift
    JSON, and resolution fields. Drives the future /discrepancies page.

Auto-discovered by scripts/run_migrations.py via the existing m*-prefix
convention; no runner changes needed.
EOF
)"
```

Do **not** push. Phase 2 (match policy) will commit on top of this; the user pushes when the larger plan is complete or asks for an interim push.

## Critical files referenced

| Path | Why |
|---|---|
| `migrations/m001_additive_inventory_schema.py` | Pattern reference for module shape |
| `migrations/m002_rename_to_omb_canonical.py` | Pattern reference for guarded ALTER TABLE |
| `migrations/m003_consolidated_source_format.py` | Pattern reference (latest applied; my m004 sorts after it) |
| `scripts/run_migrations.py` lines 36–43 | Confirms auto-discovery: any `migrations/m*.py` with `MIGRATION_ID` and `apply(conn)` is picked up automatically |
| `data/federal_ai_inventory_2025.db.pre-m004.bak` | Safety backup written in Step 5; can be restored with `cp …pre-m004.bak data/federal_ai_inventory_2025.db` if anything goes wrong |
| `docs/plans/phase0-baseline.md` | The 83/90 baseline this phase preserves |

## Verification

Phase 1 is complete when all six are true:

1. `tests/test_migration_m004.py` — all 8 tests pass.
2. `pytest tests/ audit/checks/ -q` reports **91/98 passing (7 pre-existing failures)** — exactly +8 from the Phase 0 baseline, no new failures.
3. `data/federal_ai_inventory_2025.db` contains `omb_consolidated_rows` and `omb_match_audit` tables, and `use_cases` has the 4 new columns.
4. `schema_migrations` ledger contains `004_omb_consolidated_provenance` with a timestamp.
5. Re-running `scripts/run_migrations.py` reports `No pending migrations.`
6. Backup file `data/federal_ai_inventory_2025.db.pre-m004.bak` exists and is the same size as the pre-migration DB (sanity check that we backed up before applying).

Once these are true, Phase 2 (the pure-function match policy `omb_consolidated_match.py`) is unblocked.

## What this phase does NOT do

- No data is loaded into either new table — they're empty after Phase 1.
- No use case has `omb_consolidated_id` populated yet — all NULL until Phase 3.
- No dashboard changes; the `/discrepancies` page comes in Phase 5.
- No Makefile changes; the loader hookup is Phase 3.
- No DB sync into `dashboard/data/` — that happens in Phase 4 once the data is also loaded.
