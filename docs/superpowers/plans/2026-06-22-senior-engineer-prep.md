# Per-Module Senior Deep Dives Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a uniform "Senior Deep Dive" section to the module-level `interview.md` of all 14 GenAI teaching modules (directories 01–13, including both `06_langgraph` and `06_mlops`; excluding `14_ai_projects`).

**Architecture:** Each deep dive uses a fixed 4-block template — System Design & Scale · Trade-offs & Decisions · Failure Modes & Incidents · Leadership & Behavioral — plus one Staff/Principal stretch box. Modules that already have a Senior Deep Dive (01, 03, 10, 12) are restructured to the template with existing content preserved. Modules with no `interview.md` (06_mlops, 07, 09, 13) get a new file; `08_cicd` gets a new module-level file holding only the cross-cutting deep dive. Cross-references are then added to the course README and master interview guide.

**Tech Stack:** Markdown only. Verification is structural (grep for the four block headers + the stretch marker) plus a link/anchor check — no code, no test runner.

**Spec:** `docs/superpowers/specs/2026-06-22-senior-engineer-prep-design.md`

---

## Shared Reference (read before every content task)

### The template (paste and fill — keep headings verbatim for verification)

```markdown
## Senior Deep Dive: <Module Topic>

> <1–2 sentences: why senior/staff interviews probe this area for this module.>

### System Design & Scale

#### Q: <question>

**Answer:** <punchline first, then justification. Tables/ASCII only where they clarify.>

<2–4 Q&A here>

### Trade-offs & Decisions

<2–4 Q&A here, same Q/Answer format>

### Failure Modes & Incidents

<2–4 Q&A here>

### Leadership & Behavioral

<2–3 Q&A here>

> 🎯 **Staff/Principal stretch:** <one question on org-level influence, multi-year strategy, or build-vs-buy at company scale, followed by a model answer.>
```

### Content conventions (apply to every answer)

- Lead each answer with the conclusion, then justify. Reuse the existing `**Answer:**` / `**Senior framing:**` call-out style seen in `01_generative_ai/interview.md`.
- Every Q&A must be module-specific and name the module's real tools/patterns/subtopics — no generic "what is a senior engineer" filler.
- Cloud examples: **Azure-primary, AWS-secondary**, name the equivalent in passing.
- Tables/ASCII diagrams only where they clarify (capacity math, decision matrices, failure flows).
- Staff stretch box marker must be exactly: `> 🎯 **Staff/Principal stretch:**`.

### Definition of Done (per module)

The module's `interview.md` contains, in order: `## Senior Deep Dive:`, then the four headers `### System Design & Scale`, `### Trade-offs & Decisions`, `### Failure Modes & Incidents`, `### Leadership & Behavioral`, then a line containing `🎯 **Staff/Principal stretch:**`. The section sits **before** any `## Summary`/`## References` section if one exists.

### Reusable verification command (run from `gen-ai-course/`, substitute the path)

```bash
f="01_generative_ai/interview.md"
grep -c "^## Senior Deep Dive:" "$f"            # expect 1
grep -c "^### System Design & Scale" "$f"        # expect 1
grep -c "^### Trade-offs & Decisions" "$f"       # expect 1
grep -c "^### Failure Modes & Incidents" "$f"    # expect 1
grep -c "^### Leadership & Behavioral" "$f"      # expect 1
grep -c "🎯 \*\*Staff/Principal stretch:\*\*" "$f"  # expect 1
```

All six counts must be `1`. Then skim the section once for quality (answers lead with a conclusion; module-specific; no TODO/TBD).

---

## Group A — New `interview.md` files (no existing file)

These four tasks create a complete `interview.md` (intro → a few standard Q&A → the Senior Deep Dive → Summary → References), following the layout of `02_langchain/interview.md`.

### Task 1: 06_mlops — create interview.md + deep dive

**Files:**
- Read first: `gen-ai-course/06_mlops/README.md`, and the `concepts.md` under `01_mlops_genai`, `02_experiment_tracking`, `03_data_prompt_versioning`, `04_pipeline_orchestration`.
- Create: `gen-ai-course/06_mlops/interview.md`

- [ ] **Step 1: Read module context**

Read the README and the four subtopic `concepts.md` files listed above so questions name real tools (experiment tracking, prompt/data versioning, pipeline orchestration).

- [ ] **Step 2: Write the file skeleton + standard Q&A**

Create `interview.md` with this opening (then the deep dive in Step 3):

```markdown
# MLOps for GenAI — Interview Questions

Interview questions and model answers on MLOps for generative AI: experiment tracking, data/prompt versioning, and pipeline orchestration.

---

## 1. How does MLOps for GenAI differ from classic MLOps?

**Answer:** Classic MLOps versions code + data + model weights and optimizes a fixed metric; GenAI adds **prompts, embeddings, and external model versions** as first-class artifacts, **non-deterministic** outputs that need eval-based (not accuracy-based) gates, and a heavier reliance on **managed foundation models** you don't train. The pipeline still does train/evaluate/register/deploy, but "train" is often "assemble prompt + RAG + fine-tune adapter," and "evaluate" is a golden-set / LLM-judge gate.

## 2. What do you track per experiment in a GenAI pipeline?

**Answer:** Inputs (prompt version, model id + version, retrieval config, hyperparameters/adapters), outputs (eval scores: faithfulness/groundedness, task metrics, cost/latency), and lineage (which dataset + code commit produced it). Tools: MLflow / Azure ML experiments (AWS: SageMaker Experiments).
```

- [ ] **Step 3: Append the Senior Deep Dive**

Append the template with these exact questions and answer-content requirements:

- `## Senior Deep Dive: MLOps for GenAI`
- Framing: senior MLOps roles own reproducibility, eval gates, and the seam between data scientists and platform/SRE.
- **System Design & Scale** (3 Q):
  - "Design an MLOps platform that serves 50 models/prompts across 10 teams. What are the shared vs per-team components?" — must cover: shared model/prompt registry, eval harness, feature/embedding store, per-team pipelines, RBAC, cost attribution.
  - "How do you version data, prompts, and embeddings together so any prod behavior is reproducible?" — must cover: Git+DVC pointers, registry-backed prompt versions, embedding index snapshots in object storage, a single deployable bundle id.
  - "Where does the eval harness live so it gates every promotion at scale?" — must cover: eval as a pipeline step + CI gate, golden sets per domain, drift between offline and live eval.
  - **Scenario lead-in (optional):** one paragraph on a nightly retrain/re-embed pipeline.
- **Trade-offs & Decisions** (3 Q):
  - "Build vs buy the experiment-tracking/registry layer (MLflow self-host vs Azure ML / SageMaker)?" — cover: ops burden, lineage depth, lock-in, multi-cloud.
  - "When is fine-tuning worth the MLOps cost vs prompt+RAG?" — cover: data volume, latency/cost, drift maintenance, eval to justify.
  - "Monorepo of prompts vs per-service prompt ownership?" — cover: review velocity, blast radius, discoverability.
- **Failure Modes & Incidents** (3 Q):
  - "A prompt change passed offline eval but regressed in prod. How do you detect and roll back?" — cover: live golden-set metric, canary, registry rollback to prior bundle.
  - "Training/serving skew in a RAG pipeline — symptoms and fix?" — cover: embedding model mismatch between index build and query, version pinning.
  - "Silent model upgrade by the provider broke output format. Prevention?" — cover: pin model version, contract tests, schema validation.
- **Leadership & Behavioral** (2 Q):
  - "How do you get data scientists to adopt the pipeline instead of notebooks?" — cover: golden-path tooling, paved road, incremental migration, measuring adoption.
  - "Tell me about driving a reproducibility standard across teams (STAR)." — cover: situation/task/action/result, the standard, the resistance, the outcome metric.
- Stretch: "You're asked to set a 2-year MLOps strategy as the org scales from 3 to 30 models. What do you centralize first and why?"

- [ ] **Step 4: Add Summary + References footer**

```markdown
---

## Summary

MLOps for GenAI extends classic MLOps with prompt/embedding/model-version artifacts, eval-based gates, and managed-model reliance. Senior owners build the paved road — registry, eval harness, reproducible bundles — and make adoption the default.

## References

- MLflow — experiment tracking & model registry: https://mlflow.org/docs/latest/index.html
- Azure Machine Learning — pipelines & registries: https://learn.microsoft.com/azure/machine-learning/
- DVC — data/artifact versioning: https://dvc.org/doc
```

- [ ] **Step 5: Verify**

Run the reusable verification command with `f="06_mlops/interview.md"`. All six counts = 1. Skim for quality.

- [ ] **Step 6: Commit**

```bash
git add gen-ai-course/06_mlops/interview.md
git commit -m "docs(m6-mlops): add interview.md with Senior Deep Dive"
```

### Task 2: 07_architecture — create interview.md + deep dive

**Files:**
- Read first: `gen-ai-course/07_architecture/README.md` and `concepts.md` under `01_architecture_design`, `02_scalability_performance`, `03_reliability_resilience`, `04_cost_optimization`.
- Create: `gen-ai-course/07_architecture/interview.md`

- [ ] **Step 1: Read module context** — the four subtopics above.
- [ ] **Step 2: Write skeleton + 2 standard Q&A**

```markdown
# GenAI Architecture — Interview Questions

Model answers on architecting GenAI systems: design, scalability/performance, reliability/resilience, and cost.

---

## 1. Sketch a reference architecture for a production RAG application.

**Answer:** Client → API gateway → orchestration layer (prompt assembly, guardrails) → retrieval (vector DB + reranker) → LLM (managed/self-hosted) → response post-processing/citation → observability. Cross-cutting: caching, rate limiting, secrets, async ingestion pipeline for the corpus. Azure: APIM + Container Apps + AI Search + Azure OpenAI; AWS equivalents in passing.

## 2. What are the main latency contributors and how do you attack them?

**Answer:** Retrieval (index params, network), LLM TTFT + generation length, reranking, and serialization. Levers: semantic cache, streaming, smaller/faster models for easy queries (routing), parallel retrieval, prompt trimming.
```

- [ ] **Step 3: Append the Senior Deep Dive** — `## Senior Deep Dive: GenAI Architecture`. Framing: architecture interviews are the core of senior loops — scale, reliability, and cost trade-offs under constraints.
  - **System Design & Scale** (4 Q):
    - "Scale a RAG system from 1K to 1M requests/day — what breaks first and in what order?" — cover: LLM token throughput/quotas, vector DB QPS + index memory, embedding throughput on ingest, cache hit rate, connection pools.
    - "Design multi-region GenAI serving with an SLA. Active-active or active-passive?" — cover: model availability per region, data residency, vector index replication, failover, cost.
    - "How do you size capacity for an LLM endpoint (PTU/provisioned throughput)?" — cover: tokens/sec math, peak vs avg, provisioned vs on-demand split, autoscaling.
    - "Sync vs async architecture for long generations?" — cover: streaming, job queue + webhook, timeouts, UX.
  - **Trade-offs & Decisions** (3 Q):
    - "Managed model (Azure OpenAI/Bedrock) vs self-hosted on AKS/EKS?" — cover: cost curve, control/latency, GPU ops, compliance.
    - "Monolith orchestrator vs microservices for the GenAI pipeline?" — cover: latency hops, independent scaling, complexity.
    - "Caching: exact vs semantic vs none?" — cover: hit rate, staleness, correctness risk, cost saved.
  - **Failure Modes & Incidents** (3 Q):
    - "The LLM provider has a regional outage. What did you design so you survive?" — cover: multi-provider/region fallback, graceful degradation, circuit breaker, cached answers.
    - "Cascading failure from a slow vector DB. Containment?" — cover: timeouts, bulkheads, load shedding, backpressure.
    - "Cost spiked 5x overnight. Architectural causes and guards?" — cover: retry storms, prompt bloat, missing cache, runaway agents; budgets + alerts.
  - **Leadership & Behavioral** (2 Q):
    - "How do you run a design review that surfaces the real risks?" — cover: pre-reads, explicit trade-off table, inviting dissent, decision record.
    - "Tell me about a time you argued against an over-engineered design (STAR)."
  - Stretch: "Define the architecture principles/golden paths you'd publish for every team building GenAI apps in the org."
