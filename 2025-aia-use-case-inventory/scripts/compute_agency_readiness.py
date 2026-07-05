"""Compute the Federal AI Readiness Scorecard — 5 weighted dimensions, per agency.

This is the IFP-facing scorecard backing /readiness and /readiness/methodology
on the dashboard. The existing `agency_ai_maturity` table stays unchanged
(it's an editorial heuristic); this rubric is the *published, citable* one.

# CONSTANTS MUST STAY IN SYNC WITH dashboard/lib/readiness/rubric.ts

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
                                      share with any oversight signal,
                                      shrunk toward the federal rate (v1.2)
  - adoption_breadth          (10%) — count + bureau participation, normalized

Each dimension returns a 0–100 score per agency. Composite is the weighted sum,
tier is the band the composite falls in (A/B/C/D/F), rank is dense-desc.

# v1.2 methodology corrections (2026-07)

1. "Deployed" reads the canonical `use_cases.stage_normalized` bucket
   (written by scripts/normalize_use_case_fields.py) instead of a substring
   match. The v1.1 substring matched the *Pilot* label text ("has been
   deployed in a limited test or pilot capacity"), counting 423 pilots as
   deployed. Where the column is absent (test fixtures), a Python port of
   the same CASE is used.
2. Effective-unit dedup: rows within an agency sharing an identical
   problem_statement (>= 25 chars), vendor_name, and development_type are
   scored as ONE unit. Stops atomized filings (one rollout filed as a
   dozen near-identical rows) from inflating every share-based dimension.
3. In-house cross-check: a *pure* "Developed in-house" claim only earns
   in-house credit when the row has no commercial vendor or has custom
   code. Hybrid ("both contracting and in-house") claims keep credit.
4. Risk-relevant governance is shrunk toward the pooled federal oversight
   rate (Empirical Bayes, K=5): score = (x + K*p0) / (n + K). An agency
   can no longer bank a perfect 100 off a single risky row. Zero-risky
   agencies still score 0 (absence of risk exposure is not a capability).
   The oversight predicate is also tightened: pia_url must be an actual
   URL (84% of non-blank values are placeholder text), and hi_* placeholder
   comparison is case-insensitive ("N/A" no longer counts as filled).
5. Retired units are excluded from stage-share denominators (deployed
   share, production rate); they still count toward adoption breadth.
6. Headline stats are persisted to the 1-row `readiness_headline` table
   (migration m018) — the dashboard reads it instead of re-deriving in
   TypeScript, eliminating the dual-implementation drift class.

# What we DON'T score
Pure form-filling ("reporting quality" — non-null rate across M-25-21 fields)
was dropped from the v1.1 rubric because it conflates *compliance* with
*capacity*. The aggregate "% of use cases without risk documentation" is
still surfaced on the methodology page as a compliance caveat, not as a
scored dimension.

# FedRAMP join
We use `fedramp_product_links.inventory_product_id` (curated) — NOT a
name-based join. NOTE: the Makefile runs this script AFTER the FedRAMP
link-recovery block (link_fedramp / promote / decisions) as of v1.2, so
the score sees the fully-recovered link set.

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
# IMPORTANT: keep in sync with dashboard/lib/readiness/rubric.ts
RUBRIC_VERSION = "1.2"

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

# Empirical-Bayes shrinkage strength for risk_relevant_governance. With K=5,
# an agency with one perfectly-overseen risky case scores ~(1+5*p0)/6 instead
# of 100; an agency with 90+ risky cases is barely moved off its raw rate.
GOVERNANCE_SHRINKAGE_K = 5

# Rows whose problem_statement is at least this long participate in
# effective-unit dedup; shorter/blank statements ("N/A", "TBD") are too
# generic to be a duplicate-filing signature and stay row-unique.
DEDUP_MIN_PROBLEM_LEN = 25

# vendor_name values that do NOT contradict an in-house development claim.
PLACEHOLDER_VENDORS = {
    "", "n/a", "na", "none", "not applicable", "in-house", "in house",
    "internal", "-", "multiple", "various", "tbd", "unknown",
}

# Fields used to surface the *compliance* baseline on the methodology page
# (not scored as a dimension). Kept so the methodology page can compute
# "M-25-21 disclosure completeness" as a caveat.
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

HI_FIELDS = [
    "hi_testing_conducted", "hi_assessment_completed", "hi_potential_impacts",
    "hi_independent_review", "hi_ongoing_monitoring", "hi_training_established",
    "hi_failsafe_presence", "hi_appeal_process", "hi_public_consultation",
]

HI_PLACEHOLDERS = {"", "n/a", "na", "none", "not applicable", "-"}


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


def _stage_bucket(normalized: str | None, raw: str | None) -> str:
    """Canonical stage bucket for a row. Prefers the `stage_normalized`
    column; where absent/null (test fixtures, pre-m016 snapshots) applies
    a Python port of scripts/normalize_use_case_fields.py STAGE_SQL.
    Order matters: retired and pilot are checked BEFORE deployed, because
    the OMB Pilot label text contains the word "deployed".
    """
    if normalized:
        return normalized
    if raw is None or not raw.strip():
        return "unknown"
    t = raw.lower()
    if "retired" in t:
        return "retired"
    if "pilot" in t:
        return "pilot"
    if "deployed" in t or "production" in t or "operation and maintenance" in t:
        return "deployed"
    if (
        "pre-deployment" in t
        or "pre deployment" in t
        or "development or acquisition" in t
        or "acquisition and/or development" in t
        or t.strip() in {"ideation", "sandbox", "initiated", "being evaluated"}
    ):
        return "pre_deployment"
    return "unknown"


def _is_inhouse_dev(s: str | None) -> bool:
    """Match 'b) Developed in-house', 'Developed in house', hybrid
    'c) Developed with both contracting and in-house resources', and the
    'No contract/external resources used in development.' encoding.
    """
    if not s:
        return False
    t = s.lower().replace("-", " ")
    return "in house" in t or t.strip().startswith("no contract")


def _is_pure_inhouse_dev(s: str | None) -> bool:
    """A PURE in-house claim (no contracting involvement mentioned) — the
    variant that a commercial vendor_name contradicts. Hybrid 'both
    contracting and in-house' claims are not pure.
    """
    if not _is_inhouse_dev(s):
        return False
    t = (s or "").lower()
    return not ("both" in t or "contract" in t)


def _is_purchased_dev(s: str | None) -> bool:
    """Match 'a) Purchased from a vendor' variants and the bare 'Vendor'
    encoding."""
    if not s:
        return False
    t = s.strip().lower()
    return "purchased" in t or t == "vendor"


def _is_placeholder_vendor(s: str | None) -> bool:
    return (s or "").strip().lower() in PLACEHOLDER_VENDORS


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


def _has_real_pia_url(s: str | None) -> bool:
    """v1.2: only an actual URL counts as a PIA oversight signal. 84% of
    non-blank pia_url values in the 2025 inventory are placeholder text
    ("N/A", "PIA not publically available", ...)."""
    if not s:
        return False
    return s.strip().lower().startswith("http")


def _hi_filled_count(row: sqlite3.Row, present_hi: list[str]) -> int:
    """Count meaningfully-filled Section-5 fields. Case-insensitive
    placeholder filter (v1.2 — v1.1 compared case-sensitively so a literal
    'N/A' counted as filled)."""
    n = 0
    for f in present_hi:
        v = row[f]
        if v is not None and str(v).strip().lower() not in HI_PLACEHOLDERS:
            n += 1
    return n


# --- Effective-unit corpus ---------------------------------------------------

class _Unit:
    """One effective use case: a group of rows within an agency that share an
    identical (>= DEDUP_MIN_PROBLEM_LEN chars) problem_statement, vendor_name,
    and development_type — or a single row when the statement is too short to
    be a signature. A unit qualifies for a boolean signal if ANY member row
    qualifies; a unit is 'retired' only if ALL member rows are retired."""

    __slots__ = (
        "member_count", "custom", "inhouse", "purchased", "deployed",
        "retired", "internal_platform", "frontier", "agentic", "ato",
        "risky", "overseen", "has_product",
    )

    def __init__(self) -> None:
        self.member_count = 0
        self.custom = False
        self.inhouse = False
        self.purchased = False
        self.deployed = False
        self.retired = True  # ANDed: stays True only if every member is retired
        self.internal_platform = False
        self.frontier = False
        self.agentic = False
        self.ato = False
        self.risky = False
        self.overseen = False
        self.has_product = False


def _load_units(conn: sqlite3.Connection) -> dict[int, list[_Unit]]:
    """Build the effective-unit corpus for every agency in one pass."""
    uc_cols = {r[1] for r in conn.execute("PRAGMA table_info(use_cases)")}

    def col(name: str) -> str:
        return name if name in uc_cols else f"NULL AS {name}"

    present_hi = [f for f in HI_FIELDS if f in uc_cols]
    hi_select = ("," + ", ".join(present_hi)) if present_hi else ""

    rows = conn.execute(
        f"""
        SELECT id, agency_id, has_custom_code,
               {col("development_type")}, {col("vendor_name")},
               {col("problem_statement")}, {col("stage_normalized")},
               stage_of_development, has_ato, has_pii, is_high_impact,
               {col("pia_url")}{hi_select}
          FROM use_cases
        """
    ).fetchall()

    # Tag / link sets (one query each, not per agency).
    frontier_ids = {
        r[0] for r in conn.execute(
            "SELECT use_case_id FROM use_case_tags "
            "WHERE use_case_id IS NOT NULL AND is_frontier_model = 1"
        )
    }
    has_agentic_col = any(
        r[1] == "is_agentic_ai"
        for r in conn.execute("PRAGMA table_info(use_case_tags)")
    )
    agentic_sql = (
        "SELECT use_case_id FROM use_case_tags WHERE use_case_id IS NOT NULL "
        "AND (ai_sophistication = 'agentic' OR COALESCE(is_agentic_ai, 0) = 1)"
        if has_agentic_col else
        "SELECT use_case_id FROM use_case_tags WHERE use_case_id IS NOT NULL "
        "AND ai_sophistication = 'agentic'"
    )
    agentic_ids = {r[0] for r in conn.execute(agentic_sql)}

    has_origin_col = any(
        r[1] == "product_origin"
        for r in conn.execute("PRAGMA table_info(products)")
    )
    internal_platform_uc_ids: set[int] = set()
    if has_origin_col:
        internal_platform_uc_ids = {
            r[0] for r in conn.execute(
                """
                SELECT DISTINCT ucp.use_case_id
                  FROM use_case_products ucp
                  JOIN products p ON p.id = ucp.product_id
                 WHERE p.product_origin = 'agency_internal_platform'
                """
            )
        }
    product_linked_uc_ids = {
        r[0] for r in conn.execute("SELECT DISTINCT use_case_id FROM use_case_products")
    }

    units: dict[int, dict[tuple, _Unit]] = {}
    for r in rows:
        aid = r["agency_id"]
        ps = (r["problem_statement"] or "").strip()
        if len(ps) >= DEDUP_MIN_PROBLEM_LEN:
            key = (
                ps,
                (r["vendor_name"] or "").strip(),
                (r["development_type"] or "").strip(),
            )
        else:
            key = ("__row__", r["id"])

        agency_units = units.setdefault(aid, {})
        u = agency_units.get(key)
        if u is None:
            u = _Unit()
            agency_units[key] = u
        u.member_count += 1

        # --- build/dev signals ---
        custom = _truthy(r["has_custom_code"])
        u.custom = u.custom or custom
        if _is_inhouse_dev(r["development_type"]):
            if _is_pure_inhouse_dev(r["development_type"]):
                # v1.2 cross-check: a pure in-house claim with a commercial
                # vendor and no custom code is a mislabeled commercial buy.
                if _is_placeholder_vendor(r["vendor_name"]) or custom:
                    u.inhouse = True
            else:
                u.inhouse = True  # hybrid claims keep credit
        u.purchased = u.purchased or _is_purchased_dev(r["development_type"])

        # --- stage ---
        bucket = _stage_bucket(r["stage_normalized"], r["stage_of_development"])
        u.deployed = u.deployed or bucket == "deployed"
        u.retired = u.retired and bucket == "retired"

        # --- tags / links ---
        u.internal_platform = u.internal_platform or (r["id"] in internal_platform_uc_ids)
        u.frontier = u.frontier or (r["id"] in frontier_ids)
        u.agentic = u.agentic or (r["id"] in agentic_ids)
        u.has_product = u.has_product or (r["id"] in product_linked_uc_ids)
        u.ato = u.ato or _truthy(r["has_ato"])

        # --- governance ---
        risky = _has_pii(r["has_pii"]) or _is_high_impact(r["is_high_impact"])
        if risky:
            u.risky = True
            oversight = (
                _has_real_pia_url(r["pia_url"])
                or _truthy(r["has_ato"])
                or _hi_filled_count(r, present_hi) >= 2
            )
            u.overseen = u.overseen or oversight

    return {aid: list(agency_units.values()) for aid, agency_units in units.items()}


def _active(agency_units: list[_Unit]) -> list[_Unit]:
    """Units with at least one non-retired member row."""
    return [u for u in agency_units if not u.retired]


# --- Dimension calculators -------------------------------------------------

def compute_adoption_breadth(
    conn: sqlite3.Connection,
    units: dict[int, list[_Unit]] | None = None,
) -> tuple[dict[int, float], dict[int, dict]]:
    """Two sub-signals, averaged after rank-normalization to 0–100:
      1) Total entries (effective use-case units + consolidated_use_cases).
      2) Share of bureaus participating — distinct non-null bureau_component
         strings on use_cases. Templates are not used (template_id is null
         on use_cases in current data).

    Returns (scores, raw_inputs_per_agency).
    """
    if units is None:
        units = _load_units(conn)
    agencies = _list_agencies(conn)
    raw_counts: dict[int, int] = {}
    raw_bureaus: dict[int, int] = {}
    raw_templates: dict[int, int] = {}

    for a in agencies:
        aid = a["id"]
        c_uc = len(units.get(aid, []))
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


def compute_frontier_capability(
    conn: sqlite3.Connection,
    units: dict[int, list[_Unit]] | None = None,
) -> tuple[dict[int, float], dict[int, dict]]:
    """Weighted sum of three shares per agency (over effective units):
       0.4 * share(frontier-model tagged)
     + 0.3 * share(agentic)
     + 0.3 * share(custom-coded)
    Multiplied by 100 and capped at 100.
    """
    if units is None:
        units = _load_units(conn)
    scores: dict[int, float] = {}
    raw: dict[int, dict] = {}

    for a in _list_agencies(conn):
        aid = a["id"]
        us = units.get(aid, [])
        total = len(us)
        if total == 0:
            scores[aid] = 0.0
            raw[aid] = {"frontier": 0, "agentic": 0, "custom_code": 0,
                        "total_units": 0}
            continue

        frontier = sum(1 for u in us if u.frontier)
        agentic = sum(1 for u in us if u.agentic)
        custom = sum(1 for u in us if u.custom)

        composite = (
            0.4 * (frontier / total)
            + 0.3 * (agentic / total)
            + 0.3 * (custom / total)
        ) * 100.0
        scores[aid] = round(min(composite, 100.0), 2)
        raw[aid] = {
            "frontier": frontier,
            "agentic": agentic,
            "custom_code": custom,
            "total_units": total,
        }
    return scores, raw


def compute_procurement_hygiene(
    conn: sqlite3.Connection,
    units: dict[int, list[_Unit]] | None = None,
) -> tuple[dict[int, float], dict[int, dict]]:
    """Average of two shares, multiplied by 100:
       - share of effective units where has_ato is truthy
       - share of distinct products in this agency's use_cases that have at
         least one fedramp_product_links row

    Both sub-shares are 0–1.
    """
    if units is None:
        units = _load_units(conn)
    scores: dict[int, float] = {}
    raw: dict[int, dict] = {}

    # Pre-compute the set of FedRAMP-linked inventory product IDs.
    fedramp_linked = {
        r["inventory_product_id"]
        for r in conn.execute(
            "SELECT DISTINCT inventory_product_id FROM fedramp_product_links"
        ).fetchall()
    }

    for a in _list_agencies(conn):
        aid = a["id"]
        us = units.get(aid, [])
        total = len(us)

        if total == 0:
            scores[aid] = 0.0
            raw[aid] = {
                "ato_yes": 0,
                "ato_total": 0,
                "products_total": 0,
                "products_fedramp": 0,
            }
            continue

        ato_yes = sum(1 for u in us if u.ato)
        share_ato = ato_yes / total

        # Distinct products attached to this agency's use_cases (row-level:
        # a product link is a product link regardless of filing atomization).
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


def compute_internal_capacity(
    conn: sqlite3.Connection,
    units: dict[int, list[_Unit]] | None = None,
) -> tuple[dict[int, float], dict[int, dict]]:
    """Capacity-first dimension. Average of four sub-shares per agency × 100:
       - share of units with custom code
       - share of units with (cross-checked) in-house development
       - share of ACTIVE (non-retired) units at deployed stage
       - share of units linked to a product with
         product_origin='agency_internal_platform'

    Measures the agency's actual technical capability — building, shipping,
    running AI as opposed to buying commercial chat wrappers.
    """
    if units is None:
        units = _load_units(conn)
    scores: dict[int, float] = {}
    raw: dict[int, dict] = {}

    for a in _list_agencies(conn):
        aid = a["id"]
        us = units.get(aid, [])
        total = len(us)
        if total == 0:
            scores[aid] = 0.0
            raw[aid] = {
                "custom_code": 0, "inhouse_dev": 0, "deployed": 0,
                "internal_platform": 0, "total_units": 0, "active_units": 0,
            }
            continue

        active = _active(us)
        n_active = len(active)

        custom = sum(1 for u in us if u.custom)
        inhouse = sum(1 for u in us if u.inhouse)
        deployed = sum(1 for u in active if u.deployed)
        internal_platform = sum(1 for u in us if u.internal_platform)

        deployed_share = (deployed / n_active) if n_active else 0.0
        composite = (
            (custom / total)
            + (inhouse / total)
            + deployed_share
            + (internal_platform / total)
        ) / 4.0 * 100.0
        scores[aid] = round(min(composite, 100.0), 2)
        raw[aid] = {
            "custom_code": custom,
            "inhouse_dev": inhouse,
            "deployed": deployed,
            "internal_platform": internal_platform,
            "total_units": total,
            "active_units": n_active,
        }
    return scores, raw


def compute_risk_relevant_governance(
    conn: sqlite3.Connection,
    units: dict[int, list[_Unit]] | None = None,
) -> tuple[dict[int, float], dict[int, dict]]:
    """Of *risky* effective units (PII present OR high-impact designation),
    the share with at least one meaningful oversight signal:
       - a real PIA URL (http...), OR
       - has_ato truthy, OR
       - at least 2 of the 9 hi_* Section-5 fields meaningfully filled

    v1.2: the raw share is shrunk toward the pooled federal oversight rate
    (Empirical Bayes):  score = 100 * (x + K*p0) / (n + K),  K=5.
    A 1-for-1 agency no longer scores 100 — small samples defer to the
    federal base rate; large samples keep their own rate.

    Agencies with no risky units still score 0 (we don't reward *absence*
    of risk — that's not a capacity signal). The rubric weights this at
    only 15% precisely because risk exposure is unevenly distributed.
    """
    if units is None:
        units = _load_units(conn)
    scores: dict[int, float] = {}
    raw: dict[int, dict] = {}

    # Pooled federal oversight rate (the shrinkage prior).
    fed_risky = 0
    fed_overseen = 0
    for us in units.values():
        for u in us:
            if u.risky:
                fed_risky += 1
                if u.overseen:
                    fed_overseen += 1
    p0 = (fed_overseen / fed_risky) if fed_risky else 0.0
    k = GOVERNANCE_SHRINKAGE_K

    for a in _list_agencies(conn):
        aid = a["id"]
        us = units.get(aid, [])
        risky_total = sum(1 for u in us if u.risky)
        risky_with_oversight = sum(1 for u in us if u.risky and u.overseen)

        if risky_total == 0:
            scores[aid] = 0.0
            raw_score = 0.0
            shrunk = 0.0
        else:
            raw_score = round((risky_with_oversight / risky_total) * 100.0, 2)
            shrunk = round(
                ((risky_with_oversight + k * p0) / (risky_total + k)) * 100.0, 2
            )
            scores[aid] = shrunk
        raw[aid] = {
            "risky_total": risky_total,
            "risky_with_oversight": risky_with_oversight,
            "raw_score": raw_score,
            "shrunk_score": shrunk,
            "prior_rate": round(p0, 4),
            "shrinkage_k": k,
            "total_units": len(us),
        }
    return scores, raw


# --- Tier band lookup ------------------------------------------------------

def assign_tier(composite: float) -> tuple[str, str]:
    """Assign tier by composite score. Bands published in TIER_BANDS use
    integer lower bounds (A=70+, B=55+, C=35+, D=15+, F=<15); composite is
    a float, so any value at or above a band's lower bound (and below the
    next band's) maps to that band.
    """
    # TIER_BANDS is ordered A→F; walk it and return the first whose
    # lower bound the composite meets.
    for tier, lo, _hi, label in TIER_BANDS:
        if composite >= lo:
            return tier, label
    return "F", "Insufficient Capacity"


# --- Headline stats --------------------------------------------------------

def compute_headline_stats(
    conn: sqlite3.Connection,
    scored: list[dict],
    units: dict[int, list[_Unit]] | None = None,
) -> dict:
    """Capacity-first headline candidates for the homepage hero, computed
    over effective units (v1.2).

    Three-way build split: internal_build_pct + purchased_pct +
    unreported_pct ≈ 100. The "unreported" share is itself a finding —
    half the inventory doesn't say how it was built.

    The compliance-leaning `hi_no_risk_docs_pct` is still computed and
    surfaced (the methodology page uses it as a caveat) but it's NOT the
    feature stat — counting form-fill rates conflates compliance with
    capacity. v1.2 adds the high-impact-only variant, since Section 5 is
    only conditionally required.
    """
    if units is None:
        units = _load_units(conn)
    all_units = [u for us in units.values() for u in us]
    total_units = len(all_units) or 1
    active_units = [u for u in all_units if not u.retired]
    n_active = len(active_units) or 1

    # --- Three-way build split ---
    internal = sum(
        1 for u in all_units if u.custom or u.inhouse or u.internal_platform
    )
    purchased = sum(
        1 for u in all_units
        if u.purchased and not (u.custom or u.inhouse or u.internal_platform)
    )
    internal_build_pct = round(100.0 * internal / total_units, 1)
    purchased_pct = round(100.0 * purchased / total_units, 1)
    unreported_pct = round(100.0 - internal_build_pct - purchased_pct, 1)

    # --- Production rate (active units; retired excluded from denominator) ---
    deployed_active = sum(1 for u in active_units if u.deployed)
    production_rate_pct = round(100.0 * deployed_active / n_active, 1)
    deployed_all = sum(1 for u in all_units if u.deployed)
    production_rate_all_pct = round(100.0 * deployed_all / total_units, 1)

    # --- FedRAMP coverage ---
    fedramp_linked_pids = {
        r["inventory_product_id"]
        for r in conn.execute(
            "SELECT DISTINCT inventory_product_id FROM fedramp_product_links"
        ).fetchall()
    }
    fedramp_uc_ids = {
        r[0]
        for r in conn.execute(
            """
            SELECT DISTINCT ucp.use_case_id
              FROM use_case_products ucp
             WHERE ucp.product_id IN (
               SELECT DISTINCT inventory_product_id FROM fedramp_product_links
             )
            """
        ).fetchall()
    } if fedramp_linked_pids else set()
    # Re-walk rows so unit membership maps to fedramp coverage. (Cheap: the
    # unit objects don't retain member ids, so recount at the unit level via
    # a dedicated pass.)
    uc_cols = {r[1] for r in conn.execute("PRAGMA table_info(use_cases)")}
    def col(name: str) -> str:
        return name if name in uc_cols else f"NULL AS {name}"
    fr_rows = conn.execute(
        f"""
        SELECT id, agency_id, {col("problem_statement")},
               {col("vendor_name")}, {col("development_type")}
          FROM use_cases
        """
    ).fetchall()
    unit_has_product: dict[tuple, bool] = {}
    unit_has_fedramp: dict[tuple, bool] = {}
    product_linked_uc_ids = {
        r[0] for r in conn.execute("SELECT DISTINCT use_case_id FROM use_case_products")
    }
    for r in fr_rows:
        ps = (r["problem_statement"] or "").strip()
        if len(ps) >= DEDUP_MIN_PROBLEM_LEN:
            key = (r["agency_id"], ps, (r["vendor_name"] or "").strip(),
                   (r["development_type"] or "").strip())
        else:
            key = (r["agency_id"], "__row__", r["id"])
        unit_has_product[key] = unit_has_product.get(key, False) or (
            r["id"] in product_linked_uc_ids
        )
        unit_has_fedramp[key] = unit_has_fedramp.get(key, False) or (
            r["id"] in fedramp_uc_ids
        )
    units_with_product = sum(1 for v in unit_has_product.values() if v) or 1
    units_fedramp = sum(1 for v in unit_has_fedramp.values() if v)
    fedramp_linked_pct = round(100.0 * units_fedramp / units_with_product, 1)
    fedramp_floor_pct = round(100.0 * units_fedramp / total_units, 1)

    # --- frontier_ready_agency_count — how many scored A ---
    frontier_ready_agency_count = sum(1 for r in scored if r["tier"] == "A")

    # --- Compliance baseline (caveat, not headline) ---
    # Preserved so the methodology page can explicitly contrast capacity
    # measures with the form-fill metric the rubric is rejecting. Row-based
    # (it describes filings, not deduped capability).
    real_total_uc = conn.execute("SELECT COUNT(*) FROM use_cases").fetchone()[0]
    total_uc = real_total_uc or 1
    with_risk = conn.execute(
        """
        SELECT COUNT(DISTINCT t.use_case_id) FROM use_case_tags t
        JOIN use_cases uc ON uc.id = t.use_case_id
        WHERE t.has_meaningful_risk_docs = 1
        """
    ).fetchone()[0] or 0
    hi_no_risk_docs_pct = round(100.0 * (1.0 - (with_risk / total_uc)), 1)

    hi_rows = conn.execute(
        "SELECT id, is_high_impact FROM use_cases"
    ).fetchall()
    hi_ids = [r["id"] for r in hi_rows if _is_high_impact(r["is_high_impact"])]
    if hi_ids:
        placeholders = ",".join("?" * len(hi_ids))
        hi_with_risk = conn.execute(
            f"""
            SELECT COUNT(DISTINCT t.use_case_id) FROM use_case_tags t
            WHERE t.has_meaningful_risk_docs = 1
              AND t.use_case_id IN ({placeholders})
            """,
            hi_ids,
        ).fetchone()[0] or 0
        hi_no_risk_docs_high_impact_pct = round(
            100.0 * (1.0 - hi_with_risk / len(hi_ids)), 1
        )
    else:
        hi_no_risk_docs_high_impact_pct = 0.0

    return {
        "internal_build_pct": internal_build_pct,
        "purchased_pct": purchased_pct,
        "unreported_pct": unreported_pct,
        "production_rate_pct": production_rate_pct,
        "production_rate_all_pct": production_rate_all_pct,
        "fedramp_linked_pct": fedramp_linked_pct,
        "fedramp_floor_pct": fedramp_floor_pct,
        # Back-compat alias (v1.1 name) — same value as fedramp_linked_pct.
        "fedramp_coverage_pct": fedramp_linked_pct,
        "frontier_ready_agency_count": frontier_ready_agency_count,
        "total_agencies_scored": len(scored),
        "total_units": len(all_units),
        "total_use_cases": real_total_uc,
        # Compliance baseline — not for headline use:
        "hi_no_risk_docs_pct": hi_no_risk_docs_pct,
        "hi_no_risk_docs_high_impact_pct": hi_no_risk_docs_high_impact_pct,
    }


# --- Persistence -------------------------------------------------------------

_HEADLINE_DDL = """
CREATE TABLE IF NOT EXISTS readiness_headline (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    rubric_version TEXT NOT NULL,
    internal_build_pct REAL NOT NULL,
    purchased_pct REAL NOT NULL,
    unreported_pct REAL NOT NULL,
    production_rate_pct REAL NOT NULL,
    production_rate_all_pct REAL NOT NULL,
    fedramp_linked_pct REAL NOT NULL,
    fedramp_floor_pct REAL NOT NULL,
    frontier_ready_agency_count INTEGER NOT NULL,
    total_agencies_scored INTEGER NOT NULL,
    total_units INTEGER NOT NULL,
    total_use_cases INTEGER NOT NULL,
    hi_no_risk_docs_pct REAL NOT NULL,
    hi_no_risk_docs_high_impact_pct REAL NOT NULL,
    fedramp_link_row_count INTEGER NOT NULL DEFAULT 0,
    computed_at TEXT NOT NULL
)
"""


def _persist_headline(conn: sqlite3.Connection, headline: dict, now: str) -> None:
    """Write the 1-row readiness_headline table (DDL also in migration m018;
    duplicated here so the script is self-sufficient on older snapshots)."""
    fedramp_link_rows = conn.execute(
        "SELECT COUNT(*) FROM fedramp_product_links"
    ).fetchone()[0]
    conn.execute(_HEADLINE_DDL)
    conn.execute("DELETE FROM readiness_headline")
    conn.execute(
        """
        INSERT INTO readiness_headline (
            id, rubric_version, internal_build_pct, purchased_pct,
            unreported_pct, production_rate_pct, production_rate_all_pct,
            fedramp_linked_pct, fedramp_floor_pct,
            frontier_ready_agency_count, total_agencies_scored,
            total_units, total_use_cases,
            hi_no_risk_docs_pct, hi_no_risk_docs_high_impact_pct,
            fedramp_link_row_count, computed_at
        ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            RUBRIC_VERSION,
            headline["internal_build_pct"], headline["purchased_pct"],
            headline["unreported_pct"], headline["production_rate_pct"],
            headline["production_rate_all_pct"],
            headline["fedramp_linked_pct"], headline["fedramp_floor_pct"],
            headline["frontier_ready_agency_count"],
            headline["total_agencies_scored"],
            headline["total_units"], headline["total_use_cases"],
            headline["hi_no_risk_docs_pct"],
            headline["hi_no_risk_docs_high_impact_pct"],
            fedramp_link_rows, now,
        ),
    )


