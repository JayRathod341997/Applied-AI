# MLOps for GenAI - Interview Questions

This document contains interview questions and answers covering Module 6: MLOps Foundations for GenAI Systems.

---

## 1. MLOps Overview

### Q1: Why do GenAI and Agentic systems require MLOps?

**Answer:** MLOps needs for GenAI:

- **Model Management:** Multiple models (LLM, embeddings)
- **Data Versioning:** Document versions, embeddings
- **Prompt Management:** Track prompt versions
- **Agent Workflows:** Complex, stateful systems
- **Cost Tracking:** Per-request costs
- **Quality Monitoring:** Hallucinations, retrieval quality

---

### Q2: How does MLOps differ from DevOps in the context of GenAI?

**Answer:** Differences:

| Aspect | DevOps | MLOps for GenAI |
|--------|--------|-----------------|
| Versioning | Code | Code + Models + Prompts + Embeddings |
| Testing | Unit/Integration | Quality metrics + Behavior |
| Deployment | Rolling | A/B + Gradual |
| Monitoring | Uptime | Quality + Drift |
| Rollback | Code | Prompt/Model changes |

---

### Q3: What is the end-to-end lifecycle for GenAI systems?

**Answer:** Lifecycle:

1. **Data Collection:** Gather documents, data
2. **Preprocessing:** Chunking, embedding
3. **Model Selection:** Choose LLMs
4. **Prompt Development:** Create and test prompts
5. **Agent Design:** Build workflows
6. **Deployment:** Push to production
7. **Monitoring:** Track quality
8. **Iteration:** Improve based on feedback

---

### Q4: What is an enterprise MLOps reference architecture?

**Answer:** Architecture layers:

```
┌─────────────────────────────────────┐
│         Training Layer              │
│    (Fine-tuning, Prompt Tuning)    │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         Inference Layer             │
│      (LLM APIs, Embedding)         │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│       Orchestration Layer           │
│    (LangChain, LangGraph, etc.)    │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         Monitoring Layer            │
│   (Quality, Costs, Performance)    │
└─────────────────────────────────────┘
```

---

## 2. Cloud-Native MLOps

### Q5: How do RAG pipelines fit into MLOps?

**Answer:** RAG MLOps:

- **Data Pipeline:** Document loading, chunking
- **Embedding Pipeline:** Generate and store embeddings
- **Retrieval Tuning:** Test different chunk sizes
- **Index Management:** Version vector indexes
- **Prompt Management:** Track retrieval prompts

---

### Q6: What are cloud-native MLOps platforms?

**Answer:** Platforms:

- **AWS SageMaker:** End-to-end ML platform
- **Azure ML:** Microsoft MLops solution
- **Google Vertex AI:** GCP ML platform
- **DataRobot:** AutoML platform
- **Weights & Biases:** Experiment tracking
- **MLflow:** Open-source MLOps

---

### Q7: How do you version in GenAI systems?

**Answer:** Versioning:

- **Code:** Git for application code
- **Models:** Model registry versions
- **Prompts:** Prompt library versions
- **Embeddings:** Embedding versions
- **Agent Graphs:** LangGraph state graphs
- **Data:** Document versions

---

## Production Questions

### Q8: What are the key metrics to track in GenAI MLOps?

**Answer:** Key metrics:

- **Operational:** Latency, throughput, uptime
- **Quality:** Retrieval quality, hallucination rate
- **Cost:** Per-request, daily, monthly
- **Business:** Task completion, user satisfaction

---

### Q9: How do you implement continuous deployment for GenAI?

**Answer:** CD for GenAI:

1. **Test Prompts:** Automated prompt testing
2. **Staged Rollout:** Dev → Staging → Prod
3. **Feature Flags:** Control new features
4. **A/B Testing:** Compare versions
5. **Monitoring:** Watch for issues

---

### Q10: What is the difference between training and inference in GenAI?

**Answer:**

| Aspect | Training | Inference |
|--------|----------|-----------|
| Frequency | Occasional | Continuous |
| Cost | High (one-time) | Lower (ongoing) |
| Latency | Not critical | Critical |
| GPU Needed | Yes | Often via API |

---

## Summary

Key MLOps topics:

1. **Why MLOps:** GenAI-specific needs
2. **Lifecycle:** End-to-end pipeline
3. **Cloud Platforms:** AWS, Azure, GCP
4. **Versioning:** What to version
5. **Monitoring:** Key metrics

---

## References

- [MLOps Best Practices](references.md)
- [Cloud ML Platforms](references.md)
