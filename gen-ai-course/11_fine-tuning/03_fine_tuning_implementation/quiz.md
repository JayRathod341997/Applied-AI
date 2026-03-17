# Quiz: Fine-tuning Implementation - Comprehensive

## Multiple Choice Questions

### Question 1
Which library provides 2x faster fine-tuning with 70% less memory?

A) Transformers
B) PEFT
C) Unsloth
D) LangChain

**Answer: C**

---

### Question 2
What is the primary benefit of using LoRA for fine-tuning?

A) Faster inference speed
B) Reduced training memory while maintaining performance
C) Better model accuracy
D) Smaller model size

**Answer: B**

---

### Question 3
Which Azure VM size provides NVIDIA Tesla A100 GPU?

A) Standard_NC6
B) Standard_NC24s_v3
C) Standard_ND96asr_v4
D) Standard_D4

**Answer: C**

---

### Question 4
In AWS SageMaker, what is the purpose of using spot instances?

A) Higher reliability
B) Lower cost (up to 90% savings)
C) Faster training
D) More memory

**Answer: B**

---

### Question 5
Which GCP feature allows you to track and compare experiments?

A) Cloud Storage
B) Vertex AI Experiments
C) BigQuery
D) Cloud Functions

**Answer: B**

---

### Question 6
What does 4-bit quantization reduce?

A) Training time
B) Model file size and memory usage
C) Number of parameters
D) Inference latency

**Answer: B**

---

### Question 7
What is catastrophic forgetting in fine-tuning?

A) Model forgets how to generate text
B) Model loses original capabilities after fine-tuning
C) Training process crashes
D) Model becomes too specialized

**Answer: B**

---

### Question 8
Which parameter controls how many LoRA matrices are trained?

A) alpha
B) dropout
C) r (rank)
D) target_modules

**Answer: C**

---

### Question 9
What is the recommended way to reduce GPU memory during training?

A) Increase batch size
B) Use gradient checkpointing
C) Reduce sequence length
D) Use fp16 instead of bf16

**Answer: B** (and also C, D)

---

### Question 10
Which cloud platform provides TPU support for training?

A) AWS
B) Azure
C) GCP
D) All of the above

**Answer: C**

---

## True or False

### Question 11
LoRA adapters can be merged with the base model for inference.

**Answer: True**

---

### Question 12
You should always use the largest available batch size for training.

**Answer: False** - Batch size should be adjusted based on available GPU memory.

---

### Question 13
Gradient checkpointing increases computation but reduces memory usage.

**Answer: True**

---

### Question 14
HuggingFace models can be fine-tuned without any cloud platform.

**Answer: True** - Using local GPU or Google Colab.

---

### Question 15
QLoRA combines quantization with LoRA for memory efficiency.

**Answer: True**

---

## Short Answer Questions

### Question 16
Name three techniques to reduce GPU memory during fine-tuning.

**Answer:**
1. Gradient checkpointing
2. 4-bit quantization (BitsAndBytes)
3. Reducing batch size
4. Reducing sequence length
5. Using LoRA instead of full fine-tuning
6. Enabling mixed precision (fp16/bf16)

---

### Question 17
What are the key steps in setting up Azure ML for fine-tuning?

**Answer:**
1. Install Azure ML SDK
2. Authenticate and connect to workspace
3. Create compute cluster with GPU
4. Upload data to Blob Storage
5. Create training script
6. Submit training job
7. Monitor training
8. Register model

---

### Question 18
What is the difference between training with HuggingFace locally vs using SageMaker?

**Answer:**
- **Local**: Full control, free with own GPU, manual setup
- **SageMaker**: Managed infrastructure, automatic scaling, built-in monitoring, pay-per-use

---

### Question 19
Why is it important to set the pad token in the tokenizer?

**Answer:**
- Prevents errors during training
- Ensures consistent padding
- Avoids NaN losses
- Required for batch processing

---

### Question 20
What should you do if training loss becomes NaN?

**Answer:**
1. Switch to fp16 from bf16
2. Enable gradient clipping
3. Check for data quality issues
4. Reduce learning rate
5. Validate data format

---

## Coding Questions

### Question 21
Write the code to load a model with 4-bit quantization using HuggingFace.

```python
# Answer:
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import torch

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Meta-Llama-3-8B",
    quantization_config=bnb_config,
    device_map="auto",
)
```

---

### Question 22
Write the code to configure LoRA for fine-tuning.

```python
# Answer:
from peft import LoraConfig, get_peft_model, TaskType

lora_config = LoraConfig(
    r=16,                    # Rank
    lora_alpha=32,           # Alpha
    lora_dropout=0.05,      # Dropout
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
```

---

### Question 23
Write the code to create a HuggingFace estimator for AWS SageMaker.

```python
# Answer:
from sagemaker.huggingface import HuggingFace

huggingface_estimator = HuggingFace(
    entry_point='train.py',
    source_dir='./',
    instance_type='ml.p3.2xlarge',
    instance_count=1,
    role=role,
    transformers_version='4.28.0',
    pytorch_version='2.0.0',
    py_version='py310',
    use_spot_instances=True,  # For cost savings
)

huggingface_estimator.fit({'train': train_input, 'test': test_input})
```

---

## Scenario-Based Questions

### Question 24
Your fine-tuning job keeps running out of memory on a 16GB GPU. What steps would you take?

**Answer:**
1. Reduce batch size from 4 to 1
2. Enable gradient checkpointing
3. Use 4-bit quantization
4. Reduce max sequence length
5. Use LoRA instead of full fine-tuning
6. Enable gradient accumulation
7. Use mixed precision (fp16)

---

### Question 25
You need to fine-tune a model for production use. Compare the options: local training vs cloud platforms.

**Answer:**

| Factor | Local | Cloud |
|--------|-------|-------|
| Cost | Hardware investment | Pay-per-use |
| Setup | Manual | Managed |
| Scalability | Limited | High |
| Maintenance | Self-managed | Provider-managed |
| Control | Full | Configurable |
| Best for | Experiments, learning | Production, scale |

---

## Scoring Guide

| Score | Interpretation |
|-------|----------------|
| 90-100% | Expert |
| 75-89% | Proficient |
| 60-74% | Competent |
| Below 60% | Needs Review |
