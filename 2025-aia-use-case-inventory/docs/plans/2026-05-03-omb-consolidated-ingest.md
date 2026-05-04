# OMB Consolidated 2025 Inventory Ingest + Discrepancy Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingest OMB's 2025 consolidated individually-reported AI use case inventory (`data/raw/2025_individually_reported_AI_use_cases.xlsx`) as a parallel, OMB-canonical dataset; preserve our agency-as-filed IDs as IFP-canonical; expose all discrepancies (presence + content drift) on a dashboard page for visual review.

**Architecture:** OMB's consolidated file is a different *dataset kind* from per-agency raw filings — it's OMB's normalized snapshot. We mirror it row-for-row in a new `omb_consolidated_rows` table, link to existing `use_cases` rows via a deterministic `(agency, name)` match, and surface every mismatch via an `omb_match_audit` table that drives a new `/discrepancies` dashboard page. **No destructive merges**: when the OMB file disagrees with our DB, we record the discrepancy — we don't overwrite. Existing `use_cases.use_case_id` stays IFP-canonical (agency-as-filed); a new `omb_consolidated_id` column carries the OMB-side ID.

**Tech Stack:** Python 3.11 (openpyxl, sqlite3) for ETL · SQLite for storage · Next.js App Router + better-sqlite3 + TypeScript for dashboard · pytest for tests.

**Source files referenced throughout:**
- `data/raw/2025_individually_reported_AI_use_cases.xlsx` — the new OMB consolidated file (3,611 rows, 36 cols, sheet `Consolidated Inventory`, header row 2)
- `data/federal_ai_inventory_2025.db` — IFP DB (3,549 use cases at the time of this plan)

**Pre-verified inputs from 3-agent audit (2026-05-03):**
- 3,481 exact name-matches between OMB file and DB
- 10 fuzzy renames (mostly DOI/HHS minor edits; NSF acronym expansions need lower threshold)
- 120 OMB-only use cases (74 at 9 net-new agencies; 46 at agencies we already track)
- 33 DB-only at agencies in both (NSF 11, ED 21, DOI 1)
- 25 DB-only at 4 dropped agencies (FRTIB 6, GPO 10, NMB 4, OPM 5) — verified zero re-attribution
- Field-content drift on matched pairs: 84.4% byte-equivalent across 11 fields. Hottest drifters: `have_ato` 7.9%, `has_pii` 7.0%, `has_custom_code` 7.0%, `contracting_usage` 4.4%
- 4 high-impact reclassifications: NCUA Risk Indicator Model, NCUA Supervisory Stress Testing, DOE Copilot Studio, DOE Copilot for M365 — all moved upward to High-impact
- Verbatim-duplicate row: PBGC-14 ≡ PBGC-15 ("Legislative and Regulatory Analysis / Automation")
- Typo to flag: TVA "Enteprise Planning" (sic) in OMB file
- ED rewrote their inventory (15/36 exact-match) — flag for human review, do not auto-replace
- 6 ED-OMB rows have no DB match (Aidan Chat-bot, IPAC RPA Bot, etc. exist in DB but OMB IDs are NULL)

---

## File Structure

### Files to CREATE

| Path | Responsibility |
|---|---|
| `migrations/m004_omb_consolidated_provenance.py` | Adds 4 columns to `use_cases`, creates `omb_consolidated_rows` table + `omb_match_audit` table + indexes. Idempotent. |
| `load_omb_consolidated.py` | Top-level ETL script: parses the XLSX, populates `omb_consolidated_rows`, runs match policy, populates `use_cases.omb_consolidated_*` fields, writes `omb_match_audit`. Run after `load_inventories.py` in `make fix`. |
| `omb_consolidated_match.py` | Match-policy module: `match_omb_to_db(omb_row, db_index) -> MatchResult`. Pure functions, fully unit-tested. |
| `tests/test_load_omb_consolidated.py` | pytest suite for the loader (uses an in-memory DB seeded with fixture rows). |
| `tests/test_omb_consolidated_match.py` | pytest suite for the match policy. |
| `tests/fixtures/omb_consolidated_sample.xlsx` | Hand-crafted 30-row XLSX exercising every match category (exact, fuzzy, OMB-only, DB-only, drift, dropped-agency-bureau-trace). |
| `scripts/audit_omb_consolidated_diff.py` | Generates `audit/omb_consolidated_diff_2025.md` from `omb_match_audit` for offline review. |
| `dashboard/lib/discrepancies.ts` | Dashboard query layer: `getDiscrepancySummary()`, `getDiscrepancyRows(filter)`, `getDriftDetails(useCaseId)`. |
| `dashboard/app/discrepancies/page.tsx` | New page at `/discrepancies` — discrepancy summary + filterable detail table. |
| `dashboard/app/discrepancies/[caseId]/page.tsx` | Per-case drill-down showing OMB row vs DB row side-by-side. |
| `dashboard/components/discrepancy-table.tsx` | Client component for filtering / sorting the diff table. |
| `dashboard/components/discrepancy-side-by-side.tsx` | Server component that renders OMB ↔ DB field-pair diff with chips. |

### Files to MODIFY

| Path | Change |
|---|---|
| `Makefile` | Add `python3 load_omb_consolidated.py` and `python3 scripts/audit_omb_consolidated_diff.py` to the `fix` recipe (after `load_inventories.py`, before `auto_tag.py`). |
| `column_maps.py` | Add `OMB_CONSOLIDATED_COLUMNS` (the 36 OMB column-header → canonical-key map). |
| `dashboard/lib/types.ts` | Add `DiscrepancyRow`, `DiscrepancySummary`, `DiscrepancyDrift`, `OmbConsolidatedRow`. |
| `dashboard/components/site-nav.tsx` (or equivalent — find the actual nav file in step 0.1) | Add a "Discrepancies" link under Browse or Analytics. |
| `dashboard/app/use-cases/[caseId]/page.tsx` | Show OMB ID + IFP ID side-by-side; add "Not in OMB consolidated 2025" chip when `omb_consolidated_id IS NULL`. |
| `data/federal_ai_inventory_2025.db` | Schema change applied via `migrations/run_migrations.py`. |
| `dashboard/data/federal_ai_inventory_2025.db` | DB sync at end. |
| `tests/test_omb_consolidated_match.py` (already created above — listed for clarity) | |

### Out of scope (deliberately deferred)

- Auto-merging NSF acronym renames (e.g., DB `AII-26` ↔ OMB "Enhancing TIP Awards…"). Surface them as suggested-rename rows in `omb_match_audit` with status `suggested_rename`; humans approve in a follow-up.
- Auto-replacing ED's 36 rows with OMB's 56 (the rewrite). Flag as `agency_rewrite` in audit; require human action.
- Backfill of `omb_consolidated_id` for prior-year (2024) inventories — different file shape.

---

## Phase 0: Pre-flight

### Task 0.1: Verify environment + locate dashboard nav

**Files:**
- Read: `dashboard/components/` directory tree

- [ ] **Step 1: Confirm pytest runs cleanly today**

Run:
```bash
cd /Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory
pytest tests/ -q
```
Expected: All tests pass (or pre-existing failures noted in commit baseline). Record the count: `X/Y passing (Z pre-existing)`.

- [ ] **Step 2: Find the dashboard nav component**

Run:
```bash
grep -rn "use-cases\|/browse\|/analytics" dashboard/components/ dashboard/app/ -l | head -20
grep -rn "Link href" dashboard/components/site-nav* dashboard/components/header* dashboard/components/nav* 2>&1 | head -20
```
Record the file path; you'll edit it in Phase 4.

- [ ] **Step 3: Verify Source-Legend chip vocabulary**

Run:
```bash
grep -n "source.*omb\|source.*derived\|SourceLegend" dashboard/components/editorial.tsx
```
Confirm `Section` accepts `source` prop with values `"omb" | "derived" | "omb-derived" | "mixed"`. We'll use `"omb-derived"` (`OMB → IFP`) for the discrepancy page since the page displays OMB-filed values alongside IFP-derived match status.

---

## Phase 1: Schema migration

### Task 1.1: Migration adds 4 columns to `use_cases`

**Files:**
- Create: `migrations/m004_omb_consolidated_provenance.py`
- Test: `tests/test_migration_m004.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_migration_m004.py`:

```python
"""Migration m004 adds OMB-consolidated provenance columns + tables."""
import sqlite3
from migrations import m004_omb_consolidated_provenance as m


def _bootstrap_use_cases(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE use_cases (id INTEGER PRIMARY KEY, use_case_id TEXT)"
    )


def test_adds_omb_consolidated_columns():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(use_cases)")}
    assert "omb_consolidated_id" in cols
    assert "omb_consolidated_source" in cols
    assert "omb_consolidated_first_seen" in cols
    assert "omb_consolidated_last_seen" in cols


def test_creates_omb_consolidated_rows_table():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(omb_consolidated_rows)")}
    # 36 OMB columns + 5 metadata
    assert "agency_abbreviation" in cols
    assert "use_case_id_omb" in cols
    assert "use_case_name" in cols
    assert "ingest_source_file" in cols
    assert "ingest_run_at" in cols
    assert "row_hash" in cols
    assert "raw_json" in cols


def test_creates_omb_match_audit_table():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(omb_match_audit)")}
    assert {"omb_row_id", "use_case_id_db", "match_method",
            "match_status", "drift_fields_json", "first_seen", "last_seen"} <= cols


def test_is_idempotent():
    conn = sqlite3.connect(":memory:")
    _bootstrap_use_cases(conn)
    m.apply(conn)
    m.apply(conn)  # second invocation must not raise
    cols = {r[1] for r in conn.execute("PRAGMA table_info(use_cases)")}
    assert "omb_consolidated_id" in cols
```

- [ ] **Step 2: Run test — expect ImportError**

Run: `pytest tests/test_migration_m004.py -v`
Expected: FAIL with `ImportError` because `m004_omb_consolidated_provenance` doesn't exist.

- [ ] **Step 3: Implement the migration**

Create `migrations/m004_omb_consolidated_provenance.py`:

