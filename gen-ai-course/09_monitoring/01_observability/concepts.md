# Observability — Concepts

You cannot operate what you cannot see. A GenAI service is a black box: it takes free-form text in and produces free-form text out, calls remote model providers you don't control, and fails in ways a status code rarely captures. **Observability** is the practice of instrumenting that box so you can answer questions about its behaviour — including questions you didn't anticipate. This file covers the three pillars, the metrics that matter for LLMs, how to summarise latency honestly, how to track cost, and how to turn all of it into alerts and dashboards.

---

## 1. The Three Pillars

Observability classically rests on three complementary signal types. Each answers a different question.

| Pillar | Question it answers | Granularity | LLM-specific content |
|---|---|---|---|
| **Metrics** | *How much / how fast / how often?* | Aggregated numbers over time | Token counts, latency percentiles, cost, error rate |
| **Logs** | *What exactly happened in this event?* | One record per event | Prompt/response pairs, tool calls, error detail |
| **Traces** | *Where did the time go across the chain?* | One tree per request | Retrieval span → rerank span → generation span |

```
        ┌──────────────────────────────────────────────┐
        │              One LLM Request                  │
        └──────────────────────────────────────────────┘
              │              │                │
              ▼              ▼                ▼
        ┌──────────┐  ┌────────────┐  ┌──────────────┐
        │ METRICS  │  │   LOGS     │  │   TRACES     │
        │ counters │  │ structured │  │ span tree:   │
        │ + histos │  │ JSON event │  │ retrieve →   │
        │ (cheap,  │  │ (rich, per │  │ rerank →     │
        │ aggregate)│ │  event)    │  │ generate     │
        └──────────┘  └────────────┘  └──────────────┘
```

### Monitoring vs Observability

These terms are often conflated but are not the same:

| Aspect | Monitoring | Observability |
|---|---|---|
| **Targets** | Known unknowns ("is error rate high?") | Unknown unknowns ("why is *this* user slow?") |
| **Approach** | Predefined dashboards + alerts | Ad-hoc exploration of raw signals |
| **Question style** | "Is X broken?" | "Why is X broken?" |
| **Primary tools** | Metrics, alerts | High-cardinality logs, traces |

You need both: monitoring catches the fire, observability lets you find what lit it.

### Why LLM observability differs from traditional ML

Traditional ML returns a structured, deterministic prediction you can score against a label. LLM systems generate free-form text, chain multiple model calls, invoke tools, and retrieve context — so a request can be "200 OK" yet completely wrong.

```
Traditional ML:  Input ──► Model ──► Prediction ──► compare to label

LLM system:      Input ─► Prompt ─► LLM ─► Tool ─► Retrieve ─► LLM ─► Output
                          (each arrow is a place latency, cost, and
                           quality can silently degrade)
```

This is why LLM observability adds **quality** and **cost** signals on top of the usual operational ones.

---

## 2. LLM-Specific Metrics

Split your metrics into **operational** (is the service healthy?) and **quality** (are the answers good?).

### Operational metrics

| Metric | Description | Healthy range | Alert when |
|---|---|---|---|
| **Latency P50** | Median response time | < 1 s | > 2 s |
| **Latency P99** | Tail response time | < 5 s | > 15 s |
| **Throughput** | Requests / second | Capacity-dependent | < SLA minimum |
| **Error rate** | failed / total | < 0.1% | > 1% |
| **Timeout rate** | timed-out / total | < 0.5% | > 2% |
| **Tokens / request** | input + output tokens | Workload-dependent | 3× baseline spike |
| **Cost / request** | USD per inference | Model-dependent | 2× baseline |

### Quality metrics

| Metric | What it measures | How it is measured |
|---|---|---|
| **Hallucination rate** | Factual errors / fabrications | LLM-as-judge, RAG faithfulness, human eval |
| **Relevance score** | Answer matches the query | Embedding similarity, LLM scoring |
| **Coherence score** | Internally consistent text | LLM-as-judge |
| **Toxicity score** | Harmful content | Classifier / moderation API |
| **User satisfaction** | Explicit feedback | Thumbs up/down, CSAT |
| **Task completion** | End-to-end success | Outcome tracking |

Quality metrics are expensive (they often need another model call), so they are typically computed on a **sample** of traffic, not every request.

---

## 3. Latency Percentiles — Why the Average Lies

Averages hide the worst experiences. If 99 requests take 1 s and one takes 60 s, the mean is ~1.6 s — which sounds fine while one user waited a full minute. **Percentiles** describe the distribution honestly.

```
P50 (median)  ── half of requests are faster than this
P95           ── 95% are faster; the slowest 1-in-20 is worse
P99           ── 99% are faster; the worst 1-in-100 tail
P99.9         ── extreme tail; matters at high request volume
```

| Percentile | Reads as | Who feels it |
|---|---|---|
| **P50** | "typical user" | Everyone's median experience |
| **P95** | "a bad day" | 1 in 20 requests |
| **P99** | "the tail" | 1 in 100 — power users, retries, big prompts |

Computing a percentile from a sorted list is simple — sort the samples and index by rank:

```python
def percentile(values: list[float], p: float) -> float:
    """p in [0, 100]. Nearest-rank method on a sorted copy."""
    if not values:
        raise ValueError("no samples")
    ordered = sorted(values)
    # rank: smallest index whose position covers p% of the data
    k = max(0, min(len(ordered) - 1, int(round((p / 100) * len(ordered) + 0.5)) - 1))
    return ordered[k]

lat = [120, 130, 140, 150, 900]   # ms; one slow tail request
print(percentile(lat, 50))  # 140  -> typical
print(percentile(lat, 99))  # 900  -> the tail the average hid
```

