// packages/database/src/schema/matches.ts
// Schema for cross-domain relationship matches between incidents, products, and use cases

import { serial, text, integer, pgTable, pgEnum, timestamp, real } from "drizzle-orm/pg-core";

// Note: matchConfidenceEnum is already defined in agencies.ts
// We use text columns for match_type and confidence to avoid enum conflicts

// Incident to Product matches
export const incidentProductMatches = pgTable("incident_product_matches", {
  id: serial("id").primaryKey(),
  incidentId: integer("incident_id").notNull(),
  productFedrampId: text("product_fedramp_id").notNull(),
  matchType: text("match_type").notNull(), // entity_name, keyword, embedding, etc.
  confidence: text("confidence").notNull(), // high, medium, low
  matchReason: text("match_reason"), // Human-readable explanation
  matchedEntity: text("matched_entity"), // Which entity triggered the match
  similarityScore: real("similarity_score"), // For embedding matches (0-1)
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// Incident to Use Case matches
export const incidentUseCaseMatches = pgTable("incident_use_case_matches", {
  id: serial("id").primaryKey(),
  incidentId: integer("incident_id").notNull(),
  useCaseId: integer("use_case_id").notNull(),
  matchType: text("match_type").notNull(),
  confidence: text("confidence").notNull(),
  matchReason: text("match_reason"),
  matchedEntity: text("matched_entity"),
  similarityScore: real("similarity_score"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// Entity to Product matches (many entities map to products)
export const entityProductMatches = pgTable("entity_product_matches", {
  id: serial("id").primaryKey(),
  entityId: text("entity_id").notNull(),
  productFedrampId: text("product_fedramp_id").notNull(),
  matchType: text("match_type").notNull(),
  confidence: text("confidence").notNull(),
  matchReason: text("match_reason"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// Type exports
export type IncidentProductMatchRecord = typeof incidentProductMatches.$inferSelect;
export type NewIncidentProductMatchRecord = typeof incidentProductMatches.$inferInsert;

export type IncidentUseCaseMatchRecord = typeof incidentUseCaseMatches.$inferSelect;
export type NewIncidentUseCaseMatchRecord = typeof incidentUseCaseMatches.$inferInsert;

export type EntityProductMatchRecord = typeof entityProductMatches.$inferSelect;
export type NewEntityProductMatchRecord = typeof entityProductMatches.$inferInsert;