- [ ] **Step 4: Add Summary + References** (Azure Well-Architected, AWS Well-Architected, Azure OpenAI scaling docs).
- [ ] **Step 5: Verify** with `f="07_architecture/interview.md"`.
- [ ] **Step 6: Commit** — `docs(m7-architecture): add interview.md with Senior Deep Dive`.

### Task 3: 09_monitoring — create interview.md + deep dive

**Files:**
- Read first: `gen-ai-course/09_monitoring/README.md` and `concepts.md` under `01_observability`, `02_drift_detection`, `03_logging_strategies`.
- Create: `gen-ai-course/09_monitoring/interview.md`

- [ ] **Step 1: Read module context.**
- [ ] **Step 2: Write skeleton + 2 standard Q&A**

```markdown
# Monitoring & Observability for GenAI — Interview Questions

Model answers on observability, drift detection, and logging for GenAI systems.

---

## 1. What do you monitor for an LLM app beyond standard service metrics?

**Answer:** Service (latency p50/p99, error rate, throughput) **plus** GenAI signals: token usage/cost, cache hit rate, retrieval quality, and **output quality** (faithfulness/groundedness, LLM-judge scores on sampled traffic), plus safety/guardrail trip rates. The dangerous regressions return 200 OK with worse answers.

## 2. How do you trace a single GenAI request end to end?

**Answer:** Correlation id across gateway → retrieval → LLM call(s) → post-processing; capture prompt version, model version, retrieved doc ids, token counts, and latencies per span. Tools: OpenTelemetry + Azure Monitor / App Insights (AWS: CloudWatch + X-Ray).
```

- [ ] **Step 3: Append the Senior Deep Dive** — `## Senior Deep Dive: Monitoring & Observability`. Framing: senior roles own the signal that catches silent quality regressions and the cost/noise trade-off of telemetry.
  - **System Design & Scale** (3 Q):
    - "Design observability for 100M LLM calls/day without bankrupting on logging." — cover: sampling, tiered retention, aggregate metrics vs full traces, PII redaction at ingest.
    - "How do you compute a live quality metric at scale?" — cover: sampled LLM-judge, async eval workers, golden-set canary, custom metric to the monitoring backend.
    - "Drift detection pipeline for embeddings/inputs." — cover: input distribution monitoring, embedding drift, reference window, alert thresholds.
  - **Trade-offs & Decisions** (3 Q):
    - "Sampling rate vs cost vs detection latency for quality evals." — cover: statistical power, cost, how fast you must catch a regression.
    - "Log full prompts/responses or redact?" — cover: debuggability vs PII/compliance, hashing, tokenized storage.
    - "Build dashboards vs buy an LLM observability tool (LangSmith/Arize/etc.)?" — cover: integration, lock-in, custom metrics.
  - **Failure Modes & Incidents** (3 Q):
    - "Quality dropped but all dashboards are green. Why, and how do you fix the gap?" — cover: missing quality metric, only-infra monitoring, add golden-set + judge.
    - "Alert fatigue — too many false pages. Senior fix?" — cover: SLO-based alerts, burn-rate, dedupe, severity tiers.
    - "A drift alert fired — walk the triage." — cover: confirm real vs seasonal, scope, correlate with deploys/data, decide rollback vs retrain.
  - **Leadership & Behavioral** (2 Q):
    - "How do you establish SLOs/error budgets with product stakeholders?"
    - "Tell me about leading an incident where observability gaps slowed the fix (STAR)."
  - Stretch: "Define the org-wide observability standard (required spans, metrics, quality eval) every GenAI service must emit."
- [ ] **Step 4: Add Summary + References** (OpenTelemetry, Google SRE SLOs, Azure Monitor).
- [ ] **Step 5: Verify** with `f="09_monitoring/interview.md"`.
- [ ] **Step 6: Commit** — `docs(m9-monitoring): add interview.md with Senior Deep Dive`.

### Task 4: 13_LLMops — create interview.md + deep dive

**Files:**
- Read first: `gen-ai-course/13_LLMops/README.md` and `concepts.md` under `01_llmops_overview`, `03_infrastructure_setup`, `04_deployment_strategies`, `05_monitoring_observability`, `06_security_compliance`, `09_cost_optimization`.
- Create: `gen-ai-course/13_LLMops/interview.md`

- [ ] **Step 1: Read module context.**
- [ ] **Step 2: Write skeleton + 2 standard Q&A**

```markdown
# LLMOps — Interview Questions

Model answers on operating LLM systems in production: infrastructure, deployment, monitoring, security/compliance, and cost.

---

## 1. What is LLMOps and how does it relate to MLOps and DevOps?

**Answer:** LLMOps is the operational discipline for LLM-powered systems — the DevOps/MLOps practices specialized for prompts, context pipelines, managed-model dependencies, token-cost economics, and probabilistic quality. It spans infra (gateways, GPUs/PTUs), deployment (canary/rollback on quality), monitoring (cost + quality), and security/compliance (prompt injection, data governance).

## 2. What does an LLM gateway/router do and why is it central?

**Answer:** A single ingress that handles auth, rate limiting, model routing (cheap model for easy queries), retries/fallback across providers, caching, and centralized logging/cost attribution. It's the control point for cost, reliability, and observability.
```

