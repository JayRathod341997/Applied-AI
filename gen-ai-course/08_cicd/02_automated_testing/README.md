# Automated Testing for LLM Apps

This subtopic covers how to test applications whose outputs are *probabilistic* rather than deterministic. You will learn the testing pyramid for LLM apps (unit → integration → prompt regression → manual eval), how to build a golden/reference set, how to score outputs with keyword, semantic, and LLM-as-judge methods, how a regression gate turns those scores into a pass/fail "build" decision, and how all of this wires into a CI pipeline (GitHub Actions / Azure DevOps). The goal is a suite that fails the build *before* a quality regression reaches users.

## Topics

- Why LLM testing differs from traditional testing (probabilistic outputs)
- The LLM testing pyramid: unit, integration, prompt regression, manual eval
- Golden / reference sets: curated input → expected-content pairs
- Scoring methods: exact/keyword, semantic similarity, LLM-as-judge
- Regression gates and CI pipelines (GitHub Actions / Azure DevOps)

## Files in this subtopic

- `concepts.md` — the teaching content: ASCII diagrams, comparison tables, and focused code snippets for every topic above.
- `quiz.md` — multiple-choice questions with answers and explanations to check your understanding.
- `exercise_01.md` — the brief for the hands-on coding exercise (a prompt regression test runner).
- `exercise.py` — a runnable starter scaffold with a mock prompt function; you fill in the `# TODO` sections.
- `solution.py` — the complete, offline, fully-tested reference implementation of the runner.
- `interview.md` — interview questions and model answers on testing LLM applications.
- `references.md` — curated links to authoritative docs and articles for deeper study.

## Start

Begin with `concepts.md`, then test yourself with `quiz.md`, and finally build the runner in `exercise.py` (checking against `solution.py`).
