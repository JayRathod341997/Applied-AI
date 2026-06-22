# GenAI Architecture — Interview Questions

Model answers on architecting GenAI systems: design, scalability/performance, reliability/resilience, and cost.

---

## 1. Sketch a reference architecture for a production RAG application.

**Answer:** Client → API gateway → orchestration layer (prompt assembly, guardrails) → retrieval (vector DB + reranker) → LLM (managed/self-hosted) → response post-processing/citation → observability. Cross-cutting: caching, rate limiting, secrets, async ingestion pipeline for the corpus. Azure: APIM + Container Apps + AI Search + Azure OpenAI; AWS: API Gateway + ECS/EKS + OpenSearch + Bedrock.

## 2. What are the main latency contributors and how do you attack them?

**Answer:** Retrieval (index params, network round-trips), LLM TTFT + generation length, reranking, and serialization. Levers: semantic cache for repeat/near-repeat queries, streaming to cut perceived TTFT, smaller/faster models for easy queries (complexity routing), parallel retrieval across multiple indexes, and prompt trimming to reduce input tokens.

---

## Senior Deep Dive: GenAI Architecture

> Architecture interviews are the core of senior loops. You are expected to reason about scale, reliability, and cost trade-offs under real constraints — not just describe components. Lead with conclusions, state your assumptions, and walk through what breaks at each order-of-magnitude jump.

### System Design & Scale

#### Q: Scale a RAG system from 1K to 1M requests/day — what breaks first and in what order?

**Answer:** The bottlenecks surface in a predictable sequence as load increases:

1. **LLM token throughput / provider quotas** hit first. At 1K req/day you fit inside a default rate limit; at 1M you need provisioned throughput (PTU on Azure OpenAI, provisioned concurrency on Bedrock) or a multi-provider fan-out to spread load. Token consumption math: if the average request is 2K tokens in + 500 out, 1M req/day = ~2.9B input tokens/day — that requires serious quota negotiation or self-hosted serving.

2. **Vector DB QPS and index memory** become the next wall. A typical managed vector DB handles hundreds of QPS; at ~12K req/min you will exhaust that. Fix: horizontal sharding of the vector index, read replicas, and an embedding cache to avoid re-querying for repeated or near-identical questions.

3. **Embedding throughput on ingest** — a sudden corpus re-index at high scale can starve the retrieval path. Decouple via an async event-driven ingestion pipeline (S3 event → Kafka → embed workers → index); this prevents an ingest spike from blocking live queries.

4. **Cache hit rate degrades** under long-tail query distributions. Layer exact-match first (hash lookup), then semantic cache (vector similarity). At 1M req/day even a 30% semantic hit rate saves ~$8K/month on a frontier model.

5. **Connection pool exhaustion** on the orchestration layer — each microservice needs pooled, persistent connections to the vector DB, LLM endpoint, and cache. Per-request connection open/close adds 10–50ms and exhausts fds under load.

**Senior framing:** The pattern is always compute → storage → network → coordination. State this order in the interview, then defend which knob you pull first in your specific setup.

---

#### Q: Design multi-region GenAI serving with an SLA. Active-active or active-passive?

**Answer:** For most production GenAI workloads, **active-active with regional preference** is the right call; pure active-passive wastes expensive GPU capacity and creates a slow cold-start failover path.

| Factor | Active-Active | Active-Passive |
|---|---|---|
| Failover latency | Seconds (DNS TTL) | 30–90s (warm) or minutes (cold) |
| GPU cost | Higher (2× capacity) | Lower (standby warm, not hot) |
| Data residency | Complex — must pin writes to home region | Simpler |
| Throughput ceiling | 2× a single region | Single region only |

**Design decisions:**

