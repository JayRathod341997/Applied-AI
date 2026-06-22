# CI/CD on AWS for GenAI — Concepts

The earlier subtopics taught the *patterns* — versioning, testing, gradual rollout, automated rollback — using mostly Azure-flavoured examples. This subtopic re-grounds those same patterns in the **AWS** ecosystem, because in practice you ship on a concrete cloud. We focus on the handful of services you will actually touch building a GenAI CI/CD pipeline, grouped by the job they do:

| Job in the pipeline | AWS services covered here |
|---|---|
| **Model & LLM layer** | Amazon **SageMaker** (registry, pipelines, endpoints), Amazon **Bedrock** (managed foundation models) |
| **CI/CD automation** | AWS **CodePipeline**, **CodeBuild**, **CodeDeploy** |
| **Runtime / packaging** | Amazon **ECR**, **ECS/Fargate**, AWS **Lambda** |
| **Storage, IaC, observability** | Amazon **S3**, AWS **CloudFormation/CDK**, Amazon **CloudWatch** |

The through-line: the *concepts* don't change between clouds — only the service names and the exact knobs do. Wherever a service maps to an Azure equivalent you already saw, the text calls it out.

```
   ┌──────────┐   ┌───────────┐   ┌────────────┐   ┌──────────────┐
   │  S3 / Git│──►│CodePipeline│──►│ CodeBuild  │──►│  ECR  (image)│
   │ (source) │   │ (orchestr) │   │(build+test)│   │ SageMaker reg│
   └──────────┘   └───────────┘   └────────────┘   └──────┬───────┘
                                                          │ deploy
                                          ┌───────────────▼───────────────┐
                                          │  CodeDeploy  (canary/linear)   │
                                          │  ECS/Fargate · Lambda · SM ep  │
                                          └───────────────┬───────────────┘
                                          CloudWatch alarms│ breach → rollback
                                          ◄────────────────┘
```

---

## 1. The Model & LLM Layer — SageMaker and Bedrock

A GenAI system either **hosts its own models** (fine-tuned, open-weight) or **calls a managed foundation model** (or both). On AWS those two paths are SageMaker and Bedrock.

### Amazon SageMaker — your own models, versioned and deployed

SageMaker is the rough AWS analogue of **Azure ML** (subtopic 01). The three pieces that matter for CI/CD:

| Piece | What it does | Maps to |
|---|---|---|
| **Model Registry** | Immutable, versioned `Model Packages` grouped in a *Model Package Group*; each has an **approval status** (`PendingManualApproval` → `Approved`/`Rejected`) and full lineage | MLflow / Azure ML registry stages |
| **Pipelines** | DAG of steps (process → train → evaluate → register) defined in code; the eval step can **gate registration** on a metric | Azure ML pipelines |
| **Endpoints** | Hosted inference; supports **production variants** with traffic weights and **shadow variants** | Azure ML online endpoints |

The registry is the heart of versioning: every candidate model becomes an immutable, numbered Model Package, and **approval is the promotion gate** — CI registers a package as `PendingManualApproval`, an automated eval (or a human) flips it to `Approved`, and only `Approved` packages are eligible to deploy. Rollback = deploy the previous `Approved` package version.

```python
# Register a candidate model package (CI step) — boto3 sketch
import boto3
sm = boto3.client("sagemaker")

sm.create_model_package(
    ModelPackageGroupName="rag-reranker",
    ModelApprovalStatus="PendingManualApproval",   # gate, not yet deployable
    InferenceSpecification={...},                   # image + S3 model artifact
    ModelMetrics={...},                             # eval scores attached as lineage
)
# An eval job (or reviewer) later approves it:
# sm.update_model_package(ModelPackageArn=arn, ModelApprovalStatus="Approved")
```

SageMaker **endpoints** give you the rollout primitive directly: an endpoint can serve two **production variants** with traffic weights (canary/blue-green), or a **shadow variant** that receives a copy of traffic but returns nothing to users — exactly the shadow pattern from subtopic 03, built in.

```bash
# Shift 10% of live traffic to a new variant (canary on a SageMaker endpoint)
aws sagemaker update-endpoint-weights-and-capacities \
  --endpoint-name rag-reranker \
  --desired-weights-and-capacities \
      VariantName=stable,DesiredWeight=90 \
      VariantName=candidate,DesiredWeight=10
```

### Amazon Bedrock — managed foundation models