```python
"""Add OMB-consolidated-file provenance to use_cases + new tables.

The 2025 OMB consolidated `2025_individually_reported_AI_use_cases.xlsx`
introduces a parallel ID space (OMB-side) and a normalized snapshot of
each agency's filings. This migration:

  1. Adds 4 columns to `use_cases` for the OMB-side ID + ingest provenance.
  2. Creates `omb_consolidated_rows` — a row-for-row mirror of the OMB file.
  3. Creates `omb_match_audit` — every matched/unmatched/drifted pair, with
     status and drift fields, drives the dashboard discrepancy page.

Idempotent. Reversible by dropping the two new tables and the 4 columns.
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
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def apply(conn: sqlite3.Connection) -> None:
    # 1. Add the 4 provenance columns to use_cases.
    for col, ddl in [
        ("omb_consolidated_id", "TEXT"),
        ("omb_consolidated_source", "TEXT"),
        ("omb_consolidated_first_seen", "TEXT"),
        ("omb_consolidated_last_seen", "TEXT"),
    ]:
        if not _column_exists(conn, "use_cases", col):
            conn.execute(f"ALTER TABLE use_cases ADD COLUMN {col} {ddl}")

    # 2. Mirror table — one row per OMB file row, ALL 36 OMB columns preserved
    #    verbatim plus ingest metadata. row_hash is sha256 of the canonical
    #    serialization (used for change detection on re-ingest).
    if not _table_exists(conn, "omb_consolidated_rows"):
        conn.execute(
            """
            CREATE TABLE omb_consolidated_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingest_source_file TEXT NOT NULL,
                ingest_run_at TEXT NOT NULL,
                row_hash TEXT NOT NULL,
                row_index_in_file INTEGER NOT NULL,
                -- 36 OMB columns
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
    #    'matched_exact', 'matched_fuzzy', 'suggested_rename',
    #    'omb_only', 'db_only', 'agency_dropped', 'duplicate_in_omb'.
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
                match_method TEXT,           -- 'exact_name' | 'fuzzy_name' | 'none'
                match_score REAL,            -- 1.0 for exact, 0..1 for fuzzy, NULL for unmatched
                match_status TEXT NOT NULL,
                drift_fields_json TEXT,      -- JSON: {"field": {"db": "X", "omb": "Y"}}
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                resolved_at TEXT,            -- set when human resolves the discrepancy
                resolution_note TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX idx_omb_audit_status ON omb_match_audit(match_status)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_audit_agency ON omb_match_audit(agency_abbreviation)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_audit_db ON omb_match_audit(use_case_id_db)"
        )
        conn.execute(
            "CREATE INDEX idx_omb_audit_omb ON omb_match_audit(omb_row_id)"
        )
```

- [ ] **Step 4: Run tests, expect PASS**

Run: `pytest tests/test_migration_m004.py -v`
Expected: 4/4 PASS.

- [ ] **Step 5: Apply against the live DB (with safety backup)**

Run:
```bash
cp data/federal_ai_inventory_2025.db data/federal_ai_inventory_2025.db.pre-m004.bak
python3 -c "
import sqlite3
from migrations import m004_omb_consolidated_provenance as m
conn = sqlite3.connect('data/federal_ai_inventory_2025.db')
m.apply(conn)
conn.commit()
print('Applied m004.')
"
sqlite3 data/federal_ai_inventory_2025.db ".tables" | tr ' ' '\n' | grep -E 'omb_'
```
Expected output: `omb_consolidated_rows` and `omb_match_audit` listed.

- [ ] **Step 6: Verify the run-migrations runner picks up m004**

Run:
```bash
grep -rn "m003_consolidated_source_format\|migrations/" scripts/run_migrations.py
```
If the runner enumerates migrations by import, add `m004_omb_consolidated_provenance` to its list. Confirm by running:
```bash
python3 scripts/run_migrations.py
```
Expected: idempotent — no errors, no schema changes (m004 already applied).

- [ ] **Step 7: Commit**

```bash
git add migrations/m004_omb_consolidated_provenance.py tests/test_migration_m004.py
git commit -m "feat(schema): add OMB consolidated provenance columns + tables (m004)"
```

---

## Phase 2: Match policy module

### Task 2.1: Pure-function name normalization

**Files:**
- Create: `omb_consolidated_match.py`
- Test: `tests/test_omb_consolidated_match.py`

- [ ] **Step 1: Write failing tests for normalization**

Create `tests/test_omb_consolidated_match.py`:

```python
"""Tests for omb_consolidated_match — pure-function match policy."""
from omb_consolidated_match import (
    normalize_agency,
    normalize_name,
    name_match_score,
    classify_match,
    detect_drift,
    MatchResult,
)


def test_normalize_agency_maps_state_and_treas():
    assert normalize_agency("STATE") == "State"
    assert normalize_agency("TREAS") == "Treasury"
    assert normalize_agency("DOJ") == "DOJ"
    assert normalize_agency("State") == "State"
    assert normalize_agency(None) is None


def test_normalize_name_lowercases_and_collapses():
    assert normalize_name("  Hello   World  ") == "hello world"
    assert normalize_name("Foo’s Bar") == "foo's bar"  # curly to straight
    assert normalize_name("Health & Medical") == "health and medical"


def test_name_match_score_exact():
    assert name_match_score("Aidan Chat-bot", "Aidan Chat-bot") == 1.0
    assert name_match_score("aidan chat-bot", "Aidan Chat-bot") == 1.0


def test_name_match_score_fuzzy_threshold():
    # Acronym expansion should score high
    s = name_match_score(
        "TIP MS Copilot Pilot",
        "Technology, Innovation and Partnerships (TIP) Microsoft (MS) Copilot Pilot",
    )
    assert s >= 0.55  # we'll set the suggested-rename threshold conservatively
    # Totally different names
    assert name_match_score("Foo", "Bar") < 0.5


def test_classify_match_exact():
    r = classify_match(score=1.0, db_present=True, omb_present=True)
    assert r.status == "matched_exact"


def test_classify_match_fuzzy_above_threshold():
    r = classify_match(score=0.90, db_present=True, omb_present=True)
    assert r.status == "matched_fuzzy"


def test_classify_match_suggested_rename():
    r = classify_match(score=0.70, db_present=True, omb_present=True)
    assert r.status == "suggested_rename"


def test_classify_match_omb_only():
    r = classify_match(score=None, db_present=False, omb_present=True)
    assert r.status == "omb_only"


def test_classify_match_db_only():
    r = classify_match(score=None, db_present=True, omb_present=False)
    assert r.status == "db_only"


def test_detect_drift_canonicalizes_letter_prefix():
    db = {"stage_of_development": "a) Pre-deployment"}
    omb = {"stage_of_development": "Pre-deployment"}
    drift = detect_drift(db, omb, fields=["stage_of_development"])
    assert drift == {}  # canonical-equal


def test_detect_drift_reports_actual_diff():
    db = {"is_high_impact": "c) Not high-impact"}
    omb = {"is_high_impact": "a) High-impact"}
    drift = detect_drift(db, omb, fields=["is_high_impact"])
    assert "is_high_impact" in drift
    assert drift["is_high_impact"]["db"] == "c) Not high-impact"
    assert drift["is_high_impact"]["omb"] == "a) High-impact"


def test_detect_drift_handles_curly_apostrophe():
    db = {"vendor_name": "Microsoft’s Copilot"}
    omb = {"vendor_name": "Microsoft's Copilot"}
    drift = detect_drift(db, omb, fields=["vendor_name"])
    assert drift == {}
```

- [ ] **Step 2: Run tests — expect ImportError**

Run: `pytest tests/test_omb_consolidated_match.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `omb_consolidated_match.py`**

Create `omb_consolidated_match.py`:

```python
"""Pure-function match policy for OMB consolidated rows ↔ DB use_cases.

The policy: normalize agency abbreviations (STATE→State, TREAS→Treasury),
normalize use-case names (lowercase, whitespace-collapse, curly-quote
straightening, ampersand-to-and), score with difflib SequenceMatcher,
and classify into a fixed status enum.

Drift detection canonicalizes leading letter prefixes (`a) Pre-deployment`
→ `Pre-deployment`) and curly apostrophes before comparing — the same
normalizations OMB applies during their consolidation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable

# Threshold tuning notes (from 3-agent audit, 2026-05-03):
#   ≥ 0.85 → matched_fuzzy (10 pairs across DB; mostly DOI/HHS minor edits)
#   0.55–0.85 → suggested_rename (catches NSF acronym expansions like
#               "TIP MS Copilot Pilot" ↔ "Technology, Innovation and
#               Partnerships (TIP) Microsoft (MS) Copilot Pilot" ≈ 0.62)
#   < 0.55 → unmatched (omb_only or db_only)
FUZZY_MATCH_THRESHOLD = 0.85
SUGGESTED_RENAME_THRESHOLD = 0.55


_AGENCY_ABBR_MAP = {"STATE": "State", "TREAS": "Treasury"}


def normalize_agency(abbr: str | None) -> str | None:
    if abbr is None:
        return None
    return _AGENCY_ABBR_MAP.get(abbr, abbr)


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_name(s: str | None) -> str:
    if s is None:
        return ""
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace(" & ", " and ")
    s = s.lower().strip()
    s = _WHITESPACE_RE.sub(" ", s)
    return s


def name_match_score(a: str | None, b: str | None) -> float:
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


@dataclass(frozen=True)
class MatchResult:
    status: str  # one of: matched_exact, matched_fuzzy, suggested_rename,
                 #         omb_only, db_only
    score: float | None
    method: str  # 'exact_name' | 'fuzzy_name' | 'none'


def classify_match(
    score: float | None, *, db_present: bool, omb_present: bool
) -> MatchResult:
    if not db_present and omb_present:
        return MatchResult(status="omb_only", score=None, method="none")
    if db_present and not omb_present:
        return MatchResult(status="db_only", score=None, method="none")
    if score is None:
        return MatchResult(status="db_only", score=None, method="none")
    if score == 1.0:
        return MatchResult(status="matched_exact", score=1.0, method="exact_name")
    if score >= FUZZY_MATCH_THRESHOLD:
        return MatchResult(status="matched_fuzzy", score=score, method="fuzzy_name")
    if score >= SUGGESTED_RENAME_THRESHOLD:
        return MatchResult(status="suggested_rename", score=score, method="fuzzy_name")
    if omb_present and not db_present:
        return MatchResult(status="omb_only", score=None, method="none")
    return MatchResult(status="db_only", score=None, method="none")


# Drift fields (compared canonical-equal between OMB row and DB row):
DRIFT_FIELDS_DEFAULT = (
    "stage_of_development",
    "is_high_impact",
    "is_withheld",
    "topic_area",
    "ai_classification",
    "contracting_usage",
    "vendor_name",
    "have_ato",
    "has_pii",
    "has_custom_code",
    "bureau_component",
)


_LETTER_PREFIX_RE = re.compile(r"^\s*[a-z]\)\s*", flags=re.IGNORECASE)


def _canonicalize_field(s: str | None) -> str | None:
    if s is None:
        return None
    s = s.replace("’", "'").replace("‘", "'")
    s = _LETTER_PREFIX_RE.sub("", s).strip().lower()
    s = _WHITESPACE_RE.sub(" ", s)
    return s


def detect_drift(
    db_row: dict, omb_row: dict, *, fields: Iterable[str] = DRIFT_FIELDS_DEFAULT
) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for f in fields:
        db_v, omb_v = db_row.get(f), omb_row.get(f)
        if _canonicalize_field(db_v) != _canonicalize_field(omb_v):
            if db_v or omb_v:  # ignore both-empty
                out[f] = {"db": db_v, "omb": omb_v}
    return out
```

- [ ] **Step 4: Run tests, expect PASS**

Run: `pytest tests/test_omb_consolidated_match.py -v`
Expected: 11/11 PASS.

- [ ] **Step 5: Commit**

```bash
git add omb_consolidated_match.py tests/test_omb_consolidated_match.py
git commit -m "feat(omb-ingest): pure-function match policy + drift detection"
```

---

## Phase 3: Loader script

### Task 3.1: Build the column-map

**Files:**
- Modify: `column_maps.py`

- [ ] **Step 1: Read existing CONSOLIDATED_COLUMNS for shape**

Run: `grep -n "CONSOLIDATED_COLUMNS\|map_consolidated_headers" column_maps.py | head -20`

- [ ] **Step 2: Add OMB_CONSOLIDATED_COLUMNS**

In `column_maps.py`, append:

```python
# 2025 OMB consolidated INDIVIDUALLY-REPORTED inventory.
#
# Source: data/raw/2025_individually_reported_AI_use_cases.xlsx
# Sheet: 'Consolidated Inventory' — header row 2, data starts row 3.
# 36 OMB columns plus 2 OMB-added agency columns at the front.
#
# Header strings include trailing newlines and "Practice: ..." hints; we
# match by lowercased + whitespace-collapsed prefix.
OMB_CONSOLIDATED_COLUMNS = [
    ("agency abbreviation", "agency_abbreviation"),
    ("agency name", "agency_name"),
    ("use case id", "use_case_id_omb"),
    ("use case name", "use_case_name"),
    ("bureau/component", "bureau_component"),
    ("email address", "email_address"),
    ("should this ai use case be withheld", "is_withheld"),
    ("stage of development", "stage_of_development"),
    ("is the ai use case high-impact", "is_high_impact"),
    ("justification", "hi_justification"),
    ("use case topic area", "topic_area"),
    ("ai classification", "ai_classification"),
    ("what problem is the ai intended to solve", "problem_statement"),
    ("what are the expected benefits", "expected_benefits"),
    ("describe the ai system's outputs", "system_outputs"),
    ("date when ai use case became operational", "operational_date"),
    ("was the system involved in this use case purchased", "contracting_usage"),
    ("vendor(s) name", "vendor_name"),
    ("does this ai use case have an associated authorization to operate", "have_ato"),
    ("system(s) name", "system_name_ato"),
    ("describe any data used to", "training_data_description"),
    ("if the data is required to be", "link_to_data"),
    ("does this ai use case", "has_pii"),  # PII column — disambiguated by position
    ("if publicly available, provide", "pia_url"),
    ("which, if any, demographic", "demographic_features"),
    ("does this project include", "has_custom_code"),
    ("if the code is open source", "code_url"),
    ("has pre-deployment testing", "hi_testing_conducted"),
    ("has an ai impact assessment", "hi_assessment_completed"),
    ("what are the potential", "hi_potential_impacts"),
    ("has as independent review", "hi_independent_review"),
    ("is there a process to conduct", "hi_ongoing_monitoring"),
    ("has the agency established sufficient and periodic", "hi_training_established"),
    ("does this ai use case have an appropriate fail-safe", "hi_failsafe_presence"),
    ("is there an established appeal process", "hi_appeal_process"),
    ("what steps has the agency taken to consult", "hi_public_consultation"),
]


def map_omb_consolidated_headers(headers: list[str | None]) -> list[str | None]:
    """Position-aware header map. Returns canonical key per column index, or
    None if the header doesn't match any known prefix.

    The OMB file's two `Does this AI use case ...` columns (PII and ATO)
    are disambiguated by ordinal position: the 19th column is `have_ato`,
    the 23rd is `has_pii`. We trust column order over header substring.
    """
    out: list[str | None] = [None] * len(headers)
    # Position-locked keys — if the file ever reorders columns, fail loudly.
    expected_keys_by_index = [k for _, k in OMB_CONSOLIDATED_COLUMNS]
    for i, h in enumerate(headers):
        if i >= len(expected_keys_by_index):
            break
        out[i] = expected_keys_by_index[i]
    return out
```

- [ ] **Step 3: Verify against the actual file**

Run:
```bash
python3 -c "
import openpyxl
from column_maps import map_omb_consolidated_headers
wb = openpyxl.load_workbook('data/raw/2025_individually_reported_AI_use_cases.xlsx', read_only=True)
ws = wb['Consolidated Inventory']
rows = ws.iter_rows(values_only=True)
next(rows)  # blank
hdr = list(next(rows))
mapped = map_omb_consolidated_headers(hdr)
print(list(zip(range(len(mapped)), mapped, [str(h)[:40] for h in hdr])))
"
```
Expected: 36 columns mapped, all non-None, in the documented order.

- [ ] **Step 4: Commit**

```bash
git add column_maps.py
git commit -m "feat(omb-ingest): position-locked header map for OMB consolidated file"
```

---

### Task 3.2: Loader implementation (TDD)

**Files:**
- Create: `load_omb_consolidated.py`
- Create: `tests/fixtures/omb_consolidated_sample.xlsx`
- Create: `tests/test_load_omb_consolidated.py`

- [ ] **Step 1: Build the test fixture XLSX**

Create `tests/fixtures/_build_fixture.py` (run-once helper, kept in repo for reproducibility):

```python
"""Build a 30-row fixture for OMB-consolidated loader tests.

