"""Exercise: an in-memory experiment tracker for GenAI runs.

You will build an `ExperimentTracker` that behaves like a tiny MLflow / W&B.
Each run stores params (model, temperature, prompt, ...), metrics
(faithfulness, answer_relevance, cost_usd, latency_ms, ...), and artifacts
(prompt text, eval reports). The core method is `best_run`, which selects the
winning run for a metric in either "max" or "min" direction and ignores runs
that never logged that metric.

Everything runs OFFLINE. The `Run` dataclass below is fully provided.
Complete only the sections marked `# TODO`.

Run with:  python exercise.py
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Provided: the run record. Do NOT modify this.
# ---------------------------------------------------------------------------
@dataclass
class Run:
    """A single experiment run."""

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
# TODO: implement the tracker.
# ---------------------------------------------------------------------------
class ExperimentTracker:
    """An in-memory experiment tracker for GenAI runs."""

    def __init__(self) -> None:
        # TODO: create a dict of runs and a creation-order counter
        # (itertools.count(1) is handy as a stable seq / tiebreaker).
        raise NotImplementedError("TODO: init run store and sequence counter")

    # -- lifecycle ----------------------------------------------------------
    def start_run(self, name: str, params: dict[str, Any] | None = None) -> str:
        """Create a new run with a unique id; store params + seq; status RUNNING.

        Return the new run_id.
        """
        # TODO: build a run_id (e.g. f"run-{seq:04d}"), store a Run, return id.
        raise NotImplementedError("TODO: create a run and return its id")

    def end_run(self, run_id: str, status: str = "FINISHED") -> None:
        """Mark a run finished (or FAILED / KILLED)."""
        # TODO: set the run's status.
        raise NotImplementedError("TODO: set run status")

    # -- logging ------------------------------------------------------------
    def log_metric(self, run_id: str, key: str, value: float) -> None:
        """Record (or overwrite) a numeric metric on a run."""
        # TODO: store float(value) under key in the run's metrics.
        raise NotImplementedError("TODO: log a metric")

    def log_artifact(self, run_id: str, name: str, content: Any) -> None:
        """Record a named artifact (string/bytes/any) on a run."""
        # TODO: store content under name in the run's artifacts.
        raise NotImplementedError("TODO: log an artifact")

    # -- reads --------------------------------------------------------------
    def get_run(self, run_id: str) -> dict[str, Any]:
        """Return a snapshot dict of one run."""
        # TODO: return the run's as_dict() snapshot.
        raise NotImplementedError("TODO: return a run snapshot")

    def list_runs(self) -> list[dict[str, Any]]:
        """Return snapshots of all runs in creation order."""
        # TODO: return a list of as_dict() snapshots sorted by seq.
        raise NotImplementedError("TODO: return all runs")

    # -- selection (the core logic) ----------------------------------------
    def best_run(self, metric: str, mode: str = "max") -> str:
        """Return the run_id with the best value of `metric`.

        - mode "max" picks the highest value; "min" the lowest.
        - Ignore runs that never logged `metric`.
        - Raise ValueError if mode is invalid or no run logged the metric.
        """
        # TODO: validate mode; filter to runs that logged `metric`; if none,
        #       raise ValueError; otherwise return the best run's id.
        raise NotImplementedError("TODO: implement best-run selection")


# ---------------------------------------------------------------------------
# Demonstration of intended usage.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tracker = ExperimentTracker()

    a = tracker.start_run("rag-baseline", {"model": "gpt-4o-mini", "temperature": 0.2})
    tracker.log_metric(a, "faithfulness", 0.81)
    tracker.log_metric(a, "cost_usd", 0.012)
    tracker.end_run(a)

    b = tracker.start_run("rag-reranker", {"model": "gpt-4o", "temperature": 0.0})
    tracker.log_metric(b, "faithfulness", 0.93)
    tracker.log_metric(b, "cost_usd", 0.041)
    tracker.end_run(b)

    c = tracker.start_run("rag-tiny", {"model": "llama-3-8b", "temperature": 0.3})
    tracker.log_metric(c, "faithfulness", 0.70)
    tracker.log_metric(c, "cost_usd", 0.003)
    tracker.end_run(c)

    for run in tracker.list_runs():
        print(run["run_id"], run["name"], run["metrics"])

    print("Best faithfulness (max):", tracker.best_run("faithfulness", "max"))
    print("Cheapest cost (min):", tracker.best_run("cost_usd", "min"))
