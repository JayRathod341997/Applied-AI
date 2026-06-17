# Reliability & Resilience — Concepts

AI systems face unique reliability challenges: model endpoints can timeout, return malformed output, throttle you with rate limits, or degrade in quality without raising an error. A reliable system does not try to make every dependency perfect — it assumes dependencies *will* fail and contains the blast radius. This document covers the patterns that turn a fragile pipeline into a resilient one.

A useful mental model: every remote call is a small contract that can be broken three ways — **too slow** (latency), **failing** (errors), or **wrong** (bad output). Each resilience pattern targets one or more of these failure modes.

| Failure mode | Symptom | Primary pattern |
|---|---|---|
| Too slow | Hangs, p99 latency spikes | Timeouts, deadlines |
| Failing | 5xx, connection refused, rate limits | Retries, circuit breaker, fallback |
| Wrong | Empty / malformed / off-topic output | Validation, graceful degradation |
| Cascading | One slow dep stalls the whole service | Bulkheads, circuit breaker |

---

## 1. Timeouts

A call without a timeout is a resource leak waiting to happen. If the LLM provider hangs, every waiting request holds a connection, a thread, and memory until something else breaks. **Always set a timeout** that is shorter than your own caller's deadline.

```python
# Bad: no timeout — a hung provider can stall forever
resp = client.chat.completions.create(model="gpt-4o", messages=msgs)

# Good: bounded wait
resp = client.chat.completions.create(model="gpt-4o", messages=msgs, timeout=30)
```

**Deadline propagation:** if your API has a 10s SLA and you've already spent 7s, the downstream LLM call should get *at most* 3s — not a fresh 30s. Pass the remaining budget down the call chain rather than hard-coding a per-call timeout.

---

## 2. Retries with Exponential Backoff + Jitter

Transient failures (a 503, a brief rate limit, a dropped connection) often succeed on a second attempt. But naive retries are dangerous:

- **Retrying immediately** hammers an already-struggling service.
- **Fixed-interval retries** from many clients synchronize into a "thundering herd."
- **Retrying non-idempotent or permanent errors** (400, 401) just wastes time and money.

