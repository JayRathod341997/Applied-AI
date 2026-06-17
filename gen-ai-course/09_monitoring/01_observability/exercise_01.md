# Exercise: LLM Metrics Collector

## Background

Every managed observability platform (LangSmith, Langfuse, Datadog) ultimately runs the same simple aggregations over a stream of per-request records: latency percentiles, total and average cost, and an error rate. In this exercise you build that core yourself so the math is no longer magic.

You will implement a `MetricsCollector` that ingests one record per LLM request — latency, input/output tokens, model, and success/failure — and computes the headline numbers an SRE would put on a dashboard.

Everything runs offline. The cost table and the sample request stream are provided; you only implement the collector.

## Your Task

Open `exercise.py` and complete the `MetricsCollector` class:

1. **`record(...)`** — append a `RequestRecord` to the internal list. Compute its `cost_usd` from the model's pricing and the input/output token counts (use the provided `PRICING` table; fall back to the default price for unknown models).
2. **`percentile(p)`** — return the P-th percentile of latency over all recorded requests using the nearest-rank method on a sorted copy. Raise `ValueError` if there are no records.
3. **`error_rate()`** — return failed requests / total requests (0.0 when there are no records).
4. **`summary()`** — return a dict with: `total_requests`, `error_rate`, `latency_p50`, `latency_p95`, `latency_p99`, `total_cost_usd`, and `avg_cost_usd`.

## Requirements

- Do not modify the provided `RequestRecord`, `PRICING`, or `SAMPLE_REQUESTS`.
- Pure standard library only — no numpy/pandas, no network, no API keys.
- `percentile` must work for a single record and for large lists.
- `avg_cost_usd` and `error_rate` must not divide by zero on an empty collector (return `0.0`).

## How to Run

```bash
python exercise.py
```

The starter raises `NotImplementedError` until you fill in the `# TODO` sections, so it imports cleanly but the demo fails until complete.

## Expected Output

When finished, running `python solution.py` prints a summary and self-checks with asserts, ending with:

```
=== Metrics summary ===
total_requests : 8
error_rate     : 0.25
latency_p50    : 250.0 ms
latency_p95    : 2500.0 ms
latency_p99    : 2500.0 ms
total_cost_usd : 0.0xxxxx
avg_cost_usd   : 0.0xxxxx

All assertions passed.
```
