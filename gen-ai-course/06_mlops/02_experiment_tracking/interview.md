# Experiment Tracking - Interview Questions

This document contains interview questions and model answers on experiment tracking for GenAI systems — the data model, what to log, comparing and selecting runs, and the hand-off to a model registry.

---

### Q1: What problem does experiment tracking solve, and why is it especially important for GenAI?

**Answer:** Experiment tracking records the configuration, results, and artifacts of every run so that results are reproducible, comparable, and auditable. For GenAI it is critical because:

- **Many interacting knobs** — prompt, system message, model, temperature, top_p, retriever, chunk size — each change the output.
- **Multi-dimensional quality** — there is no single accuracy number; you trade off faithfulness, answer relevance, cost, latency, and token counts.
- **Stochastic, drifting backends** — LLM calls are non-deterministic and providers update models silently, so logging the exact config and outputs is the only reliable way to explain a past result.

Without tracking, "the good prompt" becomes tribal knowledge and you cannot defend why a particular model is in production.

---

### Q2: Explain the core data model: experiment, run, param, metric, artifact, tag.

**Answer:**

| Concept | Definition | GenAI example |
|---|---|---|
| Experiment | Named bucket grouping related runs | `rag-faithfulness-tuning` |
| Run | One execution with one config | `run-0002` (temp 0.0 + reranker) |
| Param | An input you set before the run | `model=gpt-4o`, `temperature=0.0` |
| Metric | An output you measure after the run | `faithfulness=0.93`, `cost_usd=0.041` |
| Artifact | A file/blob the run produces | rendered prompt, eval report, traces |
| Tag | Free-form metadata for filtering | `owner`, `git_sha`, `dataset=v3` |

The pivotal distinction: **params are inputs you choose; metrics are outputs you measure.** That separation is what makes "best metric grouped by param" queries possible.

---

### Q3: What would you log for a RAG eval run specifically?

**Answer:**

- **Params:** model, model_version, temperature, top_p, max_tokens, prompt_id, retriever, chunk_size, top_k, embedding_model, dataset name + hash.
- **Metrics:** faithfulness, answer_relevance, context_precision/recall, cost_usd, latency_ms (p50/p95), input_tokens, output_tokens, pass_rate.
- **Artifacts:** the fully rendered prompt, the eval report JSON, per-example traces (input, retrieved chunks, output, judgment).
- **Tags:** git commit, owner, environment.

Rule of thumb: log enough to *reproduce* the run and to *judge* it on every axis you care about — quality and cost/latency together.

---

### Q4: Why log the prompt both as a param and as an artifact?

**Answer:** As a *param* (e.g. a `prompt_id` or version), it is a short, comparable value you can group and filter runs by. As an *artifact* (the fully rendered text), it captures the exact bytes that were sent — including interpolated variables — so the run is truly reproducible. The param answers "which prompt family?"; the artifact answers "exactly what was sent?".

---

### Q5: What is the difference between a param and a metric, and why does it matter for tooling?

**Answer:** A param is an input fixed for the run (temperature, model); a metric is a measured output that can be a single value or a time series (faithfulness, loss over steps). Tooling treats them differently: params are used for grouping/filtering and are immutable per run, while metrics are aggregated, charted, and used for selection. Mislabeling a metric as a param (or vice versa) breaks comparison queries and dashboards.

---

### Q6: How does `best_run` work, and what edge cases must it handle?

**Answer:** It selects the run with the best value of a metric for a given direction:

1. **Validate the mode** — `max` for quality metrics, `min` for cost/latency; anything else is a `ValueError`.
2. **Filter to runs that logged the metric** — a run that crashed before logging it must be ignored, not treated as 0 or infinity.
3. **Raise if none logged it** — asking for the best of an unrecorded metric is a `ValueError`, not a silent `None`.
4. **Resolve ties deterministically** — e.g. by earliest creation order, so results are reproducible.

```python
def best_run(runs, metric, mode="max"):
    if mode not in ("max", "min"):
        raise ValueError("mode must be 'max' or 'min'")
    candidates = [r for r in runs if metric in r["metrics"]]
    if not candidates:
        raise ValueError(f"no run logged {metric!r}")
    pick = max if mode == "max" else min
    return pick(candidates, key=lambda r: r["metrics"][metric])["run_id"]
```

---

### Q7: Why can't you pick the "best run" on a single metric in practice?

**Answer:** Because GenAI metrics trade off against each other. The most faithful run is often the most expensive and slowest. Real selection either (a) **optimizes one metric subject to constraints** — "max faithfulness where cost_usd < 0.02 and latency_ms < 1000" — or (b) **combines metrics into a weighted score**. Single-metric `best_run` is the primitive these strategies build on, not usually the final shipping decision.

---

