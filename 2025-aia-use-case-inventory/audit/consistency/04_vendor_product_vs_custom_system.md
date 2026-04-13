# Check
`vendor_product_vs_custom_system`

# Method
Queried `use_cases` joined to `use_case_tags` and `agencies` in `federal_ai_inventory_2025.db`.

Primary filter: rows tagged `entry_type = 'custom_system'` where the source `development_type` says `Purchased from a vendor` or equivalent.
Secondary spot check: rows where the source clearly names a commercial product or vendor, or where the linked product field is `Custom In-House AI` while the source still says vendor-purchased.

# Findings
The pattern is broad enough to be a real tagging issue, but not every vendor-backed row is necessarily wrong. I found `452` `custom_system` rows across `22` agencies whose source development type says the system was purchased from a vendor. The concentration is highest in `DOJ` (`137`), `VA` (`100`), `DOE` (`51`), `HHS` (`44`), and `DHS` (`40`), which suggests the issue is systematic rather than isolated.

The clearest mismatches are rows where the source itself names a commercial product or vendor, yet the record still lands in `custom_system`. One exact linked-product mismatch also appears: `State` row `10285` is tagged `custom_system` and has `cots_product_name = Custom In-House AI`, even though the source says `Purchased from a vendor` and names `Microsoft` / `DOS-O365`.

# Examples
| Agency | Row ID | Source signal | Loaded result |
| --- | ---: | --- | --- |
| DHS | 7628-7630 | Source titles are `Commercial Generative AI for Text Generation (AI Chatbot)`, `...Image Generation`, and `...Code Generation` | `custom_system` |
| DOE | 7885 | `vendor_name = Vectra`, `development_type = Purchased from a vendor` | `custom_system` |
| DOE | 7887 | `vendor_name = PassiveLogic`, source uses a vendor-built building controls product | `custom_system` |
| DOE | 7889 | `vendor_name = Microsoft`, source names `APT Analytics` | `custom_system` |
| HHS | 9194 | `use_case_name = Builder Buddy`, `vendor_name = Credal`, `development_type = Purchased from a vendor` | `custom_system` |
| EPA | 8961 | `use_case_name = Briefcam`, which is a named commercial product | `custom_system` |
| State | 10285 | `development_type = Purchased from a vendor`, `vendor_name = Microsoft`, `system_name = DOS-O365`, `cots_product_name = Custom In-House AI` | `custom_system` |

# Recommended follow-up
Relabel the obvious commercial-product rows to `product_deployment` where the source names a vendor product or explicitly says the system was purchased from a vendor.

Keep `custom_system` only for rows that are genuinely internal builds or substantial in-house customizations, and audit the product-mapping rules that collapse vendor-branded rows into `Custom In-House AI`.
