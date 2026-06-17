# Quiz

## Question 1

In a GenAI system, which set of things must MLOps treat as versioned artifacts, beyond what plain DevOps versions?

A) Only the application source code
B) Code, models, prompts, datasets, and retrieval indexes
C) Only the trained model weights
D) Only the prompts

---

**Answer: B**

GenAI behaviour is defined by a bundle of artifacts. A change to any of code, model, prompt, dataset, or index can alter the system's output, so all of them need versioning, testing, and rollback — not just the source code that DevOps tracks.

---

## Question 2

What is the most accurate relationship between DevOps, MLOps, and LLMOps?

A) They are three unrelated, competing practices
B) LLMOps replaces MLOps, which replaces DevOps
C) They are nested layers — MLOps adds model/data concerns to DevOps, and LLMOps adds prompt/token/eval concerns to MLOps
D) DevOps is only for AI; MLOps is only for web apps

---

**Answer: C**

The three are nested. You keep DevOps practices (CI/CD, IaC, observability) when you adopt MLOps, which adds the model and data lifecycle; LLMOps further specialises MLOps for prompts, tokens, and LLM evaluation.

---

## Question 3

Why is a "silent failure" a particular concern for GenAI systems compared to ordinary software?

A) The server crashes without logging anything
B) The model returns a plausible-looking but incorrect answer, with no error raised
C) The network drops the request
D) The database returns a 500 error

---

**Answer: B**

Ordinary software fails loudly (a crash or 5xx). A GenAI model can hallucinate — returning a confident, well-formed, *wrong* answer — without any exception, which is why quality monitoring (faithfulness, hallucination rate) is part of GenAI MLOps.

---

## Question 4

In the end-to-end GenAI lifecycle, which arrows make it a genuine *loop* rather than a one-way pipeline?

A) Data collection → preprocessing
B) Monitoring → iteration → back into data/prompt development
C) Model selection → deployment
D) Preprocessing → embedding

---

**Answer: B**

The feedback edges are what make it a lifecycle: production monitoring surfaces quality/cost/drift issues, which drive iteration, which feeds new data and prompts back into development. MLOps exists to make that loop fast and safe.

---

## Question 5

Why are prompts described as "code" in a GenAI MLOps practice?

A) Prompts are written in Python
B) A small prompt edit can change system behaviour and regress quality, so prompts need versioning, testing, and rollback like code
C) Prompts are compiled before deployment
D) Prompts are stored in the same file as the model weights

---

**Answer: B**

A one-word change to a prompt can materially change outputs and regress quality. Treating prompts as code means versioning them, running regression tests against a golden set, and being able to roll back — the same discipline applied to source code.

---

## Question 6

In the MLOps reference architecture, what role does the registry play?

A) It serves live inference requests
B) It is the single source of truth for versioned artifacts and tracks which version occupies each stage
C) It stores application logs
D) It compresses model weights

---

**Answer: B**

The registry is the hinge of the architecture: experimentation produces candidate artifacts, the registry holds immutable versions and records which one is in None/Staging/Production, pipelines deploy the promoted versions, and observability feeds quality back.

---

## Question 7

A registry exposes a stable name `"support-prompt"` whose Production stage currently points at version 4. What is the main benefit of addressing the artifact by *name + stage* rather than by a fixed version number?

A) It makes the artifact smaller
B) The runtime has a fixed address while the version underneath can change (or roll back) without a code change
C) It encrypts the artifact
D) It guarantees the model never changes

---

**Answer: B**

Name + stage gives the runtime a stable pointer. Releasing a new version or rolling back becomes "point Production at a different version" — a metadata change, not a redeploy or code change.

---

## Question 8

When you promote version 4 of an artifact to Production while version 3 already holds Production, what should a well-behaved registry do to version 3?

A) Delete version 3 permanently
B) Leave both at Production simultaneously
C) Demote version 3 (e.g. to Archived) so exactly one version holds Production
D) Promote version 3 to Staging

---

**Answer: C**

Exactly one version should occupy a given stage. Promoting v4 to Production must demote the previous holder (v3) — typically to Archived — so there is a single, unambiguous Production version and an auditable history.

---

## Question 9

Which monitoring signals are specific to GenAI MLOps that a plain DevOps dashboard would not track?

A) CPU utilization and disk space
B) Faithfulness / hallucination rate, retrieval quality, and per-request token cost
C) HTTP status codes
D) Server uptime

---

**Answer: B**

DevOps tracks uptime, latency, and error rates — still useful. GenAI MLOps adds quality metrics (faithfulness, hallucination rate, retrieval quality) and token-based cost, because those are the dimensions on which an LLM system actually succeeds or fails.

---

## Question 10

Why should most teams start with a managed/standard MLOps platform (e.g. MLflow, a cloud ML service) rather than building registries and pipelines from scratch?

A) Custom tooling is always slower at runtime
B) Standard platforms provide versioning, registry, stages, and experiment tracking out of the box, letting the team focus on the product
C) Building from scratch is impossible
D) Cloud platforms never cost anything

---

**Answer: B**

Established platforms already solve artifact versioning, stage promotion, experiment tracking, and lineage. Adopting them lets a team get the MLOps benefits immediately and spend its effort on the actual GenAI product rather than reinventing infrastructure.
