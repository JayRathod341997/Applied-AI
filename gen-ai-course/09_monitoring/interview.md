# Monitoring & Observability for GenAI — Interview Questions

Model answers on observability, drift detection, and logging for GenAI systems.

---

## 1. What do you monitor for an LLM app beyond standard service metrics?

**Answer:** Service (latency p50/p99, error rate, throughput) **plus** GenAI signals: token usage/cost, cache hit rate, retrieval quality, and **output quality** (faithfulness/groundedness, LLM-judge scores on sampled traffic), plus safety/guardrail trip rates. The dangerous regressions return 200 OK with worse answers.

## 2. How do you trace a single GenAI request end to end?

**Answer:** Correlation id across gateway → retrieval → LLM call(s) → post-processing; capture prompt version, model version, retrieved doc ids, token counts, and latencies per span. Tools: OpenTelemetry + Azure Monitor / App Insights (AWS: CloudWatch + X-Ray).

---

## Senior Deep Dive: Monitoring & Observability

> Senior roles own the signal that catches silent quality regressions and the cost/noise trade-off of telemetry. At this level, the conversation moves from "did you add a dashboard" to "how do you prove to the business that quality is acceptable, at scale, without burning the logging budget or the on-call rotation."

---

### System Design & Scale

#### Q: Design observability for 100M LLM calls/day without bankrupting on logging.

**Answer:** The constraint forces a tiered strategy — you cannot afford to store full traces or run LLM-judge on every request.

**Conclusion first:** Use sampling + aggregation + tiered retention. Only 1–5% of traffic needs full prompt/response traces; the rest contributes to aggregate metrics.

**Design:**

```
All 100M requests
        │
        ├── [Every request]  Emit lightweight metrics only:
        │     latency_ms, status, model, input_tokens, output_tokens,
        │     cost_usd, cache_hit, guard_trip — cheap counters/histograms
        │     → Azure Monitor / Prometheus (aggregate, no PII)
        │
        ├── [1% sample]      Full structured trace with prompt_hash,
        │     retrieved_doc_ids, LLM-judge score (async)
        │     → Azure Application Insights / hot store (7-day retention)
        │
        ├── [100% errors]    Always log full debug trace for failures
        │     → separate error store (30-day hot, 90-day warm)
        │
        └── [Async eval workers]  Pull from sampled queue, run
              faithfulness/relevance eval, write scores back
              → evaluation DB (long-term, for trend analysis)
```

**Tiered retention** keeps cost predictable:

| Log type | Hot (searchable) | Warm | Cold archive |
|---|---|---|---|
| Full prompt/response | 7 days | 30 days | 1 year |
| Error traces | 30 days | 90 days | 2 years |
| Eval scores | 30 days | 1 year | 3 years |
| Audit logs | 90 days | 1 year | 7 years |

**PII redaction at ingest** — strip emails, phones, API keys before the record crosses the process boundary. Store a `prompt_hash` (SHA-256) to deduplicate without storing raw text. At 100M calls/day, a PII leak into a third-party log store is a compliance incident at scale.

**Key insight:** Aggregate metrics answer "is anything wrong?" for free; full traces answer "why?" for 1% of calls. The sampling rate is a business parameter — tune it so you have enough statistical power to detect a 5% quality regression within an acceptable window.

---

#### Q: How do you compute a live quality metric at scale?

**Answer:** You cannot run synchronous LLM-judge on every request — it doubles latency and cost. The production pattern is async eval with a golden-set canary for continuous baseline coverage.

**Architecture:**

```
Request path (synchronous)
  User → Gateway → RAG pipeline → Response
                        │
                        └── Emit to eval queue (sampled, e.g. 2%)

Async eval workers (decoupled)
  eval queue → pull batch → run LLM-judge (faithfulness, relevance)
             → write scores → Azure Monitor custom metric
             → alert if rolling avg drops below SLO threshold
```

**Three complementary signals:**

