import { db } from './db/client';
import {
  incidents,
  entities,
  incidentEntities,
  incidentSecurity,
  incidentProductMatches,
  incidentUseCaseMatches,
  aiUseCases,
  semanticMatches,
  type Incident,
  type Entity,
  type IncidentSecurity,
} from './db/schema';
import { eq, and, or, like, sql, desc, ilike, SQL, gte } from 'drizzle-orm';

// Export types
export type { Incident, Entity, IncidentSecurity };

export interface IncidentWithSecurity extends Incident {
  security?: IncidentSecurity;
}

export interface IncidentEntityInfo {
  entityId: string;
  name: string;
  role: string;
}

export interface IncidentProductMatchInfo {
  productFedrampId: string;
  providerName: string;
  productName: string;
  confidence: string;
  matchReason: string | null;
  matchType: string;
}

export interface IncidentUseCaseMatchInfo {
  useCaseId: number;
  useCaseName: string;
  agency: string;
  confidence: string;
  matchReason: string | null;
  matchType: string;
}

export interface IncidentStats {
  totalIncidents: number;
  llmIncidents: number;
  dataLeakIncidents: number;
  cyberAttackIncidents: number;
  totalEntities: number;
  productsLinked: number;
  useCasesLinked: number;
}

export interface IncidentFilters {
  search?: string;
  hasLlm?: boolean;
  hasDataLeak?: boolean;
  hasCyberAttack?: boolean;
  year?: string;
  entity?: string;
}

/**
 * Get all incidents with optional filtering
 */
export async function getIncidents(filters?: IncidentFilters): Promise<Incident[]> {
  let baseQuery = db.select().from(incidents);

  if (filters?.search) {
    const searchTerm = `%${filters.search}%`;
    baseQuery = baseQuery.where(
      or(
        ilike(incidents.title, searchTerm),
        ilike(incidents.description, searchTerm)
      )!
    ) as typeof baseQuery;
  }

  if (filters?.year) {
    baseQuery = baseQuery.where(
      like(incidents.date, `${filters.year}%`)
    ) as typeof baseQuery;
  }

  const results = await baseQuery.orderBy(desc(incidents.incidentId)).limit(500);

  // Apply post-query filters for security data
  if (filters?.hasLlm || filters?.hasDataLeak || filters?.hasCyberAttack) {
    const incidentIds = results.map(r => r.incidentId);
    if (incidentIds.length === 0) return [];

    const securityData = await db
      .select()
      .from(incidentSecurity)
      .where(sql`${incidentSecurity.incidentId} IN (${sql.join(incidentIds.map(id => sql`${id}`), sql`, `)})`);

    const securityMap = new Map(securityData.map(s => [s.incidentId, s]));

    return results.filter(incident => {
      const security = securityMap.get(incident.incidentId);
      if (!security) return false;

      if (filters?.hasLlm && !security.llmOrChatbotInvolved) return false;
      if (filters?.hasDataLeak && security.securityDataLeakPresence !== 'confirmed' && security.securityDataLeakPresence !== 'suspected') return false;
      if (filters?.hasCyberAttack && security.cyberAttackFlag !== 'confirmed_attack' && security.cyberAttackFlag !== 'suspected_attack') return false;

      return true;
    });
  }

  return results;
}

/**
 * Get a single incident by incident_id
 */
export async function getIncidentById(incidentId: number): Promise<IncidentWithSecurity | null> {
  const results = await db
    .select()
    .from(incidents)
    .where(eq(incidents.incidentId, incidentId))
    .limit(1);

  if (results.length === 0) return null;

  const incident = results[0];

  // Get security data
  const securityResults = await db
    .select()
    .from(incidentSecurity)
    .where(eq(incidentSecurity.incidentId, incidentId))
    .limit(1);

  return {
    ...incident,
    security: securityResults.length > 0 ? securityResults[0] : undefined,
  };
}

/**
 * Get entities for an incident
 */
export async function getIncidentEntities(incidentId: number): Promise<IncidentEntityInfo[]> {
  const results = await db
    .select({
      entityId: incidentEntities.entityId,
      name: entities.name,
      role: incidentEntities.role,
    })
    .from(incidentEntities)
    .leftJoin(entities, eq(incidentEntities.entityId, entities.entityId))
    .where(eq(incidentEntities.incidentId, incidentId));

  return results.map(r => ({
    entityId: r.entityId,
    name: r.name || r.entityId,
    role: r.role,
  }));
}

