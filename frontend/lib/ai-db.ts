import { db } from './db/client';
import { aiServiceAnalysis } from './db/schema';
import { eq, or, sql } from 'drizzle-orm';
import type { AIService as AIServiceType } from './db/schema';

export interface AIService {
  id: number;
  product_id: string;
  product_name: string;
  provider_name: string;
  service_name: string;
  has_ai: boolean;
  has_genai: boolean;
  has_llm: boolean;
  relevant_excerpt: string | null;
  fedramp_status: string | null;
  impact_level: string | null;
  agencies: string | null;
  auth_date: string | null;
  analyzed_at: Date;
}

export interface AIStats {
  total_ai_services: number;
  count_ai: number;
  count_genai: number;
  count_llm: number;
  products_with_ai: number;
  providers_with_ai: number;
}

function transformAIService(result: AIServiceType): AIService {
  return {
    id: result.id,
    product_id: result.productId,
    product_name: result.productName,
    provider_name: result.providerName,
    service_name: result.serviceName,
    has_ai: result.hasAi,
    has_genai: result.hasGenai,
    has_llm: result.hasLlm,
    relevant_excerpt: result.relevantExcerpt,
    fedramp_status: result.fedrampStatus,
    impact_level: result.impactLevel,
    agencies: result.agencies,
    auth_date: result.authDate,
    analyzed_at: result.analyzedAt,
  };
}

export async function getAIServices(filterType?: 'ai' | 'genai' | 'llm'): Promise<AIService[]> {
  try {
    let condition;

    if (filterType === 'ai') {
      condition = eq(aiServiceAnalysis.hasAi, true);
    } else if (filterType === 'genai') {
      condition = eq(aiServiceAnalysis.hasGenai, true);
    } else if (filterType === 'llm') {
      condition = eq(aiServiceAnalysis.hasLlm, true);
    } else {
      condition = or(
        eq(aiServiceAnalysis.hasAi, true),
        eq(aiServiceAnalysis.hasGenai, true),
        eq(aiServiceAnalysis.hasLlm, true)
      );
    }

    const results = await db
      .select()
      .from(aiServiceAnalysis)
      .where(condition)
      .orderBy(aiServiceAnalysis.providerName, aiServiceAnalysis.productName, aiServiceAnalysis.serviceName);

    return results.map(transformAIService);
  } catch (error) {
    console.error('Error fetching AI services:', error);
    return [];
  }
}

export async function getAIStats(): Promise<AIStats> {
  try {
    const result = await db
      .select({
        total_ai_services: sql<number>`count(*)::int`,
        count_ai: sql<number>`sum(case when ${aiServiceAnalysis.hasAi} then 1 else 0 end)::int`,
        count_genai: sql<number>`sum(case when ${aiServiceAnalysis.hasGenai} then 1 else 0 end)::int`,
        count_llm: sql<number>`sum(case when ${aiServiceAnalysis.hasLlm} then 1 else 0 end)::int`,
        products_with_ai: sql<number>`count(distinct ${aiServiceAnalysis.productId})::int`,
        providers_with_ai: sql<number>`count(distinct ${aiServiceAnalysis.providerName})::int`,
      })
      .from(aiServiceAnalysis)
      .where(
        or(
          eq(aiServiceAnalysis.hasAi, true),
          eq(aiServiceAnalysis.hasGenai, true),
          eq(aiServiceAnalysis.hasLlm, true)
        )
      );

    return result[0] || {
      total_ai_services: 0,
      count_ai: 0,
      count_genai: 0,
      count_llm: 0,
      products_with_ai: 0,
      providers_with_ai: 0,
    };
  } catch (error) {
    console.error('Error fetching AI stats:', error);
    // Return empty stats if table doesn't exist or query fails
    return {
      total_ai_services: 0,
      count_ai: 0,
      count_genai: 0,
      count_llm: 0,
      products_with_ai: 0,
      providers_with_ai: 0,
    };
  }
}