- [ ] **Step 3: Append the Senior Deep Dive** — `## Senior Deep Dive: LLMOps`. Framing: senior LLMOps owns the cost/reliability/security envelope of every LLM call across the org.
  - **System Design & Scale** (4 Q):
    - "Design an LLM gateway handling all org traffic — components and scaling." — cover: routing, multi-provider failover, semantic cache, rate limit/quotas, cost attribution, circuit breaker.
    - "Cost optimization at scale — the biggest levers." — cover: model routing/right-sizing, caching, prompt compression, batching, provisioned vs on-demand, output length control.
    - "GPU/PTU capacity planning for self-hosted + managed mix." — cover: tokens/sec, utilization, autoscaling, reserved capacity.
    - "Multi-tenant LLM platform isolation." — cover: per-tenant quotas, cost, data isolation, noisy-neighbor.
  - **Trade-offs & Decisions** (3 Q):
    - "Single provider vs multi-provider abstraction." — cover: reliability, lock-in, feature parity, prompt portability.
    - "Centralized gateway vs direct SDK calls per service." — cover: control/observability vs latency hop + single point of failure.
    - "Provisioned throughput vs pay-per-token." — cover: predictable load, cost crossover, burst.
  - **Failure Modes & Incidents** (3 Q):
    - "Provider rate-limited you in prod. Immediate + structural response." — cover: backoff, fallback model/provider, queue/shed, raise quota; structurally cache + route.
    - "Retry storm caused a cost/availability incident. Root cause + guard." — cover: retries without jitter/budget, circuit breaker, cost alarms.
    - "Prompt-injection led to data exfiltration. Containment + prevention." — cover: input/output filtering, least-privilege tools, guardrails, allow-list, audit.
  - **Leadership & Behavioral** (2 Q):
    - "How do you set and enforce per-team LLM cost budgets without blocking innovation?"
    - "Tell me about leading a cost-reduction initiative that hit a quality constraint (STAR)."
  - Stretch: "Define the LLMOps platform roadmap and the build-vs-buy calls (gateway, eval, observability) for a company scaling to 100 LLM features."
- [ ] **Step 4: Add Summary + References** (Azure OpenAI provisioned throughput, AWS Bedrock, OWASP LLM Top 10).
- [ ] **Step 5: Verify** with `f="13_LLMops/interview.md"`.
- [ ] **Step 6: Commit** — `docs(m13-llmops): add interview.md with Senior Deep Dive`.

### Task 5: 08_cicd — create module-level interview.md (cross-cutting deep dive only)

**Files:**
- Read first: `gen-ai-course/08_cicd/README.md` and the four subtopic `concepts.md` (`01_versioning_deployment`, `02_automated_testing`, `03_deployment_strategies`, `04_aws_cicd`).
- Create: `gen-ai-course/08_cicd/interview.md`

- [ ] **Step 1: Read module context.** Note: subtopic-level interview.md files already exist; this new file holds only the cross-cutting Senior Deep Dive (do not duplicate subtopic Q&A).
- [ ] **Step 2: Write a short intro that points to the subtopic interview files**

```markdown
# CI/CD for AI — Senior Interview Deep Dive

Per-subtopic interview questions live in each subtopic's `interview.md` (versioning, automated testing, deployment strategies, AWS CI/CD). This file holds the cross-cutting **senior-level** deep dive that spans the whole CI/CD lifecycle for GenAI.

---
```

- [ ] **Step 3: Append the Senior Deep Dive** — `## Senior Deep Dive: CI/CD for GenAI`. Framing: senior interviews probe shipping probabilistic systems safely — eval gates, gradual rollout, and metric-driven rollback.
  - **System Design & Scale** (3 Q):
    - "Design a CI/CD pipeline that gates on AI quality for 20 services." — cover: shared eval gate (golden set), prompt/model registry, canary via CodeDeploy/Container Apps, per-service quality metric.
    - "How do you keep pipeline + eval fast as the golden set grows?" — cover: sampling/sharding eval, parallelism, tiered gates (fast unit → full eval on candidate).
    - "Versioning strategy across code, prompts, models, embeddings at scale." — cover: single deployable bundle id, registry approval gate, reproducibility.
  - **Trade-offs & Decisions** (3 Q):
    - "Canary vs blue-green vs linear for an LLM service." — cover: quality bake time, instant flip vs graduated, rollback cost.
    - "Block the build on eval pass-rate vs warn-only." — cover: false-fail noise vs shipping regressions; threshold with margin.
    - "Native cloud CI/CD (CodePipeline/Azure DevOps) vs GitHub Actions." — cover: integration, secrets, portability.
  - **Failure Modes & Incidents** (3 Q):
    - "A model change passed CI but degraded quality in prod. Detect + roll back." — cover: live quality alarm, canary auto-rollback to prior bundle.
    - "Flaky eval gate blocks deploys randomly. Fix." — cover: non-determinism (temperature), seed/threshold, retries, semantic scoring.
    - "Secret leaked into a container layer. Response + prevention." — cover: rotate, scrub history, secret manager, scanning.
  - **Leadership & Behavioral** (2 Q):
    - "How do you get teams to trust an automated quality gate they can't fully explain?"
    - "Tell me about introducing canary + auto-rollback to a team that deployed all-at-once (STAR)."
  - Stretch: "Define the org's release-safety standard for GenAI (required gates, rollback SLAs, who can override)."
- [ ] **Step 4: Add Summary + References** (link to the four subtopic folders; AWS CodeDeploy deployment configs; Google SRE canarying).
- [ ] **Step 5: Verify** with `f="08_cicd/interview.md"`.
- [ ] **Step 6: Commit** — `docs(m8-cicd): add module-level interview.md with cross-cutting Senior Deep Dive`.

