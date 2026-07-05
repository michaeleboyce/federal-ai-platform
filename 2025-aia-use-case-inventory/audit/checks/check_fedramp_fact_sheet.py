"""Machine-enforced pins for fact_sheet.md §7 (FedRAMP — authorization vs adoption).

Every number the article's FedRAMP section cites is pinned here against the
live DB, so a marketplace-snapshot refresh (or a services relabel) that
moves a figure fails `make check` instead of silently stranding the fact
sheet. WHEN A NEW SNAPSHOT LANDS: update fact_sheet.md §7, the drop-in
draft (fedramp_section_draft.md), and these pins together.

Snapshot pinned: 2026-06-12. Runs under pytest (collected by `make check`).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "federal_ai_inventory_2025.db"

FRONTIER_TRIO = (
    "ChatGPT Enterprise and API Platform",
    "Gemini for Government",
    "Perplexity Enterprise and API Platform",
)


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    yield c
    c.close()


def _scalar(conn, sql: str, params=()):
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else None


def test_beat1_core_ai_listing_counts(conn):
    """46 core-AI listings, 35 authorized, 26 never spread past one ATO."""
    assert _scalar(conn, "SELECT COUNT(*) FROM fedramp_ai_classification WHERE category='core_ai'") == 46
    assert _scalar(conn, """
        SELECT COUNT(*) FROM fedramp_ai_classification c
        JOIN fedramp_products p USING(fedramp_id)
        WHERE c.category='core_ai' AND p.status='FedRAMP Authorized'""") == 35
    single = _scalar(conn, """
        WITH pp AS (
          SELECT c.fedramp_id,
                 (SELECT COUNT(DISTINCT a.agency_id) FROM fedramp_authorizations a
                   WHERE a.fedramp_id=c.fedramp_id AND a.agency_id IS NOT NULL) n
            FROM fedramp_ai_classification c
            JOIN fedramp_products p USING(fedramp_id)
           WHERE c.category='core_ai' AND p.status='FedRAMP Authorized')
        SELECT SUM(n<=1) FROM pp""")
    assert single == 26


def test_beat1b_unlinked_split(conn):
    """203 unlinked AI listings = 156 authorized + 47 pipeline (guardrail 8).

    155→156 on 2026-07-05: readiness v1.2 removed the bare 'SEARCH' alias
    from the Aretec SEARCH catalog entry, which had false-matched FedRAMP
    listing FR2406760385 (Clarivate CIPAI-ISP, a USPTO patent-search
    platform) to an SEC-internal tool. That listing is now correctly
    unlinked."""
    row = conn.execute("""
        SELECT SUM(p.status='FedRAMP Authorized'),
               SUM(p.status!='FedRAMP Authorized')
          FROM fedramp_ai_classification c
          JOIN fedramp_products p USING(fedramp_id)
         WHERE c.category IN ('core_ai','ai_featured')
           AND c.fedramp_id NOT IN (SELECT fedramp_id FROM fedramp_product_links)
    """).fetchone()
    assert tuple(row) == (156, 47)


def test_beat2_frontier_trio_zero_reuse(conn):
    """The 20x trio: authorized, zero recorded reuses at the pinned snapshot."""
    rows = conn.execute(
        f"""SELECT cso, status, COALESCE(reuse_count,0) FROM fedramp_products
            WHERE cso IN ({','.join('?' * len(FRONTIER_TRIO))})""",
        FRONTIER_TRIO,
    ).fetchall()
    assert len(rows) == 3, rows
    for cso, status, reuse in rows:
        assert status == "FedRAMP Authorized", (cso, status)
        assert reuse == 0, (cso, reuse)


def test_beat3b_service_labels_and_qc(conn):
    """1,591 labeled services (129/122/1,340); no AI label ships un-reviewed."""
    row = conn.execute("""
        SELECT COUNT(*), SUM(category='core_ai'), SUM(category='ai_featured'),
               SUM(category='not_ai')
          FROM fedramp_ai_service_classification""").fetchone()
    assert tuple(row) == (1591, 129, 122, 1340)
    unreviewed = _scalar(conn, """
        SELECT COUNT(*) FROM fedramp_ai_service_classification
         WHERE category IN ('core_ai','ai_featured') AND source='llm'""")
    assert unreviewed == 0


def test_beat3b_shelf_counts(conn):
    """129 core-AI services / 34 host packages / 46 agencies in reach."""
    row = conn.execute("""
        SELECT COUNT(DISTINCT s.service), COUNT(DISTINCT s.fedramp_id)
          FROM fedramp_authorized_services s
          JOIN fedramp_ai_service_classification c
            ON c.service = s.service AND c.category = 'core_ai'""").fetchone()
    assert tuple(row) == (129, 34)
    agencies = _scalar(conn, """
        SELECT COUNT(DISTINCT al.inventory_agency_id)
          FROM fedramp_authorized_services s
          JOIN fedramp_ai_service_classification c
            ON c.service = s.service AND c.category = 'core_ai'
          JOIN fedramp_authorizations a ON a.fedramp_id = s.fedramp_id
          JOIN fedramp_agency_links al ON al.fedramp_agency_id = a.agency_id""")
    assert agencies == 46


def test_beat3b_bedrock_moderate_and_high(conn):
    """Bedrock in scope at Moderate (AWS East/West) AND High (GovCloud)."""
    levels = {
        r[0]
        for r in conn.execute("""
            SELECT p.impact_level FROM fedramp_authorized_services s
            JOIN fedramp_products p USING(fedramp_id)
            WHERE s.service = 'Amazon Bedrock'""")
    }
    assert {"Moderate", "High"} <= levels, levels


def test_beat4_reach_spot_pins(conn):
    """Per-agency reach pins for the article's table rows."""
    expected = {"DOJ": 63, "HHS": 110, "Treasury": 98, "State": 93,
                "HUD": 41, "SBA": 41, "DOE": 99}
    rows = dict(conn.execute("""
        SELECT ia.abbreviation, COUNT(DISTINCT s.service)
          FROM fedramp_authorized_services s
          JOIN fedramp_ai_service_classification c
            ON c.service = s.service AND c.category = 'core_ai'
          JOIN fedramp_authorizations a ON a.fedramp_id = s.fedramp_id
          JOIN fedramp_agency_links al ON al.fedramp_agency_id = a.agency_id
          JOIN agencies ia ON ia.id = al.inventory_agency_id
         WHERE ia.abbreviation IN ('DOJ','HHS','Treasury','State','HUD','SBA','DOE')
         GROUP BY ia.abbreviation""").fetchall())
    assert rows == expected, rows
