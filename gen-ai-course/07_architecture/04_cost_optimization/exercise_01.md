# Exercise: Token-Cost Estimator + Tiered Router

## Background

You are building the cost layer of an AI gateway. Before a query is sent to a model, the gateway must (a) decide **which model tier** to use based on the query's complexity, and (b) **estimate the dollar cost** of the call using a pricing table. This lets the gateway route cheaply, predict spend, and feed a budget guard.

Token counting should use `tiktoken` when it is installed, but the exercise **must run fully offline** — so you will provide a graceful fallback to a simple word-count tokenizer when `tiktoken` or its encodings are unavailable.

You will work in `exercise.py` (a starter with `# TODO`s) and can check your approach against `solution.py`.

## Your Task

1. **Implement `count_tokens(text)`** — use `tiktoken` if available; otherwise estimate tokens from the whitespace word count (a word is roughly 1.3 tokens). It must never raise on a missing dependency.
2. **Implement `estimate_cost(in_tokens, out_tokens, tier)`** — look up the tier in the provided `PRICING` table and return the dollar cost, given `input_per_1k` and `output_per_1k` prices.
3. **Implement `route_query(query)`** — apply a complexity heuristic (length in words, presence of "hard" keywords, number of question marks / constraints) and return one of the tier names (`"small"`, `"mid"`, `"frontier"`).
4. **Implement `analyze(query, expected_output_tokens)`** — combine the above: count input tokens, pick a tier, estimate cost (assuming `expected_output_tokens` output), and return a small report dict.
5. **Print a table** of several sample queries showing query → chosen tier → estimated cost.

## Requirements

- Must run with **no network and no API keys**.
- `import tiktoken` must be wrapped so the script still runs if it is missing or an encoding cannot load.
- Use the provided `PRICING` dict (do not hardcode prices elsewhere).
- A long/complex query must route to a **higher** tier than a short trivial one.
- Cost for a known token count must match the pricing math exactly.
- Stick to the standard library plus optional `tiktoken`.

## How to Run

```bash
cd "d:/Jay Rathod/Tutorials/Applied AI/gen-ai-course/07_architecture/04_cost_optimization"
python exercise.py     # your work in progress
python solution.py     # reference; runs the demo and asserts
```

## Expected Output

A table similar to (numbers depend on the tokenizer and pricing):

```
TOKENIZER: tiktoken (cl100k_base)   # or: word-count fallback

QUERY                                              TIER       IN   OUT     COST $
--------------------------------------------------------------------------------
What time is it?                                   small       5   20    0.000014
Summarize this paragraph for me.                   small       7   60    0.000040
Design and prove correct a distributed lock ...    frontier   18  400    0.004045
...
All assertions passed.
```