---

## Group B — Append deep dive to existing `interview.md` (no senior section yet)

For each task: open the file, find the end (before any trailing `## Summary`/`## References`; if present, insert before it), and append the Senior Deep Dive. Do not modify existing Q&A.

### Task 6: 02_langchain — append deep dive

**Files:** Modify `gen-ai-course/02_langchain/interview.md` (read it first; subtopics: chains, LCEL, memory/tools/agents, patterns).

- [ ] **Step 1: Read** `gen-ai-course/02_langchain/interview.md` fully; note where Summary/References begin.
- [ ] **Step 2: Append the Senior Deep Dive** — `## Senior Deep Dive: LangChain in Production`. Framing: senior interviews probe whether you can run LangChain apps reliably and cheaply, not just wire chains.
  - **System Design & Scale** (3 Q):
    - "Architect a high-throughput LangChain service — where are the bottlenecks?" — cover: LLM calls, sync vs async (`ainvoke`), connection/callback overhead, streaming, caching layer.
    - "Memory at scale for many concurrent conversations." — cover: windowed/summary memory, external store (Redis/DB), token budget, eviction.
    - "Tool/agent orchestration that stays bounded." — cover: max iterations, timeouts, parallel tool calls, structured output.
  - **Trade-offs & Decisions** (3 Q):
    - "LangChain abstraction vs direct SDK calls." — cover: velocity vs overhead/lock-in/debuggability; when to drop down.
    - "LCEL chain vs custom orchestration vs LangGraph." — cover: branching/state needs, observability.
    - "Off-the-shelf agent vs constrained workflow." — cover: reliability, cost, predictability.
  - **Failure Modes & Incidents** (3 Q):
    - "An agent looped and burned tokens. Detect + prevent." — cover: iteration caps, loop detection, budget, circuit breaker.
    - "Output parser failures in prod." — cover: structured output / function calling, validation, retries with repair.
    - "Hidden latency from sequential chain steps." — cover: tracing, parallelization, caching.
  - **Leadership & Behavioral** (2 Q):
    - "How do you set standards for prompt/chain reuse across a team?"
    - "Tell me about replacing an over-complex agent with a simpler chain (STAR)."
  - Stretch: "When would you standardize the org on a framework vs let teams choose, and how do you migrate?"
- [ ] **Step 3: Verify** with `f="02_langchain/interview.md"`.
- [ ] **Step 4: Commit** — `docs(m2-langchain): add Senior Deep Dive to interview.md`.

### Task 7: 04_agentic_systems — append deep dive

**Files:** Modify `gen-ai-course/04_agentic_systems/interview.md` (read first; subtopics: design patterns, multi-agent, A2A protocol, langgraph).

- [ ] **Step 1: Read** the file; note Summary/References position.
- [ ] **Step 2: Append the Senior Deep Dive** — `## Senior Deep Dive: Agentic Systems at Scale`. Framing: senior interviews probe reliability, cost, and control of autonomous agents.
  - **System Design & Scale** (4 Q):
    - "Design a multi-agent system for a complex workflow — supervisor vs swarm?" — cover: orchestration topology, state sharing, message bus, parallelism, cost.
    - "How do you bound cost/latency of autonomous agents at scale?" — cover: step caps, budget per task, cheaper models for sub-agents, caching, early-exit.
    - "Shared state across concurrent agents." — cover: optimistic locking/versioning, conflict resolution, idempotency.
    - "Tool execution safety/sandboxing at scale." — cover: least privilege, sandbox, allow-lists, rate limits.
  - **Trade-offs & Decisions** (3 Q):
    - "Single capable agent vs multi-agent decomposition." — cover: latency, cost, reliability, debuggability.
    - "Autonomy vs human-in-the-loop checkpoints." — cover: risk, throughput, where to gate.
    - "ReAct vs plan-and-execute vs reflection." — cover: task type, cost, error recovery.
  - **Failure Modes & Incidents** (3 Q):
    - "An agent took a destructive action. Containment + prevention." — cover: HITL on high-risk tools, dry-run, permissions, audit.
    - "Infinite loop / no progress. Detect." — cover: iteration counter, progress metric, dedup, escalate.
    - "Tool/API failure cascaded across agents." — cover: retries with backoff, circuit breaker, graceful degradation.
  - **Leadership & Behavioral** (2 Q):
    - "How do you build org trust to let agents act autonomously?"
    - "Tell me about scoping an agent's autonomy after an incident (STAR)."
  - Stretch: "Define the org's guardrail policy for what agents may do autonomously vs require approval."
- [ ] **Step 3: Verify** with `f="04_agentic_systems/interview.md"`.
- [ ] **Step 4: Commit** — `docs(m4-agentic): add Senior Deep Dive to interview.md`.

### Task 8: 05_mcp — append deep dive

**Files:** Modify `gen-ai-course/05_mcp/interview.md` (read first; subtopics: overview, servers, client, enterprise project).

