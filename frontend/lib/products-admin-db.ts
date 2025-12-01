/**
 * Database query functions for Products Admin Panel
 * Manages AI service analysis data for FedRAMP products
 */

import { db } from './db/client';
import {
  aiServiceAnalysis,
  productAuthorizations,
  type AIService,
} from './db/schema';
import { eq, sql, ilike, or, and, isNotNull, desc, asc } from 'drizzle-orm';

// ========================================
// TYPES
// ========================================

export interface ProductWithAnalysis extends AIService {
  authorizationCount: number;
}

export interface ProductStats {
  total: number;
  withAi: number;
  withGenai: number;
  withLlm: number;
  reviewed: number;
  unreviewed: number;
  // Expanded capabilities
  withChatbot: number;
  withCodingAssistant: number;
  withImageGeneration: number;
  withDocumentAnalysis: number;
  withSpeechToText: number;
  withTranslation: number;
  withAiSearch: number;
}

export interface ProductFilter {
  search?: string;
  hasAi?: boolean;
  hasGenai?: boolean;
  hasLlm?: boolean;
  isReviewed?: boolean;
}

// ========================================
// BASIC QUERIES
// ========================================

/**
 * Get all products with their AI analysis data
 */
export async function getAllProductsWithAnalysis(): Promise<ProductWithAnalysis[]> {
  // Get all products from ai_service_analysis
  const products = await db
    .select()
    .from(aiServiceAnalysis)
    .orderBy(asc(aiServiceAnalysis.providerName), asc(aiServiceAnalysis.productName));

  // Get authorization counts per product
  const authCounts = await db
    .select({
      fedrampId: productAuthorizations.fedrampId,
      count: sql<number>`count(*)::int`.as('count'),
    })
    .from(productAuthorizations)
    .groupBy(productAuthorizations.fedrampId);

  // Create a map for quick lookup
  const countMap = new Map<string, number>();
  for (const auth of authCounts) {
    countMap.set(auth.fedrampId, auth.count);
  }

  // Combine products with auth counts
  return products.map(product => ({
    ...product,
    authorizationCount: countMap.get(product.productId) ?? 0,
  }));
}

/**
 * Get a single product with analysis by product ID
 */
export async function getProductWithAnalysis(productId: string): Promise<ProductWithAnalysis | null> {
  const products = await db
    .select()
    .from(aiServiceAnalysis)
    .where(eq(aiServiceAnalysis.productId, productId))
    .limit(1);

  if (products.length === 0) return null;

  // Get authorization count
  const authCount = await db
    .select({
      count: sql<number>`count(*)::int`.as('count'),
    })
    .from(productAuthorizations)
    .where(eq(productAuthorizations.fedrampId, productId));

  return {
    ...products[0],
    authorizationCount: authCount[0]?.count ?? 0,
  };
}

/**
 * Get products by ID (database ID, not product ID)
 */
export async function getProductById(id: number): Promise<AIService | null> {
  const products = await db
    .select()
    .from(aiServiceAnalysis)
    .where(eq(aiServiceAnalysis.id, id))
    .limit(1);

  return products[0] ?? null;
}

// ========================================
// FILTERED QUERIES
// ========================================

/**
 * Get products with filters
 */
export async function getProductsByFilter(filter: ProductFilter): Promise<ProductWithAnalysis[]> {
  const conditions = [];

  if (filter.search) {
    const searchLower = `%${filter.search.toLowerCase()}%`;
    conditions.push(
      or(
        ilike(aiServiceAnalysis.productName, searchLower),
        ilike(aiServiceAnalysis.providerName, searchLower),
        ilike(aiServiceAnalysis.serviceName, searchLower)
      )
    );
  }

  if (filter.hasAi !== undefined) {
    conditions.push(eq(aiServiceAnalysis.hasAi, filter.hasAi));
  }

  if (filter.hasGenai !== undefined) {
    conditions.push(eq(aiServiceAnalysis.hasGenai, filter.hasGenai));
  }

  if (filter.hasLlm !== undefined) {
    conditions.push(eq(aiServiceAnalysis.hasLlm, filter.hasLlm));
  }

  if (filter.isReviewed !== undefined) {
    if (filter.isReviewed) {
      conditions.push(isNotNull(aiServiceAnalysis.reviewedAt));
    } else {
      conditions.push(sql`${aiServiceAnalysis.reviewedAt} IS NULL`);
    }
  }

  const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

  const products = await db
    .select()
    .from(aiServiceAnalysis)
    .where(whereClause)
    .orderBy(asc(aiServiceAnalysis.providerName), asc(aiServiceAnalysis.productName));

  // Get authorization counts
  const authCounts = await db
    .select({
      fedrampId: productAuthorizations.fedrampId,
      count: sql<number>`count(*)::int`.as('count'),
    })
    .from(productAuthorizations)
    .groupBy(productAuthorizations.fedrampId);

  const countMap = new Map<string, number>();
  for (const auth of authCounts) {
    countMap.set(auth.fedrampId, auth.count);
  }

  return products.map(product => ({
    ...product,
    authorizationCount: countMap.get(product.productId) ?? 0,
  }));
}

// ========================================
// STATISTICS
// ========================================

/**
 * Get product statistics
 */
