# Exercise: Mini DAG Runner with Retries and Cycle Detection

## Background

Every orchestrator — Airflow, Prefect, Dagster — boils down to the same core: model the work as a DAG, compute a valid run order, execute each task only after its dependencies succeed, and retry tasks that fail. In this exercise you build that core yourself, offline, with no dependencies beyond the standard library.

You will run a GenAI-flavored ingestion DAG (`ingest → chunk → embed → index`, plus a parallel `build_synonyms` branch) and make it survive flaky and failing stages.

## Your Task

Open `exercise.py` and complete the `DAGRunner` class:

1. **`add_stage(name, func, depends_on=(), retries=0)`** — register a stage. `func` is a callable returning a result. Store its dependencies and retry count.
2. **`topological_order() -> list[str]`** — return stage names in a valid topological order (every dependency appears before its dependent). Use Kahn's algorithm. If the graph contains a cycle, raise `ValueError`.
3. **`run() -> dict`** — execute stages in topological order:
   - A stage runs only after **all** its dependencies have status `SUCCESS`.
   - On failure, retry up to its `retries` count (total attempts = `retries + 1`).
   - If it still fails, mark it `FAILED` and **skip** every downstream stage that (transitively) depends on it, marking them `SKIPPED`.
   - Record per-stage `status`, `attempts`, and `output`. Return that result dict.

## Requirements

- Use Kahn's algorithm (in-degree based) and detect cycles via the "order shorter than node set" check.
- Total attempts for a stage that eventually succeeds after K failures must be `K + 1`.
- A stage with a FAILED dependency must be `SKIPPED` and must never call its `func`.
- Make the "flaky" behavior deterministic (a counter/closure) — no randomness, fully offline.
- Standard library only.

## How to Run

```bash
python exercise.py
```

The starter raises `NotImplementedError` until you fill in the `# TODO` sections, so it imports cleanly but the demo will fail until complete.

## Expected Output

When finished, running the demo should look something like:

```text
Topological order: ['ingest', 'chunk', 'embed', 'build_synonyms', 'index']
--- Run 1: all stages succeed ---
ingest: SUCCESS (attempts=1)
chunk: SUCCESS (attempts=1)
embed: SUCCESS (attempts=1)
build_synonyms: SUCCESS (attempts=1)
index: SUCCESS (attempts=1)
--- Run 2: flaky embed (fails twice, retries=2) ---
embed: SUCCESS (attempts=3)
--- Run 3: embed always fails (retries=1); index skipped ---
embed: FAILED (attempts=2)
index: SKIPPED (attempts=0)
Cycle correctly detected: cycle detected in DAG
```
