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


# ---------------------------------------------------------------------------
# Absolute rebuild-drift bands (2026-07 Phase-0 baseline).
#
# The ceilings above catch category-level false positives; these bands catch
# the other failure mode — auto_tag.py re-broadening (or re-narrowing) a flag
# wholesale while the Makefile correction chain (retag_llm.py + apply_*
# scripts, Makefile ~L46-62) silently fails to re-apply. The queries are
# copied verbatim from scripts/build_article_factsheet.py so the gated number
# is the same number the article cites.


def test_general_llm_access_band(conn):
    """Headline general-LLM count (distinct individual entries).

    Baseline 559 (2026-07-06, post completeness pass: 476 at Phase 0
    + 83 from the 66 loader-recovered + 45 OMB-ingested rows, which are
    heavily generic-LLM tools — the name-collision bug specifically
    dropped same-named Copilot/Chatbot filings). Band ±50. If this trips
    after an intentional retag pass, re-baseline in the same commit.
    """
    n = conn.execute(
        """SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
            WHERE is_general_llm_access = 1 AND use_case_id IS NOT NULL"""
    ).fetchone()[0]
    assert 509 <= n <= 609, (
        f"general-LLM distinct individual count = {n} (baseline 559, "
        "band 509-609) — auto_tag drift or a correction script dropped out "
        "of the make fix chain"
    )


def test_general_llm_access_total_band(conn):
    """All is_general_llm_access tag rows (individual + consolidated).

    Baseline 789 (2026-07-06, post completeness pass — see the distinct
    band above for the delta accounting). Band ±50.
    """
    n = conn.execute(
        "SELECT SUM(is_general_llm_access) FROM use_case_tags"
    ).fetchone()[0]
    assert 739 <= n <= 839, (
        f"general-LLM total tag rows = {n} (baseline 789, band "
        "739-839) — auto_tag drift or a correction script dropped out of "
        "the make fix chain"
    )


def test_agentic_sophistication_band(conn):
    """Agentic-by-IFP-tag count (fact-sheet query).

    Baseline 66 (2026-07-06, post completeness pass: 59 at Phase 0 + 7
    from recovered/ingested rows). Band ±10. NOTE: the +7 are auto_tag
    heuristic labels that never went through the agentic capability
    review (audit/retag/agentic_review/) — flagged as follow-up in
    audit/omb_only_ingest/ADJUDICATION.md.
    """
    n = conn.execute(
        """SELECT COUNT(DISTINCT use_case_id) FROM use_case_tags
            WHERE ai_sophistication = 'agentic' AND use_case_id IS NOT NULL"""
    ).fetchone()[0]
    assert 56 <= n <= 76, (
        f"agentic sophistication count = {n} (baseline 66, band "
        "56-76) — apply_agentic_review/apply_capability_reviews may have "
        "dropped out of the make fix chain"
    )
