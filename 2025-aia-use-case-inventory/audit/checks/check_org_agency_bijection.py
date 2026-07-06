"""agencies <-> federal_organizations bijection + maturity-collapse gates.

federal_organizations is canonical for org identity/hierarchy; `agencies`
remains the physical ingest table. The bridge is
federal_organizations.legacy_agency_id — these checks keep it bijective
so the m023 agency_ai_maturity compat view (org_ai_maturity joined
through the legacy link) can never drop or duplicate an agency.
"""


def test_every_agency_has_exactly_one_legacy_linked_org(conn):
    missing = conn.execute(
        """SELECT a.abbreviation FROM agencies a
            WHERE NOT EXISTS (SELECT 1 FROM federal_organizations fo
                               WHERE fo.legacy_agency_id = a.id)"""
    ).fetchall()
    assert not missing, (
        f"{len(missing)} agencies without a legacy-linked org: "
        f"{[m[0] for m in missing]} — add to hierarchy seed / "
        "SPECIAL_LEGACY_LINKS in scripts/seed_federal_hierarchy.py"
    )
    dups = conn.execute(
        """SELECT legacy_agency_id, COUNT(*) AS n FROM federal_organizations
            WHERE legacy_agency_id IS NOT NULL
            GROUP BY legacy_agency_id HAVING n > 1"""
    ).fetchall()
    assert not dups, (
        f"{len(dups)} agencies linked from multiple orgs: {dups[:5]}"
    )


def test_legacy_links_resolve(conn):
    dangling = conn.execute(
        """SELECT COUNT(*) FROM federal_organizations fo
            WHERE fo.legacy_agency_id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM agencies a
                               WHERE a.id = fo.legacy_agency_id)"""
    ).fetchone()[0]
    assert dangling == 0, f"{dangling} legacy_agency_id values dangle"


def test_fact_table_org_fks_resolve(conn):
    for table, col in (
        ("use_cases", "organization_id"),
        ("use_cases", "bureau_organization_id"),
        ("consolidated_use_cases", "organization_id"),
        ("consolidated_use_cases", "bureau_organization_id"),
        ("org_ai_maturity", "organization_id"),
    ):
        n = conn.execute(
            f"""SELECT COUNT(*) FROM {table} t
                 WHERE t.{col} IS NOT NULL
                   AND NOT EXISTS (SELECT 1 FROM federal_organizations fo
                                    WHERE fo.id = t.{col})"""
        ).fetchone()[0]
        assert n == 0, f"{n} dangling {table}.{col} values"


def test_agency_maturity_view_covers_every_agency_with_data(conn):
    """The m023 compat view must expose one row per agency with any 2025
    entry — same coverage contract the old physical table had."""
    missing = conn.execute(
        """SELECT a.abbreviation FROM agencies a
            WHERE (EXISTS (SELECT 1 FROM use_cases u WHERE u.agency_id = a.id)
                OR EXISTS (SELECT 1 FROM consolidated_use_cases c
                            WHERE c.agency_id = a.id))
              AND NOT EXISTS (SELECT 1 FROM agency_ai_maturity m
                               WHERE m.agency_id = a.id)"""
    ).fetchall()
    assert not missing, (
        f"agencies with data but no maturity view row: {[m[0] for m in missing]}"
    )
    dups = conn.execute(
        """SELECT agency_id, COUNT(*) AS n FROM agency_ai_maturity
            GROUP BY agency_id HAVING n > 1"""
    ).fetchall()
    assert not dups, f"duplicate agency rows in maturity view: {dups[:5]}"


def test_agency_id_org_id_agreement(conn):
    """Where a use_cases row carries both agency_id and organization_id,
    they must agree through the legacy link."""
    n = conn.execute(
        """SELECT COUNT(*) FROM use_cases u
            JOIN federal_organizations fo ON fo.id = u.organization_id
            WHERE u.organization_id IS NOT NULL
              AND fo.legacy_agency_id IS NOT NULL
              AND fo.legacy_agency_id != u.agency_id"""
    ).fetchone()[0]
    assert n == 0, (
        f"{n} use_cases rows whose organization_id disagrees with agency_id "
        "through the legacy link"
    )
