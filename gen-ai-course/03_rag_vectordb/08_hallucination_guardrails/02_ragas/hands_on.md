# RAGAS Hands-On Tutorial

## Step 1: Setup Environment

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Set up OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
```

## Step 2: Create Evaluation Dataset

```python
from datasets import Dataset

# Sample evaluation data
eval_data = {
    "question": [
        "What is the company's return policy?",
        "Who founded the company?",
        "When is the annual meeting?",
        "What was the Q3 revenue?",
        "Where is the headquarters?"
    ],
    "answer": [
        "The company offers a 30-day return policy for all items.",
        "The company was founded by John Smith in 2020.",
        "The annual meeting is scheduled for December 15th.",
        "Q3 revenue was $2.5 million.",
        "The headquarters is in San Francisco, California."
    ],
    "contexts": [
        ["Return Policy: We offer 30-day returns for all purchased items."],
        ["Founded: Company XYZ was founded in 2020 by John Smith."],
        ["Annual Meeting: Scheduled for December 15th, 2024 at 2pm."],
        ["Q3 Revenue: $2.5 million (unaudited)."],
        ["Headquarters: 123 Tech Street, San Francisco, CA 94102"]
    ],
    "ground_truth": [
        "30-day return policy for all items",
        "Founded by John Smith in 2020",
        "December 15th, 2024",
        "$2.5 million",
        "San Francisco, California"
    ]
}

eval_dataset = Dataset.from_dict(eval_data)
```

## Step 3: Evaluate with RAGAS

```python
import asyncio
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)

async def run_evaluation():
    results = await evaluate(
        dataset=eval_dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ],
        llm=ChatOpenAI(temperature=0)
    )
    return results

results = asyncio.run(run_evaluation())
print(results)
```

## Step 4: Analyze Results

```python
import pandas as pd

# Convert results to DataFrame for analysis
df = results.to_pandas()

# Identify problematic samples
problematic = df[df["faithfulness"] < 0.7]
print("Low faithfulness samples:")
print(problematic[["question", "answer", "faithfulness"]])

# Aggregate metrics
print(f"\nAverage Faithfulness: {df['faithfulness'].mean():.2f}")
print(f"Average Answer Relevancy: {df['answer_relevancy'].mean():.2f}")
print(f"Average Context Precision: {df['context_precision'].mean():.2f}")
```

## Step 5: Integrate with RAG Pipeline

```python
from langchain_openai import ChatOpenAI
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.merger import MergerRetriever
from langchain_community.callbacks import get_ragas_callback

class RAGASEvaluator:
    def __init__(self, retriever,llm):
        self.retriever = retriever
        self.llm = llm
        self.evaluator = EvaluatorChain(llm=llm, metrics=[faithfulness, answer_relevancy])
    
    def invoke(self, query):
        # Retrieve
        docs = self.retriever.invoke(query)
        contexts = [doc.page_content for doc in docs]
        
        # Generate
        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever
        )
        answer = chain.invoke(query)
        
        # Evaluate
        eval_result = self.evaluator.evaluate({
            "answer": answer["text"],
            "contexts": contexts,
            "question": query
        })
        
        return {
            "answer": answer["text"],
            "evaluation": eval_result,
            "needs_regeneration": eval_result["faithfulness"] < 0.8
        }

# Usage
evaluator = RAGASEvaluator(retriever=retriever, llm=ChatOpenAI(temperature=0))
result = evaluator.invoke("What is the return policy?")
```

## Step 6: CI/CD Integration

```python
# test_rag.py
import pytest
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

@pytest.mark.asyncio
async def test_rag_faithfulness():
    results = await evaluate(
        dataset=test_dataset,
        metrics=[faithfulness]
    )
    
    assert results["faithfulness"].mean() >= 0.8, \
        f"Faithfulness {results['faithfulness'].mean():.2f} below threshold"

@pytest.mark.asyncio
async def test_rag_answer_relevancy():
    results = await evaluate(
        dataset=test_dataset,
        metrics=[answer_relevancy]
    )
    
    assert results["answer_relevancy"].mean() >= 0.75
```

Run tests:
```bash
pytest tests/test_rag.py -v --tb=short
```

## Step 7: Continuous Monitoring

```python
# evaluation_job.py (run daily via cron/Dagster/airflow)
import asyncio
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datetime import datetime, timedelta

async def daily_evaluation():
    # Get recent queries from logs
    recent_queries = get_queries_from_logs(days=1)
    
    dataset = convert_to_ragas_format(recent_queries)
    
    results = await evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy]
    )
    
    # Log to monitoring
    log_metrics(
        metric="rag_faithfulness",
        value=results["faithfulness"].mean(),
        timestamp=datetime.now()
    )
    
    # Alert if degraded
    if results["faithfulness"].mean() < 0.7:
        alert_team(f"Faithfulness dropped to {results['faithfulness'].mean():.2f}")

asyncio.run(daily_evaluation())
```

## Complete Working Example

```python
"""
Complete RAGAS Evaluation Example
"""
import os
import asyncio
from datetime import datetime
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from langchain_openai import ChatOpenAI

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

EVAL_DATA = {
    "question": [
        "What is the refund policy?",
        "Who is the CEO?",
        "When was the company founded?"
    ],
    "answer": [
        "Full refunds within 30 days.",
        "Jane Doe is the CEO.",
        "The company was founded in 2019."
    ],
    "contexts": [
        ["Refund Policy: Full refund within 30 days of purchase."],
        ["CEO: Jane Doe since 2022."],
        ["Founded: Company started in 2019."]
    ],
    "ground_truth": [
        "Full refund within 30 days",
        "Jane Doe",
        "2019"
    ]
}

async def main():
    dataset = Dataset.from_dict(EVAL_DATA)
    
    results = await evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ],
        llm=ChatOpenAI(temperature=0)
    )
    
    print("\n=== RAGAS Evaluation Results ===")
    print(results.to_pandas())
    print(f"\nOverall Scores:")
    print(f"  Faithfulness: {results['faithfulness'].mean():.3f}")
    print(f"  Answer Relevancy: {results['answer_relevancy'].mean():.3f}")
    print(f"  Context Precision: {results['context_precision'].mean():.3f}")
    print(f"  Context Recall: {results['context_recall'].mean():.3f}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting

### API Errors
```python
# Handle rate limits with retry
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
async def evaluate_with_retry(*args, **kwargs):
    return await evaluate(*args, **kwargs)
```

### Context Too Long
```python
# Truncate contexts if they exceed model limits
def truncate_contexts(contexts, max_tokens=4000):
    import tiktoken
    encoder = tiktoken.get_encoding("cl100k_base")
    
    truncated = []
    total_tokens = 0
    
    for ctx in contexts:
        tokens = len(encoder.encode(ctx))
        if total_tokens + tokens > max_tokens:
            break
        truncated.append(ctx)
        total_tokens += tokens
    
    return truncated
```