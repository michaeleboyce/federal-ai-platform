# Public Verification Note

## Scope
This note records the public-source checks completed during the audit and points to the downloaded evidence in `audit/downloads/`.

## Downloaded evidence
- [dhs_ai_deep_dive.html](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/downloads/dhs_ai_deep_dive.html)
- [dhs_traveler_verification_service.html](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/downloads/dhs_traveler_verification_service.html)
- [dhs_cbp_translate_pia.html](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/downloads/dhs_cbp_translate_pia.html)
- [dhs_social_media_monitoring_pia.html](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/downloads/dhs_social_media_monitoring_pia.html)
- [doe_inventory_page.html](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/downloads/doe_inventory_page.html)
- [doe_nrel_elm.html](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/downloads/doe_nrel_elm.html)
- [nasa_inventory_page.html](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/downloads/nasa_inventory_page.html)
- [va_inventory_page.html](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/downloads/va_inventory_page.html)

## Verified signals
- DHS public documentation explicitly says its updated inventory includes `158 active AI use cases` and names specific use cases such as `CBP Translate`, `Babel`, `Passive Body Scanner`, `Video Analysis Tool`, and `Hurricane Score`. This supports the existence of those entries in the local inventory and confirms that at least part of the DHS row set has strong public backing.
- The downloaded DHS PIA landing pages directly align with local DHS rows for `Traveler Verification Service`, `CBP Translate`, and public social-media monitoring.
- DOE’s inventory page states that the `2025 Department of Energy Artificial Intelligence (AI) Use Case Inventory` is publicly downloadable and describes the inventory as a comprehensive view of DOE’s AI use.
- The downloaded public GitHub page for the `NatLabRockies/elm` repository says `ELM is a collection of utilities to apply Large Language Models (LLMs) to energy research` and references an `energy_wizard` chatbot example. That is useful corroboration for DOE/NREL-style LLM energy-research entries.
- NASA’s public inventory page clearly exists and exposes downloadable AI inventory spreadsheets.
- VA’s public inventory page states that the `2025 inventory includes 367 AI use cases in the Individual AI Inventory and 13 AI Use Cases in the Consolidated AI Inventory`. It also highlights named use cases including `VA GPT`, `AI-Assisted Software Development`, `STORM`, and the `Payment Redirect Fraud (PRF)` model.

## Limits
- This pass does not prove every single row has a corresponding public page. Many rows are internal, pilot, or low-detail inventory entries that do not have a standalone public artifact beyond the agency inventory itself.
- `HHS` returned `403` during direct download, so HHS public verification was limited to search results and the known official inventory URL rather than a saved local copy.
- The inventory-linked `dhs-gov/tasr_lda` GitHub URL returned `404` during download and should be rechecked manually in case the repository moved or the link in the inventory is stale.

## Recommended follow-up
- Use the downloaded DHS, DOE, NASA, and VA pages as anchor evidence for the public-verification portion of the audit.
- For agencies with high-impact or controversial rows, prioritize public verification against agency inventory pages, PIAs, and product/program pages before drawing stronger factual conclusions from auto-tags.
