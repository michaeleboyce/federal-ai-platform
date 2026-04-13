"""Tests for the extended product resolver (Agent D, plan §D.5).

The resolver must handle compound strings — e.g. ``"AWS (Textract + Bedrock)"``
should yield two product matches, not just one. The plain string-containment
matcher in ``auto_tag.match_product`` returns only the first match, so Agent D
introduces ``extract_products`` on top of it.

Fixtures use the alias seeds from ``build_lookups.PRODUCTS`` directly (no DB
round-trip) — see ``_aliases_from_seed``.
"""

from __future__ import annotations

import pytest

from build_lookups import PRODUCTS
from scripts.populate_use_case_products import extract_products


def _aliases_from_seed() -> dict[str, str]:
    """Build a lowered-alias -> canonical_name dict from build_lookups seeds.

    We key on canonical_name instead of product_id so these tests don't need
    a live DB. The production caller keys on product_id.
    """
    d: dict[str, str] = {}
    for (name, _vendor, _ptype, _g, _f, _parent, _desc, aliases) in PRODUCTS:
        for a in aliases:
            d.setdefault(a.lower(), name)
    return d


ALIASES = _aliases_from_seed()


def test_compound_product_string_yields_two_rows():
    """Plan §D.5 — 'AWS (Textract + Bedrock)' resolves to both products."""
    rows = extract_products("AWS (Textract + Bedrock)", ALIASES)
    names = {r["product_name"] for r in rows}
    assert names == {"AWS Textract", "AWS Bedrock"}


def test_plus_separator():
    rows = extract_products("ChatGPT + Claude", ALIASES)
    names = {r["product_name"] for r in rows}
    assert "ChatGPT" in names
    assert "Claude" in names


def test_and_separator():
    rows = extract_products("Gemini and Microsoft 365 Copilot", ALIASES)
    names = {r["product_name"] for r in rows}
    assert names == {"Gemini", "Microsoft 365 Copilot"}


def test_comma_separator():
    rows = extract_products("Gemini, ChatGPT, Claude", ALIASES)
    names = {r["product_name"] for r in rows}
    assert names == {"Gemini", "ChatGPT", "Claude"}


def test_paren_enclosed_multi_noun():
    rows = extract_products("Microsoft (M365 Copilot, GitHub Copilot)", ALIASES)
    names = {r["product_name"] for r in rows}
    assert "Microsoft 365 Copilot" in names
    assert "GitHub Copilot" in names


def test_single_product_still_matches():
    rows = extract_products("Microsoft 365 Copilot", ALIASES)
    assert len(rows) == 1
    assert rows[0]["product_name"] == "Microsoft 365 Copilot"


def test_empty_returns_empty():
    assert extract_products("", ALIASES) == []
    assert extract_products(None, ALIASES) == []


def test_unmatched_text_returns_empty():
    # "zzx quxor nobody's heard of" — no seeded aliases.
    assert extract_products("zzx quxor nobody has heard of", ALIASES) == []


def test_bare_copilot_no_longer_matches():
    """Agent D narrowing: 'Copilot' alone should not resolve to M365."""
    rows = extract_products("Our team uses Copilot", ALIASES)
    # May match GitHub Copilot if "github" appears elsewhere, but bare "Copilot"
    # no longer resolves to Microsoft 365 Copilot.
    names = {r["product_name"] for r in rows}
    assert "Microsoft 365 Copilot" not in names


def test_copilot_for_security_resolves_distinctly():
    rows = extract_products("Microsoft Copilot for Security", ALIASES)
    names = {r["product_name"] for r in rows}
    assert "Microsoft Copilot for Security" in names
    assert "Microsoft 365 Copilot" not in names


def test_copilot_studio_resolves_distinctly():
    rows = extract_products("We built it in Copilot Studio", ALIASES)
    names = {r["product_name"] for r in rows}
    assert "Microsoft Copilot Studio" in names
    assert "Microsoft 365 Copilot" not in names


def test_new_aliases_resolve():
    """The four newly-added products must match their vendor-text strings."""
    assert {r["product_name"] for r in extract_products("Amazon Textract", ALIASES)} == {"AWS Textract"}
    assert {r["product_name"] for r in extract_products("Adobe Photoshop", ALIASES)} == {"Adobe Photoshop"}
    assert {r["product_name"] for r in extract_products("Airtable AI", ALIASES)} == {"Airtable AI"}
    # Lowercase variant seen in data
    assert {r["product_name"] for r in extract_products("Wellsaid", ALIASES)} == {"WellSaid Labs"}
