# Module 7: Architecture Design — Interview Questions

## Table of Contents
- [Beginner Level](#beginner-level) (Q1–Q7)
- [Intermediate Level](#intermediate-level) (Q8–Q14)
- [Advanced Level](#advanced-level) (Q15–Q20)
- [Quick Reference Table](#quick-reference-table)

---

## Beginner Level

### Q1: What is the difference between a monolith and microservices architecture for AI systems?

**Answer:**

A **monolith** deploys the entire AI application (embedding, retrieval, generation, caching) as a single unit. A **microservices** architecture splits each component into independently deployable services communicating over APIs.

| Aspect | Monolith | Microservices |
|---|---|---|
| Deployment | Single artifact | Independent services |
| Scaling | Scale everything together | Scale individual components |
| Fault isolation | One crash = total failure | Blast radius contained |
| Latency | In-process (sub-ms) | Network calls (1–10 ms) |
| Model updates | Full redeploy | Update independently |
| Best for | Small teams, <5 models | Large teams, 10+ models |

**When to start with monolith:** Small team, single model, rapid prototyping. **When to migrate to microservices:** Components have different scaling needs (GPU vs CPU), teams need independent deploy cycles, or regulatory isolation is required.

---

### Q2: What is an API Gateway and what are its key responsibilities in an AI system?

**Answer:**

An API Gateway is the single entry point for all client requests. It handles cross-cutting concerns before routing to backend services:

```python
gateway_responsibilities = {
    "authentication": "Verify API keys, JWT tokens",
    "rate_limiting": "Prevent abuse, control costs (100 req/min per user)",
    "model_routing": "Route to GPT-4 vs Claude vs Llama based on request",
    "caching": "Return cached results for repeated queries",
    "logging": "Track requests for debugging and billing",
    "guard_rails": "PII detection, content filtering at the edge",
    "a_b_testing": "Split traffic 90/10 between model versions",
}
```

Without a gateway, every client must handle auth, rate limiting, and routing independently, and backend services are directly exposed.

---

### Q3: When should you use asynchronous processing instead of synchronous request-response for AI inference?

**Answer:**

**Use async when:**
- Inference takes > 5 seconds (large models, complex chains, document processing)
- You need to handle traffic spikes with queue buffering
- Batch processing is more cost-effective than real-time
- The client doesn't need an immediate response (email generation, report creation)

**Use sync when:**
- Sub-second responses are required (chat, search)
- Simple/lightweight inference
- Real-time interactive applications

**Architecture difference:**
```
Sync:   Client → API → Model → Response (client waits entire time)
Async:  Client → API → Queue → Response (job_id)
        Worker → Model → Result Store
        Client → API → Result Store → Result (polls or webhook)
```

---

### Q4: What is a message queue and how does it improve AI system architecture?

**Answer:**

A message queue (Redis Streams, Kafka, AWS SQS) is an intermediary buffer that stores messages between producers and consumers.

**Benefits for AI systems:**
1. **Decoupling:** API servers don't need to know about GPU workers
2. **Buffering:** Absorbs traffic spikes without dropping requests
3. **Retry:** Failed tasks can be automatically retried
4. **Independent scaling:** Scale API tier and GPU tier separately
5. **Prioritization:** High-priority requests can jump the queue

```python
# Producer (API server)
queue.enqueue("inference_tasks", {"prompt": "...", "model": "gpt-4"})

# Consumer (GPU worker)
task = queue.dequeue("inference_tasks")
result = model.generate(task["prompt"])
result_store.set(task["id"], result)
```

---

### Q5: What types of caching are used in AI systems and what are their trade-offs?

**Answer:**

| Cache Type | What's Cached | Hit Rate | Latency Savings | Cost Savings |
|---|---|---|---|---|
| **Exact Match** | Full response by query hash | 15–30% | ~100% (1 ms vs 1 s) | 100% for hits |
| **Semantic Cache** | Response for similar queries | 30–60% | ~100% | 100% for hits |
| **Embedding Cache** | Pre-computed embeddings | 50–80% | 50–100 ms | Latency only |
| **KV Prefix Cache** | Cached key-value states for common prefixes | 20–40% | 30–50% compute | Latency + partial cost |

```python
# Multi-layer lookup order
result = exact_cache.get(key)           # Layer 1: ~1ms
if not result:
    result = semantic_cache.search(q)   # Layer 2: ~5ms
if not result:
    kv_state = prefix_cache.get(sys)    # Layer 3: saves prefill compute
    result = model.generate(q, kv=kv_state)  # Layer 4: full inference
    populate_all_caches(q, result)
```

---

### Q6: What is the difference between horizontal and vertical scaling for AI inference?

**Answer:**

- **Vertical scaling (scale up):** Increase resources on a single machine (more GPUs, more RAM, faster GPUs). Simple but has hard hardware limits and exponential cost.
- **Horizontal scaling (scale out):** Add more machines/replicas. Near-unlimited scale but requires load balancing, state management, and orchestration.

| Factor | Vertical | Horizontal |
|---|---|---|
| Max capacity | Single node limit (e.g., 8 GPUs) | Practically unlimited |
| Downtime | May require restart | Zero downtime |
| Cost curve | Exponential at high end | Linear |
| Complexity | Low | High (Kubernetes, LB, etc.) |
| Best for | Large models that need to fit in one node | High request volume, variable load |

**Decision rule:** If the model fits in one node's GPU memory → vertical is simpler. If you need more throughput than one node provides → horizontal.

---

### Q7: What is the circuit breaker pattern and why is it important for AI systems?

**Answer:**

A circuit breaker monitors calls to a downstream service (e.g., an LLM API). If failures exceed a threshold, it "opens" the circuit and returns fallback responses immediately instead of calling the failing service.

**Three states:**
```
CLOSED (normal) → failures exceed threshold → OPEN (rejecting)
OPEN → timeout expires → HALF_OPEN (testing)
HALF_OPEN → success → CLOSED
HALF_OPEN → failure → OPEN
```

**Why it matters for AI:**
- LLM APIs can go down or become slow; without a breaker, every request waits for the timeout before failing
- Prevents cascading failures across microservices
- Protects the failing provider from additional load during recovery
- Allows graceful degradation to fallback models or cached responses

---

## Intermediate Level

### Q8: Design a cost-optimized AI inference system that handles 10,000 requests per minute.

**Answer:**

```python
class CostOptimizedSystem:
    def __init__(self):
        self.cache = SemanticCache()           # Target: 40% hit rate
        self.router = ComplexityRouter()        # cheap → expensive cascade
        self.rate_limiter = SlidingWindowLimiter()

    async def handle(self, query: str, user: str) -> str:
        # 1. Rate limit
        if not self.rate_limiter.allow(user, limit=100, window=60):
            raise RateLimitError()

        # 2. Check cache (cost: $0)
        cached = await self.cache.get(query)
        if cached:
            return cached

        # 3. Route to cheapest capable model
        complexity = self.router.classify(query)
        model = {
            "simple": "gpt-4o-mini",      # 40% of traffic
            "medium": "gpt-4o",            # 45% of traffic
            "complex": "gpt-4o",           # 15% of traffic
        }[complexity]

        # 4. Call model
        result = await call_llm(query, model=model)

        # 5. Populate cache
        await self.cache.set(query, result)
        return result
```

**Architecture:**
- API Gateway (FastAPI + rate limiting)
- Semantic cache (Redis + vector DB) — 40% hit rate target
- Model router: 40% → mini ($0.15/1M), 45% → standard ($2.50/1M), 15% → standard
- Async workers for batch-eligible requests
- Auto-scaling GPU cluster (2–10 instances)

**Cost math at 10K req/min:**
- 40% cache hits: $0
- 40% mini × ~200 tokens: ~$0.72/min
- 20% standard × ~800 tokens: ~$0.40/min
- **Total: ~$1.12/min ($67/hr)** vs $20+/min unoptimized

---

### Q9: How would you implement a multi-layer caching system for AI inference?

**Answer:**

```python
class MultiLayerCache:
    def __init__(self, redis, vector_db, gpu_cache):
        self.redis = redis           # Layer 1: Exact match
        self.vector_db = vector_db   # Layer 2: Semantic similarity
        self.gpu_cache = gpu_cache   # Layer 3: KV prefix cache

    async def get(self, query: str, model: str, system_prompt: str):
        # Layer 1: Exact match (~1ms)
        key = f"{model}:{sha256(query)}"
        result = await self.redis.get(key)
        if result:
            return {"data": result, "source": "exact", "cost": 0}

        # Layer 2: Semantic match (~5ms)
        embedding = await get_embedding(query)
        matches = await self.vector_db.search(embedding, top_k=1, threshold=0.95)
        if matches:
            return {"data": matches[0].response, "source": "semantic", "cost": 0}

        # Layer 3: Check KV prefix cache (saves prefill compute)
        kv_state = await self.gpu_cache.get_prefix(system_prompt)

        # Layer 4: Full inference
        result = await infer(query, model, prefix_kv=kv_state)

        # Populate all layers
        await self.redis.setex(key, 3600, result)
        await self.vector_db.upsert(embedding, {"query": query, "response": result})
        return {"data": result, "source": "inference", "cost": calculate_cost(model)}
```

**Expected hit rates:** Exact 15%, Semantic 25%, Prefix 20%, Full Inference 40%. Total cost reduction: ~60%.

---

### Q10: Explain graceful degradation and how to implement it for an AI system.

**Answer:**

Graceful degradation ensures the system remains functional under partial failures by progressively reducing quality rather than failing completely.

```python
class GracefulDegradation:
    levels = [
        {"name": "full",      "model": "gpt-4o",    "features": ["rag", "tools"]},
        {"name": "reduced",   "model": "gpt-4o-mini", "features": ["rag"]},
        {"name": "minimal",   "model": "gpt-4o-nano", "features": []},
        {"name": "cache",     "model": None,          "features": []},
        {"name": "template",  "model": None,          "features": []},
    ]

    async def get_response(self, query: str) -> dict:
        for level in self.levels:
            try:
                if level["name"] == "template":
                    return {"response": "Service temporarily unavailable.", "level": "template"}
                if level["name"] == "cache":
                    cached = await self.cache.get_similar(query)
                    if cached:
                        return {"response": cached, "level": "cache"}
                    continue
                result = await call_model(query, level["model"], level["features"])
                return {"response": result, "level": level["name"]}
            except Exception:
                continue
        return {"response": "Please try again later.", "level": "unavailable"}
```

**Key principles:** Define degradation levels in advance, monitor health continuously, automatically fall back when components fail, automatically recover when they heal, always return *something* useful.

---

### Q11: How do you design auto-scaling for GPU-based model serving?

**Answer:**

```python
class GPUAutoScaler:
    def __init__(self):
        self.min_instances = 2
        self.max_instances = 20
        self.cooldown_seconds = 300

    def decide(self, metrics: dict) -> str:
        gpu = metrics["avg_gpu_utilization"]
        queue = metrics["pending_requests"]
        p95 = metrics["p95_latency_ms"]

        # Scale up
        if gpu > 0.80 or queue > 50 or p95 > 5000:
            return f"scale_up_to_{min(metrics['instances'] + 2, self.max_instances)}"

        # Scale down
        if gpu < 0.30 and queue < 10 and p95 < 1000:
            return f"scale_down_to_{max(metrics['instances'] - 1, self.min_instances)}"

        return "no_change"
```

**Scaling triggers:**

| Trigger | Action | Cooldown |
|---|---|---|
| GPU utilization > 80% | Add 2 replicas | 60s |
| Queue depth > 50 | Add 2 replicas | 30s |
| P95 latency > 5s | Add replicas | 60s |
| GPU utilization < 30% | Remove 1 replica | 300s |
| Queue depth = 0 for 5 min | Remove 1 replica | 300s |

**Critical:** Scale-down cooldown must be longer than scale-up cooldown (5 min vs 1 min) to prevent thrashing.

---

### Q12: Describe the trade-offs between REST, gRPC, and streaming for model serving.

**Answer:**

| Aspect | REST | gRPC Unary | gRPC Streaming |
|---|---|---|---|
| Latency | Highest (JSON) | Medium (binary) | Lowest TTFT |
| Throughput | Lower | Higher | Highest |
| Complexity | Simple | Moderate | Complex |
| Debugging | Easy (curl, browser) | Needs tools | Needs tools |
| Client support | Universal | Most languages | Most languages |
| Best for | Public APIs | Internal microservices | Real-time chat |

```python
# gRPC streaming for LLM
class LLMServiceServicer:
    def Generate(self, request, context):
        """Unary: return complete response."""
        return Response(text=self.model.generate(request.prompt))

    def GenerateStream(self, request, context):
        """Streaming: yield tokens as generated."""
        for token in self.model.generate_stream(request.prompt):
            yield StreamResponse(token=token)
```

**Decision:** REST for external/public APIs, gRPC for internal service-to-service, streaming for real-time UX (chatbots, code generation).

---

### Q13: How would you implement zero-downtime model deployments?

**Answer:**

Two primary strategies:

**Canary Deployment (gradual traffic shift):**
```python
async def canary_deploy(model_name, new_version):
    # 1. Deploy new version alongside old
    await k8s.create_deployment(f"{model_name}-{new_version}", replicas=2)

    # 2. Health check
    if not await health_check(new_version):
        await rollback(new_version)
        raise DeploymentError("Health check failed")

    # 3. Gradual traffic shift
    for percent, hold_sec in [(5, 60), (25, 120), (50, 120), (100, 0)]:
        await traffic.shift(model_name, new_version, percent)
        metrics = await monitor(hold_sec)
        if metrics.error_rate > 0.01 or metrics.p95_latency > 5000:
            await rollback(new_version)
            raise DeploymentError(f"Degraded at {percent}%")
```

**Blue-Green (instant switchover):**
Deploy to green environment, warm up GPU, validate with shadow traffic, then instant switch. Keep blue as rollback target for 1 hour.

| Strategy | Risk | Speed | Resource Cost |
|---|---|---|---|
| Rolling update | Medium | Slow | 1x |
| Canary | Low | Medium | 1.5x |
| Blue-Green | Lowest | Fastest | 2x |

---

### Q14: How do you design a hybrid workload scheduler for real-time and batch AI on the same GPU cluster?

**Answer:**

```python
class HybridScheduler:
    def __init__(self, total_gpus: int):
        self.realtime_pool = int(total_gpus * 0.6)  # 60% reserved
        self.batch_pool = total_gpus - self.realtime_pool

    async def schedule_realtime(self, request):
        gpu = self.get_available_realtime_gpu()
        if gpu:
            return await run_inference(gpu, request)
        # Preempt lowest-progress batch job
        victim = self.preempt_batch_job()
        return await run_inference(victim.gpu, request)

    async def schedule_batch(self, job):
        while True:
            gpu = self.get_available_batch_gpu()
            if gpu:
                return await run_batch(gpu, job)
            await asyncio.sleep(1)  # Wait for capacity

    def preempt_batch_job(self):
        victim = min(self.running_batch_jobs, key=lambda j: j.progress)
        victim.save_checkpoint()
        victim.pause()
        return victim
```

```
GPU Cluster (16 GPUs):
┌────────────────────────────────┐ ┌──────────────┐
│ Real-time Pool (10 GPUs)       │ │ Batch Pool   │
│ - Chat inference               │ │ (6 GPUs)     │
│ - Search embedding             │ │ - ETL        │
│ - API responses                │ │ - Eval       │
│ Priority: HIGH                 │ │ - Finetune   │
│ Can preempt batch: YES         │ │ Preemptible  │
└────────────────────────────────┘ └──────────────┘
```

**Key decisions:** Capacity reservation for real-time SLAs, checkpointing for batch resume after preemption, dynamic reallocation based on time-of-day patterns.

---

## Advanced Level

### Q15: Design a complete multi-region AI serving architecture with disaster recovery.

**Answer:**

```python
class MultiRegionAI:
    def __init__(self):
        self.regions = {
            "us-east-1": RegionConfig(gpu_nodes=10, is_primary=True),
            "eu-west-1": RegionConfig(gpu_nodes=6, is_primary=False),
            "ap-south-1": RegionConfig(gpu_nodes=4, is_primary=False),
        }
        self.dns = GlobalDNS()  # Route53 with health checks (30s TTL)

    def route(self, client_ip: str) -> str:
        region = self.dns.resolve(client_ip, health_check=True)
        if not self.regions[region].is_healthy():
            region = self.failover(client_ip)
        return self.regions[region].lb.select(strategy="gpu_aware")

    def failover(self, client_ip: str) -> str:
        healthy = [r for r, c in self.regions.items() if c.is_healthy()]
        return min(healthy, key=lambda r: self.dns.distance(client_ip, r))
```

**Architecture decisions:**
- **Primary region:** All writes, replicated async to secondaries
- **Read replicas:** Each region has a vector DB replica
- **Model sync:** Pre-positioned artifacts via CI/CD pipeline
- **Data consistency:** Strong for user data, eventual for cache/vectors
- **RTO:** < 30s (DNS failover), **RPO:** < 5 min (async replication lag)

---

### Q16: How would you implement a cost-aware request scheduler that optimizes GPU utilization while meeting SLAs?

**Answer:**

```python
@dataclass(order=True)
class ScheduledRequest:
    priority: float
    task_id: str = field(compare=False)
    sla_deadline_ms: float = field(compare=False)
    estimated_tokens: int = field(compare=False)
    model: str = field(compare=False)

class CostAwareScheduler:
    def __init__(self, gpu_cluster, budget_per_hour: float):
        self.queue = []  # Min-heap by priority
        self.budget = budget_per_hour
        self.spent = 0.0

    def schedule(self, request: dict) -> str:
        sla_remaining = request["deadline_ms"] - time.time() * 1000
        cost = self.estimate_cost(request)
        # Lower priority value = higher priority (processed first)
        priority = (sla_remaining / 1000) - (cost * 100)
        req = ScheduledRequest(priority=priority, ...)
        heapq.heappush(self.queue, req)
        return req.task_id

    async def run_loop(self):
        while True:
            if self.spent >= self.budget:
                await self.handle_budget_exceeded()
                continue
            req = heapq.heappop(self.queue)
            batch = self.collect_compatible(req)
            model = self.select_model_for_sla(batch)
            result = await self.gpu_cluster.infer_batch(batch, model)
            self.spent += self.batch_cost(batch, model)

    def select_model_for_sla(self, batch):
        tightest = min(r.sla_deadline_ms for r in batch)
        remaining = tightest - time.time() * 1000
        if remaining > 10000: return "gpt-4o-mini"    # Cheapest
        elif remaining > 3000: return "gpt-4o"         # Balanced
        else: return "gpt-4o-nano"                     # Fastest
```

**Key optimizations:** Priority queue balances SLA urgency with cost, batching maximizes GPU utilization, dynamic model selection based on remaining SLA budget, budget guardrails prevent overruns.

---

### Q17: How would you architect an AI system serving 1 million concurrent users with < 100ms P95 latency?

**Answer:**

```
Architecture for 1M concurrent users:

┌─────────────────────────────────────────────────────────────┐
│                    CDN Edge (200 PoPs)                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │Edge     │ │Edge     │ │Edge     │ │Edge     │  × 200   │
│  │Cache    │ │Cache    │ │Cache    │ │Cache    │          │
│  │(1ms)    │ │(1ms)    │ │(1ms)    │ │(1ms)    │          │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │
└───────┼──────────┼──────────┼──────────┼──────────────────┘
┌───────▼──────────▼──────────▼──────────▼──────────────────┐
│                  Regional Clusters                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │US-East   │  │US-West   │  │EU-West   │  │AP-East   │  │
│  │50 GPUs   │  │30 GPUs   │  │30 GPUs   │  │20 GPUs   │  │
│  │TensorRT  │  │TensorRT  │  │TensorRT  │  │TensorRT  │  │
│  │INT8+KV   │  │INT8+KV   │  │INT8+KV   │  │INT8+KV   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Optimization stack:**

| Layer | Technique | Latency Savings |
|---|---|---|
| Edge | CDN + semantic cache (80% hit rate) | ~1ms for cached |
| Model | TensorRT INT8 quantization | 2–4× faster |
| KV Cache | Reuse prefix computations | 30–50% reduction |
| Speculative Decoding | Draft model proposes, main verifies | 2–3× faster generation |
| Batching | Continuous batching (vLLM) | Higher throughput |
| Routing | Geo-based to nearest region | ~50ms network savings |

**Capacity math:** 1M concurrent × 1 req/10s = 100K req/s. Edge cache 80% hit → 20K req/s to origin. 130 GPUs × 200 req/s/GPU = 26K req/s capacity. 30% headroom for spikes.

---

### Q18: How would you implement zero-downtime model deployments with automatic rollback?

**Answer:**

```python
class ModelDeploymentManager:
    async def canary_deploy(self, model_name: str, new_version: str):
        # Deploy new version alongside old
        await self.k8s.create_deployment(f"{model_name}-{new_version}", replicas=2)

        if not await self.health_check(new_version):
            await self.rollback(new_version)
            raise DeploymentError("Health check failed")

        stages = [(5, 60), (25, 120), (50, 120), (100, 0)]

        for percent, hold_seconds in stages:
            await self.traffic.shift(model_name, new_version, percent)

            metrics = await self.monitor(hold_seconds)
            if metrics.error_rate > 0.01 or metrics.p95_latency > 5000:
                await self.rollback(new_version)
                raise DeploymentError(f"Degraded at {percent}%")

        # Remove old deployment
        await self.k8s.scale_down(f"{model_name}-old", 0)

    async def blue_green_deploy(self, model_name: str, new_version: str):
        await self.k8s.create_deployment(f"{model_name}-green", new_version)
        await self.warm_up(f"{model_name}-green")  # Load model into GPU
        await self.shadow_traffic(f"{model_name}-green", 100)  # Validate
        await self.traffic.switch(from_="blue", to="green")
        # Keep blue for 1 hour as rollback target
        await asyncio.sleep(3600)
        await self.k8s.scale_down(f"{model_name}-blue", 0)
```

| Strategy | Risk | Speed | Resource Cost |
|---|---|---|---|
| Rolling update | Medium | Slow | 1× |
| Canary | Low | Medium | 1.5× |
| Blue-Green | Lowest | Fastest | 2× |
| Shadow traffic | Lowest | Medium | 2× |

---

### Q19: How do you handle both real-time and batch AI workloads on the same GPU cluster without SLA violations?

**Answer:**

Use a **capacity reservation** model with preemption:

```python
class HybridWorkloadScheduler:
    def __init__(self, total_gpus: int):
        self.realtime_reserved = int(total_gpus * 0.6)  # 60% guaranteed

    async def schedule_realtime(self, request):
        gpu = self.get_realtime_gpu()
        if not gpu:
            gpu = self.preempt_batch_job()  # Take from batch
        return await self.run_inference(gpu, request)

    async def schedule_batch(self, job):
        # Use leftover capacity, can be preempted
        while True:
            gpu = self.get_batch_gpu()
            if gpu:
                await self.run_with_checkpoint(gpu, job)  # Save state periodically
                return
            await asyncio.sleep(1)
```

**Design principles:**
- Real-time gets guaranteed capacity + ability to preempt batch
- Batch fills unused capacity and checkpoint/resumes on preemption
- Time-based reallocation (more batch at night, more real-time during day)
- Priority queues within each pool

---

### Q20: Design a complete observability stack for a production AI system that tracks cost, quality, and performance.

**Answer:**

```python
from opentelemetry import trace
from prometheus_client import Counter, Histogram, Gauge

# Four pillars of AI observability
metrics = {
    # Performance
    "llm_latency_p99": Histogram("llm_latency_seconds", "Inference latency"),
    "llm_throughput": Counter("llm_requests_total", "Total requests", ["model"]),

    # Cost
    "tokens_consumed": Counter("llm_tokens_total", "Tokens", ["model", "type"]),
    "cost_dollars": Counter("llm_cost_usd", "Cost", ["model"]),

    # Quality
    "hallucination_rate": Gauge("llm_hallucination_rate", "Quality score"),
    "user_feedback": Counter("llm_feedback_total", "Feedback", ["rating"]),

    # Resources
    "gpu_utilization": Gauge("gpu_util_percent", "GPU util", ["instance"]),
    "cache_hit_rate": Gauge("cache_hit_rate", "Cache effectiveness"),
}

# OpenTelemetry tracing
async def traced_llm_call(prompt: str, model: str):
    with tracer.start_as_current_span("llm_call") as span:
        span.set_attribute("llm.model", model)
        span.set_attribute("llm.prompt_tokens", count_tokens(prompt))
        response = await call_llm(prompt, model)
        span.set_attribute("llm.completion_tokens", response.usage.completion)
        span.set_attribute("llm.cost_usd", calculate_cost(response.usage, model))
        return response
```

**Dashboard alerts:**

| Metric | Alert Threshold |
|---|---|
| p99 latency | > 15s |
| Error rate | > 5% |
| Tokens/request | > expected + 50% |
| GPU utilization | > 90% sustained |
| Cache hit rate | < 20% |
| Cost/hour | > budget × 1.2 |

---

## Quick Reference Table

| Topic | Key Concepts |
|---|---|
| **Architecture** | Modular monolith → microservices, API gateway, event-driven |
| **Caching** | Exact match, semantic cache, embedding cache, KV prefix cache |
| **Load Balancing** | Round robin, least connections, GPU-aware, token-aware |
| **Model Serving** | vLLM (PagedAttention), TGI, TensorRT-LLM, streaming |
| **Cost Optimization** | Model routing (cascade), prompt optimization, self-hosted fallback |
| **Reliability** | Circuit breaker, exponential backoff + jitter, fallback chain |
| **Scaling** | Horizontal (HPA), vertical (bigger GPU), auto-scaling triggers |
| **Multi-Region** | Global DNS, geo-routing, async replication, data residency |
| **Deployment** | Canary, blue-green, rolling, shadow traffic |
| **Observability** | Metrics + Logs + Traces + Quality (4 pillars) |


---

## Senior Deep Dive: Enterprise AI Architecture & Scalable Pipelines on Azure

> *The JD lists "AI Architecture" and "scalable AI pipelines" with an Azure emphasis. Interviewers want a reference architecture, a build-vs-buy stance, and answers on scale, failure, and security.*

### SQ1: Sketch a reference architecture for an enterprise GenAI platform on Azure.

**Answer:** Walk the layers from the ground up. At the **data and ingestion tier**, documents and transactions land in **Azure Data Lake / Blob Storage** and structured metadata lives in **Azure Database for PostgreSQL – Flexible Server**, which also hosts **pgvector** for co-located embeddings. At the **index and retrieval tier**, embeddings are generated via **Azure OpenAI** (e.g., `text-embedding-3-large`) and stored in pgvector or a dedicated vector service; retrieval combines hybrid search (dense + BM25) and a re-ranker. At the **model tier**, conversational and generation calls go to **Azure OpenAI** or **Azure AI Foundry** for managed hosted models; high-volume or custom models run on **AKS with vLLM** for self-hosted inference. The **orchestration tier** is the application layer — LangChain, LangGraph, or raw SDK calls — which composes retrieval, tool use, and generation. Traffic enters through **Azure API Management**, which handles authentication, rate limiting, caching, and routing. Cross-cutting concerns include **Azure Application Insights** for observability, **Azure Entra ID** and **Key Vault** for identity and secrets, **Private Link** for network isolation, eval/CI quality gates, and governance/audit logging.

The reference table below shows which Azure service maps to each concern:

| Layer | Azure Service | Purpose |
|---|---|---|
| Storage | Blob / Data Lake | Raw documents, artifacts |
| Vector + relational | PostgreSQL Flexible (pgvector) | Embeddings co-located with metadata |
| Managed LLM | Azure OpenAI / AI Foundry | Inference without infra |
| Self-hosted LLM | AKS + vLLM | Cost control at scale |
| Gateway | API Management | Auth, rate-limit, caching |
| Observability | Application Insights | Metrics, logs, traces |
| Security | Entra ID, Key Vault, Private Link | Identity, secrets, network isolation |

**Trade-off to close on:** every managed Azure service trades some control and marginal cost for speed to production and compliance certification — you choose per layer based on **scale, data sensitivity, and team capacity to operate infra**.

### SQ2: Build vs buy — managed model API vs self-hosted open model?

**Answer:** **Buy (Azure OpenAI / AI Foundry)** gets you the fastest path to production: managed horizontal scaling, no GPU ops, SLA-backed uptime, and built-in compliance posture (ISO 27001, SOC 2, GDPR data-residency regions). **Build (self-host on AKS + vLLM)** pays off when **cost-per-token at high volume** tips the math, when **data sensitivity** prohibits any third-party processor, when you need **model customization** beyond fine-tuning API access, or when you want to escape vendor rate limits for latency-critical paths. The decision hinges on five dimensions: **scale** (tokens/month), **data sensitivity**, **cost-per-token at volume**, **latency SLA**, and **customization needs**. **Trade-off:** managed wins on speed and compliance; self-hosted wins on cost and control at scale. Most teams start managed and migrate only the highest-volume or most sensitive workloads to self-hosted — resist premature optimization in either direction.

### SQ3: How do you make AI pipelines scalable and cost-controlled?

**Answer:** Scalability and cost discipline require levers at every stage. At the **ingestion side**, use **async queues** (Service Bus or Event Hub) so bursts don't block; **batch embedding calls** to maximize throughput and reduce per-call overhead. At the **inference side**, use **Provisioned Throughput Units (PTU)** for steady, predictable load — they offer consistent latency and lower effective cost than PAYG at volume — and fall back to PAYG for burst. Add **semantic and exact caching** (Azure Cache for Redis) so repeated or near-identical queries never touch the model. Implement **model routing**: a small, fast model (e.g., GPT-4o-mini) handles easy queries; the expensive model is reserved for cases the router classifies as hard. Apply **token budgets**: cap system prompt length, chunk sizes, and max-output tokens per tier. Scale the serving layer with **KEDA on AKS** (event-driven autoscaling on queue depth or GPU utilization). Track the primary metric as **cost per resolved task**, not cost per call — calls that get cached or routed to a smaller model still count as resolved. **Trade-off:** each lever introduces a small quality risk or latency overhead — tie the threshold for each control to its measured impact on task quality.

### SQ4: How do you design an LLM system for failure and resilience?

**Answer:** Resilience for LLM systems combines the patterns of distributed services with LLM-specific failure modes (model errors, content filters, context-length rejections, rate limits). Start with **timeouts** on every model call (not just TCP — also a wall-clock budget for the full chain). Add **retries with exponential backoff and jitter** for transient 429 and 5xx errors, but cap retry budget so a slow model doesn't cascade. Add a **fallback chain**: try the primary model, then a cheaper model, then a cached or template response, then a graceful error. **Circuit breakers** open after N failures in a window, short-circuiting to the fallback immediately rather than exhausting retry budget. For async pipelines use **dead-letter queues** to capture unprocessable messages without dropping them. Design operations to be **idempotent** so safe retries don't double-write. For production risk workloads, consider **multi-region PTU failover** and test failover paths in staging. **Trade-off:** every resilience mechanism — timeouts, retries, circuit breakers, fallbacks — adds latency, code complexity, and operational surface; calibrate the investment to the SLA and the business cost of an outage in a regulated risk context.

### SQ5: How do security and data residency shape the architecture in a regulated domain?

**Answer:** Regulated AI workloads must treat security as a first-class architectural constraint, not an afterthought. Use **Private Link and VNet integration** for all Azure service connections so traffic never traverses the public internet — no public endpoints for OpenAI, PostgreSQL, or Storage. **Pin deployments to a specific Azure region** that satisfies data residency obligations (e.g., EU for GDPR). Use **Entra ID** for all authentication (no static API keys in application config) and enforce **RBAC** at the resource level. Store all secrets and keys in **Azure Key Vault** with access policies tied to managed identities, not service principals with passwords. Apply **PII detection and redaction** before any user data enters a model call — log redaction decisions for the audit trail. Enable **customer-managed keys (CMK)** for data at rest where the regulation demands it. Maintain **end-to-end audit logging** of every model call, tool invocation, and data access, structured for ingestion into your SIEM. **Trade-off:** strict network isolation, CMK, and PII redaction slow initial development velocity and integration complexity — the mitigation is to bake all of these into a **paved path** (infrastructure templates, SDK wrappers) so individual teams don't face the compliance burden from scratch on every project.
