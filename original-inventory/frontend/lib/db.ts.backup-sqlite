import Database from 'better-sqlite3';
import path from 'path';

export interface Product {
  id: number;
  fedramp_id: string;
  cloud_service_provider: string | null;
  cloud_service_offering: string | null;
  service_description: string | null;
  business_categories: string | null;
  service_model: string | null;
  status: string | null;
  independent_assessor: string | null;
  authorizations: string | null;
  reuse: string | null;
  parent_agency: string | null;
  sub_agency: string | null;
  ato_issuance_date: string | null;
  fedramp_authorization_date: string | null;
  annual_assessment_date: string | null;
  ato_expiration_date: string | null;
  html_scraped: number;
  html_path: string | null;
  created_at: string;
  updated_at: string;
}

const DB_PATH = path.join(process.cwd(), '..', 'data', 'fedramp.db');

export function getDb() {
  return new Database(DB_PATH, { readonly: true });
}

export function getAllProducts(): Product[] {
  const db = getDb();
  const products = db.prepare('SELECT * FROM products ORDER BY cloud_service_provider').all() as Product[];
  db.close();
  return products;
}

export function getProduct(fedrampId: string): Product | undefined {
  const db = getDb();
  const product = db.prepare('SELECT * FROM products WHERE fedramp_id = ?').get(fedrampId) as Product | undefined;
  db.close();
  return product;
}

export function searchProducts(query: string): Product[] {
  const db = getDb();
  const searchPattern = `%${query}%`;
  const products = db.prepare(`
    SELECT * FROM products
    WHERE cloud_service_provider LIKE ?
       OR cloud_service_offering LIKE ?
       OR fedramp_id LIKE ?
       OR service_description LIKE ?
    ORDER BY cloud_service_provider
    LIMIT 100
  `).all(searchPattern, searchPattern, searchPattern, searchPattern) as Product[];
  db.close();
  return products;
}

export function getStats() {
  const db = getDb();
  const stats = db.prepare(`
    SELECT
      COUNT(*) as total,
      SUM(CASE WHEN html_scraped = 1 THEN 1 ELSE 0 END) as scraped,
      COUNT(DISTINCT cloud_service_provider) as unique_providers,
      COUNT(DISTINCT service_model) as unique_models
    FROM products
  `).get() as {
    total: number;
    scraped: number;
    unique_providers: number;
    unique_models: number;
  };
  db.close();
  return stats;
}
