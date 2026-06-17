# Deployment Strategies — Interview Questions

Interview questions and model answers on containerization, IaC, rollout strategies, environment management, and automated rollback.

---

## 1. Why use a multi-stage Docker build for an LLM app?

**Answer:** To keep the production image small and secure. A builder stage installs/compiles dependencies; the production stage copies only the artifacts it needs (the installed packages and app code), leaving compilers and build caches behind. The result is a smaller image, faster pulls, and a reduced attack surface — important for LLM apps whose dependency trees are heavy.

---

## 2. What are the container security essentials for production?

**Answer:** Run as a **non-root** user; use a **minimal base** image (`-slim` or distroless); **never bake secrets** into the image (they persist in layer history — use env vars or a secret manager); pin dependencies for reproducible builds; and scan images (e.g. `trivy`). Optionally run with a read-only filesystem. A secret committed to a layer is effectively leaked forever.

---

## 3. Compare the strategies for getting model weights into a container.

**Answer:**

- **Bake at build** — self-contained image but huge and slow to build.
- **Fetch at runtime** — small image, slower cold start.
- **Init container** (K8s) — pre-fetches before the main container; clean but adds complexity.
- **Shared volume** — fast start, but you must manage the persistent volume.

Choose by your cold-start vs image-size/build-time trade-off and your orchestration platform.

---

## 4. What problems does Infrastructure as Code solve?

**Answer:** It replaces manual click-ops with version-controlled declarations, giving you **reproducibility** (recreate an identical environment from the same files), **auditability** (changes go through code review and Git history), and **drift detection** (`terraform plan` / ARM what-if shows where reality diverged from the spec). The rule: never hand-provision production — if it's not in code, it can't be reviewed, reproduced, or rolled back.

---

## 5. Terraform or Bicep — how do you choose?

**Answer:** **Terraform** is multi-cloud (HCL, its own state file, huge provider ecosystem) and the broad industry standard — pick it for multi-cloud or cross-team portability. **Bicep** is an Azure-native DSL that compiles to ARM with Azure-managed state and tight Azure integration — pick it for Azure-only teams who want the lowest-friction Azure experience.

---

## 6. Explain blue-green vs canary vs shadow deployment.

**Answer:**

- **Blue-green** — two identical environments; flip *all* traffic at once. Instant rollback (flip back) but an all-or-nothing cutover.
- **Canary** — route a small % to the new version and ramp up gradually while watching metrics; shift back to 0% if it degrades. Graduated exposure.
- **Shadow / dark launch** — the new version receives *duplicate* traffic but serves no users; you observe real-traffic behaviour at zero user risk.

---

## 7. Walk through how a canary controller works.

**Answer:** Start the canary at 0%. Each iteration: shift traffic up by an increment, observe the canary's error rate (and ideally a quality signal) at the new weight, then decide — if errors exceed the threshold, **roll back** (canary → 0%, stop); if the weight has reached 100% with no breach, **promote** (full rollout); otherwise keep ramping. The stable version stays running throughout, so rollback is a single traffic-weight change.

---

## 8. Why should an LLM canary monitor quality, not just error rate and latency?

**Answer:** The most dangerous LLM regressions succeed *technically* — they return `200 OK` quickly — but produce worse answers. HTTP error rate and latency would look perfectly healthy. You need an output-quality signal, such as a live golden-set pass-rate or an LLM-as-judge score on sampled traffic, to catch a quality regression before it ramps to 100%.

---

## 9. How should configuration differ across environments?

**Answer:** Build **one image** and inject **environment-aware config** per environment (model name, rate limits, log level, secrets source, replica counts), rather than building a separate image per environment or hardcoding values. Apply progressive strictness: relaxed limits and DEBUG logging in dev; prod-equivalent settings and approval gates in production. Same artifact everywhere; only config changes — which prevents "it worked in staging" drift.

---

## 10. Why must rollback be automated and metric-driven for AI apps?

**Answer:** Because LLM behaviour is non-deterministic, a change can pass every pre-deploy test and still regress on real-world inputs. Waiting for a human to spot a dashboard is too slow and unreliable. Automated rollback watches triggers — error-rate spike, P99 latency, quality drop on a golden set, cost anomaly — and reverts to the last stable version the moment one breaches, minimizing user impact.

---

## 11. What rollback triggers would you wire up, and at what thresholds?

**Answer:** A blend of generic and AI-specific signals:

- Error-rate spike (> ~5% over 5 min) → shift traffic to last stable.
- P99 latency (> ~3000 ms) → shift traffic to last stable.
- Quality drop (< threshold on a golden set) → revert prompt/model version. *(AI-specific.)*
- Cost anomaly (> ~2× baseline token spend) → revert + alert. *(AI-specific.)*

Thresholds get margin so normal variance doesn't trigger spurious rollbacks.

---

## 12. In a canary, what exactly does "rollback" do, and why is it so cheap?

**Answer:** It sets the canary's traffic weight to **0%**. The stable version was never removed — it kept serving the majority of traffic the whole time — so reverting is a single routing/weight change with no redeploy. That is precisely why canary + automated triggers is such a safe pattern: the known-good version is always one step away.

---

## 13. How do these strategies fit into the overall CI/CD pipeline?

**Answer:** After the build, tests, and AI eval gate pass and a container is published: deploy to **staging**, run smoke tests and synthetic traffic, then deploy to **production** via **canary** with automated monitoring. The canary's auto-promote/auto-rollback logic is the last safety net — it catches regressions that slipped through pre-deploy testing using *live* production signals, including quality.

---

## Summary

Package once with multi-stage, non-root, secret-free containers; provision surroundings with IaC for reproducibility and audit; roll out gradually (blue-green for instant flip, canary for graduated exposure, shadow for zero-risk observation); manage environments with one image + injected config and progressive strictness; and automate metric-driven rollback — including an AI-specific quality signal — so a bad release reverts in one traffic-weight change.
