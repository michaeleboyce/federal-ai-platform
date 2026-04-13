"""Unit tests for auto_tag.infer_scope() and auto_tag.infer_architecture().

Phase 2 Agent E — Scope & Uncertainty Curator.

Plan §E.4 fixtures:
  * consolidated + agency_uses='N' + no agency-wide wording  -> unknown
  * consolidated + agency_uses='N' + "agency-wide" wording    -> enterprise_wide
  * name-only "knowledge base" phrasing, no product, no
    training_data_description phrase                          -> unknown

Additional coverage:
  * consolidated + agency_uses='Y' -> enterprise_wide (authoritative signal)
  * architecture: explicit "vector database" in training_data_description
    -> rag_pipeline
  * architecture: product of type 'rag_platform' -> rag_pipeline
"""

from auto_tag import infer_architecture, infer_scope


# ---------------------------------------------------------------------------
# Plan §E.4 fixtures
# ---------------------------------------------------------------------------

def test_consolidated_agency_uses_n_is_not_enterprise_wide():
    row = {"agency_uses": "N", "description": "", "use_case_name": "Bureau tool"}
    assert infer_scope(row, is_consolidated=True) == "unknown"


def test_consolidated_explicit_agency_wide_is_enterprise_wide():
    row = {"agency_uses": "N", "description": "Deployed agency-wide", "use_case_name": ""}
    assert infer_scope(row, is_consolidated=True) == "enterprise_wide"


def test_rag_requires_evidence():
    row = {
        "problem_statement": "search the knowledge base",
        "training_data_description": "",
    }
    products_dict = {}
    arch, _ = infer_architecture(row, products_dict, product_id=None)
    assert arch == "unknown"


# ---------------------------------------------------------------------------
# Additional coverage (not strictly in §E.4 but protects the semantics)
# ---------------------------------------------------------------------------

def test_consolidated_agency_uses_y_is_enterprise_wide():
    row = {"agency_uses": "Y", "description": "", "use_case_name": ""}
    assert infer_scope(row, is_consolidated=True) == "enterprise_wide"


def test_consolidated_null_agency_uses_without_wording_is_unknown():
    row = {"agency_uses": None, "description": "Narrow pilot", "use_case_name": ""}
    assert infer_scope(row, is_consolidated=True) == "unknown"


def test_consolidated_large_license_count_alone_does_not_enterprise_tag():
    """The estimated_licenses_users substring block was dropped — a big user
    count in free-text is not sufficient evidence."""
    row = {
        "agency_uses": "N",
        "description": "",
        "use_case_name": "",
        "estimated_licenses_users": "10001-100000",
    }
    assert infer_scope(row, is_consolidated=True) == "unknown"


def test_rag_pipeline_with_vector_database_phrase():
    row = {
        "problem_statement": "answer employee questions",
        "training_data_description": "agency documents ingested into a vector database",
    }
    arch, _ = infer_architecture(row, {}, product_id=None)
    assert arch == "rag_pipeline"


def test_rag_pipeline_with_rag_platform_product_type():
    row = {"problem_statement": "search", "training_data_description": ""}
    products_dict = {42: {"product_type": "rag_platform"}}
    arch, _ = infer_architecture(row, products_dict, product_id=42)
    assert arch == "rag_pipeline"


def test_agentic_workflow_with_explicit_tool_use_phrase():
    row = {
        "problem_statement": "multi-step agent with tool use for triage",
        "training_data_description": "",
    }
    arch, _ = infer_architecture(row, {}, product_id=None)
    assert arch == "agentic_workflow"


def test_name_only_agent_keyword_is_not_agentic():
    """Name says 'agent' but no supporting evidence -> unknown."""
    row = {
        "use_case_name": "Customer agent assistant",
        "problem_statement": "help customers",
        "training_data_description": "",
    }
    arch, _ = infer_architecture(row, {}, product_id=None)
    assert arch == "unknown"
