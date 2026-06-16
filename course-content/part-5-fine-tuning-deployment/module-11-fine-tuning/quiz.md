# Module 11: Fine-Tuning LLMs — Quiz

## Instructions
- 20 multiple choice questions
- Each question has one correct answer
- Click on the answer reveal to check your response

---

## Questions

### Q1. What is the primary purpose of fine-tuning an LLM?

A) To increase the model's parameter count
B) To adapt a pre-trained model's weights to a specific task or domain
C) To reduce the model's inference latency without changing outputs
D) To add new languages to the model's tokenizer

<details>
<summary>Answer</summary>

**B)** Fine-tuning adjusts a pre-trained model's weights so it specializes in producing outputs tailored to a specific task or domain. It builds on existing knowledge rather than training from scratch.

</details>

---

### Q2. Which technique should you try FIRST before considering fine-tuning?

A) Full fine-tuning on a subset of data
B) LoRA adapter training
C) Prompt engineering with few-shot examples
D) RLHF training

<details>
<summary>Answer</summary>

**C)** Prompt engineering (including few-shot examples) is the lowest-effort approach and should always be tried first. If it's insufficient, move to RAG, and only then consider fine-tuning.

</details>

---

### Q3. In LoRA, the weight update is decomposed into two matrices B and A. What are their dimensions?

A) B ∈ ℝ^(d×d), A ∈ ℝ^(k×k)
B) B ∈ ℝ^(d×r), A ∈ ℝ^(r×k) where r ≪ min(d, k)
C) B ∈ ℝ^(r×d), A ∈ ℝ^(k×r)
D) B ∈ ℝ^(d×k), A ∈ ℝ^(k×d)

<details>
<summary>Answer</summary>

**B)** LoRA decomposes the weight update into a down-projection B ∈ ℝ^(d×r) and an up-projection A ∈ ℝ^(r×k), where r is the rank and much smaller than d or k. This reduces trainable parameters by orders of magnitude.

</details>

---

### Q4. What does QLoRA add on top of LoRA?

A) Quantization-aware training in FP16
B) 4-bit NormalFloat quantization + double quantization + paged optimizers
C) A second LoRA adapter trained in parallel
D) Dynamic rank adjustment during training

<details>
<summary>Answer</summary>

**B)** QLoRA introduces three innovations: 4-bit NormalFloat (NF4) quantization for base weights, double quantization of the quantization constants, and paged optimizers using NVIDIA unified memory for handling memory spikes.

</details>

---

### Q5. What is PEFT?

A) A specific fine-tuning algorithm from OpenAI
B) An umbrella term for parameter-efficient fine-tuning techniques
C) A preprocessing library for training data
D) A model evaluation framework

<details>
<summary>Answer</summary>

**B)** PEFT (Parameter-Efficient Fine-Tuning) is a category of techniques — including LoRA, Prefix Tuning, Prompt Tuning, IA3, and AdaLoRA — that freeze most model parameters and only train a small subset to reduce memory and compute requirements.

</details>

---

### Q6. How much GPU memory does QLoRA typically require for a 7B parameter model?

A) ~120 GB
B) ~60 GB
C) ~10 GB
D) ~2 GB

<details>
<summary>Answer</summary>

**C)** QLoRA requires approximately 10 GB of GPU memory for a 7B model, compared to ~120 GB for full fine-tuning and ~30 GB for standard LoRA. This makes it feasible on a single consumer GPU.

</details>

---

### Q7. What is the recommended data format for OpenAI fine-tuning API?

A) CSV with instruction and response columns
B) JSONL with a messages array containing role/content pairs
C) Plain text with input and output separated by a delimiter
D) Parquet files with structured columns

<details>
<summary>Answer</summary>

**B)** OpenAI's fine-tuning API expects JSONL format where each line contains a `messages` array with objects having `role` and `content` fields, typically including system, user, and assistant messages.

</details>

---

### Q8. What is SFT (Supervised Fine-Tuning)?

A) Self-supervised training on unlabeled text
B) Training a model on curated prompt-response pairs to teach desired behavior
C) Reinforcement learning from human preferences
D) Training multiple models simultaneously

