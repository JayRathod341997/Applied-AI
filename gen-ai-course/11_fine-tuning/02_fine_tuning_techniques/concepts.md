# Concepts: Fine-tuning Techniques

## 1. LoRA (Low-Rank Adaptation)

### How LoRA Works

LoRA adds small trainable adapter matrices to the model's layers without modifying the original weights.

### Key Concepts

- **Rank (r)**: The rank of the adaptation matrices
- **Low-rank decomposition**: Original weight matrix W (d×d) is approximated as W + BA
  - B is (d×r)
  - A is (r×d)
  - r is typically 8, 16, or 32

### LoRA Configuration

```python
lora_config = LoraConfig(
    r=8,              # Rank
    lora_alpha=16,    # Scaling factor
    target_modules=["q_proj", "v_proj"],  # Which layers to apply
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
```

### Advantages

- Memory efficient: Only ~1% of original weights are trainable
- Fast training: Much faster than full fine-tuning
- Modular: Can swap adapters without retraining
- No inference overhead: Can merge weights for inference

### When to Use LoRA

- Limited GPU memory
- Quick experimentation
- Multiple tasks requiring different adapters

## 2. QLoRA (Quantized LoRA)

### What is Quantization?

Quantization reduces model precision from 16-bit to 4-bit, dramatically reducing memory.

### QLoRA Approach

1. Load base model in 4-bit quantization
2. Apply LoRA adapters
3. Train on quantized model
4. Achieve near-full-precision quality

### Memory Comparison

| Method | GPU Memory (7B model) |
|--------|----------------------|
| Full FP16 | ~14 GB |
| LoRA | ~7 GB |
| QLoRA | ~3 GB |

### Advantages

- Can fine-tune 70B models on a single GPU
- Quality close to full fine-tuning
- Fast iteration

## 3. PEFT (Parameter-Efficient Fine-tuning)

### Types of PEFT

#### a) LoRA
- Add low-rank matrices to attention layers
- Most popular and effective

#### b) Prefix Tuning
- Add trainable tokens to input
- Optimizes only the prefix embeddings

#### c) Prompt Tuning
- Similar to prefix tuning
- Uses soft prompts learned from data

#### d) Adapter Methods
- Insert small adapter layers
- Less common but effective

### Comparison

| Method | Trainable Params | Quality |
|--------|-----------------|---------|
| Full Fine-tune | 100% | Best |
| LoRA | ~1-2% | Very Good |
| Prefix | ~0.1% | Good |
| Prompt | ~0.01% | Moderate |

## 4. Full Fine-tuning

### When to Use

- Maximum quality required
- Sufficient GPU resources available
- Domain significantly different from base

### Resource Requirements

| Model Size | GPU Memory (FP16) | GPUs Needed |
|------------|------------------|-------------|
| 7B | ~14 GB | 1 |
| 13B | ~26 GB | 1-2 |
| 70B | ~140 GB | 8+ |

### Risks

- Catastrophic forgetting
- Longer training time
- Higher cost

## 5. Catastrophic Forgetting

### The Problem

When fine-tuning, the model may lose capabilities it learned during pre-training.

### Prevention Strategies

1. **Multi-task Learning**: Train on both old and new tasks
2. **Regularization**: Add loss term to preserve old knowledge
3. **Keep Base Model**: Maintain original model and combine outputs
4. **Hybrid Approach**: Use fine-tuned model with RAG for grounding
5. **Lower Learning Rate**: Slower learning preserves more knowledge

### Recommended Approach

```python
# Combined loss for preventing forgetting
total_loss = task_loss + lambda * preservation_loss
```

## Choosing the Right Technique

| Scenario | Recommended Method |
|----------|-------------------|
| Consumer GPU | QLoRA |
| Quick experiments | LoRA |
| Maximum quality | Full fine-tuning |
| Multiple tasks | LoRA with adapters |
| Very limited resources | Prefix/Prompt tuning |
