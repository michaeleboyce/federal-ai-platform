import Database from 'better-sqlite3';
import path from 'path';

// Core use case record from main table
export interface UseCase {
  id: number;
  use_case_name: string;
  agency: string;
  agency_abbreviation: string | null;
  bureau: string | null;
  use_case_topic_area: string | null;
  other_use_case_topic_area: string | null;

  // Purpose and outputs
  intended_purpose: string | null;
  outputs: string | null;

  // Classification
  stage_of_development: string | null;
  is_rights_safety_impacting: string | null;
  domain_category: string | null;

  // Dates
  date_initiated: string | null;
  date_implemented: string | null;
  date_retired: string | null;

  // AI Type Flags
  has_llm: number;
  has_genai: number;
  has_chatbot: number;
  has_gp_markers: number;
  has_coding_assistant: number;
  has_coding_agent: number;
  has_classic_ml: number;
  has_rpa: number;
  has_rules: number;

  // AI Type Categories
  general_purpose_chatbot: number;
  domain_chatbot: number;
  coding_assistant: number;
  coding_agent: number;
  genai_flag: number;
  ai_type_classic_ml: number;
  ai_type_rpa_rules: number;

  // Providers
  providers_detected: string; // JSON array
  commercial_ai_product: string | null;

  // Metadata
  analyzed_at: string;
  slug: string;
}

// Extended details record
export interface UseCaseDetails {
  use_case_id: number;

  // Development and procurement
  development_approach: string | null;
  procurement_instrument: string | null;

  // High-impact service
  supports_hisp: string | null;
  which_hisp: string | null;
  which_public_service: string | null;
  disseminates_to_public: string | null;

  // Privacy and data
  involves_pii: string | null;
  privacy_assessed: string | null;
  has_data_catalog: string | null;
  agency_owned_data: string | null;
  data_documentation: string | null;
  demographic_variables: string | null;

  // Code and systems
  has_custom_code: string | null;
  has_code_access: string | null;
  code_link: string | null;
  has_ato: string | null;
  system_name: string | null;

  // Infrastructure
  wait_time_dev_tools: string | null;
  centralized_intake: string | null;
  has_compute_process: string | null;
  timely_communication: string | null;
  infrastructure_reuse: string | null;

  // Review and testing
  internal_review: string | null;
  requested_extension: string | null;
  impact_assessment: string | null;
  operational_testing: string | null;
  key_risks: string | null;
  independent_evaluation: string | null;

  // Monitoring and governance
  performance_monitoring: string | null;
  autonomous_decision: string | null;
  public_notice: string | null;
  influences_decisions: string | null;
  disparity_mitigation: string | null;
  stakeholder_feedback: string | null;
  fallback_process: string | null;
  opt_out_mechanism: string | null;

  // Information quality
  info_quality_compliance: string | null;

  // Full search text
  search_text: string | null;
}

// Combined use case with details
export interface UseCaseWithDetails extends UseCase {
  details?: UseCaseDetails;
}

// FedRAMP service match
export interface UseCaseFedRAMPMatch {
  product_id: string;
  provider_name: string;
  product_name: string;
  confidence: 'high' | 'medium' | 'low';
  match_reason: string | null;
}

// Statistics
export interface UseCaseStats {
  total_use_cases: number;
  total_agencies: number;
  genai_count: number;
  llm_count: number;
  chatbot_count: number;
  classic_ml_count: number;
  coding_assistant_count: number;
  rights_impacting_count: number;
  implemented_count: number;
  in_development_count: number;
}

// Domain statistics
export interface DomainStats {
  domain_category: string;
  count: number;
  genai_count: number;
}

// Agency statistics
export interface AgencyUseCaseStats {
  agency: string;
  total_count: number;
  genai_count: number;
  llm_count: number;
  chatbot_count: number;
  classic_ml_count: number;
}

// Filter options
export interface UseCaseFilters {
  agency?: string;
  agency_abbreviation?: string;
  bureau?: string;
  domain?: string;
  stage?: string;
  aiType?: 'genai' | 'llm' | 'chatbot' | 'classic_ml' | 'coding' | 'rpa';
  provider?: string;
  topic_area?: string;
  rights_impacting?: boolean;
  search?: string;
}

const DB_PATH = path.join(process.cwd(), '..', 'data', 'fedramp.db');

/**
 * Get all use cases with optional filtering
 */
