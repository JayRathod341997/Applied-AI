"""Exercise: a canary release controller.

You will build a `CanaryController` that shifts traffic to a new version in
increments, reads a (mock) error rate at each step, auto-promotes when the
canary reaches 100% healthy, and auto-rolls back to 0% when the error rate
exceeds a threshold.

Everything runs OFFLINE (Python standard library only). Deterministic mock
metrics sources are provided. Complete only the `# TODO` sections.

Run with:  python exercise.py
"""

from __future__ import annotations

from typing import Callable


# ---------------------------------------------------------------------------
# Provided: deterministic mock metrics sources. Do NOT modify these.
# A metrics source maps the current canary weight -> observed error rate.
# ---------------------------------------------------------------------------
def healthy_metrics(weight: int) -> float:
    """Error rate stays low and well under any sane threshold."""
    return 0.001 + weight * 0.00004      # 0.001 .. 0.005 across 0..100


def unhealthy_metrics(weight: int) -> float:
    """Error rate is high immediately -> should trigger rollback on step 1."""
    return 0.09


def degrading_metrics(weight: int) -> float:
    """Healthy at first, then spikes once the canary carries real traffic."""
    return 0.002 if weight < 50 else 0.20


# ---------------------------------------------------------------------------
# TODO: implement the controller.
# ---------------------------------------------------------------------------
class CanaryController:
    """Drives a canary rollout: ramp while healthy, rollback on error spike."""

    def __init__(
        self,
        metrics_source: Callable[[int], float],
        step: int = 25,
        error_threshold: float = 0.05,
    ) -> None:
        """Start at weight 0, status 'in_progress', empty history."""
        # TODO: store config and initialize weight / status / history.
        raise NotImplementedError("TODO: initialize the controller")

    def advance(self) -> str:
        """Perform one canary step and return the new status.

        - shift first: weight = min(weight + step, 100)
        - observe at the new weight: error_rate = self.metrics_source(weight)
        - if error_rate > threshold: weight = 0, status = 'rolled_back'
        - elif weight >= 100: status = 'promoted'
        - append {"weight", "error_rate", "status"} to history (post-step)
        """
        # TODO: implement one step of the canary loop.
        raise NotImplementedError("TODO: implement advance")

    def run(self) -> str:
        """Advance until status leaves 'in_progress'; return final status."""
        # TODO: loop advance() until done.
        raise NotImplementedError("TODO: implement run")


# ---------------------------------------------------------------------------
# Demonstration of intended usage.
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

    print("\n=== Unhealthy canary (auto-rolls back) ===")
    c = CanaryController(unhealthy_metrics, step=25, error_threshold=0.05)
    final = c.run()
    _print_history(c)
    print("Final:", final)
