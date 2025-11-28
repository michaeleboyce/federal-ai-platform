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
// packages/database/src/seed/index.ts
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const ProductRepository_1 = require("../repositories/ProductRepository");
const AIServiceRepository_1 = require("../repositories/AIServiceRepository");
const AgencyRepository_1 = require("../repositories/AgencyRepository");
const DATA_DIR = path.join(__dirname, '../../../../data/sqlite_backup');
// Helper to convert SQLite field names to camelCase and handle timestamps
function toCamelCase(obj) {
    const result = {};
    const timestampFields = ['createdAt', 'updatedAt', 'analyzedAt'];
    for (const [key, value] of Object.entries(obj)) {
        const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
        // Convert timestamp strings to Date objects
        if (timestampFields.includes(camelKey) && value && typeof value === 'string') {
            result[camelKey] = new Date(value);
        }
        else {
            result[camelKey] = value;
        }
    }
    return result;
}
async function seedProducts() {
    console.log('\n📦 Seeding products table...');
    const productsData = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'products.json'), 'utf-8'));
    const productRepo = new ProductRepository_1.ProductRepository();
    let count = 0;
    let errors = 0;
    for (const product of productsData) {
        try {
            const productData = toCamelCase(product);
            // Remove the auto-increment ID, let PostgreSQL generate it
            delete productData.id;
            await productRepo.insert(productData);
            count++;
            if (count % 100 === 0) {
                console.log(`   Inserted ${count} products...`);
            }
        }
        catch (error) {
            errors++;
            console.error(`   Error inserting product ${product.fedramp_id}:`, error.message);
        }
    }
    console.log(`✅ Products seeded: ${count} successful, ${errors} errors`);
    return count;
}
async function seedAIServices() {
    console.log('\n🤖 Seeding AI service analysis table...');
    const servicesData = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'ai_service_analysis.json'), 'utf-8'));
    const aiServiceRepo = new AIServiceRepository_1.AIServiceRepository();
    let count = 0;
    let errors = 0;
    for (const service of servicesData) {
        try {
            const serviceData = toCamelCase(service);
            delete serviceData.id;
            await aiServiceRepo.insertAnalysis(serviceData);
            count++;
            if (count % 50 === 0) {
                console.log(`   Inserted ${count} AI services...`);
            }
        }
        catch (error) {
            errors++;
            console.error(`   Error inserting AI service:`, error.message);
        }
    }
    console.log(`✅ AI services seeded: ${count} successful, ${errors} errors`);
    return count;
}
async function seedAgencies() {
    console.log('\n🏛️  Seeding agency AI usage table...');
    const agenciesData = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'agency_ai_usage.json'), 'utf-8'));
    const agencyRepo = new AgencyRepository_1.AgencyRepository();
    let count = 0;
    let errors = 0;
    for (const agency of agenciesData) {
        try {
            const agencyData = toCamelCase(agency);
            delete agencyData.id;
            await agencyRepo.insertUsage(agencyData);
            count++;
        }
        catch (error) {
            errors++;
            console.error(`   Error inserting agency:`, error.message);
        }
    }
    console.log(`✅ Agencies seeded: ${count} successful, ${errors} errors`);
    return count;
}
async function seedAgencyMatches() {
    console.log('\n🔗 Seeding agency service matches table...');
    const matchesData = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'agency_service_matches.json'), 'utf-8'));
    const agencyRepo = new AgencyRepository_1.AgencyRepository();
    let count = 0;
    let errors = 0;
    for (const match of matchesData) {
        try {
            const matchData = toCamelCase(match);
            delete matchData.id;
            await agencyRepo.insertMatch(matchData);
            count++;
        }
        catch (error) {
            errors++;
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
        // Seed in dependency order
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
        console.log('\n✨ Next steps:');
        console.log('   1. Verify data in Neon database');
        console.log('   2. Update frontend to use new database package');
        console.log('   3. Test all routes and pages\n');
    }
    catch (error) {
        console.error('\n❌ Migration failed:', error);
        process.exit(1);
    }
}
main();
//# sourceMappingURL=index.js.map