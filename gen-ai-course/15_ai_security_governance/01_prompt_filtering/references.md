# References: Prompt Filtering & Input Defense

## Standards & Frameworks

- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) - The canonical LLM risk taxonomy; LLM01 is Prompt Injection.
- [OWASP LLM01: Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) - Deep dive on the specific risk, examples, and mitigations.
- [NIST AI Risk Management Framework (AI RMF 1.0)](https://www.nist.gov/itl/ai-risk-management-framework) - Govern/Map/Measure/Manage framework for trustworthy AI.
- [MITRE ATLAS](https://atlas.mitre.org/) - Adversarial threat landscape and attack techniques for AI systems (ATT&CK for ML).

## Attacks & Research

- ["Ignore Previous Prompt: Attack Techniques For Language Models" — Perez & Ribeiro (2022)](https://arxiv.org/abs/2211.09527) - Early, foundational prompt-injection paper.
- ["Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection" — Greshake et al. (2023)](https://arxiv.org/abs/2302.12173) - The indirect/RAG-borne injection paper.
- ["Universal and Transferable Adversarial Attacks on Aligned Language Models" — Zou et al. (2023)](https://arxiv.org/abs/2307.15043) - Adversarial suffixes (GCG); motivates perplexity/anomaly detection.
- [Microsoft: Spotlighting to defend against indirect prompt injection](https://www.microsoft.com/en-us/research/publication/defending-against-indirect-prompt-injection-attacks-with-spotlighting/) - Data-marking / delimiting techniques.
- [Simon Willison — Prompt injection series](https://simonwillison.net/series/prompt-injection/) - Accessible, continually updated explainer on why injection is unsolved.
- [Crescendo multi-turn jailbreak (Microsoft)](https://arxiv.org/abs/2404.01833) - Gradual multi-turn attack that no single message reveals.

## Tools & Libraries

- [Rebuff](https://github.com/protectai/rebuff) - Self-hardening prompt-injection detector (heuristics + model + canary).
- [Lakera Guard](https://www.lakera.ai/lakera-guard) - Commercial input/output guardrail API for injection, PII, and toxicity.
- [Meta Prompt Guard / Llama Guard](https://github.com/meta-llama/PurpleLlama) - Open classifiers for jailbreak/injection and content safety.
- [Microsoft Presidio](https://microsoft.github.io/presidio/) - Open-source PII detection and redaction.
- [Guardrails AI](https://www.guardrailsai.com/) - Validation framework for LLM inputs/outputs (validators, structured output).
- [NVIDIA NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) - Programmable rails (Colang) for dialogue, topic, and safety control.
- [LLM Guard](https://llm-guard.com/) - Open-source toolkit of input/output scanners (prompt injection, PII, toxicity, secrets).
- [Open Policy Agent (OPA) / Rego](https://www.openpolicyagent.org/) - Policy-as-code engine for authorizing downstream tool/actions (defense-in-depth).

## Practical Guides

- [OpenAI — Safety best practices](https://platform.openai.com/docs/guides/safety-best-practices) - Practical mitigations for production apps.
- [Anthropic — Mitigating jailbreaks and prompt injection](https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks) - Vendor guidance on layered defenses.
- [Gandalf by Lakera](https://gandalf.lakera.ai/) - Interactive game to build intuition for prompt-injection/leak attacks.
