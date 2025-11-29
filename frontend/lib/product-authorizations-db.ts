/**
 * Product Authorizations Database Functions
 * Query functions for FedRAMP product authorization data
 */

import { db } from './db/client';
import { productAuthorizations, federalOrganizations } from './db/schema';
import { eq, sql, and, or, ilike, desc, count, isNotNull } from 'drizzle-orm';

// AI-related keywords for filtering
const AI_KEYWORDS = [
  'ai', 'artificial intelligence', 'machine learning', 'ml',
  'gpt', 'llm', 'chatbot', 'generative', 'copilot', 'cognitive',
  'neural', 'nlp', 'natural language', 'bedrock', 'vertex', 'openai',
  'claude', 'gemini', 'anthropic', 'deep learning'
];

// ========================================
// Types
// ========================================

export interface ProductAuthorization {
  id: number;
  fedrampId: string;
  organizationId: number | null;
  parentAgencyName: string;
  subAgencyName: string | null;
  atoIssuanceDate: string | null;
  atoExpirationDate: string | null;
  createdAt: Date;
  // Joined fields (null from left join)
  organizationName: string | null;
  organizationSlug: string | null;
  organizationAbbreviation: string | null;
}

export interface AuthorizationWithProduct extends ProductAuthorization {
  cloudServiceProvider: string | null;
  cloudServiceOffering: string | null;
  serviceDescription: string | null;
  status: string | null;
}

export interface ProductWithAuthCount {
  fedrampId: string;
  cloudServiceProvider: string | null;
  cloudServiceOffering: string | null;
  status: string | null;
  authorizationCount: number;
}

export interface OrganizationAuthStats {
  directCount: number;
  totalAIProducts: number;
}

// ========================================
// Product Authorization Queries
// ========================================

/**
 * Get all authorizations for a specific product
 */
export async function getProductAuthorizations(fedrampId: string): Promise<ProductAuthorization[]> {
  const results = await db
    .select({
      id: productAuthorizations.id,
      fedrampId: productAuthorizations.fedrampId,
      organizationId: productAuthorizations.organizationId,
      parentAgencyName: productAuthorizations.parentAgencyName,
      subAgencyName: productAuthorizations.subAgencyName,
      atoIssuanceDate: productAuthorizations.atoIssuanceDate,
      atoExpirationDate: productAuthorizations.atoExpirationDate,
      createdAt: productAuthorizations.createdAt,
      organizationName: federalOrganizations.name,
      organizationSlug: federalOrganizations.slug,
      organizationAbbreviation: federalOrganizations.abbreviation,
    })
    .from(productAuthorizations)
    .leftJoin(
      federalOrganizations,
      eq(productAuthorizations.organizationId, federalOrganizations.id)
    )
    .where(eq(productAuthorizations.fedrampId, fedrampId))
    .orderBy(productAuthorizations.parentAgencyName);

  return results;
}

/**
 * Get authorization count for a specific product
 */
export async function getProductAuthorizationCount(fedrampId: string): Promise<number> {
  const result = await db
    .select({ count: count() })
    .from(productAuthorizations)
    .where(eq(productAuthorizations.fedrampId, fedrampId));

  return result[0]?.count ?? 0;
}

/**
 * Get authorizations grouped by parent agency for display
 */
export async function getProductAuthorizationsGrouped(fedrampId: string): Promise<{
  parentAgency: string;
  subAgencies: ProductAuthorization[];
}[]> {
  const auths = await getProductAuthorizations(fedrampId);

  // Group by parent agency
  const grouped = new Map<string, ProductAuthorization[]>();
  for (const auth of auths) {
    const existing = grouped.get(auth.parentAgencyName) || [];
    existing.push(auth);
    grouped.set(auth.parentAgencyName, existing);
  }

  // Convert to array and sort by count
  return Array.from(grouped.entries())
    .map(([parentAgency, subAgencies]) => ({
      parentAgency,
      subAgencies: subAgencies.sort((a, b) =>
        (a.subAgencyName || '').localeCompare(b.subAgencyName || '')
      ),
    }))
    .sort((a, b) => b.subAgencies.length - a.subAgencies.length);
}

// ========================================
// Organization Authorization Queries
// ========================================

/**
 * Get AI products authorized by an organization (filtered to AI/GenAI/LLM only)
 * Joins with products table to filter by AI-related keywords
 */
