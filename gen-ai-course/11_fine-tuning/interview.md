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

## Senior Deep Dive: Fine-Tuning in Production

> Senior interviews at Staff+ level rarely test whether you know what LoRA is — they test whether you know *when fine-tuning is worth the cost*, how you operate it safely at scale, and what you do when it goes wrong. The questions below probe system design, trade-off reasoning, incident handling, and the ability to justify engineering investment to non-technical stakeholders.

---

### System Design & Scale

#### Q: Design a fine-tuning and serving pipeline for LoRA adapters spanning many domains (e.g., legal, medical, finance, support).

**Answer:** The correct answer starts with the registry, not the training loop. Fine-tuning many domains without a disciplined registry and eval gate turns into an unmaintainable collection of checkpoints nobody trusts.

**End-to-end architecture:**

```
Raw domain data
     │
     ▼
[Data Pipeline]  ── dedup, quality filter, PII scrub, format conversion
     │
     ▼
[Training Jobs]  ── Azure ML Pipelines / AzureML SDK v2, one job per domain
     │
     ▼
[Eval Gate]      ── automated: domain benchmark + general regression suite
     │  (fail → block promotion)
     ▼
[Adapter Registry]  ── Azure Blob + metadata store (domain, base model SHA,
     │                  rank, eval scores, owner, created_at, status)
     ▼
[Serving Layer]  ── base model loaded once; adapters hot-swapped per request
                    (vLLM LoRA plugin, or custom PEFT inference server)
```

**Key design decisions:**

- **Adapter registry as source of truth.** Store adapter weights in Azure Blob Storage keyed by `{base_model_id}/{domain}/{semver}`. A lightweight metadata DB (Azure Cosmos DB or Postgres on Azure) holds eval scores, status (`staging`/`canary`/`prod`), and deprecation flags. No adapter reaches serving without a registry entry.

- **Eval gate is non-negotiable.** Every promoted adapter must pass: (1) domain-specific task benchmark (F1, exact match, or human preference score above threshold), (2) general capability regression on a held-out suite (MMLU subset, instruction-following) to catch catastrophic forgetting. Gate runs as a pipeline step; failures create alerts and block the promotion step.

- **Multi-adapter serving.** Load the base model once per GPU node. Route incoming requests to the correct adapter via a request header (`X-Domain: legal`). Use vLLM's LoRA serving support or Hugging Face's `PeftModel.set_adapter()` for hot-swapping. At high throughput, pin high-traffic adapters in GPU memory; evict cold adapters to CPU/disk using an LRU cache.

- **Versioning and rollback.** Tag adapters with semver. The router reads the active version from a config service (Azure App Configuration or a simple key in Redis). Rolling back is a config change, not a redeploy.

- **Azure-primary tooling:** Azure ML Pipelines for training orchestration, Azure Blob for artifact storage, Azure Container Registry for inference images, AKS + vLLM for serving, Azure Monitor + Application Insights for latency and error tracking per adapter.

**Senior framing:** The failure mode in most orgs is skipping the registry and eval gate — teams push adapters directly to prod and have no way to trace which version is running or whether it regressed. Design the registry first; the training loop is commodity.

---

#### Q: You need to serve dozens of fine-tuned model variants cost-effectively. How do you architect this?

**Answer:** The key insight is that LoRA adapters are small (tens to hundreds of MB) while base models are large (tens of GB). The economics flip entirely when you share the base model across all variants instead of running one GPU instance per fine-tuned model.

**Serving strategies ranked by efficiency:**

| Strategy | GPU footprint | Adapter swap latency | Best for |
|---|---|---|---|
| One full model per variant | O(N × model size) | None | < 3 variants, latency critical |
| Base + adapters, single node | 1× base + small adapters | ~10–100 ms (CPU→GPU) | Moderate traffic, < ~20 adapters |
| Base + adapter pool, multi-node | 1× base per node + LRU pool | < 5 ms (pinned in GPU) | High traffic, many adapters |
| Merged adapters (offline) | 1× model per domain | None | Very high traffic, single domain |

**Production architecture for many variants:**

