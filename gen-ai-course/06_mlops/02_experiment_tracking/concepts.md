# Experiment Tracking — Concepts

Building a good GenAI system is an *empirical* process: you try a prompt, swap a model, nudge the temperature, re-run your eval set, and ask "is this better?". Experiment tracking is the discipline of recording every one of those attempts — its configuration, its results, and its artifacts — so the question can be answered with evidence instead of memory. This file walks through what tracking is, the data model behind every tracker, what to log for GenAI specifically, how the major tools compare, how to compare runs and pick a winner, and how the winner is handed off to a model registry.

---

## 1. What Experiment Tracking Is (and Why GenAI Needs It)

An *experiment* is a question ("does adding a reranker improve faithfulness?"). A *run* is one concrete attempt at answering it (one config, one eval pass, one set of numbers). A tracker persists every run so you can reproduce, compare, and audit them.

Without tracking, teams fall into the classic failure modes: results live in notebook output that gets overwritten, "the good prompt" is a Slack message no one can find, and nobody can say *why* the production model was chosen.

```
   tweak prompt / model / params
            │
            ▼
   ┌─────────────────┐     log      ┌──────────────────┐
   │   Eval run      │ ───────────► │  Experiment      │
   │ (one config)    │  params      │  Tracker         │
   │                 │  metrics     │  (MLflow / W&B)  │
   │                 │  artifacts   │                  │
   └─────────────────┘              └────────┬─────────┘
            ▲                                 │
            └──── compare & iterate ◄─────────┘
```

Why GenAI raises the stakes:

- **Many moving parts.** Prompt text, system message, model, temperature, top_p, retriever, chunk size — any one changes the output.
- **Fuzzy, multi-dimensional metrics.** Quality is not a single accuracy number; it is faithfulness, answer relevance, plus cost, latency, and token counts that trade off against each other.
- **Reproducibility is hard.** LLM calls are stochastic and providers change models silently, so logging the exact config and outputs is the only way to explain a result later.

---

## 2. The Run / Experiment / Artifact Data Model

Almost every tracker shares the same hierarchy. Learn it once and the specific tool barely matters.

```
┌──────────────────────────────────────────────────────────┐
│  EXPERIMENT  "rag-faithfulness-tuning"                    │
│                                                          │
│   ┌──────────── RUN run-0001 ────────────┐               │
│   │  params   {model, temperature, ...}   │               │
│   │  metrics  {faithfulness, cost, ...}   │               │
│   │  artifacts{prompt.txt, eval.json}     │               │
│   │  tags     {owner, dataset, git_sha}   │               │
│   │  status   FINISHED                    │               │
│   └───────────────────────────────────────┘               │
│   ┌──────────── RUN run-0002 ────────────┐               │
│   │  ...                                  │               │
│   └───────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────┘
```

| Concept | What it is | GenAI example |
|---|---|---|
| **Experiment** | A named bucket grouping related runs | `rag-faithfulness-tuning` |
| **Run** | One execution with one config | `run-0002`, temp 0.0 + reranker |
| **Param** | An *input* — set once, doesn't change mid-run | `model=gpt-4o`, `temperature=0.0` |
| **Metric** | An *output* — a measured number | `faithfulness=0.93`, `cost_usd=0.041` |
| **Artifact** | A file/blob produced by the run | rendered prompt, eval report, traces |
| **Tag** | Free-form metadata for filtering | `owner=ana`, `git_sha=ab12cd`, `dataset=v3` |
| **Status** | Lifecycle state | `RUNNING → FINISHED / FAILED` |

The key distinction beginners miss: **params are inputs you choose; metrics are outputs you measure.** A temperature is a param; a latency is a metric. This split is what makes "best run by metric, grouped by param" queries possible.

---

## 3. What to Log for GenAI

The value of a tracker is only as good as what you log. For GenAI, log enough to *reproduce* the run and *judge* it on every axis that matters.