- **Model availability per region:** Pre-deploy model weights to every active region. Azure: deploy Azure OpenAI in West Europe + East US + Southeast Asia. Do not rely on cross-region API calls; that adds 150–300ms of latency and a second potential failure point.
- **Vector index replication:** Use eventual-consistency replication for the read path (Redis cross-region replication for cache; AI Search geo-replication). Strong consistency only for billing/quota counters.
- **Data residency:** GDPR requires EU user data to stay in EU. Route at the API gateway level (APIM policy or Route 53 geolocation routing) so EU queries never leave the EU region.
- **Failover:** Health-check-based DNS failover with a 30s TTL. Set the primary and secondary at the gateway; the orchestration layer should be stateless so any region can serve any request.
- **Cost:** Run non-primary regions on reserved/committed-use pricing, not on-demand, to reduce the standby overhead.

**Azure reference:** APIM in front, with a backend pool pointing to Azure OpenAI deployments in two regions. APIM's built-in retry and circuit breaker routes around a failed backend automatically.

---

#### Q: How do you size capacity for an LLM endpoint (PTU / provisioned throughput)?

**Answer:** Start with the token math, then validate against your latency budget.

```
average tokens per request = avg_input_tokens + avg_output_tokens
peak RPM estimate          = peak_requests_per_minute
peak TPM (tokens per min)  = peak_RPM × avg_tokens_per_request

PTU needed ≈ peak_TPM / throughput_per_PTU
```

Azure OpenAI PTU benchmarks vary by model and region — at the time of writing, GPT-4o delivers roughly 2,500 TPM per PTU, but always validate against the live capacity calculator.

**Practical sizing steps:**

1. **Sample production traffic** (or load-test) to get the P95 token distribution, not just the average. A long tail of 8K-token requests drives capacity more than the mean.
2. **Decide the provisioned/on-demand split:** PTUs cover your predictable baseline at lower cost-per-token; on-demand / pay-as-you-go absorbs bursts. A 70/30 split is common: provision for P70 load, let the top 30% overflow to on-demand.
3. **Wire autoscaling at the orchestration layer**, not at the PTU level (PTUs are fixed allocations). The orchestration layer routes overflow to a secondary on-demand deployment when the primary hits its throughput ceiling.
4. **Re-evaluate monthly** — model efficiency improves and PTU prices shift; right-sizing is not a one-time task.

**AWS equivalent:** Bedrock provisioned throughput uses model units (MUs); same math, different unit names.

---

#### Q: Sync vs async architecture for long generations — when do you use each?

**Answer:** The decision is driven by latency tolerance and output length.

| Pattern | When to use | Key concern |
|---|---|---|
| Sync + streaming | Interactive chat, < 30s expected generation | TTFT, connection keep-alive |
| Async job queue | Report generation, document analysis, batch eval | Polling / webhook, timeout hygiene |
| Hybrid: stream header, async body | Dashboard summaries where skeleton is needed fast | Complexity |

**Sync + streaming** is the default for chat. Server-Sent Events (SSE) or WebSocket lets the client render tokens as they arrive, making a 10s generation feel responsive. Always set an idle-stream timeout (e.g. 60s without a new token) separate from the connect timeout.

**Async queue** is right when generation will take minutes or the client cannot hold a long connection (mobile, serverless). Pattern: POST `/jobs` → return `job_id` immediately → worker picks up from SQS/Service Bus → POST result to callback URL or client polls `/jobs/{id}`. Wire dead-letter queues for failed jobs, and cap worker concurrency with a bulkhead so a flood of long jobs does not starve short ones.

**The failure mode to watch:** sync endpoints with no server-side timeout that hold connections for 90-second generations under load will exhaust your gateway connection pool. Always enforce an upper bound at the gateway (APIM policy `backend-timeout`, AWS ALB `request_timeout`), and design the client to handle `202 Accepted` + polling when that limit is hit.

---

### Trade-offs & Decisions

#### Q: Managed model (Azure OpenAI / Bedrock) vs self-hosted on AKS/EKS — how do you choose?

**Answer:** Lead with the cost crossover, then validate against the control/compliance constraints.

