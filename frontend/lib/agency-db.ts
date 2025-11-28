import { db } from './db/client';
import { agencyAiUsage, agencyServiceMatches } from './db/schema';
import { eq, or, ilike, sql } from 'drizzle-orm';
import type { AgencyAIUsage as AgencyAIUsageType, AgencyServiceMatch as AgencyServiceMatchType } from './db/schema';

export interface AgencyAIUsage {
  id: number;
  agency_name: string;
  agency_category: string;
  has_staff_llm: string | null;
  llm_name: string | null;
  has_coding_assistant: string | null;
  scope: string | null;
  solution_type: string | null;
  non_public_allowed: string | null;
  other_ai_present: string | null;
  tool_name: string | null;
  tool_purpose: string | null;
  notes: string | null;
  sources: string | null;
  organization_id: number | null;
  analyzed_at: Date;
  slug: string;
}

export interface AgencyServiceMatch {
  product_id: string;
  provider_name: string;
  product_name: string;
  confidence: string;
  match_reason: string | null;
}

export interface AgencyStats {
  total_agencies: number;
  agencies_with_llm: number;
  agencies_with_coding: number;
  agencies_custom_solution: number;
  agencies_commercial_solution: number;
  total_matches: number;
  high_confidence_matches: number;
}

function transformAgency(result: AgencyAIUsageType): AgencyAIUsage {
  return {
    id: result.id,
    agency_name: result.agencyName,
    agency_category: result.agencyCategory,
    has_staff_llm: result.hasStaffLlm,
    llm_name: result.llmName,
    has_coding_assistant: result.hasCodingAssistant,
    scope: result.scope,
    solution_type: result.solutionType,
    non_public_allowed: result.nonPublicAllowed,
    other_ai_present: result.otherAiPresent,
    tool_name: result.toolName,
    tool_purpose: result.toolPurpose,
    notes: result.notes,
    sources: result.sources,
    organization_id: result.organizationId,
    analyzed_at: result.analyzedAt,
    slug: result.slug,
  };
}

function transformMatch(result: AgencyServiceMatchType): AgencyServiceMatch {
  return {
    product_id: result.productId,
    provider_name: result.providerName,
    product_name: result.productName,
    confidence: result.confidence,
    match_reason: result.matchReason,
  };
}

export async function getAgencies(category?: 'staff_llm' | 'specialized'): Promise<AgencyAIUsage[]> {
  try {
    let query = db.select().from(agencyAiUsage);

    if (category) {
      query = query.where(eq(agencyAiUsage.agencyCategory, category)) as typeof query;
    }

    const results = await query.orderBy(agencyAiUsage.agencyName);
    return results.map(transformAgency);
  } catch (error) {
    console.error('Error fetching agencies:', error);
    return [];
  }
}

export async function getAgencyBySlug(slug: string): Promise<AgencyAIUsage | null> {
  try {
    const results = await db
      .select()
      .from(agencyAiUsage)
      .where(eq(agencyAiUsage.slug, slug))
      .limit(1);

    return results.length > 0 ? transformAgency(results[0]) : null;
  } catch (error) {
    console.error('Error fetching agency by slug:', error);
    return null;
  }
}

export async function getAgencyMatches(agencyId: number): Promise<AgencyServiceMatch[]> {
  try {
    const results = await db
      .select()
      .from(agencyServiceMatches)
      .where(eq(agencyServiceMatches.agencyId, agencyId))
      .orderBy(
        sql`case ${agencyServiceMatches.confidence} when 'high' then 1 when 'medium' then 2 when 'low' then 3 end`,
        agencyServiceMatches.providerName
      );

    return results.map(transformMatch);
  } catch (error) {
    console.error('Error fetching agency matches:', error);
    return [];
  }
}

export async function getAgencyStats(): Promise<AgencyStats> {
  try {
    const result = await db
      .select({
        total_agencies: sql<number>`count(distinct ${agencyAiUsage.id})::int`,
        agencies_with_llm: sql<number>`sum(case when ${agencyAiUsage.hasStaffLlm} like '%Yes%' then 1 else 0 end)::int`,
        agencies_with_coding: sql<number>`sum(case when ${agencyAiUsage.hasCodingAssistant} like '%Yes%' or ${agencyAiUsage.hasCodingAssistant} like '%Allowed%' then 1 else 0 end)::int`,
        agencies_custom_solution: sql<number>`sum(case when ${agencyAiUsage.solutionType} like '%Custom%' then 1 else 0 end)::int`,
        agencies_commercial_solution: sql<number>`sum(case when ${agencyAiUsage.solutionType} like '%Commercial%' or ${agencyAiUsage.solutionType} like '%Azure%' or ${agencyAiUsage.solutionType} like '%AWS%' then 1 else 0 end)::int`,
      })
      .from(agencyAiUsage)
      .where(eq(agencyAiUsage.agencyCategory, 'staff_llm'));

    // Get match stats separately
    const matchStats = await db
      .select({
        total_matches: sql<number>`count(*)::int`,
      })
      .from(agencyServiceMatches);

    const highConfidenceMatches = await db
      .select({
        count: sql<number>`count(*)::int`,
      })
      .from(agencyServiceMatches)
      .where(eq(agencyServiceMatches.confidence, 'high'));

    return result[0] ? {
      ...result[0],
      total_matches: matchStats[0]?.total_matches || 0,
      high_confidence_matches: highConfidenceMatches[0]?.count || 0,
    } : {
      total_agencies: 0,
      agencies_with_llm: 0,
      agencies_with_coding: 0,
      agencies_custom_solution: 0,
      agencies_commercial_solution: 0,
      total_matches: 0,
      high_confidence_matches: 0,
    };
  } catch (error) {
    console.error('Error fetching agency stats:', error);
    // Return empty stats if table doesn't exist or query fails
    return {
      total_agencies: 0,
      agencies_with_llm: 0,
      agencies_with_coding: 0,
      agencies_custom_solution: 0,
      agencies_commercial_solution: 0,
      total_matches: 0,
      high_confidence_matches: 0,
    };
  }
}

export async function searchAgencies(query: string): Promise<AgencyAIUsage[]> {
  try {
    const searchTerm = `%${query}%`;

    const results = await db
      .select()
      .from(agencyAiUsage)
      .where(
        or(
          ilike(agencyAiUsage.agencyName, searchTerm),
          ilike(agencyAiUsage.llmName, searchTerm),
          ilike(agencyAiUsage.solutionType, searchTerm),
          ilike(agencyAiUsage.toolName, searchTerm),
          ilike(agencyAiUsage.notes, searchTerm)
        )
      )
      .orderBy(agencyAiUsage.agencyName);

    return results.map(transformAgency);
  } catch (error) {
    console.error('Error searching agencies:', error);
    return [];
  }
}
