# Quiz: Reusable Safety Patterns for AI Agents

## Questions

### Question 1
What is the core idea of the centralized AI Security Gateway pattern?

A) Each team writes its own guardrail library
B) Every AI call flows through one enforcement plane with the same stages
C) The LLM decides which guardrails to run
D) Guardrails run only in the CI pipeline

### Question 2
Why prefer a centralized gateway over per-app guardrail libraries?

A) It is always lower latency
B) It removes the need for output validation
C) A fix or new signature ships once and every agent inherits it
D) It lets each team pick its own audit format

### Question 3
A guardrail service throws an unexpected exception while checking a refund action.
Under a **fail-closed** design, what happens?

A) The request is allowed through
B) The request is blocked
C) The error is returned to the end user verbatim
D) The model retries without guardrails

### Question 4
In the Dual-LLM (privileged vs. quarantined) pattern, the **quarantined** model:

A) Has tools but never sees untrusted content
B) Reads untrusted content but has no tools
C) Is the only model allowed to send email
D) Signs the audit log

### Question 5
An agent uses its own broad service-account credentials to act on data an attacker
tricked it into touching. This failure mode is called:

A) Automation bias
B) Unbounded consumption
C) Confused deputy
D) Model inversion

### Question 6
Which control most directly limits the blast radius of an indirect prompt injection
that tries to **exfiltrate data through a tool**?

A) A longer system prompt
B) Egress allowlist + output URL validation (sandboxed tools)
C) Increasing the model temperature
D) Caching responses

### Question 7
What is the purpose of a **canary token** in a system prompt?

A) To speed up inference
B) To detect injection/exfiltration when the secret appears in output or egress
C) To authenticate the user
D) To compress the prompt

### Question 8
A human-in-the-loop reviewer approves every AI action in two seconds without
reading it. This is an example of:

A) Defense in depth
B) Least privilege
C) Automation bias / over-reliance (a control in name only)
D) A circuit breaker

### Question 9
In the safety maturity model, moving from a centralized gateway (L1) to L2 means:

A) Letting each team hand-roll guardrails again
B) Expressing guardrails/allowlists/risk tiers as versioned policy-as-code
C) Removing the audit log
D) Disabling human review

### Question 10
Why is packaging safety patterns as a shared internal SDK the real deliverable?

A) SDKs are faster than any other code
B) It makes security the default so every agent inherits controls; docs alone get ~0% adoption
C) It removes the need for red-teaming
D) It guarantees zero false positives

## Answers

1. B - The gateway routes every call through one enforcement plane (input → policy → LLM → output → audit) so controls are consistent and unbypassable.
2. C - Centralization means one fix/signature/policy update protects all agents at once; copy-paste libraries drift and lag.
3. B - Fail-closed treats any guardrail error as a BLOCK, especially for actions like refunds; the error is never leaked to the user.
4. B - The quarantined LLM ingests untrusted content but has no tools; the privileged (tool-using) LLM never sees raw untrusted text.
5. C - The confused deputy uses its own elevated privileges on an attacker's behalf; the fix is scoping credentials to the end user.
6. B - Sandboxing with an egress allowlist plus output URL validation stops data leaving to attacker-controlled destinations even if injection succeeds.
7. B - A canary is a unique secret whose appearance in output/egress is proof of injection or exfiltration, triggering an alert.
8. C - Rubber-stamping approvals is automation bias; a control that always approves is not a real control — add friction and audit approvers.
9. B - L1→L2 externalizes rules into versioned policy-as-code (e.g. OPA/Rego) pushed centrally instead of hard-coded and redeployed.
10. B - An SDK/gateway makes secure defaults the easy, inherited path; security in a doc or optional library has near-zero adoption.
