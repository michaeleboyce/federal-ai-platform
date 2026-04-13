/**
 * Database utility functions - PostgreSQL/Drizzle version
 * Replaces the old SQLite implementation
 */
import { productRepo, aiServiceRepo, agencyRepo } from './repositories';
import type { ProductRecord } from '../../packages/database/src/schema/products';

// Re-export the type from our schema (matches old Product interface structure)
export type Product = ProductRecord;

/**
 * Get all products
 */
export async function getAllProducts(): Promise<Product[]> {
  return await productRepo.getAll('provider');
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
