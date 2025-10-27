import { db } from './db/client';
import { aiUseCases, aiUseCaseDetails, useCaseFedRampMatches } from './db/schema';
import { eq, and, or, like, sql, desc, ilike, SQL } from 'drizzle-orm';
import type { AIUseCase, AIUseCaseDetails } from './db/schema';

// Re-export types from schema with legacy names for compatibility
export type UseCase = AIUseCase & {
  // Transform camelCase to snake_case for backwards compatibility
  use_case_name: string;
  agency_abbreviation: string | null;
  use_case_topic_area: string | null;
  other_use_case_topic_area: string | null;
  intended_purpose: string | null;
  stage_of_development: string | null;
  is_rights_safety_impacting: string | null;
  domain_category: string | null;
  date_initiated: string | null;
  date_implemented: string | null;
  date_retired: string | null;
  has_llm: boolean;
  has_genai: boolean;
  has_chatbot: boolean;
  has_gp_markers: boolean;
  has_coding_assistant: boolean;
  has_coding_agent: boolean;
  has_classic_ml: boolean;
  has_rpa: boolean;
  has_rules: boolean;
  general_purpose_chatbot: boolean;
  domain_chatbot: boolean;
  coding_assistant: boolean;
  coding_agent: boolean;
  genai_flag: boolean;
  ai_type_classic_ml: boolean;
  ai_type_rpa_rules: boolean;
  providers_detected: string[]; // JSONB array
  commercial_ai_product: string | null;
  analyzed_at: Date;
};

export type UseCaseDetails = AIUseCaseDetails & {
  use_case_id: number;
  development_approach: string | null;
  procurement_instrument: string | null;
  supports_hisp: string | null;
  which_hisp: string | null;
  which_public_service: string | null;
  disseminates_to_public: string | null;
  involves_pii: string | null;
  privacy_assessed: string | null;
  has_data_catalog: string | null;
  agency_owned_data: string | null;
  data_documentation: string | null;
  demographic_variables: string | null;
  has_custom_code: string | null;
  has_code_access: string | null;
  code_link: string | null;
  has_ato: string | null;
  system_name: string | null;
  wait_time_dev_tools: string | null;
  centralized_intake: string | null;
  has_compute_process: string | null;
  timely_communication: string | null;
  infrastructure_reuse: string | null;
  internal_review: string | null;
  requested_extension: string | null;
  impact_assessment: string | null;
  operational_testing: string | null;
  key_risks: string | null;
  independent_evaluation: string | null;
  performance_monitoring: string | null;
  autonomous_decision: string | null;
  public_notice: string | null;
  influences_decisions: string | null;
  disparity_mitigation: string | null;
  stakeholder_feedback: string | null;
  fallback_process: string | null;
  opt_out_mechanism: string | null;
  info_quality_compliance: string | null;
  search_text: string | null;
};

export interface UseCaseWithDetails extends UseCase {
  details?: UseCaseDetails;
}

export interface UseCaseFedRAMPMatch {
  product_id: string;
  provider_name: string;
  product_name: string;
  confidence: 'high' | 'medium' | 'low';
  match_reason: string | null;
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
}

/**
 * Transform Drizzle result to legacy format
 */
