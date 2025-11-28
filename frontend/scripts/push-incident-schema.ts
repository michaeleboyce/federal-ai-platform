// scripts/push-incident-schema.ts
// Creates the incident tables in PostgreSQL

import { neon } from '@neondatabase/serverless';
import * as dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.join(__dirname, '../.env.local') });

const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  console.error('DATABASE_URL not found');
  process.exit(1);
}

const sql = neon(DATABASE_URL);

async function createTables() {
  console.log('Creating incident tables...\n');

  // Create enums first
  console.log('Creating enums...');
  try {
    await sql`CREATE TYPE entity_role AS ENUM ('deployer', 'developer', 'harmed')`;
  } catch (e: any) {
    if (!e.message.includes('already exists')) throw e;
    console.log('  entity_role enum already exists');
  }

  // Create incidents table
  console.log('Creating incidents table...');
  await sql`
    CREATE TABLE IF NOT EXISTS incidents (
      id SERIAL PRIMARY KEY,
      incident_id INTEGER NOT NULL UNIQUE,
      title TEXT NOT NULL,
      description TEXT,
      date TEXT,
      deployers JSONB,
      developers JSONB,
      harmed_parties JSONB,
      report_count INTEGER DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `;
  console.log('  ✅ incidents table created');

  // Create reports table
  console.log('Creating reports table...');
  await sql`
    CREATE TABLE IF NOT EXISTS reports (
      id SERIAL PRIMARY KEY,
      report_number INTEGER NOT NULL UNIQUE,
      incident_id INTEGER,
      title TEXT,
      text TEXT,
      url TEXT,
      source_domain TEXT,
      authors JSONB,
      date_published TEXT,
      date_downloaded TEXT,
      date_modified TEXT,
      date_submitted TEXT,
      language TEXT,
      image_url TEXT,
      tags JSONB
    )
  `;
  console.log('  ✅ reports table created');

  // Create entities table
  console.log('Creating entities table...');
  await sql`
    CREATE TABLE IF NOT EXISTS entities (
      id SERIAL PRIMARY KEY,
      entity_id TEXT NOT NULL UNIQUE,
      name TEXT NOT NULL
    )
  `;
  console.log('  ✅ entities table created');

  // Create incident_entities table
  console.log('Creating incident_entities table...');
  await sql`
    CREATE TABLE IF NOT EXISTS incident_entities (
      id SERIAL PRIMARY KEY,
      incident_id INTEGER NOT NULL,
      entity_id TEXT NOT NULL,
      role TEXT NOT NULL
    )
  `;
  console.log('  ✅ incident_entities table created');

  // Create incident_security table
  console.log('Creating incident_security table...');
  await sql`
    CREATE TABLE IF NOT EXISTS incident_security (
      id SERIAL PRIMARY KEY,
      incident_id INTEGER NOT NULL UNIQUE,
      security_data_leak_presence TEXT,
      security_data_leak_modes JSONB,
      security_data_types JSONB,
      security_environment_type TEXT,
      security_expectation_level TEXT,
      regulated_context_flag BOOLEAN,
      regulatory_regimes JSONB,
      cyber_attack_flag TEXT,
      attacker_intent JSONB,
      ai_attack_type JSONB,
      major_product_flag TEXT,
      deployment_status TEXT,
      user_base_size_bucket TEXT,
      records_exposed_bucket TEXT,
      leak_duration TEXT,
      downstream_consequences JSONB,
      evidence_types JSONB,
      security_label_confidence TEXT,
      llm_or_chatbot_involved BOOLEAN,
      llm_connector_tooling JSONB,
      llm_data_source_of_leak JSONB
    )
  `;
  console.log('  ✅ incident_security table created');

  // Create classifications table
  console.log('Creating classifications table...');
  await sql`
    CREATE TABLE IF NOT EXISTS classifications (
      id SERIAL PRIMARY KEY,
      incident_id INTEGER NOT NULL,
      namespace TEXT NOT NULL,
      published BOOLEAN,
      incident_number INTEGER,
      harm_domain TEXT,
      tangible_harm TEXT,
      ai_system TEXT,
      date_of_incident_year INTEGER,
      date_of_incident_month INTEGER,
      date_of_incident_day INTEGER,
      location_country TEXT,
      location_region TEXT,
      sector_of_deployment TEXT,
      public_sector_deployment TEXT,
      intentional_harm TEXT,
      ai_task TEXT
    )
  `;
  console.log('  ✅ classifications table created');

  // Create taxa table
  console.log('Creating taxa table...');
  await sql`
    CREATE TABLE IF NOT EXISTS taxa (
      id SERIAL PRIMARY KEY,
      namespace TEXT NOT NULL,
      field_name TEXT NOT NULL,
      short_name TEXT,
      long_name TEXT,
      long_description TEXT
    )
  `;
  console.log('  ✅ taxa table created');

  // Create indexes
  console.log('Creating indexes...');
  try {
    await sql`CREATE INDEX IF NOT EXISTS idx_incidents_incident_id ON incidents(incident_id)`;
    await sql`CREATE INDEX IF NOT EXISTS idx_reports_incident_id ON reports(incident_id)`;
    await sql`CREATE INDEX IF NOT EXISTS idx_incident_entities_incident_id ON incident_entities(incident_id)`;
    await sql`CREATE INDEX IF NOT EXISTS idx_incident_entities_entity_id ON incident_entities(entity_id)`;
    await sql`CREATE INDEX IF NOT EXISTS idx_incident_security_incident_id ON incident_security(incident_id)`;
    await sql`CREATE INDEX IF NOT EXISTS idx_classifications_incident_id ON classifications(incident_id)`;
    console.log('  ✅ indexes created');
  } catch (e) {
    console.log('  Some indexes may already exist');
  }

  console.log('\n✨ All incident tables created successfully!');
}

createTables().catch(console.error);
