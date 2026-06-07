"""Tests for scripts/check_2024_tag_invariants.py"""
import pytest
from scripts.check_2024_tag_invariants import check_row, NON_GENAI_SOPHISTICATIONS


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _base() -> dict:
    """A minimal valid canonical tag row — no violations expected."""
    return {
        "use_case_id_2024": 1,
        "canonical_wave": "1",
        "agency_abbreviation": "HHS",
        "use_case_name": "Test use case",
        "entry_type": "custom_system",
        "is_generative_ai": 0,
        "ai_sophistication": "classical_ml",
        "deployment_scope": "bureau",
        "is_enterprise_wide": 0,
        "is_general_llm_access": 0,
        "is_coding_tool": 0,
        "is_cots_commercial": 0,
        "tool_product_name": "",
        "tool_vendor": "",
        "is_microsoft_copilot": 0,
        "is_openai": 0,
        "is_anthropic": 0,
        "is_github_copilot": 0,
        "confidence": "medium",
    }


def _violation_ids(row: dict) -> list[int]:
    return [v.invariant_id for v in check_row(row)]


# ---------------------------------------------------------------------------
# Rule 1: is_generative_ai=1 ⇒ sophistication NOT in non-genai set
# ---------------------------------------------------------------------------

def test_rule1_genai_classical_ml_violation():
    row = {**_base(), "is_generative_ai": 1, "ai_sophistication": "classical_ml"}
    assert 1 in _violation_ids(row)


def test_rule1_genai_computer_vision_violation():
    row = {**_base(), "is_generative_ai": 1, "ai_sophistication": "computer_vision"}
    assert 1 in _violation_ids(row)


def test_rule1_genai_predictive_analytics_violation():
    row = {**_base(), "is_generative_ai": 1, "ai_sophistication": "predictive_analytics"}
    assert 1 in _violation_ids(row)


def test_rule1_genai_general_llm_ok():
    row = {**_base(), "is_generative_ai": 1, "ai_sophistication": "general_llm"}
    assert 1 not in _violation_ids(row)


def test_rule1_nongenai_classical_ok():
    assert 1 not in _violation_ids(_base())


# ---------------------------------------------------------------------------
# Rule 2: is_general_llm_access=1 ⇒ is_generative_ai=1
# ---------------------------------------------------------------------------

def test_rule2_llm_access_without_genai_violation():
    row = {**_base(), "is_general_llm_access": 1, "is_generative_ai": 0}
    assert 2 in _violation_ids(row)


def test_rule2_llm_access_with_genai_ok():
    row = {**_base(), "is_general_llm_access": 1, "is_generative_ai": 1,
           "ai_sophistication": "general_llm"}
    assert 2 not in _violation_ids(row)


def test_rule2_no_llm_access_ok():
    assert 2 not in _violation_ids(_base())


# ---------------------------------------------------------------------------
# Rule 3: is_enterprise_wide ↔ deployment_scope='enterprise_wide'
# ---------------------------------------------------------------------------

def test_rule3_enterprise_wide_flag_without_scope_violation():
    row = {**_base(), "is_enterprise_wide": 1, "deployment_scope": "bureau"}
    assert 3 in _violation_ids(row)


def test_rule3_scope_enterprise_wide_without_flag_violation():
    row = {**_base(), "is_enterprise_wide": 0, "deployment_scope": "enterprise_wide"}
    assert 3 in _violation_ids(row)


def test_rule3_both_enterprise_wide_ok():
    row = {**_base(), "is_enterprise_wide": 1, "deployment_scope": "enterprise_wide"}
    assert 3 not in _violation_ids(row)


def test_rule3_neither_enterprise_wide_ok():
    assert 3 not in _violation_ids(_base())


# ---------------------------------------------------------------------------
# Rule 4: is_microsoft_copilot=1 ⇒ tool_vendor contains 'microsoft'
# ---------------------------------------------------------------------------

def test_rule4_copilot_without_microsoft_vendor_violation():
    row = {**_base(), "is_microsoft_copilot": 1, "tool_vendor": "OpenAI"}
    assert 4 in _violation_ids(row)


def test_rule4_copilot_with_empty_vendor_violation():
    row = {**_base(), "is_microsoft_copilot": 1, "tool_vendor": ""}
    assert 4 in _violation_ids(row)


def test_rule4_copilot_with_microsoft_vendor_ok():
    row = {**_base(), "is_microsoft_copilot": 1, "tool_vendor": "Microsoft"}
    assert 4 not in _violation_ids(row)


def test_rule4_copilot_with_microsoft_lowercase_ok():
    row = {**_base(), "is_microsoft_copilot": 1, "tool_vendor": "microsoft corporation"}
    assert 4 not in _violation_ids(row)


# ---------------------------------------------------------------------------
# Rule 5: is_openai=1 ⇒ vendor contains 'openai' or 'microsoft'
# ---------------------------------------------------------------------------

def test_rule5_openai_without_openai_vendor_violation():
    row = {**_base(), "is_openai": 1, "tool_vendor": "Anthropic"}
    assert 5 in _violation_ids(row)


def test_rule5_openai_with_openai_vendor_ok():
    row = {**_base(), "is_openai": 1, "tool_vendor": "OpenAI"}
    assert 5 not in _violation_ids(row)


