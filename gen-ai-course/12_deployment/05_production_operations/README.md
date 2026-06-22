# Module 12.5 — Production Operations

How a GenAI service actually behaves once real traffic hits it. This section is the visual, conceptual glue between the techniques (Module 12.2) and the cloud-specific implementations (12.3 Azure, 12.4 AWS): it shows the mental models — request flow, scaling, releases, and observability — that the code in those modules implements.

---

## Table of Contents

1. [The Request Lifecycle](#the-request-lifecycle)
2. [Scaling & Reliability](#scaling--reliability)
3. [Release & Rollback](#release--rollback)
4. [Observability & Cost](#observability--cost)
5. [Key Takeaways](#key-takeaways)

---

## The Request Lifecycle

A single inference request is not "call the model and wait." It passes through a gateway, authentication, rate limiting, a queue, and a batching scheduler before a GPU ever sees it — then tokens stream back as they are generated. Understanding this path explains nearly every latency and throughput decision you will make.

*Figure: the journey of one inference request from client to streamed response.*

```mermaid
sequenceDiagram
    participant C as Client
    participant G as API Gateway
    participant A as Auth / Rate Limit
    participant Q as Request Queue
    participant S as Batching Scheduler
    participant GPU as GPU Worker (vLLM)
    C->>G: POST /v1/chat/completions (stream=true)
    G->>A: validate API key, check quota
    A-->>G: ok (within rate limit)
    G->>Q: enqueue request
    Q->>S: dequeue when slot free
    S->>GPU: add to in-flight batch
    GPU-->>C: stream token 1
    GPU-->>C: stream token 2 ...
    GPU-->>C: stream final token + [DONE]
    Note over S,GPU: New requests join the running batch<br/>without waiting for it to finish (continuous batching)
```

Why a queue and a scheduler instead of one-request-per-GPU? Because GPUs are most efficient when processing many sequences at once. The scheduler packs concurrent requests into a single batch and keeps the GPU saturated.

*Figure: static batching wastes the GPU between batches; continuous batching keeps it full.*

```mermaid
flowchart TB
    subgraph Static["Static Batching"]
        direction LR
        S1[Collect N requests] --> S2[Run whole batch to completion] --> S3[GPU idle until all N finish] --> S4[Start next batch]
    end
    subgraph Continuous["Continuous Batching"]
        direction LR
        C1[Requests arrive any time] --> C2[Join the in-flight batch immediately] --> C3[Finished sequences leave, new ones take their slot] --> C2
    end
```

The other half of serving efficiency is the **KV-cache**: the attention keys/values for every token already generated are kept in GPU memory so they are not recomputed each step. This is why long contexts and many concurrent users consume GPU memory fast.

```
GPU Memory (e.g. 80 GB A100)
┌─────────────────────────────────────────────┐
│  Model weights (e.g. 7B @ fp16 ≈ 14 GB)       │
├─────────────────────────────────────────────┤
│  KV-cache  ── grows with (tokens × users)     │
│  [req A ███████      ]                         │
│  [req B ████         ]                         │
│  [req C ██████████   ]  ← evicted/blocked when │
│                          cache is full          │
├─────────────────────────────────────────────┤
│  Activations / scratch                         │
└─────────────────────────────────────────────┘
```

> **In practice:** Latency has two parts — time-to-first-token (queue wait + prompt processing) and inter-token latency (decode speed). Continuous batching improves throughput; it does not shorten a single request. When the KV-cache fills, new requests queue — that is the real meaning of "GPU at capacity."

**Maps to:** vLLM/continuous batching config in [02_deployment_techniques](../02_deployment_techniques/README.md#model-optimization-before-deployment); GPU node pools in [03_azure](../03_deployment_implementation_with_azure/README.md#azure-kubernetes-service-aks) and [04_aws_mlops](../03_deployment_implementation_with_azure/04_deployment_with_aws_mlops/README.md#sagemaker-real-time-endpoints).

---

## Scaling & Reliability

Traffic to a GenAI service is bursty. Scaling well means matching capacity to demand at two levels: scaling **pods** (replicas of your server) and scaling **nodes** (the actual GPU machines). Different signals drive each.

*Figure: the three layers of autoscaling and what triggers each.*

```mermaid
flowchart TD
    M[Metrics source] --> HPA
    M --> KEDA
    subgraph Pod["Pod-level scaling"]
        HPA[HPA<br/>CPU / GPU utilization or custom metric] -->|add/remove replicas| RS[ReplicaSet]
        KEDA[KEDA<br/>queue depth, requests/sec, event source] -->|scale 1..N or to zero| RS
    end
    RS -->|needs a node with a free GPU?| Node
    subgraph NodeScale["Node-level scaling"]
        Node[Karpenter / Cluster Autoscaler] -->|provision GPU node| GPUNode[New GPU node]
    end
    GPUNode -->|node Ready| RS
```

- **HPA** reacts to resource/custom metrics already exposed on running pods.
- **KEDA** reacts to *external* signals (queue length, requests/sec) and uniquely can scale **to zero**.
- **Karpenter / Cluster Autoscaler** adds machines when pods cannot be scheduled for lack of GPUs.

### Scale-to-zero and cold starts

Scaling to zero saves money on idle services but introduces a **cold start**: the next request must wait for a node, image pull, and model load.

*Figure: the cost of the first request after scaling from zero.*

```mermaid
sequenceDiagram
    participant U as User
    participant K as KEDA / Platform
    participant N as Node Pool
    participant P as Pod
    U->>K: first request after idle
    K->>N: scale 0 -> 1
    N->>N: provision node (~30-90s)
    N->>P: pull image + load model (~20-60s)
    P-->>U: ready — response served
    Note over U,P: Subsequent requests are warm (<1s overhead)
```

### Multi-region failover & high availability

For resilience, run in more than one region behind a global router that health-checks each backend and fails over automatically.

*Figure: active-active topology with health-checked failover.*

```mermaid
flowchart LR
    U[Users] --> GR[Global router / Traffic Manager]
    GR -->|healthy| R1
    GR -->|healthy| R2
    subgraph R1["Region A"]
        LB1[Load balancer] --> P1[Inference pods]
    end
    subgraph R2["Region B"]
        LB2[Load balancer] --> P2[Inference pods]
    end
    GR -.->|health probe fails| X[Drain region, route 100% to healthy region]
```

> **In practice:** Pick scaling signals that lead demand, not lag it — queue depth (KEDA) reacts before CPU saturation does. Keep a warm minimum replica for latency-sensitive services; use scale-to-zero only where cold-start latency is acceptable. Rate limiting at the gateway is part of reliability: it protects the GPU fleet from being overwhelmed.

**Maps to:** KEDA `ScaledObject` and GPU node pools in [03_azure](../03_deployment_implementation_with_azure/README.md#azure-kubernetes-service-aks); Karpenter and SageMaker auto-scaling in [04_aws_mlops](../03_deployment_implementation_with_azure/04_deployment_with_aws_mlops/README.md#ecs--eks-container-deployment); serverless cold starts in [02_deployment_techniques](../02_deployment_techniques/README.md#serverless-techniques).

---

## Release & Rollback

Shipping a new model or app version safely means controlling how much traffic it sees and being able to undo instantly. The three core strategies trade speed of rollout against blast radius.

*Figure: how traffic shifts under blue-green, canary, and rolling releases.*

```mermaid
flowchart TB
    subgraph BG["Blue-Green"]
        direction LR
        BGr["100% → Blue v1"] -. instant switch .-> BGg["100% → Green v2"]
    end
    subgraph Can["Canary"]
        direction LR
        Ca1[95% v1 / 5% v2] --> Ca2[75% v1 / 25% v2] --> Ca3[0% v1 / 100% v2]
    end
    subgraph Roll["Rolling"]
        direction LR
        Ro1[Replace pod 1] --> Ro2[Replace pod 2] --> Ro3[... until all v2]
    end
```

- **Blue-green:** two full environments, switch all traffic at once. Instant rollback (switch back), but double the resources during the cutover.
- **Canary:** shift traffic in small increments, watching metrics at each step. Smallest blast radius; slowest rollout.
- **Rolling:** replace replicas one batch at a time. No extra environment, but old and new run simultaneously mid-rollout.

### CI/CD pipeline with quality gates

Releases should be automated and gated — each stage must pass before the next runs.

*Figure: pipeline from commit to production with automated gates.*

```mermaid
flowchart LR
    Cm[Commit / PR] --> B[Build image]
    B --> U[Unit + lint]
    U --> E["Eval gate<br/>quality metric ≥ threshold"]
    E -->|pass| St[Deploy to staging]
    E -->|fail| Stop1[Block release]
    St --> Sm[Smoke tests + canary]
    Sm -->|healthy| Prod[Promote to production]
    Sm -->|errors/latency spike| RB[Auto-rollback]
```

### Rollback decision flow

When a release misbehaves, the decision to roll back should be mechanical, not a debate.

*Figure: deciding whether to roll back.*

```mermaid
flowchart TD
    Start[New version live] --> Q1{Error rate or latency<br/>breached SLO?}
    Q1 -->|no| Watch[Continue monitoring / proceed]
    Q1 -->|yes| Q2{"Within rollback window<br/>& previous version healthy?"}
    Q2 -->|yes| RB[Roll back to previous version]
    Q2 -->|no| FF[Fix-forward: patch + redeploy]
    RB --> Verify[Verify metrics recover]
    FF --> Verify
```

> **In practice:** Use canary for model changes where quality regressions are subtle (you need real traffic to detect them) and blue-green for infrastructure changes you can validate before the switch. Always wire an automatic rollback trigger on error-rate/latency SLO breach — humans are too slow at 3 a.m. The eval gate is what makes a GenAI pipeline different from a normal one: a green unit-test run does not mean the model still answers well.

**Maps to:** blue-green/canary/rolling configs in [02_deployment_techniques](../02_deployment_techniques/README.md#deployment-strategies); Azure ML traffic-split deployments in [03_azure](../03_deployment_implementation_with_azure/README.md#azure-machine-learning-endpoints); SageMaker production variants in [04_aws_mlops](../03_deployment_implementation_with_azure/04_deployment_with_aws_mlops/README.md#sagemaker-real-time-endpoints).

---

## Observability & Cost

You cannot operate what you cannot see. Observability for a GenAI service combines the three classic signals — metrics, logs, traces — with two GenAI-specific ones: **token usage** and **answer quality**.

*Figure: how signals flow from the service to dashboards and alerts.*

```mermaid
flowchart LR
    subgraph App["Inference service"]
        Met[Metrics: latency, QPS, GPU util, token counts]
        Log[Structured logs]
        Tr[Traces: gateway → model → tools]
    end
    Met --> TSDB[(Metrics store<br/>Prometheus / Azure Monitor / CloudWatch)]
    Log --> LStore[(Log store)]
    Tr --> TStore[(Trace store)]
    TSDB --> Dash[Dashboards: Grafana / App Insights]
    TSDB --> Alert{Alert rules}
    Alert -->|SLO breach| Page[Page on-call / trigger rollback]
```

A useful LLM dashboard groups panels by question, not by raw metric:

```
┌───────────────────────────┬───────────────────────────┐
│ Latency                   │ Reliability               │
│  • p50 / p95 TTFT         │  • error rate (4xx/5xx)   │
│  • inter-token latency    │  • timeouts / retries     │
├───────────────────────────┼───────────────────────────┤
│ Throughput & Capacity     │ Cost                      │
│  • requests/sec           │  • tokens/min (in/out)    │
│  • GPU utilization        │  • $ spend/hour           │
│  • queue depth            │  • $ per request          │
└───────────────────────────┴───────────────────────────┘
```

### Token spend & cost attribution

For LLM services, cost ≈ tokens. Attributing spend back to teams or customers requires tagging every request and aggregating by token counts × price.

*Figure: from a single request to a per-customer cost report.*

```mermaid
flowchart LR
    Req[Request tagged with<br/>customer / feature / model] --> Meter[Token meter<br/>prompt + completion tokens]
    Meter --> Price["× model price per 1K tokens"]
    Price --> Agg[Aggregate by tag]
    Agg --> Report[Cost dashboard<br/>per customer / feature]
    Agg --> Budget{Over budget?}
    Budget -->|yes| Throttle[Alert / throttle / downgrade model]
```

> **In practice:** Track p95, not averages — tail latency is what users feel. Always log `prompt_tokens` and `completion_tokens`; they are both your bill and your capacity signal. Tag requests at the gateway so cost attribution is automatic rather than a quarterly forensics exercise. Cache hits, shorter prompts, and routing easy requests to cheaper models are the three biggest cost levers.

**Maps to:** Prometheus/Grafana and middleware metrics in [02_deployment_techniques](../02_deployment_techniques/README.md#monitoring--observability); App Insights in [03_azure](../03_deployment_implementation_with_azure/README.md#monitoring-with-azure-monitor--application-insights); CloudWatch in [04_aws_mlops](../03_deployment_implementation_with_azure/04_deployment_with_aws_mlops/README.md#monitoring-with-cloudwatch--sagemaker-clarify).

---

## Key Takeaways

- A request flows gateway → auth/rate-limit → queue → batching scheduler → GPU → streamed tokens; the queue and KV-cache explain most latency and capacity behaviour.
- Continuous batching maximizes throughput, not single-request speed.
- Scale pods (HPA/KEDA) and nodes (Karpenter/Cluster Autoscaler) on signals that lead demand; scale-to-zero trades cost for cold-start latency.
- Choose canary for subtle model-quality risk, blue-green for validated infra cutovers; always wire automatic rollback on SLO breach.
- Observe metrics + logs + traces **plus** tokens and quality; tag requests for automatic cost attribution.

---

*Previous: [12.2 Deployment Techniques →](../02_deployment_techniques/README.md)*
*Next: [12.3 Azure Implementation →](../03_deployment_implementation_with_azure/README.md)*
