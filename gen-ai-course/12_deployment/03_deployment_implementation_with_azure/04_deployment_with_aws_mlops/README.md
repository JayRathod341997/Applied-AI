# Module 12.4 — Deployment with AWS & MLOps

Production deployment of GenAI models on AWS: from Amazon Bedrock to SageMaker MLOps pipelines.

---

## Table of Contents

1. [AWS GenAI Deployment Landscape](#aws-genai-deployment-landscape)
2. [Amazon Bedrock](#amazon-bedrock)
3. [SageMaker Real-Time Endpoints](#sagemaker-real-time-endpoints)
4. [SageMaker Serverless Inference](#sagemaker-serverless-inference)
5. [AWS Lambda for Lightweight Inference](#aws-lambda-for-lightweight-inference)
6. [ECS & EKS Container Deployment](#ecs--eks-container-deployment)
7. [MLOps with SageMaker Pipelines](#mlops-with-sagemaker-pipelines)
8. [Monitoring with CloudWatch & SageMaker Clarify](#monitoring-with-cloudwatch--sagemaker-clarify)
9. [Security: IAM Roles & Secrets Manager](#security-iam-roles--secrets-manager)
10. [End-to-End: Production RAG on AWS](#end-to-end-production-rag-on-aws)
11. [Cost Optimization on AWS](#cost-optimization-on-aws)

---

## AWS GenAI Deployment Landscape

```
┌──────────────────────────────────────────────────────────────────────┐
│                    AWS GenAI Deployment Options                       │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  MANAGED MODELS (AWS hosts everything)                         │  │
│  │  Amazon Bedrock                                                │  │
│  │  • Claude (Anthropic), Llama 3, Mistral, Titan, Cohere        │  │
│  │  • Managed RAG: Knowledge Bases for Bedrock                    │  │
│  │  • Managed Agents: Bedrock Agents                              │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  MANAGED COMPUTE (You bring model, AWS runs infra)             │  │
│  │  SageMaker Real-Time Endpoints (always-on, auto-scale)         │  │
│  │  SageMaker Serverless Inference (scale-to-zero)                │  │
│  │  SageMaker Async Inference (batch-like, long-running)          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  FULL CONTROL (You manage model + infra)                       │  │
│  │  EKS (Kubernetes with GPU node groups)                         │  │
│  │  ECS on EC2 (GPU-enabled container orchestration)              │  │
│  │  EC2 Bare Metal (p4d.24xlarge = 8x A100)                      │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Amazon Bedrock

The fastest path to foundation models on AWS — no infrastructure to manage.

### Architecture

```
Your VPC
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Application (Lambda / ECS / EC2)                       │
│       │                                                  │
│       │  IAM Role (no hardcoded keys)                   │
│       │  VPC Endpoint (private, no public internet)     │
│       ▼                                                  │
│  Amazon Bedrock                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Model Access (enable in console):               │    │
│  │    ✓ Claude 3.5 Sonnet (Anthropic)               │    │
│  │    ✓ Llama 3 70B (Meta)                          │    │
│  │    ✓ Mistral Large (Mistral AI)                  │    │
│  │    ✓ Amazon Titan Embeddings                     │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

### Python client (boto3)

```python
import boto3
import json

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")


def invoke_claude(prompt: str, system: str = "", max_tokens: int = 1024) -> str:
    """Invoke Claude via Amazon Bedrock."""
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
        body=json.dumps(body),
    )
    return json.loads(response["body"].read())["content"][0]["text"]


def invoke_claude_streaming(prompt: str):
    """Stream Claude response token by token."""
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = bedrock.invoke_model_with_response_stream(
        modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
        body=json.dumps(body),
    )
    for event in response["body"]:
        chunk = json.loads(event["chunk"]["bytes"])
        if chunk["type"] == "content_block_delta":
            yield chunk["delta"]["text"]


def embed_text(text: str) -> list[float]:
    """Embed text using Amazon Titan Embeddings."""
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps({"inputText": text, "dimensions": 1024}),
    )
    return json.loads(response["body"].read())["embedding"]


# Usage
print(invoke_claude("What is the capital of Japan?"))

for token in invoke_claude_streaming("Explain quantum computing."):
    print(token, end="", flush=True)
```

### Bedrock Agents (autonomous AI workflows)

```python
bedrock_agent = boto3.client("bedrock-agent-runtime", region_name="us-east-1")


def invoke_agent(agent_id: str, session_id: str, prompt: str) -> str:
    """Invoke a Bedrock Agent — it can use tools, query knowledge bases, etc."""
    response = bedrock_agent.invoke_agent(
        agentId=agent_id,
        agentAliasId="TSTALIASID",
        sessionId=session_id,
        inputText=prompt,
        enableTrace=True,
    )

    full_response = ""
    for event in response["completion"]:
        if "chunk" in event:
            chunk = event["chunk"]["bytes"].decode()
            full_response += chunk
        elif "trace" in event:
            # Inspect reasoning steps
            trace = event["trace"]["trace"]
            if "orchestrationTrace" in trace:
                thought = trace["orchestrationTrace"].get("rationale", {}).get("text", "")
                if thought:
                    print(f"[Agent reasoning]: {thought}")

    return full_response
```

### Knowledge Bases for Bedrock (managed RAG)

```python
bedrock_agent_kb = boto3.client("bedrock-agent-runtime", region_name="us-east-1")


def rag_retrieve_and_generate(query: str, kb_id: str, model_arn: str) -> dict:
    """Single-call RAG: retrieve from KB + generate with Claude."""
    response = bedrock_agent_kb.retrieve_and_generate(
        input={"text": query},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": kb_id,
                "modelArn": model_arn,
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {
                        "numberOfResults": 5,
                        "overrideSearchType": "HYBRID",
                    }
                },
                "generationConfiguration": {
                    "promptTemplate": {
                        "textPromptTemplate": (
                            "You are a helpful assistant. Use only the following context "
                            "to answer the question.\n\nContext:\n$search_results$\n\n"
                            "Question: $query$\n\nAnswer:"
                        )
                    }
                },
            },
        },
    )

    return {
        "answer": response["output"]["text"],
        "citations": [
            {
                "text": ref["content"]["text"],
                "location": ref["location"]["s3Location"]["uri"],
            }
            for citation in response.get("citations", [])
            for ref in citation.get("retrievedReferences", [])
        ],
    }
```

---

## SageMaker Real-Time Endpoints

Deploy your own fine-tuned models with SageMaker's managed inference infrastructure.

### Endpoint types

```
SageMaker Endpoint Types:

Real-Time Endpoint          Serverless Endpoint        Async Endpoint
├── Always-on instances     ├── Scale to zero          ├── Queue-based
├── <1s latency             ├── 1-60s cold start       ├── Up to 60 min
├── Auto-scaling            ├── Up to 6 GB RAM         ├── Large payloads
└── Multi-model support     └── Max 3 GB model         └── Cost-efficient
```

### Deploy Hugging Face model to SageMaker

```python
import sagemaker
from sagemaker.huggingface import HuggingFaceModel
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer

sess = sagemaker.Session()
role = sagemaker.get_execution_role()

# Deploy Mistral 7B Instruct
hub_config = {
    "HF_MODEL_ID": "mistralai/Mistral-7B-Instruct-v0.2",
    "HF_TASK": "text-generation",
    "SM_NUM_GPUS": "1",
    "MAX_INPUT_LENGTH": "2048",
    "MAX_TOTAL_TOKENS": "4096",
    "MAX_BATCH_TOTAL_TOKENS": "8192",
}

model = HuggingFaceModel(
    env=hub_config,
    role=role,
    image_uri=sagemaker.image_uris.retrieve(
        framework="huggingface-llm",
        region=sess.boto_region_name,
        version="1.4.0",
    ),
)

predictor = model.deploy(
    initial_instance_count=1,
    instance_type="ml.g5.2xlarge",     # 1x A10G GPU, 24 GB VRAM
    endpoint_name="mistral-7b-prod",
    serializer=JSONSerializer(),
    deserializer=JSONDeserializer(),
    container_startup_health_check_timeout=600,
)

# Auto-scaling policy
client = boto3.client("application-autoscaling")
client.register_scalable_target(
    ServiceNamespace="sagemaker",
    ResourceId=f"endpoint/mistral-7b-prod/variant/AllTraffic",
    ScalableDimension="sagemaker:variant:DesiredInstanceCount",
    MinCapacity=1,
    MaxCapacity=4,
)
client.put_scaling_policy(
    PolicyName="mistral-scaling",
    ServiceNamespace="sagemaker",
    ResourceId=f"endpoint/mistral-7b-prod/variant/AllTraffic",
    ScalableDimension="sagemaker:variant:DesiredInstanceCount",
    PolicyType="TargetTrackingScaling",
    TargetTrackingScalingPolicyConfiguration={
        "TargetValue": 70.0,
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance",
        },
        "ScaleInCooldown": 300,
        "ScaleOutCooldown": 60,
    },
)

# Inference
response = predictor.predict({
    "inputs": "<s>[INST] Explain neural networks in simple terms. [/INST]",
    "parameters": {
        "max_new_tokens": 256,
        "temperature": 0.7,
        "do_sample": True,
    },
})
print(response[0]["generated_text"])
```

### Shadow deployment (A/B testing with production data)

```python
# Deploy two model variants — compare quality without user impact
model.deploy(
    endpoint_name="genai-shadow-test",
    initial_instance_count=1,
    instance_type="ml.g5.2xlarge",
    production_variants=[
        {
            "VariantName": "champion",
            "ModelName": "mistral-7b-v1",
            "InstanceType": "ml.g5.2xlarge",
            "InitialInstanceCount": 1,
            "InitialVariantWeight": 100,    # all traffic goes here
        },
        {
            "VariantName": "challenger",
            "ModelName": "mistral-7b-v2",
            "InstanceType": "ml.g5.2xlarge",
            "InitialInstanceCount": 1,
            "InitialVariantWeight": 0,      # shadow: receives copy of traffic, not routed to users
        },
    ],
)
```

---

## SageMaker Serverless Inference

Scale-to-zero inference for variable or low-traffic workloads.

```python
from sagemaker.serverless import ServerlessInferenceConfig

serverless_config = ServerlessInferenceConfig(
    memory_size_in_mb=6144,      # 1 GB–6 GB in 1 GB increments
    max_concurrency=10,           # max simultaneous requests per endpoint
    provisioned_concurrency=2,    # keep 2 instances warm (reduces cold starts)
)

predictor = model.deploy(
    serverless_inference_config=serverless_config,
    endpoint_name="mistral-7b-serverless",
)

# Cold start: ~15-45s for 7B model
# Warm: <500ms overhead
# Cost: $0.0000600 per GB-second (vs $1.212/hr for ml.g5.2xlarge)
```

---

## AWS Lambda for Lightweight Inference

For small models or routing calls to Bedrock/external APIs.

### Architecture with API Gateway

```
Client ──HTTPS──► API Gateway ──► Lambda ──► Amazon Bedrock
                 (auth, throttle)            (Claude / Titan)
                      │
                      └──► SQS Queue ──► Lambda (async)
                           (for batch)
```

### Lambda function for Bedrock invocation

```python
# lambda_function.py
import json
import boto3
import os
from functools import lru_cache

# Reuse client across warm invocations
@lru_cache(maxsize=1)
def get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    prompt = body.get("prompt")
    if not prompt:
        return {"statusCode": 400, "body": json.dumps({"error": "prompt required"})}

    bedrock = get_bedrock_client()

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": body.get("max_tokens", 512),
        "messages": [{"role": "user", "content": prompt}],
    }

    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
        body=json.dumps(request_body),
    )

    result = json.loads(response["body"].read())
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({
            "text": result["content"][0]["text"],
            "usage": result["usage"],
        }),
    }
```

### SAM deployment

```yaml
# template.yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31

Resources:

  GenAIFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: lambda_function.lambda_handler
      Runtime: python3.11
      MemorySize: 256
      Timeout: 30
      Policies:
        - Version: "2012-10-17"
          Statement:
            - Effect: Allow
              Action:
                - bedrock:InvokeModel
                - bedrock:InvokeModelWithResponseStream
              Resource: "arn:aws:bedrock:us-east-1::foundation-model/*"
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /generate
            Method: post
            Auth:
              ApiKeyRequired: true

  # API key for authentication
  ApiKey:
    Type: AWS::ApiGateway::ApiKey
    Properties:
      Enabled: true
```

```bash
# Deploy
sam build && sam deploy --guided
```

---

## ECS & EKS Container Deployment

### ECS Fargate with GPU (for vLLM)

```json
// task-definition.json
{
  "family": "vllm-inference",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["EC2"],
  "containerDefinitions": [
    {
      "name": "vllm",
      "image": "vllm/vllm-openai:latest",
      "command": [
        "--model", "mistralai/Mistral-7B-Instruct-v0.2",
        "--port", "8000",
        "--tensor-parallel-size", "1"
      ],
      "portMappings": [{ "containerPort": 8000 }],
      "resourceRequirements": [
        { "type": "GPU", "value": "1" }
      ],
      "memory": 20480,
      "cpu": 4096,
      "environment": [
        { "name": "HUGGING_FACE_HUB_TOKEN", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:hf-token" }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/vllm-inference",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "vllm"
        }
      }
    }
  ]
}
```

### EKS with Karpenter for GPU auto-provisioning

```yaml
# karpenter-nodepool.yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: gpu-nodepool
spec:
  template:
    spec:
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: [amd64]
        - key: karpenter.k8s.aws/instance-gpu-count
          operator: In
          values: ["1", "4", "8"]
        - key: karpenter.k8s.aws/instance-gpu-name
          operator: In
          values: [a10g, a100]
        - key: karpenter.sh/capacity-type
          operator: In
          values: [spot, on-demand]    # prefer spot for cost savings
      nodeClassRef:
        name: gpu-nodeclass
  limits:
    cpu: 1000
    nvidia.com/gpu: 10
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 30s             # aggressively reclaim idle GPU nodes
```

---

## MLOps with SageMaker Pipelines

### Full MLOps pipeline

```python
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep, TransformStep
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.functions import JsonGet
from sagemaker.processing import ScriptProcessor
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.huggingface import HuggingFace

role = sagemaker.get_execution_role()

# ── Step 1: Data Processing ───────────────────────────────────────────────────
sklearn_processor = SKLearnProcessor(
    framework_version="1.0-1",
    role=role,
    instance_type="ml.m5.xlarge",
    instance_count=1,
)

data_prep_step = ProcessingStep(
    name="PrepareTrainingData",
    processor=sklearn_processor,
    inputs=[
        ProcessingInput(source="s3://my-bucket/raw-data", destination="/opt/ml/processing/input"),
    ],
    outputs=[
        ProcessingOutput(output_name="train", source="/opt/ml/processing/output/train"),
        ProcessingOutput(output_name="test", source="/opt/ml/processing/output/test"),
    ],
    code="scripts/prepare_data.py",
)


# ── Step 2: Fine-tuning ───────────────────────────────────────────────────────
huggingface_estimator = HuggingFace(
    entry_point="scripts/finetune.py",
    role=role,
    instance_count=1,
    instance_type="ml.g5.4xlarge",
    transformers_version="4.37",
    pytorch_version="2.1",
    py_version="py310",
    hyperparameters={
        "base_model": "mistralai/Mistral-7B-Instruct-v0.2",
        "epochs": 3,
        "learning_rate": 2e-4,
        "lora_r": 16,
    },
)

training_step = TrainingStep(
    name="FineTuneModel",
    estimator=huggingface_estimator,
    inputs={
        "train": TrainingInput(
            s3_data=data_prep_step.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri
        ),
    },
)


# ── Step 3: Evaluation ────────────────────────────────────────────────────────
evaluation_processor = ScriptProcessor(
    image_uri="...",
    command=["python3"],
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge",
)

evaluation_step = ProcessingStep(
    name="EvaluateModel",
    processor=evaluation_processor,
    inputs=[
        ProcessingInput(
            source=training_step.properties.ModelArtifacts.S3ModelArtifacts,
            destination="/opt/ml/processing/model",
        ),
    ],
    outputs=[ProcessingOutput(output_name="evaluation", source="/opt/ml/processing/evaluation")],
    code="scripts/evaluate.py",
    property_files=[
        PropertyFile(name="EvaluationReport", output_name="evaluation", path="evaluation.json")
    ],
)


# ── Step 4: Quality gate (only deploy if ROUGE > 0.5) ────────────────────────
quality_check = ConditionStep(
    name="CheckModelQuality",
    conditions=[
        ConditionGreaterThanOrEqualTo(
            left=JsonGet(
                step_name=evaluation_step.name,
                property_file="EvaluationReport",
                json_path="metrics.rouge_l",
            ),
            right=0.5,
        )
    ],
    if_steps=[deploy_step],     # defined separately
    else_steps=[],              # do nothing if quality is poor
)


# ── Assemble & run pipeline ───────────────────────────────────────────────────
pipeline = Pipeline(
    name="GenAIFinetunePipeline",
    steps=[data_prep_step, training_step, evaluation_step, quality_check],
    sagemaker_session=sagemaker.Session(),
)

pipeline.upsert(role_arn=role)
execution = pipeline.start()
execution.wait()
```

---

## Monitoring with CloudWatch & SageMaker Clarify

### Custom CloudWatch metrics

```python
import boto3
import time

cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")


def put_inference_metrics(
    model: str,
    latency_ms: float,
    input_tokens: int,
    output_tokens: int,
    success: bool,
):
    cloudwatch.put_metric_data(
        Namespace="GenAI/Inference",
        MetricData=[
            {
                "MetricName": "Latency",
                "Dimensions": [{"Name": "Model", "Value": model}],
                "Value": latency_ms,
                "Unit": "Milliseconds",
            },
            {
                "MetricName": "InputTokens",
                "Dimensions": [{"Name": "Model", "Value": model}],
                "Value": input_tokens,
                "Unit": "Count",
            },
            {
                "MetricName": "OutputTokens",
                "Dimensions": [{"Name": "Model", "Value": model}],
                "Value": output_tokens,
                "Unit": "Count",
            },
            {
                "MetricName": "ErrorRate",
                "Dimensions": [{"Name": "Model", "Value": model}],
                "Value": 0 if success else 1,
                "Unit": "Count",
            },
        ],
    )
```

### CloudWatch alarm for high latency

```python
cloudwatch.put_metric_alarm(
    AlarmName="GenAI-HighLatency",
    MetricName="Latency",
    Namespace="GenAI/Inference",
    Statistic="p95",
    Period=300,
    EvaluationPeriods=2,
    Threshold=5000.0,        # 5 seconds P95
    ComparisonOperator="GreaterThanThreshold",
    AlarmActions=["arn:aws:sns:us-east-1:123456789:genai-alerts"],
    TreatMissingData="notBreaching",
)
```

---

## Security: IAM Roles & Secrets Manager

### Principle of least privilege IAM policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvokeOnly",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
      ]
    },
    {
      "Sid": "SecretsReadOnly",
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789:secret:genai/*"
    },
    {
      "Sid": "S3ModelArtifacts",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::my-model-bucket/models/*"
    }
  ]
}
```

### Fetch secrets without hardcoding

```python
import boto3
import json
from functools import lru_cache

secrets_client = boto3.client("secretsmanager", region_name="us-east-1")


@lru_cache(maxsize=None)
def get_secret(secret_name: str) -> dict:
    response = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])


# Usage
config = get_secret("genai/production")
anthropic_key = config["anthropic_api_key"]
db_url = config["database_url"]
```

---

## End-to-End: Production RAG on AWS

### Architecture

```
Users
  │
  ▼
CloudFront (CDN + WAF)
  │
  ▼
API Gateway (auth, throttling, usage plans)
  │
  ▼
Lambda / ECS (FastAPI app)
  ├── Embed query ──────────────────► Amazon Bedrock Titan Embeddings
  ├── Vector search ────────────────► Amazon OpenSearch (k-NN)
  ├── Generate answer ──────────────► Amazon Bedrock Claude
  └── Log & trace ──────────────────► CloudWatch + X-Ray
        │
        ▼
  S3 (document store)
  DynamoDB (conversation history)
```

### Application code

```python
# app.py — FastAPI RAG on AWS
import boto3
import json
import os
from fastapi import FastAPI
from pydantic import BaseModel
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

app = FastAPI()

# Clients
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
session_table = dynamodb.Table(os.environ["SESSION_TABLE"])

# OpenSearch client with IAM auth
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    "us-east-1",
    "es",
    session_token=credentials.token,
)
opensearch = OpenSearch(
    hosts=[{"host": os.environ["OPENSEARCH_ENDPOINT"], "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    connection_class=RequestsHttpConnection,
)


def embed(text: str) -> list[float]:
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps({"inputText": text}),
    )
    return json.loads(response["body"].read())["embedding"]


def vector_search(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    response = opensearch.search(
        index="documents",
        body={
            "size": top_k,
            "query": {
                "knn": {
                    "content_vector": {
                        "vector": query_embedding,
                        "k": top_k,
                    }
                }
            },
            "_source": ["title", "content", "source_url"],
        },
    )
    return [hit["_source"] for hit in response["hits"]["hits"]]


def generate(question: str, docs: list[dict]) -> str:
    context = "\n\n".join(f"[{d['title']}]\n{d['content']}" for d in docs)
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": (
            "Answer questions using only the provided context. "
            "Say 'I don't know' if the answer isn't in the context."
        ),
        "messages": [
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ],
    }
    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
        body=json.dumps(body),
    )
    return json.loads(response["body"].read())["content"][0]["text"]


class QueryRequest(BaseModel):
    question: str
    session_id: str = ""


@app.post("/query")
async def query(req: QueryRequest):
    embedding = embed(req.question)
    docs = vector_search(embedding)
    answer = generate(req.question, docs)
    return {
        "answer": answer,
        "sources": [{"title": d["title"], "url": d.get("source_url", "")} for d in docs],
    }
```

---

## Cost Optimization on AWS

### Cost comparison (us-east-1 pricing)

```
Bedrock Claude 3.5 Sonnet
  Input:  $3.00 / 1M tokens
  Output: $15.00 / 1M tokens

SageMaker ml.g5.2xlarge (1x A10G GPU)
  On-demand: $1.515/hr → ~$1,091/month
  Spot: ~$0.45/hr → ~$324/month (70% savings)
  SageMaker Savings Plans: up to 64% off

Lambda
  $0.20 / 1M requests + $0.0000166667 / GB-second
  (Bedrock cost dominates — Lambda itself is nearly free)
```

### Spot instances for training

```python
# Use Spot for training (up to 90% cheaper)
from sagemaker.huggingface import HuggingFace

estimator = HuggingFace(
    ...
    use_spot_instances=True,
    max_wait=7200,              # wait up to 2 hours for spot
    max_run=3600,               # max training time
    checkpoint_s3_uri="s3://my-bucket/checkpoints/",  # resume if interrupted
)
```

### Cost allocation tags

```bash
# Tag all resources for cost attribution
aws sagemaker add-tags \
  --resource-arn arn:aws:sagemaker:us-east-1:123456789:endpoint/mistral-7b-prod \
  --tags Key=Project,Value=genai-prod \
         Key=Team,Value=ml-platform \
         Key=Environment,Value=production \
         Key=CostCenter,Value=engineering
```

---

## Key Takeaways

1. **Amazon Bedrock** eliminates infrastructure entirely — best for fast iteration and variable traffic.
2. **Bedrock Knowledge Bases** provides managed RAG — no vector database to operate.
3. **SageMaker Endpoints** are production-grade with built-in auto-scaling, A/B traffic splitting, and shadow deployments.
4. **Karpenter on EKS** provisions GPU nodes on demand and terminates them when idle — dramatic cost savings.
5. **SageMaker Pipelines** with a quality gate prevents bad models from reaching production automatically.
6. **Spot instances for training** cut fine-tuning costs by 70–90%.
7. **IAM roles over API keys** — no credentials in code, ever.

---

*Back to: [Azure Deployment →](../README.md) | [Deployment Overview →](../../01_deployment_overview/README.md)*