- **Single base model per node.** Deploy the base model (e.g., Llama-3-8B or Mistral-7B) once per GPU node. All adapter inference runs on that node.
- **Adapter LRU cache in GPU memory.** Keep the top-K adapters (by recent traffic) pinned in GPU VRAM. Less-used adapters live on CPU or NVMe; swap time is acceptable for low-traffic domains.
- **Request routing.** An API gateway (Azure API Management) reads a `domain` claim from the JWT or a request header and routes to the correct inference pod. The inference pod selects the adapter.
- **Horizontal scaling by traffic.** Use Azure Kubernetes Service (AKS) with node autoscaling. High-traffic domains can get dedicated node pools with pinned adapters; low-traffic domains share a pool.
- **Avoid full merges in serving.** Merging LoRA weights into the base permanently eliminates swappability. Do this only for a domain that will never change and has enough traffic to justify a dedicated deployment.
- **Cost guardrail.** Track per-adapter GPU-hours and request volume in Azure Monitor. Adapters below a request-per-day threshold are candidates for deprecation or offline inference via Azure Batch.

**Senior framing:** Most teams over-provision because they think "one fine-tuned model = one deployment." The correct mental model is "one base model deployment = N virtual model variants." This typically reduces GPU spend by 5–10× when you have 10+ adapters.

---

#### Q: Describe your data pipeline for supervised fine-tuning (SFT) and DPO at scale. What quality gates do you enforce?

**Answer:** Data quality is the dominant lever in fine-tuning. A clean 10 K-example dataset consistently outperforms a noisy 100 K-example dataset. The pipeline must be treated as a first-class software system with tests, versioning, and audit trails.

**Pipeline stages:**

```
[Collection]       Raw sources: human-labeled, scraped, synthetic (GPT-4/Claude)
      │
      ▼
[Deduplication]    MinHash LSH at document level; exact-match dedup at example level.
      │            Remove near-duplicates across train/val/test splits (critical).
      ▼
[Quality Filter]   Perplexity filter (high-perplexity = noise), length filter,
      │            language detection, format validation (schema check for SFT pairs,
      │            chosen/rejected structure for DPO).
      ▼
[Safety Filter]    Toxicity classifier (Azure Content Safety or equivalent),
      │            PII detection and redaction (Presidio), copyright/legal review flag.
      ▼
[Synthetic Mix]    Validate synthetic ratio ≤ 30% for SFT (higher risks model collapse).
      │            Diversity check: embedding-space coverage; reject batches that
      │            cluster tightly (low diversity = overfitting risk).
      ▼
[Splits]           Stratified split by domain/source. Verify no train→val leakage
      │            via embedding similarity. Hold out a "never-seen" test set
      │            in a separate, access-controlled location.
      ▼
[Versioned Dataset] Azure ML Data Assets + lineage tracking. Every training run
                    references a pinned dataset version.
```

**DPO-specific requirements:**

- Chosen/rejected pairs must have a meaningful quality gap — pairs where the gap is ambiguous (human annotators disagreed > 30%) should be excluded or downweighted.
- For automated DPO data generation (e.g., using a reward model to rank completions), validate the reward model's calibration before using it to label at scale.

**Synthetic data guardrails:**

- Cap synthetic data at 20–30% of total SFT mix. Above this, monitor training loss curves and output diversity metrics (distinct-N, embedding variance) for early signs of model collapse.
- Always include synthetic data from multiple generators if possible; monoculture from a single LLM amplifies that model's failure modes.

**Azure tooling:** Azure ML Data Assets for versioning, Azure Data Factory or Spark on Azure Databricks for large-scale ETL, Azure Content Safety API for toxicity/PII, Azure Blob for immutable dataset snapshots.

**Senior framing:** The most common data pipeline failure is eval contamination — test examples that leaked into training through sloppy dedup. Treat train/val/test isolation as a security property, not a best-effort guideline. Run embedding-similarity checks across splits before every training run.

---

### Trade-offs & Decisions

#### Q: A team asks: should we fine-tune, use prompt engineering + RAG, or both? Walk me through your decision framework.

**Answer:** Default to RAG + prompt engineering first. Fine-tuning is a capital investment with ongoing maintenance cost; it pays off only in specific conditions.

**Decision framework:**

```
Do you have < 1 000 high-quality labeled examples?
  └─ Yes → RAG + prompt engineering. Come back when you have data.
  └─ No ↓

Is the gap a knowledge/recency gap (model doesn't know the facts)?
  └─ Yes → RAG closes this gap; fine-tuning won't help.
  └─ No ↓

Is the gap a behavior/style/format gap (model knows but behaves wrong)?
  └─ Yes → Fine-tuning is the right tool.
  └─ Unclear → Run a prompt engineering sprint first; measure delta.

Do latency or cost constraints rule out long prompts/retrieval?
  └─ Yes → Fine-tuning can help (no retrieval step, shorter prompts).
  └─ No → RAG may still be sufficient.

Can you maintain a labeled dataset over time as the domain drifts?
  └─ No → RAG is lower-maintenance; fine-tuned models go stale silently.
  └─ Yes → Fine-tuning is viable; build retraining cadence into the plan.
```

