# References — Policy-as-Code & Rule Engines for AI Governance

## Policy engines & languages
- [Open Policy Agent (OPA)](https://www.openpolicyagent.org/docs/latest/) — CNCF graduated general-purpose policy engine; PEP/PDP model, bundles, sidecar deployment.
- [Rego Policy Language](https://www.openpolicyagent.org/docs/latest/policy-language/) — the declarative query language used by OPA.
- [OPA Policy Testing (`opa test`)](https://www.openpolicyagent.org/docs/latest/policy-testing/) — unit-testing policies with `test_*` rules.
- [AWS Cedar](https://www.cedarpolicy.com/) — analyzable, verifiable authorization policy language (also used by Amazon Verified Permissions).
- [JSON Logic](https://jsonlogic.com/) — portable rules as JSON that run identically in Python and JavaScript.
- [OASIS XACML 3.0](http://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html) — the standard that formalized PEP/PDP/PIP and combining algorithms (deny-overrides, etc.).
- [DMN (Decision Model and Notation)](https://www.omg.org/dmn/) — OMG standard for business decision tables, often authored by non-engineers.

## Regulation & risk frameworks
- [NIST AI Risk Management Framework (AI RMF 1.0)](https://www.nist.gov/itl/ai-risk-management-framework) — GOVERN / MAP / MEASURE / MANAGE functions.
- [NIST Generative AI Profile (NIST AI 600-1)](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) — GenAI-specific risk guidance.
- [EU AI Act (Regulation 2024/1689, official text)](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) — risk tiers, high-risk obligations, human oversight.
- [GDPR Article 22 — Automated individual decision-making](https://gdpr-info.eu/art-22-gdpr/) — right to human review of solely-automated decisions.
- [ISO/IEC 42001:2023 — AI management systems](https://www.iso.org/standard/81230.html) — documented, operating AI governance controls.

## AI security context
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — the runtime-security threat catalog governance rules enforce against.
- [MITRE ATLAS](https://atlas.mitre.org/) — adversarial threat landscape for AI systems.
- [Microsoft Presidio](https://microsoft.github.io/presidio/) — PII detection/anonymization; the kind of PIP signal that feeds `contains_pii`.
- [NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) — programmable guardrails; complements policy-as-code at the conversation layer.
- [Guardrails AI](https://www.guardrailsai.com/docs) — validation/guardrail framework for LLM I/O.

## Practical / tooling
- [Styra Academy — OPA/Rego courses](https://academy.styra.com/) — free hands-on Rego training from OPA's maintainers.
- [Conftest](https://www.conftest.dev/) — run OPA/Rego policies against config files (JSON/YAML) in CI.
- [The Rego Playground](https://play.openpolicyagent.org/) — try Rego policies against an `input` document in the browser.
- [OPA Gatekeeper](https://open-policy-agent.github.io/gatekeeper/website/docs/) — OPA as a Kubernetes admission controller (same engine, different PEP).
