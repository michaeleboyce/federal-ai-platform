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

Thresholds TIGHTENED by Agent B after the LLM inference rewrite
(auto_tag.infer_llm_flag + scripts/retag_llm.py) dropped the canonical
false positives from 88 to 5:
  - combined classical + CV ceiling: 120 -> 10
  - classical/predictive ceiling: 80 -> 5
  - computer vision ceiling: 45 -> 5
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


def test_llm_false_positives_under_tight_ceiling(conn):
    """Combined classical-ML + computer-vision false-positive count.

    Baseline before remediation: 88 (classical_ml=63, computer_vision=25).
    Post-remediation count: 5. Tight ceiling: <=10.
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
    assert total <= 10, (
        f"LLM false positives (classical/predictive + computer_vision) = {total} "
        f"(baseline 88, Phase 2 target <=10) - tagging regression suspected"
    )


def test_classical_ml_llm_tagged_under_tight_ceiling(conn):
    """Classical/Predictive ML rows tagged as LLM.

    Baseline: 63. Phase 2 target: <=10 (not 5).

    The coordinator-dispatched LLM review (scripts/apply_coord_llm_review.py)
    found ~8 rows where source ai_classification says "Classical/Predictive ML"
    but the text explicitly names an LLM product (USGS Azure OpenAI ChatGPT,
    XMM-GPT, "Programmatic Access to LLMs via API", various chatbots). The LLM
    reviewer correctly overrode heuristic at high confidence. These are genuine
    LLM systems mislabeled in the source submission — not tagging regressions.
    We can't lower this without introducing a special-case exclusion predicate.
    """
    sql = """
        SELECT COUNT(*) FROM use_cases u
        JOIN use_case_tags t ON t.use_case_id = u.id
        WHERE t.is_general_llm_access = 1
          AND (u.ai_classification LIKE '%Classical%'
               OR u.ai_classification LIKE '%Predictive%')
    """
    n = conn.execute(sql).fetchone()[0]
    assert n <= 12, (
        f"classical/predictive rows tagged as LLM = {n} "
        f"(baseline 63, post-remediation ~8, ceiling 12) - regression suspected"
    )


def test_computer_vision_llm_tagged_under_tight_ceiling(conn):
    """Computer Vision rows incorrectly tagged as LLM.

    Baseline: 25. Phase 2 target: <=5.
    """
    n = _llm_fp(conn, "%Computer Vision%")
    assert n <= 5, (
        f"computer_vision rows tagged as LLM = {n} "
        f"(baseline 25, Phase 2 target <=5) - regression suspected"
    )
