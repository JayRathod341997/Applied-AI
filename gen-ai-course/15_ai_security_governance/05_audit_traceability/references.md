# References — Audit, Traceability & Control Mechanisms

## Regulations & frameworks
- [EU AI Act — Article 12 (Record-keeping / logging)](https://artificialintelligenceact.eu/article/12/) - Automatic event logging & traceability obligations for high-risk AI.
- [GDPR — Article 22 (Automated individual decision-making)](https://gdpr-info.eu/art-22-gdpr/) - Rights around solely automated decisions; drives explainability/audit.
- [SR 11-7 — Supervisory Guidance on Model Risk Management (US Federal Reserve)](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm) - Model inventory, validation, monitoring; source of model lineage practice.
- [NIST AI Risk Management Framework (AI RMF 1.0)](https://www.nist.gov/itl/ai-risk-management-framework) - MEASURE/MANAGE functions require documented, traceable, monitored AI.
- [ISO/IEC 42001 — AI Management System](https://www.iso.org/standard/81230.html) - Management-system controls and auditable records for AI.
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) - Includes sensitive-information-disclosure and monitoring gaps relevant to audit.

## Tracing, observability & lineage
- [OpenTelemetry — Semantic Conventions for GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/) - Standard span attribute names for LLM requests, tokens, prompts.
- [OpenTelemetry Traces (spec)](https://opentelemetry.io/docs/concepts/signals/traces/) - Trace/span/context-propagation model behind correlation ids.
- [Langfuse — LLM observability & tracing](https://langfuse.com/docs) - Open-source tracing/eval for LLM apps (spans, sessions, cost).
- [Arize Phoenix — LLM tracing & evaluation](https://docs.arize.com/phoenix) - OpenTelemetry-based tracing for LLM/agent applications.
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html) - Model versioning/registry for model lineage.
- [Google — Model Cards](https://modelcards.withgoogle.com/about) - Documenting model provenance, intended use, and limitations.

## PII redaction & privacy
- [Microsoft Presidio](https://microsoft.github.io/presidio/) - Open-source PII detection & redaction (analyzer + anonymizer).
- [Python `hashlib` docs](https://docs.python.org/3/library/hashlib.html) - SHA-256 used for hash-chaining and proof-of-content.

## Tamper-evidence & immutable storage
- [AWS S3 Object Lock (WORM)](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html) - Write-once-read-many retention (governance/compliance modes).
- [Azure immutable blob storage (WORM)](https://learn.microsoft.com/en-us/azure/storage/blobs/immutable-storage-overview) - Time-based/legal-hold immutability for logs.
- [RFC 3161 — Time-Stamp Protocol (TSP)](https://www.rfc-editor.org/rfc/rfc3161) - Trusted timestamps for anchoring log integrity.
- [Amazon QLDB — cryptographically verifiable ledger](https://docs.aws.amazon.com/qldb/latest/developerguide/what-is.html) - Journal-first, hash-chained, verifiable transaction log (concept reference).

## Guardrails & controls (adjacent)
- [NVIDIA NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) - Programmable guardrails whose verdicts you should log.
- [Guardrails AI](https://www.guardrailsai.com/docs) - Output validation whose decisions belong in the audit trail.
- [OpenFeature — feature-flag standard](https://openfeature.dev/) - Vendor-neutral feature flags for kill switches / guardrail toggles.
- [MITRE ATLAS](https://atlas.mitre.org/) - Adversary tactics against AI systems; informs what forensic detail to capture.
