#!/usr/bin/env python3
"""Classify enterprise-wide GenAI rows (both years) into four delivery tiers.

The 2024->2025 enterprise-GenAI comparison changes not just in COUNT
(44 -> 232 use cases, 21 -> 24 agencies, post scope corrections) but in KIND.
This script makes that claim measurable by assigning every enterprise-wide
GenAI row to one of four tiers:

  permission       A policy permitting commercial GenAI use; no agency-run
                   service; public data only (e.g., DHS "employees are
                   permitted...", HHS Zoom/Teams blessings).
  embedded_cots    AI features arriving inside software the agency already
                   licenses (Westlaw AI, ServiceNow Now Assist, BriefCatch,
                   Adobe Firefly, Tableau).
  tenanted         A procured enterprise instance of a commercial assistant,
                   switched on for the workforce (M365 Copilot, ChatGPT
                   Enterprise/OneGov, Claude for Government, Gemini,
                   Perplexity, Palantir AIP).
  operated_build   A purpose-built, agency-branded service — usually a chat
                   UI over Azure OpenAI / Bedrock / OpenAI API inside the
                   agency boundary, approved for internal data (StateChat,
                   DHSChat, GSAi, SSA ASC, EnerGPT, CDC Chatbot, USAi).

Rules are tool-name / use-case-name keyword matches plus a hand-curated
override list for ambiguous rows. Output:

  audit/retag/enterprise-scope-2026-06/tier_classification_2024.csv
  audit/retag/enterprise-scope-2026-06/tier_classification_2025.csv

and an aggregate table on stdout (the numbers behind the dashboard chart in
the use-case-inventory repo and the personas doc table).
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT = ROOT / "audit" / "retag" / "enterprise-scope-2026-06"

# --- rule tables ----------------------------------------------------------

# Matched against tool_product_name (case-insensitive substring).
TOOL_RULES: list[tuple[str, str]] = [
    # embedded COTS features
    ("westlaw", "embedded_cots"),
    ("briefcatch", "embedded_cots"),
    ("tableau", "embedded_cots"),
    ("servicenow", "embedded_cots"),
    ("now assist", "embedded_cots"),
    ("adobe", "embedded_cots"),
    ("firefly", "embedded_cots"),
    ("microsoft teams", "embedded_cots"),
    ("percipio", "embedded_cots"),
    ("skillsoft", "embedded_cots"),
    ("grantsolutions", "embedded_cots"),
    ("google workspace", "embedded_cots"),
    ("sumtotal", "embedded_cots"),
    # tenanted commercial assistants
    ("copilot", "tenanted"),
    ("chatgpt", "tenanted"),
    ("claude", "tenanted"),
    ("gemini", "tenanted"),
    ("perplexity", "tenanted"),
    ("notebooklm", "tenanted"),
    ("palantir", "tenanted"),
    ("ask sage", "tenanted"),
    ("amazon q", "tenanted"),
    # operated builds (custom services on model APIs / RAG stacks)
    ("custom in-house", "operated_build"),
    ("azure openai", "operated_build"),
    ("openai api", "operated_build"),
    ("aws bedrock", "operated_build"),
    ("aretec", "operated_build"),
    ("energpt", "operated_build"),
    ("elsa", "operated_build"),
    ("simplifai", "operated_build"),
    ("eslate", "operated_build"),
]

# Matched against use_case_name when the tool rule doesn't decide.
# Specific products first; generic shape-of-the-name patterns last.
NAME_RULES: list[tuple[str, str]] = [
    ("commercial generative ai for", "permission"),  # DHS permission family
    ("unspecified commercial", "permission"),
    ("policy", "permission"),  # DOT GenAI Policy (2024+2025 row)
    ("permitted", "permission"),
    ("transcription in zoom", "permission"),
    ("report summarization by commercial", "permission"),
    ("ai-assisted real-time collaboration", "permission"),
    # embedded COTS named in the use-case title
    ("foia production tools", "embedded_cots"),  # FOIAXpress
    ("servicenow", "embedded_cots"),
    ("westlaw", "embedded_cots"),
    ("slack", "embedded_cots"),
    ("cryosparc", "embedded_cots"),
    ("oracle", "embedded_cots"),
    ("grammarly", "embedded_cots"),
    # tenanted assistants named in the title
    ("copilot", "tenanted"),
    ("chatgpt", "tenanted"),
    ("gemini", "tenanted"),
    ("microsoft 365", "tenanted"),
    # operated builds
    ("usai", "operated_build"),  # GSA-operated multi-model gateway
    ("statechat", "operated_build"),
    ("dhs-chat", "operated_build"),
    ("gsai", "operated_build"),
    ("agency support companion", "operated_build"),
    ("rexi", "operated_build"),
    ("doc chat", "operated_build"),
    ("ask dottie", "operated_build"),
    ("fdic chat", "operated_build"),
    ("doichatgpt", "operated_build"),
    ("govchat", "operated_build"),
    ("chatbot", "operated_build"),
    ("chat interface", "operated_build"),
    ("generative ai assistant", "operated_build"),  # DOL AI Center
    ("daisi", "operated_build"),
    ("i-nepa", "operated_build"),
    # generic shapes — bespoke internal tools (heavy in HHS's 2025 fleet)
    ("assistant", "operated_build"),
    ("virtual", "operated_build"),
    ("chat", "operated_build"),
    (" bot", "operated_build"),
    ("llm", "operated_build"),
    ("gpt", "operated_build"),
    ("generative ai", "operated_build"),
    ("ai-powered", "operated_build"),
    ("automat", "operated_build"),
]

# M-24-10 offered agencies a checklist of generic commercial-AI productivity
# tasks; 2024 rows whose commercial_ai field starts with one of these are
# workforce filings of commercial productivity AI (Copilot-class) -> tenanted.
TASK_PHRASES_2024 = (
    "improving the quality of written communications",
    "transcribing and summarizing",
    "summarizing the key points",
    "collaborating in real-time",
    "searching for information",
    "inputting large amounts of data",
    "prioritizing and categorizing incoming emails",
    "logging and analyzing time spent",
)

# (agency, use_case_name-prefix) -> tier. Hand-reviewed ambiguous rows
# (year-agnostic: the same capability keeps its tier across filings).
OVERRIDES: dict[tuple[str, str], str] = {
    "DOT|Enterprise Personal Productivity Assistant": "operated_build",
    "NASA|NASA-GPT": "operated_build",
    "NRC|Text Retrieval and Generation": "operated_build",
    "NARA|Develop a Natural Language Based Chat": "operated_build",
}
OVERRIDES = {tuple(k.split("|", 1)): v for k, v in OVERRIDES.items()}

TIERS = ["permission", "embedded_cots", "tenanted", "operated_build", "unclassified"]


def classify(agency: str, name: str, tool: str, commercial_ai: str = "") -> tuple[str, str]:
    """Return (tier, rule-that-fired)."""
    for (oa, prefix), tier in OVERRIDES.items():
        if oa == agency and name.startswith(prefix):
            return tier, "override"
    t = (tool or "").lower()
    for needle, tier in TOOL_RULES:
        if needle in t:
            return tier, f"tool:{needle}"
    n = (name or "").lower()
    for needle, tier in NAME_RULES:
        if needle in n:
            return tier, f"name:{needle}"
    c = (commercial_ai or "").lower()
    if any(c.startswith(p) for p in TASK_PHRASES_2024):
        return "tenanted", "task-phrase-2024"
    # Anything left is an enterprise GenAI row that names no commercial
    # product, no permission language, and no embedded host — in this
    # inventory those are bespoke mission tools (HHS's agent/review-tool
    # fleet). Default: operated_build, marked so it can be audited.
    return "operated_build", "default"


def rows_2025(conn: sqlite3.Connection):
    return conn.execute(
        """SELECT a.abbreviation, u.use_case_name,
                  coalesce(t.tool_product_name,''), u.stage_of_development, ''
           FROM use_cases u
           JOIN use_case_tags t ON t.use_case_id = u.id
           JOIN agencies a ON a.id = u.agency_id
           WHERE t.is_generative_ai = 1 AND t.is_enterprise_wide = 1
           ORDER BY a.abbreviation, u.use_case_name"""
    ).fetchall()


def rows_2024(conn: sqlite3.Connection):
    return conn.execute(
        """SELECT u.agency_abbreviation, u.use_case_name,
                  coalesce(t.tool_product_name,''), u.dev_stage,
                  coalesce(u.commercial_ai,'')
           FROM use_cases_2024 u
           JOIN use_case_tags_2024_canonical t ON t.use_case_id_2024 = u.id
           WHERE t.is_generative_ai = 1 AND t.is_enterprise_wide = 1
           ORDER BY u.agency_abbreviation, u.use_case_name"""
    ).fetchall()


def main() -> None:
    conn = sqlite3.connect(DB)
    rollup: list[tuple[int, str, int]] = []
    for year, rows in ((2024, rows_2024(conn)), (2025, rows_2025(conn))):
        out = OUT / f"tier_classification_{year}.csv"
        counts: dict[str, int] = {t: 0 for t in TIERS}
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(
                ["agency", "use_case_name", "tool_product_name", "stage", "tier", "rule"]
            )
            for agency, name, tool, stage, commercial_ai in rows:
                tier, rule = classify(agency, name or "", tool, commercial_ai)
                counts[tier] += 1
                w.writerow([agency, name, tool, stage, tier, rule])
        total = sum(counts.values())
        print(f"\n{year} (n={total}) -> {out.name}")
        for t in TIERS:
            if counts[t]:
                print(f"  {t:15s} {counts[t]:4d}  ({100*counts[t]/total:.0f}%)")
                rollup.append((year, t, counts[t]))

    # Persist the rollup for the dashboard (read by the /experience tier
    # chart). NOTE: `make fix` rebuilds the DB from sources and drops this
    # table — rerun this script after any full rebuild.
    with conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS enterprise_genai_tier_rollup (
                   year INTEGER NOT NULL,
                   tier TEXT NOT NULL CHECK (tier IN
                       ('permission','embedded_cots','tenanted','operated_build')),
                   n INTEGER NOT NULL,
                   PRIMARY KEY (year, tier)
               )"""
        )
        conn.execute("DELETE FROM enterprise_genai_tier_rollup")
        conn.executemany(
            "INSERT INTO enterprise_genai_tier_rollup (year, tier, n) VALUES (?,?,?)",
            rollup,
        )
    print("\nenterprise_genai_tier_rollup refreshed.")
    conn.close()


if __name__ == "__main__":
    main()
