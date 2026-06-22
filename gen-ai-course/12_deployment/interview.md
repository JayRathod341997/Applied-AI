# Module 12 — Deployment: Interview Questions

Comprehensive interview preparation covering GenAI deployment from beginner to senior/staff-level questions.

---

## Section 1: Deployment Overview (Beginner)

### Q1: What are the different deployment options for GenAI models?

**Answer:**

| Option | Description | Examples | Best For |
|---|---|---|---|
| **Cloud APIs** | Call hosted model via HTTPS | OpenAI, Anthropic, Gemini | Fast prototyping, variable traffic |
| **Managed Platforms** | Bring model, cloud runs infra | SageMaker, Azure ML, Vertex AI | Custom models, moderate control |
| **Self-hosted** | Run model on your own GPUs | vLLM on own cluster | High volume, data sovereignty |
| **Serverless** | Scale-to-zero containers/functions | Modal, Lambda + Bedrock, Cloud Run | Spiky or low-average traffic |
| **Edge** | Model runs on device | llama.cpp, MLC LLM | Offline, privacy-critical |
| **Hybrid** | Combine cloud + on-prem | Route by PII / complexity | Best-of-both |

---

### Q2: What factors determine which deployment option to choose?

**Answer:**

1. **Latency** — Interactive apps need <2s; batch workflows can tolerate minutes.
2. **Data privacy** — Regulated data (HIPAA, GDPR) may require on-premise or private cloud deployment.
3. **Cost** — Cloud API pricing is per-token (scales with usage); self-hosted is fixed infrastructure cost.
4. **Traffic pattern** — Steady high traffic → self-hosted is cheaper. Spiky traffic → serverless or cloud API.
5. **Model requirements** — Need a fine-tuned proprietary model → managed platform or self-hosted.
6. **Team capability** — Small team → cloud API or managed platform. MLOps team → self-hosted.
7. **Scalability** — SLA for burst traffic, auto-scaling requirements.
8. **Vendor lock-in risk** — Cloud API couples you to one vendor; self-hosted gives full portability.

---

### Q3: What are the main deployment patterns for GenAI applications?

**Answer:**

- **API-First:** Expose inference as a REST/gRPC endpoint. Most common pattern.
- **Streaming:** Server-Sent Events (SSE) or WebSocket to stream tokens — improves perceived latency.
- **Batch Processing:** Process large document sets offline with concurrent workers.
- **Agentic:** Model takes multi-step actions autonomously, calling tools between steps.
- **Embedded:** Model integrated directly as a library (edge devices, desktop apps).
- **Event-driven:** Queue-based async processing (SQS → Lambda → Bedrock).

---

## Section 2: Deployment Techniques (Intermediate)

### Q4: Explain serverless deployment for GenAI and its trade-offs.

**Answer:**

Serverless functions spin up on demand and shut down when idle — you pay only for invocation time.

**For GenAI specifically:**
- **Cold start problem:** Large models take 15–60 seconds to load on first request. Mitigations: provisioned concurrency (keep N instances warm), smaller quantized models, pre-loaded container images.
- **Memory limits:** AWS Lambda max 10 GB RAM, no native GPU. Suitable only for small models or API proxies to Bedrock/OpenAI.
- **GPU serverless:** Modal, Replicate, and Google Cloud Run (GPU) support GPU containers with scale-to-zero.
- **Cost:** For low-traffic internal tools, serverless can be 10× cheaper than always-on GPU instances.

**Trade-off summary:**
```
Serverless:   Low cost when idle | Cold starts hurt UX | Limited model size
Always-on:    Consistent latency | Cost $ even when idle | No size limits
```

---

### Q5: How does container-based deployment work for GenAI? What does a production Dockerfile look like?

**Answer:**

Containers package the application, dependencies, Python runtime, and CUDA libraries into a portable unit that runs identically everywhere.

Key considerations for GenAI containers:
1. **Base image:** Use NVIDIA CUDA base (`nvcr.io/nvidia/cuda:12.1.1-cudnn8`) for GPU inference.
2. **Model weights:** Do NOT bake into the image (too large, hard to update). Load from object storage at startup.
3. **Multi-stage builds:** Separate build and runtime stages to keep the final image small.
4. **Non-root user:** Run as a non-root user for security.

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/build/packages -r requirements.txt

FROM python:3.11-slim AS production
RUN useradd -m -u 1001 appuser
WORKDIR /app
COPY --from=builder /build/packages /usr/local/lib/python3.11/site-packages
COPY --chown=appuser:appuser app/ ./app/
USER appuser
EXPOSE 8000
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

---

### Q6: Explain Kubernetes deployment for GenAI. What are the critical K8s resources?

**Answer:**

Kubernetes orchestrates containers across a cluster, providing auto-healing, auto-scaling, and rolling deployments.

**Critical resources for GenAI:**

1. **Deployment** — Declares desired pod count and container spec. Sets `rollingUpdate` strategy.
2. **Service** — Stable DNS and IP for a set of pods (load balances traffic).
3. **Ingress** — Routes external HTTP/HTTPS traffic to services. Add TLS, rate limiting here.
4. **HPA (HorizontalPodAutoscaler)** — Scales pod count based on CPU, memory, or custom metrics (e.g., P95 latency).
5. **PersistentVolumeClaim** — For model weight caching across pod restarts.
6. **Secret** — Store API keys; inject as env vars (never hardcode).

