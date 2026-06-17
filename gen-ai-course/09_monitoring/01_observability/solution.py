"""Solution: an offline LLM metrics collector.

Implements `MetricsCollector`, which ingests one record per LLM request and
computes the headline observability numbers: latency percentiles (P50/P95/P99),
total and average cost, and the error rate.

Runs fully OFFLINE (no API keys, no network). The bottom of the file runs a
demo over a fixed sample stream and asserts the expected values.

Run with:  python solution.py
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Provided: a request record, a pricing table, and a fixed sample stream.
# Do NOT modify these in the exercise.
# ---------------------------------------------------------------------------
@dataclass
class RequestRecord:
    model: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    success: bool = True
    cost_usd: float = field(default=0.0)


# (input_price_per_1k, output_price_per_1k) in USD.
PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o": (0.0025, 0.01),
    "claude-3-sonnet": (0.003, 0.015),
}
DEFAULT_PRICE = (0.01, 0.03)  # used for unknown models

# A fixed offline stream: (model, latency_ms, in_tok, out_tok, success)
SAMPLE_REQUESTS = [
    ("gpt-4o-mini", 120.0, 800, 200, True),
    ("gpt-4o-mini", 250.0, 600, 150, True),
    ("gpt-4o", 320.0, 1200, 400, True),
    ("gpt-4o", 410.0, 1500, 500, True),
    ("gpt-4o-mini", 180.0, 700, 100, True),
    ("gpt-4o", 2500.0, 2000, 800, False),  # slow tail + failure
    ("claude-3-sonnet", 600.0, 1000, 300, True),
    ("gpt-4o-mini", 90.0, 400, 50, False),  # fast failure
]


# ---------------------------------------------------------------------------
# The metrics collector.
# ---------------------------------------------------------------------------
class MetricsCollector:
    """Aggregates per-request metrics into dashboard-ready numbers."""

    def __init__(self) -> None:
        self.records: list[RequestRecord] = []

    @staticmethod
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Cost in USD from token counts and the pricing table."""
        p_in, p_out = PRICING.get(model, DEFAULT_PRICE)
        return (input_tokens * p_in + output_tokens * p_out) / 1000

    def record(
        self,
        model: str,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        success: bool = True,
    ) -> RequestRecord:
        """Store a request and compute its cost."""
        rec = RequestRecord(
            model=model,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            success=success,
        )
        rec.cost_usd = self.estimate_cost(model, input_tokens, output_tokens)
        self.records.append(rec)
        return rec

    def percentile(self, p: float) -> float:
        """P-th percentile of latency (nearest-rank on a sorted copy).

        Args:
            p: percentile in [0, 100].

        Raises:
            ValueError: if no records have been collected.
        """
        if not self.records:
            raise ValueError("no records to compute a percentile from")
        ordered = sorted(r.latency_ms for r in self.records)
        n = len(ordered)
        # Nearest-rank: smallest 1-based rank covering p% of the data.
        rank = int(round((p / 100) * n + 0.5))
        idx = max(0, min(n - 1, rank - 1))
        return ordered[idx]

    def error_rate(self) -> float:
        """Failed requests / total requests (0.0 when empty)."""
        if not self.records:
            return 0.0
        failures = sum(1 for r in self.records if not r.success)
        return failures / len(self.records)

    def total_cost(self) -> float:
        return sum(r.cost_usd for r in self.records)

    def avg_cost(self) -> float:
        if not self.records:
            return 0.0
        return self.total_cost() / len(self.records)

    def summary(self) -> dict:
        """Dashboard-ready summary of all collected requests."""
        if not self.records:
            return {
                "total_requests": 0,
                "error_rate": 0.0,
                "latency_p50": 0.0,
                "latency_p95": 0.0,
                "latency_p99": 0.0,
                "total_cost_usd": 0.0,
                "avg_cost_usd": 0.0,
            }
        return {
            "total_requests": len(self.records),
            "error_rate": self.error_rate(),
            "latency_p50": self.percentile(50),
            "latency_p95": self.percentile(95),
            "latency_p99": self.percentile(99),
            "total_cost_usd": self.total_cost(),
            "avg_cost_usd": self.avg_cost(),
        }


# ---------------------------------------------------------------------------
# Demonstration + assertions.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mc = MetricsCollector()
    for model, lat, in_tok, out_tok, ok in SAMPLE_REQUESTS:
        mc.record(model, lat, in_tok, out_tok, ok)

    s = mc.summary()
    print("=== Metrics summary ===")
    print(f"total_requests : {s['total_requests']}")
    print(f"error_rate     : {s['error_rate']}")
    print(f"latency_p50    : {s['latency_p50']} ms")
    print(f"latency_p95    : {s['latency_p95']} ms")
    print(f"latency_p99    : {s['latency_p99']} ms")
    print(f"total_cost_usd : {s['total_cost_usd']:.6f}")
    print(f"avg_cost_usd   : {s['avg_cost_usd']:.6f}")

    # --- assertions ---
    assert s["total_requests"] == 8
    # 2 of 8 requests failed.
    assert abs(s["error_rate"] - 0.25) < 1e-9

    # Latencies sorted: [90, 120, 180, 250, 320, 410, 600, 2500]  (n = 8)
    # P50 nearest-rank -> idx 3 -> 250 ms; P95/P99 -> idx 7 -> 2500 ms.
    assert s["latency_p50"] == 250.0
    assert s["latency_p95"] == 2500.0
    assert s["latency_p99"] == 2500.0

    # Cost sanity: every cost is positive and total == sum of parts.
    assert s["total_cost_usd"] > 0
    assert abs(s["total_cost_usd"] - sum(r.cost_usd for r in mc.records)) < 1e-12
    assert abs(s["avg_cost_usd"] - s["total_cost_usd"] / 8) < 1e-12

    # Spot-check one cost: gpt-4o, 1200 in / 400 out
    #   = (1200*0.0025 + 400*0.01)/1000 = (3.0 + 4.0)/1000 = 0.007
    assert abs(MetricsCollector.estimate_cost("gpt-4o", 1200, 400) - 0.007) < 1e-12
    # Unknown model uses the default price.
    assert abs(MetricsCollector.estimate_cost("mystery", 1000, 1000) - 0.04) < 1e-12

    # Empty collector is safe.
    empty = MetricsCollector()
    assert empty.error_rate() == 0.0
    assert empty.avg_cost() == 0.0
    assert empty.summary()["total_requests"] == 0
    raised = False
    try:
        empty.percentile(50)
    except ValueError:
        raised = True
    assert raised, "percentile on empty collector should raise ValueError"

    print("\nAll assertions passed.")
