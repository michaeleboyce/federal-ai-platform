"""Heuristic seed for FedRAMP <-> inventory cross-references.

Builds three tables in the inventory DB:
  - fedramp_product_links  inventory.products.id <-> fedramp_products.fedramp_id
  - fedramp_agency_links   inventory.agencies.id <-> fedramp_agencies.id
  - fedramp_link_queue     ambiguous / unresolved cases needing curation

Heuristic for products:
  For each inventory product, build a token set from its canonical name and
  every product_aliases.alias_text. For each FedRAMP product, build a token
  set from its `csp` + `cso`. A "strong" match needs (a) the inventory token
  set to overlap the FedRAMP token set on at least one non-stopword token AND
  (b) the inventory product canonical name (or any alias) to appear as a
  contiguous substring inside the FedRAMP `csp + ' ' + cso` string (with both
  sides normalized — lowercased, punctuation stripped). This keeps generic
  noise like "AI" or "Cloud" from triggering matches while allowing
  "Microsoft 365 Copilot" -> "Microsoft Microsoft 365 Copilot for Government".

  - 1 strong match  -> fedramp_product_links (confidence='strong',
                       source='alias_match').
  - 2-N strong matches (vendor multi-SKU case, e.g. all the Adobe Government
    SKUs) -> top 5 by score into fedramp_link_queue with reason='multi_candidate'.
  - 0 strong matches AND inventory product is plausibly a FedRAMP candidate
    (i.e. has a vendor on file and is not flagged generic-AI-only)
        -> fedramp_link_queue with reason='no_alias'.

Heuristic for agencies:
  Match inventory.agencies.name and .abbreviation against fedramp_agencies
  .parent_agency. Direct exact-name match (case-insensitive) writes a strong
  link. Substring-wins-the-canonical-side cases ("Department of Veterans
  Affairs" -> "Department of Veterans Affairs") are also strong. Anything
  that doesn't resolve goes to the queue with reason='no_alias'.

Idempotent: clears prior `source='alias_match'` rows before re-running.
Manual-CSV decisions (`source='manual_csv'`) are NEVER touched.

Usage:
    python link_fedramp.py                  # dry-run (default — prints report)
    python link_fedramp.py --apply          # write the links + queue
    python link_fedramp.py --apply --vendor=Microsoft   # restrict to one vendor
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

from db import get_connection


LINK_SCHEMA = """
CREATE TABLE IF NOT EXISTS fedramp_product_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_product_id INTEGER NOT NULL REFERENCES products(id),
    fedramp_id TEXT NOT NULL,
    confidence TEXT NOT NULL CHECK (confidence IN ('strong', 'weak', 'manual')),
    source TEXT NOT NULL,  -- 'alias_match' | 'manual_csv' | 'llm'
    score REAL,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(inventory_product_id, fedramp_id, source)
);
CREATE INDEX IF NOT EXISTS idx_fpl_inv ON fedramp_product_links(inventory_product_id);
CREATE INDEX IF NOT EXISTS idx_fpl_fr  ON fedramp_product_links(fedramp_id);

CREATE TABLE IF NOT EXISTS fedramp_agency_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_agency_id INTEGER NOT NULL REFERENCES agencies(id),
    fedramp_agency_id INTEGER NOT NULL,
    confidence TEXT NOT NULL CHECK (confidence IN ('strong', 'weak', 'manual')),
    source TEXT NOT NULL,
    score REAL,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(inventory_agency_id, fedramp_agency_id, source)
);
CREATE INDEX IF NOT EXISTS idx_fal_inv ON fedramp_agency_links(inventory_agency_id);
CREATE INDEX IF NOT EXISTS idx_fal_fr  ON fedramp_agency_links(fedramp_agency_id);

CREATE TABLE IF NOT EXISTS fedramp_link_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_kind TEXT NOT NULL CHECK (link_kind IN ('product', 'agency')),
    inventory_id INTEGER NOT NULL,
    source_text TEXT,
    candidate_fedramp_ids TEXT,   -- JSON array of fedramp ids/scores
    reason TEXT NOT NULL,         -- 'multi_candidate' | 'no_alias' | 'ambiguous'
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'resolved' | 'rejected'
    decision_notes TEXT,
    llm_proposed_fedramp_ids TEXT,
    llm_reasoning TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_flq_status ON fedramp_link_queue(status);
