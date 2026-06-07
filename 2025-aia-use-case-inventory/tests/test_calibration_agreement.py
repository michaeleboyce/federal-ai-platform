"""Tests for scripts/calibration_agreement.py — pairwise agreement math
+ deployment_scope tier-shift collapse rule."""
import sqlite3

from migrations import m009_use_cases_2024 as m009
from migrations import m014_use_case_tags_2024 as m014
from scripts.calibration_agreement import (
    SCOPE_TIERS,
    _values_agree,
    compute_agreement,
)


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.execute(
        "CREATE TABLE agencies (id INTEGER PRIMARY KEY, "
        "abbreviation TEXT, full_name TEXT)"
    )
    c.execute("INSERT INTO agencies(id, abbreviation) VALUES (1, 'HHS')")
    m009.apply(c)
    m014.apply(c)
    for i in range(1, 5):
        c.execute(
            "INSERT INTO use_cases_2024 (id, agency_id, source_file, slug, "
            "use_case_name) VALUES (?, 1, 'x', ?, ?)",
            (i, f"row{i}", f"Row {i}"),
        )
    return c


def _ins(c, uc, agent, **fields):
    cols = ["use_case_id_2024", "wave", "tagged_by_agent"] + list(fields.keys())
    vals = [uc, "0-calibration", agent] + list(fields.values())
    ph = ",".join(["?"] * len(cols))
    c.execute(
        f"INSERT INTO use_case_tags_2024 ({','.join(cols)}) VALUES ({ph})",
        vals,
    )


# --- _values_agree / scope tier collapse ---------------------------------

def test_scope_adjacent_tiers_agree():
    assert _values_agree("deployment_scope", "bureau", "office")
    assert _values_agree("deployment_scope", "office", "team")


def test_scope_two_tier_shift_disagrees():
    assert not _values_agree("deployment_scope", "bureau", "team")
    assert not _values_agree("deployment_scope", "enterprise_wide", "office")


def test_scope_same_tier_agrees():
    assert _values_agree("deployment_scope", "bureau", "bureau")


def test_other_fields_use_strict_equality():
    assert _values_agree("is_generative_ai", 1, 1)
    assert not _values_agree("is_generative_ai", 1, 0)
    assert _values_agree("entry_type", "custom_system", "custom_system")
    assert not _values_agree("entry_type", "custom_system", "product_deployment")


def test_missing_value_is_disagreement():
    assert not _values_agree("entry_type", None, "custom_system")
    assert not _values_agree("entry_type", "custom_system", None)


# --- compute_agreement aggregate ------------------------------------------

def test_perfect_agreement_two_agents_four_rows():
    c = _conn()
    for uc in range(1, 5):
        _ins(c, uc, "A", entry_type="custom_system",
             is_generative_ai=1, ai_sophistication="general_llm",
             deployment_scope="bureau")
        _ins(c, uc, "B", entry_type="custom_system",
             is_generative_ai=1, ai_sophistication="general_llm",
             deployment_scope="bureau")
    rows = c.execute(
        "SELECT use_case_id_2024, tagged_by_agent, is_generative_ai, "
        "ai_sophistication, entry_type, deployment_scope "
        "FROM use_case_tags_2024 WHERE wave='0-calibration'"
    ).fetchall()
    agg = compute_agreement(rows)
    for field, results in agg["field_results"].items():
        for (a, b), (agree, total, pct) in results.items():
            assert pct == 1.0, f"{field}: {a}/{b} not 100%"


def test_partial_disagreement():
    c = _conn()
    # 4 rows, 2 agents. Disagree on entry_type for 1 of 4 rows.
    _ins(c, 1, "A", entry_type="custom_system")
    _ins(c, 1, "B", entry_type="custom_system")
    _ins(c, 2, "A", entry_type="custom_system")
    _ins(c, 2, "B", entry_type="custom_system")
    _ins(c, 3, "A", entry_type="custom_system")
    _ins(c, 3, "B", entry_type="custom_system")
    _ins(c, 4, "A", entry_type="custom_system")
    _ins(c, 4, "B", entry_type="product_deployment")
    rows = c.execute(
        "SELECT use_case_id_2024, tagged_by_agent, is_generative_ai, "
        "ai_sophistication, entry_type, deployment_scope "
        "FROM use_case_tags_2024 WHERE wave='0-calibration'"
    ).fetchall()
    agg = compute_agreement(rows)
    pct = agg["field_results"]["entry_type"][("A", "B")][2]
    assert abs(pct - 0.75) < 1e-9


def test_scope_tier_collapse_applies_in_aggregate():
    c = _conn()
    # A says bureau, B says office (adjacent tier) → counts as agreement.
    _ins(c, 1, "A", deployment_scope="bureau")
    _ins(c, 1, "B", deployment_scope="office")
    rows = c.execute(
        "SELECT use_case_id_2024, tagged_by_agent, is_generative_ai, "
        "ai_sophistication, entry_type, deployment_scope "
        "FROM use_case_tags_2024 WHERE wave='0-calibration'"
    ).fetchall()
    agg = compute_agreement(rows)
    pct = agg["field_results"]["deployment_scope"][("A", "B")][2]
    assert pct == 1.0


def test_top_divergent_ranks_by_field_disagreement_count():
    c = _conn()
    # Row 1: agents disagree on 3 fields. Row 2: agents disagree on 1.
    _ins(c, 1, "A", entry_type="custom_system",
         is_generative_ai=1, ai_sophistication="general_llm",
         deployment_scope="bureau")
    _ins(c, 1, "B", entry_type="product_deployment",
         is_generative_ai=0, ai_sophistication="classical_ml",
         deployment_scope="bureau")
    _ins(c, 2, "A", entry_type="custom_system",
         is_generative_ai=1, ai_sophistication="general_llm",
         deployment_scope="bureau")
    _ins(c, 2, "B", entry_type="custom_system",
         is_generative_ai=1, ai_sophistication="general_llm",
         deployment_scope="team")  # 2-tier shift = disagreement
    rows = c.execute(
        "SELECT use_case_id_2024, tagged_by_agent, is_generative_ai, "
        "ai_sophistication, entry_type, deployment_scope "
        "FROM use_case_tags_2024 WHERE wave='0-calibration'"
    ).fetchall()
    agg = compute_agreement(rows)
    top = agg["top_divergent"]
    assert top[0] == (1, 3)
    assert top[1] == (2, 1)


def test_scope_tiers_are_six_ordered_levels():
    assert SCOPE_TIERS == {
        "enterprise_wide": 0,
        "department": 1,
        "bureau": 2,
        "office": 3,
        "team": 4,
        "pilot": 5,
    }
