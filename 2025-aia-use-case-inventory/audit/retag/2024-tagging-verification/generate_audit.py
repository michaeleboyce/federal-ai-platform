"""
Phase B auditor script — generates sample_audit_raw.csv from sample_input.csv.
Each row is hand-assessed below based on the narrative text.
"""
import csv
import os

OUTDIR = os.path.dirname(os.path.abspath(__file__))
OUTPATH = os.path.join(OUTDIR, "sample_audit_raw.csv")

# Each tuple: (use_case_id_2024, agency_abbreviation, use_case_name,
#              verdict_is_generative_ai, verdict_ai_sophistication,
#              verdict_deployment_scope, verdict_entry_type, verdict_tool,
#              notes, auditor_confidence)

ROWS = [
    # -----------------------------------------------------------------------
    # 34168 DHS/CBP — Port of Entry Risk Assessments
    # Narrative: classical risk-assessment ML on trade/travel data, CBP-scope
    # is_generative_ai=0 correct; classical_ml correct; bureau correct;
    # custom_system correct; no named product → correct
    (34168, "DHS", "Port of Entry Risk Assessments",
     "correct", "correct", "correct", "correct", "correct",
     "Risk assessment ML pipeline on trade/travel data. No product named. All tags align.",
     "high"),

    # 34184 DHS/CBP — ERNIE
    # Narrative: radiation portal monitor threat detection, real-time risk assessment
    # classical_ml correct; bureau correct; custom_system correct; is_cots=1 but
    # no vendor named in narrative — tool_product_name blank → correct (no vendor in text)
    (34184, "DHS", "ERNIE",
     "correct", "correct", "correct", "correct", "correct",
     "Radiation portal ML model, classical pattern. is_cots=1 but no vendor name in narrative — tool blank is acceptable.",
     "high"),

    # 34189 DHS/CBP — Cyber Threat Analysis (Recorded Future)
    # Narrative: 'Recorded Future' is named in the use_case_name itself!
    # entry_type=custom_system but this is clearly a commercial product (Recorded Future).
    # Should be product_deployment. tool_product_name is blank but name is in title.
    # is_generative_ai=0 correct; ai_sophistication=classical_ml — debatable,
    # cyber threat intel is NLP-heavy but classical_ml is defensible.
    # entry_type=custom_system is incorrect — "Recorded Future" is a named commercial product.
    # verdict_tool=missing — Recorded Future is named in use_case_name but tool_product_name blank.
    (34189, "DHS", "Cyber Threat Analysis (Recorded Future)",
     "correct", "correct", "correct", "incorrect", "missing",
     "Recorded Future is named in use_case_name — this is a commercial product deployment, not custom_system. tool_product_name should be 'Recorded Future'. entry_type incorrect.",
     "high"),

    # 34190 DHS/CBP — Vault Access Log (SPVAA)
    # Narrative: facial matching / biometrics — this is computer_vision not classical_ml.
    # "Leverages DHS facial matching technologies" — CV/biometrics.
    # is_generative_ai=0 correct; classical_ml should be computer_vision → off_by_one;
    # bureau correct; custom_system correct; no product named → correct
    # architecture_type=rag_pipeline is suspicious for facial matching but not audited here.
    (34190, "DHS", "Vault Access Log (SPVAA)",
     "correct", "off_by_one", "correct", "correct", "correct",
     "Narrative explicitly says 'facial matching technologies' — computer_vision is a better fit than classical_ml. off_by_one.",
     "high"),

    # 34192 DHS/CISA — CISAChat
    # Narrative: LLM-based internal chatbot with RAG. Generative AI is clear.
    # is_generative_ai=1 correct; general_llm correct; bureau correct;
    # bespoke_application correct; no named vendor in narrative → tool blank correct
    (34192, "DHS", "CISAChat",
     "correct", "correct", "correct", "correct", "correct",
     "Internal GenAI RAG chatbot, clearly LLM. All tags align.",
     "high"),

    # 34198 DHS/CISA — Advanced Network Anomaly Alerting
    # Narrative: probabilistic models, automated alerting on network data, classic ML
    # is_generative_ai=0 correct; classical_ml correct; bureau correct;
    # custom_system correct; no product → correct
    (34198, "DHS", "Advanced Network Anomaly Alerting",
     "correct", "correct", "correct", "correct", "correct",
     "Probabilistic anomaly detection pipeline. Classical ML pattern. All tags align.",
     "high"),

    # 34210 DHS/DHS — Commercial Generative AI for Image Generation
    # Narrative: DHS employees using commercial GenAI for image generation (DALL-E style)
    # is_generative_ai=1 correct (explicitly generative image AI);
    # ai_sophistication=general_llm — image gen is more computer_vision/diffusion but
    # general_llm is commonly used for multimodal GenAI; debatable but off_by_one acceptable
    # department correct; generic_use_pattern correct (enterprise policy allowing commercial tools)
    # No specific vendor named in narrative → tool blank correct
    (34210, "DHS", "Commercial Generative AI for Image Generation",
     "correct", "off_by_one", "correct", "correct", "correct",
     "Image generation GenAI — technically computer_vision/diffusion, but general_llm is used for GenAI broadly. off_by_one rather than incorrect. Department scope and generic_use_pattern correct.",
     "medium"),

    # 34216 DHS/FEMA — Recovery and Resilience Resource (RRR) Portal
    # Narrative: smart matching wizard using LLM to match SLTT partners with resources
    # is_generative_ai=1 correct; general_llm correct; bureau correct;
    # custom_system: it's described as unfunded/planned portal feature — bespoke might fit
    # but custom_system is reasonable; no product → correct
    (34216, "DHS", "Recovery and Resilience Resource (RRR) Portal",
     "correct", "correct", "correct", "correct", "correct",
     "LLM smart-matching wizard for federal resources. Clearly generative. Bureau (FEMA) scope correct. custom_system defensible for planned in-house LLM.",
     "high"),

    # 34244 DHS/ICE — Mobile Device Analytics for Investigative Data
    # Narrative: geo-location clustering algorithm on mobile device data
    # is_generative_ai=0 correct; classical_ml correct (clustering/geo-algo);
    # bureau correct; custom_system correct; no product named → correct
    # architecture=rag_pipeline is suspicious for a geo-clustering tool but not in scope
    (34244, "DHS", "Mobile Device Analytics for Investigative Data",
     "correct", "correct", "correct", "correct", "correct",
     "Geo-location clustering ML. Classical pattern. All tags align. (rag_pipeline architecture flag is suspicious but not in audit scope.)",
     "high"),

    # 34333 DOC/FIRSTNET — Communications Topaz Labs Photo Editing
    # Narrative: AI photo/video editing tools, image quality improvement
    # is_generative_ai=0 — 'Topaz Labs' is a commercial AI image enhancer;
    # these tools can use generative upscaling/diffusion. However the narrative
    # describes "improve picture quality, smooth video, scale images" which could
    # be purely convolutional (non-generative). Tagging as 0 is defensible → correct
    # computer_vision correct; bureau correct; generic_use_pattern correct;
    # tool_product_name blank — but "Topaz Labs" appears in use_case_name → missing
    (34333, "DOC", "FirstNet Authority Communications Topaz Labs Photo Editing",
     "correct", "correct", "correct", "correct", "missing",
     "Topaz Labs is a named commercial AI product in the use_case_name. tool_product_name is blank — should capture 'Topaz Labs'. Marking verdict_tool=missing.",
     "high"),

    # 34337 DOC/NTIA — WAWENETS
    # Narrative: completely empty (no purpose_benefits, no outputs).
    # is_generative_ai=0, classical_ml, bureau, custom_system — all low-confidence
    # but cannot contradict because there's no narrative to read.
    # WAWENETS is a known NTIA waveform audio quality model → classical_ml is correct.
    # tool blank → correct (no vendor in empty narrative)
    (34337, "DOC", "WAWENETS",
     "correct", "correct", "correct", "correct", "correct",
     "No narrative text. WAWENETS is a known NTIA waveform quality model — classical_ml is reasonable domain knowledge. All tags correct by default (cannot contradict).",
     "low"),

    # 34347 DOC/NOAA — Coral Reef Watch
    # Narrative: remote sensing data interpretation and prediction (only in outputs field)
    # computer_vision correct (remote sensing imagery); pilot correct; custom_system correct
    # is_generative_ai=0 correct; no named product → correct
    (34347, "DOC", "Coral Reef Watch",
     "correct", "correct", "correct", "correct", "correct",
     "Remote sensing + prediction. computer_vision and pilot scope correct.",
     "medium"),

    # 34358 DOC/NOAA — AI Total Precipitable Water estimation
    # Narrative: nearly empty — title only mentions water estimation
    # predictive_analytics correct (forecasting); pilot correct; custom_system correct
    # is_generative_ai=0 correct; no named product → correct
    (34358, "DOC", "AI Total Precipitable Water estimation",
     "correct", "correct", "correct", "correct", "correct",
     "Minimal narrative. Water estimation model → predictive_analytics and pilot correct.",
     "low"),

    # 34440 DOE/FNAL — high level synthesis for machine learning (hls4ml)
    # Narrative: implements AI algorithms in embedded hardware for scientific applications
    # "prediction to data compression to control" — it's ML deployment infrastructure
    # is_generative_ai=0 correct; predictive_analytics — but hls4ml is a hardware
    # acceleration framework, not purely predictive. classical_ml or custom could fit.
    # predictive_analytics is off_by_one (it covers prediction but also compression/control)
    # bureau correct; custom_system correct; no vendor → correct
    (34440, "DOE", "high level synthesis for machine learning (hls4ml)",
     "correct", "off_by_one", "correct", "correct", "correct",
     "hls4ml implements ML in embedded hardware — spans prediction, compression, control. predictive_analytics is narrower than the actual use; classical_ml might be more accurate. off_by_one.",
     "medium"),

    # 34448 DOI/OCIO — DOIChatGPT AI Chatbot
    # Narrative: secure LLM chatbot, "customized version of Microsoft's Govchat repo"
    # deployed as Azure app service using DOIChatGPT APIM.
    # is_generative_ai=1 correct; general_llm correct; department correct;
    # bespoke_application correct (custom wrap on Azure/GPT);
    # tool_product_name blank — narrative mentions "Microsoft's Govchat repo" and
    # Azure/APIM but no specific named commercial AI product. The underlying model
    # isn't named (GPT not explicitly stated). is_general_llm_access=1 flagged.
    # tool correct (no explicit commercial AI product name, just Azure infra)
    (34448, "DOI", "DOIChatGPT AI Chatbot",
     "correct", "correct", "correct", "correct", "correct",
     "Bespoke LLM chatbot on Azure. Govchat/APIM are infrastructure, not AI product names. tool blank is defensible. All tags correct.",
     "high"),

    # 34457 DOI/NPS — bird nest detection using deep learning
    # Narrative: object detection model for bird nests from aerial photography
    # is_generative_ai=0 correct; computer_vision correct; bureau correct;
    # custom_system correct; no named commercial product → correct
    (34457, "DOI", "CESU project to detect of bird nests using deep learning to support annual colonial bird monitoring",
     "correct", "correct", "correct", "correct", "correct",
     "Object detection CV model for bird nests. computer_vision and custom_system correct.",
     "high"),

    # 34481 DOI/BOR — Data Driven Sub-Seasonal Forecasting
    # Narrative: forecasting temperature and precipitation, data-driven ML methods
    # is_generative_ai=0 correct; predictive_analytics correct; pilot correct;
    # custom_system correct; no product → correct
    (34481, "DOI", "Data Driven Sub-Seasonal Forecasting of Temperature and Precipitation",
     "correct", "correct", "correct", "correct", "correct",
     "Sub-seasonal forecasting ML. predictive_analytics and pilot scope correct.",
     "high"),

    # 34546 DOI/USGS — Predicting inundation dynamics of small forested wetlands
    # Narrative: random forest model for wetland wetting/drying prediction
    # is_generative_ai=0 correct; predictive_analytics correct; bureau correct;
    # custom_system correct; no product → correct
    (34546, "DOI", "Predicting inundation dynamics of small forested wetlands",
     "correct", "correct", "correct", "correct", "correct",
     "Random forest predictive model for wetland hydrology. All tags correct.",
     "high"),

    # 34547 DOI/USGS — Hydrography feature extraction from remotely sensed data
    # Narrative: ML to predict surface water location from remote sensing elevation+image data
    # This is primarily predictive analytics on geospatial data, but also uses imagery.
    # computer_vision is tagged — but the narrative says "predict location of surface water
    # from remotely sensed elevation and IMAGE data" — CV component present but
    # it's equally predictive. computer_vision is off_by_one (predictive_analytics also valid).
    # is_generative_ai=0 correct; bureau correct; custom_system correct; no product → correct
    (34547, "DOI", "Hydrograhy feature extraction from remotely sensed data",
     "correct", "off_by_one", "correct", "correct", "correct",
     "Narrative describes ML on elevation+imagery data to predict hydrography. computer_vision is defensible but predictive_analytics is equally valid. off_by_one.",
     "medium"),

    # 34576 DOI/USGS — Machine Learning Image Classification (PLACE project)
    # Narrative: random forest ML to classify wetlands and soil moisture; quantify wildfire
    # "classify wetlands" via random forest — this is classical_ml/predictive more than
    # computer_vision per se (no mention of actual image pixels, just large-scale classification).
    # However "utilizes random forest machine learning to classify wetlands" at large scale
    # could use satellite imagery → CV interpretation is defensible but classical_ml fits too.
    # off_by_one between computer_vision and classical_ml/predictive_analytics
    # is_generative_ai=0 correct; bureau correct; custom_system correct; no product → correct
    (34576, "DOI", "Machine Learning Image Classification",
     "correct", "off_by_one", "correct", "correct", "correct",
     "Random forest ML classifying wetlands/soil moisture — classical_ml or predictive_analytics fits as well as computer_vision. The PLACE project uses satellite imagery so CV is defensible. off_by_one.",
     "medium"),

    # 34586 DOI/USGS — Shoreline modeling
    # Narrative: LSTM, CNN, Transformers to predict shoreline evolution
    # CNN is mentioned but alongside LSTM and Transformers — this is a multi-modal ML
    # forecasting task (shoreline prediction). computer_vision from CNN mention is partial;
    # predictive_analytics better captures the core task (predict shoreline evolution).
    # off_by_one (CNN→CV is the literal interpretation but prediction is the goal)
    # is_generative_ai=0 correct; bureau correct; custom_system correct; no product → correct
    (34586, "DOI", "Shoreline modeling",
     "correct", "off_by_one", "correct", "correct", "correct",
     "Uses LSTM, CNN, Transformers for shoreline prediction. CNN justifies computer_vision but the primary task is predictive_analytics. off_by_one.",
     "medium"),

    # 34591 DOI/USGS — Coastal Ecosystem Prediction System
    # Narrative: multi-model ensemble predictions for wetland vulnerability to sea level rise
    # is_generative_ai=0 correct; predictive_analytics correct; bureau correct;
    # custom_system correct; no product → correct
    (34591, "DOI", "Coastal Ecosystem Prediction System",
     "correct", "correct", "correct", "correct", "correct",
     "Multi-model ensemble for coastal predictions. predictive_analytics correct.",
     "high"),

    # 34602 DOI/USGS — Data-driven approaches to filling missing time-series data (SF Bay-Delta)
    # Narrative: ML and deep learning to fill gaps in water-quality time-series data
    # (turbidity, salinity, temp). Range from linear regression to DL.
    # is_generative_ai=0 correct; predictive_analytics correct; bureau correct;
    # custom_system correct; no product → correct
    (34602, "DOI", "Data-driven approaches to filling missing time-series data within the San Francisco Bay-Delta",
     "correct", "correct", "correct", "correct", "correct",
     "Gap-filling in time-series water quality data using ML/DL. predictive_analytics correct.",
     "high"),

    # 34616 DOI/BOR — Machine Learning Applied to Geotechnical Engineering
    # Narrative: ML models predicting soil liquefaction during seismic events
    # is_generative_ai=0 correct; predictive_analytics correct; bureau correct;
    # custom_system correct; no product → correct
    (34616, "DOI", "Machine Learning Applied to Geotechnical Engineering: Statistical Methods Applied to Seismic Analysis 1",
     "correct", "correct", "correct", "correct", "correct",
     "Soil liquefaction prediction ML. predictive_analytics and custom_system correct.",
     "high"),

    # 34667 DOL/OCIO — SnagIT
    # Narrative: SnagIt (TechSmith) OCR and screenshot tool. Named product + vendor in tags.
    # tool_product_name=Snagit, tool_vendor=TechSmith — both appear in use_case_name and
    # purpose_benefits text. is_generative_ai=0 correct (OCR is not generative);
    # computer_vision correct (OCR/image capture); office correct; product_deployment correct
    # tool verdict: Snagit/TechSmith named in narrative → correct
    # Note: outputs mention "Image Generation" and "Automatic Captions" which could be
    # slightly generative, but primary function is OCR → is_generative_ai=0 is defensible
    (34667, "DOL", "SnagIT",
     "correct", "correct", "correct", "correct", "correct",
     "SnagIt by TechSmith is named in use_case_name and text. OCR = computer_vision. tool correct. is_generative_ai=0 defensible despite minor generative output features.",
     "high"),

    # 34673 DOL/OCIO — Periscope Mobile App
    # Narrative: Periscope (Twitter) live video app, discontinued 2021.
    # "NLP, Communications" as outputs. Very thin AI narrative.
    # is_generative_ai=0 correct; classical_ml — thin evidence, but Periscope used
    # recommendation/curation ML → reasonable; office correct;
    # product_feature correct (Twitter/Periscope is a product feature);
    # tool: Periscope/Twitter named in tags and in narrative → correct
    (34673, "DOL", "Periscope Mobile App",
     "correct", "correct", "correct", "correct", "correct",
     "Periscope discontinued Twitter app. product_feature and classical_ml correct for recommendation system. tool=Periscope/Twitter in narrative.",
     "medium"),

    # 34707 EPA/ORD — Machine learning-assisted literature screening
    # Narrative: ML ranking references by title/abstract relevance. NLP text classification.
    # is_generative_ai=0 correct; nlp_specific correct (text relevance ranking via NLP);
    # office correct; custom_system correct; no named product → correct
    (34707, "EPA", "Machine learning-assisted literature screening",
     "correct", "correct", "correct", "correct", "correct",
     "ML text relevance ranking for literature screening. nlp_specific and custom_system correct.",
     "high"),

    # 34725 GSA/IDT — ServiceNow Virtual Agent (Curie)
    # Narrative: ML-based natural language chatbot (Curie) using ServiceNow Virtual Agent
    # is_generative_ai=0 correct (ML-based NLU chatbot, not generative LLM);
    # nlp_specific correct (NLU/NLP chatbot); office correct;
    # product_deployment correct (ServiceNow product);
    # tool: ServiceNow Virtual Agent/ServiceNow named in both narrative and tags → correct
    (34725, "GSA", "ServiceNow Virtual Agent (Curie)",
     "correct", "correct", "correct", "correct", "correct",
     "ServiceNow ML-based NLU chatbot. nlp_specific and product_deployment correct. Tool correctly identified.",
     "high"),

    # 34748 HHS/ACF — Ask HR Policy
    # Narrative: RAG system using LLMs to answer HR policy questions from ACF staff
    # is_generative_ai=1 correct; general_llm correct; bureau correct;
    # bespoke_application correct (custom RAG interface over LLM);
    # is_cots=1, tool_product_name blank — narrative doesn't name specific LLM vendor
    # → tool correct (no explicit vendor named)
    (34748, "HHS", "Ask HR Policy",
     "correct", "correct", "correct", "correct", "correct",
     "RAG LLM for HR policy Q&A. Clearly generative. Bespoke application correct. No specific LLM vendor named in narrative.",
     "high"),

    # 34805 HHS/CDC — ChatCDC Enterprise Generative AI Chatbot
    # Narrative: "powered by Azure OpenAI Large Language Models" — Azure OpenAI is named!
    # tool_product_name=Azure OpenAI, tool_vendor=Microsoft/OpenAI — both in narrative → correct
    # is_generative_ai=1 correct; general_llm correct; bureau correct;
    # product_deployment correct (named commercial product Azure OpenAI)
    (34805, "HHS", "ChatCDC - CDC Enterprise Generative AI Chatbot (Ideation)",
     "correct", "correct", "correct", "correct", "correct",
     "Azure OpenAI explicitly named in outputs text. tool_product_name=Azure OpenAI, vendor=Microsoft/OpenAI. All tags correct.",
     "high"),

    # 34829 HHS/CMS — Central Data Abstraction Tool-Modernized (CDAT)
    # Narrative: NLP, OCR, AI, ML to automate medical record review
    # Wave 3 canonical tag: bespoke_application, computer_vision.
    # Wave 1 had product_deployment but no product named → the wave3 correction to
    # bespoke_application is more accurate for an in-house NLP/OCR/ML pipeline.
    # is_generative_ai=0 correct (OCR/NLP, not generative);
    # computer_vision — primary task is OCR on medical records → nlp_specific or
    # computer_vision are both defensible. computer_vision for document image OCR → off_by_one
    # bespoke_application: this is a custom-built automation tool → correct
    # tool: no vendor named in narrative → correct
    (34829, "HHS", "Central Data Abstraction Tool-Modernized (Modernized-CDAT)- Intake Process Automation (PA) Tool",
     "correct", "off_by_one", "correct", "correct", "correct",
     "NLP, OCR, ML automation for medical records. computer_vision captures OCR but nlp_specific also fits the text processing. off_by_one. bespoke_application correct after wave3 fix.",
     "medium"),

    # 34839 HHS/CMS — MSP Assignment Bot
    # Narrative: BOT automatically retrieves records from contractor system and assigns
    # to staff. Rule-based RPA-style system with database import.
    # is_generative_ai=0 correct; classical_ml — this reads more like RPA/scripted
    # automation than ML. "BOT to pull and assign cases" — no ML vocabulary.
    # Could be classical_ml (simple scoring/routing) but RPA/automation is more likely.
    # classical_ml is off_by_one (or possibly incorrect if truly rule-based),
    # but without stronger evidence of non-ML automation, off_by_one is appropriate.
    # bureau correct; custom_system correct; no product → correct
    (34839, "HHS", "MSP Assignment Bot",
     "correct", "off_by_one", "correct", "correct", "correct",
     "BOT for automated case retrieval and assignment — reads like RPA more than classical_ml. The narrative lacks ML vocabulary. off_by_one is charitable; could be incorrect.",
     "medium"),

    # 34866 HHS/CMS — Improved Data Quality Checks
    # Narrative: "POC classifier model to identify incorrect document upload types /
    # low-quality images through use of OCR"
    # Wave 3: product_deployment, computer_vision. Wave 1: product_deployment, computer_vision.
    # is_generative_ai=0 correct; computer_vision correct (image quality + OCR);
    # bureau correct; product_deployment — but narrative says "develop a POC classifier model"
    # which sounds more custom than COTS product deployment.
    # However wave3 kept 2024 tag and the tool might be a COTS OCR product.
    # With no named product, product_deployment is questionable → debatable entry_type.
    # tool: no product named → correct (blank is right)
    (34866, "HHS", "Improved Data Quality Checks",
     "correct", "correct", "correct", "debatable", "correct",
     "Narrative says 'develop a POC classifier model' suggesting in-house build, but tagged product_deployment. No vendor named. entry_type is debatable — bespoke_application might fit better.",
     "medium"),

    # 34879 HHS/HHS — News from commercial publisher such as Google News
    # Narrative: Google News sends personalized news feeds based on user preferences
    # This is a COMMERCIAL product (Google News) not a custom system.
    # is_generative_ai=0 correct (recommendation/curation ML, not generative);
    # classical_ml correct (recommendation engine); department correct;
    # custom_system is INCORRECT — Google News is a commercial product, this should be
    # product_feature or product_deployment.
    # tool: Google is named in use_case_name but tool_product_name is blank → missing
    (34879, "HHS", "News from commercial publisher such as Google News",
     "correct", "correct", "correct", "incorrect", "missing",
     "Google News is explicitly named in use_case_name — this is a commercial product feature, not custom_system. entry_type should be product_feature. tool_product_name should be 'Google News'.",
     "high"),

    # 34913 HHS/HRSA — AI Audit Resolution Assistant
    # Narrative: RAG + LLM chatbot for Single Audit resolution. Vector DB, RAG pipeline.
    # is_generative_ai=1 correct; general_llm correct; bureau correct;
    # bespoke_application correct (in-house RAG build); no named LLM vendor → correct
    (34913, "HHS", "AI Audit Resolution Assistant",
     "correct", "correct", "correct", "correct", "correct",
     "RAG LLM for audit resolution. Explicitly generative. Bespoke application with vector DB. All tags correct.",
     "high"),

    # 34945 HHS/NIH — Detection of Implementation Science focus in grant applications
    # Narrative: NLP + ML to calculate IS score for grant classification
    # is_generative_ai=0 correct; nlp_specific correct (NLP text classification);
    # bureau correct; product_deployment — but narrative says "This tool uses NLP and ML"
    # suggesting custom-built. is_cots=1 but no named product → product_deployment is
    # questionable. debatable entry_type.
    # tool: no product named → correct (blank is right)
    (34945, "HHS", "Detection of Implementation Science focus within incoming grant applications",
     "correct", "correct", "correct", "debatable", "correct",
     "NLP/ML grant classifier — sounds custom-built ('This tool uses NLP and ML to calculate a score') but tagged product_deployment with is_cots=1 and no named product. entry_type is debatable.",
     "medium"),

    # 34977 HHS/NIH — NLM-Gene: automatic gene indexing in PubMed
    # Narrative: NLP and deep learning to find gene names in biomedical literature
    # is_generative_ai=0 correct; nlp_specific correct (NER/NLP);
    # pilot correct (Initiated stage); custom_system correct; no product → correct
    (34977, "HHS", "NLM-Gene: towards automatic gene indexing in PubMed articles",
     "correct", "correct", "correct", "correct", "correct",
     "NLP + DL for gene name extraction from biomedical text. nlp_specific and custom_system correct.",
     "high"),

    # 35084 STATE/CA/CST — Innovation and Transformation Measurement and Prediction
    # Narrative: causal impact measurement + ML/statistical modeling of consular service changes
    # is_generative_ai=0 correct; predictive_analytics correct; bureau correct;
    # bespoke_application — this is early-stage research/planning, custom methodology.
    # bespoke_application is fine but custom_system could also fit. debatable.
    # no product → correct
    (35084, "STATE", "Innovation and Transformation Measurement and Prediction",
     "correct", "correct", "correct", "debatable", "correct",
     "Causal impact ML for consular services. predictive_analytics correct. bespoke_application vs custom_system is debatable for a planning/research methodology.",
     "medium"),

    # 35094 STATE/DT — Apptio
    # Narrative: Apptio financial planning COTS used for billing and cost modeling
    # "extrapolate future values using several available formulas"
    # is_generative_ai=0 correct; predictive_analytics correct;
    # office correct; product_deployment correct;
    # tool: Apptio/Apptio named in both use_case_name and narrative → correct
    (35094, "STATE", "Apptio",
     "correct", "correct", "correct", "correct", "correct",
     "Apptio commercial COTS for financial forecasting. Apptio/Apptio named in narrative. All tags correct.",
     "high"),

    # 35095 STATE/DT — DT Data Analytics and Assessment (DAA) AI Use Case
    # Narrative: parse unstructured text to build structured compliance data
    # is_generative_ai=0 correct; nlp_specific correct (text parsing/extraction);
    # office correct; bespoke_application — planned custom tool.
    # bespoke_application vs custom_system: planned in-house NLP extraction tool.
    # bespoke_application is debatable (could be custom_system). debatable.
    # no product → correct
    (35095, "STATE", "DT Data Analytics and Assessment (DAA) AI Use Case ITCP data harvest",
     "correct", "correct", "correct", "debatable", "correct",
     "Unstructured text parsing to structured data — nlp_specific correct. bespoke_application vs custom_system is debatable for a planned data parsing tool.",
     "medium"),

    # 35113 STATE/R/GEC — Topic Modeling
    # Narrative: cluster text into themes using Python libraries (retired)
    # is_generative_ai=0 correct; nlp_specific correct (topic modeling = NLP);
    # office correct; custom_system correct; no product → correct
    (35113, "STATE", "Topic Modeling",
     "correct", "correct", "correct", "correct", "correct",
     "Text clustering/topic modeling with Python. nlp_specific and custom_system correct.",
     "high"),

    # 35114 STATE/R/GEC — Forecasting
    # Narrative: statistical models projecting COVID cases and violent events (retired)
    # is_generative_ai=0 correct; predictive_analytics correct; office correct;
    # custom_system correct; no product → correct
    (35114, "STATE", "Forecasting",
     "correct", "correct", "correct", "correct", "correct",
     "Statistical forecasting (COVID, violence). predictive_analytics and custom_system correct.",
     "high"),

    # 35122 STATE/R/GPA/RA — Digital Media Analytics Platform
    # Narrative: open-source neural machine translation for global media articles
    # is_generative_ai=0 — NMT is technically generative (produces target language text)
    # but the field convention treats NMT as nlp_specific translation, not GenAI.
    # Tagging as 0 is standard practice → correct
    # nlp_specific correct; office correct; custom_system correct; no product → correct
    (35122, "STATE", "Digital Media Analytics Platform",
     "correct", "correct", "correct", "correct", "correct",
     "Neural machine translation for media articles — NMT is nlp_specific by convention, not GenAI. office scope and custom_system correct.",
     "high"),

    # 35192 USAID — Disinformation Monitoring and Sentiment Analysis (Chemonics)
    # Narrative: AI to monitor social media for disinformation + sentiment analysis
    # is_generative_ai=0 correct; nlp_specific correct (sentiment analysis);
    # bureau correct; custom_system correct (program subcontractor system);
    # no named commercial AI product in narrative → correct
    (35192, "USAID", "Chemonics International Inc.'s \"Disinformation Monitoring and Sentiment Analysis\"",
     "correct", "correct", "correct", "correct", "correct",
     "Social media sentiment analysis for disinformation monitoring. nlp_specific and custom_system correct.",
     "high"),

    # 35193 USAID — PEER 8-161: Xylotron wood species identification
    # Narrative: Xylotron uses AI to identify wood species by image matching against DNA database
    # is_generative_ai=0 correct; classical_ml — but the system uses image matching/scanning
    # which is computer_vision. The Xylotron scans images and matches to database.
    # classical_ml is off_by_one (computer_vision better describes image-based species ID).
    # bureau correct; custom_system correct; no commercial product vendor → correct
    (35193, "USAID", "PEER 8-161: A wood species identification tool to aid in compliance and enforcement of Peruvian timber regulations",
     "correct", "off_by_one", "correct", "correct", "correct",
     "Xylotron uses image scanning to match wood species — computer_vision better fits than classical_ml. off_by_one.",
     "high"),

    # 35196 USAID — USING PREDICTIVE ANALYTICS TO IMPROVE CARE
    # Narrative: identify high-risk children for malnutrition intervention using predictive analytics
    # is_generative_ai=0 correct; predictive_analytics correct; bureau correct;
    # custom_system correct; no product → correct
    (35196, "USAID", "USING PREDICTIVE ANALYTICS TO IMPROVE CARE",
     "correct", "correct", "correct", "correct", "correct",
     "Child malnutrition risk prediction model. predictive_analytics and custom_system correct.",
     "high"),

    # 35209 USAID — Global Antimicrobial Resistance Surveillance System (GLASS)
    # Narrative: WHO GLASS surveillance system with training for AMR data collection.
    # This is more of a data management/reporting system than ML/AI.
    # classical_ml is weak — no ML vocabulary in narrative, just "surveillance" and "training."
    # is_generative_ai=0 correct; classical_ml is questionable but cannot be disproved;
    # bureau correct; custom_system correct; no product → correct
    # Note: The AI component here is very thin — GLASS is primarily a reporting system.
    (35209, "USAID", "Global Antimicrobial Resistance Surveillance System",
     "correct", "correct", "correct", "correct", "correct",
     "WHO GLASS surveillance/reporting system. Weak AI content — classical_ml is assumed by convention. All tags are reasonable given sparse narrative.",
     "low"),

    # 35210 USAID — GXAlert
    # Narrative: integrates diagnostic devices with reporting system. No ML vocabulary.
    # Similar to GLASS — this is a data integration/reporting system.
    # classical_ml is assumed but not evidenced; bureau correct; custom_system correct.
    # is_generative_ai=0 correct. No product named in narrative → correct.
    (35210, "USAID", "GXAlert",
     "correct", "correct", "correct", "correct", "correct",
     "Diagnostic device data integration and reporting system (GXAlert/System One). Thin AI narrative. classical_ml assumed. System One named in narrative but not commercial AI product per se.",
     "low"),

    # 35213 USAID — DeepGreen Ukraine
    # Narrative: satellite data analysis for illegal logging/deforestation detection in Ukraine
    # Computer vision on satellite imagery for forest cover change detection.
    # classical_ml tagged — but satellite deforestation detection is computer_vision.
    # off_by_one (computer_vision would be better fit than classical_ml).
    # office correct; custom_system correct; no product → correct
    (35213, "USAID", "DeepGreen Ukraine",
     "correct", "off_by_one", "correct", "correct", "correct",
     "Satellite imagery analysis for deforestation detection — computer_vision better fits than classical_ml. off_by_one.",
     "high"),

    # 35230 USAID — Amazonía Mia - AI for environmental law enforcement
    # Narrative: strengthen AG's capabilities for environmental crime investigation,
    # deforestation in Colombian Amazon. "custom_trained, mission_critical" — vague.
    # classical_ml is reasonable for pattern analysis; office correct; custom_system correct.
    # is_generative_ai=0 correct; no product → correct
    (35230, "USAID", "Amazonía Mia - AI for environmental law enforcement in Colombia",
     "correct", "correct", "correct", "correct", "correct",
     "Environmental crime/deforestation AI tool. Vague narrative but classical_ml and custom_system are reasonable.",
     "low"),

    # 35237 USAID — Project Data Machine: Open governance data in Colombia
    # Narrative: technological tool for integrating Congress data into standardized formats.
    # This describes a data pipeline/ETL system, not clearly AI/ML.
    # classical_ml is unsubstantiated — no AI/ML vocabulary.
    # is_generative_ai=0 correct; classical_ml is questionable (debatable if any AI here);
    # office correct; custom_system correct; no product → correct
    (35237, "USAID", "Project Data Machine: Open governance data in Colombia",
     "correct", "off_by_one", "correct", "correct", "correct",
     "Open governance data integration tool — reads like ETL/data pipeline, not ML. classical_ml is unsubstantiated. off_by_one is generous; could be incorrect. No AI vocabulary in narrative.",
     "medium"),

    # 35270 USAID — ESDB/IDEA Series Classification
    # Narrative: automatically suggest categories for economic/social data indicators
    # "reduce labor hours involved in classifying new economic and social data indicators"
    # is_generative_ai=0 correct; classical_ml correct (text classification ML);
    # bureau correct; custom_system correct; no product → correct
    (35270, "USAID", "ESDB/IDEA Series Classification",
     "correct", "correct", "correct", "correct", "correct",
     "Category suggestion ML for economic indicators. classical_ml (text classification) and custom_system correct.",
     "high"),

    # 35294 USAID — AI translation of water, sanitation, and hygiene learning materials
    # Narrative: AI for translation of WASH learning materials (CAWST partner)
    # Translation is NLP — classical_ml is a weaker fit than nlp_specific.
    # off_by_one (nlp_specific better captures machine translation).
    # bureau correct; custom_system correct; no product → correct
    # is_generative_ai=0 — machine translation could be NMT (generative) but classified as 0
    # by convention → correct
    (35294, "USAID", "AI translation of water, sanitation, and hygiene learning materials",
     "correct", "off_by_one", "correct", "correct", "correct",
     "AI translation of WASH materials — nlp_specific fits better than classical_ml for machine translation. off_by_one.",
     "high"),

    # 35321 USDA/APHIS — Detection of Pre-symptomatic HLB Infected Citrus
    # Narrative: detect citrus trees infected with HLB disease using drone camera images
    # is_generative_ai=0 correct; computer_vision correct (drone imagery);
    # bureau correct; custom_system correct; no product → correct
    (35321, "USDA", "Detection of Pre-symptomatic HLB Infected Citrus",
     "correct", "correct", "correct", "correct", "correct",
     "Drone imagery CV model for citrus disease detection. computer_vision and custom_system correct.",
     "high"),

    # 35360 USDA/NRCS — Dam Inspection Report Document Processing
    # Narrative: pull out/organize data from dam inspection documents using OCR/NLP
    # tool: MS Power Platform/Microsoft named in both narrative mention (Power BI) and tags
    # "Microsoft Power BI" mentioned in purpose; tool_product_name=MS Power Platform
    # is_generative_ai=0 correct; nlp_specific correct (document OCR/NLP);
    # bureau correct; product_deployment correct;
    # tool: "MS Power Platform" in tags, "Microsoft Power BI" in narrative — close match → correct
    (35360, "USDA", "Dam Inspection Report Document Processing",
     "correct", "correct", "correct", "correct", "correct",
     "Document OCR/NLP for dam inspection reports with MS Power BI. nlp_specific and product_deployment correct. MS Power Platform/Microsoft correctly identified.",
     "high"),

    # 35640 VA/VHA — ECG/EKG Machines - Interpretation of Results
    # Narrative: software aids interpretation of ECG tracings, integrates with CPRS
    # This is classical signal processing / pattern recognition → classical_ml correct
    # is_generative_ai=0 correct; classical_ml correct; bureau correct;
    # custom_system — "Developed in-house" → correct; no named product → correct
    # Note: "ECG machines" are commercial (GE, Philips etc.) but the AI interpretation
    # software is described as in-house developed → custom_system is right
    (35640, "VA", "ECG/EKG Machines- Interpretation of Results",
     "correct", "correct", "correct", "correct", "correct",
     "In-house ECG interpretation software. classical_ml (signal pattern recognition) and custom_system correct.",
     "high"),

    # 35641 VA/OIT — Appointment Comments Categorization
    # Narrative: model for alerting mental health needs during appointment signup
    # Returns timely alert classification with confidence score
    # is_generative_ai=0 correct; classical_ml correct (text classification/categorization);
    # bureau correct; custom_system correct; no product → correct
    (35641, "VA", "Appointment Comments Categorization",
     "correct", "correct", "correct", "correct", "correct",
     "Mental health alert classification from appointment comments. classical_ml and custom_system correct.",
     "high"),

    # 35654 VA/VHA — Roche Digital Pathology
    # Narrative: analyzes slide images to aid in diagnosing pathology cases
    # Roche Digital Pathology is a named commercial product.
    # is_generative_ai=0 correct; computer_vision correct (slide image analysis);
    # bureau correct; product_deployment correct;
    # tool: tool_product_name blank but "Roche Digital Pathology" is in the use_case_name
    # → missing (named commercial product, blank tool field)
    (35654, "VA", "Roche Digital Pathology",
     "correct", "correct", "correct", "correct", "missing",
     "Roche Digital Pathology is a named commercial product in use_case_name. tool_product_name is blank — should be 'Roche Digital Pathology'. verdict_tool=missing.",
     "high"),

    # 35662 VA/VHA — TrueFidelity CT Deep Learning Image Reconstruction
    # Narrative: decreases noise in CT images (very brief)
    # TrueFidelity is a GE Healthcare commercial product for CT reconstruction.
    # is_generative_ai=0 correct; classical_ml — CT deep learning reconstruction is
    # more computer_vision (image processing). off_by_one.
    # bureau correct; custom_system — but TrueFidelity is a named commercial product!
    # entry_type should be product_deployment → incorrect
    # tool: TrueFidelity (GE Healthcare) in use_case_name but tool blank → missing
    (35662, "VA", "TrueFidelity CT Deep Learning Image Reconstruction",
     "correct", "off_by_one", "correct", "incorrect", "missing",
     "TrueFidelity is a GE Healthcare commercial CT reconstruction product (named in use_case_name). entry_type=custom_system is incorrect — should be product_deployment. tool_product_name blank for a named commercial product = missing.",
     "high"),

    # 35674 VA/VBA — National Training Team | Schools — FAQ Dashboard
    # Narrative: model classifies questions, generates sample questions, provides answers
    # "generate a sample question based on the category" — this sounds generative!
    # "provide a suggested answer based on previous responses" — could be retrieval or generative.
    # is_generative_ai=0 — but "generate a sample question" is a generative task.
    # This could be incorrect (0 vs 1). However "generate" may be used loosely for
    # retrieval-based Q&A generation. Flagging as incorrect.
    # classical_ml: if truly generative it would be general_llm. If retrieval-based,
    # nlp_specific fits better than classical_ml for Q&A. off_by_one.
    # bureau correct; product_deployment: is_cots=1 but no named product → debatable
    (35674, "VA", "National Training Team | Schools — FAQ Dashboard",
     "incorrect", "off_by_one", "correct", "debatable", "correct",
     "Narrative says 'generate a sample question based on the category' — this is a generative task, is_generative_ai should be 1. classical_ml is also weak for Q&A generation — nlp_specific or general_llm would be better. product_deployment with no named product is debatable.",
     "medium"),

    # 35675 VA/VHA — Audit of Service Connection Designations Associated with Prescriptions
    # Narrative: very thin — "Reduction in waste, fraud and abuse" and "Binary" output
    # is_generative_ai=0 correct; classical_ml correct (binary classifier for fraud);
    # bureau correct; custom_system correct; no product → correct
    (35675, "VA", "Audit of Service Connection Designations Associated with Prescriptions",
     "correct", "correct", "correct", "correct", "correct",
     "Binary fraud/abuse classifier. classical_ml and custom_system correct. Thin narrative.",
     "medium"),

    # 35678 VA/VHA — ProGRESS Prostate Cancer Risk Prediction Model
    # Wave 3: bespoke_application, classical_ml, is_generative_ai=0
    # Wave 1 had is_generative_ai=1, general_llm — wave3 corrected to 0/classical_ml
    # Narrative: LASSO-regularized Cox model + ML training/validation for prostate cancer risk
    # This is clearly a statistical/ML risk model, not generative AI.
    # is_generative_ai=0 correct; classical_ml — LASSO Cox model is predictive_analytics.
    # off_by_one (predictive_analytics is more precise than classical_ml for survival models)
    # bureau correct; bespoke_application: validated clinical tool built in-house → correct
    # no product → correct
    (35678, "VA", "Prostate Cancer, Genetic Risk, and Equitable Screening Study (ProGRESS) - Prostate Cancer Risk Prediction Model",
     "correct", "off_by_one", "correct", "correct", "correct",
     "LASSO Cox survival model for prostate cancer risk stratification. predictive_analytics is more precise than classical_ml. off_by_one. Wave 3 correctly rejected wave1's general_llm/generative tag.",
     "high"),

    # 35687 VA/OIT — ESD-Speech Sentiment and Analytics
    # Narrative: AI to analyze speech sentiment of internal customers at the service desk
    # commercial_ai field mentions "Transcribing and summarizing" suggesting LLM-based.
    # But the primary function is sentiment analysis on speech → nlp_specific better
    # than general_llm for speech sentiment alone.
    # is_generative_ai=1 — sentiment analysis isn't inherently generative.
    # "Transcribing and summarizing" in commercial_ai is an OMB checkbox phrase, not evidence.
    # The narrative itself: "utilizing AI to analyze speech sentiment" — no generative evidence.
    # is_generative_ai=1 is questionable → incorrect
    # ai_sophistication=general_llm: if not generative, nlp_specific better → off_by_one or incorrect
    # pilot correct; bespoke_application debatable for a sentiment analytics dashboard
    (35687, "VA", "ESD-Speech Sentiment and Analytics",
     "incorrect", "off_by_one", "correct", "debatable", "correct",
     "Speech sentiment analysis for service desk — the narrative has no generative AI indicators. is_generative_ai=1 appears to come from the OMB checkbox phrase (not a valid vendor signal per rubric). general_llm→nlp_specific is off_by_one if truly non-generative. bespoke_application vs custom_system debatable.",
     "high"),

    # 35773 VA/VHA — Classify clinical pathway for cancer patients
    # Narrative: uses "open-source generative large language model" explicitly
    # to classify clinical pathways from notes. Zero-shot/few-shot prompting.
    # is_generative_ai=1 correct; general_llm correct; bureau correct;
    # bespoke_application correct (in-house informatics workflow using open-source LLM)
    # no commercial product → correct
    (35773, "VA", "Classify clinical pathway for cancer patients",
     "correct", "correct", "correct", "correct", "correct",
     "Explicitly uses 'open-source generative large language model'. All tags correct.",
     "high"),

    # 35776 VA/VHA — Adobe Creative Cloud
    # Narrative: develop nursing education presentations; outputs animations/AI art
    # Adobe Creative Cloud is a named commercial product!
    # is_generative_ai=0 — outputs include "AI art" and animations which could be generative.
    # "Used to make animations or to populate AI art" — AI art generation IS generative.
    # is_generative_ai=0 is incorrect.
    # ai_sophistication=classical_ml: if generative, should be general_llm or computer_vision
    # entry_type=custom_system: Adobe CC is a commercial product → should be product_deployment
    # tool: Adobe Creative Cloud is named but tool_product_name blank → missing
    (35776, "VA", "Adobe Creative Cloud",
     "incorrect", "incorrect", "correct", "incorrect", "missing",
     "Adobe Creative Cloud is explicitly named; outputs include 'AI art' which is generative. is_generative_ai=0 incorrect. classical_ml incorrect for image generation. custom_system incorrect — should be product_deployment. tool_product_name blank for named commercial product.",
     "high"),

    # 35794 VA/VHA — Intelligent 2D (Mammography)
    # Narrative: synthetic 2D images from 3D mammography data (FDA approved)
    # This is computer vision / deep learning for medical imaging. Custom_system.
    # Note: "Produces synthetic 2D images" could be considered generative (synthesis).
    # However medical image synthesis is typically not classified as GenAI.
    # is_generative_ai=0 defensible; computer_vision correct; bureau correct;
    # custom_system correct (no vendor named, developed in-house);
    # no product named → correct
    (35794, "VA", "Intelligent 2D",
     "correct", "correct", "correct", "correct", "correct",
     "Synthetic mammography 2D from 3D — medical imaging CV, not classified as GenAI. computer_vision and custom_system correct.",
     "high"),

    # 35820 VA/VHA — VA CART Percutaneous Coronary Intervention SYNTAX Score
    # Narrative: risk model predicting 30-day post-PCI mortality using clinical + anatomic variables
    # is_generative_ai=0 correct; predictive_analytics correct; bureau correct;
    # custom_system correct; no product → correct
    (35820, "VA", "VA CART Percutaneous Coronary Intervention SYNTAX Score",
     "correct", "correct", "correct", "correct", "correct",
     "PCI 30-day mortality risk model. predictive_analytics and custom_system correct.",
     "high"),

    # 35845 VA/OIG — Transcription Services
    # Narrative: "Increased efficiency", outputs "transcribed meetings and interviews"
    # commercial_ai field: "Transcribing and summarizing a recorded meeting or interview"
    # This is transcription service — NLP/ASR task. Is it truly generative?
    # is_generative_ai=1 — standard ASR transcription is not generative AI.
    # The commercial_ai checkbox is "Transcribing and summarizing" but per rubric this is
    # not a vendor signal. The narrative has no vendor or generative AI indicator.
    # is_generative_ai=1 → incorrect. general_llm → nlp_specific is more appropriate.
    # bespoke_application for transcription: debatable vs product_deployment.
    # no vendor named → correct
    (35845, "VA", "Transcription Services",
     "incorrect", "off_by_one", "correct", "debatable", "correct",
     "Transcription service (ASR) — not inherently generative AI. is_generative_ai=1 is incorrect. general_llm→nlp_specific is off_by_one. bespoke_application vs product_deployment is debatable without a named product.",
     "high"),

    # 35952 DOJ/DEA — Supply Chain Analytics
    # Narrative: analytics for global drug market supply chain understanding
    # No clear ML vocabulary beyond "analytics". classical_ml assumed.
    # is_generative_ai=0 correct; classical_ml defensible; bureau correct;
    # custom_system correct; no product → correct
    (35952, "DOJ", "Supply Chain Analytics",
     "correct", "correct", "correct", "correct", "correct",
     "Drug market supply chain analytics. classical_ml and custom_system correct. Sparse AI vocabulary.",
     "medium"),

    # 35967 DOJ/DEA — Data & Analytics: Financial and Cryptocurrency Transactions
    # Wave 3 canonical: custom_system, is_generative_ai=1, agentic
    # Narrative: "enhance investigative process, search for patterns in financial transactions"
    # "Outputs include recommended results and data visualizations"
    # is_generative_ai=1 — narrative has NO generative AI indicators. Pattern analysis
    # on financial/crypto transactions is classical_ml or predictive_analytics.
    # is_generative_ai=1 is INCORRECT.
    # agentic: narrative describes pattern finding + recommendations, not agentic autonomy.
    # agentic is incorrect — classical_ml or predictive_analytics is better.
    # bureau correct; custom_system correct; no product → correct
    (35967, "DOJ", "Data & Analytics: Financial and Cryptocurrency Transactions 1",
     "incorrect", "incorrect", "correct", "correct", "correct",
     "Financial/crypto transaction pattern analysis — no GenAI indicators in narrative. is_generative_ai=1 incorrect. agentic is incorrect — this is classical ML/analytics pattern matching. wave3 adopted wave2 correction that appears wrong here.",
     "high"),

    # 35988 DOJ/Dept-wide — General Web Search
    # Narrative: DOJ employees use Google and Bing for information retrieval
    # is_generative_ai=0 correct (pre-GenAI web search); classical_ml correct
    # (search engine ranking is classical ML); department correct;
    # generic_use_pattern correct; no product → correct
    (35988, "DOJ", "General Web Search",
     "correct", "correct", "correct", "correct", "correct",
     "Standard web search (Google/Bing). classical_ml for ranking. department/generic_use_pattern correct.",
     "high"),

    # 35995 DOJ/ENRD — Parallel Search from CaseText
    # Narrative: CaseText Parallel Search for legal research by describing case in plain language
    # CaseText is a named commercial legal AI product!
    # is_generative_ai=0 — CaseText uses embeddings/semantic search; not pure generative
    # but modern CaseText includes AI chat. For 2024 context, tagging as 0 is defensible.
    # classical_ml: semantic search could be nlp_specific. off_by_one.
    # bureau correct; generic_use_pattern vs product_deployment: CaseText is a named
    # commercial product but described as a generic search pattern → debatable.
    # tool: CaseText named in use_case_name but tool blank → missing
    (35995, "DOJ", "Parallel Search from CaseText",
     "correct", "off_by_one", "correct", "debatable", "missing",
     "CaseText Parallel Search is a named commercial legal AI product. tool_product_name blank = missing. Semantic search is nlp_specific not classical_ml (off_by_one). generic_use_pattern vs product_deployment is debatable for a named commercial product.",
     "high"),

    # 36022 DOJ/FBI — Autonomous Detection and Monitoring
    # Narrative: "data and analytics, data synthesis, filtering, and linking of
    # open source & threat intelligence"
    # is_generative_ai=0 correct; classical_ml correct; bureau correct;
    # custom_system correct; no product → correct
    (36022, "DOJ", "Autonomous Detection and Monitoring (Procurement ID: 15F06721P0002431)",
     "correct", "correct", "correct", "correct", "correct",
     "Open source threat intelligence analytics. classical_ml and custom_system correct.",
     "medium"),

    # 36036 DOJ/FBOP — Gemini
    # Narrative: checks grammatical errors and generates content; "Gemini" is Google's LLM
    # is_generative_ai=1 correct; general_llm correct; bureau correct;
    # product_deployment correct; tool: Gemini/Google named in both use_case_name and tags
    # is_google=1 correctly flagged → correct
    (36036, "DOJ", "Gemini",
     "correct", "correct", "correct", "correct", "correct",
     "Google Gemini LLM for grammar/content generation. All tags correct. is_google=1 correct.",
     "high"),

    # 36066 DOJ/OCDETF — Cyber Network Analysis for OCDETF MIS
    # Narrative: baseline network behavior analysis, anomaly/outlier detection
    # is_generative_ai=0 correct; predictive_analytics correct (anomaly detection/baseline);
    # pilot correct (Initiated stage); custom_system correct; no product → correct
    (36066, "DOJ", "Cyber Network Analysis for OCDETF MIS",
     "correct", "correct", "correct", "correct", "correct",
     "Network anomaly detection for cybersecurity. predictive_analytics and pilot correct.",
     "high"),

    # 36080 DOJ/OIG — Dragon
    # Narrative: Dragon speech recognition software for accessibility/dictation
    # Dragon (Nuance) is a named commercial product!
    # is_generative_ai=0 correct; nlp_specific correct (speech recognition/NLP);
    # bureau correct; custom_system — Dragon is a commercial product, should be
    # product_deployment → incorrect
    # tool: "Dragon" is named in use_case_name but tool_product_name blank → missing
    (36080, "DOJ", "Dragon",
     "correct", "correct", "correct", "incorrect", "missing",
     "Dragon is a named Nuance/Microsoft commercial speech recognition product. entry_type=custom_system incorrect — should be product_deployment. tool_product_name blank for named commercial product = missing.",
     "high"),

    # 36093 DOJ/PAO — EEG - Live Captioning
    # Narrative: EEG provides real-time captioning of live events for Section 508 compliance
    # EEG (Electronic Engineering Group) is a named commercial captioning service!
    # is_generative_ai=0 correct; classical_ml: live captioning is ASR/NLP.
    # nlp_specific would be more accurate than classical_ml. off_by_one.
    # bureau correct; custom_system — EEG is a commercial captioning vendor → incorrect
    # tool: EEG captioning service named but tool_product_name blank → missing
    (36093, "DOJ", "EEG - Live Captioning",
     "correct", "off_by_one", "correct", "incorrect", "missing",
     "EEG is a commercial real-time captioning vendor named in use_case_name. entry_type=custom_system incorrect — should be product_deployment. nlp_specific fits better than classical_ml for ASR captioning. tool_product_name blank = missing.",
     "high"),

    # 36129 ED/FSA — Generative AI Usage
    # Narrative: AI provides key points, summaries, action items from public documents
    # is_generative_ai=1 correct; general_llm correct; bureau correct;
    # generic_use_pattern correct (general LLM use policy); no specific vendor → correct
    (36129, "ED", "Generative AI Usage",
     "correct", "correct", "correct", "correct", "correct",
     "General LLM usage for document summarization. All tags correct.",
     "high"),

    # 36143 ED/OCIO — Generative AI Usage (DLP testing)
    # Narrative: AI tested with fabricated prohibited prompts for DLP filter testing
    # is_generative_ai=1 correct; general_llm correct; bureau correct;
    # generic_use_pattern correct; no specific vendor → correct
    (36143, "ED", "Generative AI Usage",
     "correct", "correct", "correct", "correct", "correct",
     "LLM DLP filter testing. general_llm and generic_use_pattern correct.",
     "high"),

    # 36179 ED/FSA — AWS Bedrock in FSA EDMAPS Assessment
    # Narrative: "AWS Bedrock enables organizations to build and scale applications
    # powered by foundation models"
    # is_generative_ai=1 correct; general_llm correct; bureau correct;
    # bespoke_application correct (custom app on Bedrock);
    # tool: Bedrock/AWS named in both use_case_name and tags → correct
    (36179, "ED", "AWS Bedrock- Amazon Bedrock in FSA EDMAPS Assessment for the Department Use",
     "correct", "correct", "correct", "correct", "correct",
     "AWS Bedrock explicitly named. bespoke_application on foundation model platform correct.",
     "high"),

    # 36209 DOT/FHWA — Geolocating and Identifying Vehicle Hard Brake/Acceleration
    # Narrative: AI/ML for big traffic data analytics, connected vehicle data,
    # safety issue geolocation
    # is_generative_ai=0 correct; classical_ml correct; bureau correct;
    # custom_system correct; no product → correct
    (36209, "DOT", "Geolocating and Identifying Vehicle Hard Brake, Acceleration and Seat Belt Usage with CV Data",
     "correct", "correct", "correct", "correct", "correct",
     "Traffic safety AI/ML analytics on connected vehicle data. classical_ml and custom_system correct.",
     "high"),

    # 36212 DOT — Enterprise Knowledge Graph and Advanced AI Data Structures
    # Narrative: DOT-Private Sector collaboration on AI data structure best practices
    # is_generative_ai=0 correct (knowledge graph / data structures, not generative);
    # classical_ml: knowledge graphs are more semantic/database than classical ML.
    # off_by_one; enterprise_wide correct (CAIO, FAA, OST-R, Volpe, OCIO);
    # custom_system correct; no product → correct
    (36212, "DOT", "Enterprise Knowledge Graph and Advanced AI Data Structures Collaboration Group",
     "correct", "off_by_one", "correct", "correct", "correct",
     "Knowledge graph + AI data structures collaboration — more structural/semantic than classical_ml. off_by_one. enterprise_wide correct given cross-agency scope.",
     "medium"),
]

