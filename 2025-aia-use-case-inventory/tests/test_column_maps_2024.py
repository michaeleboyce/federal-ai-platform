"""Tests for the 2024 → 2025 schema crosswalk (Phase 0).

Unit tests for ``column_maps_2024``: the crosswalk constants, the value recode
maps, and the ordinal-aware ``map_2024_headers`` resolver. Mirrors the
assertion-driven, no-DB-round-trip style of ``tests/test_product_aliases.py``.

Note on column count: the live 2024 CSV ships **62 columns**, not the 54 quoted
in early planning notes. The 62 include 10 "If Other/No, please explain."
follow-up columns. (54 is the count of *distinct* header strings — those 10
share two literal header texts.) The crosswalk has one entry per real CSV
column, so it has 62 entries.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from column_maps_2024 import (
    COLUMN_CROSSWALK_2024,
    COMPARABILITY_VALUES,
    DEV_STAGE_ENUM_2024,
    DEV_STAGE_RECODE_2024,
    DIRECTLY_COMPARABLE,
    IMPACT_TYPE_ENUM_2024,
    IMPACT_TYPE_RECODE_2024,
    RECODED,
    YEAR_2024_ONLY,
    comparability_counts,
    map_2024_headers,
    resolve_2024_header,
)

_CSV_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "2024_consolidated_ai_inventory_raw_v2.csv"
)

EXPECTED_COLUMN_COUNT = 62


def _live_csv_headers() -> list[str]:
    """Read the real 2024 CSV header row (cp1252-encoded)."""
    with open(_CSV_PATH, encoding="cp1252", newline="") as fh:
        return next(csv.reader(fh))


# --- Completeness -----------------------------------------------------------


def test_crosswalk_has_one_entry_per_csv_column():
    assert len(COLUMN_CROSSWALK_2024) == EXPECTED_COLUMN_COUNT


def test_every_field_name_is_unique():
    """csv_header repeats (the 'If Other' columns); field names must not."""
    fields = [e["field"] for e in COLUMN_CROSSWALK_2024]
    assert len(fields) == len(set(fields))


def test_every_comparability_value_is_allowed():
    for entry in COLUMN_CROSSWALK_2024:
        assert entry["comparability"] in COMPARABILITY_VALUES


def test_every_entry_has_required_keys():
    for entry in COLUMN_CROSSWALK_2024:
        assert set(entry) == {
            "csv_header",
            "field",
            "target_2025",
            "comparability",
            "notes",
        }


def test_directly_comparable_and_recoded_have_a_target():
    """A column we can compare must name a 2025 target; 2024_only must not."""
    for entry in COLUMN_CROSSWALK_2024:
        if entry["comparability"] in (DIRECTLY_COMPARABLE, RECODED):
            assert entry["target_2025"], entry["field"]
        else:
            assert entry["target_2025"] is None, entry["field"]


# --- CSV alignment ----------------------------------------------------------


def test_crosswalk_csv_headers_match_live_file_in_order():
    """The crosswalk header strings equal the live CSV header row, in order."""
    live = _live_csv_headers()
    crosswalk = [e["csv_header"] for e in COLUMN_CROSSWALK_2024]
    assert crosswalk == live


def test_every_live_csv_header_resolves_no_silent_drops():
    """map_2024_headers must resolve every column of the real CSV header row."""
    headers = _live_csv_headers()
    mapping = map_2024_headers(headers)
    assert len(mapping) == len(headers) == EXPECTED_COLUMN_COUNT
    # Every index 0..61 present.
    assert set(mapping) == set(range(EXPECTED_COLUMN_COUNT))


def test_map_2024_headers_resolves_to_crosswalk_fields():
    """Each resolved field equals the crosswalk field at that position."""
    headers = _live_csv_headers()
    mapping = map_2024_headers(headers)
    for i, field in mapping.items():
        assert field == COLUMN_CROSSWALK_2024[i]["field"]


def test_duplicate_explain_headers_resolve_positionally():
    """The repeated 'If Other, please explain.' columns resolve distinctly."""
    headers = _live_csv_headers()
    mapping = map_2024_headers(headers)
    # Indices of the literal duplicate headers (from the live file).
    explain_idx = [
        i
        for i, h in enumerate(headers)
        if "please explain" in h.lower()
    ]
    assert len(explain_idx) == 10
    resolved = {mapping[i] for i in explain_idx}
    # All ten resolve to distinct, non-None fields.
    assert len(resolved) == 10
    assert all(mapping[i] for i in explain_idx)


def test_resolve_single_unambiguous_header():
    assert resolve_2024_header("Use Case Name") == "use_case_name"
    assert resolve_2024_header("Stage of Development") == "dev_stage"


def test_resolve_ambiguous_header_returns_none():
    """A bare repeated header cannot be resolved by text alone."""
    assert resolve_2024_header("If Other, please explain.") is None


def test_resolve_empty_returns_none():
    assert resolve_2024_header("") is None
    assert resolve_2024_header(None) is None


# --- Recode maps ------------------------------------------------------------


def test_impact_recode_covers_every_yaml_enum_value():
    for value in IMPACT_TYPE_ENUM_2024:
        assert value in IMPACT_TYPE_RECODE_2024


def test_impact_recode_entries_are_all_marked_lossy():
    """Every impact recode is lossy — the taxonomies do not map 1:1."""
    for value, entry in IMPACT_TYPE_RECODE_2024.items():
        assert entry["lossy"] is True, value
        assert "target" in entry


def test_impact_recode_targets_are_canonical_2025_values():
    valid = {
        "a) High-impact",
        "b) Presumed high-impact, but determined not high impact",
        "c) Not high-impact",
    }
    for entry in IMPACT_TYPE_RECODE_2024.values():
        assert entry["target"] in valid


def test_impact_recode_neither_is_not_high_impact():
    assert IMPACT_TYPE_RECODE_2024["Neither"]["target"] == "c) Not high-impact"
    assert IMPACT_TYPE_RECODE_2024["Both"]["target"] == "a) High-impact"
    assert IMPACT_TYPE_RECODE_2024["Rights-Impacting"]["target"] == "a) High-impact"


def test_dev_stage_recode_covers_every_yaml_enum_value():
    for value in DEV_STAGE_ENUM_2024:
        assert value in DEV_STAGE_RECODE_2024


def test_dev_stage_recode_targets_are_canonical_2025_values():
    valid = {
        "a) Pre-deployment",
        "b) Pilot",
        "c) Deployed",
        "d) Retired",
    }
    for entry in DEV_STAGE_RECODE_2024.values():
        assert entry["target"] in valid
        assert isinstance(entry["lossy"], bool)


def test_dev_stage_retired_maps_to_retired():
    assert DEV_STAGE_RECODE_2024["Retired"]["target"] == "d) Retired"
    assert DEV_STAGE_RECODE_2024["Operation and Maintenance"]["target"] == "c) Deployed"


# --- Known anchors (plan §1b) ----------------------------------------------


def _entry(field: str) -> dict:
    for e in COLUMN_CROSSWALK_2024:
        if e["field"] == field:
            return e
    raise AssertionError(f"no crosswalk entry for field {field!r}")


def test_anchor_use_case_name_directly_comparable():
    e = _entry("use_case_name")
    assert e["comparability"] == DIRECTLY_COMPARABLE
    assert e["target_2025"] == "use_case_name"


def test_anchor_impact_type_recoded():
    e = _entry("impact_type")
    assert e["comparability"] == RECODED
    assert e["target_2025"] == "is_high_impact"


def test_anchor_dev_stage_recoded():
    e = _entry("dev_stage")
    assert e["comparability"] == RECODED
    assert e["target_2025"] == "stage_of_development"


def test_anchor_date_implemented_recoded():
    e = _entry("date_implemented")
    assert e["comparability"] == RECODED
    assert e["target_2025"] == "operational_date"


def test_anchor_other_date_columns_are_2024_only():
    for field in ("date_initiated", "date_acq_dev_began", "date_retired"):
        assert _entry(field)["comparability"] == YEAR_2024_ONLY


def test_anchor_readiness_block_is_2024_only():
    """The agency-readiness/infrastructure block has no M-25-21 home."""
    for field in (
        "dev_tools_wait",
        "infra_provisioned",
        "compute_request",
        "timely_resources",
        "existing_reuse",
        "extension_request",
        "data_catalog",
    ):
        assert _entry(field)["comparability"] == YEAR_2024_ONLY, field


def test_anchor_hisp_block_is_2024_only():
    for field in ("hisp_support", "hisp_name", "public_service"):
        assert _entry(field)["comparability"] == YEAR_2024_ONLY, field


def test_anchor_iqa_and_piid_are_2024_only():
    assert _entry("iqa_compliance")["comparability"] == YEAR_2024_ONLY
    assert _entry("contract_piids")["comparability"] == YEAR_2024_ONLY


def test_anchor_purpose_benefits_recoded_to_expected_benefits():
    e = _entry("purpose_benefits")
    assert e["comparability"] == RECODED
    assert e["target_2025"] == "expected_benefits"


# --- Disposition counts -----------------------------------------------------


def test_comparability_counts_sum_to_total():
    counts = comparability_counts()
    assert sum(counts.values()) == EXPECTED_COLUMN_COUNT


def test_disposition_breakdown():
    """Lock the disposition breakdown so accidental reclassification fails CI."""
    counts = comparability_counts()
    assert counts == {
        DIRECTLY_COMPARABLE: 21,
        RECODED: 4,
        YEAR_2024_ONLY: 37,
    }
