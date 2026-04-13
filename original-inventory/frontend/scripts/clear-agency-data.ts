import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

import { db } from '../lib/db/client';
import { agencyAiUsage, aiServiceAnalysis, agencyServiceMatches } from '../lib/db/schema';

async function clearData() {
  console.log('Clearing agency-related tables...');

  // Delete in correct order (respecting foreign keys)
  await db.delete(agencyServiceMatches);
  console.log('  ✅ Cleared agency_service_matches');

  await db.delete(aiServiceAnalysis);
  console.log('  ✅ Cleared ai_service_analysis');

  await db.delete(agencyAiUsage);
  console.log('  ✅ Cleared agency_ai_usage');

  console.log('\nAll agency data cleared. Ready for fresh migration.');
  process.exit(0);
}

clearData().catch(console.error);
