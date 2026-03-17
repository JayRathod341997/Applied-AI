# Hands-on: Fine-tuning with Azure Machine Learning

## Overview

This hands-on guide demonstrates how to fine-tune Large Language Models using Azure Machine Learning (Azure ML). Azure ML provides enterprise-grade infrastructure with integrated MLflow tracking, security, and scalability.

## Prerequisites

- Azure Subscription
- Azure ML Workspace
- Azure Storage Account (Blob Storage)
- HuggingFace account and token

## Estimated Duration

90-120 minutes

---

## Step 1: Azure Environment Setup

### 1.1 Install Azure ML SDK

```bash
pip install azure-ai-ml azure-identity
```

### 1.2 Authenticate

```python
from azure.identity import DefaultAzureCredential
from azure.ai.ml import MLClient

# Authenticate using default credentials
credential = DefaultAzureCredential()

# Connect to workspace
subscription_id = "your-subscription-id"
resource_group = "your-resource-group"
workspace_name = "your-workspace-name"

ml_client = MLClient(
    credential=credential,
    subscription_id=subscription_id,
    resource_group_name=resource_group,
    workspace_name=workspace_name,
)

print(f"Connected to workspace: {workspace_name}")
```

### 1.3 Create Workspace (if needed)

```python
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Workspace
from azure.identity import DefaultAzureCredential

# Define workspace
workspace = Workspace(
    name="genai-workspace",
    location="eastus",
    resource_group="your-resource-group",
)

# Create workspace
ml_client = MLClient.from_config(credential=credential)
```

---

## Step 2: Create Compute Target

### 2.1 GPU Compute Cluster

```python
from azure.ai.ml.entities import AmlCompute

# Define compute configuration
compute = AmlCompute(
    name="gpu-cluster",
    type="amlcompute",
    size="Standard_NC24s_v3",  # 4x NVIDIA Tesla V100
    min_instances=0,
    max_instances=4,
    idle_time_before_scale_down=300,
    tier="Dedicated",
)

# Create compute
compute_cluster = ml_client.compute.begin_create_or_update(compute)
print(f"Compute created: {compute_cluster.name}")
```

### 2.2 Available VM Sizes

| Size | GPU | VRAM | Use Case |
|------|-----|------|----------|
| Standard_NC6 | K80 | 12GB | Testing |
| Standard_NC12 | K80 | 24GB | Small models |
| Standard_NC24s_v3 | V100 | 32GB | Production |
| Standard_ND96asr_v4 | A100 | 80GB | Large models |

---

## Step 3: Upload Data to Azure Blob Storage

### 3.1 Create Storage Client

```python
from azure.storage.blob import BlobServiceClient
import os

# Connection string
connection_string = "your-storage-connection-string"

# Create client
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Get container
container_name = "fine-tuning-data"
container_client = blob_service_client.get_container_client(container_name)

# Upload training data
with open("train.jsonl", "rb") as data:
    container_client.upload_blob(name="train.jsonl", data=data, overwrite=True)

with open("test.jsonl", "rb") as data:
    container_client.upload_blob(name="test.jsonl", data=data, overwrite=True)

print("Data uploaded to Blob Storage")
```

### 3.2 Create Data Asset

```python
from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes

# Create data asset
data = Data(
    name="training-data",
    version="1.0",
    type=AssetTypes.URI_FOLDER,
    path="azureml://datastores/workspaceblobstore/paths/fine-tuning/",
    description="Training data for fine-tuning",
)

# Register data asset
ml_client.data.create_or_update(data)
print(f"Data asset created: {data.name}")
```

---

## Step 4: Create Training Script

### 4.1 Create train.py

