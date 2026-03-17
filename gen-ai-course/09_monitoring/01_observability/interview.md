# Monitoring & Observability - Interview Questions

This document contains interview questions and answers covering Module 9: Monitoring, Drift & Governance for RAG & Agents.

---

## 1. Observability Fundamentals

### Q1: Why does ML monitoring differ from application monitoring in GenAI systems?

**Answer:** ML monitoring differences:

- **Model Behavior:** ML outputs are probabilistic, not deterministic
- **Quality Metrics:** Need AI-specific metrics beyond uptime
- **Data Dependencies:** Monitoring input data distribution
- **Concept Drift:** Model behavior changes over time
- **Multi-component:** RAG has retrieval + generation to monitor
- **Ground Truth Delay:** Labels may come hours/days later

---

### Q2: What are operational metrics vs AI-specific metrics?

**Answer:**

**Operational Metrics:**
- Uptime, latency, error rates, throughput
- CPU/memory usage, API response times
- Standard DevOps metrics

**AI-Specific Metrics:**
- Retrieval quality (recall, precision)
- Hallucination rates
- Response accuracy
- User satisfaction scores
- Token usage, cost per request

---

### Q3: What is data drift in RAG systems?

**Answer:** Data drift types:

- **Input Drift:** User queries change over time
- **Feature Drift:** Document content changes
- **Embedding Drift:** Embedding model updates change representations
- **Knowledge Base Staleness:** Outdated information

Detection: Monitor query distributions, track retrieval results, compare embeddings

---

### Q4: What is embedding drift and how do you detect it?

**Answer:** Embedding drift occurs when:

1. Embedding model is updated
2. Vector representations change
3. Previously similar items become dissimilar

Detection methods:
- Monitor cluster structure over time
- Track retrieval result stability
- Compare embeddings before/after updates
- A/B test old vs new embeddings

---

### Q5: How do you monitor agent behavior and failures?

**Answer:** Agent monitoring includes:

- **Execution Tracing:** Track each step in agent workflow
- **Success Rates:** Per-step and overall task completion
- **Tool Usage:** Which tools are called, how often
- **Failure Analysis:** Categorize failure types
- **Escalation Paths:** When do agents need human help?
- **Latency:** Time per step and total task time

---

### Q6: What are Human-in-the-Loop (HITL) checkpoints?

**Answer:** HITL implementations:

- **Pre-execution:** Human approves before dangerous actions
- **Post-execution:** Human reviews before returning to user
- **On-demand:** Human can interrupt agent execution
- **Escalation:** Agent requests help when uncertain

Design considerations: When to interrupt, what to show human, how to handle responses

---

### Q7: What are A/B testing strategies for prompts and agent workflows?

**Answer:** A/B testing approach:

1. **Define Metrics:** Success rate, latency, user satisfaction
2. **Traffic Split:** Random 50/50 or 90/10
3. **Run Duration:** Sufficient statistical significance
4. **Guardrail Monitoring:** Ensure no harm in test
5. **Rollout:** Gradually increase winning variant

Testing targets:
- Prompt variations
- Model changes
- Retrieval strategies
- Agent workflow modifications

---

## Production Monitoring Questions

### Q8: What metrics should you track for a RAG system?

**Answer:** Key metrics:

**Retrieval:**
- Recall@k, Precision@k
- Average similarity scores
- Zero-result rate

**Generation:**
- Token usage, latency
- Error rates
- Hallucination rate (if measurable)

**System:**
- API latency, throughput
- Vector DB query time
- Cache hit rates

**Business:**
- User satisfaction
- Task completion rate
- Cost per conversation

---

### Q9: How do you set up alerting for GenAI systems?

**Answer:** Alerting setup:

1. **Define SLAs:** Latency thresholds, error budgets
2. **Baseline Metrics:** Establish normal behavior
3. **Alert Rules:** 
   - High error rates
   - Latency exceeds threshold
   - Retrieval quality drops
   - Cost spikes
4. **Alert Channels:** PagerDuty, Slack, email
5. **Runbooks:** Document response procedures

---

### Q10: What is the difference between observability and monitoring?

**Answer:**

| Aspect | Monitoring | Observability |
|--------|------------|----------------|
| Focus | Known unknowns | Unknown unknowns |
| Approach | Predefined metrics | Explore system state |
| Questions | "Is X broken?" | "Why is X broken?" |
| Tools | Dashboards, alerts | Logs, traces, metrics |
| Use Case | Detect failures | Debug complex issues |

For GenAI: Need both traditional monitoring + observability for debugging AI-specific issues

---

## Debugging and Troubleshooting

### Q11: How do you debug a RAG system with poor retrieval?

**Answer:** Debugging steps:

1. **Query Analysis:** Is the query well-formed?
2. **Embedding Check:** Generate embedding, inspect values
3. **Index Inspection:** Verify chunks exist, are indexed
4. **Similarity Analysis:** Check returned scores
5. **Chunk Inspection:** Review retrieved content
6. **Ground Truth Test:** Test with known queries

Tools: VectorDB explorers, embedding visualizers, query log analysis

---

### Q12: How do you handle latency spikes in production?

**Answer:** Latency handling:

1. **Identify Component:** Is it retrieval, generation, or network?
2. **Check Scaling:** Are services overwhelmed?
3. **Review Dependencies:** External API status
4. **Analyze Payload Size:** Are requests too large?
5. **Implement Caching:** Cache frequent queries
6. **Add Timeouts:** Prevent hanging requests

---

### Q13: What tools are available for GenAI observability?

**Answer:** Tools:

- **LangSmith:** LangChain debugging and tracing
- **Arize AI:** ML model monitoring
- **Weights & Biases:** Experiment tracking
- **Datadog ML:** ML monitoring
- **OpenTelemetry:** Standard observability
- **Custom Dashboards:** Grafana, Looker

---

## Drift Detection

### Q14: How do you detect knowledge base staleness?

**Answer:** Staleness detection:

1. **Timestamp Tracking:** When was each document indexed?
2. **Query Analysis:** Are users asking about new topics?
3. **Retrieval Quality:** Has recall dropped?
4. **Content Change Detection:** Monitor source for updates
5. **User Feedback:** Flag outdated responses

---

### Q15: How do you handle model drift?

**Answer:** Drift handling:

1. **Continuous Monitoring:** Track quality metrics over time
2. **Retraining Triggers:** When to update models
3. **Canary Deployments:** Test new versions safely
4. **Rollback Capability:** Quick reversion if needed
5. **A/B Testing:** Compare model versions

---

## Summary

Key monitoring topics:

1. **ML vs App Monitoring:** Why AI needs special treatment
2. **Metrics:** Operational + AI-specific
3. **Drift Detection:** Data, embedding, knowledge base
4. **Agent Monitoring:** Behavior, failures, escalation
5. **A/B Testing:** Prompt and workflow experimentation

---

## References

- [Observability Best Practices](references.md)
- [ML Monitoring Tools](references.md)
- [Drift Detection Methods](references.md)
