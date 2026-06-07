"""
Wave1-E tagger: STATE + GSA + DOL + ED + EPA + SSA (~239 rows).
Reads inputs/E.csv, writes wave1/E.csv. No 2025-source reads.
"""
import csv, os, re, sys

IN = 'audit/retag/2024-tagging/inputs/E.csv'
OUT = 'audit/retag/2024-tagging/wave1/E.csv'

FIELDS = [
    'use_case_id_2024','tagged_by_agent','entry_type','is_generative_ai',
    'ai_sophistication','deployment_scope','confidence','reasoning',
    'is_general_llm_access','is_coding_tool','is_cots_commercial',
    'tool_product_name','tool_vendor','is_microsoft_copilot','is_openai',
    'is_anthropic','is_google','is_github_copilot','is_aws_ai',
    'is_enterprise_wide','architecture_type','has_model_training','use_type',
    'is_public_facing','scope_detail',
]


def short_quote(text, max_words=6):
    """Pick a 2-6 word quote — caller supplies; this just trims."""
    return text


def tag_row(r):
    """Manually-curated tagging for each row id. Returns a dict of fields."""
    rid = int(r['id'])
    fn = ROW_TAGS.get(rid)
    if fn is None:
        # If we hit a row without a manual entry, fallback to a low-confidence
        # NLP/classical inference based on commercial_ai+name.
        return generic_fallback(r)
    d = fn(r)
    d.setdefault('use_case_id_2024', r['id'])
    d.setdefault('tagged_by_agent', 'wave1-E')
    # enterprise_wide convenience
    if d.get('deployment_scope') == 'enterprise_wide':
        d['is_enterprise_wide'] = '1'
    return d


def generic_fallback(r):
    return {
        'use_case_id_2024': r['id'],
        'tagged_by_agent': 'wave1-E',
        'entry_type': 'custom_system',
        'is_generative_ai': '0',
        'ai_sophistication': 'classical_ml',
        'deployment_scope': 'office',
        'confidence': 'low',
        'reasoning': 'fallback: limited narrative signal.',
        'is_cots_commercial': '0',
        'architecture_type': 'unknown',
        'has_model_training': '0',
        'use_type': 'administrative',
        'is_public_facing': '0',
        'scope_detail': r.get('bureau','')[:60],
    }


# Helper builder
def T(entry_type, is_gen, sophistication, scope, conf, reasoning, **extra):
    base = {
        'entry_type': entry_type,
        'is_generative_ai': '1' if is_gen else '0',
        'ai_sophistication': sophistication,
        'deployment_scope': scope,
        'confidence': conf,
        'reasoning': reasoning,
    }
    base.update(extra)
    return base


# ============================================================================
# Per-row tag functions
# ============================================================================
ROW_TAGS = {}

def R(rid):
    def deco(fn):
        ROW_TAGS[rid] = fn
        return fn
    return deco


