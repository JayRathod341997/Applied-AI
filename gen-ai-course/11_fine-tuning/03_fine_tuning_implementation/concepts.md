# Concepts: Fine-tuning Implementation - Comprehensive Guide

## Overview

This module provides comprehensive hands-on implementation guides for fine-tuning Large Language Models across major cloud platforms. Each platform has unique characteristics, pricing models, and integration patterns that we'll explore in detail.

---

## Table of Contents

1. [Unsloth Implementation](#1-unsloth-implementation)
2. [Hugging Face Implementation](#2-hugging-face-implementation)
3. [Azure ML Implementation](#3-azure-ml-implementation)
4. [AWS SageMaker Implementation](#4-aws-sagemaker-implementation)
5. [GCP Vertex AI Implementation](#5-gcp-vertex-ai-implementation)
6. [Platform Comparison](#6-platform-comparison)
7. [Production Considerations](#7-production-considerations)

---

## 1. Unsloth Implementation

### What is Unsloth?

Unsloth is a library designed to make fine-tuning 2x faster while using 70% less VRAM. It achieves this through:

- **Gradient Checkpointing**: Reduces memory by recomputing activations during backpropagation
- **4-bit Loading**: Quantizes model weights to 4-bit precision
- **Dynamic Batch Sizes**: Optimizes memory usage based on available GPU
- **Optimized Kernels**: Custom CUDA kernels for faster computation

### Supported Models

- Meta Llama 2/3
- Mistral
- Phi-3
- Qwen
- Gemma

### Prerequisites

```bash
# Install Unsloth
pip install unsloth

# Or install from source
pip install git+https://github.com/unslothai/unsloth.git
```

### Step-by-Step Implementation

#### Step 1: Prepare the Environment

```python
# Import required libraries
from unsloth import FastLanguageModel
from transformers import AutoTokenizer
import torch

# Check GPU availability
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
```

#### Step 2: Load Model with Unsloth

```python
# Configuration
max_seq_length = 2048  # Choose based on your GPU
dtype = None          # Auto-detect
load_in_4bit = True   # Use 4-bit quantization

# Load model and tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit,
)

# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                    # LoRA rank
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", 
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing=True,
    random_state=3407,
)
```

#### Step 3: Prepare Training Data

```python
from datasets import load_dataset

# Load your dataset
dataset = load_dataset("json", data_files="train.jsonl")

# Format for instruction fine-tuning
def format_prompts(examples):
    texts = []
    for instruction, input_text, output in zip(
        examples["instruction"], 
        examples["input"], 
        examples["output"]
    ):
        text = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input_text}

### Response:
{output}"""
        texts.append(text)
    return {"text": texts}

dataset = dataset.map(format_prompts, batched=True)
```

#### Step 4: Configure Training

```python
from transformers import TrainingArguments
from unsloth import Trainner

training_args = TrainingArguments(
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_steps=5,
    num_train_epochs=3,
    learning_rate=2e-4,
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    logging_steps=1,
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="linear",
    seed=3407,
    output_dir="outputs",
    report_to="none",
)
```

#### Step 5: Train the Model

```python
trainer = Trainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    eval_dataset=dataset.get("test"),
    args=training_args,
)

# Start training
trainer.train()

# Save the model
model.save_pretrained("lora_model")
tokenizer.save_pretrained("lora_model")
```

### Google Colab Integration

Unsloth provides optimized Colab notebooks for free GPU access:

```python
# For Google Colab, use this command to install
!pip install unsloth[colab]

# Recommended Colab settings for fine-tuning
# GPU: T4 (free) or A100 (paid)
# Runtime: Python 3.10+
# VRAM: Minimum 15GB recommended
```

### Memory Optimization Techniques

```python
# Additional memory optimizations
model.enable_input_require_grads()  # Enable gradient computation for inputs
model.gradient_checkpointing_enable()  # Enable gradient checkpointing
model.unload()  # Unload model from VRAM when not needed
```

---

## 2. Hugging Face Implementation

### Overview

Hugging Face provides the most flexible fine-tuning approach using the Transformers library and Trainer API. It's platform-agnostic and works locally or on any cloud provider.

### Prerequisites

```bash
pip install transformers datasets peft accelerate bitsandbytes torch
```

### Implementation Steps

#### Step 1: Load Base Model

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Configure 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    "meta-llama/Meta-Llama-3-8B",
    token="your_hf_token"
)
tokenizer.pad_token = tokenizer.eos_token

# Load model with quantization
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Meta-Llama-3-8B",
    quantization_config=bnb_config,
    device_map="auto",
    token="your_hf_token"
)
```

#### Step 2: Configure LoRA

```python
from peft import LoraConfig, get_peft_model, TaskType

# Define LoRA configuration
lora_config = LoraConfig(
    r=16,                    # Rank
    lora_alpha=32,           # Alpha parameter
    lora_dropout=0.05,       # Dropout probability
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

# Apply LoRA to model
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Output: trainable params: 4,194,304 || all_params: 8,030,261,248 || trainable%: 0.05%
```

#### Step 3: Prepare Dataset

```python
from datasets import load_dataset

# Load and process dataset
dataset = load_dataset("json", data_files="training_data.json")

# Tokenize function
def tokenize_function(examples):
    # Combine instruction, input, and output
    texts = []
    for instr, inp, out in zip(
        examples["instruction"], 
        examples["input"], 
        examples["output"]
    ):
        text = f"Instruction: {instr}\nInput: {inp}\nOutput: {out}"
        texts.append(text)
    
    # Tokenize
    tokenized = tokenizer(
        texts,
        padding="max_length",
        truncation=True,
        max_length=512,
        return_tensors="pt"
    )
    
    # Labels for causal LM
    tokenized["labels"] = tokenized["input_ids"].clone()
    return tokenized

# Apply tokenization
tokenized_dataset = dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=dataset["train"].column_names,
)

# Train/test split
train_dataset = tokenized_dataset["train"].train_test_split(test_size=0.1)
```

#### Step 4: Configure Training Arguments

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./llama3_finetuned",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    weight_decay=0.01,
    warmup_ratio=0.1,
    logging_dir="./logs",
    logging_steps=10,
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=3,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    fp16=True,
    dataloader_num_workers=4,
    report_to="tensorboard",
    hub_model_id="your-username/llama3-finetuned",
    push_to_hub=False,
)
```

#### Step 5: Initialize Trainer

```python
from transformers import Trainer, DataCollatorForLanguageModeling

# Data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,  # Causal LM
)

# Initialize trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset["train"],
    eval_dataset=train_dataset["test"],
    data_collator=data_collator,
)

# Start training
trainer.train()

# Save model
trainer.save_model("./final_model")
tokenizer.save_pretrained("./final_model")
```

### Using SFTTrainer (Supervised Fine-tuning)

```python
from trl import SFTTrainer

trainer = SFTTrainer(
    model=model,
    train_dataset=train_dataset["train"],
    eval_dataset=train_dataset["test"],
    dataset_text_field="text",
    max_seq_length=512,
    tokenizer=tokenizer,
    args=training_args,
)

trainer.train()
```

---

## 3. Azure ML Implementation

### Overview

Azure Machine Learning provides enterprise-grade fine-tuning with:
- Managed compute clusters
- Integrated MLflow tracking
- Role-based access control
- Private endpoint security

### Prerequisites

```bash
pip install azure-ai-ml azure-identity
```

### Implementation Steps

#### Step 1: Connect to Workspace

```python
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

# Authenticate
credential = DefaultAzureCredential()

# Connect to workspace
ml_client = MLClient(
    credential=credential,
    subscription_id="your-subscription-id",
    resource_group_name="your-resource-group",
    workspace_name="your-workspace",
)
```

#### Step 2: Create Compute Target

```python
from azure.ai.ml import ComputeTarget
from azure.ai.ml.entities import AmlCompute

# Define compute
compute = AmlCompute(
    name="gpu-cluster",
    type="amlcompute",
    size="Standard_NC24s_v3",  # GPU VM size
    min_instances=0,
    max_instances=4,
    idle_time_before_scale_down=300,
)

# Create or get compute
compute_cluster = ml_client.compute.begin_create_or_update(compute)
print(f"Compute created: {compute_cluster.name}")
```

#### Step 3: Prepare Training Script

```python
# Create train.py
train_code = '''
import os
import json
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer
)
from peft import LoraConfig, get_peft_model

# Get input data path
data_path = os.environ.get("DATA_PATH", "./data")
model_name = os.environ.get("MODEL_NAME", "meta-llama/Meta-Llama-3-8B")

# Load model
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)

# Configure LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
)

model = get_peft_model(model, lora_config)

# Training arguments
training_args = TrainingArguments(
    output_dir="./outputs",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    learning_rate=2e-4,
    fp16=True,
    save_strategy="epoch",
    logging_steps=10,
)

# Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
)

trainer.train()
model.save_pretrained("./model")
'''

# Save training script
with open("train.py", "w") as f:
    f.write(train_code)
```

#### Step 4: Configure and Run Job

```python
from azure.ai.ml import command
from azure.ai.ml.entities import Environment

# Create environment
env = Environment(
    name="finetune-env",
    conda_file="environment.yml",
    image="mcr.microsoft.com/azureml/openmpi4.1.0-cuda11.8-cudnn8-runtime-ubuntu22.04",
)

# Define command job
job = command(
    code="./",
    command="python train.py",
    environment=env,
    compute="gpu-cluster",
    instance_count=1,
)

# Submit job
returned_job = ml_client.jobs.create_or_update(job)
print(f"Job submitted: {returned_job.name}")
```

#### Step 5: Use HuggingFace Estimator (Legacy)

```python
from azureml.core import Workspace, Experiment, ScriptRunConfig
from azureml.train.hyperdrive import HyperDriveConfig, PrimaryMetricGoal

# Legacy approach
ws = Workspace.from_config()
experiment = Experiment(ws, "fine-tuning-experiment")

# Configure hyperparameters
hyperdrive_config = HyperDriveConfig(
    run_config=ScriptRunConfig(source_directory='./', script='train.py'),
    hyperparameter_space={
        'learning_rate': [1e-5, 2e-5, 3e-5],
        'batch_size': [4, 8],
        'num_epochs': [2, 3]
    },
    primary_metric_name="eval_loss",
    primary_metric_goal=PrimaryMetricGoal.MINIMIZE,
    max_total_runs=10,
)

# Submit experiment
run = experiment.submit(hyperdrive_config)
```

---

## 4. AWS SageMaker Implementation

### Overview

AWS SageMaker provides:
- Managed training infrastructure
- Spot instance support for cost savings
- SageMaker Debugger for monitoring
- Automatic model registry

### Prerequisites

```bash
pip install sagemaker boto3
```

### Implementation Steps

#### Step 1: Upload Data to S3

```python
import boto3
import sagemaker

# Initialize clients
s3_client = boto3.client('s3')
sagemaker_session = sagemaker.Session()
role = sagemaker.get_execution_role()

# Upload training data
bucket = "your-bucket-name"
prefix = "fine-tuning/data"

s3_train_data = sagemaker_session.upload_data(
    path="train.jsonl",
    bucket=bucket,
    key_prefix=f"{prefix}/train"
)

s3_test_data = sagemaker_session.upload_data(
    path="test.jsonl",
    bucket=bucket,
    key_prefix=f"{prefix}/test"
)

print(f"Training data: {s3_train_data}")
```

#### Step 2: Create Training Script

```python
# Create train.py for SageMaker
train_script = '''
import os
import json
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments
)
from datasets import load_dataset
from peft import LoraConfig, get_peft_model

# SageMaker directories
train_dir = os.environ.get("SM_CHANNEL_TRAIN")
test_dir = os.environ.get("SM_CHANNEL_TEST")

# Load data
train_data = load_dataset("json", data_files=f"{train_dir}/train.jsonl")
test_data = load_dataset("json", data_files=f"{test_dir}/test.jsonl")

# Load model
model_name = "meta-llama/Meta-Llama-3-8B"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)

# Apply LoRA
lora_config = LoraConfig(r=16, lora_alpha=32, target_modules=["q_proj", "k_proj", "v_proj"])
model = get_peft_model(model, lora_config)

# Training arguments
training_args = TrainingArguments(
    output_dir="/opt/ml/model",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    learning_rate=2e-4,
    fp16=True,
    save_strategy="epoch",
)

# Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_data["train"],
)

trainer.train()
model.save_pretrained("/opt/ml/model")
'''

with open("train.py", "w") as f:
    f.write(train_script)
```

#### Step 3: Configure and Launch Training

```python
from sagemaker.huggingface import HuggingFace

# Create HuggingFace estimator
huggingface_estimator = HuggingFace(
    entry_point='train.py',
    source_dir='./',
    instance_type='ml.p3.2xlarge',  # V100 GPU
    instance_count=1,
    role=role,
    transformers_version='4.28.0',
    pytorch_version='2.0.0',
    py_version='py310',
    base_job_name='llama-finetuning',
    # Storage
    volume_size=100,
    # Debugging
    debugger_hook_config=False,
    # Environment
    environment={
        'HF_TOKEN': 'your-hf-token',
        'AWS_REGION': 'us-east-1'
    },
    # Enable spot training for cost savings
    use_spot_instances=True,
    max_wait=3600,
)

# Define data channels
data = {
    'train': f's3://{bucket}/fine-tuning/data/train',
    'test': f's3://{bucket}/fine-tuning/data/test'
}

# Start training
huggingface_estimator.fit(data, wait=True, logs="All")
print(f"Training job: {huggingface_estimator.latest_training_job.name}")
```

#### Step 4: Deploy Model

```python
# Deploy to endpoint
predictor = huggingface_estimator.deploy(
    initial_instance_count=1,
    instance_type='ml.g4dn.xlarge',
    container_startup_health_check_timeout=300,
)

# Test inference
response = predictor.predict({
    "inputs": "Write a poem about AI:",
    "parameters": {
        "max_new_tokens": 100,
        "temperature": 0.7
    }
})
print(response)
```

---

## 5. GCP Vertex AI Implementation

### Overview

Google Cloud Vertex AI provides:
- TPU support for large models
- Vertex Feature Store integration
- Model Registry
- AutoML capabilities

### Prerequisites

```bash
pip install google-cloud-aiplatform
```

### Implementation Steps

#### Step 1: Initialize Vertex AI

```python
from google.cloud import aiplatform

# Initialize
project_id = "your-project-id"
location = "us-central1"

aiplatform.init(
    project=project_id,
    location=location,
    staging_bucket="gs://your-bucket",
    experiment="fine-tuning-experiment"
)
```

#### Step 2: Upload Data to Cloud Storage

```python
from google.cloud import storage

# Initialize storage client
storage_client = storage.Client()

# Upload files
bucket_name = "your-bucket"
bucket = storage_client.bucket(bucket_name)

# Upload training data
blob = bucket.blob("fine-tuning/train.jsonl")
blob.upload_from_filename("train.jsonl")

blob = bucket.blob("fine-tuning/test.jsonl")
blob.upload_from_filename("test.jsonl")

print("Data uploaded to GCS")
```

#### Step 3: Create Custom Training Job

```python
from google.cloud import aiplatform

# Create custom training job
job = aiplatform.CustomTrainingJob(
    display_name="llama-finetuning-job",
    script_path="train.py",
    container_uri="gcr.io/cloud-aiplatform/training/pytorch-gpu.1-13:latest",
    requirements=[
        "transformers>=4.28.0",
        "datasets>=2.14.0",
        "peft>=0.4.0",
        "accelerate>=0.20.0"
    ],
    model_serving_container_image_uri="gcr.io/cloud-aiplatform/predictor/pytorch-gpu.1-13:latest",
)

# Run training
model = job.run(
    replica_count=1,
    machine_type="a2-highgpu-1g",  # A100 GPU
    accelerator_type="NVIDIA_TESLA_A100",
    accelerator_count=1,
    base_output_dir="gs://your-bucket/output",
    service_account="your-service-account@project.iam.gserviceaccount.com",
)
```

#### Step 4: Create Training Script for Vertex

```python
# train.py for Vertex AI
train_code = '''
import os
import json
from google.cloud import storage
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from datasets import load_dataset
from peft import LoraConfig, get_peft_model

# Download data from GCS
def download_data(bucket_name, source, destination):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source)
    blob.download_to_filename(destination)

# Download training data
download_data("your-bucket", "fine-tuning/train.jsonl", "train.jsonl")
download_data("your-bucket", "fine-tuning/test.jsonl", "test.jsonl")

# Load data
train_data = load_dataset("json", data_files="train.jsonl")
test_data = load_dataset("json", data_files="test.jsonl")

# Load model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Meta-Llama-3-8B",
    torch_dtype=torch.float16,
)

# Apply LoRA
lora_config = LoraConfig(r=16, lora_alpha=32)
model = get_peft_model(model, lora_config)

# Train
training_args = TrainingArguments(
    output_dir="/tmp/model",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    learning_rate=2e-4,
    fp16=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_data["train"],
)

trainer.train()

# Save to GCS
model.save_pretrained("/tmp/model")
blob = storage.Client().bucket("your-bucket").blob("model/model_files")
blob.upload_from_filename("/tmp/model/adapter_config.json")
'''

with open("train.py", "w") as f:
    f.write(train_code)
```

#### Step 5: Deploy for Inference

```python
# Deploy model to endpoint
endpoint = model.deploy(
    deployed_model_display_name="llama-finetuned",
    endpoint_display_name="llama-endpoint",
    machine_type="n1-standard-8",
    accelerator_type="NVIDIA_TESLA_A100",
    accelerator_count=1,
    traffic_split={"0": 100},
)

# Make prediction
response = endpoint.predict({
    "instances": [{
        "inputs": "Explain quantum computing:"
    }]
})

print(response)
```

---

## 6. Platform Comparison

| Feature | Unsloth | HuggingFace | Azure ML | AWS SageMaker | GCP Vertex |
|---------|---------|-------------|----------|---------------|------------|
| **Ease of Use** | ★★★★★ | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ |
| **Cost** | ★★★★★ | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ |
| **Speed** | ★★★★★ | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ |
| **Enterprise Features** | ★★☆☆☆ | ★★★☆☆ | ★★★★★ | ★★★★★ | ★★★★★ |
| **Scalability** | ★★☆☆☆ | ★★★☆☆ | ★★★★★ | ★★★★★ | ★★★★★ |
| **Free Tier** | Colab | Local | $200 credit | $300 credit | $300 credit |

### When to Use Each Platform

| Scenario | Recommended Platform |
|----------|---------------------|
| Quick experiments / Learning | Unsloth + Colab |
| Production on any cloud | HuggingFace Trainer |
| Enterprise Azure integration | Azure ML |
| AWS ecosystem | SageMaker |
| GCP ecosystem | Vertex AI |

---

## 7. Production Considerations

### Cost Optimization

```python
# Common cost-saving strategies:
1. Use spot/preemptible instances (60-90% savings)
2. Enable gradient checkpointing
3. Use 4-bit quantization
4. Implement early stopping
5. Optimize batch sizes
```

### Monitoring and Logging

```python
# Recommended metrics to track:
- Training loss
- Validation loss
- Learning rate
- GPU memory usage
- Token throughput
- Estimated cost
```

### Model Validation

```python
# Always validate:
1. Perplexity on held-out data
2. Human evaluation of outputs
3. Bias and safety checks
4. Response quality metrics
5. Latency requirements
```

---

## Summary

This module covered comprehensive fine-tuning implementation across five major platforms:

1. **Unsloth**: Fast, memory-efficient local fine-tuning with Colab support
2. **HuggingFace**: Flexible, portable fine-tuning using Transformers/Trainer
3. **Azure ML**: Enterprise-grade with MLflow integration
4. **AWS SageMaker**: Managed training with spot instances
5. **GCP Vertex AI**: TPU support and Google Cloud integration

Each platform has unique strengths - choose based on your infrastructure, expertise, and production requirements.
