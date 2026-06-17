# Exercise: Artifact Version Registry with Rollback

## Background

Every production GenAI system needs a way to register versioned artifacts (a model, a prompt, an index), deploy a chosen one, and — when something regresses — roll back to a prior version *fast*. The two ingredients that make rollback trustworthy are **immutable versions** (the version you roll back to is exactly what it was) and a **deployment-history audit trail** (so you know what the previous stable version was).

In this exercise you build a small, offline `ArtifactRegistry` that does exactly this. No network, no API keys — just an in-memory store.

## Your Task

Open `exercise.py` and complete the `ArtifactRegistry` class:

1. **`register(version, payload)`** — store a new immutable version. Raise `ValueError` if the version already exists (versions are immutable). Auto-record nothing here — registering is not deploying.
2. **`deploy(version)`** — make `version` the *current* deployment. Raise `KeyError` if the version was never registered. Append a history record `{"version", "action": "deploy", "from_version", "timestamp"}` where `from_version` is whatever was current before (or `None` the first time).
3. **`rollback()`** — re-point `current` to the **previous distinct version** that was deployed (per history), and append a record with `"action": "rollback"`. Raise `RuntimeError` if there is no prior version to roll back to.
4. **`current_version()`** — return the currently deployed version (or `None`).
5. **`history()`** — return a copy of the deployment-history list.

## Requirements

- Versions are **immutable**: re-registering an existing version must raise `ValueError`.
- `deploy` of an unregistered version must raise `KeyError`.
- A monotonic timestamp counter is provided so output is deterministic — use it; do not call `time.time()`.
- Must run fully offline (Python standard library only).
- `history()` and `current_version()` must not let callers mutate internal state.

## How to Run

```bash
python exercise.py
```

The starter raises `NotImplementedError` until you fill in the `# TODO` sections.

## Expected Output

When finished, running the demo should look something like:

```
Registered: ['v1', 'v2', 'v3']
Deployed v1 -> current = v1
Deployed v2 -> current = v2
Deployed v3 -> current = v3
Rolled back -> current = v2
Rolled back -> current = v1
History actions: ['deploy', 'deploy', 'deploy', 'rollback', 'rollback']
All assertions passed.
```
