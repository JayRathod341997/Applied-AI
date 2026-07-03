# Policy-as-Code & Rule Engines for AI Governance

## Overview

Governance that lives in a document is a suggestion; governance that lives in code, runs on every
request, and blocks the call is a control. This topic shows how to enforce AI governance through
code: declarative rulesets evaluated by a rule engine at a decision point (the PEP/PDP/PIP model),
Open Policy Agent (OPA) and Rego, when to reach for a real engine versus a homegrown one, the
policy lifecycle (author → test → review → deploy → audit), and how to map EU AI Act / NIST AI RMF
/ GDPR requirements to enforceable rules. You build a small Python policy engine that returns a
decision plus a matched-rule audit trace. Code-first and interview-ready.

## Learning Objectives

- Explain why policy-as-code beats policy-by-document: **versioned, testable, auditable, automatically enforced, single source of truth**
- Apply the **PEP / PDP / PIP** decomposition and separate policy from application code
- Read and write a small **OPA / Rego** policy and query it at runtime (input JSON → decision JSON)
- Choose between **OPA, Cedar, JSON Logic, decision tables, and a homegrown engine**, and pick a conflict-resolution algorithm (deny-overrides)
- Run the **policy lifecycle** with unit tests, PR review + approval (MRM / ServiceNow / Saviynt), and audit logging
- Map **EU AI Act / NIST AI RMF / GDPR Art.22** clauses to enforceable rules
- Build a **Python policy engine** returning a decision + matched-rule trace for audit

## Contents

- **[concepts.md](concepts.md)** - Theory and concepts
- **[exercise_01.md](exercise_01.md)** - Practice problem
- **[exercise.py](exercise.py)** - Starter script
- **[solution.py](solution.py)** - Reference solution
- **[quiz.md](quiz.md)** - Knowledge check
- **[references.md](references.md)** - Further reading

## Estimated Time: ~40 min