The fix is **exponential backoff** (wait longer each attempt) plus **jitter** (randomize the wait so clients don't retry in lockstep).

```
delay = min(base * 2**attempt, max_delay) + random_jitter
```

```
attempt 0 ── fail ──► wait ~1s  (1 + jitter)
attempt 1 ── fail ──► wait ~2s  (2 + jitter)
attempt 2 ── fail ──► wait ~4s  (4 + jitter)
attempt 3 ── give up / fall back
```

```python
import random, time

def retry_with_backoff(fn, max_retries=3, base=1.0, max_delay=30.0):
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except TransientError:
            if attempt == max_retries:
                raise
            delay = min(base * (2 ** attempt), max_delay) + random.uniform(0, 1)
            time.sleep(delay)
```

The `tenacity` library implements this declaratively:

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

@retry(stop=stop_after_attempt(4), wait=wait_exponential_jitter(initial=1, max=30))
def call_llm(prompt): ...
```

**Retry only what is retryable.** Build an allowlist: 429 (rate limit), 500/502/503/504, timeouts, connection errors. Never retry 400/401/403/422.

| Status | Retry? | Why |
|---|---|---|
| 429 Too Many Requests | Yes (with backoff) | Transient throttling |
| 500 / 502 / 503 / 504 | Yes | Server-side transient |
| Timeout / conn reset | Yes | Network blip |
| 400 / 422 | No | Your request is malformed |
| 401 / 403 | No | Auth won't fix itself |

---

## 3. Circuit Breaker

Retries help with *brief* blips. But if a provider is *down*, retrying every request just piles latency and cost onto a dead endpoint and ties up your own resources. The **circuit breaker** stops calling a failing dependency entirely, fails fast, and periodically probes for recovery.

It is a state machine with three states:

```
        ┌──────────────────────────────────────────────────┐
        │                 Circuit Breaker                   │
        │                                                   │
        │   ┌────────┐  failures >= threshold   ┌────────┐  │
        │   │ CLOSED │ ───────────────────────► │  OPEN  │  │
        │   └────────┘                          └───┬────┘  │
        │      ▲  ▲                                 │       │
        │      │  │ success on trial    cooldown    │       │
        │      │  │                     elapsed     ▼       │
        │      │  │                          ┌────────────┐ │
        │      │  └───────── success ─────────│ HALF_OPEN │ │
        │      │                              └─────┬──────┘ │
        │      │            trial fails             │       │
        │      └──────────────◄────────── OPEN ◄────┘       │
        └──────────────────────────────────────────────────┘
```

| State | Behavior | Transitions out |
|---|---|---|
| **CLOSED** | Calls pass through; count consecutive failures | → OPEN when failures ≥ threshold |
| **OPEN** | Reject immediately ("fail fast"), do **not** call the dependency | → HALF_OPEN after cooldown elapses |
| **HALF_OPEN** | Allow **one** trial call to test recovery | → CLOSED on success, → OPEN on failure |

Key properties:

- **Fail fast.** While OPEN, the breaker returns instantly (or invokes a fallback) instead of waiting for a timeout — protecting both your latency and the struggling provider.
- **Self-healing.** After a `cooldown`, it lets exactly one request through to test the waters. One success closes the circuit; one failure re-opens it and resets the cooldown.
- **Per-dependency.** Keep a separate breaker per model/provider so one bad endpoint doesn't trip the others.

```python
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

# Pseudocode for the core decision
def can_execute(now):
    if state == OPEN and now - opened_at >= cooldown:
        state = HALF_OPEN      # time to probe
    return state in (CLOSED, HALF_OPEN)
```

> A subtle but critical detail for **testable** breakers: never read the wall clock directly. Inject a `clock` function so tests can advance time instantly instead of really sleeping. The exercise in this subtopic does exactly that.

---

## 4. Bulkheads

Named after the watertight compartments in a ship's hull: if one floods, the others keep the ship afloat. In software, a **bulkhead** isolates resources (thread pools, connection pools, concurrency limits) so a failure in one workload cannot consume all capacity and sink the rest.

```
Without bulkhead:                With bulkhead:
┌────────────────────┐          ┌─────────┬─────────┬─────────┐
│  shared pool (50)  │          │ pool A  │ pool B  │ pool C  │
│  slow model eats   │          │ (20)    │ (20)    │ (10)    │
│  ALL 50 slots ──►  │          │ model A │ model B │ batch   │
│  everything stalls │          │ slow ►  │ fine    │ fine    │
└────────────────────┘          └─────────┴─────────┴─────────┘
```

Practical bulkheads for AI services:

- Separate concurrency limits per model/provider.
- A dedicated pool for slow batch jobs vs. interactive requests.
- Separate the embedding service from the generation service so an embedding outage doesn't block chat.

---

## 5. Graceful Degradation & Fallbacks

When the primary path fails (or its breaker is OPEN), a resilient system serves a **degraded but useful** response instead of an error. Ordered from best to worst:

```
Primary model (gpt-4o)
   │ fails / breaker OPEN
   ▼
Cheaper model (gpt-4o-mini)       ← fallback to cheaper model
   │ fails
   ▼
Cached / previously-computed answer ← fallback to cache
   │ miss
   ▼
Static canned response ("I'm having trouble right now, try again")
```

| Strategy | When to use | Trade-off |
|---|---|---|
| Fallback to cheaper model | Primary slow/down, quality can dip | Lower quality, still useful |
| Fallback to cache | Repeat or similar query seen before | Possibly stale |
| Cached/canned default | Everything else failed | Generic, but no hard error |
| Partial response | One of N sub-results failed | Show what you have |

The guiding principle: **a slightly worse answer now beats a perfect answer never.**

---

## 6. Multi-Provider Redundancy

Don't bet your uptime on a single vendor. A **fallback chain** tries providers/models in order until one succeeds, combining redundancy with cost control.

```python
FALLBACK_CHAIN = [
    {"provider": "openai",    "model": "gpt-4o"},
    {"provider": "openai",    "model": "gpt-4o-mini"},
    {"provider": "anthropic", "model": "claude-3-5-sonnet"},
    {"provider": "anthropic", "model": "claude-3-haiku"},
]

def call_with_fallback(prompt):
    errors = []
    for cfg in FALLBACK_CHAIN:
        breaker = get_breaker(cfg["model"])
        if not breaker.can_execute():      # skip OPEN circuits
            continue
        try:
            result = invoke(cfg, prompt)
            breaker.record_success()
            return {"content": result, "model": cfg["model"],
                    "fallback_used": len(errors) > 0}
        except Exception as e:
            breaker.record_failure()
            errors.append((cfg["model"], str(e)))
    raise RuntimeError(f"All providers failed: {errors}")
```

Combine this with per-model circuit breakers (Section 3): an OPEN breaker is skipped instantly, so the chain jumps to the next healthy provider without paying the failing one's timeout.

---

## 7. Health Checks: Readiness vs Liveness

Orchestrators (Kubernetes, load balancers) need to know whether a service should receive traffic. Two distinct probes answer two distinct questions:

| Probe | Question | Failure action | Should it check dependencies? |
|---|---|---|---|
| **Liveness** | "Is the process alive / not deadlocked?" | Restart the pod | **No** — keep it cheap & local |
| **Readiness** | "Can it serve traffic right now?" | Remove from load balancer (don't restart) | **Yes** — model loaded, deps reachable |

```
                ┌───────────────┐
   /livez  ───► │  process up?  │ ──► no ──► KILL & RESTART pod
                └───────────────┘
                ┌───────────────────────────────┐
   /readyz ───► │ model loaded? deps reachable? │ ─ no ─► drop from LB
                └───────────────────────────────┘            (no restart)
```

A common mistake is making the **liveness** probe check downstream dependencies. If a shared database hiccups, every pod fails liveness and gets restarted simultaneously — turning a minor blip into a self-inflicted outage. Liveness should be local and cheap; readiness can be richer. A third **startup** probe gives slow-loading models time to warm up before the other probes begin.

---

## 8. Putting It Together

A production-grade LLM client layers these patterns:

```
request
  │
  ▼
[bulkhead] limit concurrency per model
  │
  ▼
[circuit breaker] OPEN? ── yes ──► fail fast ──► [fallback chain] next model
  │ no
  ▼
[timeout + retry/backoff+jitter] call provider
  │ success            │ exhausted
  ▼                    ▼
record_success    record_failure ──► [fallback: cheaper model / cache / canned]
```

No single pattern is sufficient. Retries without a circuit breaker amplify outages; a circuit breaker without fallbacks turns failures into errors; fallbacks without health checks send traffic to dead pods. Resilience is the *composition* of these patterns.

---

## Key Takeaways

- Assume every remote call can be **slow**, **failing**, or **wrong** — design for all three.
- **Timeouts** are mandatory; propagate deadlines so downstream calls inherit the remaining budget.
- **Retry only retryable errors** (429, 5xx, timeouts) with **exponential backoff + jitter**; never retry 4xx auth/validation errors.
- The **circuit breaker** (CLOSED → OPEN → HALF_OPEN) makes a failing dependency *fail fast* and *self-heal*; use a separate breaker per provider.
- **Bulkheads** isolate resource pools so one slow workload can't starve the rest.
- **Graceful degradation** prefers a worse-but-useful answer (cheaper model, cache, canned reply) over an error.
- **Multi-provider fallback chains** remove single-vendor risk; skip OPEN breakers to jump straight to a healthy provider.
- Keep **liveness** probes cheap and local (restart), and **readiness** probes dependency-aware (drain) — never the reverse.
- For testable resilience code, **inject the clock** instead of calling `time.time()`/`sleep` directly.
