# Misuse Protection & Abuse Prevention

> Prompt filtering stops *bad content*. Misuse protection stops *bad usage patterns*:
> the same API, used at the wrong scale, frequency, cost, or intent, by the wrong actor.
> This is the runtime-security discipline that turns a demo into a service that survives contact with the internet.

---

## 1. Why this matters

Your LLM endpoint is a paid, capable, internet-facing compute primitive. That makes it a target:

- **It costs money per call.** An attacker who can call it for free (or on your dime) can burn your budget — a
  `$0.01`/request endpoint at 1000 rps is `$864/day` of someone else's fun.
- **It is a capability.** Free jailbreakable inference is a resource to resell, to generate spam/phishing/malware, or to
  distill into a competitor model.
- **It is stateful and privileged.** It touches your data (RAG stores), your tools (function calling), and your users'
  accounts. Abuse here is lateral movement.

Prompt filtering and output validation (topics 01–02) are *per-request* content checks. Misuse protection is the
*cross-request, cross-user, cross-time* layer: it reasons about **who**, **how much**, **how fast**, and **how often bad**.

---

## 2. Threat model of misuse

Map every control back to a concrete abuse category. Several map directly to the **OWASP LLM Top 10**.

| # | Abuse category | What it looks like | OWASP / ref | Primary control |
|---|----------------|--------------------|-------------|-----------------|
| 1 | **Harmful content generation** | Repeated jailbreaks to produce malware, CSAM, weapons, disinfo | LLM01 Prompt Injection | Content filter + **abuse-score suspend** |
| 2 | **Mass automation / scraping** | Bot farms harvesting outputs, dataset scraping, review spam | — | **Rate limit** + bot detection + velocity checks |
| 3 | **Cost / DoS abuse** | Huge context windows, `max_tokens` bombs, infinite agent loops, flooding | LLM04 (Model DoS) | **Cost budget** + spend caps + circuit breaker |
| 4 | **Model extraction / theft** | Systematic querying to distill/clone your model or steal the system prompt | **LLM10 Unbounded Consumption / Model Theft** | Query-pattern anomaly + rate + watermarking |
| 5 | **Data exfiltration** | Coaxing the model to dump RAG docs, PII, secrets, other tenants' data | LLM06 Sensitive Info Disclosure | Output validation + per-tenant isolation + egress checks |
| 6 | **Account takeover (ATO)** | Stolen API keys/tokens used from new geos/patterns | — | Auth + **behavioral fingerprinting** + velocity |
| 7 | **Insider misuse** | Employee over-scopes an entitlement, exports data, tests jailbreaks in prod | — | Least-privilege IAM + audit + approval workflows |

**Key mental model — the abuse funnel:**

```
        many requests
              |
      [ Authn / Authz ]  --reject--> unauthenticated / out-of-scope
              |
      [ Rate limiter  ]  --THROTTLE-> too fast (burst)
              |
      [ Cost budget   ]  --BLOCK----> too expensive (spend cap)
              |
      [ Content filter]  --strike---> harmful/jailbreak  --+
              |                                            |
      [ Abuse score   ]  --SUSPEND--< accumulates strikes -+
              |
          served (ALLOW)
```

Each layer is cheap-to-expensive left-to-right. Reject early: never spend a `$0.02` inference call on a request you were
going to block for being unauthenticated or over-budget.

---

## 3. Rate limiting & quota controls

Rate limiting answers **"how fast?"**. You limit multiple dimensions simultaneously:

| Dimension | Example limit | Why |
|-----------|---------------|-----|
| Requests / sec | 10 rps per API key | Stops flooding |
| Tokens / min | 100k TPM per tenant | Real LLM cost is tokens, not requests |
| Cost / day | `$50/day` per user | Hard financial blast-radius cap |
| Concurrency | 5 in-flight per user | Stops parallel loop attacks |
| Scope | per-user **and** per-tenant **and** per-IP | Defense in depth; one dimension alone is bypassable |

> **Rule:** limit on the axis the attacker actually consumes. For LLMs that is **tokens and dollars**, not request count.
> A single request with a 200k-token context can cost 1000× a normal one.

### 3.1 Sliding window vs token bucket

| | Fixed window | Sliding window (log) | **Token bucket** |
|---|---|---|---|
| Idea | N per calendar minute | N within trailing 60s | Bucket of N tokens, refills at rate R |
| Bursts | Allows 2N at window edge (boundary bug) | Smooth | **Allows controlled bursts up to capacity** |
| Memory | O(1) counter | O(N) timestamps per user | **O(1)** (level + timestamp) |
| Best for | Coarse quotas | Precise fairness | **API gateways** — the industry default |

