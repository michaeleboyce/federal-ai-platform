#!/usr/bin/env tsx
/**
 * Load Federal AI Use Case Inventory - simplified version
 */

import * as fs from 'fs';
import * as path from 'path';
import { parse } from 'csv-parse/sync';
import { neon } from "@neondatabase/serverless";
import * as dotenv from "dotenv";

dotenv.config({ path: "../../frontend/.env.local" });

const sql = neon(process.env.DATABASE_URL!);
const CSV_PATH = path.join(process.env.HOME!, 'Downloads', 'ai_inventory_enriched_with_tags.csv');

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

async function loadUseCases() {
  console.log('🚀 Loading Federal AI Use Case Inventory...\n');

  const fileContent = fs.readFileSync(CSV_PATH, 'utf-8');
  const records = parse(fileContent, {
    columns: true,
    skip_empty_lines: true,
  });

  console.log(`📊 Found ${records.length} use cases\n`);

  let count = 0;
  let errors = 0;

  for (const r of records) {
    try {
      const slug = `${slugify(r.agency || 'unknown')}-${slugify(r.use_case_name || 'use-case')}-${count}`;

      await sql`
        INSERT INTO ai_use_cases (
          use_case_name, agency, agency_abbreviation, bureau,
          use_case_topic_area, other_use_case_topic_area,
          intended_purpose, outputs,
          stage_of_development, is_rights_safety_impacting, domain_category,
          date_initiated, date_implemented, date_retired,
          has_llm, has_genai, has_chatbot, has_gp_markers,
          has_coding_assistant, has_coding_agent, has_classic_ml,
          has_rpa, has_rules,
          general_purpose_chatbot, domain_chatbot, coding_assistant,
          coding_agent, genai_flag, ai_type_classic_ml, ai_type_rpa_rules,
          providers_detected, commercial_ai_product, slug
        ) VALUES (
          ${r.use_case_name || 'Unknown'},
          ${r.agency || 'Unknown'},
          ${r.agency_abbreviation},
          ${r.bureau},
          ${r.use_case_topic_area},
          ${r.other_use_case_topic_area},
          ${r.what_is_the_intended_purpose_and_expected_benefits_of_the_ai},
          ${r.describe_the_ai_system_s_outputs},
          ${r.stage_of_development},
          ${r.is_the_ai_use_case_rights_impacting_safety_impacting_both_or_neither},
          ${r.domain_category},
          ${r.date_initiated},
          ${r.date_implemented},
          ${r.date_retired},
          ${r.has_llm === 'True'},
          ${r.has_genai === 'True'},
          ${r.has_chatbot === 'True'},
          ${r.has_gp_markers === 'True'},
          ${r.has_coding_assistant === 'True'},
          ${r.has_coding_agent === 'True'},
          ${r.has_classic_ml === 'True'},
          ${r.has_rpa === 'True'},
          ${r.has_rules === 'True'},
          ${r.general_purpose_chatbot === 'True'},
          ${r.domain_chatbot === 'True'},
          ${r.coding_assistant === 'True'},
          ${r.coding_agent === 'True'},
          ${r.genai_flag === 'True'},
          ${r.ai_type_classic_ml === 'True'},
          ${r.ai_type_rpa_rules === 'True'},
          ${r.providers_detected},
          ${r.is_the_ai_use_case_found_in_the_below_list_of_general_commercial_ai_products_and_services},
          ${slug}
        )
      `;

      count++;
      if (count % 100 === 0) {
        console.log(`   ✓ Imported ${count} use cases...`);
      }
    } catch (error: any) {
      errors++;
      if (errors < 3) console.error(`   ✗ Error: ${error.message}`);
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log(`✅ Imported ${count} use cases (${errors} errors)`);
  console.log('='.repeat(60));
}

loadUseCases().catch(console.error);
