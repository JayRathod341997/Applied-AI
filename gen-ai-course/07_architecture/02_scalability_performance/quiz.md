# Quiz

Test your understanding of scalability and performance for GenAI systems. Pick one answer, then check the explanation.

---

## Question 1

A 70B-parameter model does not fit on a single GPU. What is the correct first scaling move?

A) Add more replicas behind a load balancer (scale out)
B) Shard the model across GPUs on one node (scale up with parallelism)
C) Enable scale-to-zero
D) Switch the load balancer to round-robin

---

**Answer: B**

When a model is too large for one GPU, you must first scale *vertically* using tensor/pipeline parallelism so a single serving unit can hold it. Only after one replica is healthy do you scale *out* by replicating that sharded unit for throughput. You cannot add replicas of something that does not run at all.

---

## Question 2

Why is plain round-robin load balancing a poor fit for LLM serving?

A) It requires a vector database
B) It cannot perform health checks
C) Request cost varies wildly (50 vs 4,000 tokens) but round-robin treats every request as equal
D) It only works with a single replica

---

**Answer: C**

Round-robin assumes uniform request cost. LLM requests vary enormously in token count and therefore GPU time, so round-robin can pile heavy requests onto one replica while others sit idle. Least-connections or token-aware balancing adapts to actual load.

---

## Question 3

For autoscaling a vLLM deployment, which metric is the *best* scaling signal?

A) CPU utilization
B) Disk I/O
C) Number of HTTP 200 responses
D) Queue depth (requests waiting) and GPU utilization

---

**Answer: D**

GPUs, not CPUs, are the bottleneck in model serving, and CPU utilization often stays low while the GPU is saturated. Scaling on queue depth (`num_requests_waiting`) and GPU utilization reflects real inference pressure.

---

## Question 4

What is the main tradeoff of scale-to-zero?

A) It increases idle GPU cost
B) It introduces cold-start latency when the first request arrives
C) It prevents horizontal scaling
D) It disables caching

---

**Answer: B**

Scale-to-zero removes all replicas when idle (saving money), but the next request must wait for a pod to start and load multi-GB weights onto a GPU — often 30–90s. It is great for spiky/low-traffic workloads, less so for latency-critical paths.

---

## Question 5

A user asks "How do I reset my password?" and later another asks "I forgot my password, how can I change it?" Which cache type can serve the second from the first?

A) Exact-match response cache
B) Semantic cache
C) KV/prefix cache
D) None — they are different strings

---

**Answer: B**

The two queries are different strings, so an exact-match cache misses. A semantic cache embeds both and compares cosine similarity; because they are semantically close, the second query can return the first's cached answer (assuming similarity exceeds the threshold).

---

## Question 6

In a semantic cache, you *lower* the similarity threshold τ from 0.95 to 0.80. What happens?

A) Hit rate drops; fewer false positives
B) Hit rate rises; more risk of returning a wrong/irrelevant answer
C) Nothing changes
D) The cache stops expiring entries

---

**Answer: B**

A lower threshold means more queries qualify as "similar enough," raising the hit rate but also accepting looser matches — increasing the chance of returning an answer that does not actually fit the new query. τ is a precision/recall dial.

---

## Question 7

Which statement about embedding caches is correct?

A) They risk returning stale or wrong answers
B) They save cost on the LLM completion call
C) They are safe because embeddings are deterministic for a given text+model, saving latency without correctness risk
D) They require a load balancer

---

**Answer: C**

For a fixed text and embedding model, the embedding is deterministic, so caching it just avoids recomputation — pure latency/compute savings with no correctness tradeoff. It does not affect the completion call's cost.

---

## Question 8

Why does every cache entry need a TTL?

A) To make lookups faster
B) So stale data eventually expires instead of being served forever
C) Because Redis requires it
D) To enable round-robin

---

**Answer: B**

A TTL bounds how long an entry can be served. Without it, a cached answer could outlive the facts it was based on (e.g., after documents are re-indexed), serving stale or incorrect content indefinitely.

---

## Question 9

A RAG knowledge base is re-indexed with new documents. What is the right cache action?

A) Lower the load-balancer weights
B) Invalidate or version-bump the response/semantic cache so old answers are not served
C) Increase the TTL
D) Disable connection pooling

---

**Answer: B**

Cached answers were grounded in the *old* index. After re-indexing you should invalidate affected entries or bump a `kb_version` baked into cache keys, so users get answers grounded in current content rather than deleted documents.

---

## Question 10

In a multi-region deployment, which consistency model is appropriate for the response cache vs. billing/quota counters?

A) Strong for both
B) Eventual for both
C) Eventual for cache, strong for billing
D) Strong for cache, eventual for billing

---

**Answer: C**

A slightly stale cache entry is harmless and cheap to replicate eventually, so eventual consistency is fine and fast. Billing and quota enforcement must be accurate (no double-spend / overage), so they need strong consistency.

---

## Question 11

What problem does connection pooling solve?

A) It encrypts traffic between regions
B) It avoids the per-request TCP/TLS handshake and fd exhaustion by reusing warm connections
C) It selects the least-loaded replica
D) It expires stale cache entries

---

**Answer: B**

Opening a fresh connection per request adds handshake latency and can exhaust file descriptors under load. A pool keeps reusable, warm connections to downstream services so requests borrow and return connections instead of opening new ones.

---

## Question 12

Which best describes the difference between horizontal and vertical scaling cost curves?

A) Both are linear
B) Vertical is roughly linear; horizontal is exponential
C) Vertical is exponential (bigger GPUs cost disproportionately more); horizontal is roughly linear
D) Neither affects cost

---

**Answer: C**

Moving to a bigger GPU (A100 → H100) costs disproportionately more for each capacity step — an exponential-ish curve with a hard ceiling per machine. Adding identical replicas scales cost roughly linearly and has practically no ceiling.

---
