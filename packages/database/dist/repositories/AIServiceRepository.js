"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AIServiceRepository = void 0;
// packages/database/src/repositories/AIServiceRepository.ts
const db_connection_1 = require("../db-connection");
const drizzle_orm_1 = require("drizzle-orm");
const ai_services_1 = require("../schema/ai-services");
class AIServiceRepository {
    // === AI Service Analysis Methods ===
    // Insert a new AI service analysis
    async insertAnalysis(analysisData) {
        const [analysis] = await db_connection_1.db.insert(ai_services_1.aiServiceAnalysis).values(analysisData).returning();
        return analysis;
    }
    // Insert multiple AI service analyses
    async insertManyAnalyses(analysesData) {
        if (analysesData.length === 0)
            return [];
        return await db_connection_1.db.insert(ai_services_1.aiServiceAnalysis).values(analysesData).returning();
    }
    // Get analysis by ID
    async getAnalysisById(id) {
        const results = await db_connection_1.db.select().from(ai_services_1.aiServiceAnalysis).where((0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.id, id));
        return results.length ? results[0] : undefined;
    }
    // Get all analyses for a product
    async getAnalysesByProductId(productId) {
        return await db_connection_1.db
            .select()
            .from(ai_services_1.aiServiceAnalysis)
            .where((0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.productId, productId));
    }
    // Get all AI/ML services
    async getAllAIServices() {
        return await db_connection_1.db
            .select()
            .from(ai_services_1.aiServiceAnalysis)
            .where((0, drizzle_orm_1.or)((0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.hasAi, true), (0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.hasGenai, true), (0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.hasLlm, true)))
            .orderBy((0, drizzle_orm_1.asc)(ai_services_1.aiServiceAnalysis.providerName), (0, drizzle_orm_1.asc)(ai_services_1.aiServiceAnalysis.productName));
    }
    // Get AI services by type
    async getByAIType(type) {
        const condition = type === 'ai' ? (0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.hasAi, true) :
            type === 'genai' ? (0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.hasGenai, true) :
                (0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.hasLlm, true);
        return await db_connection_1.db
            .select()
            .from(ai_services_1.aiServiceAnalysis)
            .where(condition)
            .orderBy((0, drizzle_orm_1.asc)(ai_services_1.aiServiceAnalysis.providerName));
    }
    // Get AI services by provider
    async getByProvider(provider) {
        return await db_connection_1.db
            .select()
            .from(ai_services_1.aiServiceAnalysis)
            .where((0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.providerName, provider))
            .orderBy((0, drizzle_orm_1.asc)(ai_services_1.aiServiceAnalysis.serviceName));
    }
    // Get AI service statistics
    async getStats() {
        const [stats] = await db_connection_1.db
            .select({
            totalServices: (0, drizzle_orm_1.sql) `count(*)`,
            aiCount: (0, drizzle_orm_1.sql) `count(*) filter (where ${ai_services_1.aiServiceAnalysis.hasAi} = true)`,
            genaiCount: (0, drizzle_orm_1.sql) `count(*) filter (where ${ai_services_1.aiServiceAnalysis.hasGenai} = true)`,
            llmCount: (0, drizzle_orm_1.sql) `count(*) filter (where ${ai_services_1.aiServiceAnalysis.hasLlm} = true)`,
            uniqueProducts: (0, drizzle_orm_1.sql) `count(distinct ${ai_services_1.aiServiceAnalysis.productId})`,
            uniqueProviders: (0, drizzle_orm_1.sql) `count(distinct ${ai_services_1.aiServiceAnalysis.providerName})`,
        })
            .from(ai_services_1.aiServiceAnalysis)
            .where((0, drizzle_orm_1.or)((0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.hasAi, true), (0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.hasGenai, true), (0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.hasLlm, true)));
        return stats;
    }
    // Delete all analyses for a product
    async deleteByProductId(productId) {
        await db_connection_1.db.delete(ai_services_1.aiServiceAnalysis).where((0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.productId, productId));
    }
    // Clear all AI analyses
    async clearAll() {
        await db_connection_1.db.delete(ai_services_1.aiServiceAnalysis);
    }
    // === Product AI Analysis Runs Methods ===
    // Record a new analysis run
    async recordAnalysisRun(runData) {
        const [run] = await db_connection_1.db.insert(ai_services_1.productAiAnalysisRuns).values(runData).returning();
        return run;
    }
    // Get last analysis run for a product
    async getLastAnalysisRun(productId) {
        const results = await db_connection_1.db
            .select()
            .from(ai_services_1.productAiAnalysisRuns)
            .where((0, drizzle_orm_1.eq)(ai_services_1.productAiAnalysisRuns.productId, productId))
            .orderBy((0, drizzle_orm_1.desc)(ai_services_1.productAiAnalysisRuns.analyzedAt))
            .limit(1);
        return results.length ? results[0] : undefined;
    }
    // Get analysis run statistics
    async getAnalysisRunStats() {
        const [stats] = await db_connection_1.db
            .select({
            productsAnalyzed: (0, drizzle_orm_1.sql) `count(distinct ${ai_services_1.productAiAnalysisRuns.productId})`,
            lastRun: (0, drizzle_orm_1.sql) `max(${ai_services_1.productAiAnalysisRuns.analyzedAt})`,
            totalServicesFound: (0, drizzle_orm_1.sql) `sum(${ai_services_1.productAiAnalysisRuns.aiServicesFound})`,
        })
            .from(ai_services_1.productAiAnalysisRuns);
        return stats;
    }
    // Get all analysis runs
    async getAllAnalysisRuns() {
        return await db_connection_1.db
            .select()
            .from(ai_services_1.productAiAnalysisRuns)
            .orderBy((0, drizzle_orm_1.desc)(ai_services_1.productAiAnalysisRuns.analyzedAt));
    }
    // Prepared query for analyses by product ID
    preparedAnalysesByProduct = db_connection_1.db
        .select()
        .from(ai_services_1.aiServiceAnalysis)
        .where((0, drizzle_orm_1.eq)(ai_services_1.aiServiceAnalysis.productId, drizzle_orm_1.sql.placeholder('productId')))
        .prepare('get_analyses_by_product');
    async executePreparedAnalysesByProduct(productId) {
        return await this.preparedAnalysesByProduct.execute({ productId });
    }
}
exports.AIServiceRepository = AIServiceRepository;
//# sourceMappingURL=AIServiceRepository.js.map