# Logging Strategies — Concepts

Metrics tell you *that* something is wrong; logs tell you *what* happened. For a GenAI service the logs are uniquely valuable (prompt/response pairs, tool calls, retrieval scores) and uniquely dangerous (those same prompts carry PII). This file covers structured logging, log levels, PII redaction, correlation IDs and distributed tracing, log aggregation, and retention — everything needed to make logs both useful and safe.

---

## 1. Why AI Logging Is Different

| Concern | Traditional app | GenAI service |
|---|---|---|
| Output shape | Structured, deterministic | Free-form text, probabilistic |
| Pipeline | One service | Retrieval → rerank → generation → tools |
| Cost | Fixed per request | Per-token; must log usage to bill |
| PII risk | Form fields | *Anywhere* in free-text prompts |
| Debug unit | A stack trace | A whole multi-step trace |

The implication: log **structured records** (not prose), **redact PII** at the boundary, **log token usage** for cost, and **correlate** records across the chain.

---

## 2. Structured Logging

A structured log is a machine-parseable record — almost always JSON — not a human sentence. It can be queried, aggregated, and alerted on without fragile regex parsing.

```
Unstructured (bad):
  2026-06-17 10:30 INFO request from john took 1500ms model gpt-4o

Structured (good):
  {"timestamp":"2026-06-17T10:30:00Z","level":"INFO","service":"rag-api",
   "request_id":"req_abc","model":"gpt-4o","latency_ms":1500,"status":"ok"}
```

Essential fields for an LLM request record:

| Field | Purpose |
|---|---|
| `timestamp` | When (UTC, ISO-8601) |
| `level` | Severity (see below) |
| `service` | Which component emitted it |
| `request_id` / `correlation_id` / `trace_id` | Stitch records together |
| `model` | Which model served the call |
| `input_tokens` / `output_tokens` | Cost & efficiency |
| `latency_ms` | Performance |
| `status` / `error_type` | Outcome |
| `prompt_hash` | Identify identical prompts without storing raw text |

```python
import json, logging
def log_event(logger, **fields):
    logger.info(json.dumps(fields))   # one JSON object per line
```

---

## 3. Log Levels

Levels let you turn the firehose down in production and up while debugging.

| Level | Use for | In prod? |
|---|---|---|
| **DEBUG** | Full prompt/response, per-step detail | Off (sampled on) |
| **INFO** | Normal events: request served, retrieval done | On |
| **WARNING** | Recoverable issues: retry, fallback used | On |
| **ERROR** | Failed request needing attention | On |
| **CRITICAL** | System-wide failure | On + page |

A common pattern is to **always log errors** but **sample** INFO/DEBUG to control volume and cost:

```python
import random
def should_log(is_error: bool, sample_rate: float = 0.1) -> bool:
    return True if is_error else random.random() < sample_rate
```

---

## 4. PII Redaction

User prompts can contain emails, phone numbers, SSNs, credit cards, and pasted API keys. Redact **before** the record leaves the application boundary — once PII reaches a third-party log store, you have a compliance incident.

| Strategy | When | Trade-off |
|---|---|---|
| **Redaction** | Default for prod logs | Loses debugging context |
| **Hashing** | Identify same user/value without exposure | One-way, not reversible |
| **Tokenization** | Need reversibility for internal use | Requires a secure token store |
| **Exclusion** | Highly sensitive fields | No visibility at all |
| **Encryption at rest** | All log storage | Performance overhead |

```python
import re
PII = [
    (re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9]{8,}\b"),               "[API_KEY_REDACTED]"),
    (re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),    "[PHONE_REDACTED]"),
]
def redact(text: str) -> str:
    for pattern, repl in PII:
        text = pattern.sub(repl, text)
    return text
```

> Order matters: redact specific high-entropy patterns (API keys) before broad numeric ones (phones) so a generic pattern doesn't mangle a key. This is exactly what you implement in the exercise.

---

## 5. Correlation IDs & Distributed Tracing

A single user request fans out across services (gateway → retriever → reranker → LLM). To reconstruct it, every log record and every span must carry shared IDs.

