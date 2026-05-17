"""Compute the Federal AI Readiness Scorecard — 5 weighted dimensions, per agency.

This is the IFP-facing scorecard backing /readiness and /readiness/methodology
on the dashboard. The existing `agency_ai_maturity` table stays unchanged
(it's an editorial heuristic); this rubric is the *published, citable* one.

# CONSTANTS MUST STAY IN SYNC WITH dashboard/lib/readiness-rubric.ts

Five dimensions, weighted — designed to measure *state capacity*, not
disclosure compliance. An agency that filled out OMB's form perfectly but
buys all its AI as commercial chat wrappers scores lower than one that
ships fewer-but-internally-built systems with real ATOs.

  - internal_capacity         (30%) — share custom-coded + share in-house dev +
                                      share at deployed stage + share on
                                      agency-internal platforms
  - frontier_capability       (25%) — share frontier / agentic / custom-coded
  - procurement_hygiene       (20%) — share with ATO + FedRAMP coverage
  - risk_relevant_governance  (15%) — of *risky* use cases (PII, high-impact),
                                      share with any oversight signal
                                      (PIA URL, ATO, or hi_* fields filled)
  - adoption_breadth          (10%) — count + bureau participation, normalized

Each dimension returns a 0–100 score per agency. Composite is the weighted sum,
tier is the band the composite falls in (A/B/C/D/F), rank is dense-desc.

# What we DON'T score
Pure form-filling ("reporting quality" — non-null rate across M-25-21 fields)
was dropped from the v1.1 rubric because it conflates *compliance* with
*capacity*. The aggregate "% of use cases without risk documentation" is
still surfaced on the methodology page as a compliance caveat, not as a
scored dimension.

# FedRAMP join
We use `fedramp_product_links.inventory_product_id` (curated) — NOT a
name-based join. Top-50 product coverage is ~50% (verified 2026-05), well
above the 30% threshold for keeping FedRAMP in the score.

Idempotent: DELETE FROM agency_readiness then INSERT.
"""
from __future__ import annotations

import json
import sys
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a module OR `python3 scripts/compute_agency_readiness.py`.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from db import get_connection  # noqa: E402


# --- Rubric constants ------------------------------------------------------
# IMPORTANT: keep in sync with dashboard/lib/readiness-rubric.ts
RUBRIC_VERSION = "1.1"

WEIGHTS = {
    "internal_capacity": 0.30,
    "frontier_capability": 0.25,
    "procurement_hygiene": 0.20,
    "risk_relevant_governance": 0.15,
    "adoption_breadth": 0.10,
}

# (tier, min_inclusive, max_inclusive, label)
TIER_BANDS = [
    ("A", 70, 100, "Frontier-Ready"),
    ("B", 55,  69, "Operational"),
    ("C", 35,  54, "Building"),
    ("D", 15,  34, "Preliminary"),
    ("F",  0,  14, "Insufficient Capacity"),
]

# Fields used to surface the *compliance* baseline on the methodology page
# (not scored as a dimension in v1.1). Kept here so the methodology page
# can compute "M-25-21 disclosure completeness" as a caveat.
COMPLIANCE_FIELDS = [
    "problem_statement",
    "expected_benefits",
    "system_outputs",
    "vendor_name",
    "training_data_description",
    "link_to_data",
    "justification",
    "ai_classification",
    "topic_area",
    "stage_of_development",
]


# --- Helpers ---------------------------------------------------------------

def _truthy(s: str | None) -> bool:
    """Encode the messy 'yes/no/N/A/PTA, ATO/...' has_ato + has_custom_code
    values as a boolean. Affirmative tokens count; any 'no'/'n/a'/empty
    doesn't. Conservative — partial-credit strings like 'PTA, ATO' do count
    (an ATO is present), but 'PTA, waiver' does not.
    """
    if not s:
        return False
    t = s.strip().lower()
    if not t or t in {"no", "n/a", "not applicable", "false", "0"}:
        return False
    # Common affirmative encodings observed in the data
    if t in {"yes", "true", "1"}:
        return True
    # Multi-tag strings — affirm if "ato" appears AND no negation.
    if "ato" in t and "waiver" not in t and "under review" not in t and "in-progress" not in t:
        return True
    return False