<details>
<summary>Answer</summary>

**B)** SFT is the first stage of RLHF where a model is fine-tuned on a high-quality dataset of prompt-response pairs. This teaches the model the desired output behavior before reward model training.

</details>

---

### Q9. In LoRA, what does the `lora_alpha` hyperparameter control?

A) The learning rate for LoRA layers
B) The dropout rate applied to LoRA layers
C) The scaling factor applied to the low-rank update (α/r)
D) The number of layers to apply LoRA to

<details>
<summary>Answer</summary>

**C)** `lora_alpha` is the scaling factor. The effective update is multiplied by α/r, where r is the rank. A common convention is to set alpha = 2 × rank (e.g., rank=16, alpha=32).

</details>

---

### Q10. Which of the following is NOT an advantage of LoRA over full fine-tuning?

A) Lower GPU memory requirements
B) Adapter weights are small and easy to share
C) Higher final model quality
D) No catastrophic forgetting of base knowledge

<details>
<summary>Answer</summary>

**C)** While LoRA achieves near-parity with full fine-tuning, full fine-tuning generally produces the highest quality since all parameters are updated. LoRA's advantages are efficiency, not quality.

</details>

---

### Q11. What is the purpose of `prepare_model_for_kbit_training()` in PEFT?

A) To convert the model to full precision before training
B) To prepare a quantized model for gradient computation by enabling gradient checkpointing and casting layers
C) To merge existing LoRA adapters
D) To prune the model to fewer parameters

<details>
<summary>Answer</summary>

**B)** This function prepares a quantized (4-bit or 8-bit) model for training by enabling gradient checkpointing, casting the layernorm to fp32, and making other adjustments needed for stable training on quantized weights.

</details>

---

### Q12. What is the typical LoRA rank (r) range used for fine-tuning?

A) 1–4
B) 8–64
C) 256–512
D) 1024–4096

<details>
<summary>Answer</summary>

**B)** LoRA rank typically ranges from 8 to 64. Lower ranks (8–16) work well for narrow tasks; higher ranks (32–64) are used for more complex adaptations. Going beyond 64 usually has diminishing returns.

</details>

---

### Q13. When should you choose RAG over fine-tuning?

A) When you need a specific output format
B) When the underlying data changes frequently
C) When you need to reduce prompt token costs
D) When you have a large labeled dataset

<details>
<summary>Answer</summary>

**B)** RAG is preferred when knowledge changes frequently (daily/weekly) because updating a vector index is instant, while retraining a fine-tuned model takes hours to days.

</details>

---

### Q14. What does `merge_and_unload()` do in PEFT?

A) Deletes the LoRA adapters and restores the base model
B) Merges LoRA weights into the base model and removes the PEFT wrapper for faster inference
C) Saves the LoRA adapters to disk
D) Converts the model to GGUF format

<details>
<summary>Answer</summary>

**B)** `merge_and_unload()` computes W = W₀ + BA for each layer, replaces the original weights, and removes the PEFT wrapper. This eliminates the LoRA inference overhead by baking the adapter into the base model.

</details>

---

### Q15. What is double quantization in QLoRA?

A) Quantizing the model twice with different bit widths
B) Quantizing the quantization constants themselves to save additional memory
C) Using two separate LoRA adapters
D) Quantizing both weights and activations

<details>
<summary>Answer</summary>

**B)** Double quantization quantizes the quantization constants (block-wise scaling factors) of the first quantization step. This saves approximately 0.4 bits per parameter, which adds up significantly for large models.

</details>

---

### Q16. Which hyperparameter has the MOST impact on preventing overfitting during fine-tuning?

A) Batch size
B) Number of epochs
C) Warmup steps
D) Gradient accumulation steps

<details>
<summary>Answer</summary>

**B)** The number of epochs has the most direct impact on overfitting. With small datasets, even 2–3 epochs can lead to overfitting. Always monitor validation loss and use early stopping.

</details>

---

