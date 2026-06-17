# Pipeline Orchestration — Concepts

A GenAI system is never one program — it is a *chain of steps* that must run in the right order, recover from failure, and repeat on a schedule. Orchestration is the discipline of describing that chain as a graph of tasks and handing it to an engine that runs, retries, and schedules it for you. This file walks through the core ideas: why pipelines beat scripts, the DAG model that underpins every orchestrator, how training and inference pipelines look in GenAI, how Airflow/Prefect/Dagster compare, how retries and idempotency make runs robust, and what triggers a retrain.

---

## 1. Pipelines vs Scripts

A *script* does everything in one linear file: load data, embed it, push to a vector store, all top-to-bottom. It works on your laptop and falls apart in production. A *pipeline* breaks the same work into named tasks with declared dependencies, run by an orchestrator that handles ordering, retries, scheduling, and observability.

| Dimension | Script | Orchestrated pipeline |
|---|---|---|
| **Structure** | Linear, top-to-bottom | DAG of named tasks |
| **Failure** | Whole script dies; rerun from top | Retry one task; resume from failure |
| **Re-run cost** | Repeat all work | Re-run only what's needed |
| **Scheduling** | `cron` + a prayer | First-class schedules & triggers |
| **Parallelism** | Manual threads | Engine runs independent tasks in parallel |
| **Visibility** | `print()` / log file | UI, run history, lineage, alerts |
| **Backfill** | Hand-edit dates | Built-in date-range backfills |

The moment you have more than ~3 steps, real dependencies, or anything that runs on a schedule and must survive partial failure, you have outgrown the script and want a pipeline.

---

## 2. The DAG Model

Every orchestrator represents a pipeline as a **DAG — a Directed Acyclic Graph**. *Nodes* are tasks; *edges* are dependencies ("B runs after A"). "Directed" means edges point one way; "Acyclic" means there are no cycles — a task can never (even indirectly) depend on itself, otherwise nothing could ever start.

```
        ┌─────────┐
        │ ingest  │
        └────┬────┘
             │
        ┌────▼────┐
        │  chunk  │
        └────┬────┘
             │
        ┌────▼────┐         ┌──────────────┐
        │  embed  │         │ build_synonyms│  (parallel branch)
        └────┬────┘         └───────┬──────┘
             │                      │
             └───────┬──────────────┘
                     ▼
                ┌─────────┐
                │  index  │   (waits for BOTH embed + build_synonyms)
                └─────────┘
```

### Topological order

To run a DAG you need a **topological order**: a linear sequence in which every task appears *after* all of its dependencies. The graph above has valid orders like `ingest, chunk, embed, build_synonyms, index` or `ingest, chunk, build_synonyms, embed, index` — `index` is always last because it depends on two upstream tasks. Independent tasks (`embed`, `build_synonyms`) may be ordered either way, which is exactly what lets an engine run them in **parallel**.

**Kahn's algorithm** is the standard way to compute it: repeatedly emit any node whose in-degree (number of unmet dependencies) is zero, then decrement its dependents.

```python
from collections import deque

def topological_order(deps: dict[str, list[str]]) -> list[str]:
    indegree = {n: 0 for n in deps}
    for n, parents in deps.items():
        indegree[n] += len(parents)          # count unmet deps
    children = {n: [] for n in deps}
    for n, parents in deps.items():
        for p in parents:
            children[p].append(n)            # reverse edges

    ready = deque(n for n, d in indegree.items() if d == 0)
    order = []
    while ready:
        node = ready.popleft()
        order.append(node)
        for child in children[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)

    if len(order) != len(deps):              # something never reached 0
        raise ValueError("cycle detected in DAG")
    return order
```

If a cycle exists, some nodes never reach in-degree 0, so `order` is shorter than the node set — that's how Kahn's algorithm **detects cycles**. This is precisely the logic you'll implement in the exercise.

---

## 3. Training vs Inference Pipelines for GenAI

In GenAI MLOps you'll build two recurring shapes. They run on different cadences and have different failure modes.

**Training / fine-tune pipeline** — runs occasionally (weekly, on drift, on demand), produces a *versioned artifact*:

```
prepare_data ─► fine_tune ─► evaluate ─► register ─► deploy_canary ─► promote
                               │
                               └─(eval fails the quality gate)─► STOP (don't register)
```

**Inference / ingestion pipeline** — runs continuously or on a tight schedule, keeps the serving system fresh:

```
ingest ─► chunk ─► embed ─► index ─► smoke_test
```

