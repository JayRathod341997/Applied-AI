# Exercise: Semantic Response Cache

## Background

LLM calls are expensive in both latency and cost, and production traffic is full of paraphrases — "How do I reset my password?" and "I forgot my password, how can I change it?" want the same answer. An **exact-match** cache misses these because the strings differ.

A **semantic cache** fixes this: it stores `(query_embedding, response)` pairs. When a new query arrives, it is embedded and compared to every stored embedding via **cosine similarity**. If the best match exceeds a similarity threshold, the cached response is returned instead of calling the LLM. Entries also carry a **TTL** so stale answers expire.

In this exercise you build a `SemanticCache` from scratch. To keep everything **offline** (no API keys, no network), you use a provided **mock embedder** — a deterministic bag-of-words hashing vectorizer built on numpy. It is not a real semantic model, but it produces stable vectors where queries sharing words land close together, which is enough to exercise the cache logic.

## Your Task

Open `exercise.py` and implement the `SemanticCache` class:

1. **`_now()`** — return the current time. (Provided; uses `time.monotonic()`. Tests may monkeypatch it.)
2. **`set(query, response)`** — embed the query and store an entry of `(embedding, response, expires_at)` where `expires_at = now + ttl`.
3. **`_cosine(a, b)`** — return the cosine similarity between two numpy vectors. Guard against zero-norm vectors (return `0.0`).
4. **`get(query)`** — embed the query, drop expired entries, then return the response of the most-similar stored entry **if** its similarity ≥ `threshold`; otherwise return `None`. Record a hit or miss in `self.stats`.
5. **`purge_expired()`** — remove entries whose `expires_at` is in the past.

## Requirements

- Use the provided `MockEmbedder` — do **not** call any external API.
- Cosine similarity must handle zero-norm vectors without dividing by zero.
- `get()` must skip expired entries (do not return an expired response).
- Track `self.stats = {"hits": ..., "misses": ...}`.
- The code must import cleanly even before you finish (unimplemented methods raise `NotImplementedError`).
- Use only stdlib + numpy.

## How to Run

```bash
# use a python that has numpy (e.g. the launcher)
py -3 exercise.py     # your work-in-progress
py -3 solution.py     # reference solution with asserts
```

## Expected Output

When complete, `solution.py` prints something like:

```
[set] cached: 'how do i reset my password?'
[get] HIT  (sim=0.87) for 'i forgot my password, how can i change it'
[get] MISS for 'what is the capital of france'
[expiry] entry expired after TTL -> MISS
stats: {'hits': 1, 'misses': 2}
All assertions passed.
```

The exact similarity numbers depend on the mock embedder, but the behavior must hold:

- A **paraphrase** of a cached query is a **hit** (similarity ≥ threshold).
- An **unrelated** query is a **miss** (below threshold).
- After the **TTL** elapses, the same query is a **miss** (entry expired).