```python
# Create the training script
train_code = '''
import os
import json
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset

# Environment variables
DATA_PATH = os.environ.get("DATA_PATH", "./data")
MODEL_NAME = os.environ.get("MODEL_NAME", "meta-llama/Meta-Llama-3-8B")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./outputs")

print(f"Data path: {DATA_PATH}")
print(f"Model: {MODEL_NAME}")

# Load data
train_data = load_dataset("json", data_files=f"{DATA_PATH}/train.jsonl")["train"]
test_data = load_dataset("json", data_files=f"{DATA_PATH}/test.jsonl")["test"]

# Configure quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

# Load model
print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

# Apply LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Tokenize data
def tokenize_function(examples):
    texts = [f"Instruction: {i}\\nInput: {inp}\\nOutput: {out}" 
             for i, inp, out in zip(examples["instruction"], 
                                    examples["input"], 
                                    examples["output"])]
    return tokenizer(texts, padding="max_length", truncation=True, max_length=512)

train_data = train_data.map(tokenize_function, batched=True, remove_columns=train_data.column_names)
test_data = test_data.map(tokenize_function, batched=True, remove_columns=test_data.column_names)

# Training arguments
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    learning_rate=2e-4,
    weight_decay=0.01,
    warmup_ratio=0.1,
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=2,
    fp16=True,
    logging_steps=10,
    report_to="none",
)

# Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_data,
    eval_dataset=test_data,
)

print("Starting training...")
trainer.train()

# Save model
print("Saving model...")
model.save_pretrained(f"{OUTPUT_DIR}/model")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/model")
print("Training completed!")
'''

# Save training script
with open("train.py", "w") as f:
    f.write(train_code)

print("Training script created!")
```

### 4.2 Create environment.yml

```yaml
name: finetune-env
channels:
  - pytorch
  - nvidia
  - conda-forge
dependencies:
  - python=3.10
  - pip
  - pip:
    - torch>=2.0.0
    - transformers>=4.28.0
    - datasets>=2.14.0
    - peft>=0.4.0
    - accelerate>=0.20.0
    - bitsandbytes>=0.39.0
    - azure-ai-ml
    - mlflow

```

---

## Step 5: Configure and Run Job

### 5.1 Command Job

```python
from azure.ai.ml import command
from azure.ai.ml.entities import Environment

# Create environment from conda file
env = Environment(
    name="finetune-env",
    conda_file="environment.yml",
    image="mcr.microsoft.com/azureml/openmpi4.1.0-cuda11.8-cudnn8-runtime-ubuntu22.04:latest",
)

# Define command job
job = command(
    code="./",
    command="python train.py",
    environment=env,
    compute="gpu-cluster",
    instance_count=1,
    timeout="PT6H",  # 6 hours timeout
)

# Submit job
returned_job = ml_client.jobs.create_or_update(job)
print(f"Job submitted: {returned_job.name}")
```

### 5.2 Pipeline Job (Recommended for Production)

```python
from azure.ai.ml import dsl
from azure.ai.ml.entities import PipelineJob

# Define pipeline
@dsl.pipeline(
    compute="gpu-cluster",
    description="Fine-tuning pipeline"
)
def finetune_pipeline(data_path, model_name):
    # Training step
    train_step = command(
        code="./",
        command="python train.py --DATA_PATH {} --MODEL_NAME {}".format(data_path, model_name),
        environment=env,
        instance_count=1,
    )
    return train_step.outputs

# Create pipeline
pipeline_job = finetune_pipeline(
    data_path="azureml://datastores/workspaceblobstore/paths/fine-tuning/",
    model_name="meta-llama/Meta-Llama-3-8B"
)

# Submit pipeline
pipeline = ml_client.jobs.create_or_update(pipeline_job)
```

---

## Step 6: Monitor Training

### 6.1 Get Job Status

```python
# Get job details
job_name = "your-job-name"
job = ml_client.jobs.get(job_name)

print(f"Job status: {job.status}")
print(f"Start time: {job.start_time}")
print(f"End time: {job.end_time}")
```

### 6.2 Stream Logs

```python
# Stream training logs
ml_client.jobs.stream(job_name)
```

### 6.3 View in Azure ML Studio

Open Azure ML Studio at https://ml.azure.com and navigate to:
- Jobs → Your job → View details
- Metrics tab for training curves
- Logs tab for console output

---

## Step 7: Retrieve Trained Model

### 7.1 Download Model

```python
from azure.ai.ml.entities import Model

# Get model from job
model_name = "fine-tuned-llama"
model = ml_client.models.get(name=model_name, version="1")

# Download model
model.download("./downloaded_model")
```

### 7.2 Register Model

```python
from azure.ai.ml.entities import Model
from azure.ai.ml.constants import AssetTypes

# Register model from job output
model = Model(
    name="llama-finetuned",
    version="1",
    type=AssetTypes.CUSTOM_MODEL,
    path="azureml://jobs/<job-name>/outputs/model",
    description="Fine-tuned Llama model",
)

registered_model = ml_client.models.create_or_update(model)
print(f"Model registered: {registered_model.name}")
```