/**
 * Get FedRAMP product matches for an incident
 */
export async function getIncidentProductMatches(incidentId: number): Promise<IncidentProductMatchInfo[]> {
  const results = await db
    .select({
      productFedrampId: incidentProductMatches.productFedrampId,
      confidence: incidentProductMatches.confidence,
      matchReason: incidentProductMatches.matchReason,
      matchType: incidentProductMatches.matchType,
    })
    .from(incidentProductMatches)
    .where(eq(incidentProductMatches.incidentId, incidentId))
    .orderBy(
      sql`case ${incidentProductMatches.confidence} when 'high' then 1 when 'medium' then 2 when 'low' then 3 end`
    );

  // Get product details for each match
  if (results.length === 0) return [];

  // Look up product info from products table
  const productIds = results.map(r => r.productFedrampId);
  const productInfo = await db.execute(
    sql`SELECT fedramp_id, cloud_service_provider, cloud_service_offering FROM products WHERE fedramp_id IN (${sql.join(productIds.map(id => sql`${id}`), sql`, `)})`
  );

  const productMap = new Map((productInfo.rows as any[]).map(p => [p.fedramp_id, p]));

  return results.map(r => {
    const product = productMap.get(r.productFedrampId);
    return {
      productFedrampId: r.productFedrampId,
      providerName: product?.cloud_service_provider || 'Unknown',
      productName: product?.cloud_service_offering || r.productFedrampId,
      confidence: r.confidence,
      matchReason: r.matchReason,
      matchType: r.matchType,
    };
  });
}

/**
 * Get use case matches for an incident
 */
export async function getIncidentUseCaseMatches(incidentId: number): Promise<IncidentUseCaseMatchInfo[]> {
  const results = await db
    .select({
      useCaseId: incidentUseCaseMatches.useCaseId,
      confidence: incidentUseCaseMatches.confidence,
      matchReason: incidentUseCaseMatches.matchReason,
      matchType: incidentUseCaseMatches.matchType,
    })
    .from(incidentUseCaseMatches)
    .where(eq(incidentUseCaseMatches.incidentId, incidentId))
    .orderBy(
      sql`case ${incidentUseCaseMatches.confidence} when 'high' then 1 when 'medium' then 2 when 'low' then 3 end`
    )
    .limit(10);

  if (results.length === 0) return [];

  // Get use case details
  const useCaseIds = results.map(r => r.useCaseId);
  const useCaseInfo = await db
    .select({ id: aiUseCases.id, useCaseName: aiUseCases.useCaseName, agency: aiUseCases.agency })
    .from(aiUseCases)
    .where(sql`${aiUseCases.id} IN (${sql.join(useCaseIds.map(id => sql`${id}`), sql`, `)})`);

  const useCaseMap = new Map(useCaseInfo.map(uc => [uc.id, uc]));

  return results.map(r => {
    const useCase = useCaseMap.get(r.useCaseId);
    return {
      useCaseId: r.useCaseId,
      useCaseName: useCase?.useCaseName || `Use Case ${r.useCaseId}`,
      agency: useCase?.agency || 'Unknown',
      confidence: r.confidence,
      matchReason: r.matchReason,
      matchType: r.matchType,
    };
  });
}

/**
 * Get incident statistics
 */
export async function getIncidentStats(): Promise<IncidentStats> {
  const [incidentCount] = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(incidents);

  const [entityCount] = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(entities);

  const [llmCount] = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(incidentSecurity)
    .where(eq(incidentSecurity.llmOrChatbotInvolved, true));

  const [dataLeakCount] = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(incidentSecurity)
    .where(
      or(
        eq(incidentSecurity.securityDataLeakPresence, 'confirmed'),
        eq(incidentSecurity.securityDataLeakPresence, 'suspected')
      )
    );

  const [cyberAttackCount] = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(incidentSecurity)
    .where(
      or(
        eq(incidentSecurity.cyberAttackFlag, 'confirmed_attack'),
        eq(incidentSecurity.cyberAttackFlag, 'suspected_attack')
      )
    );

  const [productMatchCount] = await db
    .select({ count: sql<number>`count(distinct ${incidentProductMatches.productFedrampId})::int` })
    .from(incidentProductMatches);

  const [useCaseMatchCount] = await db
    .select({ count: sql<number>`count(distinct ${incidentUseCaseMatches.useCaseId})::int` })
    .from(incidentUseCaseMatches);

  return {
    totalIncidents: incidentCount.count,
    llmIncidents: llmCount.count,
    dataLeakIncidents: dataLeakCount.count,
    cyberAttackIncidents: cyberAttackCount.count,
    totalEntities: entityCount.count,
    productsLinked: productMatchCount.count,
    useCasesLinked: useCaseMatchCount.count,
  };
}

