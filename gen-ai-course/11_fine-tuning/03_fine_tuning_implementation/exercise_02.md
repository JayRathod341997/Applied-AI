# Exercise 02: Multi-Platform Fine-tuning Comparison

## Objective

Compare fine-tuning across multiple platforms and analyze the differences.

## Difficulty

Intermediate

## Time Duration

60 minutes

---

## Requirements

### Task 1: Setup Identical Environment (20 minutes)

Create a Python script that:
1. Loads the same base model (`TinyLlama/TinyLlama-1.1B-Chat-v1.0`)
2. Uses identical training data
3. Applies the same LoRA configuration
4. Trains for 1 epoch

### Task 2: Run Locally with HuggingFace (15 minutes)

Execute the training using HuggingFace Trainer:
- Use local GPU or Colab
- Record training time and memory usage
- Save model locally

### Task 3: Create Cloud Configuration (15 minutes)

Create configuration files for:
- Azure ML
- AWS SageMaker  
- GCP Vertex AI

Each configuration should specify:
- Same hyperparameters
- Same model
- Same data path format

### Task 4: Compare Results (10 minutes)

Document comparison:

| Metric | Local/HF | Azure | AWS | GCP |
|--------|----------|-------|-----|-----|
| Training Time | ? | ? | ? | ? |
| Memory Used | ? | ? | ? | ? |
| Cost | ? | ? | ? | ? |
| Ease of Setup | ? | ? | ? | ? |

---

## Code Template

```python
"""
Multi-Platform Fine-tuning Comparison
"""

# Configuration (same across all platforms)
CONFIG = {
    "model_name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "lora_config": {
        "r": 8,
        "lora_alpha": 16,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
    },
    "training": {
        "num_train_epochs": 1,
        "per_device_train_batch_size": 2,
        "learning_rate": 2e-4,
    },
}

# Task 1: Data Loading
def load_data():
    """Load training data."""
    # TODO: Load JSONL file
    pass

# Task 2: HuggingFace Training
def train_huggingface(data, config):
    """Train using HuggingFace Trainer."""
    # TODO: Implement training
    pass

# Task 3: Azure Config
def get_azure_config(config):
    """Get Azure ML configuration."""
    # TODO: Return Azure-specific config
    return {
        "compute_name": "gpu-cluster",
        "vm_size": "Standard_NC4as_T4_v3",
        "env": {
            "MODEL_NAME": config["model_name"],
        }
    }

# Task 4: AWS Config
def get_aws_config(config):
    """Get AWS SageMaker configuration."""
    # TODO: Return AWS-specific config
    return {
        "instance_type": "ml.g4dn.xlarge",
        "hyperparameters": config["training"],
    }

# Task 5: GCP Config
def get_gcp_config(config):
    """Get GCP Vertex AI configuration."""
    # TODO: Return GCP-specific config
    return {
        "machine_type": "n1-standard-4",
        "accelerator_type": "NVIDIA_TESLA_T4",
    }

if __name__ == "__main__":
    # Execute tasks
    print("Starting multi-platform comparison...")
    
    # Task 1
    data = load_data()
    
    # Task 2
    result = train_huggingface(data, CONFIG)
    print(f"HuggingFace training: {result}")
    
    # Task 3-4
    print("\nPlatform configurations:")
    print(f"Azure: {get_azure_config(CONFIG)}")
    print(f"AWS: {get_aws_config(CONFIG)}")
    print(f"GCP: {get_gcp_config(CONFIG)}")
```

---

## Expected Output

1. Working local training script
2. Three cloud platform configuration files
3. Comparison table with metrics
4. Analysis report (500 words)

---

## Submission

- Python script with all tasks implemented
- Screenshots of training runs
- Comparison table
- Analysis report