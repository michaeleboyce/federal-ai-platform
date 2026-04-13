import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

import { db } from '../lib/db/client';
import { aiServiceAnalysis, agencyServiceMatches } from '../lib/db/schema';

async function checkData() {
  const service = await db.select().from(aiServiceAnalysis);
  const matches = await db.select().from(agencyServiceMatches);
  console.log('ai_service_analysis records:', service.length);
  console.log('agency_service_matches records:', matches.length);
  process.exit(0);
}

checkData().catch(console.error);