**Evidence required before committing to fine-tuning:**

1. A baseline eval showing RAG + prompt engineering falls short by a measurable, meaningful margin.
2. A dataset size and quality estimate confirming you can reach the threshold.
3. A retraining plan (cadence, data refresh, eval gate) — fine-tuning without this creates technical debt.

**"Both" is often the right answer** for high-stakes production systems: fine-tune for style/format/safety behavior, RAG for factual grounding. This prevents hallucination on retrieved facts while enforcing consistent tone and format.

**Senior framing:** The senior interview trap is going straight to fine-tuning because it sounds sophisticated. The right answer always starts with "what evidence do we have that simpler approaches fail?" Fine-tuning you can't measure and maintain is worse than prompt engineering you can iterate on in a day.

---

#### Q: When do you choose full fine-tuning over LoRA/QLoRA, and what are the trade-offs?

**Answer:** In 2024–2025, LoRA or QLoRA is the correct default for the vast majority of production use cases. Full fine-tuning is a deliberate choice that requires explicit justification.

| Dimension | Full Fine-tuning | LoRA | QLoRA |
|---|---|---|---|
| GPU memory | Very high (full model in fp16/bf16) | Moderate (base + adapter) | Low (4-bit base + adapter) |
| Training cost | High | 3–10× cheaper | 5–15× cheaper |
| Quality ceiling | Highest (theoretical) | Near-parity for most tasks | Slight gap on complex reasoning |
| Adapter portability | None (monolithic checkpoint) | High (adapter is separate) | High |
| Catastrophic forgetting risk | High | Low (base weights frozen) | Low |
| Serving complexity | Simple (one checkpoint) | Moderate (base + adapter) | Moderate |
| Multi-task / multi-domain | Requires separate checkpoints | Single base, many adapters | Single base, many adapters |

**When full fine-tuning is justified:**

- You need maximum quality on a narrow, high-stakes task and have measured that LoRA falls short.
- The base model's architecture needs modification (e.g., extended context window, vocabulary extension for a new language).
- You are training from scratch or continuing pre-training, not task fine-tuning.
- You have dedicated infrastructure and a single deployment target with no need for adapter swapping.

**When LoRA/QLoRA is clearly the right choice:**

- Multiple domains or use cases from a single base.
- Consumer or cloud GPU budget constraints.
- Rapid iteration and experimentation cycles.
- Need to preserve general capabilities (base weights frozen).
- QLoRA specifically: when you cannot fit the base model in GPU memory in full precision.

**Senior framing:** Full fine-tuning's "higher quality" advantage is smaller than most teams expect for task adaptation (as opposed to continued pre-training). The portability and cost advantages of LoRA usually dominate. Before choosing full fine-tuning, run a LoRA baseline — if the quality gap is < 1–2 points on your eval, LoRA wins on every other dimension.

---

#### Q: Compare SFT, RLHF, and DPO. When do you use each, and what are the practical trade-offs?

**Answer:** These three techniques target different problems. Applying RLHF when SFT would suffice wastes significant engineering effort; applying SFT when alignment is the goal produces models that know the right answer but don't reliably give it.

| Dimension | SFT | RLHF | DPO |
|---|---|---|---|
| Primary goal | Teach format/style/task | Align to human preferences | Align to human preferences |
| Data requirement | (prompt, ideal response) pairs | Preference pairs + reward model | (prompt, chosen, rejected) pairs |
| Training complexity | Low | High (reward model + PPO loop) | Moderate (single training pass) |
| Instability risk | Low | High (PPO reward hacking) | Low-moderate |
| Infrastructure cost | Low | High | Moderate |
| Quality ceiling for alignment | Lower | Highest (with enough data) | Near-RLHF for most tasks |
| When to use | Format, domain, style | Safety, complex preference alignment | Preference alignment without RL infra |

**Practical decision path:**

