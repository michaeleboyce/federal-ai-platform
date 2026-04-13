# State Capacity in the Age of AI: Practical Steps to Get Every Federal Worker an LLM

## Introduction: The Disconnect Between AI's Promise and Government's Reality

ChatGPT has reached a staggering 700 million weekly active users as of August 2025, representing a fourfold increase from the previous year (CNBC, 2025). This isn't just another technology adoption curve—it's consumer-internet scale penetration that fundamentally changes how knowledge work gets done. Yet within the halls of government, a troubling disconnect persists between those crafting AI policy and those who could benefit from using these tools daily.

In a revealing moment on Nathan LaBenz's Cognitive Revolution podcast, former National Security Advisor Jake Sullivan acknowledged this gap when asked about his access to ChatGPT: "It's a disconnect. I acknowledge it. You know, I am now a avid would be an understatement user of these tools. I use them much less frequently when I was actually national security advisor and yet working on the issue every day." Sullivan attributed this to multiple factors: "the culture of government in terms of new technology adoption is historically slow...There are legal issues, particularly in the national security enterprise, especially if you're talking about things on what we call the high side and classified compute and the like" (The Cognitive Revolution, Episode: Jake Sullivan on Navigating AI Uncertainty and Managing Competition with China, 2025).

Dean W. Ball, who served as senior policy advisor for AI at the White House, painted an even starker picture in a subsequent episode. When asked about AI leverage in his White House work, Ball revealed the depths of the technological gap:

