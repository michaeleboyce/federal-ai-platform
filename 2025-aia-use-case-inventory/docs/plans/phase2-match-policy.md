# Phase 2 — Match policy module `omb_consolidated_match.py`

## Context

Phase 1 added the schema substrate. Phase 2 adds the *pure-function decision logic* that the loader (Phase 3) will use to classify each OMB row against the DB. Keeping it pure-function and isolated has two payoffs:

1. **Testable in milliseconds.** No DB, no XLSX, no I/O — just `(input_a, input_b) -> classification`. The 11 tests below run in <50 ms.
2. **Reusable across phases.** Phase 3 (loader), Phase 5 (dashboard drift display), and any future audit script all call the same `detect_drift()` and get the same canonicalization, so DB-rendered drift and OMB-file drift never disagree because of a normalization mismatch.

The thresholds in this module (0.85 fuzzy / 0.55 rename) come straight from the 3-agent audit:
- 0.85 captures the 10 fuzzy-rename cases at DOI/HHS (minor wording tweaks)
- 0.55 captures NSF's acronym expansions (e.g., "TIP MS Copilot Pilot" ↔ "Technology, Innovation and Partnerships (TIP) Microsoft (MS) Copilot Pilot" ≈ 0.62)

## Files to create

| Path | Responsibility |
|---|---|
| `omb_consolidated_match.py` | Pure-function module: `normalize_agency`, `normalize_name`, `name_match_score`, `classify_match`, `detect_drift`, `MatchResult` dataclass, threshold constants, drift-fields tuple. |
| `tests/test_omb_consolidated_match.py` | 11 unit tests covering all public functions + the canonicalization edge cases (curly apostrophes, letter prefixes, ampersand). |

## Public surface

```python
FUZZY_MATCH_THRESHOLD: float = 0.85
SUGGESTED_RENAME_THRESHOLD: float = 0.55
DRIFT_FIELDS_DEFAULT: tuple[str, ...] = (
    "stage_of_development", "is_high_impact", "is_withheld",
    "topic_area", "ai_classification", "contracting_usage",
    "vendor_name", "have_ato", "has_pii", "has_custom_code",
    "bureau_component",
)

@dataclass(frozen=True)
class MatchResult:
    status: str    # 'matched_exact' | 'matched_fuzzy' | 'suggested_rename' | 'omb_only' | 'db_only'
    score: float | None
    method: str    # 'exact_name' | 'fuzzy_name' | 'none'

def normalize_agency(abbr: str | None) -> str | None
def normalize_name(s: str | None) -> str
def name_match_score(a: str | None, b: str | None) -> float
def classify_match(score: float | None, *, db_present: bool, omb_present: bool) -> MatchResult
def detect_drift(db_row: dict, omb_row: dict, *, fields: Iterable[str] = DRIFT_FIELDS_DEFAULT) -> dict[str, dict[str, str]]
```

## Execution steps (TDD)

1. Write `tests/test_omb_consolidated_match.py` with 11 tests (see larger plan section "Task 2.1").
2. Run `pytest tests/test_omb_consolidated_match.py -v`. Expect ImportError.
3. Implement `omb_consolidated_match.py` per the larger plan section.
4. Run tests, expect 11/11 PASS.
5. Run full suite, target **102/109 passing** (+11 from Phase 1's 91/98, 7 pre-existing carry forward).
6. Commit.

## Verification

Phase 2 is complete when:

1. `pytest tests/test_omb_consolidated_match.py -v` shows 11/11 PASS.
2. Full suite reports 102/109 (7 pre-existing failures, no new regressions).
3. `omb_consolidated_match.py` lives at the repo root (alongside `auto_tag.py`, `load_inventories.py`, etc. — same level as the other top-level ETL modules) so the loader in Phase 3 can `from omb_consolidated_match import …` without path gymnastics.

## What this phase does NOT do

- No DB I/O — the module never touches sqlite.
- No XLSX parsing — that's Phase 3.
- No `omb_consolidated_id` writes — that's Phase 3.
- No CLI, no `__main__` block — pure library module.
