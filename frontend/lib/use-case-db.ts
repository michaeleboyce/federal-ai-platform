import { db } from './db/client';
import { aiUseCases, aiUseCaseDetails, useCaseFedRampMatches } from './db/schema';
import { eq, and, or, like, sql, desc, ilike, isNull, SQL } from 'drizzle-orm';
import type { AIUseCase, AIUseCaseDetails } from './db/schema';

// Export types from schema directly (camelCase)
export type UseCase = AIUseCase;
export type UseCaseDetails = AIUseCaseDetails;

export interface UseCaseWithDetails extends UseCase {
  details?: UseCaseDetails;
}

export interface UseCaseFedRAMPMatch {
  productId: string;
  providerName: string;
  productName: string;
  confidence: 'high' | 'medium' | 'low';
  matchReason: string | null;
}

export interface UseCaseStats {
  total_use_cases: number;
  total_agencies: number;
  genai_count: number;
  llm_count: number;
  chatbot_count: number;
  classic_ml_count: number;
  coding_assistant_count: number;
  rights_impacting_count: number;
  implemented_count: number;
  in_development_count: number;
}

export interface DomainStats {
  domain_category: string;
  count: number;
  genai_count: number;
}

export interface AgencyUseCaseStats {
  agency: string;
  total_count: number;
  genai_count: number;
  llm_count: number;
  chatbot_count: number;
  classic_ml_count: number;
}

export interface UseCaseFilters {
  agency?: string;
  agency_abbreviation?: string;
  bureau?: string;
  domain?: string;
  stage?: string;
  aiType?: 'genai' | 'llm' | 'chatbot' | 'classic_ml' | 'coding' | 'rpa';
  provider?: string;
  topic_area?: string;
  rights_impacting?: boolean;
  search?: string;
  organizationId?: number;
}


/**
 * Get all use cases with optional filtering
 */
export async function getUseCases(filters?: UseCaseFilters): Promise<UseCase[]> {
  const conditions: SQL[] = [];

  if (filters) {
    if (filters.agency) {
      conditions.push(ilike(aiUseCases.agency, `%${filters.agency}%`));
    }

    if (filters.agency_abbreviation) {
      conditions.push(eq(aiUseCases.agencyAbbreviation, filters.agency_abbreviation));
    }

    if (filters.bureau) {
      conditions.push(ilike(aiUseCases.bureau, `%${filters.bureau}%`));
    }

    if (filters.domain) {
      conditions.push(eq(aiUseCases.domainCategory, filters.domain));
    }

    if (filters.stage) {
      conditions.push(eq(aiUseCases.stageOfDevelopment, filters.stage));
    }

    if (filters.topic_area) {
      conditions.push(eq(aiUseCases.useCaseTopicArea, filters.topic_area));
    }

    if (filters.aiType) {
      switch (filters.aiType) {
        case 'genai':
          conditions.push(eq(aiUseCases.genaiFlag, true));
          break;
        case 'llm':
          conditions.push(eq(aiUseCases.hasLlm, true));
          break;
        case 'chatbot':
          conditions.push(eq(aiUseCases.hasChatbot, true));
          break;
        case 'classic_ml':
          conditions.push(eq(aiUseCases.hasClassicMl, true));
          break;
        case 'coding':
          conditions.push(
            or(
              eq(aiUseCases.hasCodingAssistant, true),
              eq(aiUseCases.hasCodingAgent, true)
            )!
          );
          break;
        case 'rpa':
          conditions.push(eq(aiUseCases.hasRpa, true));
          break;
      }
    }

    if (filters.provider) {
      // For JSONB array contains check
      conditions.push(
        sql`${aiUseCases.providersDetected} @> ${JSON.stringify([filters.provider])}`
      );
    }

    if (filters.rights_impacting !== undefined) {
      if (filters.rights_impacting) {
        conditions.push(
          or(
            ilike(aiUseCases.isRightsSafetyImpacting, '%Rights%'),
            ilike(aiUseCases.isRightsSafetyImpacting, '%Both%')
          )!
        );
      } else {
        conditions.push(
          or(
            ilike(aiUseCases.isRightsSafetyImpacting, '%Neither%'),
            isNull(aiUseCases.isRightsSafetyImpacting)
          )!
        );
      }
    }

    if (filters.search) {
      const searchTerm = `%${filters.search}%`;
      conditions.push(
        or(
          ilike(aiUseCases.useCaseName, searchTerm),
          ilike(aiUseCases.agency, searchTerm),
          ilike(aiUseCases.bureau, searchTerm),
          ilike(aiUseCases.intendedPurpose, searchTerm),
          ilike(aiUseCases.outputs, searchTerm)
        )!
      );
    }

    if (filters.organizationId !== undefined) {
      conditions.push(eq(aiUseCases.organizationId, filters.organizationId));
    }
  }

  const results = await db
    .select()
    .from(aiUseCases)
    .where(conditions.length > 0 ? and(...conditions) : undefined)
    .orderBy(aiUseCases.agency, aiUseCases.useCaseName);

  return results;
}

