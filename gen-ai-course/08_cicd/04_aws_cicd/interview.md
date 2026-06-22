# CI/CD on AWS for GenAI — Interview Questions

Interview questions and model answers on building a GenAI CI/CD pipeline with the core AWS services — SageMaker/Bedrock, CodePipeline/CodeBuild/CodeDeploy, ECR/Fargate/Lambda, and S3/CloudFormation/CloudWatch.

---

## 1. Sketch a CI/CD pipeline for a GenAI app on AWS, end to end.

**Answer:** Source (git/S3) triggers **CodePipeline**. A **CodeBuild** stage runs unit tests and the **AI eval gate** (prompt-regression / golden-set) via `buildspec.yml`, pushes the image to **ECR** (immutable tag, scan-on-push), and registers any custom model in the **SageMaker Model Registry** as `PendingManualApproval`. A gate stage requires the eval pass-rate to clear a threshold plus (optionally) a manual approval. **CodeDeploy** then releases to **Fargate/Lambda/SageMaker endpoint** using a canary or linear deployment configuration, while **CloudWatch** alarms (5xx, p99, and a custom quality metric) watch the rollout and **auto-rollback** on breach. All infra is defined in **CloudFormation/CDK**; artifacts live in **S3**.

---

## 2. How do CodePipeline, CodeBuild, and CodeDeploy divide responsibilities?

**Answer:** **CodePipeline** is the orchestrator — it defines the stages, their order, triggers, and approval actions. **CodeBuild** is the worker — it runs a build/test job in a container per a `buildspec.yml` (this is where the AI quality gate lives). **CodeDeploy** is the releaser — it shifts traffic to the new version per a named deployment configuration and rolls back automatically on a CloudWatch alarm. Roughly: Pipeline = "what runs and in what order", Build = "compile + test", Deploy = "release safely".

---

## 3. Explain the SageMaker Model Registry and how it gates promotion.

**Answer:** The registry groups **immutable, versioned model packages** into a Model Package Group with full lineage (which data, code, and metrics produced each). Each package has an **approval status**: CI registers a candidate as `PendingManualApproval`; an automated evaluation step (or a human) sets it to `Approved` or `Rejected`. Only `Approved` packages are eligible to deploy, so approval *is* the promotion gate — the AWS analogue of MLflow/Azure ML registry stages. Rollback is simply deploying the previous `Approved` version.

---

## 4. Where do SageMaker and Bedrock each fit, and what do you version on Bedrock?

**Answer:** **SageMaker** is for models *you* host (fine-tuned/open-weight): registry, training pipelines, and endpoints. **Bedrock** serves managed foundation models (Claude, Titan, Llama) behind one API with no infra. On Bedrock the versionable/promotable artifacts aren't weights but the **model id + version** (pin it, don't float to "latest"), **prompt versions** (Bedrock prompt management), **guardrail versions**, and **provisioned throughput** (a cost/rate concern). Treat model + prompt + guardrail as one deployable bundle so production behaviour is reproducible.

---

## 5. What are CodeDeploy deployment configurations, and how do they map to canary/linear?

**Answer:** They are named traffic-shift schedules. `AllAtOnce` flips 100% immediately (all-or-nothing). `Canary10Percent5Minutes` sends 10% for a 5-minute bake then jumps to 100% — a two-step canary. `Linear10PercentEvery1Minute` adds 10% each minute until 100% — a graduated ramp. They turn the hand-rolled canary controller from subtopic 03 into a declarative choice; CodeDeploy performs the shift and watches the alarms for you.

---

## 6. How does automated rollback actually work on AWS?

**Answer:** You attach **CloudWatch alarms** to the CodeDeploy deployment group and enable auto-rollback (on `DEPLOYMENT_FAILURE` / `DEPLOYMENT_STOP_ON_ALARM`). While traffic is shifting, if any attached alarm enters `ALARM`, CodeDeploy stops and reverts to the previous version automatically. The previous version is never torn down mid-shift, so reverting is just a traffic change — no human at 3 a.m. required. For LLM apps, include a **custom quality alarm** (golden-set pass-rate / LLM-judge score), not only 5xx and latency.

