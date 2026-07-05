"""Tests for scripts/apply_fedramp_service_product_map.py.

Fixture-DB tests exercise the apply path (idempotency, orphan skip, enum
rejection, unresolvable-product gate, non-core_ai gate, per-product
consistency gate, dry-run); live-DB tests assert invariants on the applied
fedramp_service_product_map table. Mirrors
test_apply_fedramp_service_classification.py.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import scripts.apply_fedramp_service_product_map as apply_mod  # noqa: E402

CSV_FIELDS = [
    "service", "product_canonical_name", "confidence",
    "capability_category", "gen_ai", "evidence_tier", "notes",
]


def _mk_db(path: Path, services: list[str], products: list[str],
           classifications: dict[str, str] | None = None) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE fedramp_authorized_services (fedramp_id TEXT, "
        "service TEXT, recency TEXT)"
    )
    conn.executemany(
        "INSERT INTO fedramp_authorized_services VALUES ('FR1', ?, 'older')",
        [(s,) for s in services],
    )
    conn.execute(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, canonical_name TEXT)"
    )
    conn.executemany(
        "INSERT INTO products (canonical_name) VALUES (?)",
        [(p,) for p in products],
    )
    conn.execute(
        "CREATE TABLE product_aliases (id INTEGER PRIMARY KEY, "
        "product_id INTEGER, alias_text TEXT)"
    )
    conn.execute(
        "CREATE TABLE fedramp_ai_service_classification ("
        "service TEXT PRIMARY KEY, category TEXT)"
    )
    conn.executemany(
        "INSERT INTO fedramp_ai_service_classification VALUES (?, ?)",
        [(s, c) for s, c in (classifications or {}).items()],
    )
    conn.commit()
    conn.close()


def _mk_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _row(service, product="AWS Bedrock", confidence="strong",
         category="genai_platform", gen_ai="1", tier="catalog"):
    return {
        "service": service, "product_canonical_name": product,
        "confidence": confidence, "capability_category": category,
        "gen_ai": gen_ai, "evidence_tier": tier, "notes": "test",
    }


def _run(monkeypatch, db, csv_path, argv=("--apply",)):
    monkeypatch.setattr(apply_mod, "DB_PATH", db)
    monkeypatch.setattr(apply_mod, "CSV_PATH", csv_path)
    monkeypatch.setattr(sys, "argv", ["apply_fedramp_service_product_map.py", *argv])
    apply_mod.main()


def test_apply_and_idempotent(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Amazon Bedrock"], ["AWS Bedrock"],
           {"Amazon Bedrock": "core_ai"})
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Amazon Bedrock")])
    _run(monkeypatch, db, csv_path)
    _run(monkeypatch, db, csv_path)  # idempotent re-run
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM fedramp_service_product_map"
    ).fetchone()[0] == 1
    assert conn.execute(
        "SELECT product_canonical_name, gen_ai, evidence_tier "
        "FROM fedramp_service_product_map WHERE service='Amazon Bedrock'"
    ).fetchone() == ("AWS Bedrock", 1, "catalog")
    conn.close()


def test_orphan_skipped(tmp_path, monkeypatch, capsys):
    db = tmp_path / "t.db"
    _mk_db(db, ["Amazon Bedrock"], ["AWS Bedrock"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Amazon Bedrock"), _row("Delisted Service")])
    _run(monkeypatch, db, csv_path)
    out = capsys.readouterr().out
    assert "orphan service 'Delisted Service'" in out
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM fedramp_service_product_map"
    ).fetchone()[0] == 1
    conn.close()


def test_bad_enum_rejected(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Amazon Bedrock"], ["AWS Bedrock"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Amazon Bedrock", tier="hyperscaler")])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, db, csv_path)
    assert e.value.code == 1


def test_inconsistent_product_attrs_rejected(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Svc A", "Svc B"], ["AWS Bedrock"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [
        _row("Svc A", category="genai_platform"),
        _row("Svc B", category="ml_platform"),  # same product, different category
    ])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, db, csv_path)
    assert e.value.code == 1


def test_gen_ai_may_disagree_within_product(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Svc A", "Svc B"], ["Google Vertex AI"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [
        _row("Svc A", product="Google Vertex AI", category="ml_platform", gen_ai="1"),
        _row("Svc B", product="Google Vertex AI", category="ml_platform", gen_ai="0"),
    ])
    _run(monkeypatch, db, csv_path)
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM fedramp_service_product_map"
    ).fetchone()[0] == 2
    conn.close()


def test_unresolvable_product_exits_2(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Amazon Bedrock"], ["Some Other Product"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Amazon Bedrock")])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, db, csv_path)
    assert e.value.code == 2


def test_alias_resolution_accepted(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Amazon Bedrock"], ["Bedrock Prime"])
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO product_aliases (product_id, alias_text) VALUES (1, 'AWS Bedrock')"
    )
    conn.commit()
    conn.close()
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Amazon Bedrock")])
    _run(monkeypatch, db, csv_path)  # resolves via alias; no exit


def test_non_core_ai_service_exits_2(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Amazon Bedrock"], ["AWS Bedrock"],
           {"Amazon Bedrock": "ai_featured"})
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Amazon Bedrock")])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, db, csv_path)
    assert e.value.code == 2


def test_dry_run_writes_nothing(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    _mk_db(db, ["Amazon Bedrock"], ["AWS Bedrock"])
    csv_path = tmp_path / "c.csv"
    _mk_csv(csv_path, [_row("Amazon Bedrock")])
    _run(monkeypatch, db, csv_path, argv=())
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT COUNT(*) FROM fedramp_service_product_map"
    ).fetchone()[0] == 0
    conn.close()


# --------------------------------------------------------------------------
# Live-DB invariants (skip cleanly until the crosswalk has been applied)
# --------------------------------------------------------------------------


def _has_table(conn, name: str) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone())


@pytest.fixture()
def applied_conn(conn):
    if not _has_table(conn, "fedramp_service_product_map"):
        pytest.skip("fedramp_service_product_map not applied in this DB build")
    return conn


def test_live_all_products_resolve(applied_conn):
    """Every mapped product must resolve by canonical_name or alias."""
    n = applied_conn.execute(
        """SELECT COUNT(*) FROM fedramp_service_product_map m
            WHERE NOT EXISTS (
              SELECT 1 FROM products p
               WHERE LOWER(p.canonical_name) = LOWER(m.product_canonical_name))
              AND NOT EXISTS (
              SELECT 1 FROM product_aliases a
               WHERE LOWER(a.alias_text) = LOWER(m.product_canonical_name))"""
    ).fetchone()[0]
    assert n == 0


def test_live_all_mapped_services_core_ai(applied_conn):
    n = applied_conn.execute(
        """SELECT COUNT(*) FROM fedramp_service_product_map m
            JOIN fedramp_ai_service_classification c ON c.service = m.service
           WHERE c.category != 'core_ai'"""
    ).fetchone()[0]
    assert n == 0


def test_live_pins(applied_conn):
    """Bedrock and Azure OpenAI rows are the canonical anchors."""
    for service, product in [
        ("Amazon Bedrock", "AWS Bedrock"),
        ("Azure OpenAI", "Azure OpenAI"),
    ]:
        row = applied_conn.execute(
            "SELECT product_canonical_name FROM fedramp_service_product_map "
            "WHERE service = ?", (service,)
        ).fetchone()
        assert row is not None and row[0] == product
