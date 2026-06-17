# Quiz

## Question 1
On most commercial LLM APIs, how do input and output token prices typically compare?

A) Input and output cost exactly the same
B) Input costs 3–5x more than output
C) Output costs 3–5x more than input
D) Output is always free

---
**Answer: C**
Output tokens are typically 3–5x more expensive than input tokens. This is why capping `max_tokens` and favoring terse, structured responses is one of the most direct cost levers.

---

## Question 2
A request uses 2,000 input tokens and 500 output tokens on a model priced at $0.0025/1K input and $0.010/1K output. What is the cost?

A) $0.0025
B) $0.0050
C) $0.0100
D) $0.0250

---
**Answer: C**
(2000/1000 * 0.0025) + (500/1000 * 0.010) = 0.005 + 0.005 = **$0.010**. Note the 500 output tokens cost as much as the 2,000 input tokens.

---

## Question 3
What is the core idea behind cascade (tiered) model routing?

A) Always use the most powerful model for consistency
B) Route each query to the cheapest model that can handle it, escalating only when needed
C) Randomly distribute queries across models to balance load
D) Use the cheapest model for everything regardless of quality

---
**Answer: B**
Cascade routing sends queries to the cheapest capable tier and escalates to expensive models only on low confidence or high complexity. FrugalGPT showed this can cut cost dramatically at matched accuracy.

---

## Question 4
What is the "escalation tax" in a confidence-based cascade?

A) A provider fee for switching models mid-request
B) The cost of paying for both the cheap call and the expensive retry when the cheap model fails
C) A tax on tokens above a certain count
D) The latency added by caching

---
**Answer: B**
If you call the cheap model first and then retry on the expensive one, you pay for both. Cascades only save money when the cheap tier resolves a large share of traffic on its own.

---

## Question 5
A semantic cache is being considered for a workload with a measured 12% hit rate. What is the most likely conclusion?

A) Deploy it immediately; any cache always saves money
B) It is probably not worth it; below ~20% hit rate the lookup and embedding overhead rarely pay off
C) Switch to a frontier model instead
D) Cache hit rate is irrelevant to ROI

---
**Answer: B**
Cache ROI is `hit_rate * cost_per_call` minus infra/embedding cost. Below ~20% hit rate the savings usually don't cover the added lookup, embedding cost, and staleness risk.

---

## Question 6
Which workload is the best candidate for a provider's batch API (~50% discount, async)?

A) A live customer-support chatbot
B) Autocomplete suggestions in an editor
C) Generating embeddings for an entire document corpus overnight
D) A real-time fraud-check on a payment

---
**Answer: C**
Batch APIs trade latency (up to ~24h) for ~50% off. If no user is blocked waiting, it's a batch candidate — corpus embeddings, nightly enrichment, and offline evals are ideal.

---

## Question 7
Which technique gives the largest input-token savings according to the prompt-optimization table?

A) Capping max_tokens
B) Switching to JSON output
C) Moving from few-shot to zero-shot (50–80% input savings)
D) Lowering temperature

---
**Answer: C**
Few-shot prompts carry many example tokens on every call. Moving to zero-shot (often via a fine-tuned or stronger model) can cut 50–80% of input tokens.

---

## Question 8
What does "right-sizing" a model mean?

A) Always picking the model with the largest context window
B) Matching model capability to task difficulty, backed by an eval set
C) Choosing the model with the most parameters
D) Using one model for the entire application to simplify ops

---
**Answer: B**
Right-sizing matches capability to task difficulty: small models for classification/extraction, frontier models for reasoning/code. An eval set with a quality bar tells you how far up you must go — no further.

---

## Question 9
Why should cost be recorded as a per-call telemetry signal (span attribute / metric)?

A) Providers require it for billing
B) So spend can be attributed by feature/tenant, the expensive traffic found, and budget alerts fired
C) It reduces token usage automatically
D) It is only needed for self-hosted models

---
**Answer: B**
Recording dollars per call and tagging by model/feature/tenant lets you attribute spend, find the costly 5% of traffic, and trigger budget-alert hooks before the bill surprises you. This is AI-native FinOps.

---

## Question 10
A budget-alert hook is configured to fire at 50%, 80%, and 100% of a monthly budget, each only once. Why fire at multiple thresholds instead of only at 100%?

A) To maximize the number of alerts
B) To give early warning so teams can react before the budget is fully exhausted
C) Because providers throttle at 50%
D) It is required by OpenTelemetry

---
**Answer: B**
Firing at 50% and 80% gives early warning, letting the team investigate a runaway router or prompt-bloat regression before spend hits the hard limit. Firing each threshold once avoids alert spam.

---

## Question 11
Which signal is a sensible up-front heuristic for routing a query to a higher (more expensive) tier?

A) The query contains a question mark
B) The query is long and contains keywords like "prove", "design", or "debug"
C) The query is in lowercase
D) The query was sent in the morning

---
**Answer: B**
Length plus complexity-signaling keywords ("prove", "derive", "design", "architect", "debug", "optimize") and multiple constraints are cheap, useful heuristics for up-front tier selection before any model call.

---

## Question 12
You have a 500-token system prompt that is identical on every one of 10 million monthly calls. What is the most cost-effective first action?

A) Switch all traffic to a frontier model
B) Compress the system prompt and/or use provider prompt-prefix caching so the static prefix isn't re-billed at full price every call
C) Add a semantic cache for the user messages
D) Increase max_tokens to reduce retries

---
**Answer: B**
A static 500-token prefix billed 10M times is pure, repeated waste. Compressing it and enabling prompt-prefix caching (which discounts the shared prefix) attacks the cost at its root.
