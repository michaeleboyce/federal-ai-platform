"""Additive schema for WIP inventory layers.

This migration keeps db.py as the core bootstrap while making the current
product-edge, review-queue, evidence, hierarchy, FedRAMP, and shared-view
schema reproducible on a fresh database.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "001_additive_inventory_schema"


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
            (table,),
        ).fetchone()
        is not None
    )


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    if not _table_exists(conn, table):
        return False
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def _add_column_if_missing(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    if _table_exists(conn, table) and not _column_exists(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


DDL = """
CREATE TABLE IF NOT EXISTS use_case_products (
    use_case_id INTEGER NOT NULL REFERENCES use_cases(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    evidence_text TEXT,
    confidence TEXT CHECK(confidence IN ('strong', 'inferred')),
    PRIMARY KEY (use_case_id, product_id)
);
CREATE INDEX IF NOT EXISTS idx_ucp_use_case ON use_case_products(use_case_id);
CREATE INDEX IF NOT EXISTS idx_ucp_product ON use_case_products(product_id);

CREATE TABLE IF NOT EXISTS consolidated_use_case_products (
    consolidated_use_case_id INTEGER NOT NULL REFERENCES consolidated_use_cases(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    evidence_text TEXT,
    confidence TEXT CHECK(confidence IN ('strong', 'inferred')),
    PRIMARY KEY (consolidated_use_case_id, product_id)
);
CREATE INDEX IF NOT EXISTS idx_cucp_cuc ON consolidated_use_case_products(consolidated_use_case_id);
CREATE INDEX IF NOT EXISTS idx_cucp_product ON consolidated_use_case_products(product_id);

CREATE TABLE IF NOT EXISTS review_queue_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    use_case_id INTEGER REFERENCES use_cases(id),
    consolidated_use_case_id INTEGER REFERENCES consolidated_use_cases(id),
    source_text TEXT,
    heuristic_product_ids TEXT,
    reason TEXT,
    llm_reviewed INTEGER DEFAULT 0,
    llm_proposed_product_ids TEXT,
    llm_confidence TEXT,
    llm_reasoning TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_rqp_use_case ON review_queue_products(use_case_id);
CREATE INDEX IF NOT EXISTS idx_rqp_consolidated ON review_queue_products(consolidated_use_case_id);

CREATE TABLE IF NOT EXISTS review_queue_llm (
    use_case_id INTEGER PRIMARY KEY REFERENCES use_cases(id),
    heuristic_label INTEGER NOT NULL,
    confidence_source TEXT NOT NULL DEFAULT 'heuristic',
    llm_label INTEGER,
    llm_confidence TEXT,
    llm_reasoning TEXT,
    applied INTEGER DEFAULT 0,
    applied_at TEXT
);

CREATE TABLE IF NOT EXISTS review_queue_scope (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_type TEXT NOT NULL,
    use_case_id INTEGER REFERENCES use_cases(id),
    consolidated_use_case_id INTEGER REFERENCES consolidated_use_cases(id),
    current_tag TEXT,
    heuristic_proposed_tag TEXT,
    raw_source TEXT,
    llm_proposed_tag TEXT,
    llm_confidence TEXT,
    llm_reasoning TEXT,
    resolved_at TEXT,
    UNIQUE (question_type, use_case_id, consolidated_use_case_id)
);
CREATE INDEX IF NOT EXISTS idx_rqs_question ON review_queue_scope(question_type);
CREATE INDEX IF NOT EXISTS idx_rqs_confidence ON review_queue_scope(llm_confidence);

CREATE TABLE IF NOT EXISTS review_queue_entry_type (
    use_case_id INTEGER PRIMARY KEY REFERENCES use_cases(id),
    heuristic_label TEXT NOT NULL,
    llm_label TEXT,
    llm_confidence TEXT,
    llm_reasoning TEXT,
    applied INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS use_case_external_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    use_case_id INTEGER REFERENCES use_cases(id),
    consolidated_use_case_id INTEGER REFERENCES consolidated_use_cases(id),
    topic TEXT NOT NULL,
    status TEXT NOT NULL,
    source_url TEXT,
    source_quote TEXT,
    confidence TEXT,
    search_method TEXT,
    captured_at TEXT NOT NULL,
    captured_by TEXT NOT NULL,
    notes TEXT,
    CHECK ((use_case_id IS NOT NULL) <> (consolidated_use_case_id IS NOT NULL)),
    CHECK (status IN ('corroborated','searched_no_source','inventory_only')),
    CHECK (status != 'corroborated' OR source_url IS NOT NULL OR source_quote IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_evidence_use_case ON use_case_external_evidence(use_case_id);
CREATE INDEX IF NOT EXISTS idx_evidence_consolidated ON use_case_external_evidence(consolidated_use_case_id);
CREATE INDEX IF NOT EXISTS idx_evidence_topic ON use_case_external_evidence(topic);
CREATE INDEX IF NOT EXISTS idx_evidence_status ON use_case_external_evidence(status);

CREATE TABLE IF NOT EXISTS federal_organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT,
    abbreviation TEXT,
    slug TEXT NOT NULL UNIQUE,
    parent_id INTEGER REFERENCES federal_organizations(id),
    level TEXT NOT NULL CHECK (level IN ('department','independent','sub_agency','office','component')),
    hierarchy_path TEXT,
    depth INTEGER NOT NULL DEFAULT 0,
    sam_org_id TEXT,
    cgac_code TEXT,
    agency_code TEXT,
    is_cfo_act_agency INTEGER NOT NULL DEFAULT 0,
    is_cabinet_department INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    display_order INTEGER DEFAULT 0,
    description TEXT,
    website TEXT,
    legacy_agency_id INTEGER REFERENCES agencies(id),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_fed_org_parent ON federal_organizations(parent_id);
CREATE INDEX IF NOT EXISTS idx_fed_org_level ON federal_organizations(level);
CREATE INDEX IF NOT EXISTS idx_fed_org_abbreviation ON federal_organizations(abbreviation);
CREATE INDEX IF NOT EXISTS idx_fed_org_hierarchy_path ON federal_organizations(hierarchy_path);
CREATE INDEX IF NOT EXISTS idx_fed_org_cfo_act ON federal_organizations(is_cfo_act_agency);
CREATE INDEX IF NOT EXISTS idx_fed_org_legacy ON federal_organizations(legacy_agency_id);

CREATE TABLE IF NOT EXISTS org_ai_maturity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL UNIQUE REFERENCES federal_organizations(id),
    total_use_cases INTEGER,
    distinct_products_deployed INTEGER,
    generative_ai_count INTEGER,
    coding_tool_count INTEGER,
    general_llm_count INTEGER,
    classical_ml_count INTEGER,
    agentic_ai_count INTEGER,
    custom_system_count INTEGER,
    has_enterprise_llm INTEGER,
    has_coding_assistants INTEGER,
    has_agentic_ai INTEGER,
    has_custom_ai INTEGER,
    pct_deployed REAL,
    pct_high_impact REAL,
    pct_with_risk_docs REAL,
    maturity_tier TEXT,
    notes TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_org_maturity_tier ON org_ai_maturity(maturity_tier);

CREATE TABLE IF NOT EXISTS fedramp_products (
    fedramp_id TEXT PRIMARY KEY,
    csp TEXT NOT NULL,
    csp_slug TEXT NOT NULL,
    cso TEXT NOT NULL,
    status TEXT NOT NULL,
    authorization_count INTEGER,
    reuse_count INTEGER,
    ready_date TEXT, ready_status TEXT,
    ip_jab_date TEXT, ip_jab_status TEXT,
    ip_prog_date TEXT, ip_prog_status TEXT,
    ip_prog_date2 TEXT,
    ip_agency_date TEXT, ip_agency_status TEXT,
    ip_pmo_date TEXT, ip_pmo_status TEXT,
    auth_date TEXT, auth_type TEXT,
    partnering_agency TEXT,
    annual_assessment_date TEXT,
    independent_assessor TEXT,
    assessor_id INTEGER,
    deployment_model TEXT,
    impact_level TEXT,
    impact_level_number INTEGER,
    service_desc TEXT,
    fedramp_msg TEXT,
    sales_email TEXT, security_email TEXT,
    website TEXT, uei TEXT,
    small_business INTEGER,
    logo TEXT,
    filter_classes TEXT, auth_category TEXT
);
CREATE INDEX IF NOT EXISTS idx_fp_csp ON fedramp_products(csp_slug);
CREATE INDEX IF NOT EXISTS idx_fp_status ON fedramp_products(status);
CREATE INDEX IF NOT EXISTS idx_fp_impact ON fedramp_products(impact_level);
CREATE INDEX IF NOT EXISTS idx_fp_assessor ON fedramp_products(assessor_id);

CREATE TABLE IF NOT EXISTS fedramp_authorizations (
    id INTEGER PRIMARY KEY,
    fedramp_id TEXT NOT NULL,
    agency_id INTEGER,
    sub_agency TEXT,
    ato_type TEXT,
    ato_issuance_date TEXT,
    fedramp_authorization_date TEXT,
    ato_expiration_date TEXT,
    annual_assessment_date TEXT
);
CREATE INDEX IF NOT EXISTS idx_fa_product ON fedramp_authorizations(fedramp_id);
CREATE INDEX IF NOT EXISTS idx_fa_agency  ON fedramp_authorizations(agency_id);
CREATE INDEX IF NOT EXISTS idx_fa_date    ON fedramp_authorizations(ato_issuance_date);

CREATE TABLE IF NOT EXISTS fedramp_agencies (
    id INTEGER PRIMARY KEY,
    parent_agency TEXT NOT NULL UNIQUE,
    parent_slug TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_fag_slug ON fedramp_agencies(parent_slug);

CREATE TABLE IF NOT EXISTS fedramp_assessors (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_fas_slug ON fedramp_assessors(slug);

CREATE TABLE IF NOT EXISTS fedramp_snapshot (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    snapshot_date TEXT,
    product_count INTEGER,
    ato_event_count INTEGER,
    agency_count INTEGER,
    csp_count INTEGER,
    assessor_count INTEGER,
    built_at TEXT
);

CREATE TABLE IF NOT EXISTS fedramp_product_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_product_id INTEGER NOT NULL REFERENCES products(id),
    fedramp_id TEXT NOT NULL,
    confidence TEXT NOT NULL CHECK (confidence IN ('strong', 'weak', 'manual')),
    source TEXT NOT NULL,
    score REAL,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(inventory_product_id, fedramp_id, source)
);
CREATE INDEX IF NOT EXISTS idx_fpl_inv ON fedramp_product_links(inventory_product_id);
CREATE INDEX IF NOT EXISTS idx_fpl_fr  ON fedramp_product_links(fedramp_id);

CREATE TABLE IF NOT EXISTS fedramp_agency_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_agency_id INTEGER NOT NULL REFERENCES agencies(id),
    fedramp_agency_id INTEGER NOT NULL,
    confidence TEXT NOT NULL CHECK (confidence IN ('strong', 'weak', 'manual')),
    source TEXT NOT NULL,
    score REAL,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(inventory_agency_id, fedramp_agency_id, source)
);
CREATE INDEX IF NOT EXISTS idx_fal_inv ON fedramp_agency_links(inventory_agency_id);
CREATE INDEX IF NOT EXISTS idx_fal_fr  ON fedramp_agency_links(fedramp_agency_id);

CREATE TABLE IF NOT EXISTS fedramp_link_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_kind TEXT NOT NULL CHECK (link_kind IN ('product', 'agency')),
    inventory_id INTEGER NOT NULL,
    source_text TEXT,
    candidate_fedramp_ids TEXT,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    decision_notes TEXT,
    llm_proposed_fedramp_ids TEXT,
    llm_reasoning TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_flq_status ON fedramp_link_queue(status);
CREATE INDEX IF NOT EXISTS idx_flq_kind   ON fedramp_link_queue(link_kind);
CREATE INDEX IF NOT EXISTS idx_flq_inv    ON fedramp_link_queue(inventory_id);
"""

VIEW_SQL = """
DROP VIEW IF EXISTS inventory_entries;
CREATE VIEW inventory_entries AS
SELECT
    'use_case' AS entry_kind,
    id AS entry_id,
    agency_id,
    organization_id,
    bureau_organization_id,
    template_id,
    slug,
    use_case_name AS title,
    source_file,
    0 AS is_consolidated
FROM use_cases
UNION ALL
SELECT
    'consolidated' AS entry_kind,
    id AS entry_id,
    agency_id,
    organization_id,
    bureau_organization_id,
    template_id,
    slug,
    ai_use_case AS title,
    source_file,
    1 AS is_consolidated
FROM consolidated_use_cases;

DROP VIEW IF EXISTS entry_product_edges;
CREATE VIEW entry_product_edges AS
SELECT
    'use_case' AS entry_kind,
    ucp.use_case_id AS entry_id,
    uc.agency_id,
    uc.organization_id,
    uc.bureau_organization_id,
    ucp.product_id,
    ucp.evidence_text,
    ucp.confidence
FROM use_case_products ucp
JOIN use_cases uc ON uc.id = ucp.use_case_id
UNION ALL
SELECT
    'consolidated' AS entry_kind,
    cucp.consolidated_use_case_id AS entry_id,
    c.agency_id,
    c.organization_id,
    c.bureau_organization_id,
    cucp.product_id,
    cucp.evidence_text,
    cucp.confidence
FROM consolidated_use_case_products cucp
JOIN consolidated_use_cases c ON c.id = cucp.consolidated_use_case_id;

DROP VIEW IF EXISTS agency_rollups;
CREATE VIEW agency_rollups AS
SELECT
    a.id AS agency_id,
    COUNT(DISTINCT CASE WHEN ie.entry_kind = 'use_case' THEN ie.entry_id END) AS total_use_cases,
    COUNT(DISTINCT CASE WHEN ie.entry_kind = 'consolidated' THEN ie.entry_id END) AS total_consolidated_entries,
    COUNT(DISTINCT epe.product_id) AS distinct_products_deployed,
    COUNT(epe.product_id) AS product_edge_count
FROM agencies a
LEFT JOIN inventory_entries ie ON ie.agency_id = a.id
LEFT JOIN entry_product_edges epe
  ON epe.agency_id = a.id
 AND epe.entry_kind = ie.entry_kind
 AND epe.entry_id = ie.entry_id
GROUP BY a.id;
"""


def apply(conn: sqlite3.Connection) -> None:
    _add_column_if_missing(conn, "use_cases", "id_provenance", "TEXT")
    _add_column_if_missing(
        conn,
        "products",
        "product_origin",
        "TEXT NOT NULL DEFAULT 'commercial'",
    )
    _add_column_if_missing(
        conn,
        "use_cases",
        "organization_id",
        "INTEGER REFERENCES federal_organizations(id)",
    )
    _add_column_if_missing(
        conn,
        "use_cases",
        "bureau_organization_id",
        "INTEGER REFERENCES federal_organizations(id)",
    )
    _add_column_if_missing(
        conn,
        "consolidated_use_cases",
        "organization_id",
        "INTEGER REFERENCES federal_organizations(id)",
    )
    _add_column_if_missing(
        conn,
        "consolidated_use_cases",
        "bureau_organization_id",
        "INTEGER REFERENCES federal_organizations(id)",
    )
    _add_column_if_missing(
        conn,
        "agency_ai_maturity",
        "organization_id",
        "INTEGER REFERENCES federal_organizations(id)",
    )

    conn.executescript(DDL)
    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_use_cases_id_provenance ON use_cases(id_provenance);
        CREATE INDEX IF NOT EXISTS idx_use_cases_org ON use_cases(organization_id);
        CREATE INDEX IF NOT EXISTS idx_use_cases_bureau_org ON use_cases(bureau_organization_id);
        CREATE INDEX IF NOT EXISTS idx_consolidated_org ON consolidated_use_cases(organization_id);
        CREATE INDEX IF NOT EXISTS idx_consolidated_bureau_org ON consolidated_use_cases(bureau_organization_id);
        CREATE INDEX IF NOT EXISTS idx_maturity_org ON agency_ai_maturity(organization_id);
        """
    )
    conn.executescript(VIEW_SQL)