def _list_agencies(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """All agencies in the agencies table — even those with 0 use cases get scored."""
    return conn.execute(
        "SELECT id, abbreviation, name FROM agencies ORDER BY id"
    ).fetchall()


def _rank_normalize(values: dict[int, float]) -> dict[int, float]:
    """Map raw values into 0–100 by linear position between min and max.

    If all values are the same (e.g. all zero), every agency scores 0.
    """
    if not values:
        return {}
    vmax = max(values.values())
    vmin = min(values.values())
    if vmax == vmin:
        # All identical; if vmax > 0 score everyone 100, else 0.
        score = 100.0 if vmax > 0 else 0.0
        return {aid: score for aid in values}
    span = vmax - vmin
    return {aid: ((v - vmin) / span) * 100.0 for aid, v in values.items()}


# --- Dimension calculators -------------------------------------------------

def compute_adoption_breadth(conn: sqlite3.Connection) -> tuple[dict[int, float], dict[int, dict]]:
    """Two sub-signals, averaged after rank-normalization to 0–100:
      1) Total entries (use_cases + consolidated_use_cases).
      2) Share of bureaus participating — distinct non-null bureau_component
         strings on use_cases. Templates are not used (template_id is null
         on use_cases in current data).

    Returns (scores, raw_inputs_per_agency).
    """
    agencies = _list_agencies(conn)
    raw_counts: dict[int, int] = {}
    raw_bureaus: dict[int, int] = {}
    raw_templates: dict[int, int] = {}

    for a in agencies:
        aid = a["id"]
        c_uc = conn.execute(
            "SELECT COUNT(*) FROM use_cases WHERE agency_id = ?", (aid,)
        ).fetchone()[0]
        c_cons = conn.execute(
            "SELECT COUNT(*) FROM consolidated_use_cases WHERE agency_id = ?",
            (aid,),
        ).fetchone()[0]
        raw_counts[aid] = c_uc + c_cons

        b = conn.execute(
            """
            SELECT COUNT(DISTINCT bureau_component)
              FROM use_cases
             WHERE agency_id = ?
               AND bureau_component IS NOT NULL
               AND TRIM(bureau_component) <> ''
            """,
            (aid,),
        ).fetchone()[0]
        raw_bureaus[aid] = b or 0

        t = conn.execute(
            """
            SELECT COUNT(DISTINCT template_id) FROM (
                SELECT template_id FROM use_cases
                 WHERE agency_id = ? AND template_id IS NOT NULL
                UNION
                SELECT template_id FROM consolidated_use_cases
                 WHERE agency_id = ? AND template_id IS NOT NULL
            )
            """,
            (aid, aid),
        ).fetchone()[0]
        raw_templates[aid] = t or 0

    score_count = _rank_normalize(raw_counts)
    score_bureau = _rank_normalize(raw_bureaus)
    score_tmpl = _rank_normalize(raw_templates)

    # If templates are all-zero (current data state), drop that subscore so
    # we don't dilute the dimension with a constant-zero signal.
    use_templates = max(raw_templates.values(), default=0) > 0

    scores: dict[int, float] = {}
    raw: dict[int, dict] = {}
    for a in agencies:
        aid = a["id"]
        parts = [score_count.get(aid, 0.0), score_bureau.get(aid, 0.0)]
        if use_templates:
            parts.append(score_tmpl.get(aid, 0.0))
        scores[aid] = round(sum(parts) / len(parts), 2)
        raw[aid] = {
            "entries": raw_counts[aid],
            "bureaus": raw_bureaus[aid],
            "templates": raw_templates[aid],
        }
    return scores, raw


def compute_frontier_capability(conn: sqlite3.Connection) -> tuple[dict[int, float], dict[int, dict]]:
    """Weighted sum of three shares per agency:
       0.4 * share(is_frontier_model)
     + 0.3 * share(is_agentic_ai or ai_sophistication='agentic')
     + 0.3 * share(has_custom_code truthy)
    Multiplied by 100. Sub-shares are over use_cases per agency.
    """
    agencies = _list_agencies(conn)
    scores: dict[int, float] = {}
    raw: dict[int, dict] = {}

    for a in agencies:
        aid = a["id"]
        total = conn.execute(
            "SELECT COUNT(*) FROM use_cases WHERE agency_id = ?", (aid,)
        ).fetchone()[0]
        if total == 0:
            scores[aid] = 0.0
            raw[aid] = {"frontier": 0, "agentic": 0, "custom": 0, "total": 0}
            continue

        frontier = conn.execute(
            """
            SELECT COUNT(*) FROM use_case_tags t
            JOIN use_cases uc ON uc.id = t.use_case_id
            WHERE uc.agency_id = ? AND t.is_frontier_model = 1
            """,
            (aid,),
        ).fetchone()[0]

        # `is_agentic_ai` exists in some schema snapshots (and in our test
        # fixture); production schema only has the ai_sophistication enum.
        # Use the enum as the primary signal and OR in the boolean flag
        # only when the column exists in this DB.
        has_agentic_col = any(
            r[1] == "is_agentic_ai"
            for r in conn.execute("PRAGMA table_info(use_case_tags)")
        )
        if has_agentic_col:
            agentic = conn.execute(
                """
                SELECT COUNT(*) FROM use_case_tags t
                JOIN use_cases uc ON uc.id = t.use_case_id
                WHERE uc.agency_id = ?
                  AND (t.ai_sophistication = 'agentic'
                       OR COALESCE(t.is_agentic_ai, 0) = 1)
                """,
                (aid,),
            ).fetchone()[0]
        else:
            agentic = conn.execute(
                """
                SELECT COUNT(*) FROM use_case_tags t
                JOIN use_cases uc ON uc.id = t.use_case_id
                WHERE uc.agency_id = ? AND t.ai_sophistication = 'agentic'
                """,
                (aid,),
            ).fetchone()[0]

        # has_custom_code is messy ('Yes'/'No'/'TRUE'/'FALSE'/...)
        custom_rows = conn.execute(
            "SELECT has_custom_code FROM use_cases WHERE agency_id = ?", (aid,)
        ).fetchall()
        custom = sum(1 for r in custom_rows if _truthy(r["has_custom_code"]))

        share_frontier = frontier / total
        share_agentic = agentic / total
        share_custom = custom / total
        composite = (
            0.4 * share_frontier + 0.3 * share_agentic + 0.3 * share_custom
        ) * 100.0
        # Cap at 100 (the three shares can collectively exceed 1 if many
        # use cases qualify under multiple categories — that's fine but the
        # output is a 0–100 score, not an unbounded weighted sum).
        scores[aid] = round(min(composite, 100.0), 2)
        raw[aid] = {
            "frontier": frontier,
            "agentic": agentic,
            "custom_code": custom,
            "total_use_cases": total,
        }
    return scores, raw


def compute_procurement_hygiene(conn: sqlite3.Connection) -> tuple[dict[int, float], dict[int, dict]]:
    """Average of two shares, multiplied by 100:
       - share of use_cases where has_ato is truthy
       - share of distinct products in this agency's use_cases that have at
         least one fedramp_product_links row

    Both sub-shares are 0–1.
    """
    agencies = _list_agencies(conn)
    scores: dict[int, float] = {}
    raw: dict[int, dict] = {}

    # Pre-compute the set of FedRAMP-linked inventory product IDs.
    fedramp_linked = {
        r["inventory_product_id"]
        for r in conn.execute(
            "SELECT DISTINCT inventory_product_id FROM fedramp_product_links"
        ).fetchall()
    }

    for a in agencies:
        aid = a["id"]
        total = conn.execute(
            "SELECT COUNT(*) FROM use_cases WHERE agency_id = ?", (aid,)
        ).fetchone()[0]

        if total == 0:
            scores[aid] = 0.0
            raw[aid] = {
                "ato_yes": 0,
                "ato_total": 0,
                "products_total": 0,
                "products_fedramp": 0,
            }
            continue

        ato_rows = conn.execute(
            "SELECT has_ato FROM use_cases WHERE agency_id = ?", (aid,)
        ).fetchall()
        ato_yes = sum(1 for r in ato_rows if _truthy(r["has_ato"]))
        share_ato = ato_yes / total

        # Distinct products attached to this agency's use_cases.
        prod_ids = [
            r["product_id"]
            for r in conn.execute(
                """
                SELECT DISTINCT ucp.product_id
                  FROM use_case_products ucp
                  JOIN use_cases uc ON uc.id = ucp.use_case_id
                 WHERE uc.agency_id = ?
                """,
                (aid,),
            ).fetchall()
        ]
        products_total = len(prod_ids)
        products_fedramp = sum(1 for pid in prod_ids if pid in fedramp_linked)
        if products_total > 0:
            share_fedramp = products_fedramp / products_total
        else:
            share_fedramp = 0.0

        composite = ((share_ato + share_fedramp) / 2.0) * 100.0
        scores[aid] = round(composite, 2)
        raw[aid] = {
            "ato_yes": ato_yes,
            "ato_total": total,
            "products_total": products_total,
            "products_fedramp": products_fedramp,
        }
    return scores, raw


def _is_inhouse_dev(s: str | None) -> bool:
    """Match 'b) Developed in-house', 'Developed in-house', 'Developed in house',
    and 'c) Developed with both contracting and in-house resources'. Anything
    with 'in' followed by an optional hyphen/space and 'house' counts.
    """
    if not s:
        return False
    t = s.lower().replace("-", " ")
    return "in house" in t


def _is_deployed_stage(s: str | None) -> bool:
    """Match production M-25-21 ('c) Deployed ...') and the legacy
    'Operation and Maintenance' label. Pre-deployment, pilot, initiated,
    acquisition, and retired do not count.
    """
    if not s:
        return False
    t = s.lower()
    return "deployed" in t or "operation and maintenance" in t


def _is_high_impact(s: str | None) -> bool:
    """Match 'a) High-impact', 'High-impact', and the simple 'Yes' encoding
    sometimes used in agency-filed forms. 'Not high-impact',
    'Presumed high-impact but determined not high-impact', and 'Neither'
    do not count.
    """
    if not s:
        return False
    t = s.strip().lower()
    if t.startswith("a)"):
        return True
    if t.startswith("high-impact") or t.startswith("high impact"):
        return True
    if t == "yes":
        return True
    return False


def _has_pii(s: str | None) -> bool:
    """Match 'Yes', 'Yes - ...' variants. 'No', 'N/A', 'FALSE', and empty
    don't count.
    """
    if not s:
        return False
    t = s.strip().lower()
    return t.startswith("yes")


def compute_internal_capacity(conn: sqlite3.Connection) -> tuple[dict[int, float], dict[int, dict]]:
    """Capacity-first dimension. Average of four sub-shares per agency × 100:
       - share with has_custom_code truthy
       - share with development_type indicating in-house involvement
       - share at deployed stage (not pre-deployment / pilot / retired)
       - share linked to a product with product_origin='agency_internal_platform'

    Measures the agency's actual technical capability — building, shipping,
    running AI as opposed to buying commercial chat wrappers.
    """
    agencies = _list_agencies(conn)
    scores: dict[int, float] = {}
    raw: dict[int, dict] = {}

    # Pre-compute the set of internal-platform product IDs. The
    # `product_origin` column is optional — older schema snapshots and
    # test fixtures may not have it. If absent, treat the set as empty
    # (and the internal_platform sub-share will be 0 for all agencies).
    has_origin_col = any(
        r[1] == "product_origin"
        for r in conn.execute("PRAGMA table_info(products)")
    )
    internal_platform_pids: set[int] = set()
    if has_origin_col:
        internal_platform_pids = {
            r["id"]
            for r in conn.execute(
                "SELECT id FROM products WHERE product_origin = 'agency_internal_platform'"
            ).fetchall()
        }

    # Detect optional use_cases columns that the fixture may omit.
    uc_cols = {r[1] for r in conn.execute("PRAGMA table_info(use_cases)")}
    select_cols = ["id", "has_custom_code"]
    has_dev_type = "development_type" in uc_cols
    if has_dev_type:
        select_cols.append("development_type")
    select_cols.append("stage_of_development")
    select_sql = ", ".join(select_cols)

    for a in agencies:
        aid = a["id"]
        rows = conn.execute(
            f"SELECT {select_sql} FROM use_cases WHERE agency_id = ?",
            (aid,),
        ).fetchall()
        total = len(rows)
        if total == 0:
            scores[aid] = 0.0
            raw[aid] = {
                "custom_code": 0, "inhouse_dev": 0, "deployed": 0,
                "internal_platform": 0, "total_use_cases": 0,
            }
            continue

        custom = sum(1 for r in rows if _truthy(r["has_custom_code"]))
        inhouse = (
            sum(1 for r in rows if _is_inhouse_dev(r["development_type"]))
            if has_dev_type else 0
        )
        deployed = sum(1 for r in rows if _is_deployed_stage(r["stage_of_development"]))

        if internal_platform_pids:
            internal_platform = conn.execute(
                f"""
                SELECT COUNT(DISTINCT uc.id)
                  FROM use_cases uc
                  JOIN use_case_products ucp ON ucp.use_case_id = uc.id
                 WHERE uc.agency_id = ?
                   AND ucp.product_id IN ({",".join("?" * len(internal_platform_pids))})
                """,
                (aid, *internal_platform_pids),
            ).fetchone()[0]
        else:
            internal_platform = 0

        composite = (
            (custom / total)
            + (inhouse / total)
            + (deployed / total)
            + (internal_platform / total)
        ) / 4.0 * 100.0
        scores[aid] = round(min(composite, 100.0), 2)
        raw[aid] = {
            "custom_code": custom,
            "inhouse_dev": inhouse,
            "deployed": deployed,
            "internal_platform": internal_platform,
            "total_use_cases": total,
        }
    return scores, raw


def compute_risk_relevant_governance(conn: sqlite3.Connection) -> tuple[dict[int, float], dict[int, dict]]:
    """Of *risky* use cases (PII present OR high-impact designation), share
    that have at least one meaningful oversight signal:
       - pia_url present, OR
       - has_ato truthy, OR
       - at least 2 of the 9 hi_* Section-5 fields filled

    Score is 0–100. Agencies with no risky use cases score 0 (we don't reward
    *absence* of risk — that's not a capacity signal). Methodology page calls
    this out: agencies that haven't deployed risky systems can't earn this
    dimension, but they also can't fail it loudly; the rubric weights it at
    only 15% precisely because not all agencies face equal risk exposure.
    """
    agencies = _list_agencies(conn)
    scores: dict[int, float] = {}
    raw: dict[int, dict] = {}

    HI_FIELDS = [
        "hi_testing_conducted", "hi_assessment_completed", "hi_potential_impacts",
        "hi_independent_review", "hi_ongoing_monitoring", "hi_training_established",
        "hi_failsafe_presence", "hi_appeal_process", "hi_public_consultation",
    ]

    # Detect which hi_* fields actually exist (the test fixture omits some).
    table_cols = {
        r[1] for r in conn.execute("PRAGMA table_info(use_cases)")
    }
    present_hi = [f for f in HI_FIELDS if f in table_cols]
    has_pia = "pia_url" in table_cols

    hi_select = (
        ", ".join(present_hi) + ", " if present_hi else ""
    )
    pia_select = "pia_url, " if has_pia else ""

    for a in agencies:
        aid = a["id"]
        rows = conn.execute(
            f"""
            SELECT {hi_select}{pia_select}has_ato, has_pii, is_high_impact
              FROM use_cases
             WHERE agency_id = ?
            """,
            (aid,),
        ).fetchall()
        risky_total = 0
        risky_with_oversight = 0
        for r in rows:
            risky = _has_pii(r["has_pii"]) or _is_high_impact(r["is_high_impact"])
            if not risky:
                continue
            risky_total += 1

            # Oversight signal: PIA URL, ATO, or >=2 hi_* fields filled.
            has_pia_url = (
                has_pia
                and r["pia_url"] is not None
                and str(r["pia_url"]).strip() != ""
            )
            has_ato_flag = _truthy(r["has_ato"])
            hi_filled = sum(
                1 for f in present_hi
                if r[f] is not None
                and str(r[f]).strip() not in ("", "n/a", "na", "none", "not applicable", "-")
            )
            if has_pia_url or has_ato_flag or hi_filled >= 2:
                risky_with_oversight += 1

        if risky_total == 0:
            scores[aid] = 0.0
        else:
            scores[aid] = round((risky_with_oversight / risky_total) * 100.0, 2)
        raw[aid] = {
            "risky_total": risky_total,
            "risky_with_oversight": risky_with_oversight,
            "total_use_cases": len(rows),
        }
    return scores, raw


# --- Tier band lookup ------------------------------------------------------

def assign_tier(composite: float) -> tuple[str, str]:
    """Assign tier by composite score. Bands published in TIER_BANDS use
    integer ranges; in practice composite is a float, so any value at or
    above the band's lower bound (and strictly below the next higher
    band's lower bound) maps to that band. This matches the methodology
    page's reader-friendly thresholds (A=75+, B=60+, C=40+, D=20+, F=<20).
    """
    # TIER_BANDS is ordered A→F; walk it and return the first whose
    # lower bound the composite meets.
    for tier, lo, _hi, label in TIER_BANDS:
        if composite >= lo:
            return tier, label
    return "F", "Insufficient Reporting"


# --- Headline stats --------------------------------------------------------

def compute_headline_stats(conn: sqlite3.Connection, scored: list[dict]) -> dict:
    """Capacity-first headline candidates for the homepage hero.

    The compliance-leaning `hi_no_risk_docs_pct` is still computed and
    surfaced (the methodology page uses it as a caveat) but it's NOT the
    feature stat — counting form-fill rates conflates compliance with
    capacity.
    """
    total_uc = conn.execute("SELECT COUNT(*) FROM use_cases").fetchone()[0] or 1

    # --- Capacity-revealing numbers ---

    # 1) internal_build_pct — share of use cases that are internally built
    #    (custom-coded OR in-house dev OR on an agency-internal platform).
    #    Most direct measure of "the federal government builds AI" vs
    #    "the federal government buys AI."
    has_origin_col = any(
        r[1] == "product_origin"
        for r in conn.execute("PRAGMA table_info(products)")
    )
    internal_platform_pids: set[int] = set()
    if has_origin_col:
        internal_platform_pids = {
            r["id"]
            for r in conn.execute(
                "SELECT id FROM products WHERE product_origin = 'agency_internal_platform'"
            ).fetchall()
        }
    uc_cols = {r[1] for r in conn.execute("PRAGMA table_info(use_cases)")}
    has_dev_type = "development_type" in uc_cols
    cols = "id, has_custom_code" + (", development_type" if has_dev_type else "")
    rows = conn.execute(f"SELECT {cols} FROM use_cases").fetchall()
    internal_uc_ids = set()
    for r in rows:
        if _truthy(r["has_custom_code"]):
            internal_uc_ids.add(r["id"])
        elif has_dev_type and _is_inhouse_dev(r["development_type"]):
            internal_uc_ids.add(r["id"])
    if internal_platform_pids:
        for r in conn.execute(
            f"""
            SELECT DISTINCT uc.id FROM use_cases uc
            JOIN use_case_products ucp ON ucp.use_case_id = uc.id
            WHERE ucp.product_id IN ({",".join("?" * len(internal_platform_pids))})
            """,
            tuple(internal_platform_pids),
        ).fetchall():
            internal_uc_ids.add(r["id"])
    internal_build_pct = round(100.0 * (len(internal_uc_ids) / total_uc), 1)

    # 2) production_rate_pct — share of use cases at deployed stage. Real
    #    deployment, not pilots/proofs-of-concept.
    deployed_count = sum(
        1 for r in conn.execute("SELECT stage_of_development FROM use_cases").fetchall()
        if _is_deployed_stage(r["stage_of_development"])
    )
    production_rate_pct = round(100.0 * (deployed_count / total_uc), 1)

    # 3) fedramp_coverage_pct — share of use cases attached to a product
    #    that has at least one FedRAMP authorization link. Procurement
    #    hygiene at federal scale.
    uc_total = conn.execute(
        """
        SELECT COUNT(DISTINCT uc.id)
          FROM use_cases uc
          JOIN use_case_products ucp ON ucp.use_case_id = uc.id
        """
    ).fetchone()[0] or 1
    uc_fedramp = conn.execute(
        """
        SELECT COUNT(DISTINCT uc.id)
          FROM use_cases uc
          JOIN use_case_products ucp ON ucp.use_case_id = uc.id
          JOIN fedramp_product_links fpl ON fpl.inventory_product_id = ucp.product_id
        """
    ).fetchone()[0] or 0
    fedramp_coverage_pct = round(100.0 * (uc_fedramp / uc_total), 1)

    # 4) frontier_ready_agency_count — how many scored A.
    frontier_ready_agency_count = sum(1 for r in scored if r["tier"] == "A")

    # --- Compliance baseline (caveat, not headline) ---
    # Preserved so the methodology page can explicitly contrast capacity
    # measures with the form-fill metric the rubric is rejecting.
    with_risk = conn.execute(
        """
        SELECT COUNT(*) FROM use_case_tags t
        JOIN use_cases uc ON uc.id = t.use_case_id
        WHERE t.has_meaningful_risk_docs = 1
        """
    ).fetchone()[0] or 0
    hi_no_risk_docs_pct = round(100.0 * (1.0 - (with_risk / total_uc)), 1)

    return {
        "internal_build_pct": internal_build_pct,
        "production_rate_pct": production_rate_pct,
        "fedramp_coverage_pct": fedramp_coverage_pct,
        "frontier_ready_agency_count": frontier_ready_agency_count,
        "total_agencies_scored": len(scored),
        # Compliance baseline — not for headline use:
        "hi_no_risk_docs_pct": hi_no_risk_docs_pct,
    }


# --- Main entrypoint -------------------------------------------------------

def compute_agency_readiness(conn: sqlite3.Connection | None = None) -> dict:
    """Compute and persist agency_readiness. Returns the headline stats."""
    own = conn is None
    if conn is None:
        conn = get_connection()
    try:
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "WEIGHTS must sum to 1.0"

        internal, raw_ic = compute_internal_capacity(conn)
        frontier, raw_fr = compute_frontier_capability(conn)
        procurement, raw_pr = compute_procurement_hygiene(conn)
        governance, raw_gv = compute_risk_relevant_governance(conn)
        adoption, raw_ad = compute_adoption_breadth(conn)

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")

        # Build composite + raw row per agency
        rows: list[dict] = []
        for a in _list_agencies(conn):
            aid = a["id"]
            ic = internal.get(aid, 0.0)
            fr = frontier.get(aid, 0.0)
            pr = procurement.get(aid, 0.0)
            gv = governance.get(aid, 0.0)
            ad = adoption.get(aid, 0.0)
            composite = (
                ic * WEIGHTS["internal_capacity"]
                + fr * WEIGHTS["frontier_capability"]
                + pr * WEIGHTS["procurement_hygiene"]
                + gv * WEIGHTS["risk_relevant_governance"]
                + ad * WEIGHTS["adoption_breadth"]
            )
            composite = round(composite, 2)
            tier, tier_label = assign_tier(composite)
            headline_inputs = {
                "internal_capacity": raw_ic.get(aid, {}),
                "frontier_capability": raw_fr.get(aid, {}),
                "procurement_hygiene": raw_pr.get(aid, {}),
                "risk_relevant_governance": raw_gv.get(aid, {}),
                "adoption_breadth": raw_ad.get(aid, {}),
            }
            rows.append({
                "agency_id": aid,
                "abbreviation": a["abbreviation"],
                "internal_capacity": ic,
                "frontier_capability": fr,
                "procurement_hygiene": pr,
                "risk_relevant_governance": gv,
                "adoption_breadth": ad,
                "composite_score": composite,
                "tier": tier,
                "tier_label": tier_label,
                "headline_inputs_json": json.dumps(headline_inputs),
            })

        # Dense rank by composite desc
        rows.sort(key=lambda r: (-r["composite_score"], r["abbreviation"]))
        prev_score = None
        prev_rank = 0
        for i, r in enumerate(rows):
            if r["composite_score"] != prev_score:
                prev_rank = i + 1
                prev_score = r["composite_score"]
            r["rank"] = prev_rank

        with conn:
            conn.execute("DELETE FROM agency_readiness")
            for r in rows:
                conn.execute(
                    """
                    INSERT INTO agency_readiness (
                        agency_id, internal_capacity, frontier_capability,
                        procurement_hygiene, risk_relevant_governance,
                        adoption_breadth, composite_score,
                        tier, tier_label, rank, headline_inputs_json, computed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        r["agency_id"], r["internal_capacity"], r["frontier_capability"],
                        r["procurement_hygiene"], r["risk_relevant_governance"],
                        r["adoption_breadth"], r["composite_score"],
                        r["tier"], r["tier_label"], r["rank"],
                        r["headline_inputs_json"], now,
                    ),
                )

        headline = compute_headline_stats(conn, rows)
        return {"rows": rows, "headline": headline, "computed_at": now}
    finally:
        if own:
            conn.close()


def main() -> int:
    result = compute_agency_readiness()
    rows = result["rows"]
    headline = result["headline"]

    print("\n=== Agency AI Readiness — top 10 by composite ===")
    print(f"{'Rank':>4} {'Agency':<10} {'Composite':>9} {'Tier':<6} "
          f"{'Internl':>7} {'Frontr':>6} {'Procmt':>6} {'RiskGv':>6} {'Adopt':>6}")
    for r in sorted(rows, key=lambda r: r["rank"])[:10]:
        print(f"{r['rank']:>4} {r['abbreviation']:<10} "
              f"{r['composite_score']:>9.2f} {r['tier']:<6} "
              f"{r['internal_capacity']:>7.1f} {r['frontier_capability']:>6.1f} "
              f"{r['procurement_hygiene']:>6.1f} {r['risk_relevant_governance']:>6.1f} "
              f"{r['adoption_breadth']:>6.1f}")

    print("\n=== Tier distribution ===")
    tiers: dict[str, int] = {}
    for r in rows:
        tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    for tier, _, _, label in TIER_BANDS:
        print(f"  {tier} ({label}): {tiers.get(tier, 0)}")

    print("\n=== Capacity-first headline candidates ===")
    print(f"  internal_build_pct          = {headline['internal_build_pct']}%")
    print(f"  production_rate_pct         = {headline['production_rate_pct']}%")
    print(f"  fedramp_coverage_pct        = {headline['fedramp_coverage_pct']}%")
    print(f"  frontier_ready_agency_count = {headline['frontier_ready_agency_count']} of {headline['total_agencies_scored']}")
    print(f"\n=== Compliance baseline (caveat, not headline) ===")
    print(f"  hi_no_risk_docs_pct         = {headline['hi_no_risk_docs_pct']}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
