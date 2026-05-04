"""One-shot in-place migration: re-normalize `use_cases.topic_area` using
`auto_tag.normalize_topic_area`.

Future loads run the normalizer at ingest (via `load_inventories.py`), so
this script exists only to bring the live DB up to parity without a full
`make fix`. Idempotent — running twice is a no-op (second run reports 0
changes).

Usage:
    python scripts/normalize_topic_areas_inplace.py [--db PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from auto_tag import normalize_topic_area  # noqa: E402

DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB,
                        help=f"Path to SQLite DB (default: {DEFAULT_DB})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would change without writing.")
    args = parser.parse_args()

    if not args.db.exists():
        print(f"DB not found: {args.db}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.db)
    try:
        before_distinct = conn.execute(
            "SELECT COUNT(DISTINCT topic_area) FROM use_cases"
        ).fetchone()[0]

        rows = conn.execute(
            "SELECT id, topic_area FROM use_cases"
        ).fetchall()

        updates: list[tuple[str | None, int]] = []
        change_summary: dict[tuple[str | None, str | None], int] = {}
        for row_id, current in rows:
            normalized = normalize_topic_area(current)
            if normalized != current:
                updates.append((normalized, row_id))
                key = (current, normalized)
                change_summary[key] = change_summary.get(key, 0) + 1

        print(f"DB: {args.db}")
        print(f"Rows scanned: {len(rows)}")
        print(f"Distinct topic_area before: {before_distinct}")
        print(f"Rows needing update: {len(updates)}")
        if change_summary:
            print("\nChanges (before -> after, count):")
            for (before, after), count in sorted(
                change_summary.items(), key=lambda kv: -kv[1]
            ):
                print(f"  {before!r} -> {after!r}: {count}")

        if args.dry_run:
            print("\n--dry-run set; no writes performed.")
            return 0

        if updates:
            conn.executemany(
                "UPDATE use_cases SET topic_area = ? WHERE id = ?",
                updates,
            )
            conn.commit()

        after_distinct = conn.execute(
            "SELECT COUNT(DISTINCT topic_area) FROM use_cases"
        ).fetchone()[0]
        print(f"\nDistinct topic_area after:  {after_distinct}")
        print(f"Rows updated: {len(updates)}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
