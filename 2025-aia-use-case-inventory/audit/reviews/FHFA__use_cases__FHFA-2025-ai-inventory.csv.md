# Source
`FHFA-2025-ai-inventory.csv` (`FHFA`, Federal Housing Finance Agency)

# Counts
- Source rows: 16
- Loaded DB rows: 16
- Parsed rows preserved: yes, including the retired placeholders and the long section header text in the raw CSV

# Findings
- Row count matches exactly, and I did not see evidence of row loss or row splitting in the DB load.
- The source meaning is mostly preserved, but several vendor-backed deployments look directionally mis-tagged as `custom_system` instead of product/COTS deployments.
- `Virtual Acquisition Office (VAO) Ally` is the clearest example: the source says it was `Purchased from a vendor` with vendor/system name `VAO Ally`, but the loaded tags mark it `custom_system` with `general_llm`. That looks inconsistent with the source record’s product-deployment framing.
- `Workflow automation and predictive analytics using ServiceNow` is tagged as `product_deployment`, which is directionally right, but the same record is also tagged `general_llm` even though the source AI classification is `Classical/Predictive Machine Learning` and the narrative emphasizes workflow automation/predictive analytics rather than an explicit LLM use case.
- Other vendor-backed FHFA records like `Citrix`, `SQL Server`, `Kiteworks`, `Commonlook Online`, and `Flowmon` are also loaded as `custom_system`. Those may be defensible for some internal tagging rules, but they read more like purchased products than custom-built systems, so the tag direction is at least suspicious.
- The retired entries appear to be loaded as mostly empty records, which matches the source. The odd punctuation in `Analytics,, Search, Queries and LLM integration for data management on Oracle` is present in the raw CSV and does not look like a parsing error.

# Recommended follow-up
- Recheck the tag rules for vendor-supplied tools versus custom systems, especially for `VAO Ally`, `ServiceNow`, `Citrix`, `SQL Server`, `Kiteworks`, `Flowmon`, and `Commonlook Online`.
- Confirm whether `general_llm` should be used only when the source explicitly describes an LLM, or whether vendor-branded AI features are enough.
