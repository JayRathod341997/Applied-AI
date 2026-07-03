# Audit, Traceability & Control Mechanisms

> "If it isn't logged, it didn't happen — and you can't defend it."

For a Senior AI Security & Governance Engineer, audit is not a dashboard you add
later. It is a **runtime engineering requirement**: every AI interaction must
leave tamper-evident, reconstructable evidence, and every dangerous action must
be **controllable** (stoppable, reviewable, reversible). This topic covers *what*
to log, *how* to make logs trustworthy, and *how* to keep control of a live system.

---

## 1. Why audit trails are non-negotiable

Four independent forces make audit a hard requirement, not a nice-to-have:

| Driver | What it demands | Concrete failure if missing |
|---|---|---|
| **Regulatory evidence** | Prove *what the system did and why* | Fines, forced shutdown, failed audit |
| **Incident forensics** | Reconstruct an incident after the fact | "We think it leaked data but can't confirm scope" |
| **Accountability** | Attribute every action to a user/agent/model | Cannot answer "who approved this?" |
| **Reproducibility** | Re-run the exact request → same answer | Cannot debug or defend a bad output |

### Regulations you must be able to answer to

| Regime | Relevant requirement (paraphrased) | Audit implication |
|---|---|---|
| **EU AI Act** (Art. 12, high-risk) | Automatic **logging** of events over the system's lifetime; traceability of functioning | Immutable, retained event logs per interaction |
| **GDPR Art. 22** | Right not to be subject to solely automated decisions; right to explanation | Must show inputs, logic version, and human-review path |
| **SR 11-7** (US Fed Model Risk Mgmt) | Model inventory, validation, ongoing monitoring | Model + version lineage, decision records |
| **NIST AI RMF** (MEASURE/MANAGE) | Documented, traceable, monitored AI | End-to-end trace + retention |
| **ISO/IEC 42001** | AI management system with records & controls | Auditable control evidence |

> **Interview soundbite:** "Audit logging is how an AI system converts *behavior*
> into *evidence*. Regulators, incident responders, and your own debugging all
> consume the same trace. Design it once, tamper-evident, and reuse it."

---

## 2. What to log for **every** AI interaction

The unit of logging is the **span**: one step of one request. A simple chat call
is one span; an agent is many spans sharing a `correlation_id`.

```
┌──────────────────────── one AI interaction (span) ────────────────────────┐
│ WHO      user_id · app_id/agent_id · session_id                            │
│ WHAT     request · response  (REDACTED)  + raw_request_hash/raw_resp_hash  │
│ MODEL    model · model_version (PINNED) · system_prompt_version · temp     │
│ CONTEXT  retrieval_sources (doc ids/versions) · tool calls                 │
│ DECISION policy_decision · guardrail_verdicts · block_reason               │
│ COST     prompt_tokens · completion_tokens · cost_usd · latency_ms         │
│ TRACE    timestamp(UTC) · correlation_id · span_id · parent_span_id        │
│ INTEGRITY prev_hash · hash                                                 │
└────────────────────────────────────────────────────────────────────────────┘
```

Field-by-field rationale:

| Field | Why it's logged |
|---|---|
| `user_id`, `app_id`/`agent_id` | Accountability + abuse attribution |
| `model`, `model_version` | **Pin the version** — "gpt-4o" is not enough; providers silently update. Reproducibility & MRM |
| `system_prompt_version`, `prompt_version` | The prompt is code; a change can flip behavior. Version it |
| `retrieval_sources` | Data lineage — *which documents produced this answer* (RAG defensibility) |
| `policy_decision`, `guardrail_verdicts` | Prove a control ran and what it decided |
| `prompt_tokens`/`completion_tokens`/`cost_usd` | Cost governance, abuse/DoS detection |
| `latency_ms` | SLOs, and anomaly detection (a spike can signal an attack) |
| `timestamp` (UTC) | Ordering & correlation across services |
| `correlation_id`, `span_id`, `parent_span_id` | Traceability across a multi-step agent |
| `hash`, `prev_hash` | Tamper-evidence (Section 4) |

> **Golden rule:** log the **redacted** payload for humans, store a **hash** of the
> raw payload for proof-of-content, and keep the raw text (if needed at all)
> **encrypted and separate** under stricter access. See Section 4.

---

## 3. Traceability & lineage

Four kinds of lineage must connect so you can answer "how did we get this output?"

### 3.1 Request lineage (spans & traces)

Borrow the distributed-tracing model (OpenTelemetry). A **trace** = one logical
request; a **span** = one operation inside it. Spans nest via `parent_span_id`.

```
trace  correlation_id = 8e3bb4e5...
 ├─ span[0] retrieval    parent=None
 ├─ span[1] generation   parent=span[0]
 └─ span[2] guardrail     parent=span[0]
```

