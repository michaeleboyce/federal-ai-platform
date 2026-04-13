"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.UseCaseRepository = void 0;
// packages/database/src/repositories/UseCaseRepository.ts
const db_connection_1 = require("../db-connection");
const drizzle_orm_1 = require("drizzle-orm");
const use_cases_1 = require("../schema/use-cases");
class UseCaseRepository {
    // === AI Use Cases Methods ===
    // Insert a new use case
    async insertUseCase(useCaseData) {
        const [useCase] = await db_connection_1.db.insert(use_cases_1.aiUseCases).values(useCaseData).returning();
        return useCase;
    }
    // Insert multiple use cases
    async insertManyUseCases(useCasesData) {
        if (useCasesData.length === 0)
            return [];
        return await db_connection_1.db.insert(use_cases_1.aiUseCases).values(useCasesData).returning();
    }
    // Update use case
    async updateUseCase(useCaseId, updateData) {
        return await db_connection_1.db
            .update(use_cases_1.aiUseCases)
            .set(updateData)
            .where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCases.id, useCaseId))
            .returning();
    }
    // Get use case by ID
    async getUseCaseById(useCaseId) {
        const results = await db_connection_1.db.select().from(use_cases_1.aiUseCases).where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCases.id, useCaseId));
        return results.length ? results[0] : undefined;
    }
    // Get use case by slug
    async getUseCaseBySlug(slug) {
        const results = await db_connection_1.db.select().from(use_cases_1.aiUseCases).where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCases.slug, slug));
        return results.length ? results[0] : undefined;
    }
    // Get all use cases
    async getAllUseCases() {
        return await db_connection_1.db.select().from(use_cases_1.aiUseCases).orderBy((0, drizzle_orm_1.asc)(use_cases_1.aiUseCases.agency), (0, drizzle_orm_1.asc)(use_cases_1.aiUseCases.useCaseName));
    }
    // Get use cases by agency
    async getUseCasesByAgency(agency) {
        return await db_connection_1.db
            .select()
            .from(use_cases_1.aiUseCases)
            .where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCases.agency, agency))
            .orderBy((0, drizzle_orm_1.asc)(use_cases_1.aiUseCases.useCaseName));
    }
    // Get use cases by domain category
    async getUseCasesByDomain(domain) {
        return await db_connection_1.db
            .select()
            .from(use_cases_1.aiUseCases)
            .where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCases.domainCategory, domain))
            .orderBy((0, drizzle_orm_1.asc)(use_cases_1.aiUseCases.useCaseName));
    }
    // Get GenAI use cases
    async getGenAIUseCases() {
        return await db_connection_1.db
            .select()
            .from(use_cases_1.aiUseCases)
            .where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCases.genaiFlag, true))
            .orderBy((0, drizzle_orm_1.asc)(use_cases_1.aiUseCases.agency));
    }
    // Get use cases with LLMs
    async getLLMUseCases() {
        return await db_connection_1.db
            .select()
            .from(use_cases_1.aiUseCases)
            .where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCases.hasLlm, true))
            .orderBy((0, drizzle_orm_1.asc)(use_cases_1.aiUseCases.agency));
    }
    // Get use cases with chatbots
    async getChatbotUseCases() {
        return await db_connection_1.db
            .select()
            .from(use_cases_1.aiUseCases)
            .where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCases.hasChatbot, true))
            .orderBy((0, drizzle_orm_1.asc)(use_cases_1.aiUseCases.agency));
    }
    // Search use cases
    async searchUseCases(searchTerm) {
        const searchPattern = `%${searchTerm}%`;
        return await db_connection_1.db
            .select()
            .from(use_cases_1.aiUseCases)
            .where((0, drizzle_orm_1.or)((0, drizzle_orm_1.like)(use_cases_1.aiUseCases.useCaseName, searchPattern), (0, drizzle_orm_1.like)(use_cases_1.aiUseCases.agency, searchPattern), (0, drizzle_orm_1.like)(use_cases_1.aiUseCases.intendedPurpose, searchPattern)))
            .orderBy((0, drizzle_orm_1.asc)(use_cases_1.aiUseCases.agency));
    }
    // Get use case statistics
    async getUseCaseStats() {
        const [stats] = await db_connection_1.db
            .select({
            totalUseCases: (0, drizzle_orm_1.sql) `count(*)`,
            uniqueAgencies: (0, drizzle_orm_1.sql) `count(distinct ${use_cases_1.aiUseCases.agency})`,
            genaiCount: (0, drizzle_orm_1.sql) `count(*) filter (where ${use_cases_1.aiUseCases.genaiFlag} = true)`,
            llmCount: (0, drizzle_orm_1.sql) `count(*) filter (where ${use_cases_1.aiUseCases.hasLlm} = true)`,
            chatbotCount: (0, drizzle_orm_1.sql) `count(*) filter (where ${use_cases_1.aiUseCases.hasChatbot} = true)`,
            classicMlCount: (0, drizzle_orm_1.sql) `count(*) filter (where ${use_cases_1.aiUseCases.hasClassicMl} = true)`,
            uniqueDomains: (0, drizzle_orm_1.sql) `count(distinct ${use_cases_1.aiUseCases.domainCategory})`,
        })
            .from(use_cases_1.aiUseCases);
        return stats;
    }
    // Delete use case
    async deleteUseCase(useCaseId) {
        await db_connection_1.db.delete(use_cases_1.aiUseCases).where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCases.id, useCaseId));
    }
    // === AI Use Case Details Methods ===
    // Insert use case details
    async insertUseCaseDetails(detailsData) {
        const [details] = await db_connection_1.db.insert(use_cases_1.aiUseCaseDetails).values(detailsData).returning();
        return details;
    }
    // Get use case details
    async getUseCaseDetails(useCaseId) {
        const results = await db_connection_1.db
            .select()
            .from(use_cases_1.aiUseCaseDetails)
            .where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCaseDetails.useCaseId, useCaseId));
        return results.length ? results[0] : undefined;
    }
    // Update use case details
    async updateUseCaseDetails(useCaseId, updateData) {
        return await db_connection_1.db
            .update(use_cases_1.aiUseCaseDetails)
            .set(updateData)
            .where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCaseDetails.useCaseId, useCaseId))
            .returning();
    }
    // Delete use case details
    async deleteUseCaseDetails(useCaseId) {
        await db_connection_1.db.delete(use_cases_1.aiUseCaseDetails).where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCaseDetails.useCaseId, useCaseId));
    }
    // === Use Case FedRAMP Matches Methods ===
    // Insert a match
    async insertMatch(matchData) {
        const [match] = await db_connection_1.db.insert(use_cases_1.useCaseFedrampMatches).values(matchData).returning();
        return match;
    }
    // Insert multiple matches
    async insertManyMatches(matchesData) {
        if (matchesData.length === 0)
            return [];
        return await db_connection_1.db.insert(use_cases_1.useCaseFedrampMatches).values(matchesData).returning();
    }
    // Get matches for a use case
    async getMatchesByUseCase(useCaseId) {
        return await db_connection_1.db
            .select()
            .from(use_cases_1.useCaseFedrampMatches)
            .where((0, drizzle_orm_1.eq)(use_cases_1.useCaseFedrampMatches.useCaseId, useCaseId))
            .orderBy((0, drizzle_orm_1.desc)(use_cases_1.useCaseFedrampMatches.confidence));
    }
    // Get matches by confidence
    async getMatchesByConfidence(useCaseId, confidence) {
        return await db_connection_1.db
            .select()
            .from(use_cases_1.useCaseFedrampMatches)
            .where((0, drizzle_orm_1.and)((0, drizzle_orm_1.eq)(use_cases_1.useCaseFedrampMatches.useCaseId, useCaseId), (0, drizzle_orm_1.eq)(use_cases_1.useCaseFedrampMatches.confidence, confidence)));
    }
    // Get matches for a product
    async getMatchesByProduct(productId) {
        return await db_connection_1.db
            .select()
            .from(use_cases_1.useCaseFedrampMatches)
            .where((0, drizzle_orm_1.eq)(use_cases_1.useCaseFedrampMatches.productId, productId));
    }
    // Delete matches for a use case
    async deleteMatchesByUseCase(useCaseId) {
        await db_connection_1.db.delete(use_cases_1.useCaseFedrampMatches).where((0, drizzle_orm_1.eq)(use_cases_1.useCaseFedrampMatches.useCaseId, useCaseId));
    }
    // Delete a specific match
    async deleteMatch(matchId) {
        await db_connection_1.db.delete(use_cases_1.useCaseFedrampMatches).where((0, drizzle_orm_1.eq)(use_cases_1.useCaseFedrampMatches.id, matchId));
    }
    // Prepared query for use cases by agency
    preparedUseCasesByAgency = db_connection_1.db
        .select()
        .from(use_cases_1.aiUseCases)
        .where((0, drizzle_orm_1.eq)(use_cases_1.aiUseCases.agency, drizzle_orm_1.sql.placeholder('agency')))
        .prepare('get_use_cases_by_agency');
    async executePreparedUseCasesByAgency(agency) {
        return await this.preparedUseCasesByAgency.execute({ agency });
    }
}
exports.UseCaseRepository = UseCaseRepository;
//# sourceMappingURL=UseCaseRepository.js.map