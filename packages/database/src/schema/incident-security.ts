// packages/database/src/schema/incident-security.ts
import { serial, text, integer, boolean, pgTable, pgEnum, jsonb } from "drizzle-orm/pg-core";

// Enums for security classifications
export const dataLeakPresenceEnum = pgEnum("data_leak_presence", ["none", "suspected", "confirmed"]);
export const securityExpectationEnum = pgEnum("security_expectation", ["low", "medium", "high"]);
export const cyberAttackFlagEnum = pgEnum("cyber_attack_flag", ["none", "suspected_attack", "confirmed_attack"]);
export const majorProductFlagEnum = pgEnum("major_product_flag", ["yes", "no", "unknown"]);
export const securityConfidenceEnum = pgEnum("security_confidence", ["low", "medium", "high"]);

// Security enrichment table
export const incidentSecurity = pgTable("incident_security", {
  id: serial("id").primaryKey(),
  incidentId: integer("incident_id").notNull().unique(),

  // Data leak information
  securityDataLeakPresence: text("security_data_leak_presence"), // none|suspected|confirmed
  securityDataLeakModes: jsonb("security_data_leak_modes").$type<string[]>(),
  securityDataTypes: jsonb("security_data_types").$type<string[]>(),

  // Security environment
  securityEnvironmentType: text("security_environment_type"),
  securityExpectationLevel: text("security_expectation_level"), // low|medium|high
  regulatedContextFlag: boolean("regulated_context_flag"),
  regulatoryRegimes: jsonb("regulatory_regimes").$type<string[]>(), // GDPR, HIPAA, etc.

  // Attack information
  cyberAttackFlag: text("cyber_attack_flag"), // none|suspected_attack|confirmed_attack
  attackerIntent: jsonb("attacker_intent").$type<string[]>(),
  aiAttackType: jsonb("ai_attack_type").$type<string[]>(), // prompt_injection, jailbreak, etc.

  // Deployment details
  majorProductFlag: text("major_product_flag"), // yes|no|unknown
  deploymentStatus: text("deployment_status"),
  userBaseSizeBucket: text("user_base_size_bucket"),
  recordsExposedBucket: text("records_exposed_bucket"), // 1-10, 11-100, etc.
  leakDuration: text("leak_duration"),

  // Consequences
  downstreamConsequences: jsonb("downstream_consequences").$type<string[]>(),
  evidenceTypes: jsonb("evidence_types").$type<string[]>(),
  securityLabelConfidence: text("security_label_confidence"), // low|medium|high

  // LLM specific
  llmOrChatbotInvolved: boolean("llm_or_chatbot_involved"),
  llmConnectorTooling: jsonb("llm_connector_tooling").$type<string[]>(),
  llmDataSourceOfLeak: jsonb("llm_data_source_of_leak").$type<string[]>(),
});

// Classifications table (CSET, GMF, MIT taxonomies)
export const classifications = pgTable("classifications", {
  id: serial("id").primaryKey(),
  incidentId: integer("incident_id").notNull(),
  namespace: text("namespace").notNull(), // CSETv1, GMF, MIT
  published: boolean("published"),
  incidentNumber: integer("incident_number"),

  // CSET fields
  harmDomain: text("harm_domain"),
  tangibleHarm: text("tangible_harm"),
  aiSystem: text("ai_system"),
  dateOfIncidentYear: integer("date_of_incident_year"),
  dateOfIncidentMonth: integer("date_of_incident_month"),
  dateOfIncidentDay: integer("date_of_incident_day"),
  locationCountry: text("location_country"),
  locationRegion: text("location_region"),
  sectorOfDeployment: text("sector_of_deployment"),
  publicSectorDeployment: text("public_sector_deployment"),
  intentionalHarm: text("intentional_harm"),
  aiTask: text("ai_task"),
});

// Taxa (taxonomy definitions)
export const taxa = pgTable("taxa", {
  id: serial("id").primaryKey(),
  namespace: text("namespace").notNull(),
  fieldName: text("field_name").notNull(),
  shortName: text("short_name"),
  longName: text("long_name"),
  longDescription: text("long_description"),
});

// Type exports
export type IncidentSecurityRecord = typeof incidentSecurity.$inferSelect;
export type NewIncidentSecurityRecord = typeof incidentSecurity.$inferInsert;

export type ClassificationRecord = typeof classifications.$inferSelect;
export type NewClassificationRecord = typeof classifications.$inferInsert;

export type TaxaRecord = typeof taxa.$inferSelect;
export type NewTaxaRecord = typeof taxa.$inferInsert;
