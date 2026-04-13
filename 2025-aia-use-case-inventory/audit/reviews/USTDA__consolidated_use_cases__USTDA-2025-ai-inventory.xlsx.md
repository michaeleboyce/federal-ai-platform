# Source
USTDA `USTDA-2025-ai-inventory.xlsx` (`consolidated_use_cases`)

# Counts
- Source sheet has 20 data rows after the header.
- Loaded DB table has 20 rows for this source.
- Parsing looks structurally clean: no blank source rows, and the five expected columns were captured for every row.

# Findings
- The overall row mapping is consistent, but the tags are somewhat coarse in a way that may understate the source's product mix. Most rows were tagged `generic_use_pattern` with `use_type=administrative`, which fits the sheet, but many capability tags are only approximate or left blank even when the use case is specific.
- Row 576 is the clearest suspicious record. The source says `Apple iPhone, Google Pixel` as commercial examples and `Apple iPhone, Lookout for mobile security` as the product used. The DB keeps that row, but it is tagged without a product capability and with `product_id=null`, which makes the commercial linkage look incomplete even though the source names a specific product.
- Several rows that mention named products are still tagged as generic classical-ML patterns rather than product-specific or generative tooling. Examples: row 557 (`Reclaim.AI`), row 559 (`Otter.ai`), row 561 (`Adobe Firefly`), and row 567 (`Microsoft Copilot`). These are directionally plausible, but the tagging is not especially precise.
- Row 563 and row 565 are the strongest cases where the labels look directionally correct: `ChatGPT`-based drafting and summarization were tagged as `general_llm` with frontier-model flags, which matches the source better than the classical-ML rows above.
- Row 568 is also reasonable: code generation was tagged as a coding assistant with GitHub Copilot flagged, which matches the source intent.

# Recommended follow-up
- Review the product-to-tag mapping for rows with named tools but blank or generic capability tags, especially row 576.
- If the tagging standard expects product-level specificity, consider tightening the capability labels for rows 557, 559, 561, and 567 so the output better distinguishes embedded software products from generic task patterns.
