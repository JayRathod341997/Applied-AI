# TruLens Framework Concepts

## Overview

TruLens provides real-time guardrails for LLM applications. Unlike RAGAS (offline evaluation), TruLens is designed for production use cases with:
- Real-time hallucination detection
- Feedback-based grounding
- Streaming evaluation
- Cost-effective monitoring

## Installation

```bash
pip install trulens trulens-apps trulens-providers
```

For OpenAI integration:
```bash
pip install trulens-providers-openai
```

For LangChain integration:
```bash
pip install trulens-langchain
```

## Core Concepts

### 1. Feedback Functions
Feedback functions evaluate outputs in real-time:

```python
from trulens import Feedback
from trulens.providers.openai import OpenAI

provider = OpenAI()

# Define feedback for hallucination detection
f_hallucination = Feedback(
    provider.hallucination_with_critique,
    higher_is_better=True
).on(output=...)

# Define feedback for relevance
f_answer_relevance = Feedback(
    provider.relevance,
    higher_is_better=True
).on(input=...).on(output=...)
```

### 2. RAG Triples
TruLens evaluates the RAG triple (query, retrieval, response):

```python
from trulens.apps.langchain import LangChainAgent
from trulens.feedback import Groundedness

# Create app with feedback
app = LangChainAgent(
    chain=qa_chain,
    feedbacks=[f_hallucination, f_answer_relevance]
)

# Use in production
response = app.query(user_query)
```

### 3. Groundedness
Measures if the response is grounded in retrieved context:

```python
from trulens.feedback import Groundedness

groundedness = Groundedness(provider=provider)

# Evaluate single interaction
result = groundedness(
    query="What is the return policy?",
    response="30-day returns available",
    retrieved_contexts=["30-day return policy"]
)
# Returns: (groundedness_score, critique)
```

## Architecture Components

### TruLens Dashboard
Visualization and monitoring interface:

```python
from trulens.dashboard import connect

# Connect to running app
trulens = connect(app)
trulens.get_dashboard_url()
```

### Feedback Store
Persistent storage for evaluation results:

```python
from trulens.db import Connect

db = Connect(database="trulens.db")

# Store feedback
db.insert_feedback(
    app_id="production-rag",
    query=query,
    response=response,
    feedbacks={
        "groundedness": 0.9,
        "relevance": 0.85
    }
)
```

### Guardrails
Real-time intervention on low-quality responses:

```python
from trulens.guardrails import RuleBasedGuardrail

guardrail = RuleBasedGuardrail(
    thresholds={
        "groundedness": 0.7,
        "relevance": 0.6
    },
    on_failure="fallback"  # or "retry" or "reject"
)

# Apply to chain
guarded_chain = guardrail.apply(rag_chain)
```

## Integration with LangChain

### Basic Integration

```python
from trulens.apps.langchain import LangChainRag
from trulens.feedback import (
    Groundedness,
    ContextRelevance
)

# Create RAG app
rag_app = LangChainRag(
    llm=ChatOpenAI(temperature=0),
    retriever=vector_store.as_retriever(),
    feedback_functions=[
        Groundedness(provider),
        ContextRelevance(provider)
    ]
)

# Query with feedback
response, feedback = rag_app.query_with_feedback(
    "What is the company's mission?"
)
```

### Streaming Integration

```python
# Use with LangChain streaming
from trulens.apps.langchain import LangChainRag

rag_app = LangChainRag(
    llm=ChatOpenAI streaming=True)
)

# Stream with evaluation
for chunk in rag_app.stream("Tell me about your product"):
    process(chunk)
    
# Get final evaluation
eval_summary = rag_app.get_feedback_summary()
```

### Custom Feedback Functions

```python
from trulens import Feedback
from trulens.providers.openai import OpenAI

provider = OpenAI()

@Feedback
def custom_relevance(query: str, response: str) -> float:
    """Custom relevance score based on entity matching."""
    query_entities = extract_entities(query)
    response_entities = extract_entities(response)
    
    overlap = len(set(query_entities) & set(response_entities))
    return overlap / max(len(query_entities), 1)
```

## Guardrail Types

### 1. Threshold Guardrails
Block responses below quality threshold:

```python
from trulens.guardrails import ThresholdGuardrail

guardrail = ThresholdGuardrail(
    metrics=["groundedness", "answer_relevance"],
    thresholds={"groundedness": 0.7, "answer_relevance": 0.6}
)
```

### 2. Rule-Based Guardrails
Custom logic:

```python
from trulens.guardrails import RuleGuardrail

guardrail = RuleGuardrail(
    rules=[
        lambda q, r: "I don't know" if r is None else r,
        lambda q, r: r if contains_citations(r) else fallback(r)
    ]
)
```

### 3. Model-Based Guardrails
Use LLM as guardrail:

```python
from trulens.guardrails import LLMBasedGuardrail

guardrail = LLMBasedGuardrail(
    prompt="Is this response hallucinated? Answer yes/no.",
    on_yes="regenerate",
    on_no="accept"
)
```

## Real-Time Monitoring

### Dashboard Setup

```python
from trulens.dashboard import TruDashboard
import streamlit as st

dashboard = TruDashboard(
    app=rag_app,
    port=8501
)

dashboard.launch()
```

### Custom Metrics Collection

```python
from trulens import Track

tracker = Track(app_name="production-rag")

# Track in production
@tracker.track
def handle_query(query: str):
    response = rag_chain.invoke(query)
    return response

# Or use context manager
with tracker.track() as track:
    response = rag_chain.invoke(query)
    metrics = track.get_metrics()
```

## Comparison: TruLens vs RAGAS

| Aspect | RAGAS | TruLens |
|--------|-------|---------|
| Use Case | Offline evaluation | Production guardrails |
| Execution | Batch after generation | Real-time |
| Cost | Pay per evaluation | Pay per evaluation + infrastructure |
| Latency | Not critical | Must be low latency |
| Setup | Simple | More setup required |
| Integration | LangChain, LangGraph | LangChain, LangGraph, LlamaIndex |

## Best Practices

1. **Start with RAGAS** for development testing
2. **Deploy TruLens** for production monitoring
3. **Use threshold guardrails** as first line of defense
4. **Collect feedback** from production for improvement
5. **Tune thresholds** based on real-world performance
6. **A/B test** different guardrail configurations