**Token bucket** is the standard because it is O(1) memory, allows legitimate short bursts (a user pasting 5 docs at once),
yet enforces a strict long-run average `R`. That is why the exercise implements it.

```python
# Minimal token bucket (see solution.py for the full version)
def try_consume(self, now, cost=1.0):
    elapsed = now - self.last_refill
    self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_s)
    self.last_refill = now
    if self.tokens >= cost:
        self.tokens -= cost
        return True, 0.0                     # ALLOW
    retry_after = (cost - self.tokens) / self.refill_per_s
    return False, retry_after                # THROTTLE  (HTTP 429 + Retry-After)
```

### 3.2 Circuit breakers & spend caps

- **Spend cap:** a hard dollar ceiling per user/tenant/window. When `spend + est_cost > cap` → **BLOCK**. This is the
  financial equivalent of a fuse. Track *estimated* cost pre-call, reconcile with *actual* token usage post-call.
- **Circuit breaker:** a *system-wide* switch. If aggregate error rate, latency, or spend velocity crosses a threshold,
  trip open and shed load (return 503) instead of melting down. Half-open after a cooldown to test recovery.

```
CLOSED  --(spend velocity > $X/min)-->  OPEN (shed load, page on-call)
  ^                                        |
  |                                   (cooldown 60s)
  +-------(probe succeeds)------ HALF-OPEN -+
```

**Failure mode:** rate limits stored per-process don't work behind a load balancer — user hits 3 replicas, gets 3× the
limit. Use a **shared store** (Redis) for counters/buckets in production, or sticky routing.

---

## 4. Abuse detection

Rate limits are static thresholds. **Detection** finds abuse *below* the threshold — the patient attacker.

| Technique | Signal | Catches |
|-----------|--------|---------|
| **Velocity checks** | Requests/min vs the user's own baseline | Sudden bot-like spikes |
| **Anomaly detection** | Deviation on features (geo, token size, timing entropy, endpoint mix) | Extraction, ATO |
| **Reputation scoring** | Historical good/bad ratio per key/IP/user | Known-bad actors |
| **Repeat-jailbreak tracking** | Count of blocked/flagged prompts per user | Determined adversaries (→ suspend) |
| **Behavioral fingerprinting** | Request-timing entropy, prompt-template reuse, UA/TLS fingerprint | Bot farms, shared stolen keys |
| **Honeypot / canary prompts** | A fake "secret" seeded in the system prompt or docs | Exfiltration attempts (if the canary leaks, you know) |

**Abuse-score pattern (core of the exercise):** maintain a per-user integer. Increment on every blocked/jailbreak
attempt; **decay** it over time so one bad day is forgiven; **auto-suspend** when it crosses a threshold. Suspension is
*sticky* until human review — this is your automated, graduated response.

```python
def add_strike(self, now, weight=1):
    self._decay(now)               # forgive old strikes
    self.score += weight
    if self.score >= self.suspend_threshold:
        self.suspended = True      # sticky; needs manual reset
    return self.suspended
```

**Canary example:** seed the system prompt with `SECRET_CANARY = "zx9-do-not-reveal"`. If that token ever appears in an
output or an attacker's prompt, you have caught a system-prompt-extraction attempt red-handed — log, strike, alert.

**Failure modes:** anomaly detectors drift (retrain), have false positives (never hard-ban solely on a score — throttle
first, suspend on repeated *confirmed* violations), and can be gamed by slow-and-low attackers (combine multiple signals).

---

## 5. Authentication / authorization context

Misuse controls are meaningless without knowing **who** the caller is and **what they may do**.

| Layer | Mechanism | Note |
|-------|-----------|------|
| **Authentication** | API keys, OAuth tokens, mTLS | Identity. Keys must be revocable + rotatable + scoped |
| **Authorization** | Scoped tokens, per-use-case entitlements | *This key may call `summarize` but not `code-exec`* |
| **Entitlement provisioning** | IAM + approval workflows | Who granted the scope, when, approved by whom |

- **Scoped tokens:** a token carries claims — allowed endpoints, model tier, rate/cost tier, tenant. The guard reads the
  scope, not a global config. A leaked read-only key can't be used to run expensive agents.
- **Per-use-case entitlements:** don't grant "LLM access"; grant "customer-support-summarization at tier-2 rate limits."
  Least privilege applied to model capability.
- **Enterprise IAM tie-in (high level):** in large orgs, entitlements are *provisioned and reviewed* through IGA tooling
  like **Saviynt** or **ServiceNow** — a request → approval → time-bound grant → periodic access recertification flow.
  Your runtime guard *enforces* what those workflows *granted*. The audit trail (topic 05) proves who approved what.

