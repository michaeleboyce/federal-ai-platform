"""SQLite database schema and connection management for 2025 Federal AI Use Case Inventory."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "federal_ai_inventory_2025.db"


def get_connection():
    """Get a SQLite connection with foreign keys enabled."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


SCHEMA_SQL = """
-- Agencies tracked in the inventory
CREATE TABLE IF NOT EXISTS agencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    abbreviation TEXT NOT NULL UNIQUE,
    agency_type TEXT,
    inventory_page_url TEXT,
    csv_download_url TEXT,
    inventory_year INTEGER,
    status TEXT,
    schema_compliance REAL,
    notes TEXT,
    last_modified TEXT,
    date_accessed TEXT
);

CREATE INDEX IF NOT EXISTS idx_agencies_abbr ON agencies(abbreviation);
CREATE INDEX IF NOT EXISTS idx_agencies_status ON agencies(status);

-- Normalized product/vendor lookup
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL UNIQUE,
    vendor TEXT,
    product_type TEXT,  -- LLM, coding_assistant, security_tool, productivity, legal_research, etc.
    is_generative_ai INTEGER DEFAULT 0,
    is_frontier_llm INTEGER DEFAULT 0,
    parent_product_id INTEGER REFERENCES products(id),
    description TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_products_vendor ON products(vendor);
CREATE INDEX IF NOT EXISTS idx_products_type ON products(product_type);

-- Maps observed variant names to canonical products
CREATE TABLE IF NOT EXISTS product_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    alias_text TEXT NOT NULL,
    UNIQUE(alias_text)
);

CREATE INDEX IF NOT EXISTS idx_aliases_text ON product_aliases(alias_text);
CREATE INDEX IF NOT EXISTS idx_aliases_product ON product_aliases(product_id);

-- OMB's standardized use case descriptions (templates that appear verbatim across agencies)
CREATE TABLE IF NOT EXISTS use_case_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_text TEXT NOT NULL UNIQUE,
    short_name TEXT UNIQUE,
    capability_category TEXT,  -- writing, coding, search, meetings, email, data_viz, travel, etc.
    is_omb_standard INTEGER DEFAULT 1,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_templates_category ON use_case_templates(capability_category);

-- Canonical 34-field M-25-21 schema (all agencies normalized here)
CREATE TABLE IF NOT EXISTS use_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agency_id INTEGER NOT NULL REFERENCES agencies(id),
    source_file TEXT NOT NULL,
    slug TEXT UNIQUE,

    -- Section 1: Use Case Identifiers
    use_case_id TEXT,
    use_case_name TEXT NOT NULL,
    bureau_component TEXT,
    email_address TEXT,
    withheld_from_public TEXT,
    stage_of_development TEXT,
    is_high_impact TEXT,
    justification TEXT,

    -- Section 2: Use Case Summary
    topic_area TEXT,
    ai_classification TEXT,
    problem_statement TEXT,
    expected_benefits TEXT,
    system_outputs TEXT,
    operational_date TEXT,

    -- Section 3: Documentation
    development_type TEXT,
    vendor_name TEXT,
    has_ato TEXT,
    system_name TEXT,
    training_data_description TEXT,

    -- Section 4: Data & Code
    federal_data_catalog_link TEXT,
    involves_pii TEXT,
    pia_link TEXT,
    demographic_variables TEXT,
    has_custom_code TEXT,
    open_source_link TEXT,

    -- Section 5: Risk Management
    pre_deployment_testing TEXT,
    impact_assessment TEXT,
    potential_impacts TEXT,
    independent_review TEXT,
    ongoing_monitoring TEXT,
    operator_training TEXT,
    has_fail_safe TEXT,
    appeal_process TEXT,
    end_user_feedback TEXT,

    -- Product/template linking
    product_id INTEGER REFERENCES products(id),
    template_id INTEGER REFERENCES use_case_templates(id),

    -- Lossless preservation
    raw_json TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_use_cases_agency ON use_cases(agency_id);
CREATE INDEX IF NOT EXISTS idx_use_cases_product ON use_cases(product_id);
CREATE INDEX IF NOT EXISTS idx_use_cases_template ON use_cases(template_id);
CREATE INDEX IF NOT EXISTS idx_use_cases_stage ON use_cases(stage_of_development);
CREATE INDEX IF NOT EXISTS idx_use_cases_high_impact ON use_cases(is_high_impact);
CREATE INDEX IF NOT EXISTS idx_use_cases_ai_class ON use_cases(ai_classification);

-- COTS/Appendix B consolidated use case format
CREATE TABLE IF NOT EXISTS consolidated_use_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agency_id INTEGER NOT NULL REFERENCES agencies(id),
    source_file TEXT NOT NULL,
    slug TEXT UNIQUE,

    ai_use_case TEXT NOT NULL,  -- the capability description
    commercial_product TEXT,  -- product name as written
    commercial_examples TEXT,  -- if listed
    agency_uses TEXT,  -- Y/N
    estimated_licenses_users TEXT,  -- "1-100", "101-1000", etc.

    -- Product/template linking
    product_id INTEGER REFERENCES products(id),
    template_id INTEGER REFERENCES use_case_templates(id),

    -- Lossless preservation
    raw_json TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_consolidated_agency ON consolidated_use_cases(agency_id);
CREATE INDEX IF NOT EXISTS idx_consolidated_product ON consolidated_use_cases(product_id);
CREATE INDEX IF NOT EXISTS idx_consolidated_template ON consolidated_use_cases(template_id);

-- Analytical metadata per use case (tagged by sub-agents)
CREATE TABLE IF NOT EXISTS use_case_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    use_case_id INTEGER REFERENCES use_cases(id),
    consolidated_use_case_id INTEGER REFERENCES consolidated_use_cases(id),

    -- What the entry represents
    entry_type TEXT,  -- generic_use_pattern, product_deployment, product_feature, custom_system, bespoke_application
    is_product_capability_entry INTEGER DEFAULT 0,
    product_capability TEXT,  -- drafting, coding, search, meetings, email, etc.

    -- Tool categorization
    is_general_llm_access INTEGER,
    is_coding_tool INTEGER,
    is_cots_commercial INTEGER,
    tool_product_name TEXT,
    tool_vendor TEXT,

    -- Sophistication
    ai_sophistication TEXT,  -- general_llm, coding_assistant, agentic, classical_ml, computer_vision, nlp_specific, predictive_analytics
    is_generative_ai INTEGER,
    is_frontier_model INTEGER,

    -- Deployment scope
    deployment_scope TEXT,  -- enterprise_wide, department, bureau, office, team, pilot
    scope_detail TEXT,
    is_enterprise_wide INTEGER,
    estimated_user_count TEXT,

    -- Architecture
    architecture_type TEXT,  -- inference_only, rag_pipeline, fine_tuned, custom_trained, agentic_workflow, unknown
    has_model_training INTEGER,

    -- Product detail
    cots_product_name TEXT,
    cots_vendor TEXT,
    is_microsoft_copilot INTEGER,
    is_openai INTEGER,
    is_anthropic INTEGER,
    is_google INTEGER,
    is_github_copilot INTEGER,
    is_aws_ai INTEGER,

    -- Mission characterization
    use_type TEXT,  -- mission_critical, administrative, it_operations, cybersecurity, research
    is_public_facing INTEGER,

    -- Governance
    has_meaningful_risk_docs INTEGER,
    high_impact_designation TEXT,
    deployment_environment TEXT,  -- azure_gov, aws_govcloud, gcp, on_prem, saas, unknown
    has_ato_or_fedramp INTEGER,

    created_at TEXT DEFAULT (datetime('now')),

    -- Must reference either use_cases or consolidated_use_cases, not both
    CHECK ((use_case_id IS NOT NULL AND consolidated_use_case_id IS NULL) OR
           (use_case_id IS NULL AND consolidated_use_case_id IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_tags_use_case ON use_case_tags(use_case_id);
CREATE INDEX IF NOT EXISTS idx_tags_consolidated ON use_case_tags(consolidated_use_case_id);
CREATE INDEX IF NOT EXISTS idx_tags_entry_type ON use_case_tags(entry_type);
CREATE INDEX IF NOT EXISTS idx_tags_llm ON use_case_tags(is_general_llm_access);
CREATE INDEX IF NOT EXISTS idx_tags_coding ON use_case_tags(is_coding_tool);
CREATE INDEX IF NOT EXISTS idx_tags_scope ON use_case_tags(deployment_scope);

-- Agency-level scoring (computed after tagging)
CREATE TABLE IF NOT EXISTS agency_ai_maturity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agency_id INTEGER NOT NULL UNIQUE REFERENCES agencies(id),

    total_use_cases INTEGER,
    total_consolidated_entries INTEGER,
    distinct_products_deployed INTEGER,  -- after dedup

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

    year_over_year_growth REAL,

    maturity_tier TEXT,  -- leading, progressing, early, minimal, none
    notes TEXT,

    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_maturity_tier ON agency_ai_maturity(maturity_tier);

-- Documents per-agency column mappings
CREATE TABLE IF NOT EXISTS column_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agency_abbreviation TEXT NOT NULL,
    source_column_name TEXT NOT NULL,
    canonical_column_name TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_column_mappings_agency ON column_mappings(agency_abbreviation);
"""