/**
 * Get incidents by year
 */
export async function getIncidentsByYear(): Promise<Array<{ year: string; count: number }>> {
  const results = await db
    .select({
      year: sql<string>`substring(${incidents.date} from 1 for 4)`,
      count: sql<number>`count(*)::int`,
    })
    .from(incidents)
    .where(sql`${incidents.date} is not null AND ${incidents.date} != ''`)
    .groupBy(sql`substring(${incidents.date} from 1 for 4)`)
    .orderBy(desc(sql`substring(${incidents.date} from 1 for 4)`));

  return results.map(r => ({
    year: r.year || 'Unknown',
    count: r.count,
  }));
}

/**
 * Get all unique entities with incident counts
 */
export async function getTopEntities(limit: number = 20): Promise<Array<{ entityId: string; name: string; incidentCount: number }>> {
  const results = await db
    .select({
      entityId: entities.entityId,
      name: entities.name,
      incidentCount: sql<number>`count(distinct ${incidentEntities.incidentId})::int`,
    })
    .from(entities)
    .leftJoin(incidentEntities, eq(entities.entityId, incidentEntities.entityId))
    .groupBy(entities.entityId, entities.name)
    .orderBy(desc(sql`count(distinct ${incidentEntities.incidentId})`))
    .limit(limit);

  return results.map(r => ({
    entityId: r.entityId,
    name: r.name,
    incidentCount: r.incidentCount,
  }));
}

/**
 * Get incidents for a specific entity
 */
export async function getIncidentsByEntity(entityId: string): Promise<Incident[]> {
  const incidentIds = await db
    .select({ incidentId: incidentEntities.incidentId })
    .from(incidentEntities)
    .where(eq(incidentEntities.entityId, entityId));

  if (incidentIds.length === 0) return [];

  const ids = incidentIds.map(r => r.incidentId);
  return await db
    .select()
    .from(incidents)
    .where(sql`${incidents.incidentId} IN (${sql.join(ids.map(id => sql`${id}`), sql`, `)})`)
    .orderBy(desc(incidents.incidentId));
}

/**
 * Get recent incidents
 */
export async function getRecentIncidents(limit: number = 10): Promise<Incident[]> {
  return await db
    .select()
    .from(incidents)
    .orderBy(desc(incidents.date), desc(incidents.incidentId))
    .limit(limit);
}

/**
 * Search incidents
 */
export async function searchIncidents(query: string): Promise<Incident[]> {
  return getIncidents({ search: query });
}

// ========================================
// HYBRID SEMANTIC MATCHING FUNCTIONS
// ========================================

export interface SemanticIncidentMatch {
  incidentId: number;
  title: string;
  description: string | null;
  date: string | null;
  similarityScore: number;
  matchSource: 'semantic' | 'text' | 'hybrid';
  // Security flags for risk display
  hasDataLeak?: boolean;
  hasCyberAttack?: boolean;
  hasLlm?: boolean;
}

export interface SemanticProductMatch {
  productFedrampId: string;
  productName: string;
  providerName: string;
  similarityScore: number;
  matchSource: 'semantic' | 'text' | 'hybrid';
}

export interface SemanticUseCaseMatch {
  useCaseId: number;
  useCaseName: string;
  agency: string;
  slug: string;
  similarityScore: number;
  matchSource: 'semantic' | 'text' | 'hybrid';
}

const SIMILARITY_THRESHOLD = 0.70; // High threshold for quality matches

/**
 * Get incidents related to a product using hybrid matching
 * Combines semantic similarity with text-based entity matching
 */
