"""Tests for scripts/apply_product_capability_labels.py.

Fixture-DB tests exercise the apply path (idempotency, none-co-occurrence
gate, gen_ai consistency gate, enum rejection, coverage gate, missing-CSV
soft skip, unknown-product skip, dry-run); live-DB tests assert invariants
on the applied product_capability_labels table. Mirrors
test_apply_fedramp_service_product_map.py.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import scripts.apply_product_capability_labels as apply_mod  # noqa: E402

CSV_FIELDS = [
    "canonical_name", "category", "gen_ai", "confidence",
    "reasoning", "model", "labeled_at", "source",
]


def _mk_db(path: Path, edged: list[str], unedged: list[str] = ()) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, canonical_name TEXT)"
    )
    conn.executemany(
        "INSERT INTO products (canonical_name) VALUES (?)",
        [(p,) for p in [*edged, *unedged]],
    )
    # entry_product_edges is a VIEW in the real DB; a plain table with the
    # same columns satisfies the apply script's read.
    conn.execute(
        "CREATE TABLE entry_product_edges (entry_id INTEGER, product_id INTEGER)"
    )
    conn.executemany(
        "INSERT INTO entry_product_edges "
        "SELECT 1, id FROM products WHERE canonical_name = ?",
        [(p,) for p in edged],
    )
    conn.commit()
    conn.close()


def _mk_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _row(name, category="genai_platform", gen_ai="1",
         confidence="high", source="llm"):
    return {
        "canonical_name": name, "category": category, "gen_ai": gen_ai,
        "confidence": confidence, "reasoning": "test reasoning",
        "model": "test-model", "labeled_at": "2026-07-05T00:00:00Z",
        "source": source,
    }


def _run(monkeypatch, db, csv_path, argv=("--apply",)):
    monkeypatch.setattr(apply_mod, "DB_PATH", db)
    monkeypatch.setattr(apply_mod, "CSV_PATH", csv_path)
    monkeypatch.setattr(sys, "argv", ["apply_product_capability_labels.py", *argv])
    apply_mod.main()


def test_apply_and_idempotent(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Claude", "Zscaler"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [
        _row("Claude"),
        _row("Zscaler", category="none", gen_ai="0"),
    ])
    _run(monkeypatch, db, csv_path)
    _run(monkeypatch, db, csv_path)  # idempotent re-run
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM product_capability_labels"
    ).fetchone()[0] == 2
    assert conn.execute(
        "SELECT gen_ai FROM product_capability_labels "
        "WHERE canonical_name='Claude'"
    ).fetchone()[0] == 1
    conn.close()


def test_multi_label_allowed(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Databricks"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [
        _row("Databricks", category="ml_platform"),
        _row("Databricks", category="assistant"),
    ])
    _run(monkeypatch, db, csv_path)
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM product_capability_labels "
        "WHERE canonical_name='Databricks'"
    ).fetchone()[0] == 2
    conn.close()


def test_none_cooccurrence_rejected(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Claude"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [
        _row("Claude"),
        _row("Claude", category="none"),
    ])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, db, csv_path)
    assert e.value.code == 1


def test_gen_ai_inconsistency_rejected(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Databricks"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [
        _row("Databricks", category="ml_platform", gen_ai="1"),
        _row("Databricks", category="assistant", gen_ai="0"),
    ])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, db, csv_path)
    assert e.value.code == 1


def test_bad_enum_rejected(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Claude"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Claude", category="robots")])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, db, csv_path)
    assert e.value.code == 1


def test_coverage_gate_exits_2(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Claude", "Unlabeled Product"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Claude")])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, db, csv_path)
    assert e.value.code == 2


def test_unknown_product_skipped(tmp_path, monkeypatch, capsys):
    db = tmp_path / "t.db"
    _mk_db(db, ["Claude"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Claude"), _row("Ghost Product")])
    _run(monkeypatch, db, csv_path)
    out = capsys.readouterr().out
    assert "unknown product 'Ghost Product'" in out


def test_unedged_but_known_product_kept(tmp_path, monkeypatch):
    """A label for a real product without edges loads fine (no gate)."""
    db = tmp_path / "t.db"
    _mk_db(db, ["Claude"], unedged=["Shelf Product"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Claude"), _row("Shelf Product", category="none", gen_ai="0")])
    _run(monkeypatch, db, csv_path)
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM product_capability_labels"
    ).fetchone()[0] == 2
    conn.close()


def test_missing_csv_soft_skip(tmp_path, monkeypatch, capsys):
    db = tmp_path / "t.db"
    _mk_db(db, ["Claude"])
    _run(monkeypatch, db, tmp_path / "does_not_exist.csv")
    out = capsys.readouterr().out
    assert "skipping" in out  # exit 0, Makefile stays green pre-labels


def test_dry_run_writes_nothing(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Claude"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Claude")])
    _run(monkeypatch, db, csv_path, argv=())
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM product_capability_labels"
    ).fetchone()[0] == 0
    conn.close()


# --------------------------------------------------------------------------
# Live-DB invariants (skip cleanly until the labels have been applied)
# --------------------------------------------------------------------------


def _has_table(conn, name: str) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone())


@pytest.fixture()
def applied_conn(conn):
    if not _has_table(conn, "product_capability_labels"):
        pytest.skip("product_capability_labels not applied in this DB build")
    return conn


def test_live_full_coverage_of_edged_products(applied_conn):
    n = applied_conn.execute(
        """SELECT COUNT(DISTINCT p.canonical_name)
             FROM products p
             JOIN entry_product_edges e ON e.product_id = p.id
            WHERE p.canonical_name NOT IN
                  (SELECT canonical_name FROM product_capability_labels)"""
    ).fetchone()[0]
    assert n == 0


def test_live_none_never_cooccurs(applied_conn):
    n = applied_conn.execute(
        """SELECT COUNT(*) FROM product_capability_labels a
            WHERE a.category = 'none'
              AND EXISTS (SELECT 1 FROM product_capability_labels b
                           WHERE b.canonical_name = a.canonical_name
                             AND b.category != 'none')"""
    ).fetchone()[0]
    assert n == 0


def test_live_pins(applied_conn):
    """Frontier chat products must carry genai_platform + gen_ai=1."""
    for name in ["Claude", "Azure OpenAI"]:
        rows = applied_conn.execute(
            "SELECT category, gen_ai FROM product_capability_labels "
            "WHERE canonical_name = ?", (name,)
        ).fetchall()
        if not rows:
            pytest.skip(f"{name} not in this DB build")
        assert any(r[0] == "genai_platform" for r in rows)
        assert all(r[1] == 1 for r in rows)
