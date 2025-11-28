// scripts/migrate-incidents.ts
// Migrates incident data from ai-incidents SQLite to federal-ai-platform PostgreSQL
// Uses sqlite3 CLI to avoid native module issues

import { execSync } from 'child_process';
import { neon } from '@neondatabase/serverless';
import * as dotenv from 'dotenv';
import path from 'path';

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../.env.local') });

const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  console.error('DATABASE_URL not found in environment');
  process.exit(1);
}

// Source SQLite database
const SQLITE_PATH = '/Users/michaelboyce/Documents/Programming/ifp/ai-incidents/data/aiid.db';

// Initialize PostgreSQL connection
const sql = neon(DATABASE_URL);

// Helper to run sqlite3 query and get JSON results
function sqliteQuery(query: string): any[] {
  try {
    const result = execSync(`sqlite3 -json "${SQLITE_PATH}" "${query}"`, {
      encoding: 'utf-8',
      maxBuffer: 50 * 1024 * 1024, // 50MB buffer
    });
    return JSON.parse(result);
  } catch (error: any) {
    if (error.stdout) {
      try {
        return JSON.parse(error.stdout);
      } catch {
        return [];
      }
    }
    return [];
  }
}

// Helper to parse JSON array from SQLite (stored as text) and return as JSON string for PostgreSQL
function parseJsonArrayToString(value: string | null): string {
  if (!value) return '[]';
  try {
    const parsed = JSON.parse(value);
    return JSON.stringify(parsed);
  } catch {
    return '[]';
  }
}

async function migrateIncidents() {
  console.log('📥 Migrating incidents...');

  const rows = sqliteQuery('SELECT * FROM incidents');
  console.log(`Found ${rows.length} incidents`);

  let migrated = 0;
  for (const row of rows) {
    try {
      const deployers = parseJsonArrayToString(row.deployers);
      const developers = parseJsonArrayToString(row.developers);
      const harmedParties = parseJsonArrayToString(row.harmed_parties);

      await sql`
        INSERT INTO incidents (
          incident_id, title, description, date, deployers, developers, harmed_parties, report_count
        ) VALUES (
          ${row.incident_id},
          ${row.title || ''},
          ${row.description || null},
          ${row.date || null},
          ${deployers}::jsonb,
          ${developers}::jsonb,
          ${harmedParties}::jsonb,
          ${row.report_count || 0}
        )
        ON CONFLICT (incident_id) DO NOTHING
      `;
      migrated++;
      if (migrated % 100 === 0) {
        console.log(`  Progress: ${migrated}/${rows.length}`);
      }
    } catch (error) {
      console.error(`Error migrating incident ${row.incident_id}:`, error);
    }
  }

  console.log(`✅ Migrated ${migrated} incidents`);
  return migrated;
}

async function migrateReports() {
  console.log('📥 Migrating reports...');

  const rows = sqliteQuery('SELECT * FROM reports');
  console.log(`Found ${rows.length} reports`);

  let migrated = 0;
  for (const row of rows) {
    try {
      const authors = parseJsonArrayToString(row.authors);
      const tags = parseJsonArrayToString(row.tags);

      await sql`
        INSERT INTO reports (
          report_number, incident_id, title, text, url, source_domain,
          authors, date_published, date_downloaded, date_modified, date_submitted,
          language, image_url, tags
        ) VALUES (
          ${row.report_number},
          ${row.incident_id || null},
          ${row.title || null},
          ${row.text || null},
          ${row.url || null},
          ${row.source_domain || null},
          ${authors}::jsonb,
          ${row.date_published || null},
          ${row.date_downloaded || null},
          ${row.date_modified || null},
          ${row.date_submitted || null},
          ${row.language || null},
          ${row.image_url || null},
          ${tags}::jsonb
        )
        ON CONFLICT (report_number) DO NOTHING
      `;
      migrated++;
      if (migrated % 500 === 0) {
        console.log(`  Progress: ${migrated}/${rows.length}`);
      }
    } catch (error) {
      console.error(`Error migrating report ${row.report_number}:`, error);
    }
  }

  console.log(`✅ Migrated ${migrated} reports`);
  return migrated;
}

