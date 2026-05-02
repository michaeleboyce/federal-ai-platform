# AI Coding-Assistant Audit: Methodology, Surprises, Gaps

## Methodology

1. **DB candidate set (3,616 individual + 192 consolidated rows).**
   - Existing tags: `is_coding_tool=1` (38 individual rows) and `is_github_copilot=1`.
   - Use-case-name LIKE matches on coding-tool product names, "code generation", "code modernization", "pair programming", "developer", "software development", "code assist", "windsurf", "tabnine", "codeium", "amazon q", "github copilot", "gemini code", "codex".
   - Problem-statement and system-outputs LIKE matches on the same plus "boilerplate code", "code refactor", "code completion", "developer productivity", "pair programmer".
   - Raw-JSON full-text scan for the major product names (caught nothing the use-case-name scan missed in this case).
   - Consolidated `ai_use_case` LIKE 'Generating code' or 'Coding%'.

2. **Per-row narrative review.** For every candidate, I read `problem_statement`, `system_outputs`, `expected_benefits`, `vendor_name`, `system_name`, and `bureau_component` to decide whether it's truly a developer coding assistant vs. an autoclassifier or a general-purpose chatbot that happens to mention code.

3. **Public corroboration.** Targeted web searches for VA GitHub Copilot (handbook + customer story confirmed), DOJ GitHub Copilot (workshop is Microsoft 365 Copilot Chat — the DB row is the stronger evidence here), DHS, DOC, DOE labs. The agency-level corroboration was strongest for VA.

4. **Per-agency rating** based on stage of development, scope language ("Department wide" vs. specific bureau), number of independent organizations within the agency, and consolidated-template signal.

## Biggest tag corrections found

### False negatives (should have been tagged coding, weren't)
1. **DOJ "Code Development"** (id 8713) — explicitly Department-wide, vendors GitHub + Microsoft, language matches GitHub Copilot. Tag is missing entirely. This is the single biggest agency-level miss in the existing tag set.
2. **DOJ "AI-assisted Legacy Code Modernization"** (id 8742) — explicit AI code translation/refactoring, untagged.
3. **DOC NOAA Amazon Q Developer Pilot** (id 7828) and **APIgee with Gemini Code Assist** (id 7829) — product names are literally in the title; both untagged. Same for **Streamlining Fisheries DevSecOps with Gemini Code Assist** (id 7697) and **Scientific Code Development Assistance** (id 7678).
4. **DOE Tabnine AI Pair Programmer** (id 8017) and DOE **Software Implementation Assistant** (id 8139, vendor explicitly "Purchased from a Vendor - Tabnine") — both Tabnine, both untagged.
5. **DOE Hanford GitHub Co-Pilot** (id 8022) — product name in title, untagged.
6. **HHS** has multiple untagged: AI DevOps (9206), AI Workspace (9333), AI-Generated Data Processing (9450), Code Conversion for PowerBI Migration (9472), Notebooks Hub (9561), Writing code using AI (9563), Coding translation (9580), CCSQ Now Assist for Creator (9339).
7. **SSA "Intelligent generation of modernized code"** (id 10228, vendor AveriSource) — clearly a coding/modernization tool, untagged.
8. **Treasury** — most coding-related entries (10395, 10396, 10399, 10444, 10449, 10472) are untagged.
9. **DOI BTFA GitHub Copilot integration** (id 8451) — product name in title, untagged.
10. **NSF AWS Assisted Software Development** (id 10087) had an Amazon CodeWhisperer product tag but `is_coding_tool` = 0. Got a corrected tag here.

### False positives (tagged coding, shouldn't be)
1. **DHS LIGER Generative AI Toolkit** (id 7499) — document drafting (PDs, SOWs, emails) for FPS, not coding.
2. **DHS PAiTH** (id 7490) — agency-wide RAG for legal/admin personas, not a coding tool.
3. **DOL Occupation Code Suggestion For Job Duties Data** (id 8779) — SOC autoclassifier, not coding.
4. **HHS OSPIDA RPAB Scientific Coding Assistance Tool** (id 9576) — assigns NIAID scientific codes to grant applications. NLP autoclassifier, not coding.
5. **HHS Stem Cell Auto Coder** (id 9520) — autoclassifier, retired.
6. **VA Internal QMS Processes Revamp** (id 10777) — document classification, not coding.
7. **NASA AIML for Code Review** (id 9798) — was real coding tool but retired; current_is_coding_tool=1 still appropriate for retired evidence, just not active deployment.

The "code" word is ambiguous: BLS/DOL/DOJ/DOC use it heavily for *autocoders* (Standard Occupational Code, ICD-10, NAICS, JASC). All BLS occupation/expenditure/SOII autocoders, DOJ MACO/OTAC/ROTA autocoders, FAA SDRS JASC code picker, HHS MedCoder + NIOCCS — every one of these is a classifier, not a coding tool.

## Surprises

1. **DOJ has not publicly announced a department-wide GitHub Copilot deployment, but its inventory describes one.** The "Code Development" use case is marked Department-wide with vendors GitHub + Microsoft. The most public evidence I found is a Microsoft 365 Copilot Chat workshop — different product. DOJ's actual GitHub Copilot footprint is bigger than the public record suggests.

