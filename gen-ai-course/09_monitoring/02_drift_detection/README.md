# Drift Detection

This subtopic covers how to detect that a GenAI system is quietly rotting because the world around it changed. You will learn the kinds of drift (data, concept, target, embedding, prompt, model), the temporal shapes concept drift takes (sudden, gradual, recurring, blip), the statistical tests that detect it — PSI, KS, chi-square, KL divergence, and centroid cosine distance — with a fully worked PSI example, how embedding drift gives RAG an early warning, and how to turn a drift score into a retraining trigger without overreacting to blips.

## Topics

- Types of drift: data/feature, concept, target/label, embedding, prompt, and model drift
- The universal detection recipe: baseline window → compare current window → flag past threshold
- Statistical methods: PSI (with worked example), KS test, chi-square, KL divergence
- Embedding drift via centroid cosine distance — the early warning for RAG retrieval quality
- From detection to action: retraining triggers, scheduled refresh, canaries, fallbacks; online vs offline

## Files in this subtopic

- `concepts.md` — the teaching content: ASCII diagrams, comparison tables, and focused code snippets for every topic above.
- `quiz.md` — 10 multiple-choice questions with answers and explanations.
- `exercise_01.md` — the brief for the hands-on coding exercise (a PSI drift detector).
- `exercise.py` — a runnable starter scaffold with sample windows; you fill in the `# TODO` sections.
- `solution.py` — the complete, offline, self-verifying reference implementation (stdlib `math` only).
- `interview.md` — interview questions and model answers on drift detection.
- `references.md` — curated links to authoritative docs and articles.

## Start

Begin with `concepts.md`, then test yourself with `quiz.md`, and finally build the PSI detector in `exercise.py` (checking against `solution.py`).