| Factor | Managed (Azure OpenAI / Bedrock) | Self-hosted (AKS + vLLM/TGI) |
|---|---|---|
| Operational burden | Near-zero | Full GPU ops: drivers, updates, OOM |
| Latency | 50–200ms per call (network) | 5–50ms (in-cluster) |
| Cost at low scale (<1M tokens/day) | Cheaper — no idle GPU cost | Expensive — GPU bill even when idle |
| Cost at high scale (>500M tokens/day) | Expensive per-token pricing | Cheaper — fixed infra, amortized |
| Model selection | Provider's catalog only | Any open-weight model (Llama, Mistral, Qwen) |
| Fine-tuned / proprietary weights | Requires BYOM or provider support | Full control |
| Data residency / air-gap | Depends on provider region | Complete control |
| Compliance (HIPAA, IL-5, FedRAMP) | Check if provider's offering is certified | Self-certifiable |

**Decision heuristic:** Start managed. Move self-hosted when (a) monthly token spend exceeds ~$20K and the math favours dedicated GPU, (b) you need a fine-tuned model the provider won't host, or (c) a compliance requirement prohibits sending data to a third-party API.

**Azure path:** Azure OpenAI with PTUs for baseline + on-demand for burst → move hot models to AKS + vLLM when the cost crossover is confirmed on real traffic data, keeping Azure OpenAI as a fallback.

---

#### Q: Monolith orchestrator vs microservices for the GenAI pipeline — when does it matter?

**Answer:** Start with a **modular monolith**; split into microservices only when a specific forcing function appears.

A monolith orchestrator runs retrieval, prompt assembly, guardrails, and LLM calls in-process. That means sub-millisecond inter-component calls, a single deployment artifact, and one log stream to debug. For a team of 2–5 engineers shipping a new product, this is almost always the right architecture.

**Microservices become justified when:**

- Components have wildly different scaling needs: the embedding service needs GPU, the guardrail needs CPU, the retrieval service needs memory-optimized nodes — you cannot right-size one pod for all three.
- Teams need independent deployment cycles: the embedding team ships weekly; the safety team ships daily; coupling them into one artifact creates release contention.
- Compliance demands isolation: PHI-handling logic must run in a certified enclave separate from general orchestration.
- The same model must serve multiple pipelines with different SLAs (chat at p99 <2s, batch at p99 <60s).

**The latency cost:** every microservice boundary adds ~1–10ms of network hop plus serialization. A five-stage pipeline in microservices can add 30–50ms of pure network overhead versus a monolith. At high scale this is fine; for a 500ms total budget it is non-trivial.

**Senior framing:** The real risk of premature microservices is distributed debugging. A single slow request now requires correlating traces across 5 services. Invest in distributed tracing (OpenTelemetry + Application Insights or AWS X-Ray) before you split.

---

#### Q: Caching — exact match vs semantic vs none?

**Answer:** Layer them; the right tier depends on hit rate potential, staleness tolerance, and correctness risk.

| Cache tier | Matches on | Typical hit rate | Correctness risk | When to use |
|---|---|---|---|---|
| None | — | 0% | None | Dynamic, personalized, real-time queries |
| Exact match | Byte-identical prompt | 15–30% | Zero | FAQs, deterministic tool calls |
| Semantic | Embedding cosine similarity ≥ τ | 30–60% | Low-medium | Paraphrased questions, support bots |
| Prefix / KV (provider-side) | Shared static system prompt prefix | 20–40% latency saving | None | Long fixed system prompts |

**Choosing the similarity threshold τ for semantic cache:**

- τ = 0.97: very conservative, few false hits, lower hit rate. Good for factual QA where a wrong cached answer is damaging.
- τ = 0.90: balanced default for most support/FAQ use cases.
- τ = 0.80: high hit rate but risks returning a semantically adjacent but wrong answer. Only safe for low-stakes use cases.

