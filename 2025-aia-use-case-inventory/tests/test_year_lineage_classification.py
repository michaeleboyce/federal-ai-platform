"""Tests for the Phase-4 year-match adjudication scaffolding.

Three layers, mirroring `tests/test_match_year_over_year.py`:
  - integrate: agent recommendation JSONs → proposed_lineage.csv; conflict
    detection routes a contested slug to conflicts.csv.
  - apply: each decision `action` mutates use_case_year_links correctly;
    idempotent (apply twice → stable); the ≥1 reconciliation invariant
    holds including split/merge; the retired cross-check fires.
  - drift: directly-comparable field drift detected; recoded-field drift
    flagged `lossy`; split/merged/retired/new links carry no drift.

Stage 1 has no real agent output — every test builds a tiny in-memory DB
plus synthetic recommendations.json / proposed_lineage.csv and exercises
the code paths directly. The scripts also no-op cleanly with no agent
output, which is asserted here too.
"""
from __future__ import annotations

import json
import sqlite3

import compute_year_lineage_drift
from migrations.m011_use_case_year_links import apply as apply_m011
import pytest

from scripts.apply_year_match_review import assert_reconciliation
from scripts.apply_year_match_review import run as apply_run
from scripts.integrate_year_match_review import integrate


# ── shared fixtures ───────────────────────────────────────────────────────


