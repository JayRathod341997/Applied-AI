# Audit, Traceability & Control Mechanisms

## Overview

How to turn AI behavior into **defensible evidence** and keep **control** of a live
system. Covers what to log for every AI interaction, correlation-id tracing across
a multi-step agent, prompt/data/model lineage, tamper-evident hash-chained logs,
PII-safe logging, and control mechanisms (kill switch, feature flags, human-in-the-loop
approvals). Maps directly to the JD line: *"Build audit, traceability, and control
mechanisms."*

## Learning Objectives

- Explain why audit trails are non-negotiable (EU AI Act logging, GDPR Art. 22, SR 11-7, forensics, reproducibility).
- Enumerate the full evidence set to log per AI interaction (identity, pinned model/prompt versions, sources, decisions, cost, trace ids).
- Trace a multi-step agent with correlation/span ids and connect prompt, data, and model lineage.
- Build a tamper-evident, append-only, **hash-chained** audit log and verify its integrity.
- Redact PII before logging while preserving proof-of-content (hashing) and privacy (encrypt-separate).
- Apply control mechanisms: kill switch, guardrail feature flags, and immutable human-in-the-loop decision records.

## Contents

- **[concepts.md](concepts.md)** - Theory and concepts
- **[exercise_01.md](exercise_01.md)** - Practice problem
- **[exercise.py](exercise.py)** - Starter script
- **[solution.py](solution.py)** - Reference solution
- **[quiz.md](quiz.md)** - Knowledge check
- **[references.md](references.md)** - Further reading

## Estimated Time: ~35 min