**The correctness risk that kills semantic caches:** if "How do I cancel my subscription?" and "How do I pause my subscription?" hash to the same cache entry, the user gets the wrong answer. Keep τ high (≥ 0.92) for anything transactional, and always include a TTL so stale answers expire when the underlying knowledge base changes.

**When cache adds zero value:** real-time personalized generation (the prompt always includes user-specific context), streaming completions with tool calls (the response depends on tool output), and agentic loops (each step is unique). In these cases, skip the cache lookup entirely to avoid the embedding + lookup overhead.

---

### Failure Modes & Incidents

#### Q: The LLM provider has a regional outage. What did you design so you survive?

**Answer:** Survival requires layered defence: multi-provider/region routing, graceful degradation, circuit breakers, and cached answers. Each layer handles a different failure duration.

**Layer 1 — Multi-provider fallback chain (seconds):**

```
primary: Azure OpenAI East US  →  failed?
fallback: Azure OpenAI West Europe  →  failed?
fallback: OpenAI direct API  →  failed?
fallback: Anthropic Claude API
```

The API gateway (or orchestration layer) walks this chain using per-provider circuit breakers. An OPEN breaker is skipped instantly — no timeout cost paid on a dead endpoint. This resolves incidents within seconds.

**Layer 2 — Graceful degradation (minutes to hours):**

If all LLM providers are unavailable (coordinated CDN incident, global BGP issue): fall back to exact-match cache for known queries, return a canned "We're experiencing issues, please try again shortly" for unknowns. A slightly worse answer beats a hard 503.

**Layer 3 — Multi-region model deployment (permanent geographic resilience):**

Deploy model endpoints in every active region. If the Azure OpenAI East US endpoint is unhealthy, traffic routes to West Europe via health-check-based DNS — this is transparent to the caller.

**What you should have built before the incident:**

- A circuit breaker per provider with configurable failure threshold and cooldown.
- A provider health dashboard and PagerDuty alert on circuit-open events.
- A runbook for "manually force all traffic to secondary provider" — because sometimes the circuit breaker is too slow and you want an ops-driven toggle.
- Load tests proving the secondary provider can absorb 100% of traffic (do not discover this during the incident).

**Senior framing:** In the postmortem, the question will be "how long until users noticed nothing?" not "did we have a fallback?" The answer depends on your circuit breaker's detection latency (failure threshold × average request duration) and the DNS TTL on your health-check failover.

---

#### Q: Cascading failure from a slow vector DB — how do you contain it?

**Answer:** The root cause of a cascade: a slow dependency holds threads/connections, queues fill up, upstream callers back up, and the whole service degrades even though the slow component is only one of many.

**Containment playbook:**

1. **Timeouts with deadline propagation.** The retrieval call to the vector DB must have a hard timeout (e.g. 2s) that is shorter than the caller's own SLA. A hanging vector DB query must not hold a goroutine/thread for 60s.

2. **Bulkhead per dependency.** The vector DB connection pool is separate from the LLM connection pool. A slow vector DB exhausts its own pool of N connections — it cannot steal the LLM pool's connections and block chat responses.

3. **Circuit breaker on the retrieval path.** After N consecutive timeouts/errors, the retrieval circuit opens. The system falls back to LLM-only mode (no retrieved context), returning a lower-quality but non-erroring response with a caveat ("Answering from general knowledge; source documents may be unavailable").

4. **Load shedding at the gateway.** When the orchestration layer's queue depth exceeds a threshold, start returning `429 Too Many Requests` with a `Retry-After` header. Controlled shedding is preferable to an uncontrolled crash.

5. **Backpressure signalling.** The retrieval service should expose a `/readyz` health check that returns `503` when its own queue is full. The load balancer drains it from rotation immediately, stopping new requests from piling onto an already-struggling node.

**Telemetry you need in real time:** `retrieval_latency_p99`, `vector_db_active_connections`, `retrieval_circuit_breaker_state`, `llm_requests_queued`. Set alerts on all four with sub-minute evaluation windows.

