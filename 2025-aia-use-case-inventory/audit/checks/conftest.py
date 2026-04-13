"""pytest fixtures for audit/checks/.

Mirrors the read-only sqlite `conn` fixture from tests/conftest.py so that
audit checks can run as a discoverable suite without depending on tests/
import order. Both fixtures point at the same DB file in read-only URI mode.
"""

import sqlite3
from pathlib import Path

import pytest

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "federal_ai_inventory_2025.db"


@pytest.fixture(scope="session")
def conn():
    c = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    yield c
    c.close()
