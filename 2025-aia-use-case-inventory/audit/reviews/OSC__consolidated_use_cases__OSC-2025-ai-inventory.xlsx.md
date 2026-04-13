# Source
`OSC-2025-ai-inventory.xlsx` / `consolidated_use_cases` / U.S. Office of Special Counsel

# Counts
- Source rows: 20 data rows, 1 header row, 0 blank rows.
- Loaded DB rows: 20.
- Row count matches the workbook, and the source order appears preserved in the database (`id` 506-525).

# Findings
- No parsing or schema issues surfaced in the workbook load. The five source columns map cleanly to the consolidated rows, and the `Agency Use (Y/N)?` / license fields were preserved as expected.
- Tagging is mostly directionally consistent, but a few rows look too coarse or arguably misclassified:
  - `id 515` (`Creating visual representations of data sets for reports or presentations using AI.`) is tagged `product_capability=data_viz` and `ai_sophistication=general_llm`. The capability fits, but `general_llm` looks broad for a Tableau/Julius-style analytics workflow.
  - `id 522` (`Curating news articles and updates based on user preferences using AI.`) is tagged `ai_sophistication=classical_ml`. That is plausible for recommendation/ranking, but the row reads more like content curation/search than a clear classical-ML example.
  - `id 510` (`Editing images, videos, or other public affairs materials using AI.`), `id 519` (`Identifying and cataloging items in a storage room using AI-driven image recognition.`), and `id 523` (`Planning travel routes using AI-driven map applications.`) have blank `product_capability` tags even though the source verbs are specific enough to map to obvious capabilities. These blanks make the tagging less useful than the rest of the file.
- The strongest positive signal is the Microsoft Copilot rows (`id 508, 512-514, 516`) which are tagged consistently as LLM / enterprise-wide / inference-only and match the source descriptions.

# Recommended follow-up
- Review the blank `product_capability` assignments for the image editing, image recognition, and travel-routing rows.
- Spot-check whether the `general_llm` and `classical_ml` labels should be narrowed for the remaining non-Copilot rows, especially `id 515` and `id 522`.
