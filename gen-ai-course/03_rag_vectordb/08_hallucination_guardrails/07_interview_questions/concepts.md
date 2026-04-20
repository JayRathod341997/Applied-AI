# Interview Questions: Hallucination Guardrails

## Theory Questions

### Q1: What is hallucination in the context of RAG systems?
**Answer:** Hallucination in RAG systems occurs when an LLM generates content that is:
- Factually incorrect or not supported by the retrieved context
- Contradicts information in the source documents
- Contains fabricated details not present in any retrieved data
- Misses critical context that would change the answer

Hallucinations differ from simple errors because they present false information as if it were true, which can be particularly dangerous in production systems.

### Q2: What are the main causes of hallucinations in RAG pipelines?
**Answer:** The main causes are:

1. **Retrieval Failures**: Wrong or irrelevant chunks retrieved due to poor embedding quality, insufficient top-k, or bad chunking strategies

2. **Context Integration Issues**: Multiple conflicting contexts not properly resolved, or context window limitations

3. **Generation Issues**: High temperature settings, insufficient grounding instructions in prompts, or model limitations

4. **Knowledge Base Problems**: Outdated information, incomplete documentation, or inconsistent source content

### Q3: Explain the difference between RAGAS and TruLens.
**Answer:**

| Aspect | RAGAS | TruLens |
|--------|-------|--------|
| Use Case | Offline evaluation, testing | Production guardrails |
| Timing | Post-generation evaluation | Real-time evaluation |
| Setup Complexity | Simple | More complex |
| Cost | Pay per evaluation | Infrastructure + evaluation |
| Integration | LangChain, LangGraph | LangChain, LangGraph, LlamaIndex |

RAGAS is ideal for development and CI/CD pipelines, while TruLens is designed for production guardrails with real-time monitoring.

### Q4: What is the "faithfulness" metric in RAGAS?
**Answer:** Faithfulness measures how accurately the generated answer reflects the information in the retrieved context without adding unverified information. It checks if the claims made in the answer can be supported by the source documents.

A faithful answer stays within the bounds of the provided context, while an unfaithful answer might add details not present in any source.

### Q5: How does context precision differ from context recall?
**Answer:**

- **Context Precision**: The proportion of retrieved chunks that are relevant to answering the query. High precision means we retrieve mostly relevant information.

- **Context Recall**: The proportion of all relevant information in the knowledge base that was successfully retrieved. High recall means we didn't miss important information.

Both metrics are important: precision ensures we don't confuse the model with irrelevant context, while recall ensures we don't miss critical information.

## Implementation Questions

### Q6: How would you implement a guardrail that prevents hallucinations in production?
**Answer:** I would implement defense in depth:

1. **Retrieval Layer**: Ensure quality retrieval with hybrid search and reranking
2. **Prompt Layer**: Include explicit grounding instructions
3. **Guardrail Layer**: Use TruLens with threshold guardrails
4. **Evaluation Layer**: Run RAGAS evaluation in CI/CD

```python
guardrail = ThresholdGuardrail(
    metrics={"groundedness": 0.7, "context_relevance": 0.5},
    on_failure="fallback"
)
guarded_app = guardrail.wrap(rag_app)
```

### Q7: What strategies would you use to tune hallucination guardrail thresholds?
**Answer:** 

1. **Start with defaults**: Use recommended thresholds (0.7 groundedness)
2. **Analyze fallback cases**: Review samples that trigger fallbacks
3. **A/B test**: Compare different threshold values
4. **Iterate based on production data**: Adjust based on real-world performance
5. **Segment by query type**: Use different thresholds for factual vs. creative queries

### Q8: How would you handle a query where the retrieval returns empty results?
**Answer:**

```python
def handle_empty_retrieval(question: str):
    docs = retriever.invoke(question)
    
    if not docs:
        # Return safe response instead of generating
        return {
            "answer": "I don't have information about that topic.",
            "is_fallback": True,
            "reason": "no_retrieval"
        }
    
    # Continue with normal flow
    return generate_with_context(question, docs)
```

