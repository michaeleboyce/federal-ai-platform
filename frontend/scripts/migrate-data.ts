/**
 * Migrate data from SQLite to Neon PostgreSQL
 *
 * This script reads all use case data from the SQLite database and migrates it
 * to Neon PostgreSQL using Drizzle ORM, transforming data types as needed.
 */

import dotenv from 'dotenv';
import path from 'path';

// Load environment variables FIRST before any other imports
dotenv.config({ path: '.env.local' });

import Database from 'better-sqlite3';
import { db } from '../lib/db/client';
import { aiUseCases, aiUseCaseDetails, agencyAiUsage, aiServiceAnalysis, agencyServiceMatches } from '../lib/db/schema';

const SQLITE_DB_PATH = path.join(process.cwd(), '..', '..', 'fedramp', 'data', 'fedramp.db');

interface SQLiteUseCase {
  id: number;
  use_case_name: string;
  agency: string;
  agency_abbreviation: string | null;
  bureau: string | null;
  use_case_topic_area: string | null;
  other_use_case_topic_area: string | null;
  intended_purpose: string | null;
  outputs: string | null;
  stage_of_development: string | null;
  is_rights_safety_impacting: string | null;
  domain_category: string | null;
  date_initiated: string | null;
  date_implemented: string | null;
  date_retired: string | null;
  has_llm: number;
  has_genai: number;
  has_chatbot: number;
  has_gp_markers: number;
  has_coding_assistant: number;
  has_coding_agent: number;
  has_classic_ml: number;
  has_rpa: number;
  has_rules: number;
  general_purpose_chatbot: number;
  domain_chatbot: number;
  coding_assistant: number;
  coding_agent: number;
  genai_flag: number;
  ai_type_classic_ml: number;
  ai_type_rpa_rules: number;
  providers_detected: string;
  commercial_ai_product: string | null;
  analyzed_at: string;
  slug: string;
}

interface SQLiteUseCaseDetails {
  use_case_id: number;
  development_approach: string | null;
  procurement_instrument: string | null;
  supports_hisp: string | null;
  which_hisp: string | null;
  which_public_service: string | null;
  disseminates_to_public: string | null;
  involves_pii: string | null;
  privacy_assessed: string | null;
  has_data_catalog: string | null;
  agency_owned_data: string | null;
  data_documentation: string | null;
  demographic_variables: string | null;
  has_custom_code: string | null;
  has_code_access: string | null;
  code_link: string | null;
  has_ato: string | null;
  system_name: string | null;
  wait_time_dev_tools: string | null;
  centralized_intake: string | null;
  has_compute_process: string | null;
  timely_communication: string | null;
  infrastructure_reuse: string | null;
  internal_review: string | null;
  requested_extension: string | null;
  impact_assessment: string | null;
  operational_testing: string | null;
  key_risks: string | null;
  independent_evaluation: string | null;
  performance_monitoring: string | null;
  autonomous_decision: string | null;
  public_notice: string | null;
  influences_decisions: string | null;
  disparity_mitigation: string | null;
  stakeholder_feedback: string | null;
  fallback_process: string | null;
  opt_out_mechanism: string | null;
  info_quality_compliance: string | null;
  search_text: string | null;
}

interface SQLiteAgencyAiUsage {
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
  analyzed_at: string;
  slug: string;
}

interface SQLiteAiServiceAnalysis {
  id: number;
  product_id: string;
  product_name: string | null;
  provider_name: string | null;
  service_name: string | null;
  has_ai: number;
  has_genai: number;
  has_llm: number;
  relevant_excerpt: string | null;
  fedramp_status: string | null;
  impact_level: string | null;
  agencies: string | null;
  auth_date: string | null;
  analyzed_at: string;
}

interface SQLiteAgencyServiceMatch {
  id: number;
  agency_id: number;
  product_id: string;
  provider_name: string;
  product_name: string;
  confidence: string;
  match_reason: string | null;
  created_at: string;
}

/**
 * Convert SQLite integer boolean to JavaScript boolean
 */
function convertBoolean(value: number | null): boolean {
  return value === 1;
}

/**
 * Parse JSON string from SQLite to array
 */
