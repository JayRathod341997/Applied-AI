# Exercise: AWS CodeDeploy-Style Traffic-Shift Deployer

## Background

AWS CodeDeploy releases a new version by following a named **deployment configuration** — a traffic-shift schedule. `AllAtOnce` flips 100% immediately; `Canary10Percent5Minutes` sends 10% for a 5-minute bake then jumps to 100%; `Linear10PercentEvery1Minute` adds 10% each minute until 100%. While it shifts, CodeDeploy watches **CloudWatch alarms** attached to the deployment group; if one enters `ALARM`, it **automatically rolls back** to the previous (stable) version.

In this exercise you build a `Deployer` that drives that loop offline. The deployment configs and a deterministic mock alarm source are provided; you implement the shift / succeed / auto-rollback logic. This is the AWS-managed form of the canary controller you built in subtopic 03 — here the *schedule* is declarative and the rollback trigger is an alarm.

## Your Task

Open `exercise.py` and complete the `Deployer`:

1. **`__init__`** — start with `weight = 0`, `status = "in_progress"`, and an empty `history` list. Store `schedule`, `alarm_source`, and `error_threshold`.
2. **`run()`** — walk the schedule. For each `(minute, target)` step in `self.schedule`:
   - Shift traffic to this step: `self.weight = target`.
   - Read the alarm metric at the new weight: `error_rate = self.alarm_source(target)`.
   - If `error_rate > self.error_threshold`: set `self.weight = 0` and `self.status = "rolled_back"`, append the record, then **stop and return** `"rolled_back"`.
   - Otherwise: `self.status = "succeeded" if target >= 100 else "in_progress"`.
   - Append a record `{"minute", "weight", "error_rate", "status"}` to `history`.
   - After the loop, return `self.status`.

## Requirements

- A breach rolls back immediately: weight goes to 0, status `"rolled_back"`, and the walk stops (no further steps).
- Success happens only when a step reaches weight 100 with no breach (status `"succeeded"`).
- Use the **provided** `DEPLOY_CONFIGS` and `alarm_source` callables — do not invent traffic numbers.
- Must run fully offline (Python standard library only) — no `boto3`, no AWS, no network.
- `run()` must terminate (the schedule is finite and ends at 100).

## How to Run

```bash
python exercise.py
```

The starter raises `NotImplementedError` until you fill in the `# TODO` sections.

## Expected Output

When finished, running the demo should look something like:

```
=== Canary10Percent5Minutes, healthy (succeeds) ===
  t+ 0m  weight= 10%  error=0.001  status=in_progress
  t+ 5m  weight=100%  error=0.005  status=succeeded
Final: succeeded

=== Canary10Percent5Minutes, unhealthy (auto-rolls back) ===
  t+ 0m  weight=  0%  error=0.090  status=rolled_back
Final: rolled_back
```

The full reference (`solution.py`) also exercises the `Linear…` config degrading at 50% and the `AllAtOnce` cases, and self-checks every result with assertions.
