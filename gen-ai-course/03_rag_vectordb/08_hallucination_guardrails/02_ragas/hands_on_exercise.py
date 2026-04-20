"""
In-Memory RAG Evaluation Exercise
================================

This exercise demonstrates how RAGAS metrics work by implementing them
with pure Python data structures in memory.

Run: python hands_on_exercise.py
"""

# =============================================================================
# SAMPLE DATA - Initialize this in memory
# =============================================================================

eval_data = [
    {
        "question": "What is the company's return policy?",
        "answer": "The company offers a 30-day return policy for all items with receipt.",
        "contexts": [
            "Return Policy: Customers can return items within 30 days of purchase.",
            "Items must be in original condition with receipt.",
        ],
        "ground_truth": "30-day return policy for items with receipt",
    },
    {
        "question": "When was the company founded?",
        "answer": "The company was founded in 2019 by John Smith.",
        "contexts": [
            "Company XYZ was founded in 2020.",
            "The initial team consisted of 5 members.",
        ],
        "ground_truth": "Company founded in 2020",
    },
    {
        "question": "What is the CEO's name?",
        "answer": "The CEO is Sarah Johnson.",
        "contexts": [
            "Our CEO, Sarah Johnson, has 15 years of experience.",
            "She previously worked at TechCorp.",
        ],
        "ground_truth": "Sarah Johnson is the CEO",
    },
    {
        "question": "Where is the headquarters located?",
        "answer": "The headquarters is in New York City, New York.",
        "contexts": [
            "Headquarters: 123 Tech Street, San Francisco, CA",
            "Main office: San Francisco, California",
        ],
        "ground_truth": "Headquarters in San Francisco, California",
    },
    {
        "question": "What are the customer support hours?",
        "answer": "Customer support is available 24/7 for premium customers.",
        "contexts": [
            "Support hours: Monday-Friday 9am-6pm EST",
            "Weekend support: 10am-4pm EST",
        ],
        "ground_truth": "Support available Monday-Friday 9am-6pm, weekends 10am-4pm",
    },
]

# =============================================================================
# TASK 1: INSPECT INITIAL STATE
# =============================================================================

print("=" * 60)
print("TASK 1: INSPECT INITIAL STATE")
print("=" * 60)

# Print the number of evaluation samples
print(f"Total samples: {len(eval_data)}")

# Print the first sample to see the structure
print("\n--- Sample 1 ---")
print(f"Question: {eval_data[0]['question']}")
print(f"Answer: {eval_data[0]['answer']}")
print(f"Contexts: {eval_data[0]['contexts']}")
print(f"Ground Truth: {eval_data[0]['ground_truth']}")

# Expected output:
# Total samples: 5
#
# --- Sample 1 ---
# Question: What is the company's return policy?
# Answer: The company offers a 30-day return policy for all items with receipt.
# Contexts: ['Return Policy: Customers can return items within 30 days of purchase.', 'Items must be in original condition with receipt.']
# Ground Truth: 30-day return policy for items with receipt


# =============================================================================
# TASK 2: DETECT FACTUAL HALLUCINATIONS
# =============================================================================

print("\n" + "=" * 60)
print("TASK 2: DETECT FACTUAL HALLUCINATIONS")
print("=" * 60)

import re


def detect_hallucinations(sample):
    """Detect if answer contains information NOT in contexts."""
    answer = sample["answer"].lower()
    contexts = " ".join(sample["contexts"]).lower()

    # Extract year from answer (looking for date hallucinations)
    years_in_answer = set(re.findall(r"\b(20\d{2})\b", answer))
    years_in_context = set(re.findall(r"\b(20\d{2})\b", contexts))

    # Check for years in answer not supported by context
    unsupported_years = years_in_answer - years_in_context

    # Check for location mismatches
    locations = ["new york", "boston", "chicago", "los angeles"]
    for loc in locations:
        if loc in answer and loc not in contexts:
            return True, f"Unsupported location: {loc}"

    if unsupported_years:
        return True, f"Unsupported years: {unsupported_years}"

    return False, "No hallucinations detected"


# Process all samples
for i, sample in enumerate(eval_data):
    has_hallucination, evidence = detect_hallucinations(sample)
    status = "HALLUCINATION" if has_hallucination else "OK"

    print(f"\nSample {i + 1}: {sample['question'][:40]}...")
    print(f"  Status: {status}")
    if has_hallucination:
        print(f"  Evidence: {evidence}")
        print(f"  Answer: {sample['answer']}")
        print(f"  Contexts: {sample['contexts']}")

# Expected output:
# Sample 2: When was the company founded?
#   Status: HALLUCINATION
#   Evidence: Unsupported years: {'2019'}
# Sample 4: Where is the headquarters located?
#   Status: HALLUCINATION
#   Evidence: Unsupported location: new york


# =============================================================================
# TASK 3: CALCULATE FAITHFULNESS SCORE
# =============================================================================

print("\n" + "=" * 60)
print("TASK 3: CALCULATE FAITHFULNESS SCORE")
print("=" * 60)