function transformUseCase(result: AIUseCase): UseCase {
  return {
    ...result,
    use_case_name: result.useCaseName,
    agency_abbreviation: result.agencyAbbreviation,
    use_case_topic_area: result.useCaseTopicArea,
    other_use_case_topic_area: result.otherUseCaseTopicArea,
    intended_purpose: result.intendedPurpose,
    stage_of_development: result.stageOfDevelopment,
    is_rights_safety_impacting: result.isRightsSafetyImpacting,
    domain_category: result.domainCategory,
    date_initiated: result.dateInitiated,
    date_implemented: result.dateImplemented,
    date_retired: result.dateRetired,
    has_llm: result.hasLlm,
    has_genai: result.hasGenai,
    has_chatbot: result.hasChatbot,
    has_gp_markers: result.hasGpMarkers,
    has_coding_assistant: result.hasCodingAssistant,
    has_coding_agent: result.hasCodingAgent,
    has_classic_ml: result.hasClassicMl,
    has_rpa: result.hasRpa,
    has_rules: result.hasRules,
    general_purpose_chatbot: result.generalPurposeChatbot,
    domain_chatbot: result.domainChatbot,
    coding_assistant: result.codingAssistant,
    coding_agent: result.codingAgent,
    genai_flag: result.genaiFlag,
    ai_type_classic_ml: result.aiTypeClassicMl,
    ai_type_rpa_rules: result.aiTypeRpaRules,
    providers_detected: result.providersDetected as string[],
    commercial_ai_product: result.commercialAiProduct,
    analyzed_at: result.analyzedAt,
  };
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
            eq(aiUseCases.isRightsSafetyImpacting, null)
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
  }

  const results = await db
    .select()
    .from(aiUseCases)
    .where(conditions.length > 0 ? and(...conditions) : undefined)
    .orderBy(aiUseCases.agency, aiUseCases.useCaseName);

  return results.map(transformUseCase);
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

  const useCase = transformUseCase(results[0]);

  // Fetch details
  const detailsResults = await db
    .select()
    .from(aiUseCaseDetails)
    .where(eq(aiUseCaseDetails.useCaseId, useCase.id))
    .limit(1);

  if (detailsResults.length > 0) {
    const details = detailsResults[0];
    return {
      ...useCase,
      details: {
        ...details,
        use_case_id: details.useCaseId,
        development_approach: details.developmentApproach,
        procurement_instrument: details.procurementInstrument,
        supports_hisp: details.supportsHisp,
        which_hisp: details.whichHisp,
        which_public_service: details.whichPublicService,
        disseminates_to_public: details.disseminatesToPublic,
        involves_pii: details.involvesPii,
        privacy_assessed: details.privacyAssessed,
        has_data_catalog: details.hasDataCatalog,
        agency_owned_data: details.agencyOwnedData,
        data_documentation: details.dataDocumentation,
        demographic_variables: details.demographicVariables,
        has_custom_code: details.hasCustomCode,
        has_code_access: details.hasCodeAccess,
        code_link: details.codeLink,
        has_ato: details.hasAto,
        system_name: details.systemName,
        wait_time_dev_tools: details.waitTimeDevTools,
        centralized_intake: details.centralizedIntake,
        has_compute_process: details.hasComputeProcess,
        timely_communication: details.timelyCommunication,
        infrastructure_reuse: details.infrastructureReuse,
        internal_review: details.internalReview,
        requested_extension: details.requestedExtension,
        impact_assessment: details.impactAssessment,
        operational_testing: details.operationalTesting,
        key_risks: details.keyRisks,
        independent_evaluation: details.independentEvaluation,
        performance_monitoring: details.performanceMonitoring,
        autonomous_decision: details.autonomousDecision,
        public_notice: details.publicNotice,
        influences_decisions: details.influencesDecisions,
        disparity_mitigation: details.disparityMitigation,
        stakeholder_feedback: details.stakeholderFeedback,
        fallback_process: details.fallbackProcess,
        opt_out_mechanism: details.optOutMechanism,
        info_quality_compliance: details.infoQualityCompliance,
        search_text: details.searchText,
      },
    };
  }

  return { ...useCase };
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
  let query = db
    .select({
      agency: aiUseCases.agency,
      total_count: sql<number>`count(*)::int`,
      genai_count: sql<number>`sum(case when ${aiUseCases.genaiFlag} then 1 else 0 end)::int`,
      llm_count: sql<number>`sum(case when ${aiUseCases.hasLlm} then 1 else 0 end)::int`,
      chatbot_count: sql<number>`sum(case when ${aiUseCases.hasChatbot} then 1 else 0 end)::int`,
      classic_ml_count: sql<number>`sum(case when ${aiUseCases.hasClassicMl} then 1 else 0 end)::int`,
    })
    .from(aiUseCases);

  if (agency) {
    query = query.where(eq(aiUseCases.agency, agency));
  }

  const results = await query
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
      product_id: useCaseFedRampMatches.productId,
      provider_name: useCaseFedRampMatches.providerName,
      product_name: useCaseFedRampMatches.productName,
      confidence: useCaseFedRampMatches.confidence,
      match_reason: useCaseFedRampMatches.matchReason,
    })
    .from(useCaseFedRampMatches)
    .where(eq(useCaseFedRampMatches.useCaseId, useCaseId))
    .orderBy(
      sql`case ${useCaseFedRampMatches.confidence} when 'high' then 1 when 'medium' then 2 when 'low' then 3 end`,
      useCaseFedRampMatches.providerName
    );

  return results.map(r => ({
    product_id: r.product_id,
    provider_name: r.provider_name,
    product_name: r.product_name,
    confidence: r.confidence,
    match_reason: r.match_reason,
  }));
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

  return results.map(transformUseCase);
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
