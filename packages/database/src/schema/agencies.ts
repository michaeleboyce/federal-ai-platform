// packages/database/src/schema/agencies.ts
import { serial, text, integer, timestamp, pgTable, pgEnum } from "drizzle-orm/pg-core";
import { products } from "./products";

// Enum for agency category
export const agencyCategoryEnum = pgEnum("agency_category", ["staff_llm", "specialized"]);

// Enum for match confidence
export const matchConfidenceEnum = pgEnum("match_confidence", ["high", "medium", "low"]);

// Agency AI Usage Table
export const agencyAiUsage = pgTable("agency_ai_usage", {
  id: serial("id").primaryKey(),
  agencyName: text("agency_name").notNull(),
  agencyCategory: text("agency_category").notNull(), // 'staff_llm' or 'specialized'
  hasStaffLlm: text("has_staff_llm"),
  llmName: text("llm_name"),
  hasCodingAssistant: text("has_coding_assistant"),
  scope: text("scope"),
  solutionType: text("solution_type"),
  nonPublicAllowed: text("non_public_allowed"),
  otherAiPresent: text("other_ai_present"),
  toolName: text("tool_name"), // for specialized AI
  toolPurpose: text("tool_purpose"),
  notes: text("notes"),
  sources: text("sources"),
  analyzedAt: timestamp("analyzed_at", { withTimezone: true }).notNull().defaultNow(),
  slug: text("slug"),
});

// Agency Service Matches Table
export const agencyServiceMatches = pgTable("agency_service_matches", {
  id: serial("id").primaryKey(),
  agencyId: integer("agency_id").notNull().references(() => agencyAiUsage.id),
  productId: text("product_id").notNull().references(() => products.fedrampId),
  providerName: text("provider_name").notNull(),
  productName: text("product_name").notNull(),
  serviceName: text("service_name"),
  confidence: text("confidence").notNull(), // 'high', 'medium', or 'low'
  matchReason: text("match_reason"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export type AgencyAIUsageRecord = typeof agencyAiUsage.$inferSelect;
export type NewAgencyAIUsageRecord = typeof agencyAiUsage.$inferInsert;
export type AgencyServiceMatchRecord = typeof agencyServiceMatches.$inferSelect;
export type NewAgencyServiceMatchRecord = typeof agencyServiceMatches.$inferInsert;
