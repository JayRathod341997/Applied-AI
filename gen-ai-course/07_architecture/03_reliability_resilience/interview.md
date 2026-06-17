# Reliability & Resilience — Interview Questions

### Q1: Walk me through the three states of a circuit breaker and the transitions between them.

**Answer:** A circuit breaker is a state machine that protects a caller from a failing dependency.

| State | Behavior | Exit transition |
|---|---|---|
| **CLOSED** | Calls pass through; count consecutive failures | → OPEN when failures reach the threshold |
| **OPEN** | Reject immediately (fail fast); never call the dependency | → HALF_OPEN after the cooldown elapses |
| **HALF_OPEN** | Allow a single trial call to test recovery | → CLOSED on success, → OPEN on failure (cooldown restarts) |

The point is to stop hammering a dead dependency (saving latency and cost), while still self-healing: after a cooldown the breaker probes once, and the result decides whether to fully recover or keep the circuit open.

---

### Q2: How is a circuit breaker different from a retry?

**Answer:** They operate at different time scales and solve complementary problems.

- A **retry** handles a *single transient blip* — it re-attempts the same request a few times, ideally with backoff and jitter.
- A **circuit breaker** handles a *sustained outage* — after many failures it stops attempting altogether for a cooldown period.

Retries without a breaker are dangerous during a full outage: every request retries N times, multiplying load on the dead service and tying up your own resources. The breaker caps that by failing fast once the failure rate crosses a threshold. In practice you layer them: retry inside the breaker for blips, breaker around the retry loop for outages.

---

### Q3: Why is jitter important in retry backoff, and what kinds of jitter exist?

**Answer:** Without jitter, all clients that failed simultaneously retry at identical offsets, re-synchronizing into load spikes (the "thundering herd") that can re-knock-over a recovering service. Jitter randomizes the delay so retries spread out.

Common strategies:
- **Full jitter:** `sleep = random(0, base * 2**attempt)` — maximum spread.
- **Equal jitter:** half fixed, half random.
- **Decorrelated jitter:** `sleep = min(cap, random(base, prev * 3))`.

AWS's analysis found full/decorrelated jitter minimizes both completion time and server load. The exact scheme matters less than *having* jitter at all.

---

### Q4: Which errors should you retry, and which should you never retry?

**Answer:** Retry only **transient, idempotent-safe** failures.

| Retry | Don't retry |
|---|---|
| 429 (rate limit, honor `Retry-After`) | 400 / 422 (malformed request) |
| 500 / 502 / 503 / 504 | 401 / 403 (auth) |
| Network timeouts, connection resets | 404 (not found) |

Retrying a 400 just re-sends the same broken request; retrying a 401 won't fix credentials. Also be careful retrying **non-idempotent** operations (e.g., a POST that charges money) — you may double-execute unless you use an idempotency key.

---

### Q5: What is a timeout, and what is deadline propagation?

**Answer:** A **timeout** bounds how long you'll wait for a call before giving up; without one, a hung dependency leaks threads/connections until your service collapses. **Deadline propagation** means passing the *remaining* time budget down the call chain instead of giving each hop a fresh full timeout. If your endpoint promises a 10s SLA and 7s is already gone, the downstream LLM call should get ≈3s — otherwise it might return an answer you can no longer use, having already blown your SLA. gRPC and many RPC frameworks propagate deadlines automatically; with HTTP/LLM SDKs you often compute and pass it manually.

---

### Q6: Explain the bulkhead pattern with an AI example.

**Answer:** A bulkhead isolates resource pools so a failure in one workload can't exhaust capacity for the others — named after a ship's watertight compartments. Concretely: give each model/provider its own concurrency limit or connection pool. If `gpt-4o` becomes slow and its 20 slots fill up, requests to `gpt-4o-mini` and your embedding service still have their own pools and stay responsive. Without a bulkhead, a single shared pool lets the slow model consume every slot, stalling everything. Other examples: separate interactive vs. batch pools, and isolating the embedding service from the generation service.

---

### Q7: What does graceful degradation look like for an LLM application?

**Answer:** Serving a worse-but-useful response instead of a hard error, via an ordered fallback:

```
primary model -> cheaper model -> cached/similar answer -> static canned reply
```

For example, if `gpt-4o` is down or its breaker is OPEN, fall back to `gpt-4o-mini`; if that fails, return a cached answer for a similar query; if there's no cache, return a friendly "I'm having trouble right now" message. The principle: *a slightly worse answer now beats a perfect answer never.* You should also surface a flag (e.g., `fallback_used: true`) so observability/quality monitoring knows degraded paths were taken.

---

### Q8: Compare liveness and readiness probes. What's a common mistake?

