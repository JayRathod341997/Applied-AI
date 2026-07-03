# References: Reusable Safety Patterns for AI Agents

## Standards & frameworks

- [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/) - Canonical risk list: LLM01 Prompt Injection, LLM06 Excessive Agency, LLM08 Vector/Agent issues, LLM05 Supply Chain, LLM09 Overreliance, LLM10 Unbounded Consumption.
- [NIST AI Risk Management Framework (AI RMF 1.0)](https://www.nist.gov/itl/ai-risk-management-framework) - Govern/Map/Measure/Manage functions for AI risk; maps well onto the maturity model.
- [NIST Generative AI Profile (NIST AI 600-1)](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) - GenAI-specific risk controls extending the AI RMF.
- [MITRE ATLAS](https://atlas.mitre.org/) - Adversarial threat landscape and attack techniques for AI systems (the ATT&CK analogue for ML).
- [C2PA — Content Provenance and Authenticity](https://c2pa.org/) - Open standard for signing and verifying content provenance.

## Patterns & foundational writing

- [Simon Willison — The Dual LLM pattern for building AI assistants that can resist prompt injection](https://simonwillison.net/2023/Apr/25/dual-llm-pattern/) - Privileged vs. quarantined LLM design.
- [Simon Willison — Prompt injection: the series](https://simonwillison.net/series/prompt-injection/) - Ongoing analysis of why input filtering alone is insufficient.
- [Google DeepMind — CaMeL: Defeating Prompt Injections by Design (2025)](https://arxiv.org/abs/2503.18813) - Capabilities/control-flow approach to containing injection in tool-using agents.
- [Anthropic — Building effective agents](https://www.anthropic.com/research/building-effective-agents) - Agent design patterns including human-in-the-loop and tool scoping.
- [Google — Secure AI Framework (SAIF)](https://safety.google/cybersecurity-advancements/saif/) - Google's layered framework for securing AI systems.

## Guardrail tooling (compose these behind the gateway)

- [Microsoft Presidio](https://microsoft.github.io/presidio/) - PII detection and anonymization for input/output stages.
- [Guardrails AI](https://www.guardrailsai.com/docs) - Validators and structured-output guards for LLM I/O.
- [NVIDIA NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) - Programmable rails (Colang) around LLM apps.
- [Rebuff](https://github.com/protectai/rebuff) - Prompt-injection detection with canary tokens.
- [Lakera Guard](https://www.lakera.ai/) - Prompt-injection / content firewall as an API.
- [Llama Guard (Purple Llama)](https://github.com/meta-llama/PurpleLlama) - Open safety classifier for input/output moderation.

## Policy-as-code & sandboxing

- [Open Policy Agent (OPA) & Rego](https://www.openpolicyagent.org/docs/latest/) - Externalize allowlists/risk tiers as versioned policy (maturity L2).
- [gVisor](https://gvisor.dev/) - Application kernel sandbox for isolating tool/code execution.
- [Canarytokens](https://canarytokens.org/) - Free honeytoken generator for canary/honeypot patterns.

## Red-teaming & testing

- [Microsoft PyRIT](https://github.com/Azure/PyRIT) - Python Risk Identification Toolkit for automated AI red-teaming.
- [garak — LLM vulnerability scanner](https://github.com/NVIDIA/garak) - Probes for injection, leakage, jailbreaks; use as a CI regression corpus.
- [OWASP GenAI Red Teaming Guide](https://genai.owasp.org/resource/genai-red-teaming-guide/) - Methodology for adversarially testing GenAI apps (maturity L3).