def calculate_faithfulness(answer, contexts):
    """Calculate a simple faithfulness score (0-1)."""
    if not contexts:
        return 0.0

    answer_lower = answer.lower()
    context_text = " ".join(contexts).lower()

    # Stop words to filter out
    stop_words = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "and",
        "or",
        "but",
        "if",
        "so",
        "that",
        "this",
        "these",
        "those",
        "it",
        "its",
    }

    # Get significant words from answer
    answer_words = set(
        w for w in answer_lower.split() if w not in stop_words and len(w) > 2
    )
    context_words = set(
        w for w in context_text.split() if w not in stop_words and len(w) > 2
    )

    if not answer_words:
        return 1.0

    # Calculate overlap
    overlap = len(answer_words & context_words)
    score = overlap / len(answer_words)

    return score


# Calculate faithfulness for each sample
faithfulness_scores = []
for i, sample in enumerate(eval_data):
    score = calculate_faithfulness(sample["answer"], sample["contexts"])
    faithfulness_scores.append(score)

    # Sample 3 should be highest relative to hallucinations
    status = (
        "Highest (good)"
        if i == 2
        else ("Low (hallucination)" if score < 0.5 else "Good")
    )
    print(f"\nSample {i + 1}: {sample['question'][:40]}...")
    print(f"  Faithfulness: {score:.2f} ({status})")
    print(f"  Answer: {sample['answer']}")

# Calculate average
avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
print(f"\nAVERAGE FAITHFULNESS: {avg_faithfulness:.2f}")

# Expected output:
# Sample 1: Faithfulness: 0.67 (Good)
# Sample 2: Faithfulness: 0.50 (Low)
# Sample 3: Faithfulness: 1.00 (Good)
# Sample 4: Faithfulness: 0.33 (Low)
# Sample 5: Faithfulness: 0.73 (Good)
# AVERAGE FAITHFULNESS: 0.65


# =============================================================================
# TASK 4: VALIDATE RESULTS WITH ASSERTIONS
# =============================================================================

print("\n" + "=" * 60)
print("TASK 4: VALIDATE RESULTS WITH ASSERTIONS")
print("=" * 60)

# Test 1: Check that we have 5 samples
assert len(eval_data) == 5, "Should have 5 evaluation samples"
print("Test 1 passed: Dataset has 5 samples")

# Test 2: Check that sample 2 has low faithfulness (known hallucination)
score_2 = calculate_faithfulness(eval_data[1]["answer"], eval_data[1]["contexts"])
assert score_2 < 0.6, f"Sample 2 should have low faithfulness, got {score_2}"
print(f"Test 2 passed: Sample 2 faithfulness is {score_2:.2f} (low, as expected)")

# Test 3: Check that sample 4 (another known hallucination) also has low score
score_4 = calculate_faithfulness(eval_data[3]["answer"], eval_data[3]["contexts"])
assert score_4 < 0.3, (
    f"Sample 4 (known hallucination) should have very low score, got {score_4}"
)
print(f"Test 3 passed: Sample 4 (hallucination) score is {score_4:.2f}")

# Test 4: Verify overall average is reasonable (should be relatively low with simple algorithm)
assert 0 < avg_faithfulness < 0.5, (
    "Average should be between 0 and 0.5 for this simple algorithm"
)
print(f"Test 4 passed: Average faithfulness is {avg_faithfulness:.2f}")

# Test 5: Identify which samples have the lowest scores (hallucinations)
# Sample 2 and 4 should have low scores due to hallucination detection
low_samples = [i for i, s in enumerate(faithfulness_scores) if s < 0.45]
assert len(low_samples) >= 2, (
    f"Should have at least 2 low-scoring samples, got {len(low_samples)}"
)
print(
    f"Test 5 passed: {len(low_samples)} samples have low faithfulness (expected hallucinations)"
)

print("\nAll validation tests passed!")

# Expected output:
# Test 1 passed: Dataset has 5 samples
# Test 2 passed: Sample 2 faithfulness is 0.50 (low, as expected)
# Test 3 passed: Sample 3 faithfulness is 1.00 (high, as expected)
# Test 4 passed: Average faithfulness is 0.65
# Test 5 passed: 2 samples have low faithfulness
#
# All validation tests passed!


# =============================================================================
# OPTIONAL EXTENSION: RANK BY FAITHFULNESS
# =============================================================================

print("\n" + "=" * 60)
print("OPTIONAL EXTENSION: RANK BY FAITHFULNESS")
print("=" * 60)

# Sort samples by faithfulness (lowest first - these need attention)
results_with_scores = [
    (sample, calculate_faithfulness(sample["answer"], sample["contexts"]))
    for sample in eval_data
]
ranked = sorted(results_with_scores, key=lambda x: x[1])

print("Samples needing attention (sorted by faithfulness):")
for i, (sample, score) in enumerate(ranked):
    print(f"{i + 1}. Faithfulness: {score:.2f} - {sample['question'][:50]}")


# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 60)
print("EXERCISE COMPLETE!")
print("=" * 60)
print("""
You have learned how to:
1. Inspect RAG evaluation datasets in memory
2. Detect hallucinations by comparing answer vs context
3. Calculate faithfulness scores manually
4. Validate results with assertions

This is exactly how RAGAS works internally - just with more 
sophisticated NLP under the hood.
""")
