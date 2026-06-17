# MLOps for GenAI - Interview Questions

This document contains interview questions and answers covering Module 6: MLOps Foundations for GenAI Systems — why GenAI needs MLOps, how it relates to DevOps and LLMOps, the end-to-end lifecycle, the reference architecture, and the artifact/registry model.

---

## 1. MLOps Foundations

### Q1: Why do GenAI and agentic systems require MLOps?

**Answer:** A clever prototype is not a production system, and GenAI widens that gap because behaviour is *data-defined* — it depends on artifacts that ordinary software pipelines never tracked. MLOps needs specific to GenAI:

- **Model management** — multiple model artifacts (LLM, embedding model, often a reranker), each versioned and swappable.
- **Data & index versioning** — the documents and the vector index built from them define what the system "knows".
- **Prompt management** — prompts are code: a one-word edit can regress quality, so they need versioning, testing, and rollback.
- **Agent workflows** — multi-step, stateful systems are harder to test and reproduce than a single call.
- **Cost tracking** — per-request, token-based cost that can spike 10×.
- **Quality monitoring** — hallucinations and retrieval quality fail *silently*, so quality is a first-class metric.

---

### Q2: How does MLOps differ from DevOps in the context of GenAI?

**Answer:** MLOps keeps everything DevOps does and adds the model, data, and prompt lifecycle on top.

| Aspect | DevOps | MLOps for GenAI |
|--------|--------|-----------------|
| Versioning | Code | Code + Models + Prompts + Embeddings |
| Testing | Unit/Integration | Quality metrics + Behaviour |
| Deployment | Rolling | A/B + Gradual |
| Monitoring | Uptime | Quality + Drift + Cost |
| Rollback | Code | Prompt/Model/Index version changes |

The crucial point in an interview: you do **not** discard DevOps. CI/CD, infrastructure-as-code, and observability still apply — MLOps layers model/data/prompt concerns and quality metrics over them.

---

### Q3: Explain the relationship between DevOps, MLOps, and LLMOps.

**Answer:** They are **nested layers**, not competitors:

- **DevOps** — automate software delivery: code, build, CI/CD, infra, logs.
- **MLOps** ⊃ DevOps — add models, datasets, experiments, and drift to the picture.
- **LLMOps** ⊃ MLOps — specialise for large language models: prompts, tokens, eval/LLM-as-judge, guardrails, semantic caching.

Each layer inherits the practices below it. LLMOps does not replace MLOps; it is MLOps tuned for the realities of LLMs (huge models, token economics, prompts as first-class artifacts).

---

### Q4: What is the end-to-end lifecycle for GenAI systems?

**Answer:** A loop, not a one-way pipeline:

1. **Data collection** — gather documents, logs, labels.
2. **Preprocessing & embedding** — clean, chunk, embed, index.
3. **Model/prompt development** — pick models, write and tune prompts.
4. **Evaluate & validate** — score on a golden set, run judges, gate quality.
5. **Deployment** — staged rollout (dev → staging → prod).
6. **Monitoring** — track quality, cost, and drift.
7. **Iteration** — feed findings back into data and prompts.

The **feedback edges** (monitoring → iteration → back into development) are what make it a lifecycle. MLOps is what makes that loop fast, safe, and repeatable.

---

### Q5: What does an enterprise MLOps reference architecture look like?

**Answer:** Separate the *control plane* (build/version/govern) from the *runtime plane* (serve), drawn as layers:

```
┌─────────────────────────────────────┐
│  Experimentation (tracking, evals)  │
├─────────────────────────────────────┤
│  Artifact / Registry (model+prompt  │
│  versions, stages)                  │
├─────────────────────────────────────┤
│  Pipeline / Orchestration           │
│  (build, train, embed, deploy)      │
├─────────────────────────────────────┤
│  Serving / Runtime (gateway, LLM,   │
│  retrieval, cache)                  │
├─────────────────────────────────────┤
│  Observability (metrics, drift, cost)│
└─────────────────────────────────────┘
```

The **registry is the hinge**: experimentation produces candidates, the registry promotes them to Staging/Production, pipelines deploy promoted versions, and observability feeds quality data back to experimentation.

---

### Q6: What is a "silent failure" in GenAI, and why does it change how you do MLOps?

**Answer:** Ordinary software fails loudly — a crash or a 5xx you can alert on. A GenAI model can **hallucinate**: return a confident, well-formed, *wrong* answer with no exception raised. Because the failure is invisible to infra-level monitoring, GenAI MLOps must add *quality* signals — faithfulness, hallucination rate, retrieval quality, LLM-as-judge scores — and gate releases on them, not just on uptime.

---

## 2. Artifacts, Registry & Promotion

### Q7: What counts as a "versioned artifact" in a GenAI system?

**Answer:** Anything whose change alters system behaviour:

- **Code** — application logic (Git).
- **Models** — LLM and embedding model versions (model registry).
- **Prompts** — templates and system prompts (prompt registry/version control).
- **Datasets** — document corpora and eval/golden sets (data versioning).
- **Embeddings / indexes** — vector index snapshots tied to a model + chunking config.
- **Config** — temperature, top_p, chunk size, retrieval k.

A reproducible release pins *all* of these together, not just the code commit.

---

### Q8: How does stage promotion (None → Staging → Production) work, and why is it useful?

**Answer:** A registry stores immutable, numbered versions and records which version holds each **stage**: `None`, `Staging`, `Production`, `Archived`. Promotion moves a version to a stage and **demotes** whoever currently holds it (typically to `Archived`), so exactly one version occupies a stage.

The benefit: the runtime addresses artifacts by **name + stage** (e.g. "the Production `support-prompt`"), giving a stable pointer while the version underneath changes safely. This decouples *release* from *redeploy*.