def _bootstrap_db() -> sqlite3.Connection:
    """In-memory DB with the minimal schema the Phase-4 scripts touch."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE agencies (id INTEGER PRIMARY KEY, name TEXT, "
        "abbreviation TEXT)"
    )
    # 2025 use_cases — only the columns drift + apply read.
    conn.execute(
        """
        CREATE TABLE use_cases (
            id INTEGER PRIMARY KEY,
            agency_id INTEGER,
            slug TEXT,
            use_case_name TEXT,
            bureau_component TEXT,
            topic_area TEXT,
            stage_of_development TEXT,
            is_high_impact TEXT,
            system_outputs TEXT,
            development_type TEXT,
            has_pii TEXT,
            training_data_description TEXT,
            demographic_features TEXT,
            has_custom_code TEXT,
            code_url TEXT,
            has_ato TEXT,
            system_name TEXT,
            hi_assessment_completed TEXT,
            hi_testing_conducted TEXT,
            hi_potential_impacts TEXT,
            hi_independent_review TEXT,
            hi_ongoing_monitoring TEXT,
            hi_public_consultation TEXT,
            hi_appeal_process TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE use_cases_2024 (
            id INTEGER PRIMARY KEY,
            agency_id INTEGER,
            slug TEXT,
            use_case_name TEXT,
            agency TEXT,
            agency_abbreviation TEXT,
            bureau TEXT,
            topic_area TEXT,
            dev_stage TEXT,
            impact_type TEXT,
            purpose_benefits TEXT,
            outputs TEXT,
            dev_method TEXT,
            contains_pii TEXT,
            agency_data TEXT,
            demo_features TEXT,
            custom_code TEXT,
            code_link TEXT,
            has_ato TEXT,
            system_name TEXT,
            impact_assessment TEXT,
            real_world_testing TEXT,
            key_risks TEXT,
            independent_eval TEXT,
            monitor_postdeploy TEXT,
            stakeholder_consult TEXT,
            appeal_process TEXT
        )
        """
    )
    apply_m011(conn)
    conn.execute(
        "INSERT INTO agencies(id, name, abbreviation) VALUES (1, 'Test', 'TEST')"
    )
    return conn


def _ins_2024(conn, uc_id, slug, name, **kw):
    cols = ["id", "agency_id", "slug", "use_case_name"]
    vals = [uc_id, 1, slug, name]
    for k, v in kw.items():
        cols.append(k)
        vals.append(v)
    conn.execute(
        f"INSERT INTO use_cases_2024({','.join(cols)}) "
        f"VALUES ({','.join('?' * len(cols))})",
        vals,
    )


def _ins_2025(conn, uc_id, slug, name, **kw):
    cols = ["id", "agency_id", "slug", "use_case_name"]
    vals = [uc_id, 1, slug, name]
    for k, v in kw.items():
        cols.append(k)
        vals.append(v)
    conn.execute(
        f"INSERT INTO use_cases({','.join(cols)}) "
        f"VALUES ({','.join('?' * len(cols))})",
        vals,
    )


def _ins_link(conn, *, uc_2024_id, uc_2025_id, status, method="fuzzy_name"):
    conn.execute(
        """INSERT INTO use_case_year_links(
               run_at, uc_2024_id, uc_2025_id, agency_id, agency_abbreviation,
               match_method, match_score, lineage_status, first_seen, last_seen)
           VALUES ('t', ?, ?, 1, 'TEST', ?, 0.6, ?, 't', 't')""",
        (uc_2024_id, uc_2025_id, method, status),
    )


def _status_for(conn, *, uc_2024_id=None, uc_2025_id=None):
    if uc_2024_id is not None:
        rows = conn.execute(
            "SELECT lineage_status FROM use_case_year_links WHERE uc_2024_id=?",
            (uc_2024_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT lineage_status FROM use_case_year_links WHERE uc_2025_id=?",
            (uc_2025_id,),
        ).fetchall()
    return [r[0] for r in rows]


def _write_recs(pass_dir, agent, decisions):
    d = pass_dir / agent
    d.mkdir(parents=True, exist_ok=True)
    (d / "recommendations.json").write_text(json.dumps(decisions))


def _write_proposed(pass_dir, rows):
    """Write a synthetic integration/proposed_lineage.csv."""
    import csv as _csv
    intdir = pass_dir / "integration"
    intdir.mkdir(parents=True, exist_ok=True)
    cols = ["action", "agency_abbreviation", "uc_2024_slugs",
            "uc_2025_slugs", "confidence", "reasoning"]
    with (intdir / "proposed_lineage.csv").open("w", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})


# ── integrate ─────────────────────────────────────────────────────────────


def test_integrate_no_agents_writes_empty_csv(tmp_path):
    """No agent_*/ directories → integrate is a clean no-op: an empty
    proposed_lineage.csv (header only) and empty conflicts.csv."""
    result = integrate(tmp_path)
    assert result["proposed"] == []
    assert result["conflicts"] == []
    proposed = tmp_path / "integration" / "proposed_lineage.csv"
    assert proposed.exists()
    import csv as _csv
    with proposed.open() as f:
        assert list(_csv.DictReader(f)) == []


def test_integrate_valid_decisions_to_csv(tmp_path):
    _write_recs(tmp_path, "agent_1", [
        {
            "action": "confirm_rename", "agency_abbreviation": "TEST",
            "uc_2024_slugs": ["a-2024"], "uc_2025_slugs": ["a-2025"],
            "confidence": "high", "reasoning": "same use case",
        },
        {
            "action": "split", "agency_abbreviation": "TEST",
            "uc_2024_slugs": ["b-2024"],
            "uc_2025_slugs": ["b1-2025", "b2-2025"],
            "confidence": "medium", "reasoning": "split in two",
        },
    ])
    result = integrate(tmp_path)
    assert len(result["proposed"]) == 2
    assert result["conflicts"] == []
    actions = {r["action"] for r in result["proposed"]}
    assert actions == {"confirm_rename", "split"}
    split = next(r for r in result["proposed"] if r["action"] == "split")
    assert split["uc_2025_slugs"] == "b1-2025|b2-2025"


def test_integrate_conflicting_slug_routed_to_conflicts(tmp_path):
    """Two decisions claiming the same 2025 slug → conflict; BOTH are
    dropped from proposed_lineage.csv."""
    _write_recs(tmp_path, "agent_1", [
        {
            "action": "confirm_rename", "agency_abbreviation": "TEST",
            "uc_2024_slugs": ["a-2024"], "uc_2025_slugs": ["shared-2025"],
            "confidence": "high", "reasoning": "x",
        },
    ])
    _write_recs(tmp_path, "agent_2", [
        {
            "action": "recover_match", "agency_abbreviation": "TEST",
            "uc_2024_slugs": ["c-2024"], "uc_2025_slugs": ["shared-2025"],
            "confidence": "low", "reasoning": "y",
        },
    ])
    result = integrate(tmp_path)
    assert result["proposed"] == []
    assert any("shared-2025" in c["reason"] for c in result["conflicts"])


def test_integrate_recover_supersedes_reject_no_conflict(tmp_path):
    """A `recover_match` and a `reject_rename` sharing one slug is NOT a
    conflict — the reject freed the slug to residual, the recover then
    legitimately re-links it. Both decisions are kept; nothing flagged.

    Mirrors the real followup pass: a batch agent rejected one fuzzy pair
    (sending `shared-24` back to retired_2024), and the followup recovers
    `shared-24` against its true 2025 partner."""
    _write_recs(tmp_path, "agent_1", [
        {
            "action": "reject_rename", "agency_abbreviation": "TEST",
            "uc_2024_slugs": ["shared-24"], "uc_2025_slugs": ["wrong-25"],
            "confidence": "high", "reasoning": "fuzzy mismatch",
        },
    ])
    _write_recs(tmp_path, "agent_followup", [
        {
            "action": "recover_match", "agency_abbreviation": "TEST",
            "uc_2024_slugs": ["shared-24"], "uc_2025_slugs": ["right-25"],
            "confidence": "high", "reasoning": "matcher missed this rename",
        },
    ])
    result = integrate(tmp_path)
    assert result["conflicts"] == []
    actions = sorted(r["action"] for r in result["proposed"])
    assert actions == ["recover_match", "reject_rename"]


def test_integrate_two_definitive_on_one_slug_still_conflicts(tmp_path):
    """Two *definitive* decisions (a recover + a confirm) on one slug is a
    genuine conflict even though one is a recover_match — the supersede
    rule only lets a definitive decision override a `reject_rename`."""
    _write_recs(tmp_path, "agent_1", [
        {
            "action": "confirm_rename", "agency_abbreviation": "TEST",
            "uc_2024_slugs": ["a-24"], "uc_2025_slugs": ["dup-25"],
            "confidence": "high", "reasoning": "x",
        },
    ])
    _write_recs(tmp_path, "agent_2", [
        {
            "action": "recover_match", "agency_abbreviation": "TEST",
            "uc_2024_slugs": ["b-24"], "uc_2025_slugs": ["dup-25"],
            "confidence": "low", "reasoning": "y",
        },
    ])
    result = integrate(tmp_path)
    assert result["proposed"] == []
    assert any("dup-25" in c["reason"] for c in result["conflicts"])


def test_integrate_two_rejects_on_one_slug_still_conflicts(tmp_path):
    """Two `reject_rename` decisions on one slug remain a conflict — with
    no definitive decision there is nothing to supersede."""
    _write_recs(tmp_path, "agent_1", [
        {
            "action": "reject_rename", "agency_abbreviation": "TEST",
            "uc_2024_slugs": ["c-24"], "uc_2025_slugs": ["dup-25"],
            "confidence": "high", "reasoning": "x",
        },
    ])
    _write_recs(tmp_path, "agent_2", [
        {
            "action": "reject_rename", "agency_abbreviation": "TEST",
            "uc_2024_slugs": ["d-24"], "uc_2025_slugs": ["dup-25"],
            "confidence": "high", "reasoning": "y",
        },
    ])
    result = integrate(tmp_path)
    assert result["proposed"] == []
    assert any("dup-25" in c["reason"] for c in result["conflicts"])


def test_integrate_bad_schema_flagged(tmp_path):
    """A split with only one 2025 slug violates the shape and is flagged."""
    _write_recs(tmp_path, "agent_1", [
        {
            "action": "split", "agency_abbreviation": "TEST",
            "uc_2024_slugs": ["a-2024"], "uc_2025_slugs": ["only-one"],
            "confidence": "high", "reasoning": "x",
        },
        {
            "action": "teleport", "agency_abbreviation": "TEST",
            "uc_2024_slugs": ["z"], "uc_2025_slugs": ["q"],
        },
    ])
    result = integrate(tmp_path)
    assert result["proposed"] == []
    assert len(result["conflicts"]) == 2


# ── apply ─────────────────────────────────────────────────────────────────


def _seed_apply_fixture(conn):
    """A fixture with one of every status the apply script transforms."""
    # confirm/reject candidates — suggested_rename pairs.
    _ins_2024(conn, 1, "confirm-24", "Confirm 24", purpose_benefits="p", outputs="o")
    _ins_2025(conn, 11, "confirm-25", "Confirm 25", system_outputs="o")
    _ins_link(conn, uc_2024_id=1, uc_2025_id=11, status="suggested_rename")

    _ins_2024(conn, 2, "reject-24", "Reject 24", purpose_benefits="p", outputs="o")
    _ins_2025(conn, 12, "reject-25", "Reject 25", system_outputs="o")
    _ins_link(conn, uc_2024_id=2, uc_2025_id=12, status="suggested_rename")

    # recover_match — a separate retired_2024 + new_2025 the matcher missed.
    _ins_2024(conn, 3, "recover-24", "Recover 24", purpose_benefits="p")
    _ins_link(conn, uc_2024_id=3, uc_2025_id=None, status="retired_2024",
              method="none")
    _ins_2025(conn, 13, "recover-25", "Recover 25", system_outputs="o")
    _ins_link(conn, uc_2024_id=None, uc_2025_id=13, status="new_2025",
              method="none")

    # split — one 2024 row → two 2025 rows. The two 2025 rows arrive as
    # new_2025; the 2024 row as suggested_rename to one of them.
    _ins_2024(conn, 4, "split-24", "Split 24", purpose_benefits="p")
    _ins_2025(conn, 14, "split-25a", "Split 25 A", system_outputs="o")
    _ins_2025(conn, 15, "split-25b", "Split 25 B", system_outputs="o")
    _ins_link(conn, uc_2024_id=4, uc_2025_id=14, status="suggested_rename")
    _ins_link(conn, uc_2024_id=None, uc_2025_id=15, status="new_2025",
              method="none")

    # merge — two 2024 rows → one 2025 row.
    _ins_2024(conn, 5, "merge-24a", "Merge 24 A", purpose_benefits="p")
    _ins_2024(conn, 6, "merge-24b", "Merge 24 B", purpose_benefits="p")
    _ins_2025(conn, 16, "merge-25", "Merge 25", system_outputs="o")
    _ins_link(conn, uc_2024_id=5, uc_2025_id=16, status="suggested_rename")
    _ins_link(conn, uc_2024_id=6, uc_2025_id=None, status="retired_2024",
              method="none")

    # A plain continued link untouched by any decision.
    _ins_2024(conn, 7, "keep-24", "Keep 24", purpose_benefits="p")
    _ins_2025(conn, 17, "keep-25", "Keep 25", system_outputs="o")
    _ins_link(conn, uc_2024_id=7, uc_2025_id=17, status="continued",
              method="exact_name")
    conn.commit()


def test_apply_noop_when_no_csv(tmp_path):
    """Absent proposed_lineage.csv → apply leaves the matcher baseline
    untouched and the ≥1 reconciliation invariant still holds."""
    conn = _bootstrap_db()
    _seed_apply_fixture(conn)
    before = conn.execute(
        "SELECT lineage_status, COUNT(*) FROM use_case_year_links "
        "GROUP BY lineage_status ORDER BY lineage_status"
    ).fetchall()
    apply_run(conn, tmp_path)  # no integration/ dir at all
    after = conn.execute(
        "SELECT lineage_status, COUNT(*) FROM use_case_year_links "
        "GROUP BY lineage_status ORDER BY lineage_status"
    ).fetchall()
    assert [tuple(r) for r in before] == [tuple(r) for r in after]


def test_apply_each_action_mutates_correctly(tmp_path):
    conn = _bootstrap_db()
    _seed_apply_fixture(conn)
    _write_proposed(tmp_path, [
        {"action": "confirm_rename", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "confirm-24", "uc_2025_slugs": "confirm-25",
         "confidence": "high", "reasoning": "same"},
        {"action": "reject_rename", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "reject-24", "uc_2025_slugs": "reject-25",
         "confidence": "high", "reasoning": "different"},
        {"action": "recover_match", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "recover-24", "uc_2025_slugs": "recover-25",
         "confidence": "medium", "reasoning": "missed"},
        {"action": "split", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "split-24", "uc_2025_slugs": "split-25a|split-25b",
         "confidence": "medium", "reasoning": "two"},
        {"action": "merge", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "merge-24a|merge-24b", "uc_2025_slugs": "merge-25",
         "confidence": "medium", "reasoning": "one"},
    ])
    apply_run(conn, tmp_path)

    # confirm_rename → renamed, llm_review, reasoning persisted.
    assert _status_for(conn, uc_2024_id=1) == ["renamed"]
    row = conn.execute(
        "SELECT match_method, llm_reasoning, resolved_at "
        "FROM use_case_year_links WHERE uc_2024_id=1"
    ).fetchone()
    assert row[0] == "llm_review"
    assert row[1] == "same"
    assert row[2] is not None

    # reject_rename → split into a retired_2024 + a new_2025.
    assert _status_for(conn, uc_2024_id=2) == ["retired_2024"]
    assert _status_for(conn, uc_2025_id=12) == ["new_2025"]

    # recover_match → one renamed link; the standalone rows are gone.
    rec = conn.execute(
        "SELECT lineage_status FROM use_case_year_links "
        "WHERE uc_2024_id=3 AND uc_2025_id=13"
    ).fetchone()
    assert rec[0] == "renamed"
    assert _status_for(conn, uc_2024_id=3) == ["renamed"]
    assert _status_for(conn, uc_2025_id=13) == ["renamed"]

    # split → two split rows, same uc_2024_id, distinct uc_2025_id.
    split_rows = conn.execute(
        "SELECT uc_2025_id, lineage_status FROM use_case_year_links "
        "WHERE uc_2024_id=4 ORDER BY uc_2025_id"
    ).fetchall()
    assert [tuple(r) for r in split_rows] == [(14, "split"), (15, "split")]

    # merge → two merged rows, same uc_2025_id, distinct uc_2024_id.
    merge_rows = conn.execute(
        "SELECT uc_2024_id, lineage_status FROM use_case_year_links "
        "WHERE uc_2025_id=16 ORDER BY uc_2024_id"
    ).fetchall()
    assert [tuple(r) for r in merge_rows] == [(5, "merged"), (6, "merged")]

    # untouched continued link stays.
    assert _status_for(conn, uc_2024_id=7) == ["continued"]


def test_apply_reconciliation_holds_with_split_merge(tmp_path):
    """The ≥1 invariant must hold after N:M decisions land."""
    conn = _bootstrap_db()
    _seed_apply_fixture(conn)
    _write_proposed(tmp_path, [
        {"action": "split", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "split-24", "uc_2025_slugs": "split-25a|split-25b",
         "confidence": "medium", "reasoning": "two"},
        {"action": "merge", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "merge-24a|merge-24b", "uc_2025_slugs": "merge-25",
         "confidence": "medium", "reasoning": "one"},
    ])
    # apply_run asserts reconciliation internally; reaching here = pass.
    apply_run(conn, tmp_path)
    n_2024 = conn.execute("SELECT COUNT(*) FROM use_cases_2024").fetchone()[0]
    n_2025 = conn.execute("SELECT COUNT(*) FROM use_cases").fetchone()[0]
    d24 = conn.execute(
        "SELECT COUNT(DISTINCT uc_2024_id) FROM use_case_year_links "
        "WHERE uc_2024_id IS NOT NULL"
    ).fetchone()[0]
    d25 = conn.execute(
        "SELECT COUNT(DISTINCT uc_2025_id) FROM use_case_year_links "
        "WHERE uc_2025_id IS NOT NULL"
    ).fetchone()[0]
    assert d24 == n_2024
    assert d25 == n_2025


def test_apply_split_orphans_suggested_partner_rehomed(tmp_path):
    """A split whose 2025 set excludes the matcher's suggested_rename
    partner orphans that partner — the rehoming pass must land it as a
    new_2025 link so the ≥1 reconciliation invariant still holds.

    Models the production bug: the matcher's suggested 2025 partner was a
    wrong-component row, discarded by the split, left in no link at all.
    """
    conn = _bootstrap_db()
    # 2024 row + its matcher-suggested (wrong-component) 2025 partner.
    _ins_2024(conn, 1, "src-24", "Source 24", purpose_benefits="p")
    _ins_2025(conn, 11, "wrong-partner-25", "Wrong Partner 25",
              system_outputs="o")
    _ins_link(conn, uc_2024_id=1, uc_2025_id=11, status="suggested_rename")
    # The two *correct* split targets — arrive as new_2025.
    _ins_2025(conn, 12, "split-a-25", "Split A 25", system_outputs="o")
    _ins_2025(conn, 13, "split-b-25", "Split B 25", system_outputs="o")
    _ins_link(conn, uc_2024_id=None, uc_2025_id=12, status="new_2025",
              method="none")
    _ins_link(conn, uc_2024_id=None, uc_2025_id=13, status="new_2025",
              method="none")
    conn.commit()

    _write_proposed(tmp_path, [
        {"action": "split", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "src-24",
         "uc_2025_slugs": "split-a-25|split-b-25",
         "confidence": "medium", "reasoning": "real split"},
    ])
    # apply_run asserts reconciliation internally; reaching here = pass.
    apply_run(conn, tmp_path)

    # The discarded suggested partner is re-homed as a new_2025 link.
    assert _status_for(conn, uc_2025_id=11) == ["new_2025"]
    row = conn.execute(
        "SELECT match_method, resolution_note FROM use_case_year_links "
        "WHERE uc_2025_id=11"
    ).fetchone()
    assert row[0] == "none"
    assert row[1] == "re-homed orphan after Phase-4 apply"
    # The split itself landed correctly.
    split_rows = conn.execute(
        "SELECT uc_2025_id, lineage_status FROM use_case_year_links "
        "WHERE uc_2024_id=1 ORDER BY uc_2025_id"
    ).fetchall()
    assert [tuple(r) for r in split_rows] == [(12, "split"), (13, "split")]


def test_apply_is_idempotent(tmp_path):
    """Applying twice (matcher baseline re-seeded between) → stable result.

    Each `make fix` rebuilds the baseline then re-applies; this models that
    by re-seeding the fixture and re-running."""
    proposed = [
        {"action": "confirm_rename", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "confirm-24", "uc_2025_slugs": "confirm-25",
         "confidence": "high", "reasoning": "same"},
        {"action": "split", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "split-24", "uc_2025_slugs": "split-25a|split-25b",
         "confidence": "medium", "reasoning": "two"},
    ]
    _write_proposed(tmp_path, proposed)

    conn1 = _bootstrap_db()
    _seed_apply_fixture(conn1)
    apply_run(conn1, tmp_path)
    snap1 = conn1.execute(
        "SELECT uc_2024_id, uc_2025_id, lineage_status FROM use_case_year_links "
        "ORDER BY uc_2024_id, uc_2025_id"
    ).fetchall()

    conn2 = _bootstrap_db()
    _seed_apply_fixture(conn2)
    apply_run(conn2, tmp_path)
    apply_run(conn2, tmp_path)  # second pass on same baseline
    snap2 = conn2.execute(
        "SELECT uc_2024_id, uc_2025_id, lineage_status FROM use_case_year_links "
        "ORDER BY uc_2024_id, uc_2025_id"
    ).fetchall()
    assert [tuple(r) for r in snap1] == [tuple(r) for r in snap2]


def _full_snapshot(conn):
    """Every link row, all columns, in a stable order — for byte-identity
    comparison across re-runs."""
    return [
        tuple(r) for r in conn.execute(
            "SELECT uc_2024_id, uc_2025_id, lineage_status, match_method, "
            "       resolution_note "
            "FROM use_case_year_links "
            "ORDER BY lineage_status, uc_2024_id, uc_2025_id"
        ).fetchall()
    ]


def test_apply_standalone_reruns_are_byte_identical(tmp_path):
    """Bug-1 regression: running apply N times in a row on the SAME baseline
    (no re-seed between) must yield a byte-identical table — row counts and
    per-status counts stable. This is the standalone-rerun case the matcher
    masks inside `make fix` (it wipes the table first each run)."""
    conn = _bootstrap_db()
    _seed_apply_fixture(conn)
    _write_proposed(tmp_path, [
        {"action": "confirm_rename", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "confirm-24", "uc_2025_slugs": "confirm-25",
         "confidence": "high", "reasoning": "same"},
        {"action": "reject_rename", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "reject-24", "uc_2025_slugs": "reject-25",
         "confidence": "high", "reasoning": "different"},
        {"action": "recover_match", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "recover-24", "uc_2025_slugs": "recover-25",
         "confidence": "medium", "reasoning": "missed"},
        {"action": "split", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "split-24", "uc_2025_slugs": "split-25a|split-25b",
         "confidence": "medium", "reasoning": "two"},
        {"action": "merge", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "merge-24a|merge-24b", "uc_2025_slugs": "merge-25",
         "confidence": "medium", "reasoning": "one"},
    ])

    apply_run(conn, tmp_path)
    snap1 = _full_snapshot(conn)
    rows1 = conn.execute("SELECT COUNT(*) FROM use_case_year_links").fetchone()[0]

    # Re-run twice more on the SAME table — no re-seed, no matcher wipe.
    apply_run(conn, tmp_path)
    apply_run(conn, tmp_path)
    snap3 = _full_snapshot(conn)
    rows3 = conn.execute("SELECT COUNT(*) FROM use_case_year_links").fetchone()[0]

    assert rows1 == rows3, f"row count drifted across re-runs: {rows1} → {rows3}"
    assert snap1 == snap3, "link table not byte-identical after standalone re-runs"


def test_assert_reconciliation_rejects_duplicate_1to1_link(tmp_path):
    """Bug-2 regression: assert_reconciliation must raise when a use case
    carries a duplicate link in a 1:1 status (a non-idempotent handler
    double-inserting would produce exactly this)."""
    conn = _bootstrap_db()
    _ins_2024(conn, 1, "a-24", "A 24", purpose_benefits="p")
    _ins_2025(conn, 11, "a-25", "A 25", system_outputs="o")
    _ins_link(conn, uc_2024_id=1, uc_2025_id=11, status="renamed")
    conn.commit()
    # Clean single 1:1 link → passes.
    assert_reconciliation(conn)

    # Inject a duplicate renamed link for the same pair → must raise.
    _ins_link(conn, uc_2024_id=1, uc_2025_id=11, status="renamed")
    conn.commit()
    with pytest.raises(AssertionError, match="1:1 uniqueness failed"):
        assert_reconciliation(conn)


def test_apply_retired_cross_check_flags(tmp_path):
    """A new_2025 row already at the Retired stage is flagged."""
    conn = _bootstrap_db()
    _ins_2024(conn, 1, "x-24", "X 24", purpose_benefits="p")
    _ins_link(conn, uc_2024_id=1, uc_2025_id=None, status="retired_2024",
              method="none")
    _ins_2025(conn, 11, "x-25", "X 25",
              stage_of_development="d) Retired", system_outputs="o")
    _ins_link(conn, uc_2024_id=None, uc_2025_id=11, status="new_2025",
              method="none")
    conn.commit()
    apply_run(conn, tmp_path)
    import csv as _csv
    flags = list(_csv.DictReader(
        (tmp_path / "integration" / "classification_flags.csv").open()
    ))
    assert any(f["flag"] == "new_2025_already_retired" for f in flags)


def test_apply_unresolvable_slug_skipped(tmp_path):
    """A decision whose slug no longer resolves is skipped, not fatal."""
    conn = _bootstrap_db()
    _seed_apply_fixture(conn)
    _write_proposed(tmp_path, [
        {"action": "confirm_rename", "agency_abbreviation": "TEST",
         "uc_2024_slugs": "ghost-24", "uc_2025_slugs": "ghost-25",
         "confidence": "high", "reasoning": "stale"},
    ])
    apply_run(conn, tmp_path)  # must not raise
    # The continued baseline link is untouched.
    assert _status_for(conn, uc_2024_id=7) == ["continued"]


# ── drift ─────────────────────────────────────────────────────────────────


def test_drift_directly_comparable_detected(tmp_path):
    """A changed directly-comparable field is recorded, not flagged lossy."""
    conn = _bootstrap_db()
    # agency / agency_abbreviation are directly-comparable too — set them to
    # the joined 2025 agency ('Test' / 'TEST') so only system_name drifts.
    _ins_2024(conn, 1, "d-24", "Same Name", agency="Test",
              agency_abbreviation="TEST",
              system_name="Old System", contains_pii="Yes")
    _ins_2025(conn, 11, "d-25", "Same Name",
              system_name="New System", has_pii="Yes")
    _ins_link(conn, uc_2024_id=1, uc_2025_id=11, status="continued",
              method="exact_name")
    conn.commit()
    stats = compute_year_lineage_drift.compute(conn)
    assert stats["eligible"] == 1
    assert stats["with_drift"] == 1
    drift = json.loads(conn.execute(
        "SELECT drift_fields_json FROM use_case_year_links WHERE uc_2024_id=1"
    ).fetchone()[0])
    assert "system_name" in drift
    assert set(drift) == {"system_name"}
    assert drift["system_name"]["v2024"] == "Old System"
    assert drift["system_name"]["v2025"] == "New System"
    assert drift["system_name"]["lossy"] is False
    # has_pii is unchanged → not in drift.
    assert "contains_pii" not in drift and "has_pii" not in drift


def test_drift_recoded_field_flagged_lossy(tmp_path):
    """dev_stage drift goes through DEV_STAGE_RECODE_2024 and is lossy."""
    conn = _bootstrap_db()
    # 2024 'Initiated' recodes to 'a) Pre-deployment'; 2025 is 'c) Deployed'
    # → genuine drift, flagged lossy because the recode is lossy.
    _ins_2024(conn, 1, "r-24", "Same", dev_stage="Initiated")
    _ins_2025(conn, 11, "r-25", "Same", stage_of_development="c) Deployed")
    _ins_link(conn, uc_2024_id=1, uc_2025_id=11, status="renamed")
    conn.commit()
    compute_year_lineage_drift.compute(conn)
    drift = json.loads(conn.execute(
        "SELECT drift_fields_json FROM use_case_year_links WHERE uc_2024_id=1"
    ).fetchone()[0])
    assert "dev_stage" in drift
    assert drift["dev_stage"]["lossy"] is True
    assert drift["dev_stage"]["v2024"] == "Initiated"
    assert drift["dev_stage"]["v2024_recoded"] == "a) Pre-deployment"


def test_drift_recoded_field_matches_after_recode(tmp_path):
    """When the recoded 2024 value equals the 2025 value, no drift entry."""
    conn = _bootstrap_db()
    # 'Operation and Maintenance' recodes to 'c) Deployed' == 2025 value.
    _ins_2024(conn, 1, "m-24", "Same", dev_stage="Operation and Maintenance")
    _ins_2025(conn, 11, "m-25", "Same", stage_of_development="c) Deployed")
    _ins_link(conn, uc_2024_id=1, uc_2025_id=11, status="continued",
              method="exact_name")
    conn.commit()
    compute_year_lineage_drift.compute(conn)
    drift = json.loads(conn.execute(
        "SELECT drift_fields_json FROM use_case_year_links WHERE uc_2024_id=1"
    ).fetchone()[0])
    assert "dev_stage" not in drift


def test_drift_skips_split_merge_retired_new(tmp_path):
    """Non-1:1-continued/renamed links never get drift_fields_json."""
    conn = _bootstrap_db()
    _ins_2024(conn, 1, "s-24", "S", dev_stage="Initiated")
    _ins_2025(conn, 11, "s-25a", "S a", stage_of_development="c) Deployed")
    _ins_2025(conn, 12, "s-25b", "S b", stage_of_development="c) Deployed")
    _ins_link(conn, uc_2024_id=1, uc_2025_id=11, status="split")
    _ins_link(conn, uc_2024_id=1, uc_2025_id=12, status="split")
    _ins_2024(conn, 2, "ret-24", "Ret")
    _ins_link(conn, uc_2024_id=2, uc_2025_id=None, status="retired_2024",
              method="none")
    _ins_2025(conn, 13, "new-25", "New")
    _ins_link(conn, uc_2024_id=None, uc_2025_id=13, status="new_2025",
              method="none")
    conn.commit()
    compute_year_lineage_drift.compute(conn)
    nulls = conn.execute(
        "SELECT COUNT(*) FROM use_case_year_links "
        "WHERE drift_fields_json IS NOT NULL"
    ).fetchone()[0]
    assert nulls == 0


def test_drift_idempotent(tmp_path):
    """Recomputing drift twice yields identical drift_fields_json."""
    conn = _bootstrap_db()
    _ins_2024(conn, 1, "i-24", "Same", system_name="Old")
    _ins_2025(conn, 11, "i-25", "Same", system_name="New")
    _ins_link(conn, uc_2024_id=1, uc_2025_id=11, status="continued",
              method="exact_name")
    conn.commit()
    compute_year_lineage_drift.compute(conn)
    first = conn.execute(
        "SELECT drift_fields_json FROM use_case_year_links WHERE uc_2024_id=1"
    ).fetchone()[0]
    compute_year_lineage_drift.compute(conn)
    second = conn.execute(
        "SELECT drift_fields_json FROM use_case_year_links WHERE uc_2024_id=1"
    ).fetchone()[0]
    assert first == second
