# Verification pass: government coding-agent deployment data (2026-07-07)

**Verdict: the blanket absence claim is REFUTED as literally worded.**
"No government anywhere has published deployment data for coding
assistants/agents" is false — the UK and Singapore both published. The
defensible reformulations are at the bottom. All access dates 2026-07-07.

## The two refutations (published usage AND outcome data)

### UK — GDS/DSIT "AI coding assistant trial" (published ~Sept 2025)
https://www.gov.uk/government/publications/ai-coding-assistant-trial/ai-coding-assistant-trial-uk-public-sector-findings-report
- ~1,900 licences across 50+ public-sector orgs (1,600 GitHub Copilot
  distributed / 1,100 redeemed; 323 Gemini Code Assist / 173 redeemed);
  trial Nov 2024–Feb 2025.
- HARD TELEMETRY: ~418 avg daily active users; ~2,298 daily chat
  interactions; **15.8% code-line acceptance rate** (tool dashboards).
- Self-reported (424 survey responses): 56 min/day saved ("28 working
  days/year"); 72% good value; 15% of AI code used unedited.
- Report's own caveats: access was trial-period-only and terminated
  after; savings self-reported; "optimism bias"; missing month-2
  telemetry; no control group.

### Singapore — GovTech pilot study (arXiv 2409.17434, Sept 2024)
https://arxiv.org/html/2409.17434v1
- GitHub Copilot for Business, Oct 2023–Jan 2024; 70 developers signed
  up / 40 survey respondents; telemetry 22% prompt acceptance;
  self-reported ~22% coding-time reduction (33% juniors), ~12% overall
  productivity; context ~8,000 public-sector developers.

## Near-misses (no published usage+outcome data)

- **US VA**: Copilot deployed (managed via "Copilot Users" team in VA's
  GitHub Enterprise; ~5,000 of OIT's 7,000+ are GitHub users) but the
  widely-cited "2,000 developers" figure could not be independently
  sourced and NO usage/outcome telemetry is published. **Conflation
  trap**: VA's published "~100,000 users / 2–3 hrs-week" metric is VA
  GPT (a chat tool), NOT the coding assistant.
- **US DoD CDAO**: Feb 2026 solicitation for AI coding tools for "tens
  of thousands of users" — explicitly admits DoD "lacks standardized,
  enterprise-wide access to AI-enabled coding tools." Solicitation only.
- **US GSA**: USAi includes code-gen; "considering AI coding agents" —
  announcements, no telemetry.
- **Australia**: the DTA trial was M365 Copilot (office productivity),
  NOT coding — the #1 conflation risk; never cite it as coding evidence.
- Canada CDS, Japan Digital Agency, Estonia, EU institutions: nothing
  found.

## Defensible reformulations (pick one)

TIGHTEST: "No government has published sustained, at-scale
production-deployment data — usage telemetry or measured outcomes — for
autonomous coding AGENTS given to its standing developer workforce. The
published government evidence to date comes entirely from time-limited
TRIALS of autocomplete/chat-style coding ASSISTANTS (UK, Singapore),
plus procurement announcements and self-reported testimony (US VA, DoD,
GSA)."

BROADER: "The only government deployment data published for coding
assistants comes from short, time-boxed trials (UK ~1,900 licences over
3 months; Singapore ~70 developers over 4 months), with headline
productivity figures that are overwhelmingly self-reported. No
government has published data from a sustained, at-scale rollout to its
permanent developer workforce, and none has published anything
comparable for autonomous coding agents."

Distinctions to preserve: trial vs sustained production; ASSISTANT
(autocomplete/chat) vs autonomous AGENT; self-reported vs telemetry;
seat announcement/testimony vs usage+outcome data.
