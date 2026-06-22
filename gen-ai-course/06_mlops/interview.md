# MLOps for GenAI — Interview Questions

Interview questions and model answers on MLOps for generative AI: experiment tracking, data/prompt versioning, and pipeline orchestration.

---

## 1. How does MLOps for GenAI differ from classic MLOps?

**Answer:** Classic MLOps versions code + data + model weights and optimizes a fixed metric; GenAI adds **prompts, embeddings, and external model versions** as first-class artifacts, **non-deterministic** outputs needing eval-based (not accuracy) gates, and heavy reliance on **managed foundation models** you don't train. The pipeline still does train/evaluate/register/deploy, but "train" is often "assemble prompt + RAG + fine-tune adapter," and "evaluate" is a golden-set / LLM-judge gate.

| Concern | Classic MLOps | GenAI MLOps |
|---|---|---|
| **What ships** | Code + model weights | Code + model + prompt + index + config |
| **Determinism** | Reproducible by default | Non-deterministic (temperature, model drift) |
| **Quality signal** | Accuracy / F1 | Faithfulness, groundedness, hallucination rate, cost |
| **Failure mode** | Crash / wrong prediction | Plausible-but-wrong answers (silent) |
| **Source of change** | A commit | A new prompt, re-embedded index, or provider model upgrade |
| **Rollback unit** | Model version | Deployable bundle: code + prompt + index + model id |

## 2. What do you track per experiment in a GenAI pipeline?

**Answer:** Inputs (prompt version, model id + version, retrieval config, hyperparameters/adapters), outputs (eval scores: faithfulness/groundedness, task metrics, cost/latency), and lineage (which dataset + code commit produced it). Tools: MLflow / Azure ML experiments (AWS: SageMaker Experiments).

```
┌──────────── PARAMS (inputs) ──────────────┐
│ model, model_version, temperature, top_p, │
│ prompt_id, retriever, chunk_size, top_k,  │
│ dataset_hash, code_commit                 │
└───────────────────────────────────────────┘
┌──────────── METRICS (outputs) ────────────┐
│ faithfulness, answer_relevance,           │
│ context_precision, cost_usd, latency_ms,  │
│ input_tokens, output_tokens, pass_rate    │
└───────────────────────────────────────────┘
┌──────────── ARTIFACTS (blobs) ────────────┐
│ rendered_prompt.txt, eval_report.json,    │
│ per_example_traces.jsonl                  │
└───────────────────────────────────────────┘
```

---

## Senior Deep Dive: MLOps for GenAI

> Senior MLOps roles own reproducibility, eval gates, and the seam between data scientists and the platform/SRE team. The job is to make correct behavior the default path — not a heroic individual effort.

---

### System Design & Scale

#### Q: Design an MLOps platform that serves 50 models/prompts across 10 teams. What are the shared vs per-team components?

**Answer:** The split follows a hub-and-spoke model: shared infrastructure handles governance, cost attribution, and common tooling; per-team components handle autonomy and iteration velocity.

**Shared (platform team owns):**

- **Model and prompt registry** — one source of truth for every versioned artifact, its stage (None → Staging → Production → Archived), and lineage back to the source experiment. In Azure this is Azure ML Model Registry + a custom prompt registry table; on AWS, SageMaker Model Registry plays the same role. Every team promotes into this registry, never into production directly.
- **Eval harness** — a standard evaluation runner that any pipeline can invoke. It holds the golden sets per domain, the LLM-judge prompts, and the pass/fail thresholds. Standardizing this means "eval" means the same thing everywhere.
- **Feature and embedding store** — shared embeddings (e.g. a company-wide Azure AI Search index) that teams pull from rather than rebuild independently. Prevents ten teams maintaining ten copies of the same chunked corpus with drift between them.
- **Observability stack** — centralized logging, token-cost attribution by team, drift dashboards. Azure Monitor + Application Insights; AWS equivalents are CloudWatch + SageMaker Model Monitor.
- **RBAC and cost attribution** — a workspace-per-team model (Azure ML workspaces, SageMaker domains) that gates who can promote to Production, separates cost budgets, and enforces data-access policies.

**Per-team (team owns):**