CREATE INDEX IF NOT EXISTS idx_flq_kind   ON fedramp_link_queue(link_kind);
CREATE INDEX IF NOT EXISTS idx_flq_inv    ON fedramp_link_queue(inventory_id);
"""


# Words that can never be the deciding factor in a match. "ai" / "for" / "and"
# show up in hundreds of products on both sides; if they were the only token
# in common, the match would be noise.
STOPWORDS = {
    "a", "an", "and", "for", "of", "the", "to", "or",
    "ai", "the", "in", "on", "with", "by",
    "inc", "llc", "corp", "corporation", "co", "ltd",
    "government", "gov", "federal", "fed", "us", "u.s.",
    "cloud", "saas", "service", "services", "platform", "suite",
    "system", "systems", "solution", "solutions", "tool", "tools",
    "enterprise", "online", "hosted",
}


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _tokenize(text: str) -> set[str]:
    """Normalize then split into tokens, dropping stopwords and 1-char tokens."""
    normed = _normalize(text)
    return {t for t in normed.split() if len(t) > 1 and t not in STOPWORDS}


def _score_overlap(inv_tokens: set[str], fr_tokens: set[str]) -> float:
    """Jaccard-like score over non-stopword token sets."""
    if not inv_tokens or not fr_tokens:
        return 0.0
    overlap = inv_tokens & fr_tokens
    if not overlap:
        return 0.0
    return len(overlap) / max(len(inv_tokens), 1)


def _substring_match(inv_phrase: str, fr_phrase: str) -> bool:
    """True if the (normalized) inventory phrase is a contiguous substring
    of the (normalized) FedRAMP phrase. A 4-character minimum guards against
    the dreaded "ai" -> "ai assistant" false positive."""
    a = _normalize(inv_phrase)
    b = _normalize(fr_phrase)
    if not a or not b or len(a) < 4:
        return False
    # Pad with spaces so we don't get partial-word hits ("copilot" inside
    # "copilotrx" would otherwise match).
    return f" {a} " in f" {b} "


def _load_inventory_products(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT id, canonical_name, vendor FROM products ORDER BY id"
    ).fetchall()
    out = []
    for r in rows:
        aliases = [
            a[0]
            for a in conn.execute(
                "SELECT alias_text FROM product_aliases WHERE product_id = ?",
                (r["id"],),
            ).fetchall()
        ]
        out.append(
            {
                "id": r["id"],
                "name": r["canonical_name"],
                "vendor": r["vendor"],
                "aliases": aliases,
                "phrases": [r["canonical_name"], *aliases],
            }
        )
    return out


def _load_fedramp_products(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT fedramp_id, csp, cso FROM fedramp_products ORDER BY csp, cso"
    ).fetchall()
    out = []
    for r in rows:
        combined = f"{r['csp']} {r['cso']}"
        out.append(
            {
                "fedramp_id": r["fedramp_id"],
                "csp": r["csp"],
                "cso": r["cso"],
                "combined": combined,
                "tokens": _tokenize(combined),
            }
        )
    return out


def match_products(
    inv_products: list[dict],
    fr_products: list[dict],
    *,
    vendor_filter: str | None = None,
) -> tuple[list[dict], list[dict], Counter]:
    """Return (strong_links, queued, unresolved_token_counter)."""
    strong: list[dict] = []
    queued: list[dict] = []
    token_counter: Counter = Counter()

    for inv in inv_products:
        if vendor_filter and (inv["vendor"] or "").lower() != vendor_filter.lower():
            continue

        # Build the inventory-side token set from name + all aliases.
        inv_tokens: set[str] = set()
        for phrase in inv["phrases"]:
            inv_tokens |= _tokenize(phrase)
        if inv["vendor"]:
            inv_tokens |= _tokenize(inv["vendor"])

        candidates: list[tuple[float, dict]] = []
        for fr in fr_products:
            score = _score_overlap(inv_tokens, fr["tokens"])
            if score == 0.0:
                continue
            # Substring confirmation against any inventory phrase.
            confirmed = any(
                _substring_match(p, fr["combined"]) for p in inv["phrases"]
            )
            if not confirmed:
                continue
            candidates.append((score, fr))

        candidates.sort(key=lambda x: x[0], reverse=True)

        if len(candidates) == 1:
            sc, fr = candidates[0]
            strong.append(
                {
                    "inventory_product_id": inv["id"],
                    "fedramp_id": fr["fedramp_id"],
                    "score": sc,
                    "notes": f"alias_match: {inv['name']} -> {fr['csp']} / {fr['cso']}",
                }
            )
        elif len(candidates) > 1:
            top = candidates[:5]
            queued.append(
                {
                    "inventory_id": inv["id"],
                    "source_text": inv["name"],
                    "candidates": [
                        {
                            "fedramp_id": fr["fedramp_id"],
                            "csp": fr["csp"],
                            "cso": fr["cso"],
                            "score": sc,
                        }
                        for sc, fr in top
                    ],
                    "reason": "multi_candidate",
                }
            )
        else:
            # No candidates. Queue iff the product has a vendor — products
            # without a vendor (custom internal systems) aren't expected to
            # appear in the FedRAMP marketplace at all.
            if inv["vendor"]:
                queued.append(
                    {
                        "inventory_id": inv["id"],
                        "source_text": inv["name"],
                        "candidates": [],
                        "reason": "no_alias",
                    }
                )
                # Track the leftover tokens for the report.
                for t in inv_tokens:
                    token_counter[t] += 1

    return strong, queued, token_counter


def match_agencies(
    conn,
    *,
    agency_filter: str | None = None,
) -> tuple[list[dict], list[dict]]:
    inv = conn.execute(
        "SELECT id, name, abbreviation FROM agencies "
        "WHERE status IN ('FOUND_2025','FOUND_2024_ONLY')"
    ).fetchall()
    fr = conn.execute(
        "SELECT id, parent_agency, parent_slug FROM fedramp_agencies"
    ).fetchall()

    fr_by_norm = {_normalize(r["parent_agency"]): dict(r) for r in fr}

    strong: list[dict] = []
    queued: list[dict] = []
    for a in inv:
        if agency_filter and a["abbreviation"].lower() != agency_filter.lower():
            continue
        norm_name = _normalize(a["name"])
        # Direct hit first.
        hit = fr_by_norm.get(norm_name)
        if hit:
            strong.append(
                {
                    "inventory_agency_id": a["id"],
                    "fedramp_agency_id": hit["id"],
                    "score": 1.0,
                    "notes": f"exact_name_match: {a['name']} = {hit['parent_agency']}",
                }
            )
            continue
        # Substring fallback: e.g. "Department of Veterans Affairs" exactly
        # matches; "Treasury" -> "Department of the Treasury" needs work.
        candidates = [
            r
            for r in fr
            if norm_name and (
                norm_name in _normalize(r["parent_agency"])
                or _normalize(r["parent_agency"]) in norm_name
            )
        ]
        if len(candidates) == 1:
            c = candidates[0]
            strong.append(
                {
                    "inventory_agency_id": a["id"],
                    "fedramp_agency_id": c["id"],
                    "score": 0.85,
                    "notes": f"substring: {a['name']} ~ {c['parent_agency']}",
                }
            )
        elif len(candidates) > 1:
            queued.append(
                {
                    "inventory_id": a["id"],
                    "source_text": f"{a['name']} ({a['abbreviation']})",
                    "candidates": [
                        {
                            "fedramp_id": str(c["id"]),
                            "parent_agency": c["parent_agency"],
                            "parent_slug": c["parent_slug"],
                        }
                        for c in candidates[:5]
                    ],
                    "reason": "multi_candidate",
                }
            )
        else:
            queued.append(
                {
                    "inventory_id": a["id"],
                    "source_text": f"{a['name']} ({a['abbreviation']})",
                    "candidates": [],
                    "reason": "no_alias",
                }
            )
    return strong, queued


def _apply_product_links(conn, strong: list[dict]) -> None:
    # Wipe prior alias_match rows; preserve manual_csv and llm rows.
    conn.execute(
        "DELETE FROM fedramp_product_links WHERE source = 'alias_match'"
    )
    conn.executemany(
        """
        INSERT OR IGNORE INTO fedramp_product_links (
            inventory_product_id, fedramp_id, confidence, source, score, notes
        ) VALUES (?, ?, 'strong', 'alias_match', ?, ?)
        """,
        [
            (
                row["inventory_product_id"],
                row["fedramp_id"],
                row["score"],
                row["notes"],
            )
            for row in strong
        ],
    )


def _apply_agency_links(conn, strong: list[dict]) -> None:
    conn.execute(
        "DELETE FROM fedramp_agency_links WHERE source = 'alias_match'"
    )
    conn.executemany(
        """
        INSERT OR IGNORE INTO fedramp_agency_links (
            inventory_agency_id, fedramp_agency_id, confidence, source, score, notes
        ) VALUES (?, ?, 'strong', 'alias_match', ?, ?)
        """,
        [
            (
                row["inventory_agency_id"],
                row["fedramp_agency_id"],
                row["score"],
                row["notes"],
            )
            for row in strong
        ],
    )


def _apply_queue(
    conn, kind: str, queued: list[dict]
) -> None:
    """Replace pending alias_match queue rows for the given kind."""
    conn.execute(
        """
        DELETE FROM fedramp_link_queue
         WHERE link_kind = ? AND status = 'pending'
        """,
        (kind,),
    )
    conn.executemany(
        """
        INSERT INTO fedramp_link_queue (
            link_kind, inventory_id, source_text, candidate_fedramp_ids,
            reason, status
        ) VALUES (?, ?, ?, ?, ?, 'pending')
        """,
        [
            (
                kind,
                q["inventory_id"],
                q["source_text"],
                json.dumps(q["candidates"]),
                q["reason"],
            )
            for q in queued
        ],
    )


def link(
    *,
    apply: bool,
    vendor: str | None,
    agency: str | None,
) -> None:
    conn = get_connection()
    try:
        conn.executescript(LINK_SCHEMA)

        inv_products = _load_inventory_products(conn)
        fr_products = _load_fedramp_products(conn)
        if not fr_products:
            raise SystemExit(
                "fedramp_products is empty — run `python load_fedramp.py` first."
            )

        strong_p, queued_p, token_counter = match_products(
            inv_products, fr_products, vendor_filter=vendor
        )
        strong_a, queued_a = match_agencies(conn, agency_filter=agency)

        if apply:
            _apply_product_links(conn, strong_p)
            _apply_agency_links(conn, strong_a)
            _apply_queue(conn, "product", queued_p)
            _apply_queue(conn, "agency", queued_a)
            conn.commit()
            verb = "Wrote"
        else:
            verb = "Would write"

        print(f"\n=== fedramp link seed ({'APPLY' if apply else 'DRY-RUN'}) ===")
        print(f"Products: {verb} {len(strong_p)} strong links")
        prod_reasons = Counter(q["reason"] for q in queued_p)
        for reason, n in prod_reasons.most_common():
            print(f"  queued (product, {reason}): {n}")
        print(f"Agencies: {verb} {len(strong_a)} strong links")
        ag_reasons = Counter(q["reason"] for q in queued_a)
        for reason, n in ag_reasons.most_common():
            print(f"  queued (agency, {reason}): {n}")

        if token_counter:
            print("\nTop 10 unresolved tokens (no_alias product queue):")
            for tok, n in token_counter.most_common(10):
                print(f"  {n:>4}  {tok}")

        # Sample 3 strong + 3 queued for the report.
        if strong_p:
            print("\nSample strong product links (3):")
            for row in strong_p[:3]:
                print(f"  inv#{row['inventory_product_id']} -> {row['fedramp_id']}  ({row['score']:.2f})")
                print(f"    {row['notes']}")
        if queued_p:
            print("\nSample queued product items (3):")
            for q in queued_p[:3]:
                print(f"  inv#{q['inventory_id']} '{q['source_text']}' [{q['reason']}]")
                for c in q["candidates"][:3]:
                    print(f"    cand: {c.get('fedramp_id')}  {c.get('csp','')} / {c.get('cso','')}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--vendor", default=None)
    parser.add_argument("--agency", default=None)
    args = parser.parse_args()
    apply = args.apply and not args.dry_run
    link(apply=apply, vendor=args.vendor, agency=args.agency)


if __name__ == "__main__":
    main()
