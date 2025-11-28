"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.agencyServiceMatches = exports.agencyAiUsage = exports.matchConfidenceEnum = exports.agencyCategoryEnum = void 0;
// packages/database/src/schema/agencies.ts
const pg_core_1 = require("drizzle-orm/pg-core");
const products_1 = require("./products");
// Enum for agency category
exports.agencyCategoryEnum = (0, pg_core_1.pgEnum)("agency_category", ["staff_llm", "specialized"]);
// Enum for match confidence
exports.matchConfidenceEnum = (0, pg_core_1.pgEnum)("match_confidence", ["high", "medium", "low"]);
// Agency AI Usage Table
exports.agencyAiUsage = (0, pg_core_1.pgTable)("agency_ai_usage", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    agencyName: (0, pg_core_1.text)("agency_name").notNull(),
    agencyCategory: (0, pg_core_1.text)("agency_category").notNull(), // 'staff_llm' or 'specialized'
    hasStaffLlm: (0, pg_core_1.text)("has_staff_llm"),
    llmName: (0, pg_core_1.text)("llm_name"),
    hasCodingAssistant: (0, pg_core_1.text)("has_coding_assistant"),
    scope: (0, pg_core_1.text)("scope"),
    solutionType: (0, pg_core_1.text)("solution_type"),
    nonPublicAllowed: (0, pg_core_1.text)("non_public_allowed"),
    otherAiPresent: (0, pg_core_1.text)("other_ai_present"),
    toolName: (0, pg_core_1.text)("tool_name"), // for specialized AI
    toolPurpose: (0, pg_core_1.text)("tool_purpose"),
    notes: (0, pg_core_1.text)("notes"),
    sources: (0, pg_core_1.text)("sources"),
    analyzedAt: (0, pg_core_1.timestamp)("analyzed_at", { withTimezone: true }).notNull().defaultNow(),
    slug: (0, pg_core_1.text)("slug"),
});
// Agency Service Matches Table
exports.agencyServiceMatches = (0, pg_core_1.pgTable)("agency_service_matches", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    agencyId: (0, pg_core_1.integer)("agency_id").notNull().references(() => exports.agencyAiUsage.id),
    productId: (0, pg_core_1.text)("product_id").notNull().references(() => products_1.products.fedrampId),
    providerName: (0, pg_core_1.text)("provider_name").notNull(),
    productName: (0, pg_core_1.text)("product_name").notNull(),
    serviceName: (0, pg_core_1.text)("service_name"),
    confidence: (0, pg_core_1.text)("confidence").notNull(), // 'high', 'medium', or 'low'
    matchReason: (0, pg_core_1.text)("match_reason"),
    createdAt: (0, pg_core_1.timestamp)("created_at", { withTimezone: true }).notNull().defaultNow(),
});
//# sourceMappingURL=agencies.js.map