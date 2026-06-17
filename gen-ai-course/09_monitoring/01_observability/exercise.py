"""Exercise: an offline LLM metrics collector.

You will build a `MetricsCollector` that ingests one record per LLM request
and computes the headline observability numbers: latency percentiles
(P50/P95/P99), total and average cost, and the error rate.

Everything runs OFFLINE. The RequestRecord, PRICING table, and SAMPLE_REQUESTS
below are fully provided. Complete only the sections marked `# TODO`.

Run with:  python exercise.py
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Provided: a request record, a pricing table, and a fixed sample stream.
# Do NOT modify these.
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
# TODO: implement the metrics collector.
# ---------------------------------------------------------------------------
class MetricsCollector:
    """Aggregates per-request metrics into dashboard-ready numbers."""

    def __init__(self) -> None:
        self.records: list[RequestRecord] = []

    @staticmethod
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Cost in USD from token counts and the pricing table.

        Look up (p_in, p_out) in PRICING, falling back to DEFAULT_PRICE for
        unknown models, then return (in*p_in + out*p_out) / 1000.
        """
        # TODO: implement cost estimation.
        raise NotImplementedError("TODO: estimate cost from tokens and PRICING")

    def record(
        self,
        model: str,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        success: bool = True,
    ) -> RequestRecord:
        """Store a RequestRecord and set its cost_usd via estimate_cost()."""
        # TODO: build a RequestRecord, compute its cost, append it, return it.
        raise NotImplementedError("TODO: record a request")

    def percentile(self, p: float) -> float:
        """P-th percentile of latency using nearest-rank on a sorted copy.

        Raise ValueError if there are no records.
        """
        # TODO: sort latencies, compute nearest-rank index, return that value.
        raise NotImplementedError("TODO: compute the latency percentile")

    def error_rate(self) -> float:
        """Failed requests / total requests (0.0 when empty)."""
        # TODO: return the fraction of records whose success is False.
        raise NotImplementedError("TODO: compute the error rate")

    def total_cost(self) -> float:
        return sum(r.cost_usd for r in self.records)

    def avg_cost(self) -> float:
        if not self.records:
            return 0.0
        return self.total_cost() / len(self.records)

    def summary(self) -> dict:
        """Return total_requests, error_rate, latency_p50/p95/p99,
        total_cost_usd, and avg_cost_usd."""
        # TODO: assemble and return the summary dict (handle the empty case).
        raise NotImplementedError("TODO: build the summary dict")


# ---------------------------------------------------------------------------
# Demonstration of intended usage.
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
