// scripts/generate-text-matches.ts
// Generates text-based matches between incidents, entities, products, and use cases

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

// Normalize text for matching
function normalize(text: string): string {
  return text.toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

// Extract core company name from variations
function extractCoreName(name: string): string[] {
  const normalized = normalize(name);
  const words = normalized.split(' ');

  // Common suffixes to strip
  const suffixes = ['inc', 'llc', 'corp', 'corporation', 'ltd', 'limited', 'company', 'co', 'technologies', 'technology'];
  const filtered = words.filter(w => !suffixes.includes(w) && w.length > 1);

  // Return both full name and first word (often company name)
  const variants = [normalized];
  if (filtered.length > 0) {
    variants.push(filtered[0]);
    variants.push(filtered.join(' '));
  }
  return [...new Set(variants)];
}

// Check if two names match
function namesMatch(name1: string, name2: string): boolean {
  const n1 = normalize(name1);
  const n2 = normalize(name2);

  if (n1 === n2) return true;
  if (n1.includes(n2) || n2.includes(n1)) return true;

  // Check core name matches
  const cores1 = extractCoreName(name1);
  const cores2 = extractCoreName(name2);

  for (const c1 of cores1) {
    for (const c2 of cores2) {
      if (c1 === c2 && c1.length > 2) return true;
    }
  }

  return false;
}

// Match confidence based on how exact the match is
function getMatchConfidence(name1: string, name2: string): 'high' | 'medium' | 'low' {
  const n1 = normalize(name1);
  const n2 = normalize(name2);

  if (n1 === n2) return 'high';
  if (n1.startsWith(n2) || n2.startsWith(n1)) return 'high';
  if (n1.includes(n2) || n2.includes(n1)) return 'medium';
  return 'low';
}

// Known tech company mappings for better matching
const COMPANY_ALIASES: Record<string, string[]> = {
  'google': ['google', 'alphabet', 'google cloud', 'gcp', 'google llc', 'deepmind', 'gemini'],
  'microsoft': ['microsoft', 'azure', 'openai', 'bing', 'copilot', 'github'],
  'amazon': ['amazon', 'aws', 'amazon web services', 'alexa'],
  'meta': ['meta', 'facebook', 'instagram', 'whatsapp', 'llama'],
  'apple': ['apple', 'siri'],
  'openai': ['openai', 'chatgpt', 'gpt-4', 'gpt-3', 'dall-e'],
  'anthropic': ['anthropic', 'claude'],
  'ibm': ['ibm', 'watson'],
  'oracle': ['oracle'],
  'salesforce': ['salesforce', 'einstein', 'slack'],
  'nvidia': ['nvidia'],
  'tesla': ['tesla', 'autopilot'],
  'uber': ['uber'],
  'tiktok': ['tiktok', 'bytedance'],
  'twitter': ['twitter', 'x'],
};

function getCanonicalCompany(name: string): string | null {
  const n = normalize(name);
  for (const [canonical, aliases] of Object.entries(COMPANY_ALIASES)) {
    if (aliases.some(alias => n.includes(alias) || alias.includes(n))) {
      return canonical;
    }
  }
  return null;
}

async function matchEntitiesToProducts() {
  console.log('🔗 Matching entities to FedRAMP products...\n');

  // Get all entities
  const entities = await sql`SELECT entity_id, name FROM entities`;
  console.log(`  Found ${entities.length} entities`);

  // Get all products
  const products = await sql`SELECT fedramp_id, cloud_service_provider, cloud_service_offering FROM products`;
  console.log(`  Found ${products.length} products\n`);

  let matchCount = 0;
  const matches: any[] = [];

  for (const entity of entities) {
    // Skip entities that don't look like companies
    if (entity.name.includes('victims') || entity.name.includes('users') ||
        entity.name.includes('employees') || entity.name.includes('customers') ||
        entity.name.includes('applicants')) {
      continue;
    }

    const entityCanonical = getCanonicalCompany(entity.name);

    for (const product of products) {
      if (!product.cloud_service_provider) continue;

      const productCanonical = getCanonicalCompany(product.cloud_service_provider);

      let matched = false;
      let matchReason = '';
      let confidence: 'high' | 'medium' | 'low' = 'low';

      // Check canonical company match
      if (entityCanonical && productCanonical && entityCanonical === productCanonical) {
        matched = true;
        matchReason = `Company family match: ${entityCanonical}`;
        confidence = 'high';
      }
      // Check direct name match
      else if (namesMatch(entity.name, product.cloud_service_provider)) {
        matched = true;
        matchReason = `Name match: ${entity.name} ≈ ${product.cloud_service_provider}`;
        confidence = getMatchConfidence(entity.name, product.cloud_service_provider);
      }

      if (matched) {
        matches.push({
          entity_id: entity.entity_id,
          product_fedramp_id: product.fedramp_id,
          match_type: 'entity_name',
          confidence,
          match_reason: matchReason,
        });
        matchCount++;
      }
    }
  }

  // Deduplicate matches
  const uniqueMatches = matches.filter((m, i, arr) =>
    arr.findIndex(x => x.entity_id === m.entity_id && x.product_fedramp_id === m.product_fedramp_id) === i
  );

  console.log(`  Generated ${uniqueMatches.length} unique entity-product matches\n`);

  // Insert matches
  if (uniqueMatches.length > 0) {
    // Clear existing matches
    await sql`DELETE FROM entity_product_matches WHERE match_type = 'entity_name'`;

    for (const match of uniqueMatches) {
      await sql`
        INSERT INTO entity_product_matches (entity_id, product_fedramp_id, match_type, confidence, match_reason)
        VALUES (${match.entity_id}, ${match.product_fedramp_id}, ${match.match_type}, ${match.confidence}, ${match.match_reason})
      `;
    }
    console.log(`  ✅ Inserted ${uniqueMatches.length} entity-product matches`);
  }

  return uniqueMatches.length;
}

async function matchIncidentsToProducts() {
  console.log('\n🔗 Matching incidents to FedRAMP products via entities...\n');

  // Get incidents with their entities
  const incidentEntities = await sql`
    SELECT ie.incident_id, e.entity_id, e.name, ie.role
    FROM incident_entities ie
    JOIN entities e ON ie.entity_id = e.entity_id
    WHERE ie.role IN ('developer', 'deployer')
  `;
  console.log(`  Found ${incidentEntities.length} incident-entity relationships`);

  // Get entity-product matches
  const entityMatches = await sql`SELECT * FROM entity_product_matches`;
  console.log(`  Found ${entityMatches.length} entity-product matches\n`);

  // Create lookup
  const entityToProducts = new Map<string, any[]>();
  for (const match of entityMatches) {
    if (!entityToProducts.has(match.entity_id)) {
      entityToProducts.set(match.entity_id, []);
    }
    entityToProducts.get(match.entity_id)!.push(match);
  }

  const matches: any[] = [];

  for (const ie of incidentEntities) {
    const productMatches = entityToProducts.get(ie.entity_id);
    if (productMatches) {
      for (const pm of productMatches) {
        matches.push({
          incident_id: ie.incident_id,
          product_fedramp_id: pm.product_fedramp_id,
          match_type: 'entity_name',
          confidence: pm.confidence,
          match_reason: `Incident entity "${ie.name}" (${ie.role}) matches FedRAMP product`,
          matched_entity: ie.entity_id,
        });
      }
    }
  }

  // Deduplicate
  const uniqueMatches = matches.filter((m, i, arr) =>
    arr.findIndex(x => x.incident_id === m.incident_id && x.product_fedramp_id === m.product_fedramp_id) === i
  );

  console.log(`  Generated ${uniqueMatches.length} unique incident-product matches\n`);

  // Insert matches
  if (uniqueMatches.length > 0) {
    await sql`DELETE FROM incident_product_matches WHERE match_type = 'entity_name'`;

    for (const match of uniqueMatches) {
      await sql`
        INSERT INTO incident_product_matches (incident_id, product_fedramp_id, match_type, confidence, match_reason, matched_entity)
        VALUES (${match.incident_id}, ${match.product_fedramp_id}, ${match.match_type}, ${match.confidence}, ${match.match_reason}, ${match.matched_entity})
      `;
    }
    console.log(`  ✅ Inserted ${uniqueMatches.length} incident-product matches`);
  }

  return uniqueMatches.length;
}

async function matchIncidentsToUseCases() {
  console.log('\n🔗 Matching incidents to AI use cases...\n');

  // Get incidents with security data showing LLM/chatbot involvement
  const llmIncidents = await sql`
    SELECT i.incident_id, i.title, s.llm_or_chatbot_involved
    FROM incidents i
    LEFT JOIN incident_security s ON i.incident_id = s.incident_id
    WHERE s.llm_or_chatbot_involved = true
  `;
  console.log(`  Found ${llmIncidents.length} LLM/chatbot-related incidents`);

  // Get use cases with LLM/chatbot flags
  const llmUseCases = await sql`
    SELECT id, use_case_name, agency, has_llm, has_chatbot, has_genai, providers_detected
    FROM ai_use_cases
    WHERE has_llm = true OR has_chatbot = true OR has_genai = true
  `;
  console.log(`  Found ${llmUseCases.length} LLM/chatbot/genai use cases\n`);

  const matches: any[] = [];

  // Technology-based matching (all LLM incidents to all LLM use cases is too broad)
  // Instead, try to match based on providers

  // Get incident entities (developers)
  const incidentDevelopers = await sql`
    SELECT ie.incident_id, e.name
    FROM incident_entities ie
    JOIN entities e ON ie.entity_id = e.entity_id
    WHERE ie.role = 'developer'
  `;

  // Build incident -> developer map
  const incidentDevs = new Map<number, string[]>();
  for (const id of incidentDevelopers) {
    if (!incidentDevs.has(id.incident_id)) {
      incidentDevs.set(id.incident_id, []);
    }
    incidentDevs.get(id.incident_id)!.push(id.name);
  }

  // Match based on providers
  for (const incident of llmIncidents) {
    const devs = incidentDevs.get(incident.incident_id) || [];

    for (const useCase of llmUseCases) {
      // Parse providers from use case
      let providers: string[] = [];
      if (useCase.providers_detected) {
        try {
          providers = JSON.parse(useCase.providers_detected);
        } catch {
          providers = [useCase.providers_detected];
        }
      }

      // Check if any incident developer matches use case provider
      for (const dev of devs) {
        const devCanonical = getCanonicalCompany(dev);
        for (const prov of providers) {
          const provCanonical = getCanonicalCompany(prov);
          if (devCanonical && provCanonical && devCanonical === provCanonical) {
            matches.push({
              incident_id: incident.incident_id,
              use_case_id: useCase.id,
              match_type: 'technology_flag',
              confidence: 'medium',
              match_reason: `LLM incident by "${dev}" matches use case using "${prov}"`,
              matched_entity: dev,
            });
          }
        }
      }
    }
  }

  // Deduplicate
  const uniqueMatches = matches.filter((m, i, arr) =>
    arr.findIndex(x => x.incident_id === m.incident_id && x.use_case_id === m.use_case_id) === i
  );

  console.log(`  Generated ${uniqueMatches.length} unique incident-use-case matches\n`);

  // Insert matches
  if (uniqueMatches.length > 0) {
    await sql`DELETE FROM incident_use_case_matches WHERE match_type = 'technology_flag'`;

    for (const match of uniqueMatches) {
      await sql`
        INSERT INTO incident_use_case_matches (incident_id, use_case_id, match_type, confidence, match_reason, matched_entity)
        VALUES (${match.incident_id}, ${match.use_case_id}, ${match.match_type}, ${match.confidence}, ${match.match_reason}, ${match.matched_entity})
      `;
    }
    console.log(`  ✅ Inserted ${uniqueMatches.length} incident-use-case matches`);
  }

  return uniqueMatches.length;
}

async function printSummary() {
  console.log('\n📊 Match Summary:');
  console.log('─'.repeat(50));

  const [entityProduct] = await sql`SELECT COUNT(*) as count FROM entity_product_matches`;
  const [incidentProduct] = await sql`SELECT COUNT(*) as count FROM incident_product_matches`;
  const [incidentUseCase] = await sql`SELECT COUNT(*) as count FROM incident_use_case_matches`;

  console.log(`Entity-Product matches:   ${entityProduct.count}`);
  console.log(`Incident-Product matches: ${incidentProduct.count}`);
  console.log(`Incident-UseCase matches: ${incidentUseCase.count}`);
  console.log('─'.repeat(50));

  // Show some example matches
  console.log('\n📋 Sample Entity-Product Matches:');
  const sampleEP = await sql`
    SELECT ep.entity_id, ep.product_fedramp_id, ep.confidence, ep.match_reason, p.cloud_service_provider
    FROM entity_product_matches ep
    JOIN products p ON ep.product_fedramp_id = p.fedramp_id
    LIMIT 5
  `;
  for (const m of sampleEP) {
    console.log(`  ${m.entity_id} → ${m.cloud_service_provider} (${m.confidence})`);
  }

  console.log('\n📋 Sample Incident-Product Matches:');
  const sampleIP = await sql`
    SELECT ip.incident_id, i.title, ip.product_fedramp_id, p.cloud_service_provider, ip.confidence
    FROM incident_product_matches ip
    JOIN incidents i ON ip.incident_id = i.incident_id
    JOIN products p ON ip.product_fedramp_id = p.fedramp_id
    LIMIT 5
  `;
  for (const m of sampleIP) {
    console.log(`  Incident ${m.incident_id}: "${m.title?.substring(0, 40)}..." → ${m.cloud_service_provider}`);
  }
}

async function main() {
  console.log('🚀 Generating text-based matches...\n');

  try {
    await matchEntitiesToProducts();
    await matchIncidentsToProducts();
    await matchIncidentsToUseCases();
    await printSummary();

    console.log('\n✨ Text-based matching complete!');
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

main();
