"""Tests for scripts/apply_fedramp_ai_classification.py.

Fixture-DB tests exercise the apply path (idempotency, orphan skip, enum
rejection, coverage gate); live-DB tests assert invariants on the applied
fedramp_ai_classification table.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import scripts.apply_fedramp_ai_classification as apply_mod  # noqa: E402


def _mk_db(path: Path, fedramp_ids: list[str]) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE fedramp_products (fedramp_id TEXT PRIMARY KEY, "
        "csp TEXT, cso TEXT, service_desc TEXT)"
    )
    conn.executemany(
        "INSERT INTO fedramp_products VALUES (?, 'V', 'P', "
        "'machine learning service')",
        [(f,) for f in fedramp_ids],
    )
    conn.commit()
    conn.close()


def _mk_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=apply_mod_fields())
        w.writeheader()
        for r in rows:
            w.writerow(r)


def apply_mod_fields():
    return [
        "fedramp_id", "csp", "cso", "category", "confidence", "reasoning",
        "signals", "model", "input_hash", "classified_at", "source",
    ]


def _row(fid, category="core_ai", confidence="high", source="llm"):
    return {
        "fedramp_id": fid, "csp": "V", "cso": "P", "category": category,
        "confidence": confidence, "reasoning": "test reasoning",
        "signals": "[]", "model": "test-model", "input_hash": "abc",
        "classified_at": "2026-06-12T00:00:00Z", "source": source,
    }


def _run(monkeypatch, db, csv_path, argv=("--apply",)):
    monkeypatch.setattr(apply_mod, "DB_PATH", db)
    monkeypatch.setattr(apply_mod, "CSV_PATH", csv_path)
    monkeypatch.setattr(sys, "argv", ["apply_fedramp_ai_classification.py", *argv])
    apply_mod.main()


def test_apply_and_idempotent(tmp_path, monkeypatch, capsys):
    db = tmp_path / "t.db"
    _mk_db(db, ["FR1", "FR2"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("FR1"), _row("FR2", category="not_ai")])
    _run(monkeypatch, db, csv_path)
    _run(monkeypatch, db, csv_path)  # idempotent re-run
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM fedramp_ai_classification"
    ).fetchone()[0] == 2
    assert conn.execute(
        "SELECT category FROM fedramp_ai_classification WHERE fedramp_id='FR2'"
    ).fetchone()[0] == "not_ai"
    conn.close()


def test_orphan_skipped_and_coverage_gate(tmp_path, monkeypatch, capsys):
    db = tmp_path / "t.db"
    _mk_db(db, ["FR1"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("FR1"), _row("FR_GONE")])
    _run(monkeypatch, db, csv_path)
    out = capsys.readouterr().out
    assert "orphan fedramp_id FR_GONE" in out
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM fedramp_ai_classification"
    ).fetchone()[0] == 1
    conn.close()


def test_unclassified_product_exits_nonzero(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["FR1", "FR2"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("FR1")])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, db, csv_path)
    assert e.value.code == 2


def test_bad_enum_rejected(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["FR1"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("FR1", category="kinda_ai")])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, db, csv_path)
    assert e.value.code == 1


def test_dry_run_writes_nothing(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["FR1"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("FR1")])
    _run(monkeypatch, db, csv_path, argv=())
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM fedramp_ai_classification"
    ).fetchone()[0] == 0
    conn.close()


# --------------------------------------------------------------------------
# Live-DB invariants (skip cleanly until the classification has been applied)
# --------------------------------------------------------------------------

def _has_table(conn) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='fedramp_ai_classification'"
    ).fetchone())


def test_live_classification_covers_all_products(conn):
    if not _has_table(conn):
        pytest.skip("fedramp_ai_classification not applied yet")
    n_products = conn.execute("SELECT COUNT(*) FROM fedramp_products").fetchone()[0]
    n_classified = conn.execute(
        "SELECT COUNT(*) FROM fedramp_ai_classification"
    ).fetchone()[0]
    assert n_classified == n_products


def test_live_classification_no_orphans(conn):
    if not _has_table(conn):
        pytest.skip("fedramp_ai_classification not applied yet")
    n = conn.execute(
        "SELECT COUNT(*) FROM fedramp_ai_classification c "
        "WHERE NOT EXISTS (SELECT 1 FROM fedramp_products p "
        "WHERE p.fedramp_id = c.fedramp_id)"
    ).fetchone()[0]
    assert n == 0


def test_live_classification_enums(conn):
    if not _has_table(conn):
        pytest.skip("fedramp_ai_classification not applied yet")
    bad = conn.execute(
        "SELECT COUNT(*) FROM fedramp_ai_classification "
        "WHERE category NOT IN ('core_ai','ai_featured','not_ai') "
        "OR confidence NOT IN ('high','medium','low') "
        "OR TRIM(reasoning) = ''"
    ).fetchone()[0]
    assert bad == 0