| ID | Scope |
|---|---|
| `trace_id` | The whole request across all services |
| `span_id` | One operation within the trace |
| `request_id` | One request at one service |
| `session_id` | A multi-turn conversation |

**OpenTelemetry** is the vendor-neutral standard: instrument once, export to Jaeger, Tempo, Datadog, etc. A trace is a tree of spans:

```
trace_id = T1
└─ span: rag.query                      (root)
   ├─ span: retrieval        docs=5  avg_score=0.91
   ├─ span: rerank           in=20  out=5
   └─ span: llm.generation   model=gpt-4o  in=250 out=120  cost=$0.0019
```

```python
# OpenTelemetry shape (illustrative — needs the SDK + an exporter)
from opentelemetry import trace
tracer = trace.get_tracer("rag")
with tracer.start_as_current_span("rag.query") as root:
    root.set_attribute("rag.top_k", 5)
    with tracer.start_as_current_span("retrieval") as s:
        s.set_attribute("retrieval.docs", 5)
```

---

## 6. Log Aggregation

Individual servers ship structured logs to a central pipeline that parses, enriches, routes, and stores them for search and alerting.

```
┌──────────┐ ┌──────────┐ ┌──────────┐
│App Server│ │App Server│ │App Server│   (JSON logs)
└────┬─────┘ └────┬─────┘ └────┬─────┘
     └────────────┼────────────┘
                  ▼
        ┌───────────────────┐
        │ Shipper           │  parse JSON, add host/region/version,
        │ (Fluentd/Filebeat)│  route to the right index
        └─────────┬─────────┘
        ┌─────────┼──────────┐
        ▼         ▼          ▼
 ┌───────────┐ ┌────────┐ ┌──────┐
 │Elasticsearch│ S3/GCS │ │ Loki │
 │ (hot/search)│ archive │ │(opt) │
 └─────┬───────┘ └────────┘ └──────┘
       ▼
   Grafana / Kibana  → dashboards, search, alerts
```

| Tool | Strength |
|---|---|
| ELK (Elasticsearch/Kibana) | Full-text search, analytics |
| Splunk | Enterprise, compliance |
| Datadog | APM + logs in one place |
| CloudWatch | AWS-native |
| Grafana Loki | Cost-effective, Grafana-integrated |

---

## 7. Retention Policies

Keep logs long enough to debug and to satisfy compliance — and no longer (storage cost + privacy risk). Tier by access speed: hot (searchable) → warm → cold archive.

| Log type | Hot | Warm | Cold archive | Total |
|---|---|---|---|---|
| Request/response | 7 days | 30 days | 1 year | 1 year |
| Error logs | 30 days | 90 days | 2 years | 2 years |
| Evaluation scores | 30 days | 1 year | 3 years | 3 years |
| Audit logs | 90 days | 1 year | 7 years | 7 years |
| Debug/trace | 3 days | — | — | 3 days |

Compliance drivers: **GDPR** (data minimisation, right to erasure), **HIPAA** (healthcare data), **CCPA** (consumer privacy), **SOC 2** (security controls).

---

## Key Takeaways

- **Structured beats prose.** Emit one JSON record per event with stable fields so logs can be queried, aggregated, and alerted on without fragile parsing.
- **Redact PII at the boundary.** Strip emails, phones, SSNs, and API keys *before* records leave the process; choose redact / hash / tokenize / exclude per field, and order patterns so specific ones run before broad ones.
- **Use levels and sampling.** Always log errors; sample INFO/DEBUG to control volume and cost while keeping the ability to turn detail up when debugging.
- **Correlate everything.** Thread `trace_id` / `span_id` / `request_id` through every record and span so a multi-step request can be reconstructed end-to-end; OpenTelemetry is the vendor-neutral way to do it.
- **Aggregate centrally, tier retention.** Ship structured logs to a pipeline (ELK / Loki / Datadog) and age them hot → warm → cold per type, balancing debuggability against cost and compliance (GDPR/HIPAA/CCPA/SOC 2).
