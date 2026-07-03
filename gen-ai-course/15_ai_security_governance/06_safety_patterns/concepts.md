# Reusable Safety Patterns for AI Agents

> **Capstone of Module 15.** The previous five topics each built one control
> (input filtering, output validation, misuse protection, policy-as-code, audit).
> This topic is the *synthesis*: how a Senior AI Security Engineer packages those
> controls into **reusable patterns** so that *every* agent in the org inherits
> them by default — not by copy-paste, not by hoping each team remembers.

---

## 1. Why this matters (the threat framing)

An "AI agent" is an LLM with **tools** and **autonomy**. That combination turns a
text bug (a bad completion) into a *systems* bug (a bad *action*): sending email,
issuing refunds, running code, calling internal APIs. The moment a model can act,
prompt injection stops being a curiosity and becomes **remote code/action execution
driven by attacker-controlled text**.

Two facts drive everything in this topic:

1. **You cannot fully "solve" prompt injection at the model layer.** There is no
   reliable way to make the model always distinguish trusted instructions from
   untrusted data. So you engineer the *surrounding system* to contain the blast
   radius. (This is the same mindset as memory-safety: assume the parser is
   fallible, sandbox it.)
2. **N teams shipping N agents will not each re-derive good security.** If security
   lives in a doc, adoption is ~0%. If it lives in a library the platform ships,
   adoption is ~100% *by default*. **Patterns are how security scales across teams.**

The JD phrase is literally *"Define safety patterns used across all AI agents"* and
*"Advise on AI risk scenarios and failure modes"* — that is this file.

---

## 2. The centralized AI Security Gateway pattern

**Core idea:** every AI call — from any agent, any team — flows through *one*
enforcement plane with the same five stages. Nothing talks to the model directly.

```
                        ┌─────────────────────────────────────────────┐
   user / tool output   │            AI SECURITY GATEWAY              │
   (untrusted text) ───►│                                             │
                        │  1. INPUT FILTER   (prompt-injection,       │
                        │                     PII, length, encoding)  │
                        │        │ block ────────────────► DENY + audit│
                        │        ▼                                     │
                        │  2. POLICY CHECK   (allowlisted action?     │
                        │                     who? risk tier?)        │
                        │        │ escalate ──► HUMAN REVIEW ──┐       │
                        │        ▼                             │       │
                        │  3. LLM CALL       (the model/agent) │       │
                        │        ▼                             │       │
                        │  4. OUTPUT VALIDATION (secrets, PII, │       │
                        │        │            exfil URLs,      │       │
                        │        │            schema, grounding)│      │
                        │        ▼                             ▼       │
                        │  5. AUDIT LOG  (immutable, hash-chained,     │
                        │                 decision + reason + hashes)  │
                        └───────────────────────┬─────────────────────┘
                                                ▼
                                      ALLOW → return output
```

Each stage returns one of **`ALLOW` / `BLOCK` / `ESCALATE`**. The gateway is
`fail-closed`: an *error* inside any stage is treated as `BLOCK`.

### Centralized gateway vs. per-app libraries

| Dimension | Per-app library (copy the code) | Centralized gateway (shared plane) |
|---|---|---|
| Adoption | Opt-in, drifts per team | Default; agents can't bypass it |
| Fix a bypass | N PRs across N repos | One deploy, everyone protected |
| Policy updates | Redeploy every app | Push policy-as-code centrally |
| Observability | N log formats | One audit schema, one dashboard |
| New attack signature | Race N teams | Ship once |
| Latency / coupling | Lower, in-process | One more hop; must be HA |
| Team autonomy | High | Lower (guardrails are mandatory) |