# --- Main entrypoint -------------------------------------------------------

def compute_agency_readiness(conn: sqlite3.Connection | None = None) -> dict:
    """Compute and persist agency_readiness + readiness_headline.
    Returns the rows and headline stats."""
    own = conn is None
    if conn is None:
        conn = get_connection()
    try:
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "WEIGHTS must sum to 1.0"

        units = _load_units(conn)

        internal, raw_ic = compute_internal_capacity(conn, units)
        frontier, raw_fr = compute_frontier_capability(conn, units)
        procurement, raw_pr = compute_procurement_hygiene(conn, units)
        governance, raw_gv = compute_risk_relevant_governance(conn, units)
        adoption, raw_ad = compute_adoption_breadth(conn, units)

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
                "rubric_version": RUBRIC_VERSION,
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

        # Competition rank ("tied for Nth") by composite desc — tied scores
        # share a rank; the next distinct score takes its ordinal position
        # (1,2,2,4). Intentional for "Rank N of M" display.
        rows.sort(key=lambda r: (-r["composite_score"], r["abbreviation"]))
        prev_score = None
        prev_rank = 0
        for i, r in enumerate(rows):
            if r["composite_score"] != prev_score:
                prev_rank = i + 1
                prev_score = r["composite_score"]
            r["rank"] = prev_rank

        headline = compute_headline_stats(conn, rows, units)

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
            _persist_headline(conn, headline, now)

        return {"rows": rows, "headline": headline, "computed_at": now}
    finally:
        if own:
            conn.close()