1. **Sampled LLM-judge** — run a judge model (GPT-4o-mini is cheap enough) on 2% of live traffic. Metrics: faithfulness score, answer relevance, coherence. Aggregate into a rolling 1-hour window. Alert when the p25 drops — a quality regression shifts the whole distribution down.

2. **Golden-set canary** — a fixed set of 50–200 hand-labeled QA pairs re-evaluated on every model/prompt deployment. This catches regression instantly at deploy time, independent of live traffic distribution.

3. **User feedback signals** — thumbs up/down, CSAT, session abandonment. Cheap and noisy but catches things judge models miss (tone, trust).

**Custom metric to backend (Azure):**

```python
# Azure Application Insights custom event
from applicationinsights import TelemetryClient
tc = TelemetryClient(instrumentation_key)
tc.track_metric("rag_faithfulness_score", score,
                properties={"model": model_version, "prompt_version": prompt_v})
tc.flush()
```

**Insight:** The golden-set canary is the quality equivalent of a smoke test — it runs in CI and on every canary deploy. Sampled LLM-judge on live traffic catches regressions that golden-set misses because user intent has drifted.

---

#### Q: Describe a drift detection pipeline for embeddings and inputs.

**Answer:** Drift detection answers "have the inputs changed enough that model quality may have silently degraded?" The pipeline has four stages: collect, compare, alert, act.

**Stage 1 — Input distribution monitoring (feature-level)**

Compute PSI (Population Stability Index) on input features — query length, token count, top-N topic bins — over a rolling window against a baseline window captured at last deploy.

```
PSI = Σ_bins  (current% − baseline%) × ln(current% / baseline%)

PSI ≤ 0.10  →  stable, keep monitoring
0.10–0.20   →  investigate
> 0.20      →  significant drift, escalate
```

Always add an epsilon to every bin proportion to avoid `ln(0)` on empty bins.

**Stage 2 — Embedding drift (semantic-level)**

Compute the centroid of a baseline embedding batch and compare with the centroid of the current window using cosine distance. Rising cosine distance means query semantics are moving outside the distribution the index and prompts were calibrated on.

```
cosine_distance(centroid_baseline, centroid_current) > threshold  →  embedding drift alert
```

For RAG, this is the early-warning system: semantic drift predicts retrieval quality drops before users notice.

**Stage 3 — Reference window and thresholds**

The baseline window is anchored to the last stable deploy (or a rolling 7-day lag). The current window is typically 24 hours. Require the drift signal to **sustain** above the threshold for a configurable period (e.g., 2 hours) before alerting — this suppresses blips and seasonal patterns.

**Stage 4 — Paired quality confirmation**

Drift in inputs is not automatically degradation. Before triggering a retrain, confirm that output quality (LLM-judge scores, retrieval NDCG) has also declined. This avoids expensive retrains triggered by benign distribution shifts (seasonal topics, new user cohort).

```
Input PSI > 0.20  AND  quality metric drops > 10%  →  retrain trigger
Input PSI > 0.20  AND  quality stable              →  log + watch
```

---

### Trade-offs & Decisions

#### Q: How do you choose a sampling rate for quality evals — cost vs detection latency?

**Answer:** Sampling rate is a statistical power decision, not an arbitrary cost cut.

**Conclusion:** The minimum sampling rate is determined by how fast you need to detect a regression of a given size. More statistical power means a lower sampling rate can still detect large regressions; catching small regressions fast requires higher sampling.

**Framework:**

| Dimension | Lower sampling rate | Higher sampling rate |
|---|---|---|
| Cost | Cheaper — fewer judge calls | More expensive |
| Detection speed | Slower — need more time to accumulate samples | Faster |
| Minimum detectable effect | Only large regressions detectable | Small regressions detectable |
| False positive risk | Lower (more averaging) | Higher (noisier windows) |

**Practical starting points:**

