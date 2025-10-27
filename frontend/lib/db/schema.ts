import {
  pgTable,
  serial,
  text,
  varchar,
  boolean,
  timestamp,
  integer,
  jsonb,
  index,
  uniqueIndex,
  pgEnum,
} from 'drizzle-orm/pg-core';

// ========================================
// ENUMS
// ========================================

export const confidenceEnum = pgEnum('confidence', ['high', 'medium', 'low']);

// ========================================
// AI USE CASES TABLES
// ========================================

/**
 * Main AI use cases table - core data for all federal AI use cases
 * Optimized for fast queries and filtering
 */
export const aiUseCases = pgTable(
  'ai_use_cases',
  {
    id: serial('id').primaryKey(),
    useCaseName: text('use_case_name').notNull(),
    agency: text('agency').notNull(),
    agencyAbbreviation: text('agency_abbreviation'),
    bureau: text('bureau'),
    useCaseTopicArea: text('use_case_topic_area'),
    otherUseCaseTopicArea: text('other_use_case_topic_area'),

    // Purpose and outputs
    intendedPurpose: text('intended_purpose'),
    outputs: text('outputs'),

    // Classification
    stageOfDevelopment: text('stage_of_development'),
    isRightsSafetyImpacting: text('is_rights_safety_impacting'),
    domainCategory: text('domain_category'),

    // Dates
    dateInitiated: text('date_initiated'),
    dateImplemented: text('date_implemented'),
    dateRetired: text('date_retired'),

    // AI Type Flags (for filtering)
    hasLlm: boolean('has_llm').default(false).notNull(),
    hasGenai: boolean('has_genai').default(false).notNull(),
    hasChatbot: boolean('has_chatbot').default(false).notNull(),
    hasGpMarkers: boolean('has_gp_markers').default(false).notNull(),
    hasCodingAssistant: boolean('has_coding_assistant').default(false).notNull(),
    hasCodingAgent: boolean('has_coding_agent').default(false).notNull(),
    hasClassicMl: boolean('has_classic_ml').default(false).notNull(),
    hasRpa: boolean('has_rpa').default(false).notNull(),
    hasRules: boolean('has_rules').default(false).notNull(),

    // AI Type Categories (for badges)
    generalPurposeChatbot: boolean('general_purpose_chatbot').default(false).notNull(),
    domainChatbot: boolean('domain_chatbot').default(false).notNull(),
    codingAssistant: boolean('coding_assistant').default(false).notNull(),
    codingAgent: boolean('coding_agent').default(false).notNull(),
    genaiFlag: boolean('genai_flag').default(false).notNull(),
    aiTypeClassicMl: boolean('ai_type_classic_ml').default(false).notNull(),
    aiTypeRpaRules: boolean('ai_type_rpa_rules').default(false).notNull(),

    // Providers (stored as JSONB array)
    providersDetected: jsonb('providers_detected').$type<string[]>().default([]),

    // Commercial AI products used
    commercialAiProduct: text('commercial_ai_product'),

    // Metadata
    analyzedAt: timestamp('analyzed_at').defaultNow().notNull(),
    slug: text('slug').unique().notNull(),
  },
  (table) => [
    index('idx_use_case_agency').on(table.agency),
    index('idx_use_case_domain').on(table.domainCategory),
    index('idx_use_case_stage').on(table.stageOfDevelopment),
    index('idx_use_case_genai').on(table.genaiFlag),
    index('idx_use_case_llm').on(table.hasLlm),
    uniqueIndex('idx_use_case_slug').on(table.slug),
  ]
);

/**
 * Extended details for AI use cases
 * Contains full metadata that's less frequently queried
 */
export const aiUseCaseDetails = pgTable('ai_use_case_details', {
  useCaseId: integer('use_case_id')
    .primaryKey()
    .references(() => aiUseCases.id, { onDelete: 'cascade' }),

  // Development and procurement
  developmentApproach: text('development_approach'),
  procurementInstrument: text('procurement_instrument'),

  // High-impact service
  supportsHisp: text('supports_hisp'),
  whichHisp: text('which_hisp'),
  whichPublicService: text('which_public_service'),
  disseminatesToPublic: text('disseminates_to_public'),

  // Privacy and data
  involvesPii: text('involves_pii'),
  privacyAssessed: text('privacy_assessed'),
  hasDataCatalog: text('has_data_catalog'),
  agencyOwnedData: text('agency_owned_data'),
  dataDocumentation: text('data_documentation'),
  demographicVariables: text('demographic_variables'),

  // Code and systems
  hasCustomCode: text('has_custom_code'),
  hasCodeAccess: text('has_code_access'),
  codeLink: text('code_link'),
  hasAto: text('has_ato'),
  systemName: text('system_name'),

  // Infrastructure
  waitTimeDevTools: text('wait_time_dev_tools'),
  centralizedIntake: text('centralized_intake'),
  hasComputeProcess: text('has_compute_process'),
  timelyCommunication: text('timely_communication'),
  infrastructureReuse: text('infrastructure_reuse'),

  // Review and testing
  internalReview: text('internal_review'),
  requestedExtension: text('requested_extension'),
  impactAssessment: text('impact_assessment'),
  operationalTesting: text('operational_testing'),
  keyRisks: text('key_risks'),
  independentEvaluation: text('independent_evaluation'),

  // Monitoring and governance
  performanceMonitoring: text('performance_monitoring'),
  autonomousDecision: text('autonomous_decision'),
  publicNotice: text('public_notice'),
  influencesDecisions: text('influences_decisions'),
  disparityMitigation: text('disparity_mitigation'),
  stakeholderFeedback: text('stakeholder_feedback'),
  fallbackProcess: text('fallback_process'),
  optOutMechanism: text('opt_out_mechanism'),

  // Information quality
  infoQualityCompliance: text('info_quality_compliance'),

  // Full search text
  searchText: text('search_text'),
});

