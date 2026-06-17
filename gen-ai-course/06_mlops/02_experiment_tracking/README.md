# Experiment Tracking

This subtopic covers how to *track experiments* for GenAI systems so that every prompt tweak, model swap, and eval run is reproducible and comparable. You will learn the core data model that tools like MLflow and Weights & Biases share — runs, experiments, params, metrics, and artifacts — and how to map it onto GenAI specifics: prompt/temperature/top_p/model as params, and faithfulness, answer relevance, cost, latency, and token counts as metrics. You will then learn how to organize and compare runs, pick the *best* one (and why metric direction — max vs min — matters), and hand that winning run off to a model registry for staged promotion. The goal is to turn "I think the new prompt is better" into a defensible, evidence-backed selection.

## Topics

- Why experiment tracking matters for GenAI (reproducibility, comparison, hand-off)
- The run / experiment / artifact data model
- What to log for GenAI: params, metrics, artifacts, and tags
- MLflow vs Weights & Biases vs Neptune — a comparison
- Comparing runs and picking the best (max vs min metric direction)
- The hand-off to a model registry: Staging → Production

## Files in this subtopic

- `concepts.md` — the teaching content: ASCII diagrams, comparison tables, and focused code snippets for every topic above.
- `quiz.md` — multiple-choice questions with answers and explanations to check your understanding.
- `exercise_01.md` — the brief for the hands-on coding exercise (an in-memory experiment tracker with best-run selection).
- `exercise.py` — a runnable starter scaffold with a provided `Run` record; you fill in the `# TODO` sections.
- `solution.py` — the complete, offline, fully-tested reference implementation of the tracker.
- `interview.md` — interview questions and model answers on experiment tracking for GenAI.
- `references.md` — curated links to authoritative docs and articles for deeper study.

## Start

Begin with `concepts.md`, then test yourself with `quiz.md`, and finally build the tracker in `exercise.py` (checking against `solution.py`).
