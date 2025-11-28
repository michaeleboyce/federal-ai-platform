// scripts/setup-embeddings.ts
// Sets up the embeddings tables for semantic similarity matching

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

// nomic-embed-text produces 768-dimensional vectors
const EMBEDDING_DIMENSIONS = 768;

async function setupEmbeddings() {
  console.log('🚀 Setting up embeddings infrastructure...\n');

  // Enable pgvector extension
  console.log('Enabling pgvector extension...');
  await sql`CREATE EXTENSION IF NOT EXISTS vector`;
  console.log('  ✅ pgvector extension enabled');

  // Create embeddings table for incidents
  console.log('\nCreating incident_embeddings table...');
  await sql`
    CREATE TABLE IF NOT EXISTS incident_embeddings (
      id SERIAL PRIMARY KEY,
      incident_id INTEGER NOT NULL UNIQUE,
      title TEXT,
      text_content TEXT,
      embedding vector(768),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `;
  console.log('  ✅ incident_embeddings table created');

  // Create embeddings table for use cases
  console.log('\nCreating use_case_embeddings table...');
  await sql`
    CREATE TABLE IF NOT EXISTS use_case_embeddings (
      id SERIAL PRIMARY KEY,
      use_case_id INTEGER NOT NULL UNIQUE,
      title TEXT,
      text_content TEXT,
      embedding vector(768),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `;
  console.log('  ✅ use_case_embeddings table created');

  // Create embeddings table for products
  console.log('\nCreating product_embeddings table...');
  await sql`
    CREATE TABLE IF NOT EXISTS product_embeddings (
      id SERIAL PRIMARY KEY,
      product_fedramp_id TEXT NOT NULL UNIQUE,
      title TEXT,
      text_content TEXT,
      embedding vector(768),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `;
  console.log('  ✅ product_embeddings table created');

  // Create vector similarity search indexes using HNSW (faster for queries)
  console.log('\nCreating vector indexes...');
  try {
    await sql`CREATE INDEX IF NOT EXISTS idx_incident_embeddings_vector ON incident_embeddings USING hnsw (embedding vector_cosine_ops)`;
    await sql`CREATE INDEX IF NOT EXISTS idx_use_case_embeddings_vector ON use_case_embeddings USING hnsw (embedding vector_cosine_ops)`;
    await sql`CREATE INDEX IF NOT EXISTS idx_product_embeddings_vector ON product_embeddings USING hnsw (embedding vector_cosine_ops)`;
    console.log('  ✅ HNSW indexes created');
  } catch (error: any) {
    console.log('  Note: HNSW indexes may already exist or require data first');
  }

  // Create semantic match results table
  console.log('\nCreating semantic_matches table...');
  await sql`
    CREATE TABLE IF NOT EXISTS semantic_matches (
      id SERIAL PRIMARY KEY,
      source_type TEXT NOT NULL,
      source_id TEXT NOT NULL,
      target_type TEXT NOT NULL,
      target_id TEXT NOT NULL,
      similarity_score REAL NOT NULL,
      match_rank INTEGER,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(source_type, source_id, target_type, target_id)
    )
  `;
  await sql`CREATE INDEX IF NOT EXISTS idx_semantic_matches_source ON semantic_matches(source_type, source_id)`;
  await sql`CREATE INDEX IF NOT EXISTS idx_semantic_matches_target ON semantic_matches(target_type, target_id)`;
  console.log('  ✅ semantic_matches table created');

  console.log('\n✨ Embeddings infrastructure setup complete!');
  console.log(`   - Using ${EMBEDDING_DIMENSIONS}-dimensional vectors (nomic-embed-text)`);
}

setupEmbeddings().catch(console.error);
