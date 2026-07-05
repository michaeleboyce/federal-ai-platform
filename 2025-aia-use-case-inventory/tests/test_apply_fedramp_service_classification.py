"""Tests for scripts/apply_fedramp_service_classification.py.

Fixture-DB tests exercise the apply path (idempotency, orphan skip, enum
rejection, coverage gate, dry-run); live-DB tests assert invariants on the
applied fedramp_ai_service_classification table. Mirrors
test_apply_fedramp_ai_classification.py.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import scripts.apply_fedramp_service_classification as apply_mod  # noqa: E402

CSV_FIELDS = [
    "service", "category", "confidence", "reasoning", "signals",
    "model", "input_hash", "classified_at", "source",
]


def _mk_db(path: Path, services: list[str]) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE fedramp_authorized_services (fedramp_id TEXT, "
        "service TEXT, recency TEXT)"
    )
    conn.executemany(
        "INSERT INTO fedramp_authorized_services VALUES ('FR1', ?, 'older')",
        [(s,) for s in services],
    )
    conn.commit()
    conn.close()


def _mk_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _row(service, category="core_ai", confidence="high", source="llm"):
    return {
        "service": service, "category": category, "confidence": confidence,
        "reasoning": "test reasoning", "signals": "[]", "model": "test-model",
        "input_hash": "abc", "classified_at": "2026-07-04T00:00:00Z",
        "source": source,
    }


def _run(monkeypatch, db, csv_path, argv=("--apply",)):
    monkeypatch.setattr(apply_mod, "DB_PATH", db)
    monkeypatch.setattr(apply_mod, "CSV_PATH", csv_path)
    monkeypatch.setattr(sys, "argv", ["apply_fedramp_service_classification.py", *argv])
    apply_mod.main()


def test_apply_and_idempotent(tmp_path, monkeypatch, capsys):
    db = tmp_path / "t.db"
    _mk_db(db, ["Amazon Bedrock", "AWS Backup"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [
        _row("Amazon Bedrock", source="qc_confirmed"),
        _row("AWS Backup", category="not_ai"),
    ])
    _run(monkeypatch, db, csv_path)
    _run(monkeypatch, db, csv_path)  # idempotent re-run
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM fedramp_ai_service_classification"
    ).fetchone()[0] == 2
    assert conn.execute(
        "SELECT category, source FROM fedramp_ai_service_classification "
        "WHERE service='Amazon Bedrock'"
    ).fetchone() == ("core_ai", "qc_confirmed")
    conn.close()


def test_orphan_skipped(tmp_path, monkeypatch, capsys):
    db = tmp_path / "t.db"
    _mk_db(db, ["Amazon Bedrock"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Amazon Bedrock"), _row("Delisted Service")])
    _run(monkeypatch, db, csv_path)
    out = capsys.readouterr().out
    assert "orphan service 'Delisted Service'" in out
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM fedramp_ai_service_classification"
    ).fetchone()[0] == 1
    conn.close()


def test_unlabeled_service_exits_nonzero(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Amazon Bedrock", "AWS Backup"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Amazon Bedrock")])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, db, csv_path)
    assert e.value.code == 2


def test_bad_enum_rejected(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Amazon Bedrock"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Amazon Bedrock", source="vibes")])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, db, csv_path)
    assert e.value.code == 1


def test_dry_run_writes_nothing(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Amazon Bedrock"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Amazon Bedrock")])
    _run(monkeypatch, db, csv_path, argv=())
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM fedramp_ai_service_classification"
    ).fetchone()[0] == 0
    conn.close()


# --------------------------------------------------------------------------
# Live-DB invariants (skip cleanly until the classification has been applied)
# --------------------------------------------------------------------------


def _has_table(conn, name: str) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone())


@pytest.fixture()
def applied_conn(conn):
    if not _has_table(conn, "fedramp_ai_service_classification"):
        pytest.skip("fedramp_ai_service_classification not applied in this DB build")
    return conn


def test_live_full_coverage(applied_conn):
    live = applied_conn.execute(
        "SELECT COUNT(DISTINCT service) FROM fedramp_authorized_services"
    ).fetchone()[0]
    labeled = applied_conn.execute(
        "SELECT COUNT(*) FROM fedramp_ai_service_classification"
    ).fetchone()[0]
    assert labeled == live


def test_live_core_ai_all_reviewed(applied_conn):
    """Article guardrail: no core_ai label ships on a single unreviewed pass."""
    n = applied_conn.execute(
        "SELECT COUNT(*) FROM fedramp_ai_service_classification "
        "WHERE category='core_ai' AND source NOT IN "
        "('qc_confirmed','qc_corrected','adjudicated','manual_override')"
    ).fetchone()[0]
    assert n == 0


def test_live_bedrock_core_ai(applied_conn):
    row = applied_conn.execute(
        "SELECT category FROM fedramp_ai_service_classification "
        "WHERE service='Amazon Bedrock'"
    ).fetchone()
    assert row is not None and row[0] == "core_ai"
