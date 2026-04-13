// packages/database/src/repositories/AgencyRepository.ts
import { db } from '../db-connection';
import { eq, and, sql, like, or, desc, asc } from 'drizzle-orm';
import {
  agencyAiUsage,
  agencyServiceMatches,
  type AgencyAIUsageRecord,
  type NewAgencyAIUsageRecord,
  type AgencyServiceMatchRecord,
  type NewAgencyServiceMatchRecord,
} from '../schema/agencies';

export class AgencyRepository {
  // === Agency AI Usage Methods ===

  // Insert a new agency AI usage record
  async insertUsage(usageData: NewAgencyAIUsageRecord): Promise<AgencyAIUsageRecord> {
    const [agency] = await db.insert(agencyAiUsage).values(usageData).returning();
    return agency;
  }

  // Insert multiple agency records
  async insertManyUsages(usagesData: NewAgencyAIUsageRecord[]): Promise<AgencyAIUsageRecord[]> {
    if (usagesData.length === 0) return [];
    return await db.insert(agencyAiUsage).values(usagesData).returning();
  }

  // Update agency by ID
  async updateUsage(agencyId: number, updateData: Partial<AgencyAIUsageRecord>): Promise<AgencyAIUsageRecord[]> {
    return await db
      .update(agencyAiUsage)
      .set(updateData)
      .where(eq(agencyAiUsage.id, agencyId))
      .returning();
  }

  // Get agency by ID
  async getUsageById(agencyId: number): Promise<AgencyAIUsageRecord | undefined> {
    const results = await db.select().from(agencyAiUsage).where(eq(agencyAiUsage.id, agencyId));
    return results.length ? results[0] : undefined;
  }

  // Get agency by slug
  async getUsageBySlug(slug: string): Promise<AgencyAIUsageRecord | undefined> {
    const results = await db.select().from(agencyAiUsage).where(eq(agencyAiUsage.slug, slug));
    return results.length ? results[0] : undefined;
  }

  // Get all agency AI usages
  async getAllUsages(): Promise<AgencyAIUsageRecord[]> {
    return await db.select().from(agencyAiUsage).orderBy(asc(agencyAiUsage.agencyName));
  }

  // Get agencies by category
  async getUsagesByCategory(category: 'staff_llm' | 'specialized'): Promise<AgencyAIUsageRecord[]> {
    return await db
      .select()
      .from(agencyAiUsage)
      .where(eq(agencyAiUsage.agencyCategory, category))
      .orderBy(asc(agencyAiUsage.agencyName));
  }

  // Get agencies with staff LLMs
  async getAgenciesWithStaffLLM(): Promise<AgencyAIUsageRecord[]> {
    return await db
      .select()
      .from(agencyAiUsage)
      .where(and(
        eq(agencyAiUsage.agencyCategory, 'staff_llm'),
        sql`${agencyAiUsage.hasStaffLlm} = 'Yes'`
      ))
      .orderBy(asc(agencyAiUsage.agencyName));
  }

  // Get agencies with coding assistants
  async getAgenciesWithCodingAssistant(): Promise<AgencyAIUsageRecord[]> {
    return await db
      .select()
      .from(agencyAiUsage)
      .where(and(
        eq(agencyAiUsage.agencyCategory, 'staff_llm'),
        sql`${agencyAiUsage.hasCodingAssistant} = 'Yes'`
      ))
      .orderBy(asc(agencyAiUsage.agencyName));
  }

  // Search agencies by name
  async searchUsages(searchTerm: string): Promise<AgencyAIUsageRecord[]> {
    const searchPattern = `%${searchTerm}%`;
    return await db
      .select()
      .from(agencyAiUsage)
      .where(like(agencyAiUsage.agencyName, searchPattern))
      .orderBy(asc(agencyAiUsage.agencyName));
  }

  // Get unique agency names
  async getUniqueAgencies(): Promise<string[]> {
    const result = await db
      .selectDistinct({ agency: agencyAiUsage.agencyName })
      .from(agencyAiUsage)
      .orderBy(asc(agencyAiUsage.agencyName));
    return result.map((r) => r.agency);
  }

  // Get agency usage count
  async getUsageCount(): Promise<number> {
    const result = await db
      .select({ count: sql<number>`count(*)` })
      .from(agencyAiUsage);
    return result[0].count;
  }

  // Delete agency usage
  async deleteUsage(agencyId: number): Promise<void> {
    await db.delete(agencyAiUsage).where(eq(agencyAiUsage.id, agencyId));
  }

  // Clear all agency usages
  async clearAllUsages(): Promise<void> {
    await db.delete(agencyAiUsage);
  }

  // === Agency Service Matches Methods ===

  // Insert a new service match
  async insertMatch(matchData: NewAgencyServiceMatchRecord): Promise<AgencyServiceMatchRecord> {
    const [match] = await db.insert(agencyServiceMatches).values(matchData).returning();
    return match;
  }

  // Insert multiple matches
  async insertManyMatches(matchesData: NewAgencyServiceMatchRecord[]): Promise<AgencyServiceMatchRecord[]> {
    if (matchesData.length === 0) return [];
    return await db.insert(agencyServiceMatches).values(matchesData).returning();
  }

  // Get all matches for an agency
  async getMatchesByAgency(agencyId: number): Promise<AgencyServiceMatchRecord[]> {
    return await db
      .select()
      .from(agencyServiceMatches)
      .where(eq(agencyServiceMatches.agencyId, agencyId))
      .orderBy(desc(agencyServiceMatches.confidence), asc(agencyServiceMatches.providerName));
  }

  // Get matches by confidence level
  async getMatchesByConfidence(
    agencyId: number,
    confidence: 'high' | 'medium' | 'low'
  ): Promise<AgencyServiceMatchRecord[]> {
    return await db
      .select()
      .from(agencyServiceMatches)
      .where(and(
        eq(agencyServiceMatches.agencyId, agencyId),
        eq(agencyServiceMatches.confidence, confidence)
      ))
      .orderBy(asc(agencyServiceMatches.providerName));
  }

  // Get all service matches for a product
  async getMatchesByProduct(productId: string): Promise<AgencyServiceMatchRecord[]> {
    return await db
      .select()
      .from(agencyServiceMatches)
      .where(eq(agencyServiceMatches.productId, productId));
  }

  // Delete matches for an agency
  async deleteMatchesByAgency(agencyId: number): Promise<void> {
    await db.delete(agencyServiceMatches).where(eq(agencyServiceMatches.agencyId, agencyId));
  }

  // Delete a specific match
  async deleteMatch(matchId: number): Promise<void> {
    await db.delete(agencyServiceMatches).where(eq(agencyServiceMatches.id, matchId));
  }

  // Clear all matches
  async clearAllMatches(): Promise<void> {
    await db.delete(agencyServiceMatches);
  }

  // Get match count for an agency
  async getMatchCountByAgency(agencyId: number): Promise<number> {
    const result = await db
      .select({ count: sql<number>`count(*)` })
      .from(agencyServiceMatches)
      .where(eq(agencyServiceMatches.agencyId, agencyId));
    return result[0].count;
  }

  // Prepared query for matches by agency
  private preparedMatchesByAgency = db
    .select()
    .from(agencyServiceMatches)
    .where(eq(agencyServiceMatches.agencyId, sql.placeholder('agencyId')))
    .prepare('get_matches_by_agency');

  async executePreparedMatchesByAgency(agencyId: number): Promise<AgencyServiceMatchRecord[]> {
    return await this.preparedMatchesByAgency.execute({ agencyId });
  }
}
