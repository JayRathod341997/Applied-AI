# References — Misuse Protection & Abuse Prevention

## Standards & threat models
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) - Canonical LLM risk list; see LLM04 (Model DoS) and LLM10 (Unbounded Consumption / Model Theft).
- [OWASP LLM10: Unbounded Consumption](https://genai.owasp.org/llmrisk/llm102025-unbounded-consumption/) - Cost/DoS abuse and model-extraction risk, with mitigations.
- [MITRE ATLAS](https://atlas.mitre.org/) - Adversarial Threat Landscape for AI Systems — the "ATT&CK for ML" TTP matrix.
- [NIST AI Risk Management Framework (AI RMF 1.0)](https://www.nist.gov/itl/ai-risk-management-framework) - Govern/Map/Measure/Manage framework for AI risk, including misuse.
- [NIST AI 600-1 — Generative AI Profile](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) - GenAI-specific risks and controls companion to the AI RMF.

## Red-teaming & abuse testing
- [HarmBench](https://www.harmbench.org/) - Standardized evaluation framework and corpora for automated red-teaming / refusal robustness.
- [Microsoft PyRIT](https://github.com/Azure/PyRIT) - Python Risk Identification Toolkit for automated LLM red-teaming.
- [Garak — LLM vulnerability scanner](https://github.com/NVIDIA/garak) - Probes an LLM for jailbreaks, prompt injection, data leakage, and more.
- [OWASP GenAI Red Teaming Guide](https://genai.owasp.org/resource/genai-red-teaming-guide/) - Practical guidance for adversarial testing of GenAI apps.

## Rate limiting & resilience patterns
- [Token bucket algorithm (Wikipedia)](https://en.wikipedia.org/wiki/Token_bucket) - The rate-limiting algorithm implemented in the exercise.
- [Stripe — Scaling your API with rate limiters](https://stripe.com/blog/rate-limiters) - Production token-bucket + concurrency limiter design from a payments API.
- [Cloudflare — How we built rate limiting](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/) - Sliding-window rate limiting at internet scale.
- [Circuit Breaker pattern (Microsoft)](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker) - Trip/half-open/close pattern for shedding load.

## Guardrails & abuse-detection tooling
- [NVIDIA NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) - Programmable runtime guardrails for LLM apps.
- [Guardrails AI](https://github.com/guardrails-ai/guardrails) - Validators and structure/policy enforcement for LLM I/O.
- [Rebuff](https://github.com/protectai/rebuff) - Prompt-injection detector with canary tokens (honeypot pattern).
- [Lakera Guard](https://www.lakera.ai/) - Commercial prompt-injection / abuse detection API.
- [Microsoft Presidio](https://github.com/microsoft/presidio) - PII detection/redaction to limit data exfiltration.

## Identity, entitlements & IR
- [OAuth 2.0 scopes](https://oauth.net/2/scope/) - Scoped-token model for per-use-case entitlements.
- [Saviynt Identity Governance](https://saviynt.com/) - Enterprise IGA: entitlement provisioning, approval workflows, access recertification.
- [ServiceNow Access Request / IGA](https://www.servicenow.com/products/governance-risk-compliance.html) - Request → approval → provisioning workflow for entitlements.
- [NIST SP 800-61r2 — Computer Security Incident Handling Guide](https://csrc.nist.gov/pubs/sp/800/61/r2/final) - The detect → contain → eradicate → recover → learn IR lifecycle.

## Papers
- ["Stealing Part of a Production Language Model" (Carlini et al., 2024)](https://arxiv.org/abs/2403.06634) - Practical model-extraction attack; motivates query-pattern limits.
- ["Extracting Training Data from Large Language Models" (Carlini et al., 2021)](https://arxiv.org/abs/2012.07805) - Data-exfiltration risk from LLMs.