| Aspect | Training pipeline | Inference/ingestion pipeline |
|---|---|---|
| **Cadence** | Occasional (days/weeks, or triggered) | Continuous / hourly / on event |
| **Output** | New model version + eval report | Updated vector index / predictions |
| **Compute** | Heavy GPU, long-running | Steady, often embarrassingly parallel |
| **Quality gate** | Eval must beat baseline to register | Smoke test the freshly built index |
| **Idempotency key** | Run/version id | Document/content hash |
| **Failure impact** | No new model (old one keeps serving) | Stale index until next successful run |

The critical pattern in the training pipeline is the **quality gate**: `evaluate` must pass (e.g. beat the current production model on a held-out eval set and a safety suite) *before* `register` and `deploy` run. A failed gate should stop the DAG, not ship a worse model.

---

## 4. Airflow vs Prefect vs Dagster

These are the three orchestrators you'll meet most. They share the DAG model but differ in philosophy: Airflow is task-centric and battle-tested, Prefect is Pythonic and dynamic, Dagster is asset/data-centric with strong typing and lineage.

| Dimension | Airflow | Prefect | Dagster |
|---|---|---|---|
| **Core abstraction** | Tasks in a DAG | `@flow` / `@task` functions | Software-defined **assets** |
| **DAG definition** | Static (defined upfront) | Dynamic (DAG emerges at runtime) | Asset graph (declarative) |
| **Mental model** | "Schedule these tasks" | "Run this Python, observe it" | "Materialize these data assets" |
| **Scheduling** | Rich cron + sensors | Schedules + event triggers | Schedules + sensors + auto-materialize |
| **Local dev** | Heavier (scheduler+webserver) | Lightweight | Lightweight, great UI |
| **Lineage / data awareness** | Limited (via XCom/datasets) | Via results & artifacts | First-class (asset lineage) |
| **Best for** | Mature, ops-heavy ETL & ML | Flexible, code-first Python flows | Data/ML platforms that think in assets |

```python
# Prefect — orchestration is just decorated Python
from prefect import flow, task

@task(retries=2, retry_delay_seconds=10)
def embed(chunks): ...

@task
def index(vectors): ...

@flow(name="ingest-pipeline")
def ingest_pipeline(path: str):
    chunks = chunk(load(path))
    vectors = embed(chunks)      # dependencies are inferred from data flow
    index(vectors)
```

```python
# Dagster — you declare ASSETS; the graph is derived from inputs
from dagster import asset

@asset
def raw_docs(): ...

@asset
def embeddings(raw_docs):       # depends on raw_docs by parameter name
    ...

@asset
def vector_index(embeddings):   # depends on embeddings
    ...
```

You do **not** need to memorize one tool. Understand the shared DAG model and the trade-offs; the concepts transfer.

---

## 5. Retries, Idempotency & Backfills

Distributed steps fail for boring reasons — a rate limit, a network blip, a node eviction. Orchestrators make this survivable with three tools.

**Retries.** A task is configured with a retry count and a backoff. Total attempts = `retries + 1`. Use **exponential backoff** so you don't hammer a struggling dependency.

```python
import time

def run_with_retries(fn, retries=3, base_delay=1.0):
    attempt = 0
    while True:
        try:
            return fn()
        except Exception:
            attempt += 1
            if attempt > retries:
                raise                       # give up after retries+1 attempts
            time.sleep(base_delay * (2 ** (attempt - 1)))  # 1s, 2s, 4s, ...
```

**Idempotency.** A retried (or backfilled) task may run more than once, so running it twice must be *safe* — same inputs produce the same effect, no duplicates. The trick is a deterministic **idempotency key**:

```python
import hashlib

def embed_and_upsert(doc_id: str, text: str, store):
    key = hashlib.sha256(f"{doc_id}:{text}".encode()).hexdigest()
    if store.exists(key):       # already done in a prior (maybe failed) run
        return key              # no-op, safe to re-run
    store.upsert(key, embed(text))   # UPSERT, not INSERT — no duplicates
    return key
```

Non-idempotent: `INSERT` a row, `+=` a counter, "send an email." Idempotent: `UPSERT` by key, write to a content-addressed path, set-to-value.

**Backfills.** When you add a new step or fix a bug, you re-run the pipeline over a *historical date range*. Idempotent tasks make backfills safe — re-processing last month's documents simply re-upserts the same keys instead of doubling your index.

