# Drift Detection - Interview Questions

This document contains interview questions and answers covering drift detection in Generative AI systems.

---

## 1. Fundamentals of Drift

### Q1: What is drift in the context of ML/AI systems?

**Answer:** Drift is the gradual change in data distributions, model behavior, or system performance over time. In Generative AI systems, drift can significantly impact response quality and accuracy. It represents the phenomenon where the statistical properties of data used for model training differ from the data the model encounters in production.

---

### Q2: What are the main types of drift in ML systems?

**Answer:** The main types of drift include:

1. **Data Drift (Feature Drift)**: Changes in the input data distribution
   - Changes in user query patterns
   - New vocabulary or terminology
   - Document format changes

2. **Concept Drift**: Changes in the relationship between input and target
   - Sudden drift: Abrupt changes (e.g., policy changes)
   - Gradual drift: Slow progressive changes
   - Recurring drift: Periodic patterns
   - Blip drift: Temporary anomalies

3. **Target Drift**: Changes in the expected output distribution

4. **Label Drift**: Changes in ground truth labels over time

---

### Q3: Why is drift detection important for GenAI systems?

**Answer:** Drift detection is crucial because:

- **Quality Degradation**: Model outputs become less accurate or relevant over time
- **User Experience**: Poor responses lead to user dissatisfaction
- **Cost Implications**: Inefficient processing of irrelevant retrievals
- **Maintenance**: Early detection enables proactive model updates
- **Trust**: Users rely on AI systems for accurate information

---

## 2. Drift Detection Methods

### Q4: What is Population Stability Index (PSI) and how is it used?

**Answer:** PSI (Population Stability Index) is a metric that measures the shift between two distributions:

- **Formula**: PSI = Σ (Actual% - Expected%) × ln(Actual% / Expected%)
- **Interpretation**:
  - PSI > 0.2: Significant drift - action required
  - 0.1 < PSI ≤ 0.2: Moderate drift - monitor closely
  - PSI ≤ 0.1: No significant drift

PSI is commonly used in finance and insurance for credit scoring models and has become standard in ML monitoring.

---

### Q5: How do you detect embedding drift?

**Answer:** Embedding drift detection methods include:

1. **Cluster Structure Monitoring**: Track how data points cluster over time
2. **Retrieval Result Stability**: Compare retrieved results before/after updates
3. **Embedding Comparison**: Test same text with old vs new embeddings
4. **A/B Testing**: Compare model versions in production
5. **Distance Distribution**: Monitor changes in embedding distance distributions

---

### Q6: What statistical tests are used for drift detection?

**Answer:** Common statistical tests include:

| Test | Use Case |
|------|----------|
| Kolmogorov-Smirnov | Continuous distribution comparison |
| Chi-Squared Test | Categorical data changes |
| Wasserstein Distance | Distribution similarity |
| KL Divergence | Information loss measurement |
| T-Test | Mean shift detection |

---

## 3. RAG-Specific Drift

### Q7: How does drift affect RAG systems specifically?

**Answer:** In RAG systems, drift impacts multiple components:

**Retrieval Stage:**
- Query embedding drift affects retrieval quality
- Knowledge base staleness reduces relevance
- Document chunking becomes misaligned with queries

**Generation Stage:**
- Context quality degrades with poor retrieval
- Model may generate hallucinations with irrelevant context
- User satisfaction drops with off-topic responses

**Indicators:**
- Increased zero-result queries
- Lower average similarity scores
- More irrelevant document retrievals
- User complaints about outdated information

---

### Q8: How do you detect knowledge base staleness?

**Answer:** Knowledge base staleness detection:

1. **Timestamp Tracking**: Monitor when documents were last updated
2. **Query Analysis**: Track queries about new topics not in knowledge base
3. **Retrieval Quality Metrics**: Monitor recall/precision over time
4. **Content Change Detection**: Monitor source documents for updates
5. **User Feedback**: Collect feedback on response accuracy
6. **Topic Coverage Analysis**: Map query topics to indexed content

---

## 4. Handling Drift

### Q9: What are reactive vs proactive drift handling strategies?

