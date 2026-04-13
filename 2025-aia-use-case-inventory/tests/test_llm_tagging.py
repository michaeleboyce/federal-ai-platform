"""Tests for the LLM-inference function used by auto_tag.py.

Agent B — LLM Tag Auditor. These fixtures encode the B.2 precedence rules:

  1. ai_classification names a non-LLM category (Classical / Predictive /
     Computer Vision / Traditional ML) -> 0, UNLESS vendor_name matches a
     known LLM product OR the name/problem mentions a named LLM explicitly.
  2. ai_classification names a generative/LLM category -> 1.
  3. Blank/unknown ai_classification -> fallback:
     - product_id resolves to a products.product_type='general_llm' row -> 1.
     - Name/problem hits EXTRACTION_ROUTING_BLACKLIST -> 0.
     - Name/problem hits narrowed LLM_KEYWORDS -> 1.
     - Otherwise 0.

The function under test is ``auto_tag.infer_llm_flag``. It must be a pure
function of the row plus the products context (so tests don't need a DB).
"""

import pytest

from auto_tag import infer_llm_flag


# Minimal stand-in for the products_dict loaded at runtime. The only field
# infer_llm_flag needs is ``product_type`` so it can detect general_llm
# products when the source ai_classification is blank.
PRODUCTS_DICT = {
    1: {"canonical_name": "Microsoft 365 Copilot", "vendor": "Microsoft",
        "product_type": "general_llm", "is_generative_ai": 1},
    2: {"canonical_name": "ChatGPT", "vendor": "OpenAI",
        "product_type": "general_llm", "is_generative_ai": 1},
    3: {"canonical_name": "AWS Textract", "vendor": "Amazon",
        "product_type": "computer_vision", "is_generative_ai": 0},
    4: {"canonical_name": "Power Automate", "vendor": "Microsoft",
        "product_type": "productivity", "is_generative_ai": 0},
}


# Helpers so cases are readable.
def _row(**kwargs):
    defaults = {
        "ai_classification": "",
        "vendor_name": "",
        "use_case_name": "",
        "problem_statement": "",
        "development_type": "",
    }
    defaults.update(kwargs)
    return defaults


@pytest.mark.parametrize("row,product_id,expected_llm,note", [
    # 1. Classical ML classification -> 0 (regression row: EPA Power Automate)
    (_row(ai_classification="Classical/Predictive Machine Learning",
          use_case_name="EPA Power Automate flow"), None, 0,
     "classical source signal wins"),

    # 2. Computer Vision classification -> 0 (regression row: DOI CV inspection)
    (_row(ai_classification="Computer Vision",
          use_case_name="DOI CV inspection"), None, 0,
     "computer vision source signal wins"),

    # 3. Predictive wording -> 0
    (_row(ai_classification="Predictive Analytics",
          use_case_name="Budget forecasting"), None, 0,
     "predictive analytics wording -> 0"),

    # 4. Generative AI classification -> 1
    (_row(ai_classification="Generative AI",
          vendor_name="Microsoft 365 Copilot",
          use_case_name="Draft memo assist"), 1, 1,
     "generative AI classification -> 1"),

    # 5. Blank classification, copilot product -> 1 (fallback via product)
    (_row(vendor_name="Microsoft 365 Copilot"), 1, 1,
     "blank classification but product is general_llm -> 1"),

    # 6. Blank classification, ChatGPT product -> 1
    (_row(vendor_name="ChatGPT"), 2, 1,
     "blank classification but product is general_llm -> 1"),

    # 7. Blank classification, extraction-only -> 0 (blacklist)
    (_row(use_case_name="Entity extraction pipeline"), None, 0,
     "blank classification, extraction blacklist -> 0"),

    # 8. Blank classification, document routing -> 0 (blacklist)
    (_row(use_case_name="Document routing classifier",
          problem_statement="Route incoming forms based on topic"), None, 0,
     "blank classification, routing blacklist -> 0"),

    # 9. Blank classification, anomaly detection -> 0 (blacklist)
    (_row(problem_statement="Anomaly detection on network traffic"), None, 0,
     "blank classification, anomaly detection blacklist -> 0"),

    # 10. Blank classification, sentiment analysis -> 0 (blacklist)
    (_row(use_case_name="Customer sentiment analysis"), None, 0,
     "blank classification, sentiment blacklist -> 0"),

    # 11. Blank classification, transcription -> 0 (blacklist, not genAI)
    (_row(use_case_name="Meeting transcription"), None, 0,
     "blank classification, transcription blacklist -> 0"),

    # 12. Blank classification, "draft memo with chatbot" -> 1
    (_row(use_case_name="Chatbot to draft responses",
          problem_statement="Use chatgpt to draft answers"), None, 1,
     "blank classification, explicit LLM keyword -> 1"),

    # 13. Blank classification, no hints either way -> 0
    (_row(use_case_name="Customer service tool"), None, 0,
     "blank classification, no signal -> 0"),

    # 14. Classical classification BUT vendor is an LLM product -> 1
    # (rare but possible: misclassified source field with clear LLM product)
    (_row(ai_classification="Classical/Predictive Machine Learning",
          vendor_name="Microsoft 365 Copilot"), 1, 1,
     "classical in source but product is LLM -> override to 1"),

    # 15. Classical classification AND name mentions Copilot by name -> 1
    (_row(ai_classification="Classical/Predictive Machine Learning",
          use_case_name="Pilot test with Microsoft 365 Copilot"), None, 1,
     "classical but name mentions Copilot explicitly -> override to 1"),

    # 16. Computer vision classification, non-LLM product -> 0
    (_row(ai_classification="Computer Vision",
          vendor_name="AWS Textract"), 3, 0,
     "computer vision + non-LLM product -> 0"),

    # 17. Traditional ML wording -> 0
    (_row(ai_classification="Traditional ML / Statistical methods"), None, 0,
     "traditional ML source signal -> 0"),

    # 18. Generative variant wording -> 1
    (_row(ai_classification="Large Language Model"), None, 1,
     "large language model source signal -> 1"),
])
def test_llm_inference(row, product_id, expected_llm, note):
    assert infer_llm_flag(row, product_id, PRODUCTS_DICT) == expected_llm, note
