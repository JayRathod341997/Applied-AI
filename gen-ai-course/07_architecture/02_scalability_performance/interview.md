# Scalability & Performance — Interview Questions

A mix of conceptual and applied questions you might field for a GenAI / ML-platform engineering role.

---

### Q1: What is the difference between horizontal and vertical scaling, and when do you use each for model serving?

**Answer:** Vertical scaling (*scale up*) gives one node more power — a bigger GPU, more VRAM. Horizontal scaling (*scale out*) runs more replicas behind a load balancer.

| | Vertical | Horizontal |
|---|---|---|
| Ceiling | One machine | Practically unlimited |
| Cost curve | Exponential | ~Linear |
| Downtime | Often needs restart | Zero |

For model serving the rule is: **scale up until the model fits and one replica is healthy** (use tensor/pipeline parallelism for models too big for one GPU), then **scale out for throughput**. You can't replicate something that doesn't run, so very large models force vertical first.

---

### Q2: Compare round-robin, least-connections, and weighted load balancing. Which suits LLM traffic?

**Answer:**
- **Round-robin** cycles through replicas in order — simple, fair only when requests cost the same.
- **Least-connections** routes to whichever replica has the fewest in-flight requests — adapts to variable processing times.
- **Weighted** assigns more traffic to stronger replicas — good for heterogeneous hardware.

LLM requests vary enormously in cost (a 50-token vs a 4,000-token completion), so round-robin can overload one replica. **Least-connections** or **token-aware** balancing (estimate tokens, route to least-loaded) fits LLM serving far better.

---

### Q3: Why scale model-serving autoscalers on queue depth and GPU utilization instead of CPU?

**Answer:** In LLM inference the GPU is the bottleneck while the CPU mostly shuffles requests, so CPU utilization stays low even when the GPU is saturated — scaling on it would never trigger. **Queue depth** (`num_requests_waiting`) directly reflects backpressure, and **GPU utilization** reflects compute saturation. Both are leading indicators of latency degradation, so they make better HPA signals.

---

### Q4: Walk through a Kubernetes HPA configuration for a vLLM deployment. What are the key knobs?

**Answer:** The HPA targets a Deployment and scales between `minReplicas` and `maxReplicas` based on custom metrics. Key knobs:

- **Custom metrics** (`vllm:num_requests_waiting`, `gpu_utilization`) exported to Prometheus / the metrics API.
- **`behavior.scaleUp`** with a short stabilization window (~60s) so you react quickly to spikes.
- **`behavior.scaleDown`** with a long stabilization window (~300s) to avoid flapping — repeatedly killing and recreating pods wastes cold-start time.
- **`minReplicas` floor** (e.g. 2) to keep capacity warm and survive a pod failure.

The asymmetry — scale up fast, scale down slowly — is the most important design choice.

---

### Q5: What is scale-to-zero, and what is its main tradeoff?

**Answer:** Scale-to-zero removes *all* replicas when a service is idle (paying \$0 for GPUs) and spins up a replica on the next request, typically via KEDA or Knative. The tradeoff is **cold-start latency**: loading multi-GB model weights onto a GPU can take 30–90s, so the first request after idle is slow. It's ideal for spiky/low-traffic workloads (internal tools, dev endpoints) but not for latency-critical user paths, where you keep a warm floor or use snapshotting/warm pools.

---

### Q6: Explain the layered caching strategy for an LLM application.

**Answer:** Layer caches cheapest/safest first:

1. **Exact-match (response) cache** — hash the normalized request; instant hit on byte-identical prompts. Zero false positives.
2. **Embedding cache** — embeddings are deterministic for text+model, so cache them; pure latency savings, no correctness risk.
3. **Semantic cache** — embed the query, cosine-compare to stored query embeddings, return a hit above a threshold; catches paraphrases.
4. **Prefix/KV cache** — reuse attention KV state for shared prompt prefixes (done inside the serving engine).

Together these can cut cost/latency dramatically; semantic caching alone often yields 30–60% hit rates.

---

### Q7: How does a semantic cache work, and how do you pick the similarity threshold?

**Answer:** It stores `(query_embedding, response)` pairs. For a new query it computes the embedding and the cosine similarity to each stored embedding; if the best match exceeds threshold τ, it returns that cached response instead of calling the LLM.

τ is a **precision/recall dial**:

| τ | Effect |
|---|---|
| High (0.97) | Few false hits, lower hit rate |
| Medium (0.90) | Balanced default |
| Low (0.80) | High hit rate, risk of wrong answers |

