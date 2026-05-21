"""Tests for match_year_over_year — the 2024↔2025 deterministic matcher.

Two layers, mirroring `tests/test_omb_consolidated_match.py`:
  - pure-function unit tests for `narrative_match_score`;
  - matcher-integration tests against an in-memory SQLite DB with a small
    fixture spanning every lineage_status, plus the reconciliation
    invariant, the queue CSV, and idempotency.
"""
import sqlite3

import match_year_over_year
from match_year_over_year import match
from migrations.m011_use_case_year_links import apply as apply_m011
from omb_consolidated_match import (
    NARRATIVE_MATCH_THRESHOLD,
    name_containment_score,
    name_match_score,
    narrative_match_score,
    normalize_name,
)


# ── Pure-function: narrative_match_score ──────────────────────────────────


def test_narrative_match_score_identical_is_one():
    text = "the system automates document review to reduce manual effort"
    assert narrative_match_score(text, text) == 1.0


def test_narrative_match_score_disjoint_is_zero():
    a = "predicts wildfire spread from satellite imagery"
    b = "translates passport applications into multiple languages"
    assert narrative_match_score(a, b) == 0.0


def test_narrative_match_score_reordered_clauses_is_high():
    """Jaccard's strength: clause reordering / light rewording barely moves
    a token-set score, unlike difflib's character ratio."""
    a = "reduce manual effort by automating invoice classification tasks"
    b = "automating invoice classification tasks to reduce manual effort"
    assert narrative_match_score(a, b) >= 0.9


def test_narrative_match_score_empty_is_zero():
    assert narrative_match_score("", "anything here") == 0.0
    assert narrative_match_score("anything here", "") == 0.0
    assert narrative_match_score(None, None) == 0.0


def test_narrative_match_score_partial_overlap_is_fractional():
    a = "automated document summarization for case files"
    b = "automated document summarization for legal briefs and memos"
    score = narrative_match_score(a, b)
    assert 0.0 < score < 1.0


# ── Pure-function: narrative containment (length-asymmetry fix) ───────────
#
# 2025 systematically lengthened narratives (3 fields vs 2024's 2). When the
# 2024 text is a clean *subset* of the longer 2025 text, plain Jaccard
# (|A∩B| / |A∪B|) dilutes below threshold even at verbatim identity. The
# fix: narrative_match_score returns max(jaccard, containment).


def test_narrative_match_score_verbatim_subset_scores_above_threshold():
    """A 2024 narrative that is a verbatim subset of a longer 2025 narrative
    must now score >= the narrative threshold — this was the systematic miss
    (DOI link 5581, NSF link 7244)."""
    text_2024 = (
        "forecast seasonal water supply volumes across western river basins "
        "using statistical regression models calibrated on snowpack data"
    )
    # 2025 keeps every 2024 token verbatim, then appends a third field.
    text_2025 = (
        text_2024
        + " the model also produces probabilistic exceedance curves and "
        "delivers monthly updated forecasts to reservoir operators and "
        "regional planning offices throughout the runoff season"
    )
    score = narrative_match_score(text_2024, text_2025)
    # Plain Jaccard would land well under 0.50 here; containment rescues it.
    assert score >= NARRATIVE_MATCH_THRESHOLD
    assert score == 1.0  # 2024 set fully contained → containment == 1.0


def test_narrative_match_score_subset_beats_plain_jaccard():
    """Containment must lift the score strictly above what plain Jaccard
    alone would give for a length-asymmetric subset pair."""
    short = "predict wildfire ignition risk from weather sensor telemetry"
    long = (
        short + " aggregated regionally and surfaced through an interactive "
        "dashboard with alerting thresholds reviewed by incident commanders"
    )
    ta = set(short.lower().split())
    tb = set(long.lower().split())
    plain_jaccard = len(ta & tb) / len(ta | tb)
    assert narrative_match_score(short, long) > plain_jaccard


def test_narrative_match_score_tiny_generic_set_does_not_spuriously_match():
    """Guard: a tiny generic 2024 narrative (< 5 substantive tokens) sitting
    verbatim inside a long unrelated 2025 narrative must NOT score 1.0 — the
    containment fallback is gated by the absolute-intersection floor."""
    tiny = "uses ai to help users"  # 'ai'/'to'/'use*' are stopwords → 1 token
    long_unrelated = (
        "uses ai to help users navigate complex passport renewal workflows "
        "by classifying scanned identity documents and routing them to the "
        "correct adjudication queue within the consular processing system"
    )
    score = narrative_match_score(tiny, long_unrelated)
    # Falls back to plain Jaccard (intersection below the floor), which is
    # heavily diluted by the long side → well below threshold.
    assert score < NARRATIVE_MATCH_THRESHOLD


