# Drop-in draft: the FedRAMP section

_Prepared 2026-07-05. Every number verified against the live DB that day
(marketplace snapshot 2026-06-12; the three 20x listings re-checked on
fedramp.gov 2026-07-03) and pinned by `audit/checks/check_fedramp_fact_sheet.py`.
Numbers and guardrails: `fact_sheet.md` §7 / §6.7–11._

**Supersedes in earlier drafts:** any phrasing that FedRAMP "can't see
what's inside packages" (it publishes scope down to the service; it tracks
adoption only at the package); any unqualified reading of the 20x zeros as
"nobody adopted these tools" (adoption flows through channels the ledger
doesn't record); any use of "203 authorized AI products" (156 are
authorized; 47 are still in the pipeline; the split was 202 = 155 + 47
before 2026-07-05, when a false Aretec-SEARCH alias link to the Clarivate
CIPAI-ISP listing was removed).

---

The government's system for approving cloud software tells a strange story
about AI — strange enough that the system itself has become part of the
story.

FedRAMP's premise is authorize once, reuse everywhere: one agency does the
security review, and every other agency can adopt the package with a
fraction of the work.[^1] For AI, the machinery has largely stalled on its
own terms. Of the 46 primary-purpose AI products on the FedRAMP
marketplace, 35 have completed authorization — and 26 of those 35 have
never spread past a single agency's authorization to operate.[^2] Even
where an agency did the paperwork, its own inventory usually shows nothing:
of the 48 agency-product authorization pairs that can be mapped to the 2025
AI use case inventories, only 10 are corroborated by a reported use case.
(Because barely a third of inventory entries name a specific product, the
honest reading is "no reported use," not "unused.")

The sharpest version of the pattern involves the most famous tools in the
world. In early 2026 the administration fast-tracked the frontier chat
platforms through FedRAMP's new 20x pathway: ChatGPT Enterprise was
authorized on January 9, Gemini for Government on January 21, Perplexity on
February 1.[^3] Months later, the marketplace ledger for all three showed
one program-level authorization apiece and zero recorded agency reuses. If
the official adoption ledger were the whole truth, the LLM mandate produced
nothing.

It is not the whole truth. Adoption is happening — it just routed around
the ledger. GSA's OneGov deals priced the frontier platforms at token
rates for every agency at once: ChatGPT Enterprise at $1 per agency for
2026, Google's stack at $0.47, Perplexity at $0.25 over eighteen
months.[^4][^5][^6] GSA's USAi platform serves multiple frontier models to
fifteen agencies, with more on a waiting list, under GSA's umbrella rather
than per-agency authorizations.[^7] And the Anthropic episode proved the
ledger's irrelevance in both directions: Claude reached an
all-of-department rollout at HHS without ever appearing on the FedRAMP
marketplace, and when a presidential directive ordered agencies to stop
using Anthropic's technology on February 27, 2026, the un-adoption didn't
touch the ledger either.[^8]

There is a third channel, and it has been hiding in FedRAMP's own
paperwork. The marketplace publishes, for each authorized package, a
catalog of the individual services its authorization covers — and inside
those catalogs sits frontier capability that package-level views never
surface. Amazon Bedrock, the AWS service that hosts Claude and other
foundation models, has been in scope of the standard AWS packages at both
the Moderate and High baselines the entire time the standalone 20x listings
sat at zero.[^9] An independent review of all 1,591 in-scope services
across the marketplace found 129 primary-purpose AI services inside 34
authorized packages — and 46 federal agencies hold an authorization on at
least one package containing one.[^10]

Which brings the story back to where it belongs: inside the agencies. A
service being in scope of a package an agency holds means the security
authorization already covers it — nothing more. It does not mean the
agency switched it on, and it emphatically does not mean an employee can
use it. Set the two facts side by side and the LLM mandate's real
bottleneck is unmistakable:

| Agency | Core-AI services in scope of packages it holds | Estimated staff access to a general-purpose AI tool† |
|---|---|---|
| HHS | 110 | broad (~50% of eligible staff) |
| Energy | 99 | broad (~81%) |
| Treasury | 98 | pilot (~5%) |
| State | 93 | near-universal (~95–100%) |
| Justice | 63 | latent (IFP assessment: ~1%) |
| HUD | 41 | pilot (~0.15%) |
| SBA | 41 | none identified (0%) |

_† IFP web-corroborated availability estimates, not OMB data; "in scope"
reflects the package's authorization, not agency enablement._

The Small Business Administration holds authorizations on packages whose
scope catalogs contain forty-one primary-purpose AI services — Azure
OpenAI among them — and its employees, as far as any public evidence
shows, have access to none of them. Justice holds sixty-three, including
Bedrock at both the Moderate and High baselines, against roughly one
percent staff access. State holds ninety-three — and
actually turned the capability into near-universal access. Same shelf,
same legal path, opposite outcomes. The variable was never the
marketplace, the models, or the money, which by 2026 cost less per agency
than a cup of coffee. It was each agency's internal decision to take what
it already had and put it on an employee's screen.

---

## Footnotes

[^1]: FedRAMP, "Agency Authorization Playbook" — each agency issues its own
ATO with a presumption of adequacy for the existing package.
https://www.fedramp.gov/resources/documents/Agency_Authorization_Playbook.pdf

[^2]: IFP analysis of the FedRAMP marketplace (snapshot June 12, 2026):
independent per-listing AI classification; distinct authorizing agencies
per product. Interactive: https://use-case-inventory.vercel.app/fedramp/coverage/spread

[^3]: FedRAMP Marketplace listings FR2533155773 (ChatGPT Enterprise and API
Platform, Moderate, Jan 9, 2026), FR2604952026 (Gemini for Government, Low,
Jan 21, 2026), FR2604643715 (Perplexity Enterprise and API Platform, Low,
Feb 1, 2026) — each showing 1 authorization, 0 reuses as of July 3, 2026.
https://www.fedramp.gov/marketplace/products/FR2533155773/

[^4]: ExecutiveGov, "OpenAI to Offer ChatGPT at $1 Per Federal Agency"
(Aug 7, 2025).
https://www.executivegov.com/articles/chatgpt-federal-subscription-openai-gsa-gruenbaum

[^5]: GSA newsroom, "GSA, Google Announce Transformative 'Gemini for
Government' OneGov Agreement" (Aug 21, 2025).
https://www.gsa.gov/about-gsa/newsroom/news-releases/gsa-google-announce-gemini-onegov-agreement-08212025

[^6]: GSA newsroom, "GSA and Perplexity Sign First Direct to Government
Deal" (Nov 19, 2025).
https://www.gsa.gov/about-gsa/newsroom/news-releases/gsa-perplexity-sign-first-direct-to-gov-deal-11192025

[^7]: Nextgov/FCW, "GSA to require agencies to pay for USAi after launching
it as a free service" (Apr 7, 2026).
https://www.nextgov.com/artificial-intelligence/2026/04/gsa-require-agencies-pay-usai-after-launching-it-free-service/412678/

[^8]: FedScoop, "Anthropic faces fallout across federal agencies from DOD
clash" (Feb 27, 2026) — cease-use directive, supply-chain-risk
designation, GSA removal from USAi and MAS termination.
https://fedscoop.com/anthropic-claude-dod-federal-agency-fallout-trump-hegseth/

[^9]: FedRAMP marketplace scope catalogs for AWS US East/West (Moderate)
and AWS GovCloud (High), which list Amazon Bedrock among services in
scope. Verifiable at:
https://use-case-inventory.vercel.app/fedramp/marketplace/products/AGENCYAMAZONEW

[^10]: IFP per-service classification of the 1,591 unique in-scope services
(129 core-AI; every AI label adversarially reviewed by a second model
pass; row-level provenance published). Interactive:
https://use-case-inventory.vercel.app/fedramp/coverage/spread#services and
https://use-case-inventory.vercel.app/fedramp/coverage/agencies
