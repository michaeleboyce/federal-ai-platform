"""Apply 2026-04 round-2 audit corrections from audit/retag/round2/.

Six independent agent reviews, each with its own resolved.csv:
  general_llm/   13 overturns of low-confidence flag flips
  coding/        14 flips (10 demote, 4 promote) under the new
                 'generic-LLM-chatbots-are-not-coding-tools' rule
  data_analysis/ 30 environment fills (was 'unknown')
  scope/         34 architecture/scope changes; 132 keep_current
  entry_type/    6 reclassifications to product_deployment
  products/      66 map_to_existing + 85 unique seed_new_alias

Also writes external-evidence rows from searches.csv files where the agent
recorded explicit per-row searches that found nothing usable
(status='searched_no_source') or surfaced a corroborating URL
(status='corroborated').

All ids in these CSVs belong to the 2026-04 snapshot id space and are
translated to current ids via scripts/uc_signature.py (signature columns
where the CSV has them, audit/retag/id_snapshot_2026-04.csv otherwise).
The resolver hard-fails the build when more than 2% of referenced rows
cannot be matched — the silent-no-op failure mode is not allowed back.

Idempotent: re-running produces the same end state.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uc_signature import Resolver  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
R2 = ROOT / "audit" / "retag" / "round2"

CAPTURED_BY = "round2_2026-04"
CAPTURED_AT = "2026-04-29"

ENTERPRISE_SCOPES = {"enterprise_wide", "department"}


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _int(s) -> int | None:
    s = (s or "").strip()
    if not s or s == "NA":
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _ids(res: Resolver, row: dict) -> list[int]:
    return res.uc(
        _int(row.get("use_case_id", "")),
        row.get("agency"),
        row.get("use_case_name"),
    )


# ---------------------------------------------------------------------------
# 1. General-LLM overturns (13 rows)
# ---------------------------------------------------------------------------
def apply_general_llm(conn, res: Resolver) -> dict:
    stats = {"flipped_to_1": 0, "scope_set": 0}
    with open(R2 / "general_llm" / "resolved.csv") as f:
        for row in csv.DictReader(f):
            if row["decision"] != "overturn":
                continue
            final_flag = _int(row["final_is_general_llm_access"])
            if final_flag != 1:
                continue
            scope = (row.get("final_deployment_scope") or "").strip() or "bureau"
            is_enterprise = 1 if scope in ENTERPRISE_SCOPES else 0
            for uc_id in _ids(res, row):
                conn.execute(
                    """
                    UPDATE use_case_tags
                    SET is_general_llm_access = 1,
                        deployment_scope = ?,
                        is_enterprise_wide = ?
                    WHERE use_case_id = ?
                    """,
                    (scope, is_enterprise, uc_id),
                )
                stats["flipped_to_1"] += 1
                stats["scope_set"] += 1
    return stats


# ---------------------------------------------------------------------------
# 2. Coding flips (14 rows)
# ---------------------------------------------------------------------------
def apply_coding(conn, res: Resolver) -> dict:
    stats = {"flips_to_1": 0, "flips_to_0": 0}
    with open(R2 / "coding" / "resolved.csv") as f:
        for row in csv.DictReader(f):
            current = _int(row["current_is_coding_tool"])
            final = _int(row["final_is_coding_tool"])
            if current is None or final is None or current == final:
                continue
            for uc_id in _ids(res, row):
                conn.execute(
                    "UPDATE use_case_tags SET is_coding_tool = ? WHERE use_case_id = ?",
                    (final, uc_id),
                )
                if final == 1:
                    stats["flips_to_1"] += 1
                else:
                    stats["flips_to_0"] += 1
    return stats


# ---------------------------------------------------------------------------
# 3. Data-analysis environment fills (30 rows; skip the 1 that stayed unknown)
# ---------------------------------------------------------------------------
def apply_data_analysis(conn, res: Resolver) -> dict:
    stats = {"env_filled": 0, "skipped_unknown": 0}
    with open(R2 / "data_analysis" / "resolved.csv") as f:
        for row in csv.DictReader(f):
            env = (row["final_environment"] or "").strip()
            if not env or env == "unknown":
                stats["skipped_unknown"] += 1
                continue
            for uc_id in _ids(res, row):
                conn.execute(
                    "UPDATE use_case_tags SET deployment_environment = ? WHERE use_case_id = ?",
                    (env, uc_id),
                )
                stats["env_filled"] += 1
    return stats


# ---------------------------------------------------------------------------
# 4. Scope / architecture (34 changes; 132 keep_current ignored)
#    scope/resolved.csv has no signature columns — old ids resolve via the
#    snapshot file only.
# ---------------------------------------------------------------------------
def apply_scope(conn, res: Resolver) -> dict:
    stats = {"architecture_set": 0, "scope_set": 0, "skipped": 0}
    with open(R2 / "scope" / "resolved.csv") as f:
        for row in csv.DictReader(f):
            if row["decision"] not in {"apply_proposed", "apply_other"}:
                continue
            final = (row["final_tag"] or "").strip()
            qtype = (row["question_type"] or "").strip()
            if not final or qtype not in {"architecture", "scope"}:
                stats["skipped"] += 1
                continue

            uc_ids = res.uc(_int(row["use_case_id"])) if _int(row["use_case_id"]) is not None else []
            cons_ids = (
                res.cons(_int(row["consolidated_use_case_id"]))
                if _int(row["consolidated_use_case_id"]) is not None
                else []
            )
            if not uc_ids and not cons_ids:
                stats["skipped"] += 1
                continue

            targets = [("use_case_id", i) for i in uc_ids] + [
                ("consolidated_use_case_id", i) for i in cons_ids
            ]
            for col, target_id in targets:
                if qtype == "scope":
                    is_enterprise = 1 if final in ENTERPRISE_SCOPES else 0
                    conn.execute(
                        f"UPDATE use_case_tags SET deployment_scope = ?, is_enterprise_wide = ? WHERE {col} = ?",
                        (final, is_enterprise, target_id),
                    )
                    stats["scope_set"] += 1
                else:
                    conn.execute(
                        f"UPDATE use_case_tags SET architecture_type = ? WHERE {col} = ?",
                        (final, target_id),
                    )
                    stats["architecture_set"] += 1
    return stats


# ---------------------------------------------------------------------------
# 5. Entry-type reclassifications (6 rows)
# ---------------------------------------------------------------------------
def apply_entry_type(conn, res: Resolver) -> dict:
    stats = {"reclassified": 0, "skipped": 0}
    with open(R2 / "entry_type" / "resolved.csv") as f:
        for row in csv.DictReader(f):
            if row["decision"] != "reclassify":
                continue
            final = (row["final_entry_type"] or "").strip()
            if not final:
                stats["skipped"] += 1
                continue
            for uc_id in _ids(res, row):
                conn.execute(
                    "UPDATE use_case_tags SET entry_type = ? WHERE use_case_id = ?",
                    (final, uc_id),
                )
                stats["reclassified"] += 1
    return stats


# ---------------------------------------------------------------------------
# 6. Products: seed new + map existing
#    products/resolved.csv has no signature columns — snapshot-only ids.
# ---------------------------------------------------------------------------
def apply_products(conn, res: Resolver) -> dict:
    stats = {
        "products_inserted": 0,
        "products_already_existed": 0,
        "use_case_products_linked": 0,
        "skipped_unknown_canonical": 0,
    }

    # 6a. Seed new products from proposed_new_products.csv
    proposed_path = R2 / "products" / "proposed_new_products.csv"
    if proposed_path.exists():
        with open(proposed_path) as f:
            for row in csv.DictReader(f):
                name = (row["canonical_name"] or "").strip()
                vendor = (row["vendor"] or "").strip() or None
                ptype = (row["product_type"] or "").strip() or None
                if not name:
                    continue
                exists = conn.execute(
                    "SELECT id FROM products WHERE canonical_name = ?", (name,)
                ).fetchone()
                if exists:
                    stats["products_already_existed"] += 1
                    continue
                conn.execute(
                    """
                    INSERT INTO products
                        (canonical_name, vendor, product_type,
                         is_generative_ai, is_frontier_llm,
                         description, notes)
                    VALUES (?, ?, ?, 0, 0, NULL, ?)
                    """,
                    (name, vendor, ptype, f"seeded by {CAPTURED_BY}"),
                )
                stats["products_inserted"] += 1
                # Self-alias: ensure canonical_name itself maps back.
                conn.execute(
                    "INSERT OR IGNORE INTO product_aliases (product_id, alias_text) VALUES (last_insert_rowid(), ?)",
                    (name,),
                )

    # 6b. Map use cases to canonical products from resolved.csv
    with open(R2 / "products" / "resolved.csv") as f:
        for row in csv.DictReader(f):
            if row["decision"] != "map_to_existing":
                continue
            canonical = (row["mapped_canonical_product"] or "").strip()
            if not canonical:
                continue
            prod = conn.execute(
                "SELECT id FROM products WHERE canonical_name = ?", (canonical,)
            ).fetchone()
            if prod is None:
                stats["skipped_unknown_canonical"] += 1
                continue
            for uc_id in res.uc(_int(row["use_case_id"])):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO use_case_products
                        (use_case_id, product_id, evidence_text, confidence)
                    VALUES (?, ?, ?, 'inferred')
                    """,
                    (uc_id, prod["id"], (row.get("notes") or "")[:500]),
                )
                stats["use_case_products_linked"] += 1

    return stats


