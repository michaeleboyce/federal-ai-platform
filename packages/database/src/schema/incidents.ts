// packages/database/src/schema/incidents.ts
import { serial, text, integer, timestamp, pgTable, jsonb } from "drizzle-orm/pg-core";

// Main incidents table
export const incidents = pgTable("incidents", {
  id: serial("id").primaryKey(),
  incidentId: integer("incident_id").notNull().unique(),
  title: text("title").notNull(),
  description: text("description"),
  date: text("date"), // ISO date string
  deployers: jsonb("deployers").$type<string[]>(), // Array of deployer names
  developers: jsonb("developers").$type<string[]>(), // Array of developer names
  harmedParties: jsonb("harmed_parties").$type<string[]>(), // Array of harmed party names
  reportCount: integer("report_count").default(0),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// Reports table
export const reports = pgTable("reports", {
  id: serial("id").primaryKey(),
  reportNumber: integer("report_number").notNull().unique(),
  incidentId: integer("incident_id"),
  title: text("title"),
  text: text("text"),
  url: text("url"),
  sourceDomain: text("source_domain"),
  authors: jsonb("authors").$type<string[]>(), // Array of author names
  datePublished: text("date_published"),
  dateDownloaded: text("date_downloaded"),
  dateModified: text("date_modified"),
  dateSubmitted: text("date_submitted"),
  language: text("language"),
  imageUrl: text("image_url"),
  tags: jsonb("tags").$type<string[]>(),
});

// Type exports
export type IncidentRecord = typeof incidents.$inferSelect;
export type NewIncidentRecord = typeof incidents.$inferInsert;

export type ReportRecord = typeof reports.$inferSelect;
export type NewReportRecord = typeof reports.$inferInsert;