**Insider angle:** the strongest control here is least privilege + audit. An insider with an over-broad entitlement is
just as dangerous as an external attacker — provision narrowly, log everything, recertify regularly.

---

## 6. Red-teaming & abuse testing

You cannot claim your defenses work without adversarially testing them — ideally **in CI, as a release gate**.

| Practice | What it is |
|----------|-----------|
| **Adversarial eval in CI** | Run a corpus of jailbreak/abuse prompts against the guarded system on every build |
| **Jailbreak pass-rate gate** | If > X% of known attacks succeed, **fail the release** (like a failing test) |
| **MITRE ATLAS** | Adversarial ML threat matrix — TTPs for attacking AI systems (the "ATT&CK for ML") |
| **HarmBench-style corpora** | Standardized harmful-behavior prompt sets to measure refusal robustness |
| **Automated red-team agents** | LLM-driven attackers that mutate prompts to find new bypasses |

```python
# Release gate sketch — runs offline against your guard + filter stack
attacks = load_corpus("jailbreaks.jsonl")          # HarmBench / internal
succeeded = sum(1 for a in attacks if attack_bypasses_defenses(a))
pass_rate = succeeded / len(attacks)
assert pass_rate <= 0.02, f"Jailbreak pass-rate {pass_rate:.1%} exceeds 2% gate"
```

Track jailbreak pass-rate as a **trend over releases**. A regression means a model/prompt/filter change weakened you.

---

## 7. Incident response for AI misuse

When abuse gets through, run the standard IR loop — adapted for AI:

```
DETECT ──► CONTAIN ──► ERADICATE ──► RECOVER ──► LEARN
  |           |            |            |          |
 alerts    kill switch   patch the    restore    postmortem +
 anomaly   / guardrail   filter/policy service    new eval case
 canary    hot-patch     root cause    to normal  added to CI
```

| Phase | AI-specific action |
|-------|--------------------|
| **Detect** | Canary fired / abuse-score spike / cost anomaly / red-team report |
| **Contain** | **Kill switch** (disable endpoint/feature), **guardrail hot-patch** (push a new filter rule without redeploy), suspend the actor |
| **Eradicate** | Fix root cause: patch the filter, tighten the prompt, add the bypass to the blocklist |
| **Recover** | Re-enable, monitor closely, un-suspend cleared users |
| **Learn** | Postmortem; **add the exploit to your CI eval corpus** so it can never regress |

**Key metric — Mean-Time-To-Policy-Update (MTTPU):** how long from *detecting* a new abuse pattern to a *deployed*
guardrail/policy change that stops it. This is the AI-security analog of MTTR. Guardrail rules should be **hot-patchable**
(config/data, not a code deploy) precisely to minimize MTTPU — minutes, not the next release train.

---

## 8. Production checklist

- [ ] **Multi-dimensional limits:** per-user + per-tenant + per-IP, on requests **and tokens and dollars**.
- [ ] **Token bucket** rate limiter backed by a **shared store** (Redis) so it holds across replicas.
- [ ] **Hard spend caps** with pre-call estimate + post-call reconciliation; alert at 80%.
- [ ] **Circuit breaker** on aggregate spend velocity / error rate (trip → shed load → page).
- [ ] **Abuse-score tracker** with decay + auto-suspend; suspension requires human review to lift.
- [ ] **Canary/honeypot** tokens seeded in system prompts and RAG docs; alert on leak.
- [ ] **Behavioral + velocity anomaly detection** feeding the abuse score (throttle first, suspend on confirmation).
- [ ] **Scoped tokens / per-use-case entitlements**; least privilege; keys revocable + rotatable.
- [ ] **Entitlement provisioning** via IAM/IGA (Saviynt/ServiceNow) with approval + recertification.
- [ ] **Red-team corpus in CI** with a **jailbreak pass-rate release gate**; track the trend.
- [ ] **IR runbook** with a **kill switch** and **hot-patchable guardrails**; measure **MTTPU**.
- [ ] **Everything logged** (topic 05) — every THROTTLE/BLOCK/SUSPEND is an audit event.
- [ ] **Fail closed** on the guard itself: if the rate-limit store is down, degrade to conservative local limits, not "allow all."

---

## 9. Key takeaways

1. Misuse protection is the **cross-request** layer: who, how much, how fast, how often bad.
2. Limit on **tokens and dollars**, not just request count — that is what LLM abuse actually consumes.
3. **Token bucket** = the default rate limiter (O(1), burst-friendly, strict average).
4. Combine **rate + cost + abuse-score** for graduated response: **ALLOW → THROTTLE → BLOCK → SUSPEND**.
5. Reject early and cheaply; **fail closed** on the guard.
6. Prove it with **adversarial CI gates**; respond with **kill switches + hot-patches**; measure **MTTPU**.