```
   ┌──────────── PARAMS (inputs) ───────────┐
   │ model, model_version, temperature,      │
   │ top_p, max_tokens, prompt_id,           │
   │ retriever, chunk_size, top_k, dataset   │
   └─────────────────────────────────────────┘
   ┌──────────── METRICS (outputs) ─────────┐
   │ faithfulness, answer_relevance,         │
   │ context_precision, cost_usd, latency_ms,│
   │ input_tokens, output_tokens, pass_rate  │
   └─────────────────────────────────────────┘
   ┌──────────── ARTIFACTS (blobs) ─────────┐
   │ rendered_prompt.txt, eval_report.json,  │
   │ per_example_traces.jsonl, confusion.csv │
   └─────────────────────────────────────────┘
```

A minimal logging loop looks like this:

```python
run_id = tracker.start_run(
    name="rag-reranker",
    params={"model": "gpt-4o", "temperature": 0.0, "top_p": 1.0, "top_k": 5},
)

# After running your eval set offline:
tracker.log_metric(run_id, "faithfulness", 0.93)
tracker.log_metric(run_id, "answer_relevance", 0.88)
tracker.log_metric(run_id, "cost_usd", 0.041)
tracker.log_metric(run_id, "latency_ms", 1500)

tracker.log_artifact(run_id, "prompt.txt", rendered_prompt)
tracker.log_artifact(run_id, "eval_report.json", report_json)
tracker.end_run(run_id, status="FINISHED")
```

Guidance on what goes where:

| Signal | Log as | Why |
|---|---|---|
| Prompt template id / version | param + artifact | param to compare, artifact to reproduce exact text |
| Temperature, top_p, max_tokens | params | sampling inputs you set |
| Faithfulness, relevance scores | metrics | the quality numbers you optimize |
| Cost, latency, token counts | metrics | the budget/SLO numbers you constrain |
| Eval dataset name + hash | tag/param | guarantees apples-to-apples comparison |
| Git commit of your code | tag | ties the run to reproducible code |

---

## 4. MLflow vs Weights & Biases vs Neptune

These are the three trackers you will most often meet. They overlap heavily; the choice usually comes down to hosting model and ecosystem.

| Dimension | MLflow | Weights & Biases (W&B) | Neptune |
|---|---|---|---|
| **Model** | Open source, self-host or managed | SaaS (managed), self-host tier | SaaS, self-host tier |
| **Tracking API** | `mlflow.log_param/metric/artifact` | `wandb.log({...})` | `run["..."] = value` |
| **Model registry** | Built-in (stages/aliases) | Built-in (Artifacts + registry) | Built-in (model registry) |
| **UI / dashboards** | Functional, no-frills | Rich, interactive, sharable | Rich, metadata-focused |
| **GenAI / LLM features** | MLflow Tracing, prompt eval | Weave (LLM tracing & eval) | LLM logging integrations |
| **Best for** | Teams wanting OSS + full control | Fast collaboration, rich viz | Heavy metadata, many runs |

```
   Your training/eval code
            │  one logging call
   ┌────────┼──────────────────────────────┐
   ▼        ▼                               ▼
 MLflow    W&B                            Neptune
 (OSS,     (SaaS,                         (SaaS,
  self-     collab +                       metadata
  hosted)   dashboards)                    store)
```

Practical note: the *concepts* (run, param, metric, artifact, registry) transfer 1:1 between them. The exercise in this subtopic implements that shared model in pure Python, so it is intentionally tool-agnostic. See [exercise_01.md](exercise_01.md).

---

## 5. Comparing Runs and Picking the Best

Once runs are logged, the payoff is comparison. A run table lets you sort and filter on any metric:

| run | model | temp | faithfulness ↑ | cost_usd ↓ | latency_ms ↓ |
|---|---|---|---|---|---|
| run-0001 | gpt-4o-mini | 0.2 | 0.81 | 0.012 | 920 |
| run-0002 | gpt-4o | 0.0 | **0.93** | 0.041 | 1500 |
| run-0003 | llama-3-8b | 0.3 | 0.70 | **0.003** | **410** |

