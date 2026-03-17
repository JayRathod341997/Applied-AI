# Hands-on: Fine-tuning with AWS SageMaker

## Overview

This hands-on guide demonstrates how to fine-tune Large Language Models using AWS SageMaker. SageMaker provides managed training infrastructure with features like spot instances, automatic model tuning, and easy deployment.

## Prerequisites

- AWS Account
- AWS CLI configured
- S3 Bucket for data and model storage
- HuggingFace account and access token

## Estimated Duration

90-120 minutes

---

## Step 1: AWS Environment Setup

### 1.1 Install Dependencies

```bash
pip install sagemaker boto3
```

### 1.2 Configure AWS Credentials

```bash
aws configure
# Enter your:
# AWS Access Key ID
# AWS Secret Access Key
# Region (e.g., us-east-1)
# Output format (json)
```

### 1.3 Initialize SageMaker Session

```python
import sagemaker
import boto3

# Initialize session
sagemaker_session = sagemaker.Session()
role = sagemaker.get_execution_role()

# Get AWS region
region = sagemaker_session.boto_region_name

print(f"Role: {role}")
print(f"Region: {region}")
print(f"Default bucket: {sagemaker_session.default_bucket()}")
```

---

## Step 2: Prepare S3 Storage

### 2.1 Create S3 Bucket

```python
import boto3

# Create S3 client
s3_client = boto3.client('s3')

bucket_name = "your-unique-bucket-name"

# Create bucket
try:
    s3_client.create_bucket(Bucket=bucket_name)
    print(f"Bucket created: {bucket_name}")
except Exception as e:
    print(f"Bucket might already exist: {e}")
```

### 2.2 Upload Training Data

```python
# Upload training data to S3
prefix = "fine-tuning/data"

# Upload train data
train_s3_path = sagemaker_session.upload_data(
    path="train.jsonl",
    bucket=bucket_name,
    key_prefix=f"{prefix}/train"
)

# Upload test data
test_s3_path = sagemaker_session.upload_data(
    path="test.jsonl",
    bucket=bucket_name,
    key_prefix=f"{prefix}/test"
)

print(f"Training data: {train_s3_path}")
print(f"Test data: {test_s3_path}")
```

---

## Step 3: Create Training Script

### 3.1 Create train.py

```python
# Create the training script for SageMaker
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

# Get environment variables
DATA_CHANNEL_TRAIN = os.environ.get("SM_CHANNEL_TRAIN", "./data")
DATA_CHANNEL_TEST = os.environ.get("SM_CHANNEL_TEST", "./data")
MODEL_NAME = os.environ.get("MODEL_NAME", "meta-llama/Meta-Llama-3-8B")
OUTPUT_DIR = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")

print(f"Training data: {DATA_CHANNEL_TRAIN}")
print(f"Test data: {DATA_CHANNEL_TEST}")
print(f"Model: {MODEL_NAME}")

# Load datasets
train_data = load_dataset("json", data_files=f"{DATA_CHANNEL_TRAIN}/train.jsonl")["train"]
test_data = load_dataset("json", data_files=f"{DATA_CHANNEL_TEST}/test.jsonl")["test"]

print(f"Train size: {len(train_data)}")
print(f"Test size: {len(test_data)}")

# Configure 4-bit quantization
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
def format_prompts(examples):
    texts = []
    for instr, inp, out in zip(examples["instruction"], examples["input"], examples["output"]):
        text = f"Instruction: {instr}\\nInput: {inp}\\nOutput: {out}"
        texts.append(text)
    return {"text": texts}

def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=512)

train_data = train_data.map(format_prompts, batched=True)
train_data = train_data.map(tokenize_function, batched=True, remove_columns=["text"])

test_data = test_data.map(format_prompts, batched=True)
test_data = test_data.map(tokenize_function, batched=True, remove_columns=["text"])

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
    load_best_model_at_end=True,
    logging_dir="/opt/ml/output/logs",
    report_to="none",
)

# Create trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_data,
    eval_dataset=test_data,
)

# Train
print("Starting training...")
trainer.train()

# Save model to model directory
print("Saving model...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print("Training completed!")
'''

# Save the training script
with open("train.py", "w") as f:
    f.write(train_code)

print("Training script created!")
```

