# Round-3 sub-agency findings — editorial summary

Three slice agents independently rated 96 federal sub-agencies on
general-purpose LLM access, AI coding tools, and AI data-analysis platforms.
The point of round-3: at the article level, "HHS" and "NASA" and "DOE" are
the wrong unit of analysis — most variance lives below them. This document
is the cross-topic synthesis, written for the article. The full per-row
evidence is in `audit/retag/round3/<topic>/sub_agency_rows.csv`.

## The headline

**Only one sub-agency in the federal civilian space hits the top tier on all
three dimensions: VA/OIT.** Veterans Affairs' Office of Information &
Technology (~7K staff, the IT shop behind VA GPT) is the cleanest example
of an agency unit that simultaneously runs an enterprise LLM, an
enterprise-class coding rollout (GitHub Copilot via the VA-GitHub Handbook
program), and a real analyst environment ("Rockies" Databricks/Azure ML
powering VHA research). No other sub-agency hits all three.

23 sub-agencies clear two of three. Most strong-on-LLM-and-data sub-agencies
fall short on coding because of the editorial rule that generic LLMs
(M365 Copilot, ChatGPT, Claude) don't count as coding tools — those agencies
have the LLM half but haven't authorized a real developer-tool deployment.

## What the sub-agency view changes

### HHS isn't a single rollout — it's a federation of LLM-enabled bureaus

The round-1 parent rating treated HHS as "Enterprise" because of the
department-wide Anthropic Claude deal plus FDA Elsa plus NIH ChIRP. The
round-3 view shows that *eight of eleven* HHS bureaus independently meet the
Enterprise threshold on general LLM: NIH (ChIRP), CDC, CMS (CMS AI Workspace),
FDA (Elsa), FDA-CDER, ACF (Discover/Horizon), CMS-OIT, HRSA, and CMS-OC.
Only AHRQ and CMS-CCIIO inherit from the parent. **The story isn't "HHS
deployed Claude"; it's "every HHS operating division independently built or
adopted an enterprise LLM."**

On data analysis, the same density holds. CDC (EDAV/1CDP), CMS (IDR-Snowflake
+ DataConnect-Databricks), NIH (IDAP+Biowulf), and ACF (Palantir) all rate
Strong. FDA is the surprising under-performer — narrative gives FDA Elsa for
LLM but the analyst-platform side is comparatively thin.

On coding, however, every HHS bureau is Limited/Pilot or None reported.
**HHS's coding posture is uniformly weak across its bureaus, in stark
contrast to its LLM posture.**

### DOE is bimodal, not federated

The DOE parent rating "Broad / Federated" papers over a 2× variance between
labs. Seven labs and HQ offices clear Enterprise on general LLM (LANL,
PNNL, INL, SRS, LLNL, Naval Reactors, NREL). Five labs and HQ offices
report no general LLM at all (BNL, FNAL, NETL, ANL, NNSA HQ).

On data analysis, it's the *opposite* alignment that's striking: LANL,
PNNL, INL, ORNL, NREL all rate Strong (lab HPC + named platforms), while
the Enterprise-LLM-but-weak-data labs (NR, SRS) lag. The two rankings
correlate but don't perfectly track.

On coding, DOE is uniformly weak — generic-LLM rule strips out the
M365 Copilot/ChatGPT/Claude rollouts that lab IT teams adopted. Only
KCNSC has a named coding-tool deployment.

### NASA Goddard is the outlier center

NASA/GSFC alone clears Enterprise on general LLM (ChatGSFC, >7K users) and
Strong on data analysis (HECC + Prithvi + NCCS). The other six NASA
centers (MSFC, JPL, LaRC, ARC, JSC, GRC) are uniformly Limited or None
reported on LLM, mixed on data analysis, and zero on coding.

**JPL's absence on coding is suspicious** — the agency is NASA's flight-
software powerhouse with thousands of developers, yet zero coding-tool
entries in its 43 use cases. Likely a reporting gap rather than a real
absence; worth flagging in the article.

### Treasury OCC is the cleanest single bureau

OCC.Chat (25 of 26 OCC use cases LLM-tagged, in production since Dec 2024)
is the cleanest bureau-level Enterprise LLM in the federal civilian space.
ChatOFR also clears Enterprise. Two of Treasury's five sub-agencies run
named bureau-wide enterprise LLMs while the parent rating stays "Broad /
Federated."

### DOJ's department-wide CoPilot is publicly thin

DOJ's parent "Broad" rating leans on a single inventory row claiming a
Department-wide CoPilot deployment. The sub-agency view rates only FBI, DEA,
and ATR at Broad — the rest of DOJ's components are Limited or None
reported. **The DOJ-wide CoPilot rollout is pre-deployment per the
inventory and uncorroborated publicly.** If the article references it, it
needs the press inquiry resolved first.

## Parent ratings worth revising in the article

| Parent | Round-1 rating | Recommended caveat |
|---|---|---|
| NASA | Broad / Federated | Anchor at GSFC; note other centers are Limited/None |
| DOJ | Broad | Downgrade to "Limited / Federated pilots" until DOJ-wide CoPilot is verified |
| DOE | Broad / Federated | Note the bimodal lab distribution — "either Enterprise or None reported" |
| VA | Enterprise | Note Enterprise rating is OIT-bound (7K staff); VHA (253 uc) and VBA inherit but don't run own coding tools |
| HHS | Enterprise | Strengthen — note 8 of 11 bureaus independently Enterprise |

## Sub-agencies worth naming in the article

The most editorially useful concrete callouts (rated High or Medium
confidence on at least 2 of 3 topics):

**Strong-across-the-board (top 8):**
1. VA/OIT — only triple-strong; GitHub Copilot + VA GPT + Rockies platform
2. NASA/GSFC — ChatGSFC + HECC; the science star
3. NIH (HHS) — ChIRP + Biowulf + IDAP; the deepest analytic stack
4. CDC (HHS) — EDAV + 1CDP + Model Studio; CDC has world-class
5. CMS (HHS) — IDR-Snowflake + DataConnect; the regulator's analyst stack
6. USGS (DOI) — 187 use cases, Vertex AI document workbench, USGS Azure OpenAI
7. LANL (DOE) — DNA-P (Palantir AIP) + lab HPC; mission-side leader
8. State/DT — Funhouse + StateChat platform; the State Dept's data-eng shop

**Surprising thinness:**
- FDA — strong on LLM (Elsa) but Limited on data-analysis platforms despite
  being one of HHS's most-cited bureaus
- JPL — zero coding tools in inventory
- BNL, FNAL, NETL — DOE labs reporting no general LLM at all

## Methodology and caveats

Foundation pack ([_foundation/sub_agencies.json](_foundation/sub_agencies.json))
includes 96 sub-agencies meeting the use-case threshold (≥5 for sub_agency
level, ≥10 for office level). Each slice agent worked from the foundation
plus the existing parent rollup; web search was used only for ambiguities
(8 searches total across the three slices).

The CHARTER ([_foundation/CHARTER.md](_foundation/CHARTER.md)) documents
the rating scale and decision rules each slice agent followed.

Bias check: the data-analysis ratings are the most generous, partly because
the agent inferred Moderate as a floor for sub-agencies of any parent rated
"Strong." The general-LLM and coding ratings are tighter. Cross-topic
findings should weight LLM and coding more heavily than data-analysis.

The 16 non-reporting agencies (DoD, USAID, ODNI, CFPB, etc.) are excluded
from this round entirely. DoD's sub-agencies (Army Research Lab, Navy
Research Lab, AFRL, DARPA) would dwarf most of the entries above if
included.
