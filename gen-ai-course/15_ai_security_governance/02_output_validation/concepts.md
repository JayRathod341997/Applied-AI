# Output Validation & Guardrails

## Overview

Input filtering (topic 01) stops bad *prompts*. It does **nothing** about what the
model actually *says back*. A perfectly benign prompt can still yield a hallucinated
fact, a leaked email address, a `<script>` tag, an API key the model memorised, or
JSON your parser chokes on. Output validation is the **independent, outbound** control
plane that inspects, sanitizes, and gates every model response *before* it reaches a
user, a database, a browser, or another service.

> **The one principle to internalise:** *An LLM's output is untrusted input to the
> next system.* Treat it exactly as you'd treat a raw HTTP body from the internet —
> validate the shape, strip the dangerous parts, and encode before use.

This maps to two OWASP LLM Top-10 risks:

| Risk | Name | What it means for outputs |
|------|------|---------------------------|
| **LLM02** | Sensitive Information Disclosure | Model emits PII, secrets, other users' data, internal system prompts |
| **LLM05** | Improper Output Handling | Downstream trusts model text as code/markup/SQL → XSS, SSRF, RCE, SQLi |
| LLM09 | Misinformation | Ungrounded / hallucinated claims presented as fact |

---

## Why outputs need their own validation

Input and output failures are **different threat classes** and neither catches the other:

```
 user ──▶ [input filter] ──▶  LLM  ──▶ [output validator] ──▶ downstream
          prompt injection,           hallucination, PII leak,
          jailbreak, PII-in           secret leak, XSS/SQLi,
                                       schema break, toxicity
```

- A clean prompt (`"summarise this ticket"`) can surface PII that lived in the context.
- A model can hallucinate a refund policy that never existed → real financial loss.
- RAG grounding does not guarantee the answer *used* the sources — models paraphrase
  from parametric memory and cite nothing.
- Function-calling / agent outputs become **executable actions**. An unvalidated
  `sql` field or `url` argument is an injection primitive.

### Failure modes to defend against

| Failure mode | Concrete example | Downstream blast radius |
|--------------|------------------|--------------------------|
| Hallucination | "Your policy covers this, refund $500." | Financial / legal liability |
| PII / data leakage | Response contains `jane@corp.com`, an SSN | Privacy breach (GDPR) |
| Secret leakage | Model echoes `AKIA…`, a bearer token | Account takeover |
| Insecure output (LLM05) | `<script>…</script>`, `javascript:` | Stored XSS in your UI |
| Unsafe code / SQL | `DROP TABLE users;` in a "generated query" | Data loss, SQLi |
| SSRF | Model returns `http://169.254.169.254/…` | Cloud metadata theft |
| Format violation | Truncated / non-JSON when caller `json.loads` | Crash, retry storms |
| Toxicity | Slurs, harassment in a support reply | Brand / safety incident |

---

## The output-validation gateway

Think of it as a **middleware chain**: the raw output flows through ordered validators,
each of which can pass, **sanitize** (mutate the output and continue), **retry**
(repairable — re-ask the model), or **block** (fail closed).

```
raw ─▶ secret ─▶ schema ─▶ pii ─▶ toxicity ─▶ unsafe-markup ─▶ groundedness ─▶ decision
        BLOCK     RETRY    SANITIZE  SANITIZE     SANITIZE        RETRY
                    │                                               │
                    └──────────────── repair hook (re-ask) ◀────────┘
```

Aggregate rule of thumb: **any BLOCK ⇒ BLOCKED**; **any unresolved RETRY ⇒ fail
closed**; **any applied SANITIZE ⇒ SANITIZED**; otherwise **ALLOW**.

Design decisions that matter:
- **Fail closed.** If a validator errors or retries are exhausted, do not ship the output.
- **Order for safety and cost.** Cheap/hard blocks (secrets) first; expensive checks
  (NLI groundedness, an LLM judge) last so you don't pay for them on already-doomed output.
- **Sanitize vs. block.** PII → redact and continue. Secrets/toxicity → block. Markup →
  encode. Never "redact" a secret and ship the rest; a partial leak is still a leak.

---

## 1. Structured output validation

The cheapest, highest-value guardrail. If you asked for JSON, *enforce* JSON.

### JSON Schema / Pydantic

```python
from pydantic import BaseModel, ValidationError

class Answer(BaseModel):
    answer: str
    confidence: float          # type coercion: "0.9" -> 0.9 on validation

try:
    obj = Answer(**json.loads(raw))     # raises on bad shape/type
except (json.JSONDecodeError, ValidationError) as e:
    feedback = str(e)                   # feed this back to the model
```

### The ret/repair loop (re-ask on failure)

Validation failure is usually **repairable** — send the error back and ask again:

```
attempt = 0
while attempt <= MAX_RETRIES:
    out = llm(prompt if attempt == 0 else prompt + f"\nYour last output was invalid: {err}")
    ok, err = validate(out)
    if ok: return out
    attempt += 1
raise Guardrail("could not produce valid output")   # fail closed
```

This is what libraries like **Guardrails AI** and **Instructor** automate.

### Constrained decoding (the stronger cousin)

Instead of validating *after* generation, constrain the tokens *during* generation so
invalid output is impossible. The decoder is masked to only sample tokens that keep the
string on a valid path through a grammar/JSON-Schema state machine (Outlines, `llama.cpp`
GBNF, vendor "JSON mode" / structured outputs). Trade-off: eliminates format retries, but
needs logit access and can subtly bias content. **Validate-and-repair works with any API;
constrained decoding needs a cooperating engine.** Use both when you can.

---

## 2. Groundedness / factuality for RAG

"The model had the context" ≠ "the answer is supported by the context." Enforce support.

