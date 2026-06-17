# Quiz

## Question 1

In a circuit breaker, what does the **OPEN** state do when a request arrives?

A) Forwards the request to the dependency and counts the result
B) Rejects the request immediately without calling the dependency ("fail fast")
C) Allows exactly one trial request through to test recovery
D) Queues the request until the dependency recovers

---

**Answer: B**

When OPEN, the breaker has decided the dependency is unhealthy. It rejects requests immediately (or invokes a fallback) rather than wasting time and resources on calls that are likely to fail. This protects both your latency and the struggling dependency. (A) describes CLOSED, and (C) describes HALF_OPEN.

---

## Question 2

Why add **jitter** (randomness) to retry backoff delays?

A) To make logs easier to read
B) To prevent many clients from retrying in synchronized waves (the "thundering herd")
C) To guarantee the request eventually succeeds
D) To reduce the total number of retries

---

**Answer: B**

Without jitter, all clients that failed at the same moment retry at the same fixed offsets, re-synchronizing load spikes onto the recovering service. Adding a random component spreads retries out over time, smoothing the load. It does not change retry count or guarantee success.

---

## Question 3

Which HTTP status code is generally **safe to retry** with backoff?

A) 400 Bad Request
B) 401 Unauthorized
C) 503 Service Unavailable
D) 422 Unprocessable Entity

---

**Answer: C**

503 indicates a transient server-side condition that may resolve on retry. 400/422 mean your request is malformed (retrying sends the same bad request), and 401 means auth failed (it won't fix itself by retrying). Retry allowlists should target 429 and 5xx plus network/timeout errors.

---

## Question 4

After the cooldown period expires, an OPEN circuit breaker transitions to which state?

A) CLOSED
B) OPEN (stays open)
C) HALF_OPEN
D) A new "RECOVERING" state

---

**Answer: C**

When the cooldown elapses, the breaker moves to HALF_OPEN and allows a single trial call. If that call succeeds it closes; if it fails it returns to OPEN and the cooldown restarts. It does not jump straight to CLOSED — it must verify recovery first.

---

## Question 5

What is the purpose of the **bulkhead** pattern?

A) To encrypt traffic between services
B) To isolate resource pools so one failing workload can't exhaust capacity for the others
C) To retry failed requests automatically
D) To cache responses for faster reads

---

**Answer: B**

Like watertight compartments in a ship, bulkheads partition resources (thread pools, connection pools, concurrency limits) per workload. If one model endpoint becomes slow and saturates its pool, the other workloads keep their own capacity and stay healthy.

---

## Question 6

Which is the **best** example of graceful degradation when your primary model is unavailable?

A) Return a 500 error to the user
B) Retry the primary model 50 times in a tight loop
C) Fall back to a cheaper model, then a cached answer, then a canned response
D) Crash the service so it restarts

---

**Answer: C**

Graceful degradation serves a worse-but-useful response instead of a hard failure. A tiered fallback (cheaper model → cache → static reply) keeps the service responsive. Tight-loop retries (B) amplify the outage, and (A)/(D) give the user nothing.

---

## Question 7

A **liveness** probe should generally:

A) Check that every downstream database and the LLM provider are reachable
B) Be cheap and local, checking only that the process itself is alive
C) Always return 200 no matter what
D) Run the full inference pipeline on each call

---

**Answer: B**

Liveness answers "is this process deadlocked?" and its failure action is a **restart**. If it checks shared dependencies, a single DB hiccup fails liveness on every pod at once, restarting them all — a self-inflicted outage. Dependency checks belong in the **readiness** probe, whose failure only drains traffic.

---

## Question 8

What happens to the circuit breaker if the **trial call in HALF_OPEN fails**?

A) It transitions to CLOSED
B) It stays in HALF_OPEN and tries again immediately
C) It transitions back to OPEN and restarts the cooldown
D) It permanently disables the dependency

---

**Answer: C**

A failed trial means the dependency is still unhealthy, so the breaker re-opens and restarts its cooldown timer before allowing another probe. Only a *successful* trial closes the circuit.

---

## Question 9

In a multi-provider fallback chain integrated with circuit breakers, what should happen when a provider's breaker is **OPEN**?

A) Wait for the breaker's cooldown before continuing
B) Skip that provider immediately and try the next one in the chain
C) Reset the breaker to CLOSED and try anyway
D) Abort the entire request

---

**Answer: B**

An OPEN breaker means that provider is known-bad, so the chain should skip it instantly (no timeout paid) and move to the next healthy provider. This is exactly why combining breakers with fallback chains is powerful — failover becomes immediate.

---

## Question 10

Why should a testable circuit breaker **inject a clock function** instead of calling `time.time()` directly?

A) `time.time()` is deprecated
B) So tests can advance time instantly and verify the cooldown transition without real sleeping
C) To make the code run faster in production
D) Because circuit breakers require asynchronous code

---

**Answer: B**

Hard-coding the wall clock forces tests to actually sleep through the cooldown, making them slow and flaky. Injecting a `clock` (e.g., a fake whose value you control) lets a test jump past the cooldown instantly and assert the OPEN → HALF_OPEN transition deterministically.

---

## Question 11

What is **deadline propagation**?

A) Giving every downstream call a fresh, full timeout
B) Passing the remaining time budget down the call chain so downstream calls can't exceed the caller's SLA
C) Removing all timeouts to avoid premature failures
D) Logging how long each call took

---

**Answer: B**

If your endpoint has a 10s SLA and 7s is already spent, the downstream LLM call should get at most ~3s — not a fresh 30s. Propagating the remaining deadline prevents downstream calls from blowing your own SLA and wasting work on responses that arrive too late to use.

---

## Question 12

Combining retries **without** a circuit breaker during a full provider outage primarily causes what problem?

A) Nothing — retries always help
B) It amplifies load on the dead dependency and ties up your own resources with doomed calls
C) It automatically opens a circuit
D) It reduces cost

---

**Answer: B**

If the dependency is fully down, every request retries several times before failing, multiplying load on the struggling service and consuming your threads/connections/budget on calls that can't succeed. The circuit breaker is what stops this by failing fast once the failure rate crosses a threshold.

---
