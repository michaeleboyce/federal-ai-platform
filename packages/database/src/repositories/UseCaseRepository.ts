// packages/database/src/repositories/UseCaseRepository.ts
import { db } from '../db-connection';
import { eq, and, sql, like, or, desc, asc } from 'drizzle-orm';
import {
  aiUseCases,
  aiUseCaseDetails,
  useCaseFedrampMatches,
  type AIUseCaseRecord,
  type NewAIUseCaseRecord,
  type AIUseCaseDetailRecord,
  type NewAIUseCaseDetailRecord,
  type UseCaseFedrampMatchRecord,
  type NewUseCaseFedrampMatchRecord,
} from '../schema/use-cases';

export class UseCaseRepository {
  // === AI Use Cases Methods ===

  // Insert a new use case
  async insertUseCase(useCaseData: NewAIUseCaseRecord): Promise<AIUseCaseRecord> {
    const [useCase] = await db.insert(aiUseCases).values(useCaseData).returning();
    return useCase;
  }

  // Insert multiple use cases
  async insertManyUseCases(useCasesData: NewAIUseCaseRecord[]): Promise<AIUseCaseRecord[]> {
    if (useCasesData.length === 0) return [];
    return await db.insert(aiUseCases).values(useCasesData).returning();
  }

  // Update use case
  async updateUseCase(useCaseId: number, updateData: Partial<AIUseCaseRecord>): Promise<AIUseCaseRecord[]> {
    return await db
      .update(aiUseCases)
      .set(updateData)
      .where(eq(aiUseCases.id, useCaseId))
      .returning();
  }

  // Get use case by ID
  async getUseCaseById(useCaseId: number): Promise<AIUseCaseRecord | undefined> {
    const results = await db.select().from(aiUseCases).where(eq(aiUseCases.id, useCaseId));
    return results.length ? results[0] : undefined;
  }

  // Get use case by slug
  async getUseCaseBySlug(slug: string): Promise<AIUseCaseRecord | undefined> {
    const results = await db.select().from(aiUseCases).where(eq(aiUseCases.slug, slug));
    return results.length ? results[0] : undefined;
  }

  // Get all use cases
  async getAllUseCases(): Promise<AIUseCaseRecord[]> {
    return await db.select().from(aiUseCases).orderBy(asc(aiUseCases.agency), asc(aiUseCases.useCaseName));
  }

  // Get use cases by agency
  async getUseCasesByAgency(agency: string): Promise<AIUseCaseRecord[]> {
    return await db
      .select()
      .from(aiUseCases)
      .where(eq(aiUseCases.agency, agency))
      .orderBy(asc(aiUseCases.useCaseName));
  }

  // Get use cases by domain category
  async getUseCasesByDomain(domain: string): Promise<AIUseCaseRecord[]> {
    return await db
      .select()
      .from(aiUseCases)
      .where(eq(aiUseCases.domainCategory, domain))
      .orderBy(asc(aiUseCases.useCaseName));
  }

  // Get GenAI use cases
  async getGenAIUseCases(): Promise<AIUseCaseRecord[]> {
    return await db
      .select()
      .from(aiUseCases)
      .where(eq(aiUseCases.genaiFlag, true))
      .orderBy(asc(aiUseCases.agency));
  }

  // Get use cases with LLMs
  async getLLMUseCases(): Promise<AIUseCaseRecord[]> {
    return await db
      .select()
      .from(aiUseCases)
      .where(eq(aiUseCases.hasLlm, true))
      .orderBy(asc(aiUseCases.agency));
  }

  // Get use cases with chatbots
  async getChatbotUseCases(): Promise<AIUseCaseRecord[]> {
    return await db
      .select()
      .from(aiUseCases)
      .where(eq(aiUseCases.hasChatbot, true))
      .orderBy(asc(aiUseCases.agency));
  }

  // Search use cases
  async searchUseCases(searchTerm: string): Promise<AIUseCaseRecord[]> {
    const searchPattern = `%${searchTerm}%`;
    return await db
      .select()
      .from(aiUseCases)
      .where(
        or(
          like(aiUseCases.useCaseName, searchPattern),
          like(aiUseCases.agency, searchPattern),
          like(aiUseCases.intendedPurpose, searchPattern)
        )
      )
      .orderBy(asc(aiUseCases.agency));
  }