- Experiment runs and local eval notebooks — teams iterate freely inside their workspace.
- Pipeline definitions (Prefect flows, Dagster assets, or Azure ML pipelines) — each team owns their DAG; the platform provides the shared steps (embed, eval, register).
- Feature engineering specific to their domain.

**Senior framing:** The forcing function for the split is "what breaks if team A changes it and team B didn't know?" Everything in that category is shared. Everything else is a tax on team autonomy if centralized.

| Component | Shared | Per-team |
|---|---|---|
| Prompt/model registry | Yes | |
| Eval harness + golden sets | Yes (golden set curation is per-team) | |
| Embedding store | Yes | |
| Observability & cost | Yes | |
| Experiment runs | | Yes |
| Pipeline definitions | | Yes |
| Data prep & domain logic | | Yes |

---

#### Q: How do you version data, prompts, and embeddings together so any prod behavior is reproducible?

**Answer:** Reproducibility requires a single deployable bundle that pins every artifact to a content-addressed identity. No floating aliases.

**Prompts** live in a prompt registry that records both a human-readable semantic version (e.g. `v2.1.0`) and the SHA-256 of the exact template bytes. The semantic version is for humans and rollback targets; the hash is the ground truth that detects silent edits. Tools: a custom registry table, LangSmith, Langfuse, or PromptLayer all support this pattern.

**Datasets and eval sets** get a canonical hash: `sha256(json.dumps(rows, sort_keys=True))`. This survives serialization differences and lets you assert "same logical data" across machines. Large files stay out of Git — a tiny `.dvc` pointer file (hash + size, ~120 bytes) commits to Git while DVC pushes the actual bytes to Azure Blob Storage (AWS: S3, GCS). `git checkout v3.0 && dvc pull` reconstructs the exact dataset that commit referenced.

**Embedding indexes** are derived artifacts: they depend on the source corpus hash, the chunking config, the embedding model id, and embedding dimensions. Version an index by recording its recipe:

```
index_snapshot_id = sha256(
    docs_hash + chunk_size + chunk_overlap +
    embed_model_id + embed_dim
)
```

Store the actual index snapshot in object storage (Azure Blob / S3) keyed by that id. Re-chunking or swapping the embedder produces a different id automatically — no accidental reuse.

**The deployable bundle** pins all four drivers together:

```
bundle_id = sha256({
    "data":   data_hash,
    "prompt": prompt_hash,
    "model":  "claude-haiku-20260301",  # dated snapshot, not floating alias
    "params": {"temperature": 0, "top_p": 1},
    "code":   git_sha,
    "index":  index_snapshot_id
})
```

The runtime resolves the bundle id to the production artifacts at deploy time. Rollback is "point the stable name at the previous bundle id" — a metadata change, not a redeploy. True bit-for-bit reproduction of LLM outputs additionally requires `temperature=0` (or a fixed seed) and a dated model snapshot rather than a floating alias like `gpt-4o`.

**Senior framing:** The most common reproducibility gap in practice is the index. Teams pin the prompt and the model but leave the index floating. A background re-embed job silently swaps the index and retrieval quality shifts without any experiment run recording it.

---

#### Q: Where does the eval harness live so it gates every promotion at scale?

**Answer:** The eval harness must live in two places simultaneously: as a **pipeline step** inside every training/fine-tune DAG, and as a **CI gate** in the pull-request workflow for prompt changes. Neither alone is sufficient.

**In the pipeline** — after `fine_tune` or `prompt_assemble`, an `evaluate` step runs the candidate bundle against the domain golden set and an LLM-judge. The step emits pass/fail and logs scores to the experiment tracker (MLflow run / Azure ML run). A failed eval kills the DAG before `register` and `deploy` ever run — the quality gate pattern:

```
prepare_data → fine_tune → evaluate ─(fail)─► STOP (nothing registers)
                                    ─(pass)─► register → deploy_canary → promote
```

**In CI** — a GitHub Actions (or Azure DevOps) workflow triggers on every PR that touches a prompt file, runs the eval harness on the golden set, and blocks merge if scores regress below threshold. This catches prompt regressions before they reach the registry.

**Golden sets** must be per-domain and curated. A shared "generic" golden set will pass for prompts it was never designed to test. Each team owns their domain golden set (50–200 examples per task type is typical), versioned alongside the prompt in the registry so eval and prompt are always aligned.

