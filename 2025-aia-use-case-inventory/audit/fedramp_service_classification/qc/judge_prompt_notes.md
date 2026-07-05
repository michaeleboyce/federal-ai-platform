# QC judge lane — operating notes

Judges run on the frontier model (main-loop tier). Sample: 100% core_ai,
100% low-confidence, 25% ai_featured, 10% not_ai (seeded, --export-qc).
Judges are prompted to REFUTE the label, not confirm it. Error-tag taxonomy
(extensible):
  marketing-name-confusion       - name sounds AI but the service is plumbing,
                                   or vice versa
  infra-with-ml-feature-overcall - infra/monitoring tagged ai_featured for a
                                   minor ML feature that isn't material
  security-analytics-undercall   - ML-detection security product missed as not_ai
  search-vs-ai-ambiguity         - search/indexing services on the semantic-ML line
  identity-biometrics-line       - identity verification vs ML biometrics boundary
  unknown-service-guess          - labeler invented capability for an obscure name
Correction triggers (computed by --apply-qc): labeler batch >10% overturned
(min 5 judged), or any tag >= 5 occurrences.
