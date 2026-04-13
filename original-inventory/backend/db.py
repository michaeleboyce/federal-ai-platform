"""
Database schema and operations for FedRAMP products
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "fedramp.db"

# Database schema matching CSV structure
SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fedramp_id TEXT NOT NULL UNIQUE,
    cloud_service_provider TEXT,
    cloud_service_offering TEXT,
    service_description TEXT,
    business_categories TEXT,
    service_model TEXT,
    status TEXT,
    independent_assessor TEXT,
    authorizations TEXT,
    reuse TEXT,
    parent_agency TEXT,
    sub_agency TEXT,
    ato_issuance_date TEXT,
    fedramp_authorization_date TEXT,
    annual_assessment_date TEXT,
    ato_expiration_date TEXT,
    html_scraped INTEGER DEFAULT 0,
    html_path TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fedramp_id ON products(fedramp_id);
CREATE INDEX IF NOT EXISTS idx_provider ON products(cloud_service_provider);
CREATE INDEX IF NOT EXISTS idx_status ON products(status);

CREATE TABLE IF NOT EXISTS ai_service_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    product_name TEXT,
    provider_name TEXT,
    service_name TEXT,
    has_ai INTEGER DEFAULT 0,
    has_genai INTEGER DEFAULT 0,
    has_llm INTEGER DEFAULT 0,
    relevant_excerpt TEXT,
    fedramp_status TEXT,
    impact_level TEXT,
    agencies TEXT,
    auth_date TEXT,
    analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(fedramp_id)
);

CREATE INDEX IF NOT EXISTS idx_ai_product_id ON ai_service_analysis(product_id);
CREATE INDEX IF NOT EXISTS idx_ai_has_ai ON ai_service_analysis(has_ai);
CREATE INDEX IF NOT EXISTS idx_ai_has_genai ON ai_service_analysis(has_genai);
CREATE INDEX IF NOT EXISTS idx_ai_has_llm ON ai_service_analysis(has_llm);
CREATE INDEX IF NOT EXISTS idx_ai_provider ON ai_service_analysis(provider_name);

CREATE TABLE IF NOT EXISTS product_ai_analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    product_name TEXT,
    provider_name TEXT,
    analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    ai_services_found INTEGER DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(fedramp_id)
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_product_id ON product_ai_analysis_runs(product_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_date ON product_ai_analysis_runs(analyzed_at);
"""

def get_connection() -> sqlite3.Connection:
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Initialize database with schema"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")

def insert_product(conn: sqlite3.Connection, product_data: Dict[str, Any]) -> int:
    """Insert or update a product record"""
    cursor = conn.cursor()

    # Check if product exists
    cursor.execute("SELECT id FROM products WHERE fedramp_id = ?", (product_data['fedramp_id'],))
    existing = cursor.fetchone()

    if existing:
        # Update existing record
        cursor.execute("""
            UPDATE products SET
                cloud_service_provider = ?,
                cloud_service_offering = ?,
                service_description = ?,
                business_categories = ?,
                service_model = ?,
                status = ?,
                independent_assessor = ?,
                authorizations = ?,
                reuse = ?,
                parent_agency = ?,
                sub_agency = ?,
                ato_issuance_date = ?,
                fedramp_authorization_date = ?,
                annual_assessment_date = ?,
                ato_expiration_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE fedramp_id = ?
        """, (
            product_data.get('cloud_service_provider'),
            product_data.get('cloud_service_offering'),
            product_data.get('service_description'),
            product_data.get('business_categories'),
            product_data.get('service_model'),
            product_data.get('status'),
            product_data.get('independent_assessor'),
            product_data.get('authorizations'),
            product_data.get('reuse'),
            product_data.get('parent_agency'),
            product_data.get('sub_agency'),
            product_data.get('ato_issuance_date'),
            product_data.get('fedramp_authorization_date'),
            product_data.get('annual_assessment_date'),
            product_data.get('ato_expiration_date'),
            product_data['fedramp_id']
        ))
        return existing[0]
    else:
        # Insert new record
        cursor.execute("""
            INSERT INTO products (
                fedramp_id, cloud_service_provider, cloud_service_offering,
                service_description, business_categories, service_model,
                status, independent_assessor, authorizations, reuse,
                parent_agency, sub_agency, ato_issuance_date,
                fedramp_authorization_date, annual_assessment_date, ato_expiration_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_data['fedramp_id'],
            product_data.get('cloud_service_provider'),
            product_data.get('cloud_service_offering'),
            product_data.get('service_description'),
            product_data.get('business_categories'),
            product_data.get('service_model'),
            product_data.get('status'),
            product_data.get('independent_assessor'),
            product_data.get('authorizations'),
            product_data.get('reuse'),
            product_data.get('parent_agency'),
            product_data.get('sub_agency'),
            product_data.get('ato_issuance_date'),
            product_data.get('fedramp_authorization_date'),
            product_data.get('annual_assessment_date'),
            product_data.get('ato_expiration_date')
        ))
        return cursor.lastrowid

def update_scrape_status(conn: sqlite3.Connection, fedramp_id: str, html_path: str):
    """Mark product as scraped with HTML path"""
    conn.execute("""
        UPDATE products
        SET html_scraped = 1, html_path = ?, updated_at = CURRENT_TIMESTAMP
        WHERE fedramp_id = ?
    """, (html_path, fedramp_id))

def get_all_products(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Get all products"""
    cursor = conn.execute("SELECT * FROM products ORDER BY cloud_service_provider")
    return [dict(row) for row in cursor.fetchall()]

def get_unscraped_products(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Get products that haven't been scraped yet"""
    cursor = conn.execute("""
        SELECT * FROM products
        WHERE html_scraped = 0
        ORDER BY fedramp_id
    """)
    return [dict(row) for row in cursor.fetchall()]

def get_scrape_stats(conn: sqlite3.Connection) -> Dict[str, int]:
    """Get scraping statistics"""
    cursor = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN html_scraped = 1 THEN 1 ELSE 0 END) as scraped,
            SUM(CASE WHEN html_scraped = 0 THEN 1 ELSE 0 END) as pending
        FROM products
    """)
    row = cursor.fetchone()
    return {
        'total': row['total'],
        'scraped': row['scraped'],
        'pending': row['pending']
    }

def insert_ai_analysis(conn: sqlite3.Connection, analysis_data: Dict[str, Any]) -> int:
    """Insert AI service analysis result"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ai_service_analysis (
            product_id, product_name, provider_name, service_name,
            has_ai, has_genai, has_llm, relevant_excerpt,
            fedramp_status, impact_level, agencies, auth_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        analysis_data['product_id'],
        analysis_data['product_name'],
        analysis_data['provider_name'],
        analysis_data['service_name'],
        1 if analysis_data.get('has_ai') else 0,
        1 if analysis_data.get('has_genai') else 0,
        1 if analysis_data.get('has_llm') else 0,
        analysis_data.get('relevant_excerpt'),
        analysis_data.get('fedramp_status'),
        analysis_data.get('impact_level'),
        analysis_data.get('agencies'),
        analysis_data.get('auth_date')
    ))
    return cursor.lastrowid

