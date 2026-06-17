# Module 12: Deployment Strategies — Interview Questions

---

## Quick Reference Table

| # | Question | Level | Topic |
|---|----------|-------|-------|
| 1 | What is containerization and why use it for LLM apps? | Beginner | Containers |
| 2 | Explain the difference between a Docker image and a container. | Beginner | Containers |
| 3 | What is a Kubernetes Deployment vs a Pod? | Beginner | Kubernetes |
| 4 | What are liveness and readiness probes? | Beginner | Health Checks |
| 5 | What is serverless deployment? | Beginner | Serverless |
| 6 | What is the difference between REST and WebSocket for LLM APIs? | Beginner | API Design |
| 7 | Explain blue-green vs canary deployments. | Intermediate | Patterns |
| 8 | What is continuous batching in LLM serving? | Intermediate | Model Serving |
| 9 | How does vLLM's PagedAttention improve inference? | Intermediate | Model Serving |
| 10 | What is AWQ quantization and why is it useful? | Intermediate | Optimization |
| 11 | How would you design auto-scaling for an LLM deployment? | Intermediate | Scaling |
| 12 | Explain the role of Azure API Management in LLM architecture. | Intermediate | Azure |
| 13 | What is tensor parallelism and when is it needed? | Intermediate | GPU |
| 14 | How do you handle long-running streaming responses in production? | Intermediate | API Design |
| 15 | Design a deployment architecture for a multi-model LLM platform. | Advanced | Architecture |
| 16 | How would you implement canary deployments for a model update? | Advanced | Patterns |
| 17 | Explain cost optimization strategies for GPU-based LLM serving. | Advanced | Cost |
| 18 | How do you achieve zero-downtime deployments for LLM services? | Advanced | Patterns |
| 19 | Design a CI/CD pipeline for LLM container deployment on Azure. | Advanced | CI/CD |
| 20 | How would you troubleshoot a production LLM deployment with high latency? | Advanced | Troubleshooting |

---

## Detailed Answers

---

### Q1. What is containerization and why use it for LLM applications?

**Level:** Beginner

**Answer:**

Containerization packages an application with all its dependencies, runtime, and configuration into a single, portable unit called a container. For LLM applications, this is critical because:

- **Dependency isolation**: LLM apps require specific CUDA versions, PyTorch builds, and Python packages that may conflict with other applications.
- **Reproducibility**: The same container runs identically on a developer laptop, CI server, and production GPU cluster.
- **Model versioning**: Model weights can be baked into or mounted onto a container, creating an immutable artifact tied to a specific model version.
- **Scaling**: Containers are the unit of scaling in Kubernetes, Container Apps, and ECS.

```dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04
COPY --from=builder /app /app
ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]
```

---

### Q2. Explain the difference between a Docker image and a container.

**Level:** Beginner

**Answer:**

| Aspect | Image | Container |
|--------|-------|-----------|
| **Nature** | Read-only template | Running (or stopped) instance of an image |
| **Mutability** | Immutable once built | Has a writable layer on top of image layers |
| **Lifecycle** | Built once, stored in registry | Created, started, stopped, destroyed |
| **Analogy** | Class definition | Object instance |

An image is built from a Dockerfile and contains all filesystem layers. A container is instantiated from an image with its own process namespace, network interface, and writable filesystem. Multiple containers can run from the same image simultaneously.

---

### Q3. What is a Kubernetes Deployment vs a Pod?

**Level:** Beginner

**Answer:**

- **Pod**: The smallest deployable unit in Kubernetes. Represents one or more tightly coupled containers sharing a network namespace and storage. A Pod is ephemeral — if it dies, it stays dead unless managed by a controller.

- **Deployment**: A higher-level controller that manages ReplicaSets, which in turn manage Pods. A Deployment ensures the desired number of pod replicas are running, handles rolling updates, and enables rollbacks.

```
Deployment → ReplicaSet → Pods
```

You almost never create Pods directly in production. Deployments provide self-healing (restart failed pods), scaling (change `replicas`), and declarative updates (change the image tag).

