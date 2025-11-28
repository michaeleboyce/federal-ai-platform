// Verify migration success
import { neon } from "@neondatabase/serverless";
import * as dotenv from "dotenv";

dotenv.config({ path: "../../frontend/.env.local" });

const sql = neon(process.env.DATABASE_URL!);

async function verifyMigration() {
  console.log("🔍 Verifying migration...\n");

  const [productsCount] = await sql`SELECT COUNT(*) as count FROM products`;
  const [servicesCount] = await sql`SELECT COUNT(*) as count FROM ai_service_analysis`;
  const [agenciesCount] = await sql`SELECT COUNT(*) as count FROM agency_ai_usage`;
  const [matchesCount] = await sql`SELECT COUNT(*) as count FROM agency_service_matches`;

  console.log("📊 Record counts:");
  console.log(`   Products:        ${productsCount.count} (expected: 615)`);
  console.log(`   AI Services:     ${servicesCount.count} (expected: 329)`);
  console.log(`   Agencies:        ${agenciesCount.count} (expected: 40)`);
  console.log(`   Agency Matches:  ${matchesCount.count} (expected: 21)`);
  console.log(`   Total:           ${Number(productsCount.count) + Number(servicesCount.count) + Number(agenciesCount.count) + Number(matchesCount.count)} (expected: 1005)`);

  const allMatch =
    productsCount.count === "615" &&
    servicesCount.count === "329" &&
    agenciesCount.count === "40" &&
    matchesCount.count === "21";

  console.log(allMatch ? "\n✅ Migration verified successfully!" : "\n⚠️  Record counts don't match expected values");

  // Sample some data
  console.log("\n📋 Sample products:");
  const products = await sql`SELECT fedramp_id, cloud_service_provider, cloud_service_offering FROM products LIMIT 3`;
  products.forEach((p: any) => console.log(`   • ${p.cloud_service_provider}: ${p.cloud_service_offering} (${p.fedramp_id})`));

  console.log("\n📋 Sample AI services:");
  const services = await sql`SELECT provider_name, product_name, service_name FROM ai_service_analysis WHERE has_llm = true LIMIT 3`;
  services.forEach((s: any) => console.log(`   • ${s.provider_name}: ${s.service_name} (${s.product_name})`));

  console.log("\n📋 Sample agencies:");
  const agencies = await sql`SELECT agency_name, agency_category FROM agency_ai_usage LIMIT 3`;
  agencies.forEach((a: any) => console.log(`   • ${a.agency_name} (${a.agency_category})`));
}

verifyMigration();