/**
 * Get a single use case by slug with full details
 */
export async function getUseCaseBySlug(slug: string): Promise<UseCaseWithDetails | null> {
  const results = await db
    .select()
    .from(aiUseCases)
    .where(eq(aiUseCases.slug, slug))
    .limit(1);

  if (results.length === 0) {
    return null;
  }

  const useCase = results[0];

  // Fetch details
  const detailsResults = await db
    .select()
    .from(aiUseCaseDetails)
    .where(eq(aiUseCaseDetails.useCaseId, useCase.id))
    .limit(1);

  if (detailsResults.length > 0) {
    return {
      ...useCase,
      details: detailsResults[0],
    };
  }

  return useCase;
}

/**
 * Get all use cases for a specific agency
 */
export async function getUseCasesByAgency(agencyAbbr: string): Promise<UseCase[]> {
  return getUseCases({ agency_abbreviation: agencyAbbr });
}

/**
 * Get all use cases in a specific domain
 */
export async function getUseCasesByDomain(domain: string): Promise<UseCase[]> {
  return getUseCases({ domain });
}

/**
 * Get all use cases for a specific organization by ID
 */
export async function getUseCasesByOrganization(organizationId: number): Promise<UseCase[]> {
  return getUseCases({ organizationId });
}

/**
 * Get all use cases mentioning a specific provider
 */
export async function getUseCasesByProvider(provider: string): Promise<UseCase[]> {
  return getUseCases({ provider });
}

/**
 * Get aggregate statistics
 */
export async function getUseCaseStats(): Promise<UseCaseStats> {
  const result = await db
    .select({
      total_use_cases: sql<number>`count(*)::int`,
      total_agencies: sql<number>`count(distinct ${aiUseCases.agency})::int`,
      genai_count: sql<number>`sum(case when ${aiUseCases.genaiFlag} then 1 else 0 end)::int`,
      llm_count: sql<number>`sum(case when ${aiUseCases.hasLlm} then 1 else 0 end)::int`,
      chatbot_count: sql<number>`sum(case when ${aiUseCases.hasChatbot} then 1 else 0 end)::int`,
      classic_ml_count: sql<number>`sum(case when ${aiUseCases.hasClassicMl} then 1 else 0 end)::int`,
      coding_assistant_count: sql<number>`sum(case when ${aiUseCases.hasCodingAssistant} or ${aiUseCases.hasCodingAgent} then 1 else 0 end)::int`,
      rights_impacting_count: sql<number>`sum(case when ${aiUseCases.isRightsSafetyImpacting} like '%Rights%' or ${aiUseCases.isRightsSafetyImpacting} like '%Both%' then 1 else 0 end)::int`,
      implemented_count: sql<number>`sum(case when ${aiUseCases.dateImplemented} is not null and ${aiUseCases.dateImplemented} != '' then 1 else 0 end)::int`,
      in_development_count: sql<number>`sum(case when ${aiUseCases.stageOfDevelopment} like '%Development%' or ${aiUseCases.stageOfDevelopment} like '%Acquisition%' then 1 else 0 end)::int`,
    })
    .from(aiUseCases);

  return result[0];
}

/**
 * Get domain distribution statistics
 */
export async function getDomainStats(): Promise<DomainStats[]> {
  const results = await db
    .select({
      domain_category: aiUseCases.domainCategory,
      count: sql<number>`count(*)::int`,
      genai_count: sql<number>`sum(case when ${aiUseCases.genaiFlag} then 1 else 0 end)::int`,
    })
    .from(aiUseCases)
    .where(and(
      sql`${aiUseCases.domainCategory} is not null`,
      sql`${aiUseCases.domainCategory} != ''`
    ))
    .groupBy(aiUseCases.domainCategory)
    .orderBy(desc(sql`count(*)`));

  return results.map(r => ({
    domain_category: r.domain_category!,
    count: r.count,
    genai_count: r.genai_count,
  }));
}