---

#### Q: Cost spiked 5× overnight. Architectural causes and how do you prevent recurrence?

**Answer:** Five-times cost spikes have a small set of root causes. Diagnose by slicing your cost telemetry, then wire guards to prevent each.

**Common causes:**

| Cause | Signature | Guard |
|---|---|---|
| Retry storm | `llm_request_rate` spikes, `success_rate` low | Cap total retries per job; circuit breaker to stop retrying dead providers |
| Prompt bloat / injection | `avg_input_tokens` jumps 3–10× | Alert on `tokens_per_request > baseline + 50%`; max token cap at gateway |
| Missing or cold cache | `cache_hit_rate` drops to near 0% | Alert on `cache_hit_rate < 20%`; check TTL expiry or cache key regression |
| Runaway agent loop | `completions_per_session` grows unbounded | Per-session token budget; max-steps cap in agent orchestration |
| Wrong model tier routing | `frontier_model_fraction` of traffic jumps | Alert on `escalation_rate` trending up; check routing logic for a regression |
| New traffic source (marketing campaign, viral) | Uniform spike across all metrics | Cost budget alert at 120% of daily spend; automatic throttling above budget |

**Architectural guards to wire before they trigger:**

- A `BudgetGuard` that fires at 50%, 80%, and 100% of daily/monthly budget. At 100%, either throttle non-critical features or auto-page the on-call engineer.
- Per-tenant and per-feature spend tags on every LLM call. "LLM costs spiked" is unactionable; "Feature X, Tenant Y costs spiked" is a 15-minute investigation.
- Gateway-level `max_tokens` enforcement — the backend cannot spend more than the configured cap regardless of what the caller requests.
- A `cost_per_successful_task` metric in your dashboards. If this trends up while traffic is flat, your prompts or routing got worse.