### Q8: Compare MLflow, Weights & Biases, and Neptune.

**Answer:**

| Dimension | MLflow | Weights & Biases | Neptune |
|---|---|---|---|
| Hosting | OSS, self-host or managed | SaaS (self-host tier) | SaaS (self-host tier) |
| API style | `mlflow.log_metric(...)` | `wandb.log({...})` | `run["k"] = v` |
| Registry | Built-in | Built-in (Artifacts) | Built-in |
| GenAI features | MLflow Tracing, prompt eval | Weave (LLM tracing/eval) | LLM integrations |
| Strength | Control + open source | Rich collaborative UI | Metadata at scale |

The concepts (run, param, metric, artifact, registry) transfer 1:1; choose on hosting model and ecosystem rather than capability.

---

### Q9: What is the relationship between experiment tracking and a model registry?

**Answer:** They are adjacent stages. Tracking is about *exploration* — recording many runs and comparing them. The registry is about *operationalization* — taking the winning run, registering it as a named, versioned model, and promoting it through stages (Staging → Production) with approvals and rollback. The hand-off carries lineage: the registered version points back to the source run, its params, metrics, and git commit.

---

### Q10: Describe the typical registry stage progression and the gate at each step.

**Answer:**

| Stage | Meaning | Gate to advance |
|---|---|---|
| None/Registered | Candidate just registered from a run | — |
| Staging | Validated in a prod-like environment | Offline evals + smoke tests pass |
| Production | Serving live traffic | Approval + healthy canary/A-B results |
| Archived | Retired, kept for rollback | Superseded by newer Production |

Keeping archived versions is what enables a one-step rollback if a newly promoted model regresses.

---

### Q11: How do you ensure two runs are an apples-to-apples comparison?

**Answer:** Pin and log everything that affects the result *except* the variable under test: the same eval dataset (logged with a name + content hash), the same scoring/judge configuration, the same retriever corpus version, and the same code commit. Then change exactly one thing (e.g. temperature) between runs. If the dataset or judge silently changes, the metric delta is no longer attributable to your change.

---

### Q12: How do you handle the stochasticity of LLM outputs in tracking?

**Answer:** Several complementary tactics:

- **Log the seed and sampling params** (temperature, top_p) so the run is as reproducible as the provider allows.
- **Use temperature 0** for eval runs where you want determinism.
- **Average over multiple samples / a fixed eval set** and log mean plus variance, not a single call.
- **Log per-example traces** so a surprising aggregate can be drilled into.

You record both the central tendency and the spread, because a metric with high variance across runs is not a reliable basis for selection.

---

### Q13: What metadata makes a tracked run reproducible months later?

**Answer:** Git commit SHA of the code, exact model name *and* version, all sampling params, the prompt template id plus the rendered prompt artifact, the eval dataset name + hash, the environment/dependency versions, and the random seed. With these, you can re-run the experiment and expect to recover the recorded metrics (within provider-side drift).

---

### Q14: How does experiment tracking connect to A/B testing and monitoring in production?

**Answer:** Tracking selects the candidate offline; A/B testing and monitoring validate it online. The flow is: pick the best run by offline metrics → register and promote to Staging → canary or A/B test against the current Production model on live traffic → compare the same metrics (now measured online) → promote to Production if healthy, otherwise roll back to the archived version. The registry's lineage ties the live model back to its originating experiment, closing the loop.

---

### Q15: If you had to build a minimal tracker yourself, what would the API be?

**Answer:** The smallest useful surface mirrors MLflow/W&B:

- `start_run(name, params) -> run_id`
- `log_metric(run_id, key, value)` (multiple per run)
- `log_artifact(run_id, name, content)`
- `end_run(run_id, status="FINISHED")`
- `get_run(run_id)` / `list_runs()`
- `best_run(metric, mode)` with `mode` in {max, min}, ignoring runs missing the metric and raising when none logged it
- optionally `promote_best(...)` to simulate the registry hand-off

That is exactly the API built in `exercise.py` / `solution.py` for this subtopic — see [exercise_01.md](exercise_01.md).

---

## Summary

Key experiment-tracking topics:

1. **Why it matters:** reproducibility, comparison, auditability for GenAI's many knobs and fuzzy metrics.
2. **Data model:** experiment → run → params (inputs) / metrics (outputs) / artifacts (blobs) / tags.
3. **What to log:** prompt/temperature/model as params; faithfulness/cost/latency/tokens as metrics; prompts + eval reports as artifacts.
4. **Selection:** best run needs a direction (max quality, min cost); ignore missing-metric runs; raise when none logged it.
5. **Registry hand-off:** promote the winner through Staging → Production with lineage and rollback.

---

## References

- [Experiment tracking tools and docs](references.md)
- [Model registry and concepts](references.md)