---

## 7. Why must an LLM rollout monitor more than 5xx and latency on AWS?

**Answer:** The most damaging LLM regressions succeed *technically* — fast `200 OK` responses — but degrade answer quality, so 5xx and latency alarms stay green. You publish a **custom CloudWatch metric** (e.g. `GoldenSetPassRate` or an LLM-as-judge score on sampled traffic) with `put-metric-data`, alarm on it falling below a threshold, and attach that alarm to the CodeDeploy group so quality breaches trigger rollback just like errors do.

---

## 8. Fargate or Lambda for a GenAI workload — how do you decide?

**Answer:** **Lambda** for spiky, short (≤15 min), event-driven glue/orchestration — especially logic that mostly calls Bedrock — because it scales to zero and bills per call. **Fargate (ECS)** for steady, heavy, large-memory/GPU, or streaming inference that needs a long-running container. (For GPUs at scale, EKS or SageMaker endpoints.) Both deploy through CodeDeploy with the same canary/linear configs, so the rollout story is consistent regardless of runtime.

---

## 9. What ECR settings matter for a reproducible, secure pipeline?

**Answer:** Enable **tag immutability** so a tag (e.g. a git SHA) maps to exactly one image forever — no silent overwrites. Enable **scan-on-push** (Inspector/basic) as the container vulnerability gate. Add **lifecycle policies** to expire old/untagged images. For deployments that must be byte-identical, reference images by **digest** (`@sha256:…`) rather than a mutable tag.

---

## 10. How is S3 used across the pipeline?

**Answer:** As the versioned artifact backbone: the **DVC remote** for large model/embedding bytes (the "bytes" half of Git+DVC, with Git holding pointers), the **artifact store** CodePipeline uses to pass outputs between stages, the home of SageMaker **model artifacts** (`model.tar.gz`), and **vector-index/embedding snapshots**. Turn on **bucket versioning** plus a lifecycle policy so any artifact you ever shipped can be retrieved and rolled back to.

---

## 11. CloudFormation, CDK, or Terraform on AWS — when each?

**Answer:** **CloudFormation** for declarative YAML/JSON templates with AWS-managed state and built-in drift detection — no extra tooling. **CDK** when you want real code (Python/TS) with loops, conditionals, and reusable typed constructs that synthesize to CloudFormation. **Terraform** when you need **multi-cloud** portability or the broad industry-standard ecosystem. All three make infrastructure reproducible, reviewable, and drift-detectable; the rule stays: never hand-provision production.

---

## 12. Map the core AWS services back to their Azure / generic equivalents.

**Answer:**

- SageMaker Model Registry ↔ Azure ML registry / MLflow (stages → approval status).
- Bedrock ↔ Azure OpenAI / managed foundation-model APIs.
- CodePipeline/CodeBuild/CodeDeploy ↔ Azure DevOps / GitHub Actions pipelines.
- ECR ↔ Azure Container Registry.
- Fargate/Lambda ↔ Azure Container Apps / Azure Functions.
- S3 ↔ Azure Blob Storage (DVC remote).
- CloudFormation/CDK ↔ Bicep (Terraform = multi-cloud).
- CloudWatch ↔ Azure Monitor / Application Insights.

The patterns — versioned artifacts, an AI eval gate, gradual rollout, alarm-driven rollback — are identical; only the service names and exact knobs change.

---

## Summary

A GenAI pipeline on AWS wires the same patterns you already know onto concrete services: version models in the **SageMaker registry** (approval = promotion) and pin **Bedrock** model+prompt+guardrail bundles; orchestrate with **CodePipeline**, gate quality in **CodeBuild**, and release with **CodeDeploy** using a canary/linear **deployment configuration**; package into **ECR** and run on **Fargate or Lambda**; back everything with versioned **S3** artifacts and **CloudFormation/CDK** infra; and close the loop with **CloudWatch** alarms — including an LLM quality metric — that auto-rollback the moment a release misbehaves.
