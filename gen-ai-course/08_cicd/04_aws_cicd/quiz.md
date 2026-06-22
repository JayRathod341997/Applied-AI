# Quiz

## Question 1

In the SageMaker Model Registry, what makes a registered model package eligible to deploy?

A) Being the most recently registered version
B) Its `ModelApprovalStatus` being set to `Approved`
C) Having the largest model artifact
D) Being stored in the default S3 bucket

---

**Answer: B**

Each model package is immutable and versioned, and carries an approval status. CI typically registers it as `PendingManualApproval`; an automated eval or a reviewer flips it to `Approved`, and only `Approved` packages are deployable. Promotion = approval; rollback = deploy the previous approved version.

---

## Question 2

You are building a new GenAI app on Amazon Bedrock. Which is the safest way to reference the foundation model?

A) Always use the "latest" alias so you get upgrades automatically
B) Pin an explicit model version id so upgrades are deliberate, reviewed changes
C) Hardcode the model into the container image
D) Pick a different model on each request

---

**Answer: B**

Floating to "latest" means a silent model upgrade becomes an unreviewed production change. Pin an explicit version id (and version the prompt and guardrail alongside it) so any model change goes through review. Default to the latest *capable* Claude model on Bedrock, but pin its explicit id.

---

## Question 3

Which AWS service runs the build and the AI quality gate (e.g. a prompt-regression / golden-set evaluation)?

A) CodePipeline
B) CodeDeploy
C) CodeBuild
D) CloudFormation

---

**Answer: C**

CodeBuild runs build/test jobs per a `buildspec.yml`. The AI eval gate lives here as a build phase that exits non-zero below a pass-rate threshold — failing the build. CodePipeline *orchestrates* stages; CodeDeploy *releases*.

---

## Question 4

What does the CodeDeploy deployment configuration `Canary10Percent5Minutes` do?

A) Shifts 10% of traffic permanently and never goes further
B) Sends 10% of traffic, holds for 5 minutes, then shifts the remaining 90% to reach 100%
C) Adds 10% every 5 minutes until 100%
D) Deploys to 10 regions over 5 minutes

---

**Answer: B**

A canary config holds a small percentage for a bake interval, then jumps the rest to 100%. (Contrast with a `Linear…` config, which adds a fixed percentage at each interval.) During the bake, CloudWatch alarms decide whether it proceeds or rolls back.

---

## Question 5

How does CodeDeploy trigger an automatic rollback during a deployment?

A) A human clicks "rollback" in the console
B) A CloudWatch alarm attached to the deployment group enters the `ALARM` state mid-shift
C) The image fails to build
D) Rollback cannot be automated

---

**Answer: B**

You attach CloudWatch alarms to the deployment group and enable auto-rollback. If an alarm fires while traffic is shifting, CodeDeploy reverts to the previous version automatically — the "previous version is one step away" property, managed for you.

---

## Question 6

For an LLM app, which CloudWatch alarm best catches a *quality* regression that error-rate and latency alarms would miss?

A) An alarm on CPU utilization
B) An alarm on 5xx error count
C) An alarm on a custom metric like `GoldenSetPassRate` falling below a threshold
D) An alarm on the number of deployments

---

**Answer: C**

The dangerous LLM regressions return `200 OK` quickly but produce worse answers, so 5xx/latency look healthy. You must publish a **custom** quality metric (golden-set pass-rate or an LLM-judge score on sampled traffic) and alarm on it to catch those.

---

## Question 7

What is the role of Amazon ECR in the pipeline, and which setting protects byte-level reproducibility?

A) It runs containers; enabling auto-scaling
B) It stores container images; enabling tag immutability so a tag can't be overwritten
C) It stores model weights; enabling encryption
D) It orchestrates deployments; enabling approvals

---

**Answer: B**

ECR is the container registry. Tag immutability ensures a tag (e.g. a git SHA) maps to exactly one set of bytes forever. Combine with scan-on-push (vulnerability scanning) and lifecycle policies to expire old images. Reference by digest for perfect reproducibility.

---

## Question 8

You have spiky, low-volume logic that mostly orchestrates calls to Bedrock and finishes in seconds. Which runtime fits best?

A) ECS on Fargate with a high minimum task count
B) AWS Lambda (scale-to-zero, pay-per-call)
C) A self-managed EC2 fleet always on
D) SageMaker real-time endpoint

---

**Answer: B**

Lambda scales to zero and bills per invocation — ideal for bursty, short, glue/orchestration work. Use Fargate (or EKS/SageMaker) for steady, heavy, GPU, or streaming inference servers. Both deploy through CodeDeploy with the same canary/linear configs.

---

## Question 9

How is Amazon S3 used as part of GenAI versioning on AWS?

A) As the compute layer for inference
B) As the DVC/large-artifact remote (the "bytes" half of Git+DVC) and for pipeline/model artifacts, ideally with bucket versioning on
C) Only for static website hosting
D) As a replacement for the model registry's approval gate

---

**Answer: B**

S3 holds the large bytes that Git can't: model artifacts, embeddings/index snapshots, and CodePipeline's inter-stage artifacts. With bucket versioning enabled, it makes "reproduce any version we ever shipped" true — Git stores pointers, S3 stores the bytes.

---

## Question 10

When would you choose Terraform over CloudFormation/CDK for AWS infrastructure?

A) Terraform only works on Azure
B) When you need multi-cloud / cross-provider portability and the industry-standard tooling
C) CloudFormation cannot detect drift, so always avoid it
D) CDK cannot use loops or conditionals

---

**Answer: B**

CloudFormation (declarative templates) and CDK (real code that synthesizes CloudFormation) are the AWS-native IaC options. Terraform is the multi-cloud, cloud-agnostic standard — pick it for portability across providers. All three give reproducible, reviewable, drift-detectable infrastructure; never hand-provision production.

---

## Question 11

What is the rough AWS equivalent of an Azure ML / MLflow model registry with promotion stages?

A) Amazon S3 buckets
B) The SageMaker Model Registry with approval status on immutable model packages
C) Amazon CloudWatch dashboards
D) AWS CodePipeline approval actions

---

**Answer: B**

The SageMaker Model Registry groups immutable, versioned model packages and uses approval status (`PendingManualApproval` → `Approved`/`Rejected`) as the promotion gate — the AWS analogue of registry stages with lineage. (CodePipeline approvals gate *pipeline* progression, a different layer.)

---

## Question 12

Why should the model id, prompt version, and guardrail version be treated as a single deployable bundle on Bedrock?

A) To reduce the number of API calls
B) Because pinning one while floating the others reintroduces the "which combination is in prod?" problem and makes regressions unreproducible
C) Because Bedrock requires it technically
D) To lower provisioned-throughput cost

---

**Answer: B**

Behaviour emerges from the *combination* of model, prompt, and guardrail. If you pin the model but let the prompt float (or vice-versa), you can't reproduce or cleanly roll back a given production behaviour — exactly the versioning failure mode subtopic 01 warned about. Version and promote them together.