**Offline-to-live drift** is the long-term failure mode: the golden set gradually diverges from the distribution of real queries. Fix it with a **shadow eval** that samples production traces weekly, runs the judge offline, and alerts when offline scores drop faster than the live eval score. This feeds a golden-set refresh loop.

**Senior framing:** The eval harness is only as trustworthy as the golden sets. Teams that own neither the eval harness nor the golden sets have no real gate — they have a ceremony. The platform's job is to make golden-set curation easy enough that teams actually do it.

---

### Trade-offs & Decisions

#### Q: Build vs buy the experiment-tracking/registry layer (MLflow self-host vs Azure ML / SageMaker)?

**Answer:** Lead with the org size and ops maturity question, then the lineage depth question, then lock-in.

**Self-host MLflow** (or W&B Server, Neptune self-hosted) makes sense when: you need full control over data residency (regulated industries), your team already runs Kubernetes and can absorb one more service, or you want to avoid per-seat SaaS costs at scale. The hidden cost is the ops burden: you own upgrades, backups, HA, storage backend configuration, and debugging "why did my artifact go missing." For a 3-person team this is often 20–30% of one engineer's time.

**Azure ML managed experiments** (AWS: SageMaker Experiments) trades control for ops-free operation, native integration with the rest of the cloud MLOps stack (pipelines, model registry, endpoints, cost tracking), and first-class lineage across the full lifecycle — data → experiment run → registered model → endpoint — without custom glue. The cost is per-resource (compute + storage) rather than per-seat for the platform itself, and you accept Microsoft's (or AWS's) data-plane boundary.

**Multi-cloud** is the sharpest lock-in risk: Azure ML's registry format is not portable to SageMaker. MLflow's artifact and run format is open and portable. If multi-cloud portability is a real requirement (not a theoretical one), MLflow wins even with the ops cost.

**Practical decision table:**

| Situation | Recommendation |
|---|---|
| Startup, <5 engineers, single cloud | Azure ML / SageMaker managed |
| Regulated data, on-prem requirement | Self-hosted MLflow on private K8s |
| Multi-cloud, need portability | Self-hosted MLflow + cloud object storage |
| Large org, deep Azure investment | Azure ML — lineage + pipelines integration worth it |

**Senior framing:** "Build vs buy" is really "ops burden vs integration depth." The hidden cost of self-hosting is never the initial setup — it's the 2am pages when the tracking server's Postgres runs out of disk during a big training run.

---

#### Q: When is fine-tuning worth the MLOps cost vs prompt+RAG?

**Answer:** Fine-tuning is worth the additional MLOps complexity when the gains it provides cannot be closed by prompt engineering + retrieval, and when the organization has the data and processes to maintain it over time.

**Start with the data bar:** fine-tuning a LoRA adapter that meaningfully outperforms prompt+RAG typically requires 500–5,000 high-quality labeled examples for the target task, plus a held-out eval set. Below that threshold, few-shot prompting almost always wins on quality and dramatically wins on iteration velocity.

**Latency and cost** are the second driver. A fine-tuned smaller model (e.g. a fine-tuned Phi-3 or Mistral-7B adapter) can match a larger base model's task performance at 3–10× lower inference cost and lower latency. If your SLO requires sub-500 ms P99 and your base model can't hit that, fine-tuning a smaller model is the engineering path.

**Drift maintenance** is the underestimated cost. A fine-tuned model requires: a retraining pipeline, a data labeling process to refresh the training set as the domain changes, a regression eval suite, and a canary/rollback capability. That is a non-trivial MLOps investment. Prompt+RAG shifts that maintenance burden to document ingestion (cheaper) and prompt iteration (faster).

**Eval to justify** — before committing to fine-tuning, run a structured experiment: measure task performance for (a) zero-shot base model, (b) few-shot base model, (c) RAG, (d) fine-tuned. If (c) is within 5% of the business target, don't fine-tune yet. If (c) plateaus and (d) closes the gap, the MLOps cost is justified.

**Senior framing:** Fine-tuning is an MLOps commitment, not just a training decision. The question isn't "can we fine-tune?" but "can we sustain a fine-tuning pipeline over 18 months as the domain drifts?"

---

