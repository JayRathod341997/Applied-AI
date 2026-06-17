# Automated Testing for LLM Apps — Concepts

Testing an LLM application is harder than testing normal software for one reason: the output is **probabilistic**. The same prompt can produce different wording every run, so `assert output == expected` is useless. Instead you test *properties* of the output — does it contain the right facts, is it semantically close to a reference, does a judge rate it acceptable — and you run those checks as a **gate** that blocks a regression from shipping. This file walks through the testing pyramid, golden sets, scoring methods, regression gates, and CI wiring.

---

## 1. Traditional vs LLM Testing

| Aspect | Traditional software | LLM applications |
|---|---|---|
| **Output type** | Deterministic | Probabilistic |
| **Assertions** | Exact equality | Keyword / semantic / judge |
| **Flakiness** | Rare (= a bug) | Inherent (non-deterministic) |
| **Failure modes** | Crashes, exceptions | Hallucination, style drift, quality regression |
| **Perf testing** | Latency, throughput | + token cost, + quality |
| **Security** | SQLi, XSS | Prompt injection, data leakage |

The practical consequence: you cannot pin an LLM test to one exact string. You either set `temperature=0` and assert on *content* (keywords, structure), or you measure *similarity* / *judged quality* against a reference and assert it clears a threshold.

---

## 2. The LLM Testing Pyramid

Cheap, fast, deterministic tests at the bottom; slow, expensive, AI-specific tests at the top. Run the bottom on every commit; run the top as a gate before deploy.

```
              ┌───────────────────────┐
              │   Manual / red-team   │  hours · human judgment
              ├───────────────────────┤
              │ Prompt regression /   │  minutes · quality on golden set
              │   eval (LLM-as-judge) │
              ├───────────────────────┤
              │   Integration tests   │  seconds · flows w/ mock LLM
              ├───────────────────────┤
              │      Unit tests       │  ms · parsers, builders, validators
              └───────────────────────┘
```

| Layer | Speed | What it covers | Example |
|---|---|---|---|
| **Unit** | ms | Deterministic logic | Prompt builder, JSON parser, token counter |
| **Integration** | seconds | End-to-end flow with a *mocked* LLM | Pipeline returns a valid label |
| **Prompt regression** | minutes | Output *quality* vs a golden set | Pass-rate ≥ threshold |
| **Manual / red-team** | hours | Edge cases, adversarial inputs | Jailbreaks, PII leakage |

### Unit tests are still deterministic

Most of an LLM app is ordinary code — build it so the deterministic parts can be unit-tested without ever calling a model.

```python
def test_builder_inserts_text():
    out = build_prompt(text="great product", categories=["pos", "neg"])
    assert "great product" in out and "pos" in out

def test_parser_reads_json():
    parsed = parse_classification('{"label": "pos", "confidence": 0.9}')
    assert parsed["label"] == "pos" and parsed["confidence"] == 0.9
```

### Integration tests mock the LLM

To test a flow deterministically and offline, inject a **stub** model so the test never hits the network:

```python
class StubLLM:
    def complete(self, prompt: str) -> str:
        return '{"label": "positive", "confidence": 0.95}'

def test_pipeline_end_to_end():
    pipe = ClassificationPipeline(llm=StubLLM())   # dependency injection
    result = pipe.classify("I love it")
    assert result["label"] in {"positive", "negative", "neutral"}
```

---

## 3. Golden / Reference Sets

A **golden set** is a curated list of `(input, expectation)` cases that define "good." It is the contract your prompt must keep passing. Each case carries the expectation in a form a scorer can check.

```python
GOLDEN = [
    {
        "input": "Q3 revenue was $4.2B, up 15% YoY. Margin improved to 28%.",
        "expected_keywords": ["$4.2B", "15%", "28%"],
        "reference": "Revenue grew 15% YoY to $4.2B at 28% margin",
    },
    {
        "input": "Model v2.1 cut hallucination from 12% to 3.4%.",
        "expected_keywords": ["12%", "3.4%"],
        "reference": "Hallucination dropped from 12% to 3.4% in v2.1",
    },
]
```

**Curation principles:** cover the common cases *and* the known-tricky ones; keep it small enough to run in CI minutes; treat it as versioned source (it lives in Git); grow it every time a real bug escapes — each escaped bug becomes a new golden case so it can never silently return.

