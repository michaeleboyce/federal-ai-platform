"""Seed the federal_organizations table from data/federal_hierarchy_seed.py.

Two-phase insert (per the federal-ai-platform reference, lines 391-441):
  1. INSERT each row with NULL hierarchy_path
  2. UPDATE its hierarchy_path to "<parent_path>/<insert_id>/" once we know the
     auto-assigned id

Idempotent: re-running clears all rows seeded by this script (we tag them with
seed_signature in `description` so manual additions survive) and reseeds.

Also populates `legacy_agency_id` on department/independent rows by matching
`agencies.abbreviation`.
"""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"

sys.path.insert(0, str(ROOT))
from data.federal_hierarchy_seed import ORG_TREE  # noqa: E402

SEED_SIGNATURE = "[seeded:federal_hierarchy_v1]"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "org"


def make_slug(node: dict, parent_slug: str | None) -> str:
    """Slug strategy: use abbreviation when present, prefixed by parent abbrev
    for sub-agencies/offices to avoid collisions ("hhs-ocio" vs "dhs-ocio").
    Top-level orgs use just the abbrev (e.g. "hhs").
    """
    abbr = node.get("abbreviation")
    name = node["name"]
    own = slugify(abbr or name)
    if parent_slug is None:
        return own
    return f"{parent_slug}-{own}"


def clear_seeded_rows(conn: sqlite3.Connection) -> int:
    """Delete previously-seeded rows (children-first to respect FKs)."""
    # Delete by descending depth so children leave before parents.
    rows = conn.execute(
        "SELECT id FROM federal_organizations WHERE description LIKE ? ORDER BY depth DESC",
        (f"%{SEED_SIGNATURE}%",),
    ).fetchall()
    n = 0
    for row in rows:
        conn.execute("DELETE FROM federal_organizations WHERE id = ?", (row["id"],))
        n += 1
    return n


def insert_node(
    conn: sqlite3.Connection,
    node: dict,
    parent_id: int | None,
    parent_slug: str | None,
    parent_path: str,
    depth: int,
) -> int:
    slug = make_slug(node, parent_slug)
    abbr = node.get("abbreviation")
    description = (node.get("description") or "") + f" {SEED_SIGNATURE}"
    aliases = node.get("aliases") or []
    if aliases:
        # Use ">>" as inter-alias separator since real names contain spaces,
        # commas, and pipes. Wrap in << >> markers for unambiguous parsing.
        description += " aliases=<<" + ">>".join(aliases) + ">>"
    cur = conn.execute(
        """
        INSERT INTO federal_organizations
            (name, short_name, abbreviation, slug, parent_id, level,
             hierarchy_path, depth, is_cfo_act_agency, is_cabinet_department,
             description, website)
        VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)
        """,
        (
            node["name"], node.get("short_name"), abbr, slug, parent_id, node["level"],
            depth,
            int(node.get("is_cfo_act_agency", False)),
            int(node.get("is_cabinet_department", False)),
            description.strip(),
            node.get("website"),
        ),
    )
    new_id = cur.lastrowid
    new_path = f"{parent_path}{new_id}/"
    conn.execute(
        "UPDATE federal_organizations SET hierarchy_path = ? WHERE id = ?",
        (new_path, new_id),
    )
    for child in node.get("children") or []:
        insert_node(conn, child, new_id, slug, new_path, depth + 1)
    return new_id


def link_legacy_agency_ids(conn: sqlite3.Connection) -> int:
    """For each top-level org, set legacy_agency_id from agencies.abbreviation."""
    n = conn.execute(
        """
        UPDATE federal_organizations
        SET legacy_agency_id = (
            SELECT a.id FROM agencies a
            WHERE a.abbreviation = federal_organizations.abbreviation
        )
        WHERE parent_id IS NULL
          AND abbreviation IS NOT NULL
          AND EXISTS (
            SELECT 1 FROM agencies a WHERE a.abbreviation = federal_organizations.abbreviation
          )
        """
    ).rowcount
    return n


def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            cleared = clear_seeded_rows(conn)
            inserted = 0
            for top in ORG_TREE:
                insert_node(conn, top, parent_id=None, parent_slug=None,
                            parent_path="/", depth=0)
                inserted += 1  # top-level only; recurses for children
            # Re-count actual inserts via depth join
            total_seeded = conn.execute(
                "SELECT COUNT(*) AS n FROM federal_organizations WHERE description LIKE ?",
                (f"%{SEED_SIGNATURE}%",),
            ).fetchone()["n"]
            linked = link_legacy_agency_ids(conn)

        print(f"[seed] cleared previously-seeded rows: {cleared}")
        print(f"[seed] inserted top-level orgs: {inserted}")
        print(f"[seed] total seeded rows: {total_seeded}")
        print(f"[seed] linked legacy_agency_id on top-level orgs: {linked}")
        rows = conn.execute(
            "SELECT level, COUNT(*) AS n FROM federal_organizations GROUP BY level ORDER BY n DESC"
        ).fetchall()
        for r in rows:
            print(f"  {r['level']:>14}  {r['n']:>4}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