- **Start with SFT** if your gap is about format, domain knowledge, or task specialization. SFT is cheap, fast, and interpretable.
- **Use DPO** if you need preference alignment (helpfulness, harmlessness, tone) and want to avoid the complexity of a reward model and PPO. DPO has largely replaced RLHF at most companies for production alignment tasks.
- **Use RLHF** only if DPO quality is insufficient and you have the infrastructure for reward model training and PPO stability monitoring. RLHF at scale requires a dedicated ML platform team.

**Common production pattern:** SFT first to get the model into the right format and domain, then DPO to align preferences on top of the SFT checkpoint. This two-stage approach is more stable than going directly from a base model to DPO.

**Senior framing:** RLHF is often cited in interviews as the gold standard. The honest senior answer is: DPO achieves comparable alignment results with 60–80% less infrastructure complexity. Choose RLHF only when you have the data volume and platform maturity to make it worth it.

---

### Failure Modes & Incidents

#### Q: Your fine-tuned model regresses on general tasks after training — classic catastrophic forgetting. How do you diagnose and fix it?

**Answer:** Catastrophic forgetting in a fine-tuned model is a data composition problem first, a hyperparameter problem second. The diagnosis drives the fix.

**Diagnosis steps:**

1. **Confirm the regression is real.** Run the general capability benchmark suite (held-out MMLU subset, instruction-following evals, your production regression suite) against the fine-tuned and base checkpoints. Quantify the delta — "it feels worse" is not a diagnosis.
2. **Check training data composition.** Was the fine-tuning dataset domain-only, or did it include general-purpose data? Pure domain data almost guarantees forgetting; the base model's "memory" for general tasks is washed out.
3. **Check training hyperparameters.** High learning rate + many epochs is a common culprit. Examine the training loss curve — if it converges very fast and then keeps going, you've overfit and overwritten.
4. **Identify which capabilities degraded.** Not all forgetting is equal. Pin down whether it's reasoning, instruction-following, or factual recall.

**Fixes, in order of preference:**

- **Mixed training data (first line of defense).** Blend 5–15% general instruction-following data (e.g., OpenHermes, Alpaca-style) into your domain dataset. This is the single most effective and cheapest mitigation.
- **Reduce learning rate and epochs.** Fine-tuning with lr ≤ 1e-4 and early stopping on a validation set that includes general tasks preserves more of the base model's priors.
- **LoRA instead of full fine-tuning.** If you are doing full fine-tuning, switching to LoRA essentially eliminates catastrophic forgetting because base weights are frozen.
- **Regularization.** Elastic Weight Consolidation (EWC) or knowledge distillation from the base model penalizes large weight deviations. Effective but adds training complexity.
- **Rollback and retrain.** If the regression is severe and the model is already in production, roll back immediately via the adapter registry config change (if LoRA) or the serving layer version pin. Treat this as an incident, not a tuning iteration.

**Eval suite design going forward:** Your eval gate must include a general capability regression score. A fine-tuned model that improves domain score by 5 points but loses 10 points on general instruction-following is a net regression.

**Senior framing:** The fix is almost always in the data, not the algorithm. Adding 10% general data to the training mix costs almost nothing and routinely eliminates 80%+ of the forgetting. Do this by default, not as a remediation.

---

#### Q: Post-training evaluation shows suspiciously high scores. You later discover eval contamination — training examples leaked into the test set. How do you handle this, and what do you put in place to prevent it?

**Answer:** This is a credibility incident, not just a technical bug. The model's reported quality is now unknown, and any decisions made on those scores are suspect.

**Immediate response:**

1. **Quarantine the eval results.** Flag all metrics derived from the contaminated evaluation as unreliable. Notify stakeholders — do not let contaminated numbers drive product or deployment decisions.
2. **Identify the blast radius.** Determine which training runs used the contaminated dataset split. Multiple model versions may be affected.
3. **Rebuild the test set from scratch.** Use a separate data collection pipeline that has no overlap with training data sources. The test set must be stored in an access-controlled location not reachable by training pipelines.
4. **Re-evaluate all affected model versions** against the clean test set. Accept that scores will likely be lower.

**Root cause (common sources):**

- Deduplication was performed per-split rather than across all splits simultaneously, allowing near-duplicates to appear in both train and test.
- The test set was constructed from the same pool as training data without a temporal or source-based isolation strategy.
- Synthetic data generated from test prompts was added to training.

**Prevention mechanisms:**

