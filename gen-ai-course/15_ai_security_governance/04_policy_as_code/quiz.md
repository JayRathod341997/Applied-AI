# Quiz — Policy-as-Code & Rule Engines for AI Governance

Test your understanding. Answers and justifications are at the bottom.

---

**1. What is the core advantage of policy-as-code over a written AI policy document?**
A. It is easier for lawyers to read
B. It is versioned, testable, auditable, and automatically enforced at runtime
C. It removes the need for any human review
D. It runs faster than documentation

**2. In the PEP/PDP/PIP model, which component actually blocks or allows the request?**
A. PDP (Policy Decision Point)
B. PIP (Policy Information Point)
C. PEP (Policy Enforcement Point)
D. The rule engine's parser

**3. What is the role of the PDP (Policy Decision Point)?**
A. It intercepts the request and enforces the outcome
B. It is a pure function that evaluates policy against a context and returns a decision
C. It supplies external facts like the approved use-case list
D. It stores the audit logs

**4. In OPA, how does an application obtain a decision at runtime?**
A. It recompiles the Rego policy into Python on each call
B. It sends an `input` JSON document to OPA and receives a decision JSON back
C. It reads a static text file of allow/deny pairs
D. It calls a paid cloud API with an API key

**5. For a security/governance ruleset, which conflict-resolution algorithm is the safe default?**
A. Permit-overrides (any ALLOW wins)
B. First-applicable (first matching rule wins, order-dependent)
C. Deny-overrides / most-restrictive-wins (any DENY beats any ALLOW)
D. Random selection among matched rules

**6. Why should a governance PDP usually "fail closed"?**
A. Because closing connections saves memory
B. So that if the PDP is unavailable, high-risk requests are denied rather than silently allowed
C. Because open-source engines require it
D. To reduce latency on the hot path

**7. Which mapping correctly ties a regulation to an enforceable rule?**
A. GDPR Art.22 → "allow all automated decisions"
B. EU AI Act high-risk → `risk_tier >= 3 → REQUIRE_REVIEW`
C. NIST AI RMF → "delete all audit logs"
D. GDPR data residency → "send all PII to the cheapest external model"

**8. What makes a policy's unit test valuable as audit evidence?**
A. It proves the rule fires for the right input AND names the specific rule/reason
B. It measures the latency of the engine
C. It confirms the policy file compiles
D. It checks the code style of the app

**9. Why is a declarative ruleset (rules as data) preferred over scattered `if` statements in app code?**
A. `if` statements are slower in Python
B. Rules-as-data can be versioned, diffed, reviewed, tested, and deployed independently of the app
C. Declarative rules never need testing
D. It lets you avoid writing any tests

**10. When should you choose a real engine (OPA/Cedar) over a homegrown Python rule engine?**
A. Never — homegrown is always better
B. When the ruleset is a one-off inside a single service
C. When policy must be shared across teams/services, hot-reloaded without app redeploys, and audited independently
D. Only when you have no unit tests

---

## Answers

1. **B** — The defining properties of policy-as-code are that governance becomes versioned, testable, auditable, automatically enforced, and a single source of truth. Readability (A) is a side benefit; it does not remove human review (C) and speed (D) isn't the point.

2. **C** — The PEP (Policy Enforcement Point) sits in the request path and *acts* on the decision (block/allow/route). The PDP only decides; the PIP only supplies facts.

3. **B** — The PDP is a stateless, side-effect-free function `(policy, context) -> decision`, which is exactly why it is reusable and testable in isolation. A is the PEP, C is the PIP, D is the audit store.

4. **B** — OPA is queried with an `input` JSON document and returns a decision JSON (typically via a local sidecar/HTTP or the Go/WASM library). No per-call recompilation, static file, or paid API is involved.

5. **C** — Deny-overrides (most-restrictive-wins) guarantees that a matching DENY can never be shadowed by an ALLOW, which is the fail-safe behavior you want for security. First-applicable (B) is order-sensitive and error-prone; permit-overrides (A) is unsafe here.

6. **B** — Fail-closed means an unavailable PDP results in denial (for high-risk paths), preventing a silent fail-open where everything is allowed. It is a safety, not performance, decision.

7. **B** — EU AI Act high-risk obligations (human oversight) map cleanly to requiring review above a risk tier. The other options invert or violate the regulation.

8. **A** — A good policy test asserts both the effect *and* the specific winning rule/reason, so it demonstrates the intended control operates correctly — that is the evidence auditors want.

9. **B** — Rules as data ride the normal git/PR/CI lifecycle and can change without an app release, unlike logic buried in scattered conditionals. Declarative rules still need tests (C/D are wrong); speed (A) isn't the reason.

10. **C** — Graduate to OPA/Cedar when the policy is shared, must hot-reload independently of the app, or needs independent auditing/analysis. A homegrown engine is fine for a small, single-service, embedded ruleset — but must still be tested.
