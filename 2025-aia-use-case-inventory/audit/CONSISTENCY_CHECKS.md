# Consistency Checks

The seven cross-cut checks for the second pass are:

1. `id_traceability`
   Verify whether source identifiers (`use_case_id`) were preserved into the normalized tables and quantify where they were dropped.

2. `row_count_and_ingest_integrity`
   Compare raw source row counts against loaded DB row counts, including blank trailing rows and header handling.

3. `llm_vs_non_llm_classification`
   Find rows where `general_llm`/`is_generative_ai` appears inconsistent with source `ai_classification`, product, or problem statement.

4. `vendor_product_vs_custom_system`
   Find rows where vendor-backed or commercial-product sources were tagged as `custom_system` or `Custom In-House AI`.

5. `product_mapping_and_alias_quality`
   Review suspicious canonical product mappings, blank product fields on obvious product rows, and likely alias mistakes.

6. `scope_and_maturity_consistency`
   Review `deployment_scope`, `is_enterprise_wide`, and related maturity or stage interpretations against source bureau/license detail.

7. `field_fullness_and_tag_coarseness`
   Quantify missingness in key structured fields and identify sources where `product_capability`, `architecture_type`, or similar labels are too blank/coarse to be useful.

Each check should produce one markdown file in `audit/consistency/`.
