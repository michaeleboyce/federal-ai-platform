// packages/database/src/schema/entities.ts
import { serial, text, integer, pgTable, pgEnum } from "drizzle-orm/pg-core";

// Enum for entity roles in incidents
export const entityRoleEnum = pgEnum("entity_role", ["deployer", "developer", "harmed"]);

// Entities table (organizations, people involved in incidents)
export const entities = pgTable("entities", {
  id: serial("id").primaryKey(),
  entityId: text("entity_id").notNull().unique(), // Normalized slug
  name: text("name").notNull(),
});

// Junction table for incident-entity relationships
export const incidentEntities = pgTable("incident_entities", {
  id: serial("id").primaryKey(),
  incidentId: integer("incident_id").notNull(),
  entityId: text("entity_id").notNull(),
  role: text("role").notNull(), // 'deployer', 'developer', 'harmed'
});

// Type exports
export type EntityRecord = typeof entities.$inferSelect;
export type NewEntityRecord = typeof entities.$inferInsert;

export type IncidentEntityRecord = typeof incidentEntities.$inferSelect;
export type NewIncidentEntityRecord = typeof incidentEntities.$inferInsert;
