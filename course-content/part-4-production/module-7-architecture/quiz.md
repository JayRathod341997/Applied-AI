# Module 7: Architecture Design — Quiz

## Instructions
- 20 multiple choice questions
- Each question has one correct answer
- Click the `<details>` tag to reveal the answer and explanation

---

## Questions

### Q1. What is the primary advantage of a modular monolith over full microservices for an early-stage AI product?

A) It provides automatic horizontal scaling  
B) It keeps operational complexity low while maintaining clean internal boundaries  
C) It eliminates the need for an API gateway  
D) It guarantees zero-downtime deployments  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** A modular monolith organizes code into well-defined modules (inference, cache, auth) within a single deployable artifact. This avoids the operational overhead of service discovery, inter-service networking, and distributed tracing that comes with microservices, while still preserving clean separation of concerns that makes future extraction easy.

</details>

---

### Q2. Which API gateway capability is MOST effective at preventing unexpected LLM cost overruns?

A) SSL termination  
B) CORS header management  
C) Rate limiting per user/org  
D) Request logging  

<details>
<summary><strong>Answer: C</strong></summary>

**Explanation:** Rate limiting directly controls how many inference requests each client can make per time window. Since LLM costs are driven by request count × token count, capping request volume per user/org is the most direct mechanism for preventing cost overruns from unbounded API usage.

</details>

---

### Q3. In an async architecture, what component decouples the API server from GPU-bound inference workers?

A) Load balancer  
B) CDN  
C) Message queue (Redis, Kafka, SQS)  
D) DNS resolver  

<details>
<summary><strong>Answer: C</strong></summary>

**Explanation:** A message queue sits between the API server and the worker pool. The API enqueues a task and immediately returns a job ID to the client. GPU workers dequeue tasks at their own pace, allowing independent scaling of request-handling (CPU) and inference (GPU) tiers.

</details>

---

### Q4. Which load balancing strategy is best suited for GPU-bound LLM inference with highly variable request sizes?

A) Round robin  
B) Source IP hash  
C) GPU utilization-aware routing  
D) Random selection  

<details>
<summary><strong>Answer: C</strong></summary>

**Explanation:** GPU utilization-aware routing tracks each replica's GPU memory usage, active requests, and latency, then routes new requests to the least-loaded replica. This prevents overload on any single GPU and maximizes aggregate throughput for workloads where individual requests vary dramatically in token count.

</details>

---

### Q5. What distinguishes a semantic cache from an exact-match cache in AI systems?

A) Semantic cache stores model weights; exact-match stores prompts  
B) Semantic cache returns cached responses for queries with similar meaning based on embedding similarity, even if the text differs  
C) Semantic cache only works with Redis; exact-match works with any store  
D) Semantic cache is always slower than exact-match  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** A semantic cache computes an embedding for each incoming query and performs a vector similarity search against cached query embeddings. If the similarity exceeds a threshold (e.g., 0.92), the cached response is returned. This yields 30–60% hit rates vs. 15–30% for exact-match, because paraphrased or equivalent questions map to the same cached answer.

</details>

---

### Q6. What is the primary trade-off of batched model serving (e.g., continuous batching in vLLM)?

A) Higher cost per request  
B) Lower GPU utilization  
C) Higher per-request latency in exchange for higher throughput  
D) Increased memory usage with no throughput benefit  

<details>
<summary><strong>Answer: C</strong></summary>

**Explanation:** Batching accumulates multiple requests into a single GPU kernel invocation, maximizing parallelism and overall throughput. The trade-off is that individual requests must wait for the batch window, adding latency. vLLM's PagedAttention mitigates this with continuous batching that dynamically adds/removes requests mid-batch.

</details>

---

### Q7. In the circuit breaker pattern, what happens when the breaker transitions to the OPEN state?

A) All requests are forwarded with increased timeout  
B) Requests are rejected immediately with a fallback response  
C) The system shuts down all model replicas  
D) Requests are queued for later processing  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** In the OPEN state, the circuit breaker has detected that failures exceed the configured threshold. Rather than continuing to send requests to the failing service (which would waste resources and increase latency), it short-circuits all calls and returns a fallback response immediately, protecting downstream services and reducing user-facing latency.

</details>

---

### Q8. What problem does adding jitter to exponential backoff solve?

