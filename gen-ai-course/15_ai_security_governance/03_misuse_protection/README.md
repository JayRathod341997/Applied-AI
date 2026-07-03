# Misuse Protection & Abuse Prevention

## Overview

Prompt filtering stops bad *content*; misuse protection stops bad *usage patterns* — the same API abused at the wrong
scale, speed, cost, or frequency, by the wrong actor. This topic is the cross-request, cross-user runtime-security layer:
rate limiting, cost budgets, abuse detection, entitlements, adversarial CI gates, and AI-specific incident response. You
finish by building a `MisuseGuard` that fuses a token-bucket rate limiter, a cost-budget enforcer, and an abuse-score
tracker into a single ALLOW / THROTTLE / BLOCK / SUSPEND decision.

## Learning Objectives

- Model the threat landscape of AI misuse (harmful-content generation, mass automation/scraping, cost/DoS, model theft LLM10, data exfiltration, account takeover, insider misuse).
- Implement multi-dimensional rate limiting with a token bucket; contrast it with sliding/fixed windows; add spend caps and circuit breakers.
- Detect low-and-slow abuse via velocity checks, anomaly detection, reputation, canary/honeypot prompts, and behavioral fingerprinting.
- Enforce scoped tokens and per-use-case entitlements, and connect them to IAM/IGA approval workflows (Saviynt/ServiceNow).
- Gate releases on jailbreak pass-rate with adversarial CI (MITRE ATLAS, HarmBench) and run the AI-misuse incident-response loop while tracking MTTPU.

## Contents

- **[concepts.md](concepts.md)** - Theory and concepts
- **[exercise_01.md](exercise_01.md)** - Practice problem
- **[exercise.py](exercise.py)** - Starter script
- **[solution.py](solution.py)** - Reference solution
- **[quiz.md](quiz.md)** - Knowledge check
- **[references.md](references.md)** - Further reading

## Estimated Time: ~40 min
