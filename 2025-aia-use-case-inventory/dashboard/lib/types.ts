/**
 * Shared TypeScript types for the Federal AI Use Case Inventory dashboard.
 *
 * These mirror the SQLite schema in `../data/federal_ai_inventory_2025.db`.
 * All nullable DB columns are modeled as `T | null` (better-sqlite3 returns
 * `null` for SQL NULL, not `undefined`). Integer boolean flags are typed as
 * `number | null` (0/1) since SQLite has no native boolean type.
 */

// -----------------------------------------------------------------------------
// Core tables
// -----------------------------------------------------------------------------

export interface Agency {
  id: number;
  name: string;
  abbreviation: string;
  agency_type: string | null;
  inventory_page_url: string | null;
  csv_download_url: string | null;
  inventory_year: number | null;
  status: string | null;
  schema_compliance: number | null;
  notes: string | null;
  last_modified: string | null;
  date_accessed: string | null;
}

export interface Product {
  id: number;
  canonical_name: string;
  vendor: string | null;
  product_type: string | null;
  is_generative_ai: number | null;
  is_frontier_llm: number | null;
  parent_product_id: number | null;
  description: string | null;
  notes: string | null;
}

export interface ProductAlias {
  id: number;
  product_id: number;
  alias_text: string;
}

export interface UseCaseTemplate {
  id: number;
  template_text: string;
  short_name: string | null;
  capability_category: string | null;
  is_omb_standard: number | null;
  notes: string | null;
}

export interface UseCase {
  id: number;
  agency_id: number;
  source_file: string;
  slug: string | null;

  // Section 1
  use_case_id: string | null;
  use_case_name: string;
  bureau_component: string | null;
  email_address: string | null;
  withheld_from_public: string | null;
  stage_of_development: string | null;
  is_high_impact: string | null;
  justification: string | null;

  // Section 2
  topic_area: string | null;
  ai_classification: string | null;
  problem_statement: string | null;
  expected_benefits: string | null;
  system_outputs: string | null;
  operational_date: string | null;

  // Section 3
  development_type: string | null;
  vendor_name: string | null;
  has_ato: string | null;
  system_name: string | null;
  training_data_description: string | null;

  // Section 4
  federal_data_catalog_link: string | null;
  involves_pii: string | null;
  pia_link: string | null;
  demographic_variables: string | null;
  has_custom_code: string | null;
  open_source_link: string | null;

  // Section 5
  pre_deployment_testing: string | null;
  impact_assessment: string | null;
  potential_impacts: string | null;
  independent_review: string | null;
  ongoing_monitoring: string | null;
  operator_training: string | null;
  has_fail_safe: string | null;
  appeal_process: string | null;
  end_user_feedback: string | null;

  product_id: number | null;
  template_id: number | null;

  raw_json: string | null;
  created_at: string | null;
}

export interface ConsolidatedUseCase {
  id: number;
  agency_id: number;
  source_file: string;
  slug: string | null;

  ai_use_case: string;
  commercial_product: string | null;
  commercial_examples: string | null;
  agency_uses: string | null;
  estimated_licenses_users: string | null;

  product_id: number | null;
  template_id: number | null;

  raw_json: string | null;
  created_at: string | null;
}

export interface UseCaseTag {
  id: number;
  use_case_id: number | null;
  consolidated_use_case_id: number | null;

  entry_type: string | null;
  is_product_capability_entry: number | null;
  product_capability: string | null;

  is_general_llm_access: number | null;
  is_coding_tool: number | null;
  is_cots_commercial: number | null;
  tool_product_name: string | null;
  tool_vendor: string | null;

  ai_sophistication: string | null;
  is_generative_ai: number | null;
  is_frontier_model: number | null;

  deployment_scope: string | null;
  scope_detail: string | null;
  is_enterprise_wide: number | null;
  estimated_user_count: string | null;

  architecture_type: string | null;
  has_model_training: number | null;

  cots_product_name: string | null;
  cots_vendor: string | null;
  is_microsoft_copilot: number | null;
  is_openai: number | null;
  is_anthropic: number | null;
  is_google: number | null;
  is_github_copilot: number | null;
  is_aws_ai: number | null;

  use_type: string | null;
  is_public_facing: number | null;

