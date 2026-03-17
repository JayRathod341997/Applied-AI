# Hands-on: Fine-tuning with Unsloth and Google Colab

## Overview

This hands-on guide walks you through fine-tuning a Large Language Model using Unsloth on Google Colab. Unsloth provides 2x faster training with 70% less memory usage.

## Prerequisites

- Google Account (for Colab)
- HuggingFace Account (for model access)
- Access to Meta Llama models (or use open models)

## Estimated Duration

45-60 minutes

---

## Step 1: Environment Setup

### 1.1 Open Google Colab

1. Go to [colab.research.google.com](https://colab.research.google.com)
2. Create a new notebook
3. Select GPU runtime (Runtime → Change runtime type → GPU)

### 1.2 Install Dependencies

```python
# Install Unsloth
!pip install unsloth

# Also install required packages
!pip install transformers datasets peft accelerate bitsandbytes
```

### 1.3 Verify GPU

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
```

---

## Step 2: Prepare Training Data

### 2.1 Create Sample Dataset

```python
# Create a sample JSONL file for instruction fine-tuning
import json

training_data = [
    {
        "instruction": "Summarize the following article",
        "input": "Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural intelligence displayed by humans or animals. AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of successfully achieving its goals.",
        "output": "Artificial Intelligence (AI) refers to machine-displayed intelligence, as opposed to natural intelligence in humans or animals. It focuses on creating intelligent agents that perceive their environment and take actions to achieve specific goals."
    },
    {
        "instruction": "Translate to French",
        "input": "Hello, how are you today?",
        "output": "Bonjour, comment allez-vous aujourd'hui?"
    },
    {
        "instruction": "Explain the concept simply",
        "input": "What is machine learning?",
        "output": "Machine learning is a way for computers to learn from data and improve at tasks without being explicitly programmed. Instead of following strict rules, computers find patterns in examples and use those patterns to make decisions."
    }
]

# Save to file
with open('train.jsonl', 'w') as f:
    for item in training_data:
        f.write(json.dumps(item) + '\n')

print("Training data created!")
```

### 2.2 Load Dataset

```python
from datasets import load_dataset

# Load the dataset
dataset = load_dataset("json", data_files="train.jsonl")
print(f"Dataset: {dataset}")
```

---

## Step 3: Load Model with Unsloth

### 3.1 Configuration

```python
from unsloth import FastLanguageModel
import torch

# Configuration
max_seq_length = 2048  # Adjust based on VRAM
dtype = None           # Auto-detect
load_in_4bit = True   # Use 4-bit quantization to save memory

# Model selection
# Options: llama-3, mistral, phi-3, qwen, gemma
model_name = "unsloth/llama-3-8b-bnb-4bit"  # Free to use
```

### 3.2 Load Model and Tokenizer

```python
# Load model and tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)

print("Model loaded successfully!")
print(f"Model parameters: {model.num_parameters() / 1e9:.2f}B")
```

### 3.3 Add LoRA Adapters

```python
# Configure LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,                    # LoRA rank - higher = more parameters trained
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", 
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,           # LoRA scaling parameter
    lora_dropout = 0,          # Dropout for LoRA layers
    bias = "none",             # Bias type
    use_gradient_checkpointing = True,  # Reduce memory usage
    random_state = 3407,
)

# Print trainable parameters
model.print_trainable_parameters()
```

---

## Step 4: Prepare Data Formatting

### 4.1 Create Formatting Function

```python
def format_prompts(examples):
    """Format instruction data for training."""
    instructions = examples["instruction"]
    inputs = examples["input"]
    outputs = examples["output"]
    
    texts = []
    for instruction, input_text, output in zip(instructions, inputs, outputs):
        # Alpaca-style prompt template
        text = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input_text}