| Technique | How it works | Cost | Catches |
|-----------|--------------|------|---------|
| **Citation enforcement** | Require `[n]` markers; every claim maps to a chunk | Cheap | Uncited assertions |
| **Lexical / numeric overlap** | Claim tokens & numbers must appear in sources | Cheap | Fabricated figures, off-topic |
| **NLI groundedness** | Entailment model scores `context ⊨ answer` | Medium | Paraphrased contradictions |
| **LLM-as-judge** | Second model rates support 0–1 | Expensive | Nuanced unsupported reasoning |

The **"answer must be supported by context"** pattern, in words: split the answer into
claims; for each claim, require an entailing source span; if any claim is unsupported →
retry with *"answer ONLY using the provided context; if unknown, say you don't know."*

Numbers are the highest-signal, cheapest tripwire — a figure in the answer that appears
in **no** source is almost always a hallucination:

```python
answer_nums = set(re.findall(r"\d+", re.sub(r"\[\d+\]", "", answer)))  # drop citations
if answer_nums - source_nums:
    return RETRY  # unsupported figure
```

---

## 3. PII redaction & DLP on outputs

Do not rely on "the model won't say it." Detect and redact on the way out.

- **Microsoft Presidio** (the reference tool): NER + regex + checksum recognisers,
  returns spans and confidence, supports custom recognisers and anonymisation operators
  (mask/hash/replace). Concept: *recognize → decide → anonymize*.
- A regex fallback covers the common, high-recall cases:

```python
RULES = [("EMAIL", r"[\w.%+\-]+@[\w.\-]+\.[A-Za-z]{2,}"),
         ("PHONE", r"\+?\d[\d\-\s().]{7,}\d"),
         ("SSN",   r"\b\d{3}-\d{2}-\d{4}\b")]
for label, pat in RULES:
    text = re.sub(pat, f"[REDACTED_{label}]", text)
```

Regex has false positives (order IDs look like phones) — tune per field, and prefer
Presidio's context-aware NER in production. Redaction is a **SANITIZE**, not a block.

### Secret / credential scanning

Different severity: a leaked key = **block**. Patterns: `AKIA…` (AWS), `sk-…`
(OpenAI-style), `-----BEGIN PRIVATE KEY-----`, `password=…`, high-entropy strings.
Reuse tooling ideas from **gitleaks / detect-secrets / trufflehog**. Never ship a
partially-redacted secret.

### Allowlist / denylist & toxicity

- **Denylist:** block/mask known-bad terms, competitor mentions, banned topics.
- **Allowlist:** for closed-domain bots, only permit outputs matching an expected shape
  (e.g. a set of intents) — far more robust than blocklisting.
- **Toxicity:** a classifier (Detoxify, Perspective API, a small guard model) scores the
  reply; mask or block above threshold. A denylist is the offline stand-in.

---

## 4. Insecure output handling (LLM05) — the deepest cut

> **Never trust LLM output as code, markup, or a query. Sanitize/encode at the boundary
> of the system that will interpret it.**

The context-appropriate encoding is what saves you — the same string is dangerous in one
sink and inert in another:

| Downstream sink | Attack if unhandled | Correct handling |
|-----------------|---------------------|------------------|
| HTML page | Stored XSS (`<script>`, `onerror=`) | HTML-encode; sanitize with a DOM allowlist (DOMPurify) |
| Shell | Command injection | Never `eval`/shell; use arg arrays, allowlist |
| SQL | SQL injection | Parameterised queries only — never string-format LLM text in |
| URL fetch / tool | SSRF to `169.254.169.254`, internal hosts | Allowlist egress hosts, block link-local/private IPs |
| Markdown | `javascript:` links, data-exfil images | Strip dangerous schemes/auto-loading images |
| File path | Path traversal `../../etc/passwd` | Canonicalise + confine to a base dir |

```python
import html
safe_for_html = html.escape(model_output)   # renders <script> as inert text
```

Agent/tool-calling outputs are the highest-risk sink: a model-produced `sql`, `path`, or
`url` argument is **attacker-influenceable data**. Validate every tool argument against a
schema and an allowlist before execution — that is output validation, too.

---

## Threat model in one line

*The model is a semi-trusted, occasionally-adversarial component inside your trust
boundary; its output crosses that boundary and must be validated like any external input.*

---

## Production checklist — output-validation gateway

- [ ] **Fail closed** — errors, timeouts, exhausted retries ⇒ do not ship the output.
- [ ] **Structured contract** enforced (JSON Schema / Pydantic) with a bounded
      **repair loop** (2–3 retries max), and constrained decoding where the engine allows.
- [ ] **PII/DLP** redaction on every response (Presidio or vetted regex), redact-and-continue.
- [ ] **Secret scanning** ⇒ hard block; alert; never partial-redact-and-ship.
- [ ] **Groundedness** for RAG: citation + NLI/overlap check; unsupported ⇒ retry or "I don't know".
- [ ] **Output encoding** per sink (HTML/SQL/shell/URL); tool arguments schema- + allowlist-validated.
- [ ] **Toxicity / policy** classifier with tuned thresholds; allowlist for closed domains.
- [ ] **Ordering**: cheap hard-blocks first, expensive judges last (cost + latency).
- [ ] **Observability**: log decision, triggered validators, severity, latency — *without*
      logging the raw sensitive content; emit metrics/alerts on block rate spikes.
- [ ] **Idempotent & versioned** rules; every change tested against a golden set + red-team suite.
- [ ] **Latency budget** measured; heavy checks async/sampled where user-facing.
- [ ] **Bypass-proof**: validator runs server-side, after the model, before *any* sink —
      not in the client, not optional.