### 3.2 Create requirements.txt

```
transformers>=4.28.0
datasets>=2.14.0
peft>=0.4.0
accelerate>=0.20.0
bitsandbytes>=0.39.0
torch>=2.0.0
scipy
```

---

## Step 4: Configure and Launch Training

### 4.1 Create HuggingFace Estimator

```python
from sagemaker.huggingface import HuggingFace

# Define hyperparameters
hyperparameters = {
    "MODEL_NAME": "meta-llama/Meta-Llama-3-8B",
    "num_train_epochs": 3,
    "per_device_train_batch_size": 4,
    "learning_rate": 2e-4,
}

# Create estimator
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
    
    # Environment
    environment={
        'HF_TOKEN': 'your-hf-token',
        'AWS_REGION': region,
    },
    
    # Storage
    volume_size=100,
    max_runtime=36000,  # 10 hours
    
    # Enable spot training for cost savings
    use_spot_instances=True,
    max_wait=7200,  # Wait 2 hours for spot capacity
)

print(f"Estimator created with role: {role}")
```

### 4.2 Define Data Channels

```python
# Define input data
input_data = {
    'train': f's3://{bucket_name}/fine-tuning/data/train',
    'test': f's3://{bucket_name}/fine-tuning/data/test',
}
```

### 4.3 Start Training

```python
# Start training job
print("Starting training job...")
huggingface_estimator.fit(
    inputs=input_data,
    wait=True,  # Wait for completion
    logs="All",  # Stream logs
)

print(f"Training job name: {huggingface_estimator.latest_training_job.name}")
print(f"Training status: {huggingface_estimator.latest_training_job.describe()['TrainingJobStatus']}")
```

---

## Step 5: Monitor Training

### 5.1 Training Job Details

```python
# Get training job description
describe = huggingface_estimator.latest_training_job.describe()

print(f"Job Name: {describe['TrainingJobName']}")
print(f"Status: {describe['TrainingJobStatus']}")
print(f"Instance Type: {describe['InputConfig']['InstanceType']}")
print(f"Instance Count: {describe['InputConfig']['InstanceCount']}")
print(f"Volume Size: {describe['InputConfig']['VolumeSizeInGB']}")
```

### 5.2 View Logs in CloudWatch

```python
import boto3

# Get CloudWatch logs
logs_client = boto3.client('logs')

log_group = f"/aws/sagemaker/TrainingJobs"
log_stream = huggingface_estimator.latest_training_job.name

# Get log events
response = logs_client.get_log_events(
    logGroupName=log_group,
    logStreamName=log_stream,
    limit=100
)

for event in response['events']:
    print(event['message'])
```

---

## Step 6: Deploy Model for Inference

### 6.1 Deploy to Endpoint

```python
# Deploy model to endpoint
print("Deploying model...")
predictor = huggingface_estimator.deploy(
    initial_instance_count=1,
    instance_type='ml.g4dn.xlarge',  # T4 GPU
    container_startup_health_check_timeout=300,
)

print(f"Endpoint deployed: {predictor.endpoint_name}")
```

### 6.2 Test Inference

```python
# Test prediction
response = predictor.predict({
    "inputs": "Explain quantum computing in simple terms",
    "parameters": {
        "max_new_tokens": 150,
        "temperature": 0.7,
        "top_p": 0.9,
    }
})

print(response)
```

### 6.3 Delete Endpoint (when done)

```python
# Clean up
predictor.delete_endpoint()
print("Endpoint deleted!")
```

---

## Step 7: Advanced Features

### 7.1 Automatic Model Tuning

```python
from sagemaker.tuner import HyperparameterTuner

# Define parameter ranges
parameter_ranges = {
    'learning_rate': ContinuousParameter(1e-5, 1e-4),
    'per_device_train_batch_size': IntegerParameter(2, 8),
    'lora_r': IntegerParameter(8, 32),
}

# Create tuner
tuner = HyperparameterTuner(
    estimator=huggingface_estimator,
    objective_metric_name='eval_loss',
    parameter_ranges=parameter_ranges,
    max_jobs=9,
    max_parallel_jobs=3,
    strategy='Bayesian',
)

# Run tuning
tuner.fit(inputs=input_data, wait=True)
```