- **2–5%** is a good default for most production systems. At 100M calls/day and 2%, that is 2M judge evaluations/day — still expensive. Batch them at off-peak hours.
- **1%** is viable if your primary quality signal is the golden-set canary. Live-traffic eval fills gaps, not the primary detection.
- **10–20%** for new launches, high-stakes use cases (legal, medical), or when a recent incident made you distrust the baseline.

**Async eval pattern:** Never run judge evals synchronously. Push sampled requests to a queue, drain with worker processes, write scores to a timeseries metric. Detection latency is queue depth / worker throughput — tune workers to keep this under your SLO for regression detection (e.g., < 1 hour).

**Key trade-off sentence:** Every doubling of sampling rate halves detection latency for a fixed regression size, but doubles eval cost — find the crossover where the cost of a missed regression (customer churn, escalation) equals the cost of faster detection.

---

#### Q: Should you log full prompts and responses, or redact?

**Answer:** Default to redacted logs with hashing, with full traces available for a sampled subset under access controls.

**Conclusion:** Full prompt/response logging gives you the richest debugging signal, but it is a PII liability at scale. The right answer is layered: redact by default, store full traces for a small sample with explicit access controls and time-bounded retention.

**Decision matrix:**

| Scenario | Recommendation |
|---|---|
| Production, uncontrolled user input | Redact PII at ingest; store `prompt_hash` |
| Internal/enterprise, known users | Tokenize (reversible) with access audit trail |
| Debugging a specific incident | Enable full trace for that `trace_id` only |
| Healthcare / finance (HIPAA, PCI) | Exclusion or encryption at rest + field-level tokenization |
| Eval dataset construction | Full capture on opted-in or synthetic traffic only |

**PII redaction patterns (redact before the record leaves the process):**

- Emails, phone numbers, SSNs, credit card numbers — regex pattern matching
- API keys (`sk-...`, `Bearer ...`) — high-entropy string patterns
- Store `SHA-256(prompt)` as `prompt_hash` — deduplicate without storing text
- Order matters: run specific high-entropy patterns before broad numeric ones

**Debuggability vs compliance balance:**

Structured metadata (model, latency, token counts, retrieval doc IDs, status code) gives you 80% of debugging value with zero PII exposure. Full text is only needed for "the answer was wrong in an unexpected way" — which is a sampled, access-controlled, short-retention use case.

---

#### Q: Build your own observability stack vs buy an LLM observability tool (LangSmith, Arize, Langfuse, etc.)?

**Answer:** Default to a managed tool for the first 12 months; build custom where the managed tool cannot reach your data residency, custom metrics, or integration requirements.

**Conclusion:** Managed tools ship traces, LLM-judge evals, cost tracking, and prompt management in days. The build path takes months and you are rebuilding commodity infrastructure. Build when you have specific needs the tools cannot meet.

**Buy side (LangSmith / Langfuse / Arize):**

- Traces with span trees out of the box — retrieval, rerank, generation
- LLM-judge eval pipelines with dataset management
- Cost tracking per model/user/feature
- Prompt version management and A/B testing

**Build side (OpenTelemetry + Azure Monitor / custom):**

- Full control over data residency and compliance (no third-party SaaS)
- Custom quality metrics the tools do not expose
- Integration with existing enterprise monitoring (Azure Monitor, Datadog, Splunk)
- No per-trace SaaS cost at 100M+ calls/day

**Lock-in mitigation:** Instrument with OpenTelemetry spans regardless of which backend you choose. OpenTelemetry is vendor-neutral — the same instrumentation exports to Jaeger, Langfuse, Azure Monitor, or Datadog. This preserves optionality without the full build cost.

**Practical approach at senior/staff level:** Start with Langfuse (self-hostable, open-source) or LangSmith. As you scale past 10M calls/day and the per-trace cost or data-residency requirements bite, extract the core metrics to Azure Monitor and retire the managed tool for high-volume paths while keeping it for eval and prompt management.

---

### Failure Modes & Incidents

#### Q: Quality dropped but all dashboards are green. Why, and how do you fix the gap?

**Answer:** The root cause is missing quality signal — the dashboards only measure infrastructure health, not answer correctness.