  // Get use case statistics
  async getUseCaseStats(): Promise<{
    totalUseCases: number;
    uniqueAgencies: number;
    genaiCount: number;
    llmCount: number;
    chatbotCount: number;
    classicMlCount: number;
    uniqueDomains: number;
  }> {
    const [stats] = await db
      .select({
        totalUseCases: sql<number>`count(*)`,
        uniqueAgencies: sql<number>`count(distinct ${aiUseCases.agency})`,
        genaiCount: sql<number>`count(*) filter (where ${aiUseCases.genaiFlag} = true)`,
        llmCount: sql<number>`count(*) filter (where ${aiUseCases.hasLlm} = true)`,
        chatbotCount: sql<number>`count(*) filter (where ${aiUseCases.hasChatbot} = true)`,
        classicMlCount: sql<number>`count(*) filter (where ${aiUseCases.hasClassicMl} = true)`,
        uniqueDomains: sql<number>`count(distinct ${aiUseCases.domainCategory})`,
      })
      .from(aiUseCases);

    return stats;
  }

  // Delete use case
  async deleteUseCase(useCaseId: number): Promise<void> {
    await db.delete(aiUseCases).where(eq(aiUseCases.id, useCaseId));
  }

  // === AI Use Case Details Methods ===

  // Insert use case details
  async insertUseCaseDetails(detailsData: NewAIUseCaseDetailRecord): Promise<AIUseCaseDetailRecord> {
    const [details] = await db.insert(aiUseCaseDetails).values(detailsData).returning();
    return details;
  }

  // Get use case details
  async getUseCaseDetails(useCaseId: number): Promise<AIUseCaseDetailRecord | undefined> {
    const results = await db
      .select()
      .from(aiUseCaseDetails)
      .where(eq(aiUseCaseDetails.useCaseId, useCaseId));
    return results.length ? results[0] : undefined;
  }

  // Update use case details
  async updateUseCaseDetails(
    useCaseId: number,
    updateData: Partial<AIUseCaseDetailRecord>
  ): Promise<AIUseCaseDetailRecord[]> {
    return await db
      .update(aiUseCaseDetails)
      .set(updateData)
      .where(eq(aiUseCaseDetails.useCaseId, useCaseId))
      .returning();
  }

  // Delete use case details
  async deleteUseCaseDetails(useCaseId: number): Promise<void> {
    await db.delete(aiUseCaseDetails).where(eq(aiUseCaseDetails.useCaseId, useCaseId));
  }

  // === Use Case FedRAMP Matches Methods ===

  // Insert a match
  async insertMatch(matchData: NewUseCaseFedrampMatchRecord): Promise<UseCaseFedrampMatchRecord> {
    const [match] = await db.insert(useCaseFedrampMatches).values(matchData).returning();
    return match;
  }

  // Insert multiple matches
  async insertManyMatches(matchesData: NewUseCaseFedrampMatchRecord[]): Promise<UseCaseFedrampMatchRecord[]> {
    if (matchesData.length === 0) return [];
    return await db.insert(useCaseFedrampMatches).values(matchesData).returning();
  }

  // Get matches for a use case
  async getMatchesByUseCase(useCaseId: number): Promise<UseCaseFedrampMatchRecord[]> {
    return await db
      .select()
      .from(useCaseFedrampMatches)
      .where(eq(useCaseFedrampMatches.useCaseId, useCaseId))
      .orderBy(desc(useCaseFedrampMatches.confidence));
  }

  // Get matches by confidence
  async getMatchesByConfidence(
    useCaseId: number,
    confidence: 'high' | 'medium' | 'low'
  ): Promise<UseCaseFedrampMatchRecord[]> {
    return await db
      .select()
      .from(useCaseFedrampMatches)
      .where(
        and(
          eq(useCaseFedrampMatches.useCaseId, useCaseId),
          eq(useCaseFedrampMatches.confidence, confidence)
        )
      );
  }

  // Get matches for a product
  async getMatchesByProduct(productId: string): Promise<UseCaseFedrampMatchRecord[]> {
    return await db
      .select()
      .from(useCaseFedrampMatches)
      .where(eq(useCaseFedrampMatches.productId, productId));
  }

  // Delete matches for a use case
  async deleteMatchesByUseCase(useCaseId: number): Promise<void> {
    await db.delete(useCaseFedrampMatches).where(eq(useCaseFedrampMatches.useCaseId, useCaseId));
  }

  // Delete a specific match
  async deleteMatch(matchId: number): Promise<void> {
    await db.delete(useCaseFedrampMatches).where(eq(useCaseFedrampMatches.id, matchId));
  }

  // Prepared query for use cases by agency
  private preparedUseCasesByAgency = db
    .select()
    .from(aiUseCases)
    .where(eq(aiUseCases.agency, sql.placeholder('agency')))
    .prepare('get_use_cases_by_agency');

  async executePreparedUseCasesByAgency(agency: string): Promise<AIUseCaseRecord[]> {
    return await this.preparedUseCasesByAgency.execute({ agency });
  }
}