export async function getProductRelatedIncidents(
  productFedrampId: string,
  limit: number = 10
): Promise<SemanticIncidentMatch[]> {
  // Get semantic matches (product -> incident)
  const semanticResults = await db.execute(sql`
    SELECT
      sm.source_id as incident_id,
      sm.similarity_score,
      i.title,
      i.description,
      i.date,
      sec.security_data_leak_presence,
      sec.cyber_attack_flag,
      sec.llm_or_chatbot_involved
    FROM semantic_matches sm
    JOIN incidents i ON sm.source_id = i.incident_id::text
    LEFT JOIN incident_security sec ON i.incident_id = sec.incident_id
    WHERE sm.target_type = 'product'
      AND sm.target_id = ${productFedrampId}
      AND sm.source_type = 'incident'
      AND sm.similarity_score >= ${SIMILARITY_THRESHOLD}
    ORDER BY sm.similarity_score DESC
    LIMIT ${limit}
  `);

  // Get text-based matches from incident_product_matches
  const textResults = await db.execute(sql`
    SELECT
      ipm.incident_id,
      i.title,
      i.description,
      i.date,
      ipm.confidence,
      sec.security_data_leak_presence,
      sec.cyber_attack_flag,
      sec.llm_or_chatbot_involved
    FROM incident_product_matches ipm
    JOIN incidents i ON ipm.incident_id = i.incident_id
    LEFT JOIN incident_security sec ON i.incident_id = sec.incident_id
    WHERE ipm.product_fedramp_id = ${productFedrampId}
    ORDER BY
      CASE ipm.confidence
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        WHEN 'low' THEN 3
      END
    LIMIT ${limit}
  `);

  // Merge and deduplicate
  const incidentMap = new Map<number, SemanticIncidentMatch>();

  // Add semantic matches first (higher priority)
  for (const row of semanticResults.rows as any[]) {
    const incidentId = parseInt(row.incident_id);
    incidentMap.set(incidentId, {
      incidentId,
      title: row.title,
      description: row.description,
      date: row.date,
      similarityScore: row.similarity_score,
      matchSource: 'semantic',
      hasDataLeak: row.security_data_leak_presence === 'confirmed' || row.security_data_leak_presence === 'suspected',
      hasCyberAttack: row.cyber_attack_flag === 'confirmed_attack' || row.cyber_attack_flag === 'suspected_attack',
      hasLlm: row.llm_or_chatbot_involved === true,
    });
  }

  // Add text matches, marking hybrid if already exists
  for (const row of textResults.rows as any[]) {
    const incidentId = row.incident_id;
    if (incidentMap.has(incidentId)) {
      // Already have semantic match, mark as hybrid
      const existing = incidentMap.get(incidentId)!;
      existing.matchSource = 'hybrid';
    } else {
      // Text-only match - assign confidence-based score
      const confidenceScore = row.confidence === 'high' ? 0.85 : row.confidence === 'medium' ? 0.70 : 0.55;
      incidentMap.set(incidentId, {
        incidentId,
        title: row.title,
        description: row.description,
        date: row.date,
        similarityScore: confidenceScore,
        matchSource: 'text',
        hasDataLeak: row.security_data_leak_presence === 'confirmed' || row.security_data_leak_presence === 'suspected',
        hasCyberAttack: row.cyber_attack_flag === 'confirmed_attack' || row.cyber_attack_flag === 'suspected_attack',
        hasLlm: row.llm_or_chatbot_involved === true,
      });
    }
  }

  // Sort by score and return
  return Array.from(incidentMap.values())
    .sort((a, b) => b.similarityScore - a.similarityScore)
    .slice(0, limit);
}

/**
 * Get incidents related to a use case using hybrid matching
 */