/**
 * Get use case statistics by agency
 */
export async function getAgencyUseCaseStats(agency?: string): Promise<AgencyUseCaseStats[]> {
  const baseQuery = db
    .select({
      agency: aiUseCases.agency,
      total_count: sql<number>`count(*)::int`,
      genai_count: sql<number>`sum(case when ${aiUseCases.genaiFlag} then 1 else 0 end)::int`,
      llm_count: sql<number>`sum(case when ${aiUseCases.hasLlm} then 1 else 0 end)::int`,
      chatbot_count: sql<number>`sum(case when ${aiUseCases.hasChatbot} then 1 else 0 end)::int`,
      classic_ml_count: sql<number>`sum(case when ${aiUseCases.hasClassicMl} then 1 else 0 end)::int`,
    })
    .from(aiUseCases);

  const results = await (agency
    ? baseQuery.where(eq(aiUseCases.agency, agency))
    : baseQuery
  )
    .groupBy(aiUseCases.agency)
    .orderBy(desc(sql`count(*)`));

  return results.map(r => ({
    agency: r.agency,
    total_count: r.total_count,
    genai_count: r.genai_count,
    llm_count: r.llm_count,
    chatbot_count: r.chatbot_count,
    classic_ml_count: r.classic_ml_count,
  }));
}

/**
 * Get FedRAMP service matches for a use case
 */
export async function getUseCaseFedRAMPMatches(useCaseId: number): Promise<UseCaseFedRAMPMatch[]> {
  const results = await db
    .select({
      productId: useCaseFedRampMatches.productId,
      providerName: useCaseFedRampMatches.providerName,
      productName: useCaseFedRampMatches.productName,
      confidence: useCaseFedRampMatches.confidence,
      matchReason: useCaseFedRampMatches.matchReason,
    })
    .from(useCaseFedRampMatches)
    .where(eq(useCaseFedRampMatches.useCaseId, useCaseId))
    .orderBy(
      sql`case ${useCaseFedRampMatches.confidence} when 'high' then 1 when 'medium' then 2 when 'low' then 3 end`,
      useCaseFedRampMatches.providerName
    );

  return results;
}

/**
 * Get all unique values for a field (for filter dropdowns)
 */
export async function getUniqueValues(
  field: 'domain_category' | 'stage_of_development' | 'use_case_topic_area' | 'agency'
): Promise<string[]> {
  const columnMap = {
    domain_category: aiUseCases.domainCategory,
    stage_of_development: aiUseCases.stageOfDevelopment,
    use_case_topic_area: aiUseCases.useCaseTopicArea,
    agency: aiUseCases.agency,
  };

  const column = columnMap[field];

  const results = await db
    .selectDistinct({ value: column })
    .from(aiUseCases)
    .where(and(sql`${column} is not null`, sql`${column} != ''`))
    .orderBy(column);

  return results.map(r => r.value!);
}

/**
 * Get recent use cases (by implementation date)
 */
export async function getRecentUseCases(limit: number = 10): Promise<UseCase[]> {
  const results = await db
    .select()
    .from(aiUseCases)
    .where(and(
      sql`${aiUseCases.dateImplemented} is not null`,
      sql`${aiUseCases.dateImplemented} != ''`
    ))
    .orderBy(desc(aiUseCases.dateImplemented))
    .limit(limit);

  return results;
}

/**
 * Search use cases with full-text search
 */
export async function searchUseCases(query: string): Promise<UseCase[]> {
  return getUseCases({ search: query });
}

/**
 * Get count of use cases by provider
 */
export async function getProviderUseCaseCounts(): Promise<Array<{ provider: string; count: number }>> {
  const results = await db
    .select({
      providers_detected: aiUseCases.providersDetected,
    })
    .from(aiUseCases)
    .where(
      and(
        sql`${aiUseCases.providersDetected} is not null`,
        sql`jsonb_array_length(${aiUseCases.providersDetected}) > 0`
      )
    );

  // Count provider mentions
  const providerCounts: Record<string, number> = {};

  results.forEach((uc) => {
    const providers = uc.providers_detected as unknown as string[];
    if (Array.isArray(providers)) {
      providers.forEach((provider) => {
        providerCounts[provider] = (providerCounts[provider] || 0) + 1;
      });
    }
  });

  // Convert to array and sort
  return Object.entries(providerCounts)
    .map(([provider, count]) => ({ provider, count }))
    .sort((a, b) => b.count - a.count);
}
