# Pipeline Orchestration - Interview Questions

This document contains interview questions and answers on pipeline orchestration for GenAI MLOps: DAGs, training vs inference pipelines, orchestrators, retries, idempotency, and retraining triggers.

---

### Q1: What is pipeline orchestration, and why not just use a script or cron?

**Answer:** Orchestration is modeling a workflow as a graph of tasks with explicit dependencies and handing it to an engine that runs, schedules, retries, and monitors it. A plain script reruns everything from the top on failure and has no native scheduling, retries, parallelism, or observability. `cron` can launch a script but can't express dependencies, resume from a failed step, backfill a date range, or show run history. Once you have real dependencies, schedules, and partial-failure recovery needs, an orchestrator (Airflow/Prefect/Dagster) pays for itself.

---

### Q2: What is a DAG and why must it be acyclic?

**Answer:** A DAG (Directed Acyclic Graph) represents a pipeline: nodes are tasks, directed edges are dependencies ("B after A"). It must be acyclic because a cycle means a task depends (directly or transitively) on itself — there is no valid starting point, so the pipeline could never begin. Orchestrators reject cyclic definitions for exactly this reason.

---

### Q3: How do you compute a valid execution order for a DAG, and how do you detect cycles?

**Answer:** With a **topological sort**, most commonly **Kahn's algorithm**:

1. Compute each node's in-degree (number of dependencies).
2. Put all in-degree-0 nodes in a queue.
3. Pop a node, emit it, and decrement each child's in-degree; enqueue any child that hits 0.
4. Repeat until the queue is empty.

If the emitted list is shorter than the node set, some nodes never reached in-degree 0 — that means a **cycle**, and you raise an error. The alternative is DFS with a recursion/visiting-stack to spot a back edge.

---

### Q4: Contrast a GenAI training pipeline with an inference/ingestion pipeline.

**Answer:**

| Aspect | Training pipeline | Inference/ingestion pipeline |
|---|---|---|
| Shape | prepare → fine_tune → evaluate → register → deploy | ingest → chunk → embed → index |
| Cadence | Occasional / triggered | Continuous / hourly / on-event |
| Output | Versioned model + eval report | Updated index / predictions |
| Compute | Heavy, long GPU jobs | Steady, parallelizable |
| Key gate | Eval must beat baseline before register | Smoke test the new index |
| Failure impact | No new model; old keeps serving | Stale index until next success |

---

### Q5: What is a quality gate in a fine-tune pipeline and why is it critical?

**Answer:** A quality gate is an `evaluate` step that must pass before `register`/`deploy` run. It checks the new model against a held-out eval set (beating the current production baseline) plus safety/regression suites. It's critical because automation will otherwise happily ship a *worse* model. A failed gate should stop the DAG so the existing model keeps serving — never deploy on a regression.

---

### Q6: Compare Airflow, Prefect, and Dagster.

**Answer:** All three orchestrate DAGs but differ in philosophy:

| Tool | Core abstraction | DAG style | Best for |
|---|---|---|---|
| **Airflow** | Tasks in a DAG | Static, defined upfront | Mature, ops-heavy ETL/ML |
| **Prefect** | `@flow`/`@task` Python | Dynamic, inferred at runtime | Flexible code-first Python flows |
| **Dagster** | Software-defined **assets** | Declarative asset graph | Data/ML platforms with strong lineage |

Airflow is task-centric and battle-tested. Prefect feels like decorated Python with great local dev. Dagster centers on data assets with first-class lineage and typing. Learn the shared DAG model; the concepts transfer.

---

### Q7: How do retries work, and what is the relationship between retries and total attempts?

**Answer:** A task is configured with a retry count and a backoff policy. **Total attempts = retries + 1** (the initial attempt plus the retries). So `retries=2` means up to 3 executions. Use **exponential backoff** (1s, 2s, 4s, ...) so retries don't hammer a struggling dependency, and cap retries so a permanently broken task fails fast instead of looping forever.

---

### Q8: What does idempotency mean for a pipeline task, and why does it matter?

