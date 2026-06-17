# Deployment Strategies — Concepts

Getting a tested artifact into production safely is its own discipline. You package the app so it runs identically anywhere (containers), provision its surroundings reproducibly (IaC), roll it out in a way that limits the blast radius of a bad release (blue-green / canary), keep environments cleanly separated (dev/staging/prod), and revert automatically the instant metrics go bad (rollback). This file walks through each, with the canary controller as the centrepiece you will build in the exercise.

---

## 1. Containerization with Docker

A container packages the app *and* its dependencies into one portable, reproducible unit — "it works on my machine" becomes "it works everywhere." For LLM apps the extra concerns are image size (dependencies are heavy), model-weight handling, and security.

### Multi-stage builds keep images small

A builder stage installs/compiles dependencies; the production stage copies only what's needed, leaving build tools behind.

```dockerfile
# ── Stage 1: builder ──
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: production ──
FROM python:3.11-slim AS production
WORKDIR /app
COPY --from=builder /install /usr/local      # only the installed packages
COPY src/ ./src/
RUN useradd -r appuser && chown -R appuser /app
USER appuser                                 # non-root
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health || exit 1
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Where do the model weights go?

| Strategy | How | Trade-off |
|---|---|---|
| **Bake at build** | download into the image | self-contained, but huge image + slow builds |
| **Fetch at runtime** | download on container start | small image, slower cold start |
| **Init container** | K8s init container pre-fetches | clean separation, extra complexity |
| **Shared volume** | weights on a persistent volume | fast start, needs volume management |

### Container security essentials

Run as a **non-root** user, use a **minimal base** (`-slim` / distroless), **never bake secrets** into the image (use env vars / a secret manager), pin dependencies, and scan images (`trivy image ...`). A leaked secret in a layer lives forever in the image history.

---

## 2. Infrastructure as Code (IaC)

IaC declares cloud resources — registries, compute, networking, managed AI services — as version-controlled files instead of click-ops. The payoff: deployments are **reproducible** (spin up an identical environment from the same file), **auditable** (changes go through code review and Git history), and **drift-detectable** (`terraform plan` shows what real-world state diverged).

```
   *.tf / *.bicep  ──plan──►  diff vs reality  ──apply──►  cloud resources
   (desired state)            (what will change)           (actual state)
```

| Feature | Terraform | Bicep |
|---|---|---|
| **Cloud scope** | Multi-cloud | Azure only |
| **Language** | HCL | Bicep DSL → ARM |
| **State** | State file (remote/local) | Azure-managed (ARM) |
| **Drift detection** | `terraform plan` | ARM / what-if |
| **Ecosystem** | Terraform Registry | Azure Verified Modules |
| **Best for** | multi-cloud / industry-standard | Azure-native teams |

```hcl
# Terraform: an Azure Container App (excerpt) — declarative, reviewable, repeatable
resource "azurerm_container_app" "main" {
  name  = "llm-${var.environment}"
  template {
    container { name = "llm"; image = var.container_image; cpu = "1.0"; memory = "2Gi" }
    min_replicas = 2
    max_replicas = 10
  }
}
```

The golden rule: **never hand-provision production infrastructure.** If it's not in code, it can't be reviewed, reproduced, or rolled back.

---

## 3. Blue-Green vs Canary vs Shadow

Releasing all-at-once means a bad version hits 100% of users instantly. Gradual strategies shrink that blast radius. AI apps benefit especially, because a model/prompt change can pass tests yet degrade real-world quality.

| Strategy | How | Rollback speed | Risk profile |
|---|---|---|---|
| **Blue-Green** | Two identical envs; flip all traffic at once | Instant (flip back) | All-or-nothing cutover |
| **Canary** | Send a small % to the new version; ramp up | Fast (shift traffic) | Gradual exposure |
| **Shadow / dark launch** | New version gets *duplicate* traffic, serves no users | N/A (no user impact) | Observe with zero risk |
| **Feature flags** | Toggle per segment / % | Instant | Flag-management overhead |

```
  BLUE-GREEN                         CANARY
  ┌────────┐ 100%                    ┌────────┐ 90% → 50% → 0%
  │ Blue   │◄── traffic              │ Stable │
  └────────┘     │  flip             └────────┘
  ┌────────┐ 0%  ▼                   ┌────────┐ 10% → 50% → 100%
  │ Green  │ ──► becomes 100%        │ Canary │  (ramp if healthy)
  └────────┘                         └────────┘