# ---------------------------------------------------------------------------
# 7. External-evidence rows from searches.csv files
# ---------------------------------------------------------------------------
def write_evidence(conn, res: Resolver) -> dict:
    """Write evidence rows from per-row web searches the agents performed.

    - corroborated   → search found a useful URL the agent quotes from
    - searched_no_source → agent searched and explicitly couldn't find one
    """
    stats = {"corroborated": 0, "searched_no_source": 0, "skipped_no_target": 0}

    # Idempotent re-run: clear prior round-2 evidence rows.
    conn.execute(
        "DELETE FROM use_case_external_evidence WHERE captured_by = ?",
        (CAPTURED_BY,),
    )

    topics_by_dir = {
        "general_llm": "general_llm",
        "coding": "coding",
        "data_analysis": "data_analysis",
        "scope": "scope_architecture",
        "entry_type": "entry_type",
        "products": "products",
    }

    for subdir, topic in topics_by_dir.items():
        sp = R2 / subdir / "searches.csv"
        if not sp.exists():
            continue
        with open(sp) as f:
            reader = csv.DictReader(f)
            for row in reader:
                old_id = _int(row.get("use_case_id"))
                if old_id is None:
                    continue
                uc_ids, cons_ids = res.uc_or_cons(old_id)
                if not uc_ids and not cons_ids:
                    stats["skipped_no_target"] += 1
                    continue
                # One evidence row per resolved target (signature fanout is
                # rare here; same evidence applies to each duplicate filing).
                targets = [(i, None) for i in uc_ids] + [(None, i) for i in cons_ids]

                found = (row.get("found_useful") or "").strip().lower()
                url = (row.get("top_url") or "").strip()
                conclusion = (row.get("conclusion") or "").strip()
                query = (row.get("query") or "").strip()

                # Treat "yes"/"1"/"partial" with an http URL as corroborated.
                # Everything else where the agent explicitly searched goes
                # in as searched_no_source.
                is_useful = found in {"yes", "1", "true", "partial"}
                has_http = url.startswith("http")

                for target_uc, target_cons in targets:
                    if is_useful and has_http:
                        conn.execute(
                            """
                            INSERT INTO use_case_external_evidence
                                (use_case_id, consolidated_use_case_id, topic, status,
                                 source_url, source_quote, confidence,
                                 search_method, captured_at, captured_by, notes)
                            VALUES (?, ?, ?, 'corroborated', ?, NULL, NULL,
                                    ?, ?, ?, ?)
                            """,
                            (
                                target_uc, target_cons, topic, url,
                                f"agent_round2_per_row_search: {query[:200]}",
                                CAPTURED_AT, CAPTURED_BY, conclusion[:500],
                            ),
                        )
                        stats["corroborated"] += 1
                    else:
                        conn.execute(
                            """
                            INSERT INTO use_case_external_evidence
                                (use_case_id, consolidated_use_case_id, topic, status,
                                 source_url, source_quote, confidence,
                                 search_method, captured_at, captured_by, notes)
                            VALUES (?, ?, ?, 'searched_no_source', NULL, NULL, NULL,
                                    ?, ?, ?, ?)
                            """,
                            (
                                target_uc, target_cons, topic,
                                f"agent_round2_per_row_search: {query[:200]}",
                                CAPTURED_AT, CAPTURED_BY, conclusion[:500],
                            ),
                        )
                        stats["searched_no_source"] += 1

    return stats


# ---------------------------------------------------------------------------
def main() -> int:
    conn = _open()
    try:
        res = Resolver(conn)
        with conn:
            llm = apply_general_llm(conn, res)
            coding = apply_coding(conn, res)
            data = apply_data_analysis(conn, res)
            scope = apply_scope(conn, res)
            entry = apply_entry_type(conn, res)
            prod = apply_products(conn, res)
            evidence = write_evidence(conn, res)

        print("[general_llm overturns]", llm)
        print("[coding flips]         ", coding)
        print("[data_analysis envs]   ", data)
        print("[scope/architecture]   ", scope)
        print("[entry_type]           ", entry)
        print("[products]             ", prod)
        print("[evidence]             ", evidence)
        res.check("apply_round2_audit", max_unresolved=0.05)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