**GPU-specific additions:**
- NVIDIA device plugin (`nvidia.com/gpu: 1` in resource limits)
- Node selectors and tolerations to schedule GPU pods on GPU nodes
- KEDA for event-driven scaling (scale to zero when queue is empty)

**HPA example:**
```yaml
metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

### Q7: What is model quantization and why is it important for deployment?

**Answer:**

Quantization reduces model weight precision from 32-bit float (FP32) to lower precision (INT8, INT4), shrinking memory footprint and often improving throughput with acceptable quality loss.

| Method | Size vs FP32 | Quality Impact | Use Case |
|---|---|---|---|
| FP16/BF16 | 2× smaller | Negligible | GPU inference (standard) |
| INT8 | 4× smaller | Slight | Production GPU/CPU |
| INT4 (GGUF Q4_K_M) | 8× smaller | Moderate | Edge, consumer GPUs |
| INT4 (NF4 + double quant) | 8× smaller | Low | Fine-tuning (QLoRA) |

**Practical impact:** A 7B parameter model:
- FP32: ~28 GB → requires A100 80GB
- FP16: ~14 GB → fits on A100 40GB
- INT4: ~4 GB → fits on RTX 3060 12GB or Apple M2 Pro

**Tools:** `bitsandbytes` (PyTorch), `llama.cpp` (GGUF), `AutoGPTQ`, `AWQ`

---

### Q8: What are the three main deployment strategies and when do you use each?

**Answer:**

**Blue-Green:**
- Maintain two identical environments. Deploy new version to "green" while "blue" serves traffic. Switch instantly.
- **Use when:** Zero-downtime required, need instant rollback capability, stateless applications.
- **Risk:** Doubles infrastructure cost during deployment.

**Canary:**
- Gradually shift traffic: 5% → 20% → 50% → 100%. Monitor error rates at each step.
- **Use when:** High-risk changes, need real traffic validation, want gradual risk exposure.
- **Risk:** Both versions run simultaneously; requires version-aware monitoring.

**Rolling:**
- Replace pods one by one (Kubernetes default). Old and new versions coexist briefly.
- **Use when:** Standard updates, backwards-compatible changes.
- **Risk:** If new version has a bug, some requests get bad responses before rollback.

**For GenAI specifically:** Canary is often preferred because LLM quality issues (hallucinations, tone drift) are better caught on real user traffic than in staging tests.

---

## Section 3: Platform Implementation (Intermediate–Advanced)

### Q9: How do you deploy a GenAI application to Azure? Walk through the options.

**Answer:**

**Azure offers four main paths:**

1. **Azure OpenAI Service** — Managed GPT-4o, DALL-E, embeddings. Best for: OpenAI models with Azure compliance (data residency, private endpoints, RBAC). Auth via Managed Identity — no API keys in code.

2. **Azure ML Online Endpoints** — Deploy your own model (HuggingFace, fine-tuned). Supports traffic splitting for A/B testing. Auto-scales on request rate. `score.py` defines `init()` (load model) and `run()` (inference).

3. **Azure Container Apps** — Serverless containers with GPU support. Scale-to-zero. Good for variable traffic. Deploy via `az containerapp create`.

4. **AKS (Azure Kubernetes Service)** — Full Kubernetes with GPU node pools. KEDA for event-driven autoscaling. Best for enterprise, high-traffic, full control.

**Key Azure security pattern:** Always use **Managed Identity** + **Azure Key Vault** — never hardcode API keys.

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

client = SecretClient(
    vault_url="https://kv-genai.vault.azure.net",
    credential=DefaultAzureCredential(),   # uses Managed Identity in Azure
)
api_key = client.get_secret("anthropic-api-key").value
```

---

### Q10: How do you deploy to AWS? Compare Bedrock vs SageMaker.

**Answer:**

| Dimension | Amazon Bedrock | SageMaker Endpoints |
|---|---|---|
| Model selection | Foundation models (Claude, Llama, Mistral, Titan) | Any custom model |
| Infrastructure | Zero (fully managed) | Managed EC2/GPU instances |
| Latency | 200–2000ms | 100–500ms (self-hosted model) |
| Cost model | Per-token | Per-hour (instance) |
| Fine-tuning | Limited (Bedrock fine-tuning) | Full control |
| Data privacy | AWS-managed, stays in region | Your EC2, VPC |

**Choose Bedrock when:** You want zero infra, foundation models are sufficient, variable traffic.
**Choose SageMaker when:** Custom/fine-tuned model, predictable high traffic, need lower latency.

**SageMaker auto-scaling:**
```python
client.put_scaling_policy(
    PolicyType="TargetTrackingScaling",
    TargetTrackingScalingPolicyConfiguration={
        "TargetValue": 70.0,
        "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance",
    },
)
```

---

### Q11: What is the full deployment process from code to production?

**Answer:**

```
1. BUILD
   ├── Package application as Docker image
   ├── Run unit & integration tests
   └── Push image to registry (ECR / ACR / GCR)

2. STAGING DEPLOY
   ├── Deploy to staging environment (identical to prod)
   ├── Run smoke tests (basic functionality)
   └── Run load tests (latency, throughput, error rate)

3. REVIEW
   ├── QA sign-off on staging
   ├── Security scan (image vulnerability scan, SAST)
   └── Change management approval (for prod)

4. PRODUCTION DEPLOY (canary or blue-green)
   ├── Deploy new version at 5% traffic
   ├── Monitor for 30 minutes (error rate, latency)
   ├── Increment: 5% → 20% → 50% → 100%
   └── Or: rollback if anomaly detected

5. POST-DEPLOY MONITORING
   ├── Watch P50/P95/P99 latency
   ├── Error rate dashboard
   ├── Token usage and cost trending
   └── LLM output quality metrics (if automated eval)
```