```

**Blue-green** gives instant rollback (just flip back to blue) but is binary — every user moves at once. **Canary** trades instant cutover for *graduated* exposure: a small slice sees the new version, you watch its metrics, and you ramp up only if it stays healthy — or shift traffic back to 0% if it doesn't.

---

## 4. The Canary Controller

A canary controller automates the ramp: shift traffic up in increments, check the canary's error rate after each step, **promote** (ramp further) while healthy, and **auto-rollback** (canary → 0%) the moment errors exceed a threshold. This is the loop you implement in the exercise.

```
 start: canary = 0%
   │
   ├─► shift +step  ──►  observe error_rate
   │                          │
   │            error > threshold ? ──yes──► ROLLBACK (canary → 0%)  ✗
   │                          │ no
   │            canary >= 100% ? ──yes──► PROMOTE (full rollout)     ✓
   └───────────────── no ◄────┘
```

```python
def canary_step(weight, step, error_rate, threshold, max_weight=100):
    if error_rate > threshold:
        return 0, "rollback"            # abort: shift all traffic back
    weight = min(weight + step, max_weight)
    if weight >= max_weight:
        return weight, "promoted"       # success: full rollout
    return weight, "continue"           # healthy so far, keep ramping
```

For LLM apps the canary should watch not just HTTP error rate and latency but a **quality** signal (e.g. a live golden-set pass-rate), because the dangerous regressions are the ones that return `200 OK` with worse answers.

---

## 5. Environment Management

Environments are separate, progressively stricter copies of the system. A change earns its way from dev to prod.

| Aspect | Development | Staging | Production |
|---|---|---|---|
| **Model** | small/cheap | prod-equivalent | prod |
| **Rate limits** | relaxed | moderate | strict |
| **Logging** | DEBUG | INFO | WARNING + alerts |
| **Secrets** | `.env` file | Key Vault | Key Vault |
| **Replicas** | 1 | 1 | 2–10 (autoscaled) |
| **Approval to deploy** | no | no | yes |
| **Prompt version** | HEAD | candidate | promoted/active |

Configuration should be **environment-aware** and injected (env vars / settings object), never hardcoded, so the same image runs in every environment and only the config differs:

```python
class Settings:
    environment: str = "development"   # overridden per env via env var
    default_model: str = "gpt-4o"
    log_level: str = "INFO"
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
```

---

## 6. Automated Rollback

Rollback must be **pre-planned, automated, and metric-driven** — a human noticing a dashboard at 3 a.m. is not a strategy. The deployment system watches signals and reverts when one breaches.

| Trigger | Threshold | Action |
|---|---|---|
| Error-rate spike | > 5% over 5 min | shift traffic to last stable |
| P99 latency | > 3000 ms | shift traffic to last stable |
| Quality drop | < threshold on golden set | revert prompt/model version |
| Cost anomaly | > 2× baseline | revert + alert |

```bash
# Azure Container Apps: shift 100% back to the previous stable revision
az containerapp ingress traffic set \
  --name llm-app --resource-group rg-llm-prod \
  --revision-weight llm-app--previous-stable=100
```

In a canary, "rollback" is simply setting the canary weight to **0%** — the stable version was never removed, so recovery is one traffic-weight change. That is why canary + automated triggers is such a safe combination: the previous version is always one step away.

---

## Key Takeaways

- **Containerize with multi-stage builds**, run as **non-root**, keep **secrets out of the image**, and choose a model-weight strategy (bake / runtime / init / volume) by your cold-start vs image-size trade-off.
- **Use IaC (Terraform multi-cloud, Bicep Azure-native)** so infrastructure is reproducible, reviewable, and drift-detectable — never hand-provision production.
- **Gradual rollouts shrink blast radius:** blue-green for instant flip/rollback, canary for graduated exposure, shadow for zero-risk observation.
- **A canary controller** ramps traffic while healthy and auto-rolls back to 0% on a threshold breach; for LLMs include a *quality* signal, not just HTTP errors.
- **Manage environments with progressive strictness** and one image + injected config; **automate rollback** on error-rate, latency, quality, and cost triggers.