---

### Q4. What are liveness and readiness probes?

**Level:** Beginner

**Answer:**

| Probe | Purpose | Failure Action | When to Use |
|-------|---------|----------------|-------------|
| **Liveness** | Is the container alive and functioning? | Restart the container | Detect deadlocks, unrecoverable states |
| **Readiness** | Is the container ready to accept traffic? | Remove from Service endpoints | Model still loading, warming up |

For LLM servers:
- **Readiness** probe checks `/health` during model loading. The pod won't receive traffic until the model is loaded.
- **Liveness** probe checks `/health` during inference. If the server deadlocks or crashes internally, Kubernetes restarts it.

```yaml
readinessProbe:
  httpGet: { path: /health, port: 8000 }
  initialDelaySeconds: 60
livenessProbe:
  httpGet: { path: /health, port: 8000 }
  initialDelaySeconds: 120
  failureThreshold: 5
```

---

### Q5. What is serverless deployment?

**Level:** Beginner

**Answer:**

Serverless deployment abstracts infrastructure management. You deploy code or containers without provisioning or managing servers. Key characteristics:

- **Scale to zero**: No cost when there's no traffic.
- **Pay per use**: Billed per request, per second of compute, or per GB-s.
- **Managed infrastructure**: The platform handles patching, scaling, and availability.

For LLM apps, serverless options include Azure Container Apps (scale-to-zero with KEDA), Google Cloud Run (GPU support), Modal (GPU with fast cold starts), and managed APIs (Azure OpenAI, AWS Bedrock). Traditional serverless (Azure Functions, AWS Lambda) lack GPU support, so they're better for orchestration than inference.

---

### Q6. What is the difference between REST and WebSocket for LLM APIs?

**Level:** Beginner

**Answer:**

| Aspect | REST (with SSE) | WebSocket |
|--------|-----------------|-----------|
| **Connection** | Request-response (SSE for streaming) | Persistent bidirectional |
| **Streaming** | Server→Client only (SSE) | Bidirectional |
| **Complexity** | Simple, well-understood | More complex, stateful |
| **Browser support** | Native (EventSource) | Native |
| **Use case** | Standard LLM completions with streaming | Interactive chat, real-time token editing |

REST with SSE is the standard for LLM APIs (OpenAI-compatible). WebSocket is preferred when the client needs to send messages during generation (e.g., stop/regenerate signals, context updates).

---

### Q7. Explain blue-green vs canary deployments.

**Level:** Intermediate

**Answer:**

| Aspect | Blue-Green | Canary |
|--------|-----------|--------|
| **Mechanism** | Two full environments; switch LB | One environment; split traffic weights |
| **Traffic shift** | 0% → 100% (instant switch) | 5% → 25% → 50% → 100% (gradual) |
| **Rollback** | Instant (switch LB back) | Instant (shift weights back) |
| **Resource cost** | 2x during deployment | 1x + canary pods |
| **Risk exposure** | All-or-nothing | Controlled blast radius |

**Blue-green**: Deploy v2 alongside v1, test v2, switch all traffic at once. Best for critical services where instant rollback is needed.

**Canary**: Deploy v2 pods, route 5% of traffic to v2, monitor error rates and latency. If healthy, gradually increase. Best for risk-averse releases where you want to validate with real traffic.

---

### Q8. What is continuous batching in LLM serving?

**Level:** Intermediate

**Answer:**

Traditional (static) batching waits for all sequences in a batch to finish generating before starting a new batch. This means short sequences wait idle for the longest sequence — wasting GPU compute.

**Continuous batching** (iteration-level scheduling) operates at the token level:
1. Generate one token for all sequences in the current batch.
2. If any sequence finishes (reaches EOS or max tokens), immediately replace it with a new request from the queue.
3. Repeat.

This eliminates padding waste and dramatically increases throughput. Both vLLM and TGI implement continuous batching.