#### Q: Monorepo of prompts vs per-service prompt ownership?

**Answer:** The real question is: where does prompt review happen, and who absorbs a breaking change?

**Monorepo of prompts** (all prompts in one repo, reviewed centrally) gives: easy cross-team discoverability, consistent versioning discipline enforced by a single CI pipeline, and a single place to audit "what changed this week." The cost is review velocity — a PR that touches a shared system prompt needs sign-off from multiple teams, slowing iteration. Blast radius is high: a bad merge to the shared repo can affect every service simultaneously.

**Per-service prompt ownership** (each service owns its prompts alongside its code) gives: teams iterate at their own pace with no external review dependency, blast radius is limited to one service, and rollback is a service-level operation. The cost is discoverability (finding "all prompts that mention X" requires cross-repo search), consistency drift (teams develop different versioning conventions), and duplicate effort (three teams maintain near-identical summarization prompts independently).

**Hybrid that works at scale:** Keep prompts per-service in their service repo, but require every prompt to be registered into the shared prompt registry (with semantic version + content hash + metadata) as part of CI. The registry becomes the discoverability and audit layer; the service repo remains the ownership layer. Changes to shared system-prompt fragments (e.g., safety guardrails) live in a shared library that services import and pin as a versioned dependency — the same pattern as a shared Python package.

**Senior framing:** The blast radius question is the deciding factor at scale. Monorepo is attractive until the first time a reviewer blocks a prompt PR for an unrelated service, or one bad merge breaks ten services simultaneously.

---

### Failure Modes & Incidents

#### Q: A prompt change passed offline eval but regressed in prod. How do you detect and roll back?

**Answer:** This is one of the most common failure modes in GenAI systems and has a specific detection-and-recovery pattern.

**Detection** requires a live eval signal, not just uptime metrics. The key instrument is a **live golden-set metric**: a subset of production queries (or synthetic traffic that mimics prod distribution) that runs through the LLM-judge on a continuous basis and writes scores to your observability stack. When the score drops more than N% from the pre-change baseline within M minutes of a deploy, the alert fires. Azure Monitor custom metrics or a Datadog monitor work well; the key is that the threshold must be set relative to the pre-deploy baseline, not an absolute value.

**Canary first** is the prevention layer. Any prompt promotion to production should go through a canary: route 5–10% of traffic to the new prompt version while holding 90% on the prior version. Compare live eval scores (and CSAT / thumbs-down signals if available) between the two cohorts for 15–30 minutes before completing the promotion. The offline-to-prod gap often only appears at real query distribution — especially on long-tail inputs the golden set didn't cover.

**Registry rollback** is the recovery operation. Because the registry stores the full bundle id (code + prompt + index + model), rollback is `registry.promote("my-assistant", previous_bundle_id, "Production")` — a metadata change that the serving layer picks up on its next config refresh (typically 30–60 seconds with a polling mechanism). No redeploy needed.

**Root cause** usually falls into one of three categories: (1) the golden set didn't cover the production query distribution — fix by refreshing the golden set with sampled prod traces; (2) the prompt was tested against the wrong model version — fix with bundle-level version pinning; (3) the index changed between offline and prod — fix by including the index snapshot id in the bundle and validating it matches at serve time.

---

#### Q: Training/serving skew in a RAG pipeline — symptoms and fix?

**Answer:** Training/serving skew in RAG manifests as retrieval quality being good at index-build time but degraded at query time, even when the queries look normal.

**Root cause:** The embedding model used to build the index and the embedding model used to encode the query at serve time are different versions — or the same model id but a different underlying checkpoint if the provider silently updated it. Because cosine similarity is computed between the query vector and the index vectors, a mismatch in embedding space means the distance scores are meaningless. The index was built in "language A" and queries arrive in "language B."

**Symptoms:** Retrieval returns semantically unrelated documents for queries that previously retrieved correctly. Faithfulness scores drop even though the generation model is unchanged. A smoke test that re-encodes a known query and checks its nearest neighbors returns unexpected results.

**Fix:** Version pinning at every interface. The index-build pipeline records `embed_model_id` = `text-embedding-3-large:2024-09-01` (a dated snapshot, not `text-embedding-3-large-latest`) in the index recipe. The serving layer reads the index recipe and asserts that the query encoder matches before accepting queries. If they don't match, the serve layer rejects the index and falls back to the prior validated index rather than silently serving skewed results.