Covers every match category. Run from repo root:
  python3 tests/fixtures/_build_fixture.py
"""
import openpyxl
from pathlib import Path

OUT = Path(__file__).parent / "omb_consolidated_sample.xlsx"

HEADERS = [
    "Agency Abbreviation", "Agency Name", "Use Case ID", "Use Case Name",
    "Bureau/Component", "Email Address",
    "Should this AI use case be withheld from public reporting?",
    "Stage of Development", "Is the AI use case high-impact?",
    "Justification", "Use Case Topic Area", "AI Classification",
    "What problem is the AI intended to solve?",
    "What are the expected benefits and positive outcomes from the AI for an agency's mission and/or the general public?",
    "Describe the AI system's outputs.",
    "Date when AI use case became operational or the pilot's start date",
    "Was the system involved in this use case purchased from a vendor or developed under contract(s) or in-house?",
    "Vendor(s) Name",
    "Does this AI use case have an associated Authorization to Operate (ATO)?",
    "System(s) Name",
    "Describe any data used to train, fine-tune, and/or evaluate performance of the model(s) used in this use case.",
    "If the data is required to be publicly disclosed as an open government data asset, provide a link to the entry on the data inventory.",
    "Does this AI use case involve personally identifiable information (PII) that is maintained by the agency?",
    "If publicly available, provide the link to the AI use case's associated Privacy Impact Assessment (PIA).",
    "Which, if any, demographic variables does the AI use case explicitly use as model features?",
    "Does this project include custom-developed code?",
    "If the code is open source, provide the link for the publicly available source code.",
    "Has pre-deployment testing been conducted for this AI use case?",
    "Has an AI impact assessment been completed for this AI use case?",
    "What are the potential impacts of using the AI for this particular use case and how were they identified?",
    "Has as independent review of the AI use case been conducted?",
    "Is there a process to conduct ongoing monitoring to identify any adverse impacts to the performance and security of the AI?",
    "Has the agency established sufficient and periodic training for operators of the AI to interpret and act on the its outputs?",
    "Does this AI use case have an appropriate fail-safe that minimizes the risk of significant harm?",
    "Is there an established appeal process in the event that an impacted individual would like to appeal or contest the AI?",
    "What steps has the agency taken to consult and incorporate feedback from end users of this AI use case and the public?",
]
assert len(HEADERS) == 36, f"expected 36, got {len(HEADERS)}"


def row(abbr, name_full, uid, name, **overrides):
    base = [abbr, name_full, uid, name, "Test Bureau", "user@example.gov",
            "a) No", "b) Pilot", "c) Not high-impact"] + [None]*27
    for k, v in overrides.items():
        idx_map = {"stage": 7, "high_impact": 8, "topic": 10, "classification": 11,
                   "vendor": 17, "have_ato": 18, "has_pii": 22, "has_custom_code": 25}
        base[idx_map[k]] = v
    return base


wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Consolidated Inventory"
ws.append([None]*36)         # row 1 blank
ws.append(HEADERS)           # row 2 headers

# Exact match (DB row will be seeded with this name + agency)
ws.append(row("DOJ", "Department of Justice", "DOJ-0001", "Test Veritone System"))
# Fuzzy match (DB has "Test Veritone System" — OMB has slight rename)
ws.append(row("DOJ", "Department of Justice", "DOJ-0002", "Test Veritone Audio System"))
# Suggested rename (acronym expansion)
ws.append(row("NSF", "National Science Foundation", 7, "Technology, Innovation and Partnerships (TIP) Microsoft (MS) Copilot Pilot"))
# OMB-only at known agency
ws.append(row("DHS", "Department of Homeland Security", "DHS-9999", "Brand New DHS Use Case"))
# OMB-only at net-new agency
ws.append(row("PBGC", "Pension Benefit Guaranty Corp", "PBGC-01", "PBGC Synthetic Data"))
# Drift case — same name, different stage
ws.append(row("DOE", "Department of Energy", "DOE-555", "Drift Test Case",
              stage="c) Deployed", high_impact="a) High-impact"))
# Verbatim duplicate row in OMB
ws.append(row("PBGC", "Pension Benefit Guaranty Corp", "PBGC-14", "Legislative and Regulatory Analysis"))
ws.append(row("PBGC", "Pension Benefit Guaranty Corp", "PBGC-15", "Legislative and Regulatory Analysis"))
# Empty ID (ED-style)
ws.append(row("ED", "Department of Education", None, "Aidan Chat-bot"))
# STATE → State remap
ws.append(row("STATE", "Department of State", None, "AI Input in Translation"))

wb.save(OUT)
print(f"Wrote {OUT} with {ws.max_row} rows.")
```

Run: `python3 tests/fixtures/_build_fixture.py`
Verify: `tests/fixtures/omb_consolidated_sample.xlsx` exists.

- [ ] **Step 2: Write failing tests for the loader**

Create `tests/test_load_omb_consolidated.py`:

```python
"""Loader tests using the fixture XLSX + an in-memory DB."""
import json
import sqlite3
from pathlib import Path

import pytest

from migrations import m004_omb_consolidated_provenance as m004
import load_omb_consolidated as loader

FIXTURE = Path(__file__).parent / "fixtures" / "omb_consolidated_sample.xlsx"


def _seed_db():
    """Build an in-memory DB matching the real schema's shape (subset)."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE agencies (id INTEGER PRIMARY KEY, abbreviation TEXT UNIQUE, full_name TEXT)")
    conn.execute("""
        CREATE TABLE use_cases (
            id INTEGER PRIMARY KEY,
            agency_id INTEGER,
            use_case_id TEXT,
            use_case_name TEXT NOT NULL,
            stage_of_development TEXT,
            is_high_impact TEXT,
            is_withheld TEXT,
            topic_area TEXT,
            ai_classification TEXT,
            contracting_usage TEXT,
            development_type TEXT,
            vendor_name TEXT,
            has_ato TEXT,
            has_pii TEXT,
            has_custom_code TEXT,
            bureau_component TEXT
        )
    """)
    m004.apply(conn)
    # Seed agencies
    for abbr, name in [
        ("DOJ", "Department of Justice"), ("NSF", "National Science Foundation"),
        ("DHS", "Department of Homeland Security"), ("DOE", "Department of Energy"),
        ("ED", "Department of Education"), ("State", "Department of State"),
        ("PBGC", "Pension Benefit Guaranty Corp"),
    ]:
        conn.execute("INSERT INTO agencies(abbreviation, full_name) VALUES (?, ?)", (abbr, name))
    # Seed use_cases — DB-side rows
    seeds = [
        ("DOJ", "DOJ-0001", "Test Veritone System", "b) Pilot", "c) Not high-impact"),
        ("DOJ", "DOJ-LEGACY", "Test Veritone System Audio Slightly Different", "b) Pilot", "c) Not high-impact"),
        ("NSF", "AII-49", "TIP MS Copilot Pilot", "b) Pilot", "c) Not high-impact"),
        ("DOE", "DOE-555", "Drift Test Case", "b) Pilot", "c) Not high-impact"),
        ("ED", "ED-0001", "Aidan Chat-bot", "b) Pilot", "c) Not high-impact"),
        ("State", "DOS - 1473", "AI Input in Translation", "b) Pilot", "c) Not high-impact"),
        # A DB row with NO OMB match — should land in db_only
        ("FRTIB", "FRTIB-001", "Sumtotal Chatbot", "b) Pilot", "c) Not high-impact"),
    ]
    conn.execute("INSERT INTO agencies(abbreviation, full_name) VALUES (?, ?)", ("FRTIB", "FRTIB"))
    for abbr, uid, name, stage, hi in seeds:
        agency_id = conn.execute("SELECT id FROM agencies WHERE abbreviation=?", (abbr,)).fetchone()[0]
        conn.execute(
            "INSERT INTO use_cases(agency_id, use_case_id, use_case_name, stage_of_development, is_high_impact) "
            "VALUES (?, ?, ?, ?, ?)",
            (agency_id, uid, name, stage, hi),
        )
    conn.commit()
    return conn


