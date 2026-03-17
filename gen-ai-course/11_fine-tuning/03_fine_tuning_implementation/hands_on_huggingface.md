# Hands-on: Fine-tuning with Hugging Face Trainer

## Overview

This hands-on guide demonstrates fine-tuning using the Hugging Face Transformers library and Trainer API. This approach is portable and works locally or on any cloud platform.

## Prerequisites

- Python 3.8+
- GPU with 16GB+ VRAM (recommended)
- HuggingFace account for token

## Estimated Duration

60-90 minutes

---

## Step 1: Environment Setup

### 1.1 Install Dependencies

```bash
pip install transformers datasets peft accelerate bitsandbytes torch
```

### 1.2 Authentication

```python
from huggingface_hub import login

# Login to HuggingFace
login(token="your_hf_token_here")

# Or use terminal
# huggingface-cli login
```

---

## Step 2: Load Base Model

### 2.1 Configure Quantization

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Configure 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",      # Normalized float 4-bit
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True, # Nested quantization
)
```

### 2.2 Load Tokenizer

```python
# Load tokenizer
model_name = "meta-llama/Meta-Llama-3-8B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    token="your_hf_token"
)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"
```

### 2.3 Load Model

```python
# Load model with quantization
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    token="your_hf_token"
)

# Set model to training mode
model.train()

print(f"Model loaded: {model.num_parameters() / 1e9:.2f}B parameters")
```

---

## Step 3: Apply LoRA

### 3.1 Configure LoRA

```python
from peft import LoraConfig, get_peft_model, TaskType

# LoRA configuration
lora_config = LoraConfig(
    r=16,                         # Rank of LoRA matrices
    lora_alpha=32,               # LoRA scaling parameter
    lora_dropout=0.05,           # Dropout probability
    target_modules=[             # Which layers to apply LoRA
        "q_proj", 
        "k_proj", 
        "v_proj", 
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj"
    ],
    bias="none",                 # No bias in LoRA layers
    task_type=TaskType.CAUSAL_LM,
)
```

### 3.2 Apply LoRA to Model

```python
# Apply LoRA adapters
model = get_peft_model(model, lora_config)

# Print trainable parameters
model.print_trainable_parameters()

# Output example:
# trainable params: 41,218,048 
# all params: 8,030,261,248 
# trainable%: 0.51%
```

---

## Step 4: Prepare Dataset

### 4.1 Create Training Data

```python
import json
from datasets import Dataset

# Create sample training data
training_data = [
    {
        "instruction": "Summarize the following text",
        "input": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data and use it to learn patterns and make decisions.",
        "output": "Machine learning is AI that allows systems to learn from data and improve through experience without explicit programming."
    },
    {
        "instruction": "Explain in simple terms",
        "input": "What is neural network?",
        "output": "A neural network is a computer system modeled on the human brain. It consists of interconnected nodes (like neurons) that process information, learning to recognize patterns and make decisions."
    },
    {
        "instruction": "Translate to Spanish",
        "input": "Good morning, how are you?",
        "output": "Buenos días, ¿cómo estás?"
    }
]

# Create dataset
train_data = [
    {"instruction": d["instruction"], "input": d["input"], "output": d["output"]}
    for d in training_data
]

# Convert to HuggingFace dataset
dataset = Dataset.from_list(train_data)
print(f"Dataset: {dataset}")
```

### 4.2 Create Formatting Function

```python
def format_prompts(examples):
    """Format instruction-following data."""
    instructions = examples["instruction"]
    inputs = examples["input"]
    outputs = examples["output"]
    
    formatted_texts = []
    for instruction, input_text, output in zip(instructions, inputs, outputs):
        text = f"""<|start_header_id|>system<|end_header_id|>

You are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>

Instruction: {instruction}
Input: {input_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{output}<|eot_id|>"""
        formatted_texts.append(text)
    
    return {"text": formatted_texts}

# Apply formatting
dataset = dataset.map(format_prompts, batched=True)
```

### 4.3 Tokenize

```python
def tokenize_function(examples):
    """Tokenize text for training."""
    # Tokenize with padding
    tokenized = tokenizer(
        examples["text"],
        padding="max_length",
        truncation=True,
        max_length=512,
        return_tensors="pt"
    )
    
    # Set labels (same as input for causal LM)
    tokenized["labels"] = tokenized["input_ids"].clone()
    
    return tokenized

# Apply tokenization
tokenized_dataset = dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=dataset.column_names,
)

# Split train/eval
train_eval = tokenized_dataset.train_test_split(test_size=0.1)
train_dataset = train_eval["train"]
eval_dataset = train_eval["test"]