def test_narrative_match_score_tiny_subset_does_not_promote():
    """Regression: the DOJ false-positive failure mode. A tiny 2025
    narrative (a 2-6-word problem_statement, near-empty benefits/outputs)
    whose handful of substantive tokens are a clean subset of a long,
    *unrelated* 2024 paragraph must NOT containment-promote — its
    intersection cannot reach the absolute-intersection floor, so it falls
    back to (heavily diluted) plain Jaccard and stays below threshold.

    Models DOJ link 17538-and-kin: e.g. ServiceNow IT-helpdesk wrongly
    linked to a tiny "Entity Extraction and Summarization" 2025 row."""
    # Tiny 2025-style narrative: 3 substantive tokens (data, triage, faster).
    tiny_2025 = "data triage faster operations"
    # Long unrelated 2024 paragraph that happens to contain all 3 tokens.
    long_2024_unrelated = (
        "the platform automates information technology helpdesk request "
        "intake by classifying incident tickets and routing them faster to "
        "the correct support queue so analysts can triage operations and "
        "resolve common data requests without manual escalation overhead"
    )
    score = narrative_match_score(tiny_2025, long_2024_unrelated)
    # Intersection is only 3 tokens — below _CONTAINMENT_MIN_INTERSECTION —
    # so containment never fires; the score must stay well under threshold.
    assert score < NARRATIVE_MATCH_THRESHOLD


def test_narrative_match_score_thin_stub_smaller_side_does_not_promote():
    """Guard 2: a one-line 2025 stub whose substantive tokens clear the
    intersection floor but whose *whole* token set is still thin (a padded
    one-liner) must NOT containment-promote — the smaller-side floor blocks
    it. Models the OBR Indexing false positive, whose 13-token 2025 side
    shared 8 tokens with a long unrelated 2024 narrative (|A∩B| tied the
    genuine VA HTM-LLM recovery, so the intersection floor alone could not
    separate them)."""
    # 2025 stub: 13 substantive tokens, 8 of which appear in the 2024 text.
    thin_2025 = (
        "searchable index of all records associated with distinct "
        "individuals supporting faster resolution"
    )
    long_2024_unrelated = (
        "the system improves firearm tracing efficiency by recognizing the "
        "structure of scanned forms and converting designated pixel data "
        "into a limited searchable index of records that points processors "
        "to potential responsive records associated with individuals while "
        "complying with statutory restrictions for faster resolution of all "
        "crime gun trace requests submitted by out of business licensees"
    )
    score = narrative_match_score(thin_2025, long_2024_unrelated)
    # Intersection >= 6 but the smaller side (13) is below the smaller-side
    # floor → containment is suppressed, plain Jaccard stays below threshold.
    assert score < NARRATIVE_MATCH_THRESHOLD


def test_narrative_match_score_genuine_low_overlap_still_promotes():
    """Counterpart: a genuine rename with real bilateral narrative content —
    both sides substantive, intersection above the floor — must still
    containment-promote. Models the VA HTM-LLM → HTM112 Tutor recovery
    (8 shared distinctive tokens, smaller side 15)."""
    # Smaller 2024 side: 15 substantive tokens of real domain content.
    narr_2024 = (
        "retrieval augmented generation chatbot using technical service "
        "manuals to aid healthcare technology management staff in medical "
        "device maintenance troubleshooting and produce chatbot responses"
    )
    # Longer 2025 side reusing the distinctive domain vocabulary.
    narr_2025 = (
        "the healthcare technology management tutor is built on a "
        "retrieval augmented generation platform that delivers conversational "
        "chatbot responses to support technical troubleshooting questions "
        "for healthcare technology management staff completing maintenance "
        "tasks across the medical device portfolio with verified citations"
    )
    score = narrative_match_score(narr_2024, narr_2025)
    assert score >= NARRATIVE_MATCH_THRESHOLD


# ── Pure-function: name containment + bracketed-tag stripping ─────────────


def test_name_containment_distinctive_single_word_matches():
    """A distinctive one-word 2024 name that is a token-subset of a longer
    2025 title must containment-match (DOI 5493 'PyForecast')."""
    score = name_containment_score(
        "PyForecast",
        "Seasonal Water Supply Forecasting: Pyforecast [2024 INV#DOI-69]",
    )
    assert score == 1.0  # single distinctive token, fully contained