**Automated CI/CD:** GitHub Actions / GitLab CI pipeline triggers build → test → staging → smoke test → production (with approval gate).

---

## Section 4: Production Operations (Advanced)

### Q12: How do you handle deployment failures in production?

**Answer:**

**Immediate response (first 5 minutes):**
1. **Auto-rollback** — If error rate > threshold, CI/CD automatically rolls back (Kubernetes: `kubectl rollout undo`).
2. **Circuit breaker** — If downstream LLM API is failing, stop sending requests (use `pybreaker` or Resilience4j).
3. **Alert** — PagerDuty/Opsgenie notifies on-call engineer.

**Investigation:**
4. **Distributed traces** (Jaeger/X-Ray) — identify which service failed.
5. **Logs** (structured JSON to ELK/CloudWatch) — find the error pattern.
6. **Metrics** (Prometheus/CloudWatch) — see when it started, request volume affected.

**Resolution:**
7. **Hotfix** — Fix the root cause, go through fast-track deploy pipeline.
8. **Post-mortem** — Document timeline, root cause, prevention measures.

**Prevention patterns:**
- Health checks (liveness + readiness probes) prevent bad pods from receiving traffic.
- Staging environment parity — prod failures should be caught in staging first.
- Feature flags — roll out risky features gradually without a full deploy.

---

### Q13: How do you optimize latency for an LLM API in production?

**Answer:**

**Latency breakdown:**
```
Network (DNS + TLS):   ~20ms
Auth middleware:       ~5ms
Prompt processing:     ~50ms (tokenization, context building)
LLM inference:         ~200–2000ms (the bottleneck)
Response serialization:~5ms
```

**Optimization strategies, ordered by impact:**

1. **Streaming** — Start sending tokens to user immediately. Time-to-first-token feels fast even if total latency is high.
2. **Smaller model** — Haiku/Phi-3 vs Sonnet/GPT-4o: 3–5× faster at the cost of quality.
3. **Reduce output tokens** — Constrain `max_tokens` tightly. Shorter prompts generate faster.
4. **Semantic caching** — Cache responses for similar queries. Cache hit = ~1ms instead of 500ms+.
5. **vLLM with PagedAttention** — 5–10× throughput improvement over naïve HuggingFace serving.
6. **Quantization** — INT4 models are faster on GPU due to reduced memory bandwidth.
7. **Speculative decoding** — Draft model generates candidates, target model verifies: 2–3× throughput.
8. **Regional deployment** — Deploy close to users (EU users → EU region).
9. **Connection pooling** — Reuse HTTP connections to LLM API rather than creating new ones.
10. **Prompt caching** — Anthropic/Azure cache common prefixes: 90% cost reduction, ~5× faster for cached portion.

---

### Q14: How do you implement semantic caching for a GenAI application?

**Answer:**

Semantic caching returns cached responses for semantically similar (not just identical) prompts, using embedding similarity.

```
Query ──► Embed query ──► Vector similarity search in cache
                                   │
                    Hit (similarity > 0.92)? ──YES──► Return cached response (~1ms)
                                   │
                                  NO
                                   │
                                   ▼
                         Call LLM API (~500ms)
                                   │
                                   ▼
                    Store embedding + response in cache
                                   │
                                   ▼
                             Return response
```

**Implementation:** Use `sentence-transformers` for embedding + Redis (with RediSearch vector module) or pgvector as the cache store.

**Threshold tuning:** Similarity threshold of 0.90–0.95 works for most cases. Lower = more cache hits but risk returning irrelevant cached answers.

**Cache invalidation:** TTL-based (expire entries after 1–24 hours). Domain-specific knowledge may need shorter TTL.

---

### Q15: How do you monitor LLM quality in production beyond just latency and error rate?

**Answer:**

Technical metrics (latency, errors) tell you if the system is up, but not if the LLM is giving good answers.

**LLM-specific quality monitoring:**

1. **Thumbs up/down user feedback** — Simplest signal. Log request → response → user rating.
2. **Automated evaluation with LLM-as-judge** — Send (question, answer, context) to a judge model (GPT-4o) to score quality. Run on a 10% sample.
3. **RAGAS metrics** (for RAG systems):
   - *Faithfulness* — Is the answer grounded in retrieved context?
   - *Answer relevancy* — Does the answer address the question?
   - *Context recall* — Did retrieval find the right documents?
4. **Hallucination detection** — Check if model claims contradict source documents.
5. **Toxicity/safety checks** — Run output through classifiers (Perspective API, Azure Content Safety).
6. **Response length distribution** — Sudden changes in average output length can signal model behavior drift.
7. **Topic drift** — Track whether questions are changing (user behavior shift → model may need updating).

**Alerting:** Alert if LLM-judge quality score drops below baseline by >10% over 1 hour.

---

### Q16: What is MLOps for GenAI and what does a mature MLOps pipeline include?

**Answer:**

MLOps (ML Operations) applies DevOps principles to machine learning: automating the path from data → model → production, with continuous monitoring and retraining.

