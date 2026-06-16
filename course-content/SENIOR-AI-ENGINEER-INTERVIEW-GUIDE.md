# Senior AI Engineer (10+ Years) — Interview Master Guide

> A JD-aligned interview companion for a **Senior AI Engineer** role focused on **AI/ML in risk management for global, regulated organisations**, with deep **Generative AI, LLMs, RAG, Azure, and MLOps** expertise plus **technical leadership**.
>
> This guide ties the JD to existing modules and adds the cross-cutting topics that don't fit a single module: **classic ML/DL/NLP/CV fundamentals**, **system design at scale**, and **leadership/behavioral** questions expected at 10+ years.

---

## Table of Contents
- [How to Use This Guide](#how-to-use-this-guide)
- [JD → Module Map](#jd--module-map)
- [Section A: Classic ML / DL / NLP / CV Fundamentals](#section-a-classic-ml--dl--nlp--cv-fundamentals)
- [Section B: System Design for AI at Scale](#section-b-system-design-for-ai-at-scale)
- [Section C: Technical Leadership & Behavioral (STAR)](#section-c-technical-leadership--behavioral-star)
- [Section D: Rapid-Fire Senior Round](#section-d-rapid-fire-senior-round)
- [Section E: Questions to Ask Your Interviewer](#section-e-questions-to-ask-your-interviewer)

---

## How to Use This Guide

A 10+ year role is assessed on four axes. Map your prep to all four — most candidates over-index on (1) and lose offers on (3) and (4):

1. **GenAI depth** — LLMs, RAG, agents, fine-tuning → Modules 1–6, 11.
2. **Production engineering** — architecture, MLOps, deployment, monitoring, governance → Modules 7–13.
3. **Breadth & fundamentals** — classic ML/DL/NLP/CV, the stuff a 10-year career is built on → **Section A** below.
4. **Leadership & judgment** — mentoring, stakeholders, trade-offs, delivering business value → **Sections B & C** below.

> **Interview tip:** For *every* technical answer at this level, close the loop with a trade-off and a business/risk consequence. "I'd use X because Y, accepting the cost of Z" beats a correct-but-flat definition every time.

> **Project deep-dives:** For the "walk me through a project you built" round, see [Project Case Studies](project-case-studies/README.md) — 13 end-to-end GenAI write-ups (RAG, multi-agent, automation agents) using a consistent 10-part structure with talking points and likely follow-ups.

---

## JD → Module Map

| JD Requirement | Where it's covered | Senior-level emphasis |
|----------------|--------------------|-----------------------|
| LLMs (GPT, **Claude**, Gemini, **Mistral**, open-source), prompting | Module 1 | Model selection trade-offs, Claude/Anthropic API, hallucination control |
| Prompt engineering, fine-tuning, RAG frameworks | Modules 1, 3, 11 | RAG vs fine-tuning decision, eval-gated promotion; **M11 deep dive: LoRA/QLoRA & synthetic data** |
| RAG architectures, conversational AI | Module 3 | Hybrid retrieval, re-ranking, **pgvector on Azure Postgres** (Module 3 deep dive) |
| AI agents, multi-agent systems, copilots | Modules 4, 5, 6 | Orchestration (LangGraph), MCP, autonomy vs control; **M4/M5/M6 deep dives** |
| LangChain / LlamaIndex orchestration | Module 2 | When to drop the framework; cost/latency; **M2 deep dive: LlamaIndex vs LangChain** |
| Vector databases (Pinecone, Weaviate, Chroma, FAISS, **pgvector**) | Module 3 | Dedicated DB vs pgvector trade-off |
| MLOps, CI/CD, Docker, Kubernetes, model monitoring | Modules 8, 9, 13 | Eval gates, canary/blue-green, drift, rollback |
| Cloud — **Azure** / Azure AI Foundry / AWS / GCP | Modules 12, 8 | **Azure deep dive** (Module 12): Foundry, Azure OpenAI, AKS, PTU |
| MLOps governance, **responsible AI**, explainability | Module 10 | **Model Risk Management / SR 11-7** deep dive (Module 10) |
| **Risk management** domain, global/regulated | Modules 10, 14 | MRM, fairness, EU AI Act, fraud/credit risk; **M14 deep dive: risk capstone** |
| **Synthetic data**, hallucination experience | Module 1 deep dive | Distillation, privacy, model collapse |
| Classic ML, deep learning, NLP, computer vision, predictive analytics | **Section A (this guide)** | Fundamentals a 10-yr engineer must own |
| Technical leadership, mentoring, stakeholder management | **Section C (this guide)** | STAR stories, influence, delivery |
| AI architecture, scalable pipelines | Module 7 + **Section B** | End-to-end design under constraints; **M7 deep dive: enterprise architecture on Azure** |

---

## Section A: Classic ML / DL / NLP / CV Fundamentals

> The course is GenAI-first, but the JD lists TensorFlow, PyTorch, Scikit-learn, deep learning, NLP, computer vision, and predictive analytics. At 10+ years you *will* be asked these — often to check you didn't skip the foundations on the way to LLMs.

### A1: Bias–variance trade-off — and how it actually guides your decisions.

**Answer:** Total error ≈ bias² + variance + irreducible noise. **High bias** (underfitting) = model too simple, high train *and* test error → add capacity/features, reduce regularization. **High variance** (overfitting) = fits noise, low train but high test error → more data, regularization, simpler model, bagging. You *diagnose* it from the train/validation gap and learning curves, then act. Senior add-on: in practice you trade these via regularization strength, model complexity, and data volume, and you decide based on whether the curves have converged (more data won't help a high-bias model).

### A2: How do you handle an imbalanced dataset (e.g., 0.5% fraud)?

**Answer:** This is the canonical risk/fraud question.
- **Don't use accuracy** — a 99.5% "always negative" model is useless. Use **precision/recall, F1, PR-AUC** (preferred over ROC-AUC under heavy imbalance), and choose the operating threshold by business cost.
- **Resampling:** SMOTE / oversampling minority, undersampling majority — fit *only on training folds* to avoid leakage.
- **Class weights / cost-sensitive learning** — penalize the rare-class errors (often cleaner than resampling).
- **Anomaly-detection framing** when positives are extremely rare.
- **Threshold tuning** to the cost matrix (a missed fraud vs a false alarm have very different costs).
Senior framing: the metric and threshold are *business decisions* — you set them with the risk owner, not in isolation.

### A3: L1 vs L2 regularization — when and why?

**Answer:** **L1 (Lasso)** adds |w| penalty → drives weights to exactly zero → feature selection / sparse, interpretable models (useful for auditable risk models). **L2 (Ridge)** adds w² penalty → shrinks weights smoothly, handles correlated features better, no hard zeros. **Elastic Net** combines both. Pick L1 when you want a sparse, explainable model or have many irrelevant features; L2 for stability with correlated predictors.

### A4: Explain gradient boosting (XGBoost/LightGBM) and why it dominates tabular risk problems.

**Answer:** Boosting builds trees **sequentially**, each fitting the residual errors (gradient) of the ensemble so far, with a learning rate shrinking each step. vs **Random Forest** (bagging — independent trees averaged to cut variance), boosting cuts **bias** and usually wins on structured/tabular data — which is most credit/fraud/risk data. Key knobs: `n_estimators`, `learning_rate`, `max_depth`, subsampling, and **`monotone_constraints`** (vital for risk models — enforce that, e.g., higher debt never lowers predicted risk). Pair with **SHAP** for per-decision explanations. This is why tabular risk teams reach for GBMs before deep nets.

### A5: Core deep-learning mechanics — backprop, vanishing gradients, and the fixes.

**Answer:** **Backpropagation** computes loss gradients w.r.t. weights via the chain rule, layer by layer; an optimizer (SGD/**Adam**) steps weights down the gradient. **Vanishing/exploding gradients** plague deep nets when repeated multiplications shrink/blow up signals. Fixes that you should name: **ReLU** activations (vs sigmoid/tanh saturation), **residual connections** (ResNet/Transformers), **batch/layer normalization**, careful initialization (He/Xavier), and **gradient clipping** for explosions. Regularize with **dropout**, weight decay, and early stopping.

### A6: PyTorch vs TensorFlow — how do you choose, and what's the modern reality?

**Answer:** **PyTorch** — dynamic graphs, Pythonic, dominant in research and increasingly production; the default for LLM/transformer work (Hugging Face is PyTorch-first). **TensorFlow/Keras** — strong production tooling historically (TF Serving, TFLite, TF.js), static-then-eager graphs. Modern reality: PyTorch has won most new work; pick TF if the existing stack/edge-deployment story demands it. Senior point: the framework rarely matters as much as data quality, evaluation, and serving — don't religious-war it.

### A7: Classic NLP before transformers — and why it still matters.

**Answer:** Be able to walk the progression: bag-of-words / **TF-IDF** → word embeddings (**Word2Vec**, GloVe — static, one vector per word) → contextual embeddings (ELMo, **BERT** — meaning shifts with context) → transformers/LLMs. Classic tasks: tokenization, lemmatization/stemming, POS tagging, NER, n-gram language models. Why it still matters: TF-IDF/BM25 powers the *sparse* half of hybrid retrieval; NER and regex still beat LLMs for cheap, deterministic PII/entity extraction; and understanding embeddings-as-vectors is the foundation of RAG.

### A8: Computer vision essentials a generalist should hold.

**Answer:** **CNNs** — convolution + pooling learn spatial feature hierarchies (edges → textures → objects); weight sharing makes them parameter-efficient and translation-invariant. Know **transfer learning** (fine-tune an ImageNet-pretrained ResNet on a small custom set — the practical default), classic tasks (classification, detection — YOLO/Faster R-CNN, segmentation — U-Net/Mask R-CNN), and the shift to **Vision Transformers (ViT)** and **multimodal models** (CLIP, GPT-4o/Claude vision) that embed image+text in a shared space — enabling multimodal RAG and document understanding (e.g., reading scanned risk/compliance docs).

### A9: How do you prevent data leakage, and why is it the #1 cause of "great in dev, broken in prod"?

**Answer:** Leakage = information available at training that won't exist at inference, inflating offline metrics. Common forms: fitting scalers/encoders/SMOTE on the **full** dataset before splitting; **target leakage** (a feature that's a proxy for the label, e.g., "collections_flag" predicting default); and **temporal leakage** (training on future data). Fixes: split first then fit transforms **inside a pipeline/CV fold**; use **time-based splits** for any time-ordered (risk/finance) data; audit top features for "too good to be true" predictors. Senior tell: you treat a suspiciously high AUC as a bug to investigate, not a win.

### A10: How do you validate a model destined for a risk/regulated decision?

**Answer:** Beyond a single test score: **time-based / out-of-time validation** (train on older, test on newer — mirrors deployment), **k-fold or stratified CV** for stability, **backtesting** on historical periods, **benchmarking** against a simpler champion, **stability** (PSI on scores across time), **calibration** (predicted probabilities match observed rates — essential when scores feed capital/pricing), and **subgroup/fairness** slicing. Document assumptions and limitations for the second-line validation team (ties to **Module 10 — SR 11-7 / MRM**).

---

## Section B: System Design for AI at Scale

> Expect 1–2 open-ended design prompts. Drive them: clarify requirements → propose architecture → name trade-offs → address scale, cost, failure, security, and evaluation. Below are common prompts with the skeleton of a senior answer.

### B1: Design an enterprise RAG assistant over 10M internal risk/compliance documents.

**Skeleton answer:**
- **Clarify:** users & QPS, latency SLA, freshness, access control (who can see which docs), accuracy/citation requirements, data residency.
- **Ingestion:** document loaders → chunking (semantic/recursive, overlap) → embeddings (Azure OpenAI) → **vector store** (pgvector on Azure Postgres if co-locating with metadata, or a dedicated DB at higher scale) + metadata for **RBAC filtering**. Incremental/CDC re-indexing on document updates.
- **Retrieval:** hybrid (vector + BM25) → **re-ranker** (cross-encoder) → top-k. Metadata/ACL filter *before* generation so users never see unauthorized content.
- **Generation:** grounded prompt with citations, low temperature, schema/guardrails; **groundedness check** before returning.
- **Cross-cutting:** semantic cache, eval harness (faithfulness/relevance) in CI, observability (latency/cost/tokens), PII handling, human escalation for low-confidence.
- **Trade-offs to voice:** dedicated vector DB vs pgvector; re-ranking latency vs precision; fine-tune vs RAG vs both.

### B2: Design a fraud-detection system that combines classic ML and an LLM.

**Skeleton answer:** Real-time tabular model (gradient-boosted, low-latency, calibrated) for the score; feature store for online/offline parity; threshold set to the cost matrix; **LLM as a second stage** to generate human-readable case narratives / explanations for analysts and to triage edge cases — *not* as the primary classifier (latency, cost, determinism, auditability). Drift monitoring + champion/challenger + human review queue. Emphasize **explainability (SHAP) and audit trail** for the regulated context.

### B3: How would you control cost and latency for a high-volume LLM product?

**Skeleton answer:** **Model routing** (small model for easy queries, frontier model only when needed); **prompt compression** and context pruning; **semantic + exact caching**; **batching** and streaming; **PTU/provisioned throughput** for predictable load vs PAYG for burst; **quantization** for self-hosted (AWQ/INT4 on vLLM/AKS); set token budgets and max-output caps; measure **cost-per-resolved-task**, not cost-per-call. Always tie the lever to its quality trade-off.

### B4: How do you evaluate and safely roll out a change to a production LLM system?

**Skeleton answer:** Offline **eval set** (golden Q&A + adversarial/red-team) scoring groundedness, relevance, safety → CI gate blocking on regression → **canary / shadow** traffic → online metrics (deflection, thumbs, escalation rate) → **blue-green or gradual rollout** with automated rollback on metric breach. Version prompts + model + retrieval together as one releasable unit. This *evaluation-gated, reversible* deployment is the senior signal (ties to Modules 8, 9, 12, 13).

---

## Section C: Technical Leadership & Behavioral (STAR)

> At 10+ years, ~30–40% of the loop is leadership and judgment. Prepare 5–6 concrete **STAR** stories (Situation, Task, Action, Result) with metrics, and map each to several of the themes below. Generic answers fail here.

### C1: "Tell me about a time you led an AI project end-to-end."
**What they assess:** ownership, scope, delivery, business impact.
**Structure:** problem & stakeholders → your architecture/decisions → how you de-risked (POC, evals, phased rollout) → **quantified outcome** (latency cut X%, $ saved, adoption, accuracy). End with what you'd do differently. Tie to a real production system.

### C2: "How do you mentor junior engineers and raise the team's bar?"
**What they assess:** the JD's explicit mentoring/technical-leadership requirement.
**Strong answer themes:** code/design reviews as teaching moments, pairing, setting standards (eval-first, testing, model cards), creating reusable templates/golden paths, sponsoring stretch work, and documenting decisions (ADRs). Give a concrete example where someone you mentored grew measurably.

### C3: "How do you translate a vague business problem into an AI solution?"
**What they assess:** stakeholder management + judgment + knowing when *not* to use AI.
**Answer:** Start from the business outcome and metric, not the tech. Assess feasibility (data, baseline, ROI), prototype the cheapest thing that could work, and **be willing to say a rules-based or classic-ML solution beats an LLM**. Define success metrics with stakeholders up front. The maturity signal is recommending the *simplest* solution that meets the need.

### C4: "Describe a time you disagreed with a stakeholder or were overruled."
**What they assess:** influence without authority, handling conflict, disagree-and-commit.
**Answer:** Show data-driven persuasion, acknowledging the other side's constraints, escalating appropriately, and committing professionally once decided. Avoid villain stories — show you optimize for the org, not ego.

### C5: "A model you shipped caused a bad outcome in production. What happened?"
**What they assess:** accountability, incident response, learning.
**Answer:** Own it. Walk detection → containment (fallback/rollback) → root cause → fix → **systemic prevention** (added monitoring, eval, governance step). For risk roles, emphasize the responsible-disclosure and audit angle. Blamelessness + concrete process improvement is what they want.

### C6: "How do you keep up with a field that changes monthly?"
**Answer:** A sustainable system, not heroics: a few primary sources, hands-on weekend prototypes, internal tech-talks/reading groups, and a bias toward **evaluating** new tech against your own benchmarks before adopting. Mention a recent thing you trialed and your verdict — shows discernment, not hype-chasing.

### C7: "How do you balance speed of delivery with responsible/safe AI?"
**What they assess:** the JD's responsible-AI + delivery tension.
**Answer:** They're not opposites if governance is built into the golden path (automated evals, content safety, logging, human-in-the-loop for high-risk). Tier the rigor by risk: a low-risk internal tool ships fast; a customer-facing credit decision goes through full MRM. Speed comes from *paved roads*, not from skipping controls.

---

## Section D: Rapid-Fire Senior Round

Crisp, correct, trade-off-aware one-liners:

- **RAG vs fine-tuning?** RAG for fresh/factual/changing knowledge + citations; fine-tuning for behavior/format/domain style/latency. Often both.
- **Temperature 0 always?** No — 0 for factual/extraction/classification; higher for creative/diverse generation.
- **Biggest RAG failure mode?** Retrieval, not generation — garbage context → garbage answer. Fix retrieval first.
- **Embedding dimension trade-off?** Higher = more expressive but more storage/compute; truncatable (Matryoshka) embeddings let you tune it.
- **When NOT to use an LLM?** Deterministic logic, simple classification with cheap features, hard latency/cost limits, or when a wrong answer is unacceptable and unverifiable.
- **Cosine vs dot product vs Euclidean?** Cosine for normalized semantic similarity (most common); dot product if magnitude carries meaning; match the index's operator class.
- **Agent vs simple chain?** Use an agent only when the path is genuinely dynamic/tool-dependent; chains are cheaper, faster, more predictable.
- **How to cut LLM cost 10x?** Route to smaller models, cache, compress prompts, cap tokens, batch — measure cost per *resolved task*.
- **Detect model drift?** PSI/KS on inputs, performance vs delayed labels, score-distribution stability; alert and trigger retrain/rollback.
- **PEFT/LoRA in one line?** Freeze base weights, train small low-rank adapters — fine-tune big models cheaply; QLoRA adds 4-bit quantization.
- **Quantization trade-off?** Smaller/faster/cheaper memory for a small quality hit; INT8/INT4 (AWQ/GPTQ) common for serving.
- **Why calibration matters in risk?** Scores feed pricing/capital/thresholds — they must mean true probabilities, not just rank order.
- **Guardrail an LLM output?** Input filters + prompt shields + schema validation + output content safety + groundedness check + human-in-the-loop for high-risk.

---

## Section E: Questions to Ask Your Interviewer

Senior candidates are also evaluating the role. Strong, signal-rich questions:

- How mature is your **MLOps/LLMOps**? What does the path from idea to production look like, and how long does it take?
- How is **model risk / responsible AI** governed here — is there an independent validation function?
- What's the **build vs buy** posture (Azure OpenAI/Foundry vs self-hosted open models)?
- How do you **evaluate** GenAI quality today, and how do you catch regressions?
- What does **technical leadership** look like — IC influence, mentoring, architecture ownership?
- Where is the team on **classic ML vs GenAI** for risk problems, and how do they decide?

---

## Related Modules

| Topic | Module |
|-------|--------|
| LLMs, prompting, hallucination, synthetic data | [Module 1](part-1-foundations/module-1-generative-ai/interview-questions.md) |
| LangChain orchestration | [Module 2](part-1-foundations/module-2-langchain/interview-questions.md) |
| RAG, vector DBs, **pgvector on Azure** | [Module 3](part-2-retrieval/module-3-rag-vectordb/interview-questions.md) |
| Agents / MCP / LangGraph | [Modules 4–6](part-3-agentic-ai/) |
| Architecture, CI/CD, Monitoring, **Governance/MRM** | [Modules 7–10](part-4-production/) |
| Fine-tuning, **Azure deployment**, LLMOps | [Modules 11–13](part-5-fine-tuning-deployment/) |
| Capstone production projects | [Module 14](part-6-capstone/module-14-projects/interview-questions.md) |

---

*This guide complements the per-module interview questions — use the modules for depth, this guide for breadth, leadership, and JD alignment.*
