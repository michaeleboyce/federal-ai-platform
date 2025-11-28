"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
// Direct SQL migration from SQLite to PostgreSQL
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const serverless_1 = require("@neondatabase/serverless");
const dotenv = __importStar(require("dotenv"));
dotenv.config({ path: "../../frontend/.env.local" });
const sql = (0, serverless_1.neon)(process.env.DATABASE_URL);
const DATA_DIR = path.join(__dirname, '../../../../data/sqlite_backup');
async function seedProducts() {
    console.log('\n📦 Seeding products table...');
    const productsData = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'products.json'), 'utf-8'));
    let count = 0;
    let errors = 0;
    for (const product of productsData) {
        try {
            await sql `
        INSERT INTO products (
          fedramp_id, cloud_service_provider, cloud_service_offering,
          service_description, business_categories, service_model,
          status, independent_assessor, authorizations, reuse,
          parent_agency, sub_agency, ato_issuance_date,
          fedramp_authorization_date, annual_assessment_date, ato_expiration_date,
          html_scraped, html_path, created_at, updated_at
        ) VALUES (
          ${product.fedramp_id}, ${product.cloud_service_provider}, ${product.cloud_service_offering},
          ${product.service_description}, ${product.business_categories}, ${product.service_model},
          ${product.status}, ${product.independent_assessor}, ${product.authorizations}, ${product.reuse},
          ${product.parent_agency}, ${product.sub_agency}, ${product.ato_issuance_date},
          ${product.fedramp_authorization_date}, ${product.annual_assessment_date}, ${product.ato_expiration_date},
          ${product.html_scraped === 1}, ${product.html_path},
          ${product.created_at ? new Date(product.created_at) : new Date()},
          ${product.updated_at ? new Date(product.updated_at) : new Date()}
        )
      `;
            count++;
            if (count % 100 === 0) {
                console.log(`   Inserted ${count} products...`);
            }
        }
        catch (error) {
            errors++;
            if (errors < 5)
                console.error(`   Error inserting product ${product.fedramp_id}:`, error.message);
        }
    }
    console.log(`✅ Products seeded: ${count} successful, ${errors} errors`);
    return count;
}
async function seedAIServices() {
    console.log('\n🤖 Seeding AI service analysis table...');
    const servicesData = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'ai_service_analysis.json'), 'utf-8'));
    let count = 0;
    let errors = 0;
    for (const service of servicesData) {
        try {
            await sql `
        INSERT INTO ai_service_analysis (
          product_id, product_name, provider_name, service_name,
          has_ai, has_genai, has_llm, relevant_excerpt,
          fedramp_status, impact_level, agencies, auth_date, analyzed_at
        ) VALUES (
          ${service.product_id}, ${service.product_name}, ${service.provider_name}, ${service.service_name},
          ${service.has_ai === 1}, ${service.has_genai === 1}, ${service.has_llm === 1}, ${service.relevant_excerpt},
          ${service.fedramp_status}, ${service.impact_level}, ${service.agencies}, ${service.auth_date},
          ${service.analyzed_at ? new Date(service.analyzed_at) : new Date()}
        )
      `;
            count++;
            if (count % 50 === 0) {
                console.log(`   Inserted ${count} AI services...`);
            }
        }
        catch (error) {
            errors++;
            if (errors < 5)
                console.error(`   Error inserting AI service:`, error.message);
        }
    }
    console.log(`✅ AI services seeded: ${count} successful, ${errors} errors`);
    return count;
}
async function seedAgencies() {
    console.log('\n🏛️  Seeding agency AI usage table...');
    const agenciesData = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'agency_ai_usage.json'), 'utf-8'));
    let count = 0;
    let errors = 0;
    for (const agency of agenciesData) {
        try {
            const result = await sql `
        INSERT INTO agency_ai_usage (
          agency_name, agency_category, has_staff_llm, llm_name, has_coding_assistant,
          scope, solution_type, non_public_allowed, other_ai_present,
          tool_name, tool_purpose, notes, sources, analyzed_at, slug
        ) VALUES (
          ${agency.agency_name}, ${agency.agency_category}, ${agency.has_staff_llm}, ${agency.llm_name}, ${agency.has_coding_assistant},
          ${agency.scope}, ${agency.solution_type}, ${agency.non_public_allowed}, ${agency.other_ai_present},
          ${agency.tool_name}, ${agency.tool_purpose}, ${agency.notes}, ${agency.sources},
          ${agency.analyzed_at ? new Date(agency.analyzed_at) : new Date()}, ${agency.slug}
        )
        RETURNING id
      `;
            // Store the mapping of old ID to new ID for matches
            if (!globalThis.agencyIdMap)
                globalThis.agencyIdMap = {};
            globalThis.agencyIdMap[agency.id] = result[0].id;
            count++;
        }
        catch (error) {
            errors++;
            if (errors < 5)
                console.error(`   Error inserting agency:`, error.message);
        }
    }
    console.log(`✅ Agencies seeded: ${count} successful, ${errors} errors`);
    return count;
}
async function seedAgencyMatches() {
    console.log('\n🔗 Seeding agency service matches table...');
    const matchesData = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'agency_service_matches.json'), 'utf-8'));
    let count = 0;
    let errors = 0;
    for (const match of matchesData) {
        try {
            const newAgencyId = globalThis.agencyIdMap[match.agency_id];
            if (!newAgencyId) {
                errors++;
                continue;
            }
            await sql `
        INSERT INTO agency_service_matches (
          agency_id, product_id, provider_name, product_name, service_name,
          confidence, match_reason, created_at
        ) VALUES (
          ${newAgencyId}, ${match.product_id}, ${match.provider_name}, ${match.product_name}, ${match.service_name},
          ${match.confidence}, ${match.match_reason},
          ${match.created_at ? new Date(match.created_at) : new Date()}
        )
      `;
            count++;
        }
        catch (error) {
            errors++;
            if (errors < 5)
                console.error(`   Error inserting agency match:`, error.message);
        }
    }
    console.log(`✅ Agency matches seeded: ${count} successful, ${errors} errors`);
    return count;
}
async function main() {
    console.log('🚀 Starting data migration from SQLite to PostgreSQL\n');
    console.log(`📁 Reading data from: ${DATA_DIR}\n`);
    const startTime = Date.now();
    try {
        const productsCount = await seedProducts();
        const servicesCount = await seedAIServices();
        const agenciesCount = await seedAgencies();
        const matchesCount = await seedAgencyMatches();
        const duration = ((Date.now() - startTime) / 1000).toFixed(2);
        console.log('\n' + '='.repeat(60));
        console.log('✅ Migration complete!');
        console.log('='.repeat(60));
        console.log(`📊 Summary:`);
        console.log(`   Products:        ${productsCount}`);
        console.log(`   AI Services:     ${servicesCount}`);
        console.log(`   Agencies:        ${agenciesCount}`);
        console.log(`   Agency Matches:  ${matchesCount}`);
        console.log(`   Total Records:   ${productsCount + servicesCount + agenciesCount + matchesCount}`);
        console.log(`   Duration:        ${duration}s`);
        console.log('='.repeat(60));
    }
    catch (error) {
        console.error('\n❌ Migration failed:', error);
        process.exit(1);
    }
}
main();
//# sourceMappingURL=migrate-direct.js.map