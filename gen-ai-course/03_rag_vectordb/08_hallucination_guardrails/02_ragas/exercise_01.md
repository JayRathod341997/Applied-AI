# In-Memory RAG Evaluation Exercise

This hands-on exercise demonstrates how RAGAS metrics work by implementing them with pure Python data structures in memory.

## Objective

- Inspect evaluation datasets in memory
- Calculate faithfulness scores manually
- Detect hallucinations through data comparison
- Validate results with assertions

## Quick Start

Run the Python exercise file:

```bash
cd gen-ai-course/03_rag_vectordb/08_hallucination_guardrails/02_ragas
python hands_on_exercise.py
```

## Exercise Structure

The exercise is in `hands_on_exercise.py` - it includes:

1. **Sample data** - 5 RAG evaluation samples with questions, answers, contexts, and ground truth
2. **Tasks** - Step-by-step instructions to inspect, analyze, and validate the data
3. **Expected outputs** - Show what results should look like after each task

## What You'll Learn

- How RAG evaluation datasets are structured (lists of dictionaries)
- How faithfulness metrics work (word overlap between answer and context)
- How to detect hallucinations (comparing years, locations in answer vs context)
- How to validate results with assertions

## Manual Calculation Example

The core of the exercise is understanding how RAGAS calculates faithfulness:

```python
# Answer words NOT in context = potential hallucination
answer_words = {"founded", "2019", "john", "smith"}
context_words = {"founded", "2020", "team", "5", "members"}

overlap = answer_words & context_words = {"founded"}
faithfulness = 1 / 4 = 0.25  # Low score = potential hallucination
```

This is exactly what RAGAS does internally - just with more sophisticated NLP.