**Answer:**

**Reactive Strategies:**
- Trigger model retraining when drift is detected
- Switch to fallback models or rules
- Route complex cases to human agents
- Alert operations teams for intervention

**Proactive Strategies:**
- Continuous monitoring with automated alerts
- Canary deployments for testing changes
- A/B testing for model version comparison
- Versioned knowledge bases
- Scheduled model updates based on calendar
- User feedback integration

---

### Q10: What are the best practices for setting drift detection thresholds?

**Answer:** Best practices include:

1. **Establish Baselines**: Create reference distributions during stable periods
2. **Historical Analysis**: Study drift patterns in historical data
3. **Business Context**: Align thresholds with business impact
4. **Granular Monitoring**: Different thresholds for different metrics
5. **Alert Fatigue**: Avoid too many false positives
6. **Iterative Tuning**: Adjust based on production experience

---

## 5. Production Implementation

### Q11: How would you implement a drift detection system for a production RAG?

**Answer:** Implementation approach:

1. **Data Collection**:
   - Log all queries and retrieval results
   - Track embedding values
   - Monitor user feedback

2. **Metrics Computation**:
   - Calculate distribution statistics
   - Compute drift scores (PSI, KL divergence)
   - Track retrieval quality metrics

3. **Alerting**:
   - Define threshold rules
   - Set up notification channels
   - Create runbooks for response

4. **Response**:
   - Automated retraining triggers
   - Fallback mechanisms
   - Dashboard for visualization

5. **Tools**:
   - Evidently AI for drift detection
   - Prometheus/Grafana for metrics
   - OpenTelemetry for observability

---

### Q12: How do you handle drift in agent workflows?

**Answer:** Agent-specific drift handling:

- **Tool Behavior**: Monitor tool success/failure rates
- **Execution Paths**: Track if agents choose different paths
- **Success Rates**: Monitor task completion rates over time
- **Latency Changes**: Track step execution times
- **Tool Updates**: Handle drift when tools change versions
- **Escalation Patterns**: Monitor when agents request human help

---

## 6. Advanced Topics

### Q13: What is the difference between offline and online drift detection?

**Answer:**

| Aspect | Offline Detection | Online Detection |
|--------|-------------------|-------------------|
| Timing | Post-hoc analysis | Real-time |
| Data | Batch processing | Streaming |
| Response | Retrospective | Immediate |
| Use Case | Model evaluation | Production monitoring |
| Tools | Jupyter, experiments | Streaming pipelines |

Online drift detection is preferred for production systems to enable rapid response.

---

### Q14: How do you handle concept drift in a production LLM system?

**Answer:** Handling concept drift in LLM systems:

1. **Prompt Adaptation**: Update prompts to handle new scenarios
2. **Fine-tuning**: Periodically fine-tune on recent data
3. **RAG Updates**: Refresh knowledge bases with new information
4. **Fallback Strategies**: Use rule-based responses for known issues
5. **Human Feedback Loop**: Route uncertain cases to humans
6. **A/B Testing**: Test prompt changes before full rollout

---

### Q15: What are the challenges in drift detection for generative AI?

**Answer:** Key challenges:

1. **Probabilistic Outputs**: Harder to define "correct" behavior
2. **Ground Truth Delay**: Labels may come days later
3. **Multi-component Systems**: Drift can occur in any component
4. **Quality Assessment**: Difficult to measure output quality automatically
5. **Latency Requirements**: Real-time detection needs efficient algorithms
6. **Alert Fatigue**: Too many alerts lead to ignored warnings
7. **False Positives**: Legitimate changes vs actual drift

---

## Summary

Key drift detection topics:

1. **Types of Drift**: Data, concept, embedding, knowledge base
2. **Detection Methods**: PSI, statistical tests, monitoring metrics
3. **RAG Impact**: Retrieval quality, generation quality
4. **Handling Strategies**: Reactive and proactive approaches
5. **Production Implementation**: Tools, thresholds, alerting

---

## References

- [Drift Detection Concepts](./concepts.md)
- [References](./references.md)
- [Observability](../01_observability/)
