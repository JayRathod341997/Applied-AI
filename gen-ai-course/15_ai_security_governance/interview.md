# AI Security & Governance Engineering — Interview Questions

Interview prep for the **Senior AI Security & Governance Engineer** role — embedding responsible-AI
controls into runtime systems through code and automation. Fundamentals first (per topic), then a
**Senior Deep Dive** for staff-level system design, trade-offs, failure modes, and leadership.

---

## 1. Prompt Filtering & Input Defense

### Q1: What is prompt injection, and how is it different from a jailbreak?
**Answer:** **Prompt injection** is when untrusted input contains instructions that the model follows as if they
came from the developer — subverting the intended task. **Direct** injection comes from the user
("ignore previous instructions…"); **indirect** injection is hidden in content the model ingests (a web page,
a RAG document, an email) and triggers when processed. A **jailbreak** specifically aims to bypass safety
guardrails to elicit disallowed content (e.g., DAN-style role-play). Injection is the broader class; jailbreaks
are a goal you might achieve via injection. It's **OWASP LLM01**, the #1 LLM risk, and has no complete fix —
you manage it with layered defenses.

### Q2: Why is input filtering necessary but not sufficient?
**Answer:** Filters reduce attack volume but attackers evade them via translation, base64/hex encoding,
homoglyphs, typos, token smuggling, and novel phrasings — so any single detector has false negatives. Indirect
injection also arrives through *trusted* data channels a filter may not inspect. Therefore input filtering is one
layer of **defense-in-depth**: you also need output validation, least-privilege tool permissions, and audit. If
you only filter input, one bypass = full compromise.

### Q3: Name concrete input-defense techniques.
**Answer:** Instruction/data separation with delimiters; **spotlighting / data-marking** (encode or tag untrusted
data so the model treats it as data, not instructions); denylist/allowlist and regex signatures for known
injection phrases; classifier-based detection (Rebuff, Lakera, Prompt Shields); perplexity/anomaly signals;
canary tokens to detect system-prompt leakage; decode-and-rescan for encoded payloads; and LLM-as-judge input
screening. Combine into a scored ALLOW/FLAG/BLOCK decision rather than a single boolean.

---

## 2. Output Validation & Guardrails

### Q4: Why validate output if you already filtered the input?
**Answer:** Because failures originate in the model, not just the input: **hallucinations**, **PII/data leakage**,
toxic content, and **insecure output** (SQL/HTML/code the model emits that harms a downstream system). OWASP
**LLM02 (Insecure Output Handling)** treats model output as **untrusted input to the next system** — you must
validate, sanitize, and encode it before use. Input and output are independent failure domains.

### Q5: How do you enforce structured output reliably?
**Answer:** Define a schema (JSON Schema / **Pydantic**), parse the model output, validate, and on failure run a
**repair loop** — re-ask the model with the validation errors, or use constrained/JSON-mode decoding to force
valid tokens. Cap retries and fall back to a safe default or human review. Never `eval()` or trust the shape
blindly.

### Q6: How do you check a RAG answer is grounded?
**Answer:** Enforce **citations** (every claim maps to a retrieved chunk), run an **NLI/groundedness** check
(does the context entail the answer?), and reject or flag ungrounded responses. Vendors call this groundedness
detection (Azure AI Content Safety, Bedrock). Also redact PII/secrets on the way out via a DLP pass
(e.g., Microsoft Presidio + regex for secrets).

---

## 3. Misuse Protection & Abuse Prevention

### Q7: What abuse vectors are specific to LLM apps and how do you throttle them?
**Answer:** Harmful-content generation, mass automation/scraping, **cost/DoS abuse** (expensive tokens), **model
extraction** (LLM10 — querying to clone behavior), and data exfiltration. Controls: per-user/tenant/IP **rate
limits** (token bucket or sliding window), **token & cost budgets** with hard spend caps, circuit breakers,
velocity/anomaly checks, and an **abuse score** that increments on blocked/jailbreak attempts and auto-suspends
past a threshold.

