# Prompt Filtering & Input Defense

## Overview

The first line of defense for any LLM application is what you let *into* the model.
This topic covers the prompt-injection threat model (direct, indirect/RAG-borne, jailbreaks,
encoding attacks, multi-turn crescendo), the input-validation and detection techniques a runtime
security engineer ships, and how to assemble them into a layered `InputFilter` pipeline that
returns an `ALLOW / FLAG / BLOCK` decision. Code-first and interview-ready.

## Learning Objectives

- Map real attacks to **OWASP LLM01: Prompt Injection** and reason about a concrete threat model
- Apply input **validation & sanitization**: delimiters, structured prompting, spotlighting, canary tokens
- Build layered **detection**: denylist signatures, classifier stubs, perplexity/anomaly signals, LLM-as-judge
- Understand why input filtering **alone is insufficient**, and tune false-positive vs false-negative trade-offs
- Ship a production input-filtering pipeline with a scored risk decision

## Contents

- **[concepts.md](concepts.md)** - Theory and concepts
- **[exercise_01.md](exercise_01.md)** - Practice problem
- **[exercise.py](exercise.py)** - Starter script
- **[solution.py](solution.py)** - Reference solution
- **[quiz.md](quiz.md)** - Knowledge check
- **[references.md](references.md)** - Further reading

## Estimated Time: ~45 min
