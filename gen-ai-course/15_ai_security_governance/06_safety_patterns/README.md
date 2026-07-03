# Reusable Safety Patterns for AI Agents

## Overview

The capstone of Module 15. The previous five topics each built one runtime control
(input filtering, output validation, misuse protection, policy-as-code, audit). This
topic synthesizes them into **reusable safety patterns** so that *every* agent in an
org inherits the same protections by default. You will learn the centralized **AI
Security Gateway** pattern (one enforcement plane: input filter → policy → LLM →
output validation → audit), defense-in-depth with **fail-closed** behavior and human
fallback, a catalog of named patterns (guardrail middleware, dual-LLM, least
privilege, sandboxing, allowlists, circuit breaker/kill switch, canaries,
provenance), the AI risk scenarios and failure modes you must advise on, and how to
package it all as a shared SDK. Directly targets the JD lines *"Define safety
patterns used across all AI agents"* and *"Advise on AI risk scenarios and failure
modes."*

## Learning Objectives

- Design the centralized **AI Security Gateway** and justify centralize-vs-per-app
- Apply **defense in depth**, decide **fail-closed vs fail-open**, and degrade gracefully
- Recall and apply the **reusable patterns catalog** (dual-LLM, least privilege, sandboxing, allowlists, circuit breaker, canary, provenance)
- Advise on **AI failure modes** (injection→exfil, excessive agency, confused deputy, supply chain, cascading multi-agent, automation bias) with the right control for each
- Package patterns as a **shared internal SDK** with tests, adoption strategy, and a **maturity model**
- Build a reusable `@secure_agent` guardrail decorator that any agent inherits

## Contents

- **[concepts.md](concepts.md)** - Theory and concepts
- **[exercise_01.md](exercise_01.md)** - Practice problem
- **[exercise.py](exercise.py)** - Starter script
- **[solution.py](solution.py)** - Reference solution
- **[quiz.md](quiz.md)** - Knowledge check
- **[references.md](references.md)** - Further reading

## Estimated Time: ~35 min