**Prevention checklist:**

1. Pin embedding model versions by dated snapshot id in both the pipeline and the serving config.
2. Store the embedding model id in the index metadata and validate at serve-time startup.
3. Add a canary smoke test to the inference pipeline: embed a fixed probe query, retrieve top-1, assert it matches the expected document.
4. Use DVC (or Azure ML dataset versioning) to snapshot the index at build time so you can replay any past serve configuration.

**Senior framing:** This failure is nearly always caused by a "helpful" abstraction — a model alias like `text-embedding-ada-002` that the provider updates without notification. The fix is not to avoid abstractions but to resolve them to immutable ids at artifact creation time and record what you resolved to.

---

#### Q: Silent model upgrade by the provider broke output format. Prevention?

**Answer:** Provider model updates are the most common source of silent regressions in GenAI production systems. A model that returns well-formed JSON in one checkpoint may start returning JSON with trailing comments, or switch from numbered to bulleted lists, in a subsequent checkpoint — with no breaking change notification.

**Pin the model version.** Every call to a managed model must use a dated snapshot id, never a floating alias. `claude-haiku-20260301` instead of `claude-haiku`. `gpt-4o-2024-08-06` instead of `gpt-4o`. The registry bundle stores the pinned id and the serving layer passes it through; it is never resolved at serve time to "latest." This is the single most effective prevention.

**Contract tests on output format.** A contract test encodes the expected output schema and runs as part of CI on every dependency upgrade. For JSON output: parse the response and validate against a Pydantic or JSON Schema model. For structured lists: assert that section headers are present and in the expected order. These tests run against a fixed prompt + fixed input (a golden input/output pair) so they catch format regressions before the code ships.

**Schema validation at the inference boundary.** The serving layer validates every LLM response against the expected schema before returning it to the caller. A validation failure triggers a fallback (retry with a stricter format instruction, or return a structured error) rather than passing malformed output downstream where it will cause a harder-to-diagnose failure.

**Model upgrade workflow.** When a new model snapshot is available: (1) update the bundle in a branch, (2) run the full eval harness + contract tests in CI, (3) run a canary against production traffic with the new model, (4) only promote to Production after the canary's eval scores match the baseline within tolerance. Treat provider model upgrades the same as first-party code changes — they go through the same gate.

**Senior framing:** The engineering discipline here is to treat the provider model as an external dependency that can break your API contract, identical to a third-party library upgrade. You wouldn't merge a `pip install --upgrade` without a test run; don't upgrade a model version without one either.

---

### Leadership & Behavioral

#### Q: How do you get data scientists to adopt the pipeline instead of notebooks?

**Answer:** Mandate without golden-path tooling produces resentment and workarounds. The sequence that works is: build the paved road first, then make it easier to walk the road than to go off-road.

**Build the golden path.** The pipeline must provide a clearly better experience than a notebook for the specific things data scientists care about: seeing results quickly, comparing runs, not losing work. This means: one-command pipeline invocation (`python run_pipeline.py --experiment rag-v2`), automatic experiment logging without boilerplate, a UI that shows run comparison in seconds. If the pipeline requires ten configuration files and a Kubernetes context, adoption will be zero regardless of mandates.

**Incremental migration, not big-bang.** Start by wrapping the existing notebook in a pipeline scaffold that calls the notebook as a step. The scientist sees their workflow unchanged but now gets experiment tracking and artifact lineage for free. In the next iteration, move data loading to a pipeline step. The migration happens in small, non-disruptive increments.

**Paved-road components.** Extract the most common operations (embed a corpus, run the eval harness, log to the registry) into shared pipeline components that teams import. When the shared component is five lines and the bespoke notebook cell is fifty, the economics favor the pipeline.

**Measure adoption.** Track the ratio of registered model versions that have an associated experiment run (lineage completeness rate). Start at 0%, set a team-level goal of 80% in 90 days, review in retrospective. Making the metric visible — per team, shown at engineering all-hands — creates social pressure without top-down mandate. Teams that hit 80% first get featured as the case study; teams at 10% get a support offer from the platform team.

