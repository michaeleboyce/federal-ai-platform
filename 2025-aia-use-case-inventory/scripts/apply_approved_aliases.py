"""Apply approved alias seeds from Worker B's CSVs to the products/aliases DB.

Idempotent migration run AFTER Worker B's alias cleanup (commit 21a1998).

Reads:
  - audit/proposed_aliases_seed_now.csv  (99 rows, each a NEW canonical product)
  - audit/proposed_aliases_dedup_drop.csv (18 rows, extra aliases for the
    canonical product kept under the same ``proposed_alias`` in seed_now)

Writes:
  - products (INSERT OR IGNORE on canonical_name UNIQUE)
  - product_aliases (INSERT OR IGNORE on alias_text UNIQUE)

Schema reference (see db.py):
  products(id, canonical_name UNIQUE, vendor, product_type, is_generative_ai,
           is_frontier_llm, parent_product_id, description, notes)
  product_aliases(id, product_id, alias_text UNIQUE)

Usage:
    python3 scripts/apply_approved_aliases.py
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_connection  # noqa: E402


SEED_NOW_CSV = Path(__file__).resolve().parent.parent / "audit" / "proposed_aliases_seed_now.csv"
DEDUP_DROP_CSV = Path(__file__).resolve().parent.parent / "audit" / "proposed_aliases_dedup_drop.csv"


# Heuristic classifiers driven off proposed_alias + source_label + llm_reasoning.
# Keys are lowercased substrings; matching is substring-contains.
LLM_HINTS = (
    "claude", "gpt", "chatgpt", "openai", "gemini", "bard", "palm",
    "copilot", "bedrock", "llama", "mistral", "grok", "vertex ai",
    "agentspace", "azure ai", "apple intelligence", "ready ai",
    "readyai", "ideation readyai", "neurasphere", "huggingface",
    "deepseek", "anthropic", "jasper", "lambda", "perplexity",
)

CODING_ASSIST_HINTS = (
    "copilot", "cursor", "codeium", "tabnine", "amazon q developer",
    "windsurf", "replit", "codewhisperer",
)

GENAI_HINTS = LLM_HINTS + (
    "generative", "hey gen", "heygen", "synthesia", "runway",
    "midjourney", "stable diffusion", "dall", "firefly",
    "agentspace", "c3 generative", "image generation",
)


def classify(row: dict) -> tuple[str | None, int, int]:
    """Return (product_type, is_generative_ai, is_frontier_llm) guesses.

    Conservative: when in doubt, leave product_type NULL and flags 0.
    """
    text = " ".join([
        row.get("proposed_alias") or "",
        row.get("source_label") or "",
        row.get("llm_reasoning") or "",
    ]).lower()

    is_llm = any(h in text for h in LLM_HINTS)
    is_coding = any(h in text for h in CODING_ASSIST_HINTS)
    is_gen = any(h in text for h in GENAI_HINTS)

    product_type = None
    if is_coding:
        product_type = "coding_assistant"
    elif is_llm:
        product_type = "general_llm"

    return product_type, (1 if is_gen else 0), 0


def upsert_product(cur: sqlite3.Cursor, canonical_name: str, vendor: str | None,
                   product_type: str | None, is_generative_ai: int,
                   is_frontier_llm: int) -> tuple[int, bool]:
    """Insert product or fetch existing id. Returns (product_id, was_inserted)."""
    cur.execute("SELECT id FROM products WHERE canonical_name = ?", (canonical_name,))
    row = cur.fetchone()
    if row:
        return int(row[0]), False
    cur.execute(
        """INSERT INTO products
           (canonical_name, vendor, product_type, is_generative_ai, is_frontier_llm)
           VALUES (?, ?, ?, ?, ?)""",
        (canonical_name, vendor or None, product_type, is_generative_ai, is_frontier_llm),
    )
    return int(cur.lastrowid), True


def upsert_alias(cur: sqlite3.Cursor, product_id: int, alias_text: str) -> bool:
    """Insert alias if not present. Returns True if newly inserted."""
    if not alias_text:
        return False
    cur.execute("SELECT id, product_id FROM product_aliases WHERE alias_text = ?", (alias_text,))
    row = cur.fetchone()
    if row:
        if int(row[1]) != product_id:
            print(f"  WARN: alias '{alias_text}' already points to product_id={row[1]}, "
                  f"not re-binding to {product_id}")
        return False
    cur.execute(
        "INSERT INTO product_aliases (product_id, alias_text) VALUES (?, ?)",
        (product_id, alias_text),
    )
    return True


def main() -> int:
    if not SEED_NOW_CSV.exists():
        print(f"ERROR: {SEED_NOW_CSV} not found", file=sys.stderr)
        return 2
    if not DEDUP_DROP_CSV.exists():
        print(f"ERROR: {DEDUP_DROP_CSV} not found", file=sys.stderr)
        return 2

    with SEED_NOW_CSV.open() as f:
        seed_rows = list(csv.DictReader(f))
    with DEDUP_DROP_CSV.open() as f:
        dedup_rows = list(csv.DictReader(f))

    print(f"Loaded {len(seed_rows)} seed_now rows, {len(dedup_rows)} dedup_drop rows")

    products_inserted = 0
    products_existing = 0
    aliases_inserted = 0
    aliases_skipped = 0
    dedup_missing: list[tuple[str, str]] = []

    # proposed_alias -> product_id (populated from seed_now pass, reused for dedup pass)
    alias_to_pid: dict[str, int] = {}

    conn = get_connection()
    try:
        cur = conn.cursor()

        # Pass 1: seed_now.csv — new canonical products + their source_label aliases
        for row in seed_rows:
            canonical_name = (row.get("proposed_alias") or "").strip()
            source_label = (row.get("source_label") or "").strip()
            vendor = (row.get("source_vendor") or "").strip() or None
            canonical_pid_raw = (row.get("canonical_product_id") or "").strip()

            if not canonical_name:
                print(f"  SKIP (empty proposed_alias): queue_id={row.get('queue_id')}")
                continue

            if canonical_pid_raw and canonical_pid_raw.lower() not in ("", "null", "none"):
                # Map source_label alias to pre-existing canonical
                try:
                    pid = int(canonical_pid_raw)
                except ValueError:
                    print(f"  SKIP (bad canonical_product_id={canonical_pid_raw}): "
                          f"queue_id={row.get('queue_id')}")
                    continue
                alias_to_pid[canonical_name] = pid
                if source_label:
                    if upsert_alias(cur, pid, source_label):
                        aliases_inserted += 1
                    else:
                        aliases_skipped += 1
                continue

            # Otherwise: insert new product keyed on proposed_alias as canonical_name
            product_type, is_gen, is_frontier = classify(row)
            try:
                pid, inserted = upsert_product(
                    cur, canonical_name, vendor, product_type, is_gen, is_frontier,
                )
            except sqlite3.Error as e:
                print(f"  ERROR inserting product '{canonical_name}' "
                      f"(queue_id={row.get('queue_id')}): {e}")
                continue

            if inserted:
                products_inserted += 1
            else:
                products_existing += 1
                print(f"  NOTE: canonical '{canonical_name}' already existed (id={pid}); "
                      f"treating source_label as extra alias")

            alias_to_pid[canonical_name] = pid

            # Also add the proposed_alias itself as an alias row (redundant but
            # lets future text-match lookups resolve through the alias table).
            if upsert_alias(cur, pid, canonical_name):
                aliases_inserted += 1
            else:
                aliases_skipped += 1

            if source_label and source_label != canonical_name:
                if upsert_alias(cur, pid, source_label):
                    aliases_inserted += 1
                else:
                    aliases_skipped += 1

        # Pass 2: dedup_drop.csv — attach source_label as alias to the canonical
        #         kept under the same proposed_alias in seed_now.
        for row in dedup_rows:
            proposed_alias = (row.get("proposed_alias") or "").strip()
            source_label = (row.get("source_label") or "").strip()
            if not proposed_alias or not source_label:
                continue
            pid = alias_to_pid.get(proposed_alias)
            if pid is None:
                # Fallback: look in DB directly
                cur.execute("SELECT id FROM products WHERE canonical_name = ?",
                            (proposed_alias,))
                r = cur.fetchone()
                if r:
                    pid = int(r[0])
                    alias_to_pid[proposed_alias] = pid
            if pid is None:
                dedup_missing.append((row.get("queue_id", ""), proposed_alias))
                print(f"  SKIP dedup row queue_id={row.get('queue_id')}: "
                      f"no canonical '{proposed_alias}' in seed_now or DB")
                continue
            if upsert_alias(cur, pid, source_label):
                aliases_inserted += 1
            else:
                aliases_skipped += 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"FATAL: rolled back. {e}", file=sys.stderr)
        raise
    finally:
        conn.close()

    print()
    print("=== Summary ===")
    print(f"Products inserted:   {products_inserted}")
    print(f"Products pre-existing: {products_existing}")
    print(f"Aliases inserted:    {aliases_inserted}")
    print(f"Aliases skipped (already present): {aliases_skipped}")
    print(f"Dedup rows with no matching canonical: {len(dedup_missing)}")
    for qid, alias in dedup_missing:
        print(f"  queue_id={qid} proposed_alias='{alias}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