A) Memory leaks in long-running processes  
B) The thundering herd problem where all clients retry simultaneously  
C) Token limit exceeded errors  
D) Cache invalidation races  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Without jitter, every client experiencing a failure retries at identical intervals (1s, 2s, 4s, ...), creating synchronized load spikes that can overwhelm a recovering service. Jitter adds a random offset to each client's delay (e.g., delay ± 50%), spreading retries across time and preventing re-overload.

</details>

---

### Q9. Which cost optimization strategy provides the highest potential savings for a production AI application?

A) Always using the cheapest available model  
B) Intelligent model routing based on query complexity classification  
C) Increasing batch sizes to maximum  
D) Disabling all caching  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Model routing classifies queries by complexity and routes simple requests (greetings, factual lookups) to cheap models (GPT-4o-mini at $0.15/1M tokens) and complex requests (analysis, code generation) to expensive models (GPT-4o at $2.50/1M tokens). This can save 40–70% on costs without quality loss, outperforming blanket strategies.

</details>

---

### Q10. What is the primary benefit of multi-region deployment for AI inference systems?

A) Reduced code complexity  
B) Lower latency, high availability, and disaster recovery  
C) Elimination of rate limiting needs  
D) Simplified model training  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Multi-region deployment places inference servers close to users (reducing network latency), provides redundant capacity across regions (high availability), and ensures that a regional outage doesn't take down the entire service (disaster recovery via DNS failover).

</details>

---

### Q11. Which metric is the MOST direct indicator of AI system cost efficiency?

A) CPU utilization across API servers  
B) Cost per query and tokens consumed per request  
C) Number of active WebSocket connections  
D) Disk I/O on the model server  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** AI inference costs are driven by token consumption (input + output tokens × per-token price) and GPU hours. Cost per query directly measures spending efficiency, while tokens-per-request reveals prompt/output optimization opportunities. These metrics have the strongest correlation to actual spend.

</details>

---

### Q12. In a well-designed fallback chain, what is typically the LAST resort when all model providers fail?

A) Retry the primary model indefinitely  
B) Return a pre-defined template response or the closest semantic cache hit  
C) Return HTTP 500 with no body  
D) Switch to a completely different application  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** A robust fallback chain progresses from high-quality/expensive to low-cost/degraded options: primary model → secondary model → semantic cache → template response. The template or cached response guarantees the user receives something functional rather than an error, maintaining service availability even during total model provider outages.

</details>

---

### Q13. What is the main limitation of vertical scaling for AI inference workloads?

A) It cannot improve performance at all  
B) It hits hardware limits (max GPUs/RAM per node) and costs scale exponentially  
C) It requires rewriting application code  
D) It increases network latency between services  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Vertical scaling is constrained by the maximum hardware available in a single machine (e.g., 8 GPUs per node). Beyond that, costs scale exponentially — an 8-GPU node costs far more than 8× a 1-GPU node. Horizontal scaling (adding more machines) avoids both limits and provides linear cost scaling.

</details>

---

### Q14. What does the HALF_OPEN state in a circuit breaker accomplish?

A) It permanently disables the downstream service  
B) It tests recovery by allowing a limited number of probe requests through  
C) It redirects all traffic to a cache  
D) It doubles the rate limit  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** After the recovery timeout expires, the circuit breaker enters HALF_OPEN and allows a small number of test requests (e.g., 3) to reach the downstream service. If they succeed, the breaker closes (resumes normal operation). If they fail, it reopens. This prevents immediately overwhelming a potentially still-unstable service.

</details>

---

### Q15. For repeated identical queries, which caching layer provides the highest cost reduction?

A) CDN cache  
B) Exact-match result cache (Redis)  
C) Semantic cache  
D) Browser cache  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** An exact-match cache keyed by hash(model + query) returns the cached response in ~1 ms with zero inference cost. For identical queries, this provides 100% cost elimination. While semantic cache has higher overall hit rates across varied queries, exact-match is the most efficient for truly repeated queries.

</details>

---

### Q16. Why is a cooldown period essential in auto-scaling policies for GPU inference clusters?

A) To allow GPU hardware to cool down thermally  
B) To prevent oscillation (thrashing) from rapid scale-up and scale-down cycles  
C) To wait for DNS propagation  
D) To flush in-flight requests  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Without a cooldown, a brief traffic spike triggers scale-up, then the immediate drop triggers scale-down, creating a continuous oscillation that wastes resources on repeated instance provisioning/teardown. A 5-minute cooldown stabilizes the system by preventing further scaling actions until the cooldown expires.

