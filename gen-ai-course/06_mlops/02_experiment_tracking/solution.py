"""Solution: an in-memory experiment tracker for GenAI runs.

Implements `ExperimentTracker`, a tiny MLflow/W&B-style tracker that stores
runs in memory. Each run holds params (prompt, temperature, model, ...),
metrics (faithfulness, answer_relevance, cost, latency, ...), and artifacts
(prompt text, eval reports). The core logic is `best_run`, which selects the
winning run for a metric in either "max" or "min" direction and ignores runs
that never logged that metric.

Runs fully OFFLINE (no API keys, no network). The bottom of the file runs a
demo and asserts the expected selection behaviour.

Run with:  python solution.py
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# The run record.
# ---------------------------------------------------------------------------
@dataclass
class Run:
    """A single experiment run.

    Attributes:
        run_id: unique identifier for the run.
        name: human-friendly name (e.g. "rag-v3-temp0.2").
        seq: monotonically increasing creation order (a stable tiebreaker).
        params: configuration of the run (model, temperature, prompt, ...).
        metrics: measured outcomes (faithfulness, cost, latency, ...).
        artifacts: named blobs (prompt text, eval report, ...).
        status: "RUNNING" while open, "FINISHED"/"FAILED"/"KILLED" once ended.
    """

    run_id: str
    name: str
    seq: int
    params: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    status: str = "RUNNING"

    def as_dict(self) -> dict[str, Any]:
        """Return a plain-dict snapshot of the run (defensive copies)."""
        return {
            "run_id": self.run_id,
            "name": self.name,
            "seq": self.seq,
            "params": dict(self.params),
            "metrics": dict(self.metrics),
            "artifacts": dict(self.artifacts),
            "status": self.status,
        }


# ---------------------------------------------------------------------------
# The tracker.
# ---------------------------------------------------------------------------
class ExperimentTracker:
    """An in-memory experiment tracker for GenAI runs.

    Mirrors the mental model of MLflow / Weights & Biases: you `start_run`,
    `log_metric` / `log_artifact` during the run, `end_run` to close it, then
    `best_run` to pick the winner for a given metric.
    """

    def __init__(self) -> None:
        self._runs: dict[str, Run] = {}
        self._seq = itertools.count(1)  # stable creation order / tiebreaker

    # -- lifecycle ----------------------------------------------------------
    def start_run(self, name: str, params: dict[str, Any] | None = None) -> str:
        """Create a new run and return its unique run_id.

        Args:
            name: human-friendly run name.
            params: configuration logged at start (copied defensively).

        Returns:
            The new run's id.
        """
        seq = next(self._seq)
        run_id = f"run-{seq:04d}"
        self._runs[run_id] = Run(
            run_id=run_id,
            name=name,
            seq=seq,
            params=dict(params or {}),
            status="RUNNING",
        )
        return run_id

    def end_run(self, run_id: str, status: str = "FINISHED") -> None:
        """Mark a run finished (or FAILED / KILLED)."""
        self._require(run_id).status = status

    # -- logging ------------------------------------------------------------
    def log_metric(self, run_id: str, key: str, value: float) -> None:
        """Record (or overwrite) a numeric metric on a run."""
        self._require(run_id).metrics[key] = float(value)

    def log_artifact(self, run_id: str, name: str, content: Any) -> None:
        """Record a named artifact (string/bytes/any) on a run."""
        self._require(run_id).artifacts[name] = content

    # -- reads --------------------------------------------------------------
    def get_run(self, run_id: str) -> dict[str, Any]:
        """Return a snapshot dict of one run's params/metrics/artifacts/status."""
        return self._require(run_id).as_dict()

    def list_runs(self) -> list[dict[str, Any]]:
        """Return snapshots of all runs in creation order."""
        return [r.as_dict() for r in sorted(self._runs.values(), key=lambda r: r.seq)]

    # -- selection (the core logic) ----------------------------------------
    def best_run(self, metric: str, mode: str = "max") -> str:
        """Return the run_id with the best value of `metric`.

        Args:
            metric: the metric key to compare on (e.g. "faithfulness").
            mode: "max" picks the highest value, "min" the lowest.

        Returns:
            The winning run's id.

        Raises:
            ValueError: if `mode` is not "max"/"min", or if no run logged
                the requested metric.
        """
        if mode not in ("max", "min"):
            raise ValueError(f"mode must be 'max' or 'min', got {mode!r}")

        # Only consider runs that actually logged this metric.
        candidates = [r for r in self._runs.values() if metric in r.metrics]
        if not candidates:
            raise ValueError(f"no run logged metric {metric!r}")

        # Sort by metric value (direction depends on mode), then by seq so ties
        # resolve to the earliest run for deterministic results.
        reverse = mode == "max"
        candidates.sort(key=lambda r: (r.metrics[metric], -r.seq), reverse=reverse)
        return candidates[0].run_id

    # -- registry hand-off --------------------------------------------------
    def promote_best(
        self, metric: str, mode: str = "max", stage: str = "Production"
    ) -> dict[str, Any]:
        """Select the best run and simulate a model-registry hand-off.

        Returns a dict describing the registered model version: the source
        run, the deciding metric, and the target stage (Staging/Production).
        """
        run_id = self.best_run(metric, mode)
        run = self._require(run_id)
        return {
            "source_run_id": run_id,
            "run_name": run.name,
            "model": run.params.get("model"),
            "selected_metric": metric,
            "metric_value": run.metrics[metric],
            "stage": stage,
            "version": run.seq,  # pretend monotonic registry version
        }

    # -- internal -----------------------------------------------------------
    def _require(self, run_id: str) -> Run:
        try:
            return self._runs[run_id]
        except KeyError:
            raise KeyError(f"unknown run_id {run_id!r}") from None


