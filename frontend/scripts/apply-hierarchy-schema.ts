import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config({ path: '.env.local' });

const sql = neon(process.env.DATABASE_URL!);

async function applyHierarchySchema() {
  console.log('Applying federal organization hierarchy schema...\n');

  try {
    // Step 1: Create the org_level enum if it doesn't exist
    console.log('1. Creating org_level enum...');
    await sql`
      DO $$ BEGIN
        CREATE TYPE org_level AS ENUM ('department', 'independent', 'sub_agency', 'office', 'component');
      EXCEPTION
        WHEN duplicate_object THEN null;
      END $$;
    `;
    console.log('   ✓ org_level enum ready\n');

    // Step 2: Create federal_organizations table
    console.log('2. Creating federal_organizations table...');
    await sql`
      CREATE TABLE IF NOT EXISTS federal_organizations (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        short_name VARCHAR(100),
        abbreviation VARCHAR(20),
        slug TEXT UNIQUE NOT NULL,
        parent_id INTEGER REFERENCES federal_organizations(id) ON DELETE SET NULL,
        level org_level NOT NULL,
        hierarchy_path TEXT,
        depth INTEGER NOT NULL DEFAULT 0,
        sam_org_id VARCHAR(50),
        cgac_code VARCHAR(10),
        agency_code VARCHAR(20),
        is_cfo_act_agency BOOLEAN NOT NULL DEFAULT false,
        is_cabinet_department BOOLEAN NOT NULL DEFAULT false,
        is_active BOOLEAN NOT NULL DEFAULT true,
        display_order INTEGER DEFAULT 0,
        description TEXT,
        website TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );
    `;
    console.log('   ✓ federal_organizations table ready\n');

    // Step 3: Create indexes for federal_organizations
    console.log('3. Creating indexes...');
    const indexes = [
      { name: 'idx_fed_org_parent', sql: sql`CREATE INDEX IF NOT EXISTS idx_fed_org_parent ON federal_organizations(parent_id)` },
      { name: 'idx_fed_org_level', sql: sql`CREATE INDEX IF NOT EXISTS idx_fed_org_level ON federal_organizations(level)` },
      { name: 'idx_fed_org_abbreviation', sql: sql`CREATE INDEX IF NOT EXISTS idx_fed_org_abbreviation ON federal_organizations(abbreviation)` },
      { name: 'idx_fed_org_hierarchy_path', sql: sql`CREATE INDEX IF NOT EXISTS idx_fed_org_hierarchy_path ON federal_organizations(hierarchy_path)` },
      { name: 'idx_fed_org_cfo_act', sql: sql`CREATE INDEX IF NOT EXISTS idx_fed_org_cfo_act ON federal_organizations(is_cfo_act_agency)` },
    ];

    for (const idx of indexes) {
      await idx.sql;
      console.log(`   ✓ ${idx.name}`);
    }
    console.log('');

    // Step 4: Add organization_id column to agency_ai_usage
    console.log('4. Adding organization_id to agency_ai_usage...');
    await sql`
      ALTER TABLE agency_ai_usage
      ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES federal_organizations(id) ON DELETE SET NULL;
    `;
    await sql`CREATE INDEX IF NOT EXISTS idx_agency_org ON agency_ai_usage(organization_id)`;
    console.log('   ✓ organization_id column added\n');

    // Step 5: Add organization_id columns to ai_use_cases
    console.log('5. Adding organization columns to ai_use_cases...');
    await sql`
      ALTER TABLE ai_use_cases
      ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES federal_organizations(id) ON DELETE SET NULL;
    `;
    await sql`
      ALTER TABLE ai_use_cases
      ADD COLUMN IF NOT EXISTS bureau_organization_id INTEGER REFERENCES federal_organizations(id) ON DELETE SET NULL;
    `;
    await sql`CREATE INDEX IF NOT EXISTS idx_use_case_org ON ai_use_cases(organization_id)`;
    await sql`CREATE INDEX IF NOT EXISTS idx_use_case_bureau_org ON ai_use_cases(bureau_organization_id)`;
    console.log('   ✓ organization_id and bureau_organization_id columns added\n');

    console.log('✅ Schema migration completed successfully!');

    // Verify the table was created
    const result = await sql`
      SELECT column_name, data_type
      FROM information_schema.columns
      WHERE table_name = 'federal_organizations'
      ORDER BY ordinal_position;
    `;
    console.log('\nfederal_organizations columns:');
    result.forEach((row: any) => {
      console.log(`  - ${row.column_name}: ${row.data_type}`);
    });

  } catch (error) {
    console.error('Error applying schema:', error);
    process.exit(1);
  }
}

applyHierarchySchema();
