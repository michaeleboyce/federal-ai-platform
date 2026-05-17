# WS2 hierarchy follow-up — notes

## Summary

- 62 decisions total
- 9 `add_product` (vendor umbrellas)
- 53 `add_hierarchy_edge`
- All 55 input candidates get parented (some go to umbrellas, some chain through
  intermediate vendor SKUs like AWS or GCP).

## Umbrella products proposed

| Umbrella | Vendor | Children parented this pass |
|---|---|---|
| Amazon | Amazon | 2 (AWS, Alexa) |
| Amazon Web Services | Amazon | 11 (Q, Bedrock, Kendra, Lex, Rekognition, Textract, Transcribe, Translate, Comprehend, SageMaker, Connect) |
| Google | Google | 14 (Gemini, NotebookLM, Workspace, GCP, Translate, Maps, Lens, Pixel, Chrome GenAI, Colab, Coral TPU, Earth Engine, News Brief, reCAPTCHA) |
| Microsoft | Microsoft | 13 (M365, Azure Platform, Power Platform, Dynamics 365, GitHub Copilot, Edge, Discovery, HoloLens, ScreenSketch, Skype, Viva, SSMS, Visual Studio) |
| Thomson Reuters | Thomson Reuters | 4 (Westlaw AI, CoCounsel, ProLaw, CLEAR) |
| ServiceNow | ServiceNow | 2 (Now Assist, ITOM Predictive AIOps) |
| Cisco | Cisco | 2 (ISE, Secure Network Analytics) |
| Salesforce | Salesforce | 3 (Einstein, Slack, Tableau) |
| Adobe | Adobe | 1 (Creative Cloud Suite) |

## Edges by parent family (53 total)

- Google: 14
- Microsoft: 13
- Amazon Web Services: 11
- Thomson Reuters: 4
- Salesforce: 3
- Amazon: 2 (AWS, Alexa)
- ServiceNow: 2
- Cisco: 2
- Adobe: 1
- Google Earth Engine: 1 (Wetlands Classifier sub-product)

## Depth analysis (CTE cap ≤ 5)

Deepest chains created:
- `Azure OpenAI → Microsoft Azure Platform → Microsoft` = depth 3
- `Google Vertex AI → Google Cloud Platform → Google` = depth 3
- `Google Agentspace → Google Vertex AI → Google Cloud Platform → Google` = depth 4
- `Microsoft 365 Copilot → Microsoft 365 → Microsoft` = depth 3
- `Google Earth Engine Wetlands Classifier → Google Earth Engine → Google` = depth 3

All comfortably under the dashboard's 5-hop limit.

## Things I explicitly did NOT propose

- **GitHub Copilot → Microsoft 365 Copilot.** Prior pass explicitly removed
  this. Parented GitHub Copilot directly to `Microsoft` instead.
- **NotebookLM → Gemini.** Prior pass explicitly removed this (model-use
  ≠ sub-SKU). Parented NotebookLM directly to `Google`.
- **Microsoft Edge → Microsoft 365.** Charter explicitly flagged Edge as
  separately licensed. Parented Edge directly to `Microsoft`.
- **IBM Watson → some IBM umbrella.** Input lists IBM Watson as orphaned,
  but the charter scope doesn't include adding a top-level "IBM" umbrella
  (IBM has many divisions; Watson is already the canonical IBM-AI parent
  via the existing `IBM ARGOS / CoreDF / watsonx Code Assistant → IBM Watson`
  edges). Left IBM Watson parent-less. If reviewer wants an `IBM` umbrella,
  it's a follow-up.
- **LexisNexis → some umbrella.** LexisNexis is itself a vendor-level row
  with existing children (Lexis+ AI, NexisXplore, LexisNexis Risk
  Solutions). No higher-level RELX/Reed Elsevier umbrella in scope. Left as-is.

## Caveats / reviewer notes

- The two `Amazon Web Services`-vendored catalog rows (Amazon Connect,
  AWS Translate) will have their `vendor` field unchanged but now sit
  under the new `Amazon Web Services` umbrella product. That's expected.
- `Amazon Q` has alias `AWS Q` and is sometimes branded as "Amazon Q" /
  "Q Developer" / "Q Business" — keeping it under AWS as a peer to
  Bedrock matches Amazon's current AWS marketing org chart.
- Created an `Amazon` top-level on top of `Amazon Web Services` to keep
  Alexa (consumer hardware/voice) separate from AWS (cloud). If the
  integration script prefers a flat structure, the `Amazon → AWS` edge
  can be dropped and AWS made top-level — that's an integration-time
  call.
- Catalog has `Google Cloud Platform` with product_type=`general_llm` and
  is_generative_ai=1, which seems mis-tagged. Out of scope for WS2 (a
  product-type fix is WS3/integration territory), but flagging.
- All edges are confidence=high except `Microsoft Discovery → Microsoft`
  (medium — niche product) and `Google News Brief → Google` (medium —
  branding is fuzzy).
