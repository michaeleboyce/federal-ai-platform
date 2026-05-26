# Placeholder Products: Vendor-as-Product Classification

All products where `LOWER(TRIM(canonical_name)) == LOWER(TRIM(vendor))`. Classified as:
- **enterprise**: multi-product company; the bare-vendor row is a catch-basin and source edges should be redirected to specific products.
- **single_product**: the company name IS the product (or so closely synonymous in the inventory context that no retag is warranted).

Total placeholders: **96** | Enterprise: **11** | Single-product: **85**

| Product ID | Name | Vendor | Total edges | Class | Reasoning |
|---|---|---|---|---|---|
| 19801 | Microsoft | Microsoft | 141 | enterprise | Sibling products include Azure AI Document Intelligence, Azure AI Foundry, Azure AI Translator, Azure AI Vision / Document Intelligence, Azure Data Factory, Azure OpenAI (45 total) — bare "Microsoft" row is a catch-basin |
| 19802 | Google | Google | 55 | enterprise | Sibling products include Gemini, Google Agentspace, Google Calendar, Google Chrome Generative AI, Google Cloud Platform, Google Cloud Vision (20 total) — bare "Google" row is a catch-basin |
| 19797 | Adobe | Adobe | 18 | enterprise | Sibling products: Adobe Creative Cloud Suite, Adobe Firefly, Adobe Photoshop, Adobe Premiere Pro, Adobe Sensei — bare "Adobe" row absorbs edges that belong to Acrobat, Firefly, Photoshop, etc. |
| 19054 | Grammarly | Grammarly | 16 | single_product | No sibling products; Grammarly the company is essentially its flagship writing-assistant product |
| 19803 | Amazon | Amazon | 15 | enterprise | Sibling products include AWS Bedrock, AWS Kendra, AWS Lex, AWS Rekognition, AWS Textract, AWS Transcribe (12 total) — bare "Amazon" row is a catch-basin |
| 19064 | Databricks | Databricks | 14 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19061 | Splunk | Splunk | 12 | enterprise | On explicit enterprise list — Splunk offers Enterprise Security / SOAR / Observability which source text often references; no siblings in catalog yet but vendor is clearly multi-product |
| 19796 | Thomson Reuters | Thomson Reuters | 11 | enterprise | Sibling products: CoCounsel, ProLaw, Thomson Reuters CLEAR, Westlaw AI — bare "Thomson Reuters" row absorbs Westlaw/CLEAR/Practical Law edges |
| 19186 | Credal | Credal | 10 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19189 | Relativity | Relativity | 9 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19365 | LexisNexis | LexisNexis | 8 | enterprise | Sibling products: Lexis+ AI, Lexis+ Protege, LexisNexis Risk Solutions, NexisXplore — bare "LexisNexis" row absorbs Accurint/Lexis+/CLEAR-style edges |
| 19079 | Sprout Social | Sprout Social | 7 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19059 | Meltwater | Meltwater | 6 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19063 | Palo Alto Networks | Palo Alto Networks | 5 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19176 | Veritone | Veritone | 5 | enterprise | Sibling products: Veritone Illuminate — bare vendor row is a placeholder |
| 19371 | Medallia | Medallia | 5 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19084 | Zoom | Zoom | 4 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19345 | Hyperscience | Hyperscience | 4 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19674 | Vyond | Vyond | 4 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19080 | FS Pro | FS Pro | 3 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19086 | Alteryx | Alteryx | 3 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19156 | Qualtrics | Qualtrics | 3 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19182 | Informatica | Informatica | 3 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19184 | Chainalysis | Chainalysis | 3 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19219 | Citrix | Citrix | 3 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19243 | Flashpoint | Flashpoint | 3 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19344 | HeyGen | HeyGen | 3 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19419 | Penlink | Penlink | 3 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19451 | Tenable | Tenable | 3 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19799 | Cisco | Cisco | 3 | enterprise | Sibling products: Cisco Identity Services Engine, Cisco Secure Network Analytics — bare vendor row is a placeholder |
| 19062 | Zscaler | Zscaler | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19071 | WellSaid Labs | WellSaid Labs | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19076 | Poolside | Poolside | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19077 | Synthesia | Synthesia | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19078 | Canva | Canva | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19081 | Asana | Asana | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19085 | BioRender | BioRender | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19090 | SentinelOne | SentinelOne | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19091 | Wiz | Wiz | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19092 | Magnet Forensics | Magnet Forensics | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19135 | Hootsuite | Hootsuite | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19171 | Verkada | Verkada | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19245 | Dynatrace | Dynatrace | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19267 | Amped Software | Amped Software | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19369 | Lookout | Lookout | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19445 | Sprinklr | Sprinklr | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19450 | Tabnine | Tabnine | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19662 | DRUID AI | DRUID AI | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19663 | Supportbench | Supportbench | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19710 | Pyramid Analytics | Pyramid Analytics | 2 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19056 | Calendly | Calendly | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19082 | Monday.com | monday.com | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19103 | AttackIQ | AttackIQ | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19110 | BriefCatch | BriefCatch | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19121 | Critical Mention | Critical Mention | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19123 | Descript | Descript | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19124 | Dun & Bradstreet | Dun & Bradstreet | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19130 | FirstTwo | FirstTwo | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19131 | Flock Safety | Flock Safety | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19134 | Harvey | Harvey | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19139 | LaserAI | LaserAI | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19144 | Mark43 | Mark43 | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19147 | NetDocuments | NetDocuments | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19159 | Rank One Computing | Rank One Computing | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19164 | Spokeo | Spokeo | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19207 | Whooster | Whooster | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19220 | Kiteworks | Kiteworks | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19223 | SumTotal | SumTotal | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19226 | Emerald Innovations | Emerald Innovations | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19242 | Cohesity | Cohesity | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19244 | AveriSource | AveriSource | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19247 | ID.me | ID.me | 1 | single_product | No siblings; ID.me is the company's identity-verification product |
| 19252 | ProcureSight | ProcureSight | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19255 | GAIA AI | GAIA AI | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19293 | CaseGuard | CaseGuard | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19300 | Clearview AI | Clearview AI | 1 | single_product | No siblings; Clearview AI is the company's facial-recognition product |
| 19304 | CrewAI | CrewAI | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19354 | Illumio | Illumio | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19357 | iProov | iProov | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19361 | Lasso Security | Lasso Security | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19418 | PassiveLogic | PassiveLogic | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19428 | Recorded Future | Recorded Future | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19430 | Rekor | Rekor | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19673 | CWTSatoTravel | CWTSatoTravel | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19675 | Mural | Mural | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19684 | NaturalReader | NaturalReader | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19686 | RedSeal | RedSeal | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19701 | Cogitativo | Cogitativo | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19712 | Pingoo.AI | Pingoo.AI | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19740 | RapidAI | RapidAI | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19775 | ReflexAI | ReflexAI | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19791 | Lyssn | Lyssn | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19792 | CareCentra | CareCentra | 1 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19224 | OneReach.ai | OneReach.ai | 0 | single_product | No sibling products in catalog — the company name is effectively the product |
| 19798 | ServiceNow | ServiceNow | 0 | enterprise | Sibling products: ServiceNow IT Operations Management (ITOM) Predictive AIOps, ServiceNow Now Assist — bare vendor row is a placeholder |
| 19800 | Salesforce | Salesforce | 0 | enterprise | Sibling products: Salesforce Einstein, Slack, Tableau — bare vendor row is a placeholder |