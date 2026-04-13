import { neon } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-http';
import * as schema from './schema';

function getDatabaseUrl(): string {
  const url = process.env.DATABASE_URL;
  if (!url) {
    throw new Error('DATABASE_URL environment variable is not set');
  }
  return url;
}

// Create Neon HTTP client (lazy evaluation allows dotenv to load first)
const sql = neon(getDatabaseUrl());

// Create Drizzle instance with schema
export const db = drizzle(sql, { schema });

// Export schema for direct access
export { schema };
