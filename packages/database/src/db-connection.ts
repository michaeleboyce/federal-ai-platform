// packages/database/src/db-connection.ts
import { drizzle } from "drizzle-orm/neon-http";
import { neon } from "@neondatabase/serverless";
import * as schema from "./schema";
import * as dotenv from "dotenv";

// Load environment variables
dotenv.config({ path: "../../frontend/.env.local" });

// Verify DATABASE_URL is set
if (!process.env.DATABASE_URL) {
  throw new Error(
    "DATABASE_URL environment variable is not set. Please add it to your .env.local file."
  );
}

// Create Neon HTTP connection
const sql = neon(process.env.DATABASE_URL);

// Create Drizzle instance with schema
export const db = drizzle(sql, { schema });
