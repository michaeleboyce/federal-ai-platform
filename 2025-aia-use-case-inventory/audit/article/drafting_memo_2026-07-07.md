# Drafting memo — comparator findings → article edits (2026-07-07)

For the author. Maps the verified comparator research (fact_sheet §8,
`research_2026-07-07/`, claims_review_2026-07-07.md) onto the current
draft (`drafts/2026-07-06-adoption-article-draft.md`). Everything cited
here survived adversarial verification; phrasing constraints are binding.

## 1. The new section the draft needs: "What the fast adopters did differently"

Placement: between "Something big is missing" and "Taking the next
steps". The argument in three moves:

1. **Access was solved everywhere, fast — and it was never enough.**
   Australia provisioned licenses ~6.5 weeks after its decision (their
   OneGov: piggybacking existing Microsoft contracts) and still got
   only a third of participants using Copilot daily. The UK's 20K-seat
   trial found the same shallow, summarisation-centric profile our
   integration-depth census found (42% standalone chat). The US is not
   behind on access mechanics; it is exactly where access-only policies
   plateau.
2. **The deep adopters added non-access mechanisms.** Singapore: a
   central build institution (see §4 below), a MANDATORY AI-literacy
   course for all 150K officers, a cross-agency usage leaderboard, and
   self-service bot-building (20K+ AIBots). Accenture: a funded
   change-management program (89% monthly-active in its measured
   tranche). Moderna: a CEO-set target — 100% adoption AND proficiency
   in six months — with a champions cohort. US states split on exactly
   this line: NJ (training-first, state-built, $1/user/month) and Utah
   (mandatory-training gate on Gemini access) built depth mechanisms;
   PA ran the classic pilot→expansion; CA built procurement plumbing.
3. **The US mandate already contains the missing half.** "…access to,
   AND APPROPRIATE TRAINING FOR, such tools." Singapore enforced its
   training clause; OMB never certified ours. This converts the
   comparative finding into a domestic legal hook — no new authority
   needed.

## 2. Upgrades to the five planks (keep all five; extend three)

- **Plank 1 (CIO certification)** → certify BOTH halves of the mandate:
  access AND training. Add the exception-categories language already
  drafted (TSA officer example). Precedents: Singapore's mandatory
  course; Utah's training-gated access; NJ's training-first rollout
  (its curriculum is already adopted by 25 states — a federal agency
  could adopt it tomorrow).
- **Plank 2 (FITARA scorecard)** → the graded metric should be USAGE
  TELEMETRY, not use-case counts: monthly-active share of eligible
  staff, per agency. Precedents: Singapore's leaderboard ("playful
  competition" — their words), Accenture's MAU discipline. This also
  future-proofs the inventory-reform plank: telemetry is what replaces
  narrative counting after the 2027-12-23 sunset.
- **Plank 5 (inventory reform)** → the reform is now demonstrated, not
  hypothetical: cite our integration-depth census as the prototype
  (measured in days from OMB's own filings), and the UK/Australia
  precedent that governments CAN publish rigorous evaluations — both
  published theirs; the US published a count.
- **USAi (within budget plank)** → reframe entirely per the OGP
  findings: the ask is not "more money for USAi" (no dollar anchor
  exists — see phrasing constraints) but the INSTITUTION: a standing,
  centrally-funded build shop distributing free over shared
  authentication, with no cost-recovery sunset. The devastating
  contrast: Pair's core team is ~8 people and reached 80%-ever-used of
  150K officers in ~2 years from a hackathon; USAi is scheduled to
  start charging agencies in FY2027 — a structural tax on exactly the
  adoption the mandate demands. (Congress could fix the FCSF
  cost-recovery constraint for USAi specifically.)
- **NEW recommendation (from the coding findings)**: a federal
  coding-assistant/agent TRIAL with published telemetry, on the UK
  model (their trial published acceptance rates and DAU; DoD's Feb-2026
  solicitation shows demand). The US would be the first government to
  publish AGENT-level production data — it already owns the only
  agent-level census (zero live).

## 3. Honesty passage (non-negotiable; guardrail §6.7)

One standard for self-reported numbers. The draft currently cites VA
2–3 hrs/week and CDC 41K-hours favorably while the comparator section
will treat UK/AU survey numbers skeptically. METR's RCT (19% slower
measured, 20%-faster believed) is the reason both get the same label.
Recommended move: keep the VA/CDC numbers WITH "(self-reported)" and a
one-sentence METR caveat — it strengthens credibility and sets up the
telemetry recommendation. Also: PA's 95-min figure only as
"participants estimated", paired with the 35-min-spent stat.

## 4. Corrections to the current draft text (do these regardless)

1. Sunset year: 2027-12-23, not 2028 (claims_review_2026-07-06b §1.1).
2. "Only three agencies (VA, NIH, CBP) adopted coding agents" → replace
   with the census numbers (70 filings; zero live agents; 4
   pre-deployment).
3. § 3613 framing (demonstrable-need inversion) — b §1.3.
4. DoD blind spot ≈ ⅓ of civilian workforce, not 60%.
5. VA Copilot ≠ VA GPT (the ~100K/2–3-hrs figure is the chat tool).
6. Do not use: Singapore default-on provisioning; Accenture timeline;
   Accenture 97%/15x; CA "1.5%/10K calls" as measured; NJ DOL/ANCHOR
   stats; PA Apr-2026 operational stats (methodology unstated).

## 5. Ready-made artifacts

- Comparison table: `research_2026-07-07/comparators.csv` (13 rows,
  outcome-type labeled).
- Visuals: /figures/adoption-comparators (mechanism matrix +
  evidence-quality panel; in build), /figures/integration-depth,
  /figures/bureau-divergence, /products frontier table.
- Every §8 number carries its verification vote and access date for
  footnoting.
