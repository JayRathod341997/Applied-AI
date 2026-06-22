# LLMOps — Interview Questions

Model answers on operating LLM systems in production: infrastructure, deployment, monitoring, security/compliance, and cost.

---

## 1. What is LLMOps and how does it relate to MLOps and DevOps?

**Answer:** LLMOps is the operational discipline for LLM-powered systems — DevOps/MLOps practices specialized for prompts, context pipelines, managed-model dependencies, token-cost economics, and probabilistic quality. It spans infra (gateways, GPUs/PTUs), deployment (canary/rollback on quality), monitoring (cost + quality), and security/compliance (prompt injection, data governance).

| Aspect | DevOps | MLOps | LLMOps |
|--------|--------|-------|--------|
| Model size | No models | MB–GB | GB–TB |
| Training cost | N/A | Moderate | Very high |
| Inference cost | N/A | Low | High (token-priced) |
| Prompt management | N/A | Not required | Critical |
| Quality measurement | Pass/fail tests | Accuracy metrics | Probabilistic, human eval |
| Caching | Standard HTTP | Simple | Semantic + provider-native |

## 2. What does an LLM gateway/router do and why is it central?

**Answer:** A single ingress for auth, rate limiting, model routing (cheap model for easy queries), retries/fallback across providers, caching, and centralized logging/cost attribution. It's the control point for cost, reliability, and observability.

---

## Senior Deep Dive: LLMOps

> A senior LLMOps engineer owns the cost/reliability/security envelope of every LLM call across the org. That means designing the control plane (gateway, caching, quotas), the deployment pipeline (canary on quality signals, not just latency), the threat model (prompt injection, data exfiltration), and the financial controls (per-team budgets, provisioned-vs-on-demand decisions). The systems they build must scale horizontally across dozens of product teams while giving each team autonomy without shared exposure.

---

### System Design & Scale

#### Q: Design an LLM gateway that handles all org traffic — what are the components and how does it scale?

**Answer:** The gateway is the single most leverage point in LLMOps. Build it as a horizontally scalable service sitting in front of all LLM providers. Core components:

**Ingress and control plane:**
- **Auth and tenant routing** — API key validation, JWT verification, map requests to tenant context (team, cost center, quota bucket).
- **Rate limiting** — token-bucket per tenant per model, enforced in Redis so all gateway replicas share state. Reject with `429` before the request reaches the provider.
- **Model router** — classify request complexity (regex + lightweight classifier), then dispatch: cheap model (GPT-3.5 / Claude Haiku) for simple Q&A, premium model (GPT-4 / Claude Sonnet) for complex reasoning. Rules are config-driven, hot-reloadable.
- **Circuit breaker per provider** — track rolling error rate and latency p95. Open the circuit (stop sending) after threshold breach; half-open after a timeout to test recovery. This prevents cascading failure when a provider is degraded.
- **Multi-provider fallback** — ordered provider list per model tier. On 429 or 5xx, retry on next provider in the list. Fallback order: Azure OpenAI → AWS Bedrock → direct OpenAI endpoint.

**Caching layer (cost multiplier):**
- **L1 exact-match cache** — Redis keyed on SHA-256 of (model, system-prompt, user-message). TTL 5 minutes. For FAQ-style traffic, hit rates of 30–50% are achievable.
- **L2 semantic cache** — embed the prompt, query a vector index (Qdrant / Azure AI Search), return the cached response if cosine similarity ≥ 0.95. Adds ~20 ms overhead but captures paraphrase-equivalent queries.
- **L3 provider-native cache** — structure prompts with stable content first (system prompt, reference docs) so the provider's KV cache reuses that prefix. On Anthropic, use explicit `cache_control` markers. On Azure OpenAI, the platform caches automatically for identical prefixes ≥ 1024 tokens.

**Observability and cost attribution:**
- Every request emits a structured log: `tenant_id`, `model`, `input_tokens`, `output_tokens`, `cost_usd`, `latency_ms`, `cache_hit`, `provider`, `request_id`.
- Cost is attributed in real time to the calling team's budget counter (Redis).
- Metrics exported to Prometheus → Grafana. Alert on cost rate anomalies (`3σ` over rolling 1h window) and per-team budget thresholds (80%, 100%).