**Mature GenAI MLOps pipeline:**

```
Data (S3/GCS/Azure Blob)
   │
   ▼
Data Pipeline (validation, formatting, versioning)
   │
   ▼
Fine-tuning Pipeline (SageMaker Pipelines / Azure ML / Kubeflow)
   │
   ▼
Model Registry (versioned artifacts, lineage, metadata)
   │
   ▼
Evaluation Gate (automated: ROUGE, human-eval sample, LLM-judge)
   │           ─── FAIL ──► Block deployment, notify team
   ▼
Deployment (canary → production)
   │
   ▼
Monitoring (quality + performance + cost)
   │
   └── Drift detected ──► Trigger retraining pipeline
```

**Key MLOps components:**
- **Experiment tracking:** MLflow, W&B — log hyperparameters, metrics, model versions.
- **Model registry:** Centralized store for versioned model artifacts with approval gates.
- **Feature/data versioning:** DVC or Delta Lake — reproducibility.
- **Automated retraining:** Schedule or trigger on data drift / quality degradation.
- **A/B testing infrastructure:** Traffic splitting, statistical significance testing.

---

### Q17: How do you optimize deployment cost for GenAI systems?

**Answer:**

**1. Model tiering** — Route queries to the cheapest model that can handle them:
```
Simple tasks (classification, extraction) → Haiku/Phi-3   ($0.25/1M tokens)
Medium tasks (summarization, Q&A)         → Sonnet/GPT-4o  ($3/1M tokens)
Complex tasks (reasoning, coding)         → Opus/GPT-4o max ($15/1M tokens)
```

**2. Semantic caching** — Cache similar query responses. Can cut API costs 30–70%.

**3. Prompt compression** — Remove redundant tokens from prompts. 10–40% reduction.

**4. Prompt caching** — Anthropic and Azure OpenAI cache common prefixes. For RAG system prompts, 90% of input tokens can be cached at 10% of the normal cost.

**5. Batch API** — For non-time-sensitive workloads, use batch APIs (50% cheaper). Anthropic Message Batches API, OpenAI Batch API.

**6. Right-sizing infrastructure** — Don't over-provision GPU instances. Use auto-scaling with scale-to-zero for variable loads.

**7. Spot/Preemptible instances** — Use for fine-tuning (70–90% cheaper). Not suitable for serving (unreliable).

**8. Reserved capacity** — For predictable high usage, commit to Provisioned Throughput (Azure) or Savings Plans (AWS) for 40–60% discount.

**Cost estimation formula:**
```
Monthly cost = requests/day × days × (avg_input_tokens × input_price + avg_output_tokens × output_price) / 1M
```

---

### Q18: How would you design a hybrid deployment that routes between local and cloud models?

**Answer:**

**Design goals:** Use cheaper/private local model for simple/sensitive queries; fall back to cloud for complex ones.

```python
class HybridRouter:
    def __init__(self, local_model, cloud_client, pii_detector):
        self.local = local_model
        self.cloud = cloud_client
        self.pii = pii_detector

    def route(self, prompt: str, context: dict) -> str:
        # Rule 1: PII → always local (data never leaves)
        if self.pii.detect(prompt):
            return self.local.generate(prompt)

        # Rule 2: Very long context → cloud (local model limited to 8K)
        if context.get("token_count", 0) > 6000:
            return self.cloud.generate(prompt)

        # Rule 3: Simple tasks → local (cheap and fast)
        complexity = self.classify_complexity(prompt)
        if complexity == "simple":
            result = self.local.generate(prompt)
            # Quality fallback: if local response is too short, escalate
            if len(result.split()) < 20:
                return self.cloud.generate(prompt)
            return result

        # Default: cloud for complex reasoning
        return self.cloud.generate(prompt)

    def classify_complexity(self, prompt: str) -> str:
        simple_keywords = ["list", "translate", "format", "extract", "summarize briefly"]
        if any(k in prompt.lower() for k in simple_keywords) and len(prompt) < 300:
            return "simple"
        return "complex"
```

**Circuit breaker for cloud fallback:**
- If cloud API is down or rate-limited → fall back to local model automatically.
- Use `pybreaker` or implement manually with exponential backoff.

---

### Q19: What security considerations are critical for production GenAI deployments?

**Answer:**

**1. Secrets management** — Never hardcode API keys. Use AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault. In containers: inject via environment variables from secrets stores, not image layers.

**2. Prompt injection** — Users may try to override system prompts ("Ignore previous instructions..."). Mitigations:
- Input validation to detect injection patterns
- Separate system and user content clearly
- Output filtering before returning to users

**3. Data privacy** — Know where data goes. Cloud API calls send prompts to third-party servers. If handling PII/PHI/PCI: use on-prem or data processing agreements. Implement PII detection and scrubbing before cloud calls.

**4. Output filtering** — Filter model outputs for toxic content, credential leakage, and hallucinated PII before returning to users.

**5. Rate limiting** — Protect against abuse and runaway cost. Limit per IP, per API key, per user. Use API Gateway rate limiting.

**6. Authentication** — All API endpoints require auth (JWT, API key, mTLS for service-to-service). Use managed identities (IAM roles) not static credentials.

**7. Network security** — Private endpoints for cloud services. No public internet access to model inference servers. TLS for all traffic.

**8. Audit logging** — Log all prompts and responses (with PII scrubbed) for compliance, debugging, and abuse detection.

