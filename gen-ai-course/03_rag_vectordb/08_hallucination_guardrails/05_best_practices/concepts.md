# Hallucination Guardrails Best Practices

## Design Principles

### 1. Defense in Depth
Implement multiple layers of hallucination protection:

```
Layer 1: Retrieval Quality
└── Ensure relevant chunks are retrieved
    ├── Tune top-k and similarity threshold
    ├── Use hybrid search
    └── Implement reranking

Layer 2: Generation Guardrails  
└── Guide the model during generation
    ├── Include grounding instructions in prompt
    ├── Require citations
    └── Use lower temperature

Layer 3: Output Validation
└── Check output before returning
    ├── Run RAGAS evaluation
    ├── Verify claims against context
    └── Check for contradictions

Layer 4: Feedback Integration
└── Learn from production feedback
    ├── Collect user feedback
    ├── Monitor fallback rates
    └── Iterate on thresholds
```

### 2. Fail Gracefully
Always have a fallback strategy:

```python
class GuardedRAG:
    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
        self.guardrail = ThresholdGuardrail(
            groundedness_threshold=0.7
        )
    
    def query(self, question: str):
        # Try primary path
        try:
            docs = self.retriever.invoke(question)
            context = format_docs(docs)
            answer = self.generate_with_context(question, context)
            
            # Evaluate
            eval_result = self.guardrail.evaluate(answer, context)
            
            if eval_result.passed:
                return answer
            else:
                # Fallback 1: Try again with different params
                answer = self.generate_with_fresh_model(question, context)
                if self.guardrail.evaluate(answer, context).passed:
                    return answer
                
        except Exception as e:
            logger.error(f"Error in primary path: {e}")
        
        # Fallback 2: Return safe response
        return self.get_fallback_response(question)
    
    def get_fallback_response(self, question: str):
        return "I don't have enough information to answer this question reliably."
```

### 3. Measure What Matters

Key metrics to track:

| Metric | Description | Target |
|--------|-------------|--------|
| Faithfulness Rate | % answers passing guardrails | > 0.85 |
| Fallback Rate | % queries using fallback | < 0.15 |
| Retrieval Precision | % retrieved chunks relevant | > 0.7 |
| Latency | Query to response time | < 3s |
| Cost per Query | Evaluation cost | < $0.01 |

## Implementation Guidelines

### Prompt Engineering

```python
# Good prompt with grounding instructions
BASE_PROMPT = """You are a helpful assistant.

Important Instructions:
1. Only use information from the provided context
2. If the context doesn't contain enough information, say so explicitly
3. Cite sources when making specific claims
4. Don't add information not present in the context

Context:
{context}

Question: {question}

Answer: """
```

### Retrieval Tuning

```python
# Tune retrieval for better context
retriever = VectorStoreRetriever(
    search_type="similarity",
    search_kwargs={
        "k": 10,  # Increased from default
        "filter": metadata_filter
    }
)

# Add hybrid search
from langchain.retrievers import EnsembleRetriever

ensemble = EnsembleRetriever(
    retrievers=[semantic_retriever, keyword_retriever],
    weights=[0.7, 0.3]
)
```

### Temperature Management

```python
# Use lower temperature for factual queries
def get_temperature(question_type: str) -> float:
    """Return appropriate temperature based on query type."""
    if question_type == "factual":
        return 0.0  # Most deterministic
    elif question_type == "explanatory":
        return 0.3
    elif question_type == "creative":
        return 0.7
    return 0.0  # Default to low
```

### Citation Requirements

```python
# Force citations in output
CITATION_PROMPT = """Format your answer as JSON:
{{
    "answer": "your answer here",
    "citations": ["source 1", "source 2"]
}}

Important: Only cite sources from the provided context.
If you cannot find relevant information, return:
{{
    "answer": "No information available",
    "citations": []
}}
"""
```

## Monitoring and Observability

### Key Dashboards

