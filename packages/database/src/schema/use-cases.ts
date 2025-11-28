// packages/database/src/schema/use-cases.ts
import { serial, text, boolean, timestamp, pgTable, integer } from "drizzle-orm/pg-core";
import { products } from "./products";

// AI Use Cases Main Table
export const aiUseCases = pgTable("ai_use_cases", {
  id: serial("id").primaryKey(),
  useCaseName: text("use_case_name").notNull(),
  agency: text("agency").notNull(),
  agencyAbbreviation: text("agency_abbreviation"),
  bureau: text("bureau"),
  useCaseTopicArea: text("use_case_topic_area"),
  otherUseCaseTopicArea: text("other_use_case_topic_area"),

  // Purpose and outputs
  intendedPurpose: text("intended_purpose"),
  outputs: text("outputs"),

  // Classification
  stageOfDevelopment: text("stage_of_development"),
  isRightsSafetyImpacting: text("is_rights_safety_impacting"),
  domainCategory: text("domain_category"),

  // Dates
  dateInitiated: text("date_initiated"),
  dateImplemented: text("date_implemented"),
  dateRetired: text("date_retired"),

  // AI Type Flags
  hasLlm: boolean("has_llm").notNull().default(false),
  hasGenai: boolean("has_genai").notNull().default(false),
  hasChatbot: boolean("has_chatbot").notNull().default(false),
  hasGpMarkers: boolean("has_gp_markers").notNull().default(false),
  hasCodingAssistant: boolean("has_coding_assistant").notNull().default(false),
  hasCodingAgent: boolean("has_coding_agent").notNull().default(false),
  hasClassicMl: boolean("has_classic_ml").notNull().default(false),
  hasRpa: boolean("has_rpa").notNull().default(false),
  hasRules: boolean("has_rules").notNull().default(false),

  // AI Type Categories (for badges)
  generalPurposeChatbot: boolean("general_purpose_chatbot").notNull().default(false),
  domainChatbot: boolean("domain_chatbot").notNull().default(false),
  codingAssistant: boolean("coding_assistant").notNull().default(false),
  codingAgent: boolean("coding_agent").notNull().default(false),
  genaiFlag: boolean("genai_flag").notNull().default(false),
  aiTypeClassicMl: boolean("ai_type_classic_ml").notNull().default(false),
  aiTypeRpaRules: boolean("ai_type_rpa_rules").notNull().default(false),

  // Providers (stored as text, could be JSON)
  providersDetected: text("providers_detected"),

  // Commercial AI products
  commercialAiProduct: text("commercial_ai_product"),

  // Metadata
  analyzedAt: timestamp("analyzed_at", { withTimezone: true }).notNull().defaultNow(),
  slug: text("slug").notNull().unique(),
});

// AI Use Case Details Table (extended metadata)
export const aiUseCaseDetails = pgTable("ai_use_case_details", {
  useCaseId: integer("use_case_id").primaryKey().references(() => aiUseCases.id),

  // Development and procurement
  developmentApproach: text("development_approach"),
  procurementInstrument: text("procurement_instrument"),

  // High-impact service
  supportsHisp: text("supports_hisp"),
  whichHisp: text("which_hisp"),
  whichPublicService: text("which_public_service"),
  disseminatesToPublic: text("disseminates_to_public"),

  // Privacy and data
  involvesPii: text("involves_pii"),
  privacyAssessed: text("privacy_assessed"),
  hasDataCatalog: text("has_data_catalog"),
  agencyOwnedData: text("agency_owned_data"),
  dataDocumentation: text("data_documentation"),
  demographicVariables: text("demographic_variables"),

  // Code and systems
  hasCustomCode: text("has_custom_code"),
  hasCodeAccess: text("has_code_access"),
  codeLink: text("code_link"),
  hasAto: text("has_ato"),
  systemName: text("system_name"),

  // Infrastructure
  waitTimeDevTools: text("wait_time_dev_tools"),
  centralizedIntake: text("centralized_intake"),
  hasComputeProcess: text("has_compute_process"),
  timelyCommunication: text("timely_communication"),
  infrastructureReuse: text("infrastructure_reuse"),

  // Review and testing
  internalReview: text("internal_review"),
  requestedExtension: text("requested_extension"),
  impactAssessment: text("impact_assessment"),
  operationalTesting: text("operational_testing"),
  keyRisks: text("key_risks"),
  independentEvaluation: text("independent_evaluation"),

  // Monitoring and governance
  performanceMonitoring: text("performance_monitoring"),
  autonomousDecision: text("autonomous_decision"),
  publicNotice: text("public_notice"),
  influencesDecisions: text("influences_decisions"),
  disparityMitigation: text("disparity_mitigation"),
  stakeholderFeedback: text("stakeholder_feedback"),
  fallbackProcess: text("fallback_process"),
  optOutMechanism: text("opt_out_mechanism"),

  // Information quality
  infoQualityCompliance: text("info_quality_compliance"),

  // Full search text
  searchText: text("search_text"),
});

// Use Case to FedRAMP Matches Table
export const useCaseFedrampMatches = pgTable("use_case_fedramp_matches", {
  id: serial("id").primaryKey(),
  useCaseId: integer("use_case_id").notNull().references(() => aiUseCases.id),
  productId: text("product_id").notNull().references(() => products.fedrampId),
  providerName: text("provider_name").notNull(),
  productName: text("product_name").notNull(),
  confidence: text("confidence").notNull(), // 'high', 'medium', or 'low'
  matchReason: text("match_reason"),
});

export type AIUseCaseRecord = typeof aiUseCases.$inferSelect;
export type NewAIUseCaseRecord = typeof aiUseCases.$inferInsert;
export type AIUseCaseDetailRecord = typeof aiUseCaseDetails.$inferSelect;
export type NewAIUseCaseDetailRecord = typeof aiUseCaseDetails.$inferInsert;
export type UseCaseFedrampMatchRecord = typeof useCaseFedrampMatches.$inferSelect;
export type NewUseCaseFedrampMatchRecord = typeof useCaseFedrampMatches.$inferInsert;
