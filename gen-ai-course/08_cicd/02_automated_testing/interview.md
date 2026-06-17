# Automated Testing for LLM Apps — Interview Questions

Interview questions and model answers on testing LLM applications: the testing pyramid, golden sets, scoring methods, regression gates, and CI.

---

## 1. Why is testing an LLM app fundamentally different from testing normal software?

**Answer:** LLM outputs are **probabilistic** — the same input can produce different wording each run — so exact-equality assertions are useless. Failure modes are also different: instead of crashes you get hallucinations, style drift, and quality regressions. Tests must therefore assert on *properties* of the output (keywords, structure, semantic similarity, a judge's score) and treat some flakiness as inherent rather than a bug.

---

## 2. Describe the LLM testing pyramid.

**Answer:** From bottom (cheap, fast, deterministic) to top (slow, expensive, AI-specific):

1. **Unit tests** (ms) — deterministic logic: prompt builders, parsers, validators.
2. **Integration tests** (seconds) — end-to-end flow with a *mocked* LLM.
3. **Prompt regression / eval** (minutes) — output quality against a golden set.
4. **Manual / red-team** (hours) — edge cases, adversarial inputs, jailbreaks.

Run the base on every commit; run the top layers as gates before deploy.

---

## 3. How do you keep most of an LLM app unit-testable?

**Answer:** Most of the app is ordinary code. Structure it so the deterministic parts — prompt construction, output parsing, validation, routing — are pure functions you can test without ever calling a model. Inject the LLM as a dependency so integration tests can swap in a stub. The fewer behaviours that *require* a live model, the more of your suite stays fast and deterministic.

---

## 4. How do you test a pipeline end-to-end without hitting a real model?

**Answer:** Dependency-inject a **stub LLM** that returns a fixed, well-formed response. The test then verifies the surrounding logic — parsing, branching, error handling, output schema — deterministically and offline. This is the standard way to make integration tests fast, free, and reproducible in CI.

---

## 5. What is a golden set and how do you curate one?

**Answer:** A golden (reference) set is a curated list of `(input, expectation)` cases that defines acceptable output — your prompt's contract. Curation principles: cover common cases *and* known-tricky ones; keep it small enough to run in CI minutes; version it in Git; and **grow it from incidents** — every bug that escapes to production becomes a new golden case so it can never silently return.

---

## 6. Compare the main output-scoring methods.

**Answer:**

| Method | Catches | Misses | Cost |
|---|---|---|---|
| **Exact / keyword** | missing facts, format | paraphrase | free |
| **Semantic similarity** | paraphrase equivalence | factual subtleties | cheap |
| **LLM-as-judge** | nuance, reasoning quality | judge bias/noise | $$ |

They are complementary: keyword checks for required facts, similarity for "means the same thing," and a judge for "is this actually good?"

---

## 7. What is LLM-as-judge and how do you make it reliable?

**Answer:** You use a (usually stronger) model to grade an output against a rubric or reference. To make it reliable: pin `temperature=0`, give an explicit scoring rubric, ask for a numeric score plus a short rationale, and validate against human labels periodically. Be aware the judge is itself non-deterministic and biasable (e.g. it may favour longer or more confident answers), so it complements — not replaces — cheaper checks.

---

## 8. How do you control the cost of LLM-as-judge in CI?

**Answer:** Tier it: run cheap keyword/similarity checks first and only invoke the judge for borderline cases that those checks can't decide. Keep the golden set small, cache judge verdicts for unchanged outputs, and use a smaller judge model where the rubric is simple. The judge is the expensive top of the pyramid — minimize how often you pay for it.

---

## 9. What is a regression gate and how does it make a build decision?

**Answer:** A regression gate runs the prompt over the golden set, scores each case, and aggregates into an overall **pass-rate**. If the pass-rate is below a configured threshold, the gate fails. In CI it must **exit non-zero** so the pipeline stops and deployment is blocked — turning per-case scores into a single, automated go/no-go.

---

## 10. Where does the eval gate belong in a CI pipeline, and why there?

**Answer:** After unit/integration tests pass and **before** the container build/deploy. Placing it there means a quality regression is caught before it can be packaged or reach users, while not wasting expensive eval cycles on code that already fails cheap deterministic tests. The downstream deploy stage is conditioned on the gate succeeding.

---

## 11. How do you sequence stages so a failing gate blocks deployment in GitHub Actions vs Azure DevOps?

**Answer:** In **GitHub Actions**, use `needs:` between jobs — `eval-gate` has `needs: test`, and `deploy` has `needs: eval-gate`, so a failing gate stops the chain. In **Azure DevOps**, use `dependsOn:` between stages plus a `condition: succeeded()` on the deploy stage so it only runs if the eval stage passed.

---

## 12. How do you handle the inherent flakiness of non-deterministic outputs in tests?

**Answer:** Reduce randomness where you can (set `temperature=0` for tests), assert on thresholds rather than exact strings, and aggregate across the golden set (pass-rate) instead of demanding every single case pass. For genuinely stochastic behaviour, run a case multiple times and assert a *success ratio*, and set thresholds with margin so normal variance doesn't flip the build.

---

## 13. What security failure modes should LLM testing specifically cover?

**Answer:** LLM-specific ones: **prompt injection** (untrusted input hijacking instructions), **data leakage** (the model revealing system prompts or other users' data), and **jailbreaks** that bypass safety guardrails. These need red-team / guardrail tests — adversarial inputs plus output validators — on top of classic checks. They have no equivalent in traditional SQLi/XSS testing.

---

## 14. Your prompt-regression suite is flaky and slow, blocking the team. What do you do?

**Answer:** Diagnose the cause. For flakiness: pin temperature, switch exact matches to threshold-based scoring, and aggregate to a pass-rate. For speed: shrink the golden set to the highest-signal cases, tier expensive judge calls behind cheap checks, cache verdicts, and run the heavy eval only on the deploy path (not every commit) while keeping fast unit/integration tests on every push. The goal is a gate that is both trustworthy and fast enough to keep in the loop.

---

## Summary

Test LLM apps on properties not exact strings; follow the pyramid (unit → integration with mocks → prompt regression → red-team); curate and grow a golden set; score with keyword/semantic/judge methods chosen to fit the check; and gate the build on an aggregate pass-rate that exits non-zero to block deployment.