```
Static Batch:   [Seq1: 10 tok] [Seq2: 100 tok] → GPU idle for Seq1 after token 10
Continuous:     [Seq1: 10 tok] → replaced with [Seq3] while Seq2 continues
```

---

### Q9. How does vLLM's PagedAttention improve inference?

**Level:** Intermediate

**Answer:**

In standard attention implementations, KV cache is allocated as contiguous blocks per request. This leads to:
- **Internal fragmentation**: Pre-allocated blocks are larger than needed.
- **External fragmentation**: Free memory exists but not in contiguous chunks.

**PagedAttention** borrows virtual memory paging from OS design:
1. KV cache is split into fixed-size blocks (pages).
2. Blocks are allocated on demand, not contiguously.
3. A block table maps logical positions to physical blocks.
4. Blocks can be shared across sequences (for parallel sampling or prefix caching).

Results:
- Near-zero KV cache waste (from 60-80% utilization to 95%+).
- Higher effective batch sizes → higher throughput.
- Enables prefix caching (shared system prompts reuse KV blocks).

---

### Q10. What is AWQ quantization and why is it useful?

**Level:** Intermediate

**Answer:**

**AWQ (Activation-Aware Weight Quantization)** is a post-training quantization method that reduces model weights from FP16 to INT4 while preserving accuracy better than naive quantization.

Key insight: Not all weight channels are equally important. AWQ identifies "salient" weight channels by observing activation distributions — channels with large activations are quantized less aggressively.

Benefits:
- **2-4x memory reduction** (70B model: 140GB → 35GB in INT4).
- **Minimal accuracy loss** (~1% perplexity increase on benchmarks).
- **Fast inference** (INT4 dequantization is fast on modern GPUs with AWQ kernels).

Compared to GPTQ, AWQ typically has better generalization across tasks because it uses activation-aware calibration rather than layer-by-layer reconstruction.

---

### Q11. How would you design auto-scaling for an LLM deployment?

**Level:** Intermediate

**Answer:**

LLM deployments need scaling based on GPU-specific signals, not just CPU:

**Scale-up signals:**
- GPU utilization > 80% sustained for 2 minutes
- Pending request queue depth > threshold (e.g., 20)
- Time-to-first-token (TTFT) > 2 seconds

**Scale-down signals:**
- GPU utilization < 30% for 10 minutes
- Queue depth < 5
- TTFT < 500 ms

**Implementation:**
```yaml
# KEDA ScaledObject for custom metrics
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: llm-scaler
spec:
  scaleTargetRef:
    name: llm-server
  minReplicaCount: 1
  maxReplicaCount: 10
  cooldownPeriod: 300
  triggers:
    - type: prometheus
      metadata:
        serverAddress: http://prometheus:9090
        metricName: vllm_pending_requests
        query: sum(vllm_pending_requests)
        threshold: "20"
```

**Key considerations:**
- Stabilization windows prevent thrashing (scale-down delay of 5+ minutes).
- GPU cold start takes 1-5 minutes (model loading), so proactive scaling is better than reactive.
- Consider scale-to-zero for off-peak hours with warm-up on first request.

---

### Q12. Explain the role of Azure API Management in LLM architecture.

**Level:** Intermediate

**Answer:**

APIM acts as a centralized API gateway between clients and one or more LLM backend services. Its responsibilities:

| Concern | APIM Feature |
|---------|-------------|
| **Authentication** | API key validation, OAuth2, managed identity |
| **Rate limiting** | Per-subscription, per-IP throttling |
| **Caching** | Response caching for repeated prompts |
| **Routing** | URL-based or header-based routing to different model backends |
| **Observability** | Request logging, Application Insights integration |
| **Transformation** | Request/response header/body manipulation |
| **Versioning** | API versioning via path or header |

For LLM workloads, APIM can:
- Route requests to different model versions (canary via headers).
- Cache responses for deterministic prompts (temperature=0).
- Enforce token budgets per API key.
- Aggregate multiple model endpoints behind a single URL.

---

### Q13. What is tensor parallelism and when is it needed?

**Level:** Intermediate

