// packages/database/src/repositories/AIServiceRepository.ts
import { db } from '../db-connection';
import { eq, and, sql, or, desc, asc } from 'drizzle-orm';
import {
  aiServiceAnalysis,
  productAiAnalysisRuns,
  type AIServiceAnalysisRecord,
  type NewAIServiceAnalysisRecord,
  type ProductAIAnalysisRunRecord,
  type NewProductAIAnalysisRunRecord,
} from '../schema/ai-services';

export class AIServiceRepository {
  // === AI Service Analysis Methods ===

  // Insert a new AI service analysis
  async insertAnalysis(analysisData: NewAIServiceAnalysisRecord): Promise<AIServiceAnalysisRecord> {
    const [analysis] = await db.insert(aiServiceAnalysis).values(analysisData).returning();
    return analysis;
  }

  // Insert multiple AI service analyses
  async insertManyAnalyses(analysesData: NewAIServiceAnalysisRecord[]): Promise<AIServiceAnalysisRecord[]> {
    if (analysesData.length === 0) return [];
    return await db.insert(aiServiceAnalysis).values(analysesData).returning();
  }

  // Get analysis by ID
  async getAnalysisById(id: number): Promise<AIServiceAnalysisRecord | undefined> {
    const results = await db.select().from(aiServiceAnalysis).where(eq(aiServiceAnalysis.id, id));
    return results.length ? results[0] : undefined;
  }

  // Get all analyses for a product
  async getAnalysesByProductId(productId: string): Promise<AIServiceAnalysisRecord[]> {
    return await db
      .select()
      .from(aiServiceAnalysis)
      .where(eq(aiServiceAnalysis.productId, productId));
  }

  // Get all AI/ML services
  async getAllAIServices(): Promise<AIServiceAnalysisRecord[]> {
    return await db
      .select()
      .from(aiServiceAnalysis)
      .where(
        or(
          eq(aiServiceAnalysis.hasAi, true),
          eq(aiServiceAnalysis.hasGenai, true),
          eq(aiServiceAnalysis.hasLlm, true)
        )
      )
      .orderBy(asc(aiServiceAnalysis.providerName), asc(aiServiceAnalysis.productName));
  }

  // Get AI services by type
  async getByAIType(type: 'ai' | 'genai' | 'llm'): Promise<AIServiceAnalysisRecord[]> {
    const condition =
      type === 'ai' ? eq(aiServiceAnalysis.hasAi, true) :
      type === 'genai' ? eq(aiServiceAnalysis.hasGenai, true) :
      eq(aiServiceAnalysis.hasLlm, true);

    return await db
      .select()
      .from(aiServiceAnalysis)
      .where(condition)
      .orderBy(asc(aiServiceAnalysis.providerName));
  }

  // Get AI services by provider
  async getByProvider(provider: string): Promise<AIServiceAnalysisRecord[]> {
    return await db
      .select()
      .from(aiServiceAnalysis)
      .where(eq(aiServiceAnalysis.providerName, provider))
      .orderBy(asc(aiServiceAnalysis.serviceName));
  }

  // Get AI service statistics
  async getStats(): Promise<{
    totalServices: number;
    aiCount: number;
    genaiCount: number;
    llmCount: number;
    uniqueProducts: number;
    uniqueProviders: number;
  }> {
    const [stats] = await db
      .select({
        totalServices: sql<number>`count(*)`,
        aiCount: sql<number>`count(*) filter (where ${aiServiceAnalysis.hasAi} = true)`,
        genaiCount: sql<number>`count(*) filter (where ${aiServiceAnalysis.hasGenai} = true)`,
        llmCount: sql<number>`count(*) filter (where ${aiServiceAnalysis.hasLlm} = true)`,
        uniqueProducts: sql<number>`count(distinct ${aiServiceAnalysis.productId})`,
        uniqueProviders: sql<number>`count(distinct ${aiServiceAnalysis.providerName})`,
      })
      .from(aiServiceAnalysis)
      .where(
        or(
          eq(aiServiceAnalysis.hasAi, true),
          eq(aiServiceAnalysis.hasGenai, true),
          eq(aiServiceAnalysis.hasLlm, true)
        )
      );

    return stats;
  }

  // Delete all analyses for a product
  async deleteByProductId(productId: string): Promise<void> {
    await db.delete(aiServiceAnalysis).where(eq(aiServiceAnalysis.productId, productId));
  }

  // Clear all AI analyses
  async clearAll(): Promise<void> {
    await db.delete(aiServiceAnalysis);
  }

  // === Product AI Analysis Runs Methods ===

  // Record a new analysis run
  async recordAnalysisRun(runData: NewProductAIAnalysisRunRecord): Promise<ProductAIAnalysisRunRecord> {
    const [run] = await db.insert(productAiAnalysisRuns).values(runData).returning();
    return run;
  }

  // Get last analysis run for a product
  async getLastAnalysisRun(productId: string): Promise<ProductAIAnalysisRunRecord | undefined> {
    const results = await db
      .select()
      .from(productAiAnalysisRuns)
      .where(eq(productAiAnalysisRuns.productId, productId))
      .orderBy(desc(productAiAnalysisRuns.analyzedAt))
      .limit(1);
    return results.length ? results[0] : undefined;
  }

  // Get analysis run statistics
  async getAnalysisRunStats(): Promise<{
    productsAnalyzed: number;
    lastRun: Date | null;
    totalServicesFound: number;
  }> {
    const [stats] = await db
      .select({
        productsAnalyzed: sql<number>`count(distinct ${productAiAnalysisRuns.productId})`,
        lastRun: sql<Date | null>`max(${productAiAnalysisRuns.analyzedAt})`,
        totalServicesFound: sql<number>`sum(${productAiAnalysisRuns.aiServicesFound})`,
      })
      .from(productAiAnalysisRuns);

    return stats;
  }

  // Get all analysis runs
  async getAllAnalysisRuns(): Promise<ProductAIAnalysisRunRecord[]> {
    return await db
      .select()
      .from(productAiAnalysisRuns)
      .orderBy(desc(productAiAnalysisRuns.analyzedAt));
  }

  // Prepared query for analyses by product ID
  private preparedAnalysesByProduct = db
    .select()
    .from(aiServiceAnalysis)
    .where(eq(aiServiceAnalysis.productId, sql.placeholder('productId')))
    .prepare('get_analyses_by_product');

  async executePreparedAnalysesByProduct(productId: string): Promise<AIServiceAnalysisRecord[]> {
    return await this.preparedAnalysesByProduct.execute({ productId });
  }
}