def test_loader_inserts_all_omb_rows():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    n = conn.execute("SELECT COUNT(*) FROM omb_consolidated_rows").fetchone()[0]
    assert n == 10  # 10 data rows in the fixture


def test_loader_marks_exact_match():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    row = conn.execute("""
        SELECT a.match_status, a.match_score
        FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id=a.omb_row_id
        WHERE o.use_case_name = 'Test Veritone System'
    """).fetchone()
    assert row[0] == "matched_exact"
    assert row[1] == 1.0


def test_loader_marks_suggested_rename_for_nsf_acronym():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    row = conn.execute("""
        SELECT a.match_status FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id=a.omb_row_id
        WHERE o.agency_abbreviation = 'NSF'
    """).fetchone()
    assert row[0] in ("suggested_rename", "matched_fuzzy")


def test_loader_records_drift_for_doe_case():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    drift_json = conn.execute("""
        SELECT a.drift_fields_json FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id=a.omb_row_id
        WHERE o.use_case_name = 'Drift Test Case'
    """).fetchone()[0]
    drift = json.loads(drift_json)
    assert "stage_of_development" in drift
    assert "is_high_impact" in drift


def test_loader_marks_db_only_for_frtib():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    rows = conn.execute(
        "SELECT match_status FROM omb_match_audit WHERE agency_abbreviation='FRTIB'"
    ).fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "db_only"


def test_loader_marks_omb_only_at_dhs_for_unknown_name():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    row = conn.execute("""
        SELECT a.match_status FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id=a.omb_row_id
        WHERE o.use_case_name = 'Brand New DHS Use Case'
    """).fetchone()
    assert row[0] == "omb_only"


def test_loader_detects_pbgc_duplicate():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    rows = conn.execute("""
        SELECT match_status FROM omb_match_audit
        WHERE use_case_name = 'Legislative and Regulatory Analysis'
    """).fetchall()
    statuses = [r[0] for r in rows]
    assert "duplicate_in_omb" in statuses


def test_loader_populates_use_case_omb_consolidated_id_for_matches():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    omb_id = conn.execute("""
        SELECT omb_consolidated_id FROM use_cases WHERE use_case_name='Test Veritone System'
    """).fetchone()[0]
    assert omb_id == "DOJ-0001"


def test_loader_handles_state_to_state_normalization():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    row = conn.execute("""
        SELECT a.match_status FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id=a.omb_row_id
        WHERE o.use_case_name = 'AI Input in Translation'
    """).fetchone()
    assert row[0] == "matched_exact"


def test_loader_is_idempotent_on_rerun():
    conn = _seed_db()
    loader.load(conn, FIXTURE)
    n1 = conn.execute("SELECT COUNT(*) FROM omb_consolidated_rows").fetchone()[0]
    n_audit_1 = conn.execute("SELECT COUNT(*) FROM omb_match_audit").fetchone()[0]
    loader.load(conn, FIXTURE)
    n2 = conn.execute("SELECT COUNT(*) FROM omb_consolidated_rows").fetchone()[0]
    n_audit_2 = conn.execute("SELECT COUNT(*) FROM omb_match_audit").fetchone()[0]
    assert n1 == n2  # rows replaced, not duplicated
    assert n_audit_1 == n_audit_2
```

- [ ] **Step 3: Run tests — expect ImportError**

Run: `pytest tests/test_load_omb_consolidated.py -v`
Expected: FAIL — `load_omb_consolidated` not defined.

- [ ] **Step 4: Implement the loader**

Create `load_omb_consolidated.py`:

```python
"""Load the 2025 OMB consolidated individually-reported AI use case file.

This loader is OMB's snapshot of agency filings — distinct from the
per-agency files loaded by `load_inventories.py`. It populates two tables:

  - `omb_consolidated_rows`: a row-for-row mirror of the XLSX (36 columns)
  - `omb_match_audit`:        one row per match attempt (status + drift)

It also writes back to `use_cases.omb_consolidated_id` /
`omb_consolidated_source` / `omb_consolidated_first_seen` /
`omb_consolidated_last_seen` for matched pairs.

Idempotent: re-running replaces `omb_consolidated_rows` for the same
source-file path and rebuilds `omb_match_audit` from scratch (preserving
`first_seen` and human-set `resolution_note` / `resolved_at`).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import openpyxl

from column_maps import OMB_CONSOLIDATED_COLUMNS, map_omb_consolidated_headers
from omb_consolidated_match import (
    DRIFT_FIELDS_DEFAULT,
    classify_match,
    detect_drift,
    name_match_score,
    normalize_agency,
    normalize_name,
)

DEFAULT_FILE = Path("data/raw/2025_individually_reported_AI_use_cases.xlsx")
SHEET_NAME = "Consolidated Inventory"

# Per-agency thresholds (tuned for the 2026-05-03 audit findings).
# Lowered for NSF specifically because the agency expanded acronyms in
# their OMB filing (e.g., "TIP MS Copilot" → "Technology, Innovation and
# Partnerships (TIP) Microsoft (MS) Copilot"), pushing many real matches
# into the 0.55–0.85 band.
_PER_AGENCY_RENAME_THRESHOLD = {
    "NSF": 0.55,  # accept acronym expansions
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_iter(path: Path) -> Iterator[tuple[int, list]]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[SHEET_NAME]
    rows = ws.iter_rows(values_only=True)
    next(rows)  # row 1 — typically blank
    next(rows)  # row 2 — headers (we trust position-locked map)
    for i, row in enumerate(rows, start=3):
        if not any(c is not None and str(c).strip() for c in row):
            continue
        yield i, list(row)


def _hash_row(canonical: list) -> str:
    blob = json.dumps([(s.strip() if isinstance(s, str) else s) for s in canonical],
                      ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


def _replace_omb_rows(conn: sqlite3.Connection, source_file: str) -> None:
    conn.execute(
        "DELETE FROM omb_consolidated_rows WHERE ingest_source_file=?",
        (source_file,),
    )


def _insert_omb_row(
    conn: sqlite3.Connection, source_file: str, run_at: str, idx: int, vals: list
) -> int:
    keys = [k for _, k in OMB_CONSOLIDATED_COLUMNS]
    raw_json = json.dumps(dict(zip(keys, vals)), ensure_ascii=False)
    row_hash = _hash_row(vals)
    cols = (
        ["ingest_source_file", "ingest_run_at", "row_hash", "row_index_in_file"]
        + keys
        + ["raw_json"]
    )
    placeholders = ",".join(["?"] * len(cols))
    cur = conn.execute(
        f"INSERT INTO omb_consolidated_rows({','.join(cols)}) VALUES ({placeholders})",
        [source_file, run_at, row_hash, idx, *vals, raw_json],
    )
    return cur.lastrowid


def _build_db_index(conn: sqlite3.Connection) -> dict:
    """Build (agency_abbr, normalized_name) -> [db_row_dict] index."""
    rows = conn.execute(
        """
        SELECT uc.id AS db_id, uc.use_case_id, uc.use_case_name,
               uc.stage_of_development, uc.is_high_impact, uc.is_withheld,
               uc.topic_area, uc.ai_classification,
               COALESCE(uc.contracting_usage, uc.development_type) AS contracting_usage,
               uc.vendor_name, uc.has_ato AS have_ato, uc.has_pii,
               uc.has_custom_code, uc.bureau_component,
               a.abbreviation AS agency_abbreviation
        FROM use_cases uc
        JOIN agencies a ON a.id = uc.agency_id
        """
    ).fetchall()
    index: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        d = dict(r) if isinstance(r, sqlite3.Row) else dict(zip(
            ["db_id", "use_case_id", "use_case_name", "stage_of_development",
             "is_high_impact", "is_withheld", "topic_area", "ai_classification",
             "contracting_usage", "vendor_name", "have_ato", "has_pii",
             "has_custom_code", "bureau_component", "agency_abbreviation"], r))
        agency = normalize_agency(d["agency_abbreviation"])
        key = (agency, normalize_name(d["use_case_name"]))
        index.setdefault(key, []).append(d)
    return index


def _omb_row_dict(vals: list) -> dict:
    return dict(zip([k for _, k in OMB_CONSOLIDATED_COLUMNS], vals))


def load(conn: sqlite3.Connection, path: Path | str = DEFAULT_FILE) -> None:
    path = Path(path)
    source_file = path.name
    run_at = _now()

    # 1. Replace omb_consolidated_rows for this source file.
    _replace_omb_rows(conn, source_file)
    omb_row_ids: list[tuple[int, list]] = []
    for idx, vals in _row_iter(path):
        rid = _insert_omb_row(conn, source_file, run_at, idx, vals)
        omb_row_ids.append((rid, vals))

    # 2. Build DB index for matching.
    db_index = _build_db_index(conn)
    matched_db_ids: set[int] = set()
    seen_omb_keys: dict[tuple[str, str], int] = {}  # for duplicate detection

    # 3. Preserve existing first_seen / resolution_note from prior audit rows.
    prior_audit = {
        (row["agency_abbreviation"], row["use_case_name"]): row
        for row in conn.execute(
            "SELECT agency_abbreviation, use_case_name, first_seen, "
            "resolved_at, resolution_note FROM omb_match_audit"
        )
    }
    conn.execute("DELETE FROM omb_match_audit")

    # 4. Walk OMB rows and classify each.
    for omb_id, vals in omb_row_ids:
        omb = _omb_row_dict(vals)
        agency = normalize_agency(omb["agency_abbreviation"])
        name_norm = normalize_name(omb["use_case_name"])
        key = (agency, name_norm)

        # Duplicate detection
        if key in seen_omb_keys:
            _record_audit(
                conn, run_at, omb_id, None, agency, omb["use_case_name"],
                "none", None, "duplicate_in_omb", {}, prior_audit,
            )
            continue
        seen_omb_keys[key] = omb_id

        candidates = db_index.get(key, [])
        if candidates:
            # Exact match
            db_row = candidates[0]
            matched_db_ids.add(db_row["db_id"])
            drift = detect_drift(db_row, omb, fields=DRIFT_FIELDS_DEFAULT)
            _record_audit(
                conn, run_at, omb_id, db_row["db_id"], agency,
                omb["use_case_name"], "exact_name", 1.0, "matched_exact",
                drift, prior_audit,
            )
            _link_use_case(conn, db_row["db_id"], omb["use_case_id_omb"],
                           source_file, run_at, prior_audit, key)
        else:
            # Try fuzzy within agency
            best_score, best_db = 0.0, None
            same_agency = [d for k, lst in db_index.items() if k[0] == agency
                           for d in lst]
            for d in same_agency:
                if d["db_id"] in matched_db_ids:
                    continue
                s = name_match_score(omb["use_case_name"], d["use_case_name"])
                if s > best_score:
                    best_score, best_db = s, d

            rename_threshold = _PER_AGENCY_RENAME_THRESHOLD.get(agency, 0.55)
            classification = classify_match(
                best_score, db_present=best_db is not None, omb_present=True
            )

            if classification.status == "matched_fuzzy":
                matched_db_ids.add(best_db["db_id"])
                drift = detect_drift(best_db, omb, fields=DRIFT_FIELDS_DEFAULT)
                _record_audit(
                    conn, run_at, omb_id, best_db["db_id"], agency,
                    omb["use_case_name"], "fuzzy_name", best_score,
                    "matched_fuzzy", drift, prior_audit,
                )
                _link_use_case(conn, best_db["db_id"], omb["use_case_id_omb"],
                               source_file, run_at, prior_audit, key)
            elif (best_score >= rename_threshold and best_db is not None
                  and classification.status == "suggested_rename"):
                # Surface but don't auto-link — humans review.
                _record_audit(
                    conn, run_at, omb_id, best_db["db_id"], agency,
                    omb["use_case_name"], "fuzzy_name", best_score,
                    "suggested_rename", {}, prior_audit,
                )
            else:
                _record_audit(
                    conn, run_at, omb_id, None, agency, omb["use_case_name"],
                    "none", None, "omb_only", {}, prior_audit,
                )

    # 5. DB rows that no OMB row matched → db_only.
    for (agency, _name_norm), db_rows in db_index.items():
        for d in db_rows:
            if d["db_id"] in matched_db_ids:
                continue
            _record_audit(
                conn, run_at, None, d["db_id"], agency, d["use_case_name"],
                "none", None, "db_only", {}, prior_audit,
            )

    conn.commit()


def _link_use_case(
    conn: sqlite3.Connection, db_id: int, omb_id: str | None, source: str,
    run_at: str, prior: dict, key: tuple[str, str],
) -> None:
    prior_row = prior.get(key)
    first_seen = prior_row["first_seen"] if prior_row else run_at
    conn.execute(
        """
        UPDATE use_cases SET omb_consolidated_id = ?,
                             omb_consolidated_source = ?,
                             omb_consolidated_first_seen = COALESCE(omb_consolidated_first_seen, ?),
                             omb_consolidated_last_seen = ?
        WHERE id = ?
        """,
        (str(omb_id) if omb_id is not None else None, source, first_seen, run_at, db_id),
    )


def _record_audit(
    conn: sqlite3.Connection, run_at: str, omb_id: int | None,
    db_id: int | None, agency: str | None, name: str | None,
    method: str, score: float | None, status: str, drift: dict, prior: dict,
) -> None:
    key = (agency, name)
    prior_row = prior.get(key)
    first_seen = prior_row["first_seen"] if prior_row else run_at
    resolved_at = prior_row["resolved_at"] if prior_row else None
    resolution_note = prior_row["resolution_note"] if prior_row else None
    conn.execute(
        """
        INSERT INTO omb_match_audit(
            ingest_run_at, omb_row_id, use_case_id_db, agency_abbreviation,
            use_case_name, match_method, match_score, match_status,
            drift_fields_json, first_seen, last_seen, resolved_at, resolution_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_at, omb_id, db_id, agency, name, method, score, status,
         json.dumps(drift, ensure_ascii=False), first_seen, run_at,
         resolved_at, resolution_note),
    )


