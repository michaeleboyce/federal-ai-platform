"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.taxa = exports.classifications = exports.incidentSecurity = exports.securityConfidenceEnum = exports.majorProductFlagEnum = exports.cyberAttackFlagEnum = exports.securityExpectationEnum = exports.dataLeakPresenceEnum = void 0;
// packages/database/src/schema/incident-security.ts
const pg_core_1 = require("drizzle-orm/pg-core");
// Enums for security classifications
exports.dataLeakPresenceEnum = (0, pg_core_1.pgEnum)("data_leak_presence", ["none", "suspected", "confirmed"]);
exports.securityExpectationEnum = (0, pg_core_1.pgEnum)("security_expectation", ["low", "medium", "high"]);
exports.cyberAttackFlagEnum = (0, pg_core_1.pgEnum)("cyber_attack_flag", ["none", "suspected_attack", "confirmed_attack"]);
exports.majorProductFlagEnum = (0, pg_core_1.pgEnum)("major_product_flag", ["yes", "no", "unknown"]);
exports.securityConfidenceEnum = (0, pg_core_1.pgEnum)("security_confidence", ["low", "medium", "high"]);
// Security enrichment table
exports.incidentSecurity = (0, pg_core_1.pgTable)("incident_security", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    incidentId: (0, pg_core_1.integer)("incident_id").notNull().unique(),
    // Data leak information
    securityDataLeakPresence: (0, pg_core_1.text)("security_data_leak_presence"), // none|suspected|confirmed
    securityDataLeakModes: (0, pg_core_1.jsonb)("security_data_leak_modes").$type(),
    securityDataTypes: (0, pg_core_1.jsonb)("security_data_types").$type(),
    // Security environment
    securityEnvironmentType: (0, pg_core_1.text)("security_environment_type"),
    securityExpectationLevel: (0, pg_core_1.text)("security_expectation_level"), // low|medium|high
    regulatedContextFlag: (0, pg_core_1.boolean)("regulated_context_flag"),
    regulatoryRegimes: (0, pg_core_1.jsonb)("regulatory_regimes").$type(), // GDPR, HIPAA, etc.
    // Attack information
    cyberAttackFlag: (0, pg_core_1.text)("cyber_attack_flag"), // none|suspected_attack|confirmed_attack
    attackerIntent: (0, pg_core_1.jsonb)("attacker_intent").$type(),
    aiAttackType: (0, pg_core_1.jsonb)("ai_attack_type").$type(), // prompt_injection, jailbreak, etc.
    // Deployment details
    majorProductFlag: (0, pg_core_1.text)("major_product_flag"), // yes|no|unknown
    deploymentStatus: (0, pg_core_1.text)("deployment_status"),
    userBaseSizeBucket: (0, pg_core_1.text)("user_base_size_bucket"),
    recordsExposedBucket: (0, pg_core_1.text)("records_exposed_bucket"), // 1-10, 11-100, etc.
    leakDuration: (0, pg_core_1.text)("leak_duration"),
    // Consequences
    downstreamConsequences: (0, pg_core_1.jsonb)("downstream_consequences").$type(),
    evidenceTypes: (0, pg_core_1.jsonb)("evidence_types").$type(),
    securityLabelConfidence: (0, pg_core_1.text)("security_label_confidence"), // low|medium|high
    // LLM specific
    llmOrChatbotInvolved: (0, pg_core_1.boolean)("llm_or_chatbot_involved"),
    llmConnectorTooling: (0, pg_core_1.jsonb)("llm_connector_tooling").$type(),
    llmDataSourceOfLeak: (0, pg_core_1.jsonb)("llm_data_source_of_leak").$type(),
});
// Classifications table (CSET, GMF, MIT taxonomies)
exports.classifications = (0, pg_core_1.pgTable)("classifications", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    incidentId: (0, pg_core_1.integer)("incident_id").notNull(),
    namespace: (0, pg_core_1.text)("namespace").notNull(), // CSETv1, GMF, MIT
    published: (0, pg_core_1.boolean)("published"),
    incidentNumber: (0, pg_core_1.integer)("incident_number"),
    // CSET fields
    harmDomain: (0, pg_core_1.text)("harm_domain"),
    tangibleHarm: (0, pg_core_1.text)("tangible_harm"),
    aiSystem: (0, pg_core_1.text)("ai_system"),
    dateOfIncidentYear: (0, pg_core_1.integer)("date_of_incident_year"),
    dateOfIncidentMonth: (0, pg_core_1.integer)("date_of_incident_month"),
    dateOfIncidentDay: (0, pg_core_1.integer)("date_of_incident_day"),
    locationCountry: (0, pg_core_1.text)("location_country"),
    locationRegion: (0, pg_core_1.text)("location_region"),
    sectorOfDeployment: (0, pg_core_1.text)("sector_of_deployment"),
    publicSectorDeployment: (0, pg_core_1.text)("public_sector_deployment"),
    intentionalHarm: (0, pg_core_1.text)("intentional_harm"),
    aiTask: (0, pg_core_1.text)("ai_task"),
});
// Taxa (taxonomy definitions)
exports.taxa = (0, pg_core_1.pgTable)("taxa", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    namespace: (0, pg_core_1.text)("namespace").notNull(),
    fieldName: (0, pg_core_1.text)("field_name").notNull(),
    shortName: (0, pg_core_1.text)("short_name"),
    longName: (0, pg_core_1.text)("long_name"),
    longDescription: (0, pg_core_1.text)("long_description"),
});
//# sourceMappingURL=incident-security.js.map