# Quiz: Misuse Protection & Abuse Prevention

## Questions

### Question 1
For an LLM API, which axis is MOST important to rate-limit on?

A) Number of requests only
B) Tokens and dollars consumed
C) Number of unique users
D) HTTP status codes returned

### Question 2
Why is a token bucket usually preferred over a fixed-window counter for an API gateway?

A) It uses more memory but is more accurate
B) It blocks all bursts completely
C) O(1) memory, allows controlled bursts, enforces a strict long-run average
D) It requires no timestamp tracking of any kind

### Question 3
A user has accumulated more spend than their rolling cost cap allows. What decision should the guard return?

A) ALLOW — cost is only advisory
B) THROTTLE
C) BLOCK
D) SUSPEND

### Question 4
What is the correct precedence (most severe wins) for the four decisions?

A) ALLOW > THROTTLE > BLOCK > SUSPEND
B) SUSPEND > BLOCK > THROTTLE > ALLOW
C) THROTTLE > SUSPEND > BLOCK > ALLOW
D) BLOCK > SUSPEND > ALLOW > THROTTLE

### Question 5
Systematically querying a model to clone it or steal its system prompt maps to which OWASP LLM risk?

A) LLM10 — Unbounded Consumption / Model Theft
B) LLM02 — Insecure Output Handling
C) LLM03 — Training Data Poisoning
D) LLM07 — Insecure Plugin Design

### Question 6
What is the purpose of a canary/honeypot token seeded in a system prompt or RAG document?

A) To speed up inference
B) To detect data-exfiltration / prompt-extraction attempts when it leaks
C) To reduce token cost
D) To authenticate the user

### Question 7
Why should the abuse score DECAY over time rather than only increase?

A) To make suspension permanent
B) So a single bad session does not ban a user forever; only sustained abuse suspends
C) Because integers overflow
D) To reduce database storage

### Question 8
In an AI-misuse incident, what does "guardrail hot-patch" mean during CONTAINMENT?

A) Retraining the base model from scratch
B) Pushing a new filter/policy rule without a full code redeploy
C) Rotating all user passwords
D) Deleting the audit logs

### Question 9
What does the Mean-Time-To-Policy-Update (MTTPU) metric measure?

A) Model inference latency
B) Time from detecting a new abuse pattern to deploying a guardrail that stops it
C) Average tokens per request
D) Time between model version releases

### Question 10
In CI, what is a "jailbreak pass-rate release gate"?

A) A limit on how many users can log in
B) Failing the build if too high a fraction of known attack prompts bypass defenses
C) A rate limit applied at deploy time
D) A test that measures model accuracy on benchmarks

## Answers

1. B - LLM abuse is consumed in tokens and dollars; a single large-context request can cost 1000× a normal one, so request count alone is a poor limit.
2. C - Token bucket is O(1) per user, permits legitimate short bursts up to capacity, yet enforces a strict average refill rate — the API-gateway default.
3. C - Exceeding the spend cap rejects that request (BLOCK) but the user stays active; SUSPEND is reserved for accumulated abuse.
4. B - Most severe wins: SUSPEND > BLOCK > THROTTLE > ALLOW, so a suspended user is cut off regardless of budget/rate state.
5. A - Systematic extraction to clone the model or steal the prompt is LLM10 (Unbounded Consumption / Model Theft).
6. B - A canary is a marked secret; if it ever surfaces in an output or attacker prompt you have caught an exfiltration/extraction attempt.
7. B - Decay forgives old strikes so only sustained abuse crosses the suspend threshold, cutting false-positive bans.
8. B - A hot-patch deploys a new filter/policy rule as config/data without a full redeploy, minimizing MTTPU during containment.
9. B - MTTPU is the AI analog of MTTR: detection of a new abuse pattern to a deployed guardrail that stops it.
10. B - It is an adversarial CI gate: if the fraction of known jailbreaks that succeed exceeds the threshold, the release fails.
