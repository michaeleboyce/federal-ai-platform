#!/usr/bin/env python3
"""Build recommendations.json for Agent A — slice_a_named_vendor_individual.csv.

Hand-written decisions keyed by use_case_id; pulls metadata from the input CSV
and writes the final JSON array.
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

BASE = Path("/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory")
INPUT = BASE / "audit/linkage_pass_2026-05/inputs/slice_a_named_vendor_individual.csv"
OUT = BASE / "audit/linkage_pass_2026-05/agent_a/recommendations.json"

# Load source rows by id
rows: dict[int, dict] = {}
with INPUT.open() as f:
    r = csv.DictReader(f)
    for row in r:
        rows[int(row["use_case_id"])] = row

# Each decision is a callable that returns a dict, or a literal dict. Helpers:
def link(uid, product_id, canonical_name, quote, notes=""):
    row = rows[uid]
    return {
        "use_case_id": uid,
        "consolidated_use_case_id": None,
        "use_case_agency": row["agency"],
        "decision": "link",
        "product_id": product_id,
        "canonical_name": canonical_name,
        "proposed_canonical_name": None,
        "vendor": None,
        "product_type": None,
        "is_generative_ai": None,
        "proposed_parent_canonical_name": None,
        "proposed_alias": None,
        "proposed_alias_replacement": None,
        "evidence_quote": quote[:120],
        "confidence": "high",
        "reasoning": notes,
        "notes": "",
    }

def add_product(uid, canonical, vendor, product_type, is_gen, quote, reasoning,
                parent=None, confidence="high", alias=None, notes=""):
    row = rows[uid]
    return {
        "use_case_id": uid,
        "consolidated_use_case_id": None,
        "use_case_agency": row["agency"],
        "decision": "add_product",
        "product_id": None,
        "canonical_name": None,
        "proposed_canonical_name": canonical,
        "vendor": vendor,
        "product_type": product_type,
        "is_generative_ai": is_gen,
        "proposed_parent_canonical_name": parent,
        "proposed_alias": alias,
        "proposed_alias_replacement": None,
        "evidence_quote": quote[:120],
        "confidence": confidence,
        "reasoning": reasoning,
        "notes": notes,
    }

def false_positive(uid, quote, reasoning):
    row = rows[uid]
    return {
        "use_case_id": uid,
        "consolidated_use_case_id": None,
        "use_case_agency": row["agency"],
        "decision": "false_positive",
        "product_id": None,
        "canonical_name": None,
        "proposed_canonical_name": None,
        "vendor": None,
        "product_type": None,
        "is_generative_ai": None,
        "proposed_parent_canonical_name": None,
        "proposed_alias": None,
        "proposed_alias_replacement": None,
        "evidence_quote": quote[:120],
        "confidence": "high",
        "reasoning": reasoning,
        "notes": "",
    }

def unclear(uid, quote, reasoning):
    row = rows[uid]
    return {
        "use_case_id": uid,
        "consolidated_use_case_id": None,
        "use_case_agency": row["agency"],
        "decision": "unclear",
        "product_id": None,
        "canonical_name": None,
        "proposed_canonical_name": None,
        "vendor": None,
        "product_type": None,
        "is_generative_ai": None,
        "proposed_parent_canonical_name": None,
        "proposed_alias": None,
        "proposed_alias_replacement": None,
        "evidence_quote": quote[:120],
        "confidence": "low",
        "reasoning": reasoning,
        "notes": "",
    }

# ---------------------------------------------------------------------------
# Decisions list
# ---------------------------------------------------------------------------
decisions = []

# Helper to add the same product when in-house custom system is the AI tool
def custom(uid, canonical, vendor, product_type, is_gen, quote, reasoning,
           parent=None, confidence="medium"):
    return add_product(uid, canonical, vendor, product_type, is_gen, quote,
                       reasoning, parent=parent, confidence=confidence)

D = decisions.append

# 61203 DHS Invariant Corporation -> existing "Invariant Acoustic Signature AI"
# product exists but not linked. Use link by canonical_name (id unknown — V can resolve).
D({
    "use_case_id": 61203, "consolidated_use_case_id": None, "use_case_agency": "DHS",
    "decision": "link", "product_id": None,
    "canonical_name": "Invariant Acoustic Signature AI",
    "proposed_canonical_name": None, "vendor": None, "product_type": None,
    "is_generative_ai": None, "proposed_parent_canonical_name": None,
    "proposed_alias": "Invariant Corporation", "proposed_alias_replacement": None,
    "evidence_quote": "Acoustic Signature AI for Gunshot Detection — vendor Invariant Corporation"[:120],
    "confidence": "high",
    "reasoning": "Catalog has 'Invariant Acoustic Signature AI' (vendor=Invariant Corporation, audio_analysis). Linker missed because alias only matches the canonical literal.",
    "notes": "Add alias 'Invariant Corporation' to the existing product.",
})

# 61212 DHS CBP Translate — custom built; multiple contracting integrators (Deloitte, Aneesh, Ellumen)
D(add_product(61212, "CBP Translate", "U.S. Customs and Border Protection",
              "translation", 0,
              "Assist officers and agents with immediate interpretation needs when human translators are not available.",
              "DHS CBP-built translation system. development_type=contracting+in-house; vendor list is integrators, not AI product vendor. Treat as custom government product.",
              confidence="medium"))

# 61216 DHS Traveler Verification Service — CBP government system (TVS). Custom.
D(add_product(61216, "Traveler Verification Service",
              "U.S. Customs and Border Protection", "biometrics", 0,
              "The TVS Biometric matching service is a cloud-based facial biometric matching service",
              "DHS CBP TVS — federal-built facial biometric matching. Vendor field lists hardware vendors (Apple, Samsung, Logitech), which are not the AI product.",
              confidence="high"))

# 61222 DHS TRM Labs Cryptocurrency Analysis -> existing TRM Labs Blockchain Analysis Platform
D(link(61222, 5149, "TRM Labs Blockchain Analysis Platform",
       "Cryptocurrency Analysis — vendor TRM Labs",
       "Vendor TRM Labs, COTS purchase, crypto-transaction analysis matches existing catalog product."))

# 61227 DHS ERNIE / ARDIS-C — DHS CWMD custom system
D(add_product(61227, "ERNIE Radiological Detection",
              "DHS Countering Weapons of Mass Destruction", "computer_vision", 0,
              "ERNIE is used to analyze Radiation Portal Monitor (RPM) data to enhance the detection of radioactive materials",
              "DHS CWMD-built. Specific named federal system (ARDIS-C). Not COTS.",
              confidence="medium"))

# 61230 DHS Department of State CCD Facial Recognition — DoS-owned system used by DHS
D(add_product(61230, "Consular Consolidated Database Facial Recognition",
              "U.S. Department of State", "biometrics", 0,
              "DHS Components use the Facial Recognition (FR) on Demand report (Visa only) to combat fraud",
              "DoS-owned Consular Consolidated Database FR service consumed by DHS. Distinct gov product.",
              confidence="medium"))

# 61232-61234, 61237 DHS Law Enforcement Sensitive — vendor redacted; no product name
D(unclear(61232, "Law Enforcement Sensitive (LES)",
          "Vendor and system name both 'Law Enforcement Sensitive (LES)'. No product can be identified."))
D(unclear(61233, "Law Enforcement Sensitive (LES)",
          "Vendor and system name both redacted as LES. No identifiable product."))
D(unclear(61234, "Law Enforcement Sensitive (LES)",
          "Vendor and system name both redacted as LES."))
D(unclear(61237, "Law Enforcement Sensitive (LES)",
          "Vendor and system name both redacted as LES."))

# 61235 DHS AIS Resume Screening Tool
D(add_product(61235, "AIS Resume Screening Tool", "AIS",
              "document_ai", 0,
              "AI-Assisted Resume Screening Tool — vendor AIS",
              "Vendor 'AIS' is the company; development_type contracting+in-house; specific tool. Limited public info — flag low confidence on vendor canonicalization.",
              confidence="low"))

# 61238 DHS Leidos+Rohde&Schwarz Low-Pfa Algorithm — TSA AIT/L3Harris/Rohde&Schwarz mmWave
D(add_product(61238, "Rohde & Schwarz QPS Walk-Through Scanner",
              "Rohde & Schwarz", "computer_vision", 0,
              "Low Probability of False Alarm (Low-Pfa) Algorithm for on-person screening",
              "TSA Advanced Imaging Technology — Rohde & Schwarz QPS is the COTS scanner. Leidos is integrator.",
              confidence="medium"))

# 61239 DHS IDEMIA CAT-2 -> existing IDEMIA CAT-2/AutoCAT (5150)
D(link(61239, 5150, "IDEMIA CAT-2/AutoCAT",
       "Credential Authentication Technology with Camera System (CAT-2) and AutoCAT",
       "Exact catalog match by canonical name."))

# 61241 DHS Inadev Text Analytics — custom USCIS
D(add_product(61241, "USCIS Text Analytics",
              "U.S. Citizenship and Immigration Services", "nlp", 0,
              "The Text Analytics capability employs machine learning and data graphing techniques",
              "USCIS-built text analytics platform; Inadev is integrator. Federal product.",
              confidence="medium"))

# 61243 DHS IBM Verification Match Model -> custom
D(add_product(61243, "USCIS Verification Match Model",
              "U.S. Citizenship and Immigration Services", "nlp", 0,
              "unified Verification Match Model within a separate microservice",
              "USCIS-built; IBM is contracting integrator. Discrete federal product.",
              confidence="medium"))

# 61244 DHS Pluribus Digital — USCIS Facial Recognition through IDENT, Customer Profile Management System
D(add_product(61244, "USCIS Customer Profile Management System Facial Recognition",
              "U.S. Citizenship and Immigration Services", "biometrics", 0,
              "I-765 - USCIS Facial Recognition through IDENT (1:1 Face Recognition/Validation)",
              "USCIS-built; Pluribus is integrator. Federal product. IDENT is downstream.",
              confidence="medium"))

# 61245 DHS MetroIBR Person-Centric Identity Services — custom
D(add_product(61245, "Person-Centric Identity Services Deduplication Model",
              "U.S. Citizenship and Immigration Services", "nlp", 0,
              "Person-Centric Identity Services Deduplication Model",
              "USCIS-built; MetroIBR is integrator.",
              confidence="medium"))

# 61247 DHS ATAP — CBP Advanced Trade Analytics Platform
D(add_product(61247, "Advanced Trade Analytics Platform",
              "U.S. Customs and Border Protection", "data_analytics", 0,
              "The Advanced Trade Analytics Platform (ATAP)",
              "CBP-built; Elder Research/DevTech/Guidehouse are integrators.",
              confidence="medium"))

# 61248 DHS Dataminr -> existing Dataminr First Alert (5138)
D(link(61248, 5138, "Dataminr First Alert",
       "Public Information Compilation for Travel Threat Analysis (Dataminr)",
       "Exact vendor match; CBP uses Dataminr open-source threat feed."))

# 61249 DHS Airship Outpost — Airship AI Holdings catalog already has "Airship AI Platform"
D({
    "use_case_id": 61249, "consolidated_use_case_id": None, "use_case_agency": "DHS",
    "decision": "link", "product_id": None,
    "canonical_name": "Airship AI Platform",
    "proposed_canonical_name": None, "vendor": None, "product_type": None,
    "is_generative_ai": None, "proposed_parent_canonical_name": None,
    "proposed_alias": "Airship Outpost", "proposed_alias_replacement": None,
    "evidence_quote": "Airship Outpost for Conveyance Identification — vendor Airship"[:120],
    "confidence": "high",
    "reasoning": "Airship Outpost is Airship AI Holdings' edge product line. Link to existing Airship AI Platform; add alias 'Airship Outpost'.",
    "notes": "",
})

# 61253 DHS PDRI Proctor — Pearson VUE? Actually PDRI is a small contractor; specific custom build.
D(add_product(61253, "PDRI Remote Proctor",
              "PDRI (Pearson)", "computer_vision", 0,
              "Customs Broker License Exam - Proctor Support — Detect potential cheating",
              "PDRI is a Pearson subsidiary providing assessment services. Specific remote-proctor product.",
              confidence="low"))

# 61259 DHS ManTech Passport Anomaly Model — custom CBP/ATS
D(add_product(61259, "ATS Passport Anomaly Model",
              "U.S. Customs and Border Protection", "nlp", 0,
              "The Passport Anomaly Model addresses challenges stemming from the lack of formal notification regarding updates to passport series",
              "Custom CBP/ATS-built; ManTech integrator. Federal product.",
              confidence="medium"))

# 61261 DHS ManTech Trade Entity Risk Model — same ATS
D(add_product(61261, "ATS Trade Entity Risk Model",
              "U.S. Customs and Border Protection", "data_analytics", 0,
              "Trade Entity Risk Model",
              "Custom CBP/ATS-built; ManTech integrator.",
              confidence="medium"))

# 61262 DHS Sandia RAVEn Investigative Prioritization
D(add_product(61262, "RAVEn Investigative Prioritization Aggregator",
              "U.S. Homeland Security Investigations", "data_analytics", 0,
              "Repository for Analytics in a Virtualized Environment ... project utilizes machine learning",
              "HSI's RAVEn platform; Sandia builds models for HSI. Federal-owned.",
              confidence="medium"))

# 61263 DHS Booz Allen Translation/Transcription — within RAVEn
D(add_product(61263, "RAVEn Translation and Transcription Service",
              "U.S. Homeland Security Investigations", "translation", 0,
              "Translation and Transcription Service leverages neural machine translation",
              "HSI/RAVEn capability; Booz Allen integrator.",
              confidence="medium"))

# 61265 DHS LES — Generative AI dark web
D(unclear(61265, "Law Enforcement Sensitive (LES)",
          "Both vendor and system redacted; can't identify product."))

# 61269 DHS BI SmartLINK -> existing 5152
D(link(61269, 5152, "BI SmartLINK",
       "Biometric Check-in for ATD-ISAP (SmartLINK)",
       "Exact match. Vendor 'BI' is BI Incorporated; SmartLINK in title."))

# 61270 DHS CANDA UEBA — vendor CANDA Solutions, system VIEW
D(add_product(61270, "CANDA UEBA",
              "CANDA Solutions", "security_tool", 0,
              "User and Entity Behavior Analytics (UEBA)",
              "CANDA Solutions provides the COTS UEBA tool deployed for DHS VIEW.",
              confidence="medium"))

# 61271 DHS Pluribus Biometrics Enrollment Tool
D(add_product(61271, "Biometrics Enrollment Tool",
              "U.S. Citizenship and Immigration Services", "biometrics", 0,
              "Biometrics Enrollment Tool (BET) Fingerprint Quality Check",
              "USCIS-built BET; Pluribus integrator. Distinct from IDENT/IDEMIA.",
              confidence="medium"))

# 61272 DHS SAIC Name/DOB Harvesting — USCIS ELIS
D(add_product(61272, "ELIS Name and DOB Harvesting Service",
              "U.S. Citizenship and Immigration Services", "nlp", 0,
              "Automated Name and Date of Birth (DOB) Harvesting Service",
              "USCIS ELIS-resident service; SAIC/DV United integrators.",
              confidence="medium",
              parent="ELIS"))

# 61273 DHS ELIS Card Photo Validation
D(add_product(61273, "ELIS Card Photo Validation Service",
              "U.S. Citizenship and Immigration Services", "computer_vision", 0,
              "ELIS Card Photo Validation Service",
              "USCIS ELIS service.",
              confidence="medium"))

# 61279 DHS Starlo and Deloitte — ClassifAI custom PD generator
D(add_product(61279, "ClassifAI",
              "DHS / Starlo", "document_ai", 1,
              "ClassifAI is designed to streamline and enhance the position description (PD) creation",
              "Specific named generative-AI HR tool (ClassifAI) built by Starlo+Deloitte for DHS.",
              confidence="medium"))

# 61288 DHS CISAChat — Microsoft vendor, custom build on Azure OpenAI very likely
D(add_product(61288, "CISAChat",
              "DHS CISA", "general_llm", 1,
              "Currently, retrieving and synthesizing content from hundreds of government documents is a slow",
              "CISA-built RAG chatbot; Microsoft is cloud vendor. Distinct named federal product.",
              confidence="medium"))

# 61289 DHS Nightwing Automated PII Detection — Nightwing Intelligence Solutions
D(add_product(61289, "Nightwing PII Detection",
              "Nightwing Intelligence Solutions", "nlp", 0,
              "AI tool uses Natural Language Processing (NLP) to automatically flag potential PII",
              "Nightwing contractor-built NLP tool for CISA TAXII server.",
              confidence="low"))

# 61302 DHS Booz Allen Normalization Services — HSI/RAVEn
D(add_product(61302, "RAVEn Normalization Services",
              "U.S. Homeland Security Investigations", "data_analytics", 0,
              "HSI utilizes artificial intelligence to enhance data accuracy and efficiency by verifying",
              "HSI/RAVEn capability; Booz Allen integrator.",
              confidence="medium"))

# 61314 DHS SAIC ELIS Evidence Classifier
D(add_product(61314, "ELIS Evidence Classifier Service",
              "U.S. Citizenship and Immigration Services", "document_ai", 0,
              "ELIS Evidence Classifier Service",
              "USCIS ELIS service.",
              confidence="medium"))

# 61317 DHS Steampunk/CVP/AOI AI Interview Simulator
D(add_product(61317, "RAIO AI Interview Simulator",
              "USCIS Refugee, Asylum, and International Operations", "training", 1,
              "AI Interview Simulator for Officer Training",
              "USCIS RAIO-built training simulator; Steampunk/CVP/AOI integrators.",
              confidence="medium"))

# 61598-61605 DOE Microsoft various R&D — Microsoft is hosting vendor not AI product. These are
# all custom DOE research projects. Mark as custom add_product where the system name is the AI.
D(add_product(61598, "APT Analytics", "DOE", "scientific_ml", 0,
              "Automate analysis of atom probe tomography (APT) data",
              "DOE R&D custom; vendor 'Microsoft' is cloud host, not AI vendor.",
              confidence="low"))
D(add_product(61599, "DOE Traffic Predictive Control", "DOE", "scientific_ml", 0,
              "AI used for predictive modeling and real time control of traffic systems",
              "DOE research project; vendor 'Microsoft' is cloud host.",
              confidence="low"))
D(add_product(61601, "SEA-CROGS", "DOE", "scientific_ml", 0,
              "Scalable, Efficient and Accelerated Causal Reasoning Operators, Graphs and Spikes for Earth and Embedded Systems",
              "DOE research project name.",
              confidence="medium"))
D(add_product(61605, "DOE ML for Disadvantaged Community Identification", "DOE",
              "nlp", 0,
              "Parse open-source text to define disadvantaged communities for energy transition planning",
              "DOE research project; Microsoft is cloud host.",
              confidence="low"))

# 61606 DOE Cisco EV parking
D(add_product(61606, "DOE EV Delivery Parking Identification",
              "DOE / Cisco", "scientific_ml", 0,
              "AI techniques for identification of suitable delivery parking spaces in an urban scenario",
              "DOE research with Cisco as research partner.",
              confidence="low"))

# 61616 DOE — vendor "No Vendor Involved". Custom NLCOO Lessons Learned tool.
D(add_product(61616, "NLCOO Lessons Learned AI", "DOE NETL",
              "search", 0,
              "NLCOO AI for Lessons Learned tool",
              "DOE-built; no vendor; AWS hosting.",
              confidence="low"))

# 61629 DOE MAPPRITE — Special Technologies Laboratory
D(add_product(61629, "MAPPRITE",
              "DOE Special Technologies Laboratory", "general_llm", 1,
              "Methodology for Analyzing and Prioritizing Policy Requirements and Integrating Them for Effectiveness (MAPPRITE)",
              "Named DOE STL-built generative AI policy mining tool.",
              confidence="medium"))

# 61641 DOE INL — vendor 'Not available' — custom on Azure
D(add_product(61641, "INL Intelligent Automation", "DOE Idaho National Lab",
              "general_llm", 1,
              "improve the timeliness and quality of manual work processes through automation where generative AI can make comparisons",
              "INL custom genAI automation on Azure.",
              confidence="low"))

# 61661 DOE LANL AI Portal — AWS as hosting
D(add_product(61661, "LANL AI Portal", "DOE Los Alamos National Lab",
              "general_llm", 1,
              "Democratized access to open-source/open-weights Large Language Models (LLMs)",
              "LANL-built LLM portal; AWS hosting.",
              confidence="high"))

# 61672 DOE Microsoft Bing Service — vendor Microsoft, just Bing. Map to Microsoft Search in Bing
D(link(61672, None, "Microsoft Search in Bing",
       "Microsoft Bing Service — DOE GSS, AI auto-integrated",
       "DOE Hanford Microsoft Bing — maps to catalog 'Microsoft Search in Bing'."))

# 61679 DOE Microsoft Co-Pilot — DOE-Hanford
D(link(61679, 4981, "Microsoft 365 Copilot",
       "Microsoft Co-Pilot — DOE Hanford Accreditation Boundary",
       "DOE Hanford Microsoft Copilot; M365 Copilot."))

# 61685 DOE NEPA App — vendor not available
D(unclear(61685, "ESH&Q NEPA App",
          "Vendor 'Not available'; system minimal; insufficient to identify a product."))

# 61690 DOE Merlin — KCNSC open-source build (vLLM, OpenWebUI, GPT-OSS-120b)
D(add_product(61690, "Merlin", "DOE Kansas City National Security Campus",
              "general_llm", 1,
              "Merlin - KCNSC Generative AI with RAG ... vLLM ... GPT-OSS-120b ... OpenWebUI",
              "Named KCNSC-built RAG genAI on open-source stack.",
              confidence="high"))

# 61704 DOE Soil Moisture Modeling — Univ of Montana
D(add_product(61704, "DOE Soil Moisture Modeling",
              "University of Montana", "scientific_ml", 0,
              "Machine learning solves issues with soil moisture",
              "Research partnership; not commercial product, but discrete named research tool.",
              confidence="low"))

# 61711 DOE Microsoft Visual C++ Runtime — Microsoft, AI auto-integrated
D(false_positive(61711, "AI was automatically integrated into the product without an identified benefit",
                 "Microsoft Visual C++ Runtime is not an AI product; agency only filed because of auto-integration. Not a real AI deployment."))

# 61714 DOE SRNS - OT In House Staff
D(custom(61714, "SRNS Computer Vision Defect Detection",
         "Savannah River Nuclear Solutions", "computer_vision", 0,
         "Computer Vision for Defect Detection — SRNS - OT In House Staff",
         "In-house SRNS computer-vision QC. Federal site contractor build.",
         confidence="low"))

# 61717 DOE Nuclear Safety Analysis — vendor not available
D(unclear(61717, "Not available",
          "Vendor not available; insufficient to identify."))

# 61723 DOE Safeguards Digital Twin — vendor not available
D(unclear(61723, "Not available", "Vendor not available."))

# 61730 DOE GitHub Co-Pilot
D(link(61730, 4985, "GitHub Copilot",
       "GitHub Co-Pilot — DOE Hanford",
       "Exact match."))

# 61734 DOE EDMS Admin — vendor not available
D(unclear(61734, "Not available", "Vendor not available; only system 'EDMS' named."))

# 61737 DOE Project Optimus — vendor not available
D(unclear(61737, "Not available", "Vendor not available."))

# 61752 DOE Microsoft Visual C++ Redistributable
D(false_positive(61752, "AI was automatically integrated into the product without an identified benefit",
                 "Microsoft Visual C++ Redistributable is not an AI product."))

# 61767 DOE SRNS AI-Tailored Learning
D(custom(61767, "SRNS AI Tailored Learning",
         "Savannah River Nuclear Solutions", "training", 1,
         "AI-Tailored Learning Management Solutions",
         "SRNS in-house genAI training tool."))

# 61780 DOE Microsoft MSPaint
D(false_positive(61780, "AI was automatically integrated into the product without an identified benefit",
                 "MSPaint is not an AI product."))

# 61781 DOE AGN-201 DT — vendor not available
D(unclear(61781, "Not available", "Vendor not available."))

# 61783 DOE SRNS AI Drafting
D(custom(61783, "SRNS AI Drafting Assistant",
         "Savannah River Nuclear Solutions", "general_llm", 1,
         "To automate and enhance the drafting of operational procedures and training materials",
         "SRNS in-house genAI drafting tool."))

# 61793 DOE QuantomVision — vendor Open AI (very likely typo for OpenAI)
D(link(61793, 4989, "ChatGPT",
       "QuantomVision — vendor Open AI",
       "Vendor 'Open AI' = OpenAI; specific product unnamed, treat as ChatGPT link."))

# 61802 DOE Georeference Figures — vendor 'Tesseract'
D(link(61802, 5154, "Tesseract OCR",
       "Georeference Figures — vendor Tesseract",
       "Exact catalog match. OCR for paper map digitization."))

# 61809 DOE Advanced Fuels Campaign — vendor not available
D(unclear(61809, "Not available", "Vendor not available."))

# 61816 DOE Groundwater Modeling — vendor PEST
D({
    "use_case_id": 61816, "consolidated_use_case_id": None, "use_case_agency": "DOE",
    "decision": "link", "product_id": None,
    "canonical_name": "PEST (Parameter Estimation)",
    "proposed_canonical_name": None, "vendor": None, "product_type": None,
    "is_generative_ai": None, "proposed_parent_canonical_name": None,
    "proposed_alias": None, "proposed_alias_replacement": None,
    "evidence_quote": "Groundwater Modeling — vendor PEST",
    "confidence": "high",
    "reasoning": "PEST is in catalog (Parameter Estimation, scientific_ml).",
    "notes": "",
})

# 61820 DOE DevSec Ops AI — vendor not available
D(unclear(61820, "Not available", "Vendor not available."))

# 61825 DOE Microsoft Visual C++ Minimum Runtime
D(false_positive(61825, "AI was automatically integrated into the product",
                 "MS Visual C++ Minimum Runtime is not an AI product."))

# 61830 DOE LISA Chatbot — AWS
D(add_product(61830, "LISA Chatbot", "DOE / AWS",
              "general_llm", 1,
              "LISA Chatbot Pilot ... Quick access to specific mission data sets",
              "Specific named DOE chatbot pilot on AWS.",
              confidence="medium"))

# 61832 DOE Climate Weather Data — vendor not available
D(unclear(61832, "Not available", "Vendor not available."))

# 61834 DOE EES&T Document Processing — vendor not available
D(unclear(61834, "Not available", "Vendor not available."))

# 61848 DOE COREII — vendor garbled date
D(add_product(61848, "COREII", "DOE Idaho National Lab",
              "general_llm", 1,
              "Support decision making for critical infrastructure OT cybersecurity operations",
              "Named INL OT-cyber genAI. Vendor field is a date string (likely a CSV corruption); use case+system suffice.",
              confidence="medium"))

# 61849 DOE GenAI Classified Subject Area — INL Advanced Analytics CoE
D(add_product(61849, "INL Classified Subject Area GenAI",
              "DOE Idaho National Lab", "general_llm", 1,
              "Help users, DCs and classification analysts more quickly determine Classified Subject Areas",
              "INL in-house genAI classifier.",
              confidence="low"))

# 61863 DOE SRNS Form/Questionnaire
D(custom(61863, "SRNS AI Form and Questionnaire Assistant",
         "Savannah River Nuclear Solutions", "general_llm", 1,
         "To automate and enhance the completion of standard forms and questionnaires",
         "SRNS in-house genAI."))

# 61869 DOE ALTEMIS — vendor 'Python'
D(false_positive(61869, "vendor 'Python'",
                 "Vendor 'Python' is a programming language, not an AI vendor. The model is custom; flag as not-a-vendor-product."))

# 61881 DOE SRNS ML operational efficiency
D(custom(61881, "SRNS Operational Efficiency ML",
         "Savannah River Nuclear Solutions", "data_analytics", 0,
         "Machine Learning to support Operational Efficiency",
         "SRNS in-house ML."))

# 61888 DOE Chatlab — vendor not available
D(unclear(61888, "Not available", "Vendor not available."))

# 61889 DOE CoPilot — Microsoft, DOE GSS
D(link(61889, 4981, "Microsoft 365 Copilot",
       "CoPilot — vendor Microsoft, DOE GSS, Other",
       "Microsoft Copilot at DOE Hanford GSS."))

# 61894 DOE Geo Threat Observable — vendor not available
D(unclear(61894, "Not available", "Vendor not available."))

# 61898 DOE EES&T Communications — vendor not available
D(unclear(61898, "Not available", "Vendor not available."))

# 61904 DOE Deep Learning Malware Analysis — vendor not available
D(unclear(61904, "Not available", "Vendor not available."))

# 61918 DOI NASA — Level 1 Survey Report Corrosion. NASA is partner not vendor.
D(add_product(61918, "BSEE Corrosion Classifier",
              "Bureau of Safety and Environmental Enforcement", "computer_vision", 0,
              "Level 1 Survey Report Corrosion Level Classification ... NASA partnership",
              "BSEE-built; NASA technical partner. Federal product.",
              confidence="medium"))

# 61985 DOI Google ML Wetlands — Google Earth Engine likely
D(add_product(61985, "Google Earth Engine Wetlands Classifier",
              "Google", "scientific_ml", 0,
              "Machine Learning Image Classification of Wetlands and Soil moisture",
              "DOI USGS use of Google ML; specific tool likely Google Earth Engine. Low confidence on canonical.",
              confidence="low"))

# 62024 DOI Ultralytics
D(add_product(62024, "Ultralytics YOLO", "Ultralytics",
              "computer_vision", 0,
              "AI to survey boat traffic ... scanning video",
              "Ultralytics is the maker of the YOLO object-detection library; this is the boat-traffic scanner.",
              confidence="high"))

# 62044 DOI Open Geospatial Consortium — wildfire risk
D(false_positive(62044, "vendor Open Geospatial Consortium",
                 "OGC is a standards body, not an AI vendor. The use case is custom modeling work using OGC standards."))

# 62055 DOI Walker Environmental Research — USGS Flow Photo Explorer
D(add_product(62055, "USGS Flow Photo Explorer",
              "USGS / Walker Environmental Research", "scientific_ml", 0,
              "Flow Photo Explorer (FPE) is an integrated database, machine learning, and data visualization platform",
              "USGS named tool, built by Walker Environmental Research.",
              confidence="high"))

# 62154 DOI Microsoft CoPilot for GitHub
D(link(62154, 4985, "GitHub Copilot",
       "Integration of AI, specifically CoPilot for GitHub",
       "CoPilot for GitHub = GitHub Copilot."))

# 62161 DOJ Azure Zen 2 Storage — Microsoft. Azure Platform automatic indexing.
D(link(62161, 5131, "Microsoft Azure Platform",
       "Azure Zen 2 Storage ... smart features automatic data indexing",
       "DOJ ATF Azure Storage smart indexing — link to Microsoft Azure Platform."))

# 62169 DOJ Federal Docket Management System — GSA
D(add_product(62169, "Federal Docket Management System",
              "GSA", "document_ai", 0,
              "Federal Docket Management System ... categorize comments based on text analytics",
              "GSA-run FDMS / Regulations.gov text-analytics features. Federal product.",
              confidence="medium"))

# 62170 DOJ FINDER — vendor FINDER (system name)
D(add_product(62170, "FINDER (ATF)", "DOJ ATF",
              "data_analytics", 0,
              "FINDER ... sift through violent crime and firearms trafficking data",
              "ATF named system; vendor field repeats system name (custom build).",
              confidence="low"))

# 62179 DOJ Western Union — SWBTRAC. Western Union is data partner not AI vendor.
D(add_product(62179, "SWBTRAC", "DOJ",
              "data_analytics", 0,
              "Southwest Border Transaction Record Analysis Center (SWBTRAC)",
              "DOJ-run SWBTRAC; Western Union is data provider. Federal product.",
              confidence="medium"))

# 62199 DOJ AWS/cloud.gov Network Routing — Amazon
D(link(62199, None, "AWS",
       "AWS/cloud.gov - Network Routing — vendor Amazon",
       "AWS network routing — no specific named AI product. Likely best mapped to a generic AWS canonical; flag for V to pick existing AWS row."))

# 62200 DOJ Azure Platform/Tools - Network Routing
D(link(62200, 5131, "Microsoft Azure Platform",
       "Azure Platform/Tools - Network Routing — vendor Microsoft",
       "Azure platform network routing."))

# 62226 DOJ NVIDIA GenAI Sandbox — NVIDIA
D(add_product(62226, "DEA GenAI R&D Sandbox",
              "DEA / NVIDIA", "general_llm", 1,
              "Generative AI R&D Sandbox ... DEA to test and prototype Generative AI",
              "DEA NVIDIA-powered sandbox; custom federal build.",
              confidence="medium"))

# 62264 DOJ ASCVD Risk Estimator — American College of Cardiology
D(add_product(62264, "ASCVD Risk Estimator",
              "American College of Cardiology", "clinical_decision_support", 0,
              "ASCVD (Atherosclerotic Cardiovascular Disease) Risk Estimator",
              "Public ACC clinical risk calculator used by FBOP.",
              confidence="high"))

# 62266 DOJ Microsoft — Automated Staffing Tool. FBOP custom.
D(add_product(62266, "FBOP Automated Staffing Tool", "DOJ FBOP",
              "data_analytics", 0,
              "Automated Staffing Tool ... assess staffing levels within the FBOP",
              "FBOP-built; Microsoft is cloud/AI host. Custom federal tool.",
              confidence="low"))

# 62277 DOJ Pathfinder — Azure
D(add_product(62277, "FBOP Pathfinder", "DOJ FBOP",
              "training", 0,
              "Pathfinder ... assist FBOP employees with career pathways",
              "FBOP-built on Azure.",
              confidence="low"))

# 62286 DOJ Truview — Advanced Technologies Group
D(add_product(62286, "Truview", "Advanced Technologies Group",
              "data_analytics", 0,
              "Truview ... TRU, visiting, case management, and volunteer systems",
              "Vendor ATG provides Truview correctional analytics platform.",
              confidence="medium"))

# 62291 DOJ Exiger DDIQ Research Engine
D(link(62291, 5141, "Exiger DDIQ",
       "Exiger Supply Chain Risk Management - DDIQ Research Engine",
       "Exact match."))

# 62292 DOJ Exiger DDIQ Due Diligence Analytics
D(link(62292, 5141, "Exiger DDIQ",
       "Exiger Supply Chain Risk Management - DDIQ Due Diligence Analytics",
       "Exact match."))

# 62309 DOJ Axon
D(add_product(62309, "Axon", "Axon Enterprise",
              "media_analysis", 1,
              "Axon ... captures raw video and audio footage ... AI functionalities for analysis",
              "Axon Body camera + Axon AI/Justice platform. Vendor-named, COTS.",
              confidence="high",
              alias="Axon"))

# 62323 DOJ JAWS — Freedom Scientific
D(add_product(62323, "JAWS Screen Reader", "Freedom Scientific",
              "productivity", 1,
              "JAWS (Text-to-Speech Assistant for Accessibility)",
              "JAWS is a real COTS accessibility product (now with AI image description).",
              confidence="high"))

# 62338 DOJ Amazon Voicemail Transcription — AWS Transcribe-ish
D(link(62338, 4999, "AWS Transcribe",
       "Voicemail Transcription, Translation and Summarization — vendor Amazon, GCC High",
       "Likely AWS Transcribe + Translate. Pick Transcribe as primary link."))

# 62389 DOJ FOIA Production Tools — FOIA Xpress, Forum One, Adobe, Polydelta
D(link(62389, 5191, "FOIAXpress AI",
       "FOIA Production Tools — FOIA Xpress ... FOIAXpress",
       "FOIA Xpress = FOIAXpress AI. Multi-vendor row; primary product is FOIAXpress."))

# 62391 DOJ Microsoft — Receipts extraction
D(add_product(62391, "DOJ Receipt Extraction Tool",
              "DOJ / Microsoft", "document_ai", 0,
              "Extracting Data from Receipts to Speed Travel Reimbursement",
              "DOJ-built on Microsoft (likely Azure Document Intelligence). Custom.",
              confidence="low"))

# 62406 DOJ GitHub+Microsoft Code Development
D(link(62406, 4985, "GitHub Copilot",
       "Code Development — vendor GitHub, Microsoft",
       "GitHub+Microsoft for code dev = GitHub Copilot."))

# 62416 DOJ TransUnion Background Searches
D(add_product(62416, "TransUnion TLOxp", "TransUnion",
              "data_analytics", 0,
              "Background Searches ... TransUnion Risk and Alternative Data Solutions",
              "TransUnion's investigative search product (TLOxp) used for background checks.",
              confidence="medium"))

# 62421 DOJ MIT Lincoln Lab Transcription/Translation
D(add_product(62421, "MIT Lincoln Lab Speech Translation",
              "MIT Lincoln Laboratory", "translation", 0,
              "Audio and Written Transcription and Translation ... Spanish and Mandarin Chinese",
              "MIT LL research-grade NMT/ASR system used by DOJ.",
              confidence="medium"))

# 62424 DOJ Bates White using Microsoft Azure
D(add_product(62424, "Bates White Economic Consulting AI",
              "Bates White", "data_analytics", 1,
              "ATR Expert/Consulting with Bates White ... using Microsoft Azure",
              "Bates White-built economic-analysis AI on Azure for DOJ ATR.",
              confidence="low"))

# 62443 DOJ Adobe Premiere -> Adobe Creative Cloud Suite parent
D({
    "use_case_id": 62443, "consolidated_use_case_id": None, "use_case_agency": "DOJ",
    "decision": "add_product", "product_id": None,
    "canonical_name": None, "proposed_canonical_name": "Adobe Premiere Pro",
    "vendor": "Adobe", "product_type": "media_analysis", "is_generative_ai": 1,
    "proposed_parent_canonical_name": "Adobe Creative Cloud Suite",
    "proposed_alias": "Adobe Premiere", "proposed_alias_replacement": None,
    "evidence_quote": "Adobe Premiere ... Seamless editing of videos and speech transcripts",
    "confidence": "high",
    "reasoning": "Adobe Premiere Pro is a named child product under Adobe Creative Cloud Suite. Add as new product with parent.",
    "notes": "",
})

# 62458 DOL Audio Transcription — Azure PIID
D(link(62458, 5131, "Microsoft Azure Platform",
       "Audio Transcription ... Azure PIID",
       "Azure-hosted custom transcription; closest catalog product is Microsoft Azure Platform (general). Could also be Azure Speech."))

# 62462 DOL Hololens — BGC/CLIRIO; system Hololens
D(link(62462, 5165, "Microsoft HoloLens",
       "Hololens ... AI used to train Inspectors",
       "MSHA HoloLens deployment."))

# 62466 DOL Synergy/Azure Automatic Document Processing
D(link(62466, 5131, "Microsoft Azure Platform",
       "Automatic Document Processing ... Azure PIID",
       "Azure-hosted document AI."))

# 62474 DOL BLS — vendor is a contract number (1605TA-21-F-00064)
D(custom(62474, "BLS Expenditure Classification Autocoder",
         "Bureau of Labor Statistics", "data_analytics", 0,
         "Expenditure Classification Autocoder ... BLS Internal System",
         "BLS-built; vendor field is a contract PIID, not a vendor name. Custom federal.",
         confidence="medium"))

# 62475 DOL Amazon PII Redaction
D(link(62475, None, "Amazon Comprehend",
       "Using Amazon Web Services Personal Identifying Information scrubber",
       "AWS Comprehend PII detection — no exact catalog row; flag V to add or map to AWS generic."))

# 62476 DOL AWS+Synergy WRP Chatbot Lex
D(link(62476, 5228, "AWS Lex",
       "WRP Website Chatbot ... Amazon Lex",
       "Amazon Lex chatbot."))

# 62479 DOL Worker PLUS — vendor is contract number
D(custom(62479, "Worker PLUS",
         "Department of Labor", "data_analytics", 0,
         "Worker Paid Leave Usage Simulation (Worker PLUS) is an open-source simulation tool",
         "DOL-built open-source policy simulator; vendor field is contract PIID.",
         confidence="medium"))

# 62483 DOL Note Taking Bot — Azure/Synergy
D(custom(62483, "DOL Auntee Bot", "Department of Labor",
         "productivity", 1,
         "Note Taking Bot ... AUNTEE BOT ... summarize the meeting notes",
         "DOL-built genAI meeting notes bot on Azure.",
         confidence="low"))

# 62493 DOL ResolveSoft AI Headset — MSHA
D(add_product(62493, "MSHA AI Headset", "ResolveSoft",
              "computer_vision", 0,
              "AI Headset ... ResolveSoft ... MSHA AI Head Gear",
              "ResolveSoft-provided AI headset for MSHA mine inspectors.",
              confidence="medium"))

# 62567 ED Aidan Chat-bot — Accenture
D(add_product(62567, "FSA Aidan Chatbot", "U.S. Department of Education / Accenture",
              "general_llm", 0,
              "Aidan Chat-bot ... Federal Student Aid's virtual assistant",
              "FSA's Aidan; Accenture integrator. Federal product, very high traffic.",
              confidence="high"))

# 62568 ED iCatalyst IPAC RPA -> iCatalyst RPA
D(link(62568, 5127, "iCatalyst RPA",
       "IPAC RPA Bot ... iCatalyst Inc",
       "Exact match."))

# 62569 ED Skillsoft CAISY
D(link(62569, 5390, "Skillsoft Percipio CAISY",
       "CAISY - Artificial Intelligence System Skillsoft Percipio",
       "Exact match."))

# 62572-62575 ED iCatalyst RAG Chatbots
for uid in (62572, 62573, 62574, 62575):
    D(link(uid, 5127, "iCatalyst RPA",
           rows[uid]["use_case_name"] + " — vendor iCatalyst Inc",
           "iCatalyst-built RAG chatbots for ED. Same vendor as 62568."))

# 62623 EPA Savan Group ARMS
D(add_product(62623, "EPA Agency Records Management System",
              "EPA", "document_ai", 0,
              "Agency Records Management System (ARMS) ... reduce burden on staff when identifying appropriate records schedules",
              "EPA-built ARMS; Savan Group integrator.",
              confidence="medium"))

# 62628 EPA University of Chicago RCRA PA
D(add_product(62628, "EPA RCRA PA",
              "EPA", "data_analytics", 0,
              "Risk scoring of Large Quantity Generators (LQGs) to support RCRA inspections",
              "EPA-built risk model; University of Chicago Energy & Environment Lab research partner.",
              confidence="medium"))

# 62669 FDIC CLEAR — Thomson Reuters
D(link(62669, 5125, "Thomson Reuters CLEAR",
       "Criminal Background Investigation — vendor CLEAR",
       "FDIC use of Thomson Reuters CLEAR for background checks."))

# 62670 FDIC Equifax/TransUnion — Financial Background
D(add_product(62670, "Equifax Background Screening", "Equifax",
              "data_analytics", 0,
              "Financial Background Investigation — Equifax, Trans Union",
              "Equifax+TransUnion credit/background screening. Add Equifax primary; TransUnion already proposed elsewhere.",
              confidence="medium",
              alias="Equifax"))

# 62673 FDIC CLEAR
D(link(62673, 5125, "Thomson Reuters CLEAR",
       "Background Check Web Application ... CLEAR service",
       "CLEAR background check."))

# 62678 FDIC CLEAR for fraud
D(link(62678, 5125, "Thomson Reuters CLEAR",
       "Background Check Tool for Fraud Investigations ... CLEAR",
       "CLEAR fraud investigation."))

# 62681 FDIC Adobe, Auto Split, Microsoft, Scan Writer, Social Discovery — OIG forensics
D(unclear(62681, "Adobe, Auto Split, Microsoft, Scan Writer, Social Discovery",
          "Multi-vendor forensics stack; no single product identifiable. Auto Split, Scan Writer, Social Discovery are vendor names; cannot canonicalize confidently."))

# 62682 FERC Zvolvant — Summarization & Policy Analysis
D(add_product(62682, "FERC Zvolvant Comment Analysis", "Zvolvant",
              "nlp", 0,
              "Summarization & Policy Analysis for Regulatory Comments ... Zvolvant (Small Business)",
              "Zvolvant SBA-vendor genAI comment analyzer for FERC.",
              confidence="medium"))

# 62683 FERC Zvolvant Safety Inspections
D(add_product(62683, "FERC Zvolvant Inspection AI", "Zvolvant",
              "computer_vision", 0,
              "Improve Safety Inspections ... dam and LNG pipeline structure inspections",
              "Zvolvant FERC inspection AI.",
              confidence="medium"))

# 62684 FERC Zvolvant Market Surveillance
D(add_product(62684, "FERC Zvolvant Market Surveillance", "Zvolvant",
              "data_analytics", 0,
              "Enhance Market Surveillance and Fraud Detection",
              "Zvolvant FERC market surveillance AI.",
              confidence="medium"))

# 62685 FERC Zvolvant Interconnection
D(add_product(62685, "FERC Zvolvant Interconnection Assistant", "Zvolvant",
              "nlp", 1,
              "Support Interconnection Request Responses",
              "Zvolvant FERC interconnection backlog AI.",
              confidence="medium"))

# 62686 FERC Zvolvant Gas Blanket Certificates
D(add_product(62686, "FERC Zvolvant Permitting Assistant", "Zvolvant",
              "nlp", 1,
              "Gas Blanket Certificates (Permitting) ... classification, tracking, and summarization",
              "Zvolvant FERC permitting genAI.",
              confidence="medium"))

# 62687 FERC Thomson Reuters Legal Research
D(link(62687, 5001, "Westlaw AI",
       "AI Enabled Assistant Legal Research — vendor Thomson Reuters",
       "FERC Thomson Reuters legal research = Westlaw AI / CoCounsel."))

# 62699 FHFA Microsoft SQL Server analytics
D(add_product(62699, "Microsoft SQL Server Intelligent Query Processing",
              "Microsoft", "data_analytics", 0,
              "Analytics, Indexing, and Anomaly Detection for Data Management on SQL Server",
              "Microsoft SQL Server IQP/Anomaly features. Distinct from Azure Platform.",
              confidence="medium",
              parent="Microsoft Azure Platform"))

# 62714 FRB Body Worn Cameras — Third Party Vendor (no name)
D(unclear(62714, "Third Party Vendor",
          "Vendor literally 'Third Party Vendor' — no product identifiable."))

# 62739 FRB Virtual Benefits Assistant — Benefits Manager
D(add_product(62739, "Benefits Manager Virtual Assistant",
              "Benefits Manager", "general_llm", 1,
              "Virtual Benefits Assistant ... Benefits Manager",
              "Vendor and system both 'Benefits Manager'. Likely the benefits-admin SaaS Benefits Manager.",
              confidence="low"))

# 62742-62744 FRTIB Accenture Converge — AVA, Fraud, Contact Center
D(add_product(62742, "FRTIB AVA", "FRTIB / Accenture Federal Services",
              "general_llm", 1,
              "AVA ... Assist with participant questions",
              "FRTIB participant assistant on Accenture Converge platform.",
              confidence="medium"))
D(add_product(62743, "FRTIB Fraud Detection", "FRTIB / Accenture Federal Services",
              "data_analytics", 0,
              "Fraud Detection Platform ... Converge",
              "FRTIB fraud detection on Accenture Converge.",
              confidence="medium"))
D(add_product(62744, "FRTIB Contact Center AI", "FRTIB / Accenture Federal Services",
              "general_llm", 1,
              "Contact Center AI ... Converge",
              "FRTIB contact center AI on Accenture Converge.",
              confidence="medium"))

# 62748-62754 FTC Leidos Sentinel — all custom FTC Sentinel modules
for (uid, name, ptype, gen) in [
    (62748, "FTC Sentinel PSC Classification", "data_analytics", 0),
    (62750, "FTC Sentinel Chatbot", "general_llm", 0),
    (62752, "FTC Sentinel Graph Analytics", "data_analytics", 0),
    (62753, "FTC Sentinel Analytic Sandbox", "data_analytics", 0),
    (62754, "FTC Sentinel Developer Productivity", "coding_assistant", 1),
]:
    D(add_product(uid, name, "FTC / Leidos", ptype, gen,
                  rows[uid]["use_case_name"] + " — Sentinel Network Services",
                  "FTC Sentinel platform module; Leidos prime integrator.",
                  confidence="medium",
                  parent="FTC Sentinel Network Services"))

# 62760 FTC Amazon IVR
D(link(62760, 5228, "AWS Lex",
       "IVR Automated Voice Assistant — vendor Amazon, Sentinel",
       "AWS Lex IVR for FTC."))

# 62761 FTC Amazon GenAI Mail Scan
D(add_product(62761, "FTC GenAI Mail Scan", "FTC / Amazon",
              "document_ai", 1,
              "GenAI Mail Scan ... interpreting handwritten and poorly formatted documents",
              "FTC handwritten-mail processor on AWS (likely Textract+Bedrock).",
              confidence="medium"))

# 62828 HHS MIT Lincoln Labs UC Program Research Tool
D(add_product(62828, "ORR Unaccompanied Children Policy Research Tool",
              "HHS Office of Refugee Resettlement", "general_llm", 1,
              "Unaccompanied Children Program Policy & Procedure Research Tool ... ACF Horizon",
              "ACF/ORR-built; MIT Lincoln Labs research partner.",
              confidence="medium"))

# 62958 HHS UIPath ORPA -> UiPath
D(link(62958, 5408, "UiPath Enterprise RPA",
       "OFR Robotics and Process Automation (ORPA) ... UIPath",
       "UiPath RPA at HHS OFR."))

# 62966 HHS L&M Policy Research comment triaging
D(add_product(62966, "L&M Policy Research Comment Triaging",
              "L&M Policy Research, LLC", "nlp", 0,
              "AI-assisted comment triaging tool ... L&M Policy Research, LLC",
              "Vendor L&M Policy Research-built triage tool.",
              confidence="low"))

# 62979 HHS Skyward CLAW (CEDAR) -> existing Skyward CEDAR/CLAW (5129)
D(link(62979, 5129, "Skyward CEDAR/CLAW",
       "CMS Labor Analysis Wizard (CLAW) ... Skyward Solutions ... CEDAR",
       "Exact match."))

# 62981 HHS Skyward AI Workspace
D(link(62981, 5129, "Skyward CEDAR/CLAW",
       "AI Workspace ... Skyward Solutions ... CEDAR",
       "Skyward CEDAR module."))

# 62993 HHS Skyward IT Solutions CMS Chat
D(link(62993, 5129, "Skyward CEDAR/CLAW",
       "CMS Chat ... Skyward IT Solutions ... CEDAR",
       "Skyward CEDAR module."))

# 63009 HHS commonFont and AWS — Medicare Customer Insights
D(add_product(63009, "CMS Medicare AI Customer Insights",
              "CMS / commonFont", "data_analytics", 1,
              "Medicare AI Customer Insights ... commonFont and AWS",
              "CMS-commonFont AWS-hosted customer insights tool.",
              confidence="low"))

# 63016 HHS Noblis AI Agent Orchestrator
D(add_product(63016, "CMS AI Agent Orchestrator",
              "CMS / Noblis", "agent_platform", 1,
              "AI Agent Orchestrator POC ... orchestrate complex, multi-step analytical workflows",
              "CMS PoC with Noblis. Named tool.",
              confidence="medium",
              parent="Skyward CEDAR/CLAW"))

# 63034 HHS GDIT IDR CAE
D(add_product(63034, "CMS Integrated Data Repository Customer Analytic Environment",
              "CMS / GDIT", "ml_platform", 0,
              "Integrated Data Repository (IDR) Customer Analytic Environment (CAE)",
              "CMS IDR/CAE ML platform.",
              confidence="medium"))

# 63035 HHS GDIT IDR Support Bot
D(add_product(63035, "CMS IDR Support Bot",
              "CMS / GDIT", "general_llm", 1,
              "IDR Support Bot ... retrieval-augmented generation",
              "CMS IDR support chatbot.",
              confidence="medium",
              parent="CMS Integrated Data Repository Customer Analytic Environment"))

# 63036 HHS Peraton ELMO Chatbot
D(add_product(63036, "CMS ELMO Chatbot",
              "CMS / Peraton", "general_llm", 1,
              "Eligibility & Enrollment Medicare Online (ELMO) Chatbot",
              "Peraton-built CMS chatbot.",
              confidence="medium"))

# 63042-63057 HHS FDA Deloitte CDEROne — many FDA AI tools
for (uid, name, ptype, gen) in [
    (63042, "FDA 356H ML Facility Supply Chain Role Classification", "document_ai", 0),
    (63048, "FDA Annual Report CMC Extraction", "document_ai", 1),
    (63049, "FDA Application-DMF Reference Extraction", "document_ai", 0),
    (63050, "FDA DMF Facilities Extraction", "document_ai", 0),
    (63053, "FDA Module 3 Facilities Extraction", "document_ai", 1),
    (63054, "FDA Packaging Materials and Suppliers Extraction", "document_ai", 1),
    (63056, "FDA Real World Data/Evidence Identification", "document_ai", 1),
    (63057, "FDA Regulatory Starting Materials Extraction", "document_ai", 1),
]:
    D(add_product(uid, name, "FDA / Deloitte", ptype, gen,
                  rows[uid]["use_case_name"] + " — CDEROne Analytics",
                  "FDA CDEROne extraction pipeline; Deloitte integrator. Distinct named module.",
                  confidence="medium",
                  parent="FDA CDEROne Analytics"))

# 63060 HHS SAIC HIVE AI Pilot
D(add_product(63060, "FDA HIVE AI Pilot",
              "FDA / SAIC", "general_llm", 1,
              "HIVE AI Pilot ... review process for INDs",
              "FDA HIVE genAI for IND review.",
              confidence="medium"))

# 63062 HHS NCTR CDER Publications
D(add_product(63062, "FDA CDER Pubs", "FDA",
              "nlp", 0,
              "CDER Publications ... CDER Pubs",
              "FDA-built; NCTR research arm.",
              confidence="medium"))

# 63067 HHS Deloitte Safety Reports Bot
D(add_product(63067, "FDA Safety Reports Categorization Bot",
              "FDA / Deloitte", "document_ai", 0,
              "Category Subcategory Classification - Safety Reports Bot",
              "FDA safety reports automation.",
              confidence="medium"))

# 63068 HHS ThinkTrends IND Safety Reports OCR
D(add_product(63068, "FDA IND Safety Reports OCR",
              "FDA / ThinkTrends", "document_ai", 0,
              "Data Extraction from IND Safety Reports using OCR/AI Technologies",
              "FDA FAERS OCR pipeline.",
              confidence="medium"))

# 63093 HHS Trigent/Digitrix PLATES -> existing 5179
D(link(63093, 5179, "PLATES/FoodTrak",
       "Product Label and Text Extraction System (PLATES) ... Trigent Solutions",
       "Exact match."))

# 63095 HHS Deloitte SSDM
D(add_product(63095, "FDA Smart Solution for Docket Management",
              "FDA / Deloitte", "nlp", 1,
              "Smart Solution for Docket Management (SSDM)",
              "FDA docket comment-management genAI.",
              confidence="medium"))

# 63104 HHS Precise Software Filer Evaluation -> Precise MLaaS
D({
    "use_case_id": 63104, "consolidated_use_case_id": None, "use_case_agency": "HHS",
    "decision": "link", "product_id": None,
    "canonical_name": "Precise MLaaS",
    "proposed_canonical_name": None, "vendor": None, "product_type": None,
    "is_generative_ai": None, "proposed_parent_canonical_name": None,
    "proposed_alias": None, "proposed_alias_replacement": None,
    "evidence_quote": "Filer Evaluation prioritization ... Precise Software Solutions, Inc.",
    "confidence": "high",
    "reasoning": "Precise Software Solutions = catalog 'Precise MLaaS'.",
    "notes": "",
})

# 63109 HHS Mindpetal AIARA
D(add_product(63109, "HRSA AI Audit Resolution Assistant",
              "HRSA / Mindpetal", "agent_platform", 1,
              "AI Audit Resolution Assistant (AIARA) ... UiPath Automation Cloud",
              "HRSA-built; Mindpetal integrator; UiPath underlying.",
              confidence="medium"))

# 63110 HHS Publicis Sapient Knowledge Navigator (BMISS)
D(add_product(63110, "HRSA Knowledge Navigator",
              "HRSA / Publicis Sapient", "general_llm", 1,
              "Knowledge Navigator ... Application and Program Guidance (APG)",
              "HRSA-built genAI for loan repayment programs.",
              confidence="medium"))

# 63113 HHS GDIT PRF Chatbot
D(add_product(63113, "HRSA PRF Program Chatbot",
              "HRSA / GDIT", "general_llm", 1,
              "PRF Program Chatbot",
              "HRSA-built genAI; GDIT integrator.",
              confidence="medium"))

# 63138 HHS Deloitte DAIT AIDS Research
D(add_product(63138, "NIAID DAIT AIDS Research Prioritization",
              "NIAID / Deloitte", "data_analytics", 0,
              "DAIT AIDS-Related Research Solution",
              "NIAID-built; Deloitte integrator.",
              confidence="medium"))

# 63142 HHS Deloitte FITARA
D(add_product(63142, "HHS FITARA Tool",
              "HHS / Deloitte", "document_ai", 0,
              "Federal IT Acquisition Reform Act (FITARA) Tool",
              "HHS contracting tool.",
              confidence="medium"))

# 63145 HHS Leidos+Highrise IRM eRA
D(add_product(63145, "NIH eRA Internal Referral Module",
              "NIH / Leidos", "nlp", 0,
              "Internal Referral Module (IRM) ... eRA ... NLP",
              "NIH-built; Leidos+Highrise integrators.",
              confidence="medium"))

# 63151 HHS Google;Barnacle NanCI
D(link(63151, None, "NanCI",
       "NanCI: Connecting Scientists ... NanCI Connecting Scientists Mobile App",
       "Exact match to NanCI (NCI app)."))

# 63152 HHS H2O.GPTe NBS Virtual Assistant
D(link(63152, 5183, "H2O GPTe",
       "NBS Virtual Assistant ... H2O.GPTe",
       "Exact match."))

# 63153 HHS ORNL/IMS MOSSAIC SEER
D(add_product(63153, "NCI MOSSAIC SEER NLP",
              "NCI / Oak Ridge National Lab", "nlp", 0,
              "MOSSAIC applies deep learning natural language processing ... OncoID ... OncoIE",
              "NCI-DOE collaboration; ORNL builds the NLP pipeline; APIs (OncoID, OncoIE, OncoMetsID).",
              confidence="high"))

# 63155 HHS Microsoft NIAMS Chatbot — Azure-hosted custom
D(add_product(63155, "NIAMS GenAI Chatbot",
              "NIH NIAMS", "general_llm", 1,
              "NIAMS AI Chatbot Pilot ... Azure-hosted NIAMS GenAI Chatbot",
              "NIAMS-built Azure OpenAI chatbot.",
              confidence="medium"))

# 63167 HHS Deloitte SRDMS NLP COI
D(add_product(63167, "NIH SRDMS NLP COI Module",
              "NIH / Deloitte", "nlp", 0,
              "SRDMS NLP COI ... conflict-of-interest (COI)",
              "NIH-built; Deloitte integrator.",
              confidence="medium"))

# 63178 HHS Google NIH Grants Virtual Assistant
D(add_product(63178, "NIH Grants Virtual Assistant",
              "NIH / Google", "general_llm", 0,
              "NIH Grants Virtual Assistant ... Chat Bot",
              "NIH-built; Google as platform.",
              confidence="medium"))

# 63181 HHS Leica Aivia
D(link(63181, 5184, "Leica Aivia",
       "Aivia ... Leica",
       "Exact match."))

# 63200 HHS NIAID TB Portals (Deloitte/Guidehouse/RDCT)
D(add_product(63200, "NIAID TB Portals (TB DEPOT)",
              "NIAID", "data_analytics", 0,
              "TB DEPOT (Tuberculosis Data Exploration Portal) ... NIAID TB Portals",
              "NIAID research portal; multi-vendor integrators.",
              confidence="medium"))

# 63201 HHS TB Portals Outlier Detection
D(add_product(63201, "NIAID TB Portals Outlier Detection",
              "NIAID", "computer_vision", 0,
              "TB Portals Outlier Detection Lambda Function",
              "NIAID TB Portals image-quality module.",
              confidence="medium",
              parent="NIAID TB Portals (TB DEPOT)"))

# 63208 HHS Technatomy Axle MirBot
D(add_product(63208, "MirBot", "NIH / Technatomy Axle",
              "nlp", 0,
              "MirBot ... efficiently and consistently processing incoming study PDFs",
              "Technatomy/Axle-built NIH grant-review NLP tool.",
              confidence="medium"))

# 63223 HHS Shabash Merops
D(link(63223, 5189, "Shabash Merops",
       "Merops ... Shabash",
       "Exact match."))

# 63224 HHS Deloitte OSPIDA RPAB CAT
D(add_product(63224, "NIAID OSPIDA Scientific Coding Assistance Tool",
              "NIAID / Deloitte", "nlp", 0,
              "OSPIDA RPAB Scientific Coding Assistance Tool (CAT)",
              "NIAID grant-coding NLP tool.",
              confidence="medium"))

# 63244 HHS Microsoft Azure+Westat NLP for prevention research
D(add_product(63244, "NIH Prevention Research NLP",
              "NIH / Westat", "nlp", 1,
              "Leveraging NLP and LLMs to identify and characterize NIH prevention research",
              "NIH-built; Westat partner; Azure platform.",
              confidence="low"))

# 63249 HHS Infer Solutions NIH Travel Chatbot
D(add_product(63249, "NIH Travel Policy AI Chatbot",
              "NIH / Infer Solutions", "general_llm", 1,
              "NIH Travel Policy AI Chatbot",
              "NIH-built; Infer Solutions integrator.",
              confidence="medium"))

# 63253 HHS Tyler Technologies AI Harvest Service
D(add_product(63253, "HealthData.gov AI Harvest Service",
              "HHS / Tyler Technologies", "data_analytics", 1,
              "AI Harvest Service ... HealthData.gov ... Tyler Technologies",
              "Tyler-built metadata-normalization service for HealthData.gov.",
              confidence="medium"))

# 63255 HHS MicroHealth Similar Opportunities (KNN) Grants.gov
D(add_product(63255, "Grants.gov Similar Opportunities",
              "HHS / MicroHealth", "data_analytics", 0,
              "Similar Opportunities (KNN) ... Grants.gov Cloud",
              "MicroHealth-built Grants.gov recommender.",
              confidence="medium",
              parent="Grants.gov AI Tools"))

# 63256 HHS Business Performance Systems Grants.gov Chatbot
D(add_product(63256, "Grants.gov Applicant Help Chatbot",
              "HHS / Business Performance Systems", "general_llm", 0,
              "Applicant Help Chatbot ... Grants.gov Cloud",
              "Grants.gov public help chatbot.",
              confidence="medium",
              parent="Grants.gov AI Tools"))

# 63257-63262 HHS GrantSolutions (Internal Federal Shared Service)
for (uid, name, ptype, gen) in [
    (63257, "GrantSolutions Text Analyzer Tool", "nlp", 0),
    (63258, "GrantSolutions AI Writing Assistant", "general_llm", 1),
    (63259, "GrantSolutions Recipient Risk Tool", "data_analytics", 0),
    (63260, "GrantSolutions Non-Competing Continuation Approval Tool", "data_analytics", 0),
    (63261, "GrantSolutions Helpdesk Agent", "general_llm", 1),
    (63262, "GrantSolutions Non-Competing Continuation Review Tool", "general_llm", 1),
]:
    D(add_product(uid, name, "GrantSolutions (HHS Shared Service)", ptype, gen,
                  rows[uid]["use_case_name"] + " — GrantSolutions",
                  "GrantSolutions federal shared-service modules.",
                  confidence="high",
                  parent="GrantSolutions"))

# 63269 HUD Deloitte Ginnie Mae Counterparty Risk
D(add_product(63269, "Ginnie Mae Counterparty Risk Anomaly Detection",
              "Ginnie Mae / Deloitte", "data_analytics", 0,
              "Counterparty Risk Anomaly Detection ... Ginnie Mae Reporting and Feedback System",
              "Ginnie Mae custom; Deloitte integrator.",
              confidence="medium"))

# 63270 HUD Ernst & Young Subledger Data Quality
D(add_product(63270, "Ginnie Mae Subledger Data Quality ML",
              "Ginnie Mae / Ernst & Young", "data_analytics", 0,
              "Subledger Data Quality Machine Learning",
              "Ginnie Mae financial accounting anomaly detection.",
              confidence="medium"))

# 63271 HUD Deloitte Automated Draft Narrative
D(add_product(63271, "Ginnie Mae Automated Draft Narrative Reports",
              "Ginnie Mae / Deloitte", "nlp", 0,
              "Automated Draft Narrative Reports ... Natural Language Generation",
              "Ginnie Mae NLG report drafter.",
              confidence="medium"))

# 63281 NARA Cortina A1 Museum
D(add_product(63281, "NARA A1 Museum AI",
              "NARA / Cortina", "computer_vision", 1,
              "A1 Museum AI Project ... Exhibit Personalization System",
              "Cortina-built museum AI for NARA A1.",
              confidence="medium"))

# 63307 NASA NLP — vendor literally 'NLP'
D(false_positive(63307, "vendor 'NLP'",
                 "Vendor field is 'NLP' (technique, not vendor). Project is internal NextGen Advanced Methods. Cannot identify product."))

# 63308 NASA FAA NextGen Letters of Agreement
D(add_product(63308, "FAA NextGen LOA/SOP Analytics",
              "FAA", "nlp", 0,
              "NextGen Data Analytics: Letters of Agreement",
              "FAA NextGen custom analytics.",
              confidence="low"))

# 63687 NASA Mitchell Vantage Systems GLOBE Image Processing -> AWS Rekognition
D(link(63687, 5190, "AWS Rekognition",
       "GLOBE Program ... Amazon Rekognition SAAS",
       "Explicit Amazon Rekognition use."))

# 63688 NASA Raytheon Earthdata Cloud cost
D(add_product(63688, "NASA CAAP Cost Analytics",
              "NASA / Raytheon", "data_analytics", 0,
              "Cloud Account Allocation Plan (CAAP) Cost Analytics Support",
              "NASA Earthdata Cloud cost prediction.",
              confidence="low"))

# 63753 NTSB Air Force Research Lab Voice-to-Text
D(add_product(63753, "AFRL Voice Recorder Transcription",
              "Air Force Research Laboratory", "transcription", 0,
              "Voice to text transcription ... Air Force Research Lab",
              "AFRL-developed transcription for NTSB.",
              confidence="low"))

# 63755 NTSB Dataminer (sic) -> Dataminr First Alert
D(link(63755, 5138, "Dataminr First Alert",
       "Dataminr ... Timely awareness of transportation safety events",
       "Typo 'Dataminer' = Dataminr. Same product as 61248."))

# 63763 SBA Microsoft Business Development -> M365 Copilot + ChatGPT
D(link(63763, 4981, "Microsoft 365 Copilot",
       "Business Development ... Microsoft Bing CoPilot and ChatGPT4",
       "Primary deployment is Microsoft Copilot (Bing CoPilot)."))

# 63776 SBA Internally created GovCon Match
D(custom(63776, "SBA GovCon Match", "SBA",
         "data_analytics", 0,
         "GovCon Match ... Certify.sba.gov",
         "SBA-built internal tool.",
         confidence="medium"))

# 63777 SBA Utah business plan tool
D(false_positive(63777, "vendor https://startup.utah.gov/business-plan/",
                 "Vendor is a Utah state website URL, not an AI product vendor. SBA likely points users to it; not a deployed AI tool."))

# 63799 SEC SkillSoft Training Conversation -> Skillsoft Percipio CAISY
D(link(63799, 5390, "Skillsoft Percipio CAISY",
       "Training Conversation Tool ... SkillSoft",
       "SkillSoft training conversation = Percipio CAISY."))

# 63809 SEC Aretec Inc Name Matching -> Aretec NEAT
D(link(63809, 5137, "Aretec NEAT",
       "Name Matching ... Aretec Inc ... NEAT",
       "Exact match."))
D(link(63810, 5137, "Aretec NEAT",
       "Parsing of Plain Language Descriptions ... Aretec Inc ... NEAT",
       "Aretec NEAT module."))
D(link(63816, 5137, "Aretec NEAT",
       "Identification of Potentially Manipulative Activity ... Aretec Inc ... NEAT",
       "Aretec NEAT module."))

# 63825 SEC GDIT FOIA Extraction
D(add_product(63825, "SEC FOIA Form Extraction", "SEC / GDIT",
              "document_ai", 1,
              "Extracting data from FOIA request forms",
              "SEC custom; GDIT integrator.",
              confidence="low"))

# 63847 SEC RELX (Lexis) Legal Research -> Lexis+ AI
D(link(63847, 5002, "Lexis+ AI",
       "Legal Research (Lexis+) ... RELX (Lexis)",
       "Exact match — Lexis+ AI."))

# 63864 SSA IBM Quick Disability Determinations
D(add_product(63864, "SSA Quick Disability Determinations Model",
              "SSA / IBM", "clinical_decision_support", 0,
              "Quick Disability Determinations Model",
              "SSA-built; IBM integrator. Long-standing program (>20 yrs).",
              confidence="high"))

# 63865 SSA AWS Mobile Wage Reporting
D(link(63865, 5019, "AWS Textract",
       "Mobile Wage Reporting ... uses AI to extract text/data from scanned images",
       "AWS-hosted text extraction; likely AWS Textract."))

# 63866 SSA AWS Q&A Bot -> AWS Lex
D(link(63866, 5228, "AWS Lex",
       "SSA 800# Public Question & Answer Bot ... AWS",
       "AWS Connect+Lex IVR."))

# 63869 SSA Microsoft Speech to Text
D(link(63869, None, "Azure Speech",
       "Speech to Text Video Transcription ... Microsoft ... Hearing Recording and Transcription",
       "Azure Speech for SSA hearing transcription."))

# 63872 SSA Espyr/Acentra Therapy Chatbot
D(add_product(63872, "Espyr Therapy Chatbot", "Espyr",
              "clinical_decision_support", 1,
              "Therapy Chatbot - Text-Based Mental Health Support",
              "Espyr (Acentra Health subsidiary) employee mental-health chatbot.",
              confidence="medium"))

# 63880 SSA Skillsoft/Percipio Training Interaction Simulator
D(link(63880, 5390, "Skillsoft Percipio CAISY",
       "Training Interaction Simulator ... Skillsoft/Percipio ... Percipio",
       "Percipio simulator."))

# 63890 State Deloitte AI Declassification
D(add_product(63890, "State Department Declassification Review AI",
              "State Department / Deloitte", "document_ai", 0,
              "AI-Augmented Declassification Review",
              "State-built; Deloitte integrator.",
              confidence="medium"))

# 63899 State GCP Within Grade Increase
D(link(63899, 5283, "Google Cloud Platform",
       "Within Grade Increase Data Extraction Automation ... GCP",
       "GCP-based extraction. Vendor literally 'GCP'."))

# 63900 State Google DS-5528 Promissory Note
D(link(63900, 5283, "Google Cloud Platform",
       "DS-5528 Promissory Note Automation ... Google",
       "State Department Google extraction."))

# 63908 State Deloitte AIRE
D(add_product(63908, "State Department AI Research Engine (AIRE)",
              "State Department / Deloitte", "general_llm", 1,
              "AI Research Engine (AIRE) ... Data.State-SBU",
              "State Department genAI research engine.",
              confidence="medium"))

# 63914 State Guidehouse Foreign Assistance NLP
D(add_product(63914, "State FACTS Info Foreign Assistance NLP",
              "State Department / Guidehouse", "nlp", 0,
              "Natural Language Processing (NLP) for Foreign Assistance Appropriations Analysis",
              "State-built; Guidehouse integrator.",
              confidence="medium"))

# 63916 State Guidehouse FA.gov PII Picker
D(add_product(63916, "FA.gov PII Picker",
              "State Department / Guidehouse", "nlp", 0,
              "FA.gov PII Picker",
              "State Department FA.gov PII tool.",
              confidence="medium"))

# 63917 State Guidehouse ICS Turbo
D(add_product(63917, "State Integrated Country Strategy Turbo",
              "State Department / Guidehouse", "nlp", 0,
              "Integrated Country Strategy (ICS) Turbo",
              "State Department ICS analytics.",
              confidence="medium"))

# 63918 State Guidehouse FA.gov RedactAid
D(add_product(63918, "FA.gov RedactAid",
              "State Department / Guidehouse", "document_ai", 0,
              "FA.gov RedactAid",
              "State Department FA.gov redaction tool.",
              confidence="medium"))

# 63932 State Microsoft Walter
D(add_product(63932, "State Department Walter Support Bot",
              "State Department / Microsoft", "general_llm", 1,
              "Walter: Generative AI Support Bot ... DOS-O365",
              "State-built genAI on M365; named tool.",
              confidence="medium"))

# 63938 State Microsoft WHA/EX
D(add_product(63938, "State Department WHA/EX Information Management",
              "State Department / Microsoft", "general_llm", 1,
              "WHA/EX Information Management ... DOS-O365",
              "State-built knowledge management on M365.",
              confidence="low"))

# 63941 State Deloitte AzureAI Translator -> Azure AI Translator
D(add_product(63941, "Azure AI Translator", "Microsoft",
              "translation", 1,
              "TIP Report Research Translation ... AzureAI ... AzureAI Translator",
              "Azure Translator service.",
              confidence="high",
              parent="Microsoft Azure Platform"))

# 63943 State Guidehouse ARRE
D(add_product(63943, "State NIV Adjudication Review Recommendation Engine",
              "State Department / Guidehouse", "data_analytics", 0,
              "NIV Adjudication Review Recommendation Engine (ARRE)",
              "State Department consular AI.",
              confidence="medium"))

# 63947 State Microsoft LCALA
D(add_product(63947, "State LCALA Consular Language Augmentation",
              "State Department / Microsoft", "translation", 1,
              "Live Consular AI Language Augmentation (LCALA)",
              "State Department consular interpretation AI on Microsoft stack.",
              confidence="medium"))

# 64134 USDA Expert AI (Cogito) -> Expert.ai Cogito
D(link(64134, 5198, "Expert.ai Cogito",
       "NAL Automated Indexing ... Expert AI (Cogito)",
       "Exact match."))

# 64144 USDA RedCastle Forest Health
D(link(64144, 5147, "RedCastle Forest Health",
       "Forest Health Detection Monitoring ... RedCastle Resources",
       "Exact match."))

# 64171 USDA AWS FSA FLP Chatbot
D(add_product(64171, "USDA FSA FLP Chatbot",
              "USDA / AWS", "general_llm", 1,
              "FSA FLP Chatbot ... Farm Loan Program",
              "USDA Farm Service Agency Loan Program chatbot on AWS.",
              confidence="medium"))

# 64184 USDA Colorado State Equine dataset
D(add_product(64184, "USDA Equine Operations Dataset",
              "USDA / Colorado State University", "scientific_ml", 0,
              "Equine Operations and Populations Dataset for the U.S.",
              "USDA-CSU partnership; specific named dataset/model.",
              confidence="low"))

# 64187 USDA Microsoft NASSportal Agent
D(add_product(64187, "USDA NASSportal Intranet Agent",
              "USDA NASS / Microsoft", "agent_platform", 1,
              "NASSportal Intranet Agent",
              "NASS-built agent on Microsoft 365.",
              confidence="medium"))

# 64189 USDA UI Path Incident Invoice -> UiPath
D(link(64189, 5408, "UiPath Enterprise RPA",
       "Incident Invoice Document Understanding ... UI Path",
       "UiPath at USDA."))

# 64203 USDA Chiral Software Wildlife Deterrent
D(add_product(64203, "Chiral Wildlife Deterrent System",
              "Chiral Software", "computer_vision", 0,
              "Wildlife Deterrent System ... Chiral Software",
              "Chiral-built wildlife computer vision.",
              confidence="medium"))

# 64206 USDA Oregon State Regional Forest Mapping
D(add_product(64206, "USDA Oregon State Forest Mapping",
              "USDA Forest Service / Oregon State University", "scientific_ml", 0,
              "AI for regional forest mapping and monitoring",
              "USDA-OSU research collaboration.",
              confidence="low"))

# 64222 USDA ACCRETE ARGUS -> existing 5203
D(link(64222, 5203, "ACCRETE ARGUS",
       "ARGUS AI Supply Chain Interference ... ACCRETE AI Government",
       "Exact match."))

# 64223 USDA Microsoft GovChat
D(add_product(64223, "USDA ARS GovChat",
              "USDA ARS / Microsoft", "general_llm", 1,
              "GovChat ... ARS AzureGov ... AI assistant that helps with time consuming tasks",
              "USDA ARS-built genAI assistant on AzureGov.",
              confidence="medium"))

# 64233 USDA VegSpec -> existing VegSpec (USDA NRCS)
D({
    "use_case_id": 64233, "consolidated_use_case_id": None, "use_case_agency": "USDA",
    "decision": "link", "product_id": None,
    "canonical_name": "VegSpec",
    "proposed_canonical_name": None, "vendor": None, "product_type": None,
    "is_generative_ai": None, "proposed_parent_canonical_name": None,
    "proposed_alias": None, "proposed_alias_replacement": None,
    "evidence_quote": "Vegetation Specifications Suite (VegSpec)",
    "confidence": "high",
    "reasoning": "Exact match to USDA NRCS VegSpec in catalog.",
    "notes": "",
})

# 64234 USDA Spatial Front NRCS Engineering Tools (NETS)
D(add_product(64234, "USDA NRCS NETS Automated Waterway Design",
              "USDA NRCS / Spatial Front", "scientific_ml", 1,
              "NETS automated waterway design ... NRCS Engineering Tools Suite",
              "NRCS-built engineering design AI.",
              confidence="medium"))

# 64237 USDA UIPath Studio Annual Soil Refresh
D(link(64237, 5408, "UiPath Enterprise RPA",
       "Annual Soil Refresh Data Staging Server Automation ... UIPath Studio",
       "UiPath Studio = UiPath."))

# 64253 USDA RedCastle Automated Road Mapping
D(link(64253, 5147, "RedCastle Forest Health",
       "Automated Road Mapping ... RedCastle Resources",
       "RedCastle USDA Forest Service computer-vision road mapping. Same vendor as 64144; link to existing RedCastle product (may want to broaden the canonical naming later)."))

# 64255 USDA Wildfire.org Turbo plan
D(add_product(64255, "Wildfire.org Turbo Plan",
              "Wildfire.org", "general_llm", 1,
              "Turbo plan ... Wildfire.org ... Wildfire Crisis Strategy",
              "Wildfire.org Turbo Plan NEPA accelerator (Element84/AI4ER).",
              confidence="medium"))

# 64256 USDA Google Forest Plan Review
D(add_product(64256, "USDA Forest Plan Review AI",
              "USDA Forest Service / Google", "general_llm", 1,
              "Forest Plan review and planning support",
              "USFS-built Google-platform genAI.",
              confidence="low"))

# 64257 USDA Google TreeSearch
D(add_product(64257, "USDA TreeSearch AI",
              "USDA Forest Service / Google", "search", 1,
              "TreeSearch ... USFS TreeSearch database",
              "USFS-built TreeSearch search AI.",
              confidence="low"))

# 64258 USDA Google Infosec Chatbot
D(add_product(64258, "USDA Forest Service Infosec Chatbot",
              "USDA Forest Service / Google", "general_llm", 1,
              "Infosec Chatbot ... NIST security publications",
              "USFS-built genAI on Google cloud.",
              confidence="low"))

# 64259 USDA Oregon State Bugnet
D(add_product(64259, "USDA Bugnet",
              "USDA Forest Service / Oregon State University", "computer_vision", 0,
              "Bugnet ... insects and disease ... satellite imagery",
              "USFS-OSU forest pest mapper.",
              confidence="medium"))

# 64260 USDA Univ of Washington Recreation Chatbot
D(add_product(64260, "USDA Recreation Site Chatbot",
              "USDA Forest Service / University of Washington", "general_llm", 0,
              "Recreation site chatbot ... Estimating recreation use",
              "USFS-UW research collaboration.",
              confidence="low"))

# 64264 USDA Kikaha Solutions Forest Health Survey
D(add_product(64264, "USDA Forest Health ML Survey",
              "USDA Forest Service / Kikaha Solutions", "scientific_ml", 0,
              "Forest Health Protection: Survey and mapping ... insects and diseases ... machine learning",
              "USFS-built; Kikaha integrator.",
              confidence="medium"))

# 64273 USDA American Museum of Natural History — Marbled Murrelet
D(add_product(64273, "USDA Marbled Murrelet Habitat Mapping",
              "USDA Forest Service / American Museum of Natural History",
              "scientific_ml", 0,
              "Forest habitat mapping for marbled murrelets",
              "USFS-AMNH research partnership.",
              confidence="low"))

# 64274 USDA Univ of Washington Forest Inventory
D(add_product(64274, "Washington Forest Inventory Maps",
              "USDA Forest Service / University of Washington",
              "scientific_ml", 0,
              "Washington state forest inventory maps",
              "USFS-UW research collaboration.",
              confidence="low"))

# 64281 USDA Booz Allen Recreation One Stop
D(add_product(64281, "USDA Recreation One Stop AI",
              "USDA Forest Service / Booz Allen", "general_llm", 1,
              "Recreation One Stop use of AI ... Recreation.gov",
              "Recreation.gov AI features.",
              confidence="medium"))

# 64288 USDA George Mason VegScape
D(add_product(64288, "USDA VegScape/CropCASMA",
              "USDA NASS / George Mason University", "scientific_ml", 0,
              "VegScape/CropCASMA Data Portals",
              "NASS-GMU partnership; specific named tool.",
              confidence="medium"))

# 64293 USDA Steampunk USDA AgCloud Chatbot
D(add_product(64293, "USDA AgCloud Helpdesk Chatbot",
              "USDA / Steampunk", "general_llm", 1,
              "Chatbot for IT Customer Help Desk ... AgCloud",
              "USDA-built genAI helpdesk chatbot on AgCloud.",
              confidence="medium"))

# ---------------------------------------------------------------------------
# Final write
# ---------------------------------------------------------------------------
covered = {d["use_case_id"] for d in decisions}
missing = sorted(set(rows) - covered)
extra = sorted(covered - set(rows))
if missing:
    print(f"MISSING {len(missing)} use_case_ids: {missing[:20]}{'...' if len(missing)>20 else ''}",
          file=sys.stderr)
if extra:
    print(f"EXTRA ids not in input: {extra}", file=sys.stderr)

# write
with OUT.open("w") as f:
    json.dump(decisions, f, indent=2)

print(f"Wrote {len(decisions)} decisions to {OUT}")
by_type = {}
for d in decisions:
    by_type[d["decision"]] = by_type.get(d["decision"], 0) + 1
for k, v in sorted(by_type.items(), key=lambda kv: -kv[1]):
    print(f"  {k}: {v}")
