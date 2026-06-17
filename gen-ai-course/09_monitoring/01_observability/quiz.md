# Quiz

## Question 1

Which of the three pillars of observability is best suited to answering "where did the time go across a multi-step RAG request?"

A) Metrics
B) Logs
C) Traces
D) Alerts

---

**Answer: C**

A trace is a tree of spans (retrieval → rerank → generation), so it shows exactly how much of the request budget each step consumed. Metrics aggregate across requests and logs describe single events, but neither reconstructs the per-step timeline of one request the way a trace does.

---

## Question 2

Why is LLM observability harder than traditional ML observability?

A) LLMs are always slower
B) LLM outputs are free-form and the chain can succeed (200 OK) while being factually wrong
C) Traditional ML has no metrics
D) LLMs never use external tools

---

**Answer: B**

Traditional ML returns a structured prediction you can score against a label. An LLM can return a perfectly valid HTTP response that is hallucinated, off-topic, or toxic — so operational health (uptime, status codes) is not enough; you must also track quality signals.

---

## Question 3

A service handles 100 requests: 99 take 1 second and 1 takes 60 seconds. What does this reveal about using the average latency as your headline metric?

A) The average (~1.6 s) accurately reflects user experience
B) The average hides a severe tail; one user waited 60 s
C) The average is the same as P99 here
D) Averages are always better than percentiles

---

**Answer: B**

The mean of ~1.6 s sounds healthy while masking a 60-second outlier. Percentiles (especially P99) surface the tail experiences that averages smooth away, which is why you alert on P95/P99.

---

## Question 4

What does P95 latency mean?

A) The average of the slowest 5% of requests
B) 95% of requests are faster than this value
C) The fastest 95 requests
D) The latency 95 ms after the request starts

---

**Answer: B**

P95 is the value below which 95% of observed latencies fall. Equivalently, the slowest 1-in-20 requests are worse than P95. It captures "a bad day" without being dominated by extreme outliers like P99.9.

---

## Question 5

For most LLM providers, which token type is typically the more expensive per token?

A) Input (prompt) tokens
B) Output (completion) tokens
C) They are always priced identically
D) System-prompt tokens are free

---

**Answer: B**

Output tokens usually cost 3–5× input tokens, so verbose responses are a hidden cost driver. This is why cost dashboards separate input and output token spend and why response-length control is a cost lever.

---

## Question 6

You want to attribute spend to the 5% of customers driving most of your bill. What should you do?

A) Track only the global total cost
B) Slice the cost metric by tenant/customer (and by model and feature)
C) Disable cost tracking to save money
D) Switch every request to the cheapest model

---

**Answer: B**

A single global cost number cannot tell you *who* or *what* is expensive. Tagging each cost record with tenant, model, and feature lets you break spend down and find the heavy users or pathological features.

---

## Question 7

What is the difference between monitoring and observability?

A) They are identical
B) Monitoring targets known unknowns with predefined dashboards/alerts; observability lets you explore unknown unknowns from raw signals
C) Observability only works for traditional ML
D) Monitoring requires traces; observability requires only metrics

---

**Answer: B**

Monitoring answers questions you anticipated ("is error rate high?") via dashboards and alerts. Observability gives you enough raw, high-cardinality data (logs, traces) to investigate questions you did not anticipate ("why is *this* user slow right now?"). Production systems need both.

---

## Question 8

Why are LLM quality metrics (e.g. hallucination rate) usually computed on a sample rather than every request?

A) Quality never matters in production
B) Each quality check often needs another (costly) model call, so sampling controls cost and latency
C) Sampling makes the metric more accurate
D) Providers forbid measuring quality

---

**Answer: B**

LLM-as-judge and faithfulness checks typically require an extra model invocation per evaluated request. Running that on 100% of traffic doubles cost and latency, so teams evaluate a random sample (e.g. 5%) to get a continuous, affordable quality signal.

---

## Question 9

Which alert is the best example of an actionable, symptom-based SLO alert for an LLM service?

A) "CPU on node-7 is at 60%"
B) "A garbage-collection pause occurred"
C) "Error rate exceeded 1% for 2 minutes"
D) "A log line was written"

---

**Answer: C**

A sustained error-rate breach is user-visible (a symptom), tied to an SLO, and gives the on-call a clear thing to investigate. CPU level and GC pauses are causes, not symptoms, and often fire without anyone needing to act — fueling alert fatigue.

---

## Question 10

What role does the `for:` duration play in a Prometheus-style alert rule (e.g. `for: 2m`)?

A) It deletes the metric after 2 minutes
B) It requires the condition to hold continuously for 2 minutes before firing, suppressing brief flaps
C) It caps request latency at 2 minutes
D) It samples 2% of requests

---

**Answer: B**

`for:` adds a sustain window: the alert fires only if the expression stays true for the whole duration. This filters out momentary spikes that self-resolve, a key defence against alert fatigue.