**Answer:**

**Tensor parallelism** splits individual model layers across multiple GPUs. Each GPU holds a shard of the weight matrix for every layer. During forward pass:
1. Each GPU computes its shard of the attention/FFN output.
2. Results are aggregated via AllReduce.
3. The next layer's computation proceeds.

**When needed:**
- Model is too large for a single GPU (e.g., 70B model needs ~140GB in FP16, but A100 has 80GB).
- Even with INT4 quantization, a very large model (e.g., 405B) requires multiple GPUs.

**Trade-offs:**
- Requires fast interconnect (NVLink, InfiniBand) — PCIe is too slow.
- Adds communication overhead (AllReduce at each layer).
- Inference latency increases with more GPUs, but throughput per GPU stays high.

```
vLLM: --tensor-parallel-size 4
# Splits Llama-3-70B across 4 A100s
```

---

### Q14. How do you handle long-running streaming responses in production?

**Level:** Intermediate

**Answer:**

LLM streaming responses can last seconds to minutes. Production handling requires:

1. **Server-Sent Events (SSE)**: Send tokens as `data:` events. The client reads incrementally. Works through most proxies and CDNs.

2. **Timeout configuration**: Increase upstream timeout (e.g., Nginx `proxy_read_timeout 300s`). Use keep-alive headers.

3. **Connection draining**: During deployments, stop accepting new requests but let existing streams complete. Kubernetes `terminationGracePeriodSeconds` should be long enough.

4. **Backpressure handling**: If the client is slow, buffer tokens or apply flow control to avoid OOM on the server.

5. **Observability**: Track tokens-per-second, time-to-first-token (TTFT), and inter-token latency (ITL) per request.

```python
# Graceful shutdown with stream completion
import signal

shutdown_requested = False

def handle_shutdown(signum, frame):
    global shutdown_requested
    shutdown_requested = True

signal.signal(signal.SIGTERM, handle_shutdown)

async def generate():
    for token in model.stream(prompt):
        if shutdown_requested:
            break
        yield f"data: {json.dumps({'token': token})}\n\n"
    yield "data: [DONE]\n\n"
```

---

### Q15. Design a deployment architecture for a multi-model LLM platform.

**Level:** Advanced

**Answer:**

```
                         ┌──────────────────────────────────────┐
                         │          Azure Front Door / CDN      │
                         └──────────────────┬───────────────────┘
                                            │
                         ┌──────────────────▼───────────────────┐
                         │       Azure API Management           │
                         │  ┌──────┐ ┌────────┐ ┌───────────┐  │
                         │  │ Auth │ │ Routing│ │Rate Limit │  │
                         │  └──┬───┘ └───┬────┘ └─────┬─────┘  │
                         └─────┼─────────┼───────────┼──────────┘
                               │         │           │
                    ┌──────────┼─────────┼───────────┼──────────┐
                    │          ▼         ▼           ▼          │
                    │  Azure Container Apps Environment          │
                    │                                           │
                    │  ┌─────────┐ ┌─────────┐ ┌─────────────┐ │
                    │  │Chat LLM│ │Code LLM │ │ Embedding   │ │
                    │  │Llama-70B│ │DeepSeek │ │ all-MiniLM  │ │
                    │  │4×A100  │ │34B 2×A100│ │ 1×T4       │ │
                    │  └─────────┘ └─────────┘ └─────────────┘ │
                    │                                           │
                    │  ┌─────────────────────────────────────┐  │
                    │  │ Shared Services (Dapr sidecars)     │  │
                    │  │ Pub/Sub · State · Secrets           │  │
                    │  └─────────────────────────────────────┘  │
                    └───────────────────────────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────┐
                    │  Azure Services       │                   │
                    │  ┌──────────┐  ┌──────▼──────┐  ┌──────┐│
                    │  │Key Vault │  │Azure Monitor│  │Redis ││
                    │  │(secrets) │  │(logs/metrics)│  │(cache)│
                    │  └──────────┘  └─────────────┘  └──────┘│
                    └──────────────────────────────────────────┘
```