  has_meaningful_risk_docs: number | null;
  high_impact_designation: string | null;
  deployment_environment: string | null;
  has_ato_or_fedramp: number | null;

  created_at: string | null;
}

export interface AgencyMaturity {
  id: number;
  agency_id: number;
  total_use_cases: number | null;
  total_consolidated_entries: number | null;
  distinct_products_deployed: number | null;
  generative_ai_count: number | null;
  coding_tool_count: number | null;
  general_llm_count: number | null;
  classical_ml_count: number | null;
  agentic_ai_count: number | null;
  custom_system_count: number | null;
  has_enterprise_llm: number | null;
  has_coding_assistants: number | null;
  has_agentic_ai: number | null;
  has_custom_ai: number | null;
  pct_deployed: number | null;
  pct_high_impact: number | null;
  pct_with_risk_docs: number | null;
  year_over_year_growth: number | null;
  maturity_tier: string | null;
  notes: string | null;
  updated_at: string | null;
}

// -----------------------------------------------------------------------------
// Joined / aggregate types used by query helpers
// -----------------------------------------------------------------------------

export interface AgencyWithMaturity extends Agency {
  maturity: AgencyMaturity | null;
}

export interface UseCaseWithTags extends UseCase {
  tags: UseCaseTag | null;
  agency_name?: string;
  agency_abbreviation?: string;
  product_name?: string | null;
  template_short_name?: string | null;
}

export interface ConsolidatedWithTags extends ConsolidatedUseCase {
  tags: UseCaseTag | null;
  agency_name?: string;
  agency_abbreviation?: string;
}

export interface ProductWithCounts extends Product {
  use_case_count: number;
  agency_count: number;
}

export interface ProductDetail extends Product {
  aliases: string[];
  agencies: Array<{ id: number; name: string; abbreviation: string; count: number }>;
  use_case_count: number;
}

export interface TemplateWithCounts extends UseCaseTemplate {
  use_case_count: number;
  agency_count: number;
}

export interface TemplateDetail extends UseCaseTemplate {
  agencies: Array<{ id: number; name: string; abbreviation: string; count: number }>;
  products: Array<{ id: number; canonical_name: string; vendor: string | null; count: number }>;
  use_case_count: number;
}

export interface GlobalStats {
  total_use_cases: number;
  total_consolidated: number;
  total_agencies: number;
  total_agencies_with_data: number;
  total_products: number;
  total_templates: number;
  total_coding_entries: number;
  total_genai_entries: number;
}

export interface BreakdownRow {
  label: string;
  count: number;
}

export interface BureauBreakdown extends BreakdownRow {
  bureau_component: string | null;
}

export interface YoYRow {
  agency_id: number;
  name: string;
  abbreviation: string;
  year_over_year_growth: number | null;
  total_use_cases: number | null;
}

export interface VendorShareRow {
  vendor: string;
  product_count: number;
  use_case_count: number;
  agency_count: number;
}

export interface HeatmapCell {
  product_id: number;
  product_name: string;
  agency_id: number;
  agency_abbreviation: string;
  count: number;
}

export interface UseCaseFilterInput {
  agencyId?: number;
  agencyAbbr?: string;
  stage?: string;
  aiClassification?: string;
  isHighImpact?: string;
  productId?: number;
  templateId?: number;
  vendor?: string;
  search?: string;
  entryType?: string;
  deploymentScope?: string;
  aiSophistication?: string;
  isCodingTool?: boolean;
  isGenAI?: boolean;
  limit?: number;
  offset?: number;

  // Multi-value filters (appended by Agent 4 — explorer page).
  // All are OR within the list, AND across different filter fields.
  agencyIds?: number[];
  agencyTypes?: string[]; // CFO_ACT | INDEPENDENT | LEGISLATIVE
  entryTypes?: string[];
  deploymentScopes?: string[];
  aiSophistications?: string[];
  architectureTypes?: string[];
  useTypes?: string[];
  highImpactDesignations?: string[]; // tags.high_impact_designation
  productIds?: number[];
  isGeneralLLMAccess?: boolean;
  isPublicFacing?: boolean;
  hasATOorFedRAMP?: boolean;
  hasMeaningfulRiskDocs?: boolean;
}
