# Module 15: AI Security & Governance Engineering

> **Role focus:** *Senior AI Security & Governance Engineer* — embedding responsible-AI controls
> **directly into runtime systems** through code and automation, not policy documents.

This module teaches you to **build** the security and governance controls that protect enterprise AI
systems while enabling innovation: prompt filtering, output validation, misuse protection, policy-as-code
enforcement, audit/traceability, and reusable safety patterns for AI agents.

It is deliberately **engineering-first** (runnable Python in every topic) and pairs with
[Module 10: AI Governance](../10_governance/) — Module 10 covers the *policy and compliance* side;
Module 15 covers *how you enforce it in code at runtime*.

## Why this module exists

Enterprises are shipping LLMs and agents into production faster than they can secure them. The
[OWASP Top 10 for LLM Applications](https://genai.owasp.org/) shows the attack surface: prompt injection,
insecure output handling, sensitive data disclosure, excessive agency. A governance *policy* that lives in a
Confluence page stops none of these. A **runtime control plane** — filters, validators, policy engines, and
audit trails wired into the request path — does. This module builds that plane.

## Topics (4-hour mastery path)

| # | Topic | What you build | Time |
|---|-------|----------------|------|
| 1 | **[01_prompt_filtering/](01_prompt_filtering/)** | Input-defense pipeline: injection/jailbreak detection, sanitization, layered risk scoring | ~45 min |
| 2 | **[02_output_validation/](02_output_validation/)** | Output guardrail: schema/Pydantic validation, PII redaction, groundedness, insecure-output handling | ~45 min |
| 3 | **[03_misuse_protection/](03_misuse_protection/)** | Abuse prevention: rate limiting, cost budgets, abuse scoring, suspension | ~40 min |
| 4 | **[04_policy_as_code/](04_policy_as_code/)** | A rule engine that enforces governance policy (OPA/Rego + a Python PDP) | ~40 min |
| 5 | **[05_audit_traceability/](05_audit_traceability/)** | Tamper-evident, hash-chained audit logger with trace reconstruction | ~35 min |
| 6 | **[06_safety_patterns/](06_safety_patterns/)** | The centralized AI Security Gateway + reusable `@secure_agent` middleware | ~35 min |

Start with the **[LEARNING_PATH.md](LEARNING_PATH.md)** for the guided 4-hour sequence, and finish with the
**[interview.md](interview.md)** covering both fundamentals and a Senior Deep Dive.

## Learning Objectives

By the end of this module, you will be able to:

- **Design and implement** prompt filtering, output validation, and misuse protection as runtime controls.
- **Enforce AI governance through code** using policy-as-code and rule engines (OPA/Rego, PDP/PEP model).
- **Build audit, traceability, and control mechanisms** that survive a regulatory / model-risk audit.
- **Define reusable safety patterns** (a security gateway + guardrail middleware) applied across all AI agents.
- **Advise on AI risk scenarios and failure modes** — prompt injection, data leakage, excessive agency — and map each to a concrete control.

## How each topic is structured

Every topic folder contains:

- **concepts.md** — theory, threat models, code examples, and a production checklist
- **exercise_01.md** — a hands-on practice problem
- **exercise.py** — runnable starter scaffold with `TODO`s
- **solution.py** — full reference implementation (`python solution.py` prints a working demo)
- **quiz.md** — knowledge check with answers
- **references.md** — curated further reading

## Prerequisites

- Solid Python (functions, classes, dataclasses, regex).
- Basic LLM/GenAI literacy (prompts, RAG, agents) — see Modules 01–04.
- Familiarity with governance concepts helps — see [Module 10](../10_governance/).

## Maps to the role

| Job requirement | Covered in |
|-----------------|-----------|
| Prompt filtering | 01_prompt_filtering |
| Output validation | 02_output_validation |
| Misuse protection | 03_misuse_protection |
| Enforce AI governance through code & automation | 04_policy_as_code |
| Build audit, traceability, and control mechanisms | 05_audit_traceability |
| Define safety patterns across all AI agents | 06_safety_patterns |
| Advise on AI risk scenarios & failure modes | 06_safety_patterns + interview.md |
| Policy-as-code / rule engines | 04_policy_as_code |
| AI risks (hallucination, prompt injection, data leakage) | all topics + interview.md |
| Saviynt/ServiceNow/IAM/approval workflows | 03 & 04 (entitlements, change-approval) |
| Responsible AI / model-risk frameworks | interview.md (Senior Deep Dive) + [Module 10](../10_governance/) |
