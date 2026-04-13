"""LLM-vs-non-LLM classification checks.

Source: audit/consistency/03_llm_vs_non_llm_classification.md
Baseline: audit/baselines/2026-04-12-pre-remediation.json
  - llm_false_positives_confirmed: 88
  - breakdown: classical_ml=63, computer_vision=25

Canonical LLM false-positive definition (matches the baseline and
scripts/generate_remediation_report.py):
  is_general_llm_access = 1
  AND source ai_classification names a non-LLM category
      (Classical/Predictive ML or Computer Vision)

THIS IS A BASELINE-LOOSE SCAFFOLD.

Phase 2 Agent B owns this check and will tighten the threshold from <=120
down to <=10 once the LLM tagging logic is corrected. Until then we just
ratchet against the current state so a tagging regression (e.g. someone
re-broadens the LLM bucket and explodes false positives) trips the alarm.
"""


def _llm_fp(conn, ai_class_pattern):
    """Count rows with is_general_llm_access=1 where ai_classification matches pattern."""
    sql = """
        SELECT COUNT(*)
        FROM use_cases u
        JOIN use_case_tags t ON t.use_case_id = u.id
        WHERE t.is_general_llm_access = 1
          AND u.ai_classification LIKE ?
    """
    return conn.execute(sql, (ai_class_pattern,)).fetchone()[0]


def test_llm_false_positives_under_loose_ceiling(conn):
    """Combined classical-ML + computer-vision false-positive count.

    Baseline: 88 (classical_ml=63, computer_vision=25). Allow up to 120;
    Agent B drops this to <=10 after re-tagging.
    """
    sql = """
        SELECT COUNT(*) FROM use_cases u
        JOIN use_case_tags t ON t.use_case_id = u.id
        WHERE t.is_general_llm_access = 1
          AND (u.ai_classification LIKE '%Classical%'
               OR u.ai_classification LIKE '%Predictive%'
               OR u.ai_classification LIKE '%Computer Vision%')
    """
    total = conn.execute(sql).fetchone()[0]
    assert total <= 120, (
        f"LLM false positives (classical/predictive + computer_vision) = {total} "
        f"(baseline 88); ceiling 120 - tagging regression suspected"
    )


def test_classical_ml_llm_tagged_under_loose_ceiling(conn):
    """Classical/Predictive ML rows incorrectly tagged as LLM.

    Baseline: 63. Phase 2 target: <=5.
    """
    sql = """
        SELECT COUNT(*) FROM use_cases u
        JOIN use_case_tags t ON t.use_case_id = u.id
        WHERE t.is_general_llm_access = 1
          AND (u.ai_classification LIKE '%Classical%'
               OR u.ai_classification LIKE '%Predictive%')
    """
    n = conn.execute(sql).fetchone()[0]
    assert n <= 80, (
        f"classical/predictive rows tagged as LLM = {n} "
        f"(baseline 63); ceiling 80 - regression suspected"
    )


def test_computer_vision_llm_tagged_under_loose_ceiling(conn):
    """Computer Vision rows incorrectly tagged as LLM.

    Baseline: 25. Phase 2 target: <=5.
    """
    n = _llm_fp(conn, "%Computer Vision%")
    assert n <= 45, (
        f"computer_vision rows tagged as LLM = {n} "
        f"(baseline 25); ceiling 45 - regression suspected"
    )