---

## Step 8: Deploy Model

### 8.1 Create Online Endpoint

```python
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    Model as AzureModel
)

# Create endpoint
endpoint = ManagedOnlineEndpoint(
    name="llama-endpoint",
    auth_mode="key",
    description="Fine-tuned Llama endpoint",
)

ml_client.online_endpoints.begin_create_or_update(endpoint)
```

### 8.2 Deploy to Endpoint

```python
# Get registered model
model = ml_client.models.get("llama-finetuned", "1")

# Create deployment
deployment = ManagedOnlineDeployment(
    name="blue",
    endpoint_name="llama-endpoint",
    model=model.id,
    instance_type="Standard_NC4as_T4_v3",  # T4 GPU
    instance_count=1,
)

# Deploy
ml_client.online_deployments.begin_create_or_update(deployment)

# Update traffic
endpoint.traffic = {"blue": 100}
ml_client.online_endpoints.begin_create_or_update(endpoint)
```

### 8.3 Test Endpoint

```python
# Get endpoint key
key = ml_client.online_endpoints.get_keys("llama-endpoint")

# Test prediction
import requests

url = "https://<your-endpoint>.eastus.inference.ml.azure.com/score"
headers = {
    "Authorization": f"Bearer {key.primary_key}",
    "Content-Type": "application/json"
}

data = {
    "inputs": "Explain quantum computing in simple terms"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

## Step 9: Hyperparameter Tuning

### 9.1 Configure Search Space

```python
from azure.ai.ml import uniform

# Define search space
search_space = {
    "learning_rate": uniform(1e-5, 1e-4),
    "batch_size": [4, 8],
    "num_epochs": [2, 3],
    "lora_r": [8, 16, 32],
}
```

### 9.2 Create HyperDrive Config

```python
from azure.ai.ml import command
from azure.ai.ml.sweep import (
    Cron,
    MedianStoppingPolicy,
    HyperparameterSettings,
)

# Configure sweep
hyperparameter_settings = HyperparameterSettings(
    search_space=search_space,
    sampling_algorithm="random",
    primary_metric="eval_loss",
    goal="Minimize",
)

# Create sweep job
sweep_job = command(
    code="./",
    command="python train.py --learning_rate ${search_space.learning_rate} --batch_size ${search_space.batch_size}",
    environment=env,
    compute="gpu-cluster",
    hyperparameter=hyperparameter_settings,
)

# Submit sweep
sweep = ml_client.jobs.create_or_update(sweep_job)
```

---

## Cost Optimization Tips

### 1. Use Spot Instances

```python
# Enable spot instances in compute
compute = AmlCompute(
    name="spot-cluster",
    size="Standard_NC24s_v3",
    tier="Spot",
    idle_time_before_scale_down=180,
)
```

### 2. Set Budget Alerts

```python
# Create budget alert in Azure Portal
# Cost Management + Billing → Budgets → Create budget
```

### 3. Enable Auto-shutdown

```python
# Set compute to scale down when idle
compute.idle_time_before_scale_down = 300  # 5 minutes
```

---

## Common Issues

### Issue 1: Storage Permission Denied

**Solution:**
- Check storage account IAM permissions
- Ensure user has "Storage Blob Data Contributor" role

### Issue 2: Quota Exceeded

**Solution:**
- Request quota increase in Azure Portal
- Use smaller instance type

### Issue 3: Model Not Found

**Solution:**
- Verify HuggingFace token has access to model
- Check model name is correct

---

## Exercises

### Exercise 1: Different Model Sizes

Try fine-tuning:
- `microsoft/Phi-3-mini-4k-instruct` (smaller, cheaper)
- `mistralai/Mistral-7B-Instruct-v0.2`
- `meta-llama/Meta-Llama-3-70B-Instruct` (requires larger GPU)

### Exercise 2: Custom Dataset

Fine-tune on:
- Your company's documentation
- Customer support conversations
- Domain-specific knowledge base

### Exercise 3: Experiment Tracking

Set up MLflow tracking to compare:
- Different learning rates
- Different LoRA ranks
- Different models

---

## Next Steps

1. Explore Azure AI Studio for prompt flow
2. Learn about model evaluation with Azure
3. Set up CI/CD for ML workflows
4. Implement MLOps with Azure