**Practical answer: do both.** Ship a **shared SDK** (a decorator/middleware —
this topic's exercise) that runs in-process *and* points at a **central policy +
audit service**. Teams get low latency and local defenses; security gets a single
control point for policy and telemetry. The gateway is a *pattern*, not necessarily
a single network box.

---

## 3. Defense in depth & the fail-closed decision

**Defense in depth** = independent, overlapping layers so that one bypassed control
is not game over. Input filtering *and* least-privilege tools *and* output
validation *and* audit. An injection that beats the input filter still faces a
sandbox, an allowlist, and an output scrubber.

### Fail-closed vs fail-open

When a guardrail itself errors or times out, what do you do?

| | **Fail-closed** (deny) | **Fail-open** (allow) |
|---|---|---|
| On guardrail error | Block the request | Let it through |
| Right for | Security-critical & high-impact actions (payments, code exec, data export) | Availability-critical, low-risk read paths |
| Risk | False positives → lost availability | A single guardrail outage disables *all* protection |

> **Default to fail-closed for anything that acts.** Fail-open is a deliberate,
> logged exception for low-risk paths — never the accident you get from an
> unhandled exception. In the exercise, `fail_closed=True` turns any stage error
> into a `BLOCK`.

### Graceful degradation & human fallback

Failing closed must not mean a stack trace to the user. Degrade gracefully:

- Guardrail down → serve a **safe canned response** ("I can't complete that right
  now") and route the request to a **human fallback / review queue**.
- High-risk action → **human-in-the-loop** approval *before* execution, not after.
- Never leak internal errors, prompts, or secrets in the failure path.

---

## 4. The reusable patterns catalog

These are the building blocks you name in an interview and wire into the SDK.

### (1) Guardrail middleware / decorator
Wrap every agent call in a function that runs the 5 stages. One decorator ⇒ every
agent inherits input filter + policy + output validation + audit. **This is the
exercise.** Think Express/Django middleware, but for LLM calls.

```python
@secure_agent()          # <- the whole gateway, in one line
def support_agent(ctx): ...
```

### (2) Dual-LLM: privileged vs. quarantined (Simon Willison)
The strongest structural defense against prompt injection. Split the work:

- **Privileged LLM** — can call tools/act, but **never sees untrusted content**.
- **Quarantined LLM** — reads the untrusted data (web page, email, doc) but **has
  no tools** and can only return *structured, validated* results.

The privileged model orchestrates using *symbolic references* ("summarize
`$VAR1`") and never ingests raw attacker text. Injection in the untrusted data
can corrupt the *summary*, but cannot make the privileged model *act*.

```
untrusted doc ─► [Quarantined LLM: no tools] ─► structured result ($VAR1)
                                                       │ (validated schema)
user request ──► [Privileged LLM: has tools] ──► acts on $VAR1, never raw text
```

### (3) Least-privilege tools + human-in-the-loop
- Give each agent the **minimum tool set** for its job (an FAQ bot has no
  `send_email`). Scope tool *credentials* to the *user's* permissions, not a
  god-mode service account (defeats the **confused deputy**).
- Gate **high-risk, irreversible actions** (payments, deletes, external sends)
  behind explicit human approval.

### (4) Sandboxing tool execution
Run any model-driven code/tool in an isolated, ephemeral environment: no ambient
credentials, **egress allowlist only**, resource limits, non-persistent FS. If the
model gets pwned, it's pwned inside a box with nothing to steal and nowhere to send.

### (5) Allowlisted actions (and destinations)
Default-deny. The model may only invoke actions on an explicit allowlist, send to
allowlisted domains/recipients, and touch allowlisted resources. Everything else is
`BLOCK` — including model-invented tool names.

### (6) Circuit breaker + kill switch
- **Circuit breaker**: auto-trip an agent/tool when error rate, block rate, spend,
  or anomaly score crosses a threshold — degrade to safe mode.
- **Kill switch**: a single flag/feature-toggle that instantly disables an agent or
  capability org-wide. Test that you can actually pull it in <5 minutes.

### (7) Canary / honeypot
- **Canary tokens**: embed a unique secret string in the system prompt or a fake
  "secret" document. If it ever appears in output or egress, you *know* you were
  injected/exfiltrated → alert.
- **Honeypot tools**: expose a tempting fake tool (`export_all_users`). Any call to
  it is, by definition, malicious → alert + block.

### (8) Content provenance / signing
Sign and tag data by trust level so downstream stages know what's untrusted. Track
provenance of prompts, RAG chunks, and tool outputs; verify signatures on plugins
and prompt templates (supply chain). Emerging standards: **C2PA** for media
provenance. Provenance is what makes "spotlighting"/trust-labeling reliable.

---

## 5. AI risk scenarios & failure modes (advise on these)

The consulting half of the JD. Know the scenario, the impact, and the *control*.

| # | Scenario / failure mode | OWASP LLM | Impact | Primary control(s) |
|---|---|---|---|---|
| 1 | **Direct prompt injection** → jailbreak, policy bypass | LLM01 | Harmful/off-policy output | Input filter, output validation, dual-LLM |
| 2 | **Indirect injection** (poisoned web page / email / RAG doc) → **data exfil via tools** | LLM01 | Secrets/PII sent to attacker | Quarantined LLM, egress allowlist, output URL guard, canary |
| 3 | **Excessive agency** (agent has more tools/permissions than needed) | LLM06/LLM08 | Unintended high-impact actions | Least privilege, allowlisted actions, human-in-loop |
| 4 | **Confused deputy** (agent uses *its* privileges on attacker's behalf) | LLM06 | Privilege escalation / IDOR-at-scale | Scope creds to end-user, per-request authz |
| 5 | **Supply chain** of prompts/plugins/models | LLM03/LLM05 | Backdoored behavior, poisoned templates | Sign & pin prompts/plugins, provenance, review |
| 6 | **Cascading multi-agent failure** (one agent's bad output is another's trusted input) | LLM05/LLM08 | Error/attack amplification, loops | Validate *between* agents, circuit breaker, loop/step limits |
| 7 | **Over-reliance / automation bias** (humans rubber-stamp AI) | LLM09 | Bad decisions shipped, review theater | Show uncertainty, sample-audit approvals, friction on high-risk |
| 8 | **Unbounded consumption** (token/spend/loop flooding) | LLM10 | DoS, cost blowout | Rate limits, budgets, circuit breaker, step caps |

> **Two failure modes people forget:** (6) *cascading* — never treat another
> agent's output as trusted; re-validate at every hop. (7) *automation bias* — a
> human-in-the-loop that approves everything in 2 seconds is not a control. Add
> friction and audit the approvers.

---

## 6. Packaging patterns as a shared internal SDK

Adoption is the real deliverable. Turn the patterns into a library the platform
ships, so agents inherit controls **by default**.

**Shape of the SDK**
- A `@secure_agent` decorator / middleware (the enforcement plane).
- Pluggable stages: `InputFilter`, `PolicyEngine` (policy-as-code, e.g. OPA/Rego),
  `OutputValidator`, `AuditSink`, `HumanReview` — swap implementations, keep the
  contract.
- **Secure defaults**: fail-closed, deny-unknown-actions, audit-on, PII-off.
- Central config: signatures, allowlists, and policies pulled from a service so a
  fix ships once.

**Testing safety patterns** (you must be able to prove they work)
- **Unit tests per stage**: known-malicious inputs must `BLOCK`; benign must `ALLOW`.
- **Red-team / attack corpus** as regression tests: every past bypass becomes a
  permanent test case. Re-run in CI.
- **Fail-closed tests**: force each stage to raise → assert `BLOCK`, not leak.
- **Metrics gates**: track false-positive (benign blocked) and false-negative
  (attack allowed) rates; block releases that regress them.

**Adoption strategy**
1. Make the secure path the **easiest** path (one decorator, great docs).
2. **Secure by default**; opting *out* requires a signed exception + review.
3. Provide a golden-path template repo so new agents start compliant.
4. **Enforce in CI/CD**: a gate that fails builds of agents not wrapped by the SDK.
5. Dashboards + a security champion per team; celebrate blocked attacks.

---

## 7. Production checklist

- [ ] Every agent call routes through the gateway (no direct model access).
- [ ] Five stages present: input filter → policy → LLM → output validation → audit.
- [ ] **Fail-closed** by default; fail-open paths are explicit, logged, low-risk.
- [ ] Graceful degradation: safe canned response, no stack traces to users.
- [ ] Least-privilege tools; credentials scoped to the *end user*.
- [ ] High-risk/irreversible actions require **human-in-the-loop** before executing.
- [ ] Tool execution is **sandboxed** with an **egress allowlist**.
- [ ] Actions, tools, and destinations are **allowlisted** (default-deny).
- [ ] **Circuit breaker** on error/block/spend; a tested **kill switch** exists.
- [ ] **Canary tokens** in prompts/secret docs; alert on appearance.
- [ ] Prompts, plugins, and models are **signed/pinned**; provenance tracked.
- [ ] Multi-agent hops **re-validate** inputs; step/loop/budget limits enforced.
- [ ] Audit log is immutable/hash-chained: decision + reason + input/output hashes.
- [ ] Red-team corpus runs in CI; FP/FN rates are tracked and gated.
- [ ] Controls shipped as a **shared SDK**; CI blocks unwrapped agents.

---

## 8. Safety maturity model

| Level | Name | What it looks like | Key gap |
|---|---|---|---|
| 0 | **Ad hoc** | Each team hand-rolls (or skips) guardrails; no audit | No consistency, no visibility |
| 1 | **Centralized gateway** | One shared enforcement plane; all calls flow through it; unified audit | Rules are hard-coded, changing them = redeploy |
| 2 | **Policy-as-code** | Guardrails/allowlists/risk tiers expressed as versioned policy (OPA/Rego), pushed centrally | Static; doesn't learn from new attacks |
| 3 | **Continuous red-team** | Automated adversarial testing in CI, canaries in prod, FP/FN dashboards, auto-updating signatures, feedback loop into policy | Cost & sophistication; this is the target state |

**Trajectory:** 0 → 1 is *centralize*. 1 → 2 is *externalize the rules*. 2 → 3 is
*make it adaptive*. Interview-ready one-liner: *"I'd move the org from ad-hoc
guardrails to a centralized fail-closed gateway, express its rules as policy-as-code,
and close the loop with continuous automated red-teaming."*

---

## 9. Interview soundbites

- *"Prompt injection isn't fully solvable at the model layer — so I contain blast
  radius with least privilege, sandboxing, and output validation, not just input
  filtering."*
- *"Security scales through patterns: a shared SDK/gateway means a fix ships once and
  every agent inherits it — copy-paste libraries drift to zero adoption."*
- *"Default fail-closed for anything that acts; fail-open is a deliberate, logged
  choice for low-risk read paths."*
- *"Dual-LLM keeps the tool-using model away from untrusted text; the model that
  reads attacker content has no tools."*
- *"A human-in-the-loop that approves everything in two seconds is automation bias,
  not a control — add friction and audit the approvers."*
