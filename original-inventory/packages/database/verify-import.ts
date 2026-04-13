#!/usr/bin/env tsx
/**
 * Verify the use case data import
 */

import { neon } from "@neondatabase/serverless";
import * as dotenv from "dotenv";

dotenv.config({ path: "../../frontend/.env.local" });

const sql = neon(process.env.DATABASE_URL!);

async function verifyImport() {
  console.log('🔍 Verifying data integrity...\n');

  // Count use cases
  const useCases = await sql`SELECT COUNT(*) as count FROM ai_use_cases`;
  console.log(`✓ Use Cases: ${useCases[0].count}`);

  // Count details
  const details = await sql`SELECT COUNT(*) as count FROM ai_use_case_details`;
  console.log(`✓ Use Case Details: ${details[0].count}`);

  // Count by AI type
  const genai = await sql`SELECT COUNT(*) as count FROM ai_use_cases WHERE genai_flag = true`;
  const llm = await sql`SELECT COUNT(*) as count FROM ai_use_cases WHERE has_llm = true`;
  const chatbot = await sql`SELECT COUNT(*) as count FROM ai_use_cases WHERE has_chatbot = true`;
  const classicMl = await sql`SELECT COUNT(*) as count FROM ai_use_cases WHERE has_classic_ml = true`;

  console.log(`\n📊 AI Type Breakdown:`);
  console.log(`   GenAI: ${genai[0].count}`);
  console.log(`   LLM: ${llm[0].count}`);
  console.log(`   Chatbot: ${chatbot[0].count}`);
  console.log(`   Classic ML: ${classicMl[0].count}`);

  // Count unique agencies
  const agencies = await sql`SELECT COUNT(DISTINCT agency) as count FROM ai_use_cases`;
  console.log(`\n✓ Unique Agencies: ${agencies[0].count}`);

  // Count by domain
  const domains = await sql`SELECT domain_category, COUNT(*) as count FROM ai_use_cases WHERE domain_category IS NOT NULL GROUP BY domain_category ORDER BY count DESC LIMIT 10`;
  console.log(`\n🏢 Top 10 Domains:`);
  domains.forEach(d => console.log(`   ${d.domain_category}: ${d.count}`));

  // Count by stage
  const stages = await sql`SELECT stage_of_development, COUNT(*) as count FROM ai_use_cases WHERE stage_of_development IS NOT NULL GROUP BY stage_of_development ORDER BY count DESC`;
  console.log(`\n🚀 Development Stages:`);
  stages.forEach(s => console.log(`   ${s.stage_of_development}: ${s.count}`));

  console.log('\n✅ Data verification complete!');
}

verifyImport().catch(console.error);
