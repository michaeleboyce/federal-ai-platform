# Rubric v2 — corrections from QC round 1 (2026-07-04)

Round-1 QC (406 rows, frontier judges): 22 overturns, 5.4%, ALL overcalls
(toward AI), zero undercalls across 217 judged not_ai rows. v2 = v1 plus
these boundary rules, each anchored to an actual overturned row:

1. "AI" in the name is NOT evidence when the service monitors, hosts,
   distributes, or administers AI rather than shipping it:
   - observability OF AI apps -> not_ai (New Relic "AI Monitoring")
   - container/compute hosting FOR AI workloads -> not_ai ("Azure AI -
     Container Platform")
   - marketplaces/app stores distributing AI apps -> not_ai ("H2O AI App
     Store")
   - admin consoles for ML products -> not_ai ("SentinelOne Management
     Console")
   - data/signals layers that power AI elsewhere -> not_ai (Microsoft
     "Substrate Intelligence Platform")
2. Host-package context is NOISE (v1 rule 1, now strict): never attribute
   the host's AI capability to a named sub-service with no independent AI
   attribution ("SkyNET 2.0", "THEIA" on a video-exploitation host; "DFIR
   services" on an ML-security host).
3. Obscure/unverifiable service names NEVER get ai_featured from name
   fragments like "Intelligence", "Cognition", "Personalization" alone ->
   not_ai, confidence low ("Cloud Input Intelligence", "Cognition Plugins",
   "IDEAs Personalization Service").
4. Solutions/templates PACKAGED ON a GenAI platform are ai_featured, not
   core_ai ("ATO In a Box" on Ask Sage).
5. Products whose engine happens to be ML but whose category is something
   else (bot mitigation, identity) are ai_featured, not core_ai
   ("reCAPTCHA Enterprise", "1Kosmos BlockID").
6. Query/search engines with a bolt-on NL/GenAI translation layer are
   ai_featured, not core_ai ("Tanium Ask").