### 7.2 Multi-Instance Training

```python
# Train across multiple instances
huggingface_estimator = HuggingFace(
    entry_point='train.py',
    source_dir='./',
    instance_type='ml.p3.2xlarge',
    instance_count=4,  # Multiple instances
    # ... other parameters
)

# Distribute training across instances
# Note: Need to update train.py to use distributed training
```

### 7.3 Use JumpStart Models

```python
from sagemaker import jumpstart

# Use pre-trained JumpStart model
model_id = "meta-textgeneration-llama-3-8b-instruct"

# Deploy directly without fine-tuning
predictor = jumpstart.deploy(model_id=model_id)
```

---

## Step 8: Cost Optimization

### 8.1 Use Spot Instances

```python
# Enable spot instances (60-90% savings)
huggingface_estimator = HuggingFace(
    entry_point='train.py',
    source_dir='./',
    instance_type='ml.p3.2xlarge',
    use_spot_instances=True,
    max_wait=3600,  # Max wait time for spot
)
```

### 8.2 Use Savings Plans

```python
# Create savings plan
# Go to AWS Console → SageMaker → Savings Plans
# Reserved capacity for up to 70% savings
```

### 8.3 Monitor Costs

```python
import boto3
from datetime import datetime, timedelta

# Get cost explorer data
ce_client = boto3.client('ce')

response = ce_client.get_cost_and_usage(
    TimePeriod={
        'Start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        'End': datetime.now().strftime('%Y-%m-%d')
    },
    Granularity='DAILY',
    Metrics=['UnblendedCost'],
    GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
)

print(response)
```

---

## Step 9: Production Best Practices

### 9.1 Model Registry

```python
import boto3

# Create model package
sm_client = boto3.client('sagemaker')

# Register model
model_package = sm_client.create_model_package(
    ModelPackageName='llama-finetuned-v1',
    InferenceSpecification={
        'Containers': [{
            'Image': huggingface_estimator.image_uri,
            'ModelDataUrl': huggingface_estimator.model_data,
        }],
        'SupportedContentTypes': ['application/json'],
        'SupportedResponseMIMETypes': ['application/json'],
    }
)
```

### 9.2 CI/CD Pipeline

```yaml
# Create in AWS CodePipeline
# pipeline.yaml
version: 1.0
stages:
  - name: train
    actions:
      - name: fine-tune
        actionTypeId:
          category: Build
          provider: SageMaker
          version: '1'
        configuration:
          TrainingJobName: llama-finetuning-{{hash}}
          AlgorithmSpecification:
            TrainingImage: !Ref TrainingImage
  - name: deploy
    actions:
      - name: create-model
      - name: deploy-endpoint
```

---

## Common Issues

### Issue 1: Insufficient Instance Capacity

**Solution:**
- Use different instance type
- Enable spot instances
- Try different region

### Issue 2: Model Download Timeout

**Solution:**
- Increase `max_runtime`
- Use data cache
- Pre-download model to S3

### Issue 3: Spot Instance Interruption

**Solution:**
- Enable checkpointing in training
- Use `max_wait` parameter
- Resume from checkpoint

---

## Exercises

### Exercise 1: Different Instance Types

Try different instances:
- `ml.p2.xlarge` (K80)
- `ml.p3.2xlarge` (V100)
- `ml.p4d.24xlarge` (A100)

### Exercise 2: Hyperparameter Tuning

Run automatic tuning:
- Learning rate: [1e-5, 5e-5, 1e-4]
- Batch size: [2, 4, 8]
- LoRA rank: [8, 16, 32]

### Exercise 3: Deploy and Test

Deploy model and test:
- Different prompts
- Different parameters
- Compare with base model

---

## Clean Up

```python
# Delete endpoint
predictor.delete_endpoint()

# Delete S3 files
import boto3
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucket_name)
bucket.objects.all().delete()

# Delete endpoint configuration
sm_client = boto3.client('sagemaker')
sm_client.delete_endpoint_config(
    EndpointConfigName=predictor.endpoint_name
)
```

---

## Next Steps

1. Explore SageMaker JumpStart for pre-trained models
2. Learn about SageMaker Canvas for no-code fine-tuning
3. Implement MLOps with SageMaker Pipelines
4. Set up model monitoring for production