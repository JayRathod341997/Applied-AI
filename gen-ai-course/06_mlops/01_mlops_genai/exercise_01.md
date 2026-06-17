# Exercise: In-Memory Model / Prompt Registry

## Background

In a GenAI MLOps practice, the **registry** is the single source of truth for versioned artifacts — models, prompts, datasets, indexes — and it tracks which *version* of each artifact occupies which *stage*. The runtime never hard-codes a version; it asks the registry for "the current Production version of `support-prompt`". Releasing a new version, or rolling back to a previous one, is then a metadata change rather than a redeploy.

In this exercise you build a small, offline registry that captures this core idea: register immutable versioned artifacts, promote a version through stages (None → Staging → Production), and fetch whatever currently holds Production.

Everything runs offline — there are no models or network calls, just plain Python objects standing in for artifacts.

## Your Task

Open `exercise.py` and complete the `ModelRegistry` class:

1. **`register(name, artifact)`** — append a new immutable `Version` under `name`. Version numbers start at 1 and increase by 1 per registration. Return the new version number. The new version's stage starts as `"None"`.
2. **`promote(name, version, stage)`** — move the given version to `stage`. First **demote** any version that currently holds that stage (set it to `"Archived"`), so exactly one version occupies a stage. Validate that `stage` is one of the allowed stages and that the version exists.
3. **`get_version(name, version)`** — return the `Version` object (raise `KeyError` if the name or version is unknown).
4. **`get_current(name, stage="Production")`** — return the `Version` currently in `stage`, or raise `KeyError` if none.
5. **`list_versions(name)`** — return the list of `Version` objects for the name (a copy).

## Requirements

- Versions are immutable once created (you only ever change their `stage`).
- Exactly one version may hold a given stage at a time (promoting demotes the previous holder).
- Allowed stages: `None`, `Staging`, `Production`, `Archived`. Reject anything else with `ValueError`.
- Must run fully offline with no API keys and no network access — standard library only.

## How to Run

```bash
python exercise.py
```

The starter raises `NotImplementedError` until you fill in the `# TODO` sections, so it imports cleanly but the demo fails until complete.

## Expected Output

When finished, running the solution demo should look something like:

```
=== Register versions ===
support-prompt -> v1, v2, v3
=== Promote v2 to Staging, then v3 to Production ===
Staging  -> v2
Production -> v3
=== Roll back: promote v2 to Production ===
Production -> v2 (v3 demoted to Archived)
All assertions passed.
```