Tune it against a labeled set of query pairs: too high wastes savings, too low serves mismatched answers. The cost of a wrong answer in your domain should drive how conservative you are.

---

### Q8: Why is cache invalidation hard, and what strategies do you use?

**Answer:** It's hard because the cache can't know when the *truth* behind an entry changes — you have to model that yourself. Strategies:

- **TTL** — every entry expires after N seconds (the safe default).
- **Explicit invalidation** — delete entries when the underlying data changes.
- **Versioned keys** — bake `model_version` / `kb_version` into the cache key; bump it to invalidate everything at once.
- **LRU eviction** — drop least-recently-used entries when full.

For RAG, the critical one is **versioning the cache by the knowledge-base index**: after re-indexing, old answers may cite deleted documents, so you bump the version to flush them.

---

### Q9: How do you decide between caching and just adding more replicas?

**Answer:** They solve different problems. Caching reduces *work* (fewer LLM calls → lower cost and latency) and is the highest-ROI lever when traffic is repetitive. Adding replicas increases *capacity* for genuinely distinct requests. The decision: measure your **cache hit-rate potential** (how repetitive is traffic?). High repetition → cache first, since it's far cheaper than GPUs. Low repetition or strict freshness requirements → caching helps little, so scale out. In practice you do both: cache to shave the easy wins, then size replicas for the residual unique traffic.

---

### Q10: What are the main considerations in a multi-region deployment?

**Answer:**

| Factor | Strategy |
|---|---|
| Latency | Geo/latency DNS routing to nearest region |
| Data residency | Keep user data in its legal region (GDPR) |
| Model availability | Pre-deploy models everywhere to avoid cold start |
| Failover | Health-check DNS failover with low TTL (~30s) |
| Consistency | Eventual for cache, strong for billing/quotas |
| Cost | Spot instances in non-primary regions |

The recurring tension is **latency/availability vs. consistency and compliance** — you accept eventual consistency for caches but demand strong consistency where money or legal boundaries are involved.

---

### Q11: Why use connection pooling, and what can go wrong if you size it badly?

**Answer:** Opening a TCP/TLS connection per request adds handshake latency and can exhaust file descriptors under load. A pool keeps warm, reusable connections that requests borrow and return. Sizing pitfalls:

- **Too small** → requests queue waiting for a free connection (pool exhaustion), inflating tail latency.
- **Too large** → you can overwhelm the backend with concurrency it can't handle.

Size the pool to expected concurrency, set a sane acquire timeout, and always reuse a single client instance — creating a new client per request defeats pooling entirely.

---

### Q12: A user reports the chatbot returned an outdated answer after you updated the docs. What's the likely cause and fix?

**Answer:** A cached response (exact-match or semantic) is being served from *before* the docs changed — the cache wasn't invalidated on re-index. Fix: bake a `kb_version` (or document-set hash) into the cache key and bump it whenever the knowledge base is re-indexed, which logically flushes stale entries. As a stopgap, lower the TTL so entries expire sooner. Longer term, wire the re-index pipeline to explicitly purge affected cache entries.

---

### Q13: Your p99 latency spikes under bursty traffic even though average GPU utilization is moderate. What's happening and how do you address it?

**Answer:** Bursts create transient **queueing**: requests pile up faster than the current replicas drain them, so p99 (tail) latency spikes while *average* utilization looks fine. Remedies:

- Autoscale on **queue depth**, not average utilization, with a **fast scale-up** window.
- Keep a small warm replica **floor** so you don't pay cold-start on every burst.
- Use **continuous batching** (e.g. vLLM PagedAttention) to absorb bursts more efficiently.
- Add a **semantic/exact cache** so repeated burst queries skip the GPU entirely.

The key insight: tail latency is driven by queueing dynamics, not averages.

---

### Q14: How would you load-test and choose autoscaling parameters before launch?

**Answer:** Drive synthetic traffic that mirrors production token-length distribution and arrival pattern (steady + bursts). Measure throughput, p50/p95/p99 latency, and queue depth per replica count to find each replica's safe capacity. From that, set `minReplicas` for baseline + failure tolerance, `maxReplicas` for peak forecast plus headroom, and the scale-up threshold below the point where p99 degrades. Then run a burst test to validate the scale-up window reacts before SLOs break, and a soak test to confirm scale-down doesn't flap. Iterate on thresholds using the observed latency-vs-load curve.

---