### Response:
{output}"""
        texts.append(text)
    
    return {"text": texts}

# Apply formatting
dataset = dataset.map(format_prompts, batched=True)
print(f"Sample formatted text:\n{dataset['train']['text'][0][:500]}...")
```

### 4.2 Tokenize Dataset

```python
# Tokenize the dataset
def tokenize_function(examples):
    """Tokenize text for training."""
    return tokenizer(
        examples["text"],
        padding="max_length",
        truncation=True,
        max_length=max_seq_length,
    )

# Apply tokenization
tokenized_dataset = dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=dataset["train"].column_names,
)

print(f"Tokenized dataset: {tokenized_dataset}")
```

---

## Step 5: Configure Training

### 5.1 Training Arguments

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    # Output
    output_dir = "llama3_finetuned",
    
    # Training steps
    num_train_epochs = 3,
    per_device_train_batch_size = 2,
    gradient_accumulation_steps = 4,  # Effective batch size = 2 * 4 = 8
    
    # Optimizer
    learning_rate = 2e-4,
    weight_decay = 0.01,
    warmup_ratio = 0.1,
    
    # Memory optimization
    fp16 = not torch.cuda.is_bf16_supported(),
    bf16 = torch.cuda.is_bf16_supported(),
    
    # Logging and saving
    logging_steps = 1,
    save_strategy = "epoch",
    save_total_limit = 2,
    
    # Other
    optim = "adamw_8bit",
    lr_scheduler_type = "linear",
    seed = 3407,
    dataloader_num_workers = 2,
    report_to = "none",  # Change to "wandb" for Weights & Biases
)
```

---

## Step 6: Train the Model

### 6.1 Initialize Trainer

```python
from unsloth import Trainer

# Create trainer
trainer = Trainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = tokenized_dataset["train"],
    args = training_args,
)
```

### 6.2 Start Training

```python
# Train!
trainer.train()

print("Training completed!")
```

### 6.3 Save Model

```python
# Save LoRA adapters
model.save_pretrained("lora_finetuned_model")
tokenizer.save_pretrained("lora_finetuned_model")

# Or save in GGUF format for llama.cpp
# model.save_pretrained_gguf("model", tokenizer)
```

---

## Step 7: Test the Fine-tuned Model

### 7.1 Load for Inference

```python
# Enable fast inference mode
FastLanguageModel.for_inference(model)

# Or reload from saved
# model, tokenizer = FastLanguageModel.from_pretrained("lora_finetuned_model")
# FastLanguageModel.for_inference(model)
```

### 7.2 Test with a Prompt

```python
# Test prompt
test_instruction = "Explain the concept simply"
test_input = "What is photosynthesis?"

prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{test_instruction}

### Input:
{test_input}

### Response:
"""

# Generate
inputs = tokenizer([prompt], return_tensors="pt").to("cuda")

from transformers import TextStreamer
text_streamer = TextStreamer(tokenizer)

_ = model.generate(
    **inputs, 
    streamer = text_streamer,
    max_new_tokens = 256,
    temperature = 0.7,
    top_p = 0.9,
)
```

---

## Common Issues and Solutions

### Issue 1: Out of Memory (OOM)

**Solution:**
- Reduce `per_device_train_batch_size`
- Enable gradient checkpointing
- Use 4-bit quantization
- Reduce `max_seq_length`

### Issue 2: Slow Training

**Solution:**
- Use A100 GPU if available
- Increase batch size
- Disable gradient checkpointing (uses more memory but faster)
- Use Flash Attention

### Issue 3: Model Not Learning

**Solution:**
- Check learning rate (try 2e-4 to 5e-5)
- Increase LoRA rank
- Verify data formatting
- Check for data leakage in validation set

---

## Exercises

### Exercise 1: Try Different Models

Experiment with different base models:
- `unsloth/mistral-7b-bnb-4bit`
- `unsloth/phi-3-bnb-4bit`
- `unsloth/gemma-7b-bnb-4bit`

### Exercise 2: Adjust LoRA Parameters

Try different LoRA configurations:
- Rank: 8, 16, 32, 64
- Alpha: 8, 16, 32, 64
- Target modules: Try targeting different modules

### Exercise 3: Add More Data

Add more training examples and observe how the model quality improves.

---

## Next Steps

After completing this hands-on, you can:
1. Try fine-tuning with your own custom dataset
2. Explore quantization options (2-bit, 4-bit, 8-bit)
3. Deploy the model for inference
4. Experiment with other fine-tuning techniques (QLoRA, full fine-tuning)