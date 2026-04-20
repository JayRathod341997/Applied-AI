# RAGAS Framework Concepts

## Overview

RAGAS (Retrieval-Augmented Generation Assessment) is a framework for evaluating RAG pipelines using automated metrics. It provides reference-based and reference-free metrics for assessing hallucination, context relevance, and answer quality.

## Installation

```bash
pip install ragas
```

For latest features including advanced metrics:
```bash
pip install ragas[azure-openai]  # or ragas[openai] or ragas[cohere]
```

## Core Metrics

### 1. Faithfulness
Measures how faithfully the answer reflects the context without adding unverified information.

```python
from ragas.metrics import faithfulness

score = await faithfulness.evaluate(
    answer="The company was founded in 2020.",
    contexts=["Company XYZ was founded in 2020 by John Doe."],
    ground_truth="The company was founded in 2020."
)
# score: 0.0 - 1.0 (higher is better)
```

### 2. Answer Relevancy
Measures how relevant the answer is to the query.

```python
from ragas.metrics import answer_relevancy

score = await answer_relevancy.evaluate(
    answer="The meeting is at 3pm in the conference room.",
    query="When and where is the meeting?",
    contexts=["Meeting scheduled 3pm Conference Room A"]
)
```

### 3. Context Precision
Measures how precise the retrieved context is.

```python
from ragas.metrics import context_precision

score = await context_precision.evaluate(
    contexts=[
        "Meeting scheduled 3pm Conference Room A",
        "Company founded in 2020",
        "Q4 revenue was $1M"
    ],
    question="When was the company founded?",
    ground_truth="Company was founded in 2020"
)
```

### 4. Context Recall
Measures if all relevant information was retrieved.

```python
from ragas.metrics import context_recall

score = await context_recall.evaluate(
    contexts=["Company founded in 2020", "Revenue was $1M"],
    ground_truth="Company founded in 2020 with revenue of $1M"
)
```

### 5. Context Entity Recall
Measures entity-level recall.

```python
from ragas.metrics import context_entity_recall

score = await context_entity_recall.evaluate(
    contexts=["Acme Corp was acquired by Beta Inc for $500M"],
    ground_truth="Acme Corp was acquired by Beta Inc for $500M"
)
```

## Reference-Free vs Reference-Based

### Reference-Free (No Ground Truth)
Uses only the generated answer and retrieved context:

- `faithfulness`
- `answer_relevancy`
- `context_precision`

### Reference-Based (Requires Ground Truth)
Uses ground truth for comparison:

- `context_recall`
- `context_entity_recall`

## Combined Evaluation

Run multiple metrics at once:

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)

results = evaluate(
    dataset=eval_dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall
    ]
)
```

## Dataset Format

RAGAS expects datasets in a specific format:

```python
from datasets import Dataset

eval_dataset = Dataset.from_dict({
    "question": [
        "When was the company founded?",
        "What is the return policy?"
    ],
    "answer": [
        "The company was founded in 2020.",
        "Returns accepted within 30 days."
    ],
    "contexts": [
        ["Company founded in 2020 by John Doe"],
        ["Return policy: 30-day returns for unused items"]
    ],
    "ground_truth": [
        "The company was founded in 2020.",
        "30-day return policy for unused items"
    ]
})
```

## Integration with LangChain

```python
from langchain.chat_models import ChatOpenAI
from ragas.langchain import EvaluatorChain

# Create evaluator chain
evaluator = EvaluatorChain(
    llm=ChatOpenAI(temperature=0),
    metrics=[faithfulness, answer_relevancy]
)

# Use in RAG pipeline
result = rag_chain.invoke(query)
eval_result = evaluator.evaluate(result)

if eval_result["faithfulness"] < 0.7:
    # Trigger retry or fallback
    result = fallback_chain.invoke(query)
```

## Integration with LangGraph

```python
from ragas.langchain import EvaluatorChain

# Define evaluation node
def evaluate_node(state):
    result = state["generation"]
    score = evaluator.evaluate(result)
    
    if score["faithfulness"] < 0.8:
        return {"needs_regeneration": True}
    return {"needs_regeneration": False}

# Add to graph
workflow.add_node("evaluate", evaluate_node)
```

## Custom Metrics

Create custom hallucination metrics:

```python
from ragas.metrics.base import MetricWithLLM

class hallucination_detector(MetricWithLLM):
    name = "hallucination_detector"
    
    async def _ascore(self, answer, contexts, prompt):
        llm = self.llm
        prompt = f"""
        Analyze if the following answer contains hallucinations.
        Answer: {answer}
        Contexts: {contexts}
        
        Return a JSON with "has_hallucination" (bool) and "reason" (str).
        """
        result = await llm.agenerate([prompt])
        return parse_json_response(result)
```

## Cost Optimization

RAGAS makes LLM calls for evaluation. Minimize costs:

1. Use gpt-3.5-turbo for eval (not gpt-4)
2. Batch evaluations in single calls
3. Use reference-free metrics when possible
4. Cache evaluation results

```python
# Batch evaluation for cost efficiency
results = evaluate(
    dataset=eval_dataset.batch(10),  # Process in batches
    metrics=[faithfulness, answer_relevancy]
)
```

## Interpreting Results

| Faithfulness | Interpretation |
|--------------|----------------|
| 0.9 - 1.0 | Excellent - minimal hallucination risk |
| 0.7 - 0.9 | Good - minor issues possible |
| 0.5 - 0.7 | Moderate - review required |
| < 0.5 | Poor - high risk of hallucinations |

| Context Precision | Interpretation |
|------------------|----------------|
| 0.8 - 1.0 | Retrieval working well |
| 0.6 - 0.8 | Room for improvement |
| < 0.6 | Significant retrieval issues |