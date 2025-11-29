import * as dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL!);

async function pushSchema() {
  console.log('Creating new enums...');

  // Create product_type enum if not exists
  await sql`
    DO $$ BEGIN
      CREATE TYPE product_type AS ENUM ('staff_chatbot', 'coding_assistant', 'document_automation', 'none_identified');
    EXCEPTION
      WHEN duplicate_object THEN null;
    END $$;
  `;
  console.log('✓ product_type enum created');

  // Create deployment_status enum if not exists
  await sql`
    DO $$ BEGIN
      CREATE TYPE deployment_status AS ENUM ('all_staff', 'pilot_or_limited', 'no_public_internal_assistant');
    EXCEPTION
      WHEN duplicate_object THEN null;
    END $$;
  `;
  console.log('✓ deployment_status enum created');

  // Create agency_ai_profiles table
  console.log('Creating agency_ai_profiles table...');
  await sql`
    CREATE TABLE IF NOT EXISTS agency_ai_profiles (
      id SERIAL PRIMARY KEY,
      agency_name TEXT NOT NULL,
      abbreviation VARCHAR(20),
      slug TEXT UNIQUE NOT NULL,
      organization_id INTEGER,
      department_level_name TEXT,
      parent_abbreviation VARCHAR(20),
      deployment_status deployment_status DEFAULT 'no_public_internal_assistant',
      has_staff_chatbot BOOLEAN NOT NULL DEFAULT false,
      has_coding_assistant BOOLEAN NOT NULL DEFAULT false,
      has_document_automation BOOLEAN NOT NULL DEFAULT false,
      tool_count INTEGER NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `;
  console.log('✓ agency_ai_profiles table created');

  // Create indexes for agency_ai_profiles
  await sql`CREATE INDEX IF NOT EXISTS idx_agency_profile_org ON agency_ai_profiles(organization_id);`;
  await sql`CREATE INDEX IF NOT EXISTS idx_agency_profile_dept ON agency_ai_profiles(department_level_name);`;
  await sql`CREATE INDEX IF NOT EXISTS idx_agency_profile_parent ON agency_ai_profiles(parent_abbreviation);`;
  await sql`CREATE INDEX IF NOT EXISTS idx_agency_profile_chatbot ON agency_ai_profiles(has_staff_chatbot);`;
  await sql`CREATE INDEX IF NOT EXISTS idx_agency_profile_coding ON agency_ai_profiles(has_coding_assistant);`;
  console.log('✓ agency_ai_profiles indexes created');

  // Create agency_ai_tools table
  console.log('Creating agency_ai_tools table...');
  await sql`
    CREATE TABLE IF NOT EXISTS agency_ai_tools (
      id SERIAL PRIMARY KEY,
      agency_profile_id INTEGER NOT NULL REFERENCES agency_ai_profiles(id) ON DELETE CASCADE,
      product_name TEXT NOT NULL,
      product_type product_type NOT NULL,
      slug TEXT UNIQUE NOT NULL,
      available_to_all_staff TEXT,
      is_pilot_or_limited BOOLEAN DEFAULT false,
      coding_assistant_flag VARCHAR(20),
      internal_or_sensitive_data TEXT,
      citation_chicago TEXT,
      citation_accessed_date TEXT,
      citation_url TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `;
  console.log('✓ agency_ai_tools table created');

  // Create indexes for agency_ai_tools
  await sql`CREATE INDEX IF NOT EXISTS idx_agency_tool_profile ON agency_ai_tools(agency_profile_id);`;
  await sql`CREATE INDEX IF NOT EXISTS idx_agency_tool_type ON agency_ai_tools(product_type);`;
  await sql`CREATE INDEX IF NOT EXISTS idx_agency_tool_availability ON agency_ai_tools(available_to_all_staff);`;
  console.log('✓ agency_ai_tools indexes created');

  console.log('\n✅ Schema migration complete!');
}

pushSchema().catch(console.error);
