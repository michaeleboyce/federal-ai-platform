// scripts/generate-embeddings.ts
// Generates embeddings using Ollama's nomic-embed-text model and stores them in PostgreSQL
// Run: npx tsx scripts/generate-embeddings.ts

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

const OLLAMA_URL = process.env.OLLAMA_URL || 'http://localhost:11434';
const EMBEDDING_MODEL = 'nomic-embed-text';
const BATCH_SIZE = 10;

// Generate embedding using Ollama
async function getEmbedding(text: string): Promise<number[]> {
  const response = await fetch(`${OLLAMA_URL}/api/embeddings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: EMBEDDING_MODEL,
      prompt: text.slice(0, 8000), // Truncate to avoid token limits
    }),
  });

  if (!response.ok) {
    throw new Error(`Ollama error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.embedding;
}

// Format embedding for PostgreSQL vector type
function formatVector(embedding: number[]): string {
  return `[${embedding.join(',')}]`;
}

async function generateIncidentEmbeddings() {
  console.log('📥 Generating incident embeddings...\n');

  // Get incidents without embeddings
  const incidents = await sql`
    SELECT i.incident_id, i.title, i.description
    FROM incidents i
    LEFT JOIN incident_embeddings e ON i.incident_id = e.incident_id
    WHERE e.id IS NULL
    LIMIT 100
  `;

  console.log(`  Found ${incidents.length} incidents without embeddings`);

  let processed = 0;
  for (const incident of incidents) {
    try {
      const textContent = `${incident.title || ''}\n\n${incident.description || ''}`.trim();
      if (!textContent) continue;

      const embedding = await getEmbedding(textContent);
      const vectorStr = formatVector(embedding);

      await sql`
        INSERT INTO incident_embeddings (incident_id, title, text_content, embedding)
        VALUES (${incident.incident_id}, ${incident.title}, ${textContent.slice(0, 10000)}, ${vectorStr}::vector)
        ON CONFLICT (incident_id) DO UPDATE SET
          title = EXCLUDED.title,
          text_content = EXCLUDED.text_content,
          embedding = EXCLUDED.embedding,
          created_at = NOW()
      `;

      processed++;
      if (processed % 10 === 0) {
        console.log(`  Progress: ${processed}/${incidents.length}`);
      }
    } catch (error) {
      console.error(`  Error processing incident ${incident.incident_id}:`, error);
    }
  }

  console.log(`  ✅ Processed ${processed} incident embeddings`);
  return processed;
}

async function generateUseCaseEmbeddings() {
  console.log('\n📥 Generating use case embeddings...\n');

  // Get use cases without embeddings
  const useCases = await sql`
    SELECT u.id, u.use_case_name, u.intended_purpose, u.outputs
    FROM ai_use_cases u
    LEFT JOIN use_case_embeddings e ON u.id = e.use_case_id
    WHERE e.id IS NULL
    LIMIT 200
  `;

  console.log(`  Found ${useCases.length} use cases without embeddings`);

  let processed = 0;
  for (const uc of useCases) {
    try {
      const textContent = `${uc.use_case_name || ''}\n\n${uc.intended_purpose || ''}\n\n${uc.outputs || ''}`.trim();
      if (!textContent) continue;

      const embedding = await getEmbedding(textContent);
      const vectorStr = formatVector(embedding);

      await sql`
        INSERT INTO use_case_embeddings (use_case_id, title, text_content, embedding)
        VALUES (${uc.id}, ${uc.use_case_name}, ${textContent.slice(0, 10000)}, ${vectorStr}::vector)
        ON CONFLICT (use_case_id) DO UPDATE SET
          title = EXCLUDED.title,
          text_content = EXCLUDED.text_content,
          embedding = EXCLUDED.embedding,
          created_at = NOW()
      `;

      processed++;
      if (processed % 20 === 0) {
        console.log(`  Progress: ${processed}/${useCases.length}`);
      }
    } catch (error) {
      console.error(`  Error processing use case ${uc.id}:`, error);
    }
  }

  console.log(`  ✅ Processed ${processed} use case embeddings`);
  return processed;
}

async function generateProductEmbeddings() {
  console.log('\n📥 Generating product embeddings...\n');

  // Get products without embeddings
  const products = await sql`
    SELECT p.fedramp_id, p.cloud_service_offering, p.cloud_service_provider, p.service_description
    FROM products p
    LEFT JOIN product_embeddings e ON p.fedramp_id = e.product_fedramp_id
    WHERE e.id IS NULL
    LIMIT 200
  `;

  console.log(`  Found ${products.length} products without embeddings`);

  let processed = 0;
  for (const product of products) {
    try {
      const textContent = `${product.cloud_service_offering || ''} by ${product.cloud_service_provider || ''}\n\n${product.service_description || ''}`.trim();
      if (!textContent) continue;

      const embedding = await getEmbedding(textContent);
      const vectorStr = formatVector(embedding);

      await sql`
        INSERT INTO product_embeddings (product_fedramp_id, title, text_content, embedding)
        VALUES (${product.fedramp_id}, ${product.cloud_service_offering}, ${textContent.slice(0, 10000)}, ${vectorStr}::vector)
        ON CONFLICT (product_fedramp_id) DO UPDATE SET
          title = EXCLUDED.title,
          text_content = EXCLUDED.text_content,
          embedding = EXCLUDED.embedding,
          created_at = NOW()
      `;

      processed++;
      if (processed % 20 === 0) {
        console.log(`  Progress: ${processed}/${products.length}`);
      }
    } catch (error) {
      console.error(`  Error processing product ${product.fedramp_id}:`, error);
    }
  }

  console.log(`  ✅ Processed ${processed} product embeddings`);
  return processed;
}

// Only keep top N matches per source item to save database space
const TOP_MATCHES_LIMIT = 10;

async function findSemanticMatches() {
  console.log('\n🔍 Finding semantic matches (top ' + TOP_MATCHES_LIMIT + ' per item)...\n');

  // Find similar incidents to use cases - only top N per incident
  console.log('  Finding incident ↔ use case matches...');
  const incidentUseCaseMatches = await sql`
    INSERT INTO semantic_matches (source_type, source_id, target_type, target_id, similarity_score, match_rank)
    SELECT source_type, source_id, target_type, target_id, similarity, rank
    FROM (
      SELECT
        'incident' as source_type,
        ie.incident_id::text as source_id,
        'use_case' as target_type,
        ue.use_case_id::text as target_id,
        1 - (ie.embedding <=> ue.embedding) as similarity,
        ROW_NUMBER() OVER (PARTITION BY ie.incident_id ORDER BY ie.embedding <=> ue.embedding) as rank
      FROM incident_embeddings ie
      CROSS JOIN use_case_embeddings ue
      WHERE 1 - (ie.embedding <=> ue.embedding) > 0.5
    ) ranked
    WHERE rank <= ${TOP_MATCHES_LIMIT}
    ON CONFLICT (source_type, source_id, target_type, target_id)
    DO UPDATE SET similarity_score = EXCLUDED.similarity_score, match_rank = EXCLUDED.match_rank
    RETURNING id
  `;
  console.log(`    Found ${incidentUseCaseMatches.length} incident-usecase matches`);

  // Find similar incidents to products - only top N per incident
  console.log('  Finding incident ↔ product matches...');
  const incidentProductMatches = await sql`
    INSERT INTO semantic_matches (source_type, source_id, target_type, target_id, similarity_score, match_rank)
    SELECT source_type, source_id, target_type, target_id, similarity, rank
    FROM (
      SELECT
        'incident' as source_type,
        ie.incident_id::text as source_id,
        'product' as target_type,
        pe.product_fedramp_id as target_id,
        1 - (ie.embedding <=> pe.embedding) as similarity,
        ROW_NUMBER() OVER (PARTITION BY ie.incident_id ORDER BY ie.embedding <=> pe.embedding) as rank
      FROM incident_embeddings ie
      CROSS JOIN product_embeddings pe
      WHERE 1 - (ie.embedding <=> pe.embedding) > 0.5
    ) ranked
    WHERE rank <= ${TOP_MATCHES_LIMIT}
    ON CONFLICT (source_type, source_id, target_type, target_id)
    DO UPDATE SET similarity_score = EXCLUDED.similarity_score, match_rank = EXCLUDED.match_rank
    RETURNING id
  `;
  console.log(`    Found ${incidentProductMatches.length} incident-product matches`);

  // Find similar use cases to products - only top N per use case
  console.log('  Finding use case ↔ product matches...');
  const useCaseProductMatches = await sql`
    INSERT INTO semantic_matches (source_type, source_id, target_type, target_id, similarity_score, match_rank)
    SELECT source_type, source_id, target_type, target_id, similarity, rank
    FROM (
      SELECT
        'use_case' as source_type,
        ue.use_case_id::text as source_id,
        'product' as target_type,
        pe.product_fedramp_id as target_id,
        1 - (ue.embedding <=> pe.embedding) as similarity,
        ROW_NUMBER() OVER (PARTITION BY ue.use_case_id ORDER BY ue.embedding <=> pe.embedding) as rank
      FROM use_case_embeddings ue
      CROSS JOIN product_embeddings pe
      WHERE 1 - (ue.embedding <=> pe.embedding) > 0.5
    ) ranked
    WHERE rank <= ${TOP_MATCHES_LIMIT}
    ON CONFLICT (source_type, source_id, target_type, target_id)
    DO UPDATE SET similarity_score = EXCLUDED.similarity_score, match_rank = EXCLUDED.match_rank
    RETURNING id
  `;
  console.log(`    Found ${useCaseProductMatches.length} usecase-product matches`);
}

async function printSummary() {
  console.log('\n📊 Embedding Summary:');
  console.log('─'.repeat(50));

  const [incidentCount] = await sql`SELECT COUNT(*) as count FROM incident_embeddings`;
  const [useCaseCount] = await sql`SELECT COUNT(*) as count FROM use_case_embeddings`;
  const [productCount] = await sql`SELECT COUNT(*) as count FROM product_embeddings`;
  const [matchCount] = await sql`SELECT COUNT(*) as count FROM semantic_matches`;

  console.log(`Incident embeddings:  ${incidentCount.count}`);
  console.log(`Use case embeddings:  ${useCaseCount.count}`);
  console.log(`Product embeddings:   ${productCount.count}`);
  console.log(`Semantic matches:     ${matchCount.count}`);
  console.log('─'.repeat(50));
}

async function main() {
  console.log('🚀 Starting embedding generation with Ollama...\n');
  console.log(`Model: ${EMBEDDING_MODEL}`);
  console.log(`Ollama URL: ${OLLAMA_URL}\n`);

  // Check if Ollama is running
  try {
    const response = await fetch(`${OLLAMA_URL}/api/tags`);
    if (!response.ok) {
      throw new Error('Ollama not responding');
    }
    console.log('✅ Ollama is running\n');
  } catch (error) {
    console.error('❌ Ollama is not running. Please start Ollama first:');
    console.error('   1. Install Ollama: https://ollama.ai');
    console.error('   2. Run: ollama pull nomic-embed-text');
    console.error('   3. Ollama should automatically start on port 11434');
    process.exit(1);
  }

  try {
    await generateIncidentEmbeddings();
    await generateUseCaseEmbeddings();
    await generateProductEmbeddings();
    await findSemanticMatches();
    await printSummary();

    console.log('\n✨ Embedding generation complete!');
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

main();
