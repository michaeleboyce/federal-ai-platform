#!/usr/bin/env python3
"""Wave1-C tagger: DOT + DHS + TREAS + FRB (353 rows).

Per-row heuristics that pick the best tag combo from a 2024 narrative.
Reasoning quotes a short phrase from the source narrative.
"""
from __future__ import annotations
import csv
import os
import re
from pathlib import Path

INPUT = Path('audit/retag/2024-tagging/inputs/C.csv')
OUT_DIR = Path('audit/retag/2024-tagging/wave1')
OUT = OUT_DIR / 'C.csv'

OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FIELDS = [
    'use_case_id_2024', 'tagged_by_agent', 'entry_type',
    'is_generative_ai', 'ai_sophistication', 'deployment_scope', 'confidence',
    'reasoning',
    'is_general_llm_access', 'is_coding_tool', 'is_cots_commercial',
    'tool_product_name', 'tool_vendor',
    'is_microsoft_copilot', 'is_openai', 'is_anthropic', 'is_google',
    'is_github_copilot', 'is_aws_ai',
    'is_enterprise_wide', 'architecture_type', 'has_model_training',
    'use_type', 'is_public_facing', 'scope_detail',
]

# Bureau scope_detail mapping for DHS sub-orgs and others
DEPT_MAP = {
    'DHS': 'Department of Homeland Security',
    'DOT': 'Department of Transportation',
    'TREAS': 'Treasury',
    'FRB': 'Federal Reserve Board',
}


def find_quote(narrative: str, candidate_phrases: list[str]) -> str | None:
    """Pick the first phrase in candidate list that appears in narrative (case-insensitive)."""
    low = narrative.lower()
    for p in candidate_phrases:
        if p.lower() in low:
            # Re-extract preserving original case from narrative
            idx = low.find(p.lower())
            return narrative[idx:idx + len(p)]
    return None


def short_quote(text: str, min_words=2, max_words=6) -> str:
    """Extract a short quotable phrase from text (first sentence-fragment)."""
    text = text.strip()
    if not text:
        return ''
    # Pull the most informative-looking 2-6 word fragment by taking
    # the first comma/period-bounded chunk and trimming to max_words.
    chunk = re.split(r'[.;\n]', text, maxsplit=1)[0]
    # Strip leading boilerplate (require trailing space to avoid trimming inside words)
    chunk = re.sub(r'^(this |the |a |an |use of |it |our |we |they )+', '', chunk, flags=re.I).strip()
    words = chunk.split()
    if len(words) < min_words:
        return ''
    return ' '.join(words[:max_words])


def detect_genai(text: str) -> bool:
    pats = [
        r'\bgenerative\b', r'\bllm[s]?\b', r'\blarge language model',
        r'\bgpt[- ]?', r'\bchatgpt\b', r'\bcopilot\b', r'\bbedrock\b',
        r'\bclaude\b', r'\bgemini\b', r'\bvertex\b', r'\bfoundation model',
        r'\btransformer-based\b', r'\bsummariz', r'\bdiffusion\b',
        r'\bcode generation\b', r'\bgithub copilot\b', r'\btext generation\b',
        r'\bnatural language generat', r'\brag\b', r'\bretrieval[- ]augmented',
        r'\bopenai\b', r'\banthropic\b',
    ]
    low = text.lower()
    return any(re.search(p, low) for p in pats)


def detect_coding(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in [
        'github copilot', 'code generation', 'coding assistant', 'codex',
        'developer productivity', 'software development assistant', 'cursor',
    ])


def detect_cv(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in [
        'computer vision', 'facial recognition', 'face recognition',
        'image recognition', 'object detection', 'license plate',
        'image classification', 'video analytics', 'lidar', 'satellite imagery',
        'aerial imagery', 'imagery analysis', 'biometric', 'optical character',
        'ocr ', ' ocr', 'x-ray', 'radar', 'image segmentation',
        '3d image', 'non-intrusive inspection', 'image processing',
        'thermal imaging',
    ])