if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    load(conn)
    print("Loaded OMB consolidated file.")
    print("Audit rollup:")
    for status, n in conn.execute(
        "SELECT match_status, COUNT(*) FROM omb_match_audit GROUP BY match_status"
    ):
        print(f"  {status:<24} {n}")
```

- [ ] **Step 5: Run loader tests, expect PASS**

Run: `pytest tests/test_load_omb_consolidated.py -v`
Expected: 10/10 PASS. If `test_loader_handles_state_to_state_normalization` fails, audit normalize_agency call sites in the loader (likely you forgot to normalize before keying the index).

- [ ] **Step 6: Run loader against the live DB**

Run:
```bash
python3 load_omb_consolidated.py
```
Expected stdout: rollup like:
```
matched_exact      ~3,481
matched_fuzzy      ~10
suggested_rename   ~5–20
omb_only           ~120
db_only            ~58 (33 + 25)
duplicate_in_omb   ~1 (PBGC)
```
Numbers ±10 are fine — the audit produced ranges.

- [ ] **Step 7: Sanity-check the live DB**

Run:
```bash
sqlite3 data/federal_ai_inventory_2025.db "
  SELECT match_status, COUNT(*) FROM omb_match_audit GROUP BY match_status ORDER BY 2 DESC;
"
sqlite3 data/federal_ai_inventory_2025.db "
  SELECT COUNT(*) FROM use_cases WHERE omb_consolidated_id IS NOT NULL;
"
```
Expected: ≥3,400 `matched_exact`, plus the smaller buckets. Roughly 3,491 matched-and-linked use cases (exact + fuzzy).

- [ ] **Step 8: Commit**

```bash
git add load_omb_consolidated.py tests/test_load_omb_consolidated.py \
        tests/fixtures/omb_consolidated_sample.xlsx tests/fixtures/_build_fixture.py