def get_ai_services(conn: sqlite3.Connection, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get AI service analysis results with optional filtering"""
    query = "SELECT * FROM ai_service_analysis WHERE 1=1"
    params = []

    if filter_type == 'ai':
        query += " AND has_ai = 1"
    elif filter_type == 'genai':
        query += " AND has_genai = 1"
    elif filter_type == 'llm':
        query += " AND has_llm = 1"
    else:
        # Get all AI-related services (at least one flag is true)
        query += " AND (has_ai = 1 OR has_genai = 1 OR has_llm = 1)"

    query += " ORDER BY provider_name, product_name, service_name"

    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

def get_ai_stats(conn: sqlite3.Connection) -> Dict[str, int]:
    """Get AI analysis statistics"""
    cursor = conn.execute("""
        SELECT
            COUNT(*) as total_ai_services,
            SUM(has_ai) as count_ai,
            SUM(has_genai) as count_genai,
            SUM(has_llm) as count_llm,
            COUNT(DISTINCT product_id) as products_with_ai,
            COUNT(DISTINCT provider_name) as providers_with_ai
        FROM ai_service_analysis
        WHERE has_ai = 1 OR has_genai = 1 OR has_llm = 1
    """)
    row = cursor.fetchone()
    return {
        'total_ai_services': row['total_ai_services'] or 0,
        'count_ai': row['count_ai'] or 0,
        'count_genai': row['count_genai'] or 0,
        'count_llm': row['count_llm'] or 0,
        'products_with_ai': row['products_with_ai'] or 0,
        'providers_with_ai': row['providers_with_ai'] or 0
    }

def clear_ai_analysis(conn: sqlite3.Connection):
    """Clear all AI analysis results (for re-running analysis)"""
    conn.execute("DELETE FROM ai_service_analysis")
    conn.commit()

def record_product_analysis_run(conn: sqlite3.Connection, product_id: str, product_name: str, provider_name: str, ai_services_found: int) -> int:
    """Record that a product was analyzed for AI services"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO product_ai_analysis_runs (
            product_id, product_name, provider_name, ai_services_found
        ) VALUES (?, ?, ?, ?)
    """, (product_id, product_name, provider_name, ai_services_found))
    return cursor.lastrowid

def get_last_analysis_run(conn: sqlite3.Connection, product_id: str) -> Optional[Dict[str, Any]]:
    """Get the last time a product was analyzed"""
    cursor = conn.execute("""
        SELECT * FROM product_ai_analysis_runs
        WHERE product_id = ?
        ORDER BY analyzed_at DESC
        LIMIT 1
    """, (product_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_analysis_run_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Get statistics about analysis runs"""
    cursor = conn.execute("""
        SELECT
            COUNT(DISTINCT product_id) as products_analyzed,
            MAX(analyzed_at) as last_run,
            SUM(ai_services_found) as total_services_found
        FROM product_ai_analysis_runs
    """)
    row = cursor.fetchone()
    return {
        'products_analyzed': row['products_analyzed'] or 0,
        'last_run': row['last_run'],
        'total_services_found': row['total_services_found'] or 0
    }

if __name__ == "__main__":
    initialize_database()
    print("Database schema created successfully!")