Never let the model generate when there's no context - this is a primary source of hallucinations.

### Q9: Explain how you would integrate RAGAS into a CI/CD pipeline.
**Answer:**

```python
# In pytest
def test_rag_faithfulness():
    results = evaluate(
        dataset=test_dataset,
        metrics=[faithfulness, answer_relevancy]
    )
    
    assert results["faithfulness"].mean() >= 0.8

# In GitHub Actions
- name: Run RAGAS evaluation
  run: |
    pytest tests/test_rag.py -v --tb=short
```

This ensures no degraded code reaches production.

### Q10: How would you monitor hallucination metrics in production?
**Answer:**

1. **Collect feedback**: Use TruLens to track groundedness over time
2. **Create dashboards**: Visualize trends in Grafana/Datadog
3. **Set alerts**: Alert when metrics degrade below threshold
4. **Review fallbacks**: Analyze cases that trigger fallbacks
5. **Iterate**: Update thresholds and retrieval based on findings

```python
# Alert on degradation
if metrics["groundedness_avg"] < 0.7:
    send_alert(f"Groundedness at {metrics['groundedness_avg']}")
```

## Scenario-Based Questions

### Q11: A user reports that the RAG system is generating incorrect dates. How would you diagnose this?
**Answer:**

1. **Check retrieval**: Is the knowledge base current?
2. **Check generation**: Is the model using stale context?
3. **Add temporal guardrails**: Include timestamps in context
4. **Review metrics**: Check if context recall is low for temporal queries

### Q12: Your guardrails are triggering too often, affecting user experience. What would you do?
**Answer:**

1. **Analyze triggers**: Review what's causing false positives
2. **Adjust thresholds**: Lower slightly (e.g., 0.7 → 0.65)
3. **Improve retrieval**: Better context often solves the problem
4. **Add query classification**: Different thresholds for different query types

### Q13: Why might faithfulness be low even when context precision is high?
**Answer:** This indicates a generation problem - the model is ignoring good context. Possible causes:
- Prompt doesn't emphasize grounding
- Temperature too high
- Model has strong prior that conflicts with context

**Solution:** Improve prompt, lower temperature, or use a different model.

### Q14: How would you handle conflicting information in retrieved documents?
**Answer:**

1. **Detect conflicts**: Use additional LLM call to identify contradictions
2. **Prioritize sources**: Apply source ranking/filtering
3. **Acknowledge uncertainty**: "Sources provide conflicting information..."
4. **Present all views**: Show multiple perspectives when conflicts exist

## Advanced Questions

### Q15: How would you implement custom hallucination detection for specific domains?
**Answer:**

```python
class DomainHallucinationDetector(MetricWithLLM):
    async def _ascore(self, answer, contexts):
        # Domain-specific checks
        if self.domain == "medical":
            # Check against known contraind interactions
            return check_medication_errors(answer)
        elif self.domain == "legal":
            # Check jurisdiction
            return check_jurisdiction(answer)
```

### Q16: What are the trade-offs between guardrail strictness and user experience?
**Answer:**

- **Strict guardrails**: Fewer hallucinations but more fallbacks
- **Lenient guardrails**: Better UX but higher hallucination risk
- **Solution**: Segment by query criticality (medical queries = strict, casual queries = lenient)

### Q17: How would you handle multilingual hallucination detection?
**Answer:** 
- Use multilingual models or language-specific evaluation
- Check cross-language consistency
- Account for translation artifacts in evaluation

### Q18: What's the relationship between retrieval quality and hallucinations?
**Answer:** Direct relationship - poor retrieval leads to hallucinations. Focus on:
- Improving retrieval > fixing generation
- Better chunking, embedding, and search strategies
- Use hybrid search + reranking