**Conclusion:** A "green dashboard" usually means you are monitoring latency, error rate, and throughput — none of which detect a prompt regression, a retrieval quality drop, or a silent model version change.

**Why the gap exists:**

- LLM systems return HTTP 200 even when the answer is wrong, incoherent, or hallucinated
- Standard service metrics (latency, error rate) measure plumbing, not semantics
- If the only quality signal is user feedback (thumbs down), detection latency is hours to days

**Common causes of silent quality regression:**

1. Prompt template changed — introduced a subtle regression
2. Model provider silently bumped the model version
3. Knowledge base / vector index became stale (embedding drift)
4. Retrieval top-K reduced for cost, degrading answer grounding
5. A dependent service changed its output format, breaking the chain

**How to fix the gap:**

1. **Add an LLM-judge metric** (faithfulness, relevance) on sampled traffic → custom metric in Azure Monitor with an SLO alert
2. **Golden-set canary** — 50–200 labeled QA pairs evaluated at every deploy and on a daily schedule; alert when pass rate drops > 5%
3. **Retrieval quality metric** — track mean NDCG or top-1 relevance score per retrieval span
4. **Prompt/model version tracking** — emit `prompt_version` and `model_version` as metric dimensions so you can correlate quality drops with deploys

**Detection timeline after fix:**

```
Deploy → golden-set eval runs in CI → catches regression before prod
Live traffic → sampled LLM-judge → 1-hour rolling quality metric → SLO alert fires
```

---

#### Q: Alert fatigue — the on-call team is getting paged on noise. What is the senior fix?

**Answer:** Move from threshold alerts to SLO-based burn-rate alerts, add severity tiers, and deduplicate at the alerting layer.

**Conclusion:** Most alert fatigue comes from alerting on instantaneous metric values rather than on error budget consumption rate. An SLO burn-rate alert fires only when you are consuming your error budget fast enough to exhaust it.

**Root causes of alert fatigue:**

- Alerting on every spike above a static threshold (too sensitive)
- No `for:` sustain window — transient blips page on-call
- All alerts routed to the same channel at the same severity
- Missing deduplication — the same condition fires ten alerts

**SLO-based burn-rate approach:**

An SLO of 99.9% availability gives an error budget of 0.1% = ~8.6 hours/month. A burn rate of 1x depletes the budget in 30 days (acceptable). A burn rate of 14.4x depletes it in 1 hour (page immediately).

```yaml
# Illustrative — Azure Monitor / Prometheus burn-rate alert
- alert: ErrorBudgetBurnRateFast
  expr: |
    (
      rate(llm_errors_total[1h]) / rate(llm_requests_total[1h])
    ) / (1 - 0.999) > 14.4
  for: 5m
  labels: { severity: critical }
  annotations:
    summary: "Burning error budget at 14.4x — exhausts in < 1h"
```

**Severity tiers and routing:**

| Tier | Burn rate | Detection window | Action |
|---|---|---|---|
| Page now | > 14.4x | 1 hour | Wake on-call |
| Ticket | > 6x | 6 hours | Slack + ticket |
| Watch | > 3x | 24 hours | Dashboard annotation |

**Deduplication:** Group related alerts (latency spike + error spike from the same deploy) into one incident. Azure Monitor alert groups / PagerDuty event intelligence handle this. One incident per root cause, not one alert per symptom.

**Quality alert deduplication:** A quality regression usually fires simultaneously on faithfulness, relevance, and user feedback signals. Route all three to one incident with the deploy context attached.

---

#### Q: A drift alert fired. Walk me through the triage.

**Answer:** The triage follows four steps: confirm real drift, scope it, correlate with changes, decide action.

**Conclusion:** Not every drift alert is a problem requiring immediate action — the first question is whether quality has actually degraded or whether this is a benign distribution shift.

**Step 1 — Confirm it is real drift, not noise or seasonal variation**

