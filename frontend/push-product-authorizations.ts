/**
 * Push product_authorizations table to Neon database
 * Run with: npx tsx push-product-authorizations.ts
 */

import * as dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

import { neon } from '@neondatabase/serverless';

async function main() {
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error('DATABASE_URL environment variable is not set');
  }

  console.log('Connecting to database...');
  const sql = neon(databaseUrl);

  console.log('Creating product_authorizations table...');

  // Create the table
  await sql`
    CREATE TABLE IF NOT EXISTS product_authorizations (
      id SERIAL PRIMARY KEY,
      fedramp_id TEXT NOT NULL,
      organization_id INTEGER REFERENCES federal_organizations(id),
      parent_agency_name TEXT NOT NULL,
      sub_agency_name TEXT,
      ato_issuance_date TEXT,
      ato_expiration_date TEXT,
      created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    )
  `;

  console.log('Creating indexes...');

  // Create unique index for deduplication
  await sql`
    CREATE UNIQUE INDEX IF NOT EXISTS product_auth_unique_idx
    ON product_authorizations (fedramp_id, parent_agency_name, COALESCE(sub_agency_name, ''))
  `;

  // Create index for product lookups
  await sql`
    CREATE INDEX IF NOT EXISTS product_auth_fedramp_idx
    ON product_authorizations (fedramp_id)
  `;

  // Create index for organization lookups
  await sql`
    CREATE INDEX IF NOT EXISTS product_auth_org_idx
    ON product_authorizations (organization_id)
  `;

  console.log('✅ product_authorizations table created successfully!');

  // Verify table structure
  const result = await sql`
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'product_authorizations'
    ORDER BY ordinal_position
  `;

  console.log('\nTable structure:');
  for (const row of result) {
    console.log(`  ${row.column_name}: ${row.data_type} (nullable: ${row.is_nullable})`);
  }
}

main().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});