async function migrateEntities() {
  console.log('📥 Migrating entities...');

  const rows = sqliteQuery('SELECT * FROM entities');
  console.log(`Found ${rows.length} entities`);

  let migrated = 0;
  for (const row of rows) {
    try {
      await sql`
        INSERT INTO entities (entity_id, name)
        VALUES (${row.entity_id}, ${row.name})
        ON CONFLICT (entity_id) DO NOTHING
      `;
      migrated++;
      if (migrated % 500 === 0) {
        console.log(`  Progress: ${migrated}/${rows.length}`);
      }
    } catch (error) {
      // Skip duplicates silently
    }
  }

  console.log(`✅ Migrated ${migrated} entities`);
  return migrated;
}

async function migrateIncidentEntities() {
  console.log('📥 Migrating incident-entity relationships...');

  const rows = sqliteQuery('SELECT * FROM incident_entities');
  console.log(`Found ${rows.length} relationships`);

  let migrated = 0;
  for (const row of rows) {
    try {
      await sql`
        INSERT INTO incident_entities (incident_id, entity_id, role)
        VALUES (${row.incident_id}, ${row.entity_id}, ${row.role})
      `;
      migrated++;
      if (migrated % 1000 === 0) {
        console.log(`  Progress: ${migrated}/${rows.length}`);
      }
    } catch (error) {
      // Skip duplicates silently
    }
  }

  console.log(`✅ Migrated ${migrated} relationships`);
  return migrated;
}

async function migrateIncidentSecurity() {
  console.log('📥 Migrating security data...');

  const rows = sqliteQuery('SELECT * FROM incident_security');
  console.log(`Found ${rows.length} security records`);

  let migrated = 0;
  for (const row of rows) {
    try {
      const securityDataLeakModes = parseJsonArrayToString(row.security_data_leak_modes);
      const securityDataTypes = parseJsonArrayToString(row.security_data_types);
      const regulatoryRegimes = parseJsonArrayToString(row.regulatory_regimes);
      const attackerIntent = parseJsonArrayToString(row.attacker_intent);
      const aiAttackType = parseJsonArrayToString(row.ai_attack_type);
      const downstreamConsequences = parseJsonArrayToString(row.downstream_consequences);
      const evidenceTypes = parseJsonArrayToString(row.evidence_types);
      const llmConnectorTooling = parseJsonArrayToString(row.llm_connector_tooling);
      const llmDataSourceOfLeak = parseJsonArrayToString(row.llm_data_source_of_leak);

      await sql`
        INSERT INTO incident_security (
          incident_id,
          security_data_leak_presence, security_data_leak_modes, security_data_types,
          security_environment_type, security_expectation_level, regulated_context_flag, regulatory_regimes,
          cyber_attack_flag, attacker_intent, ai_attack_type,
          major_product_flag, deployment_status, user_base_size_bucket, records_exposed_bucket, leak_duration,
          downstream_consequences, evidence_types, security_label_confidence,
          llm_or_chatbot_involved, llm_connector_tooling, llm_data_source_of_leak
        ) VALUES (
          ${row.incident_id},
          ${row.security_data_leak_presence || null},
          ${securityDataLeakModes}::jsonb,
          ${securityDataTypes}::jsonb,
          ${row.security_environment_type || null},
          ${row.security_expectation_level || null},
          ${row.regulated_context_flag === 1},
          ${regulatoryRegimes}::jsonb,
          ${row.cyber_attack_flag || null},
          ${attackerIntent}::jsonb,
          ${aiAttackType}::jsonb,
          ${row.major_product_flag || null},
          ${row.deployment_status || null},
          ${row.user_base_size_bucket || null},
          ${row.records_exposed_bucket || null},
          ${row.leak_duration || null},
          ${downstreamConsequences}::jsonb,
          ${evidenceTypes}::jsonb,
          ${row.security_label_confidence || null},
          ${row.llm_or_chatbot_involved === 1},
          ${llmConnectorTooling}::jsonb,
          ${llmDataSourceOfLeak}::jsonb
        )
        ON CONFLICT (incident_id) DO NOTHING
      `;
      migrated++;
      if (migrated % 100 === 0) {
        console.log(`  Progress: ${migrated}/${rows.length}`);
      }
    } catch (error) {
      console.error(`Error migrating security data for incident ${row.incident_id}:`, error);
    }
  }

  console.log(`✅ Migrated ${migrated} security records`);
  return migrated;
}

