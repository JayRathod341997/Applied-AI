# Deployment Strategies

This subtopic covers how a tested artifact actually reaches production safely. You will learn how Docker packages an LLM app for portable, reproducible deploys (multi-stage builds, non-root, no baked-in secrets), how Infrastructure as Code (Terraform / Bicep) makes the surrounding cloud resources reproducible and auditable, how blue-green and canary strategies limit the blast radius of a bad release, how environments (dev/staging/prod) are managed with progressive strictness, and how automated rollback reverts a deployment the moment metrics breach a threshold. The goal is to ship changes quickly while keeping the cost of a mistake small and recoverable.

## Topics

- Containerization with Docker: multi-stage builds, model-weight handling, security
- Infrastructure as Code concepts (Terraform vs Bicep)
- Blue-green vs canary vs shadow deployment strategies
- Environment management: dev → staging → prod with progressive strictness
- Automated rollback: traffic shifting, error-rate triggers

## Files in this subtopic

- `concepts.md` — the teaching content: ASCII diagrams, comparison tables, and focused code snippets for every topic above.
- `quiz.md` — multiple-choice questions with answers and explanations to check your understanding.
- `exercise_01.md` — the brief for the hands-on coding exercise (a canary release controller).
- `exercise.py` — a runnable starter scaffold with a mock metrics source; you fill in the `# TODO` sections.
- `solution.py` — the complete, offline, fully-tested reference implementation of the controller.
- `interview.md` — interview questions and model answers on deployment strategies.
- `references.md` — curated links to authoritative docs and articles for deeper study.

## Start

Begin with `concepts.md`, then test yourself with `quiz.md`, and finally build the controller in `exercise.py` (checking against `solution.py`).
