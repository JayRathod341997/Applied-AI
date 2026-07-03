# Exercise 01 — Build a `MisuseGuard`

## Scenario

You run the API gateway in front of a company LLM endpoint. Every request costs money and the model is jailbreakable if
hammered hard enough. Marketing bots, a cost-bomb "whale," and a determined jailbreaker named **mallory** all share the
same endpoint as your legitimate users. Your job: build the runtime gate that decides — *before and after* each call —
whether to serve, slow down, reject, or cut off each caller.

You will implement a single `MisuseGuard` class that fuses **three independent controls** into one decision.

## Your task

Implement the stubs in `exercise.py` so the guard returns one of four decisions per request:

| Decision | Meaning | Triggered by |
|----------|---------|--------------|
| `ALLOW` | Serve normally | Passed all checks |
| `THROTTLE` | Rate-limited; client should back off | Token bucket empty |
| `BLOCK` | This request rejected (user still active) | Cost budget exceeded, or a single violation |
| `SUSPEND` | User cut off entirely until review | Abuse score crossed threshold |

Build these pieces:

1. **`TokenBucket.try_consume(now, cost)`** — refill by elapsed × rate (cap at capacity); consume `cost` tokens if
   available, else return `(False, retry_after_s)`.
2. **`CostBudget`** — a rolling-window spend cap: `current_spend`, `can_afford`, `charge`. Drop events older than the window.
3. **`AbuseTracker`** — a strike counter: `add_strike` (with optional decay) and `is_suspended`. Sticky suspension once the
   threshold is reached.
4. **`MisuseGuard.check(user_id, est_cost, req_tokens)`** — apply the four checks in **severity order**:
   `SUSPEND > BLOCK(budget) > THROTTLE(rate) > ALLOW`. Only `ALLOW` charges the budget and consumes tokens.
5. **`MisuseGuard.report_violation(user_id)`** — add a strike after the safety layer flags a prompt/response; return
   `SUSPEND` if it crossed the threshold, else `BLOCK`.

Then extend the demo to stream benign + abusive users and print the decisions.

## Acceptance criteria

- `python exercise.py` runs with **no network calls** and prints a decision per request.
- A user sending a burst larger than the bucket capacity gets `THROTTLE` once the bucket drains.
- A user whose accumulated cost exceeds the cap gets `BLOCK` on the offending request.
- A user who triggers `suspend_threshold` violations flips to `SUSPEND` and **stays** suspended on subsequent requests.
- Decision precedence is respected: a suspended user is `SUSPEND` even if they are also under budget and rate limit.
- Only `ALLOW`ed requests consume tokens / charge the budget (blocked requests are free to the user's quota).

## Hints

- Inject a **virtual clock** (`clock` callable) so you can fast-forward time in the simulation without `time.sleep`.
- Refill *before* checking, using `min(capacity, tokens + elapsed * refill_per_s)`.
- Keep suspension **sticky**: once `suspended = True`, `is_suspended` stays true until a manual `reset_user`.
- Check suspension **first** — it is the cheapest and most severe check.
- Retry-after for the bucket: `(cost - tokens) / refill_per_s`.
- Compare your output against `solution.py` — mallory should reach `SUSPEND` on the 3rd jailbreak, the scraper should
  `THROTTLE`, and the whale should `BLOCK` on the 2nd expensive job.
