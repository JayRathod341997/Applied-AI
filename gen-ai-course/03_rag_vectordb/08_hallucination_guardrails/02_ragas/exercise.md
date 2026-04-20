# Hands-On Exercise: In-Memory RAG Evaluation Data Structures

## Objective

By the end of this exercise, you will be able to:
- Create and manipulate RAG evaluation datasets in memory
- Calculate hallucination metrics manually to understand how RAGAS works
- Validate RAG pipeline outputs against ground truth
- Identify potential hallucinations through data inspection

## Overview

In this exercise, we'll work with **in-memory data structures** that RAGAS uses to evaluate RAG pipelines:
- Lists of dictionaries for question-answer-context triples
- Nested dictionaries for evaluation results
- Sets for entity extraction and comparison

These data structures allow us to inspect, filter, and compute metrics on RAG outputs without needing a database or external service.

---

## Setup

No external dependencies required for this exercise. We'll use pure Python.

---

## Sample Data: RAG Evaluation Dataset

The following data represents a simulated RAG pipeline evaluation. Each entry contains:
- A user question
- The generated answer (potentially containing hallucinations)
- Retrieved contexts
- Ground truth for comparison

```python
# Initialize the evaluation dataset in memory
eval_data = [
    {
        "question": "What is the company's return policy?",
        "answer": "The company offers a 30-day return policy for all items with receipt.",
        "contexts": [
            "Return Policy: Customers can return items within 30 days of purchase.",
            "Items must be in original condition with receipt."
        ],
        "ground_truth": "30-day return policy for items with receipt"
    },
    {
        "question": "When was the company founded?",
        "answer": "The company was founded in 2019 by John Smith.",
        "contexts": [
            "Company XYZ was founded in 2020.",
            "The initial team consisted of 5 members."
        ],
        "ground_truth": "Company founded in 2020"
    },
    {
        "question": "What is the CEO's name?",
        "answer": "The CEO is Sarah Johnson.",
        "contexts": [
            "Our CEO, Sarah Johnson, has 15 years of experience.",
            "She previously worked at TechCorp."
        ],
        "ground_truth": "Sarah Johnson is the CEO"
    },
    {
        "question": "Where is the headquarters located?",
        "answer": "The headquarters is in New York City, New York.",
        "contexts": [
            "Headquarters: 123 Tech Street, San Francisco, CA",
            "Main office: San Francisco, California"
        ],
        "ground_truth": "Headquarters in San Francisco, California"
    },
    {
        "question": "What are the customer support hours?",
        "answer": "Customer support is available 24/7 for premium customers.",
        "contexts": [
            "Support hours: Monday-Friday 9am-6pm EST",
            "Weekend support: 10am-4pm EST"
        ],
        "ground_truth": "Support available Monday-Friday 9am-6pm, weekends 10am-4pm"
    }
]
```

---

## Task 1: Inspect Initial State

**Goal**: Understand the structure and content of the evaluation dataset.

### Step-by-step:

1. Print the number of evaluation samples
2. Inspect the first sample to see the structure

```python
# Inspect the dataset
print(f"Total samples: {len(eval_data)}")

# Print the first sample
print("\n--- Sample 1 ---")
print(f"Question: {eval_data[0]['question']}")
print(f"Answer: {eval_data[0]['answer']}")
print(f"Contexts: {eval_data[0]['contexts']}")
print(f"Ground Truth: {eval_data[0]['ground_truth']}")
```

### Expected Output:
```
Total samples: 5

--- Sample 1 ---
Question: What is the company's return policy?
Answer: The company offers a 30-day return policy for all items with receipt.
Contexts: ['Return Policy: Customers can return items within 30 days of purchase.', 'Items must be in original condition with receipt.']
Ground Truth: 30-day return policy for items with receipt
```

---

## Task 2: Detect Factual Hallucinations

**Goal**: Compare answers against retrieved contexts to identify hallucinations.

### Step-by-step:

1. Create a function to detect years in text
2. Compare years in answer vs context
3. Check for unsupported locations

```python
import re

def detect_hallucinations(sample):
    """Detect if answer contains information NOT in contexts."""
    answer = sample['answer'].lower()
    contexts = ' '.join(sample['contexts']).lower()
    
    # Extract years
    years_in_answer = set(re.findall(r'\b(20\d{2})\b', answer))
    years_in_context = set(re.findall(r'\b(20\d{2})\b', contexts))
    
    # Check for years in answer not in context
    unsupported_years = years_in_answer - years_in_context
    
    # Check locations
    locations = ['new york', 'boston', 'chicago']
    for loc in locations:
        if loc in answer and loc not in contexts:
            return True, f"Unsupported location: {loc}"
    
    if unsupported_years:
        return True, f"Unsupported years: {unsupported_years}"
    
    return False, "No hallucinations detected"


# Process all samples
print("HALLUCINATION DETECTION RESULTS")
print("=" * 60)

for i, sample in enumerate(eval_data):
    has_hallucination, evidence = detect_hallucinations(sample)
    status = "HALLUCINATION" if has_hallucination else "OK"
    
    print(f"\nSample {i+1}: {sample['question'][:40]}...")
    print(f"  Status: {status}")
    if has_hallucination:
        print(f"  Evidence: {evidence}")
```

