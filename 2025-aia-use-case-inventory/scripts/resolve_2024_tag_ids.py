"""Re-resolve `use_case_id_2024` in agent-tagged CSVs after a DB rebuild.

The 2024 tagging workflow has subagents producing CSVs that reference
`use_cases_2024.id`. Those ids are NOT stable across rebuilds — a parallel
agent's `make fix` (or any DELETE+INSERT on `use_cases_2024`) rotates the
AUTOINCREMENT sequence. See `CLAUDE.md` § Multi-agent safety.

This script reads each agent CSV's `use_case_id_2024`, looks up the slug
in a snapshot/backup DB where the ids match the agent's view, then writes
the new id from the current live DB. Output is written in place (with a
`.bak` next to the original).

Usage:
    python3 scripts/resolve_2024_tag_ids.py \\
        --from data/federal_ai_inventory_2025.db.backup-pre-m014-... \\
        --to   data/federal_ai_inventory_2025.db \\
        audit/retag/2024-tagging/calibration/
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LIVE_DB = ROOT / "data" / "federal_ai_inventory_2025.db"


def _build_id_to_slug(db_path: Path) -> dict[int, str]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT id, slug FROM use_cases_2024"
            ).fetchall()
        }
    finally:
        conn.close()


def _build_slug_to_id(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return {
            row[1]: row[0]
            for row in conn.execute(
                "SELECT id, slug FROM use_cases_2024"
            ).fetchall()
        }
    finally:
        conn.close()


def resolve_file(
    csv_path: Path,
    old_id_to_slug: dict[int, str],
    slug_to_new_id: dict[str, int],
) -> tuple[int, int]:
    """Returns (n_rows, n_remapped). Leaves a .bak next to the file."""
    backup = csv_path.with_suffix(csv_path.suffix + ".bak")
    if not backup.exists():
        shutil.copy2(csv_path, backup)

    rows: list[dict] = []
    with backup.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            rows.append(dict(row))

    remapped = 0
    for row in rows:
        old_id = int(row["use_case_id_2024"])
        slug = old_id_to_slug.get(old_id)
        if slug is None:
            raise ValueError(
                f"{csv_path}: old id {old_id} not found in --from snapshot"
            )
        new_id = slug_to_new_id.get(slug)
        if new_id is None:
            raise ValueError(
                f"{csv_path}: slug {slug!r} (was id {old_id}) "
                "not found in --to live DB"
            )
        if new_id != old_id:
            remapped += 1
        row["use_case_id_2024"] = str(new_id)

    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)

    return len(rows), remapped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--from",
        dest="from_db",
        type=Path,
        required=True,
        help="Snapshot/backup DB whose ids match the agent CSVs",
    )
    ap.add_argument(
        "--to",
        dest="to_db",
        type=Path,
        default=DEFAULT_LIVE_DB,
        help="Live DB to remap ids into",
    )
    ap.add_argument(
        "inputs",
        type=Path,
        nargs="+",
        help="CSV files or directories of CSVs to resolve",
    )
    args = ap.parse_args()

    if not args.from_db.exists():
        print(f"missing --from DB: {args.from_db}", file=sys.stderr)
        return 1
    if not args.to_db.exists():
        print(f"missing --to DB: {args.to_db}", file=sys.stderr)
        return 1

    old_id_to_slug = _build_id_to_slug(args.from_db)
    slug_to_new_id = _build_slug_to_id(args.to_db)

    csv_paths: list[Path] = []
    for p in args.inputs:
        if p.is_dir():
            csv_paths.extend(sorted(p.glob("*.csv")))
        else:
            csv_paths.append(p)

    total_rows = 0
    total_remapped = 0
    for csv_path in csv_paths:
        rows, remapped = resolve_file(csv_path, old_id_to_slug, slug_to_new_id)
        print(f"  {csv_path}: {rows} rows, {remapped} remapped")
        total_rows += rows
        total_remapped += remapped
    print(f"total: {total_rows} rows, {total_remapped} remapped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