- Check whether the alert sustained past the `for:` window (not a blip)
- Look at the last 7 and 30 days — is this a weekly pattern (e.g., weekend traffic is different)?
- Compare PSI score trend — is it climbing steadily or was it a one-off spike?
- Check embedding centroid distance — corroborating drift in semantic space strengthens the case

**Step 2 — Scope it**

- Which features drifted? Query length? Topic distribution? Language?
- Is it all users or a specific cohort/tenant?
- Is it correlated with a specific time of day, region, or product surface?
- How large is the affected window (% of traffic, absolute volume)?

**Step 3 — Correlate with deployments and data changes**

- Did a deploy go out in the window before drift started? (Check deploy log)
- Did the knowledge base / vector index get updated?
- Did the upstream data source change schema or content?
- Did the model provider announce or silently apply a model update?

**Step 4 — Check output quality**

Input distribution drift alone is not sufficient to act. Confirm that quality metrics (LLM-judge scores, retrieval NDCG, user feedback) have also declined. If quality is stable, the drift is benign — log it, widen the baseline window, and continue monitoring.

**Decision matrix:**

| Drift confirmed | Quality degraded | Action |
|---|---|---|
| Yes | Yes | Investigate root cause → rollback, retrain, or refresh index |
| Yes | No | Log + annotate baseline; likely benign population shift |
| No (blip) | Yes | Quality incident, not drift — different triage path |
| No (blip) | No | False positive; tune alert threshold or sustain window |

**Rollback vs retrain:** If a deploy correlates cleanly, rollback is fastest. If the drift is gradual (input distribution evolved), retrain or refresh the knowledge base on a current data snapshot. Always deploy the fix as a canary first, validate golden-set scores, then promote.

---

### Leadership & Behavioral

#### Q: How do you establish SLOs and error budgets with product stakeholders who don't know what a percentile is?

**Answer:** Translate technical metrics into user-visible promises, then work backward to the numbers.

Start with the user experience, not the metric: "99% of answers will come back within 5 seconds" and "fewer than 1 in 200 questions will get a wrong or incoherent answer." These are statements a PM can take to customers.

Then make the error budget concrete: "Our 99.9% availability target gives us 8.6 hours of downtime budget per month. At our current traffic level, that is about 86,000 failed requests. Right now we are spending that budget at a rate of X." Budget framing turns SLOs from engineering constraints into shared business resources — burning the budget fast affects the product team's roadmap (no new feature deploys until the budget recovers).

Practical approach:

- Run a 30-minute workshop with PM and engineering. Show the last 90 days of error rate and latency on one slide. Ask: "What user experience are we promising?" Let them set the aspiration; help them understand the cost of tighter SLOs (faster incident response, more redundancy, less deployment velocity).
- Agree on two SLOs: one infrastructure (availability/latency) and one quality (LLM-judge pass rate). Quality SLOs are new to most PMs — introduce them as "answer quality guarantee."
- Publish a live SLO dashboard accessible to product. Shared visibility removes the "engineering hid it" dynamic and creates joint accountability.

The error budget becomes a forcing function: when budget runs low, the engineering team has a principled reason to say "no more feature deploys this sprint" that the business can understand and accept.

---

#### Q: Tell me about a time you led an incident where observability gaps slowed the fix. (STAR)

**Answer (STAR template — adapt to your own experience):**

**Situation:** A RAG-based enterprise search product had been live for three months. Customer support escalations started increasing — users reporting "the answers are worse lately." No alerts had fired; all dashboards were green.

**Task:** As the senior engineer on-call, I needed to identify the root cause, fix it, and prevent recurrence. The immediate blocker was that we had no quality signal in our monitoring stack — we were flying blind on answer correctness.

**Action:**
First, I added temporary verbose logging (full prompt/response on 10% of traffic, PII-redacted) and ran a manual LLM-judge evaluation on a 200-sample batch pulled from the past 48 hours. Faithfulness score had dropped from 0.89 to 0.71 — a significant regression that had been invisible to our infrastructure metrics.

