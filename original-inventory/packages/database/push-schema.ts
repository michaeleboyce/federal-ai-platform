// Manually push schema to Neon database
import { neon } from "@neondatabase/serverless";
import * as dotenv from "dotenv";

dotenv.config({ path: "../../frontend/.env.local" });

const sql = neon(process.env.DATABASE_URL!);

async function pushSchema() {
  console.log("🚀 Pushing schema to Neon database...\n");

  try {
    // Create enums
    console.log("Creating enums...");
    await sql`CREATE TYPE agency_category AS ENUM('staff_llm', 'specialized')`;
    await sql`CREATE TYPE match_confidence AS ENUM('high', 'medium', 'low')`;
    await sql`CREATE TYPE product_status AS ENUM('FedRAMP Authorized', 'FedRAMP Ready', 'In Process', 'FedRAMP Connect', 'Compliant')`;
    await sql`CREATE TYPE service_model AS ENUM('SaaS', 'PaaS', 'IaaS', 'Other')`;

    // Create products table
    console.log("Creating products table...");
    await sql`
      CREATE TABLE products (
        id serial PRIMARY KEY,
        fedramp_id text NOT NULL UNIQUE,
        cloud_service_provider text,
        cloud_service_offering text,
        service_description text,
        business_categories text,
        service_model text,
        status text,
        independent_assessor text,
        authorizations text,
        reuse text,
        parent_agency text,
        sub_agency text,
        ato_issuance_date text,
        fedramp_authorization_date text,
        annual_assessment_date text,
        ato_expiration_date text,
        html_scraped boolean DEFAULT false NOT NULL,
        html_path text,
        created_at timestamp with time zone DEFAULT now() NOT NULL,
        updated_at timestamp with time zone DEFAULT now() NOT NULL
      )
    `;

    // Create AI service analysis table
    console.log("Creating ai_service_analysis table...");
    await sql`
      CREATE TABLE ai_service_analysis (
        id serial PRIMARY KEY,
        product_id text NOT NULL REFERENCES products(fedramp_id),
        product_name text,
        provider_name text,
        service_name text,
        has_ai boolean DEFAULT false NOT NULL,
        has_genai boolean DEFAULT false NOT NULL,
        has_llm boolean DEFAULT false NOT NULL,
        relevant_excerpt text,
        fedramp_status text,
        impact_level text,
        agencies text,
        auth_date text,
        analyzed_at timestamp with time zone DEFAULT now() NOT NULL
      )
    `;

    // Create product AI analysis runs table
    console.log("Creating product_ai_analysis_runs table...");
    await sql`
      CREATE TABLE product_ai_analysis_runs (
        id serial PRIMARY KEY,
        product_id text NOT NULL REFERENCES products(fedramp_id),
        product_name text,
        provider_name text,
        analyzed_at timestamp with time zone DEFAULT now() NOT NULL,
        ai_services_found integer DEFAULT 0 NOT NULL
      )
    `;

    // Create agency AI usage table
    console.log("Creating agency_ai_usage table...");
    await sql`
      CREATE TABLE agency_ai_usage (
        id serial PRIMARY KEY,
        agency_name text NOT NULL,
        agency_category text NOT NULL,
        has_staff_llm text,
        llm_name text,
        has_coding_assistant text,
        scope text,
        solution_type text,
        non_public_allowed text,
        other_ai_present text,
        tool_name text,
        tool_purpose text,
        notes text,
        sources text,
        analyzed_at timestamp with time zone DEFAULT now() NOT NULL,
        slug text
      )
    `;

    // Create agency service matches table
    console.log("Creating agency_service_matches table...");
    await sql`
      CREATE TABLE agency_service_matches (
        id serial PRIMARY KEY,
        agency_id integer NOT NULL REFERENCES agency_ai_usage(id),
        product_id text NOT NULL REFERENCES products(fedramp_id),
        provider_name text NOT NULL,
        product_name text NOT NULL,
        service_name text,
        confidence text NOT NULL,
        match_reason text,
        created_at timestamp with time zone DEFAULT now() NOT NULL
      )
    `;

    // Create AI use cases table
    console.log("Creating ai_use_cases table...");
    await sql`
      CREATE TABLE ai_use_cases (
        id serial PRIMARY KEY,
        use_case_name text NOT NULL,
        agency text NOT NULL,
        agency_abbreviation text,
        bureau text,
        use_case_topic_area text,
        other_use_case_topic_area text,
        intended_purpose text,
        outputs text,
        stage_of_development text,
        is_rights_safety_impacting text,
        domain_category text,
        date_initiated text,
        date_implemented text,
        date_retired text,
        has_llm boolean DEFAULT false NOT NULL,
        has_genai boolean DEFAULT false NOT NULL,
        has_chatbot boolean DEFAULT false NOT NULL,
        has_gp_markers boolean DEFAULT false NOT NULL,
        has_coding_assistant boolean DEFAULT false NOT NULL,
        has_coding_agent boolean DEFAULT false NOT NULL,
        has_classic_ml boolean DEFAULT false NOT NULL,
        has_rpa boolean DEFAULT false NOT NULL,
        has_rules boolean DEFAULT false NOT NULL,
        general_purpose_chatbot boolean DEFAULT false NOT NULL,
        domain_chatbot boolean DEFAULT false NOT NULL,
        coding_assistant boolean DEFAULT false NOT NULL,
        coding_agent boolean DEFAULT false NOT NULL,
        genai_flag boolean DEFAULT false NOT NULL,
        ai_type_classic_ml boolean DEFAULT false NOT NULL,
        ai_type_rpa_rules boolean DEFAULT false NOT NULL,
        providers_detected text,
        commercial_ai_product text,
        analyzed_at timestamp with time zone DEFAULT now() NOT NULL,
        slug text NOT NULL UNIQUE
      )
    `;

    // Create AI use case details table
    console.log("Creating ai_use_case_details table...");
    await sql`
      CREATE TABLE ai_use_case_details (
        use_case_id integer PRIMARY KEY REFERENCES ai_use_cases(id),
        development_approach text,
        procurement_instrument text,
        supports_hisp text,
        which_hisp text,
        which_public_service text,
        disseminates_to_public text,
        involves_pii text,
        privacy_assessed text,
        has_data_catalog text,
        agency_owned_data text,
        data_documentation text,
        demographic_variables text,
        has_custom_code text,
        has_code_access text,
        code_link text,
        has_ato text,
        system_name text,
        wait_time_dev_tools text,
        centralized_intake text,
        has_compute_process text,
        timely_communication text,
        infrastructure_reuse text,
        internal_review text,
        requested_extension text,
        impact_assessment text,
        operational_testing text,
        key_risks text,
        independent_evaluation text,
        performance_monitoring text,
        autonomous_decision text,
        public_notice text,
        influences_decisions text,
        disparity_mitigation text,
        stakeholder_feedback text,
        fallback_process text,
        opt_out_mechanism text,
        info_quality_compliance text,
        search_text text
      )
    `;

    // Create use case FedRAMP matches table
    console.log("Creating use_case_fedramp_matches table...");
    await sql`
      CREATE TABLE use_case_fedramp_matches (
        id serial PRIMARY KEY,
        use_case_id integer NOT NULL REFERENCES ai_use_cases(id),
        product_id text NOT NULL REFERENCES products(fedramp_id),
        provider_name text NOT NULL,
        product_name text NOT NULL,
        confidence text NOT NULL,
        match_reason text
      )
    `;

    console.log("\n✅ Schema pushed successfully!");
    console.log("   All tables and enums created in Neon database\n");
  } catch (error) {
    console.error("Error pushing schema:", error);
  }
}

pushSchema();
