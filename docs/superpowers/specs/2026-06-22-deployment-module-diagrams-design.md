# Design — Enhance Module 12 (Deployment) with New Content + Diagrams

**Date:** 2026-06-22
**Target:** `gen-ai-course/12_deployment/`
**Goal:** Add new conceptual content and diagrams that visualize how a GenAI system actually runs in production, across four themes: request lifecycle & serving internals, scaling & reliability, release & rollback, and observability & cost.

---

## Background

Module 12 currently has 5 files (~5,200 lines total):

- `01_deployment_overview/README.md` (946 lines) — options, trade-offs, decision framework, one "Architecture Diagrams" section
- `02_deployment_techniques/README.md` (1,302 lines) — Docker, K8s, serverless, optimization, deployment strategies, CI/CD, monitoring, security, cost, load testing
- `03_deployment_implementation_with_azure/README.md` (1,283 lines) — Azure OpenAI, ACA, AKS, ML endpoints, Managed Identity, App Insights
- `03_.../04_deployment_with_aws_mlops/README.md` (990 lines) — Bedrock, SageMaker, Lambda, ECS/EKS, SageMaker Pipelines
- `interview.md` (658 lines) — Q&A prep

The content is rich in code but visually sparse. There are **no Mermaid diagrams anywhere in the entire `gen-ai-course/`** — existing visuals are ASCII box-art in the main README only. The dense, code-heavy files lack a coherent visual mental model of how production serving works end to end.

---

## Approach (chosen: A — new diagram-driven sub-module + light in-place diagrams)

Create one new sibling section that teaches the four themes conceptually and visually (home for the large Mermaid diagrams), and insert a small number of targeted diagrams into the existing technique/cloud files beside the code they explain. This matches "new content + diagrams throughout" while keeping the already-large existing files stable and giving the cross-cutting concepts a coherent home.

Rejected alternatives:
- **B — enhance everything in place:** pushes already-large files toward 1,800+ lines and scatters the cross-cutting mental model across four files.
- **C — pure visual companion file:** under-delivers on the "more content" request and divorces diagrams from explanation.

**Diagram format policy:** Mermaid for anything with branching/flow/sequence; ASCII only for tiny inline structures. Every Mermaid block gets a one-line caption above it.

---

## Deliverables

### 1. New sub-module: `05_production_operations/README.md`

Organized into four teaching sections. Each section = prose explanation + diagram(s) + a short "What this means in practice" callout + a "Maps to" line linking to concrete code in files 02/03/04.

1. **The Request Lifecycle** — how one inference request travels: client → API gateway → auth/rate-limit → request queue → continuous batching → GPU (KV-cache) → token stream back. Explains why batching and KV-cache exist.
2. **Scaling & Reliability** — autoscaling triggers (HPA on CPU/GPU, KEDA on queue depth, Karpenter node provisioning), scale-to-zero & cold starts, multi-region failover/HA, rate limiting.
3. **Release & Rollback** — blue-green vs canary vs rolling as traffic-shift diagrams, the CI/CD pipeline with automated quality gates, and a rollback decision flow.
4. **Observability & Cost** — metrics/logs/traces pipeline, dashboard layout, alert routing, token-spend tracking, cost attribution.

File ends with a "Key Takeaways" section and a prev/next footer matching the other sub-modules.

### 2. Diagram inventory

**In the new `05_production_operations/README.md`:**

| # | Diagram | Format | Section |
|---|---|---|---|
| 1 | Request lifecycle (client→gateway→queue→batch→GPU→stream) | Mermaid sequence | Request Lifecycle |
| 2 | Continuous batching vs static batching | Mermaid flowchart | Request Lifecycle |
| 3 | KV-cache / GPU memory layout | ASCII | Request Lifecycle |
| 4 | Autoscaling triggers (HPA / KEDA / Karpenter layers) | Mermaid flowchart | Scaling |
| 5 | Scale-to-zero + cold-start timeline | Mermaid sequence | Scaling |
| 6 | Multi-region failover / HA topology | Mermaid flowchart | Scaling |
| 7 | Blue-green vs canary vs rolling (traffic shift) | Mermaid (3 small graphs) | Release |
| 8 | CI/CD pipeline with quality gates | Mermaid flowchart | Release |
| 9 | Rollback decision flow | Mermaid flowchart | Release |
| 10 | Observability pipeline (metrics/logs/traces → store → dashboard/alert) | Mermaid flowchart | Observability |
| 11 | Dashboard layout (panels) | ASCII | Observability |
| 12 | Token-spend / cost attribution flow | Mermaid flowchart | Observability |

**Targeted in-place diagrams (inserted beside relevant code):**

- Canary traffic-shift (Mermaid) → `02_deployment_techniques` Deployment Strategies section
- KEDA scaling-trigger (Mermaid) → `03_azure` AKS/KEDA section
- SageMaker endpoint + autoscaling (Mermaid) → `04_aws_mlops`

Total: ~12 diagrams in the new file + ~3–4 in-place = **~15–16 diagrams**.

### 3. Navigation updates — `12_deployment/README.md`

- Add `05_production_operations/` to the Module Map tree with a one-line description.
- Insert a "Step 2.5 — Production Operations" box into the ASCII Learning Path between Step 2 (Techniques) and Step 3 (Azure/AWS).
- Add one row to the Estimated Time table (~1.5–2 hours; update total).

### 4. Interview prep — `interview.md`

Add ~6 new Q&A covering the new themes:
- Walk me through what happens to an inference request from gateway to response.
- Why continuous batching over static batching?
- HPA vs KEDA vs Karpenter — when does each apply?
- How do you roll back a bad model deployment safely?
- What metrics matter most for an LLM service?
- How do you attribute token cost per customer?

### 5. Cross-linking

- New file's "Maps to" lines link into 02/03/04.
- The three in-place diagrams link back to the relevant `05_production_operations` section for the deep explanation.

---

## Verification

- **Mermaid validity:** every Mermaid block uses valid fence syntax and node/edge grammar that renders on GitHub.
- **Links:** every new relative link resolves to a real file/anchor (no broken links).
- **Consistency:** tone and format match existing files — H2 sections, captioned diagrams, "Key Takeaways" section, prev/next footer.

---

## Out of Scope (YAGNI)

- No new runnable code or repositories.
- No binary image files — all diagrams are text-based Mermaid/ASCII.
- No changes to existing cloud code samples beyond adding diagrams beside them.
- No changes to other modules in `gen-ai-course/`.