- [ ] **Step 1: Read** the file; note Summary/References position.
- [ ] **Step 2: Append the Senior Deep Dive** — `## Senior Deep Dive: MCP in the Enterprise`. Framing: senior interviews probe securing and scaling MCP servers/tools across an org.
  - **System Design & Scale** (3 Q):
    - "Design an MCP server platform serving many tools to many agents." — cover: server registry/discovery, auth, transport (stdio vs HTTP/SSE), versioning, multi-tenant.
    - "How do you scale and isolate tool execution behind MCP?" — cover: per-tool sandboxing, rate limits, timeouts, resource quotas.
    - "Resource/context management for large tool outputs." — cover: pagination, truncation, streaming, token budget.
  - **Trade-offs & Decisions** (3 Q):
    - "MCP vs direct/custom tool integration." — cover: standardization/interop vs overhead, ecosystem.
    - "One mega MCP server vs many focused servers." — cover: blast radius, ownership, deploy cadence.
    - "stdio vs remote transport." — cover: locality, security, scaling, latency.
  - **Failure Modes & Incidents** (3 Q):
    - "A malicious/compromised MCP tool. Containment + prevention." — cover: least privilege, allow-list, output validation, audit, signing.
    - "An MCP server became a bottleneck/SPOF." — cover: redundancy, timeouts, circuit breaker.
    - "Version skew between client and server broke tools." — cover: capability negotiation, semver, contract tests.
  - **Leadership & Behavioral** (2 Q):
    - "How do you govern which MCP servers/tools are approved for org use?"
    - "Tell me about standardizing tool access via MCP across teams (STAR)."
  - Stretch: "Define the enterprise MCP governance model (registry, security review, ownership) as adoption scales."
- [ ] **Step 3: Verify** with `f="05_mcp/interview.md"`.
- [ ] **Step 4: Commit** — `docs(m5-mcp): add Senior Deep Dive to interview.md`.

### Task 9: 06_langgraph — append deep dive

**Files:** Modify `gen-ai-course/06_langgraph/interview.md` (read first; subtopics: overview, building blocks — state, nodes, edges, checkpointing).

- [ ] **Step 1: Read** the file; note Summary/References position.
- [ ] **Step 2: Append the Senior Deep Dive** — `## Senior Deep Dive: LangGraph in Production`. Framing: senior interviews probe stateful, durable, recoverable agent workflows.
  - **System Design & Scale** (3 Q):
    - "Design a durable, resumable LangGraph workflow at scale." — cover: checkpointer backend (Redis/Postgres), state size, thread/session partitioning, replay.
    - "Human-in-the-loop at scale." — cover: interrupt/resume, durable pause, queueing approvals, timeouts.
    - "Managing large graph state and token budgets." — cover: state pruning, summaries, external storage of big blobs.
  - **Trade-offs & Decisions** (3 Q):
    - "LangGraph vs simple chain vs custom state machine." — cover: branching/cycles/HITL needs, complexity.
    - "Checkpoint everything vs selectively." — cover: durability vs storage/latency.
    - "Subgraphs vs one large graph." — cover: reuse, testability, blast radius.
  - **Failure Modes & Incidents** (3 Q):
    - "A node crashed mid-run — does the workflow recover?" — cover: checkpoint resume, idempotent nodes, retries.
    - "State bloat/corruption over long runs." — cover: schema validation, pruning, versioned state.
    - "A cycle never terminates." — cover: recursion limit, conditions, progress checks.
  - **Leadership & Behavioral** (2 Q):
    - "How do you decide when a team should adopt LangGraph vs simpler tools?"
    - "Tell me about debugging a hard stateful-workflow bug and what you changed (STAR)."
  - Stretch: "Define patterns/standards for durable agent workflows you'd publish org-wide."
- [ ] **Step 3: Verify** with `f="06_langgraph/interview.md"`.
- [ ] **Step 4: Commit** — `docs(m6-langgraph): add Senior Deep Dive to interview.md`.

### Task 10: 11_fine-tuning — append deep dive

**Files:** Modify `gen-ai-course/11_fine-tuning/interview.md` (read first; subtopics: overview, techniques — LoRA/QLoRA/RLHF/DPO, implementation incl. Azure MLOps, projects).

- [ ] **Step 1: Read** the file; note Summary/References position.
- [ ] **Step 2: Append the Senior Deep Dive** — `## Senior Deep Dive: Fine-Tuning in Production`. Framing: senior interviews probe when fine-tuning is justified and how to operate it.
  - **System Design & Scale** (3 Q):
    - "Design a fine-tuning + serving pipeline for adapters across many domains." — cover: data pipeline, LoRA adapter registry, eval gate, multi-adapter serving, versioning.
    - "Serve many fine-tuned variants cost-effectively." — cover: LoRA hot-swap/multi-adapter, base model sharing, routing, GPU utilization.
    - "Data pipeline for SFT/DPO at scale." — cover: collection, dedup, quality/toxicity filtering, PII, synthetic data ratio, splits.
  - **Trade-offs & Decisions** (3 Q):
    - "Fine-tune vs prompt+RAG vs both." — cover: data volume, latency/cost, drift maintenance, eval evidence.
    - "Full fine-tune vs LoRA/QLoRA." — cover: cost, quality, portability, catastrophic forgetting.
    - "SFT vs RLHF vs DPO." — cover: data needs, complexity, alignment goal.
  - **Failure Modes & Incidents** (3 Q):
    - "Fine-tuned model regressed on general tasks (catastrophic forgetting)." — cover: mixed data, eval suite, regularization, rollback.
    - "Training data leakage/contamination of eval." — cover: dedup across splits, leakage checks.
    - "Model collapse from too much synthetic data." — cover: cap synthetic ratio, mix real, monitor diversity.
  - **Leadership & Behavioral** (2 Q):
    - "How do you justify fine-tuning spend to leadership?"
    - "Tell me about killing a fine-tuning project when RAG was enough (STAR)."
  - Stretch: "Define the org's decision framework + guardrails for when teams may fine-tune vs must use managed models."
- [ ] **Step 3: Verify** with `f="11_fine-tuning/interview.md"`.
- [ ] **Step 4: Commit** — `docs(m11-finetuning): add Senior Deep Dive to interview.md`.

---

## Group C — Restructure existing deep dives to the template (preserve content)

For each: keep all existing Q&A content, but reorganize the existing `## Senior Deep Dive...` section so its questions fall under the four block headers, then add any missing block(s) and the Staff stretch box. Move/rename only — do not delete existing answers.

