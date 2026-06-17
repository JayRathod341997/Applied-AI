# Exercise: Circuit Breaker for LLM Calls

## Background

LLM endpoints fail. When a provider goes down, retrying every request just piles latency and cost onto a dead endpoint while tying up your own threads and connections. A **circuit breaker** solves this: once it sees enough consecutive failures, it stops calling the dependency entirely and *fails fast*, then periodically probes to see whether the dependency has recovered.

You will implement a circuit breaker that wraps a flaky (mock) LLM client. The breaker is a three-state machine:

```
   CLOSED ──(N consecutive failures)──► OPEN
     ▲                                    │
     │ (trial succeeds)         (cooldown │ elapses)
     │                                    ▼
     └──────────── HALF_OPEN ◄────────────┘
                      │
                      └──(trial fails)──► OPEN  (cooldown restarts)
```

| State | What it does |
|---|---|
| **CLOSED** | Calls pass through to the LLM. Count consecutive failures; reset the count on success. Open after N consecutive failures. |
| **OPEN** | Fail fast — raise without calling the LLM. After `cooldown` seconds, move to HALF_OPEN. |
| **HALF_OPEN** | Allow exactly one trial call. Success → CLOSED (reset). Failure → OPEN (restart cooldown). |

Because cooldowns are time-based, the breaker must be **testable without real sleeping**. You will use an **injectable clock** — a function returning "the current time" — so tests can advance time instantly.

## Your Task

Open `exercise.py` and complete the `CircuitBreaker` class:

1. Implement `_now()` to return the current time using the injected `clock` function (default: `time.monotonic`).
2. Implement `can_execute()`:
   - CLOSED → return `True`.
   - OPEN → if `cooldown` has elapsed since `opened_at`, transition to HALF_OPEN and return `True`; otherwise return `False`.
   - HALF_OPEN → return `True` (allow the single trial).
3. Implement `record_success()`: reset `failure_count`; if in HALF_OPEN (or OPEN), transition to CLOSED.
4. Implement `record_failure()`:
   - In HALF_OPEN: a failed trial re-opens the circuit (restart cooldown).
   - In CLOSED: increment `failure_count`; open the circuit when it reaches `failure_threshold`.
5. Implement `call(fn, *args, **kwargs)`: the public entry point.
   - If `can_execute()` is `False`, raise `CircuitOpenError` (fail fast) without calling `fn`.
   - Otherwise call `fn`; on success call `record_success()` and return the result; on exception call `record_failure()` and re-raise.

## Requirements

- No network, no API keys — the provided `MockLLM` runs entirely offline.
- **No real sleeping.** Use the injected `clock`; tests advance a fake clock manually.
- Use only the standard library (plus the provided `MockLLM`).
- A separate breaker instance is independent (no global state).

## How to Run

```bash
cd "d:/Jay Rathod/Tutorials/Applied AI/gen-ai-course/07_architecture/03_reliability_resilience"
python exercise.py        # your work-in-progress
python solution.py        # reference solution with asserts
```

## Expected Output

Running the completed solution prints a clear trace of state transitions and ends with all assertions passing, for example:

```
[CLOSED]    call ok       -> CLOSED
[CLOSED]    call FAILED   -> CLOSED (failures=1/3)
[CLOSED]    call FAILED   -> CLOSED (failures=2/3)
[CLOSED]    call FAILED   -> OPEN   (threshold reached)
[OPEN]      fail fast (no LLM call)
... cooldown elapses ...
[HALF_OPEN] trial call ok -> CLOSED
All assertions passed.
```
