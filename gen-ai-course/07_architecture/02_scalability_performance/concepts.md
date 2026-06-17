# Scalability & Performance — Concepts

Scaling a GenAI system is different from scaling a typical web app. Each request can occupy a GPU for seconds, memory is dominated by model weights and KV-cache, and a single LLM call can cost more than thousands of database queries. This document walks through the levers you pull to handle growth: scaling, load balancing, autoscaling, caching, multi-region, and connection pooling.

---

## 1. Horizontal vs Vertical Scaling

**Vertical scaling (scale up)** means giving one node more power — a bigger GPU, more VRAM, more cores. **Horizontal scaling (scale out)** means running more replicas behind a load balancer.

```
   VERTICAL (scale up)              HORIZONTAL (scale out)

      ┌─────────┐                 ┌────┐ ┌────┐ ┌────┐ ┌────┐
      │  A100   │   ──►  H100     │ R1 │ │ R2 │ │ R3 │ │ R4 │
      │  80 GB  │                 └────┘ └────┘ └────┘ └────┘
      └─────────┘                    ▲      ▲     ▲      ▲
   one bigger box                    └──── load balancer ───┘
```

| Dimension | Vertical (Scale Up) | Horizontal (Scale Out) |
|---|---|---|
| What changes | Bigger GPU/CPU per node | More nodes/replicas |
| Max limit | One machine (e.g. 8 GPUs) | Practically unlimited |
| Downtime | Usually needs a restart | Zero downtime |
| Cost curve | Exponential (A100 → H100) | Roughly linear |
| Complexity | Low | High (orchestration, LB, state) |
| Best for | Models too large for one node | High request volume |

**Rule of thumb:** scale *up* until the model fits and a single replica is healthy, then scale *out* for throughput. Large models that don't fit on one GPU need vertical first (tensor/pipeline parallelism), then horizontal replicas of the sharded unit.

---

## 2. Load Balancing

A load balancer spreads inference requests across replicas to maximize throughput and minimize latency. The "right" algorithm depends on how uniform your requests are.

| Strategy | How it works | Best for |
|---|---|---|
| **Round Robin** | Cycle through replicas in order | Uniform request sizes |
| **Least Connections** | Send to the replica with fewest in-flight requests | Variable inference times |
| **Weighted** | Give bigger weights to stronger GPUs | Heterogeneous hardware |
| **Latency-Based** | Track p99, route to the fastest | Latency-sensitive apps |
| **Token-Aware** | Estimate token count, route to least-loaded | LLM serving (vLLM) |

```
Round Robin:        Least Connections:        Weighted (2:1:1):
  req1 → R1           R1 [■■■■]  4 active        R1 weight 2  ← 50%
  req2 → R2           R2 [■]     1 active ◄──     R2 weight 1  ← 25%
  req3 → R3           R3 [■■]    2 active         R3 weight 1  ← 25%
  req4 → R1           (pick the least busy)
```

Round-robin is naive for LLMs because a 50-token request and a 4,000-token request both count as "one." **Least-connections** and **token-aware** balancing adapt to the fact that LLM request cost varies wildly. A token-aware balancer scores each healthy replica by estimated load and picks the minimum:

```python
def select_replica(replicas, estimated_tokens):
    healthy = [r for r in replicas if r.health_score > 0.5]
    if not healthy:
        raise RuntimeError("no healthy replicas")
    def score(r):
        load = (r.gpu_memory_used + estimated_tokens * 0.001) / r.gpu_memory_total
        return load + r.active_requests * 0.1 + r.avg_latency_ms * 0.001
    return min(healthy, key=score)  # lower score = less loaded
```

Always pair load balancing with **health checks**: a replica that fails its `/health` probe is removed from rotation so requests don't hit a dead pod.

---

## 3. Autoscaling

Traffic is rarely flat. Autoscaling adds replicas under load and removes them when idle. In Kubernetes this is the **Horizontal Pod Autoscaler (HPA)**.