### Q17. What is the effective batch size if `per_device_train_batch_size=4` and `gradient_accumulation_steps=4`?

A) 4
B) 8
C) 16
D) 64

<details>
<summary>Answer</summary>

**C)** Effective batch size = per_device_batch_size × gradient_accumulation_steps × num_devices. With one device: 4 × 4 × 1 = 16.

</details>

---

### Q18. Which metric is best for evaluating a summarization fine-tuned model?

A) Accuracy
B) Perplexity
C) ROUGE score
D) F1 Score

<details>
<summary>Answer</summary>

**C)** ROUGE (Recall-Oriented Understudy for Gisting Evaluation) measures n-gram overlap between generated and reference summaries. It's the standard metric for summarization tasks.

</details>

---

### Q19. What is the main advantage of Azure OpenAI fine-tuning over self-hosted fine-tuning?

A) It produces higher quality models
B) It requires no GPU infrastructure management
C) It supports larger model sizes
D) It allows full fine-tuning only

<details>
<summary>Answer</summary>

**B)** Azure OpenAI fine-tuning is a managed service — you upload data and receive a fine-tuned endpoint without managing GPU clusters, distributed training, or model serving infrastructure.

</details>

---

### Q20. What is catastrophic forgetting and how does LoRA help prevent it?

A) Forgetting to save checkpoints; LoRA auto-saves
B) Model losing pre-trained knowledge during fine-tuning; LoRA freezes base weights
C) GPU memory overflow; LoRA reduces memory
D) Training divergence; LoRA uses smaller learning rates

<details>
<summary>Answer</summary>

**B)** Catastrophic forgetting occurs when fine-tuning overwrites pre-trained knowledge with task-specific patterns. Since LoRA freezes all base weights and only trains low-rank adapters, the original knowledge is preserved.

</details>

---

## Score Interpretation

| Score | Level | Recommendation |
|-------|-------|----------------|
| 18–20 | Expert | Ready for production fine-tuning work and advanced interviews |
| 14–17 | Proficient | Strong foundation; review LoRA/QLoRA details and implementation |
| 10–13 | Intermediate | Revisit Sections 11.2 and 11.3; practice the implementation walkthrough |
| 6–9 | Beginner | Review all of Module 11; focus on the comparison table and decision framework |
| 0–5 | Needs Study | Start with Section 11.1 and work through each concept methodically |


---

## Bonus: Senior / JD-Aligned Questions (Fine-Tuning, PEFT & Synthetic Data)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. You need the model to reliably cite up-to-date internal policies. Fine-tune or RAG?

A) Fine-tune — it memorizes facts best  
B) RAG — fresh facts with citations and access control  
C) Neither is possible  
D) Increase temperature  

**Answer: B** — RAG handles changing factual knowledge with citations; fine-tuning is for behavior, not fresh facts.

### BQ2. What does LoRA do?

A) Retrains all model weights  
B) Freezes the base model and trains small low-rank adapter matrices  
C) Quantizes the dataset  
D) Replaces the tokenizer  

**Answer: B** — LoRA trains compact, swappable adapters on top of a frozen base.

### BQ3. What does QLoRA add over LoRA?

A) Nothing  
B) 4-bit (NF4) quantization of the frozen base so large models fine-tune on a single GPU  
C) A larger context window  
D) Automatic RAG  

**Answer: B** — QLoRA quantizes the base to 4-bit, slashing memory needs for fine-tuning.

### BQ4. What is the biggest risk of training primarily on model-generated synthetic data?

A) It is always perfect  
B) Model collapse, bias amplification, and drift — mitigate by mixing real data, ensuring diversity, and human review  
C) It needs no evaluation  
D) It removes the need for a base model  

**Answer: B** — synthetic data that dominates the mix degrades the model; treat it as a supplement.

### BQ5. What is the right gate before promoting a fine-tuned model?

A) Deploy immediately  
B) Evaluate on a golden + hold-out set and run a regression check against the base model  
C) Check only training loss  
D) Ask the model if it improved  

**Answer: B** — eval-gated promotion catches task gains that come at the cost of general regressions.