**Scaling:**
- Gateway is stateless beyond the Redis-backed rate limit counters. Deploy as Kubernetes Deployment behind an Azure Application Gateway (or AWS ALB). Autoscale on request rate (HPA) or latency p95.
- Redis cluster for rate limiting state; read replicas for cache lookups.
- At very high volume, shard the semantic cache by tenant to avoid hot-key contention.

```
Client → Azure App Gateway → LLM Gateway Pods (k8s HPA)
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              Rate Limiter    Model Router    Semantic Cache
              (Redis cluster) (config rules)  (Qdrant)
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              Azure OpenAI    AWS Bedrock      OpenAI Direct
              (primary)       (fallback)       (fallback)
```

#### Q: What are the biggest cost levers at scale, and in what order do you pull them?

**Answer:** Start with the highest-impact, lowest-effort changes and work toward the strategic ones.

| Order | Lever | Effort | Typical Saving |
|-------|-------|--------|----------------|
| 1 | Set `max_tokens` on every call + brevity instructions | Minutes | 20–40% on output |
| 2 | Provider-native prompt caching (structure stable prefix first) | Hours | 60–90% on repeated system prompts |
| 3 | Semantic cache (L2) | Days | 20–40% of remaining traffic |
| 4 | Model routing (right-size by task complexity) | Days | 30–60% depending on mix |
| 5 | Batch API for offline workloads | Hours | 50% on eligible traffic |
| 6 | Fine-tune a small model for narrow high-volume tasks | Weeks | 80–95% vs. GPT-4 for that task |
| 7 | Self-host open-source model (LLaMA, Mistral) | Months | 80–90% at sufficient volume |

**Biggest single lever is output token control.** Output tokens cost 3–5x more per token than input tokens on most providers. Enforcing `max_tokens`, structured output (JSON mode eliminates filler), and brevity instructions often cuts the monthly bill by 20–30% within a day.

**Second biggest: provider-native prompt caching.** For any system with a long, stable system prompt or reference document in the context, put the stable content first and mark it for caching. On Anthropic, cache reads cost $0.30/1M tokens vs. $3.00/1M for regular input — a 90% saving on those tokens. The cost is one cache-write pass at $3.75/1M.

**Model routing** requires a classifier (even a regex heuristic is a good start) but pays off immediately at scale. A query like "What does API stand for?" does not need GPT-4.

#### Q: How do you capacity-plan for a self-hosted + managed mix?

**Answer:** Start by measuring, not guessing.

**For managed (Azure OpenAI / Bedrock):**
- Measure peak tokens per minute (TPM) and requests per minute (RPM) over 30 days. Take p99 of peak-hour load, add 30% headroom.
- Azure OpenAI capacity is measured in PTUs (provisioned throughput units). One PTU handles a deterministic throughput level; calculate required PTUs from the model's published PTU-to-TPM table.
- Compare monthly cost: `PTU monthly rate` vs. `estimated pay-per-token cost at that volume`. The crossover for Azure OpenAI GPT-4o is typically around 50–100K tokens/day sustained. Below that: pay-per-token. Above: PTU is cheaper and eliminates rate-limit risk.
- Reserve base load as PTU; absorb bursts via pay-per-token overflow (Azure supports this with a priority queue).

**For self-hosted (vLLM on GPU):**
- Baseline metric is tokens/sec per GPU at the serving batch size. Use vLLM's throughput benchmarking tool against your P95 prompt length and expected concurrency.
- GPU memory sizing (FP16): 7B model ≈ 14 GB, 13B ≈ 26 GB, 70B ≈ 140 GB. Always add 20% for KV cache.
- Autoscaling: use KEDA to trigger HPA based on pending-request queue depth (not CPU/RAM, which are poor signals for GPU workloads). Scale-out triggers at queue depth > 10 for 2 minutes; scale-in after 15 minutes of low utilization (GPU model loading is slow, so be conservative on scale-in).
- Reserve capacity for base load; use spot/preemptible GPU instances for burst if the workload is latency-tolerant.

#### Q: How do you run a multi-tenant LLM platform with isolation guarantees?

**Answer:** Isolation has four dimensions: quota, cost, data, and noisy-neighbor.

**Quota isolation:** Per-tenant rate limits enforced in the gateway (Redis token bucket). Each team gets a TPM and RPM quota. Tenants that exhaust their quota get `429`; they cannot consume other tenants' quota. Quotas are stored in a config service, hot-reloadable without gateway restart.

