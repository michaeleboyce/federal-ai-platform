// scripts/push-matches-schema.ts
// Creates the matching tables in PostgreSQL for cross-domain relationship tracking

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

async function createMatchingTables() {
  console.log('Creating matching tables...\n');

  // Create incident_product_matches table
  console.log('Creating incident_product_matches table...');
  await sql`
    CREATE TABLE IF NOT EXISTS incident_product_matches (
      id SERIAL PRIMARY KEY,
      incident_id INTEGER NOT NULL,
      product_fedramp_id TEXT NOT NULL,
      match_type TEXT NOT NULL,
      confidence TEXT NOT NULL,
      match_reason TEXT,
      matched_entity TEXT,
      similarity_score REAL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `;
  console.log('  ✅ incident_product_matches table created');

  // Create incident_use_case_matches table
  console.log('Creating incident_use_case_matches table...');
  await sql`
    CREATE TABLE IF NOT EXISTS incident_use_case_matches (
      id SERIAL PRIMARY KEY,
      incident_id INTEGER NOT NULL,
      use_case_id INTEGER NOT NULL,
      match_type TEXT NOT NULL,
      confidence TEXT NOT NULL,
      match_reason TEXT,
      matched_entity TEXT,
      similarity_score REAL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `;
  console.log('  ✅ incident_use_case_matches table created');

  // Create entity_product_matches table
  console.log('Creating entity_product_matches table...');
  await sql`
    CREATE TABLE IF NOT EXISTS entity_product_matches (
      id SERIAL PRIMARY KEY,
      entity_id TEXT NOT NULL,
      product_fedramp_id TEXT NOT NULL,
      match_type TEXT NOT NULL,
      confidence TEXT NOT NULL,
      match_reason TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `;
  console.log('  ✅ entity_product_matches table created');

  // Create indexes for efficient queries
  console.log('Creating indexes...');
  await sql`CREATE INDEX IF NOT EXISTS idx_incident_product_matches_incident ON incident_product_matches(incident_id)`;
  await sql`CREATE INDEX IF NOT EXISTS idx_incident_product_matches_product ON incident_product_matches(product_fedramp_id)`;
  await sql`CREATE INDEX IF NOT EXISTS idx_incident_use_case_matches_incident ON incident_use_case_matches(incident_id)`;
  await sql`CREATE INDEX IF NOT EXISTS idx_incident_use_case_matches_use_case ON incident_use_case_matches(use_case_id)`;
  await sql`CREATE INDEX IF NOT EXISTS idx_entity_product_matches_entity ON entity_product_matches(entity_id)`;
  await sql`CREATE INDEX IF NOT EXISTS idx_entity_product_matches_product ON entity_product_matches(product_fedramp_id)`;
  console.log('  ✅ indexes created');

  console.log('\n✨ All matching tables created successfully!');
}

createMatchingTables().catch(console.error);
