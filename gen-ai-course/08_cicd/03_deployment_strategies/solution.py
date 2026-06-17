"""Solution: a canary release controller.

Implements `CanaryController`: shifts traffic to a new version in increments,
reads a (mock) error rate at each step, auto-promotes when the canary reaches
100% healthy, and auto-rolls back to 0% when the error rate exceeds a threshold.

Runs fully OFFLINE (no API keys, no network). Deterministic mock metrics
sources make the demo reproducible. The bottom runs a demo and asserts the
promote/rollback behaviour.

Run with:  python solution.py
"""

from __future__ import annotations

from typing import Any, Callable


# ---------------------------------------------------------------------------
# Deterministic mock metrics sources.
# A metrics source maps the current canary weight -> observed error rate.
# ---------------------------------------------------------------------------
def healthy_metrics(weight: int) -> float:
    """Error rate stays low and well under any sane threshold."""
    return 0.001 + weight * 0.00004      # 0.001 .. 0.005 across 0..100


def unhealthy_metrics(weight: int) -> float:  # noqa: ARG001 - fixed signature
    """Error rate is high immediately -> should trigger rollback on step 1."""
    return 0.09


def degrading_metrics(weight: int) -> float:
    """Healthy at first, then spikes once the canary carries real traffic."""
    return 0.002 if weight < 50 else 0.20


# ---------------------------------------------------------------------------
# The controller.
# ---------------------------------------------------------------------------
class CanaryController:
    """Drives a canary rollout: ramp while healthy, rollback on error spike."""

    def __init__(
        self,
        metrics_source: Callable[[int], float],
        step: int = 25,
        error_threshold: float = 0.05,
    ) -> None:
        self.metrics_source = metrics_source
        self.step = step
        self.error_threshold = error_threshold
        self.weight = 0
        self.status = "in_progress"
        self.history: list[dict[str, Any]] = []

    def advance(self) -> str:
        # Shift traffic first, then observe the canary at its new weight.
        self.weight = min(self.weight + self.step, 100)
        error_rate = self.metrics_source(self.weight)

        if error_rate > self.error_threshold:
            self.weight = 0
            self.status = "rolled_back"
        elif self.weight >= 100:
            self.status = "promoted"
        else:
            self.status = "in_progress"

        self.history.append({
            "weight": self.weight,
            "error_rate": error_rate,
            "status": self.status,
        })
        return self.status

    def run(self) -> str:
        while self.status == "in_progress":
            self.advance()
        return self.status


# ---------------------------------------------------------------------------
# Demonstration + assertions.
# ---------------------------------------------------------------------------
def _print_history(controller: CanaryController) -> None:
    for rec in controller.history:
        print(
            f"  weight={rec['weight']:>3}%  "
            f"error={rec['error_rate']:.3f}  status={rec['status']}"
        )


if __name__ == "__main__":
    print("=== Healthy canary (auto-promotes) ===")
    c = CanaryController(healthy_metrics, step=25, error_threshold=0.05)
    final = c.run()
    _print_history(c)
    print("Final:", final)
    assert final == "promoted"
    assert c.weight == 100
    assert len(c.history) == 4                    # 25 -> 50 -> 75 -> 100
    assert [r["weight"] for r in c.history] == [25, 50, 75, 100]

    print("\n=== Unhealthy canary (auto-rolls back) ===")
    c = CanaryController(unhealthy_metrics, step=25, error_threshold=0.05)
    final = c.run()
    _print_history(c)
    print("Final:", final)
    assert final == "rolled_back"
    assert c.weight == 0                          # traffic shifted fully back
    assert len(c.history) == 1                    # bailed on the first step
    assert c.history[-1]["status"] == "rolled_back"

    print("\n=== Degrading canary (healthy then spikes at 50%) ===")
    c = CanaryController(degrading_metrics, step=25, error_threshold=0.05)
    final = c.run()
    _print_history(c)
    print("Final:", final)
    assert final == "rolled_back"
    assert c.weight == 0
    # Step 1 -> 25% healthy (in_progress); step 2 -> 50% spikes -> rollback.
    assert [r["status"] for r in c.history] == ["in_progress", "rolled_back"]

    # Weight never exceeds 100, even with a small final step.
    c = CanaryController(healthy_metrics, step=40, error_threshold=0.05)
    c.run()
    assert c.weight == 100
    assert all(r["weight"] <= 100 for r in c.history)

    print("\nAll assertions passed.")