---

### Q20: How would you approach a GPU memory out-of-error in a self-hosted vLLM deployment?

**Answer:**

**Diagnosis steps:**
1. Check `nvidia-smi` — which processes are using GPU memory, how much is used vs. available.
2. Check vLLM startup logs — model loading, KV cache allocation.
3. Check concurrency — too many concurrent long-context requests fills the KV cache.

**Solutions by root cause:**

| Cause | Fix |
|---|---|
| Model too large for GPU | Quantize (INT4 via AWQ/GGUF), or use tensor parallelism across multiple GPUs |
| KV cache exhausted | Reduce `--max-model-len`, lower `--gpu-memory-utilization` (e.g., 0.85), reduce `--max-num-seqs` |
| Memory leak | Pin to specific vLLM version, check for known memory leak issues |
| Context too long | Implement context truncation in the application layer before sending to vLLM |

**Preventive configuration:**
```bash
python -m vllm.entrypoints.openai.api_server \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --gpu-memory-utilization 0.90 \    # reserve 10% for OS + CUDA overhead
  --max-model-len 8192 \             # truncate beyond 8K context
  --max-num-seqs 128 \               # limit concurrent sequences
  --tensor-parallel-size 2           # spread across 2 GPUs
```

---

## Summary: Deployment Maturity Model

```
Level 1 — Ad Hoc
├── Manual deployments
├── Cloud API with hardcoded keys (don't do this)
└── No monitoring

Level 2 — Managed
├── Containerized app on cloud platform
├── Secrets in vault, managed identity
├── Basic CloudWatch/Azure Monitor metrics
└── Manual deployment with rollback plan

Level 3 — Automated
├── CI/CD pipeline: build → test → staging → prod
├── Health checks + readiness probes
├── Auto-scaling (HPA or serverless)
├── Alerting on latency + error rate
└── Canary or blue-green deployments

Level 4 — Production-Grade
├── Semantic caching (30-70% cost reduction)
├── LLM quality monitoring (LLM-as-judge, RAGAS)
├── Distributed tracing (OpenTelemetry)
├── Model tiering (cost optimization)
└── Hybrid routing (privacy + quality)

Level 5 — MLOps Mature
├── Automated fine-tune → evaluate → deploy pipeline
├── Data and model versioning
├── Automated retraining on drift detection
├── A/B testing with statistical significance
└── Cost attribution per team/feature
```

---

## Quick Reference: Key Tools by Category

| Category | Tools |
|---|---|
| **Serving (self-hosted)** | vLLM, Ollama, llama.cpp, TensorRT-LLM |
| **Managed inference** | SageMaker, Azure ML, Vertex AI, Hugging Face Endpoints |
| **Foundation model APIs** | Bedrock, Azure OpenAI, Anthropic API, Vertex AI |
| **Serverless GPU** | Modal, Replicate, Google Cloud Run (GPU) |
| **Containers** | Docker, Kubernetes, ECS, Azure Container Apps |
| **CI/CD** | GitHub Actions, GitLab CI, Azure DevOps, AWS CodePipeline |
| **Monitoring** | Prometheus + Grafana, CloudWatch, Azure Monitor, Datadog |
| **Tracing** | OpenTelemetry, Jaeger, AWS X-Ray, Azure Application Insights |
| **Secrets** | AWS Secrets Manager, Azure Key Vault, HashiCorp Vault |
| **Load testing** | Locust, k6, Artillery |
| **Quantization** | bitsandbytes, llama.cpp, AutoGPTQ, AWQ |
| **MLOps** | SageMaker Pipelines, Azure ML Pipelines, Kubeflow, MLflow |

---

## Senior Deep Dive: GenAI Deployment

> *Interviewers at the senior/staff level want you to reason across the full deployment spectrum — from picking the right Azure or AWS surface, to designing for HA, to owning failure incidents and setting org-wide standards. The questions below span system design, trade-offs, failure modes, and leadership.*

### System Design & Scale

Azure-centric roles in particular probe your ability to pick the right Azure surface for a workload and reason about quota, cost, latency, and enterprise security. The four Q&As below come from that lens; the patterns generalize to AWS and GCP equivalents.

#### Q: What is Azure AI Foundry and how does it relate to Azure OpenAI and Azure ML?

**Answer:** **Azure AI Foundry** (formerly Azure AI Studio) is the unified platform/SDK for building, evaluating, and deploying generative-AI apps on Azure. Layers: a **model catalog** (Azure OpenAI models + open models like Llama/Mistral/Phi, deployable as **serverless APIs / MaaS pay-per-token** or to **managed compute**); **Azure OpenAI Service** (managed OpenAI endpoints in *your* tenant — private networking, RBAC, regional control, content filtering — what enterprises use instead of api.openai.com); **Foundry capabilities** (prompt flow, evaluations, tracing, content safety, agent service, fine-tuning); and **Azure Machine Learning** (broader MLOps for any model, classic ML included — pipelines, registry, managed endpoints). Framing: **Foundry = GenAI app lifecycle; Azure OpenAI = hosted frontier models; Azure ML = general MLOps + custom/open models.**

#### Q: Serverless API (MaaS/PTU) vs Managed Online Endpoint vs self-hosted on AKS — how do you choose?

**Answer:**