**Key design decisions:**
- **APIM**: Single entry point, auth, per-model routing (`/v1/chat` → Chat LLM, `/v1/embeddings` → Embedding model).
- **Separate container apps per model**: Independent scaling. Chat model gets 10 replicas at peak; embedding model stays at 1.
- **Dapr**: Service invocation, pub/sub for async jobs, state management for conversation history.
- **Managed identity**: No secrets in code. Container Apps authenticate to Key Vault, ACR, and Azure Monitor via identity.
- **Auto-scaling**: KEDA-based on GPU utilization and queue depth per model.

---

### Q16. How would you implement canary deployments for a model update?

**Level:** Advanced

**Answer:**

**Scenario**: Deploy Llama-3-8B v2 (fine-tuned) alongside v1 (current) with gradual traffic shift.

**Step 1: Deploy canary revision**
```bash
az containerapp update \
    --name llm-server \
    --resource-group rg-llm-prod \
    --image myregistry.azurecr.io/llm-server:v2.0.0 \
    --revision-suffix v2
```

**Step 2: Split traffic**
```bash
az containerapp ingress traffic set \
    --name llm-server \
    --resource-group rg-llm-prod \
    --revision-weight llm-server--v1=95 llm-server--v2=5
```

**Step 3: Monitor for 30 minutes**
- Track per-revision error rates, latency P95/P99, and token throughput.
- Automated rollback if error rate > 1% or P99 latency > 2x baseline.

**Step 4: Gradually increase canary weight**
```
T+0:   95/5    → Monitor
T+30m: 80/20   → Monitor
T+60m: 50/50   → Monitor
T+90m: 0/100   → Full promotion
```

**Step 5: Decommission old revision**
```bash
az containerapp revision deactivate \
    --name llm-server \
    --resource-group rg-llm-prod \
    --revision llm-server--v1
```

**Istio alternative** (for Kubernetes): Use VirtualService with weight-based routing and DestinationRule subsets.

---

### Q17. Explain cost optimization strategies for GPU-based LLM serving.

**Level:** Advanced

**Answer:**

| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| **Quantization (INT4)** | 2-4x fewer GPUs needed | ~1% quality loss |
| **Spot/preemptible instances** | 60-80% cheaper | Can be evicted with 30s notice |
| **Scale to zero** | 100% savings during idle | Cold start latency (1-5 min) |
| **Right-sizing** | Avoid over-provisioning | Requires load testing |
| **Batch processing** | Max GPU utilization for offline jobs | Higher latency per request |
| **Shared model server** | Multiple models on same GPU (with MIG or time-sharing) | Resource contention |
| **Off-peak scheduling** | Scale down nights/weekends | Delayed response for off-peak users |
| **Caching (APIM/Redis)** | Avoid repeated inference | Cache invalidation complexity |

**Example: Azure cost comparison for 70B model**

| Config | Monthly Cost | Notes |
|--------|-------------|-------|
| 4×A100 dedicated (ND96amsr) | ~$27,000 | Always-on, full control |
| 4×A100 spot | ~$9,000 | Risk of eviction |
| INT4 on 1×A100 dedicated | ~$7,000 | Lower hardware, minimal quality loss |
| Scale-to-zero Container Apps | ~$2,000-10,000 | Pay only when serving |
| Azure OpenAI (GPT-4o) | Variable | Per-token, no ops overhead |

---

### Q18. How do you achieve zero-downtime deployments for LLM services?

**Level:** Advanced

**Answer:**

Zero-downtime deployment requires the system to remain fully available during updates:

**1. Rolling updates (Kubernetes)**
```yaml
strategy:
  rollingUpdate:
    maxSurge: 1        # Add 1 new pod before removing old
    maxUnavailable: 0  # Never reduce below desired count
```

**2. Readiness gates**: New pods don't receive traffic until readiness probe passes (model loaded).

**3. Connection draining**: Old pods stop accepting new requests but complete in-flight streams. Set `terminationGracePeriodSeconds` to cover max stream duration.

