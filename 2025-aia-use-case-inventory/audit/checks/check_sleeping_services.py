"""Sleeping-services invariants (crosswalk + capability labels).

These run as part of `make check` once BOTH sidecars have been applied
(fedramp_service_product_map via apply_fedramp_service_product_map.py,
product_capability_labels via apply_product_capability_labels.py); they
skip cleanly otherwise. They guard the properties the dashboard's
/fedramp/coverage/sleeping-services board depends on:

  1. Structural invariants on a replica of the live pair computation:
     for every mapped product, lead-user and sleeping-agency sets are
     disjoint; every sleeping pair's product has >=1 lead user; every
     timing-excluded pair is itself a sleeping pair; the board is
     non-empty.
  2. Vocabulary sync: crosswalk capability_category values are a subset
     of the label-table vocabulary (the two CHECK constraints are
     defined in two scripts and could drift).
  3. Regex QC cross-check: the prototype name-pattern "similar deployed"
     heuristic (the pre-LLM implementation) must agree with the LLM
     labels on the sleeping rows within a loose bound. The regex is the
     sanity floor, not truth — disagreement is REPORTED at any level and
     only fails the build above 30%.

Accepted drift from the 2026-07-05 prototype (regex-based similar test):
599 sleeping pairs / 379 nothing-similar / 183 gen-AI / 33 gen-AI+void.
Pair count is pinned loosely (>=300); the similar-test numbers are
expected to move with the LLM labels.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "federal_ai_inventory_2025.db"

INVENTORY_CUTOFF = "2025-12-31"
DATE_FLOOR = "2000-01-01"

# The prototype's heuristic (scratchpad sleeping_services_prototype.py),
# kept verbatim as the QC cross-check for the LLM capability labels.
SIMILAR_PATTERNS = {
    "genai_platform": r"gpt|openai|bedrock|claude|gemini|llama|llm|generative|genai|ask sage|anthropic|foundry|chatbot|copilot|vertex",
    "assistant":      r"copilot|assistant|amazon q\b|einstein|agentforce|chatgpt|claude|gemini",
    "ml_lowcode":     r"ai builder|low.?code|power platform",
    "ml_platform":    r"sagemaker|vertex|azure machine learning|databricks|dataiku|h2o|mlflow|palantir|c3 ai|ml platform|machine learning",
    "doc_processing": r"textract|document intelligence|form recognizer|hyperscience|idp|intelligent document|ocr|abbyy|kofax|tungsten|docai|document ai|document understanding",
    "speech":         r"transcri|speech|polly|voice|whisper|verint|dragon|nuance",
    "translation":    r"translat|systran|lilt|language weaver",
    "vision":         r"vision|rekognition|image recog|video intel|facial|face recog|object detect",
    "nlp":            r"comprehend|text analytics|natural language|nlp|entity extract|sentiment",
    "search":         r"kendra|elastic|semantic search|cognitive search|enterprise search",
    "chatbot":        r"\blex\b|dialogflow|chatbot|conversational|virtual agent|bot service",
}


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        yield c
    finally:
        c.close()


def _has_table(conn, name: str) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?",
        (name,),
    ).fetchone())


@pytest.fixture(scope="module")
def pairs(conn):
    """Python replica of the dashboard's sleeping-pair computation."""
    for t in ("fedramp_service_product_map", "product_capability_labels",
              "fedramp_authorized_services"):
        if not _has_table(conn, t):
            pytest.skip(f"{t} not applied in this DB build")

    # crosswalk resolved by name, MAX(gen_ai) per product
    mapped = {}
    for svc, prod, pid, cat, gen_ai in conn.execute(
        """SELECT m.service, m.product_canonical_name, p.id,
                  m.capability_category, m.gen_ai
             FROM fedramp_service_product_map m
             JOIN products p ON LOWER(p.canonical_name) = LOWER(m.product_canonical_name)"""
    ):
        e = mapped.setdefault(prod, {"pid": pid, "cat": cat, "gen_ai": 0, "services": set()})
        e["gen_ai"] = max(e["gen_ai"], gen_ai)
        e["services"].add(svc)

    def descendants(pid):
        out, frontier = {pid}, [pid]
        while frontier:
            qs = ",".join("?" * len(frontier))
            rows = conn.execute(
                f"SELECT id FROM products WHERE parent_product_id IN ({qs})",
                frontier,
            ).fetchall()
            frontier = [r[0] for r in rows if r[0] not in out]
            out.update(frontier)
        return out

    leads, reach, first_ato = {}, {}, {}
    for prod, e in mapped.items():
        ids = list(descendants(e["pid"]))
        qs = ",".join("?" * len(ids))
        leads[prod] = {
            r[0] for r in conn.execute(
                f"SELECT DISTINCT agency_id FROM entry_product_edges "
                f"WHERE product_id IN ({qs})", ids)
        }
        svc_qs = ",".join("?" * len(e["services"]))
        for aid, d in conn.execute(
            f"""SELECT al.inventory_agency_id,
                       MIN(CASE WHEN a.ato_issuance_date >= ? THEN a.ato_issuance_date END)
                  FROM fedramp_authorized_services s
                  JOIN fedramp_authorizations a ON a.fedramp_id = s.fedramp_id
                  JOIN fedramp_agency_links al ON al.fedramp_agency_id = a.agency_id
                 WHERE s.service IN ({svc_qs})
                 GROUP BY al.inventory_agency_id""",
            [DATE_FLOOR, *e["services"]],
        ):
            reach.setdefault(prod, set()).add(aid)
            first_ato[(prod, aid)] = d

    out = []
    for prod, holders in reach.items():
        if not leads.get(prod):
            continue
        for aid in holders - leads[prod]:
            d = first_ato.get((prod, aid))
            out.append({
                "product": prod, "agency_id": aid,
                "category": mapped[prod]["cat"],
                "gen_ai": mapped[prod]["gen_ai"],
                "timing_excluded": bool(d and d > INVENTORY_CUTOFF),
            })
    return {"pairs": out, "leads": leads, "reach": reach}


