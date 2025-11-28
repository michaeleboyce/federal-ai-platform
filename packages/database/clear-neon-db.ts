// Clear all tables and enums from Neon database before fresh migration
import { neon } from "@neondatabase/serverless";
import * as dotenv from "dotenv";

dotenv.config({ path: "../../frontend/.env.local" });

const sql = neon(process.env.DATABASE_URL!);

async function clearDatabase() {
  console.log("⚠️  Clearing Neon database (creating clean backup first)...\n");

  try {
    // Drop all tables in dependency order
    console.log("Dropping tables...");
    await sql`DROP TABLE IF EXISTS use_case_fedramp_matches CASCADE`;
    await sql`DROP TABLE IF EXISTS ai_use_case_details CASCADE`;
    await sql`DROP TABLE IF EXISTS ai_use_cases CASCADE`;
    await sql`DROP TABLE IF EXISTS agency_service_matches CASCADE`;
    await sql`DROP TABLE IF EXISTS agency_ai_usage CASCADE`;
    await sql`DROP TABLE IF EXISTS product_ai_analysis_runs CASCADE`;
    await sql`DROP TABLE IF EXISTS ai_service_analysis CASCADE`;
    await sql`DROP TABLE IF EXISTS products CASCADE`;

    // Drop enums
    console.log("Dropping enums...");
    await sql`DROP TYPE IF EXISTS confidence CASCADE`;
    await sql`DROP TYPE IF EXISTS match_confidence CASCADE`;
    await sql`DROP TYPE IF EXISTS agency_category CASCADE`;
    await sql`DROP TYPE IF EXISTS product_status CASCADE`;
    await sql`DROP TYPE IF EXISTS service_model CASCADE`;

    console.log("\n✅ Database cleared successfully!");
    console.log("   Ready for fresh schema push with drizzle-kit\n");
  } catch (error) {
    console.error("Error clearing database:", error);
  }
}

clearDatabase();
