# Hands-on: Fine-tuning with GCP Vertex AI

## Overview

This hands-on guide demonstrates how to fine-tune Large Language Models using Google Cloud Platform (GCP) Vertex AI. Vertex AI provides powerful infrastructure with TPU support, integration with Google Cloud services, and enterprise-grade features.

## Prerequisites

- Google Cloud Platform Account
- GCP Project with billing enabled
- Cloud Storage Bucket
- HuggingFace account and token

## Estimated Duration

90-120 minutes

---

## Step 1: GCP Environment Setup

### 1.1 Install Dependencies

```bash
pip install google-cloud-aiplatform google-cloud-storage
```

### 1.2 Authenticate

```python
from google.auth import default

# Authenticate
credentials, project_id = default()

print(f"Project ID: {project_id}")
```

### 1.3 Initialize Vertex AI

```python
from google.cloud import aiplatform

# Initialize
project_id = "your-project-id"
location = "us-central1"  # or us-east1, europe-west4, etc.

aiplatform.init(
    project=project_id,
    location=location,
    staging_bucket="gs://your-bucket-name",
    experiment="fine-tuning-experiment",
)

print(f"Vertex AI initialized in {location}")
```

---

## Step 2: Prepare Cloud Storage

### 2.1 Create Bucket

```python
from google.cloud import storage

# Create client
storage_client = storage.Client()

# Create bucket
bucket_name = "your-unique-bucket-name"
bucket = storage_client.create_bucket(
    bucket_name,
    location="US",
    project=project_id
)

print(f"Bucket created: {bucket.name}")
```

### 2.2 Upload Training Data

```python
# Upload training data
bucket = storage_client.bucket(bucket_name)

# Upload train data
blob_train = bucket.blob("fine-tuning/train.jsonl")
blob_train.upload_from_filename("train.jsonl")

# Upload test data
blob_test = bucket.blob("fine-tuning/test.jsonl")
blob_test.upload_from_filename("test.jsonl")

print("Data uploaded to Cloud Storage")
print(f"Train: gs://{bucket_name}/fine-tuning/train.jsonl")
print(f"Test: gs://{bucket_name}/fine-tuning/test.jsonl")
```

---

## Step 3: Create Training Script

### 3.1 Create train.py

```python
# Create training script
train_code = '''
import os
import json
from google.cloud import storage
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
MODEL_NAME = os.environ.get("MODEL_NAME", "meta-llama/Meta-Llama-3-8B")
TRAIN_DATA_PATH = os.environ.get("TRAIN_DATA_PATH")
TEST_DATA_PATH = os.environ.get("TEST_DATA_PATH")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/tmp/model")

print(f"Model: {MODEL_NAME}")
print(f"Train data: {TRAIN_DATA_PATH}")
print(f"Test data: {TEST_DATA_PATH}")

# Download data from GCS
def download_from_gcs(bucket_name, source_blob, destination_file):
    """Download file from Google Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob)
    blob.download_to_filename(destination_file)
    print(f"Downloaded: {source_blob} -> {destination_file}")

# Extract bucket name and paths
train_bucket = TRAIN_DATA_PATH.replace("gs://", "").split("/")[0]
test_bucket = TEST_DATA_PATH.replace("gs://", "").split("/")[0]
train_path = "/".join(TRAIN_DATA_PATH.replace("gs://", "").split("/")[1:])
test_path = "/".join(TEST_DATA_PATH.replace("gs://", "").split("/")[1:])

# Download data
download_from_gcs(train_bucket, train_path, "train.jsonl")
download_from_gcs(test_bucket, test_path, "test.jsonl")

# Load datasets
train_data = load_dataset("json", data_files="train.jsonl")["train"]
test_data = load_dataset("json", data_files="test.jsonl")["test"]

print(f"Train size: {len(train_data)}")
print(f"Test size: {len(test_data)}")

# Configure quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype="float16",
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

# Format and tokenize data
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

# Save model
print("Saving model...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

# Upload model to GCS
def upload_to_gcs(bucket_name, source_dir, destination_prefix):
    """Upload files to Google Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    import os
    import glob
    
    for file_path in glob.glob(os.path.join(source_dir, "**"), recursive=True):
        if os.path.isfile(file_path):
            relative_path = os.path.relpath(file_path, source_dir)
            blob = bucket.blob(f"{destination_prefix}/{relative_path}")
            blob.upload_from_filename(file_path)
            print(f"Uploaded: {relative_path}")

upload_to_gcs("your-bucket-name", OUTPUT_DIR, "model/output")
print("Model uploaded to GCS")
'''

# Save training script
with open("train.py", "w") as f:
    f.write(train_code)

print("Training script created!")
```

