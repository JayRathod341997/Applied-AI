# Quiz

## Question 1

A three-person team is building their first GenAI product with two models and an uncertain feature set. Which deployment topology should they most likely start with?

A) Full microservices with a service mesh
B) A modular monolith
C) One serverless function per model call
D) A separate repo and cluster per model

---

**Answer: B**

A modular monolith gives a single deployable artifact (low operational overhead) while keeping clean internal seams that can later be split into services. Microservices add complexity that a small team and undefined product rarely need yet.

---

## Question 2

In the five-layer reference architecture (presentation, orchestration, inference, knowledge, data), where does agent logic, routing, and guardrail enforcement belong?

A) Presentation layer
B) Inference layer
C) Orchestration layer
D) Data layer

---

**Answer: C**

The orchestration layer coordinates the workflow — routing requests, running agent logic, enforcing guardrails, and managing sessions. It sits between presentation and inference and hides model details from the UI.

---

## Question 3

What is the primary purpose of a *provider abstraction* layer inside an API gateway?

A) To compress request payloads
B) To let application code call one interface while the actual vendor can be swapped via configuration
C) To encrypt traffic between services
D) To store the vector index

---

**Answer: B**

Provider abstraction exposes a single, stable interface to the app. Swapping OpenAI for Claude or a self-hosted Llama becomes a configuration change rather than a code rewrite, which also enables fallback chains.

---

## Question 4

A gateway tries the primary provider, and on failure tries the secondary, then the tertiary, returning the first success. This pattern is called a:

A) Round-robin load balancer
B) Fallback chain
C) Circuit breaker
D) Sidecar proxy

---

**Answer: B**

A fallback chain attempts providers in priority order and returns the first that succeeds, improving resilience when a vendor has an outage or rate-limits you. (A circuit breaker is related but instead *stops* calling a failing dependency for a cooldown period.)

---

## Question 5

Which workload is the best fit for a queue-based async architecture rather than synchronous request/response?

A) A real-time chat reply that must appear in under two seconds
B) Embedding 50,000 documents overnight
C) A health-check endpoint
D) Returning a cached value

---

**Answer: B**

Batch embedding is compute-heavy and latency-tolerant, so the client should get a `job_id` immediately while a worker pool processes the queue. Synchronous responses are reserved for fast, interactive calls.

---

## Question 6

In an event-driven document ingestion pipeline (parse → chunk → embed → index), what is the main advantage of making each stage its own consumer?

A) It guarantees exactly-once UI rendering
B) Each stage scales independently, so a slow embedder cannot stall the uploader
C) It removes the need for any storage
D) It eliminates the need for authentication

---

**Answer: B**

Decoupling stages via events lets each one scale on its own bottleneck. A slow or backlogged embedding stage simply builds queue depth without blocking upstream stages like upload and parsing.

---

## Question 7

What does vLLM's PagedAttention primarily improve?

A) Model accuracy on benchmarks
B) KV-cache memory efficiency, enabling larger batch sizes
C) Training speed
D) Network encryption

---

**Answer: B**

PagedAttention stores the KV cache in non-contiguous pages (like OS virtual memory), nearly eliminating fragmentation. The freed memory lets vLLM pack more concurrent sequences and run continuous batching for higher throughput.

---

## Question 8

You are deploying a 70B-parameter model that needs about 140 GB in FP16, but each GPU has only 80 GB. What technique lets you serve it?

A) Increase the batch size
B) Tensor parallelism across multiple GPUs
C) Lower the temperature
D) Disable the KV cache

---

**Answer: B**

Tensor parallelism (`--tensor-parallel-size`) splits each layer's weight matrices across GPUs so the model that doesn't fit on one card is sharded across several, with an all-reduce step per layer.

---

## Question 9

For a 7B model that fits comfortably in a single GPU's memory, why is `--tensor-parallel-size 1` usually the right choice?

A) Tensor parallelism would add inter-GPU communication overhead with no benefit
B) The model cannot run on more than one GPU
C) Quantization is impossible otherwise
D) Single GPU prevents continuous batching

---

**Answer: A**

When weights fit on one GPU, splitting them adds per-layer all-reduce communication that makes inference *slower*, not faster. Multi-GPU is justified only when the model doesn't fit on a single card.

---

## Question 10

Which gateway function directly protects backend model servers from a sudden traffic spike?

A) Provider abstraction
B) Token metering for billing
C) Rate limiting / request queuing
D) Response caching of identical prompts

---

**Answer: C**

Rate limiting (and buffering excess requests in a queue) caps the load reaching the backends so a spike cannot overwhelm them. Caching helps cost and latency but does not by itself bound the request rate.
