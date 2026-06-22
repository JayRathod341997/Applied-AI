"""Exercise: an AWS CodeDeploy-style traffic-shift deployer.

You will build a `Deployer` that models how AWS CodeDeploy releases a new
version. You pick a named *deployment configuration* (AllAtOnce / Canary /
Linear) — a traffic-shift schedule — and the deployer walks it, reading a
(mock) CloudWatch alarm metric at each weight. If the alarm breaches the
threshold mid-shift it AUTO-ROLLS-BACK to 0% (back to the stable version);
otherwise it reaches 100% and the deployment succeeds.

Everything runs OFFLINE (Python standard library only). The deployment
configs and deterministic mock alarm sources are provided. Complete only the
`# TODO` sections.

Run with:  python exercise.py
"""

from __future__ import annotations

from typing import Any, Callable


# ---------------------------------------------------------------------------
# Provided: deployment configurations (named traffic-shift schedules).
# A schedule is a list of (minute_offset, canary_weight) steps ending at 100.
# Do NOT modify these.
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


DEPLOY_CONFIGS: dict[str, list[tuple[int, int]]] = {
    "AllAtOnce": all_at_once(),
    "Canary10Percent5Minutes": canary(10, 5),
    "Linear10PercentEvery1Minute": linear(10, 1),
}


# ---------------------------------------------------------------------------
# Provided: deterministic mock CloudWatch alarm sources. Do NOT modify these.
# An alarm source maps the current canary weight -> observed error rate.
# ---------------------------------------------------------------------------
def healthy_alarm(weight: int) -> float:
    """Error rate stays low and well under any sane threshold."""
    return 0.001 + weight * 0.00004      # 0.001 .. 0.005 across 0..100


def unhealthy_alarm(weight: int) -> float:
    """Error rate is high immediately -> rollback on the first shift."""
    return 0.09


def degrading_alarm(weight: int) -> float:
    """Healthy at low exposure, spikes once the new version carries real load."""
    return 0.002 if weight < 50 else 0.20


# ---------------------------------------------------------------------------
# TODO: implement the deployer.
# ---------------------------------------------------------------------------
class Deployer:
    """Walks a deployment-config schedule; auto-rolls-back on an alarm breach."""

    def __init__(
        self,
        schedule: list[tuple[int, int]],
        alarm_source: Callable[[int], float],
        error_threshold: float = 0.05,
    ) -> None:
        """Start at weight 0, status 'in_progress', empty history.

        Store `schedule`, `alarm_source`, and `error_threshold`.
        """
        # TODO: store config and initialize weight / status / history.
        raise NotImplementedError("TODO: initialize the deployer")

    def run(self) -> str:
        """Walk the schedule step by step and return the final status.

        For each (minute, target) in self.schedule:
          - shift traffic: self.weight = target
          - read the alarm at the new weight:
                error_rate = self.alarm_source(target)
          - if error_rate > self.error_threshold:
                self.weight = 0; self.status = "rolled_back"
                append the record, then STOP and return "rolled_back"
          - else: self.status = "succeeded" if target >= 100 else "in_progress"
          - append a record {"minute", "weight", "error_rate", "status"}
        Return self.status after the loop.
        """
        # TODO: implement the traffic-shift loop with auto-rollback.
        raise NotImplementedError("TODO: implement run")


# ---------------------------------------------------------------------------
# Demonstration of intended usage.
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

    print("\n=== Canary10Percent5Minutes, unhealthy (auto-rolls back) ===")
    d = Deployer(DEPLOY_CONFIGS["Canary10Percent5Minutes"], unhealthy_alarm)
    final = d.run()
    _print_history(d)
    print("Final:", final)
