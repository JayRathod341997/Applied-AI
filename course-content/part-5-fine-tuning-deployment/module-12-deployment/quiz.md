# Module 12: Deployment Strategies — Quiz

**Instructions:** Select the best answer for each question. Click the toggle to reveal the correct answer and explanation.

---

### Q1. What is the primary advantage of multi-stage Docker builds for LLM applications?

- A) They allow running multiple models in one container
- B) They reduce final image size by separating build and runtime dependencies
- C) They automatically download models from HuggingFace
- D) They enable GPU passthrough to Docker

<details>
<summary>Answer</summary>

**B) They reduce final image size by separating build and runtime dependencies.**

Multi-stage builds copy only the compiled artifacts and runtime dependencies into the final image, excluding compilers, build tools, and intermediate layers. This can reduce image size by 40-60%.
</details>

---

### Q2. In Kubernetes, what resource type ensures a specified number of pod replicas are always running?

- A) Pod
- B) Service
- C) Deployment
- D) ConfigMap

<details>
<summary>Answer</summary>

**C) Deployment**

A Deployment manages ReplicaSets and ensures the desired number of pods are running. It also handles rolling updates and rollbacks. A Pod is a single instance, a Service provides networking, and a ConfigMap stores configuration.
</details>

---

### Q3. Which Kubernetes object provides a stable network endpoint for a set of pods?

- A) Deployment
- B) Service
- C) Ingress
- D) HorizontalPodAutoscaler

<details>
<summary>Answer</summary>

**B) Service**

A Kubernetes Service abstracts access to a set of pods using label selectors and provides a stable ClusterIP, NodePort, or LoadBalancer address. Ingress handles HTTP routing, but Service is the fundamental networking primitive.
</details>

---

### Q4. What is PagedAttention, used in vLLM?

- A) A method to paginate API responses
- B) A memory management technique for KV cache that reduces waste by treating it like virtual memory pages
- C) A prompt engineering technique
- D) A way to distribute attention across multiple GPUs

<details>
<summary>Answer</summary>

**B) A memory management technique for KV cache that reduces waste by treating it like virtual memory pages.**

PagedAttention borrows the concept of virtual memory paging from operating systems. It allocates KV cache blocks on demand, eliminating internal fragmentation and enabling near-zero wasted memory during batched inference.
</details>

---

### Q5. In a blue-green deployment, when do you switch traffic to the new version?

- A) Immediately after building the new image
- B) After the new version passes smoke tests and health checks
- C) Gradually over 24 hours
- D) Only during maintenance windows

<details>
<summary>Answer</summary>

**B) After the new version passes smoke tests and health checks.**

Blue-green deployments stand up the full new environment (green), validate it, then switch the load balancer. This provides instant rollback capability. Traffic is not gradual (that's canary) and doesn't require maintenance windows.
</details>

---

### Q6. Which scaling signal is most relevant for LLM inference workloads?

- A) CPU utilization
- B) Network bandwidth
- C) Request queue depth or GPU utilization
- D) Disk I/O

<details>
<summary>Answer</summary>

**C) Request queue depth or GPU utilization.**

LLM inference is GPU-bound. CPU utilization may stay low while the GPU is saturated. Request queue depth and GPU utilization directly reflect the model server's capacity to handle more work.
</details>

---

### Q7. What does AWQ (Activation-Aware Quantization) do?

- A) Quantizes only the activation tensors
- B) Quantizes model weights to INT4 while preserving accuracy by considering activation distributions
- C) Adds quantization-aware training to existing models
- D) Compresses the KV cache to INT8

<details>
<summary>Answer</summary>

**B) Quantizes model weights to INT4 while preserving accuracy by considering activation distributions.**

AWQ observes which weight channels are most important for preserving activation magnitudes and applies less aggressive quantization to those channels, achieving INT4 compression with minimal accuracy degradation.
</details>

---

### Q8. What is the purpose of a readiness probe in a Kubernetes deployment?

- A) To restart the container if it crashes
- B) To check if the container is ready to accept traffic
- C) To verify the container has enough memory
- D) To test network connectivity to external services

<details>
<summary>Answer</summary>

**B) To check if the container is ready to accept traffic.**

Readiness probes determine whether a pod should receive traffic via the Service. A failing readiness probe removes the pod from the Service endpoints without restarting it. Liveness probes handle crash detection and restarts.
</details>

---

### Q9. In Azure Container Apps, what enables scale-to-zero behavior?

- A) Azure Functions runtime
- B) KEDA (Kubernetes Event-Driven Autoscaling)
- C) Azure Load Balancer health probes
- D) Application Gateway

<details>
<summary>Answer</summary>

**B) KEDA (Kubernetes Event-Driven Autoscaling).**

Azure Container Apps uses KEDA for autoscaling. KEDA supports scaling to zero replicas when no events (HTTP requests, queue messages, etc.) are detected, then scales back up when traffic arrives.
</details>

