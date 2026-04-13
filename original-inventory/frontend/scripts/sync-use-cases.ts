/**
 * Sync AI use cases from CSV to PostgreSQL
 *
 * This script:
 * 1. Reads the enriched CSV file with AI type tags
 * 2. Compares with existing database records (by use_case_name + agency)
 * 3. Adds missing records
 * 4. Updates AI type flags on existing records if different
 */

import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { parse } from 'csv-parse/sync';

// Load environment variables FIRST
dotenv.config({ path: '.env.local' });

import { db } from '../lib/db/client';
import { aiUseCases } from '../lib/db/schema';
import { eq, and } from 'drizzle-orm';

const CSV_PATH = '/Users/michaelboyce/Downloads/ai_inventory_enriched_with_tags.csv';

interface CSVRecord {
  use_case_name: string;
  agency: string;
  agency_abbreviation: string;
  bureau: string;
  use_case_topic_area: string;
  other_use_case_topic_area: string;
  is_the_ai_use_case_found_in_the_below_list_of_general_commercial_ai_products_and_services: string;
  what_is_the_intended_purpose_and_expected_benefits_of_the_ai: string;
  describe_the_ai_system_s_outputs: string;
  stage_of_development: string;
  is_the_ai_use_case_rights_impacting_safety_impacting_both_or_neither: string;
  date_initiated: string;
  date_when_acquisition_and_or_development_began: string;
  date_implemented: string;
  date_retired: string;
  // ... many more fields in between ...
  _search_text: string;
  _has_llm: string;
  _has_genai_signal: string;
  _has_chatbot: string;
  _has_gp_markers: string;
  _in_coding_context: string;
  _has_coding_assistant: string;
  _has_coding_agent: string;
  _has_classic_ml: string;
  _has_rpa: string;
  _has_rules: string;
  _general_purpose_chatbot: string;
  _domain_chatbot: string;
  _coding_assistant: string;
  _coding_agent: string;
  _genai_flag: string;
  _ai_type_classic_ml: string;
  _ai_type_rpa_rules: string;
  _domain_category: string;
  _providers_detected: string;
}

/**
 * Parse boolean from CSV string
 */
function parseBoolean(value: string | undefined): boolean {
  if (!value) return false;
  const v = value.toLowerCase().trim();
  return v === 'true' || v === '1' || v === 'yes';
}

/**
 * Parse providers array from CSV string
 */