**Senior framing:** Cost spikes are often the first signal of a correctness or reliability regression (retry storms, agent loops that can't terminate). Treat cost as a telemetry signal, not just a finance concern — wire it alongside latency and error rate from day one.

---

### Leadership & Behavioral

#### Q: How do you run a design review that actually surfaces the real risks?

**Answer:** Most design reviews fail because they become status updates rather than adversarial explorations of failure. Fix the structure:

**Before the review:**

- Require a written design doc with an explicit trade-off table (not just a diagram). The act of writing forces clarity that diagrams hide.
- Distribute the doc 48 hours in advance with specific questions: "What breaks at 10× load?" and "What happens if provider X is unavailable for 2 hours?"
- Identify one "red team" reviewer whose job is to argue against the design.

**During the review:**

- Start with the author stating their assumptions and the constraints they optimised for. This establishes the frame — a reviewer who disagrees with an assumption can surface it early rather than arguing about conclusions.
- Explicitly walk through failure modes: "Walk me through what happens when [dependency] is slow / down / returns garbage." This consistently uncovers missing timeouts, missing circuit breakers, and missing fallbacks.
- Keep a live trade-off table visible. Every time a trade-off is made, write it down: "We are accepting X risk in exchange for Y benefit." This prevents the review from cycling back to settled decisions.
- Invite dissent explicitly: "What is the worst version of this design?" Psychological safety must be named, not assumed.

**After the review:**

- Publish a decision record (ADR) capturing the decision, the alternatives considered, and the reasons rejected. Future engineers need this context when they want to change the design.
- Track open questions with owners and due dates. Unresolved questions do not block the doc from being merged — they have owners.

---

#### Q: Tell me about a time you argued against an over-engineered design. (STAR)

**Answer:**

**Situation:** A team was building the first internal GenAI feature — a support ticket classifier. The proposed architecture had five microservices (ingest, classify, cache, gateway, notify), a Kafka cluster, and a Redis cluster, for a system that would handle ~500 requests/day.

**Task:** I was reviewing the design before it went to the sprint. My concern was that the complexity was calibrated for 10M req/day, not 500, and that the team had three engineers — two of whom had never run Kubernetes in production.

**Action:** I asked for 30 minutes before the design was finalised. I brought a single-slide cost/complexity comparison: the proposed microservices architecture required 8 Kubernetes deployments, 3 persistent volumes, a Kafka topic, and on-call knowledge of 5 systems. The alternative — a modular monolith on a single Container App with a Redis cache and Azure Service Bus for async — handled the same workload with 1 deployment and 1 stateful dependency. I made the argument explicitly: "We are paying microservices complexity tax for a feature that doesn't need it yet. The correct time to split is when we hit a scaling wall or a team-size forcing function — not day one." I proposed a migration path: "Design the modules with clean interfaces now; if we need to split in 6 months, the seams are already there."

**Result:** The team adopted the modular monolith. It shipped two weeks earlier than the original estimate, the first production incident was resolved in 45 minutes (single log stream, single deployment), and when the feature scaled 10× six months later, the modular boundaries made the extraction straightforward. The original team lead later said the design review was the highest-leverage hour of the project.

---

> 🎯 **Staff/Principal stretch:** "Define the architecture principles and golden paths you would publish for every team building GenAI apps in the organisation."

**Answer:** Golden paths exist to eliminate repeated discovery of the same failure modes across teams. The goal is not to mandate a single stack, but to provide a well-tested, secure, cost-managed starting point that teams can diverge from with justification.

**The principles I would publish:**

1. **Start with a modular monolith.** Split into microservices only when a specific forcing function is documented: distinct scaling needs, team boundary, or compliance isolation. "Future scalability" is not a forcing function.

2. **Provider abstraction is non-negotiable.** Every LLM call goes through a gateway layer that hides the provider behind a common interface. No team hardcodes `openai.chat.completions.create` in their business logic. This makes provider failover, model upgrades, and cost routing transparent.

3. **Observability before you ship.** Every LLM call emits: latency, token counts, cost (USD), model name, feature tag, and tenant tag. These are correlation dimensions, not afterthoughts. No observability = no on-call runbook.

4. **Cost is a first-class design axis.** Every design doc includes a cost estimate at 10× projected load. Cache ROI must be positive before a cache is added. Model tier must be justified by an eval, not by habit.

5. **Multi-provider fallback from day one.** A system that depends on one provider is one outage away from a P0. The golden path ships with a two-provider fallback chain and a circuit breaker.

6. **Async for long work, sync+streaming for chat.** Generation > 10s goes on a job queue. Sync endpoints have hard timeouts enforced at the gateway.

**The golden path artefacts I would ship:**

- A reference Terraform/Bicep module for the base infrastructure (APIM + Container Apps + AI Search + Azure OpenAI + Redis).
- A Python/TypeScript SDK wrapper that implements the gateway, circuit breaker, semantic cache, and cost meter — teams drop it in as a dependency.
- A cookiecutter project template that wires the SDK, an OpenTelemetry exporter, and a BudgetGuard with sane defaults.
- An ADR template with mandatory sections: failure mode analysis, cost estimate at 10×, provider fallback strategy.

**How I would enforce them:** golden paths are the path of least resistance, not a mandate. If a team diverges, they write an ADR explaining why. I review those ADRs in the weekly architecture office hours — this surfaces patterns where the golden path is genuinely wrong and needs updating, rather than just teams ignoring it.

---

## Summary

Senior GenAI architecture is about scaling, reliability, and cost under real constraints: know what breaks first at 100×, design multi-region/fallback for provider outages, and make cost a first-class design axis.

## References

- Azure Well-Architected Framework: https://learn.microsoft.com/azure/well-architected/
- AWS Well-Architected Framework: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html
- Azure OpenAI — provisioned throughput (PTU): https://learn.microsoft.com/azure/ai-services/openai/concepts/provisioned-throughput
