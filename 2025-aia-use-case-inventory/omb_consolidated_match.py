"""Pure-function match policy for OMB consolidated rows ↔ DB use_cases.

The policy: normalize agency abbreviations (STATE→State, TREAS→Treasury),
normalize use-case names (lowercase, whitespace-collapse, curly-quote
straightening, ampersand-to-and), score with difflib SequenceMatcher,
and classify into a fixed status enum.

Drift detection canonicalizes leading letter prefixes (`a) Pre-deployment`
→ `Pre-deployment`) and curly apostrophes before comparing — the same
normalizations OMB applies during their consolidation.

This module is pure-function: no DB, no I/O, no global state. Phase 3
(loader) and Phase 5 (dashboard) both call into it so DB-rendered drift
and OMB-file drift never disagree on canonicalization.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable

# Threshold tuning notes (calibrated against Python stdlib difflib.SequenceMatcher
# — note: agent audit numbers used rapidfuzz which scores higher; difflib is
# stricter on length-imbalanced strings):
#   ≥ 0.85 → matched_fuzzy (DOI/HHS minor edits; near-identical names)
#   0.40–0.85 → suggested_rename (catches NSF-style acronym expansions like
#               "TIP MS Copilot Pilot" ↔ "Technology, Innovation and
#               Partnerships (TIP) Microsoft (MS) Copilot Pilot" ≈ 0.43)
#   < 0.40 → unmatched (omb_only or db_only)
# Loaders may apply tighter per-agency thresholds when noisy renames are a concern.
FUZZY_MATCH_THRESHOLD = 0.85
SUGGESTED_RENAME_THRESHOLD = 0.40


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
    status: str
    score: float | None
    method: str


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
            if db_v or omb_v:
                out[f] = {"db": db_v, "omb": omb_v}
    return out