export async function getOrganizationAIAuthorizations(
  organizationId: number
): Promise<AuthorizationWithProduct[]> {
  // Build AI keyword filter - check name and description
  const aiFilter = sql`(
    ${sql.join(
      AI_KEYWORDS.map(keyword =>
        sql`LOWER(p.cloud_service_offering) LIKE ${`%${keyword}%`}
            OR LOWER(p.service_description) LIKE ${`%${keyword}%`}
            OR LOWER(p.business_categories) LIKE ${`%${keyword}%`}`
      ),
      sql` OR `
    )}
  )`;

  const results = await db.execute(sql`
    SELECT
      pa.id,
      pa.fedramp_id as "fedrampId",
      pa.organization_id as "organizationId",
      pa.parent_agency_name as "parentAgencyName",
      pa.sub_agency_name as "subAgencyName",
      pa.ato_issuance_date as "atoIssuanceDate",
      pa.ato_expiration_date as "atoExpirationDate",
      pa.created_at as "createdAt",
      p.cloud_service_provider as "cloudServiceProvider",
      p.cloud_service_offering as "cloudServiceOffering",
      p.service_description as "serviceDescription",
      p.status
    FROM product_authorizations pa
    INNER JOIN products p ON pa.fedramp_id = p.fedramp_id
    WHERE pa.organization_id = ${organizationId}
      AND ${aiFilter}
    ORDER BY pa.ato_issuance_date DESC NULLS LAST
  `);

  return results.rows as unknown as AuthorizationWithProduct[];
}

/**
 * Get AI authorization stats for an organization
 */
export async function getOrganizationAIAuthorizationStats(
  organizationId: number
): Promise<OrganizationAuthStats> {
  // Build AI keyword filter
  const aiFilter = sql`(
    ${sql.join(
      AI_KEYWORDS.map(keyword =>
        sql`LOWER(p.cloud_service_offering) LIKE ${`%${keyword}%`}
            OR LOWER(p.service_description) LIKE ${`%${keyword}%`}
            OR LOWER(p.business_categories) LIKE ${`%${keyword}%`}`
      ),
      sql` OR `
    )}
  )`;

  const result = await db.execute(sql`
    SELECT
      COUNT(DISTINCT pa.id) as "directCount",
      COUNT(DISTINCT pa.fedramp_id) as "totalAIProducts"
    FROM product_authorizations pa
    INNER JOIN products p ON pa.fedramp_id = p.fedramp_id
    WHERE pa.organization_id = ${organizationId}
      AND ${aiFilter}
  `);

  const row = result.rows[0] as { directCount: string; totalAIProducts: string } | undefined;

  return {
    directCount: parseInt(row?.directCount || '0', 10),
    totalAIProducts: parseInt(row?.totalAIProducts || '0', 10),
  };
}

// ========================================
// Top Products Queries
// ========================================

/**
 * Get products with most authorizations
 */
export async function getTopAuthorizedProducts(limit = 20): Promise<ProductWithAuthCount[]> {
  const results = await db.execute(sql`
    SELECT
      pa.fedramp_id as "fedrampId",
      p.cloud_service_provider as "cloudServiceProvider",
      p.cloud_service_offering as "cloudServiceOffering",
      p.status,
      COUNT(pa.id)::int as "authorizationCount"
    FROM product_authorizations pa
    INNER JOIN products p ON pa.fedramp_id = p.fedramp_id
    GROUP BY pa.fedramp_id, p.cloud_service_provider, p.cloud_service_offering, p.status
    ORDER BY "authorizationCount" DESC
    LIMIT ${limit}
  `);

  return results.rows as unknown as ProductWithAuthCount[];
}

/**
 * Get top AI products by authorization count
 */
export async function getTopAIAuthorizedProducts(limit = 20): Promise<ProductWithAuthCount[]> {
  const aiFilter = sql`(
    ${sql.join(
      AI_KEYWORDS.map(keyword =>
        sql`LOWER(p.cloud_service_offering) LIKE ${`%${keyword}%`}
            OR LOWER(p.service_description) LIKE ${`%${keyword}%`}
            OR LOWER(p.business_categories) LIKE ${`%${keyword}%`}`
      ),
      sql` OR `
    )}
  )`;

  const results = await db.execute(sql`
    SELECT
      pa.fedramp_id as "fedrampId",
      p.cloud_service_provider as "cloudServiceProvider",
      p.cloud_service_offering as "cloudServiceOffering",
      p.status,
      COUNT(pa.id)::int as "authorizationCount"
    FROM product_authorizations pa
    INNER JOIN products p ON pa.fedramp_id = p.fedramp_id
    WHERE ${aiFilter}
    GROUP BY pa.fedramp_id, p.cloud_service_provider, p.cloud_service_offering, p.status
    ORDER BY "authorizationCount" DESC
    LIMIT ${limit}
  `);

  return results.rows as unknown as ProductWithAuthCount[];
}

// ========================================
// Stats Queries
// ========================================

/**
 * Get overall authorization statistics
 */
export async function getAuthorizationStats(): Promise<{
  totalAuthorizations: number;
  uniqueProducts: number;
  uniqueAgencies: number;
  matchedToHierarchy: number;
}> {
  const result = await db.execute(sql`
    SELECT
      COUNT(*)::int as "totalAuthorizations",
      COUNT(DISTINCT fedramp_id)::int as "uniqueProducts",
      COUNT(DISTINCT parent_agency_name)::int as "uniqueAgencies",
      COUNT(CASE WHEN organization_id IS NOT NULL THEN 1 END)::int as "matchedToHierarchy"
    FROM product_authorizations
  `);

  const row = result.rows[0] as {
    totalAuthorizations: number;
    uniqueProducts: number;
    uniqueAgencies: number;
    matchedToHierarchy: number;
  };

  return row;
}
