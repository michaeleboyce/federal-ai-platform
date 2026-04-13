"""LLM-vs-non-LLM classification checks.

Source: audit/consistency/03_llm_vs_non_llm_classification.md
Baseline: audit/baselines/2026-04-12-pre-remediation.json
  - llm_false_positives_confirmed: 88
  - breakdown: classical_ml=63, computer_vision=25

THIS IS A BASELINE-LOOSE SCAFFOLD.

Phase 2 Agent B owns this check and will tighten the threshold from <=120
down to <=10 once the LLM tagging logic is corrected. Until then we just
ratchet against the current state so a tagging regression (e.g. someone
re-broadens the LLM bucket and explodes false positives) trips the alarm.
"""


def _llm_classified_as(conn, ai_class_pattern):
    """Count rows tagged as general_llm where source ai_classification is X."""
    sql = """
        SELECT COUNT(*)
        FROM use_cases u
        JOIN use_case_tags t ON t.use_case_id = u.id
        WHERE t.ai_sophistication = 'general_llm'
          AND u.ai_classification LIKE ?
    """
    return conn.execute(sql, (ai_class_pattern,)).fetchone()[0]


def test_llm_false_positives_under_loose_ceiling(conn):
    """Combined classical-ML + computer-vision false-positive count.

    Baseline strict count (general_llm + classical/CV classification) ~= 76.
    Audit-narrative count was 88. We allow up to 120 for now; Agent B will
    drop this to <=10 after re-tagging.
    """
    classical = _llm_classified_as(conn, "%Classical/Predictive Machine Learning%")
    cv = _llm_classified_as(conn, "%Computer Vision%")
    total = classical + cv
    assert total <= 120, (
        f"LLM false positives (classical_ml + computer_vision) = {total} "
        f"(baseline ~88, current ~76); ceiling 120 - tagging regression suspected. "
        f"Breakdown: classical_ml={classical}, computer_vision={cv}"
    )


def test_classical_ml_llm_tagged_under_loose_ceiling(conn):
    """Classical/Predictive ML rows incorrectly tagged general_llm.

    Baseline narrative: 63. Strict query: 57. Phase 2 target: <=5.
    """
    n = _llm_classified_as(conn, "%Classical/Predictive Machine Learning%")
    assert n <= 80, (
        f"classical_ml rows tagged general_llm = {n} "
        f"(baseline 63, current ~57); ceiling 80 - regression suspected"
    )


def test_computer_vision_llm_tagged_under_loose_ceiling(conn):
    """Computer Vision rows incorrectly tagged general_llm.

    Baseline narrative: 25. Strict query: 19. Phase 2 target: <=5.
    """
    n = _llm_classified_as(conn, "%Computer Vision%")
    assert n <= 45, (
        f"computer_vision rows tagged general_llm = {n} "
        f"(baseline 25, current ~19); ceiling 45 - regression suspected"
    )