| Option | What it is | Choose when |
|--------|-----------|-------------|
| **Serverless API / PTU** | Pay-per-token, or **Provisioned Throughput Units** for reserved capacity | Fastest to ship, no infra; PTU for predictable high volume, latency SLAs, quota guarantees |
| **Managed Online Endpoint (Azure ML)** | Azure-managed real-time endpoint with autoscale | You bring a fine-tuned/open/custom model but don't want to run K8s |
| **Self-hosted on AKS** (vLLM/Triton) | Your own GPU cluster | Max control over batching/quantization, data stays in-cluster, multi-model, cost at scale |

Key lever: **PTU (Provisioned Throughput)** trades a fixed reservation for guaranteed throughput + stable latency (size from peak tokens/min). Below break-even volume PAYG is cheaper; above it PTU wins and protects against 429 throttling.

#### Q: How do you handle Azure OpenAI quota, throttling, and high availability?

**Answer:** Quota is **per-region, per-model, in TPM (tokens/min) and RPM** — design within it. Handle **429s** with exponential backoff + jitter and respect `Retry-After`. HA pattern: put **Azure API Management (APIM)** or a gateway in front of **multiple** Azure OpenAI deployments across regions and **load-balance/failover** (the "AOAI smart load balancer" pattern) — spreads load across quota pools and survives a regional incident. Use **PTU for baseline + PAYG spillover** for burst, **semantic/exact caching** (Azure Cache for Redis) for repeated prompts, and the **Batch API** for non-real-time bulk jobs at lower cost.

#### Q: How do you secure an enterprise Azure OpenAI / Foundry deployment?

**Answer:** **Identity** — Microsoft Entra ID + **Managed Identity** (no API keys in code); least-privilege RBAC. **Network** — **Private Endpoints / VNet integration**, disable public access, egress control; region pinning / **EU Data Boundary** for residency. **Secrets** — Azure Key Vault. **Data protection** — Azure OpenAI does **not** train on your prompts/completions and isolates per tenant (document for compliance); CMK for at-rest encryption. **Safety** — Content Safety filters + prompt shields + groundedness at the gateway. **Auditability** — Azure Monitor / Log Analytics + Microsoft Purview for full request logging and lineage (also feeds the model-risk audit trail).

#### Q: Describe an end-to-end MLOps/LLMOps pipeline on Azure.

**Answer:** (1) **Source/data** — Azure Repos/GitHub for code+prompts; Data Lake/Blob + Purview for data. (2) **Train/build** — Azure ML pipelines or Foundry fine-tuning; track with **MLflow** (native). (3) **Register** — versioned model + prompt + eval artifacts in the **Azure ML registry** with model cards. (4) **Evaluate (the LLM gate)** — **Foundry evaluations** (groundedness/relevance/coherence/safety) in CI; block promotion on regression. (5) **CI/CD** — Azure DevOps or GitHub Actions → staging endpoint → automated eval → **canary/blue-green** promotion to a managed endpoint or PTU deployment. (6) **Monitor** — Azure Monitor + App Insights for latency/cost/tokens; Azure ML drift monitors; online groundedness/safety sampling → retrain/rollback loop. (7) **Govern** — human-in-the-loop for high-risk, audit logs, periodic revalidation. The senior signal: the **eval gate and rollback loop are first-class, not bolted on**.

---

### Trade-offs & Decisions

#### Q: Managed service (Azure OpenAI / AWS Bedrock) vs self-hosted on AKS/EKS — how do you decide?

**Answer:** Default to managed unless you have a specific reason to self-host. Managed services (Azure OpenAI, Bedrock) give you zero-ops, SLA-backed reliability, built-in compliance controls, and instant access to frontier models — the right answer for most enterprise workloads. Self-hosting on AKS/EKS with vLLM or Triton makes sense when: (a) you need a fine-tuned or proprietary model not available as a managed endpoint; (b) data-sovereignty requirements prohibit sending data to a third-party API even within Azure/AWS; (c) volume is high enough that per-token costs dominate and a fixed GPU fleet is cheaper at steady state; or (d) you need deep control over batching, quantization, or KV-cache configuration for latency. The hidden cost of self-hosting is ops burden — GPU node management, CUDA compatibility, vLLM upgrades, OOM debugging. Size this against the managed-service premium before committing.

#### Q: Serverless vs container vs dedicated endpoint — how do you choose the right serving shape?

**Answer:** Match the serving shape to the traffic pattern. **Serverless** (Azure Container Apps, AWS Lambda + Bedrock, Modal) is right for spiky or low-average traffic where scale-to-zero economics matter — but cold starts (15–60s for large models) make it unsuitable for latency-sensitive user-facing products. Use provisioned concurrency or keep a warm instance if P95 cold-start is unacceptable. **Containerized endpoints** (Azure ML managed endpoint, SageMaker real-time endpoint) provide consistent latency, autoscale on request rate, and no cold-start problem at the cost of a minimum always-on instance. Right for steady interactive traffic. **Dedicated/self-hosted** (GPU VMs or AKS node pools) gives maximum throughput-per-dollar at high volume and full control over model runtime, but requires your team to own scaling, node health, and failover. Decision tree: prototype → serverless or managed API; production interactive → managed endpoint; high-volume or custom model → dedicated/AKS.

#### Q: Provisioned throughput (PTU/reserved capacity) vs pay-per-token — when does each win?