Bedrock serves foundation models (Anthropic Claude, Amazon Titan, Llama, etc.) behind one API — no infra to manage. For CI/CD the versionable, promotable artifacts are different from "model weights":

| Bedrock artifact | What you version / promote |
|---|---|
| **Model ID + version** | Pin an explicit model version (e.g. a dated Claude id), don't float to "latest" — a silent model upgrade is an unreviewed prod change |
| **Inference profiles** | Route to a model across regions; swap the profile to change routing without touching app code |
| **Prompt management / versions** | Bedrock can store **versioned prompts** — the registry-backed prompt versioning of subtopic 01, managed |
| **Provisioned throughput** | Reserved capacity; a deployment concern (cost + rate limits per environment) |
| **Guardrails** | Versioned content-filter/policy configs attached at invoke time |

> **GenAI-specific rule:** treat the *model id/version*, the *prompt version*, and the *guardrail version* as a single deployable bundle. Pinning the model but floating the prompt (or vice-versa) reintroduces exactly the "which combination is in prod?" problem versioning was meant to solve.

When you build a new GenAI app on AWS, default to the **latest, most capable Claude model on Bedrock** and pin its explicit version id so upgrades are deliberate, reviewed changes.

---

## 2. CI/CD Automation — CodePipeline, CodeBuild, CodeDeploy

These three are AWS's native CI/CD trio (the rough analogue of **GitHub Actions / Azure DevOps** from subtopic 02). They divide cleanly:

| Service | Role | One-liner |
|---|---|---|
| **CodePipeline** | Orchestrator | The pipeline *definition*: stages, order, approvals, what triggers what |
| **CodeBuild** | Worker | Runs a build/test job in a container per a `buildspec.yml` |
| **CodeDeploy** | Releaser | Shifts traffic to a new version (canary/linear/all-at-once) with alarm-based rollback |

```
 Source ──► Build ───────► Eval-Gate ──► Approval ──► Deploy
(CodePipeline stage)                    (manual or                (CodeDeploy)
            │                            CloudWatch)
            └─ CodeBuild: lint, unit, prompt-regression (subtopic 02)
```

**CodeBuild** is where the **AI quality gate** lives. A `buildspec.yml` runs your prompt-regression / golden-set evaluation and **fails the build below a pass-rate threshold** — the exact gate built in subtopic 02, now expressed as a build phase:

```yaml
# buildspec.yml — the AI eval gate as a CodeBuild phase
version: 0.2
phases:
  install:
    runtime-versions: { python: 3.11 }
    commands: [ pip install -r requirements.txt ]
  build:
    commands:
      - pytest tests/unit                       # fast, deterministic
      - python eval/run_golden_set.py --min-pass-rate 0.90   # AI gate: exits non-zero below 90%
artifacts:
  files: [ imagedefinitions.json ]              # handed to the deploy stage
```

**CodeDeploy** owns the rollout. Its *deployment configurations* are named traffic-shift strategies — and this is the single most important AWS-specific idea in this subtopic, so it gets its own section below.

A **manual approval** action in CodePipeline (often gated on a CloudWatch alarm or an eval result) is how you implement the "production needs approval" row from subtopic 03's environment table.

---

## 3. CodeDeploy Deployment Configurations — canary & linear, named

Subtopic 03 taught canary as a hand-rolled controller. AWS CodeDeploy gives you the same behaviour as **declarative, named configurations** — you pick a strategy and CodeDeploy shifts the traffic and watches the alarms for you.

| Deployment config | Traffic shift schedule | Pattern (subtopic 03) |
|---|---|---|
| `AllAtOnce` | 100% immediately | All-at-once cutover |
| `Canary10Percent5Minutes` | 10% now, hold 5 min, then 100% | **Canary** (two-step) |
| `Canary10Percent30Minutes` | 10% now, hold 30 min, then 100% | Canary (longer bake) |
| `Linear10PercentEvery1Minute` | +10% each minute → 100% over ~10 min | **Linear** (graduated ramp) |
| `Linear10PercentEvery3Minutes` | +10% every 3 min | Linear (slower) |

```
 Canary10Percent5Minutes          Linear10PercentEvery1Minute
   100%┤        ┌────────           100%┤              ┌──
       │        │                       │          ┌───┘
    10%┤────────┘  (bake 5m)         10%┤──┬──┬──┬──┘
       └────────┴────────►              └──┴──┴──┴────────►
        t=0    t=5  time                 +10% each minute
```

The deploy targets differ by runtime but the *config* is the same idea:

- **ECS/Fargate** + CodeDeploy → blue-green: spins up a new task set, shifts ALB traffic per the config.
- **Lambda** + CodeDeploy → shifts traffic between two function **aliases/versions** per the config.
- **SageMaker endpoints** → variant weights (the `update-endpoint-weights-and-capacities` call above) achieve the canary manually.

The rollback trigger is wired declaratively: attach **CloudWatch alarms** to the deployment group. If an alarm enters `ALARM` *during* the shift, CodeDeploy **automatically rolls back** to the previous version — the "previous version is one step away" property from subtopic 03, managed for you. This is exactly the loop you implement (offline) in this subtopic's exercise.

```json
// CodeDeploy deployment group — auto-rollback on alarm (excerpt)
{
  "deploymentConfigName": "Canary10Percent5Minutes",
  "alarmConfiguration":   { "enabled": true, "alarms": [{ "name": "rag-5xx-high" }] },
  "autoRollbackConfiguration": {
    "enabled": true,
    "events": ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM"]
  }
}
```

> For LLM apps, the alarm must include a **quality** metric (a custom CloudWatch metric like golden-set pass-rate or an LLM-as-judge score on sampled traffic), not just 5xx and latency — the dangerous regressions return `200 OK` with worse answers (subtopic 03, §4).

---

## 4. Runtime & Packaging — ECR, ECS/Fargate, Lambda

Once CodeBuild produces an image, it needs a home and a runtime.

### Amazon ECR — the image registry

ECR is the AWS container registry (analogue of Azure Container Registry / Docker Hub). CI/CD essentials:

- **Immutable tags** — turn on tag immutability so a tag (e.g. a git SHA) can never be overwritten; "which bytes are `:v1.4`?" must have one answer (the byte-level versioning point from subtopic 01).
- **Image scanning** — enable scan-on-push (Amazon Inspector / basic scan) — the `trivy`-equivalent gate from subtopic 03.
- **Lifecycle policies** — auto-expire old/untagged images so the registry doesn't grow without bound.

Reference images by **digest** (`@sha256:...`), not by a floating tag, when you want a deployment to be perfectly reproducible.

### Choosing a runtime — Fargate vs Lambda

| | **ECS on Fargate** | **AWS Lambda** |
|---|---|---|
| **Model** | Long-running container | Event-driven function (also container images up to 10 GB) |
| **Cold start** | Warm once running | Cold start per idle scale-up |
| **Max duration** | Unbounded | 15 min hard cap |
| **Best for GenAI** | Persistent inference servers, heavy/large model containers, streaming responses | Lightweight orchestration, RAG glue, async/batch, spiky low-volume traffic |
| **Scale-to-zero** | No (min tasks) | Yes |
| **Rollout** | CodeDeploy blue-green via ALB | CodeDeploy traffic-shift via aliases |

Rule of thumb for GenAI: a **stateful, GPU/large-memory or streaming** inference service → Fargate (or EKS/SageMaker for GPUs); **glue, routing, and bursty/low-volume** logic that calls Bedrock → Lambda. Both deploy through CodeDeploy with the same canary/linear configs.

```
 Spiky, short, calls Bedrock  ─────►  Lambda  (scale-to-zero, pay-per-call)
 Steady, heavy, self-hosted   ─────►  Fargate / EKS / SageMaker endpoint
```

---

## 5. Storage, IaC & Observability — S3, CloudFormation/CDK, CloudWatch

### Amazon S3 — the artifact backbone

S3 is everywhere in an AWS GenAI pipeline:

- **DVC / large-artifact remote** — the "bytes" half of the Git+DVC split from subtopic 01 (`dvc remote add -d storage s3://bucket/path`). Git holds pointers; S3 holds the model/embedding bytes.
- **Pipeline artifacts** — CodePipeline passes build outputs between stages via an S3 artifact bucket.
- **Model artifacts** — SageMaker reads/writes `model.tar.gz` to S3.
- **Vector-store snapshots / embeddings** — versioned with **bucket versioning** on, so an embedding index is reproducible and rollback-able.

Turn on **versioning** and a sensible lifecycle policy; an immutable, versioned object store is what makes "reproduce any version we ever shipped" true.

### CloudFormation & CDK — Infrastructure as Code on AWS

The AWS-native IaC stack (analogue of **Bicep** for Azure; **Terraform** still works on AWS and is the multi-cloud option from subtopic 03):

