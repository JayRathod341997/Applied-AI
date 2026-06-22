# CI/CD on AWS for GenAI

The first three subtopics taught CI/CD *patterns* — versioning, testing, gradual rollout, automated rollback — with mostly Azure-flavoured examples. This subtopic re-grounds those same patterns in **AWS**, since in practice you ship on a concrete cloud. It is deliberately scoped to the handful of services you actually touch building a GenAI pipeline, grouped by the job each one does: the model/LLM layer (SageMaker, Bedrock), the CI/CD automation layer (CodePipeline, CodeBuild, CodeDeploy), the runtime/packaging layer (ECR, ECS/Fargate, Lambda), and the storage/IaC/observability layer (S3, CloudFormation/CDK, CloudWatch). Throughout, each AWS service is mapped back to the concept (and Azure equivalent) you already met, so this is a translation layer, not a fresh start.

## Topics

- The model & LLM layer: SageMaker Model Registry (approval-gated promotion), pipelines, endpoints with variant weights; Bedrock managed foundation models, versioned prompts, and guardrails
- CI/CD automation: CodePipeline (orchestration), CodeBuild (build + the AI eval gate via `buildspec.yml`), CodeDeploy (release)
- CodeDeploy deployment configurations: `AllAtOnce`, `Canary…`, `Linear…` as named, declarative canary/linear strategies with CloudWatch-alarm auto-rollback
- Runtime & packaging: ECR (immutable tags, scan-on-push) and choosing Fargate vs Lambda for GenAI workloads
- Storage, IaC & observability: S3 as the versioned artifact backbone (DVC remote), CloudFormation/CDK (vs Terraform), and CloudWatch metrics/alarms closing the rollback loop

## Files in this subtopic

- `concepts.md` — the teaching content: the reference AWS pipeline, ASCII diagrams, service-comparison tables, and focused `boto3`/`buildspec`/CDK snippets for every topic above.
- `quiz.md` — multiple-choice questions with answers and explanations to check your understanding.
- `exercise_01.md` — the brief for the hands-on coding exercise (an AWS CodeDeploy-style traffic-shift deployer with alarm-driven rollback).
- `exercise.py` — a runnable starter scaffold with provided deployment configs and mock alarms; you fill in the `# TODO` sections.
- `solution.py` — the complete, offline, fully-tested reference implementation of the deployer.
- `interview.md` — interview questions and model answers on AWS CI/CD for GenAI.
- `references.md` — curated links to authoritative AWS docs for deeper study.

## Start

Begin with `concepts.md`, then test yourself with `quiz.md`, and finally build the deployer in `exercise.py` (checking against `solution.py`).