def test_name_containment_generic_stub_does_not_match():
    """A generic stub whose only tokens are stopwords/short must NOT
    containment-match into a long unrelated title."""
    # "AI Tool" → both tokens are stopwords → empty substantive set → 0.0
    assert name_containment_score(
        "AI Tool", "Enterprise Document Processing Tool for Claims Review"
    ) == 0.0


def test_name_containment_unchanged_name_match_score():
    """name_match_score itself must stay difflib-only — containment is a
    separate signal, other callers depend on the original behavior."""
    # Distinct strings: containment may be high, but name_match_score's
    # difflib ratio for a short subset of a long string stays low.
    s = name_match_score(
        "PyForecast",
        "Seasonal Water Supply Forecasting: Pyforecast",
    )
    assert s < 0.85


def test_normalize_name_strips_bracketed_inv_tag():
    """Bracketed [2024 INV#...] provenance tags are matching noise — they
    must be stripped (tolerant of casing and the optional space)."""
    assert normalize_name("Pyforecast [2024 INV#DOI-69]") == "pyforecast"
    assert normalize_name("Tool [2024 Inv# WO0000000111250]") == "tool"
    # An identical pair where only one side carries the tag now matches.
    assert name_match_score(
        "Liable Party Research",
        "Liable Party Research [2024 INV#WO0000000110496]",
    ) == 1.0
    # A non-INV bracket is left intact (not a provenance tag).
    assert normalize_name("Chatbot (v2) [pilot]") == "chatbot (v2) [pilot]"


# ── Matcher integration ───────────────────────────────────────────────────