**Cost isolation:** Every request tags `tenant_id`. The gateway debits the tenant's real-time budget counter (Redis). At 80% of monthly budget, the gateway sends a webhook alert to the team. At 100%, requests are throttled or rejected (configurable per team policy). Cost attribution is also exported to the data warehouse for monthly chargeback.

**Data isolation:** Logs and traces are tagged with `tenant_id` and written to tenant-scoped storage partitions. The semantic cache is sharded by tenant — a tenant's cached responses are never served to another tenant. For regulated tenants (healthcare, finance), route to a dedicated Azure OpenAI instance in a private VNet, not the shared gateway backend.

**Noisy-neighbor prevention:** A single tenant doing a batch job should not degrade latency for other tenants. Solve this with priority queuing: interactive requests (low latency budget) get higher priority in the gateway's dispatch queue than batch requests. Enforce per-tenant concurrency limits (max N in-flight requests) independent of rate limits.

---

### Trade-offs & Decisions

#### Q: Single provider vs. multi-provider abstraction — when is each right?

**Answer:** The decision is fundamentally about reliability vs. complexity.

**Single provider (Azure OpenAI primary):**
- Simpler: one SDK, one billing account, one compliance posture.
- Azure OpenAI provides enterprise SLA (99.9%), private endpoints (VNet), and content safety built-in.
- Risk: a provider outage or a rate-limit surge during a product launch can take down your LLM features entirely.
- Right for: early-stage, single-region, non-critical features.

**Multi-provider abstraction:**
- Eliminates single-point-of-failure: fallback from Azure OpenAI to AWS Bedrock (Claude) or direct OpenAI on degradation.
- Enables model best-of-breed routing: use Anthropic Claude for long-context tasks (200K window), OpenAI for function calling, Google Gemini for multimodal.
- Cost: prompt portability is not free. System prompts tuned for GPT-4 often produce different behavior on Claude. You need a prompt testing matrix for each model.
- Feature parity gaps: tool-use schemas, streaming behavior, and safety filter sensitivity differ across providers. Your abstraction layer must normalize these.
- Right for: any production system with >99% availability requirement, or one that needs the best model per task type.

**Practical recommendation:** Build a thin provider abstraction from day one (a simple routing class), start with a single provider, and add fallback as a second provider when the first incident occurs. Do not invest in full multi-provider prompt portability until you have evidence you need it.

#### Q: Centralized gateway vs. direct SDK calls per service — what's the call?

**Answer:** The centralized gateway wins for any org with more than two teams consuming LLMs. The tradeoff is real but manageable.

**Centralized gateway advantages:**
- Unified observability: all cost, token, and error data flows through one place. Without it, you get N silos of usage data with no org-wide view.
- Consistent policy enforcement: rate limits, content filtering, key rotation, and budget controls are implemented once, not N times across N services.
- A/B testing and model routing at the org level: you can transparently upgrade all services from GPT-3.5 to GPT-4o-mini without each service redeploying.

**Direct SDK call advantages:**
- Lower latency: removes one network hop (typically 2–5 ms for in-region).
- No single point of failure: each service is independent.

**Managing the single-point-of-failure risk:** Deploy the gateway as a highly available service (3+ replicas, multi-AZ, circuit breakers per backend). Implement a "bypass" mode: each service has the provider SDK as a fallback path with direct API key, activated only when the gateway health check fails. This gives you the observability benefits of a gateway with no hard dependency on it.

**Latency mitigation:** Co-locate the gateway in the same AZ as the calling services. Use HTTP/2 multiplexing and connection pooling to the gateway. The 2–5 ms overhead is negligible compared to a 300–2000 ms LLM call.

#### Q: Provisioned throughput vs. pay-per-token — how do you decide?

**Answer:** This is a breakeven analysis, not a philosophy.

**Azure OpenAI provisioned throughput (PTU):**
- You pre-purchase a throughput reservation (PTUs) at a fixed monthly price.
- Eliminates rate-limit risk: your quota is guaranteed, not shared with other Azure tenants.
- Favorable unit economics above a volume threshold. For GPT-4o, PTU becomes cheaper than pay-per-token at approximately 50–100K tokens/day sustained (varies by model and region).

**Pay-per-token:**
- Zero commitment, scales to zero when not used.
- Rate-limit risk: quota is shared across Azure tenants in your tier; during provider congestion, you get throttled.
- Favorable for: bursty, unpredictable, or low-average-volume workloads.

