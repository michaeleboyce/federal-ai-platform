"""Guard: the band_labels_2026-07 pass must keep resolving after rebuilds.

Same failure mode as test_retag_apply_resolution.py: label CSVs written
against one DB generation, ids rotated by `make fix`, apply silently
no-ops. Band labels resolve primarily by the deterministic
`consolidated_use_cases.slug`, so these tests assert (a) every label slug
still resolves against the live DB, (b) every banded row has a label once
the pass has landed, and (c) the apply module's validation rejects bad
vocabulary. Read-only.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from apply_band_labels import (  # noqa: E402
    MAX_UNRESOLVED,
    PASS_DIR,
    _validate,
    load_labels,
)

DB = ROOT / "data" / "federal_ai_inventory_2025.db"

_HAS_LABELS = bool(sorted(PASS_DIR.glob("labels_*.csv")))

pytestmark = pytest.mark.skipif(
    not _HAS_LABELS, reason="band_labels_2026-07 batches not landed yet"
)


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        yield c
    finally:
        c.close()


def test_labels_load_clean():
    labels, errors = load_labels()
    assert not errors, f"label CSVs invalid: {errors[:10]}"
    assert labels


def test_label_slugs_resolve(conn):
    labels, _ = load_labels()
    live = {
        r[0]
        for r in conn.execute(
            """
            SELECT slug FROM consolidated_use_cases
             WHERE estimated_licenses_users IS NOT NULL
               AND estimated_licenses_users != ''
            """
        )
    }
    unresolved = [s for s in labels if s not in live]
    frac = len(unresolved) / max(1, len(labels))
    assert frac <= MAX_UNRESOLVED, (
        f"{len(unresolved)} label slugs unresolved ({frac:.1%}); "
        f"first: {unresolved[:5]}"
    )


def test_every_banded_row_labeled(conn):
    """Once applied, consolidated_band_labels covers every banded row."""
    n_labels = conn.execute(
        "SELECT COUNT(*) FROM consolidated_band_labels"
    ).fetchone()[0]
    if n_labels == 0:
        pytest.skip("labels not applied to this DB yet")
    missing = conn.execute(
        """
        SELECT COUNT(*) FROM consolidated_use_cases c
         WHERE c.estimated_licenses_users IS NOT NULL
           AND c.estimated_licenses_users != ''
           AND NOT EXISTS (SELECT 1 FROM consolidated_band_labels l
                            WHERE l.consolidated_use_case_id = c.id)
        """
    ).fetchone()[0]
    assert missing == 0, f"{missing} banded rows have no band label"


def test_input_coverage():
    """Every frozen input row appears in the label batches."""
    labels, _ = load_labels()
    with (PASS_DIR / "input.csv").open() as f:
        input_slugs = {r["slug"] for r in csv.DictReader(f)}
    missing = input_slugs - set(labels)
    assert not missing, f"{len(missing)} input rows unlabeled: {sorted(missing)[:5]}"


def test_validation_rejects_bad_vocab():
    bad = {
        "slug": "x",
        "unit_counted": "people",  # not in vocab
        "population": "everyone",  # not in vocab
        "org_scope": "enterprise",
        "stratum": "general",
        "confidence": "high",
    }
    errs = _validate(bad, "unit-test")
    assert any("unit_counted" in e for e in errs)
    assert any("population" in e for e in errs)


def test_validation_accepts_occupation_tail():
    ok = {
        "slug": "x",
        "unit_counted": "employees",
        "population": "occupation:attorneys",
        "org_scope": "component",
        "stratum": "legal",
        "confidence": "medium",
    }
    assert _validate(ok, "unit-test") == []