For model serving, CPU utilization is a poor signal — GPUs are the bottleneck. Scale on **queue depth** (`num_requests_waiting`) and **GPU utilization** instead.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Pods
      pods:
        metric:
          name: vllm:num_requests_waiting   # custom metric from vLLM
        target:
          type: AverageValue
          averageValue: "10"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60        # react fast to spikes
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300       # scale down slowly (avoid flapping)
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

**Scaling decision matrix:**

| Trigger | Action | Cool-down |
|---|---|---|
| GPU utilization > 85% | Add replica | 60s |
| Queue depth > 50 | Add replica | 30s |
| p99 latency > 10s | Add replica | 60s |
| GPU utilization < 30% | Remove replica | 300s |
| Queue empty for 5m | Remove replica | 300s |

### Scale-to-Zero

For spiky or low-traffic workloads (internal tools, dev endpoints), **scale-to-zero** removes all replicas when idle and spins one up on the next request. Tools like **KEDA** and **Knative** enable this.

```
traffic ──►  0 replicas  ──(first request)──►  cold start  ──►  serving
   idle          $0                ~30–90s (load weights)        $$$
```

The tradeoff is **cold-start latency**: loading multi-GB weights onto a GPU can take 30–90s. Mitigate with warm pools, model snapshotting, or a small `minReplicas` floor for latency-critical paths. Scale-to-zero shines when the cost of idle GPUs outweighs occasional cold-start delay.

---

## 4. Caching Strategies

Caching is the **highest-ROI optimization** for AI systems. LLM calls are expensive in both latency and dollars, and real traffic is full of repeats and near-duplicates ("How do I reset my password?" vs "I forgot my password, help").

| Cache type | What's cached | Hit-rate potential | Saves |
|---|---|---|---|
| **Exact match (response)** | Full response for identical prompts | 15–30% | Cost + latency |
| **Semantic** | Response for *similar* prompts | 30–60% | Cost + latency |
| **Embedding** | Pre-computed embedding vectors | 50–80% | Latency only |
| **Prefix / KV** | KV-cache for shared prompt prefixes | 20–40% | Latency only |

```
                  ┌──────────────────────────────┐
   query ───►     │  1. exact-match (hash) lookup │──hit──► return
                  └──────────────┬───────────────┘
                                 │ miss
                  ┌──────────────▼───────────────┐
                  │  2. embed query (use cache)   │
                  └──────────────┬───────────────┘
                                 │
                  ┌──────────────▼───────────────┐
                  │  3. semantic lookup           │──sim ≥ τ──► return
                  │     (cosine vs stored embeds) │
                  └──────────────┬───────────────┘
                                 │ miss
                  ┌──────────────▼───────────────┐
                  │  4. call LLM, then store      │──────► return
                  └──────────────────────────────┘
```

### Exact-Match / Response Cache

Hash the normalized request (prompt + params) and store the response under that key. Simple, fast, zero false positives — but it only catches *byte-identical* requests.

```python
key = "llm:" + hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
if (cached := redis.get(key)):
    return json.loads(cached)
result = call_llm(**params)
redis.setex(key, ttl, json.dumps(result))   # setex = set with TTL
```

### Semantic Cache

Embed the query and compare against stored query embeddings via **cosine similarity**. If the best match exceeds a threshold τ (commonly 0.85–0.95), return its cached response. This catches paraphrases that exact-match misses.

```python
def semantic_get(query, threshold=0.92):
    q = embed(query)
    for entry in store:                       # production: a vector DB
        sim = cosine(q, entry.embedding)
        if sim >= threshold:
            return entry.response             # cache hit
    return None                               # miss → call LLM
```

**Choosing τ is a precision/recall tradeoff:**

| Threshold τ | Effect |
|---|---|
| High (0.97) | Few false hits, lower hit rate (conservative) |
| Medium (0.90) | Balanced — common default |
| Low (0.80) | High hit rate, risk of wrong/stale answers |

### Embedding Cache

Embeddings are deterministic for a given text+model, so cache them too. This avoids re-embedding the same documents/queries and is the cheapest cache to maintain (latency-only savings, no correctness risk).

### Cache Invalidation & TTL

