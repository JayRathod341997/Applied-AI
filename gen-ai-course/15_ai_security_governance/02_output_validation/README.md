# Output Validation & Guardrails

## Overview

Input filtering stops bad prompts; it does nothing about what the model *says back*. This
topic covers the **outbound** control plane — validating, sanitizing, and gating every LLM
response before it reaches a user, database, browser, or downstream service. The governing
principle: *an LLM's output is untrusted input to the next system.* We cover structured-output
validation with repair loops, RAG groundedness checks, PII/secret scanning, and safe handling
of unsafe content (OWASP **LLM02** and **LLM05**), then build a production-style validation gateway.

## Learning Objectives

- Explain why outputs need validation independent of inputs, and the failure modes involved
  (hallucination, PII/secret leakage, insecure output handling, format/toxicity violations).
- Enforce structured outputs with JSON Schema / Pydantic and a bounded **retry/repair** loop;
  understand constrained decoding.
- Check RAG **groundedness** (citations, numeric/lexical overlap, NLI, "supported by context").
- Apply PII redaction / DLP, secret scanning, and toxicity/allowlist filtering on outputs.
- Handle insecure output safely — encode/sanitize per downstream sink (HTML/SQL/shell/URL).
- Assemble a fail-closed output-validation gateway and ship it against a production checklist.

## Contents

- **[concepts.md](concepts.md)** - Theory and concepts
- **[exercise_01.md](exercise_01.md)** - Practice problem
- **[exercise.py](exercise.py)** - Starter script
- **[solution.py](solution.py)** - Reference solution
- **[quiz.md](quiz.md)** - Knowledge check
- **[references.md](references.md)** - Further reading

## Estimated Time: ~45 min
