# References — Output Validation & Guardrails

## Standards & threat models
- [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/) — the canonical risk list; see **LLM02 Sensitive Information Disclosure** and **LLM05 Improper Output Handling**.
- [OWASP LLM05: Improper Output Handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/) — treating LLM output as untrusted input; XSS/SSRF/SQLi/RCE downstream.
- [OWASP LLM02: Sensitive Information Disclosure](https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/) — PII/secret/data leakage in responses.
- [NIST AI Risk Management Framework (AI RMF 1.0)](https://www.nist.gov/itl/ai-risk-management-framework) — MAP/MEASURE/MANAGE controls for trustworthy AI.
- [NIST Generative AI Profile (NIST-AI-600-1)](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) — GenAI-specific risk actions incl. output integrity.
- [MITRE ATLAS](https://atlas.mitre.org/) — adversarial ML tactics/techniques knowledge base.

## Structured output & constrained decoding
- [Guardrails AI](https://www.guardrailsai.com/docs) — validators, structured output, and automatic re-ask/repair loops.
- [Pydantic](https://docs.pydantic.dev/latest/) — schema/type validation and coercion for Python.
- [Instructor](https://python.useinstructor.com/) — structured LLM outputs into Pydantic models with retries.
- [Outlines](https://dottxt-ai.github.io/outlines/) — constrained/structured generation via grammars and JSON Schema.
- [JSON Schema](https://json-schema.org/) — the vocabulary for declaring output contracts.

## Guardrail frameworks
- [NVIDIA NeMo Guardrails](https://docs.nvidia.com/nemo/guardrails/) — programmable input/output/dialog rails (Colang).
- [Rebuff](https://github.com/protectai/rebuff) — prompt-injection detection (input side, complements output checks).
- [Lakera Guard](https://www.lakera.ai/) — hosted guardrails for injection, PII, and content safety.
- [Llama Guard (Meta)](https://ai.meta.com/research/publications/llama-guard-llm-based-input-output-safeguard-for-human-ai-conversations/) — LLM-based input/output safety classifier.

## PII / DLP / secret scanning
- [Microsoft Presidio](https://microsoft.github.io/presidio/) — PII detection (NER + regex + checksums) and anonymisation.
- [gitleaks](https://github.com/gitleaks/gitleaks) — secret-scanning rules/patterns you can reuse for output scanning.
- [Yelp detect-secrets](https://github.com/Yelp/detect-secrets) — entropy + regex secret detection.
- [Detoxify](https://github.com/unitaryai/detoxify) — toxicity classification models.
- [Perspective API](https://perspectiveapi.com/) — Google Jigsaw toxicity scoring.

## Groundedness / factuality
- [RAGAS](https://docs.ragas.io/) — faithfulness / groundedness metrics for RAG.
- [TruLens groundedness feedback](https://www.trulens.org/) — evaluate whether answers are supported by retrieved context.
- [Natural Language Inference (entailment) — overview](https://nlp.stanford.edu/projects/snli/) — the `context ⊨ answer` primitive behind NLI groundedness.

## Insecure output handling / downstream sinks
- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) — context-appropriate output encoding.
- [DOMPurify](https://github.com/cure53/DOMPurify) — allowlist HTML sanitizer for rendering model markup safely.
- [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html) — egress allowlisting for model-produced URLs/tool args.