**Answer:** Idempotent means running the task multiple times has the same effect as running it once — no duplicates, no double-counting. It matters because retries and backfills cause tasks to run more than once. Patterns: **UPSERT by an idempotency key**, write to a **content-addressed path** (hash of the content), or set-to-value instead of increment. Non-idempotent operations (raw INSERT, `+=` counters, "send an email") are dangerous under retry.

---

### Q9: Give a concrete idempotency strategy for an embed-and-upsert step.

**Answer:** Derive a deterministic key from the input, e.g. `sha256(f"{doc_id}:{text}")`. Before embedding, check whether that key already exists in the vector store; if so, no-op. Otherwise embed and **UPSERT** under that key. A re-run (after a crash, or a backfill of last month) recomputes the same key and either skips or overwrites the same record — never creating a duplicate vector.

---

### Q10: What is a backfill and why is idempotency a prerequisite?

**Answer:** A backfill re-runs a pipeline over a historical date range — for instance after adding a new step or fixing a bug. Because backfills re-process data that may already have been processed, the tasks must be idempotent; otherwise you'd double your index or inflate counters. With idempotent tasks, each historical run is independent and safe, and the runs can even execute in parallel.

---

### Q11: What are the three main retraining triggers and when do you use each?

**Answer:**

| Trigger | Fires when | Use when |
|---|---|---|
| **Schedule (cron)** | A clock condition (weekly, nightly) | Stable domain, predictable budget |
| **Drift-based** | Distribution shifts past a threshold | Quality is the priority; monitoring exists |
| **Data-volume-based** | N new records accumulate | Fresh labeled data trickles in |

Mature systems use the **OR of all three with guardrails**: retrain if it's been a week, OR drift exceeds threshold, OR 10k new docs arrived — but at most once per day, and only deploy if the eval gate passes.

---

### Q12: How do you detect drift to power a drift-based trigger?

**Answer:** Compare the live distribution to a reference (training) distribution using metrics such as **PSI (Population Stability Index)**, **KL divergence**, or, for GenAI, **embedding-distribution shift** and **eval-score decay** on a golden set. Set a threshold (e.g. PSI > 0.2) and fire the training pipeline when it's breached. Guard against noise with smoothing/windows so a single noisy spike doesn't trigger a costly retrain.

---

### Q13: A pipeline stage fails permanently after exhausting retries. What happens to downstream stages?

**Answer:** They are **SKIPPED**, not run. A downstream stage's precondition — its dependency succeeding — is unmet, so running it would feed it missing or invalid input. The orchestrator records the failure, skips the affected branch (transitively), and lets unrelated branches continue. This is exactly the behavior implemented in the exercise's `run()`.

---

### Q14: What are sensors/triggers and how do they differ from schedules?

**Answer:** A **schedule** launches a run on a *time* condition (cron). A **sensor/trigger** launches a run on an *external* condition — a new file landing in S3, an upstream dataset being updated, or an event/webhook (e.g. a drift alert). Sensors make pipelines event-driven and reactive rather than purely time-driven, so work starts the moment data arrives instead of waiting for the next scheduled tick.

---

### Q15: How would you design automation for a RAG index that must stay fresh and a model that must stay accurate?

**Answer:**

- **Ingestion pipeline** (`ingest → chunk → embed → index`) triggered by an **S3/object sensor** the moment a document lands, plus a nightly **cron** sweep to catch anything missed. Tasks are idempotent (content-hash keys) and retried with backoff.
- **Training pipeline** (`prepare → fine_tune → evaluate → register → deploy`) triggered by the **OR** of a weekly schedule, a **drift event** from monitoring, and a **data-volume threshold**, with guardrails (max once/day) and an **eval quality gate** before deploy.
- Both run through the same orchestrator with run history, alerting on failure, and lineage so you can trace which data/model produced a given output.

---

## Summary

Key orchestration topics:

1. **DAG model:** nodes, edges, topological sort, cycle detection (Kahn's algorithm).
2. **Two pipeline shapes:** gated training pipelines vs continuous ingestion pipelines.
3. **Orchestrators:** Airflow (tasks), Prefect (Pythonic flows), Dagster (assets).
4. **Robustness:** retries with backoff, idempotency keys, safe backfills.
5. **Automation:** schedule-, drift-, and data-volume-based retraining triggers, plus sensors.

---

## References

- [Orchestration Docs & Algorithms](references.md)
