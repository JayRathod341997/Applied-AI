# Policy-as-Code & Rule Engines for AI Governance

> Governance that lives in a Confluence page is a *suggestion*. Governance that lives
> in code, runs on every request, and blocks the call is a *control*. This topic is
> about turning the second sentence into a real system.

---

## Why this matters (the threat model)

Your org publishes an "AI Acceptable Use Policy": *don't send customer PII to external
models, don't use un-approved use-cases, high-risk decisions need human review*. Then:

- A well-meaning engineer pastes a support transcript (full of PII) into a third-party
  API to "test something." **Nobody was malicious. The document didn't stop them.**
- Six months later an auditor asks: *"Prove that on 2026-03-14 this request was allowed
  under an approved use-case."* You have Slack messages and a wiki page. You lose.

The gap is **enforcement** and **evidence**. Policy-as-code closes both: the policy is
executable, sits in the request path, and every decision emits an audit record.

| Governance-by-document | Governance-by-code (policy-as-code) |
|---|---|
| Enforced by hope / training | Enforced automatically at a decision point |
| "Latest" version is ambiguous | Versioned in git; one source of truth |
| Untestable | Unit-tested like any code |
| Change = edit a wiki | Change = PR + review + approval + deploy |
| Audit = screenshots | Audit = immutable decision logs |
| Drifts from reality | Is reality (it's what runs) |

**The five properties you sell in an interview:** policy-as-code is *versioned, testable,
auditable, automatically enforced, and a single source of truth.*

---

## Core mental model: PEP / PDP / PIP

Separate the **policy** from the **application**. The classic access-control decomposition
(from XACML, and how OPA is deployed) has three roles:

```
                        ┌─────────────────────────────┐
   AI request ─────────▶│  PEP  Policy Enforcement Pt  │   (in your app / gateway)
                        │  "should I allow this call?" │
                        └──────────────┬──────────────┘
                                       │ input JSON (context)
                                       ▼
                        ┌─────────────────────────────┐
                        │  PDP  Policy Decision Pt     │   (OPA / your rule engine)
                        │  evaluates rules → decision  │
                        └──────┬───────────────┬──────┘
                               │ needs data?   │ decision (allow/deny/review + reason)
                               ▼               ▼
                     ┌───────────────┐   back to PEP, which ENFORCES it
                     │ PIP  Policy   │   (blocks, allows, or routes to a reviewer)
                     │ Information Pt│
                     │ (use-case DB, │
                     │  risk registry)│
                     └───────────────┘
```

| Role | What it does | Example in an AI stack |
|---|---|---|
| **PEP** — Enforcement | Intercepts the action, asks the PDP, *acts* on the answer | Your LLM gateway / middleware that wraps `model.generate()` |
| **PDP** — Decision | Pure function: `(policy, context) -> decision`. No side effects | OPA server, or the `PolicyEngine` in this exercise |
| **PIP** — Information | Supplies extra facts the PDP needs | Approved-use-case registry, model risk tier, user's trust level |

Why the split matters: the PDP is **stateless and testable in isolation**, the same policy
is reused across many PEPs (API, batch job, notebook), and security reviews the policy
without reading your whole app. **Never inline `if pii and external: raise` all over the
codebase** — that's ungovernable and untestable.

---

## Declarative vs imperative policy

Imperative (control flow buried in app code):

```python
if req.use_case not in APPROVED:            # scattered
    raise Forbidden()
elif req.contains_pii and req.dest == "external":
    raise Forbidden()
elif req.risk_tier >= 3:
    route_to_review()
# ...repeated in 5 services, drifts, untested
```

Declarative (policy as *data*, evaluated by an engine):

```python
rules = [
  {"id": "pii-external", "effect": "DENY", "when": [
      {"field": "contains_pii", "op": "is_true"},
      {"field": "model_destination", "op": "eq", "value": "external"}]},
  # ...
]
decision = engine.evaluate(rules, context)   # one engine, one place, tested once
```

Declarative wins because rules become **data you can version, diff, review, test, and ship**
independently of application releases. A compliance officer can read the ruleset; they can't
read your Python.

---

## Open Policy Agent (OPA) & Rego

**OPA** is the de-facto industry standard general-purpose PDP (a CNCF graduated project). You
write policies in **Rego** (a declarative query language), OPA loads them, and your app queries
it with an `input` JSON document; OPA returns a decision JSON. It's the same PEP/PDP model above.

A small Rego policy governing an AI request:

```rego
package ai.governance

# default decision: deny-by-default is the safe posture for governance
default decision := {"allow": false, "reason": "no rule matched (default deny)"}

approved_use_cases := {"customer_support", "code_assist", "internal_search"}

# Rule 1: deny un-approved use-cases
decision := {"allow": false, "reason": "use-case not approved"} if {
    not approved_use_cases[input.use_case]
}

# Rule 2: deny PII in a prompt bound for an external model (GDPR Art.22 / data residency)
decision := {"allow": false, "reason": "PII may not leave to an external model"} if {
    input.contains_pii == true
    input.model_destination == "external"
}

# Rule 3: require human review above a risk tier (EU AI Act high-risk / NIST RMF)
decision := {"allow": true, "review": true, "reason": "high risk tier needs review"} if {
    input.risk_tier >= 3
}

# Rule 4: allow everything else that is an approved, low-risk, internal call
decision := {"allow": true, "reason": "approved low-risk request"} if {
    approved_use_cases[input.use_case]
    input.risk_tier < 3
    not (input.contains_pii == true; input.model_destination == "external")
}
```

How it's queried at runtime (input JSON → decision):

```bash
# OPA as a sidecar/server; your PEP POSTs the request context and reads the decision
curl -s localhost:8181/v1/data/ai/governance/decision \
  -d '{"input": {"use_case":"customer_support","contains_pii":true,
                 "model_destination":"external","risk_tier":2}}' \
  -H 'Content-Type: application/json'
# => {"result": {"allow": false, "reason": "PII may not leave to an external model"}}
```

Two big ideas to remember about Rego:
1. Rego is about **querying structured data** (the `input` document), not writing loops. Rules
   are logical statements that are true or false for a given input.
2. OPA runs **out-of-band** as a library or sidecar, so the *same* policy bundle secures Kubernetes
   admission, API authz, Terraform plans, **and** your AI gateway. One policy engine, everywhere.

---

## Alternatives & complements (know when to reach for which)

| Tool | Shape | Best for | Watch out |
|---|---|---|---|
| **OPA / Rego** | General policy engine, sidecar/lib | Org-wide policy, k8s, authz, complex logic | Rego learning curve |
| **AWS Cedar** | Policy language (verifiable, analyzable) | Fine-grained authz, provable properties | AWS-centric ecosystem |
| **JSON Logic** | Rules as portable JSON | Same rule runs in Python **and** browser JS | Verbose nested JSON |
| **YAML/JSON rule DSL** | Your own `{when, effect}` schema (this exercise) | Small, domain-specific policy sets | You own the engine + tests |
| **Decision tables** | Rows = conditions → outcome (a spreadsheet) | Non-engineers author rules; combinatorial coverage | Explodes with many columns |
| **DMN** (Camunda etc.) | Business-rule standard, visual tables | BPM shops, business-authored rules | Heavy stack |
| **Homegrown Python engine** | `list[Rule]` + evaluator | Prototypes, tight embedding, learning | Reinventing conflict resolution, testing |

**When to use a real engine vs a homegrown one:** use OPA/Cedar when policy is shared across
teams/services, needs hot-reload without redeploying the app, must be audited independently, or
grows complex. Roll your own (like the exercise) when the ruleset is small, lives inside one
service, and you want zero new infrastructure — but the moment two services need the same rules,
graduate to OPA. Never let "homegrown" mean "untested and undocumented."

Conflict resolution is the part people get wrong. Decide your combining algorithm up front:

| Algorithm | Behavior | Use when |
|---|---|---|
| **Deny-overrides** (most-restrictive-wins) | Any DENY beats any ALLOW | **Default for security/governance** |
| First-applicable | First matching rule wins | Ordered, priority-driven policies |
| Permit-overrides | Any ALLOW wins | Rarely — permissive systems |

This exercise uses **deny-overrides** (`DENY > REQUIRE_REVIEW > ALLOW`) — the safe choice.

---

## Policy lifecycle: author → test → review → deploy → audit

Policy-as-code is *code*, so it rides your existing SDLC and change-management rails.

```
 author ──▶ TEST ──▶ PR review + approval ──▶ deploy ──▶ audit
 (write     (unit    (security/MRM sign-off,   (CI ships   (immutable
  rule)      tests    ServiceNow/Saviynt         bundle)     decision logs)
             for      change ticket)
             policy)
```

- **Author.** Add/change a rule in the versioned policy file. Small, reviewable diffs.
- **Test.** Unit-test the *policy itself* — governance you don't test is governance you don't have:

  ```python
  def test_pii_to_external_is_denied():
      d = engine.evaluate({"contains_pii": True, "model_destination": "external",
                           "use_case": "customer_support", "risk_tier": 1})
      assert d.effect is Effect.DENY
      assert d.winning_rule_id == "GDPR-A22-pii-external"   # right rule, right reason
  ```
  (OPA has this built in: `opa test policy/` runs `test_*` rules in Rego.)

- **PR review + approval.** The diff is reviewed by security/compliance. This is where a
  **Model Risk Management (MRM) sign-off** or a **ServiceNow/Saviynt change-approval** ticket
  is attached — the merge is the auditable approval event.
- **Deploy.** CI publishes the policy bundle (OPA bundle, or a config artifact). Policy can be
  updated **without redeploying the app** — a key operational win.
- **Audit.** Every decision logs `{who, what, decision, winning_rule, policy_version, timestamp}`
  to an append-only store. This is your evidence trail (ties into 05_audit_traceability).

---

## Mapping regulation → enforceable rules

The senior skill: translate a legal clause into a testable rule. Regulators want *evidence of a
control*; a policy rule + its unit test + its decision logs **is** that evidence.

| Regulation / clause | Requirement (plain English) | Enforceable rule |
|---|---|---|
| **EU AI Act** – high-risk systems | Human oversight for high-risk AI | `risk_tier >= 3 → REQUIRE_REVIEW` |
| **EU AI Act** – prohibited/limited use | Only approved use-cases in production | `use_case not_in approved → DENY` |
| **NIST AI RMF** – GOVERN/MAP/MEASURE/MANAGE | Inventory + risk-tier every use-case; manage risk | Rules keyed to a use-case registry & risk tier (PIP) |
| **GDPR Art.22** | No solely-automated decision with legal effect w/o human review | `automated AND legal_effect → REQUIRE_REVIEW` |
| **GDPR** – data residency / minimization | Don't export personal data to third parties | `contains_pii AND destination=external → DENY` |
| **ISO/IEC 42001** – AI management system | Documented, operating controls | The policy file + tests + logs are the documented control |

The point: each row becomes a rule in the ruleset, a unit test proving it fires, and a stream of
decision logs proving it fired *in production*. That triangle is what passes an audit.

---

## Failure modes (what goes wrong in production)

| Failure | Symptom | Mitigation |
|---|---|---|
| **Fail-open** | PDP is down → PEP allows everything | Fail **closed** for high-risk paths; cache last-known-good policy |
| **Missing default** | Unmatched request silently allowed | Explicit `default_effect` (prefer DENY for governance) |
| **Rule-order bug** | ALLOW shadows a DENY | Use deny-overrides, not first-applicable, for security |
| **Stale PIP data** | Denying on last week's use-case list | Version + TTL the info sources; log the policy_version used |
| **Untested policy** | A "fix" silently breaks another rule | Unit tests + CI gate on the policy repo |
| **No trace** | Can't answer "why was this denied?" | Every decision returns the winning rule id + full matched set |
| **Latency** | PDP call on the hot path adds ms | Co-locate OPA as a sidecar; cache decisions for identical inputs |
| **Policy/app drift** | App checks differ from the policy file | One PDP, no inline `if` checks in app code |

---

## Production checklist

- [ ] Policy lives in a **versioned repo**, separate from app deploy, one source of truth.
- [ ] Combining algorithm is explicit and **deny-overrides** for governance rules.
- [ ] **Explicit default** decision; high-risk paths **fail closed** if the PDP is unavailable.
- [ ] Every rule has a stable **id** and a human-readable **reason** returned in the decision.
- [ ] **Unit tests per rule** (fires when it should, and only then); CI blocks merge on failure.
- [ ] Policy changes go through **PR review + approval** (security/MRM/ServiceNow-Saviynt ticket).
- [ ] Each decision emits an **audit record**: subject, context hash, decision, winning rule,
      `policy_version`, timestamp — to an append-only/WORM store.
- [ ] **PIP data** (use-case registry, risk tiers) is versioned, TTL'd, and logged with the decision.
- [ ] Regulatory clauses are **mapped to rules**; the mapping table is kept current.
- [ ] PDP latency is measured; decisions cached where safe; sidecar co-located with the PEP.

---

## Interview soundbites

- *"Policy-as-code makes governance versioned, testable, auditable, automatically enforced, and a
  single source of truth — a document does none of those."*
- *"I separate PEP, PDP, and PIP so the policy is a stateless, testable pure function reused across
  every entry point."*
- *"OPA/Rego is queried with an input JSON and returns a decision JSON; the same bundle secures
  k8s, authz, and the AI gateway."*
- *"For governance I use deny-overrides with an explicit default-deny and fail-closed on the PDP."*
- *"I map each regulatory clause to a rule, a unit test, and a decision-log stream — that triangle
  is the audit evidence."*
