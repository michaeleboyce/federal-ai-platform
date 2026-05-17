"""Remap stale use_case_ids in linkage_pass_2026-05 integration outputs.

Background: the labeling agents ran against a DB snapshot whose autoincrement
IDs were re-keyed between Phase 0 and Phase 4 (the use_cases table was
rebuilt; same rows, different `id` values).

This script rebuilds (agency, use_case_name) → new_use_case_id and
(agency, ai_use_case) → new_consolidated_id mappings using:
  - audit/linkage_pass_2026-05/inputs/slice_*.csv  (old id + agency + name)
  - data/federal_ai_inventory_2025.db              (new id + same agency + name)

Then rewrites in place:
  - audit/linkage_pass_2026-05/integration/proposed_links.csv
  - audit/linkage_pass_2026-05/integration/proposed_new_products.csv
    (the linking_use_case_ids and linking_consolidated_ids columns)

Stale ids that don't resolve get logged to stderr and dropped.
Idempotent: safe to re-run; second pass is a no-op once IDs match.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
PASS_DIR = ROOT / "audit" / "linkage_pass_2026-05"
INPUTS = PASS_DIR / "inputs"
INT = PASS_DIR / "integration"


def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


def _build_old_id_to_signature() -> dict[int, tuple[str, str]]:
    """old_id → (agency_abbrev, name_lower) from the input CSVs."""
    out: dict[int, tuple[str, str]] = {}

    # Individual slices
    for fname in [
        "slice_a_named_vendor_individual.csv",
        "slice_b_mention_only_individual.csv",
        "slice_c_dark_sample.csv",
    ]:
        path = INPUTS / fname
        if not path.exists():
            continue
        with path.open() as f:
            for r in csv.DictReader(f):
                try:
                    uid = int(r["use_case_id"])
                except (KeyError, ValueError):
                    continue
                out[uid] = ("__uc__" + _norm(r.get("agency")), _norm(r.get("use_case_name")))

    # Consolidated slice
    path = INPUTS / "slice_b_named_consolidated.csv"
    if path.exists():
        with path.open() as f:
            for r in csv.DictReader(f):
                try:
                    cid = int(r["consolidated_use_case_id"])
                except (KeyError, ValueError):
                    continue
                out[cid] = ("__c__" + _norm(r.get("agency")), _norm(r.get("ai_use_case")))
    return out


def _build_signature_to_new_id(conn: sqlite3.Connection) -> dict[tuple[str, str], int]:
    """signature → new id (use_case or consolidated)."""
    out: dict[tuple[str, str], int] = {}

    for row in conn.execute(
        """
        SELECT uc.id, a.abbreviation, uc.use_case_name
          FROM use_cases uc JOIN agencies a ON a.id = uc.agency_id
        """
    ):
        out[("__uc__" + _norm(row[1]), _norm(row[2]))] = row[0]

    for row in conn.execute(
        """
        SELECT c.id, a.abbreviation, c.ai_use_case
          FROM consolidated_use_cases c JOIN agencies a ON a.id = c.agency_id
        """
    ):
        out[("__c__" + _norm(row[1]), _norm(row[2]))] = row[0]

    return out


def _remap_links(remap: dict[int, int]) -> None:
    path = INT / "proposed_links.csv"
    if not path.exists():
        print(f"skip: {path} not found", file=sys.stderr)
        return
    with path.open() as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys()) if rows else []
    new_rows = []
    dropped = 0
    for r in rows:
        try:
            old = int(r["entry_id"])
        except (KeyError, ValueError):
            new_rows.append(r)
            continue
        new = remap.get(old, old)  # if not in remap, keep as-is (likely already current)
        if new == old and old not in remap:
            # row didn't have a stale signature; keep (may have already been current)
            new_rows.append(r)
            continue
        if new == old:
            new_rows.append(r)
        else:
            r["entry_id"] = str(new)
            new_rows.append(r)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(new_rows)
    print(f"links: rewrote {len(new_rows)} rows, dropped {dropped}")


def _remap_new_products(remap: dict[int, int]) -> None:
    path = INT / "proposed_new_products.csv"
    if not path.exists():
        print(f"skip: {path} not found", file=sys.stderr)
        return
    with path.open() as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys()) if rows else []

    def _remap_list(raw: str) -> str:
        if not raw:
            return raw
        out = []
        for token in raw.split(","):
            t = token.strip()
            if t and t.isdigit():
                old = int(t)
                out.append(str(remap.get(old, old)))
            elif t:
                out.append(t)
        return ",".join(out)

    for r in rows:
        r["linking_use_case_ids"] = _remap_list(r.get("linking_use_case_ids", ""))
        r["linking_consolidated_ids"] = _remap_list(r.get("linking_consolidated_ids", ""))

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"new_products: rewrote {len(rows)} rows (linking ids remapped)")


def main() -> int:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        old_to_sig = _build_old_id_to_signature()
        sig_to_new = _build_signature_to_new_id(conn)
        remap: dict[int, int] = {}
        misses: list[int] = []
        for old, sig in old_to_sig.items():
            new = sig_to_new.get(sig)
            if new and new != old:
                remap[old] = new
            elif new is None:
                misses.append(old)
        print(f"built remap: {len(remap)} stale ids → new ids; {len(misses)} unresolved")
        if misses[:5]:
            print(f"  first unresolved: {misses[:5]}", file=sys.stderr)

        _remap_links(remap)
        _remap_new_products(remap)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
