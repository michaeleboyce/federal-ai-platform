#!/usr/bin/env tsx
/**
 * Load Federal AI Use Case Inventory data from CSV into PostgreSQL
 * Processes 2,133+ use cases from 43+ federal agencies
 */

import * as fs from 'fs';
import * as path from 'path';
import { parse } from 'csv-parse/sync';
import { neon } from "@neondatabase/serverless";
import * as dotenv from "dotenv";

dotenv.config({ path: "../../frontend/.env.local" });

const sql = neon(process.env.DATABASE_URL!);
const CSV_PATH = path.join(process.env.HOME!, 'Downloads', 'ai_inventory_enriched_with_tags.csv');

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function parseProviders(text: string | null): string | null {
  if (!text) return null;

  const providers = text.split(',').map(p => p.trim()).filter(p => p);
  return providers.length > 0 ? JSON.stringify(providers) : null;
}

async function loadUseCases() {
  console.log('🚀 Loading Federal AI Use Case Inventory...\n');
  console.log(`📁 Reading CSV from: ${CSV_PATH}\n`);

  // Read and parse CSV (remove BOM if present)
  let fileContent = fs.readFileSync(CSV_PATH, 'utf-8');
  // Remove BOM if present
  if (fileContent.charCodeAt(0) === 0xFEFF) {
    fileContent = fileContent.slice(1);
  }
  const records = parse(fileContent, {
    columns: true,
    skip_empty_lines: true,
    bom: true,
  });

  console.log(`📊 Found ${records.length} use cases to import\n`);

  let successCount = 0;
  let errorCount = 0;
  let detailsCount = 0;

  for (const record of records) {
    try {
      // Skip if no use case name
      if (!record.use_case_name || record.use_case_name.trim() === '') {
        continue;
      }

      // Create slug
      const slug = slugify(`${record.agency || ''}-${record.use_case_name || ''}`);

      // Insert main use case
      const result = await sql`
        INSERT INTO ai_use_cases (
          use_case_name, agency, agency_abbreviation, bureau,
          use_case_topic_area, other_use_case_topic_area,
          intended_purpose, outputs,
          stage_of_development, is_rights_safety_impacting, domain_category,
          date_initiated, date_implemented, date_retired,
          has_llm, has_genai, has_chatbot, has_gp_markers,
          has_coding_assistant, has_coding_agent, has_classic_ml,
          has_rpa, has_rules,
          general_purpose_chatbot, domain_chatbot, coding_assistant,
          coding_agent, genai_flag, ai_type_classic_ml, ai_type_rpa_rules,
          providers_detected, commercial_ai_product,
          slug
        ) VALUES (
          ${record.use_case_name},
          ${record.agency},
          ${record.agency_abbreviation},
          ${record.bureau},
          ${record.use_case_topic_area},
          ${record.other_use_case_topic_area},
          ${record.what_is_the_intended_purpose_and_expected_benefits_of_the_ai},
          ${record.describe_the_ai_system_s_outputs},
          ${record.stage_of_development},
          ${record.is_the_ai_use_case_rights_impacting_safety_impacting_both_or_neither},
          ${record._domain_category || null},
          ${record.date_initiated},
          ${record.date_implemented},
          ${record.date_retired},
          ${record._has_llm === 'True'},
          ${record._has_genai_signal === 'True'},
          ${record._has_chatbot === 'True'},
          ${record._has_gp_markers === 'True'},
          ${record._has_coding_assistant === 'True'},
          ${record._has_coding_agent === 'True'},
          ${record._has_classic_ml === 'True'},
          ${record._has_rpa === 'True'},
          ${record._has_rules === 'True'},
          ${record._general_purpose_chatbot === 'True'},
          ${record._domain_chatbot === 'True'},
          ${record._coding_assistant === 'True'},
          ${record._coding_agent === 'True'},
          ${record._genai_flag === 'True'},
          ${record._ai_type_classic_ml === 'True'},
          ${record._ai_type_rpa_rules === 'True'},
          ${parseProviders(record._providers_detected)},
          ${record.is_the_ai_use_case_found_in_the_below_list_of_general_commercial_ai_products_and_services},
          ${slug}
        ) RETURNING id
      `;

      const useCaseId = result[0].id;

      // Insert details
      await sql`
        INSERT INTO ai_use_case_details (
          use_case_id, development_approach, procurement_instrument,
          supports_hisp, which_hisp, which_public_service, disseminates_to_public,
          involves_pii, privacy_assessed, has_data_catalog, agency_owned_data,
          data_documentation, demographic_variables,
          has_custom_code, has_code_access, code_link, has_ato, system_name,
          wait_time_dev_tools, centralized_intake, has_compute_process,
          timely_communication, infrastructure_reuse,
          internal_review, requested_extension, impact_assessment,
          operational_testing, key_risks, independent_evaluation,
          performance_monitoring, autonomous_decision, public_notice,
          influences_decisions, disparity_mitigation, stakeholder_feedback,
          fallback_process, opt_out_mechanism, info_quality_compliance,
          search_text
        ) VALUES (
          ${useCaseId},
          ${record.was_the_ai_system_involved_in_this_use_case_developed_or_is_it_to_be_developed_under_contract_s_or_in_house},
          ${record.provide_the_procurement_instrument_identifier_s_piid_of_the_contract_s_used},
          ${record.is_this_ai_use_case_supporting_a_high_impact_service_provider_hisp_public_facing_service},
          ${record.which_hisp_is_the_ai_use_case_supporting},
          ${record.which_public_facing_service_is_the_ai_use_case_supporting},
          ${record.does_this_ai_use_case_disseminate_information_to_the_public},
          ${record.does_this_ai_use_case_involve_personally_identifiable_information_pii_that_is_maintained_by_the_agency},
          ${record.has_the_senior_agency_official_for_privacy_saop_assessed_the_privacy_risks_associated_with_this_ai_use_case},
          ${record.do_you_have_access_to_an_enterprise_data_catalog_or_agency_wide_data_repository_that_enables_you_to_identify_whether_or_not_the_necessary_datasets_exist_and_are_ready_to_develop_your_use_case},
          ${record.describe_any_agency_owned_data_used_to_train_fine_tune_and_or_evaluate_performance_of_the_model_s_used_in_this_use_case},
          ${record.is_there_available_documentation_for_the_model_training_and_evaluation_data_that_demonstrates_the_degree_to_which_it_is_appropriate_to_be_used_in_analysis_or_for_making_predictions},
          ${record.which_if_any_demographic_variables_does_the_ai_use_case_explicitly_use_as_model_features},
          ${record.does_this_project_include_custom_developed_code},
          ${record.does_the_agency_have_access_to_the_code_associated_with_the_ai_use_case},
          ${record.if_the_code_is_open_source_provide_the_link_for_the_publicly_available_source_code},
          ${record.does_this_ai_use_case_have_an_associated_authority_to_operate_ato_for_an_ai_system},
          ${record.system_name},
          ${record.how_long_have_you_waited_for_the_necessary_developer_tools_to_implement_the_ai_use_case},
          ${record.for_this_ai_use_case_is_the_required_it_infrastructure_provisioned_via_a_centralized_intake_form_or_process_inside_the_agency},
          ${record.do_you_have_a_process_in_place_to_request_access_to_computing_resources_for_model_training_and_development_of_the_ai_involved_in_this_use_case},
          ${record.has_communication_regarding_the_provisioning_of_your_requested_resources_been_timely},
          ${record.how_are_existing_data_science_tools_libraries_data_products_and_internally_developed_ai_infrastructure_being_re_used_for_the_current_ai_use_case},
          ${record.has_information_regarding_the_ai_use_case_including_performance_metrics_and_intended_use_of_the_model_been_made_available_for_review_and_feedback_within_the_agency},
          ${record.has_your_agency_requested_an_extension_to_implement_the_minimum_risk_management_practices_for_this_ai_use_case},
          ${record.has_an_ai_impact_assessment_been_conducted_for_this_ai_use_case},
          ${record.has_the_ai_use_case_been_tested_in_operational_or_real_world_environments_to_understand_the_performance_and_impact_it_may_have_on_affected_individuals_or_communities},
          ${record.what_are_the_key_risks_from_using_the_ai_for_this_particular_use_case_and_how_were_they_identified},
          ${record.has_an_independent_evaluation_of_the_ai_use_case_been_conducted},
          ${record.is_there_a_process_to_monitor_performance_of_the_ai_system_s_functionality_and_changes_to_its_impact_on_rights_or_safety_as_part_of_the_post_deployment_plan_for_the_ai_use_case},
          ${record.for_this_particular_use_case_can_the_ai_carry_out_a_decision_or_action_without_direct_human_involvement_that_could_result_in_a_significant_impact_on_rights_or_safety},
          ${record.how_is_the_agency_providing_reasonable_and_timely_notice_regarding_the_use_of_ai_when_people_interact_with_an_ai_enabled_service_as_a_result_of_this_ai_use_case},
          ${record.is_the_ai_used_to_significantly_influence_or_inform_decisions_or_actions_that_could_have_an_adverse_or_negative_impact_on_specific_individuals_or_groups},
          ${record.what_steps_has_the_agency_taken_to_detect_and_mitigate_significant_disparities_in_the_model_s_performance_across_demographic_groups_for_this_ai_use_case},
          ${record.what_steps_has_the_agency_taken_to_consult_and_incorporate_feedback_from_groups_affected_by_this_ai_use_case},
          ${record.is_there_an_established_fallback_and_escalation_process_for_this_ai_use_case_in_the_event_that_an_impacted_individual_or_group_would_like_to_appeal_or_contest_the_ai_system_s_outcome},
          ${record.where_practicable_and_consistent_with_applicable_law_and_governmentwide_policy_is_there_an_established_mechanism_for_individuals_to_opt_out_from_the_ai_functionality_in_favor_of_a_human_alternative},
          ${record.how_is_the_agency_ensuring_compliance_with_information_quality_act_guidelines_if_applicable},
          ${record._search_text || null}
        )
      `;

      successCount++;
      detailsCount++;

      if (successCount % 100 === 0) {
        console.log(`   ✓ Imported ${successCount} use cases...`);
      }
    } catch (error: any) {
      errorCount++;
      if (errorCount < 5) {
        console.error(`   ✗ Error importing use case: ${error.message}`);
      }
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log('✅ Import complete!');
  console.log('='.repeat(60));
  console.log(`📊 Summary:`);
  console.log(`   Use Cases:  ${successCount} imported`);
  console.log(`   Details:    ${detailsCount} imported`);
  console.log(`   Errors:     ${errorCount}`);
  console.log('='.repeat(60));
}

loadUseCases().catch(console.error);