export async function getProductStats(): Promise<ProductStats> {
  const result = await db
    .select({
      total: sql<number>`count(*)::int`.as('total'),
      withAi: sql<number>`sum(case when ${aiServiceAnalysis.hasAi} then 1 else 0 end)::int`.as('with_ai'),
      withGenai: sql<number>`sum(case when ${aiServiceAnalysis.hasGenai} then 1 else 0 end)::int`.as('with_genai'),
      withLlm: sql<number>`sum(case when ${aiServiceAnalysis.hasLlm} then 1 else 0 end)::int`.as('with_llm'),
      reviewed: sql<number>`sum(case when ${aiServiceAnalysis.reviewedAt} is not null then 1 else 0 end)::int`.as('reviewed'),
      unreviewed: sql<number>`sum(case when ${aiServiceAnalysis.reviewedAt} is null then 1 else 0 end)::int`.as('unreviewed'),
      withChatbot: sql<number>`sum(case when ${aiServiceAnalysis.hasChatbot} then 1 else 0 end)::int`.as('with_chatbot'),
      withCodingAssistant: sql<number>`sum(case when ${aiServiceAnalysis.hasCodingAssistant} then 1 else 0 end)::int`.as('with_coding'),
      withImageGeneration: sql<number>`sum(case when ${aiServiceAnalysis.hasImageGeneration} then 1 else 0 end)::int`.as('with_image'),
      withDocumentAnalysis: sql<number>`sum(case when ${aiServiceAnalysis.hasDocumentAnalysis} then 1 else 0 end)::int`.as('with_doc'),
      withSpeechToText: sql<number>`sum(case when ${aiServiceAnalysis.hasSpeechToText} then 1 else 0 end)::int`.as('with_speech'),
      withTranslation: sql<number>`sum(case when ${aiServiceAnalysis.hasTranslation} then 1 else 0 end)::int`.as('with_translation'),
      withAiSearch: sql<number>`sum(case when ${aiServiceAnalysis.hasAiSearch} then 1 else 0 end)::int`.as('with_search'),
    })
    .from(aiServiceAnalysis);

  return {
    total: result[0]?.total ?? 0,
    withAi: result[0]?.withAi ?? 0,
    withGenai: result[0]?.withGenai ?? 0,
    withLlm: result[0]?.withLlm ?? 0,
    reviewed: result[0]?.reviewed ?? 0,
    unreviewed: result[0]?.unreviewed ?? 0,
    withChatbot: result[0]?.withChatbot ?? 0,
    withCodingAssistant: result[0]?.withCodingAssistant ?? 0,
    withImageGeneration: result[0]?.withImageGeneration ?? 0,
    withDocumentAnalysis: result[0]?.withDocumentAnalysis ?? 0,
    withSpeechToText: result[0]?.withSpeechToText ?? 0,
    withTranslation: result[0]?.withTranslation ?? 0,
    withAiSearch: result[0]?.withAiSearch ?? 0,
  };
}

// ========================================
// UPDATE OPERATIONS
// ========================================

/**
 * Update product analysis data
 */
export async function updateProductAnalysis(
  id: number,
  data: Partial<{
    // Original AI flags
    hasAi: boolean;
    hasGenai: boolean;
    hasLlm: boolean;
    relevantExcerpt: string | null;
    // Expanded capabilities
    hasChatbot: boolean;
    hasCodingAssistant: boolean;
    hasImageGeneration: boolean;
    hasDocumentAnalysis: boolean;
    hasSpeechToText: boolean;
    hasTranslation: boolean;
    hasAiSearch: boolean;
    // Admin metadata
    adminNotes: string | null;
    customDescription: string | null;
  }>
): Promise<AIService> {
  const result = await db
    .update(aiServiceAnalysis)
    .set({
      ...data,
      reviewedAt: new Date(),
    })
    .where(eq(aiServiceAnalysis.id, id))
    .returning();

  if (result.length === 0) {
    throw new Error(`Product with ID ${id} not found`);
  }

  return result[0];
}

/**
 * Mark product as reviewed without changing other fields
 */
export async function markProductReviewed(id: number): Promise<AIService> {
  const result = await db
    .update(aiServiceAnalysis)
    .set({
      reviewedAt: new Date(),
    })
    .where(eq(aiServiceAnalysis.id, id))
    .returning();

  if (result.length === 0) {
    throw new Error(`Product with ID ${id} not found`);
  }

  return result[0];
}

/**
 * Clear reviewed status for a product
 */
export async function clearProductReviewed(id: number): Promise<AIService> {
  const result = await db
    .update(aiServiceAnalysis)
    .set({
      reviewedAt: null,
    })
    .where(eq(aiServiceAnalysis.id, id))
    .returning();

  if (result.length === 0) {
    throw new Error(`Product with ID ${id} not found`);
  }

  return result[0];
}

// ========================================
// AUTHORIZATION HELPERS
// ========================================

/**
 * Get authorizations for a specific product
 */
export async function getProductAuthorizations(fedrampId: string) {
  return db
    .select()
    .from(productAuthorizations)
    .where(eq(productAuthorizations.fedrampId, fedrampId))
    .orderBy(asc(productAuthorizations.parentAgencyName));
}
