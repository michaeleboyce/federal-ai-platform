"""Populate the use_case_products join table (Phase 2 Agent D).

Idempotent migration: for every row in ``use_cases``, resolve all products
evidenced by the combined vendor/system/name/problem text and write
``(use_case_id, product_id)`` pairs into ``use_case_products``.

Compound-string handling: text like ``"AWS (Textract + Bedrock)"`` must yield
TWO matches (not just the first alias hit, which was the old behavior in
``auto_tag.match_product``). ``extract_products`` walks the text looking for
every alias substring, with longest-alias-first to avoid "AWS" stealing a
match that "AWS Textract" would resolve more specifically.

Also enqueues ambiguous rows (compound strings, unmatched vendor text) into
``review_queue_products`` for a later LLM review pass. The coordinator runs
that pass — this script just populates the queue.

Usage:
    python3 scripts/populate_use_case_products.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

# Allow ``python3 scripts/populate_use_case_products.py`` from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_connection  # noqa: E402
from product_resolution import (  # noqa: E402
    confidence_for_evidence,
    consolidated_search_text,
    extract_products as shared_extract_products,
    load_product_aliases,
    load_products,
    looks_compound,
    sync_primary_product_cache,
    use_case_search_text,
)


# Punctuation we treat as hard separators when collecting matches. Matches
# inside these tokens are still fine — we just make sure tokens on either
# side are considered independently.
_COMPOUND_SEP_RE = re.compile(
    r"\s*(?:\+|\band\b|,|;|/|\(|\)|\|)\s*", re.IGNORECASE
)


def _normalize(s: Any) -> str:
    if s is None:
        return ""
    return str(s).lower()


def extract_products(text: str | None, aliases_dict: dict[str, Any]) -> list[dict[str, Any]]:
    """Compatibility wrapper around product_resolution.extract_products."""
    return shared_extract_products(text, aliases_dict)


def _looks_compound(text: str) -> bool:
    """Rough check: does the text contain a compound separator?"""
    return looks_compound(text)


def _load_aliases_by_product_id(conn) -> dict[str, int]:
    return load_product_aliases(conn)


def _load_products(conn) -> dict[int, dict[str, Any]]:
    return load_products(conn)


def _use_case_search_text(row: dict[str, Any]) -> str:
    """The text we scan for product aliases. Matches the auto_tag.py fields."""
    return use_case_search_text(row)


def _consolidated_search_text(row: dict[str, Any]) -> str:
    """Text to scan for consolidated rows. IMPORTANT: `commercial_examples`
    is NOT included. That column is the OMB template's boilerplate
    "example products of this type" list (the identical strings "Calendly,
    Reclaim.AI", "ChatGPT, Gemini", "Otter.ai, Evernote, Fireflies" repeat
    verbatim across dozens of rows) — it's not evidence the agency uses
    those tools. Matching on it produced a 57% false-positive rate on an
    agent audit. Only `commercial_product` (what the agency declared) and
    `agency_uses` / `ai_use_case` (narrative context) are safe.
    """
    return consolidated_search_text(row)


def _consolidated_primary_text(row: dict[str, Any]) -> str:
    """Only the agency-declared product field. Used to gate primary-FK
    seeding so we never auto-seed from narrative context."""
    return consolidated_primary_text(row)


def populate() -> dict[str, int]:
    conn = get_connection()
    try:
        # Clean slate (idempotent re-run).
        conn.execute("DELETE FROM use_case_products")
        conn.execute("DELETE FROM consolidated_use_case_products")
        conn.execute("DELETE FROM review_queue_products")
        conn.commit()

        aliases = _load_aliases_by_product_id(conn)
        products = _load_products(conn)

        rows = conn.execute("SELECT * FROM use_cases").fetchall()

        zero = one = many = 0
        queued = 0

        for r in rows:
            row = dict(r)
            text = _use_case_search_text(row)
            matches = extract_products(text, aliases)

            if not matches:
                # Flag rows with populated vendor but no match for LLM review.
                vendor = (row.get("vendor_name") or "").strip()
                if vendor:
                    conn.execute(
                        """
                        INSERT INTO review_queue_products
                            (use_case_id, source_text, heuristic_product_ids,
                             reason)
                        VALUES (?, ?, ?, ?)
                        """,
                        (row["id"], text.strip(), "[]", "unmatched_vendor_text"),
                    )
                    queued += 1
                zero += 1
                continue

            # Insert each product match. Confidence: 'strong' if the match is
            # >= 5 chars and canonical_name appears verbatim; else 'inferred'.
            inserted_pids: list[int] = []
            for m in matches:
                pid = m["product_name"]  # Already product_id (from DB aliases)
                pname = (products.get(pid, {}) or {}).get("canonical_name", "")
                evidence = m.get("evidence") or m.get("alias") or ""
                confidence = confidence_for_evidence(evidence)
                conn.execute(
                    """
                    INSERT OR IGNORE INTO use_case_products
                        (use_case_id, product_id, evidence_text, confidence)
                    VALUES (?, ?, ?, ?)
                    """,
                    (row["id"], pid, evidence, confidence),
                )
                inserted_pids.append(pid)

            if len(matches) == 1:
                one += 1
            else:
                many += 1
                # Compound-text / multi-product rows go to the review queue so
                # the coordinator can LLM-review them.
                if _looks_compound(text):
                    conn.execute(
                        """
                        INSERT INTO review_queue_products
                            (use_case_id, source_text, heuristic_product_ids,
                             reason)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            row["id"],
                            text.strip(),
                            json.dumps(inserted_pids),
                            "compound_string",
                        ),
                    )
                    queued += 1

        # ------------------------------------------------------------
        # Consolidated pass: populate consolidated_use_case_products. The
        # compatibility product_id cache is derived from these edges below.
        # ------------------------------------------------------------
        crows = conn.execute("SELECT * FROM consolidated_use_cases").fetchall()
        c_zero = c_one = c_many = 0

        for r in crows:
            row = dict(r)
            text = _consolidated_search_text(row)
            matches = extract_products(text, aliases)

            if not matches:
                c_zero += 1
                continue

            for m in matches:
                pid = m["product_name"]
                evidence = m.get("evidence") or m.get("alias") or ""
                confidence = confidence_for_evidence(evidence)
                conn.execute(
                    """
                    INSERT OR IGNORE INTO consolidated_use_case_products
                        (consolidated_use_case_id, product_id, evidence_text, confidence)
                    VALUES (?, ?, ?, ?)
                    """,
                    (row["id"], pid, evidence, confidence),
                )
            if len(matches) == 1:
                c_one += 1
            else:
                c_many += 1

        cache_sync = sync_primary_product_cache(conn)
        conn.commit()

        stats = {
            "individual": {
                "rows_with_zero_products": zero,
                "rows_with_one_product": one,
                "rows_with_two_or_more_products": many,
                "total_use_case_products": conn.execute(
                    "SELECT COUNT(*) FROM use_case_products"
                ).fetchone()[0],
                "queued_for_llm_review": queued,
            },
            "consolidated": {
                "rows_with_zero_products": c_zero,
                "rows_with_one_product": c_one,
                "rows_with_two_or_more_products": c_many,
                "total_consolidated_use_case_products": conn.execute(
                    "SELECT COUNT(*) FROM consolidated_use_case_products"
                ).fetchone()[0],
            },
            "primary_product_cache": cache_sync,
        }
        print(json.dumps(stats, indent=2))

        # Write the unresolved CSV so the coordinator can pick up.
        unresolved_path = (
            Path(__file__).resolve().parent.parent
            / "audit"
            / "review_queue_products_unresolved.csv"
        )
        unresolved_path.parent.mkdir(parents=True, exist_ok=True)
        with unresolved_path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "queue_id",
                    "use_case_id",
                    "source_text",
                    "heuristic_product_ids",
                    "reason",
                ]
            )
            for qr in conn.execute(
                """
                SELECT id, use_case_id, source_text,
                       heuristic_product_ids, reason
                  FROM review_queue_products
                 ORDER BY id
                """
            ):
                w.writerow(list(qr))

        return stats
    finally:
        conn.close()


if __name__ == "__main__":
    populate()