**Decision framework:**
1. Measure your P50 and P95 daily token volume over 4 weeks.
2. Calculate monthly pay-per-token cost at P50 volume.
3. Get the PTU monthly price for coverage at P50 volume from Azure pricing.
4. If PTU monthly < pay-per-token monthly and the workload is predictable: buy PTU for base load.
5. Configure pay-per-token as overflow for bursts above PTU capacity (Azure supports this natively).
6. Revisit quarterly as pricing and volume change.

**Common mistake:** buying PTU for a new feature before production traffic is established. Always run pay-per-token for the first 4–8 weeks to gather real usage data.

---

### Failure Modes & Incidents

#### Q: A provider rate-limited you in production. What do you do immediately and what do you change structurally?

**Answer:**

**Immediate response (first 5 minutes):**
1. Confirm it is a rate limit (`429` with `Retry-After` header) and not a 5xx outage. Different response.
2. Activate the fallback provider in the gateway (e.g., switch routing to AWS Bedrock or the secondary Azure OpenAI deployment). If the gateway has circuit-breaker logic, this should be automatic.
3. If no fallback is configured: implement exponential backoff with jitter immediately (start at 1s, max at 60s, ±20% jitter). Do not retry immediately — it worsens the throttle.
4. Communicate to stakeholders: what is degraded, what is the ETA, what is being done. Do not wait to have a fix before communicating.
5. Shed load if necessary: disable non-critical LLM features (e.g., background summarization) to protect interactive features.

**Structural changes after the incident:**
- **Raise quota:** Submit a quota increase request to the provider immediately. Azure OpenAI quota increases can take 1–3 business days; have a request template ready.
- **Add a fallback provider:** Any single-provider setup is one incident away from this situation again.
- **Semantic cache:** A well-seeded cache absorbs repeated queries, reducing effective TPM by 20–50% and providing a buffer during provider degradation.
- **Circuit breaker:** The gateway should detect rate limit responses and route around the affected provider automatically, not require a human intervention.
- **Load testing:** Run provider failure scenarios (chaos engineering) in staging before the next launch.

#### Q: A retry storm caused a cost and availability incident. What was the root cause and how do you guard against it?

**Answer:**

**Root cause pattern:** Services configured with aggressive retry logic (e.g., retry immediately on any 5xx, up to 5 times) encountered a transient provider slowdown. Each failed request generated 5 retries. Traffic amplified 5x. The provider, already under stress, received a surge that converted a brief degradation into a prolonged outage. Meanwhile, costs for the retried tokens (billed by the provider even for failed calls in some configurations) spiked.

**Specific failure conditions to look for:**
- No exponential backoff: fixed-interval retries at 100ms intervals.
- No retry budget: total retries per time window are unbounded.
- No jitter: all instances retry at exactly the same intervals, creating synchronized bursts.
- No circuit breaker: services keep retrying even when the provider is clearly down.

