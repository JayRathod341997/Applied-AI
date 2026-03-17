# CI/CD & Lifecycle Management - Interview Questions

This document contains interview questions and answers covering Module 8: CI/CD & Lifecycle Management for GenAI.

---

## 1. Versioning and Deployment

### Q1: What do you version in GenAI systems?

**Answer:** What to version:

- **Code:** Application code
- **Models:** LLM model versions
- **Prompts:** Prompt templates and versions
- **Embeddings:** Vector database indexes
- **Agent Graphs:** LangGraph/LangChain workflows
- **Configuration:** System settings
- **Data:** Training data, documents

---

### Q2: How does CI/CD differ for software vs ML vs GenAI systems?

**Answer:** Comparison:

| Aspect | Software | ML | GenAI |
|--------|----------|----|----|------|
| Build | Compile | Train | Prompt + Build |
| Test | Unit tests | Quality metrics | Behavior tests |
| Artifacts | Binary | Model weights | Prompts + Indexes |
| Rollback | Easy | Hard | Prompt changes |

---

### Q3: How do you design promotion flows for GenAI?

**Answer:** Promotion flow:

```
Dev → Staging → Production
```

Steps:
1. **Dev:** Test new prompts/models locally
2. **Staging:** Integration tests, A/B with small traffic
3. **Production:** Full rollout with monitoring

---

### Q4: What are rollback strategies for GenAI?

**Answer:** Rollback strategies:

- **Prompt Rollback:** Revert to previous prompt version
- **Model Rollback:** Switch to previous model version
- **Embedding Rollback:** Restore previous vector index
- **Agent Rollback:** Revert to previous workflow

---

### Q5: How do you manage changes to agent logic?

**Answer:** Agent change management:

1. **Version Control:** Store agent graphs in Git
2. **Testing:** Test new agent behavior thoroughly
3. **Canary:** Deploy to small subset first
4. **Monitoring:** Watch for failures
5. **Rollback Plan:** Always have backup

---

## Production Questions

### Q6: What CI/CD tools work well with GenAI?

**Answer:** Tools:

- **GitHub Actions:** Workflow automation
- **GitLab CI:** Pipeline management
- **Jenkins:** Custom pipelines
- **AWS CodePipeline:** Cloud-native
- **Azure DevOps:** Microsoft ecosystem
- **Weights & Biases:** ML experiment tracking

---

### Q7: How do you test prompts in CI/CD?

**Answer:** Prompt testing:

1. **Unit Tests:** Test prompt outputs
2. **Golden Sets:** Expected responses
3. **Regression Tests:** Ensure no degradation
4. **Quality Checks:** Hallucination detection

---

## Summary

Key CI/CD topics:

1. **Versioning:** What to track
2. **Promotions:** Dev → Staging → Prod
3. **Rollbacks:** Strategies
4. **Tools:** CI/CD for GenAI

---

## References

- [CI/CD Best Practices](references.md)
- [GenAI Deployment Guide](references.md)