> Tail latency dominates user perception in agentic systems, because a single slow step in a 5-step chain blows the whole request budget. Always alert on P95/P99, not the mean.

---

## 4. Cost Metrics

LLM cost is usage-based: you pay per token, with different prices for input and output. Cost monitoring prevents bill shock and exposes inefficiency (runaway loops, oversized prompts, expensive models on cheap tasks).

```
cost = (input_tokens  / 1000) * input_price_per_1k
     + (output_tokens / 1000) * output_price_per_1k
```

| Model (illustrative) | Input $/1K | Output $/1K |
|---|---|---|
| gpt-4o-mini | 0.00015 | 0.0006 |
| gpt-4o | 0.0025 | 0.010 |
| claude-3-sonnet | 0.003 | 0.015 |
| claude-3-opus | 0.015 | 0.075 |

```python
PRICING = {  # (input_per_1k, output_per_1k) USD
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o": (0.0025, 0.01),
}

def estimate_cost(model: str, in_tok: int, out_tok: int) -> float:
    p_in, p_out = PRICING.get(model, (0.01, 0.03))   # default = expensive
    return (in_tok * p_in + out_tok * p_out) / 1000
```

Slice cost by **model**, **feature**, and **tenant/customer** so you can attribute spend and spot the 5% of users driving 80% of the bill. Output tokens are usually 3–5× the price of input tokens, so verbose responses are a hidden cost driver.

---

## 5. Alerting on SLOs

An **SLO** (Service Level Objective) is a target like "99% of requests succeed" or "P99 latency < 5 s". Alert when you are *burning the error budget*, not on every blip.

```yaml
# prometheus/alert-rules.yml  (illustrative)
groups:
  - name: llm_service
    rules:
      - alert: HighErrorRate
        expr: rate(llm_errors_total[5m]) / rate(llm_requests_total[5m]) > 0.01
        for: 2m
        labels: { severity: critical }
        annotations: { summary: "LLM error rate exceeds 1%" }

      - alert: HighLatencyP99
        expr: histogram_quantile(0.99, rate(llm_request_duration_bucket[5m])) > 15000
        for: 5m
        labels: { severity: warning }

      - alert: CostSpike
        expr: rate(llm_cost_total[1h]) > 2 * rate(llm_cost_total[1h] offset 24h)
        for: 30m
        labels: { severity: warning }
```

Good alerts are **actionable** (a human can do something), **symptom-based** (alert on user-visible pain, not CPU), and resistant to **alert fatigue** (use `for:` durations to suppress flapping).

---

## 6. Dashboard Design

A monitoring dashboard should answer "is the service healthy?" in five seconds, then let you drill down. Lead with the four golden signals (rate, errors, latency, saturation) plus LLM cost and quality.

```
┌─────────────────────────────────────────────────────────────┐
│                  LLM Service Overview                        │
├────────────┬────────────┬────────────┬─────────────────────┤
│ Req Rate   │ Error Rate │ Avg Latency│  Hourly Cost (USD)   │
│  142 rps   │   0.12%    │   1.2 s    │   $12.45             │
├────────────┴────────────┴────────────┴─────────────────────┤
│  Latency:  P50 0.8s   P95 3.5s   P99 8.2s                   │
├─────────────────────────────────────────────────────────────┤
│  Tokens by model     │  Quality (sampled)                   │
│  gpt-4o ███████ 1.2M │  relevance 0.92  hallucination 0.03  │
├──────────────────────┴───────────────────────────────────────┤
│  Errors by type:  timeout 45% │ rate-limit 30% │ other 25%   │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Managed Tracing: LangSmith & Langfuse

You can build all of this yourself, but managed platforms give you traces, evals, and cost tracking out of the box. They wrap each request in a trace and each sub-step (retrieval, generation) in a span.

| Tool | Niche | Strengths |
|---|---|---|
| **LangSmith** | LangChain ecosystem | Deep tracing, dataset-based evals, prompt playground |
| **Langfuse** | Open-source, framework-agnostic | Self-hostable, strong cost tracking, prompt management |
| **Arize / Phoenix** | ML + LLM observability | Embedding drift, evaluation at scale |
| **OpenTelemetry** | Vendor-neutral standard | Instrument once, export anywhere |

```python
# Langfuse: a trace with nested spans (illustrative — needs keys + network)
from langfuse import Langfuse
lf = Langfuse()                       # reads keys from env
trace = lf.trace(name="rag-query", user_id="u-123")
span = trace.span(name="retrieval", input={"q": "what is RAG?"})
span.end(output={"docs": 3, "top_score": 0.95})
trace.generation(name="answer", model="gpt-4o",
                 usage={"input": 250, "output": 120})
lf.flush()
```

> These calls need API keys and network access, so the exercise in this subtopic uses a **local, offline metrics collector** instead — the same percentile, cost, and error-rate math these platforms run for you.

---

## Key Takeaways

- **Three pillars, three questions.** Metrics = how much/fast/often (cheap, aggregated); logs = what happened (rich, per-event); traces = where time went (per-request tree). LLM systems add quality and cost signals on top.
- **Observability ≠ monitoring.** Monitoring answers known questions with dashboards and alerts; observability lets you explore unknown ones from raw signals. Production needs both.
- **Percentiles, not averages.** Always report and alert on P50/P95/P99 latency — the mean hides the tail that users actually feel, especially in multi-step agent chains.
- **Track cost as a first-class metric.** Compute per-request cost from input/output tokens and slice it by model, feature, and tenant; output tokens dominate the bill.
- **Alert on SLOs and symptoms.** Make alerts actionable and use `for:` durations to avoid alert fatigue.
- **Buy or build.** LangSmith / Langfuse / OpenTelemetry give you tracing and evals out of the box, but the underlying math — percentiles, cost, error rate — is the same simple aggregation you'll implement in the exercise.
