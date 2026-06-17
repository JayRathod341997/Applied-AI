# Exercise: LLM Gateway with Fallback Chain

## Background

In production you rarely call a single model provider directly. Vendors have outages, rate limits, and latency spikes — so robust AI systems route every request through a **gateway** that hides the provider behind one interface and *falls back* to another provider when the primary fails.

In this exercise you will build a small, offline gateway that:

1. Treats every provider through one common interface (`complete(prompt) -> str`).
2. Tries providers in priority order — **primary → secondary → tertiary** — and returns the first success.
3. Counts how many times each provider was *called*, so you can observe the fallback behaviour.

Everything runs offline using mock providers that are already written for you. You only implement the gateway.

## Your Task

Open `exercise.py` and complete the `LLMGateway` class:

1. **Store the providers** in the order they are passed (index 0 is the primary).
2. **Initialize a call counter** — a dict mapping each provider's `name` to `0`.
3. **Implement `complete(prompt)`:**
   - Iterate through providers in order.
   - Increment that provider's call count *before* calling it.
   - `try` calling `provider.complete(prompt)`; on success, return the result immediately.
   - On any `Exception`, remember the error and continue to the next provider.
   - If every provider fails, raise a `RuntimeError` that includes the last error.
4. **Implement `stats()`** to return the call-count dict (a copy, so callers can't mutate internal state).

## Requirements

- Do not modify the provided `MockProvider` classes.
- The gateway must be provider-agnostic — it must work for any object exposing `name` and `complete()`.
- Must run fully offline with no API keys and no network access.
- The fallback chain must stop at the first success (do not call later providers unnecessarily).

## How to Run

```bash
python exercise.py
```

The starter raises `NotImplementedError` until you fill in the `# TODO` sections, so it imports cleanly but the demo will fail until complete.

## Expected Output

When finished, running the demo should look something like:

```
=== Demo 1: primary succeeds ===
Result: [openai] Echo: hello world
Call counts: {'openai': 1, 'anthropic': 0, 'local-llama': 0}

=== Demo 2: primary fails, secondary succeeds ===
Result: [anthropic] Echo: ping
Call counts: {'openai': 1, 'anthropic': 1, 'local-llama': 0}

=== Demo 3: primary + secondary fail, tertiary succeeds ===
Result: [local-llama] Echo: hi
Call counts: {'openai': 1, 'anthropic': 1, 'local-llama': 1}

All providers down raises RuntimeError as expected.
```