def _bootstrap_db() -> sqlite3.Connection:
    """In-memory DB with the minimal schema the matcher touches."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE agencies (id INTEGER PRIMARY KEY, name TEXT, "
        "abbreviation TEXT)"
    )
    conn.execute(
        """
        CREATE TABLE use_cases (
            id INTEGER PRIMARY KEY,
            agency_id INTEGER,
            use_case_name TEXT,
            problem_statement TEXT,
            expected_benefits TEXT,
            system_outputs TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE use_cases_2024 (
            id INTEGER PRIMARY KEY,
            agency_id INTEGER,
            use_case_name TEXT,
            purpose_benefits TEXT,
            outputs TEXT
        )
        """
    )
    apply_m011(conn)
    return conn


def _seed_fixture(conn: sqlite3.Connection) -> None:
    """A small fixture spanning every lineage_status.

    Agency 1 (TEST):
      - exact-name pair                → continued
      - fuzzy-rename pair              → renamed (fuzzy_name)
      - narrative-only rename          → renamed (narrative)
      - 2024-only row                  → retired_2024
      - 2025-only row                  → new_2025
      - ambiguous [0.40,0.85)          → suggested_rename
      - length-asymmetry containment   → renamed (the systematic-miss case:
        2024 name + narrative are a clean verbatim subset of the longer
        2025 ones; difflib ratio / plain Jaccard would miss it).
    """
    conn.execute(
        "INSERT INTO agencies(id, name, abbreviation) VALUES (1, 'Test', 'TEST')"
    )

    # 2024 rows -----------------------------------------------------------
    conn.executemany(
        "INSERT INTO use_cases_2024(id, agency_id, use_case_name, "
        "purpose_benefits, outputs) VALUES (?, ?, ?, ?, ?)",
        [
            # exact-name pair
            (1, 1, "Customer Service Chatbot",
             "answer common questions", "chat replies"),
            # fuzzy-rename pair (tiny edit → high difflib ratio)
            (2, 1, "Fraud Detection Model",
             "detect fraudulent claims", "risk scores"),
            # narrative-only rename: name is unrelated, narrative overlaps
            (3, 1, "Project Falcon",
             "predict equipment failure from sensor telemetry data streams",
             "maintenance alerts and failure probability estimates"),
            # 2024-only → retired_2024
            (4, 1, "Legacy Mainframe Optimizer",
             "tune batch job scheduling", "schedule tables"),
            # ambiguous pair: combined name score in [0.40, 0.85) and no
            # clean token containment (so it stays a suggested_rename, not
            # a fuzzy match), narratives too sparse for the narrative stage.
            (5, 1, "Translation Tool",
             "translate documents", "translated text"),
            # length-asymmetry containment: short distinctive 2024 name +
            # narrative are a verbatim subset of a much longer 2025 row.
            (6, 1, "PyForecast",
             "forecast seasonal water supply volumes across western river "
             "basins using statistical regression models calibrated on "
             "mountain snowpack measurements",
             "monthly volumetric runoff forecasts"),
        ],
    )

    # 2025 rows -----------------------------------------------------------
    conn.executemany(
        "INSERT INTO use_cases(id, agency_id, use_case_name, "
        "problem_statement, expected_benefits, system_outputs) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            # exact-name counterpart of 2024 id 1
            (10, 1, "Customer Service Chatbot",
             "answer common questions", "faster service", "chat replies"),
            # fuzzy-rename counterpart of 2024 id 2
            (11, 1, "Fraud Detection Models",
             "detect fraudulent claims", "less loss", "risk scores"),
            # narrative-only counterpart of 2024 id 3 — name fully unrelated
            (12, 1, "Predictive Maintenance Platform",
             "predict equipment failure from sensor telemetry data streams",
             "reduced downtime",
             "maintenance alerts and failure probability estimates"),
            # 2025-only → new_2025
            (13, 1, "Brand New Generative Assistant",
             "draft policy memos", "save staff time", "draft documents"),
            # ambiguous counterpart of 2024 id 5: character-overlap with
            # "Translation Tool" but no shared whole token, so combined
            # name score lands mid-band (~0.67) → suggested_rename.
            (14, 1, "Translator Toolkit Service",
             "review machine translation quality",
             "better accuracy", "quality reports"),
            # containment counterpart of 2024 id 6: 2025 lengthened the
            # title (acronym → full name) and stamped a [2024 INV#...] tag;
            # the narrative keeps every 2024 token then adds a third field.
            (15, 1,
             "Seasonal Water Supply Forecasting: Pyforecast [2024 INV#DOI-69]",
             "forecast seasonal water supply volumes across western river "
             "basins using statistical regression models calibrated on "
             "mountain snowpack measurements",
             "monthly volumetric runoff forecasts delivered to reservoir "
             "operators and regional planning offices",
             "probabilistic exceedance curves and updated forecast tables"),
        ],
    )
    conn.commit()


def test_matcher_assigns_every_lineage_status(monkeypatch, tmp_path):
    monkeypatch.setattr(
        match_year_over_year, "QUEUE_CSV", tmp_path / "year_match_queue.csv"
    )
    conn = _bootstrap_db()
    _seed_fixture(conn)
    match(conn)

    def status_of_2024(uc_id):
        return conn.execute(
            "SELECT lineage_status FROM use_case_year_links WHERE uc_2024_id=?",
            (uc_id,),
        ).fetchone()[0]

    assert status_of_2024(1) == "continued"
    assert status_of_2024(2) == "renamed"
    assert status_of_2024(3) == "renamed"
    assert status_of_2024(4) == "retired_2024"
    assert status_of_2024(5) == "suggested_rename"
    # length-asymmetry containment case: a verbatim subset must now link
    # (was the systematic miss — would land in retired_2024 before the fix).
    assert status_of_2024(6) == "renamed"
    # it links to the lengthened 2025 row id 15.
    assert conn.execute(
        "SELECT uc_2025_id FROM use_case_year_links WHERE uc_2024_id=6"
    ).fetchone()[0] == 15

    # 2025-only row 13 must be new_2025 with no 2024 partner.
    new_row = conn.execute(
        "SELECT lineage_status, uc_2024_id FROM use_case_year_links "
        "WHERE uc_2025_id=13"
    ).fetchone()
    assert new_row[0] == "new_2025"
    assert new_row[1] is None

    # match_method wired correctly per stage.
    assert conn.execute(
        "SELECT match_method FROM use_case_year_links WHERE uc_2024_id=1"
    ).fetchone()[0] == "exact_name"
    assert conn.execute(
        "SELECT match_method FROM use_case_year_links WHERE uc_2024_id=2"
    ).fetchone()[0] == "fuzzy_name"
    assert conn.execute(
        "SELECT match_method FROM use_case_year_links WHERE uc_2024_id=3"
    ).fetchone()[0] == "narrative"


def test_matcher_reconciliation_invariant(monkeypatch, tmp_path):
    monkeypatch.setattr(
        match_year_over_year, "QUEUE_CSV", tmp_path / "year_match_queue.csv"
    )
    conn = _bootstrap_db()
    _seed_fixture(conn)
    match(conn)

    n_2024 = conn.execute("SELECT COUNT(*) FROM use_cases_2024").fetchone()[0]
    n_2025 = conn.execute("SELECT COUNT(*) FROM use_cases").fetchone()[0]

    linked_2024 = conn.execute(
        "SELECT COUNT(*) FROM use_case_year_links WHERE uc_2024_id IS NOT NULL"
    ).fetchone()[0]
    distinct_2024 = conn.execute(
        "SELECT COUNT(DISTINCT uc_2024_id) FROM use_case_year_links "
        "WHERE uc_2024_id IS NOT NULL"
    ).fetchone()[0]
    linked_2025 = conn.execute(
        "SELECT COUNT(*) FROM use_case_year_links WHERE uc_2025_id IS NOT NULL"
    ).fetchone()[0]
    distinct_2025 = conn.execute(
        "SELECT COUNT(DISTINCT uc_2025_id) FROM use_case_year_links "
        "WHERE uc_2025_id IS NOT NULL"
    ).fetchone()[0]

    assert linked_2024 == distinct_2024 == n_2024
    assert linked_2025 == distinct_2025 == n_2025


def test_matcher_queue_csv_contains_ambiguous_pair(monkeypatch, tmp_path):
    queue_csv = tmp_path / "year_match_queue.csv"
    monkeypatch.setattr(match_year_over_year, "QUEUE_CSV", queue_csv)
    conn = _bootstrap_db()
    _seed_fixture(conn)
    match(conn)

    assert queue_csv.exists()
    import csv as _csv
    with queue_csv.open(encoding="utf-8") as fh:
        rows = list(_csv.DictReader(fh))

    # exactly the one ambiguous pair (2024 id 5 ↔ 2025 id 14).
    assert len(rows) == 1
    assert rows[0]["uc_2024_id"] == "5"
    assert rows[0]["uc_2025_id"] == "14"
    assert rows[0]["lineage_status"] == "suggested_rename"

    # CSV row count must equal the suggested_rename count in the table.
    n_suggested = conn.execute(
        "SELECT COUNT(*) FROM use_case_year_links "
        "WHERE lineage_status='suggested_rename'"
    ).fetchone()[0]
    assert len(rows) == n_suggested


def test_matcher_idempotent_preserves_first_seen(monkeypatch, tmp_path):
    monkeypatch.setattr(
        match_year_over_year, "QUEUE_CSV", tmp_path / "year_match_queue.csv"
    )
    conn = _bootstrap_db()
    _seed_fixture(conn)

    match(conn)
    count_1 = conn.execute(
        "SELECT COUNT(*) FROM use_case_year_links"
    ).fetchone()[0]
    first_seen_1 = conn.execute(
        "SELECT first_seen FROM use_case_year_links WHERE uc_2024_id=1"
    ).fetchone()[0]

    match(conn)
    count_2 = conn.execute(
        "SELECT COUNT(*) FROM use_case_year_links"
    ).fetchone()[0]
    first_seen_2 = conn.execute(
        "SELECT first_seen FROM use_case_year_links WHERE uc_2024_id=1"
    ).fetchone()[0]

    assert count_1 == count_2
    assert first_seen_1 == first_seen_2


def test_matcher_does_not_match_across_agencies(monkeypatch, tmp_path):
    """A 2024 row and an identically-named 2025 row at *different* agencies
    must never link — matching is strictly per-agency."""
    monkeypatch.setattr(
        match_year_over_year, "QUEUE_CSV", tmp_path / "year_match_queue.csv"
    )
    conn = _bootstrap_db()
    conn.execute(
        "INSERT INTO agencies(id, name, abbreviation) VALUES (1, 'A', 'A')"
    )
    conn.execute(
        "INSERT INTO agencies(id, name, abbreviation) VALUES (2, 'B', 'B')"
    )
    conn.execute(
        "INSERT INTO use_cases_2024(id, agency_id, use_case_name, "
        "purpose_benefits, outputs) VALUES (1, 1, 'Shared Name', 'x', 'y')"
    )
    conn.execute(
        "INSERT INTO use_cases(id, agency_id, use_case_name, "
        "problem_statement, expected_benefits, system_outputs) "
        "VALUES (10, 2, 'Shared Name', 'x', '', 'y')"
    )
    conn.commit()
    match(conn)

    # 2024 row is retired (no same-agency partner); 2025 row is new.
    assert conn.execute(
        "SELECT lineage_status FROM use_case_year_links WHERE uc_2024_id=1"
    ).fetchone()[0] == "retired_2024"
    assert conn.execute(
        "SELECT lineage_status FROM use_case_year_links WHERE uc_2025_id=10"
    ).fetchone()[0] == "new_2025"