export function getUseCases(filters?: UseCaseFilters): UseCase[] {
  const db = new Database(DB_PATH, { readonly: true });

  let query = 'SELECT * FROM ai_use_cases WHERE 1=1';
  const params: any[] = [];

  if (filters) {
    if (filters.agency) {
      query += ' AND LOWER(agency) LIKE ?';
      params.push(`%${filters.agency.toLowerCase()}%`);
    }

    if (filters.agency_abbreviation) {
      query += ' AND LOWER(agency_abbreviation) = ?';
      params.push(filters.agency_abbreviation.toLowerCase());
    }

    if (filters.bureau) {
      query += ' AND LOWER(bureau) LIKE ?';
      params.push(`%${filters.bureau.toLowerCase()}%`);
    }

    if (filters.domain) {
      query += ' AND domain_category = ?';
      params.push(filters.domain);
    }

    if (filters.stage) {
      query += ' AND stage_of_development = ?';
      params.push(filters.stage);
    }

    if (filters.topic_area) {
      query += ' AND use_case_topic_area = ?';
      params.push(filters.topic_area);
    }

    if (filters.aiType) {
      switch (filters.aiType) {
        case 'genai':
          query += ' AND genai_flag = 1';
          break;
        case 'llm':
          query += ' AND has_llm = 1';
          break;
        case 'chatbot':
          query += ' AND has_chatbot = 1';
          break;
        case 'classic_ml':
          query += ' AND has_classic_ml = 1';
          break;
        case 'coding':
          query += ' AND (has_coding_assistant = 1 OR has_coding_agent = 1)';
          break;
        case 'rpa':
          query += ' AND has_rpa = 1';
          break;
      }
    }

    if (filters.provider) {
      query += ' AND providers_detected LIKE ?';
      params.push(`%${filters.provider}%`);
    }

    if (filters.rights_impacting !== undefined) {
      if (filters.rights_impacting) {
        query += ' AND (is_rights_safety_impacting LIKE "%Rights%" OR is_rights_safety_impacting LIKE "%Both%")';
      } else {
        query += ' AND (is_rights_safety_impacting LIKE "%Neither%" OR is_rights_safety_impacting IS NULL)';
      }
    }

    if (filters.search) {
      query += ` AND (
        LOWER(use_case_name) LIKE ? OR
        LOWER(agency) LIKE ? OR
        LOWER(bureau) LIKE ? OR
        LOWER(intended_purpose) LIKE ? OR
        LOWER(outputs) LIKE ?
      )`;
      const searchTerm = `%${filters.search.toLowerCase()}%`;
      params.push(searchTerm, searchTerm, searchTerm, searchTerm, searchTerm);
    }
  }

  query += ' ORDER BY agency, use_case_name';

  const useCases = db.prepare(query).all(...params) as UseCase[];
  db.close();

  return useCases;
}

/**
 * Get a single use case by slug with full details
 */
export function getUseCaseBySlug(slug: string): UseCaseWithDetails | null {
  const db = new Database(DB_PATH, { readonly: true });

  const useCase = db.prepare('SELECT * FROM ai_use_cases WHERE slug = ?').get(slug) as UseCase | undefined;

  if (!useCase) {
    db.close();
    return null;
  }

  const details = db.prepare('SELECT * FROM ai_use_case_details WHERE use_case_id = ?').get(useCase.id) as UseCaseDetails | undefined;

  db.close();

  return {
    ...useCase,
    details
  };
}

/**
 * Get all use cases for a specific agency
 */
export function getUseCasesByAgency(agencyAbbr: string): UseCase[] {
  return getUseCases({ agency_abbreviation: agencyAbbr });
}

/**
 * Get all use cases in a specific domain
 */
export function getUseCasesByDomain(domain: string): UseCase[] {
  return getUseCases({ domain });
}

/**
 * Get all use cases mentioning a specific provider
 */
export function getUseCasesByProvider(provider: string): UseCase[] {
  return getUseCases({ provider });
}

/**
 * Get aggregate statistics
 */
export function getUseCaseStats(): UseCaseStats {
  const db = new Database(DB_PATH, { readonly: true });

  const stats = db.prepare(`
    SELECT
      COUNT(*) as total_use_cases,
      COUNT(DISTINCT agency) as total_agencies,
      SUM(genai_flag) as genai_count,
      SUM(has_llm) as llm_count,
      SUM(has_chatbot) as chatbot_count,
      SUM(has_classic_ml) as classic_ml_count,
      SUM(CASE WHEN has_coding_assistant = 1 OR has_coding_agent = 1 THEN 1 ELSE 0 END) as coding_assistant_count,
      SUM(CASE WHEN is_rights_safety_impacting LIKE '%Rights%' OR is_rights_safety_impacting LIKE '%Both%' THEN 1 ELSE 0 END) as rights_impacting_count,
      SUM(CASE WHEN date_implemented IS NOT NULL AND date_implemented != '' THEN 1 ELSE 0 END) as implemented_count,
      SUM(CASE WHEN stage_of_development LIKE '%Development%' OR stage_of_development LIKE '%Acquisition%' THEN 1 ELSE 0 END) as in_development_count
    FROM ai_use_cases
  `).get() as UseCaseStats;

  db.close();
  return stats;
}

