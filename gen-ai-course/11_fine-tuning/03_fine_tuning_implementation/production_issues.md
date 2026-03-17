# Production Issues and Debugging Guide

## Overview

This document covers common production issues encountered during fine-tuning LLMs, along with debugging steps and solutions.

---

## Table of Contents

1. [Memory Issues](#1-memory-issues)
2. [Training Issues](#2-training-issues)
3. [Model Quality Issues](#3-model-quality-issues)
4. [Cloud Platform Issues](#4-cloud-platform-issues)
5. [Deployment Issues](#5-deployment-issues)
6. [Monitoring and Debugging](#6-monitoring-and-debugging)

---

## 1. Memory Issues

### Issue 1.1: CUDA Out of Memory (OOM)

**Symptoms:**
```
RuntimeError: CUDA out of memory. Tried to allocate X.XX GiB
```

**Debug Steps:**

```python
# 1. Check current GPU memory usage
import torch
print(f"Allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
print(f"Cached: {torch.cuda.memory_reserved() / 1e9:.2f} GB")

# 2. Check memory breakdown
print(torch.cuda.memory_summary(device=0))
```

**Solutions:**

1. **Reduce batch size:**
```python
training_args = TrainingArguments(
    per_device_train_batch_size=1,  # Reduce from 4 to 1
    gradient_accumulation_steps=8,   # Compensate with accumulation
)
```

2. **Enable gradient checkpointing:**
```python
model.gradient_checkpointing_enable()
# Or in TrainingArguments
training_args = TrainingArguments(
    gradient_checkpointing=True,
)
```

3. **Use quantization:**
```python
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
)
```

4. **Reduce sequence length:**
```python
# Use shorter max_length
tokenizer = AutoTokenizer.from_pretrained(model_name, model_max_length=512)
```

5. **Offload to CPU:**
```python
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="cpu",
    # Or use "auto" for automatic placement
)
```

---

### Issue 1.2: Memory Leak

**Symptoms:**
- GPU memory increases over time
- Memory not freed after training

**Debug Steps:**

```python
# Monitor memory over time
import torch
import time

for step in range(100):
    # Training step
    loss = trainer.train_step()
    
    # Check memory
    if step % 10 == 0:
        print(f"Step {step}: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
        torch.cuda.empty_cache()
```

**Solutions:**

1. **Clear cache regularly:**
```python
torch.cuda.empty_cache()

# In training loop
if step % 100 == 0:
    torch.cuda.empty_cache()
```

2. **Delete unused objects:**
```python
# Delete large objects
del large_tensor
del model
torch.cuda.empty_cache()
```

3. **Use garbage collection:**
```python
import gc
gc.collect()
torch.cuda.empty_cache()
```

---

## 2. Training Issues

### Issue 2.1: Training Not Converging

**Symptoms:**
- Loss stays constant
- Loss increases
- Loss oscillates

**Debug Steps:**

```python
# 1. Check learning rate
print(f"Learning rate: {trainer.args.learning_rate}")

# 2. Check model output
outputs = model(**inputs)
print(f"Logits shape: {outputs.logits.shape}")
print(f"Loss: {outputs.loss}")

# 3. Check data
print(f"Sample input: {tokenizer.decode(inputs['input_ids'][0])}")
```

**Solutions:**

1. **Adjust learning rate:**
```python
training_args = TrainingArguments(
    learning_rate=1e-4,  # Try lower
    # Or try different scheduler
    lr_scheduler_type="cosine",
)
```

2. **Check data format:**
```python
# Ensure labels are correctly set
def tokenize_function(examples):
    tokenized = tokenizer(examples["text"], ...)
    tokenized["labels"] = tokenized["input_ids"].clone()
    return tokenized
```

3. **Warm up learning rate:**
```python
training_args = TrainingArguments(
    warmup_ratio=0.1,
    warmup_steps=100,
)
```

---

### Issue 2.2: Loss = NaN

**Symptoms:**
```
RuntimeError: ValueError: Loss is NaN
```

**Debug Steps:**

```python
# Check for NaN in inputs
import numpy as np
print(np.isnan(inputs['input_ids'].numpy()).any())

# Check data for issues
for i, example in enumerate(dataset):
    if any(v is None or (isinstance(v, str) and len(v) == 0) 
           for v in [example['instruction'], example['output']]):
        print(f"Empty field in example {i}")
```

**Solutions:**

1. **Add loss filtering:**
```python
# Filter problematic examples
def filter_nan_labels(example):
    if 'labels' in example:
        return not any(np.isnan(example['labels']))
    return True

dataset = dataset.filter(filter_nan_labels)
```

2. **Use stable loss computation:**
```python
training_args = TrainingArguments(
    fp16=True,  # Use fp16 instead of bf16 if hardware unstable
    loss_scale="dynamic",
)
```

3. **Clip gradients:**
```python
training_args = TrainingArguments(
    max_grad_norm=1.0,
)
```

---

### Issue 2.3: Slow Training

**Symptoms:**
- Training takes very long
- Low throughput

**Debug Steps:**

```python
# Check throughput
from transformers import TrainerCallback

class ThroughputCallback(TrainerCallback):
    def on_log(self, args, state, control, logs=None):
        if 'train_runtime' in logs:
            print(f"Steps per second: {state.max_steps / logs['train_runtime']:.2f}")
```

**Solutions:**

1. **Increase batch size:**
```python
training_args = TrainingArguments(
    per_device_train_batch_size=8,  # Increase
    gradient_accumulation_steps=1,   # Reduce accumulation
)
```

2. **Disable gradient checkpointing (sacrifices memory for speed):**
```python
model.gradient_checkpointing_disable()
```

3. **Use Flash Attention:**
```python
# Install flash-attn
!pip install flash-attn

# Use in model config
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    attn_implementation="flash_attention_2",
)
```

4. **Use faster optimizer:**
```python
training_args = TrainingArguments(
    optim="adamw_torch",  # Or "adamw_bnb_8bit"
)
```

---

## 3. Model Quality Issues

### Issue 3.1: Model Generates Garbage

**Symptoms:**
- Random characters
- Repetitive text
- Nonsensical output

**Debug Steps:**

```python
# Test with simple prompt
prompt = "Explain AI in one sentence:"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

output = model.generate(**inputs, max_new_tokens=50)
print(tokenizer.decode(output[0]))
```

**Solutions:**

1. **Check tokenizer:**
```python
# Ensure pad token is set
tokenizer.pad_token = tokenizer.eos_token
```

2. **Fine-tune longer:**
```python
training_args = TrainingArguments(
    num_train_epochs=5,  # Increase
)
```

3. **Use better base model:**
```python
# Try instruction-tuned model
model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
```

---

### Issue 3.2: Catastrophic Forgetting

**Symptoms:**
- Model loses original capabilities
- Can't perform simple tasks it could before

**Debug Steps:**

```python
# Test before and after on held-out tasks
def evaluate_task(task_prompt):
    output = generate(task_prompt)
    return score(output)
```

**Solutions:**

1. **Use lower learning rate:**
```python
training_args = TrainingArguments(
    learning_rate=5e-5,  # Lower than default
)
```

2. **Mix with original data:**
```python
# Combine fine-tuning data with original instruction data
combined_dataset = concatenate_datasets([
    fine_tuning_data,
    original_instruct_data,
])
```

3. **Use gradual unfreezing:**
```python
# Freeze most layers initially
for name, param in model.named_parameters():
    if "layer" not in name:
        param.requires_grad = False
```

---

## 4. Cloud Platform Issues

### Issue 4.1: Azure - Insufficient Quota

**Symptoms:**
```
OperationNotAllowed: Subscription quota exceeded
```

**Solutions:**

1. **Request quota increase:**
```python
# In Azure Portal
# Subscriptions → Your Sub → Usage + quotas
# Request increase for NC series
```

2. **Use smaller instance:**
```python
compute = AmlCompute(
    name="small-cluster",
    size="Standard_NC6s_v3",  # Smaller than NC24s_v3
)
```

---

### Issue 4.2: AWS - Spot Instance Interruption

**Symptoms:**
```
CapacityNotAvailableException
```

**Solutions:**

1. **Enable checkpointing:**
```python
training_args = TrainingArguments(
    # Save checkpoint before interruption
    save_strategy="steps",
    save_steps=100,
)
```

2. **Use on-demand instances:**
```python
huggingface_estimator = HuggingFace(
    use_spot_instances=False,
)
```

---

### Issue 4.3: GCP - Permission Errors

**Symptoms:**
```
Permission 'aiplatform.endpoints.predict' denied
```

**Solutions:**

```python
# Grant required roles to service account
# In GCP Console:
# IAM & Admin → IAM
# Add role: Vertex AI User
```

---

## 5. Deployment Issues

### Issue 5.1: Model Too Large for Inference

**Symptoms:**
- Slow inference
- High memory usage in production

**Solutions:**

1. **Quantize for inference:**
```python
# Convert to 8-bit
model = model.quantize(8)
```

2. **Use smaller batch size:**
```python
predictor = model.deploy(
    instance_type="ml.t2.medium",  # CPU
    instance_count=1,
)
```

3. **Use optimization libraries:**
```python
# Use vLLM for faster inference
from vllm import LLM, SamplingParams
llm = LLM(model="your-model")
```

---

### Issue 5.2: High Latency

**Symptoms:**
- Slow response times
- Timeout errors

**Solutions:**

1. **Cache model in memory:**
```python
# Keep model loaded in memory
model = load_model()
```

2. **Use streaming:**
```python
# Stream responses
for text in generate_stream(prompt):
    print(text)
```

3. **Use optimized inference engine:**
```python
# Use TensorRT-LLM
# Or vLLM with PagedAttention
```

---

## 6. Monitoring and Debugging

### 6.1 Enable Comprehensive Logging

```python
import logging

# Set logging level
logging.basicConfig(level=logging.INFO)

# Log training metrics
training_args = TrainingArguments(
    logging_dir="./logs",
    logging_steps=1,
    log_level="debug",
)
```

### 6.2 Use Callbacks for Debugging

```python
from transformers import TrainerCallback

class DebugCallback(TrainerCallback):
    def on_log(self, args, state, control, logs=None):
        print(f"Step {state.global_step}: {logs}")
    
    def on_train_begin(self, args, state, control):
        print("Training started!")
    
    def on_train_end(self, args, state, control):
        print("Training ended!")

trainer = Trainer(
    model=model,
    callbacks=[DebugCallback()],
)
```

### 6.3 Debug WandB Integration

```python
# Install wandb
!pip install wandb

# Login
!wandb login

# Track with wandb
training_args = TrainingArguments(
    report_to="wandb",
    run_name="fine-tuning-run",
)
```

---

## Quick Reference: Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| CUDA OOM | GPU memory full | Reduce batch size, enable gradient checkpointing |
| NaN loss | Numerical instability | Use fp16, clip gradients |
| Tokenizer error | Special chars | Use correct encoding |
| Model not found | Wrong path | Check model ID |
| Permission denied | IAM issue | Check service account |
| Quota exceeded | Cloud limit | Request increase |

---

## Emergency Checklist

When encountering issues:

1. ✅ Check GPU memory: `nvidia-smi`
2. ✅ Check Python version: `python --version`
3. ✅ Check package versions: `pip list | grep -E "torch|transformers|peft"`
4. ✅ Check data format: print first 3 examples
5. ✅ Test with small dataset
6. ✅ Enable logging
7. ✅ Clear cache: `torch.cuda.empty_cache()`
8. ✅ Restart kernel/runtime