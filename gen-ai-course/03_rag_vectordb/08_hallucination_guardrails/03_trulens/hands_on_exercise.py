"""
In-Memory Guardrail Evaluation Exercise (TruLens-style)
==========================================================

This exercise demonstrates how TruLens-style guardrails work by implementing
them with pure Python data structures in memory.

Run: python hands_on_exercise.py
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
import time

# =============================================================================
# SAMPLE DATA - Production query log with feedback
# =============================================================================


@dataclass
class QueryResult:
    """Structure for a query result with evaluation feedback"""

    query: str
    answer: str
    contexts: List[str]
    feedback: Dict[str, float]
    timestamp: float = field(default_factory=time.time)
    is_fallback: bool = False
    fallback_reason: Optional[str] = None


# Simulated production query results with feedback scores
production_log = [
    QueryResult(
        query="What is the return policy?",
        answer="The company offers a 30-day return policy for all items.",
        contexts=["Return Policy: 30-day returns for all items with receipt."],
        feedback={
            "groundedness": 0.95,
            "context_relevance": 0.88,
            "answer_relevance": 0.92,
        },
    ),
    QueryResult(
        query="When was the company founded?",
        answer="The company was founded in 2019.",
        contexts=["Founded in 2020 by John Smith."],
        feedback={
            "groundedness": 0.30,
            "context_relevance": 0.45,
            "answer_relevance": 0.60,
        },
    ),
    QueryResult(
        query="What is the CEO's name?",
        answer="The CEO is Sarah Johnson.",
        contexts=["CEO Sarah Johnson has 15 years experience."],
        feedback={
            "groundedness": 0.98,
            "context_relevance": 0.95,
            "answer_relevance": 0.97,
        },
    ),
    QueryResult(
        query="Where is the headquarters?",
        answer="Headquarters is in New York City.",
        contexts=["Headquarters: San Francisco, CA"],
        feedback={
            "groundedness": 0.25,
            "context_relevance": 0.30,
            "answer_relevance": 0.80,
        },
    ),
    QueryResult(
        query="Tell me about the product features",
        answer="The product includes AI-powered analytics, automated reporting, and real-time dashboards.",
        contexts=[
            "Product Features: AI analytics, automated reports, real-time dashboards"
        ],
        feedback={
            "groundedness": 0.91,
            "context_relevance": 0.85,
            "answer_relevance": 0.89,
        },
    ),
]


# =============================================================================
# TASK 1: INSPECT QUERY RESULTS AND FEEDBACK
# =============================================================================

print("=" * 60)
print("TASK 1: INSPECT QUERY RESULTS AND FEEDBACK")
print("=" * 60)

for i, result in enumerate(production_log):
    print(f"\n--- Query {i + 1} ---")
    print(f"Question: {result.query}")
    print(f"Answer: {result.answer}")
    print(f"Contexts: {result.contexts}")
    print(f"Feedback:")
    print(f"  - Groundedness: {result.feedback['groundedness']}")
    print(f"  - Context Relevance: {result.feedback['context_relevance']}")
    print(f"  - Answer Relevance: {result.feedback['answer_relevance']}")


# =============================================================================
# TASK 2: IMPLEMENT THRESHOLD GUARDRAIL
# =============================================================================

print("\n" + "=" * 60)
print("TASK 2: IMPLEMENT THRESHOLD GUARDRAIL")
print("=" * 60)


class ThresholdGuardrail:
    """
    Simulates TruLens-style threshold guardrail.
    Checks if feedback scores meet minimum thresholds.
    """

    def __init__(self, thresholds: Dict[str, float], on_failure: str = "fallback"):
        """
        Args:
            thresholds: Dict of metric names to minimum threshold values
            on_failure: Action to take when thresholds not met
        """
        self.thresholds = thresholds
        self.on_failure = on_failure

    def evaluate(self, result: QueryResult) -> Dict:
        """Evaluate a query result against thresholds."""
        failed_metrics = []

        for metric, threshold in self.thresholds.items():
            if metric in result.feedback:
                if result.feedback[metric] < threshold:
                    failed_metrics.append(
                        {
                            "metric": metric,
                            "actual": result.feedback[metric],
                            "threshold": threshold,
                        }
                    )

        return {
            "passed": len(failed_metrics) == 0,
            "failed_metrics": failed_metrics,
            "can_proceed": len(failed_metrics) == 0 or self.on_failure != "reject",
        }


# Initialize guardrail with default thresholds
guardrail = ThresholdGuardrail(
    thresholds={"groundedness": 0.7, "context_relevance": 0.5, "answer_relevance": 0.6},
    on_failure="fallback",
)

# Evaluate each production query
print("\nGUARDRAIL EVALUATION RESULTS")
print("-" * 40)

for i, result in enumerate(production_log):
    eval_result = guardrail.evaluate(result)
    status = "PASSED" if eval_result["passed"] else "FAILED"

    print(f"\nQuery {i + 1}: {result.query[:35]}...")
    print(f"  Status: {status}")

    if not eval_result["passed"]:
        print(f"  Failed Metrics:")
        for failed in eval_result["failed_metrics"]:
            print(
                f"    - {failed['metric']}: {failed['actual']:.2f} < {failed['threshold']}"
            )


# =============================================================================
# TASK 3: IMPLEMENT FALLBACK CHAIN
# =============================================================================

print("\n" + "=" * 60)
print("TASK 3: IMPLEMENT FALLBACK CHAIN")
print("=" * 60)


class FallbackChain:
    """Simulates a fallback chain for when guardrails fail."""

    def __init__(self, guardrail: ThresholdGuardrail):
        self.guardrail = guardrail
        self.fallback_count = 0
        self.total_count = 0

    def process(self, query: str, generate_func: Callable) -> QueryResult:
        """Process a query through guardrails and fallback if needed."""
        self.total_count += 1

        # Generate response using provided function
        result = generate_func(query)

        # Evaluate with guardrail
        eval_result = self.guardrail.evaluate(result)

        if not eval_result["passed"]:
            # Trigger fallback
            self.fallback_count += 1
            return self._apply_fallback(query)

        return result

    def _apply_fallback(self, query: str) -> QueryResult:
        """Apply fallback response when guardrail fails"""
        return QueryResult(
            query=query,
            answer="I don't have enough reliable information to answer that question. Please contact support.",
            contexts=[],
            feedback={
                "groundedness": 1.0,
                "context_relevance": 1.0,
                "answer_relevance": 1.0,
            },
            is_fallback=True,
            fallback_reason="Guardrail threshold not met",
        )

    def get_stats(self) -> Dict:
        """Get chain statistics"""
        return {
            "total_queries": self.total_count,
            "fallbacks": self.fallback_count,
            "fallback_rate": self.fallback_count / self.total_count
            if self.total_count > 0
            else 0,
        }


# Demonstrate the fallback chain
chain = FallbackChain(guardrail)

print("FALLBACK CHAIN DEMONSTRATION")
print("-" * 40)

for result in production_log:
    processed = chain.process(
        result.query,
        lambda q: result,  # Pass through existing result
    )

    status = "DIRECT" if not processed.is_fallback else "FALLBACK"
    print(f"\nQuery: {result.query[:35]}...")
    print(f"  Response: {processed.answer[:40]}...")
    print(f"  Status: {status}")
    if processed.is_fallback:
        print(f"  Reason: {processed.fallback_reason}")

# Print statistics
stats = chain.get_stats()
print(f"\n{'=' * 60}")
print("CHAIN STATISTICS")
print(f"{'=' * 60}")
print(f"Total Queries: {stats['total_queries']}")
print(f"Fallbacks: {stats['fallbacks']}")
print(f"Fallback Rate: {stats['fallback_rate'] * 100:.1f}%")


# =============================================================================
# TASK 4: VALIDATE RESULTS WITH ASSERTIONS
# =============================================================================

print("\n" + "=" * 60)
print("TASK 4: VALIDATE RESULTS WITH ASSERTIONS")
print("=" * 60)

# Create a fresh instance for testing
test_guardrail = ThresholdGuardrail(
    thresholds={"groundedness": 0.7, "context_relevance": 0.5, "answer_relevance": 0.6}
)

# Test 1: High-quality result should pass
high_quality = QueryResult(
    query="Test query",
    answer="Test answer",
    contexts=["Context 1"],
    feedback={"groundedness": 0.9, "context_relevance": 0.8, "answer_relevance": 0.85},
)
result = test_guardrail.evaluate(high_quality)
assert result["passed"] == True, "High quality should pass"
print("Test 1 passed: High-quality result passes guardrail")

# Test 2: Low groundedness should fail
low_groundedness = QueryResult(
    query="Test query",
    answer="Wrong answer about 2019",
    contexts=["Actually founded in 2020"],
    feedback={"groundedness": 0.3, "context_relevance": 0.8, "answer_relevance": 0.8},
)
result = test_guardrail.evaluate(low_groundedness)
assert result["passed"] == False, "Low groundedness should fail"
print("Test 2 passed: Low groundedness triggers guardrail")

# Test 3: Multiple failures should be captured
multiple_failures = QueryResult(
    query="Test query",
    answer="Wrong answer",
    contexts=[],
    feedback={"groundedness": 0.2, "context_relevance": 0.1, "answer_relevance": 0.5},
)
result = test_guardrail.evaluate(multiple_failures)
assert len(result["failed_metrics"]) >= 1, "Should capture at least one failure"
print(f"Test 3 passed: Captured {len(result['failed_metrics'])} failed metrics")

# Test 4: Fallback chain should track statistics
test_chain = FallbackChain(test_guardrail)
_ = test_chain.process("Query 1", lambda q: production_log[0])
_ = test_chain.process("Query 2", lambda q: production_log[1])
stats = test_chain.get_stats()
assert stats["total_queries"] == 2, "Should track 2 queries"
print("Test 4 passed: Fallback chain tracks statistics")

print("\nAll validation tests passed!")


# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 60)
print("EXERCISE COMPLETE!")
print("=" * 60)
print("""
You have learned how to:
1. Inspect production query logs with feedback scores
2. Implement threshold-based guardrails (like TruLens)
3. Build fallback chains for graceful degradation
4. Track statistics and validate with assertions

This demonstrates the core concepts behind TruLens' 
real-time guardrail system - all with pure Python!
""")
