"""Pure-function match policy for OMB consolidated rows ↔ DB use_cases.

The policy: normalize agency abbreviations (STATE→State, TREAS→Treasury),
normalize use-case names (lowercase, whitespace-collapse, curly-quote
straightening, ampersand-to-and), score with difflib SequenceMatcher,
and classify into a fixed status enum.

Drift detection canonicalizes leading letter prefixes (`a) Pre-deployment`
→ `Pre-deployment`) and curly apostrophes before comparing — the same
normalizations OMB applies during their consolidation.

This module is pure-function: no DB, no I/O, no global state. Phase 3
(loader) and Phase 5 (dashboard) both call into it so DB-rendered drift
and OMB-file drift never disagree on canonicalization.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable

# Threshold tuning notes (calibrated against Python stdlib difflib.SequenceMatcher
# — note: agent audit numbers used rapidfuzz which scores higher; difflib is
# stricter on length-imbalanced strings):
#   ≥ 0.85 → matched_fuzzy (DOI/HHS minor edits; near-identical names)
#   0.40–0.85 → suggested_rename (catches NSF-style acronym expansions like
#               "TIP MS Copilot Pilot" ↔ "Technology, Innovation and
#               Partnerships (TIP) Microsoft (MS) Copilot Pilot" ≈ 0.43)
#   < 0.40 → unmatched (omb_only or db_only)
# Loaders may apply tighter per-agency thresholds when noisy renames are a concern.
FUZZY_MATCH_THRESHOLD = 0.85
SUGGESTED_RENAME_THRESHOLD = 0.40

# Narrative-similarity threshold for the year-over-year matcher
# (`match_year_over_year.py`, Phase 3). Token-set Jaccard over the
# concatenated narrative paragraphs is a *coarse* deterministic signal —
# it catches use cases whose names were rewritten between 2024 and 2025
# but whose described problem/benefits/outputs stayed substantially the
# same. 0.50 is a deliberately conservative starting point; it wants
# calibration against a labelled sample. Phase 4's per-row LLM review does
# the real semantic adjudication of the residual.
NARRATIVE_MATCH_THRESHOLD = 0.50


_AGENCY_ABBR_MAP = {"STATE": "State", "TREAS": "Treasury"}


def normalize_agency(abbr: str | None) -> str | None:
    if abbr is None:
        return None
    return _AGENCY_ABBR_MAP.get(abbr, abbr)


_WHITESPACE_RE = re.compile(r"\s+")

# Year-over-year provenance tags 2025 stamps onto names that were carried
# over from the 2024 inventory — e.g. "Pyforecast [2024 INV#DOI-69]" or
# "... [2024 Inv# WO0000000111250]". These are matching noise (they only
# exist on one side) and dilute every name score, so strip them before
# comparison. Tolerant of casing and the optional space after "INV#".
_INV_TAG_RE = re.compile(r"\s*\[[^\]]*\binv#[^\]]*\]", flags=re.IGNORECASE)


def normalize_name(s: str | None) -> str:
    if s is None:
        return ""
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = _INV_TAG_RE.sub("", s)
    s = s.replace(" & ", " and ")
    s = s.lower().strip()
    s = _WHITESPACE_RE.sub(" ", s)
    return s


def name_match_score(a: str | None, b: str | None) -> float:
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


# A substantive token of at least this length counts as "distinctive" on
# its own — enough to let a one-word name like "PyForecast" containment-match
# even though it contributes only a single token.
_DISTINCTIVE_TOKEN_LEN = 6


def name_containment_score(a: str | None, b: str | None) -> float:
    """Token-containment signal for names where one is a subset of the other.

    Companion to `name_match_score` (which difflib's character-ratio
    penalizes for *length asymmetry*). 2025 systematically lengthened
    titles — appending qualifiers, expanding acronyms — so a 2024 name is
    often a clean token-subset of its 2025 counterpart ("PyForecast" →
    "Seasonal Water Supply Forecasting: Pyforecast"). Returns
    ``|A∩B| / min(|A|,|B|)`` over stopword-filtered name token sets — i.e.
    "what fraction of the shorter name's substantive tokens appear in the
    longer one".

    **Guard:** to fire, the *shorter* name must contribute either
      - at least 2 substantive (stopword-filtered) tokens, OR
      - at least 1 substantive token of length >= `_DISTINCTIVE_TOKEN_LEN`.
    This lets distinctive single-word names ("PyForecast") match while
    refusing generic stubs ("AI Tool" → both tokens are stopwords; "Data
    Hub" → two short generic tokens still passes the count guard but the
    intersection requirement keeps it honest). Returns 0.0 when the guard
    is not met or either side has no substantive tokens.

    Pure — no DB, no I/O. `name_match_score` is intentionally left
    unchanged; this is a separate signal the matcher combines via `max`.
    """
    ta = {
        t for t in _strip_punct(normalize_name(a)).split(" ")
        if t and t not in _STEM_STOPWORDS
    }
    tb = {
        t for t in _strip_punct(normalize_name(b)).split(" ")
        if t and t not in _STEM_STOPWORDS
    }
    if not ta or not tb:
        return 0.0
    smaller = ta if len(ta) <= len(tb) else tb
    if not (
        len(smaller) >= 2
        or any(len(t) >= _DISTINCTIVE_TOKEN_LEN for t in smaller)
    ):
        return 0.0
    intersection = len(ta & tb)
    return intersection / len(smaller)


# Floors that the containment fallback in `narrative_match_score` must
# clear before it is allowed to promote a pair. The earlier guard
# ("smaller side has >= 5 substantive tokens") was both on the wrong
# quantity *and* set far too low: it gates the size of the *shorter*
# narrative, not the size of the *shared* content, and 5 is well under
# what any genuine rename carries. A tiny 2-6-word 2025 narrative whose
# few tokens happen to sit inside a long unrelated 2024 paragraph cleared
# it, and containment then scored a spurious 0.50-0.62 — 5 DOJ
# false-positive `renamed` links (ServiceNow→Entity Extraction, FBOP
# Inmate Projections→Audio Clarity Tool, OBR Indexing→Entity Resolution,
# ArcGIS→OCR Tool, Veritone→Symphony).
#
# Replacement: an **absolute-intersection floor**. The honest signal is
# the absolute number of substantive (stopword-filtered) tokens the two
# narratives actually *share*. Measured on the regression sample:
#   - the 5 DOJ false positives have |A∩B| ∈ {3, 3, 3, 5, 8};
#   - the genuine low-scoring renames have |A∩B| = 8 (VA HTM-LLM →
#     HTM112 Tutor) and 12 (VA AIDOC → AIDOC BriefCase); the strong
#     genuine recoveries (Merbok 13, Finding the State 56, REACH VET 105)
#     sit far higher.
# A 2-6-word narrative cannot reach 6 substantive shared tokens, so
# K = 6 sits squarely in the 5↔8 gap and drops the four thin FPs.
#
# One FP — OBR Indexing → Entity Resolution — is pathological: its |A∩B|
# is exactly 8, *tying* the genuine VA HTM-LLM recovery, so no scalar
# intersection floor can separate them. The discriminator there is the
# *containment denominator*: OBR's smaller side is 13 substantive tokens
# (a one-line 2025 stub padded just past the intersection floor) while
# every genuine narrative-matched recovery has a smaller side >= 15
# (Merbok 15, HTM-LLM 15, AIDOC 21, Finding the State 58, REACH VET 139).
# So containment additionally requires the smaller token set to carry at
# least _CONTAINMENT_MIN_SMALLER tokens — a corrected, calibrated version
# of the original (broken-at-5) smaller-side guard. Sub-floor pairs fall
# back to plain Jaccard, which the long side dilutes well below threshold.
_CONTAINMENT_MIN_INTERSECTION = 6
_CONTAINMENT_MIN_SMALLER = 14


def narrative_match_score(a: str | None, b: str | None) -> float:
    """Containment-aware token-set similarity over two narrative paragraphs.

    Used by the year-over-year matcher (`match_year_over_year.py`) as the
    third deterministic stage: when two use cases' names don't match but
    their narrative text (problem / benefits / outputs) overlaps heavily,
    they're likely the same use case renamed.

    Returns ``max(jaccard, containment)`` where ``jaccard = |A∩B| / |A∪B|``
    and ``containment = |A∩B| / min(|A|,|B|)`` over the same
    stopword-filtered token sets. Plain Jaccard penalizes *length
    asymmetry*: 2025 systematically lengthened narratives (three fields vs
    2024's two), so when the 2024 text is a clean subset of the longer 2025
    text, Jaccard dilutes well below threshold even at verbatim identity.
    Containment measures "how much of the smaller side is covered" and is
    immune to that.

    **Guard:** containment only counts when *both* the intersection itself
    has at least `_CONTAINMENT_MIN_INTERSECTION` substantive tokens (the
    two narratives genuinely share that much distinctive content) *and*
    the smaller token set has at least `_CONTAINMENT_MIN_SMALLER` tokens
    (the shorter narrative is not a thin one-line stub padded just past
    the intersection floor). Gating only the shorter narrative's size (the
    prior guard) — and at just 5 tokens — was the wrong quantity at the
    wrong threshold: a tiny 2-6-word 2025 narrative whose handful of
    tokens sit inside a long unrelated 2024 paragraph still passed it and
    scored a spurious 0.5+. Sub-floor pairs fall back to plain Jaccard,
    which is heavily diluted by the long side and stays below threshold.

    Jaccard (order-independent set overlap) also suits narrative paragraphs
    better than difflib's character-ratio: agencies routinely reorder and
    lightly reword clauses between years, which tanks a character-level
    ratio but barely moves a token-set score. Words are lowercased,
    stripped of punctuation, whitespace-split, and filtered through
    `_STEM_STOPWORDS` (the same small stopword set used by the
    consolidation-stem extractor). Returns 0.0 when either side is empty
    or has no significant tokens.
    """
    ta = {t for t in _strip_punct(a or "").split(" ") if t and t not in _STEM_STOPWORDS}
    tb = {t for t in _strip_punct(b or "").split(" ") if t and t not in _STEM_STOPWORDS}
    if not ta or not tb:
        return 0.0
    intersection = len(ta & tb)
    union = len(ta | tb)
    jaccard = intersection / union if union else 0.0
    smaller = min(len(ta), len(tb))
    if (
        intersection < _CONTAINMENT_MIN_INTERSECTION
        or smaller < _CONTAINMENT_MIN_SMALLER
    ):
        return jaccard
    containment = intersection / smaller if smaller else 0.0
    return max(jaccard, containment)


@dataclass(frozen=True)
class MatchResult:
    status: str
    score: float | None
    method: str


def classify_match(
    score: float | None, *, db_present: bool, omb_present: bool
) -> MatchResult:
    if not db_present and omb_present:
        return MatchResult(status="omb_only", score=None, method="none")
    if db_present and not omb_present:
        return MatchResult(status="db_only", score=None, method="none")
    if score is None:
        return MatchResult(status="db_only", score=None, method="none")
    if score == 1.0:
        return MatchResult(status="matched_exact", score=1.0, method="exact_name")
    if score >= FUZZY_MATCH_THRESHOLD:
        return MatchResult(status="matched_fuzzy", score=score, method="fuzzy_name")
    if score >= SUGGESTED_RENAME_THRESHOLD:
        return MatchResult(status="suggested_rename", score=score, method="fuzzy_name")
    if omb_present and not db_present:
        return MatchResult(status="omb_only", score=None, method="none")
    return MatchResult(status="db_only", score=None, method="none")


DRIFT_FIELDS_DEFAULT = (
    "stage_of_development",
    "is_high_impact",
    "is_withheld",
    "topic_area",
    "ai_classification",
    "contracting_usage",
    "vendor_name",
    "have_ato",
    "has_pii",
    "has_custom_code",
    "bureau_component",
)


_LETTER_PREFIX_RE = re.compile(r"^\s*[a-z]\)\s*", flags=re.IGNORECASE)
_PUNCT_DRIFT_RE = re.compile(r"[,;.]+")  # NB: colons handled separately as long-form divider
# Long-form divider: OMB canonical text often uses "ShortForm – Long form"
# (em dash) or "ShortForm: Long description". Our DB sometimes stores the
# long form WITHOUT a divider (just `\n` or extra whitespace). Splitting at
# either divider AND taking the first phrase normalizes the OMB long-form
# to match the DB short-form.
_LONG_FORM_DIVIDER_RE = re.compile(r"\s*[–—:]\s+|\s*\n+\s*")
# Parenthetical clarifications like "(NLP)", "(Azure)" — agencies add these
# but OMB's canonical short forms don't. Strip during drift comparison only.
_PAREN_RE = re.compile(r"\s*\([^)]*\)")


def _canonicalize_field(s: str | None) -> str | None:
    """Canonicalize a field value for drift comparison.

    Normalizes the same axes OMB applies during consolidation, plus several
    DB-specific quirks discovered during the 2025 load:
      - curly → straight quotes; strip apostrophes entirely (DB strips them
        in some passes; OMB keeps them — yields 'agencys' ≡ 'agency's')
      - em/en dash → space (DB uses ASCII; OMB uses U+2013 em dash)
      - hyphen → space ('high-impact' ≡ 'high impact')
      - strip leading "a) " / "b) " enum-letter prefix
      - take prefix before " – ", " — ", ": ", or newline (OMB long-form
        canonical text starts with the short form followed by a divider)
      - lowercase + collapse whitespace
      - strip ,;. punctuation (catches "high-impact, but" ≡ "high-impact but")
    """
    if s is None:
        return None
    # cp1252-byte mojibake fix: many DB rows were ingested from latin-1 /
    # cp1252 source files and the punctuation bytes got stored as their
    # raw single-byte values rather than UTF-8 code points. Map the common
    # ones back to their intended Unicode equivalents BEFORE other
    # normalization.
    s = (
        s.replace("\x91", "'").replace("\x92", "'")  # smart single quotes
         .replace("\x93", '"').replace("\x94", '"')  # smart double quotes
         .replace("\x96", "–").replace("\x97", "—")  # en/em dash
    )
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("'", "")
    s = s.replace(" & ", " and ")
    s = _PAREN_RE.sub("", s)
    s = _LETTER_PREFIX_RE.sub("", s).strip().lower()
    # Split BEFORE replacing em dash with space — the dividers must still
    # be present to fire. Take prefix before the first long-form divider
    # (en/em dash with spaces, ": " with following space, or newline).
    # This collapses OMB's "deployed – the use case is being actively..."
    # down to "deployed" so it matches DB's bare "deployed".
    parts = _LONG_FORM_DIVIDER_RE.split(s, maxsplit=1)
    s = parts[0] if parts else s
    # Now the residual em/en dashes (if any in middle of short form) are
    # treated as spaces.
    s = s.replace("–", " ").replace("—", " ")
    s = _PUNCT_DRIFT_RE.sub("", s)
    s = s.replace("-", " ")
    s = _WHITESPACE_RE.sub(" ", s).strip()
    return s


def detect_drift(
    db_row: dict, omb_row: dict, *, fields: Iterable[str] = DRIFT_FIELDS_DEFAULT
) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for f in fields:
        db_v, omb_v = db_row.get(f), omb_row.get(f)
        if _canonicalize_field(db_v) != _canonicalize_field(omb_v):
            if db_v or omb_v:
                out[f] = {"db": db_v, "omb": omb_v}
    return out


# ──────────────────────────────────────────────────────────────────────────
# Consolidation-upstream detection (Phase-5 forensic upgrade).
#
# Goal: when OMB intentionally rolls up agency-specific rows into a generic
# category aggregator at the same agency, surface that as a separate
# `consolidated_upstream` status rather than the catch-all `db_only`. This
# is purely a re-classification of already-unmatched DB rows — no rows are
# added or removed.
# ──────────────────────────────────────────────────────────────────────────

_STEM_STOPWORDS = frozenset(
    {
        "ai", "the", "a", "an", "and", "or", "of", "for", "to", "in", "on",
        "with", "by", "at", "as", "is", "use", "using", "case", "tool",
        "generative", "gen", "ms", "department", "agency",
    }
)

_AGGREGATOR_PREFIX_RE = re.compile(
    r"^\s*(generative\s+ai|ai)\s*[\-—–:]\s*"
    r"(idea|text|code|content|chat|assistant|search|summary|"
    r"summarization|automation|information|image|design|capability|"
    r"data|translation|generation|classification|analysis)",
    flags=re.IGNORECASE,
)
_AGGREGATOR_HINT_RE = re.compile(r"(generative\s+ai|ai\s*[\-—–])", flags=re.IGNORECASE)


def _strip_punct(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    return _WHITESPACE_RE.sub(" ", s).strip()


def consolidation_stem_tokens(name: str | None, *, max_tokens: int = 3) -> list[str]:
    """Extract up to `max_tokens` significant stem tokens from a name.

    Drops stopwords ("the", "for", "ai", "generative", …) so legitimate
    product/topic stems surface ("copilot", "azure", "veritone",
    "summarization").

      "Microsoft Copilot for Education" → ["microsoft", "copilot", "education"]
      "MS Copilot - Summarization"      → ["copilot", "summarization"]
      "Azure AI Document Intelligence"  → ["azure", "document", "intelligence"]
    """
    if not name:
        return []
    s = _strip_punct(name)
    toks = [t for t in s.split(" ") if t and t not in _STEM_STOPWORDS]
    return toks[:max_tokens]


def is_omb_aggregator_name(name: str | None) -> bool:
    """True if a name looks like an OMB-side generic category aggregator.

    Two signals:
      1. Matches the precise generic-prefix pattern
         ("Generative AI - <topic>" / "AI - <topic>").
      2. Is short (<35 chars) AND mentions "Generative AI" / "AI -".
    """
    if not name:
        return False
    if _AGGREGATOR_PREFIX_RE.match(name):
        return True
    if len(name) < 35 and _AGGREGATOR_HINT_RE.search(name):
        return True
    return False


def detect_consolidated_upstream(
    unmatched_db_rows: Iterable[dict],
    omb_aggregator_candidates: Iterable[dict],
    *,
    min_cluster_size: int = 3,
) -> dict[int, int]:
    """Return {db_id: aggregator_omb_id} for rows judged consolidated upstream.

    Parameters
    ----------
    unmatched_db_rows : iterable of dicts with `db_id` and `use_case_name`.
        Pre-filtered to a single agency.
    omb_aggregator_candidates : iterable of dicts with `id` and
        `use_case_name`. Pre-filtered to the same agency.
    min_cluster_size : minimum number of unmatched DB rows sharing a stem
        token before the cluster is promoted.

    Procedure:
      1. For each unmatched DB row, extract stem tokens.
      2. Build inverted index token → {db_ids}.
      3. Check there's at least one aggregator name in the OMB pool.
      4. If no aggregator exists, return {} (no promotion).
      5. For every token whose row count ≥ min_cluster_size, mark every
         row in the bucket as consolidated upstream, pointing each at the
         lowest-id aggregator (stable; OMB's source_row order).
    """
    unmatched = [d for d in unmatched_db_rows if d.get("use_case_name")]
    aggregators = [
        a
        for a in omb_aggregator_candidates
        if is_omb_aggregator_name(a.get("use_case_name"))
    ]
    if not aggregators or len(unmatched) < min_cluster_size:
        return {}

    aggregator_id = min(int(a["id"]) for a in aggregators)

    token_to_db_ids: dict[str, set[int]] = {}
    for d in unmatched:
        toks = consolidation_stem_tokens(d["use_case_name"])
        for t in toks:
            token_to_db_ids.setdefault(t, set()).add(int(d["db_id"]))

    clustered: set[int] = set()
    for _tok, ids in token_to_db_ids.items():
        if len(ids) >= min_cluster_size:
            clustered.update(ids)

    return {db_id: aggregator_id for db_id in clustered}