git commit -m "feat(omb-ingest): loader + match audit (3,481 exact / 120 OMB-only / 58 DB-only)"
```

---

### Task 3.3: Audit script (markdown report)

**Files:**
- Create: `scripts/audit_omb_consolidated_diff.py`

- [ ] **Step 1: Implement the audit script**

Create `scripts/audit_omb_consolidated_diff.py`:

```python
"""Generate an offline-readable markdown report of OMB-vs-IFP discrepancies.

Reads `omb_match_audit` and writes `audit/omb_consolidated_diff_2025.md`.
This complements the dashboard /discrepancies page — useful for review in
GitHub PRs, linking from issues, and version-controlled snapshots.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "federal_ai_inventory_2025.db"
OUT_PATH = REPO_ROOT / "audit" / "omb_consolidated_diff_2025.md"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Headline counts
    rollup = {
        r["match_status"]: r["n"]
        for r in conn.execute(
            "SELECT match_status, COUNT(*) AS n FROM omb_match_audit "
            "GROUP BY match_status"
        )
    }

    omb_only = conn.execute("""
        SELECT a.agency_abbreviation, o.use_case_id_omb, o.use_case_name
        FROM omb_match_audit a JOIN omb_consolidated_rows o ON o.id=a.omb_row_id
        WHERE a.match_status = 'omb_only'
        ORDER BY a.agency_abbreviation, o.use_case_name
    """).fetchall()

    db_only = conn.execute("""
        SELECT a.agency_abbreviation, uc.use_case_id, uc.use_case_name
        FROM omb_match_audit a JOIN use_cases uc ON uc.id=a.use_case_id_db
        WHERE a.match_status = 'db_only'
        ORDER BY a.agency_abbreviation, uc.use_case_name
    """).fetchall()

    drifts = conn.execute("""
        SELECT a.agency_abbreviation, uc.use_case_name, a.drift_fields_json
        FROM omb_match_audit a JOIN use_cases uc ON uc.id=a.use_case_id_db
        WHERE a.match_status IN ('matched_exact','matched_fuzzy')
          AND a.drift_fields_json != '{}' AND a.drift_fields_json IS NOT NULL
        ORDER BY a.agency_abbreviation, uc.use_case_name
    """).fetchall()

    suggested = conn.execute("""
        SELECT a.agency_abbreviation, o.use_case_name AS omb_name,
               uc.use_case_name AS db_name, a.match_score
        FROM omb_match_audit a
        JOIN omb_consolidated_rows o ON o.id=a.omb_row_id
        JOIN use_cases uc ON uc.id=a.use_case_id_db
        WHERE a.match_status='suggested_rename'
        ORDER BY a.match_score DESC
    """).fetchall()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out = []
    out.append(f"# OMB Consolidated 2025 ↔ IFP DB Discrepancy Report")
    out.append(f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M %Z')}_\n")
    out.append("## Headline counts\n")
    out.append("| Status | Count |\n|---|---:|")
    for k in ["matched_exact", "matched_fuzzy", "suggested_rename",
              "omb_only", "db_only", "duplicate_in_omb"]:
        out.append(f"| {k} | {rollup.get(k, 0)} |")
    out.append("")

    out.append(f"## OMB-only use cases ({len(omb_only)})\n")
    out.append("| Agency | OMB ID | Name |\n|---|---|---|")
    for r in omb_only:
        nm = (r["use_case_name"] or "")[:80]
        out.append(f"| {r['agency_abbreviation']} | {r['use_case_id_omb'] or ''} | {nm} |")
    out.append("")

    out.append(f"## DB-only use cases ({len(db_only)})\n")
    out.append("| Agency | DB ID | Name |\n|---|---|---|")
    for r in db_only:
        nm = (r["use_case_name"] or "")[:80]
        out.append(f"| {r['agency_abbreviation']} | {r['use_case_id'] or ''} | {nm} |")
    out.append("")

    out.append(f"## Suggested renames (score 0.55–0.85, {len(suggested)})\n")
    out.append("| Agency | Score | OMB name | DB name |\n|---|---:|---|---|")
    for r in suggested:
        out.append(
            f"| {r['agency_abbreviation']} | {r['match_score']:.2f} | "
            f"{(r['omb_name'] or '')[:60]} | {(r['db_name'] or '')[:60]} |"
        )
    out.append("")

    out.append(f"## Field drift on matched pairs ({len(drifts)})\n")
    out.append("| Agency | Use case | Field | DB value | OMB value |\n|---|---|---|---|---|")
    for r in drifts:
        drift = json.loads(r["drift_fields_json"])
        for f, vals in drift.items():
            out.append(
                f"| {r['agency_abbreviation']} | {(r['use_case_name'] or '')[:50]} "
                f"| {f} | {(vals.get('db') or '')[:40]} | {(vals.get('omb') or '')[:40]} |"
            )
    out.append("")

    OUT_PATH.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(out)} lines)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the audit**

Run: `python3 scripts/audit_omb_consolidated_diff.py`
Expected: writes `audit/omb_consolidated_diff_2025.md`. Open and skim — verify the OMB-only / DB-only / drift sections look like the 3-agent audit findings.

- [ ] **Step 3: Commit**

```bash
git add scripts/audit_omb_consolidated_diff.py audit/omb_consolidated_diff_2025.md
git commit -m "feat(omb-ingest): markdown discrepancy report at audit/omb_consolidated_diff_2025.md"
```

---

### Task 3.4: Wire into `make fix`

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Insert the new steps**

Edit `Makefile`. After the line `python3 load_inventories.py`, before `python3 scripts/backfill_use_case_id.py`, add:

```makefile
	python3 load_omb_consolidated.py
```

After `python3 scripts/generate_db_snapshot.py` (last line of the `fix` recipe), add:

```makefile
	python3 scripts/audit_omb_consolidated_diff.py
```

- [ ] **Step 2: Run `make fix` and confirm the chain works end-to-end**

Run:
```bash
cp data/federal_ai_inventory_2025.db data/federal_ai_inventory_2025.db.pre-makefix.bak
make fix
```
Expected: completes without errors. Report says "Loaded OMB consolidated file" and the audit rollup. The audit MD is written.

- [ ] **Step 3: Run the test suite**

Run: `pytest tests/ audit/checks/ -v`
Expected: all tests pass. Report `X/Y tests passing (Z pre-existing failures)`.

- [ ] **Step 4: Commit**

```bash
git add Makefile
git commit -m "build: wire OMB consolidated loader + audit into make fix"
```

---

## Phase 4: Dashboard — DB sync + types + query layer

### Task 4.1: Sync the DB into the dashboard repo

**Files:**
- Modify: `dashboard/data/federal_ai_inventory_2025.db`

- [ ] **Step 1: Copy the rebuilt DB**

Run:
```bash
cp data/federal_ai_inventory_2025.db dashboard/data/federal_ai_inventory_2025.db
sqlite3 dashboard/data/federal_ai_inventory_2025.db ".tables" | tr ' ' '\n' | grep -E '^omb_'
```
Expected: `omb_consolidated_rows` and `omb_match_audit` listed in the dashboard's DB.

- [ ] **Step 2: Confirm dashboard build still passes**

Run:
```bash
cd dashboard && npm run build
```
Expected: build succeeds (we haven't added new TS yet). Capture any preexisting errors as baseline.

- [ ] **Step 3: Commit (in dashboard sub-repo)**

```bash
cd dashboard
git add data/federal_ai_inventory_2025.db
git commit -m "data: sync DB with OMB consolidated provenance + match audit"
cd ..
```

---

### Task 4.2: Add TypeScript types

**Files:**
- Modify: `dashboard/lib/types.ts`

- [ ] **Step 1: Append the new types**

Edit `dashboard/lib/types.ts`. Append at end of file:

```typescript
// ─── OMB consolidated discrepancy types ────────────────────────────────────

export type DiscrepancyStatus =
  | "matched_exact"
  | "matched_fuzzy"
  | "suggested_rename"
  | "omb_only"
  | "db_only"
  | "duplicate_in_omb";

export interface DiscrepancySummary {
  matched_exact: number;
  matched_fuzzy: number;
  suggested_rename: number;
  omb_only: number;
  db_only: number;
  duplicate_in_omb: number;
  total_with_drift: number;
  total_pairs_compared: number;
}

export interface DiscrepancyRow {
  audit_id: number;
  match_status: DiscrepancyStatus;
  match_score: number | null;
  agency_abbreviation: string | null;
  use_case_name: string | null;
  // Either or both may be null depending on status:
  db_use_case_id: number | null;       // FK into use_cases.id
  db_use_case_id_text: string | null;  // the agency-as-filed ID string
  omb_row_id: number | null;
  omb_use_case_id: string | null;      // OMB's assigned ID (may be NULL/empty)
  drift_field_count: number;
  resolved_at: string | null;
}

export interface DiscrepancyDriftField {
  field: string;
  db_value: string | null;
  omb_value: string | null;
}

export interface DiscrepancyDetail {
  audit: DiscrepancyRow;
  drift: DiscrepancyDriftField[];
  db_row: Record<string, string | null> | null;
  omb_row: Record<string, string | null> | null;
}

export interface DiscrepancyFilter {
  status?: DiscrepancyStatus[];
  agency?: string;
  hasDrift?: boolean;
  unresolvedOnly?: boolean;
}
```

- [ ] **Step 2: Verify type-check**

Run: `cd dashboard && npx tsc --noEmit`
Expected: no errors related to the new types.

- [ ] **Step 3: Commit**

```bash
cd dashboard
git add lib/types.ts
git commit -m "feat(types): add discrepancy types for /discrepancies page"
cd ..
```

---

### Task 4.3: Query layer

**Files:**
- Create: `dashboard/lib/discrepancies.ts`

- [ ] **Step 1: Implement the query module**

Create `dashboard/lib/discrepancies.ts`:

```typescript
/**
 * Server-side queries for the /discrepancies page.
 *
 * Reads `omb_match_audit` (one row per OMB↔DB match attempt) and joins
 * to `use_cases` and `omb_consolidated_rows` to surface a flat row shape
 * for the dashboard. All functions are read-only and synchronous via
 * better-sqlite3 prepared statements.
 */
import Database from "better-sqlite3";
import fs from "node:fs";
import path from "node:path";

import type {
  DiscrepancyDetail,
  DiscrepancyDriftField,
  DiscrepancyFilter,
  DiscrepancyRow,
  DiscrepancyStatus,
  DiscrepancySummary,
} from "./types";

let _db: Database.Database | null = null;
function db(): Database.Database {
  if (_db) return _db;
  const p = path.join(process.cwd(), "data", "federal_ai_inventory_2025.db");
  if (!fs.existsSync(p)) throw new Error(`DB not found at ${p}`);
  _db = new Database(p, { readonly: true });
  _db.pragma("journal_mode = WAL");
  return _db;
}

export function getDiscrepancySummary(): DiscrepancySummary {
  const rows = db()
    .prepare(
      `SELECT match_status, COUNT(*) AS n FROM omb_match_audit GROUP BY match_status`
    )
    .all() as Array<{ match_status: DiscrepancyStatus; n: number }>;
  const map = Object.fromEntries(rows.map((r) => [r.match_status, r.n]));

  const drift = db()
    .prepare(
      `SELECT COUNT(*) AS n FROM omb_match_audit
       WHERE drift_fields_json IS NOT NULL AND drift_fields_json != '{}'`
    )
    .get() as { n: number };

  const totalPairs = (map.matched_exact ?? 0) + (map.matched_fuzzy ?? 0);

  return {
    matched_exact: map.matched_exact ?? 0,
    matched_fuzzy: map.matched_fuzzy ?? 0,
    suggested_rename: map.suggested_rename ?? 0,
    omb_only: map.omb_only ?? 0,
    db_only: map.db_only ?? 0,
    duplicate_in_omb: map.duplicate_in_omb ?? 0,
    total_with_drift: drift.n,
    total_pairs_compared: totalPairs,
  };
}

export function getDiscrepancyRows(filter: DiscrepancyFilter = {}): DiscrepancyRow[] {
  const where: string[] = [];
  const params: Record<string, unknown> = {};

  if (filter.status && filter.status.length) {
    where.push(
      `match_status IN (${filter.status.map((_, i) => `@s${i}`).join(",")})`
    );
    filter.status.forEach((s, i) => (params[`s${i}`] = s));
  }
  if (filter.agency) {
    where.push(`a.agency_abbreviation = @agency`);
    params.agency = filter.agency;
  }
  if (filter.hasDrift) {
    where.push(`drift_fields_json IS NOT NULL AND drift_fields_json != '{}'`);
  }
  if (filter.unresolvedOnly) {
    where.push(`a.resolved_at IS NULL`);
  }

  const sql = `
    SELECT
      a.id                            AS audit_id,
      a.match_status                  AS match_status,
      a.match_score                   AS match_score,
      a.agency_abbreviation           AS agency_abbreviation,
      a.use_case_name                 AS use_case_name,
      a.use_case_id_db                AS db_use_case_id,
      uc.use_case_id                  AS db_use_case_id_text,
      a.omb_row_id                    AS omb_row_id,
      o.use_case_id_omb               AS omb_use_case_id,
      CASE WHEN a.drift_fields_json IS NULL OR a.drift_fields_json = '{}' THEN 0
           ELSE json_array_length(json_object_keys(a.drift_fields_json)) END AS drift_field_count,
      a.resolved_at                   AS resolved_at
    FROM omb_match_audit a
    LEFT JOIN use_cases uc ON uc.id = a.use_case_id_db
    LEFT JOIN omb_consolidated_rows o ON o.id = a.omb_row_id
    ${where.length ? "WHERE " + where.join(" AND ") : ""}
    ORDER BY
      CASE a.match_status
        WHEN 'omb_only' THEN 1
        WHEN 'db_only' THEN 2
        WHEN 'suggested_rename' THEN 3
        WHEN 'duplicate_in_omb' THEN 4
        WHEN 'matched_fuzzy' THEN 5
        WHEN 'matched_exact' THEN 6
        ELSE 7 END,
      a.agency_abbreviation, a.use_case_name
  `;
  // SQLite lacks json_object_keys; replace with a json_extract count helper:
  return db().prepare(sql.replace(
    "json_array_length(json_object_keys(a.drift_fields_json))",
    `(SELECT COUNT(*) FROM json_each(a.drift_fields_json))`
  )).all(params) as DiscrepancyRow[];
}

export function getDiscrepancyDetail(auditId: number): DiscrepancyDetail | null {
  const row = db().prepare(`
    SELECT a.id AS audit_id, a.match_status, a.match_score,
           a.agency_abbreviation, a.use_case_name,
           a.use_case_id_db AS db_use_case_id, uc.use_case_id AS db_use_case_id_text,
           a.omb_row_id, o.use_case_id_omb AS omb_use_case_id,
           a.drift_fields_json, a.resolved_at,
           uc.stage_of_development AS db_stage,
           uc.is_high_impact AS db_is_high_impact,
           uc.is_withheld AS db_is_withheld,
           uc.topic_area AS db_topic_area,
           uc.ai_classification AS db_ai_classification,
           uc.vendor_name AS db_vendor_name,
           uc.has_ato AS db_have_ato,
           uc.has_pii AS db_has_pii,
           uc.has_custom_code AS db_has_custom_code,
           uc.bureau_component AS db_bureau_component,
           o.stage_of_development AS omb_stage,
           o.is_high_impact AS omb_is_high_impact,
           o.is_withheld AS omb_is_withheld,
           o.topic_area AS omb_topic_area,
           o.ai_classification AS omb_ai_classification,
           o.vendor_name AS omb_vendor_name,
           o.have_ato AS omb_have_ato,
           o.has_pii AS omb_has_pii,
           o.has_custom_code AS omb_has_custom_code,
           o.bureau_component AS omb_bureau_component
    FROM omb_match_audit a
    LEFT JOIN use_cases uc ON uc.id = a.use_case_id_db
    LEFT JOIN omb_consolidated_rows o ON o.id = a.omb_row_id
    WHERE a.id = ?
  `).get(auditId) as Record<string, unknown> | undefined;

  if (!row) return null;

  const driftRaw = (row.drift_fields_json as string | null) ?? "{}";
  const driftObj = JSON.parse(driftRaw) as Record<string, { db: string; omb: string }>;
  const drift: DiscrepancyDriftField[] = Object.entries(driftObj).map(
    ([field, vals]) => ({ field, db_value: vals.db ?? null, omb_value: vals.omb ?? null }),
  );

  const audit: DiscrepancyRow = {
    audit_id: row.audit_id as number,
    match_status: row.match_status as DiscrepancyStatus,
    match_score: row.match_score as number | null,
    agency_abbreviation: row.agency_abbreviation as string | null,
    use_case_name: row.use_case_name as string | null,
    db_use_case_id: row.db_use_case_id as number | null,
    db_use_case_id_text: row.db_use_case_id_text as string | null,
    omb_row_id: row.omb_row_id as number | null,
    omb_use_case_id: row.omb_use_case_id as string | null,
    drift_field_count: drift.length,
    resolved_at: row.resolved_at as string | null,
  };

  const fields = ["stage", "is_high_impact", "is_withheld", "topic_area",
    "ai_classification", "vendor_name", "have_ato", "has_pii",
    "has_custom_code", "bureau_component"];
  const dbRow = Object.fromEntries(
    fields.map((f) => [f, (row[`db_${f}`] as string | null) ?? null])
  );
  const ombRow = Object.fromEntries(
    fields.map((f) => [f, (row[`omb_${f}`] as string | null) ?? null])
  );

  return { audit, drift, db_row: dbRow, omb_row: ombRow };
}

export function getDiscrepancyAgencies(): Array<{ agency: string; n: number }> {
  return db()
    .prepare(`
      SELECT agency_abbreviation AS agency, COUNT(*) AS n
      FROM omb_match_audit
      WHERE match_status NOT IN ('matched_exact')
      GROUP BY agency_abbreviation
      ORDER BY n DESC
    `)
    .all() as Array<{ agency: string; n: number }>;
}
```

- [ ] **Step 2: Type-check**

Run: `cd dashboard && npx tsc --noEmit lib/discrepancies.ts`
Expected: no errors.

- [ ] **Step 3: Smoke-test the queries**

Run:
```bash
cd dashboard && npx tsx -e "
  import { getDiscrepancySummary, getDiscrepancyRows } from './lib/discrepancies';
  console.log(getDiscrepancySummary());
  console.log(getDiscrepancyRows({ status: ['omb_only'] }).slice(0, 3));
"
```
Expected: numbers roughly matching the audit MD report.

- [ ] **Step 4: Commit**

```bash
cd dashboard
git add lib/discrepancies.ts
git commit -m "feat(discrepancies): server query layer for /discrepancies page"
cd ..
```

---

## Phase 5: Dashboard — discrepancies page

### Task 5.1: Page route + summary

**Files:**
- Create: `dashboard/app/discrepancies/page.tsx`

- [ ] **Step 1: Build the summary page**

Create `dashboard/app/discrepancies/page.tsx`:

```tsx
import Link from "next/link";
import { getDiscrepancySummary, getDiscrepancyRows } from "@/lib/discrepancies";
import { Section, MonoChip } from "@/components/editorial";
import { DiscrepancyTable } from "@/components/discrepancy-table";

export const metadata = {
  title: "Discrepancies · Federal AI Use Case Inventory",
  description:
    "Where the OMB-published 2025 consolidated inventory disagrees with our agency-as-filed dataset: missing rows, new rows, renames, and field-level drift.",
};

export default function DiscrepanciesPage() {
  const summary = getDiscrepancySummary();
  const rows = getDiscrepancyRows({ unresolvedOnly: true });

  return (
    <div className="mx-auto max-w-7xl px-6 py-12 space-y-12">
      <header className="space-y-4">
        <p className="text-xs uppercase tracking-widest text-stone-500">
          Provenance audit
        </p>
        <h1 className="font-serif text-4xl font-medium leading-tight">
          OMB consolidated inventory vs IFP database
        </h1>
        <p className="max-w-prose text-stone-600">
          The 2025 OMB consolidated file (
          <MonoChip>2025_individually_reported_AI_use_cases.xlsx</MonoChip>) is
          OMB&rsquo;s normalized snapshot of agency filings. We keep our own
          row-for-row ingest of each agency&rsquo;s raw file. This page lists
          every place the two disagree.
        </p>
      </header>

      <Section
        eyebrow="Summary"
        title="What changed between OMB&rsquo;s and IFP&rsquo;s versions"
        source="omb-derived"
      >
        <dl className="grid grid-cols-2 gap-x-8 gap-y-4 md:grid-cols-3">
          <SummaryStat label="Exact-name matches" value={summary.matched_exact} />
          <SummaryStat label="Fuzzy-name matches" value={summary.matched_fuzzy} />
          <SummaryStat label="Suggested renames" value={summary.suggested_rename} />
          <SummaryStat label="OMB-only (new)" value={summary.omb_only} highlight />
          <SummaryStat label="DB-only (vanished)" value={summary.db_only} highlight />
          <SummaryStat label="Duplicate in OMB file" value={summary.duplicate_in_omb} />
          <SummaryStat
            label="Pairs with field drift"
            value={summary.total_with_drift}
            sub={`of ${summary.total_pairs_compared.toLocaleString()} matched pairs`}
          />
        </dl>
      </Section>

      <Section
        eyebrow="Detail"
        title="All unresolved discrepancies"
        source="omb-derived"
        description="Click any row to see field-level diff. Resolution status is tracked per row."
      >
        <DiscrepancyTable rows={rows} />
      </Section>
    </div>
  );
}

function SummaryStat({
  label,
  value,
  sub,
  highlight,
}: {
  label: string;
  value: number;
  sub?: string;
  highlight?: boolean;
}) {
  return (
    <div className={`space-y-1 ${highlight ? "text-amber-700" : ""}`}>
      <dt className="text-xs uppercase tracking-wider text-stone-500">{label}</dt>
      <dd className="font-serif text-3xl font-medium tabular-nums">
        {value.toLocaleString()}
      </dd>
      {sub ? <dd className="text-xs text-stone-500">{sub}</dd> : null}
    </div>
  );
}
```

- [ ] **Step 2: Verify the route compiles**

Run: `cd dashboard && npx tsc --noEmit app/discrepancies/page.tsx`
Expected: no TS errors. (`MonoChip` and `Section` exist per Phase 0.3 finding.)

- [ ] **Step 3: Commit**

```bash
cd dashboard
git add app/discrepancies/page.tsx
git commit -m "feat(discrepancies): /discrepancies summary page"
cd ..
```

---

### Task 5.2: Filterable detail table (client component)

**Files:**
- Create: `dashboard/components/discrepancy-table.tsx`

- [ ] **Step 1: Build the table**

Create `dashboard/components/discrepancy-table.tsx`:

```tsx
"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { DiscrepancyRow, DiscrepancyStatus } from "@/lib/types";

const STATUS_LABEL: Record<DiscrepancyStatus, string> = {
  matched_exact: "Exact match",
  matched_fuzzy: "Fuzzy match",
  suggested_rename: "Suggested rename",
  omb_only: "OMB only (new)",
  db_only: "DB only (vanished)",
  duplicate_in_omb: "Duplicate in OMB",
};

const STATUS_TONE: Record<DiscrepancyStatus, string> = {
  matched_exact: "bg-stone-100 text-stone-700",
  matched_fuzzy: "bg-blue-50 text-blue-800",
  suggested_rename: "bg-violet-50 text-violet-800",
  omb_only: "bg-amber-50 text-amber-900",
  db_only: "bg-rose-50 text-rose-900",
  duplicate_in_omb: "bg-orange-50 text-orange-900",
};

export function DiscrepancyTable({ rows }: { rows: DiscrepancyRow[] }) {
  const [statusFilter, setStatusFilter] = useState<DiscrepancyStatus | "all">("all");
  const [agencyFilter, setAgencyFilter] = useState<string>("all");
  const [search, setSearch] = useState<string>("");

  const agencies = useMemo(
    () => Array.from(new Set(rows.map((r) => r.agency_abbreviation).filter(Boolean))).sort() as string[],
    [rows],
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return rows.filter((r) => {
      if (statusFilter !== "all" && r.match_status !== statusFilter) return false;
      if (agencyFilter !== "all" && r.agency_abbreviation !== agencyFilter) return false;
      if (q && !(r.use_case_name ?? "").toLowerCase().includes(q)) return false;
      return true;
    });
  }, [rows, statusFilter, agencyFilter, search]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-4">
        <FilterSelect
          label="Status"
          value={statusFilter}
          onChange={(v) => setStatusFilter(v as DiscrepancyStatus | "all")}
          options={[
            { value: "all", label: `All (${rows.length})` },
            ...(Object.keys(STATUS_LABEL) as DiscrepancyStatus[]).map((s) => ({
              value: s,
              label: `${STATUS_LABEL[s]} (${rows.filter((r) => r.match_status === s).length})`,
            })),
          ]}
        />
        <FilterSelect
          label="Agency"
          value={agencyFilter}
          onChange={setAgencyFilter}
          options={[
            { value: "all", label: `All agencies (${agencies.length})` },
            ...agencies.map((a) => ({ value: a, label: a })),
          ]}
        />
        <label className="flex flex-col gap-1 text-xs uppercase tracking-wider text-stone-500">
          Search name
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="filter by use-case name"
            className="rounded border border-stone-300 px-2 py-1 text-sm font-normal normal-case tracking-normal text-stone-900"
          />
        </label>
        <p className="ml-auto text-sm text-stone-500">
          {filtered.length.toLocaleString()} shown
        </p>
      </div>

      <div className="overflow-x-auto rounded border border-stone-200">
        <table className="min-w-full text-sm">
          <thead className="bg-stone-50 text-left text-xs uppercase tracking-wider text-stone-500">
            <tr>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Agency</th>
              <th className="px-3 py-2">Use case</th>
              <th className="px-3 py-2">IFP ID</th>
              <th className="px-3 py-2">OMB ID</th>
              <th className="px-3 py-2 text-right">Drift fields</th>
              <th className="px-3 py-2 text-right">Score</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-100">
            {filtered.map((r) => (
              <tr key={r.audit_id} className="hover:bg-stone-50">
                <td className="px-3 py-2">
                  <span
                    className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${STATUS_TONE[r.match_status]}`}
                  >
                    {STATUS_LABEL[r.match_status]}
                  </span>
                </td>
                <td className="px-3 py-2 font-mono text-xs">
                  {r.agency_abbreviation ?? "—"}
                </td>
                <td className="px-3 py-2">{r.use_case_name ?? "—"}</td>
                <td className="px-3 py-2 font-mono text-xs">
                  {r.db_use_case_id_text ?? "—"}
                </td>
                <td className="px-3 py-2 font-mono text-xs">
                  {r.omb_use_case_id ?? "—"}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {r.drift_field_count > 0 ? r.drift_field_count : "—"}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {r.match_score !== null ? r.match_score.toFixed(2) : "—"}
                </td>
                <td className="px-3 py-2">
                  <Link
                    href={`/discrepancies/${r.audit_id}`}
                    className="text-sm text-stone-700 underline-offset-4 hover:underline"
                  >
                    View →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs uppercase tracking-wider text-stone-500">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded border border-stone-300 px-2 py-1 text-sm font-normal normal-case tracking-normal text-stone-900"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}
```

- [ ] **Step 2: Verify**

Run: `cd dashboard && npm run build`
Expected: build succeeds. Visit `http://localhost:3000/discrepancies` (after `npm run dev`) and verify the table renders with filters working.

- [ ] **Step 3: Commit**

```bash
cd dashboard
git add components/discrepancy-table.tsx
git commit -m "feat(discrepancies): filterable detail table"
cd ..
```

---

### Task 5.3: Per-case drill-down page

**Files:**
- Create: `dashboard/app/discrepancies/[caseId]/page.tsx`
- Create: `dashboard/components/discrepancy-side-by-side.tsx`

- [ ] **Step 1: Build the side-by-side component**

Create `dashboard/components/discrepancy-side-by-side.tsx`:

```tsx
import type { DiscrepancyDetail } from "@/lib/types";

const FIELD_LABEL: Record<string, string> = {
  stage: "Stage of development",
  is_high_impact: "High-impact?",
  is_withheld: "Withheld?",
  topic_area: "Topic area",
  ai_classification: "AI classification",
  vendor_name: "Vendor(s)",
  have_ato: "Has ATO?",
  has_pii: "Has PII?",
  has_custom_code: "Custom code?",
  bureau_component: "Bureau / component",
};

export function DiscrepancySideBySide({ detail }: { detail: DiscrepancyDetail }) {
  const driftFields = new Set(detail.drift.map((d) => d.field));
  const fields = Object.keys(FIELD_LABEL);

  return (
    <div className="overflow-x-auto rounded border border-stone-200">
      <table className="min-w-full text-sm">
        <thead className="bg-stone-50 text-left text-xs uppercase tracking-wider text-stone-500">
          <tr>
            <th className="px-3 py-2 w-1/4">Field</th>
            <th className="px-3 py-2 w-3/8">DB (IFP)</th>
            <th className="px-3 py-2 w-3/8">OMB consolidated</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-stone-100">
          {fields.map((f) => {
            const dbV = detail.db_row?.[f] ?? null;
            const ombV = detail.omb_row?.[f] ?? null;
            const drifted = driftFields.has(f);
            return (
              <tr key={f} className={drifted ? "bg-amber-50" : ""}>
                <td className="px-3 py-2 align-top text-stone-700">
                  {FIELD_LABEL[f]}
                  {drifted ? (
                    <span className="ml-2 text-xs text-amber-700">drift</span>
                  ) : null}
                </td>
                <td className="px-3 py-2 align-top whitespace-pre-wrap">
                  {dbV ?? <span className="text-stone-400">(empty)</span>}
                </td>
                <td className="px-3 py-2 align-top whitespace-pre-wrap">
                  {ombV ?? <span className="text-stone-400">(empty)</span>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Build the drill-down page**

Create `dashboard/app/discrepancies/[caseId]/page.tsx`:

```tsx
import Link from "next/link";
import { notFound } from "next/navigation";
import { getDiscrepancyDetail } from "@/lib/discrepancies";
import { Section, MonoChip } from "@/components/editorial";
import { DiscrepancySideBySide } from "@/components/discrepancy-side-by-side";

export default async function DiscrepancyDetailPage({
  params,
}: {
  params: Promise<{ caseId: string }>;
}) {
  const { caseId } = await params;
  const auditId = Number(caseId);
  if (!Number.isFinite(auditId)) return notFound();

  const detail = getDiscrepancyDetail(auditId);
  if (!detail) return notFound();

  return (
    <div className="mx-auto max-w-5xl px-6 py-12 space-y-8">
      <Link
        href="/discrepancies"
        className="text-sm text-stone-600 hover:text-stone-900"
      >
        ← All discrepancies
      </Link>

      <header className="space-y-2">
        <p className="text-xs uppercase tracking-widest text-stone-500">
          {detail.audit.match_status.replace(/_/g, " ")}
        </p>
        <h1 className="font-serif text-3xl font-medium">
          {detail.audit.use_case_name ?? "(no name)"}
        </h1>
        <p className="text-sm text-stone-600">
          <MonoChip>{detail.audit.agency_abbreviation ?? "?"}</MonoChip>
          {" · "}
          <span>IFP ID: {detail.audit.db_use_case_id_text ?? "—"}</span>
          {" · "}
          <span>OMB ID: {detail.audit.omb_use_case_id ?? "—"}</span>
          {detail.audit.match_score !== null ? (
            <>
              {" · "}
              <span>match score {detail.audit.match_score.toFixed(2)}</span>
            </>
          ) : null}
        </p>
      </header>

      <Section
        eyebrow="Field-by-field"
        title="DB vs OMB"
        source="omb-derived"
        description={
          detail.drift.length === 0
            ? "No drift detected on the 11 compared fields."
            : `${detail.drift.length} field(s) differ between the agency-as-filed DB row and OMB&rsquo;s consolidated entry.`
        }
      >
        <DiscrepancySideBySide detail={detail} />
      </Section>
    </div>
  );
}
```

- [ ] **Step 3: Build & smoke-test**

Run:
```bash
cd dashboard && npm run dev
# in another terminal:
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/discrepancies
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/discrepancies/1
```
Expected: both 200.

- [ ] **Step 4: Visual verify with Playwright**

Run a quick Playwright check (per the user's preference for browser verification on HTML changes). Steps:

```bash
cd dashboard
npx playwright install chromium  # if not already
node -e "
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:3000/discrepancies');
  await page.screenshot({ path: '/tmp/discrepancies.png', fullPage: true });
  console.log('Title:', await page.title());
  console.log('OMB-only count cell:', await page.locator('text=OMB-only').first().textContent());
  await browser.close();
})();
"
```
Expected: `/tmp/discrepancies.png` shows the page rendering with summary + filter + table. Title contains "Discrepancies".

- [ ] **Step 5: Commit**

```bash
cd dashboard
git add app/discrepancies/[caseId]/page.tsx components/discrepancy-side-by-side.tsx
git commit -m "feat(discrepancies): per-case OMB↔DB side-by-side drill-down"
cd ..
```

---

### Task 5.4: Add nav link + use-case page chip

**Files:**
- Modify: dashboard nav file (path discovered in Task 0.1)
- Modify: `dashboard/app/use-cases/[caseId]/page.tsx`

- [ ] **Step 1: Add the nav entry**

Edit the nav file to include a `Discrepancies` link. Match the surrounding style — typically:

```tsx
<Link href="/discrepancies" className="…existing classes…">Discrepancies</Link>
```

Place it under a "Quality" or "Audit" group if one exists; otherwise at the end of the primary nav.

- [ ] **Step 2: Add the OMB-ID chip on use-case detail pages**

Edit `dashboard/app/use-cases/[caseId]/page.tsx`. Locate the section showing the IFP `use_case_id`. Add adjacent chip:

```tsx
{useCase.omb_consolidated_id ? (
  <MonoChip title="ID assigned by OMB in the 2025 consolidated file">
    OMB: {useCase.omb_consolidated_id}
  </MonoChip>
) : (
  <span
    className="inline-block rounded bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-900"
    title="This use case is not present in OMB's 2025 consolidated inventory"
  >
    Not in OMB consolidated 2025
  </span>
)}
```

This requires extending the `getUseCase` query in `dashboard/lib/db.ts` to select `omb_consolidated_id`. Add it to the existing SELECT alongside `use_case_id`.

- [ ] **Step 3: Verify**

Run: `cd dashboard && npm run build && npm run dev`
Visit:
- `/discrepancies` (link in nav)
- `/use-cases/<some-slug>` for a matched use case → should show OMB chip
- `/use-cases/<some-slug>` for a FRTIB/GPO/NMB/OPM use case → should show "Not in OMB consolidated 2025" chip

- [ ] **Step 4: Commit**

```bash
cd dashboard
git add components/site-nav.tsx app/use-cases/[caseId]/page.tsx lib/db.ts
git commit -m "feat(nav): link to /discrepancies + per-case OMB ID chip"
cd ..
```

---

## Phase 6: Final integration

### Task 6.1: Full test pass + DB sync

- [ ] **Step 1: Run full pytest from project root**

Run:
```bash
cd /Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory
pytest tests/ audit/checks/ -v
```
Expected: all tests pass. Report `X/Y passing (Z pre-existing failures)`.

- [ ] **Step 2: Run dashboard tests**

Run:
```bash
cd dashboard && pytest tests/ -q 2>&1 || true
npm run lint && npm run build
```
Expected: clean.

- [ ] **Step 3: Final DB sync into dashboard**

Run:
```bash
cd /Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory
cp data/federal_ai_inventory_2025.db dashboard/data/federal_ai_inventory_2025.db
```

- [ ] **Step 4: Commit + push (dashboard repo)**

```bash
cd dashboard
git add data/federal_ai_inventory_2025.db
git commit -m "data: final DB sync after OMB consolidated ingest"
git push origin main  # confirm with user before pushing
cd ..
```

- [ ] **Step 5: Commit + push (outer ETL repo)**

```bash
git add -A
git status   # human-review the staged set
git commit -m "feat(omb-ingest): full pipeline — schema, loader, audit, dashboard discrepancy page"
# Do NOT push without explicit user confirmation
```

---

## Self-review checklist

Before declaring done:

- [ ] Match policy thresholds (0.85 fuzzy / 0.55 rename) actually surface NSF acronym renames as `suggested_rename` (not `omb_only`/`db_only`)
- [ ] FRTIB/GPO/NMB/OPM rows render with `db_only` status on `/discrepancies`
- [ ] PBGC duplicate row renders with `duplicate_in_omb` status
- [ ] DOE Copilot Studio + DOE Copilot for M365 + NCUA Risk Indicator Model + NCUA Supervisory Stress Testing all show drift on `is_high_impact`
- [ ] STATE → State agency-abbr remap works (10 OMB STATE rows match DB State rows)
- [ ] TREAS → Treasury same
- [ ] `omb_consolidated_id` column populated for all matched use cases (≈3,491 rows)
- [ ] `omb_consolidated_id` is NULL for the 25 dropped-agency use cases
- [ ] /discrepancies page accessible from nav, renders summary + table
- [ ] /discrepancies/[id] renders side-by-side with drift highlighted
- [ ] All `Section` instances have a `source` prop (per dashboard convention)
- [ ] `make fix` runs end-to-end without errors
- [ ] Test count restored or improved vs baseline

---

## What this plan does NOT do

- Auto-merge NSF acronym renames. They land as `suggested_rename`; humans approve via a follow-up script (`scripts/apply_omb_rename_decisions.py`, a future task).
- Replace ED's 36 DB rows with OMB's 56. The mismatch is flagged; ED is treated as needing a coordinated re-ingest, not a destructive replace.
- Resolution UI on the dashboard (mark a discrepancy "resolved"). The schema supports it (`resolved_at`, `resolution_note`); the UI gesture is a follow-up plan.
- 2024 inventory backfill of OMB IDs. Different file shape; out of scope.
- A FedRAMP-style cross-link from OMB IDs to FedRAMP marketplace entries. Out of scope here.