print(f"Train size: {len(train_dataset)}")
print(f"Eval size: {len(eval_dataset)}")
```

---

## Step 5: Configure Training

### 5.1 Data Collator

```python
from transformers import DataCollatorForLanguageModeling

# Data collator for causal LM
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,  # Causal LM, not masked LM
)
```

### 5.2 Training Arguments

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    # Output directory
    output_dir="./llama3_finetuned",
    
    # Training steps
    num_train_epochs=3,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=4,  # Effective: 2 * 4 = 8
    
    # Optimizer
    learning_rate=2e-4,
    weight_decay=0.01,
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    
    # Evaluation
    eval_strategy="epoch",
    eval_accumulation_steps=4,
    
    # Saving
    save_strategy="epoch",
    save_total_limit=2,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    
    # Mixed precision
    fp16=True,
    bf16=False,
    
    # Logging
    logging_dir="./logs",
    logging_steps=10,
    
    # Other
    dataloader_num_workers=2,
    seed=3407,
    report_to="tensorboard",
)
```

---

## Step 6: Train the Model

### 6.1 Initialize Trainer

```python
from transformers import Trainer

# Create trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    data_collator=data_collator,
)
```

### 6.2 Start Training

```python
# Train
train_result = trainer.train()

# Get metrics
metrics = train_result.metrics
trainer.log_metrics("train", metrics)
trainer.save_metrics("train", metrics)

print(f"Training completed! Final loss: {metrics['train_loss']:.4f}")
```

---

## Step 7: Save Model

### 7.1 Save Locally

```python
# Save model and tokenizer
trainer.save_model("./final_model")
tokenizer.save_pretrained("./final_model")

# Also save training state
trainer.save_state()
```

### 7.2 Push to Hub

```python
# Push to HuggingFace Hub
model.push_to_hub("your-username/llama3-finetuned")
tokenizer.push_to_hub("your-username/llama3-finetuned")
```

---

## Step 8: Inference

### 8.1 Load Fine-tuned Model

```python
# Load for inference
from peft import PeftModel
from transformers import AutoModelForCausalLM

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    token="your_hf_token"
)

# Load LoRA adapters
model = PeftModel.from_pretrained(
    base_model, 
    "./final_model"
)

# Set to eval mode
model.eval()
```

### 8.2 Generate

```python
# Test prompt
prompt = """<|start_header_id|>system<|end_header_id|>

You are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>

Instruction: Explain in simple terms
Input: What is deep learning?
<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

# Generate
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

output = model.generate(
    **inputs,
    max_new_tokens=150,
    temperature=0.7,
    top_p=0.9,
    do_sample=True,
)

response = tokenizer.decode(output[0], skip_special_tokens=True)
print(response)
```

---

## Advanced: Using SFTTrainer

### What is SFTTrainer?

SFTTrainer (Supervised Fine-tuning Trainer) from TRL library simplifies the fine-tuning process.

```python
from trl import SFTTrainer
from transformers import TrainingArguments

# SFTTrainer
trainer = SFTTrainer(
    model=model,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    dataset_text_field="text",
    max_seq_length=512,
    tokenizer=tokenizer,
    args=TrainingArguments(
        output_dir="./sft_finetuned",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        learning_rate=2e-4,
    ),
)

trainer.train()
```

---

## Common Issues

### 1. CUDA Out of Memory

**Solutions:**
```python
# Reduce batch size
per_device_train_batch_size=1

# Enable gradient checkpointing
model.gradient_checkpointing_enable()

# Use more aggressive quantization
load_in_4bit=True
```

### 2. Training is Very Slow

**Solutions:**
- Use A100 GPU
- Increase batch size
- Use gradient checkpointing=False (sacrifices memory for speed)
- Use Flash Attention

### 3. Model Not Generating Coherent Text

**Solutions:**
- Check learning rate (try lower)
- Increase training epochs
- Verify data formatting
- Ensure tokenizer is correct

---

## Exercises

### Exercise 1: Different Base Models

Try fine-tuning:
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (small, fast)
- `microsoft/Phi-3-mini-4k-instruct`
- `Qwen/Qwen2-7B-Instruct`

### Exercise 2: Hyperparameter Tuning

Experiment with:
- LoRA r: [8, 16, 32, 64]
- Learning rate: [1e-5, 2e-5, 5e-5, 1e-4]
- Epochs: [1, 2, 3, 5]

### Exercise 3: Custom Dataset

Fine-tune on your own dataset:
- Customer support chats
- Code documentation
- Domain-specific knowledge

---

## Next Steps

1. Explore RAG + Fine-tuning combinations
2. Learn about DPO (Direct Preference Optimization)
3. Deploy model with vLLM for fast inference
4. Experiment with fine-tuning on consumer GPUs