async function migrateClassifications() {
  console.log('📥 Migrating classifications...');

  const rows = sqliteQuery('SELECT * FROM classifications');
  console.log(`Found ${rows.length} classifications`);

  let migrated = 0;
  for (const row of rows) {
    try {
      await sql`
        INSERT INTO classifications (
          incident_id, namespace, published, incident_number,
          harm_domain, tangible_harm, ai_system,
          date_of_incident_year, date_of_incident_month, date_of_incident_day,
          location_country, location_region, sector_of_deployment,
          public_sector_deployment, intentional_harm, ai_task
        ) VALUES (
          ${row.incident_id},
          ${row.namespace || 'unknown'},
          ${row.published === 1},
          ${row.incident_number || null},
          ${row.harm_domain || null},
          ${row.tangible_harm || null},
          ${row.ai_system || null},
          ${row.date_of_incident_year || null},
          ${row.date_of_incident_month || null},
          ${row.date_of_incident_day || null},
          ${row.location_country || null},
          ${row.location_region || null},
          ${row.sector_of_deployment || null},
          ${row.public_sector_deployment || null},
          ${row.intentional_harm || null},
          ${row.ai_task || null}
        )
      `;
      migrated++;
    } catch (error) {
      console.error(`Error migrating classification:`, error);
    }
  }

  console.log(`✅ Migrated ${migrated} classifications`);
  return migrated;
}

async function migrateTaxa() {
  console.log('📥 Migrating taxa...');

  const rows = sqliteQuery('SELECT * FROM taxa');
  console.log(`Found ${rows.length} taxa records`);

  let migrated = 0;
  for (const row of rows) {
    try {
      await sql`
        INSERT INTO taxa (namespace, field_name, short_name, long_name, long_description)
        VALUES (
          ${row.namespace},
          ${row.field_name},
          ${row.short_name || null},
          ${row.long_name || null},
          ${row.long_description || null}
        )
      `;
      migrated++;
    } catch (error) {
      console.error(`Error migrating taxa:`, error);
    }
  }

  console.log(`✅ Migrated ${migrated} taxa records`);
  return migrated;
}

async function main() {
  console.log('🚀 Starting incident data migration from SQLite to PostgreSQL...\n');
  console.log(`Source: ${SQLITE_PATH}`);
  console.log(`Target: Neon PostgreSQL\n`);

  const results = {
    incidents: 0,
    reports: 0,
    entities: 0,
    incidentEntities: 0,
    incidentSecurity: 0,
    classifications: 0,
    taxa: 0,
  };

  try {
    // Migrate in order (respecting dependencies)
    results.incidents = await migrateIncidents();
    results.reports = await migrateReports();
    results.entities = await migrateEntities();
    results.incidentEntities = await migrateIncidentEntities();
    results.incidentSecurity = await migrateIncidentSecurity();
    results.classifications = await migrateClassifications();
    results.taxa = await migrateTaxa();

    console.log('\n📊 Migration Summary:');
    console.log('─'.repeat(40));
    console.log(`Incidents:        ${results.incidents}`);
    console.log(`Reports:          ${results.reports}`);
    console.log(`Entities:         ${results.entities}`);
    console.log(`Relationships:    ${results.incidentEntities}`);
    console.log(`Security Data:    ${results.incidentSecurity}`);
    console.log(`Classifications:  ${results.classifications}`);
    console.log(`Taxa:             ${results.taxa}`);
    console.log('─'.repeat(40));
    console.log(`Total Records:    ${Object.values(results).reduce((a, b) => a + b, 0)}`);
    console.log('\n✨ Migration complete!');
  } catch (error) {
    console.error('\n❌ Migration failed:', error);
    process.exit(1);
  }
}

main();
