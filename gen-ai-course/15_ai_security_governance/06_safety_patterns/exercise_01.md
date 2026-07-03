# Exercise 01: Build a reusable `@secure_agent` guardrail decorator

## Scenario

Your platform team runs a dozen LLM agents (support bot, refund bot, internal
search, ...). Each team wired up guardrails differently — some skipped them. A
recent indirect prompt-injection incident leaked an API key through a "support"
agent. Leadership wants **one reusable safety layer that every agent inherits by
default**, so a fix ships once and no agent can bypass it.

You will build that layer as a **decorator / middleware** — a miniature *AI Security
Gateway*. It must run every agent call through the same five stages and be
**fail-closed**.

```
input filter  ->  policy check  ->  (call agent/LLM)  ->  output validation  ->  audit log
```

## Your tasks

Implement `secure_agent(...)` in `exercise.py` so that wrapping any
`agent(ctx: AgentContext) -> str` produces a function returning a `GatewayResult`.

1. **Stage 1 — input filter.** Block prompts matching prompt-injection signatures
   (e.g. "ignore previous instructions", "reveal system prompt") or that are
   absurdly long.
2. **Stage 2 — policy check.** Block actions not on the allowlist. Return
   `ESCALATE` for high-risk actions (`send_email`, `refund`) or `risk == "high"`;
   otherwise `ALLOW`.
3. **Stage 3 — call the agent** (the LLM). If it raises, do **not** leak the error —
   return a `BLOCK`.
4. **Stage 4 — output validation.** Block responses that leak secrets (e.g. `sk-...`)
   or contain a non-allowlisted outbound URL (data-exfiltration guard).
5. **Stage 5 — human-in-the-loop.** For `ESCALATE`d calls, invoke the
   `human_review` hook; approve → `ALLOW`, reject → `BLOCK`.
6. **Fail-closed.** Any *unexpected* exception in a guardrail stage must become a
   `BLOCK` when `fail_closed=True`.
7. **Audit.** Every terminal decision (allow/block/escalate outcome) is written to
   the audit log with `request_id`, `decision`, `stage`, and `reason`.

## Acceptance criteria

`python exercise.py` runs with no network and demonstrates:

- [ ] A **benign** call returns `ALLOW`.
- [ ] A **prompt-injection** call returns `BLOCK` at `input_filter`.
- [ ] An output that **leaks a secret** returns `BLOCK` at `output_validation`.
- [ ] A **non-allowlisted action** returns `BLOCK` at `policy_check`.
- [ ] A **high-risk** action is `ESCALATE`d, then `ALLOW`/`BLOCK` per the human hook.
- [ ] Forcing any stage to raise yields `BLOCK` (fail-closed), not a leaked output.
- [ ] The audit log contains one record per call with a decision + reason.

## Stretch goals

- Make the audit log **hash-chained** (tamper-evident) and add a `verify()` method.
- Add a **circuit breaker**: after N blocks from one user, short-circuit to `BLOCK`.
- Add a **canary token** to the prompt and alert if it appears in the output.
- Make stages **pluggable** (pass `input_filter`/`policy`/`validator` as callables).

## Hints

- `functools.wraps` preserves the wrapped agent's metadata.
- Use `re.search` on the lowercased prompt for signatures.
- Structure each stage as `try/except GuardrailError` (→ BLOCK with reason) plus a
  broad `except Exception` guarded by `fail_closed`.
- Keep one helper that writes the audit record *and* builds the `GatewayResult` so
  you can't forget to audit a path.
- Compare against `solution.py` only after your own attempt.