function parseProviders(value: string | undefined): string[] {
  if (!value || value.trim() === '' || value === '[]') return [];
  try {
    // Handle Python-style list strings like "['meta', 'openai']"
    let normalized = value.trim();
    if (normalized.startsWith('[') && normalized.endsWith(']')) {
      // Replace single quotes with double quotes for JSON parsing
      normalized = normalized.replace(/'/g, '"');
      const parsed = JSON.parse(normalized);
      return Array.isArray(parsed) ? parsed.filter(p => typeof p === 'string' && p.length > 0) : [];
    }
    return [];
  } catch {
    return [];
  }
}

/**
 * Generate a unique slug from use case name and agency
 */
function generateSlug(name: string, agency: string): string {
  const base = `${name}-${agency}`
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .substring(0, 100);
  return `${base}-${Date.now()}`;
}

/**
 * Create a composite key for matching records
 */
function getCompositeKey(name: string, agency: string): string {
  return `${name.trim().toLowerCase()}|||${agency.trim().toLowerCase()}`;
}

async function main() {
  console.log('='.repeat(80));
  console.log('🔄 Syncing AI Use Cases from CSV to PostgreSQL');
  console.log('='.repeat(80));

  // Read CSV file
  console.log(`\n📂 Reading CSV: ${CSV_PATH}`);
  const csvContent = fs.readFileSync(CSV_PATH, 'utf-8');
  const records: CSVRecord[] = parse(csvContent, {
    columns: true,
    skip_empty_lines: true,
    bom: true,
  });
  console.log(`   Found ${records.length} records in CSV`);

  // Get existing records from database
  console.log('\n📊 Fetching existing records from database...');
  const existingRecords = await db.select().from(aiUseCases);
  console.log(`   Found ${existingRecords.length} records in database`);

  // Create lookup map for existing records
  const existingMap = new Map<string, typeof existingRecords[0]>();
  for (const record of existingRecords) {
    const key = getCompositeKey(record.useCaseName, record.agency);
    existingMap.set(key, record);
  }

  // Track stats
  let addedCount = 0;
  let updatedCount = 0;
  let skippedCount = 0;
  const toAdd: Array<typeof aiUseCases.$inferInsert> = [];
  const toUpdate: Array<{ id: number; updates: Partial<typeof aiUseCases.$inferInsert> }> = [];

  // Process each CSV record
  console.log('\n🔍 Analyzing records...');
  for (const csvRecord of records) {
    const key = getCompositeKey(csvRecord.use_case_name, csvRecord.agency);
    const existing = existingMap.get(key);

    const csvFlags = {
      hasLlm: parseBoolean(csvRecord._has_llm),
      hasGenai: parseBoolean(csvRecord._has_genai_signal),
      hasChatbot: parseBoolean(csvRecord._has_chatbot),
      hasGpMarkers: parseBoolean(csvRecord._has_gp_markers),
      hasCodingAssistant: parseBoolean(csvRecord._has_coding_assistant),
      hasCodingAgent: parseBoolean(csvRecord._has_coding_agent),
      hasClassicMl: parseBoolean(csvRecord._has_classic_ml),
      hasRpa: parseBoolean(csvRecord._has_rpa),
      hasRules: parseBoolean(csvRecord._has_rules),
      generalPurposeChatbot: parseBoolean(csvRecord._general_purpose_chatbot),
      domainChatbot: parseBoolean(csvRecord._domain_chatbot),
      codingAssistant: parseBoolean(csvRecord._coding_assistant),
      codingAgent: parseBoolean(csvRecord._coding_agent),
      genaiFlag: parseBoolean(csvRecord._genai_flag),
      aiTypeClassicMl: parseBoolean(csvRecord._ai_type_classic_ml),
      aiTypeRpaRules: parseBoolean(csvRecord._ai_type_rpa_rules),
      providersDetected: parseProviders(csvRecord._providers_detected),
      domainCategory: csvRecord._domain_category || null,
    };

    if (!existing) {
      // Record doesn't exist - add it
      toAdd.push({
        useCaseName: csvRecord.use_case_name,
        agency: csvRecord.agency,
        agencyAbbreviation: csvRecord.agency_abbreviation || null,
        bureau: csvRecord.bureau || null,
        useCaseTopicArea: csvRecord.use_case_topic_area || null,
        otherUseCaseTopicArea: csvRecord.other_use_case_topic_area || null,
        intendedPurpose: csvRecord.what_is_the_intended_purpose_and_expected_benefits_of_the_ai || null,
        outputs: csvRecord.describe_the_ai_system_s_outputs || null,
        stageOfDevelopment: csvRecord.stage_of_development || null,
        isRightsSafetyImpacting: csvRecord.is_the_ai_use_case_rights_impacting_safety_impacting_both_or_neither || null,
        dateInitiated: csvRecord.date_initiated || null,
        dateImplemented: csvRecord.date_implemented || null,
        dateRetired: csvRecord.date_retired || null,
        commercialAiProduct: csvRecord.is_the_ai_use_case_found_in_the_below_list_of_general_commercial_ai_products_and_services || null,
        slug: generateSlug(csvRecord.use_case_name, csvRecord.agency),
        ...csvFlags,
      });
    } else {
      // Record exists - check if flags need updating
      const needsUpdate =
        existing.genaiFlag !== csvFlags.genaiFlag ||
        existing.hasLlm !== csvFlags.hasLlm ||
        existing.hasGenai !== csvFlags.hasGenai ||
        existing.hasChatbot !== csvFlags.hasChatbot ||
        existing.hasGpMarkers !== csvFlags.hasGpMarkers ||
        existing.hasCodingAssistant !== csvFlags.hasCodingAssistant ||
        existing.hasCodingAgent !== csvFlags.hasCodingAgent ||
        existing.hasClassicMl !== csvFlags.hasClassicMl ||
        existing.hasRpa !== csvFlags.hasRpa ||
        existing.hasRules !== csvFlags.hasRules ||
        existing.generalPurposeChatbot !== csvFlags.generalPurposeChatbot ||
        existing.domainChatbot !== csvFlags.domainChatbot ||
        existing.codingAssistant !== csvFlags.codingAssistant ||
        existing.codingAgent !== csvFlags.codingAgent ||
        existing.aiTypeClassicMl !== csvFlags.aiTypeClassicMl ||
        existing.aiTypeRpaRules !== csvFlags.aiTypeRpaRules ||
        (csvFlags.domainCategory && existing.domainCategory !== csvFlags.domainCategory);

      if (needsUpdate) {
        toUpdate.push({
          id: existing.id,
          updates: csvFlags,
        });
      } else {
        skippedCount++;
      }
    }
  }

  console.log(`\n📋 Summary:`);
  console.log(`   • Records to add: ${toAdd.length}`);
  console.log(`   • Records to update: ${toUpdate.length}`);
  console.log(`   • Records unchanged: ${skippedCount}`);

  // Add missing records in batches
  if (toAdd.length > 0) {
    console.log(`\n➕ Adding ${toAdd.length} new records...`);
    const batchSize = 100;
    for (let i = 0; i < toAdd.length; i += batchSize) {
      const batch = toAdd.slice(i, i + batchSize);
      await db.insert(aiUseCases).values(batch);
      addedCount += batch.length;
      console.log(`   Added ${addedCount}/${toAdd.length} records...`);
    }
    console.log(`   ✅ Added ${addedCount} new records`);
  }

  // Update existing records
  if (toUpdate.length > 0) {
    console.log(`\n🔄 Updating ${toUpdate.length} existing records...`);
    for (const { id, updates } of toUpdate) {
      await db.update(aiUseCases).set(updates).where(eq(aiUseCases.id, id));
      updatedCount++;
      if (updatedCount % 100 === 0) {
        console.log(`   Updated ${updatedCount}/${toUpdate.length} records...`);
      }
    }
    console.log(`   ✅ Updated ${updatedCount} records`);
  }

  // Verify final count
  console.log('\n🔍 Verifying final counts...');
  const finalCount = await db.select().from(aiUseCases);
  console.log(`   Database now has ${finalCount.length} records`);

  // Count genai flags
  const genaiCount = finalCount.filter(r => r.genaiFlag).length;
  console.log(`   GenAI flag count: ${genaiCount}`);

  console.log('\n' + '='.repeat(80));
  console.log('✅ Sync completed successfully!');
  console.log(`   • Added: ${addedCount}`);
  console.log(`   • Updated: ${updatedCount}`);
  console.log(`   • Unchanged: ${skippedCount}`);
  console.log(`   • Total in DB: ${finalCount.length}`);
  console.log('='.repeat(80));

  process.exit(0);
}

main().catch((error) => {
  console.error('\n❌ Sync failed:', error);
  process.exit(1);
});
