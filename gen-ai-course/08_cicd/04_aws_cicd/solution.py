"""Solution: an AWS CodeDeploy-style traffic-shift deployer.

Models how AWS CodeDeploy releases a new version: you pick a named
*deployment configuration* (AllAtOnce / Canary / Linear), and the deployer
walks its traffic-shift schedule, reading a (mock) CloudWatch alarm metric at
each weight. If the alarm breaches the threshold mid-shift it AUTO-ROLLS-BACK
to 0% (back to the previous/stable version); otherwise it reaches 100% and
the deployment succeeds.

Runs fully OFFLINE (no AWS account, no boto3, no network). Deterministic mock
alarm sources make the demo reproducible. The bottom runs a demo and asserts
the succeed/rollback behaviour.

Run with:  python solution.py
"""

from __future__ import annotations

from typing import Any, Callable


# ---------------------------------------------------------------------------
# Deployment configurations: named traffic-shift schedules, like CodeDeploy's.
# A schedule is a list of (minute_offset, canary_weight) steps ending at 100.
# ---------------------------------------------------------------------------
def all_at_once() -> list[tuple[int, int]]:
    """Shift 100% of traffic immediately."""
    return [(0, 100)]


def canary(canary_pct: int, bake_minutes: int) -> list[tuple[int, int]]:
    """Hold `canary_pct` for `bake_minutes`, then jump to 100% (two steps)."""
    return [(0, canary_pct), (bake_minutes, 100)]


def linear(step_pct: int, interval_minutes: int) -> list[tuple[int, int]]:
    """Add `step_pct` every `interval_minutes` until reaching 100%."""
    schedule: list[tuple[int, int]] = []
    minute, weight = 0, step_pct
    while weight < 100:
        schedule.append((minute, weight))
        minute += interval_minutes
        weight += step_pct
    schedule.append((minute, 100))
    return schedule


# Named configs mirroring CodeDeploy's built-ins.
DEPLOY_CONFIGS: dict[str, list[tuple[int, int]]] = {
    "AllAtOnce": all_at_once(),
    "Canary10Percent5Minutes": canary(10, 5),
    "Linear10PercentEvery1Minute": linear(10, 1),
}


# ---------------------------------------------------------------------------
# Deterministic mock CloudWatch alarm sources.
# An alarm source maps the current canary weight -> observed error rate.
# ---------------------------------------------------------------------------
def healthy_alarm(weight: int) -> float:
    """Error rate stays low and well under any sane threshold."""
    return 0.001 + weight * 0.00004      # 0.001 .. 0.005 across 0..100


def unhealthy_alarm(weight: int) -> float:  # noqa: ARG001 - fixed signature
    """Error rate is high immediately -> rollback on the first shift."""
    return 0.09


def degrading_alarm(weight: int) -> float:
    """Healthy at low exposure, spikes once the new version carries real load."""
    return 0.002 if weight < 50 else 0.20


# ---------------------------------------------------------------------------
# The deployer.
# ---------------------------------------------------------------------------
class Deployer:
    """Walks a deployment-config schedule; auto-rolls-back on an alarm breach."""

    def __init__(
        self,
        schedule: list[tuple[int, int]],
        alarm_source: Callable[[int], float],
        error_threshold: float = 0.05,
    ) -> None:
        self.schedule = schedule
        self.alarm_source = alarm_source
        self.error_threshold = error_threshold
        self.weight = 0
        self.status = "in_progress"
        self.history: list[dict[str, Any]] = []

    def run(self) -> str:
        for minute, target in self.schedule:
            # Shift traffic to this step's target, then read the alarm there.
            self.weight = target
            error_rate = self.alarm_source(target)
            in_alarm = error_rate > self.error_threshold

            if in_alarm:
                # CloudWatch alarm fired mid-shift -> CodeDeploy auto-rollback.
                self.weight = 0
                self.status = "rolled_back"
                self.history.append({
                    "minute": minute, "weight": self.weight,
                    "error_rate": error_rate, "status": self.status,
                })
                return self.status

            self.status = "succeeded" if target >= 100 else "in_progress"
            self.history.append({
                "minute": minute, "weight": self.weight,
                "error_rate": error_rate, "status": self.status,
            })
        return self.status


# ---------------------------------------------------------------------------
# Demonstration + assertions.
# ---------------------------------------------------------------------------
def _print_history(deployer: Deployer) -> None:
    for rec in deployer.history:
        print(
            f"  t+{rec['minute']:>2}m  weight={rec['weight']:>3}%  "
            f"error={rec['error_rate']:.3f}  status={rec['status']}"
        )


if __name__ == "__main__":
    print("=== Canary10Percent5Minutes, healthy (succeeds) ===")
    d = Deployer(DEPLOY_CONFIGS["Canary10Percent5Minutes"], healthy_alarm)
    final = d.run()
    _print_history(d)
    print("Final:", final)
    assert final == "succeeded"
    assert d.weight == 100
    assert [r["weight"] for r in d.history] == [10, 100]

    print("\n=== Canary10Percent5Minutes, unhealthy (auto-rolls back) ===")
    d = Deployer(DEPLOY_CONFIGS["Canary10Percent5Minutes"], unhealthy_alarm)
    final = d.run()
    _print_history(d)
    print("Final:", final)
    assert final == "rolled_back"
    assert d.weight == 0                          # traffic shifted fully back
    assert len(d.history) == 1                    # bailed on the first shift

    print("\n=== Linear10PercentEvery1Minute, degrading at 50% (rolls back) ===")
    d = Deployer(DEPLOY_CONFIGS["Linear10PercentEvery1Minute"], degrading_alarm)
    final = d.run()
    _print_history(d)
    print("Final:", final)
    assert final == "rolled_back"
    assert d.weight == 0
    # Healthy through 10..40%, then 50% spikes -> rollback on the 5th step.
    assert [r["status"] for r in d.history] == [
        "in_progress", "in_progress", "in_progress", "in_progress", "rolled_back"
    ]

    print("\n=== AllAtOnce, healthy (succeeds in one shift) ===")
    d = Deployer(DEPLOY_CONFIGS["AllAtOnce"], healthy_alarm)
    final = d.run()
    _print_history(d)
    print("Final:", final)
    assert final == "succeeded"
    assert d.weight == 100
    assert len(d.history) == 1

    print("\n=== AllAtOnce, unhealthy (full-blast failure rolls back) ===")
    d = Deployer(DEPLOY_CONFIGS["AllAtOnce"], unhealthy_alarm)
    final = d.run()
    print("Final:", final)
    assert final == "rolled_back"
    assert d.weight == 0

    # The linear schedule ends at exactly 100 and never overshoots.
    sched = DEPLOY_CONFIGS["Linear10PercentEvery1Minute"]
    assert sched[-1][1] == 100
    assert all(w <= 100 for _, w in sched)

    print("\nAll assertions passed.")
