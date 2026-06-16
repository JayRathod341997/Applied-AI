# Module 11: Fine-Tuning LLMs — Interview Questions

## Table of Contents
- [Beginner Level](#beginner-level)
- [Intermediate Level](#intermediate-level)
- [Advanced Level](#advanced-level)

---

## Beginner Level

### Q1: What is fine-tuning in the context of LLMs?

**Answer:** Fine-tuning is the process of continuing to train a pre-trained language model on a domain-specific or task-specific dataset. The model's weights are adjusted so it specializes in producing outputs tailored to the target use case — such as a specific tone, output format, domain vocabulary, or task behavior.

Fine-tuning builds on the general knowledge captured during pre-training and adapts it, rather than training from scratch.

### Q2: What is the difference between fine-tuning and prompt engineering?

**Answer:**

| Aspect | Prompt Engineering | Fine-Tuning |
|--------|-------------------|-------------|
| Mechanism | Crafting input text to guide behavior | Updating model weights via training |
| Data needed | None (or few examples in prompt) | Labeled dataset (hundreds–thousands) |
| Cost | API tokens only | Training compute + API tokens |
| Consistency | Variable | High |
| Setup time | Minutes | Hours to days |
| Best for | Prototyping, general tasks | Domain-specific, consistent outputs |

### Q3: When should you use RAG instead of fine-tuning?

**Answer:** Use RAG when:
- The knowledge base changes frequently (daily/weekly updates)
- You need the model to cite specific source documents
- You don't have enough labeled data for fine-tuning
- The task requires access to a large, dynamic knowledge store

Fine-tuning is better when you need consistent tone, format, or domain-specific behavior that doesn't depend on dynamic data.

### Q4: What is LoRA and why is it important?

**Answer:** LoRA (Low-Rank Adaptation) is a parameter-efficient fine-tuning technique that freezes all original model weights and injects small trainable low-rank matrices into attention layers. Instead of updating all d×k parameters in a weight matrix, LoRA adds a decomposition B·A where B is d×r and A is r×k, with r much smaller than d or k. This reduces trainable parameters by 100–1000×, making fine-tuning feasible on consumer GPUs.

### Q5: What data format does the Azure OpenAI fine-tuning API require?

**Answer:** Azure OpenAI fine-tuning expects JSONL (JSON Lines) format where each line contains a `messages` array. Each message has a `role` (system, user, or assistant) and `content` field. Example:

```jsonl
{"messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi! How can I help you?"}]}
```

### Q6: What is the difference between full fine-tuning and LoRA?

**Answer:** Full fine-tuning updates every parameter in the model (billions of weights), requiring massive GPU memory (4× model size for Adam optimizer). LoRA freezes all original weights and only trains low-rank adapter matrices, typically 0.01–1% of total parameters. For a 7B model, full fine-tuning needs ~120 GB GPU memory while LoRA needs ~30 GB.

---

## Intermediate Level

### Q7: Explain the LoRA weight update equation and what rank (r) controls.

**Answer:** For a pre-trained weight matrix W₀ ∈ ℝ^(d×k), LoRA computes:

W = W₀ + ΔW = W₀ + (α/r) · B·A

Where:
- B ∈ ℝ^(d×r) is the down-projection matrix
- A ∈ ℝ^(r×k) is the up-projection matrix
- α is a scaling hyperparameter (lora_alpha)
- r is the rank, controlling the expressiveness of the update

The rank r is the key trade-off: lower r (e.g., 8) means fewer parameters and less overfitting risk but limited capacity; higher r (e.g., 64) means more capacity but more memory and overfitting risk. For most tasks, r=16 is a strong starting point.

### Q8: What are the three key innovations in QLoRA?

**Answer:**
1. **4-bit NormalFloat (NF4)**: A quantization data type that is information-theoretically optimal for normally distributed neural network weights. It quantizes the base model to 4 bits per parameter.
2. **Double Quantization**: After quantizing weights to 4 bits, the block-wise scaling constants are themselves quantized, saving ~0.4 bits per parameter.
3. **Paged Optimizers**: Uses NVIDIA unified memory to page optimizer states between CPU and GPU during training, preventing out-of-memory errors from activation spikes during gradient checkpointing.

### Q9: How do you prevent overfitting during fine-tuning?

**Answer:**
- **Limit epochs**: 1–3 epochs for small datasets; monitor validation loss
- **Use LoRA**: Fewer trainable parameters = less overfitting risk
- **Learning rate warmup**: Start with a small LR and gradually increase
- **Weight decay**: Add L2 regularization (0.01–0.1)
- **Dropout**: Apply dropout to LoRA layers (lora_dropout=0.05)
- **Early stopping**: Stop when validation loss stops improving
- **Data augmentation**: Paraphrase inputs, add diverse examples
- **Evaluation**: Use held-out validation set throughout training

### Q10: What is instruction tuning and how does it differ from standard fine-tuning?

**Answer:** Instruction tuning is a form of fine-tuning where the training data consists of (instruction, input, output) triples. The model learns to follow diverse instructions rather than just continuing text or performing a single task. Standard fine-tuning typically adapts to one task (e.g., sentiment classification), while instruction tuning produces a general-purpose instruction-following model (like Alpaca, Vicuna). It's the "SFT" stage in RLHF pipelines.

### Q11: What is the purpose of `gradient_checkpointing` and when should you use it?

**Answer:** Gradient checkpointing trades compute for memory. Instead of storing all intermediate activations during the forward pass (needed for backpropagation), it only stores activations at certain "checkpoints" and recomputes the rest during the backward pass. This reduces memory usage by ~60% at the cost of ~20–30% slower training. Use it when GPU memory is the bottleneck, which is common when fine-tuning large models.

### Q12: How do you merge a LoRA adapter into the base model and why would you do this?

**Answer:**
```python
from peft import PeftModel
model = PeftModel.from_pretrained(base_model, adapter_path)
model = model.merge_and_unload()
```

This computes W = W₀ + (α/r)·BA for each layer and replaces the original weights. Reasons to merge:
- **Eliminates inference overhead** from the adapter forward pass
- **Simplifies deployment** — single model, no PEFT dependency
- **Required for formats** like GGUF or ONNX that don't support PEFT

### Q13: What learning rate should you use for fine-tuning and how does it differ from pre-training?

**Answer:** Pre-training uses higher learning rates (1e-4 to 3e-4) because weights are initialized randomly or from a smaller model. Fine-tuning uses lower learning rates (1e-5 to 5e-4) because the model already has useful representations, and large updates would destroy them.

For LoRA, higher learning rates (1e-4 to 2e-4) are acceptable since the adapters are randomly initialized and base weights are frozen. For full fine-tuning, use 1e-5 to 5e-5.

---

## Advanced Level

### Q14: How would you fine-tune a 70B parameter model on a single GPU?

**Answer:** Use QLoRA with the following configuration:
1. Load the model in 4-bit NF4 quantization (~35 GB for 70B)
2. Apply LoRA with rank 16–32 to attention + MLP layers
3. Enable gradient checkpointing to reduce activation memory
4. Use paged AdamW 8-bit optimizer
5. Set a small batch size (1–2) with gradient accumulation

This requires a single GPU with 48+ GB memory (e.g., A6000 or A100). Training will be slower than multi-GPU but feasible. Effective throughput: ~100–200 tokens/sec.

### Q15: Compare LoRA, AdaLoRA, and Prefix Tuning as PEFT methods.

**Answer:**

| Method | Mechanism | Pros | Cons |
|--------|-----------|------|------|
| **LoRA** | Low-rank matrices added to attention projections | Simple, effective, mergeable | Fixed rank across all layers |
| **AdaLoRA** | Dynamically adjusts rank per layer based on importance | Better parameter allocation | More complex, slightly slower |
| **Prefix Tuning** | Learns continuous prefix vectors prepended to attention | Very few parameters, no model modification | Cannot merge into base model, less effective for causal LM |

LoRA is the default recommendation due to its simplicity, mergeability, and strong empirical results. AdaLoRA is useful when you suspect different layers need different adaptation capacity.

### Q16: How do you evaluate a fine-tuned model beyond automated metrics?

**Answer:**
1. **Human evaluation**: Have domain experts rate outputs on accuracy, helpfulness, tone, and format adherence
2. **Side-by-side comparison**: Present outputs from base and fine-tuned models, ask evaluators to choose
3. **Task-specific benchmarks**: Create a held-out test set with known correct outputs
4. **Red teaming**: Test adversarial inputs, edge cases, and failure modes
5. **Regression testing**: Ensure the model still handles general tasks it was previously good at
6. **A/B testing**: Deploy both versions to production and compare user engagement / satisfaction metrics

### Q17: What is the RLHF pipeline and where does SFT fit in?

**Answer:** RLHF (Reinforcement Learning from Human Feedback) has three stages:

1. **SFT (Supervised Fine-Tuning)**: Fine-tune the base model on high-quality prompt-response pairs to establish baseline instruction-following behavior.
2. **Reward Model Training**: Train a separate model to predict human preference rankings between pairs of model outputs.
3. **PPO/DPO Optimization**: Use the reward model to further optimize the SFT model via Proximal Policy Optimization or Direct Preference Optimization.

SFT is the foundation — without it, the reward model and RL stages have no meaningful signal to work with.

### Q18: How would you design a data pipeline for fine-tuning at scale?

**Answer:**
1. **Data collection**: Aggregate from existing logs, human annotations, synthetic generation (using a stronger model)
2. **Deduplication**: Remove near-duplicates using MinHash or embedding similarity
3. **Quality filtering**: Score examples with a reward model or heuristic rules; remove low-quality samples
4. **Formatting**: Convert all examples to the target JSONL schema with consistent prompt templates
5. **Balancing**: Ensure coverage across task types, difficulty levels, and output lengths
6. **Validation split**: Hold out 5–10% stratified by task type
7. **Versioning**: Track dataset versions with DVC or similar tools
8. **Iterative improvement**: Analyze model errors on validation set, collect more data for failure cases

### Q19: What are the trade-offs of training LoRA on different target modules (attention vs MLP)?

**Answer:**

| Target | Parameters Added | Impact |
|--------|-----------------|--------|
| Attention only (q, k, v, o) | Moderate | Good for style, format, attention pattern changes |
| MLP only (gate, up, down) | Moderate | Good for knowledge injection, factual accuracy |
| Both attention + MLP | Higher | Best overall quality, closest to full fine-tuning |
| q, v only | Lowest | Minimal viable; common default for simple tasks |

Research shows that applying LoRA to both attention and MLP layers (especially `gate_proj` and `down_proj`) produces the best results, but at the cost of ~2× more trainable parameters compared to attention-only.

### Q20: How would you handle catastrophic forgetting in a production fine-tuning pipeline?

**Answer:**
1. **Use PEFT methods**: LoRA/QLoRA freeze base weights, inherently preventing forgetting
2. **Mix training data**: Include a small portion (5–10%) of general-purpose data alongside domain data
3. **Replay buffer**: Keep a subset of pre-training data and sample from it during fine-tuning
4. **Regularization**: Use Elastic Weight Consolidation (EWC) or L2 regularization toward original weights
5. **Low learning rate**: Use 1e-5 to 5e-5 for full fine-tuning
6. **Evaluation**: Maintain a regression test suite covering general capabilities
7. **Distillation**: Fine-tune a student model to match both domain outputs and general outputs from the teacher

---

## Quick Reference Table

| Question | Topic | Key Concept |
|----------|-------|-------------|
| Q1 | Definition | Fine-tuning = adapting pre-trained weights |
| Q2 | Comparison | Prompt engineering vs fine-tuning trade-offs |
| Q3 | Decision | RAG for dynamic data, fine-tune for behavior |
| Q4 | Technique | LoRA = low-rank weight decomposition |
| Q5 | API | Azure OpenAI expects JSONL messages format |
| Q6 | Comparison | Full FT = all params; LoRA = 0.01–1% params |
| Q7 | Theory | W = W₀ + (α/r)·BA; rank controls expressiveness |
| Q8 | QLoRA | NF4 + double quantization + paged optimizers |
| Q9 | Training | Epochs, LR warmup, dropout, early stopping |
| Q10 | Instruction tuning | SFT stage with (instruction, input, output) triples |
| Q11 | Memory | Gradient checkpointing: compute ↔ memory trade-off |
| Q12 | Inference | merge_and_unload() bakes adapter into base model |
| Q13 | Hyperparameters | Fine-tuning LR: 1e-5 to 5e-4; LoRA LR: 1e-4 to 2e-4 |
| Q14 | Scaling | QLoRA on 70B: 4-bit + LoRA + gradient checkpointing |
| Q15 | PEFT comparison | LoRA > AdaLoRA > Prefix Tuning for most cases |
| Q16 | Evaluation | Human eval, side-by-side, red teaming, A/B testing |
| Q17 | RLHF | SFT → Reward Model → PPO/DPO |
| Q18 | Data pipeline | Collect → Dedupe → Filter → Format → Version |
| Q19 | Architecture | Attention + MLP targets give best quality |
| Q20 | Forgetting | PEFT, data mixing, replay buffer, EWC |


---

## Senior Deep Dive: Fine-Tuning vs RAG, LoRA/QLoRA & Synthetic Data on Azure

> *The JD lists fine-tuning, PEFT, and "synthetic information to train LLM as part of Azure" with a hallucination angle. Interviewers probe whether you fine-tune for the right reasons and guard against synthetic-data failure modes.*

### SQ1: RAG vs fine-tuning vs both — what's your decision framework?

**Answer:** The choice turns on whether the gap is *knowledge* or *behavior*. **RAG** is the right tool for **fresh, factual, and frequently changing knowledge**: it retrieves grounding at query time, supports source citations, and enforces access control without retraining. **Fine-tuning** is the right tool for **behavior, format, tone, and domain style** — teaching the model to respond in a specific way — and for cutting latency and cost by internalizing task conventions that would otherwise require long prompts. Fine-tuning is *not* a reliable mechanism for injecting new facts; a fine-tuned model may learn patterns from factual training data but will still hallucinate when that knowledge is absent or stale. **Both together** is a common production pattern: fine-tune the model's behavioral style and conversational register, then RAG the facts in at inference time. **Trade-off:** fine-tuning incurs upfront training cost and produces a static artifact that must be retrained as the domain shifts; RAG incurs per-query retrieval cost but remains current — choose based on whether the gap is knowledge (RAG) or behavior (fine-tuning).

### SQ2: Explain PEFT, LoRA, and QLoRA.

**Answer:** **Full fine-tuning** updates every parameter in the model, which for large models requires enormous GPU memory (four times the model size for an Adam optimizer) and produces a full-weight artifact per task. **PEFT (Parameter-Efficient Fine-Tuning)** is the umbrella category for methods that freeze most of the base model and train only a small addition. **LoRA (Low-Rank Adaptation)** is the dominant PEFT technique: the base model weights are frozen entirely, and two small **low-rank adapter matrices** (B and A, with product rank r much smaller than the original dimensions) are injected at attention projections. The effective update is W₀ + (α/r)·BA. Adapters are typically 0.01–1% of total parameters, are tiny to store, and can be swapped — multiple adapters can be maintained per base model for different tasks. **QLoRA** extends LoRA by also **quantizing the frozen base to 4-bit NF4 (NormalFloat)**, combined with double quantization of the scaling constants and paged optimizers — together enabling fine-tuning of a 70B model on a single GPU. **Trade-off:** PEFT trades a small quality delta against a very large reduction in compute and memory; for almost all production work outside frontier research this is the right default, and the quality gap versus full fine-tuning is typically negligible on the target task.

### SQ3: How do you use synthetic data to fine-tune, and what are the risks?

**Answer:** Synthetic data generation uses a stronger **teacher model** to produce (instruction, response) pairs — a form of **knowledge distillation** — or to augment scarce real data in a low-resource domain. Common uses include bootstrapping a new domain where labeled data does not exist, balancing class or scenario distributions, and keeping **real PII out of the training pipeline** by generating privacy-safe examples. The critical **risks** are: **model collapse** (the student converges on the teacher's failure modes and loses diversity), **bias amplification** (if the teacher is biased, the student amplifies it), **distribution drift** (synthetic distribution drifts from real usage), and **hallucinated or incorrect labels** (the teacher fabricates facts that then bake into the student). Mitigations include mandatory **human review of a sample**, enforcing **lexical and semantic diversity**, always **mixing in real data** rather than training on pure synthetic, and running a held-out evaluation against real examples before any deploy. This is directly relevant to the JD's hallucination concern: a model trained primarily on synthetic data can inherit and amplify the teacher's hallucinations. **Trade-off:** synthetic data unblocks low-data domains and protects privacy, but degrades quality if it dominates the training mix — treat it as a supplement, not a replacement.

### SQ4: How do you run and evaluate fine-tuning on Azure?

**Answer:** The two main paths are **Azure OpenAI fine-tuning** (managed: upload JSONL, configure hyperparameters, Azure handles training and serving) and **Azure ML** (self-managed: bring your own training script and GPU compute, deploy to an endpoint). For both paths, prepare training data as **JSONL** with a `messages` array (system/user/assistant turns) and validate the file before upload. Gate every promotion with a structured **eval**: a **hold-out set** unseen during training (5–10%), a **golden set** of manually verified examples covering critical behaviors, and a **regression check against the base model** that verifies the fine-tune has not degraded general capabilities. **Version data and model artifact together** so a rollback also reverts the training data. On Azure OpenAI, evaluate the fine-tuned endpoint against the base endpoint on the same eval set before promoting to production traffic. **Trade-off:** an eval gate adds a release cycle overhead but is what prevents a fine-tune that improves the target task while silently regressing on everything else — in a regulated context a silent regression is a risk event, not just a quality issue.

### SQ5: How do you prevent overfitting and catastrophic forgetting during fine-tuning?

**Answer:** Overfitting and catastrophic forgetting are related but distinct failure modes. For **overfitting**, the primary levers are: a **small learning rate** (1e-5 to 5e-5 for full fine-tuning, 1e-4 to 2e-4 for LoRA adapters), **very few epochs** (1–3 for small datasets), **validation-based early stopping** before validation loss diverges from training loss, and keeping LoRA rank low enough to limit expressiveness. For **catastrophic forgetting** — the base model losing general capabilities — the most effective remedy is **LoRA itself**: because base weights are frozen, forgetting cannot occur. For full fine-tuning, mix in a small proportion (5–10%) of **general-domain data** alongside the task data, apply **L2 regularization** toward original weights (Elastic Weight Consolidation), and keep the learning rate low. In both cases, evaluate on a **broad benchmark** of capabilities beyond the target task, not just the task metrics. **Trade-off:** stronger task specialization risks eroding general capability — the balance is tuned by the use case, and verified empirically with broad evals before any production deployment.
