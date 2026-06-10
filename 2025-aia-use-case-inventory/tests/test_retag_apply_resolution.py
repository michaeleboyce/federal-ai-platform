"""Guard: the 2026-04 retag apply passes must keep resolving after rebuilds.

The original failure mode (see scripts/apply_retag_audit.py docstring): the
audit CSVs carry 2026-04 snapshot ids, `make fix` rotates the id space, and
the apply scripts silently no-op'd for weeks — StateChat stayed
bureau-scoped, DOJ's department-wide coding deployment stayed untagged,
and the dashboard published heuristic numbers the audits had corrected.

These tests resolve every audit row against the LIVE DB via the same
Resolver the apply scripts use, and fail loudly when resolution degrades.
They run read-only.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from uc_signature import Resolver, _norm  # noqa: E402

DB = ROOT / "data" / "federal_ai_inventory_2025.db"


@pytest.fixture(scope="module")
def resolver():
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        yield Resolver(conn)
    finally:
        conn.close()


def _int(s):
    s = (s or "").strip()
    if not s or s == "NA" or "-" in s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _resolve_csv(resolver: Resolver, path: Path) -> tuple[int, int]:
    """Resolve every row of an audit CSV; returns (attempted, unresolved)."""
    attempted = unresolved = 0
    with open(path) as f:
        for row in csv.DictReader(f):
            name = (row.get("use_case_name") or "").strip()
            old_id = _int(row.get("use_case_id"))
            if "-" in (row.get("use_case_id") or ""):
                continue  # agency-platform range rows ("9099-9114") — the
                # apply script skips these; they feed by_agency.md instead
            if old_id is None and not name:
                continue  # queue-only rows
            attempted += 1
            if name.lower().endswith("(consolidated)"):
                base = name[: name.lower().rfind("(consolidated)")].strip()
                ids = resolver.cons_by_signature(row.get("agency"), base)
            else:
                ids = resolver.uc(old_id, row.get("agency"), name or None)
            if not ids:
                unresolved += 1
    return attempted, unresolved


ROUND1 = [
    ROOT / "audit" / "retag" / "general_llm" / "by_row.csv",
    ROOT / "audit" / "retag" / "coding" / "by_row.csv",
    ROOT / "audit" / "retag" / "data_analysis" / "by_row.csv",
]
ROUND2 = [
    ROOT / "audit" / "retag" / "round2" / "general_llm" / "resolved.csv",
    ROOT / "audit" / "retag" / "round2" / "coding" / "resolved.csv",
    ROOT / "audit" / "retag" / "round2" / "data_analysis" / "resolved.csv",
    ROOT / "audit" / "retag" / "round2" / "entry_type" / "resolved.csv",
]


@pytest.mark.parametrize("path", ROUND1 + ROUND2, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_audit_csv_resolution_rate(resolver, path):
    attempted, unresolved = _resolve_csv(resolver, path)
    assert attempted > 0
    frac = unresolved / attempted
    assert frac <= 0.02, (
        f"{path.relative_to(ROOT)}: {unresolved}/{attempted} rows "
        f"({frac:.1%}) no longer resolve against the live DB — the retag "
        f"apply pass is degrading. Regenerate signatures or fix the resolver "
        f"before shipping a rebuild."
    )


def test_anchor_rows_resolve(resolver):
    """The three audited rows we use as canaries must resolve exactly."""
    assert resolver.uc(10265, "State", "StateChat"), "StateChat must resolve"
    assert resolver.uc(8713, "DOJ", "Code Development"), "DOJ Code Development must resolve"
    assert resolver.uc(7437, "DHS", "Source Code Development Tool"), (
        "DHS Source Code Development Tool must resolve"
    )


def test_applied_state_statechat():
    """After `make fix`, the audit's flagship correction must be present:
    StateChat is enterprise-wide (45K active users; FedScoop-verified)."""
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        row = conn.execute(
            """
            SELECT t.deployment_scope, t.is_enterprise_wide
              FROM use_cases u
              JOIN use_case_tags t ON t.use_case_id = u.id
             WHERE u.use_case_name LIKE '%StateChat%'
            """
        ).fetchone()
    finally:
        conn.close()
    assert row is not None, "StateChat row missing from use_cases"
    assert row[0] == "enterprise_wide" and row[1] == 1, (
        f"StateChat scope is {row!r} — apply_retag_audit corrections "
        "are not reaching the DB (silent no-op regression)."
    )


def test_applied_state_doj_coding():
    """DOJ 'Code Development' (department-wide GitHub Copilot filing) must
    carry is_coding_tool=1 after the apply pass."""
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        row = conn.execute(
            """
            SELECT t.is_coding_tool
              FROM use_cases u
              JOIN agencies a ON a.id = u.agency_id
              JOIN use_case_tags t ON t.use_case_id = u.id
             WHERE a.abbreviation = 'DOJ' AND u.use_case_name = 'Code Development'
            """
        ).fetchone()
    finally:
        conn.close()
    assert row is not None and row[0] == 1, (
        f"DOJ Code Development is_coding_tool={row!r} — retag corrections absent."
    )


def test_norm():
    assert _norm("  StateChat  ") == "statechat"
    assert _norm("A  B") == "a b" or _norm("A  B") == "a b"
