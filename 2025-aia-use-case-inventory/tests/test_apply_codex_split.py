"""Tests for apply_codex_split.

Builds an in-memory DB with the products / aliases / consolidated tables
the splitter touches, seeds the upstream state (a bare "OpenAI Codex"
product plus OPM's consolidated "Codex" row), runs the split, and asserts
the two distinct products exist and the OPM row is wired to the CLI.
"""
from __future__ import annotations

import sqlite3

import pytest

from scripts import apply_codex_split as cs


def _bootstrap(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_name TEXT NOT NULL UNIQUE,
            vendor TEXT,
            product_type TEXT,
            is_generative_ai INTEGER DEFAULT 0,
            is_frontier_llm INTEGER DEFAULT 0,
            parent_product_id INTEGER REFERENCES products(id),
            description TEXT,
            notes TEXT,
            product_origin TEXT NOT NULL DEFAULT 'commercial'
        );
        CREATE TABLE product_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            alias_text TEXT NOT NULL UNIQUE
        );
        CREATE TABLE agencies (
            id INTEGER PRIMARY KEY,
            abbreviation TEXT NOT NULL UNIQUE
        );
        CREATE TABLE consolidated_use_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agency_id INTEGER NOT NULL REFERENCES agencies(id),
            slug TEXT UNIQUE,
            ai_use_case TEXT NOT NULL,
            commercial_product TEXT,
            product_id INTEGER REFERENCES products(id)
        );
        CREATE TABLE consolidated_use_case_products (
            consolidated_use_case_id INTEGER NOT NULL
                REFERENCES consolidated_use_cases(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            evidence_text TEXT,
            confidence TEXT,
            PRIMARY KEY (consolidated_use_case_id, product_id)
        );
        CREATE TABLE use_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER REFERENCES products(id)
        );
        CREATE TABLE use_case_products (
            use_case_id INTEGER NOT NULL REFERENCES use_cases(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            evidence_text TEXT,
            confidence TEXT,
            PRIMARY KEY (use_case_id, product_id)
        );
        """
    )


def _seed_upstream(conn: sqlite3.Connection) -> None:
    """Reproduce the state the catalog + linkage pass leave behind."""
    conn.execute(
        "INSERT INTO products (id, canonical_name, vendor, product_type) "
        "VALUES (1, ?, 'OpenAI', 'coding_assistant')",
        (cs.BARE,),
    )
    conn.execute(
        "INSERT INTO product_aliases (product_id, alias_text) VALUES (1, ?)",
        (cs.BARE,),
    )
    conn.execute("INSERT INTO agencies (id, abbreviation) VALUES (1, 'OPM')")
    conn.execute(
        "INSERT INTO consolidated_use_cases "
        "(agency_id, slug, ai_use_case, commercial_product) "
        "VALUES (1, ?, 'Generating code using AI.', 'Codex')",
        (cs.OPM_SLUG,),
    )


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys = ON")
    _bootstrap(c)
    yield c
    c.close()


def test_split_renames_bare_and_creates_cli(conn):
    _seed_upstream(conn)
    cs.run(conn)

    names = {r[0] for r in conn.execute("SELECT canonical_name FROM products")}
    assert cs.LEGACY in names
    assert cs.CLI in names
    assert cs.BARE not in names  # bare name fully retired


def test_legacy_keeps_the_bare_products_links(conn):
    """Renaming (not deleting) preserves links the upstream passes attached."""
    _seed_upstream(conn)
    conn.execute("INSERT INTO use_cases (id) VALUES (99)")
    conn.execute(
        "INSERT INTO use_case_products (use_case_id, product_id) VALUES (99, 1)"
    )
    cs.run(conn)

    legacy_id = conn.execute(
        "SELECT id FROM products WHERE canonical_name = ?", (cs.LEGACY,)
    ).fetchone()[0]
    linked = conn.execute(
        "SELECT product_id FROM use_case_products WHERE use_case_id = 99"
    ).fetchone()[0]
    assert linked == legacy_id


def test_opm_row_linked_to_cli_by_slug(conn):
    _seed_upstream(conn)
    cs.run(conn)

    cli_id = conn.execute(
        "SELECT id FROM products WHERE canonical_name = ?", (cs.CLI,)
    ).fetchone()[0]
    opm_id = conn.execute(
        "SELECT id FROM consolidated_use_cases WHERE slug = ?", (cs.OPM_SLUG,)
    ).fetchone()[0]

    junction = conn.execute(
        "SELECT product_id FROM consolidated_use_case_products "
        "WHERE consolidated_use_case_id = ?",
        (opm_id,),
    ).fetchall()
    assert [r[0] for r in junction] == [cli_id]

    fk = conn.execute(
        "SELECT product_id FROM consolidated_use_cases WHERE id = ?", (opm_id,)
    ).fetchone()[0]
    assert fk == cli_id


def test_cli_aliases_present(conn):
    _seed_upstream(conn)
    cs.run(conn)

    cli_id = conn.execute(
        "SELECT id FROM products WHERE canonical_name = ?", (cs.CLI,)
    ).fetchone()[0]
    aliases = {
        r[0]
        for r in conn.execute(
            "SELECT alias_text FROM product_aliases WHERE product_id = ?",
            (cli_id,),
        )
    }
    assert {"OpenAI Codex CLI", "Codex CLI"} <= aliases


def test_idempotent(conn):
    _seed_upstream(conn)
    cs.run(conn)
    first = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    cs.run(conn)
    cs.run(conn)
    second = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert first == second

    # exactly one junction row for OPM, no duplication
    n = conn.execute(
        "SELECT COUNT(*) FROM consolidated_use_case_products"
    ).fetchone()[0]
    assert n == 1


def test_runs_with_no_upstream_codex_product(conn):
    """If the catalog ever drops Codex, the script still creates both."""
    conn.execute("INSERT INTO agencies (id, abbreviation) VALUES (1, 'OPM')")
    conn.execute(
        "INSERT INTO consolidated_use_cases "
        "(agency_id, slug, ai_use_case, commercial_product) "
        "VALUES (1, ?, 'Generating code using AI.', 'Codex')",
        (cs.OPM_SLUG,),
    )
    cs.run(conn)

    names = {r[0] for r in conn.execute("SELECT canonical_name FROM products")}
    assert cs.LEGACY in names
    assert cs.CLI in names