### Q8: How does red-teaming fit into misuse protection?
**Answer:** You quantify resistance by running adversarial evals in CI against jailbreak corpora (HarmBench,
internal libraries), tracking **jailbreak pass-rate as a release gate**. Structured human red-teams run
periodically; findings feed guardrail/policy updates. The leadership metric is **mean time to policy update
after a red-team finding** — it shows whether the governance loop actually closes. Reference frameworks:
**MITRE ATLAS** for the adversarial-ML tactic taxonomy.

---

## 4. Policy-as-Code & Rule Engines

### Q9: What is policy-as-code and why is it better than a policy document?
**Answer:** Policy-as-code expresses governance rules as **versioned, testable, executable** artifacts that are
enforced automatically at runtime — not prose humans may ignore. Benefits: single source of truth, code review +
approval workflow on every change, unit-testable rules, automatic enforcement, and an audit trail of *who changed
which rule when*. A doc describes intent; policy-as-code *is* the control.

### Q10: Explain the PEP/PDP/PIP model with an OPA example.
**Answer:** The **Policy Enforcement Point (PEP)** is where you intercept the request (your AI gateway). It sends
context to the **Policy Decision Point (PDP)** — e.g., **Open Policy Agent (OPA)** evaluating **Rego** — which
returns allow/deny. A **Policy Information Point (PIP)** supplies extra data the decision needs (user entitlements,
risk tier). Example Rego:
```rego
package ai.gateway
default allow = false
allow {
  input.use_case_approved
  not input.contains_pii            # no PII to external models
  input.risk_tier != "high"         # high-risk requires human review
}
require_review { input.risk_tier == "high" }
```
The app stays free of policy logic; policy changes ship without redeploying the app.

### Q11: How does this tie into approval workflows (ServiceNow/Saviynt/IAM)?
**Answer:** Policy changes and high-risk use-case launches route through **change-approval workflows** — a
ServiceNow change request or Saviynt access/entitlement request with model-risk (MRM) sign-off before the rule or
entitlement goes live. IAM provides the identity/entitlement context the PDP consumes (which user/app may call
which model for which use-case). Governance = *policy enforced in code* + *access granted through approvals*.

---

## 5. Audit, Traceability & Control Mechanisms

### Q12: What must you log for every AI interaction, and why?
**Answer:** Request/response (PII-redacted), user & app/agent identity, pinned model + version, prompt/system-prompt
version, retrieval sources, **guardrail and policy decisions**, token counts, cost, latency, and a **correlation
ID**. Why: regulatory evidence (EU AI Act logging, GDPR Art. 22, SR 11-7 MRM), incident forensics, reproducibility,
and accountability. Without it you can't answer *"why did the AI do that?"* — which regulators and incident reviews
demand.

### Q13: How do you make audit logs tamper-evident?
**Answer:** Append-only storage plus **hash-chaining** — each record includes a hash of the previous record, so
altering any record breaks the chain and is detectable. Combine with **WORM** storage, restricted (least-privilege)
access, and separation of redacted logs (searchable) from encrypted raw payloads. Add retention policies matching
regulation. This gives an immutable, verifiable trail.

---

## 6. Safety Patterns for AI Agents

