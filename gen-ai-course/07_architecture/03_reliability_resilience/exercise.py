"""Exercise: Circuit Breaker for LLM calls (STARTER).

Implement a three-state circuit breaker (CLOSED / OPEN / HALF_OPEN) that wraps a
flaky mock LLM client. Everything runs OFFLINE with no API keys and NO real
sleeping: time is provided by an injectable `clock` function so tests can advance
a fake clock instantly.

Fill in every method that raises NotImplementedError, then run this file. When
you are done, compare against solution.py.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Callable


# --------------------------------------------------------------------------- #
# Provided: a controllable, offline mock LLM. Do not modify.
# --------------------------------------------------------------------------- #
class MockLLMError(RuntimeError):
    """Raised by MockLLM when it is configured to fail."""


class MockLLM:
    """A fake LLM client whose failure behavior is fully controllable.

    Set `fail = True` to make every call raise MockLLMError; set it back to
    False to make calls succeed. This lets you simulate provider outages and
    recovery deterministically, with no network access.
    """

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.call_count = 0  # number of times the LLM was actually invoked

    def complete(self, prompt: str) -> str:
        self.call_count += 1
        if self.fail:
            raise MockLLMError("mock provider is down")
        return f"echo: {prompt}"


# --------------------------------------------------------------------------- #
# Circuit breaker
# --------------------------------------------------------------------------- #
class CircuitState(Enum):
    CLOSED = "closed"        # normal operation; calls pass through
    OPEN = "open"            # failing; reject immediately
    HALF_OPEN = "half_open"  # probing recovery with one trial call


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
        """Return the current time using the injected clock."""
        # TODO: return the current time from self._clock
        raise NotImplementedError("TODO: implement _now using the injected clock")

    # -- decision ---------------------------------------------------------- #
    def can_execute(self) -> bool:
        """Return True if a call may proceed; may transition OPEN -> HALF_OPEN.

        CLOSED    -> True
        OPEN      -> if cooldown elapsed since opened_at: go HALF_OPEN, True
                     else: False
        HALF_OPEN -> True (allow the single trial call)
        """
        # TODO: implement the state-dependent gate described above.
        raise NotImplementedError("TODO: implement can_execute")

    # -- result recording -------------------------------------------------- #
    def record_success(self) -> None:
        """Record a successful call.

        Reset failure_count. If we were HALF_OPEN (or OPEN), close the circuit.
        """
        # TODO: reset failures and (if probing) close the circuit.
        raise NotImplementedError("TODO: implement record_success")

    def record_failure(self) -> None:
        """Record a failed call.

        HALF_OPEN: a failed trial re-opens the circuit (restart cooldown).
        CLOSED:    increment failure_count; open when it reaches the threshold.
        """
        # TODO: implement failure handling and state transitions.
        raise NotImplementedError("TODO: implement record_failure")

    def _open(self) -> None:
        """Transition to OPEN and stamp the time (restarts the cooldown)."""
        # TODO: set state to OPEN and record opened_at = self._now()
        raise NotImplementedError("TODO: implement _open")

    # -- public entry point ------------------------------------------------ #
    def call(self, fn: Callable[..., str], *args, **kwargs) -> str:
        """Execute `fn` through the breaker.

        - If can_execute() is False, raise CircuitOpenError WITHOUT calling fn.
        - Otherwise call fn; on success record_success() and return its result;
          on exception record_failure() and re-raise.
        """
        # TODO: implement the guarded call described above.
        raise NotImplementedError("TODO: implement call")


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # A fake clock you control: advance time without sleeping.
    fake_time = {"t": 0.0}
    clock = lambda: fake_time["t"]

    llm = MockLLM(fail=False)
    breaker = CircuitBreaker(failure_threshold=3, cooldown=10.0, clock=clock)

    # Once implemented, this should pass through while the LLM is healthy,
    # open after 3 failures, fail fast while OPEN, then recover after cooldown.
    print(breaker.call(llm.complete, "hello"))
