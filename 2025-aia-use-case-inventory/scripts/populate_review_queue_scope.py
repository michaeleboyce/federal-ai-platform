"""Populate ``review_queue_scope`` with rows that need LLM adjudication.

Phase 2 Agent E' — the per-row review micro-agent pattern.

Population rules (plan §E'):
  1. All consolidated rows where ``agency_uses IN ('N', NULL)`` and the
     text contains NO explicit agency-wide phrasing — these are the 36
     demotion candidates that the heuristic just re-tagged from
     enterprise_wide -> unknown.
  2. Random sample of 184 of the 443 rows that would have been tagged
     ``rag_pipeline`` / ``agentic_workflow`` under the OLD name-only
     keyword heuristic (stratified by agency).

Each queue row gets:
    use_case_id, consolidated_use_case_id, question_type,
    current_tag, heuristic_proposed_tag, raw_source

The LLM-review step fills in ``llm_proposed_tag``, ``llm_confidence``,
``llm_reasoning``.

Idempotent; safe to re-run (uses ``INSERT OR REPLACE`` keyed on the
(question_type, use_case_id, consolidated_use_case_id) triple).
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auto_tag import (  # noqa: E402
    AGENTIC_KEYWORDS,
    ENTERPRISE_WIDE_PHRASES,
    RAG_KEYWORDS,
    keyword_any,
    normalize,
)
from db import get_connection  # noqa: E402

RANDOM_SEED = 20260412
ARCH_SAMPLE_SIZE = 184


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS review_queue_scope (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_type TEXT NOT NULL,  -- 'scope' or 'architecture'
    use_case_id INTEGER REFERENCES use_cases(id),
    consolidated_use_case_id INTEGER REFERENCES consolidated_use_cases(id),
    current_tag TEXT,
    heuristic_proposed_tag TEXT,
    raw_source TEXT,
    llm_proposed_tag TEXT,
    llm_confidence TEXT,  -- 'high' | 'medium' | 'low'
    llm_reasoning TEXT,
    resolved_at TEXT,
    UNIQUE (question_type, use_case_id, consolidated_use_case_id)
);
CREATE INDEX IF NOT EXISTS idx_rqs_question ON review_queue_scope(question_type);
CREATE INDEX IF NOT EXISTS idx_rqs_confidence ON review_queue_scope(llm_confidence);
"""


def ensure_table(conn):
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def _old_arch_guess(row):
    """Reproduce the pre-Agent-E architecture heuristic to identify the
    443-row candidate set (rag_pipeline + agentic_workflow).
    """
    train_desc = normalize(row.get("training_data_description", ""))
    problem = normalize(
        (row.get("problem_statement") or "")
        + " "
        + (row.get("use_case_name") or "")
        + " "
        + (row.get("ai_use_case") or "")
    )
    if keyword_any(problem + " " + train_desc, RAG_KEYWORDS):
        return "rag_pipeline"
    if keyword_any(problem, AGENTIC_KEYWORDS):
        return "agentic_workflow"
    return None


