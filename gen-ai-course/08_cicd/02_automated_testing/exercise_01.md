# Exercise: Prompt Regression Test Runner

## Background

A prompt regression suite runs your prompt against a **golden set** of curated cases, scores each output, and produces a single pass/fail **build decision** based on the overall pass-rate. In CI this gate must fail the "build" (exit non-zero) when quality drops, so a regression can't reach users.

In this exercise you build that runner — fully offline. A mock prompt function and a golden set are provided; you implement the scoring and gating.

## Your Task

Open `exercise.py` and complete the `RegressionRunner`:

1. **`keyword_score(output, keywords)`** — return the fraction (0.0–1.0) of `keywords` that appear as substrings of `output`. If `keywords` is empty, return `1.0`.
2. **`score_case(output, case)`** — return a `CaseResult` with the case input, the keyword score, and `passed = score >= case_pass_threshold` (default 0.5).
3. **`run(prompt_fn)`** — run `prompt_fn(input)` for every golden case, score each, and return a `RunReport` containing the per-case results and the overall `pass_rate` (fraction of cases that passed).
4. **`gate(report)`** — return `True` if `report.pass_rate >= self.build_threshold`, else `False`. This is the build decision.

## Requirements

- Scoring is by keyword substring presence — no embeddings, no network, no API keys.
- A case passes when its keyword score ≥ `case_pass_threshold` (default 0.5).
- The build passes when the overall pass-rate ≥ `build_threshold`.
- Must run fully offline (Python standard library only).
- `run` must not mutate the golden set.

## How to Run

```bash
python exercise.py
```

The starter raises `NotImplementedError` until you fill in the `# TODO` sections.

## Expected Output

When finished, running the demo should look something like:

```
=== Good prompt (passes the gate) ===
  PASS  score=1.00  input='Q3 revenue was $4.2B, up 15% YoY...'
  PASS  score=1.00  input='Model v2.1 cut hallucination from...'
  PASS  score=1.00  input='Latency dropped from 800ms to 210ms...'
pass-rate=100% threshold=80% -> BUILD PASSES

=== Regressed prompt (fails the gate) ===
  FAIL  score=0.00  input='Q3 revenue was $4.2B, up 15% YoY...'
  FAIL  score=0.00  input='Model v2.1 cut hallucination from...'
  FAIL  score=0.00  input='Latency dropped from 800ms to 210ms...'
pass-rate=0% threshold=80% -> BUILD FAILS
All assertions passed.
```
