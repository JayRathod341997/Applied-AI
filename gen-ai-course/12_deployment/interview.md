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

*References:*
- *[01 Deployment Overview →](01_deployment_overview/README.md)*
- *[02 Deployment Techniques →](02_deployment_techniques/README.md)*
- *[03 Azure Implementation →](03_deployment_implementation_with_azure/README.md)*
- *[04 AWS MLOps →](03_deployment_implementation_with_azure/04_deployment_with_aws_mlops/README.md)*
