"""Unit tests for auto_tag.infer_entry_type().

Phase 2 Agent C — Vendor/Custom Reclassifier.

Fixtures reflect the corrected precedence in plan §C.2:
  1. Consolidated rows -> generic_use_pattern
  2. Template match w/o tool-ish noun -> generic_use_pattern
  3. development_type starts with "a)" (purchased) OR vendor populated
     with blank development_type -> product_deployment
  4. development_type contains "in-house" AND vendor blank -> custom_system
  5. Any mix of in-house + vendor/product -> bespoke_application
  6. Default: product_deployment if vendor populated else custom_system
"""

import pytest

from auto_tag import infer_entry_type


# Minimal products_dict mapping with no parent_product_id so
# product_deployment path does not short-circuit to product_feature.
PRODUCTS_DICT = {
    5: {
        "canonical_name": "Microsoft 365 Copilot",
        "vendor": "Microsoft",
        "product_type": "general_llm",
        "is_generative_ai": 1,
        "is_frontier_llm": 1,
        "parent_product_id": None,
    },
}


@pytest.mark.parametrize(
    "row,product_id,template_id,is_consolidated,expected",
    [
        # 1. Purchased from a vendor (Adobe) — no product match yet — should be product_deployment
        (
            {
                "use_case_name": "Adobe Creative Cloud AI features",
                "problem_statement": "design work",
                "development_type": "a) Purchased from a vendor",
                "vendor_name": "Adobe",
            },
            None,
            None,
            False,
            "product_deployment",
        ),
        # 2. Purchased from a vendor (Axon) — should be product_deployment
        (
            {
                "use_case_name": "Axon Draft One",
                "problem_statement": "report writing",
                "development_type": "a) Purchased from a vendor",
                "vendor_name": "Axon",
            },
            None,
            None,
            False,
            "product_deployment",
        ),
        # 3. Strictly in-house, no vendor — custom_system
        (
            {
                "use_case_name": "Internal fraud detection model",
                "problem_statement": "detect fraud",
                "development_type": "b) Developed in-house",
                "vendor_name": "",
            },
            None,
            None,
            False,
            "custom_system",
        ),
        # 4. "c) Developed with both" + vendor + product match — bespoke_application
        (
            {
                "use_case_name": "Custom Copilot Studio chatbot",
                "problem_statement": "employee Q&A on top of M365 Copilot",
                "development_type": "c) Developed with both contracting and in-house resources",
                "vendor_name": "Microsoft",
            },
            5,
            None,
            False,
            "bespoke_application",
        ),
        # 5. Blank development_type + vendor populated — safe default to product_deployment
        (
            {
                "use_case_name": "Leidos-supplied analytics",
                "problem_statement": "analytics platform",
                "development_type": "",
                "vendor_name": "Leidos",
            },
            None,
            None,
            False,
            "product_deployment",
        ),
        # 6. Consolidated row — always generic_use_pattern
        (
            {
                "use_case_name": "",
                "problem_statement": "",
                "development_type": "",
                "vendor_name": "",
            },
            None,
            None,
            True,
            "generic_use_pattern",
        ),
        # 7. "c) both" + vendor populated but no product match — still bespoke_application
        (
            {
                "use_case_name": "Custom integration",
                "problem_statement": "",
                "development_type": "c) Developed with both contracting and in-house resources",
                "vendor_name": "Leidos",
            },
            None,
            None,
            False,
            "bespoke_application",
        ),
        # 8. in-house AND vendor_name populated — bespoke_application (mix)
        (
            {
                "use_case_name": "In-house tuning atop vendor model",
                "problem_statement": "",
                "development_type": "b) Developed in-house",
                "vendor_name": "Microsoft",
            },
            None,
            None,
            False,
            "bespoke_application",
        ),
        # 9. Blank everything — custom_system default
        (
            {
                "use_case_name": "Mystery system",
                "problem_statement": "",
                "development_type": "",
                "vendor_name": "",
            },
            None,
            None,
            False,
            "custom_system",
        ),
    ],
)
def test_entry_type(row, product_id, template_id, is_consolidated, expected):
    assert (
        infer_entry_type(row, product_id, template_id, is_consolidated, PRODUCTS_DICT)
        == expected
    )
