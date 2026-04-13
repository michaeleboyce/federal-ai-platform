"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.productAiAnalysisRuns = exports.aiServiceAnalysis = void 0;
// packages/database/src/schema/ai-services.ts
const pg_core_1 = require("drizzle-orm/pg-core");
const products_1 = require("./products");
// AI Service Analysis Table
exports.aiServiceAnalysis = (0, pg_core_1.pgTable)("ai_service_analysis", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    productId: (0, pg_core_1.text)("product_id").notNull().references(() => products_1.products.fedrampId),
    productName: (0, pg_core_1.text)("product_name"),
    providerName: (0, pg_core_1.text)("provider_name"),
    serviceName: (0, pg_core_1.text)("service_name"),
    hasAi: (0, pg_core_1.boolean)("has_ai").notNull().default(false),
    hasGenai: (0, pg_core_1.boolean)("has_genai").notNull().default(false),
    hasLlm: (0, pg_core_1.boolean)("has_llm").notNull().default(false),
    relevantExcerpt: (0, pg_core_1.text)("relevant_excerpt"),
    fedrampStatus: (0, pg_core_1.text)("fedramp_status"),
    impactLevel: (0, pg_core_1.text)("impact_level"),
    agencies: (0, pg_core_1.text)("agencies"),
    authDate: (0, pg_core_1.text)("auth_date"),
    analyzedAt: (0, pg_core_1.timestamp)("analyzed_at", { withTimezone: true }).notNull().defaultNow(),
});
// Product AI Analysis Runs Table (tracking table)
exports.productAiAnalysisRuns = (0, pg_core_1.pgTable)("product_ai_analysis_runs", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    productId: (0, pg_core_1.text)("product_id").notNull().references(() => products_1.products.fedrampId),
    productName: (0, pg_core_1.text)("product_name"),
    providerName: (0, pg_core_1.text)("provider_name"),
    analyzedAt: (0, pg_core_1.timestamp)("analyzed_at", { withTimezone: true }).notNull().defaultNow(),
    aiServicesFound: (0, pg_core_1.integer)("ai_services_found").notNull().default(0),
});
//# sourceMappingURL=ai-services.js.map