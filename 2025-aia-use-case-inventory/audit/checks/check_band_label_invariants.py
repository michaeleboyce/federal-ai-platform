"""Band-label + workforce invariants for the stratified seat model.

These run as part of `make check` once the band_labels_2026-07 pass has
been applied. They guard the properties the /experience seat model
depends on:

  1. Every banded consolidated row carries a population label.
  2. Every 10k+ band row (81% of seat mass) has been Fable-audited.
  3. Label vocabularies stay within the m017 CHECK constraints (defense
     in depth — the CHECKs exist, but a future migration could loosen).
  4. agency_workforce_profile has no orphans and exactly one row per
     organization (the 2026-07 duplication bug must never return).
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "federal_ai_inventory_2025.db"

POPULATION_RE = re.compile(
    r"^(all_staff|office_staff|single_component|unknown|occupation:[a-z0-9_]+)$"
)


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        yield c
    finally:
        c.close()


def _labels_applied(conn) -> bool:
    return (
        conn.execute(
            "SELECT COUNT(*) FROM consolidated_band_labels"
        ).fetchone()[0]
        > 0
    )


def test_every_banded_row_labeled(conn):
    if not _labels_applied(conn):
        pytest.skip("band labels not applied yet")
    missing = conn.execute(
        """
        SELECT COUNT(*) FROM consolidated_use_cases c
         WHERE c.estimated_licenses_users IS NOT NULL
           AND c.estimated_licenses_users != ''
           AND NOT EXISTS (SELECT 1 FROM consolidated_band_labels l
                            WHERE l.consolidated_use_case_id = c.id)
        """
    ).fetchone()[0]
    assert missing == 0, f"{missing} banded rows unlabeled"


def test_big_band_rows_all_audited(conn):
    """The 10k+ rows carry 81% of seat mass — 100% Fable-audit required."""
    if not _labels_applied(conn):
        pytest.skip("band labels not applied yet")
    unaudited = conn.execute(
        """
        SELECT COUNT(*) FROM consolidated_use_cases c
          JOIN consolidated_band_labels l
            ON l.consolidated_use_case_id = c.id
         WHERE c.estimated_licenses_users IN ('10,000-50,000', '50,000+')
           AND l.audited = 0
        """
    ).fetchone()[0]
    assert unaudited == 0, f"{unaudited} big-band rows never audited"


def test_population_vocabulary(conn):
    if not _labels_applied(conn):
        pytest.skip("band labels not applied yet")
    bad = conn.execute(
        "SELECT slug, population FROM consolidated_band_labels"
    ).fetchall()
    offenders = [
        (slug, pop) for slug, pop in bad if not POPULATION_RE.match(pop or "")
    ]
    assert not offenders, f"bad population values: {offenders[:5]}"


def test_workforce_no_orphans_no_duplicates(conn):
    rows, orphans = conn.execute(
        """
        SELECT COUNT(*), SUM(fo.id IS NULL)
          FROM agency_workforce_profile p
          LEFT JOIN federal_organizations fo ON fo.id = p.organization_id
        """
    ).fetchone()
    assert rows > 0, "agency_workforce_profile is empty"
    assert (orphans or 0) == 0, f"{orphans} orphaned workforce rows"
    dupes = conn.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT organization_id FROM agency_workforce_profile
             GROUP BY organization_id HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]
    assert dupes == 0, f"{dupes} organizations with duplicate workforce rows"


def test_agency_level_denominators_cover_banded_agencies(conn):
    """Every agency with banded rows should have a level='agency'
    denominator (soft floor: allow a small unresolved tail)."""
    total, covered = conn.execute(
        """
        SELECT COUNT(*), SUM(has_wf) FROM (
            SELECT c.agency_id,
                   EXISTS(SELECT 1 FROM agency_workforce_profile w
                           WHERE w.agency_id = c.agency_id
                             AND w.level = 'agency') AS has_wf
              FROM consolidated_use_cases c
             WHERE c.estimated_licenses_users IS NOT NULL
               AND c.estimated_licenses_users != ''
             GROUP BY c.agency_id
        )
        """
    ).fetchone()
    assert covered >= total - 5, (
        f"only {covered}/{total} banded agencies have workforce denominators"
    )
