# Exercise: An Experiment Tracker with Best-Run Selection

## Background

When you tune a GenAI system you produce many runs — each with a different prompt, model, or temperature, and each scored on faithfulness, answer relevance, cost, and latency. To decide which configuration to ship, you need to *track* every run and then *select* the best one for a given metric. That selection has subtleties: quality metrics are maximized while cost/latency are minimized, runs that never logged a metric must be ignored, and asking for a metric nobody recorded is an error.

In this exercise you will build a small, offline `ExperimentTracker` — the same data model MLflow and Weights & Biases share, reduced to pure Python. The `Run` record is provided; you implement the tracker and, most importantly, the `best_run` selection logic.

## Your Task

Open `exercise.py` and complete the `ExperimentTracker` class:

1. **`__init__`** — create an empty run store (a dict) and a creation-order counter (`itertools.count(1)` is handy as a stable seq / tiebreaker).
2. **`start_run(name, params)`** — create a run with a unique id (e.g. `f"run-{seq:04d}"`), store the params and seq, set status `"RUNNING"`, and return the run_id.
3. **`log_metric(run_id, key, value)`** — record a numeric metric (support multiple metrics per run; store `float(value)`).
4. **`log_artifact(run_id, name, content)`** — record a named artifact (just keep the string/bytes/object in memory).
5. **`end_run(run_id, status="FINISHED")`** — mark the run finished (or `FAILED`/`KILLED`).
6. **`get_run(run_id)`** and **`list_runs()`** — return snapshot dicts (use the provided `Run.as_dict()`).
7. **`best_run(metric, mode="max")`** — the core logic:
   - Validate `mode` is `"max"` or `"min"` (else `ValueError`).
   - Consider only runs that logged `metric`; ignore the rest.
   - If no run logged it, raise `ValueError`.
   - Return the run_id with the best value for the given direction.

## Requirements

- Do not modify the provided `Run` dataclass.
- Use the Python standard library only — no external packages, no network, no API keys.
- `best_run` must ignore runs missing the metric and must raise `ValueError` when none logged it.
- Support multiple metrics per run and multiple runs per tracker.

## How to Run

```bash
python exercise.py
```

The starter raises `NotImplementedError` until you fill in the `# TODO` sections, so it imports cleanly but the demo will fail until complete. Check your work against `solution.py`.

## Expected Output

When finished, running the demo should look something like:

```text
run-0001 rag-baseline {'faithfulness': 0.81, 'cost_usd': 0.012}
run-0002 rag-reranker {'faithfulness': 0.93, 'cost_usd': 0.041}
run-0003 rag-tiny {'faithfulness': 0.7, 'cost_usd': 0.003}
Best faithfulness (max): run-0002
Cheapest cost (min): run-0003
```

The full reference (`solution.py`) goes further: it logs four runs, asserts that the missing-metric run is ignored, asserts a `ValueError` when no run logged the metric, and simulates a registry hand-off — finishing with `All assertions passed.`