**Guards to implement:**
1. **Exponential backoff with jitter:** base 1s, multiplier 2x, max 60s, ±30% jitter. Standard pattern in all provider SDKs; use it.
2. **Retry budget:** max 3 retries per request, and independently, max N retries per minute across all instances (enforced in the gateway's circuit breaker state).
3. **Circuit breaker:** after 10% error rate over 30 seconds, open the circuit for 30 seconds. Half-open: send 1 test request; if it succeeds, close. This stops retry storms at the source.
4. **Cost alarms:** alert if cost rate exceeds 2x the rolling 1-hour baseline. A retry storm shows up as a cost spike before it shows up as a P0 incident.
5. **Idempotency keys:** ensure retried requests do not cause duplicate side effects downstream.

#### Q: A prompt-injection attack led to data exfiltration. How do you contain it and what do you change?

**Answer:**

**Containment (first hour):**
1. Identify the affected session(s) via audit logs: which `user_id`, which `session_id`, which tool calls were made, what data was accessed.
2. Revoke the API key or session token involved. If a tool (e.g., database query function) was exploited, temporarily disable that tool.
3. Assess blast radius: what data could the model have accessed through its granted tools? Was it user-specific data or shared data? Notify your security and legal teams per your incident response plan.
4. Preserve evidence: freeze the relevant logs and traces before any rotation or cleanup.
5. Patch the immediate vector: if the injection came via a specific input field, add a validation block on that field.

**Structural prevention:**

**Input filtering:** Deploy a prompt injection detector at the gateway (regex patterns for known injection phrases: "ignore previous instructions", "you are now", "show me your system prompt", delimiter injections). Flag or block high-confidence detections. Use Azure AI Content Safety or a dedicated guardrails model (e.g., Llama Guard, Bedrock Guardrails) for higher accuracy at the cost of latency.

**Least-privilege tool design:** The model should only have access to tools it needs for the current task. Never give a customer-facing chatbot a tool with `SELECT *` on arbitrary tables. Scope tool permissions: the database query tool should only return data scoped to the authenticated user's `tenant_id`. Even a fully successful injection should not be able to reach data it is not authorized to access.

**Output filtering:** Scan model outputs for PII patterns (email, SSN, credit card regexes) and secrets (API key patterns) before returning to the client. A model that was injected and asked to exfiltrate data must pass through this filter.

**Allow-list for tool inputs:** Instead of accepting arbitrary SQL or arbitrary file paths from the model, use structured tool schemas with validated enum inputs. The model picks from a predefined list of allowed operations.

**Audit logging:** Log every tool call with its inputs and outputs, tagged to `session_id` and `user_id`. This is non-negotiable for post-incident forensics and for compliance (SOC 2, HIPAA).

**Defense in depth — the key principle:** No single layer stops all injections. The combination of input filtering + least-privilege tools + output filtering + audit logs means a successful injection still has a very narrow blast radius.

---

### Leadership & Behavioral

#### Q: How do you set and enforce per-team LLM cost budgets without blocking innovation?

**Answer:** The goal is guardrails, not gates. Teams should be able to move fast and still know when they are about to exceed their budget.

**Setting budgets:** Start from observed data, not estimates. Run pay-per-token for 4–6 weeks across teams, then set initial budgets at 120% of each team's P75 monthly spend. This gives headroom for growth without enabling unchecked runaway costs.

**Enforcement tiers (not a hard wall):**
- **80% of budget:** automated alert to the team's engineering lead and product manager. No action required, just visibility.
- **90% of budget:** soft throttle — the gateway routes that team's requests to cheaper fallback models instead of blocking them. The team still functions, just at lower quality.
- **100% of budget:** the team lead gets a real-time alert with a self-service button to request an emergency budget increase (approved async by a cost committee, not requiring an on-call engineer). Optional: hard block on non-interactive (batch) workloads only, preserve interactive features.

**Enabling innovation:** Teams should be able to run experiments in a designated "sandbox" environment with a separate small budget (e.g., $50/month) that does not count against their production budget. This lets them prototype without fear of triggering alarms.

**Visibility over control:** A real-time dashboard showing each team's current spend, projected monthly total, top-cost endpoints, and cache hit rate is more valuable than hard blocks. Teams self-correct when they can see the cost.

**Regular cadence:** Monthly cost review with each team — show them their top 3 cost drivers and one specific optimization recommendation (e.g., "your `/api/summarize` endpoint has 8% cache hit rate; moving the system prompt to a cached prefix would save 40%"). This creates a culture of cost ownership rather than top-down enforcement.

#### Q: Tell me about a time you led a cost-reduction initiative that ran into a quality constraint (STAR).

**Answer (model STAR structure):**

**Situation:** At peak, our LLM-powered document analysis service was spending $45K/month. 80% of that was on a single GPT-4 deployment used for all document tasks, from simple classification ("is this a contract or an invoice?") to complex clause extraction. The business needed a 40% cost reduction without degrading user-facing quality scores.

**Task:** I led a team of three engineers to design and implement a model routing and caching strategy. I was responsible for the technical design, stakeholder alignment on quality thresholds, and the rollout plan.

**Action:** We ran a two-week analysis phase first. We logged every request with its model, token count, and downstream user satisfaction signal (thumbs up/down). We found 60% of requests were simple classification tasks that correlated with a complexity score below a threshold.

I proposed routing these to GPT-3.5. The initial A/B test showed a 22% drop in user satisfaction on the "simple" bucket — worse than expected. Rather than rolling back, I dug into the failures. The issue was not the model; it was that the routing classifier was miscategorizing ambiguous documents as "simple." We spent a week improving the classifier (adding a confidence threshold — route to GPT-4 if classifier confidence < 0.8, even for "simple" tasks).

Re-ran the A/B test: user satisfaction delta dropped to 1.2%, which was within our pre-agreed acceptable range (< 2% delta). We also implemented provider-native prompt caching for the large reference schema we were including in every system prompt (saving 30% on input tokens independently of the routing).

**Result:** Total cost reduced from $45K to $23K/month — a 49% reduction, exceeding the 40% target. User satisfaction held within threshold. The routing classifier and caching layer are now standard components in our platform template for any new LLM service. The key learning: always separate the routing accuracy problem from the model quality problem. A bad classifier blamed on the cheaper model will kill a valid cost initiative.

---

> 🎯 **Staff/Principal stretch:** Define the LLMOps platform roadmap and the build-vs-buy decisions (gateway, eval, observability) for a company scaling from 5 to 100 LLM features.

**Answer:** The core principle at this scale is that platform investment must stay ahead of adoption. The worst outcome is 100 features each building their own gateway, observability, and eval — you get 100 snowflakes, no visibility, and no ability to enforce policy.

**Phase 1 (5–20 features): Thin platform, maximum observability**

Buy over build. The goal is to centralize observability without blocking teams.

- **Gateway:** Deploy an open-source or commercial LLM gateway (LiteLLM, Portkey, or Azure APIM with LLM policies). Buy, do not build. Mandate that all LLM calls route through it. Implement auth, per-team cost attribution, and basic rate limiting. Time to value: 2 weeks.
- **Observability:** Use a managed LLM observability tool (LangSmith for LangChain-heavy teams, Helicone or Langtrace for provider-agnostic). Buy. Custom Grafana dashboards for cost and latency, fed from gateway logs. Do not build a custom tracing system at this stage.
- **Eval:** Use LangSmith eval datasets or simple pytest-based golden-set regression tests per feature team. No centralized eval platform yet — it is premature.

**Phase 2 (20–50 features): Platform hardening**

The shared infrastructure becomes load-bearing. Now the build-vs-buy calculus shifts.

- **Gateway:** The commercial gateway's cost or feature gaps become visible. Consider building a thin internal gateway on top of it (or replacing it with a custom one) if: (a) you need deep custom routing logic, (b) the vendor's pricing exceeds the engineering cost, or (c) compliance requires full control of the traffic path. Otherwise, keep buying.
- **Observability:** Build a custom cost attribution and budgeting layer (the commercial tools do not model per-team chargebacks well). Feed it from gateway telemetry. Everything else (metrics, traces): keep buying (Datadog or Azure Monitor).
- **Eval:** Build a centralized eval service. This is the most important build decision at this phase. You need: a shared benchmark dataset library, an LLM-as-judge harness, automated regression on every deployment, and a quality gate in CI/CD. No commercial product does this well for your specific use cases — build it. Timeline: 6–8 weeks for the core.
- **Prompt registry:** Build a versioned prompt store (Git-backed + API) so teams can manage prompt versions independently of code deploys. This pays for itself immediately.

**Phase 3 (50–100 features): Platform as a product**

The platform team functions like an internal product team with external (internal) customers.

- **Gateway:** Fully owned internally. Features: semantic cache, multi-provider failover, per-feature model routing policies, A/B traffic splitting managed through the gateway config.
- **Eval:** Mature eval platform with a shared LLM-as-judge model, human review queues for borderline cases, integration with the deployment pipeline (quality gate blocks promotion if score regresses > 2%).
- **Self-hosting decision:** At 100 features and high volume, run a cost analysis on whether self-hosting open-source models (LLaMA 3, Mistral) for commodity tasks (classification, embedding, summarization) is economically justified. The break-even is typically around 500M–1B tokens/month for a given task. Build a hybrid: managed APIs for frontier tasks (complex reasoning, new capabilities), self-hosted for commodity tasks.
- **Key build-vs-buy principle:** Buy commodities (logging pipelines, cloud infra, standard monitoring), build differentiators (routing policy engine, eval harness, prompt registry). The eval harness and routing policy engine are where your organization's LLM quality standards live — that is intellectual property worth owning.

---

## Summary

LLMOps specializes DevOps/MLOps for the cost, reliability, and security of LLM calls. The senior lever is the gateway — routing, fallback, caching, cost attribution — plus budgets and prompt-injection defenses that scale across the org.

## References

- Azure OpenAI — provisioned throughput: https://learn.microsoft.com/azure/ai-services/openai/concepts/provisioned-throughput
- Amazon Bedrock: https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html
- OWASP Top 10 for LLM Applications: https://owasp.org/www-project-top-10-for-large-language-model-applications/