FIELDNAMES = [
    "use_case_id_2024", "agency_abbreviation", "use_case_name",
    "verdict_is_generative_ai", "verdict_ai_sophistication",
    "verdict_deployment_scope", "verdict_entry_type", "verdict_tool",
    "notes", "auditor_confidence"
]

os.makedirs(OUTDIR, exist_ok=True)
with open(OUTPATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(FIELDNAMES)
    for row in ROWS:
        writer.writerow(row)

print(f"Written {len(ROWS)} rows to {OUTPATH}")

# Quick sanity checks
assert len(ROWS) == 82, f"Expected 82 rows, got {len(ROWS)}"
allowed_genai = {"correct", "incorrect"}
allowed_soph = {"correct", "off_by_one", "incorrect"}
allowed_scope = {"correct", "off_by_one_tier", "incorrect"}
allowed_entry = {"correct", "debatable", "incorrect"}
allowed_tool = {"correct", "hallucinated", "missing", "na"}
allowed_conf = {"high", "medium", "low"}

for r in ROWS:
    uid, agency, name, v_gen, v_soph, v_scope, v_entry, v_tool, notes, conf = r
    assert v_gen in allowed_genai, f"{uid}: bad verdict_is_generative_ai: {v_gen}"
    assert v_soph in allowed_soph, f"{uid}: bad verdict_ai_sophistication: {v_soph}"
    assert v_scope in allowed_scope, f"{uid}: bad verdict_deployment_scope: {v_scope}"
    assert v_entry in allowed_entry, f"{uid}: bad verdict_entry_type: {v_entry}"
    assert v_tool in allowed_tool, f"{uid}: bad verdict_tool: {v_tool}"
    assert conf in allowed_conf, f"{uid}: bad auditor_confidence: {conf}"

print("All assertions passed.")