**4. Blue-green**: Switch load balancer to new environment after validation. Instant rollback.

**5. Health check validation**: Deployment pipeline verifies new pods are healthy before proceeding.

**6. Database migrations**: Use backward-compatible schema changes (expand-contract pattern) so old and new code can coexist.

```yaml
# Kubernetes lifecycle hooks for graceful shutdown
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 15"]  # Drain time
terminationGracePeriodSeconds: 300  # Allow long streams to complete
```

---

### Q19. Design a CI/CD pipeline for LLM container deployment on Azure.

**Level:** Advanced

**Answer:**

```
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐    ┌────────┐
│  Commit  │───▶│  Build   │───▶│  Test   │───▶│  Stage   │───▶│ Prod   │
│ (GitHub) │    │(ACR Build)│    │(Unit+  │    │(Deploy + │    │(Canary │
│          │    │          │    │Perf)   │    │Smoke)    │    │→ Full) │
└─────────┘    └──────────┘    └─────────┘    └──────────┘    └────────┘
```

```yaml
# .github/workflows/llm-deploy.yml
name: LLM Deploy Pipeline
on:
  push:
    branches: [main]
    paths: ['src/**', 'Dockerfile']

env:
  ACR: myregistry
  RG: rg-llm-prod

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v1
        with: { creds: ${{ secrets.AZURE_CREDENTIALS }} }
      - name: Build & Push
        run: |
          az acr build --registry ${{ env.ACR }} \
            --image llm-server:${{ github.sha }} .
      - name: Trivy Scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: '${{ env.ACR }}.azurecr.io/llm-server:${{ github.sha }}'

  test:
    needs: build
    runs-on: gpu-runner  # Self-hosted with GPU
    steps:
      - name: Start local server
        run: |
          docker run -d --gpus all -p 8000:8000 \
            ${{ env.ACR }}.azurecr.io/llm-server:${{ github.sha }}
      - name: Wait for ready
        run: |
          for i in $(seq 1 60); do
            curl -sf http://localhost:8000/health && break
            sleep 5
          done
      - name: Run integration tests
        run: pytest tests/integration/ -v
      - name: Performance benchmark
        run: python benchmarks/throughput_test.py --requests 100 --concurrency 10

  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: azure/login@v1
        with: { creds: ${{ secrets.AZURE_CREDENTIALS }} }
      - name: Deploy to staging
        run: |
          az containerapp update --name llm-server --resource-group ${{ env.RG }} \
            --image ${{ env.ACR }}.azurecr.io/llm-server:${{ github.sha }}
      - name: Smoke test
        run: |
          ENDPOINT=$(az containerapp show --name llm-server --resource-group ${{ env.RG }} \
            --query "properties.configuration.ingress.fqdn" -o tsv)
          curl -sf "https://${ENDPOINT}/health"

  deploy-prod:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      - uses: azure/login@v1
        with: { creds: ${{ secrets.AZURE_CREDENTIALS }} }
      - name: Canary deploy (10%)
        run: |
          az containerapp update --name llm-server --resource-group ${{ env.RG }} \
            --image ${{ env.ACR }}.azurecr.io/llm-server:${{ github.sha }} \
            --revision-suffix canary-${{ github.sha }}
      - name: Monitor canary (10 min)
        run: |
          sleep 600
          # Check error rate from Azure Monitor
          ERROR_RATE=$(az monitor metrics list --resource ... --query "...")
          if [ "$ERROR_RATE" -gt 1 ]; then
            echo "Canary failed, rolling back"
            exit 1
          fi
      - name: Promote to 100%
        run: |
          az containerapp ingress traffic set --name llm-server --resource-group ${{ env.RG }} \
            --revision-weight llm-server--canary-${{ github.sha }}=100
```

---

### Q20. How would you troubleshoot a production LLM deployment with high latency?

**Level:** Advanced

**Answer:**

**Diagnostic framework:**