I traced the drop to a knowledge base refresh that had silently introduced chunking artifacts — chunks were being split at sentence boundaries in a way that removed context. The retrieval pipeline was returning high-similarity but context-poor chunks.

I fixed the chunking strategy, rebuilt the index on a maintenance window, and ran our golden-set (which we had, but had not wired into CI). Golden-set pass rate recovered to baseline.

The harder problem was the observability gap. Over the next sprint, I shipped: (1) async LLM-judge on 2% of live traffic as a custom metric in Azure Monitor, (2) a golden-set CI gate that blocked deploys if pass rate dropped > 5%, (3) a retrieval quality metric (mean top-1 relevance score) as a dedicated dashboard panel.

**Result:** The next knowledge base update three weeks later triggered a golden-set alert in CI before it reached production. The regression was caught in 8 minutes rather than three days. The incident also became the catalyst for the team's first formal quality SLO, which we agreed with the PM within two sprints.

**Reflection:** The gap was predictable — we had instrumented what was easy (HTTP metrics) and skipped what was hard (semantic quality). The lesson I apply now: quality metrics are day-one requirements, not post-incident retrofits.

---

> **Staff/Principal stretch:** Define the org-wide observability standard — required spans, metrics, and quality evaluations that every GenAI service must emit.

**Answer:** At staff/principal level, the goal is a contract — a spec that any team building a GenAI service can implement independently, producing signals that roll up into a single org-wide quality and cost view.

**Required spans (OpenTelemetry, minimum viable):**

Every GenAI service must emit the following spans on every request:

| Span name | Required attributes |
|---|---|
| `genai.request` (root) | `trace_id`, `request_id`, `prompt_version`, `model`, `model_version`, `feature_name`, `tenant_id` |
| `genai.retrieval` | `retrieval.top_k`, `retrieval.mean_score`, `retrieval.source` |
| `genai.generation` | `llm.input_tokens`, `llm.output_tokens`, `llm.cost_usd`, `llm.latency_ms` |
| `genai.guardrails` | `guard.trip` (bool), `guard.category` (if tripped) |

**Required metrics (emit on every request, no sampling):**

```
genai_request_total                  {model, feature, status}
genai_latency_ms                     histogram {model, feature}  (p50/p95/p99)
genai_tokens_total                   {model, feature, type=input|output}
genai_cost_usd_total                 {model, feature, tenant}
genai_guard_trip_total               {category}
genai_cache_hit_total                {feature}
```

**Required quality evaluations (async, on 2% sampled traffic minimum):**

```
genai_faithfulness_score             gauge, rolling 1-hour p25/p50
genai_relevance_score                gauge, rolling 1-hour p50
genai_golden_set_pass_rate           gauge, per-deploy CI gate + daily schedule
```

**Required SLOs (org-wide defaults, teams may tighten):**

- P99 latency < 15 s
- Error rate < 1%
- Quality SLO: golden-set pass rate > 90%, faithfulness p50 > 0.80

**Enforcement:**

- SDK wrapper library ships the instrumentation — teams import the library, not the spec. One implementation, one upgrade path.
- CI gate: deploy pipeline queries golden-set pass rate; blocks on < 90%
- Service mesh / API gateway validates that required span attributes are present at deploy registration
- Monthly observability review: any service missing required metrics is flagged to its engineering manager

**Why this matters at org scale:** Without a standard, each team reinvents telemetry with different field names, different sampling rates, and different quality definitions. You cannot answer "how is GenAI quality across the org this quarter?" A standard makes that a single query.

---

## Summary

GenAI observability adds quality and cost signals on top of service metrics — and the senior skill is catching silent quality regressions cheaply, with SLO-based alerting and an org-wide telemetry standard.

## References

- OpenTelemetry: https://opentelemetry.io/docs/
- Google SRE — Service Level Objectives: https://sre.google/sre-book/service-level-objectives/
- Azure Monitor / Application Insights: https://learn.microsoft.com/azure/azure-monitor/