export async function getUseCaseRelatedIncidents(
  useCaseId: number,
  limit: number = 10
): Promise<SemanticIncidentMatch[]> {
  // Get semantic matches (use_case -> incident)
  const semanticResults = await db.execute(sql`
    SELECT
      sm.source_id as incident_id,
      sm.similarity_score,
      i.title,
      i.description,
      i.date,
      sec.security_data_leak_presence,
      sec.cyber_attack_flag,
      sec.llm_or_chatbot_involved
    FROM semantic_matches sm
    JOIN incidents i ON sm.source_id = i.incident_id::text
    LEFT JOIN incident_security sec ON i.incident_id = sec.incident_id
    WHERE sm.target_type = 'use_case'
      AND sm.target_id = ${useCaseId.toString()}
      AND sm.source_type = 'incident'
      AND sm.similarity_score >= ${SIMILARITY_THRESHOLD}
    ORDER BY sm.similarity_score DESC
    LIMIT ${limit}
  `);

  // Get text-based matches
  const textResults = await db.execute(sql`
    SELECT
      ium.incident_id,
      i.title,
      i.description,
      i.date,
      ium.confidence,
      sec.security_data_leak_presence,
      sec.cyber_attack_flag,
      sec.llm_or_chatbot_involved
    FROM incident_use_case_matches ium
    JOIN incidents i ON ium.incident_id = i.incident_id
    LEFT JOIN incident_security sec ON i.incident_id = sec.incident_id
    WHERE ium.use_case_id = ${useCaseId}
    ORDER BY
      CASE ium.confidence
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        WHEN 'low' THEN 3
      END
    LIMIT ${limit}
  `);

  // Merge and deduplicate
  const incidentMap = new Map<number, SemanticIncidentMatch>();

  for (const row of semanticResults.rows as any[]) {
    const incidentId = parseInt(row.incident_id);
    incidentMap.set(incidentId, {
      incidentId,
      title: row.title,
      description: row.description,
      date: row.date,
      similarityScore: row.similarity_score,
      matchSource: 'semantic',
      hasDataLeak: row.security_data_leak_presence === 'confirmed' || row.security_data_leak_presence === 'suspected',
      hasCyberAttack: row.cyber_attack_flag === 'confirmed_attack' || row.cyber_attack_flag === 'suspected_attack',
      hasLlm: row.llm_or_chatbot_involved === true,
    });
  }

  for (const row of textResults.rows as any[]) {
    const incidentId = row.incident_id;
    if (incidentMap.has(incidentId)) {
      const existing = incidentMap.get(incidentId)!;
      existing.matchSource = 'hybrid';
    } else {
      const confidenceScore = row.confidence === 'high' ? 0.85 : row.confidence === 'medium' ? 0.70 : 0.55;
      incidentMap.set(incidentId, {
        incidentId,
        title: row.title,
        description: row.description,
        date: row.date,
        similarityScore: confidenceScore,
        matchSource: 'text',
        hasDataLeak: row.security_data_leak_presence === 'confirmed' || row.security_data_leak_presence === 'suspected',
        hasCyberAttack: row.cyber_attack_flag === 'confirmed_attack' || row.cyber_attack_flag === 'suspected_attack',
        hasLlm: row.llm_or_chatbot_involved === true,
      });
    }
  }

  return Array.from(incidentMap.values())
    .sort((a, b) => b.similarityScore - a.similarityScore)
    .slice(0, limit);
}

/**
 * Get products related to an incident using hybrid matching
 */
export async function getIncidentRelatedProducts(
  incidentId: number,
  limit: number = 10
): Promise<SemanticProductMatch[]> {
  // Get semantic matches
  const semanticResults = await db.execute(sql`
    SELECT
      sm.target_id as product_id,
      sm.similarity_score,
      p.cloud_service_offering as product_name,
      p.cloud_service_provider as provider_name
    FROM semantic_matches sm
    JOIN products p ON sm.target_id = p.fedramp_id
    WHERE sm.source_type = 'incident'
      AND sm.source_id = ${incidentId.toString()}
      AND sm.target_type = 'product'
      AND sm.similarity_score >= ${SIMILARITY_THRESHOLD}
    ORDER BY sm.similarity_score DESC
    LIMIT ${limit}
  `);

  // Get text-based matches
  const textResults = await db.execute(sql`
    SELECT
      ipm.product_fedramp_id as product_id,
      ipm.confidence,
      p.cloud_service_offering as product_name,
      p.cloud_service_provider as provider_name
    FROM incident_product_matches ipm
    JOIN products p ON ipm.product_fedramp_id = p.fedramp_id
    WHERE ipm.incident_id = ${incidentId}
    ORDER BY
      CASE ipm.confidence
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        WHEN 'low' THEN 3
      END
    LIMIT ${limit}
  `);

  const productMap = new Map<string, SemanticProductMatch>();

  for (const row of semanticResults.rows as any[]) {
    productMap.set(row.product_id, {
      productFedrampId: row.product_id,
      productName: row.product_name,
      providerName: row.provider_name,
      similarityScore: row.similarity_score,
      matchSource: 'semantic',
    });
  }

  for (const row of textResults.rows as any[]) {
    if (productMap.has(row.product_id)) {
      const existing = productMap.get(row.product_id)!;
      existing.matchSource = 'hybrid';
    } else {
      const confidenceScore = row.confidence === 'high' ? 0.85 : row.confidence === 'medium' ? 0.70 : 0.55;
      productMap.set(row.product_id, {
        productFedrampId: row.product_id,
        productName: row.product_name,
        providerName: row.provider_name,
        similarityScore: confidenceScore,
        matchSource: 'text',
      });
    }
  }

  return Array.from(productMap.values())
    .sort((a, b) => b.similarityScore - a.similarityScore)
    .slice(0, limit);
}

