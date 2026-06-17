# Exercise: Canary Release Controller

## Background

A canary release shifts a small slice of traffic to a new version, watches its error rate, and ramps up only while it stays healthy — or rolls back the instant errors exceed a threshold. Automating that loop turns a risky all-at-once deploy into a graduated, self-protecting one.

In this exercise you build a `CanaryController` that drives the loop offline. A deterministic mock metrics source is provided; you implement the ramp/promote/rollback logic.

## Your Task

Open `exercise.py` and complete the `CanaryController`:

1. **`__init__`** — start with `weight = 0`, `status = "in_progress"`, and an empty `history` list. Store `step`, `error_threshold`, and the `metrics_source` callable.
2. **`advance()`** — perform one canary step (shift first, then observe):
   - Increase `weight` by `step` (capped at 100).
   - Read the error rate at the new weight: `error_rate = self.metrics_source(self.weight)`.
   - If `error_rate > self.error_threshold`: set `weight = 0`, `status = "rolled_back"`.
   - Elif `weight >= 100`: set `status = "promoted"`.
   - Append a record `{"weight", "error_rate", "status"}` (the *post-step* weight and status) to `history`.
   - Return the new `status`.
3. **`run()`** — call `advance()` repeatedly until `status` is no longer `"in_progress"`; return the final `status`.

## Requirements

- Rollback sets weight to 0 immediately and stops (status `"rolled_back"`).
- Promotion happens only when weight reaches 100 with no threshold breach (status `"promoted"`).
- Weight never exceeds 100.
- Must run fully offline (Python standard library only) — use the provided `metrics_source`, not real metrics.
- `run()` must terminate (the status leaves `"in_progress"`).

## How to Run

```bash
python exercise.py
```

The starter raises `NotImplementedError` until you fill in the `# TODO` sections.

## Expected Output

When finished, running the demo should look something like:

```
=== Healthy canary (auto-promotes) ===
  weight= 25%  error=0.002  status=in_progress
  weight= 50%  error=0.003  status=in_progress
  weight= 75%  error=0.004  status=in_progress
  weight=100%  error=0.005  status=promoted
Final: promoted

=== Unhealthy canary (auto-rolls back) ===
  weight=  0%  error=0.090  status=rolled_back
Final: rolled_back
All assertions passed.
```
