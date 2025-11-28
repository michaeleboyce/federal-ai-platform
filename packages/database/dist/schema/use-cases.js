"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.useCaseFedrampMatches = exports.aiUseCaseDetails = exports.aiUseCases = void 0;
// packages/database/src/schema/use-cases.ts
const pg_core_1 = require("drizzle-orm/pg-core");
const products_1 = require("./products");
// AI Use Cases Main Table
exports.aiUseCases = (0, pg_core_1.pgTable)("ai_use_cases", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    useCaseName: (0, pg_core_1.text)("use_case_name").notNull(),
    agency: (0, pg_core_1.text)("agency").notNull(),
    agencyAbbreviation: (0, pg_core_1.text)("agency_abbreviation"),
    bureau: (0, pg_core_1.text)("bureau"),
    useCaseTopicArea: (0, pg_core_1.text)("use_case_topic_area"),
    otherUseCaseTopicArea: (0, pg_core_1.text)("other_use_case_topic_area"),
    // Purpose and outputs
    intendedPurpose: (0, pg_core_1.text)("intended_purpose"),
    outputs: (0, pg_core_1.text)("outputs"),
    // Classification
    stageOfDevelopment: (0, pg_core_1.text)("stage_of_development"),
    isRightsSafetyImpacting: (0, pg_core_1.text)("is_rights_safety_impacting"),
    domainCategory: (0, pg_core_1.text)("domain_category"),
    // Dates
    dateInitiated: (0, pg_core_1.text)("date_initiated"),
    dateImplemented: (0, pg_core_1.text)("date_implemented"),
    dateRetired: (0, pg_core_1.text)("date_retired"),
    // AI Type Flags
    hasLlm: (0, pg_core_1.boolean)("has_llm").notNull().default(false),
    hasGenai: (0, pg_core_1.boolean)("has_genai").notNull().default(false),
    hasChatbot: (0, pg_core_1.boolean)("has_chatbot").notNull().default(false),
    hasGpMarkers: (0, pg_core_1.boolean)("has_gp_markers").notNull().default(false),
    hasCodingAssistant: (0, pg_core_1.boolean)("has_coding_assistant").notNull().default(false),
    hasCodingAgent: (0, pg_core_1.boolean)("has_coding_agent").notNull().default(false),
    hasClassicMl: (0, pg_core_1.boolean)("has_classic_ml").notNull().default(false),
    hasRpa: (0, pg_core_1.boolean)("has_rpa").notNull().default(false),
    hasRules: (0, pg_core_1.boolean)("has_rules").notNull().default(false),
    // AI Type Categories (for badges)
    generalPurposeChatbot: (0, pg_core_1.boolean)("general_purpose_chatbot").notNull().default(false),
    domainChatbot: (0, pg_core_1.boolean)("domain_chatbot").notNull().default(false),
    codingAssistant: (0, pg_core_1.boolean)("coding_assistant").notNull().default(false),
    codingAgent: (0, pg_core_1.boolean)("coding_agent").notNull().default(false),
    genaiFlag: (0, pg_core_1.boolean)("genai_flag").notNull().default(false),
    aiTypeClassicMl: (0, pg_core_1.boolean)("ai_type_classic_ml").notNull().default(false),
    aiTypeRpaRules: (0, pg_core_1.boolean)("ai_type_rpa_rules").notNull().default(false),
    // Providers (stored as text, could be JSON)
    providersDetected: (0, pg_core_1.text)("providers_detected"),
    // Commercial AI products
    commercialAiProduct: (0, pg_core_1.text)("commercial_ai_product"),
    // Metadata
    analyzedAt: (0, pg_core_1.timestamp)("analyzed_at", { withTimezone: true }).notNull().defaultNow(),
    slug: (0, pg_core_1.text)("slug").notNull().unique(),
});
// AI Use Case Details Table (extended metadata)
exports.aiUseCaseDetails = (0, pg_core_1.pgTable)("ai_use_case_details", {
    useCaseId: (0, pg_core_1.integer)("use_case_id").primaryKey().references(() => exports.aiUseCases.id),
    // Development and procurement
    developmentApproach: (0, pg_core_1.text)("development_approach"),
    procurementInstrument: (0, pg_core_1.text)("procurement_instrument"),
    // High-impact service
    supportsHisp: (0, pg_core_1.text)("supports_hisp"),
    whichHisp: (0, pg_core_1.text)("which_hisp"),
    whichPublicService: (0, pg_core_1.text)("which_public_service"),
    disseminatesToPublic: (0, pg_core_1.text)("disseminates_to_public"),
    // Privacy and data
    involvesPii: (0, pg_core_1.text)("involves_pii"),
    privacyAssessed: (0, pg_core_1.text)("privacy_assessed"),
    hasDataCatalog: (0, pg_core_1.text)("has_data_catalog"),
    agencyOwnedData: (0, pg_core_1.text)("agency_owned_data"),
    dataDocumentation: (0, pg_core_1.text)("data_documentation"),
    demographicVariables: (0, pg_core_1.text)("demographic_variables"),
    // Code and systems
    hasCustomCode: (0, pg_core_1.text)("has_custom_code"),
    hasCodeAccess: (0, pg_core_1.text)("has_code_access"),
    codeLink: (0, pg_core_1.text)("code_link"),
    hasAto: (0, pg_core_1.text)("has_ato"),
    systemName: (0, pg_core_1.text)("system_name"),
    // Infrastructure
    waitTimeDevTools: (0, pg_core_1.text)("wait_time_dev_tools"),
    centralizedIntake: (0, pg_core_1.text)("centralized_intake"),
    hasComputeProcess: (0, pg_core_1.text)("has_compute_process"),
    timelyCommunication: (0, pg_core_1.text)("timely_communication"),
    infrastructureReuse: (0, pg_core_1.text)("infrastructure_reuse"),
    // Review and testing
    internalReview: (0, pg_core_1.text)("internal_review"),
    requestedExtension: (0, pg_core_1.text)("requested_extension"),
    impactAssessment: (0, pg_core_1.text)("impact_assessment"),
    operationalTesting: (0, pg_core_1.text)("operational_testing"),
    keyRisks: (0, pg_core_1.text)("key_risks"),
    independentEvaluation: (0, pg_core_1.text)("independent_evaluation"),
    // Monitoring and governance
    performanceMonitoring: (0, pg_core_1.text)("performance_monitoring"),
    autonomousDecision: (0, pg_core_1.text)("autonomous_decision"),
    publicNotice: (0, pg_core_1.text)("public_notice"),
    influencesDecisions: (0, pg_core_1.text)("influences_decisions"),
    disparityMitigation: (0, pg_core_1.text)("disparity_mitigation"),
    stakeholderFeedback: (0, pg_core_1.text)("stakeholder_feedback"),
    fallbackProcess: (0, pg_core_1.text)("fallback_process"),
    optOutMechanism: (0, pg_core_1.text)("opt_out_mechanism"),
    // Information quality
    infoQualityCompliance: (0, pg_core_1.text)("info_quality_compliance"),
    // Full search text
    searchText: (0, pg_core_1.text)("search_text"),
});
// Use Case to FedRAMP Matches Table
exports.useCaseFedrampMatches = (0, pg_core_1.pgTable)("use_case_fedramp_matches", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    useCaseId: (0, pg_core_1.integer)("use_case_id").notNull().references(() => exports.aiUseCases.id),
    productId: (0, pg_core_1.text)("product_id").notNull().references(() => products_1.products.fedrampId),
    providerName: (0, pg_core_1.text)("provider_name").notNull(),
    productName: (0, pg_core_1.text)("product_name").notNull(),
    confidence: (0, pg_core_1.text)("confidence").notNull(), // 'high', 'medium', or 'low'
    matchReason: (0, pg_core_1.text)("match_reason"),
});
//# sourceMappingURL=use-cases.js.map