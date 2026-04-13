// packages/database/drizzle.config.ts
import type { Config } from "drizzle-kit";
import * as dotenv from "dotenv";

// Load environment variables from frontend .env.local
dotenv.config({ path: "../../frontend/.env.local" });

if (!process.env.DATABASE_URL) {
  throw new Error("DATABASE_URL is not set in environment variables");
}

export default {
  schema: "./src/schema/*",
  out: "./drizzle",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.DATABASE_URL,
  },
  verbose: true,
  strict: true,
} satisfies Config;
