# Cost Optimization — Interview Questions

### Q1: Why are input and output tokens priced differently, and how does that affect design?

**Answer:** Output tokens are generated autoregressively — each one requires a full forward pass conditioned on everything before it — so they are far more expensive to produce than input tokens, which are processed in a single batched pass. Providers reflect this with output prices typically 3–5x the input price.

| Token type | Relative price | Design response |
|---|---|---|
| Input | 1x | Compress prompts, reuse static prefixes |
| Output | 3–5x | Cap `max_tokens`, prefer terse/structured output |

The practical takeaway: trimming output is usually the highest-value-per-effort lever.

---

### Q2: Walk me through cascade (tiered) model routing. Why does it save so much?

**Answer:** Instead of sending every query to your most capable (expensive) model, you route each one to the cheapest model that can handle it, escalating only when needed. Real traffic is heavily skewed — most queries are easy. If a small model that costs ~6–9% of the frontier model resolves 70–80% of requests acceptably, your blended cost collapses. FrugalGPT reported up to ~98% cost reduction at matched accuracy using cascades plus scoring. Two escalation strategies: up-front heuristic/classifier routing, and confidence-based escalation (cheap first, retry expensive on low confidence).

---

### Q3: What is the "escalation tax" and when does a cascade stop being worth it?

**Answer:** In a confidence-based cascade you call the cheap model, and if it fails you *also* call the expensive one — paying for both. The expected cost per query is `cheap_cost + (1 - resolve_rate) * expensive_cost`. If the cheap tier only resolves a small fraction, you pay nearly the full expensive price *plus* the cheap call's overhead, and the cascade is worse than going straight to the expensive model. Cascades win only when the cheap tier has a high standalone resolve rate. Up-front routing avoids the double-pay but risks misrouting hard queries to a weak model.

---

### Q4: How do you decide whether a cache is worth deploying?

**Answer:** It's arithmetic: `savings = hit_rate * cost_per_call` versus `cost = infra + (embedding_cost for semantic caches)`. Below roughly a 20% hit rate, the lookup overhead, embedding cost, and staleness risk usually outweigh savings. I always instrument `cache_hit_rate` before trusting a cache. Cache type matters too:

| Type | Matches on | Good for |
|---|---|---|
| Exact | identical prompt | FAQs, deterministic tools |
| Semantic | embedding similarity | paraphrased queries |
| Prompt-prefix (provider) | shared static prefix | long fixed system prompts |

---

### Q5: When would you choose a batch API over real-time inference?

**Answer:** Whenever no human is blocked waiting for the result. Batch APIs offer ~50% discounts in exchange for asynchronous turnaround (up to ~24h). Ideal candidates: generating embeddings for a corpus, nightly ticket summarization, dataset labeling, and offline evals. Interactive chat, autocomplete, and real-time fraud checks must stay on the synchronous tier because latency is part of the product.

---

### Q6: What does "right-sizing" a model mean and how do you do it methodically?

**Answer:** Matching model capability to task difficulty rather than defaulting to the biggest model "to be safe." Method: (1) start on the cheapest tier that plausibly works; (2) build an eval set with an explicit quality bar; (3) move *up* tiers only until the bar is met; (4) re-evaluate when cheaper models ship, since the "good enough" frontier drops every few months. Classification/extraction/routing usually fit small models; multi-step reasoning and code generation need frontier models.

---

### Q7: A feature's monthly LLM bill tripled overnight. How do you debug it?

**Answer:** I rely on per-call cost telemetry tagged by `model`, `feature`, and `tenant`. Checklist:
1. **Token-per-request average** — a jump signals prompt bloat, a longer system prompt, or runaway context (RAG retrieving too much).
2. **Escalation rate** — is the router suddenly sending more traffic to the frontier tier?
3. **Cache hit rate** — did a deploy break the cache key?
4. **Request volume** — organic growth vs. a retry storm or abuse.
5. **Output length** — did someone remove a `max_tokens` cap?
Without cost recorded as a first-class signal, this is guesswork; with it, you isolate the offending feature/tenant in minutes.

---

### Q8: How do you implement a budget-alert hook?

**Answer:** Accumulate spend in a guard that fires a callback when thresholds are crossed, each only once to avoid spam:

```python
class BudgetGuard:
    def __init__(self, budget, on_alert):
        self.budget, self.spent, self.on_alert = budget, 0.0, on_alert
        self._fired = set()
    def record(self, cost):
        self.spent += cost
        for pct in (0.5, 0.8, 1.0):
            if self.spent >= self.budget * pct and pct not in self._fired:
                self._fired.add(pct); self.on_alert(pct, self.spent)
```

I fire at 50% / 80% / 100% so teams get early warning, not just a post-mortem. In production the alert routes to Slack/PagerDuty and can optionally trip a circuit breaker to downgrade tiers or shed non-critical traffic.

---

### Q9: What is prompt compression and when is it more than just "write shorter prompts"?

**Answer:** Basic compression is human-driven: trim verbose system prompts, drop few-shot examples, enforce structured output. Automated compression (e.g. **LLMLingua**) uses a small model to score and remove low-information tokens from long contexts — especially RAG prompts padded with retrieved chunks — while preserving meaning. It shines when the prompt is large and machine-generated, where a human can't hand-trim every call. The trade-off is a small quality risk and added pre-processing latency, so it must be evaluated against your quality bar.

---

### Q10: How does prompt-prefix caching differ from a response cache, and why does it matter for cost?

**Answer:** A response cache stores the *final answer* keyed on the request. Provider prompt-prefix caching instead discounts the *static prefix* of the input (e.g. a long fixed system prompt or document) when it's reused across calls — the provider keeps the prefix's computed state warm and bills it at a steep discount. Response caches help when the *whole* request recurs; prefix caching helps when only the *beginning* is shared but the user message differs every time, which is the common chatbot pattern.

---

### Q11: You estimate costs before calling the model. Why is the estimate useful if it's not exact?

**Answer:** Pre-call estimation (count input tokens, assume an output budget, multiply by tier price) drives decisions *before* you spend: it feeds the router's tier choice, lets a budget guard reject or downgrade a call that would blow the budget, populates cost dashboards, and exposes prompt bloat early. It doesn't need to be exact — input tokens are known precisely and output is bounded by `max_tokens`, so the estimate brackets the real cost well enough to gate decisions.

---

### Q12: Self-hosting an open model looks ~10x cheaper per token. What's the catch?

**Answer:** The per-token price ignores total cost of ownership: GPU rental or purchase, idle capacity (you pay for the GPU whether or not it's busy), ops/on-call, autoscaling complexity, model-quality gaps, and security/patching. Self-hosting wins for **high, steady volume** where you can keep GPUs saturated and the task fits a smaller open model. For spiky or low volume, a hosted API's pay-per-token model is usually cheaper and far less operational burden. Right answer is workload-dependent and should be backed by a break-even calculation on expected utilization.

---

### Q13: How would you keep cost optimization from silently degrading quality?

**Answer:** Pair every cost lever with an eval gate. Maintain a representative eval set with a quality bar; any change — cheaper tier, compressed prompt, smaller `max_tokens`, new cache — must pass it before shipping. In production, track `cost_per_successful_task` (not just raw cost) so you notice if "cheaper" routing is actually causing retries/escalations that erase the savings. Cost and quality are a joint optimization, not a unilateral one.

---

### Q14: What is FinOps for AI and how is it different from classic cloud FinOps?

**Answer:** FinOps brings financial accountability to variable cloud spend through visibility, allocation, and optimization. The AI twist: spend is driven by *tokens and model choice*, not just compute hours, and it's highly variable per request. AI FinOps means tagging spend by feature/tenant/model, attributing cost to product value (`cost_per_task`), setting per-feature budgets with alert hooks, and treating model routing/right-sizing as the primary optimization knob. It also adds a quality dimension absent from classic FinOps — the cheapest option that still meets the quality bar, not just the cheapest option.

---

### Q15: Give a concrete cost-reduction plan for a chatbot costing $50K/month on a frontier model.

**Answer:** In rough order of leverage:
1. **Cascade routing** — classify complexity; send the easy majority to a small model. Biggest single win if traffic is skewed (often 40–70% reduction).
2. **Right-size the default tier** — confirm with evals the frontier model is actually needed for the queries that stay.
3. **Prompt-prefix caching + compress the system prompt** — stop re-billing a long static prefix on every call.
4. **Cap `max_tokens`** and prefer structured output — directly cuts the expensive output line item.
5. **Move offline work to the batch API** — evals, summaries, enrichment at ~50% off.
6. **Add cost telemetry + budget hooks** — so the savings are measured and don't regress.
Each step is guarded by the eval set so quality holds, and `cost_per_successful_task` confirms the savings are real.