**OpenTelemetry for LLMs**: the emerging **OTel GenAI semantic conventions**
standardize attribute names (`gen_ai.request.model`, `gen_ai.usage.input_tokens`,
`gen_ai.prompt`, etc.). Using them means your traces work in Grafana/Jaeger/
Datadog/Langfuse/Arize without custom glue. In code: create a span per LLM call,
set the standard attributes, propagate the trace/correlation id across services.

### 3.2 Prompt / version lineage

Prompts and system prompts are **deployable artifacts**. Store them in a registry
with a version id; log that id on every span. A regression is then diffable:
"answers got worse after `support-sys-v6 → v7`."

### 3.3 Data lineage (RAG)

Log the **exact doc ids and versions** (`kb://refund-policy#v4`) that were
retrieved and injected. This is what lets you say "the wrong answer came from an
out-of-date policy doc," and it is central to GDPR/EU-AI-Act explainability.

### 3.4 Model lineage

A **model registry** (e.g., MLflow, SageMaker Model Registry) plus a **model card**
(intended use, eval results, limitations, training data summary) gives you
per-model provenance. Log the registry id + version on the span; SR 11-7 and the
EU AI Act both expect this inventory.

> **Anti-pattern:** using `model="latest"` or an unversioned prompt. You lose
> reproducibility and can never prove what actually ran.

---

## 4. Tamper-evidence & integrity

An audit log is only evidence if you can prove **no one edited it**. Four
mechanisms, strongest combined:

### 4.1 Append-only

Never `UPDATE`/`DELETE`; only `INSERT`. Open files in append mode (`"a"`), use
insert-only tables, revoke update/delete grants. This is the baseline.

### 4.2 Hash-chaining (tamper-**evidence**)

Each record stores the hash of the previous record; its own hash is computed over
its content **including** `prev_hash`. Alter record *N* and every hash from *N*
onward no longer matches → the tampering is **detectable** by anyone who
recomputes the chain. (This is the core of the exercise.)

```
rec0.hash = H( content0 + prev=000..0 )
rec1.hash = H( content1 + prev=rec0.hash )
rec2.hash = H( content2 + prev=rec1.hash )
             ▲ change content1  → rec1.hash changes → rec2.prev mismatch → BREAK
```

```python
import hashlib, json

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def canonical(obj) -> str:                      # deterministic serialization
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))

def link(record: dict, prev_hash: str) -> dict:
    record["prev_hash"] = prev_hash
    record["hash"] = sha256_hex(canonical({k: v for k, v in record.items()
                                           if k != "hash"}))
    return record

def verify(chain: list[dict]) -> bool:
    prev = "0" * 64
    for r in chain:
        body = {k: v for k, v in r.items() if k != "hash"}
        if r["prev_hash"] != prev or sha256_hex(canonical(body)) != r["hash"]:
            return False
        prev = r["hash"]
    return True
```