/**
 * Get use cases related to an incident using hybrid matching
 */
export async function getIncidentRelatedUseCases(
  incidentId: number,
  limit: number = 10
): Promise<SemanticUseCaseMatch[]> {
  // Get semantic matches
  const semanticResults = await db.execute(sql`
    SELECT
      sm.target_id as use_case_id,
      sm.similarity_score,
      u.use_case_name,
      u.agency,
      u.slug
    FROM semantic_matches sm
    JOIN ai_use_cases u ON sm.target_id = u.id::text
    WHERE sm.source_type = 'incident'
      AND sm.source_id = ${incidentId.toString()}
      AND sm.target_type = 'use_case'
      AND sm.similarity_score >= ${SIMILARITY_THRESHOLD}
    ORDER BY sm.similarity_score DESC
    LIMIT ${limit}
  `);

  // Get text-based matches
  const textResults = await db.execute(sql`
    SELECT
      ium.use_case_id,
      ium.confidence,
      u.use_case_name,
      u.agency,
      u.slug
    FROM incident_use_case_matches ium
    JOIN ai_use_cases u ON ium.use_case_id = u.id
    WHERE ium.incident_id = ${incidentId}
    ORDER BY
      CASE ium.confidence
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        WHEN 'low' THEN 3
      END
    LIMIT ${limit}
  `);

  const useCaseMap = new Map<number, SemanticUseCaseMatch>();

  for (const row of semanticResults.rows as any[]) {
    const ucId = parseInt(row.use_case_id);
    useCaseMap.set(ucId, {
      useCaseId: ucId,
      useCaseName: row.use_case_name,
      agency: row.agency,
      slug: row.slug,
      similarityScore: row.similarity_score,
      matchSource: 'semantic',
    });
  }

  for (const row of textResults.rows as any[]) {
    if (useCaseMap.has(row.use_case_id)) {
      const existing = useCaseMap.get(row.use_case_id)!;
      existing.matchSource = 'hybrid';
    } else {
      const confidenceScore = row.confidence === 'high' ? 0.85 : row.confidence === 'medium' ? 0.70 : 0.55;
      useCaseMap.set(row.use_case_id, {
        useCaseId: row.use_case_id,
        useCaseName: row.use_case_name,
        agency: row.agency,
        slug: row.slug,
        similarityScore: confidenceScore,
        matchSource: 'text',
      });
    }
  }

  return Array.from(useCaseMap.values())
    .sort((a, b) => b.similarityScore - a.similarityScore)
    .slice(0, limit);
}

/**
 * Get all products with their max incident match score
 * Used for filtering products by incident relevance
 */
export async function getProductsWithIncidentScores(): Promise<
  Map<string, { maxScore: number; matchCount: number }>
> {
  const result = await db.execute(sql`
    SELECT
      sm.target_id as product_id,
      MAX(sm.similarity_score) as max_score,
      COUNT(*) as match_count
    FROM semantic_matches sm
    WHERE sm.source_type = 'incident'
      AND sm.target_type = 'product'
      AND sm.similarity_score >= 0.60
    GROUP BY sm.target_id
  `);

  const scoreMap = new Map<string, { maxScore: number; matchCount: number }>();
  for (const row of result.rows as any[]) {
    scoreMap.set(row.product_id, {
      maxScore: row.max_score,
      matchCount: parseInt(row.match_count),
    });
  }

  return scoreMap;
}

/**
 * Get all use cases with their max incident match score
 * Used for filtering use cases by incident relevance
 */
export async function getUseCasesWithIncidentScores(): Promise<
  Map<number, { maxScore: number; matchCount: number }>
> {
  const result = await db.execute(sql`
    SELECT
      sm.target_id as use_case_id,
      MAX(sm.similarity_score) as max_score,
      COUNT(*) as match_count
    FROM semantic_matches sm
    WHERE sm.source_type = 'incident'
      AND sm.target_type = 'use_case'
      AND sm.similarity_score >= 0.60
    GROUP BY sm.target_id
  `);

  const scoreMap = new Map<number, { maxScore: number; matchCount: number }>();
  for (const row of result.rows as any[]) {
    scoreMap.set(parseInt(row.use_case_id), {
      maxScore: row.max_score,
      matchCount: parseInt(row.match_count),
    });
  }

  return scoreMap;
}
