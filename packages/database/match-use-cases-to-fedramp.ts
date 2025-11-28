#!/usr/bin/env tsx
/**
 * Match AI Use Cases to FedRAMP Services
 * Creates intelligent matches based on providers, products, and capabilities
 */

import { neon } from "@neondatabase/serverless";
import * as dotenv from "dotenv";

dotenv.config({ path: "../../frontend/.env.local" });

const sql = neon(process.env.DATABASE_URL!);

interface UseCase {
  id: number;
  use_case_name: string;
  agency: string;
  commercial_ai_product: string | null;
  providers_detected: string[] | null;
  has_genai: boolean;
  has_llm: boolean;
  has_chatbot: boolean;
}

interface FedRAMPService {
  product_id: string;
  product_name: string;
  provider_name: string;
  service_name: string;
  has_ai: boolean;
  has_genai: boolean;
  has_llm: boolean;
}

async function matchUseCasesToFedRAMP() {
  console.log('🔗 Matching AI Use Cases to FedRAMP Services...\n');

  // Get all use cases with provider or product info
  const useCases = await sql<UseCase[]>`
    SELECT id, use_case_name, agency, commercial_ai_product, providers_detected,
           has_genai, has_llm, has_chatbot
    FROM ai_use_cases
    WHERE providers_detected IS NOT NULL
       OR commercial_ai_product IS NOT NULL
  `;

  console.log(`📊 Found ${useCases.length} use cases with provider/product information\n`);

  // Get all FedRAMP AI services
  const fedRAMPServices = await sql<FedRAMPService[]>`
    SELECT product_id, product_name, provider_name, service_name,
           has_ai, has_genai, has_llm
    FROM ai_service_analysis
    WHERE has_ai = true
  `;

  console.log(`📊 Found ${fedRAMPServices.length} FedRAMP AI services\n`);

  let highConfidenceMatches = 0;
  let mediumConfidenceMatches = 0;
  let lowConfidenceMatches = 0;
  let totalMatches = 0;

  // Clear existing matches
  await sql`DELETE FROM use_case_fedramp_matches`;

  for (const useCase of useCases) {
    const matches: Array<{
      service: FedRAMPService;
      confidence: 'high' | 'medium' | 'low';
      reason: string
    }> = [];

    // Parse providers if available
    const providers = useCase.providers_detected || [];

    for (const service of fedRAMPServices) {
      let confidence: 'high' | 'medium' | 'low' | null = null;
      let reason = '';

      // HIGH CONFIDENCE: Direct provider name match
      if (providers.length > 0) {
        for (const provider of providers) {
          const providerLower = provider.toLowerCase();
          const serviceLower = service.provider_name.toLowerCase();

          // Exact or substring match
          if (serviceLower.includes(providerLower) || providerLower.includes(serviceLower)) {
            confidence = 'high';
            reason = `Provider match: "${provider}" matches "${service.provider_name}"`;
            break;
          }
        }
      }

      // HIGH CONFIDENCE: Commercial product mention
      if (!confidence && useCase.commercial_ai_product) {
        const productLower = useCase.commercial_ai_product.toLowerCase();
        const serviceNameLower = service.service_name.toLowerCase();
        const productNameLower = service.product_name.toLowerCase();

        if (productLower.includes(serviceNameLower) ||
            serviceNameLower.includes(productLower) ||
            productLower.includes(productNameLower)) {
          confidence = 'high';
          reason = `Product match: Commercial product "${useCase.commercial_ai_product}" matches "${service.service_name}"`;
        }
      }

      // MEDIUM CONFIDENCE: AI capability match (GenAI + LLM)
      if (!confidence && useCase.has_genai && service.has_genai) {
        if (useCase.has_llm && service.has_llm) {
          confidence = 'medium';
          reason = 'Both use GenAI and LLM capabilities';
        } else {
          confidence = 'medium';
          reason = 'Both use GenAI capabilities';
        }
      }

      // MEDIUM CONFIDENCE: LLM match only
      if (!confidence && useCase.has_llm && service.has_llm) {
        confidence = 'medium';
        reason = 'Both use LLM capabilities';
      }

      // LOW CONFIDENCE: Chatbot use case with GenAI service
      if (!confidence && useCase.has_chatbot && service.has_genai) {
        confidence = 'low';
        reason = 'Chatbot use case could potentially use GenAI service';
      }

      // Add match if we found one
      if (confidence) {
        matches.push({ service, confidence, reason });
      }
    }

    // Insert matches into database
    for (const match of matches) {
      try {
        await sql`
          INSERT INTO use_case_fedramp_matches (
            use_case_id, product_id, provider_name, product_name,
            confidence, match_reason
          ) VALUES (
            ${useCase.id},
            ${match.service.product_id},
            ${match.service.provider_name},
            ${match.service.product_name},
            ${match.confidence},
            ${match.reason}
          )
        `;

        totalMatches++;
        if (match.confidence === 'high') highConfidenceMatches++;
        else if (match.confidence === 'medium') mediumConfidenceMatches++;
        else lowConfidenceMatches++;

      } catch (error: any) {
        // Skip duplicates
        if (!error.message.includes('duplicate')) {
          console.error(`Error inserting match: ${error.message}`);
        }
      }
    }

    if (matches.length > 0 && totalMatches % 50 === 0) {
      console.log(`   ✓ Created ${totalMatches} matches...`);
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log('✅ Matching complete!');
  console.log('='.repeat(60));
  console.log(`📊 Summary:`);
  console.log(`   Total Matches:    ${totalMatches}`);
  console.log(`   High Confidence:  ${highConfidenceMatches}`);
  console.log(`   Medium Confidence: ${mediumConfidenceMatches}`);
  console.log(`   Low Confidence:   ${lowConfidenceMatches}`);
  console.log('='.repeat(60));
}

matchUseCasesToFedRAMP().catch(console.error);
