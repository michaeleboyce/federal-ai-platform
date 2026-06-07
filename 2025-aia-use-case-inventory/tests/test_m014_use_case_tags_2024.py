"""Tests for migrations/m014_use_case_tags_2024.py — creates the
`use_case_tags_2024` table + `use_case_tags_2024_canonical` view.
Idempotent."""
import sqlite3

from migrations import m009_use_cases_2024 as m009
from migrations import m014_use_case_tags_2024 as m014


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    # m009 has a FK to agencies — stub the agencies table.
    c.execute(
        "CREATE TABLE agencies (id INTEGER PRIMARY KEY, "
        "abbreviation TEXT, full_name TEXT)"
    )
    c.execute("INSERT INTO agencies(id, abbreviation) VALUES (1, 'HHS')")
    m009.apply(c)
    return c


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _indexes(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA index_list({table})").fetchall()]


def _seed_use_case(c: sqlite3.Connection, name: str = "Test") -> int:
    c.execute(
        "INSERT INTO use_cases_2024 (agency_id, source_file, slug, "
        "use_case_name) VALUES (1, 'test.csv', ?, ?)",
        (name.lower(), name),
    )
    return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def test_creates_table_with_expected_columns():
    c = _conn()
    m014.apply(c)
    cols = _columns(c, "use_case_tags_2024")
    expected = {
        "id", "use_case_id_2024",
        "entry_type", "is_product_capability_entry", "product_capability",
        "is_general_llm_access", "is_coding_tool", "is_cots_commercial",
        "tool_product_name", "tool_vendor",
        "ai_sophistication", "is_generative_ai", "is_frontier_model",
        "deployment_scope", "scope_detail", "is_enterprise_wide",
        "estimated_user_count",
        "architecture_type", "has_model_training",
        "cots_product_name", "cots_vendor",
        "is_microsoft_copilot", "is_openai", "is_anthropic", "is_google",
        "is_github_copilot", "is_aws_ai",
        "use_type", "is_public_facing",
        "has_meaningful_risk_docs", "high_impact_designation",
        "deployment_environment", "has_ato_or_fedramp",
        "wave", "tagged_by_agent", "reasoning", "quality_flags_json",
        "confidence", "created_at", "updated_at",
    }
    assert expected.issubset(set(cols)), expected - set(cols)


def test_creates_expected_indexes():
    c = _conn()
    m014.apply(c)
    idx = set(_indexes(c, "use_case_tags_2024"))
    expected = {
        "idx_uct2024_use_case", "idx_uct2024_wave",
        "idx_uct2024_is_gen_ai", "idx_uct2024_scope",
        "idx_uct2024_entry_type", "idx_uct2024_uc_wave",
    }
    # SQLite also creates an autoindex for the UNIQUE constraint, prefixed
    # `sqlite_autoindex_…`. We only assert our named indexes are present.
    assert expected.issubset(idx), expected - idx


def test_apply_is_idempotent():
    c = _conn()
    m014.apply(c)
    m014.apply(c)  # must not raise
    assert "use_case_tags_2024" in {
        r["name"]
        for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def test_canonical_view_picks_wave3_over_wave1():
    c = _conn()
    m014.apply(c)
    uc = _seed_use_case(c, "wave3-test")
    c.execute(
        "INSERT INTO use_case_tags_2024 (use_case_id_2024, wave, "
        "tagged_by_agent, entry_type) VALUES (?, '1', 'agentA', 'custom_system')",
        (uc,),
    )
    c.execute(
        "INSERT INTO use_case_tags_2024 (use_case_id_2024, wave, "
        "tagged_by_agent, entry_type) VALUES (?, '3', 'agentR', 'product_deployment')",
        (uc,),
    )
    canonical = c.execute(
        "SELECT entry_type FROM use_case_tags_2024_canonical "
        "WHERE use_case_id_2024 = ?",
        (uc,),
    ).fetchall()
    assert len(canonical) == 1
    assert canonical[0]["entry_type"] == "product_deployment"


def test_canonical_view_picks_wave2a_over_wave1():
    c = _conn()
    m014.apply(c)
    uc = _seed_use_case(c, "wave2-test")
    c.execute(
        "INSERT INTO use_case_tags_2024 (use_case_id_2024, wave, "
        "tagged_by_agent, entry_type) VALUES (?, '1', 'agentA', 'custom_system')",
        (uc,),
    )
    c.execute(
        "INSERT INTO use_case_tags_2024 (use_case_id_2024, wave, "
        "tagged_by_agent, entry_type) VALUES (?, '2a', 'qa1', 'bespoke_application')",
        (uc,),
    )
    canonical = c.execute(
        "SELECT entry_type FROM use_case_tags_2024_canonical "
        "WHERE use_case_id_2024 = ?",
        (uc,),
    ).fetchall()
    assert len(canonical) == 1
    assert canonical[0]["entry_type"] == "bespoke_application"


def test_canonical_view_excludes_calibration_only_rows():
    c = _conn()
    m014.apply(c)
    uc = _seed_use_case(c, "calib-only")
    c.execute(
        "INSERT INTO use_case_tags_2024 (use_case_id_2024, wave, "
        "tagged_by_agent, entry_type) "
        "VALUES (?, '0-calibration', 'agentA', 'custom_system')",
        (uc,),
    )
    rows = c.execute(
        "SELECT 1 FROM use_case_tags_2024_canonical "
        "WHERE use_case_id_2024 = ?",
        (uc,),
    ).fetchall()
    assert rows == []


def test_unique_constraint_blocks_duplicate_agent_in_same_wave():
    c = _conn()
    m014.apply(c)
    uc = _seed_use_case(c, "dup-test")
    c.execute(
        "INSERT INTO use_case_tags_2024 (use_case_id_2024, wave, "
        "tagged_by_agent) VALUES (?, '1', 'agentA')",
        (uc,),
    )
    import pytest
    with pytest.raises(sqlite3.IntegrityError):
        c.execute(
            "INSERT INTO use_case_tags_2024 (use_case_id_2024, wave, "
            "tagged_by_agent) VALUES (?, '1', 'agentA')",
            (uc,),
        )


def test_fk_enforced_against_use_cases_2024():
    c = _conn()
    m014.apply(c)
    import pytest
    with pytest.raises(sqlite3.IntegrityError):
        c.execute(
            "INSERT INTO use_case_tags_2024 (use_case_id_2024, wave, "
            "tagged_by_agent) VALUES (999999, '1', 'agentA')"
        )