def test_rule5_openai_via_microsoft_azure_ok():
    row = {**_base(), "is_openai": 1, "tool_vendor": "Microsoft Azure OpenAI"}
    assert 5 not in _violation_ids(row)


# ---------------------------------------------------------------------------
# Rule 6: is_anthropic=1 ⇒ vendor contains 'anthropic'
# ---------------------------------------------------------------------------

def test_rule6_anthropic_without_anthropic_vendor_violation():
    row = {**_base(), "is_anthropic": 1, "tool_vendor": ""}
    assert 6 in _violation_ids(row)


def test_rule6_anthropic_with_anthropic_vendor_ok():
    row = {**_base(), "is_anthropic": 1, "tool_vendor": "Anthropic"}
    assert 6 not in _violation_ids(row)


# ---------------------------------------------------------------------------
# Rule 7: is_github_copilot=1 ⇒ is_coding_tool=1
# ---------------------------------------------------------------------------

def test_rule7_github_copilot_without_coding_violation():
    row = {**_base(), "is_github_copilot": 1, "is_coding_tool": 0}
    assert 7 in _violation_ids(row)


def test_rule7_github_copilot_with_coding_ok():
    row = {**_base(), "is_github_copilot": 1, "is_coding_tool": 1,
           "tool_vendor": "GitHub/Microsoft"}
    assert 7 not in _violation_ids(row)


# ---------------------------------------------------------------------------
# Rule 8: coding_tool + generic_use_pattern ⇒ sophistication coding/llm/agentic
# ---------------------------------------------------------------------------

def test_rule8_coding_generic_pattern_classical_ml_violation():
    row = {
        **_base(),
        "is_coding_tool": 1,
        "entry_type": "generic_use_pattern",
        "ai_sophistication": "classical_ml",
    }
    assert 8 in _violation_ids(row)


def test_rule8_coding_generic_pattern_coding_assistant_ok():
    row = {
        **_base(),
        "is_coding_tool": 1,
        "entry_type": "generic_use_pattern",
        "ai_sophistication": "coding_assistant",
    }
    assert 8 not in _violation_ids(row)


def test_rule8_coding_product_deployment_no_trigger():
    # Rule only fires for generic_use_pattern
    row = {
        **_base(),
        "is_coding_tool": 1,
        "entry_type": "product_deployment",
        "ai_sophistication": "classical_ml",
        "tool_product_name": "GitHub Copilot",
    }
    assert 8 not in _violation_ids(row)


# ---------------------------------------------------------------------------
# Rule 9: product_deployment + no tool_product_name
# ---------------------------------------------------------------------------

def test_rule9_product_deployment_no_name_violation():
    row = {**_base(), "entry_type": "product_deployment", "tool_product_name": ""}
    assert 9 in _violation_ids(row)


def test_rule9_product_deployment_with_name_ok():
    row = {**_base(), "entry_type": "product_deployment",
           "tool_product_name": "Salesforce Einstein"}
    assert 9 not in _violation_ids(row)


def test_rule9_custom_system_no_name_ok():
    row = {**_base(), "entry_type": "custom_system", "tool_product_name": ""}
    assert 9 not in _violation_ids(row)


# ---------------------------------------------------------------------------
# Rule 10: is_cots_commercial=1 + no tool_product_name
# ---------------------------------------------------------------------------

def test_rule10_cots_without_name_violation():
    row = {**_base(), "is_cots_commercial": 1, "tool_product_name": ""}
    assert 10 in _violation_ids(row)


def test_rule10_cots_with_name_ok():
    row = {**_base(), "is_cots_commercial": 1, "tool_product_name": "AWS SageMaker"}
    assert 10 not in _violation_ids(row)


def test_rule10_not_cots_no_name_ok():
    assert 10 not in _violation_ids(_base())


# ---------------------------------------------------------------------------
# Rule 11: confidence='high' + no entry_type
# ---------------------------------------------------------------------------

def test_rule11_high_confidence_no_entry_type_violation():
    row = {**_base(), "confidence": "high", "entry_type": ""}
    assert 11 in _violation_ids(row)


def test_rule11_high_confidence_with_entry_type_ok():
    row = {**_base(), "confidence": "high", "entry_type": "custom_system"}
    assert 11 not in _violation_ids(row)


def test_rule11_medium_confidence_no_entry_type_ok():
    row = {**_base(), "confidence": "medium", "entry_type": ""}
    assert 11 not in _violation_ids(row)


# ---------------------------------------------------------------------------
# Clean row produces no violations
# ---------------------------------------------------------------------------

def test_clean_row_no_violations():
    assert check_row(_base()) == []


def test_multiple_violations_on_single_row():
    # A completely broken row should produce multiple violations.
    row = {
        **_base(),
        "is_generative_ai": 1,
        "ai_sophistication": "classical_ml",  # rule 1
        "is_general_llm_access": 1,           # rule 2 — wait, genai=1, so no rule 2
        "is_enterprise_wide": 1,
        "deployment_scope": "bureau",          # rule 3
        "is_microsoft_copilot": 1,
        "tool_vendor": "OpenAI",               # rule 4
        "is_github_copilot": 1,
        "is_coding_tool": 0,                   # rule 7
    }
    ids = _violation_ids(row)
    assert 1 in ids
    assert 3 in ids
    assert 4 in ids
    assert 7 in ids