def detect_nlp(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in [
        'natural language process', 'nlp ', ' nlp', 'text classification',
        'sentiment analysis', 'topic modeling', 'named entity',
        'document classification', 'text mining', 'text analytics',
        'speech recognition', 'speech-to-text', 'transcription',
        'translation', 'chatbot', 'virtual assistant', 'document extraction',
        'document understanding', 'entity extraction',
    ])


def detect_predictive(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in [
        'forecast', 'prediction', 'predictive', 'time series', 'risk model',
        'risk scoring', 'fraud detection', 'anomaly detection', 'audit selection',
        'classification model', 'regression', 'demand forecast', 'workload',
        'risk identification',
    ])


def detect_public_facing(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in [
        'public-facing', 'public facing', 'taxpayers', 'travelers',
        'applicants', 'citizens', 'public website', 'public chatbot',
    ])


def classify_one(row: dict) -> dict:
    name = (row.get('use_case_name') or '').strip()
    purpose = (row.get('purpose_benefits') or '').strip()
    outputs = (row.get('outputs') or '').strip()
    commercial = (row.get('commercial_ai') or '').strip()
    dev_method = (row.get('dev_method') or '').strip()
    dev_stage = (row.get('dev_stage') or '').strip()
    bureau = (row.get('bureau') or '').strip()
    agency = (row.get('agency_abbreviation') or '').strip()
    narrative = ' '.join([name, purpose, outputs, commercial]).strip()
    low_narr = narrative.lower()
    low_name = name.lower()

    out: dict = {f: '' for f in OUT_FIELDS}
    out['use_case_id_2024'] = row['id']
    out['tagged_by_agent'] = 'wave1-C'

    # ---------------- Vendor flags / product detection ----------------
    is_mc = int(bool(re.search(r'\b(m365 copilot|microsoft 365 copilot|microsoft copilot|copilot chat|copilot for security|copilot for power platform|copilot for m365|m365 apps|using m365)\b', low_narr)))
    is_oai = int(bool(re.search(r'\b(openai|chatgpt enterprise|chatgpt)\b', low_narr)))
    is_anth = int(bool(re.search(r'\b(claude|anthropic)\b', low_narr)))
    is_goog = int(bool(re.search(r'\b(gemini|vertex ai|google duet|duet ai|palm)\b', low_narr)))
    is_ghc = int(bool(re.search(r'\bgithub copilot\b', low_narr)))
    is_aws = int(bool(re.search(r'\b(bedrock|sagemaker|amazon comprehend|amazon rekognition|amazon textract|aws ai)\b', low_narr)))

    out['is_microsoft_copilot'] = is_mc
    out['is_openai'] = is_oai
    out['is_anthropic'] = is_anth
    out['is_google'] = is_goog
    out['is_github_copilot'] = is_ghc
    out['is_aws_ai'] = is_aws

    # Tool product name / vendor (only when explicit)
    if is_ghc:
        out['tool_product_name'] = 'GitHub Copilot'
        out['tool_vendor'] = 'GitHub/Microsoft'
    elif is_mc:
        out['tool_product_name'] = 'Microsoft 365 Copilot'
        out['tool_vendor'] = 'Microsoft'
    elif 'chatgpt' in low_narr:
        out['tool_product_name'] = 'ChatGPT'
        out['tool_vendor'] = 'OpenAI'
    elif 'bedrock' in low_narr:
        out['tool_product_name'] = 'AWS Bedrock'
        out['tool_vendor'] = 'AWS'
    elif 'sagemaker' in low_narr:
        out['tool_product_name'] = 'AWS SageMaker'
        out['tool_vendor'] = 'AWS'
    elif 'gemini' in low_narr:
        out['tool_product_name'] = 'Gemini'
        out['tool_vendor'] = 'Google'

    # is_general_llm_access — agency-wide chatbot access
    is_glla = 0
    if any(k in low_narr for k in ['agency-wide access', 'enterprise-wide chatbot', 'enterprise chatbot platform']):
        is_glla = 1
    if any(k in low_name for k in ['chatgpt enterprise', 'copilot chat']) and any(k in low_narr for k in ['enterprise', 'agency']):
        is_glla = 1
    out['is_general_llm_access'] = is_glla

    out['is_coding_tool'] = int(detect_coding(narrative))

    # is_cots_commercial: heuristic from dev_method/commercial_ai
    is_cots = ''
    if 'contracting' in dev_method.lower() or 'acquired' in dev_method.lower() or 'commercial' in dev_method.lower():
        is_cots = 1
    elif 'in-house' in dev_method.lower() or 'no contract' in dev_method.lower():
        is_cots = 0
    if (is_mc or is_oai or is_anth or is_goog or is_ghc) and is_cots != 0:
        is_cots = 1
    out['is_cots_commercial'] = is_cots

    # ---------------- ai_sophistication ----------------
    has_genai = detect_genai(narrative)
    is_cv = detect_cv(narrative)
    is_nlp = detect_nlp(narrative)
    is_pred = detect_predictive(narrative)
    if detect_coding(narrative):
        soph = 'coding_assistant'
    elif 'agentic' in low_narr or 'autonomous agent' in low_narr:
        soph = 'agentic'
    elif has_genai and not is_cv:
        # Any genai signal that isn't CV → general_llm
        soph = 'general_llm'
    elif is_cv:
        soph = 'computer_vision'
    elif is_nlp:
        soph = 'nlp_specific'
    elif is_pred:
        soph = 'predictive_analytics'
    else:
        soph = 'classical_ml'

    # genai final flag
    is_genai = 0
    if soph in ('general_llm', 'coding_assistant', 'agentic'):
        is_genai = 1
    elif has_genai and not is_cv:
        is_genai = 1
    out['is_generative_ai'] = is_genai
    out['ai_sophistication'] = soph

    # ---------------- entry_type ----------------
    # Default by dev method + product mention
    if is_mc or is_ghc or (is_oai and 'chatgpt' in low_narr) or is_goog or 'salesforce einstein' in low_narr:
        entry_type = 'product_deployment'
    elif 'in-house' in dev_method.lower() and (is_aws or 'bedrock' in low_narr or 'fine-tune' in low_narr or 'fine tuned' in low_narr or 'rag' in low_narr or 'wrap' in low_narr):
        entry_type = 'bespoke_application'
    elif 'contracting' in dev_method.lower() and (is_aws or is_oai or 'bedrock' in low_narr or 'foundation model' in low_narr):
        entry_type = 'bespoke_application'
    elif 'in-house' in dev_method.lower():
        entry_type = 'custom_system'
    elif 'contracting' in dev_method.lower():
        # contracted classical ML — could be bespoke_application or custom_system
        entry_type = 'bespoke_application' if has_genai else 'custom_system'
    elif 'no contract' in dev_method.lower():
        entry_type = 'custom_system'
    else:
        entry_type = 'custom_system'

    # Governance / policy / compliance entries -> generic_use_pattern.
    # Only flip when the *name* signals governance and the narrative lacks an AI artifact.
    name_gov_markers = [
        'compliance plan', 'governance plan', 'ai governance',
        'ai strategy', 'ai roadmap', 'ai inventory',
        'omb memorandum', 'm-24-10', 'working group',
        'emerging technology team', 'ai policy', 'genai policy',
        'procurement team', 'acquisitions and training team',
        'review (sr2) committee', 'sr2 committee',
        'ai coordination', 'aica working',
    ]
    if any(g in low_name for g in name_gov_markers):
        if not any(k in low_narr for k in ['trained on', 'fine-tune', 'rag search', 'embedding model', 'inference']):
            entry_type = 'generic_use_pattern'

    # DHS "Commercial Generative AI for X" entries — agency-wide permission patterns
    if low_name.startswith('commercial generative ai for') or 'employees are permitted to use commercially available generative ai' in low_narr:
        entry_type = 'generic_use_pattern'

    out['entry_type'] = entry_type

    # ---------------- deployment_scope ----------------
    scope = 'bureau'
    if entry_type == 'generic_use_pattern' and agency in ('DOT', 'TREAS', 'DHS', 'FRB'):
        scope = 'department'
    elif low_name.startswith('enterprise ') or 'enterprise-wide' in low_name or 'ask dottie' in low_name:
        scope = 'enterprise_wide'
    elif is_mc or is_glla or 'deployed enterprise-wide' in low_narr or 'enterprise-wide deployment' in low_narr:
        scope = 'enterprise_wide'
    elif (
        ('pilot program' in low_narr or 'pilot deployment' in low_narr or 'pilot project' in low_narr
         or 'pilot phase' in low_narr or 'in pilot' in low_narr or 'pilot stage' in low_narr
         or 'as a pilot' in low_narr or 'pilot study' in low_narr)
        or 'proof of concept' in low_narr or 'proof-of-concept' in low_narr
        or ' poc' in low_name
    ):
        # Exclude air-traffic / aviation contexts where "pilot" = aircraft pilot
        if not any(k in low_narr for k in ['aircraft pilot', 'atc and pilot', 'pilot-controller', 'pilot communications']):
            scope = 'pilot'
    elif bureau.startswith('CAIO') or bureau in ('DOT', 'DHS'):
        scope = 'department'
    elif agency == 'FRB' and bureau.startswith('Office of'):
        scope = 'office'

    out['deployment_scope'] = scope
    out['is_enterprise_wide'] = 1 if scope == 'enterprise_wide' else 0

    # scope_detail
    scope_detail = ''
    if scope == 'bureau' and bureau and bureau != agency:
        scope_detail = bureau
    elif scope == 'department':
        scope_detail = DEPT_MAP.get(agency, agency)
    elif scope == 'office' and bureau:
        scope_detail = bureau
    elif bureau and bureau != agency:
        scope_detail = bureau
    out['scope_detail'] = scope_detail

    # ---------------- architecture_type ----------------
    arch = 'inference_only'
    if 'rag' in low_narr or 'retrieval-augmented' in low_narr or 'retrieval augmented' in low_narr:
        arch = 'rag_pipeline'
    elif 'fine-tune' in low_narr or 'fine tuned' in low_narr or 'fine-tuning' in low_narr:
        arch = 'fine_tuned'
    elif 'agentic' in low_narr or 'autonomous agent' in low_narr:
        arch = 'agentic_workflow'
    elif 'in-house' in dev_method.lower() and (soph in ('classical_ml', 'computer_vision', 'predictive_analytics') or 'trained' in low_narr or 'train' in low_narr):
        arch = 'custom_trained'
    elif soph in ('computer_vision', 'classical_ml', 'predictive_analytics', 'nlp_specific') and ('trained' in low_narr or 'train ' in low_narr or 'training data' in low_narr):
        arch = 'custom_trained'
    elif entry_type == 'generic_use_pattern':
        arch = 'unknown'
    out['architecture_type'] = arch

    # has_model_training: 1 if narrative or arch implies training
    has_train = 0
    if arch in ('custom_trained', 'fine_tuned'):
        has_train = 1
    elif 'trained' in low_narr or 'training' in low_narr or 'fine-tune' in low_narr:
        has_train = 1
    out['has_model_training'] = has_train

    # ---------------- use_type ----------------
    use_type = 'mission_critical'
    if agency == 'DHS' and bureau in ('CBP', 'ICE', 'TSA', 'USCIS', 'FEMA', 'CISA', 'CWMD', 'OHS', 'USCG', 'USSS'):
        use_type = 'mission_critical'
    if bureau == 'CISA' or any(k in low_narr for k in ['cyber threat', 'cybersecurity', 'security operations center', 'malware', 'intrusion detection', 'phishing detect']):
        use_type = 'cybersecurity'
    if any(k in low_narr for k in [
        'human resources', 'hr ', ' hr,', 'employee onboard', 'budget process',
        'procurement', 'travel processing', 'time and attendance', 'help desk',
        'meeting summariz', 'document drafting',
    ]) and use_type == 'mission_critical':
        use_type = 'administrative'
    if any(k in low_narr for k in [
        'research', 'economic forecast', 'monetary policy', 'literature review',
        'scientific', 'experimental',
    ]) and agency in ('FRB',) and use_type == 'mission_critical':
        use_type = 'research'
    if any(k in low_narr for k in ['it operations', 'devops', 'cloud monitoring', 'log analy', 'ticket triag', 'system administration']):
        use_type = 'it_operations'
    out['use_type'] = use_type

    # is_public_facing
    out['is_public_facing'] = 1 if detect_public_facing(narrative) else 0

    # ---------------- reasoning ----------------
    quoted = ''
    # Try to find a substantive phrase from purpose or outputs
    for src in (purpose, outputs, name):
        cand = short_quote(src)
        if cand and len(cand.split()) >= 2:
            quoted = cand
            break
    if not quoted:
        quoted = name[:60]
    quoted = quoted.replace('"', "'").strip()

    # Build reason
    soph_label = {
        'general_llm': 'LLM use',
        'coding_assistant': 'coding assistant',
        'agentic': 'agentic workflow',
        'classical_ml': 'classical ML',
        'computer_vision': 'computer vision',
        'nlp_specific': 'specialized NLP',
        'predictive_analytics': 'predictive analytics',
    }[soph]
    scope_label = scope.replace('_', ' ')
    reasoning = f'"{quoted}" — {soph_label}, {scope_label} ({bureau or agency}).'
    out['reasoning'] = reasoning

    # ---------------- confidence ----------------
    confidence = 'medium'
    if is_mc or is_ghc or is_oai or is_anth or is_goog or 'github copilot' in low_narr:
        confidence = 'high'
    elif len(purpose) < 60 and len(outputs) < 60:
        confidence = 'low'
    elif entry_type == 'generic_use_pattern' and not (is_mc or is_oai):
        confidence = 'low'
    elif soph in ('computer_vision', 'classical_ml', 'predictive_analytics', 'nlp_specific') and len(purpose) > 100:
        confidence = 'high' if any(k in low_narr for k in ['trained on', 'model uses', 'algorithm', 'detect', 'classif', 'predict', 'forecast', 'recognition']) else 'medium'
    out['confidence'] = confidence

    return out


def main():
    with INPUT.open() as f:
        rows = list(csv.DictReader(f))
    out_rows = [classify_one(r) for r in rows]

    with OUT.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS, extrasaction='ignore')
        w.writeheader()
        for r in out_rows:
            w.writerow(r)

    # Validation
    assert len(out_rows) == len(rows), f'row mismatch: {len(out_rows)} vs {len(rows)}'
    print(f'Wrote {len(out_rows)} rows to {OUT}')

    # Report
    from collections import Counter
    print('is_generative_ai:', Counter(r['is_generative_ai'] for r in out_rows))
    print('deployment_scope:', Counter(r['deployment_scope'] for r in out_rows).most_common())
    print('ai_sophistication:', Counter(r['ai_sophistication'] for r in out_rows).most_common())
    print('entry_type:', Counter(r['entry_type'] for r in out_rows).most_common())
    print('tool_vendor:', Counter(r['tool_vendor'] for r in out_rows).most_common())
    print('use_type:', Counter(r['use_type'] for r in out_rows).most_common())
    print('confidence:', Counter(r['confidence'] for r in out_rows).most_common())


if __name__ == '__main__':
    main()
