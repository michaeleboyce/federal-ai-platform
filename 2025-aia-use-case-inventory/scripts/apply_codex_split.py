"""Split the conflated "OpenAI Codex" product into two distinct records.

The catalog seed (`data/expanded_product_catalog.csv`) and the May 2026
linkage pass (`audit/linkage_pass_2026-05/`) both create a single product
named "OpenAI Codex". That name conflates two genuinely different things:

  * the deprecated 2021 code-generation model that powered the original
    GitHub Copilot (what DOE's "GitHub Copilot with the OpenAI Codex"
    individually-reported use case refers to), and
  * the agentic Codex CLI OpenAI shipped in April 2025 (the peer to
    Anthropic's Claude Code, and the most plausible referent of OPM's
    bare "Codex" entry in the consolidated COTS file).

This script is the sole authority for both products. It runs late in
`make fix` (after both linkage passes and recategorization) and:

  1. ensures "OpenAI Codex (legacy model)" exists — by renaming the
     bare "OpenAI Codex" the upstream seeds create, so any links those
     passes attached (e.g. the DOE use case) carry over untouched;
  2. ensures "OpenAI Codex CLI" exists, with aliases;
  3. links OPM's consolidated COTS row to the CLI product.

The OPM row is resolved by its content-derived `slug`, NOT by row id:
the linkage pass references a now-stale integer id (10480), which is why
the OPM link silently never lands on a rebuild. Slugs are stable across
rebuilds; ids are not.

Idempotent — safe to re-run against an already-split DB.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"

BARE = "OpenAI Codex"
LEGACY = "OpenAI Codex (legacy model)"
CLI = "OpenAI Codex CLI"
OPM_SLUG = "opm-generating-code-using-ai"

LEGACY_DESC = (
    "Deprecated 2021 OpenAI code-generation model that powered the original "
    "GitHub Copilot; sunset March 2023. Distinct from the 2025 OpenAI Codex CLI."
)
CLI_DESC = (
    "OpenAI's agentic coding CLI, released April 2025. Terminal-based AI "
    "software-engineering agent; peer to Anthropic's Claude Code. Distinct "
    "from the deprecated 2021 Codex model."
)
OPM_EVIDENCE = (
    "OPM consolidated COTS entry 'Generating code using AI' lists "
    "commercial_product 'Codex'; in a 2025 code-generation context this reads "
    "as the OpenAI Codex CLI, not the deprecated 2021 model."
)


def _ensure_alias(conn: sqlite3.Connection, product_id: int, alias: str,
                  stats: dict[str, int]) -> None:
    """Insert an alias unless one already exists (UNIQUE(alias_text))."""
    row = conn.execute(
        "SELECT product_id FROM product_aliases WHERE alias_text = ?", (alias,)
    ).fetchone()
    if row is not None:
        if row[0] != product_id:
            stats["alias_collisions"] += 1
        return
    conn.execute(
        "INSERT INTO product_aliases (product_id, alias_text) VALUES (?, ?)",
        (product_id, alias),
    )
    stats["aliases_inserted"] += 1


def _merge_product(conn: sqlite3.Connection, src_id: int, dst_id: int) -> None:
    """Repoint every reference from src_id to dst_id, then delete src.

    Defensive path: a normal `make fix` never produces both the bare and the
    renamed product in the same DB. This keeps the script bulletproof if it
    is ever run twice against a hand-mutated snapshot.
    """
    conn.execute(
        "UPDATE OR IGNORE product_aliases SET product_id = ? WHERE product_id = ?",
        (dst_id, src_id),
    )
    conn.execute("DELETE FROM product_aliases WHERE product_id = ?", (src_id,))
    for table, col in (
        ("use_case_products", "use_case_id"),
        ("consolidated_use_case_products", "consolidated_use_case_id"),
    ):
        conn.execute(
            f"UPDATE OR IGNORE {table} SET product_id = ? WHERE product_id = ?",
            (dst_id, src_id),
        )
        conn.execute(f"DELETE FROM {table} WHERE product_id = ?", (src_id,))
    conn.execute(
        "UPDATE products SET parent_product_id = ? WHERE parent_product_id = ?",
        (dst_id, src_id),
    )
    # (The scalar use_cases/consolidated product_id caches were dropped by
    # m025 — the edge updates above are the complete re-point.)
    conn.execute("DELETE FROM products WHERE id = ?", (src_id,))


def run(conn: sqlite3.Connection) -> dict[str, int]:
    """Apply the split. Returns a stats dict; caller commits."""
    stats = {
        "renamed": 0,
        "legacy_created": 0,
        "merged_duplicate": 0,
        "cli_created": 0,
        "aliases_inserted": 0,
        "alias_collisions": 0,
        "opm_linked": 0,
    }

    def _pid(name: str) -> int | None:
        row = conn.execute(
            "SELECT id FROM products WHERE canonical_name = ?", (name,)
        ).fetchone()
        return row[0] if row else None

    # 1. Ensure the legacy-model product exists.
    bare_id = _pid(BARE)
    legacy_id = _pid(LEGACY)
    if bare_id is not None and legacy_id is None:
        conn.execute(
            "UPDATE products SET canonical_name = ?, description = ? WHERE id = ?",
            (LEGACY, LEGACY_DESC, bare_id),
        )
        legacy_id = bare_id
        stats["renamed"] = 1
    elif bare_id is not None and legacy_id is not None:
        _merge_product(conn, bare_id, legacy_id)
        conn.execute(
            "UPDATE products SET description = ? WHERE id = ?",
            (LEGACY_DESC, legacy_id),
        )
        stats["merged_duplicate"] = 1
    elif legacy_id is None:
        conn.execute(
            """INSERT INTO products
                   (canonical_name, vendor, product_type,
                    is_generative_ai, description)
               VALUES (?, ?, 'coding_assistant', 1, ?)""",
            (LEGACY, "OpenAI", LEGACY_DESC),
        )
        legacy_id = conn.execute(
            "SELECT id FROM products WHERE canonical_name = ?", (LEGACY,)
        ).fetchone()[0]
        stats["legacy_created"] = 1

    _ensure_alias(conn, legacy_id, LEGACY, stats)
    _ensure_alias(conn, legacy_id, BARE, stats)

    # 2. Ensure the 2025 CLI product exists.
    cli_id = _pid(CLI)
    if cli_id is None:
        conn.execute(
            """INSERT INTO products
                   (canonical_name, vendor, product_type,
                    is_generative_ai, description)
               VALUES (?, ?, 'coding_assistant', 1, ?)""",
            (CLI, "OpenAI", CLI_DESC),
        )
        cli_id = conn.execute(
            "SELECT id FROM products WHERE canonical_name = ?", (CLI,)
        ).fetchone()[0]
        stats["cli_created"] = 1

    _ensure_alias(conn, cli_id, CLI, stats)
    _ensure_alias(conn, cli_id, "Codex CLI", stats)

    # 3. Wire OPM's consolidated COTS row to the CLI product, by stable slug.
    opm = conn.execute(
        "SELECT id FROM consolidated_use_cases WHERE slug = ?", (OPM_SLUG,)
    ).fetchone()
    if opm is not None:
        cur = conn.execute(
            """INSERT OR IGNORE INTO consolidated_use_case_products
                   (consolidated_use_case_id, product_id,
                    evidence_text, confidence)
               VALUES (?, ?, ?, 'inferred')""",
            (opm[0], cli_id, OPM_EVIDENCE),
        )
        stats["opm_linked"] = cur.rowcount
        # (Scalar consolidated_use_cases.product_id cache dropped by m025 —
        # the edge insert above is the linkage.)

    return stats


def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            stats = run(conn)
    finally:
        conn.close()
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