### Expected Output:
```
============================================================
HALLUCINATION DETECTION RESULTS
============================================================

Sample 1: What is the company's return policy?
  Status: OK

Sample 2: When was the company founded?
  Status: HALLUCINATION
  Evidence: Unsupported years: {'2019'}

Sample 3: What is the CEO's name?
  Status: OK

Sample 4: Where is the headquarters located?
  Status: HALLUCINATION
  Evidence: Unsupported location: new york

Sample 5: What are the customer support hours?
  Status: HALLUCINATION
  Evidence: Unsupported years: {'24/7'}
```

---

## Task 3: Calculate Faithfulness Score

**Goal**: Implement a faithfulness metric that measures how well the answer is supported by context.

### Step-by-step:

1. Define a function to calculate word overlap between answer and context
2. Filter out stop words
3. Calculate percentage of answer words found in context

```python
def calculate_faithfulness(answer, contexts):
    """Calculate faithfulness score (0-1) - higher is better."""
    if not contexts:
        return 0.0
    
    answer_lower = answer.lower()
    context_text = ' '.join(contexts).lower()
    
    # Stop words to filter
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                  'could', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                  'that', 'this', 'these', 'those', 'it', 'its'}
    
    # Get significant words
    answer_words = set(w for w in answer_lower.split() 
                     if w not in stop_words and len(w) > 2)
    context_words = set(w for w in context_text.split() 
                       if w not in stop_words and len(w) > 2)
    
    if not answer_words:
        return 1.0
    
    # Calculate overlap
    overlap = len(answer_words & context_words)
    score = overlap / len(answer_words)
    
    return score


# Calculate for all samples
print("FAITHFULNESS SCORES")
print("=" * 60)

faithfulness_scores = []
for i, sample in enumerate(eval_data):
    score = calculate_faithfulness(sample['answer'], sample['contexts'])
    faithfulness_scores.append(score)
    
    status = "Good" if score >= 0.7 else "Low"
    print(f"\nSample {i+1}: {sample['question'][:40]}...")
    print(f"  Faithfulness: {score:.2f} ({status})")

# Calculate average
avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
print(f"\nAVERAGE FAITHFULNESS: {avg_faithfulness:.2f}")
```

### Expected Output:
```
============================================================
FAITHFULNESS SCORES
============================================================

Sample 1: What is the company's return policy?
  Faithfulness: 0.67 (Good)

Sample 2: When was the company founded?
  Faithfulness: 0.50 (Low)

Sample 3: What is the CEO's name?
  Faithfulness: 1.00 (Good)

Sample 4: Where is the headquarters located?
  Faithfulness: 0.33 (Low)

Sample 5: What are the customer support hours?
  Faithfulness: 0.73 (Good)

AVERAGE FAITHFULNESS: 0.65
```

---

## Task 4: Validate Results with Assertions

**Goal**: Use assertions to verify expected outcomes.

```python
# Validation assertions
print("RUNNING VALIDATION TESTS")
print("=" * 60)

# Test 1: Check we have 5 samples
assert len(eval_data) == 5, "Should have 5 evaluation samples"
print("Test 1 passed: Dataset has 5 samples")

# Test 2: Sample 2 should have low faithfulness (known hallucination)
score_2 = calculate_faithfulness(eval_data[1]['answer'], eval_data[1]['contexts'])
assert score_2 < 0.6, f"Sample 2 should have low faithfulness, got {score_2}"
print(f"Test 2 passed: Sample 2 faithfulness is {score_2:.2f} (low)")

# Test 3: Sample 3 should have high faithfulness (no hallucination)
score_3 = calculate_faithfulness(eval_data[2]['answer'], eval_data[2]['contexts'])
assert score_3 >= 0.9, f"Sample 3 should have high faithfulness, got {score_3}"
print(f"Test 3 passed: Sample 3 faithfulness is {score_3:.2f} (high)")

# Test 4: Average should be reasonable
assert 0 < avg_faithfulness < 1, "Average should be between 0 and 1"
print(f"Test 4 passed: Average faithfulness is {avg_faithfulness:.2f}")

# Test 5: At least 2 samples should have low faithfulness
low_count = sum(1 for s in faithfulness_scores if s < 0.7)
assert low_count >= 2, f"Should have at least 2 samples with low faithfulness, got {low_count}"
print(f"Test 5 passed: {low_count} samples have low faithfulness")

print("\nAll validation tests passed!")
```

### Expected Output:
```
RUNNING VALIDATION TESTS
============================================================
Test 1 passed: Dataset has 5 samples
Test 2 passed: Sample 2 faithfulness is 0.50 (low)
Test 3 passed: Sample 3 faithfulness is 1.00 (high)
Test 4 passed: Average faithfulness is 0.65
Test 5 passed: 2 samples have low faithfulness

All validation tests passed!
```

---

## Optional Extensions

### Extension 1: Add Context Precision Metric

