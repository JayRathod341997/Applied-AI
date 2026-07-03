# Exercise 01 — Build a Python Policy Engine for AI Governance

## Scenario

You are the runtime security engineer for an internal **LLM gateway**. Every AI request that
passes through it must be checked against your org's AI governance policy *before* the model is
called. Product teams keep asking for exceptions and auditors keep asking for evidence, so
hard-coding `if` statements in the gateway is no longer acceptable. You will build a small
**Policy Decision Point (PDP)**: a reusable engine that evaluates a *declarative ruleset* against
a *request context* and returns a decision plus an audit trace of which rule fired.

The gateway (the PEP) will call your engine like this:

```python
decision = engine.evaluate(context)
if decision.effect is Effect.DENY:
    reject(decision.reason)
elif decision.effect is Effect.REQUIRE_REVIEW:
    route_to_human(decision)
else:
    call_model()
```

## Request context (the "input JSON")

Each request is a dict with these fields:

| Field | Type | Example |
|---|---|---|
| `user` | str | `"alice"` |
| `user_trust` | str | `"internal"` / `"external"` |
| `use_case` | str | `"customer_support"` |
| `risk_tier` | int (1–5) | `4` |
| `contains_pii` | bool | `True` |
| `model_destination` | str | `"internal"` / `"external"` |

## Policy (declarative — a list of rules)

A **rule** is `{id, description, effect, priority, when:[conditions]}`. A **condition** is
`{field, op, value}`. A rule *matches* when **all** its conditions are true (logical AND).
Effects are `ALLOW`, `REQUIRE_REVIEW`, `DENY`.

## Tasks

1. **Operators.** Implement condition operators: `eq`, `ne`, `in`, `not_in`, `gte`, `is_true`
   (add `lte`, `is_false`, `contains` if you like). `gte` must not crash on a `None` field.
2. **Condition + Rule.** `Condition.evaluate(context)` applies one operator; `Rule.matches(context)`
   is true only when every condition passes (an empty `when` list is a catch-all default rule).
3. **from_policy().** Parse a policy dict (JSON/YAML-shaped) into `Rule`/`Condition` objects.
4. **evaluate().** Collect all matching rules. If none match, return the engine's `default_effect`.
   Otherwise pick a winner using **deny-overrides** (most-restrictive-wins:
   `DENY > REQUIRE_REVIEW > ALLOW`).
5. **Audit trace.** The returned `Decision` must include `winning_rule_id`, a human-readable
   `reason`, and `matched_rules` (the full list of rules that fired) — you must be able to answer
   *"which rule denied this, and what else matched?"*
6. **Bonus — Rego stub.** In a comment or a `.rego` file, write the equivalent of one rule in Rego
   and show the `curl` query shape (`input` JSON → decision JSON).

## Policy to implement (minimum ruleset)

| id | effect | condition |
|---|---|---|
| `AIA-001-usecase-approved` | DENY | `use_case` not in `{customer_support, code_assist, internal_search}` |
| `GDPR-A22-pii-external` | DENY | `contains_pii` is true AND `model_destination == external` |
| `NIST-RMF-high-risk-review` | REQUIRE_REVIEW | `risk_tier >= 3` |
| `SEC-untrusted-user-external` | REQUIRE_REVIEW | `user_trust == external` AND `model_destination == external` |

## Acceptance criteria

- `python exercise.py` runs with **no network and no third-party deps** and prints a decision per request.
- A clean internal, approved, low-risk request → **ALLOW** (via default).
- PII to an external model → **DENY**, winner `GDPR-A22-pii-external`.
- Unapproved use-case → **DENY**, winner `AIA-001-usecase-approved`.
- `risk_tier == 4` on an approved use-case → **REQUIRE_REVIEW**.
- A request that matches *both* a DENY rule and a REVIEW rule → **DENY** (deny-overrides), and the
  trace still lists all matched rules.
- Decisions are serializable to JSON (for the audit log).

## Hints

- Store effect restrictiveness as `{ALLOW:0, REQUIRE_REVIEW:1, DENY:2}` and pick the winner with
  `max(matched, key=lambda r: RANK[r.effect])`.
- Keep operators as a `dict[str, Callable]` — adding a new operator becomes one line, not an
  `if/elif` ladder.
- Sort rules by `priority` before evaluating so the trace reads in a stable, human-friendly order.
- Prefer **deny-overrides** over first-applicable for security policies — order bugs can't silently
  let a request through.
- Think about `default_effect`: `ALLOW` is convenient for a demo, but a real governance PDP usually
  wants **DENY** (fail-closed).