/**
 * Get domain distribution statistics
 */
export function getDomainStats(): DomainStats[] {
  const db = new Database(DB_PATH, { readonly: true });

  const stats = db.prepare(`
    SELECT
      domain_category,
      COUNT(*) as count,
      SUM(genai_flag) as genai_count
    FROM ai_use_cases
    WHERE domain_category IS NOT NULL AND domain_category != ''
    GROUP BY domain_category
    ORDER BY count DESC
  `).all() as DomainStats[];

  db.close();
  return stats;
}

/**
 * Get use case statistics by agency
 */
export function getAgencyUseCaseStats(agency?: string): AgencyUseCaseStats[] {
  const db = new Database(DB_PATH, { readonly: true });

  let query = `
    SELECT
      agency,
      COUNT(*) as total_count,
      SUM(genai_flag) as genai_count,
      SUM(has_llm) as llm_count,
      SUM(has_chatbot) as chatbot_count,
      SUM(has_classic_ml) as classic_ml_count
    FROM ai_use_cases
  `;

  if (agency) {
    query += ' WHERE agency = ?';
  }

  query += ' GROUP BY agency ORDER BY total_count DESC';

  const stats = agency
    ? db.prepare(query).all(agency) as AgencyUseCaseStats[]
    : db.prepare(query).all() as AgencyUseCaseStats[];

  db.close();
  return stats;
}

/**
 * Get FedRAMP service matches for a use case
 */
export function getUseCaseFedRAMPMatches(useCaseId: number): UseCaseFedRAMPMatch[] {
  const db = new Database(DB_PATH, { readonly: true });

  const matches = db.prepare(`
    SELECT product_id, provider_name, product_name, confidence, match_reason
    FROM use_case_fedramp_matches
    WHERE use_case_id = ?
    ORDER BY
      CASE confidence
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        WHEN 'low' THEN 3
      END,
      provider_name
  `).all(useCaseId) as UseCaseFedRAMPMatch[];

  db.close();
  return matches;
}

/**
 * Get all unique values for a field (for filter dropdowns)
 */
export function getUniqueValues(field: 'domain_category' | 'stage_of_development' | 'use_case_topic_area' | 'agency'): string[] {
  const db = new Database(DB_PATH, { readonly: true });

  const values = db.prepare(`
    SELECT DISTINCT ${field}
    FROM ai_use_cases
    WHERE ${field} IS NOT NULL AND ${field} != ''
    ORDER BY ${field}
  `).all() as Array<Record<string, string>>;

  db.close();

  return values.map(v => v[field]);
}

/**
 * Get recent use cases (by implementation date)
 */
export function getRecentUseCases(limit: number = 10): UseCase[] {
  const db = new Database(DB_PATH, { readonly: true });

  const useCases = db.prepare(`
    SELECT * FROM ai_use_cases
    WHERE date_implemented IS NOT NULL AND date_implemented != ''
    ORDER BY date_implemented DESC
    LIMIT ?
  `).all(limit) as UseCase[];

  db.close();
  return useCases;
}

/**
 * Search use cases with full-text search
 */
export function searchUseCases(query: string): UseCase[] {
  return getUseCases({ search: query });
}

/**
 * Get count of use cases by provider
 */
export function getProviderUseCaseCounts(): Array<{ provider: string; count: number }> {
  const db = new Database(DB_PATH, { readonly: true });

  // Get all use cases with providers
  const useCases = db.prepare(`
    SELECT providers_detected
    FROM ai_use_cases
    WHERE providers_detected IS NOT NULL AND providers_detected != '[]'
  `).all() as Array<{ providers_detected: string }>;

  db.close();

  // Count provider mentions
  const providerCounts: Record<string, number> = {};

  useCases.forEach(uc => {
    try {
      const providers = JSON.parse(uc.providers_detected) as string[];
      providers.forEach(provider => {
        providerCounts[provider] = (providerCounts[provider] || 0) + 1;
      });
    } catch (e) {
      // Skip invalid JSON
    }
  });

  // Convert to array and sort
  return Object.entries(providerCounts)
    .map(([provider, count]) => ({ provider, count }))
    .sort((a, b) => b.count - a.count);
}