---

### Q10. Which protocol is best suited for streaming LLM token responses to a client?

- A) gRPC unary calls
- B) Server-Sent Events (SSE) or WebSocket
- C) Raw TCP sockets
- D) SMTP

<details>
<summary>Answer</summary>

**B) Server-Sent Events (SSE) or WebSocket.**

SSE is ideal for one-way server-to-client streaming (simple, works over HTTP). WebSocket is better for bidirectional communication. Both are standard for LLM token streaming. gRPC supports streaming but is less common in browser-based clients.
</details>

---

### Q11. What is a canary deployment?

- A) Deploying to a single replica first
- B) Routing a small percentage of traffic to the new version while most traffic goes to the stable version
- C) Testing in production with feature flags only
- D) Deploying the same version to two regions simultaneously

<details>
<summary>Answer</summary>

**B) Routing a small percentage of traffic to the new version while most traffic goes to the stable version.**

Canary deployments gradually shift traffic (e.g., 5% → 25% → 50% → 100%) to a new version. If errors are detected, traffic is routed back to the stable version. This minimizes the blast radius of bad deployments.
</details>

---

### Q12. What is the primary role of Azure API Management (APIM) in an LLM deployment?

- A) Training models
- B) Providing authentication, rate limiting, caching, and observability as a gateway layer
- C) Storing model weights
- D) Managing Kubernetes clusters

<details>
<summary>Answer</summary>

**B) Providing authentication, rate limiting, caching, and observability as a gateway layer.**

APIM acts as an API gateway that sits in front of backend services. It handles cross-cutting concerns like auth, throttling, response caching, request/response transformation, and logging — all without modifying the LLM server code.
</details>

---

### Q13. What is continuous batching in LLM serving?

- A) Processing all queued requests simultaneously
- B) Dynamically adding and removing requests from a batch as they complete, rather than waiting for the longest request
- C) Batching requests by time window
- D) Pre-batching prompts during tokenization

<details>
<summary>Answer</summary>

**B) Dynamically adding and removing requests from a batch as they complete, rather than waiting for the longest request.**

Without continuous batching, a batch waits for the longest sequence to finish, wasting GPU cycles. Continuous batching (iteration-level scheduling) immediately slots in new requests as existing ones complete, dramatically improving throughput.
</details>

---

### Q14. In a Dockerfile, what does the HEALTHCHECK instruction do?

- A) Installs health monitoring software
- B) Tells Docker how to test if the container is still working, and marks it unhealthy if the check fails repeatedly
- C) Configures Kubernetes liveness probes
- D) Sends alerts to Azure Monitor

<details>
<summary>Answer</summary>

**B) Tells Docker how to test if the container is still working, and marks it unhealthy if the check fails repeatedly.**

HEALTHCHECK is a Docker-level instruction that runs a command periodically. If the command fails (non-zero exit) enough times, Docker marks the container as "unhealthy." This is independent of Kubernetes probes, though both serve similar purposes.
</details>

---

### Q15. Which quantization method is best for reducing GPU memory usage of a 70B parameter model to fit on a single A100 (80GB)?

- A) FP16
- B) BF16
- C) INT4 AWQ or GPTQ
- D) INT8 only

<details>
<summary>Answer</summary>

**C) INT4 AWQ or GPTQ.**

A 70B model in FP16 requires ~140GB VRAM. INT8 brings it to ~70GB (still tight with KV cache). INT4 AWQ/GPTQ reduces it to ~35GB, leaving room for KV cache and activations on a single 80GB A100.
</details>

---

### Q16. What is the benefit of prefix caching in vLLM?

- A) Caches HTTP responses at the API gateway
- B) Reuses KV cache computations for shared prompt prefixes across requests, reducing prefill time
- C) Stores model weights in CPU cache
- D) Caches tokenized prompts in Redis

<details>
<summary>Answer</summary>

**B) Reuses KV cache computations for shared prompt prefixes across requests, reducing prefill time.**

When multiple requests share a common prefix (e.g., the same system prompt), prefix caching avoids recomputing the KV cache for that prefix. This significantly reduces time-to-first-token for batched workloads.
</details>

---

### Q17. In Azure Container Apps, what is a "revision"?

- A) A Git commit
- B) An immutable snapshot of a container app's configuration and containers, enabling traffic splitting and rollbacks
- C) A backup of the container image
- D) A version of the Bicep template

<details>
<summary>Answer</summary>

**B) An immutable snapshot of a container app's configuration and containers, enabling traffic splitting and rollbacks.**

Each time you update a Container App, a new revision is created. You can split traffic between revisions (e.g., 90/10 for canary) and instantly roll back by shifting all traffic to a previous revision.
</details>

---

### Q18. Why is a "scale-down stabilization window" important for LLM deployments?

