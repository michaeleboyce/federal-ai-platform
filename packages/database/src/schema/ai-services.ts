// packages/database/src/schema/ai-services.ts
import { serial, text, boolean, integer, timestamp, pgTable } from "drizzle-orm/pg-core";
import { products } from "./products";

// AI Service Analysis Table
export const aiServiceAnalysis = pgTable("ai_service_analysis", {
  id: serial("id").primaryKey(),
  productId: text("product_id").notNull().references(() => products.fedrampId),
  productName: text("product_name"),
  providerName: text("provider_name"),
  serviceName: text("service_name"),
  hasAi: boolean("has_ai").notNull().default(false),
  hasGenai: boolean("has_genai").notNull().default(false),
  hasLlm: boolean("has_llm").notNull().default(false),
  relevantExcerpt: text("relevant_excerpt"),
  fedrampStatus: text("fedramp_status"),
  impactLevel: text("impact_level"),
  agencies: text("agencies"),
  authDate: text("auth_date"),
  analyzedAt: timestamp("analyzed_at", { withTimezone: true }).notNull().defaultNow(),
});

// Product AI Analysis Runs Table (tracking table)
export const productAiAnalysisRuns = pgTable("product_ai_analysis_runs", {
  id: serial("id").primaryKey(),
  productId: text("product_id").notNull().references(() => products.fedrampId),
  productName: text("product_name"),
  providerName: text("provider_name"),
  analyzedAt: timestamp("analyzed_at", { withTimezone: true }).notNull().defaultNow(),
  aiServicesFound: integer("ai_services_found").notNull().default(0),
});

export type AIServiceAnalysisRecord = typeof aiServiceAnalysis.$inferSelect;
export type NewAIServiceAnalysisRecord = typeof aiServiceAnalysis.$inferInsert;
export type ProductAIAnalysisRunRecord = typeof productAiAnalysisRuns.$inferSelect;
export type NewProductAIAnalysisRunRecord = typeof productAiAnalysisRuns.$inferInsert;
