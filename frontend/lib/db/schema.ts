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

export const orgLevelEnum = pgEnum('org_level', [
  'department',    // Cabinet department (e.g., Department of Defense)
  'independent',   // Independent agency (e.g., EPA, NASA)
  'sub_agency',    // Sub-agency/bureau (e.g., FBI under DOJ)
  'office',        // Office/division
  'component',     // Lower-level unit
]);

// ========================================
// FEDERAL ORGANIZATIONS HIERARCHY
// ========================================

/**
 * Federal Organizations Hierarchy Table
 * Self-referential table for storing the federal agency hierarchy
 * Based on SAM.gov Federal Hierarchy structure
 */
export const federalOrganizations = pgTable(
  'federal_organizations',
  {
    id: serial('id').primaryKey(),

    // Core identifiers
    name: text('name').notNull(),
    shortName: varchar('short_name', { length: 100 }),
    abbreviation: varchar('abbreviation', { length: 20 }),
    slug: text('slug').unique().notNull(),

    // Hierarchy (self-referential - parentId references this table's id)
    parentId: integer('parent_id'),
    level: orgLevelEnum('level').notNull(),
    hierarchyPath: text('hierarchy_path'), // Materialized path: "/1/5/23/"
    depth: integer('depth').notNull().default(0),

    // SAM.gov / GSA identifiers
    samOrgId: varchar('sam_org_id', { length: 50 }),
    cgacCode: varchar('cgac_code', { length: 10 }),
    agencyCode: varchar('agency_code', { length: 20 }),

    // Classification
    isCfoActAgency: boolean('is_cfo_act_agency').notNull().default(false),
    isCabinetDepartment: boolean('is_cabinet_department').notNull().default(false),

    // Display settings
    isActive: boolean('is_active').notNull().default(true),
    displayOrder: integer('display_order').default(0),

    // Metadata
    description: text('description'),
    website: text('website'),
    createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [
    index('idx_fed_org_parent').on(table.parentId),
    index('idx_fed_org_level').on(table.level),
    index('idx_fed_org_abbreviation').on(table.abbreviation),
    index('idx_fed_org_hierarchy_path').on(table.hierarchyPath),
    index('idx_fed_org_cfo_act').on(table.isCfoActAgency),
    uniqueIndex('idx_fed_org_slug').on(table.slug),
  ]
);

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

    // Federal Organization Hierarchy Links
    organizationId: integer('organization_id'),
    bureauOrganizationId: integer('bureau_organization_id'),

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
    index('idx_use_case_org').on(table.organizationId),
    index('idx_use_case_bureau_org').on(table.bureauOrganizationId),
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
    productId: varchar('product_id', { length: 255 }).notNull(),
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

    // Federal Organization Hierarchy Link
    organizationId: integer('organization_id'),

    // Metadata
    analyzedAt: timestamp('analyzed_at').defaultNow().notNull(),
    slug: text('slug').unique().notNull(),
  },
  (table) => [
    index('idx_agency_name').on(table.agencyName),
    index('idx_agency_category').on(table.agencyCategory),
    index('idx_agency_org').on(table.organizationId),
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

export type FederalOrganization = typeof federalOrganizations.$inferSelect;
export type NewFederalOrganization = typeof federalOrganizations.$inferInsert;

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

// ========================================
// AGENCY AI PROFILES & TOOLS (NEW)
// ========================================

/**
 * Enums for agency AI tool types and deployment status
 */
export const productTypeEnum = pgEnum('product_type', [
  'staff_chatbot',
  'coding_assistant',
  'document_automation',
  'none_identified',
]);

export const deploymentStatusEnum = pgEnum('deployment_status', [
  'all_staff',
  'pilot_or_limited',
  'no_public_internal_assistant',
]);

/**
 * Agency AI Profiles - One row per agency
 * Links to federal_organizations for hierarchy support
 */
export const agencyAiProfiles = pgTable(
  'agency_ai_profiles',
  {
    id: serial('id').primaryKey(),

    // Agency identification
    agencyName: text('agency_name').notNull(),
    abbreviation: varchar('abbreviation', { length: 20 }),
    slug: text('slug').unique().notNull(),

    // Hierarchy link
    organizationId: integer('organization_id'),
    departmentLevelName: text('department_level_name'),
    parentAbbreviation: varchar('parent_abbreviation', { length: 20 }),

    // Overall deployment status
    deploymentStatus: deploymentStatusEnum('deployment_status').default('no_public_internal_assistant'),

    // Summary flags (derived from tools for fast queries)
    hasStaffChatbot: boolean('has_staff_chatbot').notNull().default(false),
    hasCodingAssistant: boolean('has_coding_assistant').notNull().default(false),
    hasDocumentAutomation: boolean('has_document_automation').notNull().default(false),
    toolCount: integer('tool_count').notNull().default(0),

    // Metadata
    createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [
    index('idx_agency_profile_org').on(table.organizationId),
    index('idx_agency_profile_dept').on(table.departmentLevelName),
    index('idx_agency_profile_parent').on(table.parentAbbreviation),
    index('idx_agency_profile_chatbot').on(table.hasStaffChatbot),
    index('idx_agency_profile_coding').on(table.hasCodingAssistant),
    uniqueIndex('idx_agency_profile_slug').on(table.slug),
  ]
);

/**
 * Agency AI Tools - One row per tool
 * Multiple tools can belong to one agency profile
 */
export const agencyAiTools = pgTable(
  'agency_ai_tools',
  {
    id: serial('id').primaryKey(),

    // Link to agency profile
    agencyProfileId: integer('agency_profile_id')
      .notNull()
      .references(() => agencyAiProfiles.id, { onDelete: 'cascade' }),

    // Tool identification
    productName: text('product_name').notNull(),
    productType: productTypeEnum('product_type').notNull(),
    slug: text('slug').unique().notNull(),

    // Deployment details
    availableToAllStaff: text('available_to_all_staff'), // yes/no/subset
    isPilotOrLimited: boolean('is_pilot_or_limited').default(false),

    // Coding assistant flag (yes/no/partial)
    codingAssistantFlag: varchar('coding_assistant_flag', { length: 20 }),

    // Data sensitivity
    internalOrSensitiveData: text('internal_or_sensitive_data'),

    // Citation/source information
    citationChicago: text('citation_chicago'),
    citationAccessedDate: text('citation_accessed_date'),
    citationUrl: text('citation_url'),

    // Metadata
    createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [
    index('idx_agency_tool_profile').on(table.agencyProfileId),
    index('idx_agency_tool_type').on(table.productType),
    index('idx_agency_tool_availability').on(table.availableToAllStaff),
    uniqueIndex('idx_agency_tool_slug').on(table.slug),
  ]
);

// Type exports for new tables
export type AgencyAiProfile = typeof agencyAiProfiles.$inferSelect;
export type NewAgencyAiProfile = typeof agencyAiProfiles.$inferInsert;

export type AgencyAiTool = typeof agencyAiTools.$inferSelect;
export type NewAgencyAiTool = typeof agencyAiTools.$inferInsert;

export type ProductType = 'staff_chatbot' | 'coding_assistant' | 'document_automation' | 'none_identified';
export type DeploymentStatus = 'all_staff' | 'pilot_or_limited' | 'no_public_internal_assistant';

// ========================================
// AI INCIDENT TABLES
// ========================================

/**
 * AI Incidents table
 * Tracks AI-related incidents from the AI Incident Database
 */
export const incidents = pgTable(
  'incidents',
  {
    id: serial('id').primaryKey(),
    incidentId: integer('incident_id').notNull().unique(),
    title: text('title').notNull(),
    description: text('description'),
    date: text('date'),
    deployers: jsonb('deployers').$type<string[]>(),
    developers: jsonb('developers').$type<string[]>(),
    harmedParties: jsonb('harmed_parties').$type<string[]>(),
    reportCount: integer('report_count').default(0),
    createdAt: timestamp('created_at').defaultNow().notNull(),
  },
  (table) => [
    index('idx_incidents_incident_id').on(table.incidentId),
    index('idx_incidents_date').on(table.date),
  ]
);

/**
 * Entities involved in incidents
 */
export const entities = pgTable(
  'entities',
  {
    id: serial('id').primaryKey(),
    entityId: text('entity_id').notNull().unique(),
    name: text('name').notNull(),
  },
  (table) => [
    uniqueIndex('idx_entities_entity_id').on(table.entityId),
  ]
);

/**
 * Junction table for incident-entity relationships
 */
export const incidentEntities = pgTable(
  'incident_entities',
  {
    id: serial('id').primaryKey(),
    incidentId: integer('incident_id').notNull(),
    entityId: text('entity_id').notNull(),
    role: text('role').notNull(), // 'deployer', 'developer', 'harmed'
  },
  (table) => [
    index('idx_incident_entities_incident').on(table.incidentId),
    index('idx_incident_entities_entity').on(table.entityId),
  ]
);

/**
 * Security data for incidents
 */
export const incidentSecurity = pgTable(
  'incident_security',
  {
    id: serial('id').primaryKey(),
    incidentId: integer('incident_id').notNull().unique(),
    securityDataLeakPresence: text('security_data_leak_presence'),
    securityDataLeakModes: jsonb('security_data_leak_modes').$type<string[]>(),
    securityDataTypes: jsonb('security_data_types').$type<string[]>(),
    securityEnvironmentType: text('security_environment_type'),
    securityExpectationLevel: text('security_expectation_level'),
    regulatedContextFlag: boolean('regulated_context_flag'),
    regulatoryRegimes: jsonb('regulatory_regimes').$type<string[]>(),
    cyberAttackFlag: text('cyber_attack_flag'),
    attackerIntent: jsonb('attacker_intent').$type<string[]>(),
    aiAttackType: jsonb('ai_attack_type').$type<string[]>(),
    majorProductFlag: text('major_product_flag'),
    deploymentStatus: text('deployment_status'),
    userBaseSizeBucket: text('user_base_size_bucket'),
    recordsExposedBucket: text('records_exposed_bucket'),
    leakDuration: text('leak_duration'),
    downstreamConsequences: jsonb('downstream_consequences').$type<string[]>(),
    evidenceTypes: jsonb('evidence_types').$type<string[]>(),
    securityLabelConfidence: text('security_label_confidence'),
    llmOrChatbotInvolved: boolean('llm_or_chatbot_involved'),
    llmConnectorTooling: jsonb('llm_connector_tooling').$type<string[]>(),
    llmDataSourceOfLeak: jsonb('llm_data_source_of_leak').$type<string[]>(),
  },
  (table) => [
    index('idx_incident_security_incident').on(table.incidentId),
    index('idx_incident_security_llm').on(table.llmOrChatbotInvolved),
  ]
);

/**
 * Cross-domain matches: incidents to products
 */
export const incidentProductMatches = pgTable(
  'incident_product_matches',
  {
    id: serial('id').primaryKey(),
    incidentId: integer('incident_id').notNull(),
    productFedrampId: text('product_fedramp_id').notNull(),
    matchType: text('match_type').notNull(),
    confidence: text('confidence').notNull(),
    matchReason: text('match_reason'),
    matchedEntity: text('matched_entity'),
    similarityScore: integer('similarity_score'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
  },
  (table) => [
    index('idx_incident_product_incident').on(table.incidentId),
    index('idx_incident_product_product').on(table.productFedrampId),
  ]
);

/**
 * Cross-domain matches: incidents to use cases
 */
export const incidentUseCaseMatches = pgTable(
  'incident_use_case_matches',
  {
    id: serial('id').primaryKey(),
    incidentId: integer('incident_id').notNull(),
    useCaseId: integer('use_case_id').notNull(),
    matchType: text('match_type').notNull(),
    confidence: text('confidence').notNull(),
    matchReason: text('match_reason'),
    matchedEntity: text('matched_entity'),
    similarityScore: integer('similarity_score'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
  },
  (table) => [
    index('idx_incident_use_case_incident').on(table.incidentId),
    index('idx_incident_use_case_use_case').on(table.useCaseId),
  ]
);

// Incident type exports
export type Incident = typeof incidents.$inferSelect;
export type NewIncident = typeof incidents.$inferInsert;

export type Entity = typeof entities.$inferSelect;
export type NewEntity = typeof entities.$inferInsert;

export type IncidentEntity = typeof incidentEntities.$inferSelect;
export type NewIncidentEntity = typeof incidentEntities.$inferInsert;

export type IncidentSecurity = typeof incidentSecurity.$inferSelect;
export type NewIncidentSecurity = typeof incidentSecurity.$inferInsert;

export type IncidentProductMatch = typeof incidentProductMatches.$inferSelect;
export type NewIncidentProductMatch = typeof incidentProductMatches.$inferInsert;

export type IncidentUseCaseMatch = typeof incidentUseCaseMatches.$inferSelect;
export type NewIncidentUseCaseMatch = typeof incidentUseCaseMatches.$inferInsert;

// ========================================
// SEMANTIC MATCHING TABLES
// ========================================

/**
 * Semantic matches table
 * Pre-computed similarity matches using vector embeddings
 */
export const semanticMatches = pgTable(
  'semantic_matches',
  {
    id: serial('id').primaryKey(),
    sourceType: text('source_type').notNull(), // 'incident', 'use_case', 'product'
    sourceId: text('source_id').notNull(),
    targetType: text('target_type').notNull(), // 'incident', 'use_case', 'product'
    targetId: text('target_id').notNull(),
    similarityScore: integer('similarity_score').notNull(), // Stored as real in DB but integer here for drizzle
    matchRank: integer('match_rank'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
  },
  (table) => [
    index('idx_semantic_matches_source').on(table.sourceType, table.sourceId),
    index('idx_semantic_matches_target').on(table.targetType, table.targetId),
    index('idx_semantic_matches_score').on(table.similarityScore),
  ]
);

export type SemanticMatch = typeof semanticMatches.$inferSelect;
export type NewSemanticMatch = typeof semanticMatches.$inferInsert;

// ========================================
// HIERARCHY HELPER TYPES
// ========================================

export type OrgLevel = 'department' | 'independent' | 'sub_agency' | 'office' | 'component';

export interface FederalOrganizationWithChildren extends FederalOrganization {
  children: FederalOrganizationWithChildren[];
}

export interface HierarchyBreadcrumb {
  id: number;
  name: string;
  abbreviation: string | null;
  slug: string;
  level: OrgLevel;
}
