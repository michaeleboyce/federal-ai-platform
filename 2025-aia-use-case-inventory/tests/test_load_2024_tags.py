"""Tests for scripts/load_2024_tags.py — the CSV-to-DB loader that
populates `use_case_tags_2024` from per-agent wave outputs."""
import csv
import sqlite3
from pathlib import Path

import pytest

from migrations import m009_use_cases_2024 as m009
from migrations import m014_use_case_tags_2024 as m014
from scripts.load_2024_tags import load


def _seed():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.execute(
        "CREATE TABLE agencies (id INTEGER PRIMARY KEY, "
        "abbreviation TEXT, full_name TEXT)"
    )
    c.execute("INSERT INTO agencies(id, abbreviation) VALUES (1, 'HHS')")
    m009.apply(c)
    m014.apply(c)
    c.execute(
        "INSERT INTO use_cases_2024 (id, agency_id, source_file, slug, "
        "use_case_name) VALUES (1, 1, 's.csv', 'a', 'A')"
    )
    c.execute(
        "INSERT INTO use_cases_2024 (id, agency_id, source_file, slug, "
        "use_case_name) VALUES (2, 1, 's.csv', 'b', 'B')"
    )
    c.commit()
    return c


def _write_csv(path: Path, rows: list[dict]):
    fieldnames = sorted({k for r in rows for k in r.keys()})
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def test_loads_a_basic_row(tmp_path):
    c = _seed()
    csv_path = tmp_path / "a.csv"
    _write_csv(csv_path, [{
        "use_case_id_2024": "1",
        "tagged_by_agent": "agentA",
        "entry_type": "product_deployment",
        "is_generative_ai": "1",
        "ai_sophistication": "general_llm",
        "deployment_scope": "enterprise_wide",
        "confidence": "high",
        "reasoning": "explicit ChatGPT deployment",
    }])
    n = load(c, "1", [csv_path])
    assert n == 1
    row = c.execute(
        "SELECT * FROM use_case_tags_2024 WHERE use_case_id_2024=1"
    ).fetchone()
    assert row["wave"] == "1"
    assert row["tagged_by_agent"] == "agentA"
    assert row["entry_type"] == "product_deployment"
    assert row["is_generative_ai"] == 1
    assert row["reasoning"] == "explicit ChatGPT deployment"


def test_idempotent_upsert(tmp_path):
    c = _seed()
    p = tmp_path / "a.csv"
    _write_csv(p, [{
        "use_case_id_2024": "1",
        "tagged_by_agent": "agentA",
        "entry_type": "custom_system",
        "confidence": "medium",
    }])
    load(c, "1", [p])
    # Same agent, same wave, different value — should UPDATE not duplicate
    _write_csv(p, [{
        "use_case_id_2024": "1",
        "tagged_by_agent": "agentA",
        "entry_type": "product_deployment",
        "confidence": "high",
    }])
    load(c, "1", [p])
    rows = c.execute(
        "SELECT entry_type, confidence FROM use_case_tags_2024 "
        "WHERE use_case_id_2024=1 AND wave='1' AND tagged_by_agent='agentA'"
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["entry_type"] == "product_deployment"
    assert rows[0]["confidence"] == "high"


def test_rejects_unknown_use_case_id(tmp_path):
    c = _seed()
    p = tmp_path / "a.csv"
    _write_csv(p, [{
        "use_case_id_2024": "999",
        "tagged_by_agent": "agentA",
    }])
    with pytest.raises(ValueError, match="unknown use_case_id_2024"):
        load(c, "1", [p])


def test_rejects_invalid_enum(tmp_path):
    c = _seed()
    p = tmp_path / "a.csv"
    _write_csv(p, [{
        "use_case_id_2024": "1",
        "tagged_by_agent": "agentA",
        "entry_type": "not-a-real-type",
    }])
    with pytest.raises(ValueError, match="invalid entry_type"):
        load(c, "1", [p])


def test_rejects_invalid_wave(tmp_path):
    c = _seed()
    p = tmp_path / "a.csv"
    _write_csv(p, [{
        "use_case_id_2024": "1",
        "tagged_by_agent": "agentA",
    }])
    with pytest.raises(ValueError, match="invalid wave"):
        load(c, "99", [p])


def test_requires_tagged_by_agent(tmp_path):
    c = _seed()
    p = tmp_path / "a.csv"
    _write_csv(p, [{
        "use_case_id_2024": "1",
        "tagged_by_agent": "",
    }])
    with pytest.raises(ValueError, match="missing required column"):
        load(c, "1", [p])


def test_distinct_agents_get_distinct_rows(tmp_path):
    c = _seed()
    p = tmp_path / "a.csv"
    _write_csv(p, [
        {"use_case_id_2024": "1", "tagged_by_agent": "agentA", "entry_type": "custom_system"},
        {"use_case_id_2024": "1", "tagged_by_agent": "agentB", "entry_type": "product_deployment"},
    ])
    load(c, "0-calibration", [p])
    rows = c.execute(
        "SELECT tagged_by_agent, entry_type FROM use_case_tags_2024 "
        "WHERE use_case_id_2024=1 ORDER BY tagged_by_agent"
    ).fetchall()
    assert len(rows) == 2
    assert rows[0]["tagged_by_agent"] == "agentA"
    assert rows[1]["tagged_by_agent"] == "agentB"


def test_boolean_strings_normalize_to_int(tmp_path):
    c = _seed()
    p = tmp_path / "a.csv"
    _write_csv(p, [{
        "use_case_id_2024": "1",
        "tagged_by_agent": "agentA",
        "is_generative_ai": "true",
        "is_coding_tool": "yes",
        "is_microsoft_copilot": "false",
    }])
    load(c, "1", [p])
    row = c.execute(
        "SELECT is_generative_ai, is_coding_tool, is_microsoft_copilot "
        "FROM use_case_tags_2024 WHERE use_case_id_2024=1"
    ).fetchone()
    assert row["is_generative_ai"] == 1
    assert row["is_coding_tool"] == 1
    assert row["is_microsoft_copilot"] == 0
