# References

### Model & LLM layer
- **Amazon SageMaker Model Registry** — register, version, and approve model packages: https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html
- **SageMaker Pipelines** — build, automate, and gate ML workflows: https://docs.aws.amazon.com/sagemaker/latest/dg/pipelines.html
- **SageMaker — Update endpoint variant weights** — canary/shadow on a live endpoint: https://docs.aws.amazon.com/sagemaker/latest/dg/model-ab-testing.html
- **Amazon Bedrock** — managed foundation models: https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html
- **Bedrock Prompt management** — versioned prompts as first-class artifacts: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-management.html
- **Bedrock Guardrails** — versioned content/policy filters: https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html

### CI/CD automation
- **AWS CodePipeline** — continuous delivery pipeline orchestration: https://docs.aws.amazon.com/codepipeline/latest/userguide/welcome.html
- **AWS CodeBuild — Build spec reference** — `buildspec.yml` phases, including test/eval gates: https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html
- **AWS CodeDeploy — Deployment configurations** — the built-in Canary/Linear/AllAtOnce strategies: https://docs.aws.amazon.com/codedeploy/latest/userguide/deployment-configurations.html
- **CodeDeploy — Redeploy and roll back** — automatic rollback on CloudWatch alarms: https://docs.aws.amazon.com/codedeploy/latest/userguide/deployments-rollback-and-redeploy.html

### Runtime & packaging
- **Amazon ECR — Image tag mutability** — immutable tags for reproducible references: https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html
- **Amazon ECR — Image scanning** — scan-on-push vulnerability detection: https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html
- **Amazon ECS / AWS Fargate** — serverless containers for long-running services: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html
- **AWS Lambda — Deploying with CodeDeploy (traffic shifting)** — alias/version traffic shifting: https://docs.aws.amazon.com/lambda/latest/dg/lambda-rolling-deployments.html

### Storage, IaC & observability
- **Amazon S3 — Using versioning in buckets** — versioned, reproducible artifacts: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html
- **DVC — Amazon S3 remote** — using S3 as the DVC large-artifact remote: https://dvc.org/doc/user-guide/data-management/remote-storage/amazon-s3
- **AWS CloudFormation** — declarative infrastructure as code: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html
- **AWS CDK Developer Guide** — define infra in code that synthesizes CloudFormation: https://docs.aws.amazon.com/cdk/v2/guide/home.html
- **Terraform — AWS Provider** — the multi-cloud IaC option on AWS: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **Amazon CloudWatch — Alarms** — threshold alarms that drive auto-rollback: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html
- **CloudWatch — Publishing custom metrics** — `put-metric-data` for quality/cost signals: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html

### Big picture
- **AWS Well-Architected — Operational Excellence Pillar** — CI/CD, deployment, and observability practices: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html
- **AWS — MLOps with SageMaker** — reference patterns for ML CI/CD on AWS: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-projects.html