function parseProviders(value: string | null): string[] {
  if (!value || value === '[]') return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

/**
 * Migrate ai_use_cases table
 */
async function migrateUseCases(sqlite: Database.Database): Promise<number> {
  console.log('\n📦 Migrating ai_use_cases table...');

  // Check if already migrated
  const existing = await db.select().from(aiUseCases);
  if (existing.length > 0) {
    console.log(`   ⚠️  Table already has ${existing.length} records, skipping migration`);
    return existing.length;
  }

  const rows = sqlite.prepare('SELECT * FROM ai_use_cases ORDER BY id').all() as SQLiteUseCase[];
  console.log(`   Found ${rows.length} records in SQLite`);

  let migrated = 0;
  const batchSize = 100;

  for (let i = 0; i < rows.length; i += batchSize) {
    const batch = rows.slice(i, i + batchSize);

    const values = batch.map((row) => ({
      useCaseName: row.use_case_name,
      agency: row.agency,
      agencyAbbreviation: row.agency_abbreviation,
      bureau: row.bureau,
      useCaseTopicArea: row.use_case_topic_area,
      otherUseCaseTopicArea: row.other_use_case_topic_area,
      intendedPurpose: row.intended_purpose,
      outputs: row.outputs,
      stageOfDevelopment: row.stage_of_development,
      isRightsSafetyImpacting: row.is_rights_safety_impacting,
      domainCategory: row.domain_category,
      dateInitiated: row.date_initiated,
      dateImplemented: row.date_implemented,
      dateRetired: row.date_retired,
      hasLlm: convertBoolean(row.has_llm),
      hasGenai: convertBoolean(row.has_genai),
      hasChatbot: convertBoolean(row.has_chatbot),
      hasGpMarkers: convertBoolean(row.has_gp_markers),
      hasCodingAssistant: convertBoolean(row.has_coding_assistant),
      hasCodingAgent: convertBoolean(row.has_coding_agent),
      hasClassicMl: convertBoolean(row.has_classic_ml),
      hasRpa: convertBoolean(row.has_rpa),
      hasRules: convertBoolean(row.has_rules),
      generalPurposeChatbot: convertBoolean(row.general_purpose_chatbot),
      domainChatbot: convertBoolean(row.domain_chatbot),
      codingAssistant: convertBoolean(row.coding_assistant),
      codingAgent: convertBoolean(row.coding_agent),
      genaiFlag: convertBoolean(row.genai_flag),
      aiTypeClassicMl: convertBoolean(row.ai_type_classic_ml),
      aiTypeRpaRules: convertBoolean(row.ai_type_rpa_rules),
      providersDetected: parseProviders(row.providers_detected),
      commercialAiProduct: row.commercial_ai_product,
      analyzedAt: new Date(row.analyzed_at),
      slug: row.slug,
    }));

    await db.insert(aiUseCases).values(values);
    migrated += batch.length;

    if (migrated % 500 === 0 || migrated === rows.length) {
      console.log(`   Migrated ${migrated}/${rows.length} records...`);
    }
  }

  console.log(`   ✅ Successfully migrated ${migrated} records`);
  return migrated;
}

/**
 * Migrate ai_use_case_details table
 */
async function migrateUseCaseDetails(sqlite: Database.Database): Promise<number> {
  console.log('\n📦 Migrating ai_use_case_details table...');

  // Check if already migrated
  const existing = await db.select().from(aiUseCaseDetails);
  if (existing.length > 0) {
    console.log(`   ⚠️  Table already has ${existing.length} records, skipping migration`);
    return existing.length;
  }

  const rows = sqlite.prepare('SELECT * FROM ai_use_case_details ORDER BY use_case_id').all() as SQLiteUseCaseDetails[];
  console.log(`   Found ${rows.length} records in SQLite`);

  if (rows.length === 0) {
    console.log('   ⚠️  No records to migrate');
    return 0;
  }

  let migrated = 0;
  const batchSize = 100;

  for (let i = 0; i < rows.length; i += batchSize) {
    const batch = rows.slice(i, i + batchSize);

    const values = batch.map((row) => ({
      useCaseId: row.use_case_id,
      developmentApproach: row.development_approach,
      procurementInstrument: row.procurement_instrument,
      supportsHisp: row.supports_hisp,
      whichHisp: row.which_hisp,
      whichPublicService: row.which_public_service,
      disseminatesToPublic: row.disseminates_to_public,
      involvesPii: row.involves_pii,
      privacyAssessed: row.privacy_assessed,
      hasDataCatalog: row.has_data_catalog,
      agencyOwnedData: row.agency_owned_data,
      dataDocumentation: row.data_documentation,
      demographicVariables: row.demographic_variables,
      hasCustomCode: row.has_custom_code,
      hasCodeAccess: row.has_code_access,
      codeLink: row.code_link,
      hasAto: row.has_ato,
      systemName: row.system_name,
      waitTimeDevTools: row.wait_time_dev_tools,
      centralizedIntake: row.centralized_intake,
      hasComputeProcess: row.has_compute_process,
      timelyCommunication: row.timely_communication,
      infrastructureReuse: row.infrastructure_reuse,
      internalReview: row.internal_review,
      requestedExtension: row.requested_extension,
      impactAssessment: row.impact_assessment,
      operationalTesting: row.operational_testing,
      keyRisks: row.key_risks,
      independentEvaluation: row.independent_evaluation,
      performanceMonitoring: row.performance_monitoring,
      autonomousDecision: row.autonomous_decision,
      publicNotice: row.public_notice,
      influencesDecisions: row.influences_decisions,
      disparityMitigation: row.disparity_mitigation,
      stakeholderFeedback: row.stakeholder_feedback,
      fallbackProcess: row.fallback_process,
      optOutMechanism: row.opt_out_mechanism,
      infoQualityCompliance: row.info_quality_compliance,
      searchText: row.search_text,
    }));

    await db.insert(aiUseCaseDetails).values(values);
    migrated += batch.length;

    if (migrated % 500 === 0 || migrated === rows.length) {
      console.log(`   Migrated ${migrated}/${rows.length} records...`);
    }
  }

  console.log(`   ✅ Successfully migrated ${migrated} records`);
  return migrated;
}

/**
 * Migrate agency_ai_usage table
 */
async function migrateAgencyAiUsage(sqlite: Database.Database): Promise<number> {
  console.log('\n📦 Migrating agency_ai_usage table...');

  // Check if already migrated
  const existing = await db.select().from(agencyAiUsage);
  if (existing.length > 0) {
    console.log(`   ⚠️  Table already has ${existing.length} records, skipping migration`);
    return existing.length;
  }

  const rows = sqlite.prepare('SELECT * FROM agency_ai_usage ORDER BY id').all() as SQLiteAgencyAiUsage[];
  console.log(`   Found ${rows.length} records in SQLite`);

  if (rows.length === 0) {
    console.log('   ⚠️  No records to migrate');
    return 0;
  }

  let migrated = 0;
  const batchSize = 100;

  for (let i = 0; i < rows.length; i += batchSize) {
    const batch = rows.slice(i, i + batchSize);

    const values = batch.map((row) => ({
      agencyName: row.agency_name,
      agencyCategory: row.agency_category,
      hasStaffLlm: row.has_staff_llm,
      llmName: row.llm_name,
      hasCodingAssistant: row.has_coding_assistant,
      scope: row.scope,
      solutionType: row.solution_type,
      nonPublicAllowed: row.non_public_allowed,
      otherAiPresent: row.other_ai_present,
      toolName: row.tool_name,
      toolPurpose: row.tool_purpose,
      notes: row.notes,
      sources: row.sources,
      analyzedAt: new Date(row.analyzed_at),
      slug: row.slug,
    }));

    await db.insert(agencyAiUsage).values(values);
    migrated += batch.length;
    console.log(`   Migrated ${migrated}/${rows.length} records...`);
  }

  console.log(`   ✅ Successfully migrated ${migrated} records`);
  return migrated;
}

/**
 * Migrate ai_service_analysis table
 */
async function migrateAiServiceAnalysis(sqlite: Database.Database): Promise<number> {
  console.log('\n📦 Migrating ai_service_analysis table...');

  // Check if already migrated
  const existing = await db.select().from(aiServiceAnalysis);
  if (existing.length > 0) {
    console.log(`   ⚠️  Table already has ${existing.length} records, skipping migration`);
    return existing.length;
  }

  const rows = sqlite.prepare('SELECT * FROM ai_service_analysis ORDER BY id').all() as SQLiteAiServiceAnalysis[];
  console.log(`   Found ${rows.length} records in SQLite`);

  if (rows.length === 0) {
    console.log('   ⚠️  No records to migrate');
    return 0;
  }

  let migrated = 0;
  const batchSize = 100;

  for (let i = 0; i < rows.length; i += batchSize) {
    const batch = rows.slice(i, i + batchSize);

    const values = batch.map((row) => ({
      productId: row.product_id,
      productName: row.product_name || '',
      providerName: row.provider_name || '',
      serviceName: row.service_name || '',
      hasAi: convertBoolean(row.has_ai),
      hasGenai: convertBoolean(row.has_genai),
      hasLlm: convertBoolean(row.has_llm),
      relevantExcerpt: row.relevant_excerpt,
      fedrampStatus: row.fedramp_status,
      impactLevel: row.impact_level,
      agencies: row.agencies,
      authDate: row.auth_date,
      analyzedAt: new Date(row.analyzed_at),
    }));

    await db.insert(aiServiceAnalysis).values(values);
    migrated += batch.length;

    if (migrated % 100 === 0 || migrated === rows.length) {
      console.log(`   Migrated ${migrated}/${rows.length} records...`);
    }
  }

  console.log(`   ✅ Successfully migrated ${migrated} records`);
  return migrated;
}

/**
 * Migrate agency_service_matches table
 */
async function migrateAgencyServiceMatches(sqlite: Database.Database): Promise<number> {
  console.log('\n📦 Migrating agency_service_matches table...');

  // Check if already migrated
  const existing = await db.select().from(agencyServiceMatches);
  if (existing.length > 0) {
    console.log(`   ⚠️  Table already has ${existing.length} records, skipping migration`);
    return existing.length;
  }

  const rows = sqlite.prepare('SELECT * FROM agency_service_matches ORDER BY id').all() as SQLiteAgencyServiceMatch[];
  console.log(`   Found ${rows.length} records in SQLite`);

  if (rows.length === 0) {
    console.log('   ⚠️  No records to migrate');
    return 0;
  }

  // Get all migrated agencies from Neon to map SQLite IDs to Neon IDs
  const neonAgencies = await db.select().from(agencyAiUsage);
  console.log(`   Found ${neonAgencies.length} agencies in Neon for ID mapping`);

  let migrated = 0;
  let skipped = 0;
  const batchSize = 100;

  for (let i = 0; i < rows.length; i += batchSize) {
    const batch = rows.slice(i, i + batchSize);

    const values = batch
      .map((row) => {
        // Find the Neon agency ID by matching the SQLite row's agency_id
        // Since we're migrating in order, agency_id should correspond to the Neon record
        const neonAgency = neonAgencies[row.agency_id - 1]; // SQLite IDs are 1-indexed

        if (!neonAgency) {
          console.log(`   ⚠️  Skipping match: agency_id ${row.agency_id} not found in Neon`);
          skipped++;
          return null;
        }

        return {
          agencyId: neonAgency.id,
          productId: row.product_id,
          providerName: row.provider_name,
          productName: row.product_name,
          confidence: row.confidence as 'high' | 'medium' | 'low',
          matchReason: row.match_reason,
          createdAt: new Date(row.created_at),
        };
      })
      .filter((v): v is NonNullable<typeof v> => v !== null);

    if (values.length > 0) {
      await db.insert(agencyServiceMatches).values(values);
      migrated += values.length;
    }

    console.log(`   Migrated ${migrated}/${rows.length} records (${skipped} skipped)...`);
  }

  console.log(`   ✅ Successfully migrated ${migrated} records (${skipped} skipped)`);
  return migrated;
}

/**
 * Verify migration
 */
async function verifyMigration(sqlite: Database.Database): Promise<boolean> {
  console.log('\n🔍 Verifying migration...');

  // Check ai_use_cases count
  const sqliteCount = sqlite.prepare('SELECT COUNT(*) as count FROM ai_use_cases').get() as { count: number };
  const neonResult = await db.select().from(aiUseCases);
  const neonCount = neonResult.length;

  console.log(`   ai_use_cases: SQLite=${sqliteCount.count}, Neon=${neonCount}`);
  if (sqliteCount.count !== neonCount) {
    console.log('   ❌ Record count mismatch!');
    return false;
  }

  // Check ai_use_case_details count
  const sqliteDetailsCount = sqlite.prepare('SELECT COUNT(*) as count FROM ai_use_case_details').get() as { count: number };
  const neonDetailsResult = await db.select().from(aiUseCaseDetails);
  const neonDetailsCount = neonDetailsResult.length;

  console.log(`   ai_use_case_details: SQLite=${sqliteDetailsCount.count}, Neon=${neonDetailsCount}`);
  if (sqliteDetailsCount.count !== neonDetailsCount) {
    console.log('   ❌ Record count mismatch!');
    return false;
  }

  // Check agency_ai_usage count
  const sqliteAgencyCount = sqlite.prepare('SELECT COUNT(*) as count FROM agency_ai_usage').get() as { count: number };
  const neonAgencyResult = await db.select().from(agencyAiUsage);
  const neonAgencyCount = neonAgencyResult.length;

  console.log(`   agency_ai_usage: SQLite=${sqliteAgencyCount.count}, Neon=${neonAgencyCount}`);
  if (sqliteAgencyCount.count !== neonAgencyCount) {
    console.log('   ❌ Record count mismatch!');
    return false;
  }

  // Check ai_service_analysis count
  const sqliteServiceCount = sqlite.prepare('SELECT COUNT(*) as count FROM ai_service_analysis').get() as { count: number };
  const neonServiceResult = await db.select().from(aiServiceAnalysis);
  const neonServiceCount = neonServiceResult.length;

  console.log(`   ai_service_analysis: SQLite=${sqliteServiceCount.count}, Neon=${neonServiceCount}`);
  if (sqliteServiceCount.count !== neonServiceCount) {
    console.log('   ❌ Record count mismatch!');
    return false;
  }

  // Check agency_service_matches count
  const sqliteMatchCount = sqlite.prepare('SELECT COUNT(*) as count FROM agency_service_matches').get() as { count: number };
  const neonMatchResult = await db.select().from(agencyServiceMatches);
  const neonMatchCount = neonMatchResult.length;

  console.log(`   agency_service_matches: SQLite=${sqliteMatchCount.count}, Neon=${neonMatchCount}`);
  if (sqliteMatchCount.count !== neonMatchCount) {
    console.log('   ❌ Record count mismatch!');
    return false;
  }

  // Sample check: verify a few slugs exist
  const sampleSlugs = sqlite.prepare('SELECT slug FROM ai_use_cases LIMIT 5').all() as Array<{ slug: string }>;

  for (const { slug } of sampleSlugs) {
    const found = neonResult.find(r => r.slug === slug);
    if (!found) {
      console.log(`   ❌ Sample record '${slug}' not found in Neon!`);
      return false;
    }
  }

  console.log('   ✅ Verification passed!');
  return true;
}

/**
 * Main migration function
 */
async function main() {
  console.log('='.repeat(80));
  console.log('🚀 Starting SQLite → Neon PostgreSQL Migration');
  console.log('='.repeat(80));

  // Connect to SQLite
  console.log(`\n📂 Connecting to SQLite: ${SQLITE_DB_PATH}`);
  const sqlite = new Database(SQLITE_DB_PATH, { readonly: true });

  try {
    // Migrate tables
    const useCasesCount = await migrateUseCases(sqlite);
    const detailsCount = await migrateUseCaseDetails(sqlite);
    const agencyCount = await migrateAgencyAiUsage(sqlite);
    const serviceCount = await migrateAiServiceAnalysis(sqlite);
    const matchCount = await migrateAgencyServiceMatches(sqlite);

    // Verify migration
    const verified = await verifyMigration(sqlite);

    if (verified) {
      console.log('\n' + '='.repeat(80));
      console.log('✅ Migration completed successfully!');
      console.log(`   • Migrated ${useCasesCount} use cases`);
      console.log(`   • Migrated ${detailsCount} detail records`);
      console.log(`   • Migrated ${agencyCount} agency AI usage records`);
      console.log(`   • Migrated ${serviceCount} AI service analysis records`);
      console.log(`   • Migrated ${matchCount} agency-service matches`);
      console.log('='.repeat(80));
      process.exit(0);
    } else {
      console.log('\n❌ Migration verification failed!');
      process.exit(1);
    }
  } catch (error) {
    console.error('\n❌ Migration failed with error:', error);
    process.exit(1);
  } finally {
    sqlite.close();
  }
}

main();