---

### Q9: How do you roll back a bad prompt or model release with a registry?

**Answer:** Rollback is just **promoting the previous version back to Production**. Because the runtime resolves `name + Production stage` at request time, pointing Production at version N-1 instantly restores the old behaviour — no code change, no redeploy, no rebuild. This is why stages plus immutable versions are so powerful: rollback is a metadata operation, and the full version history stays auditable.

---

### Q10: Why address artifacts by name + stage instead of by a fixed version number?

**Answer:** Hard-coding a version (`support-prompt:v4`) couples the runtime to a specific artifact and forces a code change for every release or rollback. Addressing by `name + stage` (`support-prompt @ Production`) gives the runtime a **stable address** whose target the registry controls. Releasing, A/B testing, and rolling back all become registry operations rather than deployments.

---

## 3. RAG, Versioning & Platforms

### Q11: How do RAG pipelines fit into MLOps?

**Answer:** RAG adds several pipelines that all need MLOps discipline:

- **Data pipeline** — document loading, cleaning, chunking.
- **Embedding pipeline** — generate and store embeddings; the embedding *model version* matters.
- **Retrieval tuning** — experiment with chunk sizes, k, rerankers (track as experiments).
- **Index management** — version vector indexes; an index is only valid for the embedding model that built it.
- **Prompt management** — version the retrieval-augmented prompts.

A subtle but important rule: **the index version is bound to the embedding-model version** — change the embedder and you must re-embed and re-index.

---

### Q12: What are the main cloud-native MLOps platforms?

**Answer:**

- **AWS SageMaker** — end-to-end ML platform (pipelines, registry, deployment).
- **Azure ML** — Microsoft's MLOps/GenAIOps solution.
- **Google Vertex AI** — GCP's managed ML platform.
- **MLflow** — open-source experiment tracking + model registry (cloud-agnostic).
- **Weights & Biases** — experiment tracking and model management.
- **DataRobot** — AutoML / enterprise ML platform.

For most teams, adopting one of these beats building registries and pipelines from scratch — they provide versioning, stages, and lineage out of the box.

---

### Q13: What do you version in a GenAI system, and with which tool?

**Answer:**

| Artifact | Tool / mechanism |
|--------|------------------|
| Code | Git |
| Models | Model registry (MLflow, SageMaker, Vertex) |
| Prompts | Prompt registry / Git + content hash |
| Embeddings & indexes | Index snapshots, DVC, content hashing |
| Datasets | DVC / data versioning |
| Agent graphs | Versioned graph definitions (e.g. LangGraph state graphs) |

The unifying idea is **content-addressable identity** for large/binary artifacts and **named, staged versions** for things the runtime resolves at request time.

---

### Q14: What are the key metrics to track in GenAI MLOps?

**Answer:**

- **Operational** — latency (p50/p95/p99), throughput, uptime, error rate.
- **Quality** — faithfulness, answer relevance, retrieval quality, hallucination rate.
- **Cost** — per-request, per-user, daily, and monthly token spend.
- **Business** — task completion rate, user satisfaction, deflection rate.

The differentiator from DevOps is that *quality* and *token cost* are first-class metrics, not afterthoughts.

---

### Q15: How do you implement continuous deployment for GenAI safely?

**Answer:**

1. **Test prompts** — automated regression against a golden set, with LLM-as-judge where needed.
2. **Quality gates** — block promotion if eval metrics regress beyond a threshold.
3. **Staged rollout** — dev → staging → prod via registry stage promotion.
4. **Feature flags** — gate new behaviour for controlled exposure.
5. **A/B testing** — compare prompt/model versions on live traffic.
6. **Monitoring + auto-rollback** — watch quality/cost; roll back by re-promoting the previous version if metrics degrade.

---

### Q16: What is the difference between training and inference in GenAI, from an MLOps view?

**Answer:**

| Aspect | Training / fine-tuning | Inference |
|--------|----------|-----------|
| Frequency | Occasional | Continuous |
| Cost | High (one-time, GPU-heavy) | Lower per call, ongoing |
| Latency | Not critical | Critical |
| GPU needed | Yes | Often via API |
| MLOps focus | Reproducible pipelines, experiment tracking | Serving, scaling, monitoring, cost |

Many GenAI teams do little or no training — they use hosted models — so their MLOps weight shifts toward prompts, retrieval, serving, and monitoring rather than training pipelines.

---

### Q17: A team has a working notebook prototype. What are the first MLOps steps to make it production-ready?

**Answer:** A pragmatic ordering:

1. **Get artifacts under version control** — code in Git, prompts and config in a registry, datasets/indexes content-hashed.
2. **Build an eval/golden set** so you can measure quality and catch regressions.
3. **Introduce a registry with stages** so releases and rollbacks are metadata changes.
4. **Automate the build/deploy pipeline** (orchestrate ingest → embed → index → deploy).
5. **Add observability** — latency, cost, and quality metrics with alerting.
6. **Close the loop** — feed production findings back into data and prompts.

Start with versioning and evaluation; they unlock safe iteration, which is the whole point of MLOps.

---

## Summary

Key MLOps foundations covered:

1. **Why MLOps for GenAI** — behaviour is data-defined; version more than code.
2. **DevOps ⊂ MLOps ⊂ LLMOps** — nested, cumulative layers.
3. **The lifecycle** — a loop from data to deploy to monitor to iterate.
4. **Reference architecture** — experimentation, registry, pipelines, serving, observability, with the registry as the hinge.
5. **Artifacts, stages, promotion** — immutable versions addressed by name + stage; rollback is metadata.

---

## References

See [references.md](./references.md) for curated MLOps and GenAI lifecycle resources (Google MLOps, MLflow, AWS/Azure/GCP platforms, and more).
