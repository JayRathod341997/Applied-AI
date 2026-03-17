"""
Embeddings & Chunking - Hands-on Exercise

This exercise covers different chunking strategies and embedding generation.

Estimated Time: 45 minutes
"""

import re
from typing import List, Dict, Any, Callable
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    SpacyTextSplitter,
)

# ============================================================================
# PART 1: Sample Document
# ============================================================================

SAMPLE_DOCUMENT = """
Machine Learning Fundamentals

Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that enables systems 
to learn and improve from experience without being explicitly programmed. 
It focuses on developing algorithms that can access data and use it to learn 
for themselves.

Types of Machine Learning

There are three main types of machine learning:

1. Supervised Learning
Supervised learning uses labeled datasets to train algorithms. The algorithm 
learns from example input-output pairs to predict outputs for new inputs. 
Common applications include classification and regression tasks.

2. Unsupervised Learning
Unsupervised learning finds patterns in unlabeled data. The system tries 
to learn the underlying structure without explicit labels. Common techniques 
include clustering and dimensionality reduction.

3. Reinforcement Learning
Reinforcement learning involves an agent learning to make decisions by 
interacting with an environment. The agent receives rewards or penalties 
based on its actions and learns to maximize rewards over time.

Key Concepts

- Features: Individual measurable properties of the data
- Labels: The target variable we want to predict
- Training: The process of learning from data
- Testing: Evaluating the model on unseen data
- Overfitting: When a model learns training data too well
- Underfitting: When a model is too simple to capture patterns

Machine learning is widely used in applications such as image recognition, 
natural language processing, recommendation systems, and autonomous vehicles.
"""


def main():
    """Demonstrate different chunking strategies."""

    print("=" * 60)
    print("Embeddings & Chunking - Hands-on Exercise")
    print("=" * 60)

    strategies = {
        "Fixed Size": CharacterTextSplitter(
            separator="\n", chunk_size=300, chunk_overlap=30
        ),
        "Sentence Based": SpacyTextSplitter(chunk_size=300, chunk_overlap=30),
        "Recursive": RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30),
    }

    for name, chunker in strategies.items():
        print(f"\n{name} Chunker")
        print("-" * 40)

        texts = chunker.split_text(SAMPLE_DOCUMENT)

        print(f"Total chunks: {len(texts)}")

        # Show first 3 chunks
        for i, chunk in enumerate(texts[:3]):
            print(f"\nChunk {i+1} ({len(chunk)} chars):")
            print(f"  {chunk[:100]}...")

    print("\n" + "=" * 60)
    print("Exercise: Try different chunk sizes and overlap values")
    print("=" * 60)


if __name__ == "__main__":
    main()


# ============================================================================
# EXERCISE TASKS
# ============================================================================

"""
EXERCISE TASKS:
1. Add overlap handling to maintain context between chunks
2. Implement semantic chunking using embeddings
3. Add metadata preservation (page numbers, section headers)
4. Create a function to evaluate chunk quality
5. Implement chunking for code files

BONUS: Use actual embeddings to create semantically coherent chunks
"""