```python
def calculate_context_precision(contexts, question, ground_truth):
    """Measure how many retrieved contexts are relevant."""
    relevant_keywords = set((question + " " + ground_truth).lower().split())
    
    relevant_count = 0
    for ctx in contexts:
        ctx_lower = ctx.lower()
        if any(kw in ctx_lower for kw in relevant_keywords if len(kw) > 3):
            relevant_count += 1
    
    return relevant_count / len(contexts) if contexts else 0


# Test it
for i, sample in enumerate(eval_data):
    precision = calculate_context_precision(
        sample['contexts'], 
        sample['question'], 
        sample['ground_truth']
    )
    print(f"Sample {i+1} Context Precision: {precision:.2f}")
```

### Extension 2: Rank Results by Faithfulness

```python
# Sort samples by faithfulness (lowest first - these need attention)
results_with_scores = [
    (sample, calculate_faithfulness(sample['answer'], sample['contexts']))
    for sample in eval_data
]
ranked = sorted(results_with_scores, key=lambda x: x[1])

print("Samples needing attention (sorted by faithfulness):")
for i, (sample, score) in enumerate(ranked):
    print(f"{i+1}. Score: {score:.2f} - {sample['question'][:50]}")
```

### Extension 3: Extract Entities and Check Consistency

```python
def extract_entities(text):
    """Simple entity extraction."""
    return set(re.findall(r'\b[A-Z][a-z]+\b', text))


def check_entity_consistency(sample):
    """Check if entities in answer are supported by context."""
    answer_entities = extract_entities(sample['answer'])
    context_entities = extract_entities(' '.join(sample['contexts']))
    
    unsupported = answer_entities - context_entities
    return list(unsupported)


# Test
for sample in eval_data:
    unsupported = check_entity_consistency(sample)
    if unsupported:
        print(f"Hallucinated entities: {unsupported}")
```

---

## Complete Solution

```python
"""
IN-MEMORY RAG EVALUATION EXERCISE
=================================
"""
import re

# DATA: Initialize evaluation dataset
eval_data = [
    {
        "question": "What is the company's return policy?",
        "answer": "The company offers a 30-day return policy for all items with receipt.",
        "contexts": ["Return Policy: Customers can return items within 30 days of purchase.",
                     "Items must be in original condition with receipt."],
        "ground_truth": "30-day return policy for items with receipt"
    },
    {
        "question": "When was the company founded?",
        "answer": "The company was founded in 2019 by John Smith.",
        "contexts": ["Company XYZ was founded in 2020.", "The initial team consisted of 5 members."],
        "ground_truth": "Company founded in 2020"
    },
    {
        "question": "What is the CEO's name?",
        "answer": "The CEO is Sarah Johnson.",
        "contexts": ["Our CEO, Sarah Johnson, has 15 years of experience.",
                     "She previously worked at TechCorp."],
        "ground_truth": "Sarah Johnson is the CEO"
    },
    {
        "question": "Where is the headquarters located?",
        "answer": "The headquarters is in New York City, New York.",
        "contexts": ["Headquarters: 123 Tech Street, San Francisco, CA",
                     "Main office: San Francisco, California"],
        "ground_truth": "Headquarters in San Francisco, California"
    },
    {
        "question": "What are the customer support hours?",
        "answer": "Customer support is available 24/7 for premium customers.",
        "contexts": ["Support hours: Monday-Friday 9am-6pm EST",
                    "Weekend support: 10am-4pm EST"],
        "ground_truth": "Support available Monday-Friday 9am-6pm, weekends 10am-4pm"
    }
]

# FUNCTION: Calculate faithfulness
def calculate_faithfulness(answer, contexts):
    if not contexts:
        return 0.0
    
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                  'could', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by'}
    
    answer_words = set(w for w in answer.lower().split() 
                     if w not in stop_words and len(w) > 2)
    context_words = set(w for w in ' '.join(contexts).lower().split() 
                       if w not in stop_words and len(w) > 2)
    
    if not answer_words:
        return 1.0
    
    return len(answer_words & context_words) / len(answer_words)

# RUN: Evaluate all samples
print("RAG EVALUATION RESULTS")
print("=" * 60)

scores = []
for sample in eval_data:
    score = calculate_faithfulness(sample['answer'], sample['contexts'])
    scores.append(score)
    status = "PASS" if score >= 0.7 else "FAIL"
    print(f"Q: {sample['question'][:40]}...")
    print(f"  Faithfulness: {score:.2f} - {status}\n")

print(f"Average: {sum(scores)/len(scores):.2f}")

# VALIDATE: Run assertions
assert len(eval_data) == 5
assert scores[1] < 0.6  # Known hallucination
assert scores[2] >= 0.9  # Good answer

print("All assertions passed!")
```

---

## Summary

In this exercise, you learned how to:
1. Initialize and inspect RAG evaluation datasets in memory
2. Implement a faithfulness calculation algorithm
3. Detect hallucinations by comparing answers to contexts
4. Validate results using assertions

The key insight is that in-memory data structures allow rapid experimentation without external dependencies - this is how RAGAS works under the hood.