def populate_scope_candidates(conn):
    """Consolidated EW demotion candidates: rows that WERE tagged
    ``enterprise_wide`` (under the old licenses-user-count heuristic) and
    whose ``agency_uses`` is 'N' or NULL. Plan §E': 29 (N) + 7 (NULL) = 36.

    After the retag migration runs first, these rows are already ``unknown``
    in the DB; we identify them by simulating the old heuristic rule that
    big licenses_users counts promoted to enterprise_wide.
    """
    rows = conn.execute(
        """
        SELECT c.id AS cid, c.ai_use_case, c.commercial_product,
               c.commercial_examples, c.agency_uses,
               c.estimated_licenses_users, c.raw_json,
               t.deployment_scope AS current_tag,
               a.abbreviation AS agency_abbr
        FROM consolidated_use_cases c
        JOIN agencies a ON a.id = c.agency_id
        LEFT JOIN use_case_tags t ON t.consolidated_use_case_id = c.id
        WHERE (c.agency_uses IS NULL OR UPPER(c.agency_uses) = 'N')
        """
    ).fetchall()

    def _is_scope_review_candidate(row) -> bool:
        """The plan identifies 36 consolidated rows with agency_uses IN
        ('N', NULL) that were tagged enterprise_wide under the old heuristic
        and are demoted to 'unknown' by plan §E.1. Post-migration the DB no
        longer tells us which subset those were, so we enqueue ALL
        consolidated rows with agency_uses IN ('N', NULL) — a superset that
        contains the 36 and gives the LLM micro-agent a chance to promote
        back to enterprise_wide where justified."""
        return (row["agency_uses"] or "").strip().upper() in ("", "N")

    inserted = 0
    for r in rows:
        if not _is_scope_review_candidate(r):
            continue  # not a review candidate
        text = normalize(
            (r["ai_use_case"] or "")
            + " "
            + (r["commercial_product"] or "")
            + " "
            + (r["commercial_examples"] or "")
        )
        if any(p in text for p in ENTERPRISE_WIDE_PHRASES):
            continue  # heuristic keeps these as enterprise_wide
        # Heuristic-proposed tag for this row under plan §E.1 is 'unknown'.
        raw_source = json.dumps(
            {
                "agency": r["agency_abbr"],
                "ai_use_case": r["ai_use_case"],
                "commercial_product": r["commercial_product"],
                "commercial_examples": r["commercial_examples"],
                "agency_uses": r["agency_uses"],
                "estimated_licenses_users": r["estimated_licenses_users"],
            }
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO review_queue_scope
                (question_type, use_case_id, consolidated_use_case_id,
                 current_tag, heuristic_proposed_tag, raw_source)
            VALUES ('scope', NULL, ?, ?, 'unknown', ?)
            """,
            (r["cid"], r["current_tag"], raw_source),
        )
        inserted += 1
    return inserted


def populate_architecture_candidates(conn):
    """Random sample of 184 rows (stratified by agency) that would have been
    tagged rag_pipeline or agentic_workflow under the OLD heuristic.
    """
    # Canonical use_cases.
    canonical = conn.execute(
        """
        SELECT u.id AS uid, u.use_case_name, u.problem_statement,
               u.training_data_description, u.vendor_name, u.raw_json,
               t.architecture_type AS current_tag,
               a.abbreviation AS agency_abbr
        FROM use_cases u
        JOIN agencies a ON a.id = u.agency_id
        LEFT JOIN use_case_tags t ON t.use_case_id = u.id
        """
    ).fetchall()
    # Consolidated too (plan counted 443 total).
    cons = conn.execute(
        """
        SELECT c.id AS cid, c.ai_use_case AS use_case_name,
               NULL AS problem_statement, NULL AS training_data_description,
               c.commercial_product AS vendor_name, c.raw_json,
               t.architecture_type AS current_tag,
               a.abbreviation AS agency_abbr
        FROM consolidated_use_cases c
        JOIN agencies a ON a.id = c.agency_id
        LEFT JOIN use_case_tags t ON t.consolidated_use_case_id = c.id
        """
    ).fetchall()

    candidates = []
    for r in canonical:
        d = dict(r)
        d["_kind"] = "canonical"
        guess = _old_arch_guess(d)
        if guess is not None:
            d["_guess"] = guess
            candidates.append(d)
    for r in cons:
        d = dict(r)
        d["_kind"] = "consolidated"
        guess = _old_arch_guess(d)
        if guess is not None:
            d["_guess"] = guess
            candidates.append(d)

    print(f"  architecture candidate pool: {len(candidates)}")

    # Stratify by agency. Aim for roughly proportional sampling up to 184.
    by_agency: dict[str, list] = {}
    for c in candidates:
        by_agency.setdefault(c["agency_abbr"], []).append(c)

    rng = random.Random(RANDOM_SEED)
    sampled: list[dict] = []
    if candidates:
        # Compute per-agency quota proportional to share, floor >=1 where agency
        # has any candidates, capped by total ARCH_SAMPLE_SIZE.
        total = len(candidates)
        quotas = {
            ag: max(1, round(len(rows) * ARCH_SAMPLE_SIZE / total))
            for ag, rows in by_agency.items()
        }
        # Adjust to total ARCH_SAMPLE_SIZE.
        while sum(quotas.values()) > ARCH_SAMPLE_SIZE:
            ag = max(quotas, key=lambda a: quotas[a])
            if quotas[ag] <= 1:
                break
            quotas[ag] -= 1
        while sum(quotas.values()) < ARCH_SAMPLE_SIZE and any(
            quotas[a] < len(by_agency[a]) for a in quotas
        ):
            ag = max(
                (a for a in quotas if quotas[a] < len(by_agency[a])),
                key=lambda a: len(by_agency[a]),
            )
            quotas[ag] += 1

        for ag, rows in by_agency.items():
            q = min(quotas.get(ag, 0), len(rows))
            sampled.extend(rng.sample(rows, q))

    inserted = 0
    for c in sampled:
        raw_source = json.dumps(
            {
                "agency": c["agency_abbr"],
                "use_case_name": c.get("use_case_name"),
                "problem_statement": c.get("problem_statement"),
                "training_data_description": c.get("training_data_description"),
                "vendor_name": c.get("vendor_name"),
            }
        )
        if c["_kind"] == "canonical":
            uc_id, cc_id = c["uid"], None
        else:
            uc_id, cc_id = None, c["cid"]
        conn.execute(
            """
            INSERT OR REPLACE INTO review_queue_scope
                (question_type, use_case_id, consolidated_use_case_id,
                 current_tag, heuristic_proposed_tag, raw_source)
            VALUES ('architecture', ?, ?, ?, ?, ?)
            """,
            (uc_id, cc_id, c["current_tag"], c["_guess"], raw_source),
        )
        inserted += 1
    return inserted


def main():
    conn = get_connection()
    try:
        ensure_table(conn)
        scope_n = populate_scope_candidates(conn)
        arch_n = populate_architecture_candidates(conn)
        conn.commit()
        print(f"Inserted {scope_n} scope + {arch_n} architecture review rows")
        total = conn.execute("SELECT COUNT(*) FROM review_queue_scope").fetchone()[0]
        print(f"review_queue_scope total = {total}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