</details>

---

### Q17. What advantage does gRPC streaming provide over REST for LLM inference?

A) Simpler client-side integration  
B) Lower time-to-first-token by sending partial results as they're generated  
C) Automatic model fine-tuning  
D) Better error handling  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** gRPC streaming allows the server to push generated tokens to the client as they are produced, rather than waiting for the complete response. This reduces perceived latency (time-to-first-token) from seconds to milliseconds, critical for chat and code-generation UX, even though total generation time is unchanged.

</details>

---

### Q18. What is the primary decision factor when choosing between horizontal and vertical scaling for large language model inference?

A) Programming language of the serving framework  
B) Whether the model's memory requirements fit within a single node's GPU memory  
C) Number of API consumers  
D) Geographic distribution of users  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** If a model's weights + KV cache fit within one node's GPU memory (e.g., Llama 8B on a single A100), vertical scaling is simpler and avoids inter-node communication overhead. If the model exceeds single-node memory (e.g., Llama 405B), horizontal tensor/pipeline parallelism across multiple nodes is required.

</details>

---

### Q19. Which observability signal is MOST likely to indicate a prompt injection attack in progress?

A) Increased GPU utilization  
B) Sudden spike in tokens-per-request without a corresponding increase in request count  
C) Higher cache hit rate  
D) Lower p99 latency  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Prompt injection attacks typically append long adversarial strings to user inputs, dramatically increasing input token counts. A sudden increase in tokens-per-request without a matching increase in request volume is a strong signal of abuse, prompt bloat, or injection — all of which directly drive cost overruns.

</details>

---

### Q20. When all fallback strategies in a reliability chain have been exhausted, what is the recommended response?

A) Return an infinite retry loop  
B) Return a graceful error response with a correlation ID for debugging and alert on-call  
C) Silently return `null`  
D) Crash the process to trigger container restart  

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** The system should return a user-friendly error message containing a correlation/request ID that support engineers can use to trace the failure in logs and traces. Simultaneously, an alert should fire to the on-call team. This balances user experience (no crash, useful error info) with operational awareness for rapid incident response.

</details>

---

## Score Interpretation

| Score | Level | Recommendation |
|---|---|---|
| 18–20 | **Excellent** | Ready for Module 8: CI/CD |
| 14–17 | **Good** | Review weak areas before proceeding |
| 10–13 | **Fair** | Re-read `concepts.md` and retry the quiz |
| Below 10 | **Needs Work** | Study the module thoroughly; focus on reliability patterns and caching |


---

## Bonus: Senior / JD-Aligned Questions (Enterprise AI Architecture on Azure)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. What is the strongest reason to choose Azure OpenAI / AI Foundry over self-hosting?

A) It is always cheaper at every scale  
B) Speed to production plus managed scaling and compliance, with no infrastructure burden  
C) It allows arbitrary weight surgery  
D) It removes the need for evaluation  

**Answer: B** — managed services win on speed, scaling, and compliance; self-hosting wins on cost-at-scale and control.

### BQ2. What is the strongest reason to self-host an open model on AKS?

A) It is simpler than a managed API  
B) Lower cost-per-token at high volume, full data control, customization, and no vendor rate limits  
C) It needs no monitoring  
D) It guarantees higher accuracy  

**Answer: B** — self-hosting pays off for high-volume, sensitive, or heavily-customized workloads.

### BQ3. Which lever gives predictable cost/latency for steady high-volume LLM traffic on Azure?

A) Always PAYG  
B) Provisioned throughput (PTU) for steady load, combined with caching and routing  
C) Disabling retries  
D) A larger context window  

**Answer: B** — PTU reserves throughput for predictable load; caching/routing cut redundant spend.

### BQ4. Which Azure control keeps AI traffic off the public internet in a regulated system?

A) A public IP  
B) Private Link / VNet integration  
C) A larger SKU  
D) Disabling TLS  

**Answer: B** — Private Link / VNet integration removes public egress for sensitive workloads.

### BQ5. What is the right primary cost metric for an LLM platform?

A) Cost per API call  
B) Cost per resolved task  
C) Number of tokens generated  
D) Number of deployed models  

**Answer: B** — cost per resolved task reflects real business value, not just per-call price.
