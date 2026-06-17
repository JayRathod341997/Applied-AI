# Quiz

## Question 1

Why use a multi-stage Docker build for an LLM application?

A) To run the app in multiple containers at once
B) To reduce final image size by leaving build dependencies out of the production stage
C) To support multiple programming languages
D) To deploy to multiple regions

---

**Answer: B**

A builder stage installs/compiles dependencies; the production stage copies only the artifacts it needs, discarding build tools. The result is a smaller image with a reduced attack surface and faster pulls.

---

## Question 2

Which is a container security best practice for production LLM apps?

A) Run as root for convenience
B) Bake the API key into the image so it's always available
C) Run as a non-root user and inject secrets via env vars / a secret manager
D) Use the largest possible base image

---

**Answer: C**

Run as non-root and keep secrets out of the image (they would otherwise live forever in a layer). Use a minimal base image, pin dependencies, and scan the image.

---

## Question 3

You want a small image but can tolerate a slower first request. Which model-weight strategy fits?

A) Bake weights into the image at build time
B) Fetch weights at runtime when the container starts
C) Never load weights
D) Email the weights to the container

---

**Answer: B**

Fetching at runtime keeps the image small at the cost of a slower cold start. Baking at build gives the opposite trade-off (large, self-contained image, slow builds).

---

## Question 4

What is the primary benefit of Infrastructure as Code?

A) It makes the app run faster
B) Reproducible, auditable, version-controlled infrastructure with drift detection
C) It removes the need for any cloud provider
D) It encrypts all network traffic automatically

---

**Answer: B**

IaC declares resources as code, so environments are reproducible, changes go through review/Git history (auditable), and tools like `terraform plan` reveal drift between desired and actual state.

---

## Question 5

Which statement correctly distinguishes Terraform from Bicep?

A) Terraform is Azure-only; Bicep is multi-cloud
B) Terraform is multi-cloud (HCL); Bicep is Azure-native (compiles to ARM)
C) They are identical
D) Bicep cannot detect drift at all

---

**Answer: B**

Terraform is cloud-agnostic and uses HCL with its own state file. Bicep is a Microsoft DSL that compiles to ARM templates and is tightly integrated with Azure's managed state.

---

## Question 6

What is the key advantage of a blue-green deployment?

A) It uses the least compute
B) Instant rollback by flipping traffic back to the previous environment
C) It automatically fixes bugs
D) It requires no infrastructure

---

**Answer: B**

Blue-green keeps two identical environments; switching is one routing change, so rollback is instant (flip back to blue). The downside is that the cutover is all-or-nothing.

---

## Question 7

How does a canary deployment differ from blue-green?

A) Canary moves all users at once; blue-green moves them gradually
B) Canary routes a small % of traffic to the new version and ramps up gradually while watching metrics
C) Canary requires no monitoring
D) They are the same

---

**Answer: B**

Canary exposes the new version to a small traffic slice first, then ramps up only if metrics stay healthy (or shifts back to 0% if not). Blue-green is an instant, all-or-nothing flip.

---

## Question 8

What is a shadow (dark launch) deployment?

A) Deploying without monitoring
B) Routing duplicate traffic to the new version without serving its responses to users
C) Deploying to a hidden region
D) Running in debug mode

---

**Answer: B**

Shadow deployment sends a copy of live traffic to the new version for observation, but users still receive responses from the stable version — letting you test with real traffic at zero user-facing risk.

---

## Question 9

In a canary controller, what happens when the observed error rate exceeds the threshold?

A) Traffic is ramped up faster to "push through" the errors
B) The canary weight is set to 0% (rollback), shifting traffic back to the stable version
C) The stable version is deleted
D) The threshold is automatically raised

---

**Answer: B**

Exceeding the error threshold triggers rollback: the canary weight goes to 0% so all traffic returns to the still-running stable version. Recovery is a single traffic-weight change.

---

## Question 10

Why should a canary for an LLM app monitor a quality signal, not just HTTP error rate and latency?

A) Quality signals are cheaper to compute
B) A model/prompt regression can return 200 OK with worse answers, which error-rate checks miss
C) Latency is never relevant for LLMs
D) HTTP errors don't exist for LLM apps

---

**Answer: B**

The dangerous LLM regressions succeed technically (`200 OK`) but degrade answer quality. Only a quality signal — e.g. a live golden-set pass-rate — catches them; error rate and latency would look fine.

---

## Question 11

How should configuration differ across dev, staging, and production with one container image?

A) Build a separate image per environment with hardcoded config
B) Use one image and inject environment-aware config (env vars / settings) per environment
C) Edit the running container by hand in production
D) Store production config in the source code

---

**Answer: B**

Build once, configure per environment: the same image runs everywhere and only injected config (model, log level, secrets source, replicas) changes. This keeps environments consistent and avoids drift between images.

---

## Question 12

Why must rollback be automated and metric-driven for AI applications?

A) AI apps never fail
B) Model behaviour is non-deterministic, so quality regressions may not appear in pre-deploy tests and need fast metric-based reversion in production
C) Manual rollback is always faster
D) Rollback only matters for databases

---

**Answer: B**

Because LLM outputs are probabilistic, a change can pass tests yet regress in production. Automated, threshold-driven rollback (error rate, latency, quality, cost) reverts before users are significantly impacted — far faster and more reliable than waiting for a human to notice.