### Task 11: 01_generative_ai — restructure + complete

**Files:** Modify `gen-ai-course/01_generative_ai/interview.md` (existing deep dive at the "Senior Deep Dive: Hallucination Mitigation & Synthetic Data" section, lines ~491–520, before `## Summary`).

- [ ] **Step 1: Read** the existing Senior Deep Dive section.
- [ ] **Step 2: Restructure** — rename the heading to `## Senior Deep Dive: GenAI Fundamentals` (keep the hallucination/synthetic-data Q&A). Place the existing hallucination/faithfulness Q&A under `### Failure Modes & Incidents` and the synthetic-data Q&A under `### Trade-offs & Decisions`. Add the two missing blocks:
  - **System Design & Scale** (2 Q): "Design a hallucination-bounded RAG answer service at scale" (cover: grounding, citation enforcement, groundedness eval at scale, abstention); "How do you choose model size/family per use case at scale?" (cover: routing, cost/quality, latency).
  - **Leadership & Behavioral** (2 Q): "How do you set a team policy for acceptable hallucination risk per use case?"; "Tell me about convincing stakeholders that 'we can't eliminate hallucination, only bound it' (STAR)."
- [ ] **Step 3: Add the stretch box** — "Define the org-wide standard for grounding + eval that every GenAI feature must meet before launch."
- [ ] **Step 4: Verify** with `f="01_generative_ai/interview.md"` (ensure the section sits before `## Summary`).
- [ ] **Step 5: Commit** — `docs(m1-genai): restructure Senior Deep Dive to 4-block template`.

### Task 12: 03_rag_vectordb — restructure + complete

**Files:** Modify `gen-ai-course/03_rag_vectordb/interview.md` (existing "Senior Deep Dive: pgvector on Azure Database for PostgreSQL" at ~line 535).

- [ ] **Step 1: Read** the existing section.
- [ ] **Step 2: Restructure** — rename to `## Senior Deep Dive: RAG & Vector Databases`. Keep the pgvector/Azure content under `### System Design & Scale` (it is scaling/infra). Add:
  - **Trade-offs & Decisions** (3 Q): "Vector DB choice (pgvector vs dedicated like AI Search/Pinecone/Milvus)"; "HNSW vs IVF-PQ index trade-offs"; "Chunking strategy trade-offs at scale".
  - **Failure Modes & Incidents** (3 Q): "Retrieval returns irrelevant chunks in prod — debug"; "Embedding model change invalidated the index"; "Recall dropped after scaling vectors — index tuning".
  - **Leadership & Behavioral** (2 Q): "How do you set retrieval-quality standards/SLAs"; "Tell me about leading a re-embedding migration (STAR)".
- [ ] **Step 3: Add stretch box** — "Define the org's retrieval evaluation + quality bar for all RAG features."
- [ ] **Step 4: Verify** with `f="03_rag_vectordb/interview.md"`.
- [ ] **Step 5: Commit** — `docs(m3-rag): restructure Senior Deep Dive to 4-block template`.

### Task 13: 10_governance — restructure + complete

**Files:** Modify `gen-ai-course/10_governance/interview.md` (existing "Senior Deep Dive: AI in Risk Management & Responsible AI" at ~line 387).

- [ ] **Step 1: Read** the existing section.
- [ ] **Step 2: Restructure** — rename to `## Senior Deep Dive: AI Governance & Responsible AI`. Map existing risk/responsible-AI Q&A under `### Trade-offs & Decisions` (governance trade-offs) and `### Failure Modes & Incidents` (what goes wrong: bias, leakage, non-compliance). Add:
  - **System Design & Scale** (2 Q): "Design org-wide guardrails/policy enforcement for all GenAI traffic" (cover: gateway-level filters, content safety, audit, versioned policies); "Scaling human review / red-teaming."
  - **Leadership & Behavioral** (2 Q): "How do you build a responsible-AI review process teams will actually use"; "Tell me about blocking/altering a launch on governance grounds (STAR)."
- [ ] **Step 3: Add stretch box** — "Define the org's AI governance operating model (who owns policy, review gates, regulatory mapping like EU AI Act) as you scale globally."
- [ ] **Step 4: Verify** with `f="10_governance/interview.md"`.
- [ ] **Step 5: Commit** — `docs(m10-governance): restructure Senior Deep Dive to 4-block template`.

### Task 14: 12_deployment — restructure + complete

**Files:** Modify `gen-ai-course/12_deployment/interview.md` (existing "Senior Deep Dive: Deploying GenAI on Azure (AI Foundry, Azure OpenAI, Azure ML, AKS)" at ~line 620).

- [ ] **Step 1: Read** the existing section.
- [ ] **Step 2: Restructure** — rename to `## Senior Deep Dive: GenAI Deployment`. Keep the Azure-deployment content under `### System Design & Scale`. Add:
  - **Trade-offs & Decisions** (3 Q): "Managed (Azure OpenAI/Bedrock) vs self-hosted on AKS/EKS"; "Serverless vs container vs dedicated endpoint"; "Provisioned throughput vs pay-per-token deployment."
  - **Failure Modes & Incidents** (3 Q): "Endpoint outage/region failover"; "Cold-start latency on scale-up of a model container"; "Cost spike after a deploy."
  - **Leadership & Behavioral** (2 Q): "How do you set deployment/rollback standards for GenAI services"; "Tell me about leading a zero-downtime model migration (STAR)."
- [ ] **Step 3: Add stretch box** — "Define the org's GenAI deployment platform strategy (managed vs self-hosted mix, multi-region, build-vs-buy) over 2 years."
- [ ] **Step 4: Verify** with `f="12_deployment/interview.md"`.
- [ ] **Step 5: Commit** — `docs(m12-deployment): restructure Senior Deep Dive to 4-block template`.

---