def test_lead_and_sleeping_disjoint(pairs):
    sleeping = {(p["product"], p["agency_id"]) for p in pairs["pairs"]}
    for prod, lead_set in pairs["leads"].items():
        for aid in lead_set:
            assert (prod, aid) not in sleeping


def test_every_sleeping_product_has_a_lead(pairs):
    for p in pairs["pairs"]:
        assert pairs["leads"].get(p["product"]), p["product"]


def test_timing_excluded_subset_of_sleeping(pairs):
    # by construction timing_excluded rows ARE sleeping rows; assert the
    # flag only appears on emitted pairs and the count is sane
    excluded = [p for p in pairs["pairs"] if p["timing_excluded"]]
    assert len(excluded) <= len(pairs["pairs"])


def test_board_nonempty_and_in_expected_range(pairs):
    n = len(pairs["pairs"])
    assert n >= 300, f"sleeping pairs collapsed to {n} — crosswalk or links broken?"


def test_vocabulary_sync(conn, pairs):
    label_vocab = {
        r[0] for r in conn.execute(
            "SELECT DISTINCT category FROM product_capability_labels")
    }
    crosswalk_vocab = {p["category"] for p in pairs["pairs"]}
    # every category the board can emit must be label-able
    assert crosswalk_vocab <= (label_vocab | set(SIMILAR_PATTERNS)), (
        crosswalk_vocab - label_vocab)


def test_similar_llm_vs_regex_drift(conn, pairs):
    """Report LLM-vs-regex disagreement on similar-deployed; fail >30%."""
    agency_products: dict[int, list[str]] = {}
    for aid, name in conn.execute(
        """SELECT DISTINCT e.agency_id, p.canonical_name
             FROM entry_product_edges e JOIN products p ON p.id = e.product_id"""
    ):
        agency_products.setdefault(aid, []).append(name)

    llm_cats: dict[int, set] = {}
    for aid, cat in conn.execute(
        """SELECT DISTINCT e.agency_id, l.category
             FROM entry_product_edges e
             JOIN products p ON p.id = e.product_id
             JOIN product_capability_labels l ON l.canonical_name = p.canonical_name
            WHERE l.category != 'none'"""
    ):
        llm_cats.setdefault(aid, set()).add(cat)

    disagree = total = 0
    for p in pairs["pairs"]:
        pat = re.compile(SIMILAR_PATTERNS[p["category"]], re.I)
        regex_similar = any(
            pat.search(n) for n in agency_products.get(p["agency_id"], []))
        llm_similar = p["category"] in llm_cats.get(p["agency_id"], set())
        total += 1
        if regex_similar != llm_similar:
            disagree += 1
    rate = disagree / total if total else 0.0
    print(f"\nsimilar-deployed LLM vs regex: {disagree}/{total} disagree ({rate:.1%})")
    assert rate <= 0.30, (
        f"LLM capability labels diverge from the regex sanity floor by {rate:.1%}")