### 3.2 Create Dockerfile (for custom container)

```dockerfile
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy training script
COPY train.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run training
CMD ["python", "train.py"]
```

### 3.3 Create requirements.txt

```
transformers>=4.28.0
datasets>=2.14.0
peft>=0.4.0
accelerate>=0.20.0
bitsandbytes>=0.39.0
torch>=2.0.0
google-cloud-storage
```

---

## Step 4: Create Custom Training Job

### 4.1 Build Container Image

```bash
# Build and push container image
IMAGE_NAME = "llama-finetuning"
IMAGE_TAG = "latest"
PROJECT_ID = "your-project-id"

IMAGE_URI = f"gcr.io/{PROJECT_ID}/{IMAGE_NAME}:{IMAGE_TAG}"

# Build using Cloud Build
!gcloud builds submit --tag $IMAGE_URI .
```

### 4.2 Define Training Job

```python
from google.cloud import aiplatform

# Create custom training job
job = aiplatform.CustomTrainingJob(
    display_name="llama-finetuning-job",
    script_path="train.py",
    container_uri=f"gcr.io/{project_id}/llama-finetuning:latest",
    requirements=[
        "transformers>=4.28.0",
        "datasets>=2.14.0",
        "peft>=0.4.0",
        "accelerate>=0.20.0",
        "bitsandbytes>=0.39.0",
        "google-cloud-storage>=2.10.0",
    ],
    model_serving_container_image_uri="pytorch/torchserve:latest",
)
```

### 4.3 Run Training Job

```python
# Set environment variables
env = {
    "MODEL_NAME": "meta-llama/Meta-Llama-3-8B",
    "TRAIN_DATA_PATH": f"gs://{bucket_name}/fine-tuning/train.jsonl",
    "TEST_DATA_PATH": f"gs://{bucket_name}/fine-tuning/test.jsonl",
    "HF_TOKEN": "your-hf-token",
}

# Run training
model = job.run(
    replica_count=1,
    machine_type="a2-highgpu-1g",  # A100 GPU
    accelerator_type="NVIDIA_TESLA_A100",
    accelerator_count=1,
    base_output_dir=f"gs://{bucket_name}/output",
    service_account=f"your-service-account@{project_id}.iam.gserviceaccount.com",
    env=env,
    tensorboard=True,  # Enable TensorBoard
)

print(f"Training completed! Model: {model}")
```

---

## Step 5: Monitor Training

### 5.1 Check Job Status

```python
# Get job resource
job_name = "projects/{}/locations/{}/trainingPipelines/{}".format(
    project_id, location, job.resource_name
)

# Get job details
job = aiplatform.get_training_pipeline(job_name)
print(f"Job state: {job.state}")
print(f"Create time: {job.create_time}")
```

### 5.2 View in Console

Navigate to:
- Google Cloud Console → Vertex AI → Training
- View job details
- Access TensorBoard logs

---

## Step 6: Deploy Model

### 6.1 Register Model

```python
# Register the trained model
model = aiplatform.Model.upload(
    display_name="llama-finetuned",
    artifact_uri=f"gs://{bucket_name}/model/output",
    serving_container_image_uri=f"gcr.io/{project_id}/llama-finetuning:latest",
    description="Fine-tuned Llama model",
)

print(f"Model registered: {model.name}")
```

### 6.2 Create Endpoint

```python
# Create endpoint
endpoint = aiplatform.Endpoint.create(
    display_name="llama-endpoint",
    description="Fine-tuned Llama endpoint",
)

print(f"Endpoint created: {endpoint.name}")
```

### 6.3 Deploy to Endpoint

```python
# Deploy model to endpoint
deployed_model = endpoint.deploy(
    model=model,
    deployed_model_display_name="llama-finetuned",
    machine_type="n1-standard-8",
    accelerator_type="NVIDIA_TESLA_T4",
    accelerator_count=1,
    traffic_split={"0": 100},
)

print(f"Model deployed! Endpoint: {endpoint.name}")
```

### 6.4 Test Prediction

```python
# Make prediction
response = endpoint.predict(
    instances=[{
        "inputs": "Explain quantum computing in simple terms",
        "parameters": {
            "max_new_tokens": 150,
            "temperature": 0.7,
            "top_p": 0.9,
        }
    }]
)

print(response.predictions)
```

---

## Step 7: Use Pre-built Containers

### 7.1 HuggingFace Container