> Hash-chaining gives **tamper-evidence**, not tamper-*prevention*: a determined
> attacker with write access could recompute the whole chain. Defeat that by
> (a) periodically **anchoring** the head hash somewhere external/immutable
> (WORM store, notary, another team's ledger) and (b) **signing** records.

### 4.3 WORM storage (tamper-**resistance**)

Write-Once-Read-Many storage (e.g., **S3 Object Lock / Glacier compliance mode**,
Azure immutable blobs) physically prevents modification/deletion until retention
expires — even for admins. Combine with hash-chaining: WORM stops edits, the chain
proves it.

### 4.4 PII-safe logging

Logs are widely read (SREs, auditors) → they must **not** contain raw PII/secrets.

```
raw input ──► redact_pii() ──► REDACTED text  ──► audit log (broadly readable)
          └─► sha256(raw)  ──► raw_*_hash      ──► proof-of-content, no PII
          └─► encrypt(raw) ──► secure store    ──► restricted, short retention
```

Pattern:
* **Log redacted** payloads + a **hash** of the raw (proves content without
  exposing it, and lets you match two identical inputs).
* Store raw text only if truly needed, **encrypted** in a separate store with
  tighter access and shorter retention.
* Count PII types found (`{"EMAIL":1,"SSN":1}`) — useful for DLP metrics without
  storing values.

### 4.5 Retention policies

| Log class | Typical retention | Driver |
|---|---|---|
| Security/audit trail | 1–7 years | Regulatory / MRM |
| Raw prompts w/ PII | Minimal (days) or none | GDPR data-minimization |
| Aggregated metrics | Long | Cheap, low-risk |

Retention is a **two-sided constraint**: keep long enough to satisfy audit, delete
soon enough to satisfy privacy (GDPR "right to erasure"). Encode it explicitly.

---

## 5. Control mechanisms

Audit tells you what happened; **controls** let you change what happens next.

| Control | What it is | When it fires |
|---|---|---|
| **Kill switch** | One flag that hard-stops (or degrades) the AI feature globally | Active incident, jailbreak wave, data leak |
| **Guardrail feature flags** | Toggle individual guardrails / thresholds without redeploy | Tune false-positive rate; enable stricter mode |
| **Human-in-the-loop (HITL) approval** | High-risk actions require a human `approve/reject`, recorded | Refunds > $X, PII disclosure, irreversible tool calls |
| **Immutable decision records** | Append-only record of every allow/block/approve with reason | Every governed decision, forever |

```python
# Minimal, auditable kill switch + HITL gate
FLAGS = {"ai_enabled": True, "guardrail_strict": True, "require_human_approval": True}

def guarded_action(action, amount, logger, ctx):
    if not FLAGS["ai_enabled"]:
        logger.log(step="killswitch", policy_decision="block", ...)   # recorded
        raise RuntimeError("AI feature disabled by kill switch")
    if FLAGS["require_human_approval"] and amount > 100:
        approval = request_human_approval(action, amount)             # blocks
        logger.log(step="hitl", policy_decision=approval.decision,
                   guardrail_verdicts={"approver": approval.user}, ...)  # immutable
        if approval.decision != "allow":
            raise PermissionError("Rejected by human reviewer")
    return action()
```

Key properties: the kill switch is **fast** (no deploy), **global**, and **logged**;
HITL approvals are **recorded as immutable decision records** (who, when, why) so
you can prove a human authorized a consequential action.

---

## 6. Privacy vs auditability trade-off

These pull in opposite directions:

```
   AUDITABILITY  ◄──────────────────────────────►  PRIVACY
   log everything, keep forever          log nothing, keep nothing
```

Resolve it by **layering**, not by choosing a side:

| Need | Technique |
|---|---|
| Prove content without exposing it | Store **hash** of raw, log redacted |
| Investigate rare incidents | Raw encrypted, **break-glass** access with its own audit |
| Satisfy erasure requests | Separate PII store with short retention; audit trail keeps only redacted + hashes |
| Least-privilege on logs | RBAC: most engineers see redacted; few see raw; access itself is logged |

**Who can read audit logs?** Least privilege:

| Role | Access |
|---|---|
| On-call engineer | Redacted logs, metrics |
| Security/IR | Redacted + ability to request raw via break-glass |
| Compliance/auditor | Read-only, redacted + integrity proofs |
| Nobody | Standing access to raw PII; every raw access is itself audited |

> The audit system must **audit access to itself**. "Who read the logs?" is a
> question you must be able to answer.

---

## 7. Failure modes (what breaks in the real world)

| Failure mode | Symptom | Fix |
|---|---|---|
| Non-deterministic serialization | Valid chain fails verification | Canonical JSON (`sort_keys`, fixed separators) |
| PII redacted *after* logging | PII already on disk / in SIEM | Redact **before** the write, always |
| `model="latest"` | Can't reproduce a past output | Pin `model_version` per call |
| Log-and-forget | No integrity check ever runs | Scheduled `verify_chain()` + alert on break |
| Chain but no external anchor | Attacker with write recomputes chain | Periodically anchor head hash to WORM/notary |
| Unbounded raw retention | GDPR violation, huge blast radius | Separate store, short retention, encryption |
| Missing correlation id | Can't reconstruct agent trace | Generate at entry, propagate through every span |
| Logging is on the hot path | Latency spikes, dropped logs under load | Async/buffered writer; never drop audit silently |

---

## 8. Production checklist

- [ ] Every AI call logs a **span**: who, what (redacted), model+**pinned version**, prompt version, sources, decision, tokens, cost, latency, timestamp.
- [ ] **`correlation_id`** generated at request entry and propagated across every step/tool/service (OTel-style span/trace ids).
- [ ] Payloads **redacted before** writing; raw kept only encrypted + separate, or not at all; **hash** of raw stored for proof-of-content.
- [ ] Log is **append-only** and **hash-chained**; head hash periodically **anchored** to WORM / external immutable store.
- [ ] **`verify_chain()` runs on a schedule** and **alerts** on any break.
- [ ] Logs stored on **WORM / immutable** storage with **defined retention** (audit-long, PII-short).
- [ ] **RBAC + least privilege** on log access; **raw access is itself audited** (break-glass).
- [ ] Model **registry + model cards**; prompts **versioned** in a registry.
- [ ] **Kill switch** (fast, global, logged) and **guardrail feature flags** (no redeploy).
- [ ] **HITL approval** for high-risk actions, recorded as **immutable decision records** (who/when/why).
- [ ] Retention honors both **audit obligations** and **GDPR erasure**.
- [ ] Audit writer is **async/non-blocking** and **never silently drops** records.

---

## 9. Key takeaways

1. **Log the span, not the string** — a structured evidence set, one per step.
2. **Redact before you write; hash for proof; encrypt raw separately.**
3. **Append-only + hash-chain = tamper-evidence; WORM + anchoring = tamper-resistance.**
4. **Correlation ids make a multi-step agent reconstructable.**
5. **Pin model & prompt versions** or you can never reproduce or defend an output.
6. **Controls (kill switch, flags, HITL) turn observation into governance.**
7. **The audit system must audit access to itself.**

Now build it: see `exercise_01.md` and implement `exercise.py` → compare with
`solution.py`.