```
Backfill 2024-01-01 .. 2024-01-31:
  run(2024-01-01) ─ run(2024-01-02) ─ ... ─ run(2024-01-31)
  (each run is independent and idempotent, so they can run in parallel)
```

---

## 6. Retraining Triggers

What kicks off the training pipeline? There are three canonical triggers, and mature systems combine them.

| Trigger | Fires when | Pros | Cons |
|---|---|---|---|
| **Schedule (cron)** | A clock condition (e.g. weekly Sunday 02:00) | Simple, predictable, easy to reason about | Retrains even when nothing changed; or too late if drift is fast |
| **Drift-based** | Input/output distribution shifts past a threshold | Retrains exactly when quality is at risk | Needs monitoring + good metrics; noisy signals cause false alarms |
| **Data-volume-based** | N new labeled/ingested records accumulate | Ties cost to actual new signal | Volume ≠ value; may miss qualitative shifts |

```python
def should_retrain(state) -> tuple[bool, str]:
    if state.days_since_last_train >= 7:
        return True, "schedule: weekly cadence reached"
    if state.psi > 0.2:                       # population stability index
        return True, f"drift: PSI={state.psi:.2f} exceeds 0.2"
    if state.new_docs >= 10_000:
        return True, f"data volume: {state.new_docs} new docs"
    return False, "no trigger met"
```

- **Schedule-based** suits stable domains and predictable budgets.
- **Drift-based** is the gold standard for quality but requires monitoring (PSI, KL divergence, embedding-distribution shift, eval-score decay). It is the bridge between your *monitoring* subtopic and this one.
- **Data-volume-based** fits systems where fresh labeled data trickles in (e.g. accumulate 10k thumbs-up/down before re-tuning).

A robust setup is **OR of all three with guardrails**: "retrain if it's been a week, OR drift > threshold, OR 10k new docs — but never more than once per day, and only if the eval gate passes before deploy."

---

## 7. Scheduling & Automation

Beyond clock schedules, orchestrators automate runs with **sensors / triggers** that wait for an external condition, then launch the DAG.

```
                       ┌──────────────────────────────┐
   cron schedule ─────►│                              │
   file/S3 sensor ────►│   ORCHESTRATOR (scheduler)   │──► launch DAG run
   drift alert ───────►│                              │
   API / manual ──────►│                              │
                       └──────────────────────────────┘
```

| Mechanism | What it waits on | GenAI example |
|---|---|---|
| **Cron schedule** | A time expression | Re-embed the docs index nightly at 02:00 |
| **File / object sensor** | A new file lands (e.g. S3 `ObjectCreated`) | New PDF uploaded → ingest pipeline |
| **Upstream-dataset trigger** | Another pipeline's output updated | Embeddings refreshed → rebuild index |
| **Event / webhook** | An external signal (alert, message) | Drift monitor fires → training pipeline |
| **Manual / API** | A human or service triggers a run | On-demand re-fine-tune from the UI |

```text
# cron quick reference  (min hour day-of-month month day-of-week)
0  2  *  *  *     # every day at 02:00
0  2  *  *  0     # every Sunday at 02:00
*/15 * *  *  *    # every 15 minutes
0  0  1  *  *     # first day of every month, midnight
```

Automation glue you'll wire together: a **schedule** fires the routine retrain; a **sensor** catches new data the moment it arrives; an **event** from your monitoring stack triggers drift-based retraining; and every triggered run flows through the same DAG with retries, idempotency, and a quality gate before anything deploys.

---

## Key Takeaways

- **Graduate from scripts to pipelines** once you have real dependencies, schedules, or partial-failure recovery needs — orchestration buys you ordering, retries, parallelism, and observability.
- **Everything is a DAG.** Tasks are nodes, dependencies are edges, and a valid run order is a *topological sort*. No cycles allowed — Kahn's algorithm both orders the graph and detects cycles.
- **Know your two pipeline shapes:** the occasional training pipeline (`fine-tune → eval → register → deploy`, gated by evaluation) and the continuous ingestion pipeline (`ingest → chunk → embed → index`).
- **Airflow, Prefect, Dagster** all share the DAG model; they differ in task-centric vs Pythonic vs asset-centric philosophy. Learn the model, not just one tool.
- **Make tasks idempotent and retryable.** Retries with backoff plus idempotency keys (UPSERT, content hashing) make runs and backfills safe to repeat.
- **Retrain on a trigger, not a hunch:** combine schedule-, drift-, and data-volume-based triggers, with guardrails and an eval gate so you never ship a worse model.