## Group D — Cross-references & final verification

### Task 15: Add Senior Deep Dives index to README + master guide

**Files:**
- Modify: `gen-ai-course/README.md`
- Modify: `gen-ai-course/interview_preparation_guide.md`
- Also ensure each module's own `README.md` links its `interview.md` (check the 5 new/changed-file modules: 06_mlops, 07, 08, 09, 13 — add a link if missing).

- [ ] **Step 1: Read** `gen-ai-course/README.md` and `gen-ai-course/interview_preparation_guide.md` to find the right insertion point (a section listing modules / resources).
- [ ] **Step 2: Add a "Senior Deep Dives" index** to `gen-ai-course/interview_preparation_guide.md` (append a new section) listing all 14 module deep dives as links:

```markdown
---

## Senior Deep Dives by Module

Each module's `interview.md` includes a Senior Deep Dive (system design & scale, trade-offs & decisions, failure modes & incidents, leadership/behavioral, plus a Staff/Principal stretch):

- [01 Generative AI](01_generative_ai/interview.md#senior-deep-dive-genai-fundamentals)
- [02 LangChain](02_langchain/interview.md#senior-deep-dive-langchain-in-production)
- [03 RAG & Vector DBs](03_rag_vectordb/interview.md#senior-deep-dive-rag--vector-databases)
- [04 Agentic Systems](04_agentic_systems/interview.md#senior-deep-dive-agentic-systems-at-scale)
- [05 MCP](05_mcp/interview.md#senior-deep-dive-mcp-in-the-enterprise)
- [06 LangGraph](06_langgraph/interview.md#senior-deep-dive-langgraph-in-production)
- [06 MLOps](06_mlops/interview.md#senior-deep-dive-mlops-for-genai)
- [07 Architecture](07_architecture/interview.md#senior-deep-dive-genai-architecture)
- [08 CI/CD](08_cicd/interview.md#senior-deep-dive-cicd-for-genai)
- [09 Monitoring](09_monitoring/interview.md#senior-deep-dive-monitoring--observability)
- [10 Governance](10_governance/interview.md#senior-deep-dive-ai-governance--responsible-ai)
- [11 Fine-Tuning](11_fine-tuning/interview.md#senior-deep-dive-fine-tuning-in-production)
- [12 Deployment](12_deployment/interview.md#senior-deep-dive-genai-deployment)
- [13 LLMOps](13_LLMops/interview.md#senior-deep-dive-llmops)
```

- [ ] **Step 3: Add a one-line pointer** in `gen-ai-course/README.md` to that index (e.g. under a resources/interview section): `- **Senior interview prep:** every module's interview.md has a Senior Deep Dive — see the index in interview_preparation_guide.md.`
- [ ] **Step 4: Ensure module READMEs link interview.md** for 06_mlops, 07_architecture, 08_cicd, 09_monitoring, 13_LLMops (add a bullet linking `./interview.md` if absent).
- [ ] **Step 5: Verify links** — confirm each target file exists:

```bash
cd "gen-ai-course"
for f in 01_generative_ai 02_langchain 03_rag_vectordb 04_agentic_systems 05_mcp 06_langgraph 06_mlops 07_architecture 08_cicd 09_monitoring 10_governance 11_fine-tuning 12_deployment 13_LLMops; do test -f "$f/interview.md" && echo "OK $f" || echo "MISSING $f"; done
```

Expected: 14 lines all `OK`.

- [ ] **Step 6: Commit** — `docs(course): index Senior Deep Dives in README & master interview guide`.

### Task 16: Final full verification

- [ ] **Step 1: Run the structural check across all 14 files**

```bash
cd "gen-ai-course"
for f in 01_generative_ai 02_langchain 03_rag_vectordb 04_agentic_systems 05_mcp 06_langgraph 06_mlops 07_architecture 08_cicd 09_monitoring 10_governance 11_fine-tuning 12_deployment 13_LLMops; do
  c1=$(grep -c "^## Senior Deep Dive:" "$f/interview.md")
  c2=$(grep -c "^### System Design & Scale" "$f/interview.md")
  c3=$(grep -c "^### Trade-offs & Decisions" "$f/interview.md")
  c4=$(grep -c "^### Failure Modes & Incidents" "$f/interview.md")
  c5=$(grep -c "^### Leadership & Behavioral" "$f/interview.md")
  c6=$(grep -c "Staff/Principal stretch" "$f/interview.md")
  echo "$f: $c1$c2$c3$c4$c5$c6 (want 111111)"
done
```

Expected: every line ends in `111111`.

- [ ] **Step 2: Placeholder scan**

```bash
cd "gen-ai-course"
grep -rniE "TODO|TBD|fill in|lorem ipsum" */interview.md || echo "CLEAN"
```

Expected: `CLEAN`.

- [ ] **Step 3: Confirm no existing content was deleted** in the four restructured files — `git log --stat` / `git diff` review shows additions/moves, not net deletions of prior Q&A.

- [ ] **Step 4: Final commit if any fixes were made** — `docs(course): finalize Senior Deep Dives verification`.

---

## Self-Review (completed by plan author)

- **Spec coverage:** All 14 modules have a task (Group A creates 4 + 08_cicd; Group B appends 5; Group C restructures 4). Template (4 blocks + stretch) defined in Shared Reference and required by Definition of Done. Azure-primary/AWS-secondary convention stated. Cross-references covered by Task 15. Verification covered by Task 16. ✓
- **Placeholder scan:** Each content task lists exact files, exact section headings, exact question text, and required answer-content bullets (the engineer writes the prose; the questions and key points are concrete, not "TBD"). ✓
- **Type/heading consistency:** The four block headings and the `Staff/Principal stretch` marker are identical across the Shared Reference, every task, and the verification commands. The README index anchors are derived from the exact section titles each task sets. ✓
