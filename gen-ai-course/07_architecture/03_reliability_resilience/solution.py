"""Solution: Circuit Breaker for LLM calls.

A complete, OFFLINE three-state circuit breaker (CLOSED / OPEN / HALF_OPEN)
wrapping a controllable mock LLM. No API keys, no network, and NO real sleeping:
time comes from an injectable `clock`, so the cooldown transition is testable
instantly.

Run:
    python solution.py

It prints a trace of state transitions and asserts that the breaker:
  * opens after N consecutive failures,
  * fails fast while OPEN (without calling the LLM),
  * transitions to HALF_OPEN after the cooldown,
  * closes again on a successful trial call,
  * and re-opens on a failed trial call.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Callable


# --------------------------------------------------------------------------- #
# Controllable, offline mock LLM
# --------------------------------------------------------------------------- #
class MockLLMError(RuntimeError):
    """Raised by MockLLM when it is configured to fail."""


class MockLLM:
    """A fake LLM client whose failure behavior is fully controllable.

    Set `fail = True` to make every call raise MockLLMError; set it back to
    False to make calls succeed. `call_count` tracks how many times the LLM was
    actually invoked, which lets tests prove the breaker fails fast (the count
    must not increase while OPEN).
    """

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.call_count = 0

    def complete(self, prompt: str) -> str:
        self.call_count += 1
        if self.fail:
            raise MockLLMError("mock provider is down")
        return f"echo: {prompt}"


# --------------------------------------------------------------------------- #
# Circuit breaker
# --------------------------------------------------------------------------- #
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    """Raised by CircuitBreaker.call when the circuit is OPEN (fail fast)."""


class CircuitBreaker:
    """Three-state circuit breaker with an injectable clock.

    Args:
        failure_threshold: consecutive failures in CLOSED before opening.
        cooldown: seconds the circuit stays OPEN before allowing a trial.
        clock: zero-arg callable returning the current time in seconds.
               Defaults to time.monotonic. Inject a fake in tests.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        cooldown: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self._clock = clock

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at: float | None = None

    # -- helpers ----------------------------------------------------------- #
    def _now(self) -> float:
        return self._clock()

    def _open(self) -> None:
        """Transition to OPEN and stamp the time (restarts the cooldown)."""
        self.state = CircuitState.OPEN
        self.opened_at = self._now()

    def _cooldown_elapsed(self) -> bool:
        return (
            self.opened_at is not None
            and (self._now() - self.opened_at) >= self.cooldown
        )

    # -- decision ---------------------------------------------------------- #
    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self._cooldown_elapsed():
                # Time to probe: allow a single trial call.
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        # HALF_OPEN: allow the single trial call.
        return True

    # -- result recording -------------------------------------------------- #
    def record_success(self) -> None:
        # Any success means the dependency is healthy: reset and close.
        self.failure_count = 0
        if self.state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
            self.state = CircuitState.CLOSED
        self.opened_at = None

    def record_failure(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            # A failed trial: the dependency is still bad -> re-open.
            self._open()
            return

        # CLOSED: count consecutive failures and open at the threshold.
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self._open()

    # -- public entry point ------------------------------------------------ #
    def call(self, fn: Callable[..., str], *args, **kwargs) -> str:
        if not self.can_execute():
            raise CircuitOpenError(
                f"circuit is {self.state.value}; failing fast"
            )

        try:
            result = fn(*args, **kwargs)
        except Exception:
            self.record_failure()
            raise
        else:
            self.record_success()
            return result


# --------------------------------------------------------------------------- #
# Demo + assertions
# --------------------------------------------------------------------------- #
def _label(b: CircuitBreaker) -> str:
    return f"[{b.state.value.upper():<9}]"


if __name__ == "__main__":
    # Fake clock: advance time deterministically, no real sleeping.
    fake_time = {"t": 0.0}

    def clock() -> float:
        return fake_time["t"]

    def advance(seconds: float) -> None:
        fake_time["t"] += seconds

    llm = MockLLM(fail=False)
    breaker = CircuitBreaker(failure_threshold=3, cooldown=10.0, clock=clock)

    # 1) Healthy call passes through while CLOSED.
    out = breaker.call(llm.complete, "hello")
    print(f"{_label(breaker)} call ok       -> {breaker.state.value}  ({out!r})")
    assert breaker.state == CircuitState.CLOSED
    assert out == "echo: hello"

    # 2) Provider goes down: drive consecutive failures up to the threshold.
    llm.fail = True
    for i in range(1, breaker.failure_threshold + 1):
        try:
            breaker.call(llm.complete, "ping")
        except MockLLMError:
            note = (
                "(threshold reached)"
                if breaker.state == CircuitState.OPEN
                else f"(failures={breaker.failure_count}/{breaker.failure_threshold})"
            )
            print(f"{_label(breaker)} call FAILED   -> {breaker.state.value:<9} {note}")

    # Breaker opens after N consecutive failures.
    assert breaker.state == CircuitState.OPEN, breaker.state

    # 3) While OPEN it fails fast WITHOUT calling the LLM.
    calls_before = llm.call_count
    try:
        breaker.call(llm.complete, "ping")
        raise AssertionError("expected CircuitOpenError while OPEN")
    except CircuitOpenError:
        print(f"{_label(breaker)} fail fast (no LLM call attempted)")
    assert llm.call_count == calls_before, "OPEN breaker must not call the LLM"

    # Still OPEN before cooldown elapses.
    advance(5.0)  # less than cooldown (10s)
    assert breaker.can_execute() is False
    assert breaker.state == CircuitState.OPEN

    # 4) After cooldown elapses, next attempt transitions OPEN -> HALF_OPEN.
    advance(6.0)  # total 11s > 10s cooldown
    assert breaker.can_execute() is True
    assert breaker.state == CircuitState.HALF_OPEN
    print(f"{_label(breaker)} cooldown elapsed -> probing")

    # 4a) If the trial FAILS, the breaker re-opens (cooldown restarts).
    try:
        breaker.call(llm.complete, "ping")
    except MockLLMError:
        pass
    assert breaker.state == CircuitState.OPEN
    print(f"{_label(breaker)} trial FAILED  -> OPEN (cooldown restarted)")

    # 5) Provider recovers. After cooldown, a successful trial closes the circuit.
    llm.fail = False
    advance(11.0)
    assert breaker.can_execute() is True
    assert breaker.state == CircuitState.HALF_OPEN
    out = breaker.call(llm.complete, "recovered")
    print(f"{_label(breaker)} trial ok      -> {breaker.state.value}  ({out!r})")
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    assert out == "echo: recovered"

    print("\nAll assertions passed.")
