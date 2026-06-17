# Quiz

## Question 1

What is the primary reason logging for a GenAI service differs from traditional application logging?

A) AI systems use more storage
B) Outputs are free-form text and a request fans out across retrieval, generation, and tools — so you must log richer, correlatable records
C) AI systems are always faster
D) Logging is legally required only for AI

---

**Answer: B**

A GenAI request is a multi-step, probabilistic pipeline whose output is free-form text. Useful debugging needs per-step records (prompt hashes, retrieval scores, token counts) correlated by a shared ID — far richer than a single deterministic app log line.

---

## Question 2

Why should a structured (JSON) log record be preferred over a free-text log line?

A) JSON files are smaller than text
B) It is machine-parseable, so it can be queried, aggregated, and alerted on without fragile regex parsing
C) JSON cannot contain PII
D) Free text is impossible to store

---

**Answer: B**

Structured records expose stable, typed fields. Aggregation tools index and query them directly, whereas prose log lines require brittle parsing that breaks the moment the message wording changes.

---

## Question 3

Which PII-handling technique lets you still identify that two log records came from the same user, without storing the raw identifier?

A) Deletion
B) Hashing
C) Compression
D) Encryption at rest only

---

**Answer: B**

A stable one-way hash (e.g. SHA-256, truncated) maps the same input to the same token every time, so you can correlate a user's activity while keeping the original PII unrecoverable. Encryption is reversible; deletion removes the linkage entirely.

---

## Question 4

In the PII regex pipeline, why does order matter (e.g. redact API keys before the generic phone-number pattern)?

A) Regex engines run patterns alphabetically anyway
B) A broad numeric pattern could mangle a high-entropy value like an API key before its specific pattern runs
C) Order has no effect on substitution
D) API keys are not PII

---

**Answer: B**

If a generic pattern (like a digit-run phone matcher) runs first, it can partially rewrite an API key or other structured secret, leaving a corrupted residue. Running the specific, high-entropy patterns first ensures each value is replaced cleanly by its own placeholder.

---

## Question 5

At what point should PII be redacted from logs?

A) After logs are shipped to the third-party store
B) Before the record leaves the application boundary
C) Only during the nightly batch job
D) Never — redaction breaks debugging

---

**Answer: B**

Once raw PII reaches a third-party log store, you have a compliance incident even if you redact later. Redaction must happen in-process, before the record is written or shipped anywhere.

---

## Question 6

Which correlation ID is used to tie together all the individual service calls that make up a single user request across a distributed system?

A) request_id
B) session_id
C) trace_id
D) user_id

---

**Answer: C**

`trace_id` spans the entire request across every service; `span_id` identifies one operation within it; `request_id` is local to one service; `session_id` groups a multi-turn conversation. Tracing tools (OpenTelemetry) propagate the `trace_id` so the whole tree can be reconstructed.

---

## Question 7

Which log level is appropriate for a recoverable issue such as an automatic retry or a fallback to a secondary provider?

A) DEBUG
B) INFO
C) WARNING
D) CRITICAL

---

**Answer: C**

WARNING signals something went wrong but the system recovered (a retry, a fallback). It is worth surfacing for trend analysis without paging anyone, unlike ERROR (a failed request) or CRITICAL (system-wide failure).

---

## Question 8

A high-traffic service wants to control log volume and cost. What is a common, safe sampling strategy?

A) Drop all logs randomly, including errors
B) Always log errors; sample INFO/DEBUG at a fraction (e.g. 10%)
C) Log only the very first request of the day
D) Disable logging entirely above a request rate

---

**Answer: B**

Errors are rare and high-value, so they should always be captured. Routine INFO/DEBUG records are voluminous and low-value individually, so sampling them (e.g. 10%) preserves statistical visibility while slashing storage cost.

---

## Question 9

What is the main benefit of instrumenting with OpenTelemetry rather than a vendor-specific tracing SDK?

A) It is the only tool that can trace LLMs
B) It is vendor-neutral: instrument once and export to Jaeger, Tempo, Datadog, etc.
C) It removes the need for any backend
D) It automatically redacts PII

---

**Answer: B**

OpenTelemetry is an open standard. You add instrumentation once and can route the same traces/metrics/logs to any compatible backend, avoiding lock-in to a single observability vendor.

---

## Question 10

Why are log retention policies usually tiered (hot → warm → cold) and capped per log type?

A) To make logs harder to read
B) To balance debuggability against storage cost, privacy risk, and compliance requirements
C) Because regulators forbid keeping any logs
D) Cold storage is faster to query than hot storage

---

**Answer: B**

Recent logs need fast (expensive) hot storage for debugging; older logs move to cheaper warm/cold tiers. Caps per type keep cost and privacy exposure down while still meeting compliance retention windows (e.g. audit logs for years, debug traces for days). Cold storage is cheaper but slower to query, not faster.