# ---------------------------------------------------------------------------
# Demonstration + assertions.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tracker = ExperimentTracker()

    print("=== Logging 4 GenAI runs ===")

    # Run A: balanced baseline.
    a = tracker.start_run("rag-baseline", {"model": "gpt-4o-mini", "temperature": 0.2, "top_p": 1.0})
    tracker.log_metric(a, "faithfulness", 0.81)
    tracker.log_metric(a, "answer_relevance", 0.74)
    tracker.log_metric(a, "cost_usd", 0.012)
    tracker.log_metric(a, "latency_ms", 920)
    tracker.log_artifact(a, "prompt.txt", "Answer using ONLY the context.\n{context}\nQ: {q}")
    tracker.end_run(a)

    # Run B: most faithful but pricier.
    b = tracker.start_run("rag-reranker", {"model": "gpt-4o", "temperature": 0.0, "top_p": 1.0})
    tracker.log_metric(b, "faithfulness", 0.93)
    tracker.log_metric(b, "answer_relevance", 0.88)
    tracker.log_metric(b, "cost_usd", 0.041)
    tracker.log_metric(b, "latency_ms", 1500)
    tracker.log_artifact(b, "eval_report.json", '{"n": 50, "passed": 47}')
    tracker.end_run(b)

    # Run C: cheapest but lower quality.
    c = tracker.start_run("rag-tiny", {"model": "llama-3-8b", "temperature": 0.3, "top_p": 0.9})
    tracker.log_metric(c, "faithfulness", 0.70)
    tracker.log_metric(c, "answer_relevance", 0.65)
    tracker.log_metric(c, "cost_usd", 0.003)
    tracker.log_metric(c, "latency_ms", 410)
    tracker.end_run(c)

    # Run D: crashed early — never logged faithfulness or cost.
    d = tracker.start_run("rag-broken", {"model": "gpt-4o", "temperature": 0.9, "top_p": 0.8})
    tracker.log_metric(d, "latency_ms", 300)
    tracker.end_run(d, status="FAILED")

    for run in tracker.list_runs():
        print(f"  {run['run_id']} {run['name']:<14} status={run['status']:<8} metrics={run['metrics']}")

    # -- selection assertions ----------------------------------------------
    print("\n=== Selecting best runs ===")

    best_faith = tracker.best_run("faithfulness", mode="max")
    print("Best faithfulness (max):", best_faith)
    assert best_faith == b, f"expected {b} (0.93), got {best_faith}"

    cheapest = tracker.best_run("cost_usd", mode="min")
    print("Cheapest cost (min):", cheapest)
    assert cheapest == c, f"expected {c} (0.003), got {cheapest}"

    fastest = tracker.best_run("latency_ms", mode="min")
    print("Fastest latency (min):", fastest)
    assert fastest == d, f"expected {d} (300ms), got {fastest}"

    # Run D never logged faithfulness, so it is ignored entirely.
    assert "faithfulness" not in tracker.get_run(d)["metrics"]
    assert tracker.best_run("faithfulness", "max") != d

    # No run logged this metric -> ValueError.
    raised = False
    try:
        tracker.best_run("toxicity", "min")
    except ValueError as e:
        raised = True
        print("Missing-metric selection raised ValueError as expected:", e)
    assert raised, "expected ValueError when no run logged the metric"

    # Invalid mode -> ValueError.
    raised = False
    try:
        tracker.best_run("faithfulness", "highest")
    except ValueError:
        raised = True
    assert raised, "expected ValueError on invalid mode"

    # -- registry hand-off --------------------------------------------------
    print("\n=== Registry hand-off ===")
    promotion = tracker.promote_best("faithfulness", "max", stage="Production")
    print("Promoted:", promotion)
    assert promotion["source_run_id"] == b
    assert promotion["stage"] == "Production"
    assert promotion["selected_metric"] == "faithfulness"
    assert abs(promotion["metric_value"] - 0.93) < 1e-9

    print("\nAll assertions passed.")