> "There are only two hard things in computer science: cache invalidation and naming things."

Every cache entry needs a **time-to-live (TTL)** so stale answers expire. Strategies:

| Mechanism | When to use |
|---|---|
| **TTL expiry** | Default — entries auto-expire after N seconds |
| **Explicit invalidation** | When the underlying knowledge/document changes |
| **Versioned keys** | Embed a `model_version` / `kb_version` in the key; bump to invalidate all |
| **LRU eviction** | When the cache is full, drop least-recently-used entries |

For RAG systems, invalidate (or version) the cache whenever the source documents are re-indexed — otherwise users get answers grounded in deleted content.

---

## 5. Multi-Region Deployment

Global apps deploy across regions to cut latency (serve users from the nearest region) and survive regional outages (disaster recovery).

```
                    ┌──────────────────────┐
                    │     Global DNS       │
                    │  (Route 53 / CF)     │  ◄── latency/geo routing + health checks
                    └──┬───────┬───────┬───┘
            ┌──────────┘       │       └──────────┐
            ▼                  ▼                  ▼
     ┌────────────┐    ┌────────────┐     ┌────────────┐
     │  US-East   │    │  EU-West   │     │  AP-South  │
     │ API GW     │    │ API GW     │     │ API GW     │
     │ vLLM x4    │    │ vLLM x2    │     │ vLLM x2    │
     │ Redis      │    │ Redis      │     │ Redis      │
     └─────┬──────┘    └─────┬──────┘     └─────┬──────┘
           └─────────────────┼──────────────────┘
                       Cross-region replication
                     (cache: eventual, billing: strong)
```

| Factor | Strategy |
|---|---|
| **Data residency** | Keep user data in its legal region (GDPR, etc.) |
| **Model replication** | Pre-deploy models to every region (avoid cold start) |
| **Cache** | Redis Cluster with cross-region replication |
| **Failover** | Health-check-based DNS failover (low TTL, ~30s) |
| **Cost** | Spot instances in non-primary regions |
| **Consistency** | Eventual for cache, strong for billing/quotas |

---

## 6. Connection Pooling

Opening a TCP/TLS connection per request is wasteful — the handshake adds latency and exhausts file descriptors under load. A **connection pool** keeps a set of reusable, warm connections to downstream services (databases, vector DBs, model endpoints).

```
   Without pool                 With pool
   ─────────────                ─────────
   req → open → use → close     req ─┐
   req → open → use → close          ├─► [ pool: c1 c2 c3 c4 ]  reuse
   req → open → use → close     req ─┘     borrow ─► use ─► return
   (handshake every time)              (handshake once, reuse many times)
```

```python
# httpx with a bounded connection pool + keep-alive
import httpx
limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
client = httpx.Client(limits=limits, timeout=30)   # reuse one client, not per-request
```

**Sizing tips:** pool size should track expected concurrency, not be unbounded (a too-large pool can overwhelm the backend). Watch for **pool exhaustion** (requests queue waiting for a free connection) and tune `max_connections` plus a sane acquire timeout. Always reuse a single client instance — creating a new client per request defeats the pool entirely.

---

## Key Takeaways

- **Scale up first, then out:** vertical until the model fits and is healthy, horizontal for throughput.
- **Match the load-balancing algorithm to your traffic:** round-robin for uniform requests, least-connections / token-aware for variable LLM workloads. Always health-check.
- **Autoscale on the right signal:** queue depth and GPU utilization, not CPU. Scale up fast, down slowly to avoid flapping.
- **Scale-to-zero** saves money on spiky workloads but pays a cold-start tax — keep a warm floor for latency-critical paths.
- **Caching is the highest-ROI optimization.** Layer exact-match → embedding → semantic caches. Semantic caching alone can cut cost/latency 30–60%.
- **Every cache entry needs a TTL** and an invalidation story; version keys by model/KB to flush stale answers.
- **Go multi-region** for global latency and disaster recovery; keep cache eventual and billing strong, and mind data residency.
- **Pool connections** and reuse clients to avoid per-request handshakes and fd exhaustion.