# ---------- DOL ----------
@R(34628)
def _(r): return T('custom_system', False, 'computer_vision', 'office', 'high',
    "'Custom machine learning model to extract data from complex forms' for OWCP benefits.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='DOL OWCP')

@R(34629)
def _(r): return T('generic_use_pattern', False, 'nlp_specific', 'department', 'medium',
    "'automatically translate unofficial documents' via NLP — dept-wide initiative.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='1', scope_detail='DOL Department Wide')

@R(34630)
def _(r): return T('generic_use_pattern', False, 'nlp_specific', 'department', 'medium',
    "'Transcription of speech to text' shared across OWCP/VETS/WHD.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='DOL OWCP/VETS/WHD')

@R(34631)
def _(r): return T('generic_use_pattern', False, 'nlp_specific', 'department', 'medium',
    "'Text to speech (Neural) for more realistic human sounding applications'.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='DOL EBSA/OHR')

@R(34632)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'training custom natural language processing models' for OWCP claims notes.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='DOL OWCP')

@R(34633)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'chatbot helps the end user' for OTAA petition status — pre-determined Q&A.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='mission_critical', is_public_facing='1', scope_detail='DOL OTAA')

@R(34634)
def _(r): return T('custom_system', False, 'computer_vision', 'office', 'high',
    "'Custom machine learning model to extract data from complex forms' for WHD payroll.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='DOL WHD')

@R(34635)
def _(r): return T('product_deployment', False, 'computer_vision', 'office', 'high',
    "'Hololens... AI used to train Inspectors' — Microsoft MR headset.",
    is_cots_commercial='1', tool_product_name='HoloLens', tool_vendor='Microsoft',
    architecture_type='inference_only', has_model_training='0',
    use_type='mission_critical', is_public_facing='0', scope_detail='DOL OSHA')

@R(34636)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'medium',
    "'Conversational AI Assistant & DOL intranet websites' for procurement Qs.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='DOL OSPE')

@R(34637)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'medium',
    "'AI detection of mismatched addresses and garbled text' in benefits letters.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='mission_critical', is_public_facing='0', scope_detail='DOL OWCP')

@R(34638)
def _(r): return T('generic_use_pattern', False, 'nlp_specific', 'department', 'medium',
    "'using AI to identify data within the document, and... NLP to classify' — dept-wide ERM.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='DOL Department Wide')

@R(34639)
def _(r): return T('generic_use_pattern', False, 'nlp_specific', 'office', 'high',
    "'AI is used only for transcription' of EBSA IVR call recordings.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='DOL EBSA')

@R(34640)
def _(r): return T('custom_system', False, 'computer_vision', 'office', 'high',
    "'Automatic processing of continuation of benefits form' for OWCP.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='DOL OWCP')

@R(34641)
def _(r): return T('bespoke_application', True, 'general_llm', 'office', 'medium',
    "'The GPT will extract the data and into a spreadsheet' — ETA Form Recognizer with GPT.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='mission_critical', is_public_facing='0', scope_detail='DOL ETA')

@R(34642)
def _(r): return T('bespoke_application', True, 'general_llm', 'office', 'high',
    "'open source large language model to summarize publicly available case recording'.",
    is_cots_commercial='0', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='DOL OSHA')

@R(34643)
def _(r): return T('custom_system', False, 'nlp_specific', 'bureau', 'high',
    "'autocoder reads the job title and assigns... SOC codes' for OEWS survey.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='BLS OEWS')

@R(34644)
def _(r): return T('custom_system', False, 'nlp_specific', 'bureau', 'high',
    "'BLS receives bulk data from some corporations' classified via ML.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='BLS CPI')

@R(34645)
def _(r): return T('custom_system', False, 'nlp_specific', 'bureau', 'high',
    "'assign a reported expense description... to expense classification categories'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='BLS CE')

@R(34646)
def _(r): return T('bespoke_application', True, 'general_llm', 'department', 'high',
    "'Private and secure in-house solution... Generative AI models and semantic search'.",
    is_general_llm_access='1', is_cots_commercial='0', architecture_type='rag_pipeline',
    has_model_training='0', use_type='administrative', is_public_facing='0',
    scope_detail='DOL OCIO')

@R(34657)
def _(r): return T('product_deployment', True, 'coding_assistant', 'office', 'high',
    "'Automatically generate software code using Microsoft Copilot'.",
    is_coding_tool='1', is_cots_commercial='1', tool_product_name='GitHub Copilot',
    tool_vendor='Microsoft', is_microsoft_copilot='1', is_github_copilot='1',
    architecture_type='inference_only', has_model_training='0', use_type='it_operations',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34662)
def _(r): return T('generic_use_pattern', True, 'general_llm', 'office', 'medium',
    "'The bot will take the transcript and summarize the meeting notes'.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='DOL OCIO')

@R(34664)
def _(r): return T('product_deployment', False, 'classical_ml', 'office', 'high',
    "'Camtasia... screen recordings and video tutorials' COTS AI features.",
    is_cots_commercial='1', tool_product_name='Camtasia', tool_vendor='TechSmith',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34665)
def _(r): return T('product_deployment', False, 'classical_ml', 'office', 'high',
    "'Adobe Premiere Pro incorporates several AI components' for video editing.",
    is_cots_commercial='1', tool_product_name='Premiere Pro', tool_vendor='Adobe',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34666)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'high',
    "'Audiate primarily uses AI for Speech-to-text transcription' — TechSmith COTS.",
    is_cots_commercial='1', tool_product_name='Audiate', tool_vendor='TechSmith',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34667)
def _(r): return T('product_deployment', False, 'computer_vision', 'office', 'high',
    "'SnagIt's Optional Character Recognition' — COTS OCR.",
    is_cots_commercial='1', tool_product_name='Snagit', tool_vendor='TechSmith',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34668)
def _(r): return T('product_feature', True, 'general_llm', 'team', 'high',
    "'MetaAI offer search and chatbot assistance with the Facebook application'.",
    is_cots_commercial='1', tool_product_name='Meta AI', tool_vendor='Meta',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO PR')

@R(34669)
def _(r): return T('product_feature', False, 'classical_ml', 'office', 'high',
    "'Google Authenticator adds an extra layer of security' — auth product feature.",
    is_cots_commercial='1', tool_product_name='Google Authenticator', tool_vendor='Google',
    is_google='1', architecture_type='inference_only', has_model_training='0',
    use_type='cybersecurity', is_public_facing='0', scope_detail='DOL OCIO')

@R(34670)
def _(r): return T('product_feature', False, 'predictive_analytics', 'office', 'high',
    "'real-time traffic and route prediction' inside Google Maps.",
    is_cots_commercial='1', tool_product_name='Google Maps', tool_vendor='Google',
    is_google='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='DOL OCIO')

@R(34671)
def _(r): return T('product_feature', False, 'classical_ml', 'office', 'high',
    "'Instagram Mobile App' — feed AI 'cannot be turned off'.",
    is_cots_commercial='1', tool_product_name='Instagram', tool_vendor='Meta',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34672)
def _(r): return T('product_feature', False, 'classical_ml', 'office', 'high',
    "'Microsoft Authenticator for easy, secure sign-ins' — auth feature.",
    is_cots_commercial='1', tool_product_name='Microsoft Authenticator', tool_vendor='Microsoft',
    architecture_type='inference_only', has_model_training='0', use_type='cybersecurity',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34673)
def _(r): return T('product_feature', False, 'classical_ml', 'office', 'low',
    "'Periscope mobile app will be discontinued' — minimal AI exposure.",
    is_cots_commercial='1', tool_product_name='Periscope', tool_vendor='Twitter',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34674)
def _(r): return T('product_feature', False, 'classical_ml', 'office', 'high',
    "'X (formerly Twitter) Mobile App' — feed ranking AI feature.",
    is_cots_commercial='1', tool_product_name='X (Twitter)', tool_vendor='X',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34675)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'high',
    "'Nuance Dragon Naturally Speaking... software used for diction'.",
    is_cots_commercial='1', tool_product_name='Dragon NaturallySpeaking', tool_vendor='Nuance',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34676)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'high',
    "'ZoomText Magnifier/Reader... for low-vision users' — accessibility TTS.",
    is_cots_commercial='1', tool_product_name='ZoomText', tool_vendor='Freedom Scientific',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34677)
def _(r): return T('product_feature', True, 'coding_assistant', 'office', 'medium',
    "'Visual Studio IDE... edit, debug, and build code' with AI assist.",
    is_coding_tool='1', is_cots_commercial='1', tool_product_name='Visual Studio',
    tool_vendor='Microsoft', architecture_type='inference_only', has_model_training='0',
    use_type='it_operations', is_public_facing='0', scope_detail='DOL OCIO')

@R(34678)
def _(r): return T('product_deployment', False, 'computer_vision', 'office', 'high',
    "'ABBYY FineReader is an optical character recognition (OCR) system'.",
    is_cots_commercial='1', tool_product_name='FineReader', tool_vendor='ABBYY',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34679)
def _(r): return T('product_feature', False, 'computer_vision', 'office', 'medium',
    "'Google Earth Pro... advanced GIS and mapping features'.",
    is_cots_commercial='1', tool_product_name='Google Earth Pro', tool_vendor='Google',
    is_google='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='DOL OCIO')

@R(34680)
def _(r): return T('product_deployment', True, 'classical_ml', 'office', 'high',
    "'Adobe Creative Cloud leverages AI' for design generation.",
    is_cots_commercial='1', tool_product_name='Creative Cloud', tool_vendor='Adobe',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34681)
def _(r): return T('product_deployment', False, 'classical_ml', 'office', 'medium',
    "'Autodesk Civil 3D incorporates AI components' for engineering models.",
    is_cots_commercial='1', tool_product_name='Civil 3D', tool_vendor='Autodesk',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34682)
def _(r): return T('product_deployment', True, 'general_llm', 'office', 'medium',
    "'AI tool to recommend the structure of a course' — course-design GenAI.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='DOL OCIO')

@R(34683)
def _(r): return T('product_feature', False, 'nlp_specific', 'office', 'high',
    "'Webex has an internal transcription feature' — meeting transcript COTS.",
    is_cots_commercial='1', tool_product_name='Webex', tool_vendor='Cisco',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34684)
def _(r): return T('product_deployment', False, 'computer_vision', 'office', 'high',
    "'Convert physical documents or image-based text' — OmniPage OCR.",
    is_cots_commercial='1', tool_product_name='OmniPage', tool_vendor='Kofax',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34685)
def _(r): return T('product_deployment', False, 'classical_ml', 'office', 'high',
    "'Tableau Public 2023... share data visualizations' — Tableau AI features.",
    is_cots_commercial='1', tool_product_name='Tableau Public', tool_vendor='Salesforce',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34686)
def _(r): return T('product_deployment', False, 'computer_vision', 'office', 'high',
    "'Text-searchable PDFs' via Adobe Acrobat OCR.",
    is_cots_commercial='1', tool_product_name='Acrobat Pro', tool_vendor='Adobe',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34687)
def _(r): return T('product_deployment', False, 'predictive_analytics', 'office', 'medium',
    "'Tableau Creator... visual data dashboards, reports, and predictive models'.",
    is_cots_commercial='1', tool_product_name='Tableau', tool_vendor='Salesforce',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34688)
def _(r): return T('product_deployment', True, 'nlp_specific', 'office', 'high',
    "'Grammarly 14... grammar, punctuation, and style errors' COTS NLP.",
    is_cots_commercial='1', tool_product_name='Grammarly', tool_vendor='Grammarly',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34689)
def _(r): return T('product_deployment', True, 'classical_ml', 'office', 'high',
    "'automating repetitive tasks' in Adobe CC + Acrobat.",
    is_cots_commercial='1', tool_product_name='Creative Cloud', tool_vendor='Adobe',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34690)
def _(r): return T('product_feature', False, 'predictive_analytics', 'office', 'medium',
    "'Optimized project timelines... predictive alerts' in MS Project 365.",
    is_cots_commercial='1', tool_product_name='Microsoft Project 365', tool_vendor='Microsoft',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34691)
def _(r): return T('product_deployment', False, 'predictive_analytics', 'office', 'high',
    "'advanced statistical tools... regression models' — Stata.",
    is_cots_commercial='1', tool_product_name='Stata/MP', tool_vendor='StataCorp',
    architecture_type='inference_only', has_model_training='0', use_type='research',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34692)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'high',
    "'transcribe spoken language into text' — Dragon Legal.",
    is_cots_commercial='1', tool_product_name='Dragon Legal', tool_vendor='Nuance',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34693)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'high',
    "'Converts written text into natural-sounding speech' — Speechify TTS.",
    is_cots_commercial='1', tool_product_name='Speechify', tool_vendor='Speechify',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34694)
def _(r): return T('product_feature', True, 'general_llm', 'office', 'high',
    "'AI-driven automation' inside Adobe Express — generative design feature.",
    is_cots_commercial='1', tool_product_name='Adobe Express', tool_vendor='Adobe',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34695)
def _(r): return T('product_deployment', True, 'general_llm', 'office', 'high',
    "'Westlaw Precision & CoCounsel... case analysis, and predictions'.",
    is_cots_commercial='1', tool_product_name='CoCounsel', tool_vendor='Thomson Reuters',
    architecture_type='rag_pipeline', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34696)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'high',
    "'Kurzweil 1000 makes printed or electronic text accessible' TTS.",
    is_cots_commercial='1', tool_product_name='Kurzweil 1000', tool_vendor='Kurzweil',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='DOL OCIO')

@R(34697)
def _(r): return T('product_deployment', True, 'general_llm', 'office', 'medium',
    "'Microsoft Office Suite' — broad productivity AI features.",
    is_cots_commercial='1', tool_product_name='Microsoft Office', tool_vendor='Microsoft',
    is_microsoft_copilot='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='DOL OCIO')

@R(34647)
def _(r): return T('custom_system', False, 'nlp_specific', 'bureau', 'high',
    "'Suggest appropriate occupation code... via NLP' for ETA UI data.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='DOL ETA')

@R(34648)
def _(r): return T('bespoke_application', True, 'general_llm', 'office', 'medium',
    "'Application of custom Generative AI model to create Notice of Deficiency'.",
    is_cots_commercial='0', architecture_type='fine_tuned', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='DOL ETA')

@R(34649)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'high',
    "'Amazon Web Services Personal Identifying Information scrubber' — AWS Comprehend.",
    is_cots_commercial='1', tool_product_name='Comprehend PII', tool_vendor='AWS',
    is_aws_ai='1', architecture_type='inference_only', has_model_training='0',
    use_type='mission_critical', is_public_facing='0', scope_detail='DOL OSHA')

@R(34650)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'medium',
    "'chatbot helps the end user with basic information about the Workforce Recruitment Program'.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='mission_critical', is_public_facing='1', scope_detail='DOL ODEP')

@R(34651)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'medium',
    "'AI tool to help perform initial analysis of the incoming 9141 and 9089 applications'.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='mission_critical', is_public_facing='0', scope_detail='DOL ETA')

@R(34652)
def _(r): return T('product_deployment', True, 'general_llm', 'office', 'medium',
    "'AI-powered algorithms analyze course content and quickly generate test questions'.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='DOL OSHA')

@R(34653)
def _(r): return T('custom_system', False, 'predictive_analytics', 'office', 'high',
    "'Worker PLUS model... evolutionary iteration of the Paid Family and Medical Leave Simulator'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='research', is_public_facing='0', scope_detail='DOL CEO')

@R(34654)
def _(r): return T('custom_system', False, 'nlp_specific', 'bureau', 'high',
    "'SOII... narratives describing cases of work-related injury and illness... codes'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='BLS SOII')

@R(34655)
def _(r): return T('custom_system', False, 'classical_ml', 'bureau', 'high',
    "'CFOI Record Matching programs' for fatal injury data.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='BLS CFOI')

@R(34656)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'medium',
    "'Auto-code assigning Occupational Injury and Illness Classification (OIICS)'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='DOL OSHA')

@R(34658)
def _(r): return T('custom_system', False, 'predictive_analytics', 'bureau', 'high',
    "'BLS productivity office publishes measures of hours worked' via prediction.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='BLS Productivity')

@R(34659)
def _(r): return T('custom_system', False, 'classical_ml', 'bureau', 'high',
    "'establishment-based surveys' using Frame API similarity scoring.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='BLS')

@R(34660)
def _(r): return T('custom_system', False, 'nlp_specific', 'bureau', 'high',
    "'Custom machine learning model to predict an expense classification category'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='BLS CE')

@R(34661)
def _(r): return T('custom_system', False, 'predictive_analytics', 'bureau', 'high',
    "'Custom machine learning statistical models to impute missing expenditure values'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='BLS CE')

@R(34663)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'high',
    "'NIOCCS, a free tool offered by NIOSH... code industry and occupation from text'.",
    is_cots_commercial='0', tool_product_name='NIOCCS', tool_vendor='NIOSH',
    architecture_type='inference_only', has_model_training='0', use_type='mission_critical',
    is_public_facing='1', scope_detail='DOL OSHA')


# ---------- ED Generative AI Usage rows (36126-36176) ----------
# All filed under template "Generative AI Usage" — one row per bureau per task.
# Tag uniformly as generic_use_pattern, is_general_llm_access=1.
ED_GENAI_IDS = list(range(36126, 36177))

def _ed_genai(r, pb_quote):
    bureau = r['bureau']
    return T('generic_use_pattern', True, 'general_llm', 'bureau', 'high',
        pb_quote,
        is_general_llm_access='1', is_cots_commercial='1',
        architecture_type='inference_only', has_model_training='0',
        use_type='administrative', is_public_facing='0',
        scope_detail=f'ED {bureau}')

@R(36126)
def _(r): return _ed_genai(r, "'AI will provide summaries and outlines for projects and presentations'.")
@R(36127)
def _(r): d=_ed_genai(r, "'AI will provide code snippets in various languages'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36128)
def _(r): return _ed_genai(r, "'AI suggests possible courses of actions for given scenarios'.")
@R(36129)
def _(r): return _ed_genai(r, "'AI provides key points, summaries, and action items'.")
@R(36130)
def _(r): return _ed_genai(r, "'AI provides sample paragraphs that may assist in the writing process'.")
@R(36131)
def _(r): return _ed_genai(r, "'AI will create paragraphs and images to augment visual designs'.")
@R(36132)
def _(r): d=_ed_genai(r, "'AI will provide code snippets... Excel or Power BI DAX formulas'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36133)
def _(r): d=_ed_genai(r, "'AI will provide snippets of R code for data analysis'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36134)
def _(r): return _ed_genai(r, "'AI provides sample paragraphs that may assist in the communications process'.")
@R(36135)
def _(r): d=_ed_genai(r, "'AI will provide suggestions of code optimization opportunities'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36136)
def _(r): d=_ed_genai(r, "'train employees on prompt engineering, by comparing... generated code snippets'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36137)
def _(r): return _ed_genai(r, "'AI is used to convert between related data types (county name to county FIPS code)'.")
@R(36138)
def _(r): return _ed_genai(r, "'training employees by generating paragraphs and images related to the topic'.")
@R(36139)
def _(r): return _ed_genai(r, "'AI is used to generate mock data sets for testing'.")
@R(36140)
def _(r): d=_ed_genai(r, "'AI is used to generate sample snippets of code'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36141)
def _(r): return _ed_genai(r, "'AI will generate portions of outreach strategies, outline project plans'.")
@R(36142)
def _(r): return _ed_genai(r, "'AI is used to research and analyze public articles and policies'.")
@R(36143)
def _(r): return _ed_genai(r, "'fabricated examples of prohibited prompt information' for DLP tests.")
@R(36144)
def _(r): return _ed_genai(r, "'AI is leveraged to suggest descriptive paragraphs, workflow diagrams'.")
@R(36145)
def _(r): return _ed_genai(r, "'AI is provided with publicly available examples of document structures'.")
@R(36146)
def _(r): d=_ed_genai(r, "'AI is used to create sample DAX code'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36147)
def _(r): return _ed_genai(r, "'AI is used to help with message communication in written paragraphs'.")
@R(36148)
def _(r): d=_ed_genai(r, "'AI provides examples of the latest technologies that can assist in the development of code'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36149)
def _(r): return _ed_genai(r, "'asked to describe them for 508 accessibility compliance'.")
@R(36150)
def _(r): d=_ed_genai(r, "'AI is used to generate snippets of code that can be used for data visualization'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36151)
def _(r): return _ed_genai(r, "'create summaries of publicly available reports, policies, and media'.")
@R(36152)
def _(r): return _ed_genai(r, "'generate email templates and drafts of content for public consumption'.")
@R(36153)
def _(r): d=_ed_genai(r, "'AI provides code snippets to assist in data analysis and troubleshooting in power BI and python'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36154)
def _(r): return _ed_genai(r, "'identify trends in specific programs and provide summary narratives'.")
@R(36155)
def _(r): return _ed_genai(r, "'AI provides public policy analysis, templates of written materials, sample paragraphs'.")
@R(36156)
def _(r): return _ed_genai(r, "'AI is used to generate text for many uses, including: sample drafts for emails'.")
@R(36157)
def _(r): return _ed_genai(r, "'list of potential uses for AI in Department business'.")
@R(36158)
def _(r): d=_ed_genai(r, "'Code snippets are generated to assist in Data analysis and statistics'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36159)
def _(r): return _ed_genai(r, "'assisting employees in project plan documentation, writing program communications'.")
@R(36160)
def _(r): return _ed_genai(r, "'find and summarize publicly available cases involving AI'.")
@R(36161)
def _(r): return _ed_genai(r, "'summaries of the strengths and weaknesses of AI tools'.")
@R(36162)
def _(r): return _ed_genai(r, "'Approved AI tools are tested to evaluate their capability to provide legal information'.")
@R(36163)
def _(r): return _ed_genai(r, "'AI is used to gather information... structure of contracts, state and federal laws'.")
@R(36164)
def _(r): return _ed_genai(r, "'AI is tested to evaluate the breadth of available information surrounding Congressional Directives'.")
@R(36165)
def _(r): d=_ed_genai(r, "'AI generates Excel Macros and Complex Formulae'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36166)
def _(r): return _ed_genai(r, "'brainstorm project ideas, and explore potential use cases for educators'.")
@R(36167)
def _(r): return _ed_genai(r, "'Public AI tools are used to summarize publicly available documents'.")
@R(36168)
def _(r): return _ed_genai(r, "'AI tools provide drafts of narratives, marketing materials, public webinar scripts'.")
@R(36169)
def _(r): return _ed_genai(r, "'AI is tested to provide a review of the potential uses of AI'.")
@R(36170)
def _(r): d=_ed_genai(r, "'AI is prompted to provide snippets of VBA Code and complex formulae for Excel'."); d['is_coding_tool']='1'; d['use_type']='it_operations'; return d
@R(36171)
def _(r): return _ed_genai(r, "'AI is prompted to create images representing the Team Values'.")
@R(36172)
def _(r): return _ed_genai(r, "'AI tools provide summaries of accomplishment reports'.")
@R(36173)
def _(r): return _ed_genai(r, "'summaries of publicly available assistance materials, publicly shared materials'.")
@R(36174)
def _(r): return _ed_genai(r, "'examples of paragraphs to augment written materials including blog posts'.")
@R(36175)
def _(r): return _ed_genai(r, "'Written paragraphs are generated to assist in drafting public remarks'.")
@R(36176)
def _(r): return _ed_genai(r, "'AI is prompted to provide instances where AI technology can be used to assist in the higher education arena'.")

@R(36177)
def _(r): return T('product_deployment', True, 'general_llm', 'office', 'high',
    "'CAISY is designed to enhance decision-making... predictive analytics, and intelligent automation' — Skillsoft Percipio AI.",
    is_cots_commercial='1', tool_product_name='Skillsoft Percipio CAISY', tool_vendor='Skillsoft',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='ED OFO')

@R(36178)
def _(r): return T('product_deployment', True, 'nlp_specific', 'office', 'high',
    "'Otter.AI... real-time transcription' COTS deployment for public meetings.",
    is_cots_commercial='1', tool_product_name='Otter.ai', tool_vendor='Otter.ai',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='1', scope_detail='ED OUS')

@R(36179)
def _(r): return T('bespoke_application', True, 'general_llm', 'bureau', 'high',
    "'AWS Bedrock... text generation, summarization, conversational AI' in FSA EDMAPS.",
    is_cots_commercial='1', tool_product_name='Bedrock', tool_vendor='AWS',
    is_aws_ai='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='FSA EDMAPS')


# ---------- EPA ----------
@R(34698)
def _(r): return T('bespoke_application', True, 'general_llm', 'department', 'high',
    "'generative AI chatbot tool to EPA staff' — agency GovChat platform.",
    is_general_llm_access='1', is_cots_commercial='0', architecture_type='inference_only',
    has_model_training='0', use_type='administrative', is_public_facing='0',
    scope_detail='EPA Office of Mission Support')

@R(34699)
def _(r): return T('bespoke_application', True, 'general_llm', 'office', 'medium',
    "'20 years of help requests... transition to Jira Service Desk' via LLM.",
    is_cots_commercial='0', architecture_type='rag_pipeline', has_model_training='0',
    use_type='it_operations', is_public_facing='0', scope_detail='EPA OAR helpdesk')

@R(34700)
def _(r): return T('bespoke_application', True, 'general_llm', 'office', 'high',
    "'Provide a chatbot to respond to EPA monitoring system analyst questions'.",
    is_cots_commercial='0', architecture_type='rag_pipeline', has_model_training='0',
    use_type='mission_critical', is_public_facing='0', scope_detail='EPA OAR emissions')

@R(34701)
def _(r): return T('custom_system', False, 'predictive_analytics', 'office', 'high',
    "'predictive tools to identify lead service lines' via microbiome biomarkers.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='research', is_public_facing='0', scope_detail='EPA ORD')

@R(34702)
def _(r): return T('bespoke_application', True, 'general_llm', 'office', 'high',
    "'Generative AI for Study Evaluation and Document Chat'.",
    is_cots_commercial='0', architecture_type='rag_pipeline', has_model_training='0',
    use_type='research', is_public_facing='0', scope_detail='EPA ORD')

@R(34703)
def _(r): return T('product_deployment', True, 'general_llm', 'office', 'medium',
    "'create realistic audio narration files' — TTS COTS for Natural Gas STAR videos.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='1', scope_detail='EPA OAR')

@R(34704)
def _(r): return T('custom_system', False, 'classical_ml', 'department', 'high',
    "'machine learning model predicts records schedules' across EPA.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='administrative', is_public_facing='0', scope_detail='EPA Office of Mission Support')

@R(34705)
def _(r): return T('product_deployment', True, 'general_llm', 'department', 'high',
    "'Microsoft CoPilot within the M365 Purview Security' suite.",
    is_general_llm_access='0', is_cots_commercial='1', tool_product_name='Copilot for Security',
    tool_vendor='Microsoft', is_microsoft_copilot='1', architecture_type='inference_only',
    has_model_training='0', use_type='cybersecurity', is_public_facing='0',
    scope_detail='EPA Office of Mission Support')

@R(34706)
def _(r): return T('product_feature', True, 'general_llm', 'department', 'medium',
    "'ServiceNow's upcoming AI tools for employees to engage with'.",
    is_cots_commercial='1', tool_product_name='Now Assist', tool_vendor='ServiceNow',
    architecture_type='inference_only', has_model_training='0', use_type='it_operations',
    is_public_facing='0', scope_detail='EPA Office of Mission Support')

@R(34707)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'machine learning to rank references by title and abstract' for ORD literature review.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='research', is_public_facing='0', scope_detail='EPA ORD')

@R(34708)
def _(r): return T('bespoke_application', False, 'classical_ml', 'department', 'low',
    "'DMAP... Proposed use of AI and ML to enhance' — planning stage platform.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='it_operations', is_public_facing='0', scope_detail='EPA Office of Mission Support')

@R(34709)
def _(r): return T('bespoke_application', True, 'general_llm', 'office', 'high',
    "'intelligent... search and processing system' for Superfund SEMS chatbot.",
    is_cots_commercial='0', architecture_type='rag_pipeline', has_model_training='0',
    use_type='mission_critical', is_public_facing='0', scope_detail='EPA OLEM')

@R(34710)
def _(r): return T('custom_system', False, 'predictive_analytics', 'office', 'high',
    "'Risk scoring of Large Quantity Generators (LQGs) to support RCRA inspections'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='EPA Enforcement')

@R(34711)
def _(r): return T('custom_system', False, 'predictive_analytics', 'office', 'high',
    "'Identify high risk NPDES facilities that don't submit Discharge Monitoring Reports'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='EPA Enforcement')

@R(34712)
def _(r): return T('custom_system', False, 'predictive_analytics', 'office', 'high',
    "'Risk scoring of Majors and Synthetic Minor Facilities to support CAA inspections'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='EPA Enforcement')

@R(34713)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'medium',
    "'Extracting references from technical documents' for NCEE researcher visibility.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='research', is_public_facing='0', scope_detail='EPA NCEE')

@R(34714)
def _(r): return T('custom_system', False, 'predictive_analytics', 'office', 'high',
    "'Prediction of whether a streamflow is perennial, intermittent, or ephemeral'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='research', is_public_facing='0', scope_detail='EPA OW')


# ---------- GSA ----------
@R(34715)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'SRT intakes SAM.gov data... machine learning algorithms... Natural Language' for ICT compliance.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='GSA OGP')

@R(34716)
def _(r): return T('custom_system', False, 'classical_ml', 'office', 'high',
    "'classifies each transaction within the Government-wide Category Management Taxonomy'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='GSA FAS')

@R(34717)
def _(r): return T('custom_system', False, 'predictive_analytics', 'office', 'high',
    "'City Pair Program air travel purchase data and creates near-term forecasts'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='GSA FAS')

@R(34718)
def _(r): return T('custom_system', False, 'classical_ml', 'office', 'high',
    "'Classification of obligation transactions in to GWAS subcategories'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='GSA FAS')

@R(34719)
def _(r): return T('custom_system', False, 'predictive_analytics', 'office', 'high',
    "'Applies obligation forecasting to ITC contracts' for breach risk.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='GSA FAS')

@R(34720)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'medium',
    "'Uses token extraction from product descriptions' to refine PSC categories.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='GSA FAS')

@R(34721)
def _(r): return T('custom_system', False, 'predictive_analytics', 'office', 'medium',
    "'historical data... near-term forecasts for the upcoming fiscal year' — KPI pilot.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='GSA FAS')

@R(34722)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'high',
    "'document repository by Tanjo (tanjo.ai)' — semantic discovery COTS.",
    is_cots_commercial='1', tool_product_name='Enterprise Brain', tool_vendor='Tanjo',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='GSA IT')

@R(34723)
def _(r): return T('custom_system', False, 'computer_vision', 'office', 'high',
    "'AI model that can solve AWS's captcha' so Selenium isn't blocked.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='it_operations', is_public_facing='0', scope_detail='GSA IT')

@R(34724)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'building a model to take generic Service Now tickets and classify them'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='it_operations', is_public_facing='0', scope_detail='GSA IT')

@R(34725)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'high',
    "'Virtual agent that uses ML... natural language chatbot... named Curie'.",
    is_cots_commercial='1', tool_product_name='ServiceNow Virtual Agent', tool_vendor='ServiceNow',
    architecture_type='inference_only', has_model_training='0', use_type='it_operations',
    is_public_facing='0', scope_detail='GSA IT')

@R(34726)
def _(r): return T('bespoke_application', False, 'computer_vision', 'office', 'medium',
    "'pilot program to test the feasibility... AWS cloud service' for GREX leasing docs.",
    is_cots_commercial='1', tool_vendor='AWS', is_aws_ai='1',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='GSA PBS')

@R(34727)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'automated machine learning evaluation tool... evaluation of vendor proposals'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='GSA FAS QP0A')

@R(34728)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'medium',
    "'survey comments are worth the time of analysts reading' — USA.gov spam classifier.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='administrative', is_public_facing='0', scope_detail='GSA TTS')

@R(34729)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'high',
    "'Classifying Qualitative Data with Medallia' for USA.gov topic classification.",
    is_cots_commercial='1', tool_product_name='Medallia', tool_vendor='Medallia',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='GSA TTS USA.gov')

@R(34730)
def _(r): return T('product_deployment', False, 'classical_ml', 'department', 'high',
    "'Elastic Machine Learning' to alert on anomalous data patterns for SOC analysts.",
    is_cots_commercial='1', tool_product_name='Elastic ML', tool_vendor='Elastic',
    architecture_type='inference_only', has_model_training='0', use_type='cybersecurity',
    is_public_facing='0', scope_detail='GSA SOC')

@R(34731)
def _(r): return T('bespoke_application', True, 'general_llm', 'department', 'medium',
    "'Leverage an LLM that has been given access to our security logs' for SOC search.",
    is_cots_commercial='1', architecture_type='rag_pipeline', has_model_training='0',
    use_type='cybersecurity', is_public_facing='0', scope_detail='GSA SOC')

@R(34732)
def _(r): return T('bespoke_application', True, 'general_llm', 'office', 'medium',
    "'introduction of a chatbot will enable the GSA FAS NCSC to streamline the customer experience'.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='mission_critical', is_public_facing='1', scope_detail='GSA FAS NCSC')

@R(34733)
def _(r): return T('bespoke_application', False, 'computer_vision', 'office', 'medium',
    "'intelligently capture, classify, and transfer critical data from unstructured' docs.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='GSA IT')

@R(34734)
def _(r): return T('bespoke_application', False, 'nlp_specific', 'office', 'medium',
    "'ChatBot to easily capture employee peer to peer recognitions' with NLP.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='GSA OAS')

@R(34735)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'medium',
    "'off-the-shelf product that provides natural language driven, contextual help using Maximo'.",
    is_cots_commercial='1', tool_product_name='Maximo', tool_vendor='IBM',
    architecture_type='inference_only', has_model_training='0', use_type='it_operations',
    is_public_facing='0', scope_detail='GSA PBS NCMMS')

@R(34736)
def _(r): return T('bespoke_application', False, 'computer_vision', 'department', 'high',
    "'facial matching AI component' inside Login.gov identity verification.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='mission_critical', is_public_facing='1', scope_detail='GSA Login.gov')

@R(34737)
def _(r): return T('product_deployment', True, 'general_llm', 'enterprise_wide', 'high',
    "'Gemini for Workspace pilot study... enhance productivity, collaboration, and efficiency'.",
    is_general_llm_access='1', is_cots_commercial='1', tool_product_name='Gemini for Workspace',
    tool_vendor='Google', is_google='1', architecture_type='inference_only',
    has_model_training='0', use_type='administrative', is_public_facing='0',
    scope_detail='GSA agency-wide')

@R(34738)
def _(r): return T('product_deployment', True, 'computer_vision', 'office', 'high',
    "'QBIQ pilot is to test the capabilities to rapidly test-fit spaces' via generative layout.",
    is_cots_commercial='1', tool_product_name='QBIQ', tool_vendor='QBIQ',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='GSA PBS')


# ---------- SSA ----------
@R(35052)
def _(r): return T('custom_system', False, 'nlp_specific', 'bureau', 'high',
    "'Insight... decision support software used by hearings and appeals-level Disability... 43 Quality flags'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA OARO')

@R(35053)
def _(r): return T('custom_system', False, 'nlp_specific', 'bureau', 'high',
    "'visualize, search, and more easily identify relevant clinical content in medical records'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA OCIO IMAGEN')

@R(35054)
def _(r): return T('custom_system', False, 'classical_ml', 'bureau', 'high',
    "'identifies, flags, and marks duplicates' for hearings.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA OCIO')

@R(35055)
def _(r): return T('custom_system', False, 'computer_vision', 'bureau', 'high',
    "'classify, identify and extract structured, semi-structured forms containing printed and handwritten fields'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA OCIO')

@R(35056)
def _(r): return T('custom_system', False, 'classical_ml', 'bureau', 'high',
    "'reviews data during case development so it can be better categorized'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA OARO MDW')

@R(35057)
def _(r): return T('custom_system', False, 'predictive_analytics', 'bureau', 'high',
    "'identifies high-risk iClaims... further review before additional action'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA OARO')

@R(35058)
def _(r): return T('custom_system', False, 'predictive_analytics', 'bureau', 'high',
    "'identifies high likelihood of error in certain claims and refers them for review'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA OARO')

@R(35059)
def _(r): return T('custom_system', False, 'predictive_analytics', 'bureau', 'high',
    "'identifies possible representative payee fraud and flags for review'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA OARO')

@R(35060)
def _(r): return T('custom_system', False, 'predictive_analytics', 'bureau', 'high',
    "'identifies disability cases with the greatest likelihood of medical improvement' for CDRs.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA OARO')

@R(35061)
def _(r): return T('custom_system', False, 'predictive_analytics', 'bureau', 'high',
    "'identifies SSI overpayment cases that have highest expected overpayments'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA OARO')

@R(35062)
def _(r): return T('custom_system', False, 'predictive_analytics', 'bureau', 'high',
    "'flags high likelihood favorable claims and refers them to human adjudicators'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA OARO PATH')

@R(35063)
def _(r): return T('custom_system', False, 'predictive_analytics', 'bureau', 'high',
    "'screen initial applications to identify cases where a favorable disability determination is highly likely'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA ORDP QDD')

@R(35064)
def _(r): return T('custom_system', False, 'computer_vision', 'bureau', 'high',
    "'extract text/data from scanned images/documents representing pay stubs'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='1', scope_detail='SSA OCIO MOBWR')

@R(35065)
def _(r): return T('custom_system', False, 'nlp_specific', 'bureau', 'high',
    "'bot answers caller's questions using approved FAQs found on SSA.GOV'.",
    is_cots_commercial='0', architecture_type='rag_pipeline', has_model_training='0',
    use_type='mission_critical', is_public_facing='1', scope_detail='SSA 800#')

@R(35066)
def _(r): return T('bespoke_application', True, 'general_llm', 'bureau', 'high',
    "'Generative AI model to analyze SSA's National 800 Number transcripts'.",
    is_cots_commercial='0', architecture_type='inference_only', has_model_training='0',
    use_type='mission_critical', is_public_facing='0', scope_detail='SSA OARO')

@R(35067)
def _(r): return T('custom_system', False, 'nlp_specific', 'bureau', 'high',
    "'employ learning to rank functionality based on user entered thumbs up/thumbs down'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='administrative', is_public_facing='0', scope_detail='SSA OCIO PolicyNet')

@R(35068)
def _(r): return T('custom_system', False, 'nlp_specific', 'bureau', 'high',
    "'Generate transcript from recorded audio of disability hearings'.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='SSA OCIO')

@R(35069)
def _(r): return T('custom_system', False, 'nlp_specific', 'bureau', 'high',
    "'Survey analysis tool that evaluates sentiment and categorization'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='administrative', is_public_facing='0', scope_detail='SSA OT')

@R(35070)
def _(r): return T('custom_system', True, 'general_llm', 'bureau', 'high',
    "'Generate high fidelity synthetic benefits and earnings data for external researches'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='research', is_public_facing='1', scope_detail='SSA ORDP')

@R(35071)
def _(r): return T('product_deployment', True, 'general_llm', 'office', 'medium',
    "'therapy chatbot that employees can access on their own personal devices'.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='SSA OHR')

@R(35072)
def _(r): return T('bespoke_application', True, 'general_llm', 'enterprise_wide', 'high',
    "'Agency Support Companion (ASC) chatbot... Generative AI model to create content'.",
    is_general_llm_access='1', is_cots_commercial='0', architecture_type='rag_pipeline',
    has_model_training='0', use_type='administrative', is_public_facing='0',
    scope_detail='SSA agency-wide ASC')

@R(35073)
def _(r): return T('bespoke_application', True, 'coding_assistant', 'bureau', 'high',
    "'cluster analysis, pattern matching, templates, and programming language models to generate modernized code'.",
    is_coding_tool='1', is_cots_commercial='0', architecture_type='inference_only',
    has_model_training='0', use_type='it_operations', is_public_facing='0',
    scope_detail='SSA OCIO modernization')

@R(35074)
def _(r): return T('product_feature', False, 'classical_ml', 'bureau', 'medium',
    "'Vendor built in AI engine for data cataloging' inside DGP product.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='it_operations', is_public_facing='0', scope_detail='SSA OCIO DGP')


# ---------- STATE ----------
@R(35075)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'medium',
    "'proof-of-concept machine learning model to scan unstructured... procurement data'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='administrative', is_public_facing='0', scope_detail='STATE A/GO')

@R(35076)
def _(r): return T('bespoke_application', False, 'predictive_analytics', 'office', 'low',
    "'Piloted the use of ILMS transactional data and planned transactions' — cancelled.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='STATE A/GO ILMS')

@R(35077)
def _(r): return T('custom_system', False, 'predictive_analytics', 'office', 'medium',
    "'machine learning model for detecting patterns of potential anomalous' procurement activity.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='mission_critical', is_public_facing='0', scope_detail='STATE A/GO ILMS')

@R(35078)
def _(r): return T('generic_use_pattern', False, 'nlp_specific', 'office', 'medium',
    "'Leveraging machine-based tools to streamline workflows in translation work'.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='STATE A/PRI/LS')

@R(35079)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'medium',
    "'machine learning algorithm to generate index metadata for the documents... FOIA Library'.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='1', scope_detail='STATE A/PRI/TI FOIA')

@R(35080)
def _(r): return T('bespoke_application', True, 'general_llm', 'office', 'medium',
    "'BudgetChat... consolidate budget documents to make searching and summarizing them easier'.",
    is_cots_commercial='0', architecture_type='rag_pipeline', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='STATE BP/RPBI')

@R(35081)
def _(r): return T('generic_use_pattern', True, 'general_llm', 'office', 'medium',
    "'rewriting Public Facing content on International Travel Safety & Security'.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='1', scope_detail='STATE CA/CST')

@R(35082)
def _(r): return T('bespoke_application', True, 'general_llm', 'bureau', 'medium',
    "'Predictive Analytics platform facilitates AI R&D and AI modeling, LLMs with services like Azure AI'.",
    is_cots_commercial='1', tool_vendor='Microsoft', architecture_type='unknown',
    has_model_training='0', use_type='it_operations', is_public_facing='0',
    scope_detail='STATE CA/CST platform')

@R(35083)
def _(r): return T('product_deployment', False, 'computer_vision', 'bureau', 'high',
    "'automatically check passport photo quality during the Online Passport Renewal' — FaceVACS.",
    is_cots_commercial='1', tool_product_name='FaceVACS', tool_vendor='Cognitec',
    architecture_type='inference_only', has_model_training='0', use_type='mission_critical',
    is_public_facing='1', scope_detail='STATE CA Consular Affairs')

@R(35084)
def _(r): return T('bespoke_application', False, 'predictive_analytics', 'bureau', 'low',
    "'measure and understand causal impacts of consular service changes' — planning.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='research', is_public_facing='0', scope_detail='STATE CA/CST')

@R(35085)
def _(r): return T('bespoke_application', True, 'general_llm', 'bureau', 'medium',
    "'leverage Natural Language Processing (NLP) and secure Large Language Models (LLM) on unstructured text'.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='STATE CA/CST')

@R(35086)
def _(r): return T('generic_use_pattern', True, 'general_llm', 'bureau', 'medium',
    "'leverage AI translation models to increase CA's capacity to provide consular content'.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='mission_critical', is_public_facing='1', scope_detail='STATE CA/CST')

@R(35087)
def _(r): return T('bespoke_application', False, 'nlp_specific', 'bureau', 'medium',
    "'chatbot and enhanced search on the TSG website processing existing FAQs'.",
    is_cots_commercial='0', architecture_type='rag_pipeline', has_model_training='0',
    use_type='mission_critical', is_public_facing='1', scope_detail='STATE CA/CST TSG')

@R(35088)
def _(r): return T('bespoke_application', True, 'coding_assistant', 'bureau', 'high',
    "'CodeGen... seamless integration with Large Language Models (LLMs) that aims to enhance... developers'.",
    is_coding_tool='1', is_cots_commercial='0', architecture_type='inference_only',
    has_model_training='0', use_type='it_operations', is_public_facing='0',
    scope_detail='STATE CA/CST CodeGen')

@R(35089)
def _(r): return T('custom_system', False, 'predictive_analytics', 'bureau', 'high',
    "'machine learning model... to forecast mass civilian killings' globally.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='STATE CSO')

@R(35090)
def _(r): return T('custom_system', False, 'computer_vision', 'bureau', 'high',
    "'AI and machine learning on moderate and high-resolution commercial satellite imagery'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='STATE CSO')

@R(35091)
def _(r): return T('custom_system', False, 'computer_vision', 'bureau', 'high',
    "'Daily scans of moderate resolution commercial satellite imagery to identify anomalies using the near-infrared band'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='STATE CSO')

@R(35092)
def _(r): return T('custom_system', False, 'predictive_analytics', 'bureau', 'medium',
    "'stakeholder/influence-driven model that identifies where key decision makers fall' — Senturion.",
    is_cots_commercial='1', tool_product_name='Senturion', tool_vendor='Sentia',
    architecture_type='inference_only', has_model_training='0', use_type='mission_critical',
    is_public_facing='0', scope_detail='STATE CSO')

@R(35093)
def _(r): return T('custom_system', False, 'predictive_analytics', 'bureau', 'high',
    "'machine learning forecasting model... to predict mass mobilizations (protests and riots)'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='STATE CSO')

@R(35094)
def _(r): return T('product_deployment', False, 'predictive_analytics', 'office', 'low',
    "'Apptio to bill bureaus for consolidated services' — financial planning COTS, minimal AI.",
    is_cots_commercial='1', tool_product_name='Apptio', tool_vendor='Apptio',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='STATE DT WCF')

@R(35095)
def _(r): return T('bespoke_application', False, 'nlp_specific', 'office', 'low',
    "'parse unstructured text from key DT documents to build structured data' — planned.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='it_operations', is_public_facing='0', scope_detail='STATE DT DAA')

@R(35096)
def _(r): return T('product_deployment', False, 'nlp_specific', 'office', 'high',
    "'ServiceNow's Virtual Agent into existing applications' — chatbot COTS.",
    is_cots_commercial='1', tool_product_name='ServiceNow Virtual Agent', tool_vendor='ServiceNow',
    architecture_type='inference_only', has_model_training='0', use_type='it_operations',
    is_public_facing='0', scope_detail='STATE DT/BMP')

@R(35097)
def _(r): return T('bespoke_application', False, 'classical_ml', 'office', 'low',
    "'orchestration of automatically opening and closing of Plan of Action and Milestones'.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='cybersecurity', is_public_facing='0', scope_detail='STATE DT/DCIO POA&M')

@R(35098)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'Natural Language Processing (NLP) application for F/RA to streamline the extraction of earmarks'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='STATE F')

@R(35099)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'custom Natural Language Processing (NLP) model to recommend information for tagging'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='administrative', is_public_facing='1', scope_detail='STATE F ForeignAssistance.gov')

@R(35100)
def _(r): return T('bespoke_application', True, 'general_llm', 'office', 'low',
    "'dynamic integration between multiple AI tools to create stored/persistent personas'.",
    is_cots_commercial='1', architecture_type='agentic_workflow', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='STATE FSI EdTech')

@R(35101)
def _(r): return T('bespoke_application', False, 'classical_ml', 'office', 'low',
    "'pilot program to better accommodate the need for experiential learning through gaming and simulations'.",
    is_cots_commercial='1', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='STATE FSI')

@R(35102)
def _(r): return T('generic_use_pattern', True, 'general_llm', 'office', 'low',
    "'sustain our AI action plan... to promote content generation, analytical tasks'.",
    is_cots_commercial='1', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='STATE FSI')

@R(35103)
def _(r): return T('product_feature', False, 'predictive_analytics', 'office', 'medium',
    "'AI on the Cornerstone Learning Management System to enhance employee learning'.",
    is_cots_commercial='1', tool_product_name='Cornerstone LMS', tool_vendor='Cornerstone',
    architecture_type='inference_only', has_model_training='0', use_type='administrative',
    is_public_facing='0', scope_detail='STATE FSI/EX/EDS')

@R(35104)
def _(r): return T('bespoke_application', True, 'general_llm', 'office', 'high',
    "'DCT is an AI-driven research assistant... AI-generated summaries and translations'.",
    is_cots_commercial='0', architecture_type='rag_pipeline', has_model_training='0',
    use_type='mission_critical', is_public_facing='0', scope_detail='STATE J')

@R(35105)
def _(r): return T('bespoke_application', True, 'general_llm', 'office', 'high',
    "'TIP Report Translation AI system provides informal, unofficial translations'.",
    is_cots_commercial='0', architecture_type='inference_only', has_model_training='0',
    use_type='mission_critical', is_public_facing='0', scope_detail='STATE J/TIP')

@R(35106)
def _(r): return T('bespoke_application', False, 'nlp_specific', 'office', 'medium',
    "'FOIA process better by spotting similar requests and documents to cut down on duplication'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='STATE M/SS/CFA FOIA')

@R(35107)
def _(r): return T('bespoke_application', True, 'general_llm', 'enterprise_wide', 'high',
    "'StateChat is the Department's enterprise Generative AI-powered chatbot'.",
    is_general_llm_access='1', is_cots_commercial='0', architecture_type='inference_only',
    has_model_training='0', use_type='administrative', is_public_facing='0',
    scope_detail='STATE enterprise StateChat')

@R(35108)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'optical character recognition and Natural Language Processing (NLP) on Department cables'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='administrative', is_public_facing='0', scope_detail='STATE M/SS/CFA')

@R(35109)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'NLP to pull key information from unstructured text... country names and agreement dates'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='administrative', is_public_facing='0', scope_detail='STATE PM')

@R(35110)
def _(r): return T('generic_use_pattern', True, 'general_llm', 'office', 'medium',
    "'use approved Large Language Models to create artifacts for leadership' in ECA.",
    is_general_llm_access='1', is_cots_commercial='1', architecture_type='inference_only',
    has_model_training='0', use_type='administrative', is_public_facing='0',
    scope_detail='STATE R/ECA/EX/IT')

@R(35111)
def _(r): return T('product_deployment', False, 'computer_vision', 'office', 'high',
    "'Storyzy... Improve detected use of synthetic content' — disinfo detection COTS.",
    is_cots_commercial='1', tool_product_name='Storyzy', tool_vendor='Storyzy',
    architecture_type='inference_only', has_model_training='0', use_type='mission_critical',
    is_public_facing='0', scope_detail='STATE R/GEC')

@R(35112)
def _(r): return T('custom_system', False, 'computer_vision', 'office', 'high',
    "'Extracted text from images using standard python libraries' — retired OCR.",
    is_cots_commercial='0', architecture_type='inference_only', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='STATE R/GEC')

@R(35113)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'Cluster text into themes based on frequency of used words' — topic modeling.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='research', is_public_facing='0', scope_detail='STATE R/GEC')

@R(35114)
def _(r): return T('custom_system', False, 'predictive_analytics', 'office', 'high',
    "'statistical models, projecting expected outcomes into the future' applied to COVID/violence.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='research', is_public_facing='0', scope_detail='STATE R/GEC')

@R(35115)
def _(r): return T('custom_system', False, 'computer_vision', 'office', 'high',
    "'Deep learning model that took in an image containing a person's face' for deepfake detection.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='mission_critical', is_public_facing='0', scope_detail='STATE R/GEC')

@R(35116)
def _(r): return T('bespoke_application', False, 'nlp_specific', 'office', 'high',
    "'sentiment model was trained by fine-tuning a multilingual, BERT model' — SentiBERTIQ.",
    is_cots_commercial='0', architecture_type='fine_tuned', has_model_training='1',
    use_type='research', is_public_facing='0', scope_detail='STATE R/GEC')

@R(35117)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'using Latent Dirichlet Allocation (LDA), to extract topics' — TOPIQ.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='research', is_public_facing='0', scope_detail='STATE R/GEC')

@R(35118)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'Identified different texts that were identical or nearly identical by calculating cosine similarity'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='0',
    use_type='research', is_public_facing='0', scope_detail='STATE R/GEC')

@R(35119)
def _(r): return T('custom_system', False, 'computer_vision', 'office', 'high',
    "'pretrained deep learning model to generate image embeddings, then... hierarchical clustering'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='0',
    use_type='research', is_public_facing='0', scope_detail='STATE R/GEC')

@R(35120)
def _(r): return T('custom_system', False, 'classical_ml', 'office', 'high',
    "'Took in a social network and clusters nodes together into communities'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='0',
    use_type='research', is_public_facing='0', scope_detail='STATE R/GEC')

@R(35121)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'medium',
    "'Fast Text was an AI approach to identifying similar terms and phrases'.",
    is_cots_commercial='0', architecture_type='custom_trained', has_model_training='1',
    use_type='research', is_public_facing='0', scope_detail='STATE R/GEC')

@R(35122)
def _(r): return T('custom_system', False, 'nlp_specific', 'office', 'high',
    "'open-source neural machine translation models to translate global media articles'.",
    is_cots_commercial='0', architecture_type='inference_only', has_model_training='0',
    use_type='research', is_public_facing='0', scope_detail='STATE R/GPA/RA DMAP')

@R(35123)
def _(r): return T('custom_system', False, 'predictive_analytics', 'office', 'low',
    "'Used PowerBI to create an interactive map' — minimal AI, retired.",
    is_cots_commercial='1', tool_product_name='Power BI', tool_vendor='Microsoft',
    architecture_type='unknown', has_model_training='0', use_type='research',
    is_public_facing='0', scope_detail='STATE R/GPA/RA')

@R(35124)
def _(r): return T('product_deployment', True, 'general_llm', 'office', 'high',
    "'leverage ChatGPT Licenses to streamline existing Public Diplomacy workflows'.",
    is_general_llm_access='1', is_cots_commercial='1', tool_product_name='ChatGPT',
    tool_vendor='OpenAI', is_openai='1', architecture_type='inference_only',
    has_model_training='0', use_type='administrative', is_public_facing='0',
    scope_detail='STATE R/GPA/RA')

@R(35125)
def _(r): return T('bespoke_application', False, 'nlp_specific', 'office', 'low',
    "'LEO - Budget Office Inquiries... Answer questions frequently asked about budget'.",
    is_cots_commercial='0', architecture_type='unknown', has_model_training='0',
    use_type='administrative', is_public_facing='0', scope_detail='STATE WHA/EX')


def main():
    if not os.path.exists(IN):
        print(f'missing input: {IN}', file=sys.stderr); sys.exit(1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(IN, newline='') as f:
        rows = list(csv.DictReader(f))
    out_rows = []
    missing = []
    for r in rows:
        rid = int(r['id'])
        if rid not in ROW_TAGS:
            missing.append((rid, r['agency_abbreviation'], r['use_case_name']))
        d = tag_row(r)
        # Ensure FIELDS columns exist
        for k in FIELDS:
            d.setdefault(k, '')
        out_rows.append({k: d.get(k, '') for k in FIELDS})
    if missing:
        print(f'MISSING TAGS for {len(missing)} rows:', file=sys.stderr)
        for m in missing[:50]:
            print('  ', m, file=sys.stderr)
        sys.exit(2)
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for row in out_rows:
            w.writerow(row)
    # Stats
    from collections import Counter
    print(f'rows written: {len(out_rows)}')
    print('is_generative_ai:', Counter(r['is_generative_ai'] for r in out_rows))
    print('deployment_scope top 3:', Counter(r['deployment_scope'] for r in out_rows).most_common(3))
    print('tool_vendor top 3:', Counter(r['tool_vendor'] for r in out_rows if r['tool_vendor']).most_common(3))

if __name__ == '__main__':
    main()
