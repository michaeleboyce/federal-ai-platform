#!/usr/bin/env python3
"""
Load Federal AI Use Case Inventory data from CSV into SQLite database.

This script processes the enriched AI inventory CSV containing 2,133+ use cases
from 43+ federal agencies with comprehensive metadata and AI classification.
"""

import csv
import sqlite3
import json
import re
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / 'data'
DB_PATH = DATA_DIR / 'fedramp.db'
CSV_PATH = Path.home() / 'Downloads' / 'ai_inventory_enriched_with_tags.csv'

def create_tables(conn):
    """Create database tables for AI use case inventory."""
    cursor = conn.cursor()

    # Main use cases table - optimized for fast queries
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_use_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            use_case_name TEXT NOT NULL,
            agency TEXT NOT NULL,
            agency_abbreviation TEXT,
            bureau TEXT,
            use_case_topic_area TEXT,
            other_use_case_topic_area TEXT,

            -- Purpose and outputs (summarized for table views)
            intended_purpose TEXT,
            outputs TEXT,

            -- Classification
            stage_of_development TEXT,
            is_rights_safety_impacting TEXT,
            domain_category TEXT,

            -- Dates
            date_initiated TEXT,
            date_implemented TEXT,
            date_retired TEXT,

            -- AI Type Flags (for filtering)
            has_llm BOOLEAN DEFAULT 0,
            has_genai BOOLEAN DEFAULT 0,
            has_chatbot BOOLEAN DEFAULT 0,
            has_gp_markers BOOLEAN DEFAULT 0,
            has_coding_assistant BOOLEAN DEFAULT 0,
            has_coding_agent BOOLEAN DEFAULT 0,
            has_classic_ml BOOLEAN DEFAULT 0,
            has_rpa BOOLEAN DEFAULT 0,
            has_rules BOOLEAN DEFAULT 0,

            -- AI Type Categories (for badges)
            general_purpose_chatbot BOOLEAN DEFAULT 0,
            domain_chatbot BOOLEAN DEFAULT 0,
            coding_assistant BOOLEAN DEFAULT 0,
            coding_agent BOOLEAN DEFAULT 0,
            genai_flag BOOLEAN DEFAULT 0,
            ai_type_classic_ml BOOLEAN DEFAULT 0,
            ai_type_rpa_rules BOOLEAN DEFAULT 0,

            -- Providers (stored as JSON array)
            providers_detected TEXT,

            -- Commercial AI products used
            commercial_ai_product TEXT,

            -- Metadata
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            slug TEXT UNIQUE NOT NULL
        )
    ''')

    # Extended details table - full metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_use_case_details (
            use_case_id INTEGER PRIMARY KEY,

            -- Development and procurement
            development_approach TEXT,
            procurement_instrument TEXT,

            -- High-impact service
            supports_hisp TEXT,
            which_hisp TEXT,
            which_public_service TEXT,
            disseminates_to_public TEXT,

            -- Privacy and data
            involves_pii TEXT,
            privacy_assessed TEXT,
            has_data_catalog TEXT,
            agency_owned_data TEXT,
            data_documentation TEXT,
            demographic_variables TEXT,

            -- Code and systems
            has_custom_code TEXT,
            has_code_access TEXT,
            code_link TEXT,
            has_ato TEXT,
            system_name TEXT,

            -- Infrastructure
            wait_time_dev_tools TEXT,
            centralized_intake TEXT,
            has_compute_process TEXT,
            timely_communication TEXT,
            infrastructure_reuse TEXT,

            -- Review and testing
            internal_review TEXT,
            requested_extension TEXT,
            impact_assessment TEXT,
            operational_testing TEXT,
            key_risks TEXT,
            independent_evaluation TEXT,

            -- Monitoring and governance
            performance_monitoring TEXT,
            autonomous_decision TEXT,
            public_notice TEXT,
            influences_decisions TEXT,
            disparity_mitigation TEXT,
            stakeholder_feedback TEXT,
            fallback_process TEXT,
            opt_out_mechanism TEXT,

            -- Information quality
            info_quality_compliance TEXT,

            -- Full search text
            search_text TEXT,

            FOREIGN KEY (use_case_id) REFERENCES ai_use_cases (id)
        )
    ''')

    # Linking table for use cases to FedRAMP services
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS use_case_fedramp_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            use_case_id INTEGER NOT NULL,
            product_id TEXT NOT NULL,
            provider_name TEXT NOT NULL,
            product_name TEXT NOT NULL,
            confidence TEXT NOT NULL CHECK(confidence IN ('high', 'medium', 'low')),
            match_reason TEXT,
            FOREIGN KEY (use_case_id) REFERENCES ai_use_cases (id)
        )
    ''')

    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_use_case_agency ON ai_use_cases(agency)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_use_case_domain ON ai_use_cases(domain_category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_use_case_stage ON ai_use_cases(stage_of_development)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_use_case_genai ON ai_use_cases(genai_flag)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_use_case_llm ON ai_use_cases(has_llm)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fedramp_match_product ON use_case_fedramp_matches(product_id)')

    conn.commit()
    print("✅ Database tables created")


def generate_slug(use_case_name, agency_abbr, row_id):
    """Generate unique URL-friendly slug from use case name."""
    # Start with use case name
    slug = use_case_name.lower() if use_case_name else f"use-case-{row_id}"

    # Remove special characters, keep alphanumeric and spaces
    slug = re.sub(r'[^\w\s-]', '', slug)

    # Replace spaces with hyphens
    slug = re.sub(r'[-\s]+', '-', slug)

    # Trim to reasonable length and add agency prefix
    slug = slug[:80].strip('-')

    # Add agency abbreviation as prefix if available
    if agency_abbr:
        agency_slug = re.sub(r'[^\w]', '', agency_abbr.lower())
        slug = f"{agency_slug}-{slug}"

    return slug


def parse_providers(providers_str):
    """Parse providers_detected string into clean JSON array."""
    if not providers_str or providers_str == '[]':
        return '[]'

    try:
        # Remove brackets and split by comma
        providers_str = providers_str.strip('[]')
        if not providers_str:
            return '[]'

        providers = [p.strip().strip("'\"") for p in providers_str.split(',')]
        providers = [p for p in providers if p]  # Remove empty strings

        return json.dumps(providers)
    except:
        return '[]'


def normalize_boolean(value):
    """Convert various boolean representations to 1/0."""
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, str):
        val_lower = value.lower().strip()
        if val_lower in ('true', 't', 'yes', 'y', '1'):
            return 1
    return 0


def load_use_cases(conn, csv_path):
    """Load use cases from CSV into database."""
    cursor = conn.cursor()

    count = 0
    skipped = 0

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            # Skip empty rows
            if not row.get('use_case_name') or not row.get('agency'):
                skipped += 1
                continue

            # Generate slug
            slug = generate_slug(
                row.get('use_case_name', ''),
                row.get('agency_abbreviation', ''),
                row_num
            )

            # Check for slug collision, make unique if needed
            cursor.execute('SELECT COUNT(*) FROM ai_use_cases WHERE slug = ?', (slug,))
            if cursor.fetchone()[0] > 0:
                slug = f"{slug}-{row_num}"

            # Parse providers
            providers = parse_providers(row.get('_providers_detected', ''))

            # Insert main use case record
            try:
                cursor.execute('''
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
                        providers_detected, commercial_ai_product, slug
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('use_case_name', ''),
                    row.get('agency', ''),
                    row.get('agency_abbreviation', ''),
                    row.get('bureau', ''),
                    row.get('use_case_topic_area', ''),
                    row.get('other_use_case_topic_area', ''),
                    row.get('what_is_the_intended_purpose_and_expected_benefits_of_the_ai', ''),
                    row.get('describe_the_ai_system_s_outputs', ''),
                    row.get('stage_of_development', ''),
                    row.get('is_the_ai_use_case_rights_impacting_safety_impacting_both_or_neither', ''),
                    row.get('_domain_category', ''),
                    row.get('date_initiated', ''),
                    row.get('date_implemented', ''),
                    row.get('date_retired', ''),
                    normalize_boolean(row.get('_has_llm', '')),
                    normalize_boolean(row.get('_has_genai_signal', '')),
                    normalize_boolean(row.get('_has_chatbot', '')),
                    normalize_boolean(row.get('_has_gp_markers', '')),
                    normalize_boolean(row.get('_has_coding_assistant', '')),
                    normalize_boolean(row.get('_has_coding_agent', '')),
                    normalize_boolean(row.get('_has_classic_ml', '')),
                    normalize_boolean(row.get('_has_rpa', '')),
                    normalize_boolean(row.get('_has_rules', '')),
                    normalize_boolean(row.get('_general_purpose_chatbot', '')),
                    normalize_boolean(row.get('_domain_chatbot', '')),
                    normalize_boolean(row.get('_coding_assistant', '')),
                    normalize_boolean(row.get('_coding_agent', '')),
                    normalize_boolean(row.get('_genai_flag', '')),
                    normalize_boolean(row.get('_ai_type_classic_ml', '')),
                    normalize_boolean(row.get('_ai_type_rpa_rules', '')),
                    providers,
                    row.get('is_the_ai_use_case_found_in_the_below_list_of_general_commercial_ai_products_and_services', ''),
                    slug
                ))

                use_case_id = cursor.lastrowid

                # Insert extended details
                cursor.execute('''
                    INSERT INTO ai_use_case_details (
                        use_case_id,
                        development_approach, procurement_instrument,
                        supports_hisp, which_hisp, which_public_service,
                        disseminates_to_public, info_quality_compliance,
                        involves_pii, privacy_assessed,
                        has_data_catalog, agency_owned_data, data_documentation,
                        demographic_variables,
                        has_custom_code, has_code_access, code_link,
                        has_ato, system_name,
                        wait_time_dev_tools, centralized_intake,
                        has_compute_process, timely_communication,
                        infrastructure_reuse, internal_review,
                        requested_extension, impact_assessment,
                        operational_testing, key_risks,
                        independent_evaluation, performance_monitoring,
                        autonomous_decision, public_notice,
                        influences_decisions, disparity_mitigation,
                        stakeholder_feedback, fallback_process,
                        opt_out_mechanism, search_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    use_case_id,
                    row.get('was_the_ai_system_involved_in_this_use_case_developed_or_is_it_to_be_developed_under_contract_s_or_in_house', ''),
                    row.get('provide_the_procurement_instrument_identifier_s_piid_of_the_contract_s_used', ''),
                    row.get('is_this_ai_use_case_supporting_a_high_impact_service_provider_hisp_public_facing_service', ''),
                    row.get('which_hisp_is_the_ai_use_case_supporting', ''),
                    row.get('which_public_facing_service_is_the_ai_use_case_supporting', ''),
                    row.get('does_this_ai_use_case_disseminate_information_to_the_public', ''),
                    row.get('how_is_the_agency_ensuring_compliance_with_information_quality_act_guidelines_if_applicable', ''),
                    row.get('does_this_ai_use_case_involve_personally_identifiable_information_pii_that_is_maintained_by_the_agency', ''),
                    row.get('has_the_senior_agency_official_for_privacy_saop_assessed_the_privacy_risks_associated_with_this_ai_use_case', ''),
                    row.get('do_you_have_access_to_an_enterprise_data_catalog_or_agency_wide_data_repository_that_enables_you_to_identify_whether_or_not_the_necessary_datasets_exist_and_are_ready_to_develop_your_use_case', ''),
                    row.get('describe_any_agency_owned_data_used_to_train_fine_tune_and_or_evaluate_performance_of_the_model_s_used_in_this_use_case', ''),
                    row.get('is_there_available_documentation_for_the_model_training_and_evaluation_data_that_demonstrates_the_degree_to_which_it_is_appropriate_to_be_used_in_analysis_or_for_making_predictions', ''),
                    row.get('which_if_any_demographic_variables_does_the_ai_use_case_explicitly_use_as_model_features', ''),
                    row.get('does_this_project_include_custom_developed_code', ''),
                    row.get('does_the_agency_have_access_to_the_code_associated_with_the_ai_use_case', ''),
                    row.get('if_the_code_is_open_source_provide_the_link_for_the_publicly_available_source_code', ''),
                    row.get('does_this_ai_use_case_have_an_associated_authority_to_operate_ato_for_an_ai_system', ''),
                    row.get('system_name', ''),
                    row.get('how_long_have_you_waited_for_the_necessary_developer_tools_to_implement_the_ai_use_case', ''),
                    row.get('for_this_ai_use_case_is_the_required_it_infrastructure_provisioned_via_a_centralized_intake_form_or_process_inside_the_agency', ''),
                    row.get('do_you_have_a_process_in_place_to_request_access_to_computing_resources_for_model_training_and_development_of_the_ai_involved_in_this_use_case', ''),
                    row.get('has_communication_regarding_the_provisioning_of_your_requested_resources_been_timely', ''),
                    row.get('how_are_existing_data_science_tools_libraries_data_products_and_internally_developed_ai_infrastructure_being_re_used_for_the_current_ai_use_case', ''),
                    row.get('has_information_regarding_the_ai_use_case_including_performance_metrics_and_intended_use_of_the_model_been_made_available_for_review_and_feedback_within_the_agency', ''),
                    row.get('has_your_agency_requested_an_extension_to_implement_the_minimum_risk_management_practices_for_this_ai_use_case', ''),
                    row.get('has_an_ai_impact_assessment_been_conducted_for_this_ai_use_case', ''),
                    row.get('has_the_ai_use_case_been_tested_in_operational_or_real_world_environments_to_understand_the_performance_and_impact_it_may_have_on_affected_individuals_or_communities', ''),
                    row.get('what_are_the_key_risks_from_using_the_ai_for_this_particular_use_case_and_how_were_they_identified', ''),
                    row.get('has_an_independent_evaluation_of_the_ai_use_case_been_conducted', ''),
                    row.get('is_there_a_process_to_monitor_performance_of_the_ai_system_s_functionality_and_changes_to_its_impact_on_rights_or_safety_as_part_of_the_post_deployment_plan_for_the_ai_use_case', ''),
                    row.get('for_this_particular_use_case_can_the_ai_carry_out_a_decision_or_action_without_direct_human_involvement_that_could_result_in_a_significant_impact_on_rights_or_safety', ''),
                    row.get('how_is_the_agency_providing_reasonable_and_timely_notice_regarding_the_use_of_ai_when_people_interact_with_an_ai_enabled_service_as_a_result_of_this_ai_use_case', ''),
                    row.get('is_the_ai_used_to_significantly_influence_or_inform_decisions_or_actions_that_could_have_an_adverse_or_negative_impact_on_specific_individuals_or_groups', ''),
                    row.get('what_steps_has_the_agency_taken_to_detect_and_mitigate_significant_disparities_in_the_model_s_performance_across_demographic_groups_for_this_ai_use_case', ''),
                    row.get('what_steps_has_the_agency_taken_to_consult_and_incorporate_feedback_from_groups_affected_by_this_ai_use_case', ''),
                    row.get('is_there_an_established_fallback_and_escalation_process_for_this_ai_use_case_in_the_event_that_an_impacted_individual_or_group_would_like_to_appeal_or_contest_the_ai_system_s_outcome', ''),
                    row.get('where_practicable_and_consistent_with_applicable_law_and_governmentwide_policy_is_there_an_established_mechanism_for_individuals_to_opt_out_from_the_ai_functionality_in_favor_of_a_human_alternative', ''),
                    row.get('_search_text', '')
                ))

                count += 1

                # Progress indicator
                if count % 100 == 0:
                    print(f"   Processed {count} use cases...")

            except sqlite3.IntegrityError as e:
                print(f"   ⚠️  Skipping row {row_num} due to integrity error: {e}")
                skipped += 1
                continue

    conn.commit()
    print(f"✅ Loaded {count} use cases ({skipped} skipped)")
    return count


def main():
    """Main execution function."""
    print("🚀 Loading Federal AI Use Case Inventory into database...")
    print(f"   CSV file: {CSV_PATH}")
    print(f"   Database: {DB_PATH}")
    print()

    # Check if CSV file exists
    if not CSV_PATH.exists():
        print(f"❌ CSV file not found: {CSV_PATH}")
        print("   Please ensure ai_inventory_enriched_with_tags.csv is in your Downloads folder")
        return 1

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    # Create tables
    create_tables(conn)
    print()

    # Clear existing data (optional - uncomment to keep existing data)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ai_use_case_details')
    cursor.execute('DELETE FROM ai_use_cases')
    cursor.execute('DELETE FROM use_case_fedramp_matches')
    conn.commit()
    print("🗑️  Cleared existing use case data")
    print()

    # Load data
    total = load_use_cases(conn, CSV_PATH)
    print()

    # Show summary
    cursor.execute('SELECT COUNT(*) FROM ai_use_cases')
    use_case_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT agency) FROM ai_use_cases')
    agency_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM ai_use_cases WHERE genai_flag = 1')
    genai_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM ai_use_cases WHERE has_llm = 1')
    llm_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM ai_use_cases WHERE has_chatbot = 1')
    chatbot_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM ai_use_cases WHERE has_classic_ml = 1')
    ml_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT domain_category) FROM ai_use_cases WHERE domain_category IS NOT NULL AND domain_category != ""')
    domain_count = cursor.fetchone()[0]

    print("📈 Summary:")
    print(f"   Total use cases: {use_case_count}")
    print(f"   Unique agencies: {agency_count}")
    print(f"   GenAI use cases: {genai_count}")
    print(f"   With LLMs: {llm_count}")
    print(f"   With chatbots: {chatbot_count}")
    print(f"   Classic ML: {ml_count}")
    print(f"   Domain categories: {domain_count}")
    print()

    # Show top agencies
    print("📋 Top 10 Agencies by Use Case Count:")
    cursor.execute('''
        SELECT agency, COUNT(*) as count
        FROM ai_use_cases
        GROUP BY agency
        ORDER BY count DESC
        LIMIT 10
    ''')
    for agency, count in cursor.fetchall():
        print(f"   • {agency}: {count} use cases")
    print()

    # Show domain distribution
    print("📋 Use Cases by Domain Category:")
    cursor.execute('''
        SELECT domain_category, COUNT(*) as count
        FROM ai_use_cases
        WHERE domain_category IS NOT NULL AND domain_category != ""
        GROUP BY domain_category
        ORDER BY count DESC
        LIMIT 10
    ''')
    for domain, count in cursor.fetchall():
        print(f"   • {domain}: {count} use cases")
    print()

    # Sample records
    print("📋 Sample Use Cases:")
    cursor.execute('''
        SELECT use_case_name, agency, domain_category,
               CASE WHEN genai_flag = 1 THEN 'GenAI' ELSE 'Other' END as type
        FROM ai_use_cases
        LIMIT 5
    ''')
    for name, agency, domain, ai_type in cursor.fetchall():
        domain_str = domain if domain else 'Unclassified'
        print(f"   • [{ai_type}] {name} ({agency}) - {domain_str}")

    conn.close()
    print()
    print("✅ Done! AI Use Case Inventory loaded successfully")
    print(f"   Run the frontend to view at: http://localhost:3000/use-cases")
    return 0

if __name__ == '__main__':
    exit(main())
