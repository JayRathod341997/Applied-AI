# Exercise 01 — Build an Output-Validation Gateway

## Scenario

You run the platform team for a customer-support RAG assistant. The model is helpful but
occasionally: returns malformed JSON, leaks a customer's email/phone, invents figures that
aren't in the retrieved documents, wraps answers in `<script>` tags that your web UI would
render, and once echoed an AWS key that appeared in a support ticket.

Input filtering is already handled upstream. Your job is the **outbound** control plane: a
gateway that inspects every model response *before* it reaches a browser, database, or user,
and either allows it, ships a sanitized version, or blocks it — with a bounded retry that
re-asks the (simulated) model on repairable failures.

Work in `exercise.py`. Everything runs **offline** — the LLM and its retry are simulated by
`fake_llm_repair`. `pydantic` is optional; your code must run with or without it.

## Tasks

1. **`SecretScanner`** — if the output matches any credential pattern, return a `Finding`
   with `Action.BLOCK` and `Severity.CRITICAL`. Never redact-and-ship a secret.
2. **`SchemaValidator`** — when `ctx.expect_json`, parse the output; on invalid JSON or a
   schema/type violation return `Action.RETRY` with a message describing the error. Validate
   against `ctx.pydantic_model` when pydantic is available, else `ctx.required_fields`.
3. **`PIIRedactor`** — replace emails/phones with `[REDACTED_<LABEL>]`; if anything changed,
   return `Action.SANITIZE` carrying the redacted text in `Finding.output`.
4. **`UnsafeContentScanner`** — on active markup (`<script>`, `javascript:`, `on*=`),
   HTML-encode the whole output (`html.escape`) and return `Action.SANITIZE`.
5. **`GroundednessChecker`** — when `ctx.grounding` is non-empty, fail with `Action.RETRY`
   if a numeric claim in the answer is absent from the sources (strip `[1]`-style citations
   first), or if content-word overlap with the sources is too low.
6. **`OutputValidator.validate`** — run the chain over a running `working` output:
   - apply each `SANITIZE` result to `working` and keep going;
   - any `BLOCK` ⇒ return `Decision.BLOCKED`;
   - any `RETRY` ⇒ call `repair_fn(current, feedback)` (up to `max_retries`) and re-run;
     if retries are exhausted, **fail closed** (`BLOCKED`);
   - otherwise return `SANITIZED` if anything changed, else `ALLOW`.

## Acceptance criteria

- `python exercise.py` runs with no crash and prints a decision per sample.
- The five demo samples produce: `ALLOW`, `SANITIZED` (PII), `ALLOW` after 1 retry
  (ungrounded → repaired), `SANITIZED` (script encoded), `BLOCKED` (secret).
- The gateway **fails closed**: unresolved retries and blocks never ship the output.
- Works whether or not `pydantic` is installed.

## Hints

- A validator returns exactly one `Finding`; the gateway aggregates them.
- Order matters: put hard, cheap blocks (secrets) early and expensive checks (groundedness)
  late. `SANITIZE` mutates the stream; `BLOCK`/`RETRY` are verdicts.
- For groundedness, numbers are the cheapest tripwire: `set(re.findall(r"\d+", answer))`
  minus the source numbers should be empty. Remember to strip `[\d+]` citations first.
- Keep validators pure and stateless — they take `(output, ctx)` and return a `Finding`.
- Compare your output against `solution.py` once it runs.