| | **CloudFormation** | **AWS CDK** |
|---|---|---|
| **Authoring** | YAML/JSON templates | Real code (Python/TS/…) that *synthesizes* CloudFormation |
| **State** | AWS-managed (stacks) | AWS-managed (synth → CFN) |
| **Drift detection** | Built-in drift detection | Via CFN |
| **Best for** | Declarative, no extra tooling | Loops/conditionals, sharing constructs, typed infra |

```python
# AWS CDK (Python) — a Lambda behind an API, infra as reviewable code
from aws_cdk import aws_lambda as _lambda, Stack
class RagStack(Stack):
    def __init__(self, scope, id, **kw):
        super().__init__(scope, id, **kw)
        _lambda.Function(self, "RagFn",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="app.handler",
            code=_lambda.Code.from_asset("src"),
            environment={"BEDROCK_MODEL_ID": "anthropic.claude-..."},  # pinned, not 'latest'
        )
```

Same golden rule as subtopic 03: **never hand-provision production** — if it's not in a template/stack, it can't be reviewed, reproduced, or rolled back.

### CloudWatch — metrics, alarms, and the rollback trigger

CloudWatch is the observability plane that *closes the CI/CD loop*:

- **Metrics** — built-in (5xx, latency, invocation errors, throttles) plus **custom metrics** you publish (token spend, golden-set pass-rate, LLM-judge score).
- **Alarms** — threshold rules on those metrics; an alarm in `ALARM` state is the signal CodeDeploy watches to **auto-rollback** (§3).
- **Logs / Logs Insights** — structured request/trace logs for debugging regressions.

| Rollback trigger (subtopic 03) | CloudWatch implementation |
|---|---|
| Error-rate spike | Alarm on `5xx` / `Errors` > threshold over N min |
| P99 latency | Alarm on `p99` latency metric |
| **Quality drop** | Alarm on a **custom** `GoldenSetPassRate` metric < threshold |
| **Cost anomaly** | Alarm on a **custom** `TokenSpend` metric > 2× baseline |

```bash
# A custom quality metric feeding the rollback alarm
aws cloudwatch put-metric-data \
  --namespace "RagApp" --metric-name "GoldenSetPassRate" \
  --value 0.88 --unit Percent
# An alarm on it (created once via IaC) is attached to the CodeDeploy group → auto-rollback if it fires
```

This is the full circle: **CloudWatch alarm fires → CodeDeploy shifts traffic back to the previous version → no human at 3 a.m. required.**

---

## Putting it together — a reference GenAI pipeline on AWS

```
 1. Source     git push  /  s3 artifact            (CodePipeline: Source stage)
 2. Build      buildspec.yml: unit + prompt-regression eval gate   (CodeBuild)
                 │  image ──► ECR (immutable tag, scan-on-push)
                 │  model  ──► SageMaker Model Registry (PendingManualApproval)
 3. Gate       eval pass-rate ≥ threshold + manual approval        (CodePipeline)
 4. Deploy     Canary10Percent5Minutes to Fargate / Lambda / SM    (CodeDeploy)
 5. Watch      CloudWatch alarms: 5xx, p99, GoldenSetPassRate, cost
                 └─ ALARM ──► auto-rollback to previous version
 (infra everywhere defined in CloudFormation / CDK; artifacts in S3)
```

---

## Key Takeaways

- **SageMaker** versions/promotes your *own* models (Model Registry + approval gate, endpoints with variant weights for canary/shadow); **Bedrock** serves managed foundation models — pin the **model version + prompt version + guardrail** as one deployable bundle; default to the latest Claude on Bedrock.
- **CodePipeline / CodeBuild / CodeDeploy** are the native CI/CD trio: CodePipeline orchestrates, CodeBuild runs the build + **AI eval gate** (`buildspec.yml`), CodeDeploy releases.
- **CodeDeploy deployment configurations** (`Canary…`, `Linear…`, `AllAtOnce`) are canary/linear rollout as *named, declarative* strategies, with **CloudWatch-alarm auto-rollback** — the controller from subtopic 03, managed.
- **ECR** stores images (immutable tags, scan-on-push); choose **Fargate** for steady/heavy/streaming inference and **Lambda** for spiky glue and Bedrock orchestration.
- **S3** is the versioned artifact backbone (DVC remote, pipeline + model artifacts); **CloudFormation/CDK** are AWS-native IaC (Terraform = multi-cloud); **CloudWatch** custom metrics + alarms close the loop by triggering rollback — including an LLM **quality** signal, not just 5xx/latency.
