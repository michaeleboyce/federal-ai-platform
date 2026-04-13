"""Tests that header variants for the Use Case ID column all map to use_case_id.

Regression: the header variant ``"Use Case ID\n\n[Agency Abbrev.] - [#]"`` was
silently failing to map because EXPLICIT_OVERRIDES was checked against the raw
header before normalization, and the normalized fuzzy ratio fell below threshold.
"""

from column_maps import map_header_to_canonical


def test_newline_use_case_id_header_maps_to_use_case_id():
    raw = "Use Case ID\n\n[Agency Abbrev.] - [#]"
    assert map_header_to_canonical(raw) == "use_case_id"


def test_plain_use_case_id_still_maps():
    assert map_header_to_canonical("Use Case ID") == "use_case_id"


def test_use_case_identifier_still_maps():
    assert map_header_to_canonical("Use Case Identifier") == "use_case_id"
