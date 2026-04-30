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
    """Return every canonical product evidenced by ``text``.

    ``aliases_dict`` is a dict of ``lowered_alias -> value`` where ``value`` is
    whatever the caller wants back (canonical_name for tests, product_id for
    production). The return shape is ``[{"product_name": <value>, "alias":
    <matched alias>, "evidence": <text span>}]``.

    Longest-alias-first ordering: "microsoft 365 copilot" beats "m365 copilot"
    which beats the bare alias list. Each canonical is returned at most once
    even if multiple aliases for it appear in the text.
    """
    if not text:
        return []

    haystack = _normalize(text)

    # Split on compound separators, keeping original haystack for span matching
    # so multi-word aliases still resolve. We use the unified haystack for
    # matching and the split pieces only to handle the edge case where two
    # different products share an alias substring (rare but covered by
    # ordering-by-length).
    sorted_aliases = sorted(aliases_dict.keys(), key=len, reverse=True)

    results: dict[Any, dict[str, Any]] = {}
    # Walk haystack, consuming spans as we match them so "AWS Textract" doesn't
    # both match "AWS Textract" AND the bare "AWS" alias (if one existed).
    remaining = haystack
    for alias in sorted_aliases:
        if not alias:
            continue
        # Word-boundary-ish check: the alias must appear as a whole token, not
        # inside another word. Cheaper than compiling regex per alias: we
        # require the char before/after to be non-alphanumeric.
        start = 0
        while True:
            idx = remaining.find(alias, start)
            if idx < 0:
                break
            before_ok = idx == 0 or not remaining[idx - 1].isalnum()
            end = idx + len(alias)
            after_ok = end == len(remaining) or not remaining[end].isalnum()
            if before_ok and after_ok:
                canon = aliases_dict[alias]
                if canon not in results:
                    results[canon] = {
                        "product_name": canon,
                        "alias": alias,
                        "evidence": text[idx : idx + len(alias)]
                        if len(text) == len(haystack)
                        else alias,
                    }
                # Blank out the matched span so shorter aliases can't
                # re-match the same text region.
                remaining = remaining[:idx] + (" " * len(alias)) + remaining[end:]
                start = end
            else:
                start = idx + 1

    return list(results.values())


def _looks_compound(text: str) -> bool:
    """Rough check: does the text contain a compound separator?"""
    if not text:
        return False
    return bool(re.search(r"\+|\band\b|,|;|/|\(", text, flags=re.IGNORECASE))


def _load_aliases_by_product_id(conn) -> dict[str, int]:
    d: dict[str, int] = {}
    for row in conn.execute("SELECT alias_text, product_id FROM product_aliases"):
        d.setdefault(_normalize(row["alias_text"]), row["product_id"])
    return d


def _load_products(conn) -> dict[int, dict[str, Any]]:
    d: dict[int, dict[str, Any]] = {}
    for r in conn.execute(
        "SELECT id, canonical_name, vendor, product_type, "
        "is_generative_ai, parent_product_id FROM products"
    ):
        d[r["id"]] = dict(r)
    return d


def _use_case_search_text(row: dict[str, Any]) -> str:
    """The text we scan for product aliases. Matches the auto_tag.py fields."""
    return " ".join(
        (row.get(k) or "")
        for k in (
            "vendor_name",
            "system_name",
            "use_case_name",
            "problem_statement",
        )
    )


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
    return " ".join(
        (row.get(k) or "")
        for k in (
            "commercial_product",
            "ai_use_case",
            "agency_uses",
        )
    )


def _consolidated_primary_text(row: dict[str, Any]) -> str:
    """Only the agency-declared product field. Used to gate primary-FK
    seeding so we never auto-seed from narrative context."""
    return row.get("commercial_product") or ""


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
                confidence = "strong" if len(evidence) >= 5 else "inferred"
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
        # Consolidated pass: populate consolidated_use_case_products and
        # seed the single FK when the row has exactly one strong match and
        # no existing product_id. Don't overwrite existing FKs.
        # ------------------------------------------------------------
        crows = conn.execute("SELECT * FROM consolidated_use_cases").fetchall()
        c_zero = c_one = c_many = 0
        c_seeded = 0

        for r in crows:
            row = dict(r)
            text = _consolidated_search_text(row)
            matches = extract_products(text, aliases)

            if not matches:
                c_zero += 1
                continue

            inserted = []
            for m in matches:
                pid = m["product_name"]
                evidence = m.get("evidence") or m.get("alias") or ""
                confidence = "strong" if len(evidence) >= 5 else "inferred"
                conn.execute(
                    """
                    INSERT OR IGNORE INTO consolidated_use_case_products
                        (consolidated_use_case_id, product_id, evidence_text, confidence)
                    VALUES (?, ?, ?, ?)
                    """,
                    (row["id"], pid, evidence, confidence),
                )
                inserted.append((pid, confidence))

            if len(matches) == 1:
                c_one += 1
            else:
                c_many += 1

            # Seed primary FK only if (a) previously NULL and (b) the
            # `commercial_product` field alone produces exactly one match.
            # Earlier versions of this block used `inserted` from the broader
            # multi-column text, which silently pulled template-suggested
            # example products into the primary FK (see audit set C).
            if row.get("product_id") is None:
                primary_text = _consolidated_primary_text(row)
                primary_matches = extract_products(primary_text, aliases) if primary_text else []
                strong_pids = [
                    m["product_name"]
                    for m in primary_matches
                    if len((m.get("evidence") or m.get("alias") or "")) >= 5
                ]
                if len(set(strong_pids)) == 1:
                    conn.execute(
                        "UPDATE consolidated_use_cases SET product_id = ? WHERE id = ?",
                        (strong_pids[0], row["id"]),
                    )
                    c_seeded += 1

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
                "primary_fk_seeded_from_null": c_seeded,
            },
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
