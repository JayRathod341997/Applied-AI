# TruLens Hands-On Tutorial

## Step 1: Environment Setup

```python
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["TRUERA_API_KEY"] = os.getenv("TRUERA_API_KEY")  # Optional, for TruEra cloud
```

## Step 2: Basic RAG with Guardrails

```python
from trulens.apps.langchain import LangChainRag
from trulens.feedback import Groundedness
from trulens.providers.openai import OpenAI as OpenAIFeedback
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Setup provider
provider = OpenAIFeedback()

# Define feedback functions
f_groundedness = (
    Feedback(
        provider.groundedness_measure,
        higher_is_better=True,
    )
    .on(context=...)
    .on(response=...)
)

f_context_relevance = (
    Feedback(
        provider.context_relevance,
        higher_is_better=True,
    )
    .on(question=...)
    .on(context=...)
)

# Create RAG app with guardrails
rag_app = LangChainRag(
    llm=ChatOpenAI(temperature=0),
    retriever=vector_store.as_retriever(),
    feedback_functions=[f_groundedness, f_context_relevance]
)

# Query with feedback
response, feedback = rag_app.query_with_feedback(
    "What is the return policy?"
)
print(f"Response: {response}")
print(f"Groundedness: {feedback['groundedness']}")
```

## Step 3: Implementing Guardrails

```python
from trulens.guardrails import ThresholdGuardrail
from trulens.apps.langchain import LangChainRag

# Create guardrail with thresholds
guardrail = ThresholdGuardrail(
    metrics={
        "groundedness": 0.7,
        "context_relevance": 0.5
    },
    action="fallback"  # What to do when threshold is breached
)

# Wrap the RAG app
guarded_app = guardrail.wrap(rag_app)

# Use in production
def query_with_guardrails(query: str):
    response = guarded_app.query(query)
    
    if response.is_fallback:
        # Handle fallback gracefully
        return {
            "text": "I couldn't find a reliable answer. Please contact support.",
            "is_fallback": True
        }
    
    return {
        "text": response.text,
        "is_fallback": False,
        "metrics": response.feedback
    }
```

## Step 4: Complete Example with All Integrations

```python
"""
Complete TruLens Integration Example
"""
import os
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

from trulens.apps.langchain import LangChainRag
from trulens.feedback import (
    Groundedness,
    ContextRelevance,
    AnswerRelevance
)
from trulens.providers.openai import OpenAI as OpenAIFeedback
from trulens.guardrails import ThresholdGuardrail
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA

# 1. Setup feedback provider
provider = OpenAIFeedback()

# 2. Setup vector store
embeddings = OpenAIEmbeddings()
vector_store = Chroma(
    collection_name="company_docs",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

# 3. Create feedback functions
feedbacks = [
    Groundedness(provider),
    ContextRelevance(provider),
    AnswerRelevance(provider)
]

# 4. Create RAG app
rag_app = LangChainRag(
    llm=ChatOpenAI(temperature=0),
    retriever=vector_store.as_retriever(),
    feedback_functions=feedbacks
)

# 5. Create guardrail
guardrail = ThresholdGuardrail(
    metrics={
        "groundedness": 0.75,
        "context_relevance": 0.6,
        "answer_relevance": 0.7
    },
    on_failure="fallback",
    fallback_response="I don't have enough information to answer that reliably."
)

# 6. Wrap with guardrail
guarded_app = guardrail.wrap(rag_app)

# 7. Production query handler
def query_user(question: str):
    """
    Query handler with automatic hallucination protection.
    """
    # Get response with evaluation
    response, feedback = guarded_app.query_with_feedback(question)
    
    return {
        "answer": response,
        "feedback": feedback,
        "guardrails_passed": feedback["groundedness"] >= 0.75
    }

# Test
if __name__ == "__main__":
    test_queries = [
        "What is the return policy?",
        "Who founded the company?"
    ]
    
    for query in test_queries:
        result = query_user(query)
        print(f"\nQuery: {query}")
        print(f"Answer: {result['answer']}")
        print(f"Groundedness: {result['feedback']['groundedness']}")
        print(f"Passed: {result['guardrails_passed']}")
```

## Step 5: Dashboard for Monitoring

```python
"""
Launch TruLens Dashboard for monitoring
"""
from trulens.dashboard import TruDashboard

# Create dashboard
dashboard = TruDashboard(
    app=guarded_app,
    port=8501,
    share=True  # Create public link
)

# Launch
dashboard.launch()
```

## Step 6: CI/CD Integration

```python
# test_guardrails.py
import pytest
from trulens.apps.langchain import LangChainRag
from trulens.feedback import Groundedness

@pytest.mark.asyncio
async def test_guardrails_threshold():
    """Ensure guardrails pass in CI/CD"""
    
    # Run evaluation
    response, feedback = app.query_with_feedback(
        "What is the return policy?"
    )
    
    # Assert thresholds
    assert feedback["groundedness"] >= 0.7
    assert feedback["context_relevance"] >= 0.5

# Run in CI
# pytest tests/test_guardrails.py -v
```

## Step 7: Async Production Usage

```python
import asyncio
from trulens.apps.langchain import LangChainRag

# Create app
app = LangChainRag(...)

async def handle_query_async(query: str):
    """Async query handler"""
    response, feedback = await app.aquery_with_feedback(query)
    return response, feedback

async def stream_handler(query: str):
    """Streaming with async feedback"""
    async for chunk, feedback in app.astream_with_feedback(query):
        yield chunk, feedback

# Run
async def main():
    response, feedback = await handle_query_async("Tell me about the company")
    print(response)
```

## Cost Optimization

```python
# Use smaller models for feedback evaluation
from trulens.providers.openai import OpenAI as OpenAIFeedback

# Initialize with cheaper model
provider = OpenAIFeedback(
    model_name="gpt-3.5-turbo"  # Instead of gpt-4
)

# Lower frequency of evaluations
guardrail = ThresholdGuardrail(
    eval_every_n=5,  # Evaluate every 5 queries
    thresholds={...}
)
```

## Running in Production

```python
# production_app.py
from fastapi import FastAPI
from trulens.apps.langchain import LangChainRag
from trulens.dashboard import TruDashboard
import uvicorn

app = FastAPI()

# Initialize RAG with guardrails
rag_app = create_guarded_rag()

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    response, feedback = rag_app.aquery_with_feedback(request.question)
    
    return {
        "answer": response,
        "feedback": feedback,
        "latency_ms": feedback.get("latency_ms", 0)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Troubleshooting

### Connection Issues
```python
# Check TruLens connection
from trulens import connect

# Verify setup
trulens = connect(app)
print(trulens.get_status())
```

### Performance Issues
```python
# Enable caching for feedback
from trulens.cache import DiskCache

cache = DiskCache(provider=provider)

# Use cached evaluations
feedback = cached_feedback(
    query=query,
    response=response,
    contexts=contexts
)
```