```
High Latency
│
├─ Time-to-First-Token (TTFT) high?
│  ├─ YES → Prefill bottleneck
│  │  ├─ Long prompts? → Check prompt length distribution
│  │  ├─ GPU busy? → Check concurrent request count
│  │  └─ Model loading? → Check readiness probe
│  └─ NO → Decoding bottleneck
│     ├─ KV cache full? → Check gpu-memory-utilization
│     ├─ Batch too large? → Reduce max-num-seqs
│     └─ Slow tokens? → Check inter-token latency
│
├─ Intermittent spikes?
│  ├─ Garbage collection? → Check Python GC logs
│  ├─ Preemptible eviction? → Check spot eviction logs
│  └─ Scaling events? → Check HPA/KEDA logs
│
└─ Consistent slowness?
   ├─ Wrong GPU? → Verify nvidia-smi shows A100, not T4
   ├─ CPU bottleneck? → Check tokenizer/detokenizer CPU usage
   ├─ Network? → Check intra-node latency (NVLink status)
   └─ Configuration? → Review vLLM/TGI launch flags
```

**Troubleshooting commands:**

```bash
# GPU utilization
nvidia-smi -l 1

# vLLM internal metrics
curl http://localhost:8000/metrics | grep vllm_

# Check pending requests
curl http://localhost:8000/metrics | grep vllm_pending_requests

# Memory breakdown
curl http://localhost:8000/metrics | grep vllm_gpu_cache

# Container resource usage
kubectl top pods -l app=llm-server

# Application logs
kubectl logs -l app=llm-server --tail=100 -f | grep -E "(latency|timeout|error)"

# Network latency between pods
kubectl exec -it llm-server-0 -- ping llm-server-1
```

**Common fixes:**
- High TTFT: Enable prefix caching, reduce prompt length, increase `max-num-batched-tokens`.
- High ITL: Reduce batch size, increase GPU memory for KV cache, upgrade to faster GPU.
- OOM: Quantize model (AWQ INT4), reduce `max-model-len`, reduce batch size.
- Timeout: Increase proxy timeout, check for deadlocked threads, verify model isn't swapping to CPU.

---

## Senior Deep Dive: Deploying GenAI on Azure (Azure AI Foundry, Azure OpenAI, Azure ML, AKS)

> *For Azure-centric roles. Interviewers want to know you can pick the right Azure surface for a workload, reason about quota/cost/latency, and run it securely in an enterprise tenant.*

### SQ1: What is Azure AI Foundry and how does it relate to Azure OpenAI and Azure ML?

**Answer:** **Azure AI Foundry** (formerly Azure AI Studio) is the unified platform/SDK for building, evaluating, and deploying generative-AI applications on Azure. Mental model of the layers:

- **Model catalog** — Azure OpenAI models (GPT-4o, o-series), plus open models (Llama, Mistral, Phi) and partner models, deployable as **serverless APIs (MaaS, pay-per-token)** or to **managed compute**.
- **Azure OpenAI Service** — the managed endpoint for OpenAI models in *your* Azure tenant (private networking, RBAC, regional control, content filtering). This is what enterprises use instead of api.openai.com for data-residency and compliance.
- **Foundry capabilities** — prompt flow (orchestration), evaluations, tracing, content safety, agent service, and fine-tuning, all wired together.
- **Azure Machine Learning (Azure ML)** — the broader MLOps platform (custom training, pipelines, model registry, managed online/batch endpoints) for *any* model, classic ML included. Foundry builds on and integrates with it.

Senior framing: **Foundry = GenAI app lifecycle; Azure OpenAI = the hosted frontier models; Azure ML = general MLOps + custom/open models.** They compose; you pick the entry point by workload.

### SQ2: Serverless API (MaaS) vs Managed Online Endpoint vs self-hosted on AKS — how do you choose?

**Answer:**