---

## 4. Scoring Methods

How do you decide a single output "passes"? Three escalating methods, often combined:

| Method | How | Cost | Catches | Misses |
|---|---|---|---|---|
| **Exact / keyword** | substring / regex match | free | missing facts, format | paraphrase, nuance |
| **Semantic similarity** | embedding cosine ≥ τ | cheap | paraphrase equivalence | factual subtleties |
| **LLM-as-judge** | ask a model to grade | $ + latency | nuance, reasoning quality | judge bias, non-determinism |

```python
def keyword_score(output: str, keywords: list[str]) -> float:
    """Fraction of required keywords present (0.0–1.0)."""
    hits = sum(1 for k in keywords if k in output)
    return hits / len(keywords) if keywords else 1.0
```

**LLM-as-judge** uses a (usually stronger) model to rate an output against a rubric or reference — invaluable for "is this answer good?" where keywords can't capture nuance. Guard it: pin `temperature=0`, give an explicit rubric, ask for a numeric score + reason, and remember the judge is itself non-deterministic and can be biased (e.g. toward longer answers). A test that passes can still be *evaluated*; combining a cheap keyword check with a judge for borderline cases controls cost.

```
output ──► keyword score ──► ≥ τ? ──pass─────────────────► PASS
                              │ no
                              ▼
                       LLM-as-judge ──► score ≥ τ? ──► PASS / FAIL
```

---

## 5. Regression Gate

A regression gate turns per-case scores into one **build decision**: compute the **pass-rate** across the golden set and fail the build if it drops below a threshold. This is the AI-specific quality gate that standard pipelines lack.

```python
def run_gate(prompt_fn, golden, threshold=0.8) -> bool:
    passed = 0
    for case in golden:
        out = prompt_fn(case["input"])
        if keyword_score(out, case["expected_keywords"]) >= 0.5:
            passed += 1
    pass_rate = passed / len(golden)
    print(f"pass-rate {pass_rate:.0%} (threshold {threshold:.0%})")
    return pass_rate >= threshold    # False -> CI fails the build
```

The gate must **exit non-zero** in CI when it fails, so the pipeline stops and deployment is blocked. (This pass-rate gate is exactly what you build in the exercise.)

---

## 6. CI Pipelines (GitHub Actions / Azure DevOps)

The gate runs as a stage after unit/integration tests and *before* the container build, so a quality regression can never reach packaging.

```
Source → Build → Unit/Integration → ► EVAL GATE ◄ → Package → Deploy
                                       (golden set)
                                    fail = stop pipeline
```

**GitHub Actions** — the eval job `needs` the test job; a failing gate fails the job and blocks downstream:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest tests/unit tests/integration

  eval-gate:
    needs: test                       # only runs if tests pass
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python scripts/run_gate.py --threshold 0.80   # exits 1 on fail
```

**Azure DevOps** — the same idea with stages and a `condition` that blocks deploy unless the eval stage passed:

```yaml
stages:
  - stage: Test
    jobs: [ ... unit + integration ... ]
  - stage: Eval
    dependsOn: Test
    jobs: [ ... run golden-set gate, exit non-zero on fail ... ]
  - stage: Deploy
    dependsOn: Eval
    condition: succeeded()            # deploy only if the gate passed
```

| | GitHub Actions | Azure DevOps |
|---|---|---|
| **Sequencing** | `needs:` between jobs | `dependsOn:` between stages |
| **Conditional** | `if:` | `condition:` |
| **Secrets** | repo/org secrets | variable groups + Key Vault |
| **Best for** | GitHub-centric teams | enterprise Azure ecosystems |

---

## Key Takeaways

- **LLM outputs are probabilistic** — never `assert ==` on raw text; assert on content, similarity, or a judge's score against a threshold.
- **Follow the pyramid:** many fast deterministic unit tests, integration tests with a *mocked* LLM, then a slower prompt-regression eval; manual red-teaming at the top.
- **A golden set is your contract.** Curate common + tricky cases, version it, and add every escaped bug as a new case.
- **Pick the scorer to fit the check:** keyword for facts/format, semantic similarity for paraphrase, LLM-as-judge for nuance (with a pinned rubric and cost control).
- **The regression gate is the AI-specific CI stage** — it computes a pass-rate over the golden set and must exit non-zero to block deployment when quality drops.
