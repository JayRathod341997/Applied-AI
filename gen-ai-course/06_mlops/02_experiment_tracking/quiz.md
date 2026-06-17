# Quiz

## Question 1

In experiment-tracking terminology, what is the difference between an *experiment* and a *run*?

A) They are synonyms used interchangeably
B) An experiment is one execution; a run groups many experiments
C) An experiment is a named bucket grouping related runs; a run is one concrete execution with one config
D) An experiment stores metrics; a run stores only artifacts

---

**Answer: C**

An experiment is the question or named grouping (e.g. "rag-faithfulness-tuning"), while a run is a single attempt at answering it — one configuration, one eval pass, one set of recorded numbers. Many runs live under one experiment.

---

## Question 2

You log `temperature=0.0` and `faithfulness=0.93` for a run. Which is a *param* and which is a *metric*?

A) Both are params
B) `temperature` is a param (input), `faithfulness` is a metric (output)
C) `temperature` is a metric, `faithfulness` is a param
D) Both are metrics

---

**Answer: B**

Params are inputs you choose before the run (temperature, model, top_p, prompt id). Metrics are outputs you measure after running (faithfulness, cost, latency). This split is what enables queries like "best metric grouped by param".

---

## Question 3

For a GenAI run, which item is best logged as an *artifact* rather than a param or metric?

A) The temperature value
B) The measured cost in USD
C) The fully rendered prompt text and the eval report file
D) The model name

---

**Answer: C**

Artifacts are files/blobs the run produces — rendered prompts, eval reports, per-example traces. Scalars like temperature (param) and cost (metric) are not artifacts, though a prompt *id* may also be logged as a param for easy comparison.

---

## Question 4

Why does calling `best_run("faithfulness")` without specifying a mode (max/min) make the result ambiguous for GenAI metrics?

A) Because faithfulness is always minimized
B) Because some metrics should be maximized (quality) and others minimized (cost/latency), so direction must be explicit
C) Because the tracker cannot read floats
D) Because faithfulness is a param, not a metric

---

**Answer: B**

Selection requires a direction. Quality metrics (faithfulness, relevance) are maximized while cost, latency, and token counts are minimized. Without a mode, "best" is undefined, so a tracker takes `mode` in {"max", "min"}.

---

## Question 5

A run crashed before it logged `faithfulness`. What should `best_run("faithfulness", "max")` do with it?

A) Treat its missing value as 0.0 and possibly let it win
B) Treat its missing value as infinity
C) Ignore the run entirely, considering only runs that logged the metric
D) Raise an error because one run is incomplete

---

**Answer: C**

Runs that never logged the requested metric must be filtered out before comparison. Substituting 0 or infinity would distort the ranking; the correct behaviour is to consider only runs that actually recorded the metric.

---

## Question 6

What should `best_run("toxicity", "min")` do if *no* run ever logged a `toxicity` metric?

A) Return None
B) Return the first run
C) Raise a ValueError
D) Return an empty string

---

**Answer: C**

Asking for the best of a metric that no run measured is a data/programming error, not a valid silent result. Raising `ValueError` surfaces the problem instead of returning a misleading `None` or arbitrary run.

---

## Question 7

Given runs A (cost 0.012), B (cost 0.041), C (cost 0.003), which does `best_run("cost_usd", "min")` return?

A) Run A
B) Run B
C) Run C
D) It raises because cost should be maximized

---

**Answer: C**

Cost is a metric you minimize, so the best (lowest) cost is run C at 0.003. Note this is a different winner than the highest-faithfulness run — GenAI selection is a trade-off across competing metrics.

---

## Question 8

Which statement about MLflow, Weights & Biases, and Neptune is most accurate?

A) Only MLflow has a model registry
B) They use completely different data models, so concepts do not transfer
C) They share the same core concepts (run, param, metric, artifact, registry); the choice is mostly hosting model and ecosystem
D) W&B is open source and self-hosted only

---

**Answer: C**

All three expose the same mental model — runs with params, metrics, artifacts, plus a model registry. They differ in hosting (MLflow is OSS/self-host; W&B and Neptune are primarily SaaS) and UI/ecosystem, not in the fundamental abstractions.

---

## Question 9

In a model registry, what is the typical stage progression for a promoted model version?

A) Production → Staging → Archived
B) None/Registered → Staging → Production → Archived
C) Staging → Production → Staging
D) Archived → Production → None

---

**Answer: B**

A version is first registered, validated in Staging (offline evals + smoke tests), promoted to Production (with approval and canary/A-B checks), and later Archived when superseded — while remaining available for one-step rollback.

---

## Question 10

What is the main reason a registry stores lineage back to the source run?

A) To make the UI look richer
B) To answer "why is this model in production?" and enable reproducible rollback to a prior version
C) To delete the original experiment
D) To increase inference speed

---

**Answer: B**

Lineage links a registered model version to the run, params, metrics, and git commit that produced it. That traceability is what lets teams justify the production choice later and roll back deterministically when quality regresses.