| Option | What it is | Choose when |
|--------|-----------|-------------|
| **Serverless API / PTU** | Pay-per-token (PAYG) or **Provisioned Throughput Units** for reserved capacity | Fastest to ship, no infra; PTU for predictable high-volume, latency SLAs, and quota guarantees |
| **Managed Online Endpoint (Azure ML)** | Azure-managed real-time endpoint backing your model/container with autoscale | You bring a fine-tuned/open/custom model but don't want to operate K8s |
| **Self-hosted on AKS** (vLLM/Triton) | Your own GPU cluster | Max control over batching/quantization, data never leaves your cluster, multi-model, cost optimization at scale |

Key cost lever to mention: **PTU (Provisioned Throughput)** trades a fixed monthly reservation for guaranteed throughput and stable latency — you size PTUs from peak tokens/min. Below the break-even volume, PAYG is cheaper; above it, PTU wins and protects you from throttling (429s).

### SQ3: How do you handle Azure OpenAI quota, throttling, and high availability?

**Answer:**
- **Quota is per-region, per-model, measured in TPM (tokens/min) and RPM (requests/min).** You design within it, not around 429s after the fact.
- **Handle 429s** with exponential backoff + jitter and respect `Retry-After`; the SDK does some of this but you own the policy.
- **Scale/HA pattern:** put **Azure API Management (APIM)** or a gateway in front of *multiple* Azure OpenAI deployments across regions and **load-balance / failover** (the "AOAI smart load balancer" pattern). Spreads load across quota pools and survives a regional incident.
- **PTU + spillover:** reserved PTU deployment for baseline, PAYG deployment for burst spillover.
- **Caching:** semantic/exact cache (e.g. Azure Cache for Redis) for repeated prompts to cut tokens and latency.
- **Batch API** for non-real-time bulk jobs at lower cost.

### SQ4: How do you secure an enterprise Azure OpenAI / Foundry deployment?

**Answer (the controls an enterprise interviewer expects):**
- **Identity:** Microsoft Entra ID + **Managed Identity** for service-to-service auth — *no API keys in code/config*; RBAC scoped to least privilege.
- **Network:** **Private Endpoints / VNet integration**, disable public network access, egress control; data stays on the Microsoft backbone. Use the **EU Data Boundary** / region pinning for residency.
- **Secrets:** Azure Key Vault for any remaining secrets; Key Vault references in App Config.
- **Data protection:** Azure OpenAI does **not** use your prompts/completions to train models and isolates data per tenant; document this for compliance reviews. Customer-managed keys (CMK) for at-rest encryption.
- **Safety:** Azure AI Content Safety filters + prompt shields + groundedness checks at the gateway.
- **Auditability:** Azure Monitor / Log Analytics + Microsoft Purview for full request logging and data lineage (also feeds the model-risk audit trail).

### SQ5: Describe an end-to-end MLOps/LLMOps pipeline on Azure.

**Answer:**
1. **Source & data:** Git (Azure Repos/GitHub) for code/prompts; Azure Data Lake / Blob + Purview for data; feature store if classic ML.
2. **Train/build:** Azure ML pipelines or Foundry fine-tuning; track experiments and lineage with **MLflow** (native in Azure ML).
3. **Register:** versioned model + prompt + eval artifacts in the **Azure ML model registry** with model cards.
4. **Evaluate (the LLM gate):** **Azure AI Foundry evaluations** — groundedness, relevance, coherence, safety — run in CI; block promotion on regression. For classic ML, accuracy/AUC + Responsible AI scorecard.
5. **CI/CD:** Azure DevOps Pipelines or GitHub Actions → deploy to staging endpoint → automated eval → **canary/blue-green** promotion to production (managed endpoint or PTU deployment).
6. **Monitor:** Azure Monitor + Application Insights for latency/cost/tokens; data & model drift monitors in Azure ML; online groundedness/safety sampling; alerting → retrain/rollback loop.
7. **Govern:** human-in-the-loop for high-risk paths, audit logs, periodic revalidation.

The thing that signals seniority here: the **evaluation gate and rollback loop** are first-class, not bolted on — promotion is automated *and* guarded.

---

*End of Module 12 Interview Questions*