2. **VA is the cleanest "enterprise" deployment in our dataset.** They have a public VA-GitHub-Handbook with explicit Copilot-access policies, a 30-day activity policy, and the strategy document explicitly names GitHub Copilot. ~7,000 OIT staff appear to be the addressable population.

3. **ED has a quietly large coding deployment via OpenAI + Google Distributed Cloud.** Eleven program offices each filed effectively the same use case ("Generative AI - Code Generation") with consistent narrative about generating Python, R, VBA, DAX, and Excel snippets. Plus a separate agency-wide M365 Copilot deployment. Combined, this likely exceeds VA in user count.

4. **SSA picked Windsurf** — the only agency in the dataset using it. They are also the only agency with IBM watsonx Code Assistant + Broadcom Code for Z (mainframe-specific).

5. **SBA is running Q Developer and GitHub Copilot side-by-side as a head-to-head.** This is unusual — most agencies pick one.

6. **DOE labs are independently procuring fragmented tooling.** SLAC, WAPA, PNNL, Hanford, KCNSC, Savannah River, ORNL, INL, LLNL each have their own deployment with different products. The "DOE coding posture" depends entirely on which lab.

7. **FCC's consolidated entry includes Amazon Q Developer at 101–1000 users** despite no individual-row narrative anywhere. Worth digging into for the article.

8. **FDIC has GitHub Copilot enterprise per the consolidated template (101–1000 users) but their 50-row individual inventory contains zero coding-tool narratives.** This is a reporting-quality issue: the template captures it, but the detail is missing.

9. **The OMB Appendix B "Generating code using AI" template is checked Y by 8 of 11 agencies that file consolidated.** That's a higher rate than the individual-row evidence supports — many of those Y boxes are for M365 Copilot's chat code feature, not a managed coding assistant.

## Ambiguous cases

- **M365 Copilot for code vs. real coding assistant.** M365 Copilot Chat can produce code on demand. Several agencies (ED, CSOSA, USITC, FCC, possibly DOJ) effectively rely on this for code generation rather than provisioning GitHub Copilot. I treated these as "Limited/Pilot" with low-to-medium confidence rather than "Enterprise/Broad" coding-tool deployments, because the M365 license is administrative and the code feature is incidental.
- **Amazon Q in Connect (SBA, id 10120)** — Q-branded but it's a contact-center agent assist. Excluded.
- **Databricks Genie / Genie Code (HHS CDC id 9299, SEC id 10184).** These let analysts query data in natural language and emit SQL — analyst tooling, not developer tooling. Excluded.
- **Microsoft Copilot Studio (DOE ORNL id 7917).** This is a low-code citizen-developer canvas, not a pro-developer coding assistant. Excluded.
- **HHS CDC AIP Assist (id 9316).** Palantir AIP support tool that "guides users in developing their own applications." Borderline — counted as platform-help rather than coding assistant.
- **DOE general-LLM rows (INL Microsoft Copilot 8043, ChatGPT 8072, Anthropic Claude 8150).** These are general-purpose enterprise LLM access at INL with explicit code-generation narrative. Included as Limited/Pilot for "code uses" but they're not dedicated coding assistants.

## Gaps where I could not confirm

- **FCC 101–1000 Q Developer users** — no individual entries, no public press release found.
- **FDIC 101–1000 GitHub Copilot + Appian users** — same.
- **CSOSA 1001–5000 M365 Copilot for code users** — small agency claiming a large code footprint via M365; no individual narrative to verify.
- **DHS** — public DHS AI page lists 158 active use cases but I did not find a public mention of agency-wide GitHub Copilot. The 2025 inventory also does not show one. CBP and FEMA appear to be running independent coding tool pilots rather than a department program.
- **NASA** — I expected an enterprise code-assistant program given NASA's GitHub presence, but the 2025 file shows only center-by-center pilots (GSFC dominantly). Possibly NASA-wide procurement is upcoming but not yet in inventory.
- **DOT** — surprising absence given FAA's IT modernization workload.
- **GSA** — runs USAi.gov for government but their own internal developer-coding-tool footprint is invisible in the 2025 file. May be a reporting gap.

## Article-relevant gaps that worry me

1. **DOJ Department-wide GitHub Copilot** is not corroborated by a public announcement — only by the inventory row. A reporter should ask DOJ to confirm rollout scope and population.
2. **FDIC, FCC, CSOSA, USITC consolidated-template Y entries** are essentially the only evidence for those agencies. Worth FOIA / direct-confirmation.
3. **DOE national-lab fragmentation** — labs procure individually under M&O contracts, so "DOE has GitHub Copilot" is misleading without naming the labs.
4. **The 22 "None reported" agencies are a mix of high- and low-confidence absences.** Small independent agencies (NMB, NCUA, NTSB, FERC, FRTIB) genuinely have small dev shops; HUD, USDA, GSA, DOT, SEC have larger dev shops and the absence is more suspicious — possibly a reporting completeness gap rather than a real "no."

## Files

- `audit/retag/coding/by_agency.md` — agency rollup
- `audit/retag/coding/by_row.csv` — per-row review
- `audit/retag/coding/notes.md` — this file