**Senior framing:** The job title is MLOps engineer, not MLOps police. If adoption is low, the pipeline isn't good enough yet. Fix the pipeline, not the scientists.

---

#### Q: Tell me about driving a reproducibility standard across teams (STAR).

**Answer:**

**Situation:** I joined a team where four product teams were each running their own RAG pipeline experiments with no shared tooling. Every team had a different convention for logging eval results — some in spreadsheets, some in Weights & Biases, one in a Confluence page. When a production quality regression occurred, it took three days to identify which prompt version was running and which index version it was paired with. Audit requests from compliance took a week to answer.

**Task:** My remit was to define and drive adoption of a reproducibility standard — a minimum bar for every team that would make any production artifact traceable back to the experiment that produced it, within one business day.

**Action:** I started by shadowing two teams for a week to understand their real workflows rather than the idealized version. The core blocker was not that people didn't care about reproducibility — it was that logging lineage added 30–45 minutes per experiment because of setup friction. I drafted a one-page standard (data hash + prompt hash + model id + code commit = bundle id) and built a thin Python library that computed and logged the bundle id in three lines of code. I ran a workshop with tech leads from all four teams, incorporated their feedback on the standard, and got sign-off from the engineering director to make the library a required dependency in the shared requirements.txt. I added a CI lint check that failed if an experiment run was logged without a bundle id. I then ran office hours for two weeks to unblock adoption.

**Result:** Adoption reached 85% of new experiment runs within 60 days, measured by the lineage completeness metric I had set up. The next production regression was traced to its source experiment and rolled back within 2 hours instead of 3 days. The compliance team reduced their audit preparation time from one week to four hours. The library became a module in the internal developer platform and was adopted by two other business units outside my original scope.

---

> **Staff/Principal stretch:** You're asked to set a 2-year MLOps strategy as the org scales from 3 to 30 models. What do you centralize first and why?

**Answer:** Centralize in the order of blast-radius and irreversibility: the registry first, the eval harness second, the observability stack third.

**Year 1, Q1–Q2 — Model and prompt registry.** At 3 models you can keep mental state about what's in prod. At 10 you cannot. The registry is the single highest-leverage investment because it is the foundation everything else depends on: pipelines promote into it, eval gates reference it, rollback uses it. Without a registry, centralized eval and centralized observability are impossible — you have nothing to anchor metrics to. Start with the simplest viable registry (a table with artifact name, version, stage, bundle id, and lineage pointer) and iterate; the shape matters more than the features. Azure ML Model Registry or MLflow Registry both work; the important thing is that all teams use the same one. Time investment: one engineer for 8 weeks.

**Year 1, Q3–Q4 — Eval harness and golden-set discipline.** With a registry in place, you can now gate promotions. Build the shared eval runner, establish the golden-set schema, and help each team seed their domain golden set. The harness runs as a pipeline step and as a CI check. This is the highest-leverage quality investment: it is far cheaper to catch a regression before it reaches production than to debug it after. Target: 100% of promotions to Production run through the eval gate by end of Year 1.

**Year 2 — Shared observability and embedding store.** Once the registry and eval are working, the next bottleneck is usually observability fragmentation: each team has its own dashboards, cost attribution is unclear, and detecting cross-team regressions requires manual coordination. Centralize into a shared observability stack (Azure Monitor / OpenTelemetry + a cost attribution tag standard). Simultaneously, audit whether teams are rebuilding the same embedding indexes independently; if so, stand up a shared embedding store with index snapshot versioning.

**What not to centralize:** Pipeline definitions (team autonomy), domain-specific data prep (teams know their data), and experiment iteration workflows (notebooks are fine for exploration). Centralizing these creates a platform bottleneck and kills velocity. The principle: centralize what governs correctness and auditability; leave autonomy where speed is the value.

---

## Summary

MLOps for GenAI extends classic MLOps with prompt/embedding/model-version artifacts, eval-based gates, and managed-model reliance. Senior owners build the paved road — registry, eval harness, reproducible bundles — and make adoption the default.

## References

- MLflow — experiment tracking & model registry: https://mlflow.org/docs/latest/index.html
- Azure Machine Learning — pipelines & registries: https://learn.microsoft.com/azure/machine-learning/
- DVC — data/artifact versioning: https://dvc.org/doc