### Q14: Why centralize controls in an AI security gateway instead of per-app libraries?
**Answer:** A gateway is a **single enforcement plane** every AI call flows through, so a policy deployed once
protects all apps — versus asking each team to correctly wire safety libraries (they won't, uniformly). It
centralizes input filtering, policy checks, output validation, and audit, gives consistent telemetry, and lets you
hot-patch a guardrail org-wide during an incident. Trade-off: it's a latency hop and a single point of failure, so
you engineer it for HA and fail-closed behavior.

### Q15: Fail-open or fail-closed when a guardrail errors?
**Answer:** For security controls, **fail-closed** by default — if the filter/validator/policy engine is
unavailable, block or degrade to a safe fallback (cached safe response, human handoff), never pass the request
through unchecked. Fail-open trades safety for availability and is only acceptable for low-risk, non-sensitive
use-cases with explicit sign-off. Always make the choice explicit per use-case and log it.

### Q16: Advise on the top AI risk scenarios and their controls.
**Answer:**
| Scenario | OWASP | Impact | Primary control |
|----------|-------|--------|-----------------|
| Prompt injection → data exfiltration via tools | LLM01 | Data breach | Input filter + least-privilege tools + output DLP |
| Insecure output handling | LLM02 | Downstream XSS/SQLi | Output sanitization/encoding, treat output as untrusted |
| Sensitive data disclosure | LLM06 | PII/IP leak | PII redaction in/out, data minimization |
| Excessive agency | LLM08 | Unauthorized actions | Human-in-the-loop, allowlisted actions, scoped permissions |
| Model DoS / cost abuse | LLM04 | Outage/spend | Rate limits, budgets, circuit breakers |
| Model theft | LLM10 | IP loss | Auth, rate limits, anomaly detection |

---

## Senior Deep Dive: AI Security & Governance Engineering

> *For senior/staff roles embedding responsible-AI controls into runtime systems at enterprise scale.
> Interviewers test whether you can design an org-wide enforcement plane, make hard fail-open/closed and
> latency/safety trade-offs, survive a security or model-risk audit, and lead teams through incidents — not
> just define terms.*

### System Design & Scale

#### Q: Design an org-wide AI security control plane that every LLM/agent call must pass through.
**Answer:** Build a **centralized AI security gateway** as the single enforcement plane. Request path:
**(1) AuthN/AuthZ** — validate identity and per-use-case entitlement (IAM/OIDC; entitlements provisioned via
Saviynt/ServiceNow). **(2) Misuse guard** — token-bucket rate limit + cost budget + abuse score per
user/tenant. **(3) Input filter** — prompt-injection/jailbreak detection (Prompt Shields/Rebuff/Lakera + regex +
decode-and-rescan), PII scrub. **(4) Policy check** — a PDP (OPA/Rego) decides allow / deny / require-review from
{user, use_case, risk_tier, contains_pii, model_destination}. **(5) Model call** — pinned model version.
**(6) Output validation** — schema/Pydantic, groundedness, PII/secret redaction, insecure-output sanitization.
**(7) Audit** — append-only, hash-chained log with correlation ID to Log Analytics/CloudWatch. Cross-cutting:
policies and filter configs stored **as code** (Terraform/Bicep + Rego), versioned, PR-reviewed with MRM sign-off;
**fail-closed** with a human-review fallback queue; kill switch + guardrail feature flags for incident hot-patching.
Cloud realization: Azure API Management + Azure OpenAI + AI Content Safety + Azure Monitor, or AWS API Gateway +
Bedrock Guardrails + CloudWatch. Senior insight: enforce once at the plane, not N times in N apps.

#### Q: How do you keep the gateway from becoming a latency bottleneck or single point of failure?
**Answer:** Run detectors **in parallel** and short-circuit on the cheapest signal first (regex denylist before a
classifier before an LLM-judge). Cache policy decisions and classifier verdicts on identical inputs. Make heavy
checks (LLM-judge groundedness) **async/sampled** for low-risk tiers, synchronous only for high-risk. Deploy the
gateway HA (multi-AZ, autoscale), with health checks and a **defined fail mode per use-case** (fail-closed for
sensitive, fail-open-with-alert only where signed off). Budget a latency SLO (e.g., +150 ms p95) and measure it as
a first-class metric; if a control blows the budget, move it off the hot path (post-hoc audit) rather than removing
it silently.

#### Q: How do you roll out and version guardrail/policy changes safely across the org?
**Answer:** Treat policies like code: policy repo → unit tests for rules (assert given-context ⇒ expected-decision)
→ PR review + MRM/change-approval (ServiceNow) → staged rollout (shadow mode logging what *would* be blocked →
canary tenant → global). Every threshold change is versioned and attributable. Shadow mode is key: you measure
false-positive/false-negative impact on real traffic before enforcing, avoiding a filter that blocks legitimate
business overnight.

### Trade-offs & Decisions

#### Q: Guardrail false positives block real users; false negatives let attacks through. How do you tune?
**Answer:** Frame it as a risk-weighted threshold, not a binary. Use a **scored** decision (ALLOW/FLAG/BLOCK):
BLOCK only high-confidence attacks, FLAG the ambiguous middle to review/step-up-auth, ALLOW the rest — this shrinks
both hard-error classes. Tune per **use-case risk tier**: a medical/financial agent tolerates more false positives
(safety-first); an internal brainstorming tool tolerates more false negatives (UX-first). Measure precision/recall
against a labeled corpus + red-team set, watch the FLAG rate (review-queue load), and revisit as attackers adapt.
The senior move is making the trade-off *explicit and owned per use-case*, backed by data, not a global magic number.

#### Q: When do you build a homegrown control vs. buy a vendor guardrail (Lakera, Prompt Shields, Guardrails AI)?
**Answer:** Buy the commoditized, fast-moving detection (jailbreak/injection classifiers) — vendors retrain against
the evolving threat landscape faster than you can. Build the parts that encode **your** business rules and
governance (the policy engine, use-case entitlements, audit schema, repair loops) — those are your differentiators
and can't be outsourced. Wrap vendors behind your own interface so you can swap them and add fallbacks. Avoid the
extremes: all-homegrown can't keep up with novel jailbreaks; all-vendor leaves your governance logic in someone
else's black box.

#### Q: Which regulations/frameworks shape what you build, and how do they become code?
**Answer:** **EU AI Act** (risk-tiered; high-risk systems need logging, human oversight, transparency → maps to
audit logging + review gates + model cards); **GDPR Art. 22** (no solely-automated significant decisions → HITL
records); **SR 11-7 / PRA SS1/23** (MRM → model inventory, validation, pinned versions treated as the "model");
**NIST AI RMF** (Govern/Map/Measure/Manage) and **ISO/IEC 42001**; **OWASP LLM Top 10** and **MITRE ATLAS** for the
threat side. You make them concrete: each requirement → a control → evidence (a policy rule, an audit field, a CI
gate) an auditor can inspect. Governance-as-code means the mapping is a living cross-reference, not a slide.

### Failure Modes & Incidents

#### Q: An indirect prompt injection in a RAG document caused an agent to exfiltrate data via a tool call. Walk through response.
**Answer:** **Detect:** audit trail (correlation ID) shows the tool call and the triggering retrieved chunk;
anomaly on outbound tool usage fired. **Contain:** hit the kill switch / feature-flag the tool off for that agent,
hot-patch the gateway policy to deny that tool + destination, revoke the leaked-scope credential. **Eradicate:**
identify the poisoned document(s), purge from the index, add output-DLP + destination-allowlist so exfil can't
succeed even if injection recurs, and tighten tool permissions to least-privilege (the root cause was excessive
agency, LLM08). **Recover:** restore service with the guardrail on, replay audit logs to scope the blast radius,
notify per breach-obligation. **Learn:** add the payload to the red-team corpus, add a CI test, and file the
framework gap (indirect injection via RAG) to the model-risk committee. The whole flow depends on having built the
audit + kill-switch controls *before* the incident.

#### Q: What are the most dangerous failure modes when the control plane itself misbehaves?
**Answer:** (1) **Fail-open under load** — the validator times out and requests pass unchecked; mitigate with
fail-closed defaults and load-shedding. (2) **Silent guardrail regression** — a model/prompt update quietly changes
behavior past the filters; mitigate with continuous eval + shadow monitoring. (3) **Audit gap** — logging drops
under pressure, destroying forensics; make audit writes durable and back-pressure the request, not the log.
(4) **Confused deputy** — the gateway's own privileged identity is abused; least-privilege the gateway.
(5) **Over-blocking incident** — a bad rule blocks all traffic; mitigate with staged rollout + fast rollback +
canary. Design so the *safety system's* failure is itself safe.

### Leadership & Behavioral

#### Q: How do you get every product team to adopt central safety controls without becoming a blocker?
**Answer:** **Make the secure path the easy path.** Ship safety as a drop-in SDK/middleware (a `@secure_agent`
decorator, a gateway endpoint) so teams get input filtering, policy checks, output validation, and audit *for
free* by using the platform — not by reading a policy and reimplementing it. Tier the friction: automated CI gates
and self-service checklists for low-risk use-cases, central review only above a risk threshold (escalation, not
gatekeeping). Publish a use-case registry so shipping through governance is a visible badge. Measure adoption
(% of AI calls through the gateway) and review cycle time (target < 5 business days). A control teams bypass is
worse than none — it creates false assurance.

#### Q: Tell me about a time you blocked or reshaped a launch on AI-security grounds. (STAR)
**Answer:** **Situation:** A week before an internal support agent launched with tool access (ticketing + email),
my pre-launch red-team found an **indirect injection** path: a malicious ticket body could make the agent email
its context (including other customers' data) to an attacker — a data-exfiltration + excessive-agency exposure.
**Task:** As the security-and-governance owner on the launch gate, decide block vs. mitigate vs. ship-scoped.
**Action:** Same-day call with product, the agent team, and security. I quantified it (any inbound ticket could
trigger it — unacceptable) and proposed three options with timelines: (a) 2-day fix — output-DLP + recipient
allowlist + human approval on outbound email (least-privilege the tool), (b) 2-week redesign to a dual-LLM
quarantined pattern, (c) launch read-only (no send tool). Product took (a). I wrote the gateway policy rule and the
recipient allowlist, validated against the red-team corpus, and logged the decision + evidence in the model
inventory. **Result:** Launched 2 days late with the guardrail; the pattern became a standard pre-launch test
(indirect-injection + outbound-action review) for every tool-using agent, and I packaged the fix into the shared
safety SDK so future agents inherited it.

---

> 🎯 **Staff/Principal stretch:** Define the org's **AI safety engineering operating model** and its maturity
> path. Model answer: run a **hub-and-spoke** model — a small central platform team owns the security gateway,
> the policy-as-code framework, the shared safety SDK, the audit schema, and the regulatory→control mapping;
> embedded "AI safety champions" in each product org own day-to-day integration and escalate novel/high-risk
> use-cases to the hub. Drive a **maturity model**: L1 *ad hoc* (each team wires its own filters) → L2
> *centralized gateway* (one enforcement plane, consistent audit) → L3 *policy-as-code* (governance rules
> versioned, tested, PR-approved, auto-enforced) → L4 *continuous assurance* (automated red-team + eval in CI as
> release gates, shadow-mode rollout, mean-time-to-policy-update tracked). Gate cadence: automated CI safety gates
> on every deploy; human review at use-case intake and major model/prompt changes. Keep a living cross-reference
> from EU AI Act / NIST AI RMF / SR 11-7 clauses to internal policy IDs and the code that enforces them, updated
> per regulation or jurisdiction change. Scale signal: if the hub reviews > ~20 use-cases/sprint, your risk-tiering
> thresholds are wrong or a high-volume org needs its own champion. North-star metric: **% of production AI traffic
> passing through the enforced control plane**, with mean-time-to-policy-update as the health check on whether the
> loop actually closes.

---

## Rapid-Fire Fundamentals (flash-card style)

| Question | Answer |
|----------|--------|
| #1 LLM risk (OWASP)? | LLM01 Prompt Injection |
| Direct vs indirect injection? | User-supplied vs hidden in ingested content (RAG/web/email) |
| Why validate output separately? | Model itself hallucinates/leaks; output = untrusted input to next system |
| Enforce structured output? | JSON Schema/Pydantic + repair loop + constrained decoding |
| Rate-limit algorithm? | Token bucket or sliding window |
| PDP/PEP/PIP? | Decision / Enforcement / Information point |
| Policy engine + language? | Open Policy Agent + Rego |
| Tamper-evident logs? | Append-only + hash-chaining + WORM |
| Fail mode for security controls? | Fail-closed with safe fallback |
| Centralize controls where? | An AI security gateway (single enforcement plane) |
| PII redaction tool? | Microsoft Presidio (+ regex for secrets) |
| Adversarial-ML threat taxonomy? | MITRE ATLAS |
| Excessive agency control? | Least-privilege tools + human-in-the-loop + allowlist |
| Key leadership metric? | Mean time to policy update after a red-team finding |

---

## References

- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [MITRE ATLAS](https://atlas.mitre.org/)
- Per-topic `references.md` files in each subfolder
- [Module 10: AI Governance](../10_governance/interview.md) — policy/compliance & Responsible-AI deep dive
