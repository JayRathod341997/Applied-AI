# Cost Optimization — Concepts

LLM spend grows linearly with usage. Left unmanaged, a popular feature becomes a budget emergency. Cost optimization is the discipline of getting an *acceptable* answer for the *fewest dollars*, applied at three layers: the **prompt**, the **model**, and the **architecture**.

This document walks through the levers and shows the diagrams, tables, and snippets you need to reason about them.

---

## 1. Token Economics

You pay per token, and **input and output are priced separately** — output is typically 3–5x more expensive than input. This single fact drives most optimization decisions.

A token is roughly 4 characters or ~0.75 words of English. A 500-word prompt is ~650 tokens.

### Representative pricing (per 1M tokens)

| Model (tier) | Input $/1M | Output $/1M | Context | Relative cost |
|---|---|---|---|---|
| Frontier (e.g. GPT-4o / Claude Sonnet) | $2.50–$3.00 | $10.00–$15.00 | 128K–200K | 1x (baseline) |
| Mid (e.g. GPT-4o-mini) | $0.15 | $0.60 | 128K | ~6% |
| Small / fast (e.g. Claude Haiku) | $0.25 | $1.25 | 200K | ~9% |
| Self-hosted small (Llama 3 8B) | ~$0.07* | ~$0.07* | 8K | ~0.5% (*infra) |

> Prices move constantly — always check the live pricing page (see `references.md`). The *ratios* are what matter for design.

### Cost of a single request

```python
def cost_usd(in_tokens, out_tokens, price_in_per_1k, price_out_per_1k):
    return (in_tokens / 1000) * price_in_per_1k + (out_tokens / 1000) * price_out_per_1k

# 1,200 input + 400 output on a frontier model ($0.0025 in / $0.010 out per 1K)
print(cost_usd(1200, 400, 0.0025, 0.010))  # -> $0.007
```

That looks tiny. Multiply by 5 million requests/month and it is **$35,000**. Optimization is about that multiplier.

**Key implications:**
- Long system prompts that repeat on every call are pure waste — pay once in design, save forever.
- Capping `max_tokens` directly caps your most expensive line item.
- A chatty model that pads answers costs more than a terse one of equal quality.

---

## 2. Prompt Compression / Concise Prompting

The cheapest token is the one you never send.

| Technique | Typical savings | How |
|---|---|---|
| Shorter system prompts | 20–40% input | Strip verbose instructions, keep the essentials |
| Few-shot → zero-shot | 50–80% input | Fine-tune or use a stronger base model instead of examples |
| Structured output (JSON) | 10–30% output | Forces terse, parseable answers |
| `max_tokens` cap | Variable | Refuse to pay for rambling |
| Prompt caching | ~50–90% on cached prefix | Reuse a static prefix across calls (see §4) |

```python
# BAD: verbose, example-laden system prompt (~500 tokens, billed every call)
BAD = """You are a helpful assistant. When asked about weather respond like this:
Example 1: User: 'What's the weather?' -> 'Sunny, 72F'
Example 2: ... (many more) ..."""

# GOOD: concise + structured output (~25 tokens)
GOOD = "Weather assistant. Reply as JSON: {city, temp_f, condition}"
```

Prompt-compression tooling (e.g. **LLMLingua**) goes further, using a small model to drop low-information tokens from long contexts while preserving meaning — useful for RAG prompts stuffed with retrieved chunks.

---

## 3. Tiered / Cascade Model Routing

Not every query needs your most expensive model. **Route to the cheapest model that can handle the task, and escalate only when needed.** This is the single highest-leverage architectural lever (the FrugalGPT paper reports up to ~98% cost reduction at matched accuracy).

### Cascade router flow

```
                 ┌─────────────────────┐
   query ───────►│  complexity heuristic│
                 │ (length, keywords,   │
                 │  cheap classifier)   │
                 └─────────┬───────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      simple           medium            complex
          │                │                │
          ▼                ▼                ▼
   ┌────────────┐   ┌────────────┐   ┌────────────┐
   │ small/cheap│   │  mid model │   │  frontier  │
   │   model    │   │            │   │   model    │
   └─────┬──────┘   └─────┬──────┘   └────────────┘
         │ low confidence?│ low confidence?
         └───── escalate ─┴───── escalate ──────►
```

Two complementary escalation strategies:

1. **Up-front routing** — a cheap heuristic or classifier picks the tier *before* the call (length, keyword signals like "prove", "design", "debug", number of constraints).
2. **Confidence-based escalation** — call the cheap model first; if it returns low confidence, says "I don't know", or fails a verifier, retry on the expensive model.

```python
TIERS = ["small", "mid", "frontier"]

def route(query: str) -> str:
    """Up-front heuristic routing -> returns a tier name."""
    words = len(query.split())
    hard_kw = ("prove", "derive", "design", "architect", "debug", "optimize")
    score = 0
    if words > 60:            score += 2
    elif words > 20:          score += 1
    if any(k in query.lower() for k in hard_kw): score += 2
    if query.count("?") > 1:  score += 1
    return TIERS[min(score, 2)] if score else "small"
```

