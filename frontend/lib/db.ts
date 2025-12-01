/**
 * Database utility functions - PostgreSQL/Drizzle version
 * Replaces the old SQLite implementation
 */
import { productRepo, aiServiceRepo, agencyRepo } from './repositories';
import type { ProductRecord } from '@federal-ai-platform/database/schema/products';

// Re-export the type from our schema (matches old Product interface structure)
export type Product = ProductRecord;

/**
 * Get all products
 */
export async function getAllProducts(): Promise<Product[]> {
  return await productRepo.getAll('provider');
}

/**
 * Get all products with AI service counts
 */
export async function getAllProductsWithServiceCounts() {
  const { db } = await import('./db/client');
  const { sql } = await import('drizzle-orm');

  const result = await db.execute(sql`
    SELECT
      p.*,
      COALESCE(COUNT(DISTINCT a.id), 0)::int as ai_service_count,
      COALESCE(
        ARRAY_AGG(DISTINCT a.service_name) FILTER (WHERE a.service_name IS NOT NULL),
        ARRAY[]::text[]
      ) as ai_services,
      COALESCE(
        ARRAY_AGG(DISTINCT a.impact_level) FILTER (WHERE a.impact_level IS NOT NULL),
        ARRAY[]::text[]
      ) as impact_levels,
      COALESCE(pa_counts.auth_count, 0)::int as authorization_count,
      COALESCE(BOOL_OR(a.has_ai), false) as has_ai,
      COALESCE(BOOL_OR(a.has_genai), false) as has_genai,
      COALESCE(BOOL_OR(a.has_llm), false) as has_llm
    FROM products p
    LEFT JOIN ai_service_analysis a ON p.fedramp_id = a.product_id
    LEFT JOIN (
      SELECT fedramp_id, COUNT(*)::int as auth_count
      FROM product_authorizations
      GROUP BY fedramp_id
    ) pa_counts ON p.fedramp_id = pa_counts.fedramp_id
    GROUP BY p.id, pa_counts.auth_count
    ORDER BY p.cloud_service_provider ASC
  `);

  return result.rows.map((row: Record<string, unknown>) => ({
    id: row.id as number,
    fedrampId: row.fedramp_id as string,
    cloudServiceProvider: row.cloud_service_provider as string | null,
    cloudServiceOffering: row.cloud_service_offering as string | null,
    serviceDescription: row.service_description as string | null,
    businessCategories: row.business_categories as string | null,
    serviceModel: row.service_model as string | null,
    status: row.status as string | null,
    independentAssessor: row.independent_assessor as string | null,
    authorizations: row.authorizations as string | null,
    reuse: row.reuse as string | null,
    parentAgency: row.parent_agency as string | null,
    subAgency: row.sub_agency as string | null,
    atoIssuanceDate: row.ato_issuance_date as string | null,
    fedrampAuthorizationDate: row.fedramp_authorization_date as string | null,
    annualAssessmentDate: row.annual_assessment_date as string | null,
    atoExpirationDate: row.ato_expiration_date as string | null,
    htmlScraped: row.html_scraped as boolean,
    htmlPath: row.html_path as string | null,
    createdAt: new Date(row.created_at as string),
    updatedAt: new Date(row.updated_at as string),
    aiServiceCount: row.ai_service_count as number,
    aiServices: (row.ai_services as string[]) || [],
    impactLevels: (row.impact_levels as string[]) || [],
    authorizationCount: row.authorization_count as number,
    hasAi: row.has_ai as boolean,
    hasGenai: row.has_genai as boolean,
    hasLlm: row.has_llm as boolean,
  }));
}

/**
 * Get a single product by FedRAMP ID
 */
export async function getProduct(fedrampId: string): Promise<Product | undefined> {
  return await productRepo.getByFedrampId(fedrampId);
}

/**
 * Search products by query
 */
export async function searchProducts(query: string): Promise<Product[]> {
  return await productRepo.search(query);
}

/**
 * Get product statistics
 */
export async function getStats() {
  const total = await productRepo.getCount();
  const providers = await productRepo.getUniqueProviders();
  const aiStats = await aiServiceRepo.getStats();

  return {
    total,
    scraped: 0, // Not tracked in PostgreSQL version
    unique_providers: providers.length,
    unique_models: 0, // Can calculate if needed
    ai_services: aiStats.totalServices,
    ai_products: aiStats.uniqueProducts,
  };
}

/**
 * Get AI services statistics
 */
export async function getAIStats() {
  return await aiServiceRepo.getStats();
}

/**
 * Get all AI services
 */
export async function getAllAIServices() {
  return await aiServiceRepo.getAllAIServices();
}

/**
 * Get AI services by type
 */
export async function getAIServicesByType(type: 'ai' | 'genai' | 'llm') {
  return await aiServiceRepo.getByAIType(type);
}

/**
 * Get all agencies
 */
export async function getAllAgencies() {
  return await agencyRepo.getAllUsages();
}

/**
 * Get agency by slug
 */
export async function getAgencyBySlug(slug: string) {
  return await agencyRepo.getUsageBySlug(slug);
}

/**
 * Get matches for an agency
 */
export async function getAgencyMatches(agencyId: number) {
  return await agencyRepo.getMatchesByAgency(agencyId);
}