def main() -> int:
    result = compute_agency_readiness()
    rows = result["rows"]
    headline = result["headline"]

    print(f"\n=== Agency AI Readiness v{RUBRIC_VERSION} — top 10 by composite ===")
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

    print("\n=== Capacity-first headline stats (persisted to readiness_headline) ===")
    print(f"  internal_build_pct          = {headline['internal_build_pct']}%")
    print(f"  purchased_pct               = {headline['purchased_pct']}%")
    print(f"  unreported_pct              = {headline['unreported_pct']}%")
    print(f"  production_rate_pct         = {headline['production_rate_pct']}% (active units)")
    print(f"  production_rate_all_pct     = {headline['production_rate_all_pct']}% (incl. retired)")
    print(f"  fedramp_linked_pct          = {headline['fedramp_linked_pct']}% (of product-linked units)")
    print(f"  fedramp_floor_pct           = {headline['fedramp_floor_pct']}% (of all units)")
    print(f"  frontier_ready_agency_count = {headline['frontier_ready_agency_count']} of {headline['total_agencies_scored']}")
    print(f"\n=== Compliance baseline (caveat, not headline) ===")
    print(f"  hi_no_risk_docs_pct             = {headline['hi_no_risk_docs_pct']}%")
    print(f"  hi_no_risk_docs_high_impact_pct = {headline['hi_no_risk_docs_high_impact_pct']}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
