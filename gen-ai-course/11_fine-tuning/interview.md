# Fine-tuning - Interview Questions

This document contains interview questions and answers covering Module 11: Fine-tuning.

---

## 1. Fine-tuning Overview

### Q1: What is Fine-tuning?

**Answer:** Fine-tuning is the process of taking a pre-trained model and further training it on a specific dataset to adapt it for particular tasks or domains. It allows:

- **Domain Adaptation:** Specialize for specific fields (legal, medical, etc.)
- **Task Specialization:** Improve performance on specific tasks
- **Style Transfer:** Learn specific response styles
- **Format Learning:** Follow specific output formats

---

### Q2: When should you fine-tune vs use RAG?

**Answer:**

| Scenario | Use Fine-tuning | Use RAG |
|----------|----------------|---------|
| Specific domain | ✓ | ✓ |
| Need latest info | | ✓ |
| Limited data | | ✓ |
| Custom format/style | ✓ | |
| Cost sensitive | | ✓ |
| Fast iteration | | ✓ |

Often both are used together for best results.

---

### Q3: What are the benefits of fine-tuning?

**Answer:** Benefits:

- **Better Quality:** Tailored to your use case
- **Lower Latency:** No retrieval step needed
- **Lower Cost:** Smaller model can outperform larger
- **Offline:** Can run without API
- **Consistency:** More predictable outputs
- **Control:** More control over behavior

---

## 2. Fine-tuning Techniques

### Q4: What is LoRA fine-tuning?

**Answer:** LoRA (Low-Rank Adaptation):

- **Concept:** Train small "adapter" weights
- **Efficiency:** Doesn't modify base model weights
- **Memory:** Much less GPU memory needed
- **Speed:** Faster than full fine-tuning
- **Modular:** Can swap adapters

```python
# LoRA config
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05
)
```

---

### Q5: What is QLoRA fine-tuning?

**Answer:** QLoRA (Quantized LoRA):

- **Quantization:** Uses 4-bit quantized base model
- **LoRA:** Adds adapter weights
- **Memory Efficient:** Fine-tune large models on consumer GPUs
- **Quality:** Similar to full fine-tuning

Combines quantization with LoRA for extreme efficiency.

---

### Q6: What is PEFT fine-tuning?

**Answer:** PEFT (Parameter-Efficient Fine-Tuning):

- **Methods:** LoRA, Prefix Tuning, Prompt Tuning, etc.
- **Goal:** Minimal parameter changes
- **LoRA:** Add small matrices
- **Prefix:** Add trainable tokens
- **Prompt:** Update embeddings only
- **Comparison:** All aim to reduce compute

---

### Q7: What is Full Fine-tuning?

**Answer:** Full Fine-tuning:

- **Updates:** All model weights change
- **Resource Intensive:** Requires significant GPU memory
- **Best Quality:** Maximum adaptation
- **Risk:** Can cause catastrophic forgetting
- **Use Case:** When resources aren't limited

---

### Q8: What is catastrophic forgetting?

**Answer:** Catastrophic Forgetting:

- **Problem:** Model loses original capabilities
- **Cause:** Overwriting all weights
- **Solutions:**
  - Multi-task learning
  - Regularization
  - Keep base model separate
  - Combined with RAG

---

## 3. Implementation

### Q9: How do you implement fine-tuning with Unsloth?

**Answer:** Unsloth:

- **Library:** Fast fine-tuning for Llama, Mistral
- **Speed:** 2x faster, 70% less memory
- **Features:** 
  - Gradient checkpointing
  - 4-bit loading
  - Dynamic batch sizes

```python
from unsloth import FineTunedModel

model, tokenizer = FineTunedModel.from_pretrained(
    "model_name",
    finetune_type="lora"
)
model.train()
```

---

### Q10: How do you fine-tune with Hugging Face?

**Answer:** Hugging Face approach:

```python
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    learning_rate=2e-5
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset
)
trainer.train()
```

---

### Q11: How do you fine-tune on Azure ML?

**Answer:** Azure ML Fine-tuning:

1. **Create Compute:** GPU cluster
2. **Upload Data:** To Azure Blob
3. **Script:** Training script
4. **Configure:** ML pipeline
5. **Submit:** Run training job

```python
from azureml.core import Workspace, Experiment
# Azure ML configuration
```

---

### Q12: How do you fine-tune on AWS?

**Answer:** AWS SageMaker:

1. **S3:** Upload training data
2. **Instance:** Choose GPU instance
3. **Framework:** Use HuggingFace estimator
4. **Train:** Submit training job

```python
from sagemaker.huggingface import HuggingFace

estimator = HuggingFace(
    entry_point='train.py',
    instance_type='ml.p3.2xlarge',
    instance_count=1
)
```

---

### Q13: How do you fine-tune on GCP?

**Answer:** GCP Vertex AI:

1. **Cloud Storage:** Upload data
2. **Custom Job:** Submit training job
3. **GPU:** Use TPU/GPU resources
4. **Deploy:** Host the fine-tuned model

---

## Production Questions

### Q14: How do you evaluate fine-tuned models?

**Answer:** Evaluation:

- **Metrics:** Accuracy, BLEU, ROUGE
- **Human Evaluation:** Quality ratings
- **Benchmarks:** Compare to base model
- **Specific Tasks:** Domain-specific tests
- **A/B Testing:** Compare in production

---

### Q15: What are best practices for fine-tuning?

**Answer:** Best practices:

1. **Start Small:** Test on subset first
2. **Quality Data:** Better data > more data
3. **Hyperparameters:** Learning rate is critical
4. **Regularization:** Prevent overfitting
5. **Evaluation:** Test thoroughly before deployment

---

## Summary

Key fine-tuning topics:

1. **Overview:** When to fine-tune vs RAG
2. **Techniques:** LoRA, QLoRA, PEFT, Full
3. **Implementation:** Unsloth, HF, Azure, AWS, GCP
4. **Production:** Evaluation, best practices

---

## References

- [LoRA Paper](references.md)
- [PEFT Library](references.md)
- [Fine-tuning Guides](references.md)