**Answer:** Pay-per-token is strictly better at low or unpredictable volume — you pay only for what you use, with no commitment. Provisioned throughput (Azure PTU, SageMaker Provisioned Concurrency, Bedrock Provisioned Throughput) trades a fixed reservation fee for three benefits: (1) **guaranteed capacity** — no 429 throttling during peaks; (2) **stable latency** — shared-pool congestion does not affect your endpoint; (3) **lower per-token cost** above the break-even volume. Calculate break-even: monthly PTU cost / (PAYG token price × tokens saved per month). For Azure OpenAI, Microsoft publishes a PTU sizing calculator — input your peak TPM requirement, get the PTU count, compare against PAYG. Common pattern: reserve PTU for baseline load, overflow to PAYG for bursts. This gives the cost predictability of a reservation with the safety valve of elastic capacity.

---

### Failure Modes & Incidents

#### Q: Your Azure OpenAI endpoint goes down mid-traffic — what is your failover design?

**Answer:** The right answer is that a single endpoint should never be a single point of failure. Production design: deploy to **two or more Azure OpenAI instances in different regions** (e.g., East US + West Europe) behind **Azure API Management** or a custom gateway. APIM retry policy routes around a 5xx or timeout to the next backend within the same request, invisible to the caller. Health probes continuously verify each backend; unhealthy ones are removed from rotation. For AKS-hosted models, use a multi-region AKS cluster with Azure Front Door or Traffic Manager routing. During an incident: (1) confirm the scope (single model, single region, full service); (2) shift 100% traffic to the surviving region; (3) open an Azure support ticket if it is a platform issue; (4) engage PTU support channel if capacity is degraded. Post-incident: add runbook entry, validate that the automatic failover fired correctly, and review whether the quota in the failover region was sufficient to absorb full traffic.

#### Q: Cold-start latency spikes after a model container scales up — how do you diagnose and fix it?

**Answer:** Cold-start latency has two components: **container startup** (image pull, process init) and **model weight load** (reading multi-GB weights from disk or network storage into GPU VRAM). The fix targets whichever is dominant. For container startup: pre-pull images onto nodes with a DaemonSet or use Azure Container Registry geo-replication; keep image layers small (multi-stage builds, no weights baked in). For model weight load: mount weights from a PersistentVolumeClaim backed by an SSD-tier disk (Azure Premium SSD or UltraDisk) rather than pulling from Blob every cold start; on AKS, use **node image caching** or a **init container** that warms the weight file into the node's page cache before the serving container starts. Operationally: set an **HPA min-replicas > 0** to prevent full scale-to-zero for latency-sensitive workloads; use KEDA's scale-from-zero only for batch or asynchronous inference jobs. Measure time-to-first-token on the first request after a scale-up event as your cold-start SLI; alert if it exceeds the budget.

#### Q: You receive an alert that inference costs spiked 10× overnight after a new model version deployed — what do you do?

**Answer:** Treat it as an incident: contain first, investigate second. Immediate actions: (1) check if the new model version is still rolling out and pause the canary if so; (2) compare average prompt + completion token counts between the old and new version — a prompt engineering regression or a model that generates verbose output explains most cost spikes; (3) verify the per-token price did not change (model version may map to a different pricing tier); (4) check if a feature flag opened a previously throttled code path (e.g., a summarization step that was disabled is now calling the model for every request). Root causes in order of frequency: (a) new system prompt is much longer; (b) new version does not apply `max_tokens` correctly and generates until the context limit; (c) traffic increased legitimately (check request count vs token-per-request ratio separately); (d) a bug causes retry storms — each failed request is retried N times. Fix and redeploy; add a **cost anomaly alert** (Azure Cost Management budget alert or CloudWatch billing alarm) with a threshold at 2× the daily baseline so this is caught within hours next time.

---

### Leadership & Behavioral

#### Q: How do you set deployment and rollback standards for GenAI services across your team?

**Answer:** Standards only stick when they are encoded in tooling, not just documented. The deployment standard I establish has three components. First, a **promotion gate**: no artifact reaches production without passing an automated evaluation suite (latency regression test, LLM-judge quality score, safety filter pass rate) — this is a hard CI check, not a recommendation. Second, a **graduated rollout policy**: all changes start at canary (5% traffic) with an automatic hold period and SLO watch; promotion to 100% is automated only if error rate and P95 latency stay within budget, otherwise it pages the on-call and halts. Third, a **rollback SLA**: the team commits to a rollback time (typically under 5 minutes for a managed endpoint, under 15 for AKS rolling deployment); we test this quarterly in a chaos drill. For GenAI specifically, quality regressions (hallucination rate, tone drift) are harder to detect than latency spikes — I require the LLM-judge score to be part of the automated promotion gate, not just a post-hoc dashboard. The first time a rollback actually fires automatically and saves a production incident, the team believes in the standard. Until then, it is just paperwork.

#### Q: Tell me about a time you led a zero-downtime model migration in production. (STAR)

**Answer (STAR format):**

**Situation:** Our customer-facing summarization service was running a fine-tuned GPT-3.5 model on Azure ML managed endpoints. We needed to migrate to a fine-tuned GPT-4o-mini variant to improve output quality, but the service handled ~2 M requests/day and any latency or quality regression would directly impact customer NPS.

**Task:** Lead the migration with zero downtime, measurable quality improvement, and a tested rollback path — on a two-week timeline before a product launch.

