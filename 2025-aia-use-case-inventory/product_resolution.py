"""Shared product-resolution helpers.

Product attribution is modeled as many-to-many edges in use_case_products and
consolidated_use_case_products. Legacy product_id columns are maintained only
as a compatibility cache derived from those edges.
"""
from __future__ import annotations

import re
from typing import Any


def normalize(s: Any) -> str:
    if s is None:
        return ""
    return str(s).lower().strip()


def load_product_aliases(conn) -> dict[str, int]:
    """Build a lowered alias -> product_id lookup."""
    aliases: dict[str, int] = {}
    for row in conn.execute("SELECT alias_text, product_id FROM product_aliases"):
        aliases[normalize(row["alias_text"])] = row["product_id"]
    return aliases


def load_products(conn) -> dict[int, dict[str, Any]]:
    """Build product_id -> product metadata."""
    products: dict[int, dict[str, Any]] = {}
    for row in conn.execute(
        """
        SELECT id, canonical_name, vendor, product_type, is_generative_ai,
               is_frontier_llm, parent_product_id
          FROM products
        """
    ):
        products[row["id"]] = dict(row)
    return products


# Strings that agencies enter as a product but that aren't products. Treat as
# non-evidence and skip extraction so we don't surface them as compound strings
# or queue them as unmatched-vendor noise.
NON_PRODUCT_PLACEHOLDERS = frozenset(
    {
        "various",
        "n/a",
        "na",
        "none",
        "tbd",
        "tbd.",
        "unknown",
        "webapps",
        "response",
        "external- chatbots",
        "external chatbots",
        "internal gov cloud- chatbots",
        "internal gov cloud chatbots",
    }
)


def is_non_product_placeholder(text: str | None) -> bool:
    """True if `text` (after normalize) is a placeholder, not a product name."""
    return normalize(text) in NON_PRODUCT_PLACEHOLDERS


def extract_products(
    text: str | None,
    aliases_dict: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return every canonical product evidenced by text.

    aliases_dict is lowered_alias -> value, where value is usually product_id
    in production and can be a canonical name in tests.
    """
    if not text:
        return []
    if is_non_product_placeholder(text):
        return []

    haystack = normalize(text)
    sorted_aliases = sorted(aliases_dict.keys(), key=len, reverse=True)

    results: dict[Any, dict[str, Any]] = {}
    remaining = haystack
    for alias in sorted_aliases:
        if not alias:
            continue
        start = 0
        while True:
            idx = remaining.find(alias, start)
            if idx < 0:
                break
            before_ok = idx == 0 or not remaining[idx - 1].isalnum()
            end = idx + len(alias)
            after_ok = end == len(remaining) or not remaining[end].isalnum()
            if before_ok and after_ok:
                product = aliases_dict[alias]
                if product not in results:
                    results[product] = {
                        "product_name": product,
                        "alias": alias,
                        "evidence": text[idx : idx + len(alias)]
                        if len(text) == len(haystack)
                        else alias,
                    }
                remaining = remaining[:idx] + (" " * len(alias)) + remaining[end:]
                start = end
            else:
                start = idx + 1
    return list(results.values())


def use_case_search_text(row: dict[str, Any]) -> str:
    """Fields that evidence a product for individual inventory rows.

    `expected_benefits` is included because some agencies (notably VA)
    name the AI product only in their benefits prose ("Implementing
    AI Builder will tangibly improve …"), with vendor/system/name
    fields blank. Adding this field is monotonic — boundary-checked
    alias matching means more text only catches more *real* mentions.
    """
    return " ".join(
        (row.get(k) or "")
        for k in (
            "vendor_name",
            "system_name",
            "use_case_name",
            "problem_statement",
            "expected_benefits",
        )
    )


def consolidated_search_text(row: dict[str, Any]) -> str:
    """Fields that evidence a product for consolidated rows.

    Deliberately excludes commercial_examples: those are OMB boilerplate
    examples, not evidence that the filing agency used the products.
    """
    return " ".join(
        (row.get(k) or "")
        for k in (
            "commercial_product",
            "ai_use_case",
            "agency_uses",
        )
    )


def consolidated_primary_text(row: dict[str, Any]) -> str:
    """The agency-declared product field only."""
    return row.get("commercial_product") or ""


def looks_compound(text: str) -> bool:
    if not text:
        return False
    return bool(re.search(r"\+|\band\b|,|;|/|\(", text, flags=re.IGNORECASE))


def confidence_for_evidence(evidence: str | None) -> str:
    return "strong" if evidence and len(evidence) >= 5 else "inferred"


def sync_primary_product_cache(conn) -> dict[str, int]:
    """Derive legacy product_id columns from authoritative edge tables."""
    stats = {
        "use_cases_updated": 0,
        "consolidated_updated": 0,
        "use_cases_cleared": 0,
        "consolidated_cleared": 0,
    }
    stats["use_cases_cleared"] = conn.execute(
        "UPDATE use_cases SET product_id = NULL"
    ).rowcount
    stats["consolidated_cleared"] = conn.execute(
        "UPDATE consolidated_use_cases SET product_id = NULL"
    ).rowcount

    stats["use_cases_updated"] = conn.execute(
        """
        UPDATE use_cases
           SET product_id = (
             SELECT ucp.product_id
               FROM use_case_products ucp
              WHERE ucp.use_case_id = use_cases.id
              ORDER BY CASE ucp.confidence WHEN 'strong' THEN 0 ELSE 1 END,
                       ucp.product_id
              LIMIT 1
           )
         WHERE EXISTS (
             SELECT 1 FROM use_case_products ucp
              WHERE ucp.use_case_id = use_cases.id
         )
        """
    ).rowcount
    stats["consolidated_updated"] = conn.execute(
        """
        UPDATE consolidated_use_cases
           SET product_id = (
             SELECT cucp.product_id
               FROM consolidated_use_case_products cucp
              WHERE cucp.consolidated_use_case_id = consolidated_use_cases.id
              ORDER BY CASE cucp.confidence WHEN 'strong' THEN 0 ELSE 1 END,
                       cucp.product_id
              LIMIT 1
           )
         WHERE EXISTS (
             SELECT 1 FROM consolidated_use_case_products cucp
              WHERE cucp.consolidated_use_case_id = consolidated_use_cases.id
         )
        """
    ).rowcount
    return stats

