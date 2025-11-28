import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

import { sql } from 'drizzle-orm';
import { db } from '../lib/db/client';

async function dropConstraint() {
  console.log('Dropping unique constraint on ai_service_analysis.product_id...');

  try {
    await db.execute(sql`ALTER TABLE ai_service_analysis DROP CONSTRAINT IF EXISTS ai_service_analysis_product_id_unique`);
    console.log('✅ Constraint dropped successfully');
  } catch (error) {
    console.error('Error dropping constraint:', error);
  }

  process.exit(0);
}

dropConstraint().catch(console.error);