**Action:** I structured it as a four-phase canary migration. Phase 1: deployed the new model as a second Azure ML endpoint behind the same APIM gateway, with 0% traffic — ran offline eval (Foundry groundedness + human spot-check on 500 samples) to confirm quality uplift. Phase 2: routed 5% of live traffic to the new endpoint, collected 48 h of real-traffic LLM-judge scores and latency data, compared to the control cohort. Phase 3: incremented to 25%, then 75% over 72 h with automated SLO gates at each step — the gate checked that P95 TTFT was within 15% of baseline and LLM-judge score was ≥ baseline. Phase 4: cutover to 100% and decommissioned the old endpoint after a 24 h observation window. I wrote the rollback runbook before starting: APIM weight back to 0%/100% within 2 minutes, triggered by on-call or by the automated SLO breach alert.

**Result:** Migration completed in 11 days with zero customer-visible incidents. P95 TTFT improved by 8% (new model was more quantization-friendly at the same instance SKU). LLM-judge quality score rose 12 points. The canary framework I built became the team's standard model migration playbook.

---

> 🎯 **Staff/Principal stretch:** Define your organization's GenAI deployment platform strategy — managed vs self-hosted mix, multi-region architecture, and build-vs-buy decisions — over a 2-year horizon.
>
> **Model answer:** The strategy I would propose starts from a "managed by default, self-host by exception" principle: Azure OpenAI PTU for frontier models used in customer-facing products (SLA-backed, compliance controls, no GPU ops burden), Azure ML managed endpoints for fine-tuned or open models where managed API is not available, and AKS GPU node pools reserved for the subset of workloads with volume, latency, or data-residency requirements that managed services cannot satisfy. Multi-region is non-negotiable for any service with an SLA: primary region for low latency, secondary for failover, with APIM load-balancing across Azure OpenAI quota pools. Build-vs-buy framework: build only the thin orchestration and routing layer (gateway, semantic cache, cost attribution) that gives you vendor optionality; buy the inference infrastructure. The 2-year trajectory: Year 1 — standardize on managed endpoints and establish the LLMOps pipeline (eval gate, canary automation, cost attribution); Year 2 — consolidate open-model workloads onto a shared AKS inference platform with a model registry to prevent N teams each running their own vLLM clusters. The senior signal is recognizing that platform strategy is as much about preventing fragmentation as it is about picking the right technology.

---

## Section 5: Serving Internals & Production Operations (Senior Deep-Dive)

> Visual companion: [12.5 Production Operations](05_production_operations/README.md) diagrams the request lifecycle, scaling, releases, and observability covered below.

### Q: Walk me through what happens to an inference request from gateway to response.

**Answer:** Client hits the API gateway → auth + rate-limit check → the request is enqueued → a batching scheduler dequeues it and adds it to the in-flight batch on a GPU worker → tokens stream back as they are generated. The queue + continuous batching keep the GPU saturated; the **KV-cache** holds prior tokens' attention state so they are not recomputed each step. Latency splits into **time-to-first-token** (queue wait + prompt processing) and **inter-token latency** (decode speed).

### Q: Why use continuous batching instead of static batching?

**Answer:** Static batching collects N requests, runs the whole batch to completion, and leaves the GPU idle until the slowest sequence finishes. **Continuous batching** lets new requests join the running batch immediately and lets finished sequences free their slot, keeping the GPU full. It raises **throughput**; it does not make a single request faster.

### Q: HPA vs KEDA vs Karpenter — when does each apply?

**Answer:** **HPA** scales pod replicas on resource/custom metrics already exposed on the pods. **KEDA** scales on external event signals (queue depth, requests/sec) and can uniquely **scale to zero**. **Karpenter** (or Cluster Autoscaler) adds/removes **nodes** when pods can't be scheduled for lack of GPUs. The distinction: pods vs nodes, and internal vs external signals.

### Q: How do you roll back a bad model deployment safely?

**Answer:** Prefer strategies with fast undo — **blue-green** (switch traffic back instantly) or **canary** (small blast radius; abort by routing 100% back to the old version). Wire an **automatic trigger** on SLO breach (error rate / p95 latency) rather than relying on a human at 3 a.m. If the previous version is unhealthy or the rollback window has passed, **fix-forward** instead. Verify metrics recover after either path.

### Q: What metrics matter most for an LLM service?

**Answer:** p50/p95 **time-to-first-token** and **inter-token latency**; error/timeout rate; throughput (req/s) and GPU utilization; **queue depth**; and the GenAI-specific signals — **prompt/completion token counts** (both your bill and your capacity signal) and **answer quality**. Track **p95, not averages** — tail latency is what users actually feel.

### Q: How do you attribute token cost per customer?

**Answer:** **Tag each request at the gateway** (customer / feature / model), meter prompt + completion tokens, multiply by the per-1K-token price, and aggregate by tag into a cost dashboard. Add a budget check that can alert, throttle, or **downgrade to a cheaper model**. Tagging at the edge makes attribution automatic rather than a quarterly forensics exercise.

---

*References:*
- *[01 Deployment Overview →](01_deployment_overview/README.md)*
- *[02 Deployment Techniques →](02_deployment_techniques/README.md)*
- *[03 Azure Implementation →](03_deployment_implementation_with_azure/README.md)*
- *[04 AWS MLOps →](03_deployment_implementation_with_azure/04_deployment_with_aws_mlops/README.md)*
- *[05 Production Operations →](05_production_operations/README.md)*