Watch the **escalation tax**: if you call cheap-then-expensive, you pay for *both*. Cascades only win when the cheap tier resolves a large fraction of traffic on its own.

---

## 4. Caching ROI

If the same (or semantically similar) request recurs, serving from cache costs near zero and milliseconds instead of dollars and seconds.

| Cache type | Matches on | Best for |
|---|---|---|
| **Exact-match** | Identical prompt string | FAQs, deterministic tools |
| **Semantic** | Embedding similarity | Paraphrased questions |
| **Prompt-prefix (provider)** | Shared static prefix | Long fixed system prompts / docs |

ROI is simple arithmetic:

```
savings = hit_rate * cost_per_call
cost    = cache_infra + embedding_cost (semantic only)

cache pays off  ⇔  savings > cost
```

A cache with a **<20% hit rate is usually not worth it** — it adds a lookup, an embedding call (if semantic), and a staleness risk for little gain. Always emit a `cache_hit_rate` metric so you can tell.

```python
cache = {}
def cached_call(prompt, llm):
    if prompt in cache:
        return cache[prompt]          # ~free, ~0ms
    out = llm(prompt)                  # full cost + latency
    cache[prompt] = out
    return out
```

---

## 5. Batch vs Real-Time Trade-offs

Many providers offer a **batch API at ~50% discount** in exchange for asynchronous (often up to 24h) turnaround. The trade is latency for money.

| Dimension | Real-time / sync | Batch / async |
|---|---|---|
| Price | Full | ~50% off |
| Latency | Seconds | Minutes to 24h |
| Use case | Chat, interactive UX | Nightly enrichment, bulk classification, evals, embeddings |
| Throughput | Rate-limited | Very high |
| UX coupling | User is waiting | No user waiting |

**Rule of thumb:** if no human is blocked waiting for the result, it is a batch candidate. Backfills, summarizing yesterday's tickets, generating embeddings for a corpus, and offline evals should almost always run on the batch tier.

```
  request ──► is a user blocked, waiting now?
                 │yes                  │no
                 ▼                     ▼
            real-time API        queue for batch API (½ price)
```

---

## 6. Right-Sizing Models

Right-sizing means matching model **capability to task difficulty** — the same idea as cloud instance right-sizing.

- Classification, extraction, routing, simple summarization → small/mid model.
- Multi-step reasoning, code generation, nuanced writing → frontier model.
- Don't pay frontier prices to label sentiment or extract a date.

Process:
1. Start on the cheapest tier that plausibly works.
2. Build an eval set with a quality bar.
3. Move *up* only until the bar is met — not "to be safe."
4. Re-evaluate when new, cheaper models ship (the frontier of "good enough" drops every few months).

```python
# Right-sizing by task type, not by habit
TASK_MODEL = {
    "classify":  "small",
    "extract":   "small",
    "summarize": "mid",
    "reason":    "frontier",
    "code":      "frontier",
}
```

---

## 7. Spend Monitoring & Budget-Alert Hooks

You cannot optimize what you do not measure. Treat **cost as a first-class telemetry signal** alongside latency and errors. This is the cost slice of observability: every LLM call should record its token counts and computed dollar cost as span attributes / metrics.

| Metric | Alert threshold | Why |
|---|---|---|
| `llm_cost_per_hour` | > budget * 1.2 | Cost overrun |
| `llm_tokens_per_request` (avg) | > expected + 50% | Prompt bloat / injection |
| `cache_hit_rate` | < 20% | Cache ineffective |
| `escalation_rate` | rising trend | Router sending too much to frontier |
| `cost_per_successful_task` | trending up | Efficiency regression |

A minimal **budget-alert hook** — accumulate spend and fire a callback when a threshold is crossed:

```python
class BudgetGuard:
    def __init__(self, monthly_budget, on_alert):
        self.budget = monthly_budget
        self.spent = 0.0
        self.on_alert = on_alert
        self._fired = set()

    def record(self, cost_usd):
        self.spent += cost_usd
        for pct in (0.5, 0.8, 1.0):
            if self.spent >= self.budget * pct and pct not in self._fired:
                self._fired.add(pct)
                self.on_alert(pct, self.spent, self.budget)

guard = BudgetGuard(1000, lambda p, s, b: print(f"ALERT {p:.0%}: ${s:.2f}/${b}"))
```

Tag every call with `model`, `feature`, and `tenant` so you can attribute spend, find the expensive 5% of traffic, and apply per-feature budgets. This is the AI-native side of **FinOps**.

---

## Key Takeaways

- **Output tokens cost 3–5x input** — cap output and prefer terse, structured responses.
- **The cheapest token is the one you never send** — compress prompts, prefer zero-shot, reuse static prefixes via prompt caching.
- **Cascade routing is the biggest lever** — cheap model first, escalate on low confidence or complexity; but beware paying twice (escalation tax).
- **Cache only pays off above ~20% hit rate** — measure the rate before trusting it.
- **If no user is waiting, use the batch API** for ~50% off.
- **Right-size by task difficulty**, backed by an eval set, and revisit as cheaper models ship.
- **Make cost a telemetry signal**: record per-call dollars, tag by feature/tenant, and wire budget-alert hooks before the bill surprises you.