def _column_exists(conn, table: str, column: str) -> bool:
    """Return True if `column` is defined on `table`."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def apply_migrations(conn=None) -> None:
    """Apply additive schema migrations idempotently.

    Currently:
      * use_cases.id_provenance — TEXT, nullable, no default.
        Values: 'source' | 'backfilled_from_raw_json' | 'source_missing'.
        Distinguishes IDs that came from the source spreadsheet from those
        recovered post-hoc and from those genuinely missing in the source.
      * use_case_products — many-to-many join table (Phase 2 Agent D).
        Multi-product evidence per use case; keeps use_cases.product_id
        for back-compat (highest-confidence single match).
      * review_queue_products — surface rows that need LLM review for
        product resolution (compound strings + unmatched vendor text).
    """
    own = False
    if conn is None:
        conn = get_connection()
        own = True
    try:
        if not _column_exists(conn, "use_cases", "id_provenance"):
            conn.execute("ALTER TABLE use_cases ADD COLUMN id_provenance TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_use_cases_id_provenance "
                "ON use_cases(id_provenance)"
            )
            conn.commit()

        # use_case_products join table (Agent D)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS use_case_products (
                use_case_id INTEGER NOT NULL REFERENCES use_cases(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                evidence_text TEXT,
                confidence TEXT CHECK(confidence IN ('strong', 'inferred')),
                PRIMARY KEY (use_case_id, product_id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ucp_use_case "
            "ON use_case_products(use_case_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ucp_product "
            "ON use_case_products(product_id)"
        )

        # review_queue_products for coordinator LLM review pass
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS review_queue_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                use_case_id INTEGER REFERENCES use_cases(id),
                consolidated_use_case_id INTEGER REFERENCES consolidated_use_cases(id),
                source_text TEXT,
                heuristic_product_ids TEXT,  -- JSON array of product IDs resolved heuristically
                reason TEXT,                  -- 'compound_string' | 'unmatched_vendor_text'
                llm_reviewed INTEGER DEFAULT 0,
                llm_proposed_product_ids TEXT,
                llm_confidence TEXT,
                llm_reasoning TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rqp_use_case "
            "ON review_queue_products(use_case_id)"
        )
        conn.commit()
    finally:
        if own:
            conn.close()


def init_schema():
    """Create all tables and indexes, then apply additive migrations."""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        print(f"Schema initialized at {DB_PATH}")
    finally:
        conn.close()
    apply_migrations()


def drop_all():
    """Drop all tables. Use with caution."""
    conn = get_connection()
    try:
        tables = [
            "use_case_tags",
            "agency_ai_maturity",
            "use_cases",
            "consolidated_use_cases",
            "product_aliases",
            "products",
            "use_case_templates",
            "column_mappings",
            "agencies",
        ]
        for t in tables:
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        conn.commit()
        print(f"All tables dropped from {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        drop_all()
    init_schema()
