# Source
EPA `use_cases` inventory for the Environmental Protection Agency (`EPA-2025-ai-inventory.csv`). The raw file parses to 29 data rows, and the SQLite load also contains 29 EPA rows. I did not see a row-count or delimiter loss issue.

# Counts
- Source rows: 29
- Loaded DB rows: 29
- Tagged rows: 29
- Untagged rows: 0

# Findings
- The load is structurally consistent, but a few tag assignments drift from the source meaning.
- `8958` / `Microsoft Power Automate (custom document processing model)`: the source describes a document extraction workflow for utility bills, and the row is classified as `Classical/Predictive Machine Learning`. The tag set marks it as `product_deployment`, `general_llm`, and `is_generative_ai=1`, which is directionally wrong for this use case. The product label also collapses this to `Custom In-House AI`, which obscures that the source names Microsoft Power Automate.
- `8961` / `Briefcam`: the source clearly describes a computer-vision surveillance review tool. The `ai_sophistication=computer_vision` tag fits, but the row is stored as a `custom_system` with no product record, even though the source reads like a commercial product deployment rather than a bespoke EPA-built system.
- Most other EPA rows look directionally aligned. For example, the Brownfields drafting and response-to-comments use cases are correctly treated as generative-AI style drafting workflows, and the RCRA/PA rows are tagged as classical ML with training and risk documentation.

# Recommended follow-up
- Retag `8958` away from generative/LLM categories and restore the Microsoft/Power Automate product identity if that is available in the product catalog.
- Review `8961` for commercial-product handling so the entry type and product mapping better reflect Briefcam as a vendor tool rather than an internal custom system.
