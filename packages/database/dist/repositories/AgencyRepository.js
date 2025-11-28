"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AgencyRepository = void 0;
// packages/database/src/repositories/AgencyRepository.ts
const db_connection_1 = require("../db-connection");
const drizzle_orm_1 = require("drizzle-orm");
const agencies_1 = require("../schema/agencies");
class AgencyRepository {
    // === Agency AI Usage Methods ===
    // Insert a new agency AI usage record
    async insertUsage(usageData) {
        const [agency] = await db_connection_1.db.insert(agencies_1.agencyAiUsage).values(usageData).returning();
        return agency;
    }
    // Insert multiple agency records
    async insertManyUsages(usagesData) {
        if (usagesData.length === 0)
            return [];
        return await db_connection_1.db.insert(agencies_1.agencyAiUsage).values(usagesData).returning();
    }
    // Update agency by ID
    async updateUsage(agencyId, updateData) {
        return await db_connection_1.db
            .update(agencies_1.agencyAiUsage)
            .set(updateData)
            .where((0, drizzle_orm_1.eq)(agencies_1.agencyAiUsage.id, agencyId))
            .returning();
    }
    // Get agency by ID
    async getUsageById(agencyId) {
        const results = await db_connection_1.db.select().from(agencies_1.agencyAiUsage).where((0, drizzle_orm_1.eq)(agencies_1.agencyAiUsage.id, agencyId));
        return results.length ? results[0] : undefined;
    }
    // Get agency by slug
    async getUsageBySlug(slug) {
        const results = await db_connection_1.db.select().from(agencies_1.agencyAiUsage).where((0, drizzle_orm_1.eq)(agencies_1.agencyAiUsage.slug, slug));
        return results.length ? results[0] : undefined;
    }
    // Get all agency AI usages
    async getAllUsages() {
        return await db_connection_1.db.select().from(agencies_1.agencyAiUsage).orderBy((0, drizzle_orm_1.asc)(agencies_1.agencyAiUsage.agencyName));
    }
    // Get agencies by category
    async getUsagesByCategory(category) {
        return await db_connection_1.db
            .select()
            .from(agencies_1.agencyAiUsage)
            .where((0, drizzle_orm_1.eq)(agencies_1.agencyAiUsage.agencyCategory, category))
            .orderBy((0, drizzle_orm_1.asc)(agencies_1.agencyAiUsage.agencyName));
    }
    // Get agencies with staff LLMs
    async getAgenciesWithStaffLLM() {
        return await db_connection_1.db
            .select()
            .from(agencies_1.agencyAiUsage)
            .where((0, drizzle_orm_1.and)((0, drizzle_orm_1.eq)(agencies_1.agencyAiUsage.agencyCategory, 'staff_llm'), (0, drizzle_orm_1.sql) `${agencies_1.agencyAiUsage.hasStaffLlm} = 'Yes'`))
            .orderBy((0, drizzle_orm_1.asc)(agencies_1.agencyAiUsage.agencyName));
    }
    // Get agencies with coding assistants
    async getAgenciesWithCodingAssistant() {
        return await db_connection_1.db
            .select()
            .from(agencies_1.agencyAiUsage)
            .where((0, drizzle_orm_1.and)((0, drizzle_orm_1.eq)(agencies_1.agencyAiUsage.agencyCategory, 'staff_llm'), (0, drizzle_orm_1.sql) `${agencies_1.agencyAiUsage.hasCodingAssistant} = 'Yes'`))
            .orderBy((0, drizzle_orm_1.asc)(agencies_1.agencyAiUsage.agencyName));
    }
    // Search agencies by name
    async searchUsages(searchTerm) {
        const searchPattern = `%${searchTerm}%`;
        return await db_connection_1.db
            .select()
            .from(agencies_1.agencyAiUsage)
            .where((0, drizzle_orm_1.like)(agencies_1.agencyAiUsage.agencyName, searchPattern))
            .orderBy((0, drizzle_orm_1.asc)(agencies_1.agencyAiUsage.agencyName));
    }
    // Get unique agency names
    async getUniqueAgencies() {
        const result = await db_connection_1.db
            .selectDistinct({ agency: agencies_1.agencyAiUsage.agencyName })
            .from(agencies_1.agencyAiUsage)
            .orderBy((0, drizzle_orm_1.asc)(agencies_1.agencyAiUsage.agencyName));
        return result.map((r) => r.agency);
    }
    // Get agency usage count
    async getUsageCount() {
        const result = await db_connection_1.db
            .select({ count: (0, drizzle_orm_1.sql) `count(*)` })
            .from(agencies_1.agencyAiUsage);
        return result[0].count;
    }
    // Delete agency usage
    async deleteUsage(agencyId) {
        await db_connection_1.db.delete(agencies_1.agencyAiUsage).where((0, drizzle_orm_1.eq)(agencies_1.agencyAiUsage.id, agencyId));
    }
    // Clear all agency usages
    async clearAllUsages() {
        await db_connection_1.db.delete(agencies_1.agencyAiUsage);
    }
    // === Agency Service Matches Methods ===
    // Insert a new service match
    async insertMatch(matchData) {
        const [match] = await db_connection_1.db.insert(agencies_1.agencyServiceMatches).values(matchData).returning();
        return match;
    }
    // Insert multiple matches
    async insertManyMatches(matchesData) {
        if (matchesData.length === 0)
            return [];
        return await db_connection_1.db.insert(agencies_1.agencyServiceMatches).values(matchesData).returning();
    }
    // Get all matches for an agency
    async getMatchesByAgency(agencyId) {
        return await db_connection_1.db
            .select()
            .from(agencies_1.agencyServiceMatches)
            .where((0, drizzle_orm_1.eq)(agencies_1.agencyServiceMatches.agencyId, agencyId))
            .orderBy((0, drizzle_orm_1.desc)(agencies_1.agencyServiceMatches.confidence), (0, drizzle_orm_1.asc)(agencies_1.agencyServiceMatches.providerName));
    }
    // Get matches by confidence level
    async getMatchesByConfidence(agencyId, confidence) {
        return await db_connection_1.db
            .select()
            .from(agencies_1.agencyServiceMatches)
            .where((0, drizzle_orm_1.and)((0, drizzle_orm_1.eq)(agencies_1.agencyServiceMatches.agencyId, agencyId), (0, drizzle_orm_1.eq)(agencies_1.agencyServiceMatches.confidence, confidence)))
            .orderBy((0, drizzle_orm_1.asc)(agencies_1.agencyServiceMatches.providerName));
    }
    // Get all service matches for a product
    async getMatchesByProduct(productId) {
        return await db_connection_1.db
            .select()
            .from(agencies_1.agencyServiceMatches)
            .where((0, drizzle_orm_1.eq)(agencies_1.agencyServiceMatches.productId, productId));
    }
    // Delete matches for an agency
    async deleteMatchesByAgency(agencyId) {
        await db_connection_1.db.delete(agencies_1.agencyServiceMatches).where((0, drizzle_orm_1.eq)(agencies_1.agencyServiceMatches.agencyId, agencyId));
    }
    // Delete a specific match
    async deleteMatch(matchId) {
        await db_connection_1.db.delete(agencies_1.agencyServiceMatches).where((0, drizzle_orm_1.eq)(agencies_1.agencyServiceMatches.id, matchId));
    }
    // Clear all matches
    async clearAllMatches() {
        await db_connection_1.db.delete(agencies_1.agencyServiceMatches);
    }
    // Get match count for an agency
    async getMatchCountByAgency(agencyId) {
        const result = await db_connection_1.db
            .select({ count: (0, drizzle_orm_1.sql) `count(*)` })
            .from(agencies_1.agencyServiceMatches)
            .where((0, drizzle_orm_1.eq)(agencies_1.agencyServiceMatches.agencyId, agencyId));
        return result[0].count;
    }
    // Prepared query for matches by agency
    preparedMatchesByAgency = db_connection_1.db
        .select()
        .from(agencies_1.agencyServiceMatches)
        .where((0, drizzle_orm_1.eq)(agencies_1.agencyServiceMatches.agencyId, drizzle_orm_1.sql.placeholder('agencyId')))
        .prepare('get_matches_by_agency');
    async executePreparedMatchesByAgency(agencyId) {
        return await this.preparedMatchesByAgency.execute({ agencyId });
    }
}
exports.AgencyRepository = AgencyRepository;
//# sourceMappingURL=AgencyRepository.js.map