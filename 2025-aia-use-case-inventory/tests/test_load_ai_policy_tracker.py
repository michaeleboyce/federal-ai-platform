"""Tests for scripts/load_ai_policy_tracker.py — reads
audit/research/ai_strategies/{documents,coverage}.csv into the two
agency_ai_policy_* tables. Idempotent wipe-and-reload."""
import sqlite3
import textwrap
from pathlib import Path

from migrations import m012_ai_policy_tracker as m012
from scripts import load_ai_policy_tracker as loader


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    m012.apply(c)
    return c


def _write_csvs(tmp: Path, docs_csv: str, cov_csv: str) -> Path:
    d = tmp / "ai_strategies"
    d.mkdir()
    (d / "documents.csv").write_text(textwrap.dedent(docs_csv))
    (d / "coverage.csv").write_text(textwrap.dedent(cov_csv))
    return d


DOCS_HEADER = (
    "agency_abbr,agency_name,agency_type,issuing_office,document_type,"
    "document_title,publication_year,publication_date,pages,issuing_memo,"
    "superseded,is_public,url,local_path,access_status,date_accessed,notes\n"
)
COV_HEADER = (
    "agency_abbr,agency_name,agency_type,searched,date_searched,"
    "ai_landing_page_url,ai_strategy_year,compliance_plan_year,"
    "genai_policy_year,caio_status,other_policy_count,total_documents,"
    "gaps,notes\n"
)


def test_loads_documents_and_coverage_row_counts(tmp_path):
    base = _write_csvs(
        tmp_path,
        DOCS_HEADER
        + "DHS,Department of Homeland Security,Cabinet,DHS OCIO,M-25-21 AI Strategy,DHS AI Strategy,2025,2025-09-26,10,M-25-21,no,yes,https://example.gov/dhs.pdf,documents/DHS/x.pdf,Downloaded,2026-05-21,\n"
        + "DHS,Department of Homeland Security,Cabinet,DHS OCIO,M-25-21 Compliance Plan,DHS Plan,2025,2025-09-26,12,M-25-21,no,yes,https://example.gov/dhs-plan.pdf,documents/DHS/y.pdf,Downloaded,2026-05-21,\n",
        COV_HEADER
        + "DHS,Department of Homeland Security,Cabinet,yes,2026-05-21,https://www.dhs.gov/ai,2025,2025,,Designated,2,2,,\n",
    )
    conn = _conn()
    loader.load(conn, base)
    assert conn.execute(
        "SELECT COUNT(*) FROM agency_ai_policy_documents"
    ).fetchone()[0] == 2
    assert conn.execute(
        "SELECT COUNT(*) FROM agency_ai_policy_compliance"
    ).fetchone()[0] == 1


def test_loader_coerces_year_and_pages_to_int(tmp_path):
    base = _write_csvs(
        tmp_path,
        DOCS_HEADER
        + "VA,Department of Veterans Affairs,Cabinet,VA OIT,M-25-21 AI Strategy,Building the Future,2026,,,M-25-21,no,yes,https://va.gov/x,,Link only,2026-05-21,\n",
        COV_HEADER
        + "VA,Department of Veterans Affairs,Cabinet,yes,2026-05-21,https://va.gov/ai,2026,,,Designated,0,1,,\n",
    )
    conn = _conn()
    loader.load(conn, base)
    row = conn.execute(
        "SELECT publication_year, pages FROM agency_ai_policy_documents"
    ).fetchone()
    assert row["publication_year"] == 2026
    assert row["pages"] is None  # blank pages stays NULL, not 0


def test_loader_coerces_boolean_flags(tmp_path):
    base = _write_csvs(
        tmp_path,
        DOCS_HEADER
        + "DOJ,Department of Justice,Cabinet,DOJ,M-24-10 Compliance Plan,DOJ Plan,2024,2024-10-01,11,M-24-10,yes,yes,https://justice.gov/x,documents/DOJ/x.pdf,Downloaded,2026-05-21,\n",
        COV_HEADER
        + "DOJ,Department of Justice,Cabinet,yes,2026-05-21,https://justice.gov/ai,,2024,,Designated,1,2,No M-25-21 strategy,\n",
    )
    conn = _conn()
    loader.load(conn, base)
    row = conn.execute(
        "SELECT superseded, is_public FROM agency_ai_policy_documents"
    ).fetchone()
    assert row["superseded"] == 1
    assert row["is_public"] == 1


def test_loader_is_idempotent(tmp_path):
    base = _write_csvs(
        tmp_path,
        DOCS_HEADER
        + "OPM,Office of Personnel Management,Independent,OPM,M-25-21 AI Strategy,OPM Strategy,2025,2025-09-30,7,M-25-21,no,yes,https://opm.gov/x.pdf,documents/OPM/x.pdf,Downloaded,2026-05-21,\n",
        COV_HEADER
        + "OPM,Office of Personnel Management,Independent,yes,2026-05-21,https://opm.gov/ai,2025,2025,,Designated,0,2,,\n",
    )
    conn = _conn()
    loader.load(conn, base)
    loader.load(conn, base)
    assert conn.execute(
        "SELECT COUNT(*) FROM agency_ai_policy_documents"
    ).fetchone()[0] == 1
    assert conn.execute(
        "SELECT COUNT(*) FROM agency_ai_policy_compliance"
    ).fetchone()[0] == 1
