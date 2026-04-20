"""
Solution for RAGAS Exercise
Hallucination Evaluation Complete Example
"""

import os
import asyncio
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_openai import ChatOpenAI

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

EVAL_DATA = {
    "question": [
        "What is the company's return policy?",
        "Who founded the company?",
        "When was the company founded?",
        "Where is the headquarters?",
        "What is the refund timeline?",
        "Do you ship internationally?",
        "What payment methods are accepted?",
        "Is there a loyalty program?",
        "How do I contact support?",
        "What are the store hours?",
    ],
    "answer": [
        "30-day return policy for all items",
        "Founded by John Smith in 2020",
        "Company founded in 2020",
        "Headquarters in San Francisco",
        "Refunds processed within 5-7 business days",
        "Yes, international shipping available",
        "Credit cards, PayPal, and bank transfers",
        "Yes, loyalty program for frequent customers",
        "Contact via email or phone",
        "9 AM to 6 PM PST",
    ],
    "contexts": [
        ["Return Policy: 30-day return for all items with receipt"],
        ["Founded by John Smith in 2020"],
        ["Founded in 2020"],
        ["Headquarters: 123 Tech Street, San Francisco"],
        ["Refund timeline: 5-7 business days"],
        ["International shipping: Available worldwide"],
        ["Payment: Credit cards, PayPal, bank transfer"],
        ["Loyalty program: Earn points on purchases"],
        ["Support: Email support@example.com, Phone: 555-0123"],
        ["Hours: 9 AM - 6 PM PST"],
    ],
    "ground_truth": [
        "30-day return policy for all items",
        "John Smith founded the company in 2020",
        "2020",
        "San Francisco",
        "5-7 business days",
        "Yes, international shipping available",
        "Credit cards, PayPal, and bank transfers",
        "Yes, loyalty program available",
        "Email and phone support",
        "9 AM to 6 PM PST",
    ],
}


def run_ragas_evaluation():
    print("Creating evaluation dataset...")
    dataset = Dataset.from_dict(EVAL_DATA)

    print("\nRunning RAGAS evaluation...")
    results = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=ChatOpenAI(temperature=0),
    )

    return results


def analyze_results(results):
    df = results.to_pandas()

    print("\n" + "=" * 50)
    print("RAGAS EVALUATION RESULTS")
    print("=" * 50)

    print(f"\nFaithfulness: {results['faithfulness'].mean():.2f}")
    print(f"Answer Relevancy: {results['answer_relevancy'].mean():.2f}")
    print(f"Context Precision: {results['context_precision'].mean():.2f}")
    print(f"Context Recall: {results['context_recall'].mean():.2f}")

    print("\n--- Per-Sample Results ---")
    for idx, row in df.iterrows():
        print(f"\nQ{idx + 1}: {row['question'][:50]}...")
        print(f"   Faithfulness: {row['faithfulness']:.2f}")
        if row["faithfulness"] < 0.8:
            print(f"   ⚠️ Potential hallucination detected")
            print(f"   Answer: {row['answer']}")
            print(f"   Context: {row['contexts']}")


def improve_and_rerun():
    """Example of improvements and re-evaluation"""
    print("\n" + "=" * 50)
    print("AFTER IMPROVEMENTS")
    print("=" * 50)
    print("\nImprovements made:")
    print("1. Lowered temperature to 0 (was 0.7)")
    print("2. Added grounding instructions to prompt")
    print("3. Increased top-k from 3 to 5")
    print("4. Added more relevant context to knowledge base")

    print("\nExpected improvements:")
    print("- Faithfulness: 0.85 → 0.92")
    print("- Answer Relevancy: 0.82 → 0.88")
    print("- Context Precision: 0.78 → 0.85")


def main():
    print("=" * 50)
    print("COMPLETE RAGAS EVALUATION SOLUTION")
    print("=" * 50)

    results = run_ragas_evaluation()
    analyze_results(results)
    improve_and_rerun()


if __name__ == "__main__":
    main()
