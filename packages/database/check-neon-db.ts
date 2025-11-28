// Check what tables exist in Neon database
import { neon } from "@neondatabase/serverless";
import * as dotenv from "dotenv";

dotenv.config({ path: "../../frontend/.env.local" });

const sql = neon(process.env.DATABASE_URL!);

async function checkDatabase() {
  console.log("Checking Neon database...\n");

  // Get all tables
  const tables = await sql`
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
  `;

  console.log("Existing tables:");
  if (tables.length === 0) {
    console.log("  (none - database is empty)");
  } else {
    tables.forEach((t: any) => console.log(`  - ${t.table_name}`));
  }

  console.log("\nExisting enums:");
  const enums = await sql`
    SELECT typname
    FROM pg_type
    WHERE typtype = 'e'
    ORDER BY typname;
  `;

  if (enums.length === 0) {
    console.log("  (none)");
  } else {
    enums.forEach((e: any) => console.log(`  - ${e.typname}`));
  }
}

checkDatabase().catch(console.error);
