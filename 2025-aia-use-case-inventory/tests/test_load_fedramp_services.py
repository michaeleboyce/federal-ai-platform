"""Live-DB invariants for the fedramp_authorized_services mirror.

The mirror is populated by load_fedramp.py from the marketplace DB's
product_authorized_services (sourced from the raw export's service_last_90 +
all_others fields — NOT the always-empty authorized_services field). Guarded
skips keep the suite green on a DB built before the services ingest.
"""

import pytest


def _has_table(conn, name: str) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone())


@pytest.fixture()
def services_conn(conn):
    if not _has_table(conn, "fedramp_authorized_services"):
        pytest.skip("fedramp_authorized_services not present in this DB build")
    return conn


def test_services_mirror_populated(services_conn):
    n = services_conn.execute(
        "SELECT COUNT(*) FROM fedramp_authorized_services"
    ).fetchone()[0]
    assert n >= 1900, f"services mirror suspiciously small: {n}"


def test_services_mirror_no_orphans(services_conn):
    n = services_conn.execute("""
        SELECT COUNT(*) FROM fedramp_authorized_services s
        LEFT JOIN fedramp_products p ON p.fedramp_id = s.fedramp_id
        WHERE p.fedramp_id IS NULL""").fetchone()[0]
    assert n == 0


def test_services_mirror_recency_enum(services_conn):
    rows = services_conn.execute(
        "SELECT DISTINCT recency FROM fedramp_authorized_services "
        "WHERE recency NOT IN ('last_90', 'older')"
    ).fetchall()
    assert rows == [], rows


def test_bedrock_present_in_mirror(services_conn):
    hosts = [r[0] for r in services_conn.execute("""
        SELECT p.cso FROM fedramp_authorized_services s
        JOIN fedramp_products p ON p.fedramp_id = s.fedramp_id
        WHERE s.service = 'Amazon Bedrock'""")]
    assert any(c.startswith("AWS US East/West") for c in hosts), hosts