- A) It prevents models from being deleted
- B) It delays scale-down to avoid thrashing when traffic is bursty, preventing premature pod termination
- C) It ensures models are cached before scaling down
- D) It limits the number of scale-down events per day

<details>
<summary>Answer</summary>

**B) It delays scale-down to avoid thrashing when traffic is bursty, preventing premature pod termination.**

LLM workloads can be bursty. Without a stabilization window, the autoscaler might scale down pods immediately after a burst, then have to scale back up moments later. This thrashing wastes resources and adds latency from cold starts.
</details>

---

### Q19. What does the `--tensor-parallel-size` flag do in vLLM?

- A) Sets the number of CPU threads
- B) Splits model layers across multiple GPUs for parallel computation
- C) Configures the number of API workers
- D) Sets the batch size for tensor operations

<details>
<summary>Answer</summary>

**B) Splits model layers across multiple GPUs for parallel computation.**

Tensor parallelism partitions each model layer's weight matrices across N GPUs. Each GPU computes a portion of each layer, then results are aggregated. This is essential for models too large for a single GPU.
</details>

---

### Q20. In a CI/CD pipeline for LLM deployment, what should happen after the container image is pushed?

- A) Delete the old image immediately
- B) Update the deployment to use the new image, run health checks, and verify the service
- C) Notify the data science team
- D) Retrain the model

<details>
<summary>Answer</summary>

**B) Update the deployment to use the new image, run health checks, and verify the service.**

After pushing the image, the pipeline should update the container orchestrator (K8s deployment, Container App, etc.), wait for the rollout, run health/smoke tests, and either proceed or roll back based on results.
</details>

---

## Score Interpretation

| Score | Level | Recommendation |
|-------|-------|----------------|
| **18-20** | Expert | Ready for production deployment architecture. Focus on advanced patterns (service mesh, multi-region). |
| **14-17** | Proficient | Solid foundation. Review Kubernetes autoscaling and GPU optimization in depth. |
| **10-13** | Intermediate | Good conceptual understanding. Practice hands-on with Docker, K8s manifests, and Azure CLI. |
| **6-9** | Developing | Review containerization fundamentals and API design patterns. Revisit Module 12 concepts. |
| **0-5** | Beginner | Start with Docker basics and Kubernetes concepts before attempting LLM deployment. |

---

## Bonus: Senior / JD-Aligned Questions (Deploying GenAI on Azure)

> Self-contained — answer follows each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. What is the relationship between Azure AI Foundry, Azure OpenAI Service, and Azure Machine Learning?

A) They are three names for the same product  
B) Foundry = GenAI app lifecycle platform; Azure OpenAI = hosted frontier models in your tenant; Azure ML = general MLOps for any/custom model  
C) Azure ML is only for image generation  
D) Azure OpenAI replaces Azure ML entirely  

**Answer: B** — they compose: Foundry orchestrates the GenAI app lifecycle, Azure OpenAI serves the managed OpenAI models, and Azure ML provides broader MLOps including classic/custom models.

### BQ2. Your LLM workload has predictable, sustained high volume with a strict latency SLA. Which Azure OpenAI capacity model fits best?

A) Pay-as-you-go (PAYG) only  
B) Provisioned Throughput Units (PTU) for reserved, stable-latency capacity  
C) The free tier  
D) Self-hosting on a single CPU VM  

**Answer: B** — PTU reserves guaranteed throughput with stable latency and avoids 429 throttling; PAYG is better below the break-even volume or for bursty spillover.

### BQ3. What is the standard pattern to scale beyond per-region Azure OpenAI quota and survive a regional outage?

A) Retry forever with no backoff  
B) Put APIM / a gateway in front of multiple Azure OpenAI deployments across regions and load-balance + failover  
C) Increase `max_tokens` on every call  
D) Disable content filtering  

**Answer: B** — the "smart load balancer" pattern spreads load across regional quota pools and provides failover; combine with backoff that honors `Retry-After`.

### BQ4. Which is the most secure way for an app to authenticate to Azure OpenAI in an enterprise tenant?

A) Hard-code the API key in the container image  
B) Microsoft Entra ID with Managed Identity (no keys in code) + least-privilege RBAC  
C) Share one key across all teams via email  
D) Put the key in a public environment variable  

**Answer: B** — Managed Identity removes long-lived secrets from code; pair with Private Endpoints, Key Vault, and region/data-boundary controls.

### BQ5. In an Azure LLMOps pipeline, what should gate promotion of a new prompt/model to production?

A) Whoever approves first by Slack message  
B) An automated evaluation step (groundedness/relevance/safety) that blocks on regression, followed by canary/blue-green rollout with rollback  
C) Only unit tests on the API wrapper  
D) Manual eyeballing of three examples  

**Answer: B** — the senior signal is an eval-gated, reversible deployment; Foundry evaluations in CI plus canary/blue-green and automated rollback.

---

*End of Module 12 Quiz*