"LLMs are actually not permitted on White House computers. That's not true of all of government. That's specific to the White House." He explained this stemmed from compliance issues with the Presidential Records Act, a post-Watergate law that "relates to, you know, as it sounds like the specific documents produced within the basically within the executive office of the president...And there's something about compliance with that law that affects the ability of the White House to use, as I understand it, lots of modern technology. So, like, we can't use Slack or Microsoft Teams. You can't use, like, Zoom or Google Meet or Microsoft Teams for you to use, like, WebEx. Google Docs is another good example and also LLMs" (The Cognitive Revolution, Episode: Dean W. Ball on America's AI Action Plan & 4 Months at the White House, 2025).

Despite these restrictions, Ball found workarounds: "I used AI as a chief of staff for me and as kind of a research assistant...not a single word of the action plan was written by, edited by, or seen by AI prior to the release. At least not by me. But there were so many times when...I want to try to develop some policies relating to XYZ. And so, sometimes it might be, like, well, let's brainstorm."

This reality—where the architects of national AI policy cannot use the very tools they're regulating—should alarm every stakeholder in America's technological future. It's not just an ironic footnote; it's a fundamental impediment to informed policymaking and effective government service delivery.

## The Stakes: Why Every Constituency Should Care

The case for universal federal AI access transcends traditional political divides. Whether you believe in lean government efficiency or expansive public services, whether you prioritize AI safety or technological acceleration, the logic remains compelling: federal workers need these tools to do their jobs effectively in 2025.

### The Economic Imperative

Federal IT spending reached $102 billion in fiscal year 2024, with civilian agencies alone accounting for $76.8 billion projected for fiscal 2025 (Statista, 2024; Washington Technology, 2024). To put this in perspective, even a conservative 5% productivity gain through AI adoption could yield over $5 billion in efficiency savings annually. The private sector has already demonstrated AI's potential: Microsoft's IDC report shows businesses strategically integrating generative AI are achieving an average ROI of 3.7 times their investment, with top performers reaching $10.30 ROI per dollar invested (IDC/Microsoft, 2025).

For small-government advocates and Silicon Valley entrepreneurs alike, this represents a massive opportunity. The federal government remains one of the largest software purchasers globally, yet agencies predominantly rely on hyperscaler offerings from Azure, AWS, and Google. Startups like OpenAI and Anthropic have struggled to achieve full authorization in federal environments, though some companies like Windsurf have broken through—demonstrating both the challenges and the appetite for innovation in government IT procurement.

### The AI Safety Perspective

AI safety advocates face a fundamental challenge that undermines their entire agenda: it's nearly impossible to get federal government employees to take AI risks seriously when they perceive these tools as mere "stochastic parrots" rather than the transformative technologies reshaping every other sector.

This isn't hypothetical. In conversations with federal officials about AI safety measures, I've repeatedly encountered a troubling pattern: those making decisions about AI governance often have minimal hands-on experience with the technology. They've read the reports, attended the briefings, but haven't spent hours using Claude to analyze complex datasets or watched GPT-4 write functional code in real-time. As the Department of Homeland Security noted in its AI safety initiatives, understanding AI capabilities firsthand is essential for developing appropriate safeguards (DHS, 2024).

The irony is palpable. We ask leaders at DOD, DHS, Commerce, and beyond to craft nuanced policies about AGI risks while denying them the opportunity to "feel the AGI" through daily use. It's like asking someone who's never driven to design traffic safety regulations—theoretically possible, but practically unwise.

### The State Capacity Vision

For state capacity advocates and abundance believers—those united by the conviction that technology can materially improve lives and that government must work more effectively—the current situation represents a tragic missed opportunity. Whatever your views on government size, the fact remains: much of federal work involves text manipulation, analysis, and synthesis. These happen to be exactly what LLMs excel at.

Consider the daily work of a typical federal policy analyst: reviewing hundreds of pages of public comments, synthesizing research across disciplines, drafting clear communications for diverse audiences, translating technical concepts for policymakers. These tasks, which might consume days or weeks, can be augmented and accelerated by AI tools that millions of Americans already use freely.

The White House's "Winning the Race: America's AI Action Plan" (July 2025) explicitly acknowledges this reality, calling for agencies to "ensure employees who could benefit have access to frontier LLMs and training." The House's managed Copilot rollout, reversing an earlier ban, signals that even the legislative branch recognizes the tide has turned.

## What AI Adoption Actually Requires (And Doesn't)

The path to universal federal AI access is blocked less by genuine technical barriers than by misconceptions, bureaucratic inertia, and misaligned incentives. Let's address each supposed obstacle with the clarity it deserves.

### The Training vs. Inference Distinction

Many security officials worry about risks like data leaks, prompt injection, and PII exposure—concerns that would be valid if agencies were training their own models. But this fundamentally misunderstands how agencies actually use AI. As someone who helped implement AI governance across federal agencies, I can attest: the vast majority of use cases involve inference, not training.

Most agency AI use resembles using Microsoft Word more than building a nuclear reactor. When a State Department analyst uses ChatGPT to help translate diplomatic cables, they're not teaching the model new languages—they're using capabilities that already exist. When a CDC researcher uses Claude to summarize public health studies, no model weights are being updated. The right frame is secure SaaS usage, not model development.

Existing control frameworks already address these patterns. NIST Special Publication 800-53 Revision 5 provides comprehensive security controls that map directly to inference-only usage. Its control families—Access Control (AC), Audit and Accountability (AU), Incident Response (IR), Planning (PL), System and Services Acquisition (SA)—cover the security requirements for LLM-as-a-service implementations (NIST, 2020).

### FedRAMP as the Model, Not the Exception

FedRAMP's evolution offers a blueprint for AI authorization. Established by OMB in 2011 and modernized through M-24-15 in 2024, FedRAMP provides reusable cloud security authorizations that agencies can leverage rather than duplicate. The July 2024 memorandum explicitly states: "FedRAMP will provide procedures for issuing a time-specific temporary authorization...that would allow Federal agencies to pilot the use of new cloud services that do not yet have a full FedRAMP authorization" (OMB, 2024).

This framework already contemplates AI services. The memo emphasizes automation, presumption of adequacy for authorized services, and machine-readable compliance artifacts. If we can authorize complex cloud infrastructures that handle classified data, surely we can authorize text generation services with appropriate controls.

### Debunking the Data Readiness Myth

One of the most pernicious myths blocking AI adoption is the belief that agencies need perfect data estates before deploying LLMs. This narrative, promoted by consultancies and vendors with data modernization services to sell, misunderstands how modern AI works.

Articles breathlessly declare that agencies "can't adopt AI until their data is AI-ready" (Code for America, 2024) or push sponsored content about "bridging the AI readiness gap" (FedScoop, 2024). A typical example from Nextgov insists agencies must achieve data perfection before AI deployment (Nextgov, 2024).

This is backwards. Commercial LLMs come pre-trained on massive datasets—OpenAI, Anthropic, and Google have invested billions creating models with impressive baseline capabilities. Early wins come from generic capabilities: summarization, drafting, code assistance, translation. No proprietary data required. No pristine data lakes necessary.

In my experience at OMB, I saw agencies paralyzed by the belief they needed perfect data before starting. Meanwhile, their employees could have been using ChatGPT to draft better briefing memos immediately. It's like refusing to use email until you've digitized every paper file—a category error that conflates different use cases.

What agencies do have is increasingly modern cloud infrastructure. Most major hyperscalers—Azure, AWS, Google Cloud Platform—have achieved FedRAMP authorization at numerous agencies. These platforms already offer cutting-edge models like GPT-4, Claude, Gemini, and open source alternatives. The pipes exist; we just need to turn on the water.

### Addressing the Parade of Objections

**"Hallucinations mean we can't use it."** This objection might have held water in 2022. Today, it's obsolete. Model reliability has improved dramatically, and more importantly, most federal use cases involve human-in-the-loop oversight. When a budget analyst uses Claude to help draft a Congressional justification, they're not blindly copying output—they're using AI as a thought partner. Emails don't send themselves. Memos require approval chains. Accountability lines remain crystal clear.

For coding applications, the safeguards are even more robust. Every competent development process includes code review, testing, and quality assurance. Whether a human or AI writes the initial code matters less than whether it passes tests and peer review. GitHub Copilot doesn't deploy code to production—developers do.

**"Security needs brand-new rules."** I've spent countless hours in meetings where security officials insisted AI required entirely novel control frameworks. When pressed for specifics about which existing controls don't apply to inference scenarios, the room typically goes quiet. The truth is that LLM usage maps cleanly to existing NIST 800-53 control families. Access Control still means access control. Audit logs still mean audit logs.

Yes, there are nuances—GPU architectures have different attack surfaces than traditional CPUs, and prompt injection represents a novel risk vector. But these are refinements to existing frameworks, not grounds for paralysis. No CISO would accept "we need brand new rules" as a reason to block email or web browsers in 2025.

**"Agencies need to define their use cases first."** GSA's AI Guide advises agencies to meticulously catalog use cases before adoption (GSA COE, 2025). This reflects outdated thinking from the machine learning era when you'd train specific models for specific tasks—a vision classifier, a sentiment analyzer, a recommendation engine.

LLMs are general-purpose tools. Requiring agencies to enumerate every possible use is like demanding they list every possible Excel formula before approving spreadsheet software. It's a bureaucratic exercise that mistakes motion for progress while preventing actual experimentation and learning.

I witnessed this firsthand during my time in government. Agencies would spend months crafting theoretical use case inventories while their private sector counterparts were already shipping AI-enhanced products. The requirement becomes a convenient excuse for inaction—a Sisyphean task that ensures agencies never quite get around to actual deployment.

**"Everything needs red teaming."** Red teaming has become the security theater of the AI age. While valuable for novel, high-risk implementations, demanding red team exercises for every ChatGPT deployment is like requiring penetration testing before installing Microsoft Office.

OpenAI's GPT-4 model card runs over 60 pages detailing capabilities, limitations, and safety measures. Anthropic publishes extensive documentation on Claude's training and safety protocols. For general-purpose usage, agency red teams are unlikely to discover vulnerabilities that escaped the thousands of researchers already probing these systems.

Academic research supports this skepticism. Feffer et al. from Carnegie Mellon found that red teaming exercises often suffer from "threat-model mismatch," disproportionately targeting "dissentive risks" (context-dependent harms like bias) over "consentive risks" (universally unacceptable outcomes like PII leakage). The result? Exaggerated refusals and "over-safety" that prevents beneficial uses while failing to address actual security concerns (Feffer et al., Carnegie Mellon University).

**"People need training."** As someone who led implementation of government-wide AI training and personally trained over 8,000 federal employees, I can say definitively: formal training is overrated. Have you attended internal government training? With rare exceptions, these sessions devolve into checkbox exercises that satisfy compliance requirements while teaching little of practical value.

The busy frontline staff who could most benefit from AI tools rarely have time to step away for multi-day training sessions. They learn the way everyone learns new software: by using it and sharing knowledge with colleagues. No one took a three-day course to learn Gmail.

During my time at OMB, we partnered with GSA and Stanford's Human-AI Interaction Lab to create world-class training. Even then, I had to fight constant attempts to water down content. Other offices wanted to red-line individual lesson plans, turning cutting-edge insights into bureaucratic pablum. At one point, the conflict escalated to the Office of the Federal CIO. I held firm—if Stanford professors were teaching federal employees, they'd do so without censorship. But I heard that after I returned to my home agency, the red-lining returned in force.

The obsession with formal training becomes another convenient delay tactic. "We can't deploy until everyone is trained" ensures deployment never happens.

## Evidence of Value: Federal Success Stories

While some agencies remain mired in analysis paralysis, pioneers across government are demonstrating what's possible when leadership prioritizes results over process.

### CDC: First-Mover Advantage Pays Off

The Centers for Disease Control and Prevention deserves recognition as the first federal agency to achieve enterprise-wide ChatGPT deployment in 2023. This wasn't a limited pilot or proof-of-concept—CDC made the tool available to its entire workforce with appropriate safeguards.

The results speak louder than any theoretical risk assessment: 1.2 million chats logged, an estimated 41,000 hours saved, and a remarkable 500% return on investment. As CDC's acting chief AI officer Travis Hoppe reported at FedScoop's FedTalks, employees are using ChatGPT for everything from analyzing epidemiological data to drafting public health communications. "With 81.47% ChatGPT market share, it leads in generative AI," Hoppe noted, highlighting how quickly the tool became indispensable (FedScoop, 2025).

What's particularly instructive about CDC's success is how they handled the rollout. Rather than spending years on hypothetical risk frameworks, they implemented practical controls: usage monitoring, data handling protocols, and clear guidance on appropriate use cases. Then they let their scientists and public health experts experiment and innovate.

### DHS: From Caution to Comprehensive Deployment

The Department of Homeland Security's journey illustrates how agencies can move from skepticism to sophisticated implementation. DHS launched DHSChat, now serving nearly 19,000 employees with enhanced legal and data protections. But the real innovation lies in their systematic approach to measuring impact.

Their GenAI Public Sector Playbook, which should be required reading for every federal CIO, documents tangible benefits across three pilot programs. Employees report saving an average of 30 minutes per day on routine tasks—time now redirected to mission-critical activities. As Secretary Alejandro Mayorkas stated, "This cutting-edge tool will help men and women across DHS draft vital reports, summarize critical information, develop new software, streamline administrative tasks and much more" (DHS, 2024).

What I find most compelling about DHS's approach is their willingness to publish detailed lessons learned. They acknowledge challenges—initial user hesitation, need for prompt engineering skills, integration with existing workflows—while demonstrating how each can be overcome through thoughtful implementation.

Even with Microsoft offering OpenAI GPT-4 in Azure at minimal cost on approved contracts in secure environments, DHS still faced 3-5 months of authorization delays. From a technical standpoint, integration with monitoring environments required perhaps a few days of engineering work. The paperwork consumed exponentially more time—a pattern I witnessed repeatedly across agencies where CISOs effectively pocket-vetoed progress through bureaucratic delays.

### State Department: Enhancing Diplomatic Effectiveness

State's deployment of StateChat to 45,000-50,000 of its 80,000 employees demonstrates AI's potential for mission enhancement. Foreign Service officers rotate positions every two to three years, requiring rapid familiarization with new countries, issues, and stakeholder networks. StateChat helps them get up to speed faster through intelligent querying of policy manuals and diplomatic history.

The numbers tell the story: State processes approximately 6,000 diplomatic cables daily. AI-assisted analysis doesn't replace human judgment but augments it, helping analysts identify patterns and surface relevant precedents. As CIO Kelly Fletcher acknowledged, successful adoption required "a huge amount of education and training"—though notably, this training focused on effective usage rather than endless risk assessments (State Magazine, 2024; FedScoop, 2024).

### Congressional Evolution: From Ban to Embrace

Perhaps no story better illustrates the inevitability of AI adoption than the House of Representatives' reversal. After banning Copilot in March 2024 due to data leakage concerns—a reasonable initial reaction—the House recognized that prohibition wasn't sustainable.

By September 2025, Speaker Mike Johnson announced a managed rollout of Microsoft Copilot with "heightened legal and data protections" for up to 6,000 staffers. The key insight: rather than maintaining a blanket ban while competitors gained AI advantages, the House chose to implement appropriate controls and move forward (Axios, 2025).

This evolution mirrors what I've seen across government. Initial fear gives way to curiosity, then cautious experimentation, and finally recognition that the benefits far outweigh manageable risks. The question isn't whether agencies will adopt AI, but whether they'll do so proactively or be dragged into the future.

## Concrete Policy Actions for Universal Access

The success stories prove federal AI adoption is possible. The question now is how to accelerate from pockets of excellence to universal access. Based on my experience implementing federal technology policy, here are five actionable proposals that could be implemented within the next year.

### A. Universal LLM Access Mandate: Creating Constructive Pressure

Within 180 days, require each CFO Act agency CIO to certify that all white-collar staff (GS-11 and above) have access to an enterprise LLM for brainstorming, summarization, research, drafting, and translation—or file a specific exception citing undue hardship with detailed justification.

The key innovation here is the accountability mechanism. Agencies claiming monetary restrictions must work with their OMB examiner to explain why $1 access offers from OpenAI, Anthropic, Google, and Microsoft are insufficient. OMB should publish these exception responses publicly, creating both time pressure and reputational incentives.

This approach leverages a fundamental insight about federal CIOs: they care deeply about their standing among peers and their future career prospects. No CIO wants to be publicly listed as the one blocking their workforce from tools every private sector employee takes for granted. The transparency creates constructive pressure for action while respecting legitimate agency-specific concerns.

The White House's AI Action Plan already provides top cover, explicitly mandating that agencies ensure employee access to frontier LLMs. This proposal simply operationalizes that mandate with teeth.

### B. Coding Assistants by Default: Modernizing Federal Software Development

Federal agencies spend billions annually on custom software development and data analysis. Meanwhile, private sector developers report 30-50% productivity gains using AI coding assistants. The disconnect is unconscionable.

Within 180 days, require CIO certification that any custom software effort on government-furnished equipment includes approved AI coding assistants (GitHub Copilot, Claude Code, Amazon CodeWhisperer, etc.) with non-training tenancy, audit logging, and standard SDLC gates—or document why such tools would impair the specific development effort.

These tools largely run locally with secure API connections through already-authorized cloud environments. Many are bundled with existing enterprise agreements. The technical barriers are minimal; the cultural resistance is not.

I've seen too many federal development teams coding like it's 2005 while their private sector counterparts leverage AI to ship features faster. This isn't about replacing developers—it's about amplifying their capabilities and freeing them to focus on architecture and problem-solving rather than boilerplate.

### C. Provisional ATO Authority: Breaking the Authorization Bottleneck

OMB M-24-15 already provides for 12-month FedRAMP-free trials under specific conditions. We should expand this to 24 months specifically for generative AI products using pre-trained models when:

- No customer data is used for model training
- Appropriate boundary and egress controls exist
- Comprehensive audit logging is enabled
- The agency CIO authorizes use for coding, assistance, and office automation
- A streamlined System Security Plan (SSP-lite) documents controls

This extended timeline recognizes the reality of federal procurement and authorization cycles. Twelve months sounds reasonable until you realize it takes six months just to get on an agency's roadmap. Twenty-four months provides breathing room for proper evaluation while maintaining urgency for permanent authorization.

The "SSP-lite" concept is crucial. Current authorization packages can run thousands of pages, much of it boilerplate. For inference-only SaaS offerings, we need documentation proportionate to actual risk.

### D. CISO Accountability: From Silent Veto to Transparent Decision-Making

Chief Information Security Officers wield enormous informal power through their ability to slow-roll authorizations. Even when cloud environments have FedRAMP High authorization and vendors offer AI services within those boundaries, CISOs can effectively pocket veto by simply not prioritizing the additional authorization.

Here's how to break this logjam:

1. FedRAMP identifies all current High and Moderate authorized systems that include approved generative AI APIs or components
2. Agencies with these authorizations report to OMB within 30 days
3. CISOs have 60 days to specify via the CISO Council what additional controls would prevent full AI service authorization
4. OMB publishes guidance addressing these concerns within 60 days
5. CISOs must provide updated authorizations within 60 days of guidance

The crucial element: if Claude Sonnet is available in a High AWS environment already authorized by FedRAMP at High, the CISO cannot arbitrarily restrict it to Moderate use. No more security theater where identical technical architectures receive different risk ratings based on CISO comfort levels.

This proposal respects CISOs' security responsibilities while preventing them from becoming innovation bottlenecks. Legitimate security concerns get addressed through the formal process. Foot-dragging becomes visible.

### E. Budget Line Items: Making AI Adoption Real

Money talks. In the Spring Budget Guidance, OMB should direct agencies to establish dedicated object classes for:

- Enterprise LLM subscriptions
- AI coding assistants
- Advanced features (code interpreter, retrieval augmented generation, agentic workflows)

Then require actual dollar amounts in IT spend portions of each agency's budget submission. This mirrors successful strategies from the Biden Administration's AI governance push but focuses on tool adoption rather than oversight infrastructure.

Budget requirements create powerful dynamics. To submit compliant budgets, agencies must make trade-offs explicit. CFOs get involved. Procurement offices engage. What starts as a compliance exercise becomes organizational commitment.

Small agencies should receive particular attention—they often have the most to gain from AI tools but the least capacity to navigate complex authorizations. A dedicated funding stream could provide them with pre-authorized, turnkey solutions.

## Closing: The Competence Imperative

We face a defining moment for American state capacity. While citizens routinely use AI to amplify their capabilities, too many federal employees work with digital tools from the last decade. This isn't just inefficiency—it's a competence crisis that undermines public trust and government effectiveness.

The paradox cuts deep: to govern AI wisely, policymakers must understand it viscerally. Yet we deny them the very access that would build this understanding. It's like asking judges to rule on internet law without letting them go online—theoretically possible but practically foolish.

When federal leaders experience firsthand how LLMs transform research, analysis, and communication, they make better decisions. They understand why a startup founder sees transformative potential. They grasp why safety researchers worry about capability jumps. They feel in their daily work what abstract briefings can never convey.

This transcends partisan dividing lines. Conservatives who champion government efficiency should celebrate tools that help workers do more with less. Progressives who believe in effective public services should embrace technologies that help agencies better serve citizens. Those worried about AI risks should want decision-makers who deeply understand the technology they're governing.

The path forward demands managed access with appropriate safeguards, not prohibition masquerading as prudence. We've proven it works—CDC, DHS, State, and others show the way. The frameworks exist. The successes mount. What remains is the will to universalize what pioneers have demonstrated.

Federal workers deserve the same tools that make their private sector counterparts more effective. Not eventually. Not after perfect frameworks. Now. Because every day of delay is another day American government falls further behind in the race to understand, govern, and deploy transformative AI.

Twenty years ago, the federal government helped pioneer email adoption. Today, we stand at another technological inflection point. The question isn't whether agencies will adopt AI—market forces and citizen expectations make that inevitable. The question is whether we'll lead this transformation or stumble into it apologetically.

America maintains its edge by using technology responsibly at scale. That requires federal workers who understand AI not as an abstract concept but as a daily tool. Provide modern infrastructure, measure real outcomes, iterate governance based on evidence rather than fear.

The tools exist. The frameworks exist. The success stories exist. What we need now is leadership with the courage to say: every federal knowledge worker deserves access to AI, and they deserve it now. Our national competitiveness and government effectiveness depend on closing the gap between AI's promise and government's reality.

In a world where AI shapes everything from commerce to national security, a government that doesn't use AI is a government that doesn't understand the future it's trying to shape. That's not just inefficient—it's dangerous. The time for pilot projects has passed. The era of universal federal AI access must begin.

## References

- Axios. (2025, September 17). Exclusive: Microsoft Copilot AI lands in the House. https://www.axios.com/2025/09/17/microsoft-ai-house-of-representatives
- CDC. (2024). CDC's Vision for Using Artificial Intelligence in Public Health. https://www.cdc.gov/data-modernization/php/ai/cdcs-vision-for-use-of-artificial-intelligence-in-public-health.html
- CNBC. (2025, August 4). OpenAI's ChatGPT to hit 700 million weekly users, up 4x from last year. https://www.cnbc.com/2025/08/04/openai-chatgpt-700-million-users.html
- Code for America. (2024). Getting Your Data Ready for AI. https://codeforamerica.org/news/getting-your-data-ready-for-ai/
- Department of Homeland Security. (2024). Artificial Intelligence at DHS. https://www.dhs.gov/ai
- Department of Homeland Security. (2025). DHS Generative AI Public Sector Playbook. https://www.dhs.gov/publication/dhs-generative-ai-public-sector-playbook
- Feffer, M., Sinha, A., Deng, W. H., Lipton, Z. C., & Heidari, H. (n.d.). Red-Teaming for Generative AI: Silver Bullet or Security Theater? Carnegie Mellon University.
- FedScoop. (2025). CDC official says generative AI already saved agency workers 41,000 hours. https://fedscoop.com/cdc-official-says-generative-ai-already-saved-agency-workers-41000-hours/
- FedScoop. (2024). From translation to email drafting, State Department turns to AI to assist workforce. https://fedscoop.com/state-department-ai-chatbot-email-drafting-northstar-famsearch/
- FedScoop. (2024). Bridging the AI readiness gap in government begins with trusted data. https://fedscoop.com/bridging-the-ai-readiness-gap-in-government-begins-with-trusted-data/
- GSA Centers of Excellence. (2025). AI Guide for Government: Identifying AI Use Cases in Your Organization. https://coe.gsa.gov/coe/ai-guide-for-government/identifying-ai-use-cases-in-your-organization/
- IDC/Microsoft. (2025). Generative AI's Strategic Revolution: How Tech Sector Partnerships Are Delivering Scalable ROI.
- National Institute of Standards and Technology. (2020). NIST Special Publication 800-53 Revision 5: Security and Privacy Controls for Information Systems and Organizations. https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final
- Nextgov. (2024, September). How to be data ready for AI adoption. https://www.nextgov.com/ideas/2024/09/how-be-data-ready-ai-adoption/399417/
- Office of Management and Budget. (2024). M-24-15: Modernizing the Federal Risk and Authorization Management Program (FedRAMP). https://bidenwhitehouse.archives.gov/omb/management/ofcio/m-24-15-modernizing-the-federal-risk-and-authorization-management-program-fedramp/
- Office of Management and Budget. (2025). M-25-22: Eliminating Barriers for Federal Artificial Intelligence Use and Procurement.
- State Magazine. (2024, December 1). AI in Action. https://statemag.state.gov/2024/12/1224feat03/
- Statista. (2024). Federal government information technology (IT) expenditure in the United States from FY 2011 to FY 2025. https://www.statista.com/statistics/554000/united-states-federal-it-expenditure-by-investment-significance/
- The Cognitive Revolution. (2025). Dean W. Ball on America's AI Action Plan & 4 Months at the White House [Podcast episode]. https://www.cognitiverevolution.ai/dean-w-ball-on-americas-ai-action-plan-4-months-at-the-white-house/
- The Cognitive Revolution. (2025). Jake Sullivan on Navigating AI Uncertainty and Managing Competition with China [Podcast episode].
- Washington Technology. (2024, October 7). Federal civilian IT spending set to surge in fiscal 2025. https://www.washingtontechnology.com/opinion/2024/10/federal-civilian-it-spending-set-surge-fiscal-2025/400096/
- White House. (2025, July 23). Winning the Race: America's AI Action Plan. https://www.whitehouse.com/insight-alert/white-house-unveils-comprehensive-ai-strategy-winning-race-americas-ai-action-plan