```python
# Use HuggingFace pre-built container
job = aiplatform.CustomTrainingJob(
    display_name="llama-finetuning-hf",
    script_path="train.py",
    container_uri="gcr.io/cloud-aiplatform/training/pytorch-gpu.1-13:latest",
    requirements=[
        "transformers>=4.28.0",
        "datasets>=2.14.0",
        "peft>=0.4.0",
    ],
)

# Run with pre-built container
model = job.run(
    machine_type="a2-highgpu-1g",
    accelerator_type="NVIDIA_TESLA_A100",
    accelerator_count=1,
)
```

---

## Step 8: Vertex AI Feature Comparison

### Available Accelerators

| Accelerator | Memory | Best For |
|-------------|--------|----------|
| NVIDIA_TESLA_T4 | 16GB | Inference, small models |
| NVIDIA_TESLA_V100 | 32GB | Medium fine-tuning |
| NVIDIA_TESLA_A100 | 40GB/80GB | Large fine-tuning |
| TPU_V4 | 80GB HBM | Very large models |

### Machine Types

| Type | vCPUs | Memory | Use Case |
|------|-------|--------|----------|
| n1-standard-4 | 4 | 15GB | Testing |
| n1-standard-8 | 8 | 30GB | Small training |
| n1-standard-16 | 16 | 60GB | Medium training |
| a2-highgpu-1g | 12 | 85GB | GPU training |

---

## Step 9: Cost Optimization

### 9.1 Use Preemptible VMs

```python
# Note: Vertex AI uses "spot" equivalent through
# machine configuration in some regions
```

### 9.2 Set Budget Alerts

```python
# Set up billing alerts in Google Cloud Console
# Billing → Budgets & alerts → Create budget
```

### 9.3 Use Commitment Discounts

```python
# Purchase committed use discounts
# Go to: Compute Engine → Committed use discounts
```

---

## Step 10: Advanced Features

### 10.1 Vertex AI Feature Store

```python
# Store and serve features for RAG
from google.cloud import aiplatform

# Create feature store
feature_store = aiplatform.Featurestore.create(
    featurestore_id="llama-features",
    online_serving_fixed_nodes=1,
)
```

### 10.2 Vertex AI Model Registry

```python
# Register model with metadata
model = aiplatform.Model.upload(
    display_name="llama-finetuned-v2",
    artifact_uri=f"gs://{bucket_name}/model/output",
    container_uri="pytorch/torchserve:latest",
    metadata=[  # Add metadata
        {"training_dataset": "custom-dataset-v1"},
        {"base_model": "llama-3-8b"},
        {"fine_tuning_method": "lora"},
    ]
)
```

### 10.3 Vertex AI Experiments

```python
# Track experiments
aiplatform.init(experiment="fine-tuning-exp")

with aiplatform.start_run(run_name="run-1"):
    # Log metrics
    aiplatform.log_metrics({"train_loss": 0.5, "eval_loss": 0.3})
    
    # Log parameters
    aiplatform.log_params({
        "learning_rate": 2e-4,
        "lora_r": 16,
    })
```

---

## Common Issues

### Issue 1: Permission Denied

**Solution:**
```python
# Ensure service account has required permissions
# Storage Object Admin
# Vertex AI User
# Compute Admin
```

### Issue 2: Quota Exceeded

**Solution:**
```
# Request quota increase in Google Cloud Console
# IAM & Admin → Quotas
```

### Issue 3: Container Build Failed

**Solution:**
- Check Dockerfile syntax
- Verify base image availability
- Check Cloud Build logs

---

## Clean Up

```python
# Delete endpoint
endpoint.delete(force=True)

# Delete model
model.delete()

# Delete training job
job.delete()

# Delete storage
bucket = storage_client.bucket(bucket_name)
bucket.delete(force=True)
```

---

## Exercises

### Exercise 1: Different Machine Types

Try different configurations:
- `n1-standard-8` with T4
- `a2-highgpu-1g` with A100
- Multi-replica training

### Exercise 2: Different Models

Experiment with:
- `meta-llama/Meta-Llama-3-8B`
- `mistralai/Mistral-7B-Instruct-v0.2`
- `google/gemma-7b`

### Exercise 3: Experiment Tracking

Use Vertex AI Experiments to:
- Compare different hyperparameters
- Track metrics across runs
- Log artifacts

---

## Next Steps

1. Explore Vertex AI AutoML for no-code fine-tuning
2. Learn about prediction Explainability
3. Set up Model Monitoring for production
4. Implement CI/CD with Cloud Build