/**
 * Linking table for use cases to FedRAMP services
 * Connects use cases with their potential FedRAMP-authorized service matches
 */
export const useCaseFedRampMatches = pgTable(
  'use_case_fedramp_matches',
  {
    id: serial('id').primaryKey(),
    useCaseId: integer('use_case_id')
      .notNull()
      .references(() => aiUseCases.id, { onDelete: 'cascade' }),
    productId: text('product_id').notNull(),
    providerName: text('provider_name').notNull(),
    productName: text('product_name').notNull(),
    confidence: confidenceEnum('confidence').notNull(),
    matchReason: text('match_reason'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
  },
  (table) => [
    index('idx_use_case_fedramp_use_case').on(table.useCaseId),
    index('idx_use_case_fedramp_product').on(table.productId),
    index('idx_use_case_fedramp_confidence').on(table.confidence),
  ]
);

// ========================================
// AI SERVICE ANALYSIS TABLES
// ========================================

/**
 * AI service analysis table
 * Tracks FedRAMP services analyzed for AI capabilities
 */
export const aiServiceAnalysis = pgTable(
  'ai_service_analysis',
  {
    id: serial('id').primaryKey(),
    productId: varchar('product_id', { length: 255 }).notNull().unique(),
    productName: text('product_name').notNull(),
    providerName: text('provider_name').notNull(),
    serviceName: text('service_name').notNull(),

    // AI classification flags
    hasAi: boolean('has_ai').default(false).notNull(),
    hasGenai: boolean('has_genai').default(false).notNull(),
    hasLlm: boolean('has_llm').default(false).notNull(),

    // Analysis results
    relevantExcerpt: text('relevant_excerpt'),

    // FedRAMP metadata
    fedrampStatus: text('fedramp_status'),
    impactLevel: text('impact_level'),
    agencies: text('agencies'),
    authDate: text('auth_date'),

    // Metadata
    analyzedAt: timestamp('analyzed_at').defaultNow().notNull(),
  },
  (table) => [
    index('idx_ai_service_product').on(table.productId),
    index('idx_ai_service_provider').on(table.providerName),
    index('idx_ai_service_has_ai').on(table.hasAi),
    index('idx_ai_service_has_genai').on(table.hasGenai),
    index('idx_ai_service_has_llm').on(table.hasLlm),
  ]
);

// ========================================
// AGENCY AI USAGE TABLES
// ========================================

/**
 * Agency AI usage tracking
 * Stores information about agency AI tool adoption and policies
 */
export const agencyAiUsage = pgTable(
  'agency_ai_usage',
  {
    id: serial('id').primaryKey(),
    agencyName: text('agency_name').notNull(),
    agencyCategory: text('agency_category').notNull(),

    // LLM usage
    hasStaffLlm: text('has_staff_llm'),
    llmName: text('llm_name'),
    hasCodingAssistant: text('has_coding_assistant'),
    scope: text('scope'),

    // Solution details
    solutionType: text('solution_type'),
    nonPublicAllowed: text('non_public_allowed'),

    // Other AI tools
    otherAiPresent: text('other_ai_present'),
    toolName: text('tool_name'),
    toolPurpose: text('tool_purpose'),

    // Additional info
    notes: text('notes'),
    sources: text('sources'),

    // Metadata
    analyzedAt: timestamp('analyzed_at').defaultNow().notNull(),
    slug: text('slug').unique().notNull(),
  },
  (table) => [
    index('idx_agency_name').on(table.agencyName),
    index('idx_agency_category').on(table.agencyCategory),
    uniqueIndex('idx_agency_slug').on(table.slug),
  ]
);

/**
 * Agency to FedRAMP service matches
 * Links agencies with FedRAMP services they might be using
 */
export const agencyServiceMatches = pgTable(
  'agency_service_matches',
  {
    id: serial('id').primaryKey(),
    agencyId: integer('agency_id')
      .notNull()
      .references(() => agencyAiUsage.id, { onDelete: 'cascade' }),
    productId: text('product_id').notNull(),
    providerName: text('provider_name').notNull(),
    productName: text('product_name').notNull(),
    confidence: confidenceEnum('confidence').notNull(),
    matchReason: text('match_reason'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
  },
  (table) => [
    index('idx_agency_service_agency').on(table.agencyId),
    index('idx_agency_service_product').on(table.productId),
    index('idx_agency_service_confidence').on(table.confidence),
  ]
);

// ========================================
// TYPE EXPORTS
// ========================================

export type AIUseCase = typeof aiUseCases.$inferSelect;
export type NewAIUseCase = typeof aiUseCases.$inferInsert;

export type AIUseCaseDetails = typeof aiUseCaseDetails.$inferSelect;
export type NewAIUseCaseDetails = typeof aiUseCaseDetails.$inferInsert;

export type UseCaseFedRAMPMatch = typeof useCaseFedRampMatches.$inferSelect;
export type NewUseCaseFedRAMPMatch = typeof useCaseFedRampMatches.$inferInsert;

export type AIService = typeof aiServiceAnalysis.$inferSelect;
export type NewAIService = typeof aiServiceAnalysis.$inferInsert;

export type AgencyAIUsage = typeof agencyAiUsage.$inferSelect;
export type NewAgencyAIUsage = typeof agencyAiUsage.$inferInsert;

export type AgencyServiceMatch = typeof agencyServiceMatches.$inferSelect;
export type NewAgencyServiceMatch = typeof agencyServiceMatches.$inferInsert;
