# Service classification rubric v1

Unit: one FedRAMP "service in scope" name (with host-package context).
Output categories:

- core_ai — the named service IS an AI/ML capability: LLM or model hosting /
  inference (Amazon Bedrock, Azure OpenAI, SageMaker AI, Gemini/Vertex);
  chat assistants and copilots; agent builders; CV / NLP / speech /
  translation / transcription / document-intelligence APIs; ML training,
  tooling, feature stores; ML-based identity/biometric verification.
- ai_featured — a broader service that ships material AI/ML capability as an
  embedded feature (e.g. security analytics with ML detection, a low-code
  platform with an AI builder module, search with a semantic/ML core that is
  secondary to the product).
- not_ai — everything else: compute, storage, networking, identity, plain
  monitoring/logging, databases, collaboration. Marketing mentions of "AI"
  do not qualify.

Rules:
1. Judge what the named service actually is — use your knowledge of the
   AWS / Azure / GCP / vendor catalogs. The service NAME is primary
   evidence; the host snippet is context only (its boundary/asterisk
   language is noise).
2. When unsure, prefer not_ai with confidence=low. Precision over recall:
   core_ai rows become cited article claims.
3. reasoning: 1–2 sentences. signals: up to 4 short verbatim cues (name
   fragments or snippet phrases).
