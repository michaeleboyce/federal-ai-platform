CREATE TYPE "public"."confidence" AS ENUM('high', 'medium', 'low');--> statement-breakpoint
CREATE TABLE "agency_ai_usage" (
	"id" serial PRIMARY KEY NOT NULL,
	"agency_name" text NOT NULL,
	"agency_category" text NOT NULL,
	"has_staff_llm" text,
	"llm_name" text,
	"has_coding_assistant" text,
	"scope" text,
	"solution_type" text,
	"non_public_allowed" text,
	"other_ai_present" text,
	"tool_name" text,
	"tool_purpose" text,
	"notes" text,
	"sources" text,
	"analyzed_at" timestamp DEFAULT now() NOT NULL,
	"slug" text NOT NULL,
	CONSTRAINT "agency_ai_usage_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
CREATE TABLE "agency_service_matches" (
	"id" serial PRIMARY KEY NOT NULL,
	"agency_id" integer NOT NULL,
	"product_id" text NOT NULL,
	"provider_name" text NOT NULL,
	"product_name" text NOT NULL,
	"confidence" "confidence" NOT NULL,
	"match_reason" text,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ai_service_analysis" (
	"id" serial PRIMARY KEY NOT NULL,
	"product_id" varchar(255) NOT NULL,
	"product_name" text NOT NULL,
	"provider_name" text NOT NULL,
	"service_name" text NOT NULL,
	"has_ai" boolean DEFAULT false NOT NULL,
	"has_genai" boolean DEFAULT false NOT NULL,
	"has_llm" boolean DEFAULT false NOT NULL,
	"relevant_excerpt" text,
	"fedramp_status" text,
	"impact_level" text,
	"agencies" text,
	"auth_date" text,
	"analyzed_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "ai_service_analysis_product_id_unique" UNIQUE("product_id")
);
--> statement-breakpoint
CREATE TABLE "ai_use_case_details" (
	"use_case_id" integer PRIMARY KEY NOT NULL,
	"development_approach" text,
	"procurement_instrument" text,
	"supports_hisp" text,
	"which_hisp" text,
	"which_public_service" text,
	"disseminates_to_public" text,
	"involves_pii" text,
	"privacy_assessed" text,
	"has_data_catalog" text,
	"agency_owned_data" text,
	"data_documentation" text,
	"demographic_variables" text,
	"has_custom_code" text,
	"has_code_access" text,
	"code_link" text,
	"has_ato" text,
	"system_name" text,
	"wait_time_dev_tools" text,
	"centralized_intake" text,
	"has_compute_process" text,
	"timely_communication" text,
	"infrastructure_reuse" text,
	"internal_review" text,
	"requested_extension" text,
	"impact_assessment" text,
	"operational_testing" text,
	"key_risks" text,
	"independent_evaluation" text,
	"performance_monitoring" text,
	"autonomous_decision" text,
	"public_notice" text,
	"influences_decisions" text,
	"disparity_mitigation" text,
	"stakeholder_feedback" text,
	"fallback_process" text,
	"opt_out_mechanism" text,
	"info_quality_compliance" text,
	"search_text" text
);
--> statement-breakpoint
CREATE TABLE "ai_use_cases" (
	"id" serial PRIMARY KEY NOT NULL,
	"use_case_name" text NOT NULL,
	"agency" text NOT NULL,
	"agency_abbreviation" text,
	"bureau" text,
	"use_case_topic_area" text,
	"other_use_case_topic_area" text,
	"intended_purpose" text,
	"outputs" text,
	"stage_of_development" text,
	"is_rights_safety_impacting" text,
	"domain_category" text,
	"date_initiated" text,
	"date_implemented" text,
	"date_retired" text,
	"has_llm" boolean DEFAULT false NOT NULL,
	"has_genai" boolean DEFAULT false NOT NULL,
	"has_chatbot" boolean DEFAULT false NOT NULL,
	"has_gp_markers" boolean DEFAULT false NOT NULL,
	"has_coding_assistant" boolean DEFAULT false NOT NULL,
	"has_coding_agent" boolean DEFAULT false NOT NULL,
	"has_classic_ml" boolean DEFAULT false NOT NULL,
	"has_rpa" boolean DEFAULT false NOT NULL,
	"has_rules" boolean DEFAULT false NOT NULL,
	"general_purpose_chatbot" boolean DEFAULT false NOT NULL,
	"domain_chatbot" boolean DEFAULT false NOT NULL,
	"coding_assistant" boolean DEFAULT false NOT NULL,
	"coding_agent" boolean DEFAULT false NOT NULL,
	"genai_flag" boolean DEFAULT false NOT NULL,
	"ai_type_classic_ml" boolean DEFAULT false NOT NULL,
	"ai_type_rpa_rules" boolean DEFAULT false NOT NULL,
	"providers_detected" jsonb DEFAULT '[]'::jsonb,
	"commercial_ai_product" text,
	"analyzed_at" timestamp DEFAULT now() NOT NULL,
	"slug" text NOT NULL,
	CONSTRAINT "ai_use_cases_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
CREATE TABLE "use_case_fedramp_matches" (
	"id" serial PRIMARY KEY NOT NULL,
	"use_case_id" integer NOT NULL,
	"product_id" text NOT NULL,
	"provider_name" text NOT NULL,
	"product_name" text NOT NULL,
	"confidence" "confidence" NOT NULL,
	"match_reason" text,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "agency_service_matches" ADD CONSTRAINT "agency_service_matches_agency_id_agency_ai_usage_id_fk" FOREIGN KEY ("agency_id") REFERENCES "public"."agency_ai_usage"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "ai_use_case_details" ADD CONSTRAINT "ai_use_case_details_use_case_id_ai_use_cases_id_fk" FOREIGN KEY ("use_case_id") REFERENCES "public"."ai_use_cases"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "use_case_fedramp_matches" ADD CONSTRAINT "use_case_fedramp_matches_use_case_id_ai_use_cases_id_fk" FOREIGN KEY ("use_case_id") REFERENCES "public"."ai_use_cases"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "idx_agency_name" ON "agency_ai_usage" USING btree ("agency_name");--> statement-breakpoint
CREATE INDEX "idx_agency_category" ON "agency_ai_usage" USING btree ("agency_category");--> statement-breakpoint
CREATE UNIQUE INDEX "idx_agency_slug" ON "agency_ai_usage" USING btree ("slug");--> statement-breakpoint
CREATE INDEX "idx_agency_service_agency" ON "agency_service_matches" USING btree ("agency_id");--> statement-breakpoint
CREATE INDEX "idx_agency_service_product" ON "agency_service_matches" USING btree ("product_id");--> statement-breakpoint
CREATE INDEX "idx_agency_service_confidence" ON "agency_service_matches" USING btree ("confidence");--> statement-breakpoint
CREATE INDEX "idx_ai_service_product" ON "ai_service_analysis" USING btree ("product_id");--> statement-breakpoint
CREATE INDEX "idx_ai_service_provider" ON "ai_service_analysis" USING btree ("provider_name");--> statement-breakpoint
CREATE INDEX "idx_ai_service_has_ai" ON "ai_service_analysis" USING btree ("has_ai");--> statement-breakpoint
CREATE INDEX "idx_ai_service_has_genai" ON "ai_service_analysis" USING btree ("has_genai");--> statement-breakpoint
CREATE INDEX "idx_ai_service_has_llm" ON "ai_service_analysis" USING btree ("has_llm");--> statement-breakpoint
CREATE INDEX "idx_use_case_agency" ON "ai_use_cases" USING btree ("agency");--> statement-breakpoint
CREATE INDEX "idx_use_case_domain" ON "ai_use_cases" USING btree ("domain_category");--> statement-breakpoint
CREATE INDEX "idx_use_case_stage" ON "ai_use_cases" USING btree ("stage_of_development");--> statement-breakpoint
CREATE INDEX "idx_use_case_genai" ON "ai_use_cases" USING btree ("genai_flag");--> statement-breakpoint
CREATE INDEX "idx_use_case_llm" ON "ai_use_cases" USING btree ("has_llm");--> statement-breakpoint
CREATE UNIQUE INDEX "idx_use_case_slug" ON "ai_use_cases" USING btree ("slug");--> statement-breakpoint
CREATE INDEX "idx_use_case_fedramp_use_case" ON "use_case_fedramp_matches" USING btree ("use_case_id");--> statement-breakpoint
CREATE INDEX "idx_use_case_fedramp_product" ON "use_case_fedramp_matches" USING btree ("product_id");--> statement-breakpoint
CREATE INDEX "idx_use_case_fedramp_confidence" ON "use_case_fedramp_matches" USING btree ("confidence");