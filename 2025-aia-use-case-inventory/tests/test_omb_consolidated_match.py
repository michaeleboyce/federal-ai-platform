"""Tests for omb_consolidated_match — pure-function match policy."""
from omb_consolidated_match import (
    classify_match,
    detect_drift,
    name_match_score,
    normalize_agency,
    normalize_name,
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
    """NSF acronym-expansion case must score above the suggested_rename floor
    (0.40) but below matched_fuzzy (0.85). Unrelated strings score < 0.40.
    """
    s = name_match_score(
        "TIP MS Copilot Pilot",
        "Technology, Innovation and Partnerships (TIP) Microsoft (MS) Copilot Pilot",
    )
    assert 0.40 <= s < 0.85
    assert name_match_score("Foo", "Bar") < 0.40


def test_classify_match_below_rename_floor_is_omb_only_when_omb_present():
    """Score < SUGGESTED_RENAME_THRESHOLD should not promote to suggested_rename."""
    r = classify_match(score=0.30, db_present=True, omb_present=True)
    assert r.status in ("omb_only", "db_only")


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
    assert drift == {}


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
