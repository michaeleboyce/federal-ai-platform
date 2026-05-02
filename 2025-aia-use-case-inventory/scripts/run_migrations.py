"""Run ordered, idempotent SQLite migrations."""
from __future__ import annotations

import importlib
import pkgutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
MIGRATIONS_PACKAGE = "migrations"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_ledger(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_id TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )


def _migration_modules():
    package = importlib.import_module(MIGRATIONS_PACKAGE)
    modules = []
    for info in pkgutil.iter_modules(package.__path__):
        if info.ispkg or not info.name.startswith("m"):
            continue
        modules.append(importlib.import_module(f"{MIGRATIONS_PACKAGE}.{info.name}"))
    return sorted(modules, key=lambda m: getattr(m, "MIGRATION_ID", m.__name__))


def apply_migrations(conn: sqlite3.Connection | None = None) -> list[str]:
    own = conn is None
    if conn is None:
        conn = _open()
    applied: list[str] = []
    try:
        _ensure_ledger(conn)
        seen = {
            r["migration_id"]
            for r in conn.execute("SELECT migration_id FROM schema_migrations")
        }
        for mod in _migration_modules():
            migration_id = mod.MIGRATION_ID
            if migration_id in seen:
                continue
            with conn:
                mod.apply(conn)
                conn.execute(
                    "INSERT INTO schema_migrations (migration_id) VALUES (?)",
                    (migration_id,),
                )
            applied.append(migration_id)
        return applied
    finally:
        if own:
            conn.close()


def main() -> int:
    applied = apply_migrations()
    if applied:
        print("Applied migrations:")
        for migration_id in applied:
            print(f"  {migration_id}")
    else:
        print("No pending migrations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