**Answer:**

| | Liveness | Readiness |
|---|---|---|
| Question | "Is the process alive / not deadlocked?" | "Can it serve traffic right now?" |
| Failure action | **Restart** the pod | **Remove from load balancer** (drain) |
| Checks deps? | No — cheap & local | Yes — model loaded, deps reachable |

The classic mistake is making **liveness** check downstream dependencies. If a shared database hiccups, every pod fails liveness at once and gets restarted simultaneously — converting a minor blip into a self-inflicted outage and possibly a crash loop. Keep liveness local; put dependency checks in readiness, whose failure only drains traffic without killing the pod. A **startup** probe additionally protects slow-loading models from being killed before they warm up.

---

### Q9: How do you combine circuit breakers with a multi-provider fallback chain?

**Answer:** Keep one breaker per provider/model and iterate a chain ordered by preference/cost:

```python
for cfg in FALLBACK_CHAIN:
    breaker = get_breaker(cfg["model"])
    if not breaker.can_execute():   # OPEN -> skip instantly, no timeout paid
        continue
    try:
        result = invoke(cfg, prompt)
        breaker.record_success()
        return result
    except Exception:
        breaker.record_failure()
raise RuntimeError("all providers unavailable")
```

The synergy: an OPEN breaker is skipped immediately, so failover to a healthy provider is instant rather than waiting on the bad one's timeout. This removes single-vendor risk and controls cost (try cheaper/faster options first or as fallbacks).

---

### Q10: Why should a circuit breaker not read the wall clock directly, and how do you test it?

**Answer:** If the breaker calls `time.time()`/`time.monotonic()` internally, the only way to test the cooldown transition is to actually sleep through it — making tests slow and flaky. Inject a `clock` callable (defaulting to `time.monotonic`). In tests, pass a fake whose value you control and "advance" it to jump past the cooldown instantly, then assert the OPEN → HALF_OPEN transition deterministically. This is the dependency-injection-of-time technique and applies to any time-based logic (rate limiters, TTL caches, retry schedulers).

---

### Q11: What is the difference between `monotonic` and wall-clock time, and which should a breaker use?

**Answer:** Wall-clock time (`time.time()`) can jump backwards or forwards due to NTP corrections, daylight-saving, or manual clock changes. **Monotonic** time (`time.monotonic()`) only ever moves forward and is immune to such adjustments, making it correct for measuring *elapsed durations* like a cooldown. A breaker should measure cooldown with monotonic time; using wall-clock risks a clock adjustment making the cooldown appear to elapse instantly or never.

---

### Q12: How would you choose the failure threshold and cooldown for a circuit breaker?

**Answer:** There's no universal value — tune to the dependency's behavior and your traffic:

- **Failure threshold:** too low (e.g., 1) trips on isolated blips and harms availability; too high delays protection during a real outage. Many systems use a *failure rate over a rolling window* (e.g., "open if >50% of the last 20 requests failed") rather than a raw consecutive count, which is more robust under high volume.
- **Cooldown:** long enough to let the dependency actually recover, short enough to restore service quickly. Often combined with **exponential cooldown** (back off the cooldown itself on repeated trial failures) to avoid hammering a still-broken dependency.

Always pair with metrics so you can observe trip frequency and tune empirically.

---

### Q13: What failure modes do these patterns NOT protect against?

**Answer:** Resilience patterns handle *availability* and *latency* failures, but not necessarily *correctness*. A model can return a 200 with confident, wrong, or off-topic output — the circuit breaker sees a "success." Protecting against bad-but-successful responses requires **output validation** (schema/grounding checks), **quality monitoring**, and possibly an **LLM-as-judge** or guardrail layer. Likewise, breakers and retries don't fix systemic capacity problems, data-corruption bugs, or poisoned caches. Reliability engineering is necessary but not sufficient; pair it with correctness controls.

---

### Q14: Describe a fully layered reliable LLM client.

**Answer:** From outermost to innermost:

1. **Bulkhead** — per-model concurrency limit so one slow model can't starve others.
2. **Circuit breaker** — per provider; if OPEN, fail fast and let the fallback chain skip it.
3. **Timeout + retry with backoff/jitter** — bound each call and retry transient errors.
4. **Fallback chain** — cheaper model → cache → canned response on exhaustion.
5. **Health checks** — readiness drains unhealthy pods; liveness restarts dead ones.
6. **Observability** — record state transitions, fallback usage, retry counts.

No single layer suffices: retries without a breaker amplify outages; a breaker without fallbacks turns failures into errors; fallbacks without health checks send traffic to dead pods. Resilience is the *composition* of these patterns, each targeting a different failure mode.

---
