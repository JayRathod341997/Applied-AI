# Exercise: TruLens Guardrails Implementation

## Objective

Implement real-time guardrails using TruLens for a production RAG system.

## Setup

```bash
pip install trulens trulens-apps trulens-providers trulens-langchain langchain-openai
```

## Tasks

### Task 1: Setup Feedback Provider

```python
from trulens.providers.openai import OpenAI as OpenAIFeedback

provider = OpenAIFeedback()
```

### Task 2: Create Feedback Functions

1. Groundedness - how well answer is supported by context
2. Context Relevance - relevance of retrieved chunks
3. Answer Relevance - answer addresses the question

```python
from trulens import Feedback

f_groundedness = (
    Feedback(
        provider.groundedness_measure,
        higher_is_better=True
    )
    .on(context=...)
    .on(response=...)
)
```

### Task 3: Create Threshold Guardrail

Implement guardrails that:
- Block responses below threshold
- Use fallback response

```python
from trulens.guardrails import ThresholdGuardrail

guardrail = ThresholdGuardrail(
    metrics={
        "groundedness": 0.7,
        "context_relevance": 0.5
    },
    on_failure="fallback"
)
```

### Task 4: Integrate with RAG App

Wrap the RAG application with guardrails:

```python
guarded_app = guardrail.wrap(rag_app)

response, feedback = guarded_app.query_with_feedback(question)
```

### Task 5: Handle Fallbacks

Handle fallback scenarios properly:

```python
def handle_response(response, feedback):
    if feedback["groundedness"] < 0.7:
        return {
            "answer": get_fallback_response(),
            "is_fallback": True
        }
    return {"answer": response, "is_fallback": False}
```

## Deliverables

1. Complete working Python script
2. Guardrail threshold configuration
3. Fallback handling implementation
4. Test cases showing guardrails in action

## Expected Output

```
Query: What is the return policy?
Answer: 30-day returns available
Groundedness: 0.92
Guardrails: PASSED ✓

Query: [Question with no context]
Answer: I don't have that information
Groundedness: N/A (fallback)
Guardrails: FALLBACK ✓
```