```python
# Generate monitoring metrics
def get_hallucination_metrics(app_id: str, time_range: str) -> dict:
    """Return key metrics for monitoring."""
    return {
        "faithfulness_avg": db.query(
            f"SELECT AVG(groundedness) FROM feedback "
            f"WHERE app_id = {app_id} AND timestamp > {time_range}"
        ),
        "fallback_rate": db.query(
            f"SELECT COUNT(*) * 1.0 / total "
            f"FROM feedback WHERE is_fallback = true"
        ),
        "worst_queries": db.query(
            f"SELECT query, groundedness "
            f"FROM feedback WHERE groundedness < 0.5 "
            f"ORDER BY timestamp DESC LIMIT 10"
        )
    }
```

### Alerting Rules

```python
# Alert on metric degradation
def check_and_alert(metrics: dict):
    if metrics["faithfulness_avg"] < 0.7:
        send_alert(
            channel="alerts",
            message=f"Faithfulness degraded to {metrics['faithfulness_avg']:.2f}"
        )
    
    if metrics["fallback_rate"] > 0.2:
        send_alert(
            channel="alerts", 
            message=f"Fallback rate increased to {metrics['fallback_rate']:.2f}"
        )
```

## Common Pitfalls to Avoid

### 1. Over-Relying on One Guardrail
**Bad:** Single evaluation metric
```python
# ❌ Don't do this
guardrail = ThresholdGuardrail(groundedness=0.7)
```

**Good:** Multiple feedback functions
```python
# ✅ Do this instead
feedbacks = [
    Groundedness(provider),
    ContextRelevance(provider),
    AnswerRelevance(provider),
    FactCorrectness(provider)  # Custom metric
]
```

### 2. Ignoring Edge Cases
**Bad:** No handling for unknown queries
```python
# ❌ Don't let unknown queries pass through
answer = llm.invoke(question)  # May fabricate
```

**Better:** Explicit unknown handling
```python
# ✅ Check for unknown queries
contexts = retriever.invoke(question)
if not contexts:
    return "I don't have information about that."
```

### 3. Setting Thresholds Too High
**Bad:** Unrealistic thresholds
```python
# ❌ Causes excessive fallbacks
guardrail = ThresholdGuardrail(groundedness=0.95)
```

**Good:** Tuned thresholds
```python
# ✅ Start with reasonable defaults
guardrail = ThresholdGuardrail(
    groundedness=0.7,  # Adjust based on data
    context_relevance=0.5
)
```

### 4. No Feedback Loop
**Bad:** Static guardrails
```python
# ❌ No improvement over time
guardrail = StaticGuardrail(thresholds={...})
```

**Good:** Adaptive thresholds
```python
# ✅ Learn from production
guardrail = AdaptiveGuardrail(
    initial_thresholds={...},
    adaptation_rate=0.1,  # Update based on feedback
    min_samples=100  # Wait for enough data
)
```

## Testing Best Practices

### Unit Tests
```python
def test_retrieval_quality():
    # Test retrieval returns relevant docs
    docs = retriever.invoke("return policy")
    assert len(docs) >= 3
    assert any("return" in d.page_content.lower() for d in docs)

def test_guardrail_threshold():
    # Test guardrail correctly identifies hallucination
    result = guardrail.evaluate(
        answer="Company founded in 2020",  # Not in context
        context=["Company founded in 2019"]
    )
    assert not result.passed
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_full_pipeline():
    # End-to-end test with guardrails
    result = app.query("What is the return policy?")
    assert result.answer is not None
    assert result.feedback["groundedness"] >= 0.7
```

### Load Tests
```python
async def test_guardrail_performance():
    # Test latency under load
    times = []
    for _ in range(100):
        start = time.time()
        app.query("test query?")
        times.append(time.time() - start)
    
    avg_time = sum(times) / len(times)
    assert avg_time < 3.0  # Within SLA
```