The single most important subtlety is **metric direction**:

- **Maximize** quality metrics — faithfulness, answer relevance, pass rate.
- **Minimize** cost metrics — cost_usd, latency_ms, token counts, hallucination rate.

So "best run" is meaningless without a *mode*. `best_run("faithfulness", "max")` returns run-0002; `best_run("cost_usd", "min")` returns run-0003. They are different winners — which is exactly why GenAI selection is a trade-off, not a single ranking.

```python
def best_run(runs, metric, mode="max"):
    if mode not in ("max", "min"):
        raise ValueError("mode must be 'max' or 'min'")
    # Ignore runs that never logged this metric.
    candidates = [r for r in runs if metric in r["metrics"]]
    if not candidates:
        raise ValueError(f"no run logged metric {metric!r}")
    pick = max if mode == "max" else min
    return pick(candidates, key=lambda r: r["metrics"][metric])["run_id"]
```

Two rules this encodes, both of which you will implement in the exercise:

1. **Ignore runs missing the metric.** A run that crashed before logging `faithfulness` must not win the faithfulness comparison just because its value is absent.
2. **Raise when nobody logged it.** Asking for the best `toxicity` when no run measured it is a programming/data error, not a silent `None`.

In practice you rarely pick on a single metric. You either (a) optimize one metric subject to constraints ("max faithfulness where cost_usd < 0.02 and latency_ms < 1000"), or (b) combine into a weighted score. Single-metric selection is the primitive everything else builds on.

---

## 6. The Hand-off to a Model Registry

A winning run is not yet a deployment. The **model registry** is the bridge: it takes the chosen run, registers it as a named, versioned model, and promotes it through stages with approvals and rollback.

```
  Experiment Tracking            Model Registry
  ┌───────────────────┐          ┌───────────────────────────┐
  │ run-0002 wins      │  promote │  rag-assistant            │
  │ faithfulness 0.93  │ ───────► │   v1 ── Archived          │
  │ (source run + cfg) │          │   v2 ── Staging  ◄ tests  │
  └───────────────────┘          │   v3 ── Production ◄ live  │
                                  └───────────────────────────┘
```

| Stage | Meaning | Gate before advancing |
|---|---|---|
| **None / Registered** | Candidate just registered from a run | — |
| **Staging** | Under validation in a prod-like env | Offline evals + smoke tests pass |
| **Production** | Serving live traffic | Approval, canary/A-B results healthy |
| **Archived** | Retired version, kept for rollback | Superseded by a newer Production |

Crucially, the registry stores the **lineage** back to the source run: which experiment, which params, which metrics, which git commit. That is what lets you answer "why is *this* model in production?" months later — and what lets you roll back to the previous version in one step if quality regresses.

```python
# Selecting the winner and simulating the hand-off.
best = tracker.best_run("faithfulness", mode="max")
promotion = {
    "source_run_id": best,
    "selected_metric": "faithfulness",
    "stage": "Production",   # after Staging passes its gates
}
```

This subtopic's exercise includes a small `promote_best` helper that returns exactly such a hand-off dict — the link between tracking and the registry covered in the next subtopics.

---

## Key Takeaways

- **Tracking turns opinions into evidence.** Log every run's config and results so "the new prompt is better" becomes reproducible and auditable.
- **Learn the shared data model:** experiment → run → params (inputs) / metrics (outputs) / artifacts (blobs) / tags. Params are what you set; metrics are what you measure.
- **Log GenAI-specifically:** prompt/temperature/top_p/model as params; faithfulness, answer relevance, cost, latency, and token counts as metrics; rendered prompts and eval reports as artifacts.
- **MLflow, W&B, and Neptune share the same concepts** — choose on hosting model and ecosystem, not on capability gaps.
- **"Best run" requires a direction.** Maximize quality, minimize cost/latency; ignore runs missing the metric and raise when none logged it.
- **The registry is the hand-off.** Promote the winning run through Staging → Production with lineage back to its source run for explainability and one-step rollback.
