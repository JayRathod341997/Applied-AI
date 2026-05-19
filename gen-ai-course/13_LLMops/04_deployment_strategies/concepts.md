# Deployment Strategies - Concepts

## Table of Contents
1. [Deployment Patterns](#deployment-patterns)
2. [Blue-Green Deployment](#blue-green-deployment)
3. [Canary Deployment](#canary-deployment)
4. [Rolling Deployment](#rolling-deployment)
5. [A/B Testing](#ab-testing)
6. [Feature Flags](#feature-flags)
7. [Rollback Strategies](#rollback-strategies)
8. [CI/CD Integration](#cicd-integration)

---

## Deployment Patterns

### What Are Deployment Strategies and Why Do They Matter?

A **deployment strategy** is the method used to release a new version of software while minimizing downtime and risk. For LLMs, this is especially critical because:

- LLM inference is **stateful** (conversation history, context windows) — bad updates break ongoing sessions.
- GPU resources are **expensive** — you can't afford to run double capacity indefinitely.
- Model quality is **hard to test exhaustively** before production — real traffic reveals edge cases.
- Users notice quality regressions immediately (wrong tone, hallucinations, slower responses).

> **Interview angle:** "Why can't you just restart the server with the new model?"  
> Because that causes downtime, loses in-flight requests, and gives you no way to catch a bad update before it hits all users.

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  LLM Deployment Strategies                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Pattern          │ Complexity │ Risk    │ Rollback Speed      │
│   ─────────────────────────────────────────────────────────────  │
│   Blue-Green      │   Low     │  Low    │  Instant            │
│   Canary          │   Medium  │  Low    │  Fast               │
│   Rolling         │   Medium  │  Medium │  Gradual            │
│   A/B Testing     │   High    │  Medium │  Depends            │
│   Shadow          │   High    │  Low    │  Instant            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Concepts to Know for Interviews

| Term | Meaning |
|---|---|
| **Rollback** | Reverting to the previous stable version when a deployment goes wrong |
| **Traffic split** | Sending a percentage of requests to a new version while the rest go to the old |
| **Health check** | An endpoint (`/health`) the orchestrator calls to verify a pod is ready |
| **Canary** | Named after "canary in a coal mine" — a small group exposed first to detect problems |
| **Zero-downtime deployment** | Releasing new code without any users experiencing service unavailability |

---

## Blue-Green Deployment

### Theory

Blue-Green is the simplest zero-downtime strategy. The idea is to always maintain **two identical production environments** — one live (e.g., Blue), one idle (Green). You deploy to the idle environment, test it thoroughly, then flip the traffic switch.

**Why it works well for LLMs:**
- You can load the new model weights into Green and warm up the GPU cache before any real traffic hits it.
- If something breaks, rollback is **instant** — just switch traffic back to Blue. No re-deployment needed.
- There is **no mixed-version state** — all users are on the same version at any point.

**The tradeoff:** You need **double the infrastructure** during the transition window. For large LLMs (e.g., a 70B parameter model needing 4x A100s), this is expensive.

**When to use Blue-Green:**
- Major model upgrades (e.g., switching from LLaMA 2 to LLaMA 3)
- Changes that are hard to make backward-compatible (prompt format changes, API schema changes)
- When you have strict SLA requirements and cannot afford gradual risk

> **Interview question:** "What's the main limitation of Blue-Green for LLMs?"  
> **Answer:** Infrastructure cost doubles temporarily. For large GPU clusters, this can be prohibitively expensive. Canary deployments solve this by gradual traffic shifting.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Blue-Green Deployment                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Initial State                    After Switch                  │
│                                                                  │
│   ┌─────────────┐                 ┌─────────────┐               │
│   │   Blue     │                 │   Green     │               │
│   │  (Active)  │                 │  (Active)   │               │
│   │   v1.0     │    ──────▶     │   v1.1      │               │
│   │             │   Switch       │             │               │
│   │  Traffic:  │   Traffic      │  Traffic:   │               │
│   │   100%     │   ◀──────     │   100%      │               │
│   └─────────────┘                 └─────────────┘               │
│         │                               │                        │
│         ▼                               ▼                        │
│   ┌─────────────┐                 ┌─────────────┐               │
│   │  Green     │                 │   Blue     │               │
│   │  (Idle)    │                 │  (Idle)    │               │
│   │   v0.9     │                 │   v1.0     │               │
│   └─────────────┘                 └─────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```yaml
# kubernetes-blue-green.yaml
apiVersion: v1
kind: Service
metadata:
  name: llm-service
spec:
  selector:
    app: llm-api
    version: green
  ports:
  - port: 80
    targetPort: 8000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-deployment-blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-api
      version: blue
  template:
    metadata:
      labels:
        app: llm-api
        version: blue
    spec:
      containers:
      - name: llm-api
        image: llm-api:v1.0
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
            nvidia.com/gpu: 1
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-deployment-green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-api
      version: green
  template:
    metadata:
      labels:
        app: llm-api
        version: green
    spec:
      containers:
      - name: llm-api
        image: llm-api:v1.1
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
            nvidia.com/gpu: 1
```

```bash
# blue-green-deployment.sh
#!/bin/bash

# Deploy to green (new version)
kubectl apply -f llm-deployment-green.yaml

# Wait for green to be ready
kubectl rollout status deployment/llm-deployment-green

# Test green deployment
kubectl run test-green --image=curlimages/curl -- curl http://llm-service-green/health

# Switch traffic to green
kubectl patch service llm-service -p '{"spec":{"selector":{"version":"green"}}}'

# Keep blue for rollback
# If issue, switch back: kubectl patch service llm-service -p '{"spec":{"selector":{"version":"blue"}}}'
```

---

## Canary Deployment

### Theory

Canary deployment is a **risk-reduction strategy** where you release the new version to a small percentage of users first, monitor it, and only promote it to 100% if metrics look healthy. The rest of the traffic continues to the stable version.

**Why "Canary"?** Coal miners used to bring a canary bird underground. If toxic gas was present, the canary would die first — alerting miners before they were harmed. Similarly, a small group of users "absorbs" the risk of a bad deployment before it reaches everyone.

**How it works step by step:**
1. Deploy new version alongside the old one.
2. Route 5-10% of traffic to the new version.
3. Monitor error rates, latency, and business metrics.
4. Gradually increase traffic: 10% → 30% → 50% → 100%.
5. If metrics degrade at any step → roll back immediately.

**Why Canary is preferred for LLMs over Blue-Green:**
- You don't need to provision the full GPU cluster twice — just a small fraction.
- Real user traffic reveals prompt-injection edge cases, context-length issues, and tone problems that synthetic tests miss.
- Gradual rollout limits the **blast radius** of a bad deployment.

**Automated vs Manual promotion:**
- Automated: Tools like Argo Rollouts use Prometheus metrics (success rate, P95 latency) to decide whether to advance or abort automatically.
- Manual: A human watches the dashboard and clicks "promote" or "abort".

> **Interview question:** "How do you decide the right canary percentage?"  
> **Answer:** Start at 1-5% for high-risk changes (new model architecture), 10-20% for low-risk (prompt tuning). The goal is enough traffic to get statistically significant signal quickly, while limiting user impact if something goes wrong.

> **Interview question:** "What metrics do you watch during a canary rollout for an LLM?"  
> **Answer:** HTTP error rate (5xx), P95/P99 latency, token generation throughput, user feedback signals (thumbs down, regeneration rate), and business-level metrics (task completion rate, session abandonment).

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Canary Deployment                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Phase 1: 90/10 Split           Phase 2: 50/50 Split          │
│                                                                  │
│   ┌─────────────────┐           ┌─────────────────┐             │
│   │ v1.0 (Production)│          │ v1.0 (Production)│            │
│   │    90%          │           │    50%          │             │
│   │    ███████████ │           │    ██████       │             │
│   └─────────────────┘           └─────────────────┘             │
│          │                             │                         │
│          ▼                             ▼                        │
│   ┌─────────────────┐           ┌─────────────────┐             │
│   │ v1.1 (Canary)  │           │ v1.1 (Canary)  │             │
│   │    10%         │           │    50%          │             │
│   │    █           │           │    ██████       │             │
│   └─────────────────┘           └─────────────────┘             │
│                                                                  │
│   Phase 3: 100% (Full Rollout)                                  │
│                                                                  │
│   ┌─────────────────┐                                           │
│   │ v1.1 (Production)│                                          │
│   │    100%         │                                           │
│   │    ████████████ │                                           │
│   └─────────────────┘                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation with Argo Rollouts

```yaml
# canary-rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: llm-rollout
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: llm-canary
      stableService: llm-stable
      trafficRouting:
        nginx:
          stableIngress: llm-ingress
          additionalIngressAnnotations:
            canary-by-header: X-Canary
      steps:
        - setWeight: 10
        - pause: {duration: 10m}
        - setWeight: 30
        - pause: {duration: 10m}
        - setWeight: 50
        - pause: {duration: 10m}
        - setWeight: 80
        - pause: {duration: 10m}
        - setWeight: 100
      analysis:
        templates:
          - templateName: success-rate
        startingStep: 1
        args:
          - name: service-name
            value: llm-canary
  selector:
    matchLabels:
      app: llm-api
  template:
    metadata:
      labels:
        app: llm-api
    spec:
      containers:
      - name: llm-api
        image: llm-api:v1.1
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: 1m
      successCondition: result[0] >= 0.95
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            sum(rate(http_requests_total{service="{{args.service-name}}",status=~"2.."}[5m])) 
            / 
            sum(rate(http_requests_total{service="{{args.service-name}}"}[5m]))
    - name: latency
      interval: 1m
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            histogram_quantile(0.95, 
              sum(rate(http_request_duration_seconds_bucket{service="{{args.service-name}}"}[5m])) by (le)
            )
```

### Istio Canary Deployment

```yaml
# istio-canary.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: llm-virtual-service
spec:
  hosts:
  - llm-service
  http:
  - name: canary
    match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: llm-service-canary
      weight: 100
  - name: main
    route:
    - destination:
        host: llm-service-stable
        subset: v1.0
      weight: 90
    - destination:
        host: llm-service-canary
        subset: v1.1
      weight: 10
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: llm-destination
spec:
  host: llm-service
  subsets:
  - name: v1.0
    labels:
      version: "1.0"
  - name: v1.1
    labels:
      version: "1.1"
```

---

## Rolling Deployment

### Theory

Rolling deployment updates instances **one at a time** (or in small batches), gradually replacing the old version with the new one. At any point during the rollout, some pods run v1.0 and others run v1.1.

**How it differs from Blue-Green and Canary:**
- Blue-Green: All traffic on one version at a time, full switch at the end.
- Canary: Traffic split by percentage to two simultaneous stable deployments.
- Rolling: Pods are replaced one by one — the version mix changes over time.

**The critical challenge — version skew:** During a rolling update, users might hit v1.0 on one request and v1.1 on the next. If the two versions have incompatible behavior (e.g., different context formats, different tool call schemas), this creates inconsistent experiences. This is why rolling updates require **backward-compatible changes**.

**Key Kubernetes parameters:**
- `maxSurge`: How many extra pods can exist above the desired count during the update (controls speed).
- `maxUnavailable`: How many pods can be down simultaneously (controls minimum availability).

**When to use Rolling:**
- Stateless LLM APIs where each request is independent (no multi-turn session stickiness).
- Minor updates: bug fixes, dependency bumps, configuration changes.
- When you want to conserve GPU resources (no double provisioning).

**When NOT to use Rolling:**
- Breaking API changes between versions.
- Multi-turn conversation services where session stickiness matters — a user mid-conversation might get switched to a different model version.

> **Interview question:** "What is version skew and why is it a problem in rolling deployments?"  
> **Answer:** Version skew is when different versions of your service run simultaneously. For LLMs, if v1.0 and v1.1 have different system prompt formats or tool schemas, a user's conversation could behave inconsistently if routed to different versions on successive requests.

> **Interview question:** "How do readiness probes help in rolling deployments?"  
> **Answer:** A readiness probe checks if a pod is ready to serve traffic before Kubernetes routes requests to it. For LLMs, this is critical because model loading takes time (loading weights into GPU memory). Without a readiness probe, Kubernetes might send traffic to a pod that is still loading the model, causing request failures.

### Implementation

```yaml
# rolling-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-deployment
spec:
  replicas: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2           # Allow 2 extra pods during update
      maxUnavailable: 2    # Max 2 pods can be unavailable
  selector:
    matchLabels:
      app: llm-api
  template:
    metadata:
      labels:
        app: llm-api
        version: v1.1
    spec:
      containers:
      - name: llm-api
        image: llm-api:v1.1
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
            nvidia.com/gpu: 1
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

```bash
# Rolling update commands
kubectl set image deployment/llm-deployment llm-api=llm-api:v1.1

# Watch rollout
kubectl rollout status deployment/llm-deployment

# Rollback if needed
kubectl rollout undo deployment/llm-deployment

# Check rollout history
kubectl rollout history deployment/llm-deployment

# Rollback to specific revision
kubectl rollout undo deployment/llm-deployment --to-revision=2
```

---

## A/B Testing

### Theory

A/B testing in LLM deployments is about answering the question: **"Which model or configuration produces better outcomes for users?"** Unlike canary (which is about safe rollout), A/B testing is about **measurement and comparison**.

**The core difference between Canary and A/B Testing:**

| | Canary | A/B Testing |
|---|---|---|
| **Goal** | Safe rollout of a new version | Measure which version performs better |
| **Duration** | Temporary (hours to days) | Longer (days to weeks for significance) |
| **Success metric** | Error rate, latency | Business KPIs, user satisfaction |
| **Who decides outcome** | Automated metrics | Statistical analysis |

**Why A/B testing is hard for LLMs:**
- LLM quality is **subjective** — latency is easy to measure, but "better response" requires human evaluation or proxy metrics.
- You need **statistical significance** — too little traffic and your result is noise.
- LLM outputs are **non-deterministic** — same prompt can give different answers, adding variance.

**Good A/B test metrics for LLMs:**
- Task completion rate (did the user accomplish their goal?)
- Session length (did users stay longer or leave faster?)
- Explicit feedback (thumbs up/down, regenerate clicks)
- Follow-up question rate (a sign the first answer was unclear)
- Conversion rate (for product-embedded LLMs)

**Consistent user assignment:** Users must always see the same variant — otherwise their experience is inconsistent and your data is contaminated. The standard approach is to hash `experiment_name + user_id` to assign a stable bucket.

> **Interview question:** "How do you ensure users always see the same A/B variant?"  
> **Answer:** Hash the user ID with the experiment name using a deterministic hash (e.g., MD5), then take modulo 100 to get a bucket number. Map bucket ranges to variants. This gives consistent assignment without storing per-user state.

> **Interview question:** "What's the minimum sample size for an A/B test?"  
> **Answer:** You calculate it using a power analysis: define the minimum detectable effect (e.g., 2% improvement in task completion), desired statistical power (80%), and significance level (p < 0.05). Tools like Evan Miller's calculator give you the required sample size. For LLMs with subtle quality differences, you typically need tens of thousands of requests.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    A/B Testing Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Request                                                   │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────┐                                                │
│   │  Splitter   │                                                │
│   │  (Traffic  │                                                │
│   │   Router)  │                                                │
│   └──────┬──────┘                                                │
│          │                                                       │
│    ┌─────┴─────┬────────────┐                                   │
│    ▼            ▼            ▼                                   │
│ ┌──────┐  ┌──────┐  ┌──────┐                                   │
│ │ A:   │  │ B:   │  │ C:   │                                   │
│ │ GPT4 │  │ GPT3.5│  │Claude│                                   │
│ │ 40%  │  │ 40%  │  │ 20%  │                                   │
│ └──────┘  └──────┘  └──────┘                                   │
│    │          │          │                                      │
│    └──────────┴──────────┘                                      │
│               │                                                  │
│               ▼                                                  │
│   ┌──────────────────────┐                                      │
│   │  Metrics Collection  │                                      │
│   │  - Latency           │                                      │
│   │  - Success Rate      │                                      │
│   │  - User Feedback     │                                      │
│   │  - Task Completion   │                                      │
│   └──────────────────────┘                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# ab_testing.py
from typing import Dict, List
import random
import hashlib
from dataclasses import dataclass

@dataclass
class Experiment:
    name: str
    variants: List[Dict]
    traffic_split: List[int]  # Percentages
    
    def get_variant(self, user_id: str) -> str:
        """Determine variant based on user ID for consistent assignment"""
        # Use hash for deterministic assignment
        hash_value = int(
            hashlib.md5(f"{self.name}:{user_id}".encode()).hexdigest(), 16
        )
        bucket = hash_value % 100
        
        cumulative = 0
        for i, split in enumerate(self.traffic_split):
            cumulative += split
            if bucket < cumulative:
                return self.variants[i]["name"]
        
        return self.variants[-1]["name"]

class ABTester:
    """
    A/B testing for LLM deployments
    """
    
    def __init__(self):
        self.experiments = {}
    
    def register_experiment(
        self,
        name: str,
        variants: List[Dict],
        traffic_split: List[int]
    ):
        """Register a new A/B test"""
        assert len(variants) == len(traffic_split)
        assert sum(traffic_split) == 100
        
        self.experiments[name] = Experiment(
            name=name,
            variants=variants,
            traffic_split=traffic_split
        )
    
    def get_variant(self, experiment_name: str, user_id: str) -> Dict:
        """Get the variant for a user"""
        exp = self.experiments.get(experiment_name)
        if not exp:
            raise ValueError(f"Experiment {experiment_name} not found")
        
        variant_name = exp.get_variant(user_id)
        return next(v for v in exp.variants if v["name"] == variant_name)
    
    def run_experiment(self, prompt: str, user_id: str, experiment_name: str):
        """Run A/B test and return results"""
        variant = self.get_variant(experiment_name, user_id)
        
        # Call LLM based on variant
        if variant["model"] == "gpt-4":
            result = call_gpt4(prompt)
        elif variant["model"] == "gpt-3.5-turbo":
            result = call_gpt35(prompt)
        else:
            result = call_claude(prompt)
        
        return {
            "variant": variant["name"],
            "model": variant["model"],
            "result": result
        }

# Usage
tester = ABTester()
tester.register_experiment(
    name="model_comparison",
    variants=[
        {"name": "control", "model": "gpt-4"},
        {"name": "variant_a", "model": "gpt-3.5-turbo"},
        {"name": "variant_b", "model": "claude-3-sonnet"}
    ],
    traffic_split=[40, 40, 20]
)
```

---

## Feature Flags

### Theory

A **feature flag** (also called a feature toggle) is a configuration switch that lets you enable or disable a feature at runtime — without deploying new code. For LLMs, this is a powerful tool for **decoupling deployment from release**.

**The core principle:** Deploy the code (new model, new prompt, new API integration), but keep it turned off. Then turn it on for specific users, regions, or conditions — all without touching the codebase again.

**Why feature flags matter for LLMs:**

1. **Gradual rollout without redeployment:** You can push a new model to production and enable it for 1% of users on Monday, 10% on Wednesday, 50% on Friday — all by changing a config value.
2. **Kill switch:** If a new model starts misbehaving, you flip the flag to instantly revert — no need to roll back a deployment.
3. **User segmentation:** Enable a more powerful (and expensive) model only for premium users, without maintaining two separate deployments.
4. **Testing in production safely:** Enable a feature for internal users or beta testers only.

**Types of feature flags:**
- **Boolean flags:** Feature is ON or OFF.
- **Multivariate flags:** Choose between multiple values (e.g., which model to use: "gpt-4", "gpt-4-turbo", "claude-3").
- **Targeting rules:** Flags that evaluate based on user context (user tier, region, request volume).

**Feature flags vs Canary deployment:**
- Canary = controlled rollout at the infrastructure level (routing layer).
- Feature flags = controlled rollout at the application level (code logic).
- They complement each other: deploy with canary, release with flags.

> **Interview question:** "What's the difference between a feature flag and a canary deployment?"  
> **Answer:** A canary deployment splits traffic at the infrastructure level (load balancer/ingress) and requires two running versions. A feature flag splits behavior at the application level — there's only one deployed version, but a code branch decides which path to take based on user context. Feature flags are more flexible but add code complexity.

> **Interview question:** "What are the risks of feature flags?"  
> **Answer:** Flag debt — old flags that are never cleaned up accumulate and make the codebase hard to reason about. Also, testing all combinations of active flags is exponentially complex. Best practice: set a TTL for each flag and delete it after the rollout is complete.

### Implementation

```python
# feature_flags.py
from typing import Dict, Callable, Any
import json
import os

class FeatureFlagManager:
    """
    Manage feature flags for LLM deployments
    """
    
    def __init__(self):
        self.flags: Dict[str, Dict] = {}
    
    def register_flag(
        self,
        name: str,
        default_value: Any = False,
        description: str = ""
    ):
        """Register a feature flag"""
        self.flags[name] = {
            "default": default_value,
            "description": description,
            "rules": []
        }
    
    def add_rule(
        self,
        flag_name: str,
        condition: Callable[[Dict], bool],
        value: Any
    ):
        """Add a targeting rule"""
        if flag_name not in self.flags:
            raise ValueError(f"Flag {flag_name} not registered")
        
        self.flags[flag_name]["rules"].append({
            "condition": condition,
            "value": value
        })
    
    def is_enabled(
        self,
        flag_name: str,
        context: Dict = None
    ) -> bool:
        """Check if feature flag is enabled"""
        if flag_name not in self.flags:
            return self.flags[flag_name]["default"]
        
        flag = self.flags[flag_name]
        context = context or {}
        
        # Check rules in order
        for rule in flag["rules"]:
            if rule["condition"](context):
                return rule["value"]
        
        return flag["default"]
    
    def get_value(
        self,
        flag_name: str,
        context: Dict = None,
        default: Any = None
    ) -> Any:
        """Get feature flag value"""
        if flag_name not in self.flags:
            return default
        
        if self.is_enabled(flag_name, context):
            return self.flags[flag_name].get("value", default)
        
        return default

# Usage
flags = FeatureFlagManager()

# Register flags
flags.register_flag("new_model", False, "Enable new GPT-4 model")
flags.register_flag("streaming_enabled", True, "Enable streaming responses")
flags.register_flag("enhanced_caching", False, "Enable semantic caching")

# Add targeting rules
flags.add_rule(
    "new_model",
    lambda ctx: ctx.get("user_tier") == "premium",
    True
)

flags.add_rule(
    "enhanced_caching",
    lambda ctx: ctx.get("request_count", 0) > 100,
    True
)

# Check flags in request
def handle_request(request: Dict):
    context = {
        "user_id": request["user_id"],
        "user_tier": get_user_tier(request["user_id"]),
        "request_count": get_request_count(request["user_id"])
    }
    
    # Use flags
    use_new_model = flags.is_enabled("new_model", context)
    use_streaming = flags.is_enabled("streaming_enabled", context)
    
    # Route accordingly
    if use_new_model:
        result = call_gpt4(request["prompt"])
    else:
        result = call_gpt35(request["prompt"])
    
    return result
```

---

## Rollback Strategies

### Theory

A rollback is the process of reverting a deployment to the previous stable version when the current version is causing problems. The speed and ease of rollback is one of the most important design goals in any deployment system.

**Why rollbacks are especially critical for LLMs:**
- Model behavior is hard to fully test before production — a fine-tuned model might generate biased or harmful outputs only in rare real-world scenarios.
- LLM errors can be **silent** — the service returns HTTP 200 but the answer is wrong, hallucinated, or off-tone. Latency monitors alone won't catch this.
- GPU memory is slow to load — rolling out a fix takes time, so a fast rollback to the last known good state is essential.

**Types of rollback triggers:**

| Trigger Type | Example | Who Decides |
|---|---|---|
| **Automated (metric-based)** | Error rate > 5% for 3 minutes | Alerting system / Argo Rollouts |
| **Manual** | On-call engineer observes bad outputs | Human |
| **Scheduled** | Canary auto-aborts after timeout if not promoted | Policy |

**The rollback decision framework:**
1. **Monitor**: Track error rate, latency, and quality metrics in real time.
2. **Alert**: Set thresholds — when breached, notify immediately.
3. **Decide**: Is this a transient spike or a sustained regression?
4. **Execute**: Blue-Green = patch service selector. Canary = abort rollout. Rolling = `kubectl rollout undo`.
5. **Post-mortem**: Understand root cause before re-deploying.

**Common rollback mistakes:**
- No pre-deployment snapshot → can't compare "before" metrics to "after".
- Rollback brings back an old bug that was fixed in v1.0 but forgotten.
- Rolling back the model but not the prompt/config that was co-deployed.

> **Interview question:** "How do you detect that you need to roll back an LLM deployment?"  
> **Answer:** You need both technical metrics (P99 latency, error rate, token throughput) and quality signals (user thumbs-down rate, regeneration clicks, session abandonment). A model can be technically healthy but producing bad answers — you need both layers of monitoring. Set automated rollback on the technical metrics and have a human review process for quality.

> **Interview question:** "What should you do before every deployment to make rollback easier?"  
> **Answer:** Take a versioned snapshot of: the model artifact/image tag, the serving configuration, the prompt templates, and the baseline metrics. Store rollback history with timestamps. This way, rolling back to a specific known-good state is deterministic, not guesswork.

### Automated Rollback

```python
# rollback_manager.py
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import time

@dataclass
class DeploymentSnapshot:
    version: str
    timestamp: datetime
    config: Dict
    metrics: Dict

class RollbackManager:
    """
    Manage deployment rollbacks
    """
    
    def __init__(self):
        self.snapshots: Dict[str, List[DeploymentSnapshot]] = {}
        self.thresholds = {
            "error_rate": 0.05,      # 5% error rate
            "latency_p99": 5.0,       # 5 seconds
            "success_rate": 0.95      # 95% success rate
        }
    
    def take_snapshot(
        self,
        version: str,
        config: Dict,
        metrics: Dict
    ):
        """Take a deployment snapshot"""
        if version not in self.snapshots:
            self.snapshots[version] = []
        
        snapshot = DeploymentSnapshot(
            version=version,
            timestamp=datetime.now(),
            config=config,
            metrics=metrics
        )
        self.snapshots[version].append(snapshot)
    
    def should_rollback(self, current_metrics: Dict) -> bool:
        """Determine if rollback is needed"""
        if current_metrics.get("error_rate", 0) > self.thresholds["error_rate"]:
            return True
        
        if current_metrics.get("latency_p99", 0) > self.thresholds["latency_p99"]:
            return True
        
        if current_metrics.get("success_rate", 1) < self.thresholds["success_rate"]:
            return True
        
        return False
    
    async def rollback(
        self,
        version: str,
        reason: str
    ) -> bool:
        """Execute rollback to previous version"""
        if version not in self.snapshots or not self.snapshots[version]:
            return False
        
        # Get previous version
        previous = self.snapshots[version][-1]
        
        # Execute rollback
        print(f"Rolling back to version: {previous.version}")
        print(f"Reason: {reason}")
        
        # Apply previous configuration
        await self._apply_config(previous.config)
        
        return True
    
    async def _apply_config(self, config: Dict):
        """Apply configuration (implementation depends on deployment method)"""
        # Kubernetes rollback
        # import subprocess
        # subprocess.run(["kubectl", "rollout", "undo", "deployment/llm-deployment"])
        pass
```

---

## CI/CD Integration

### Theory

CI/CD (Continuous Integration / Continuous Deployment) is the automation pipeline that takes code from a developer's commit to a running production service. For LLMs, the pipeline is more complex than a standard API service because:

- **Model artifacts are large** — pushing a 10GB model weight file is not the same as pushing a Python package. You need artifact stores (S3, GCS, Hugging Face Hub) instead of Docker layers.
- **Evaluation is domain-specific** — unit tests verify code correctness but not model quality. You need LLM-specific eval suites (e.g., RAGAS for RAG, Evals for instruction following).
- **Deployment involves GPU scheduling** — spinning up a GPU node takes minutes, not seconds.
- **Rollback must cover both code and model** — a bad fine-tune might pass all tests but regress on user-facing quality.

**Typical LLM CI/CD pipeline stages:**

```
Commit → Unit Tests → Build Docker Image → Integration Tests
→ Deploy to Staging → LLM Eval Suite → Deploy Canary to Prod
→ Monitor Metrics → Promote / Rollback
```

**Key gates you should add for LLMs:**
1. **Prompt regression tests**: Run a fixed set of prompts and compare outputs to known-good baselines (using embedding similarity or LLM-as-judge).
2. **Latency benchmarks**: Ensure P95 latency stays within SLA before promoting.
3. **Safety checks**: Run harmful content classifiers against model outputs on a test set.
4. **Smoke tests**: Simple end-to-end health check on staging before production.

**Environment strategy:**
- **Development**: Local or dev cluster — fast iteration, no real traffic.
- **Staging**: Production-like environment — run full eval suite here.
- **Canary**: 5-10% of production traffic — real users, monitored closely.
- **Production**: Full traffic — automated alerts and rollback.

> **Interview question:** "How does CI/CD for LLMs differ from CI/CD for a regular web service?"  
> **Answer:** Three main differences: (1) Model artifacts are gigabytes, not megabytes — you need dedicated artifact management, not just Docker images. (2) Correctness is subjective — you need LLM eval suites alongside unit tests. (3) Deployment involves GPU scheduling and model loading time, making pipelines slower. You also need separate rollback for model weights vs. application code.

> **Interview question:** "How do you prevent a bad model fine-tune from reaching production?"  
> **Answer:** Add an automated eval gate in CI: run the fine-tuned model against a curated benchmark dataset, compute metrics (accuracy, BLEU, RAGAS scores), and fail the pipeline if they drop below a threshold compared to the baseline. This is analogous to code coverage gates in traditional CI.

### GitHub Actions Workflow

```yaml
# .github/workflows/llm-deployment.yml
name: LLM Deployment

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest tests/ --cov=llm
      
      - name: Run integration tests
        run: |
          pytest tests/integration/ -v

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
      - name: Deploy to staging
        run: |
          kubectl set image deployment/llm-staging \
            llm-api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
      
      - name: Wait for deployment
        run: |
          kubectl rollout status deployment/llm-staging --timeout=300s
      
      - name: Run smoke tests
        run: |
          curl -f https://staging.llm.example.com/health

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - name: Deploy canary
        run: |
          # Deploy canary with 10% traffic
          kubectl apply -f canary-deployment.yaml
          kubectl argo rollouts set weighting llm-rollout --weight 10 -n argo-rollouts
      
      - name: Monitor canary
        run: |
          # Wait and check metrics
          sleep 600
          
          # Check error rate
          ERROR_RATE=$(curl -s http://prometheus/api/v1/query?query=sum(rate(llm_requests_total{status=~"5.."}[5m]))/sum(rate(llm_requests_total[5m])))
          
          if (( $(echo "$ERROR_RATE > 0.05" | bc -l) )); then
            echo "Error rate too high, rolling back"
            kubectl argo rollouts abort llm-rollout -n argo-rollouts
            exit 1
          fi
      
      - name: Promote canary
        run: |
          # Full rollout
          kubectl argo rollouts set weighting llm-rollout --weight 100 -n argo-rollouts
```

---

## Best Practices

1. **Start with Blue-Green**: For initial deployments
2. **Use Canary for Production**: Reduces risk significantly
3. **Automate Rollbacks**: Based on metrics and alerts
4. **Monitor Continuously**: Track key metrics during deployment
5. **Use Feature Flags**: For granular control
6. **A/B Test Intelligently**: Test model changes separately
7. **Keep Rollback Simple**: Always have a way to revert quickly
8. **Document Changes**: Track what changed and why