- **Cross-split dedup at pipeline creation time.** Run MinHash LSH or embedding-similarity dedup across the union of all splits before assignment. Any example within cosine distance threshold of a test example must go to training only, not test.
- **Leakage audit step in the data pipeline.** Add an automated step that samples 1% of training data and checks embedding similarity against the test set. Fail the pipeline if any pair exceeds a similarity threshold.
- **Test set provenance isolation.** Store the test set in a separate Azure Blob container with read-only access for the evaluation service. Training pipelines cannot write to this container.
- **Dataset versioning with lineage.** Azure ML Data Assets with lineage tracking ensures you can audit exactly which data went into any model version.

**Senior framing:** Eval contamination is the silent killer of model credibility. Orgs that don't discover it keep reporting increasingly impressive numbers until a production deployment exposes the gap. Treat test set integrity as a security invariant.

---

#### Q: You observe model collapse symptoms after incorporating a large batch of synthetic training data — outputs are repetitive, diversity drops, and performance degrades. How do you respond?

**Answer:** Model collapse from synthetic data monoculture is a real and under-discussed production risk. It manifests as the model "learning to sound like" the generator rather than solving the underlying task.

**Symptoms to confirm:**

- Output diversity metrics (distinct-1, distinct-2, embedding variance across outputs) drop significantly vs. the base model or previous fine-tuned version.
- The model over-uses specific phrases, structures, or reasoning patterns common to the synthetic generator (e.g., GPT-4's formatting habits if all data was GPT-4-generated).
- Performance on out-of-distribution examples degrades while in-distribution scores remain high.

**Immediate response:**

1. **Halt promotion** of the collapsed model. Do not deploy to production.
2. **Quantify the synthetic ratio** in the training mix. If it exceeds 30–40%, that is likely the primary cause.
3. **Compare output diversity** on a fixed prompt set between the collapsed model and the previous production version.

**Remediation:**

- **Reduce synthetic ratio to ≤ 20–30%** and retrain. This is the primary lever.
- **Diversify synthetic generators.** If all synthetic data came from one LLM, add samples from another (Claude, Mistral, etc.) to reduce monoculture. Different generators have different stylistic biases that partially cancel out.
- **Add real human-written data.** Even a small proportion of real, diverse human data anchors the distribution and counteracts synthetic homogeneity.
- **Monitor diversity during training.** Track distinct-N and embedding variance on a held-out set at each checkpoint. Early stopping when diversity begins to drop can catch collapse before it fully manifests.

**Prevention going forward:**

- Hard cap: synthetic data ≤ 30% of SFT mix, enforced in the data pipeline quality gate.
- Diversity gate: embedding variance of the training batch must exceed a minimum threshold before training starts.
- Weekly diversity monitoring in production via a diversity probe (fixed diverse prompt set, measure output variance).

**Senior framing:** Synthetic data is a force multiplier for data-scarce domains, but it introduces a distributional risk that real data does not. The discipline is to treat it as an ingredient with a maximum safe dose, not a free lunch.

---

### Leadership & Behavioral

#### Q: How do you justify fine-tuning spend to leadership? What does the business case look like?

**Answer:** Leadership does not fund ML techniques — they fund business outcomes. The fine-tuning ROI case must be framed in terms of cost reduction, revenue impact, or risk reduction, with concrete numbers.

**Structure of the business case:**

1. **Baseline: what does the current approach cost and deliver?**
   - Current accuracy/quality metric with prompt + RAG.
   - Inference cost per request at current volume.
   - Any latency or reliability issues limiting adoption.

2. **Delta: what does fine-tuning change, and what evidence do you have?**
   - Measured quality improvement from a pilot/prototype (not projected).
   - Projected inference cost change (fine-tuned smaller model vs. large model + RAG overhead).
   - Latency reduction if applicable.

3. **Investment: full cost of ownership, not just compute.**
   - Training compute (Azure ML GPU cluster hours).
   - Data collection and labeling cost.
   - Engineering time (pipeline, eval, serving, monitoring).
   - Ongoing retraining cadence (data refresh, compute, evaluation).

4. **Break-even and payback period.**
   - At what request volume does the inference cost saving pay back the upfront investment?
   - What is the annual run-rate saving or revenue uplift?

5. **Risk and alternatives.**
   - What is the fallback if fine-tuning does not achieve target quality?
   - Why is fine-tuning superior to the next-best alternative (e.g., a better prompt, a different base model)?

**Common mistake to avoid:** Presenting fine-tuning as a technical win ("we achieved 8% better ROUGE-L") without translating to business impact. Leadership needs to hear: "This reduces our LLM API spend by $X/month, pays back in Y months, and improves customer task completion rate from A% to B%."

**Senior framing:** The most credible version of this conversation includes a small, time-boxed proof-of-concept with measured results before requesting full investment. "Here's what we measured in 2 weeks with 2K examples" is more convincing than any projection.

---

#### Q: Tell me about a time you killed a fine-tuning project because RAG was sufficient. (STAR format)

**Answer:**

**Situation:** Our team was tasked with improving a customer-support assistant for a SaaS product. The model was answering questions about product features but frequently hallucinated pricing details, API parameter names, and recent release notes. Initial proposal from the team was to fine-tune Llama-2-13B on historical support tickets and product documentation.

**Task:** I was leading the ML platform work and needed to evaluate whether fine-tuning was the right investment. We had a 6-week window, limited labeled data (~3 K support tickets of variable quality), and a product manager who needed reliable answers about constantly-updating product docs.

**Action:**
- I ran a 2-week sprint to implement a RAG baseline: embedded the product docs and release notes into a vector store (Azure AI Search), added a retrieval step to the existing prompt, and tuned the retrieval and context window.
- I defined a shared eval set of 200 representative user questions across feature explanation, pricing, and troubleshooting categories.
- RAG baseline closed 70% of the quality gap we had measured vs. the target. Fine-tuning a model on 3 K noisy tickets was unlikely to close the remaining 30% — the errors were almost entirely factual (wrong version numbers, stale pricing), not stylistic.
- I presented the measured comparison to the team: RAG at 2 weeks of work vs. fine-tuning requiring 8+ weeks of data cleaning, training, eval, and serving infrastructure, with high uncertainty on whether factual accuracy would improve.
- The team aligned on killing the fine-tuning track. We invested the remaining 4 weeks in improving retrieval quality (hybrid search, reranking) and prompt engineering for edge cases.

**Result:** The RAG system reached production in 6 weeks. Hallucination rate on factual questions dropped from ~25% to ~4%. We avoided ~$40 K in estimated infrastructure and labeling cost for the fine-tuning track. The product shipped on schedule.

**What I would flag in an interview:** The key judgment call was recognizing that the quality gap was *knowledge-shaped*, not *behavior-shaped*. Fine-tuning cannot teach a model facts that weren't in its training data and change weekly. Knowing the difference is the core senior skill here.

---

> **Staff/Principal stretch:** Define the org's decision framework and guardrails for when engineering teams may fine-tune independently versus when they must use managed/approved models.

**Model answer:**

The risk with decentralized fine-tuning is that every team becomes a model operator without the infrastructure, eval discipline, or safety awareness to do it safely. The framework needs to balance team autonomy with org-wide accountability.

**Tiered authorization model:**

| Tier | Activity | Who can approve | Requirements |
|---|---|---|---|
| 0 | Prompt engineering, RAG | Team lead | None beyond standard code review |
| 1 | LoRA/QLoRA on approved base models, internal use | ML platform + team lead | Registered dataset, eval gate, internal-only serving |
| 2 | LoRA/QLoRA, customer-facing | ML platform + Security + Legal | Tier 1 + safety eval, PII audit, red-team exercise |
| 3 | Full fine-tuning or continued pre-training | CTO/VP Eng + ML platform | Full MLOps review, dedicated infra, compliance sign-off |

**Guardrails that apply to all tiers ≥ 1:**

- **Approved base model list.** Teams may only fine-tune from a vetted list of base models (reviewed for license, safety, and supply chain). Adding a new base model requires ML platform approval.
- **Dataset registration.** All fine-tuning datasets must be registered in the central data catalog with provenance, PII audit status, and license documentation. Training on unregistered data is not permitted.
- **Eval gate before any promotion.** Every adapter must pass a defined eval gate (domain metric + general regression + safety scan) before reaching staging or production. The gate is enforced by the platform pipeline, not self-reported.
- **Adapter registry.** All adapters live in the central registry. Rogue checkpoints on individual laptops or team storage accounts are a policy violation.
- **Retraining SLA.** Teams that own a fine-tuned model must commit to a retraining cadence (e.g., quarterly for slow-moving domains, monthly for fast-moving) and own the monitoring alerts. No model ships without a named owner.

**Why this matters at Staff/Principal level:** Without this framework, fine-tuning proliferates as "ML debt" — dozens of checkpoints, no clear ownership, no eval history, no rollback path. The framework is not bureaucracy; it is the infrastructure that makes sustainable, trustworthy fine-tuning possible at org scale.

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
