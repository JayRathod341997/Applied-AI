# Drift Detection — Concepts

A model that was accurate on launch day slowly rots. Not because the weights changed, but because the *world* changed around them: users ask new things, documents get updated, vocabulary shifts, and the provider silently swaps the model behind the API. **Drift** is this gradual divergence between the data and behaviour you calibrated on and the data and behaviour you see in production. This file covers the kinds of drift, the statistical tests that detect them (with a worked PSI example), embedding drift, and what to do when drift fires.

---

## 1. What Is Drift?

Drift is a change over time in the statistical properties of inputs, outputs, or the input→output relationship. Left undetected it quietly degrades quality long before anything "breaks".

```
Calibration window (baseline)        Production window (current)
  query lengths ~ N(50, 10)            query lengths ~ N(70, 15)
        ▁▂▅█▅▂▁                               ▁▂▃▅█▆▄▂▁
        └────── same distribution? ──────┘
                       │
                       ▼
            drift score (e.g. PSI) > threshold  →  alert
```

The detection recipe is always the same: pick a **baseline** distribution, compare a **current** window against it with a divergence metric, and **flag** when the divergence exceeds a threshold.

---

## 2. Types of Drift

| Drift type | What changes | LLM example | Detection signal |
|---|---|---|---|
| **Data / feature drift** | Input distribution `P(X)` | New topics, longer queries, new language | PSI / KS on input features or embeddings |
| **Concept drift** | Relationship `P(Y\|X)` | Same query, the "right" answer has changed | Quality-metric trend, change-point tests |
| **Target / label drift** | Output distribution `P(Y)` | Class mix shifts in a classifier head | PSI / chi-square on outputs |
| **Embedding drift** | Semantic distribution of vectors | New domain vocabulary shifts centroids | Cosine distance between centroids |
| **Prompt drift** | Effective prompt stops working | Template degrades after a model update | A/B quality scores over time |
| **Model drift** | Provider changes the model | Silent version bump changes outputs | Output-distribution comparison |

### Temporal shapes of concept drift

```
Sudden      Gradual        Recurring        Blip
 ──┐         ──╲             ╱╲  ╱╲  ╱╲      ──┐ ┌──
   └──         ╲──          ╱  ╲╱  ╲╱  ╲       └─┘
abrupt jump   slow slide    seasonal/cyclic   transient spike
```

- **Sudden** — a policy change or news event flips behaviour overnight.
- **Gradual** — user behaviour slowly evolves over weeks.
- **Recurring** — seasonal patterns (holiday traffic, quarterly cycles).
- **Blip** — a one-off anomaly that should *not* trigger retraining.

---

## 3. Detection Methods

| Method | Data type | Output | When to use |
|---|---|---|---|
| **PSI** (Population Stability Index) | Binned continuous/categorical | Single score | The workhorse for feature drift |
| **KS test** (Kolmogorov–Smirnov) | Continuous | Statistic + p-value | Two-sample distribution comparison |
| **Chi-square** | Categorical | Statistic + p-value | Class/category distribution shifts |
| **KL divergence** | Probability distributions | Score (asymmetric) | Information-loss between distributions |
| **Cosine distance of centroids** | Embeddings | Score in [0, 2] | Embedding / semantic drift |

### Population Stability Index (PSI) — the workhorse

PSI compares how the **proportion** of data in each bin changed between baseline and current windows:

```
PSI = Σ  (current% − baseline%) × ln( current% / baseline% )
      bins
```

Interpretation (the standard credit-risk thresholds, widely reused in ML):

| PSI | Meaning | Action |
|---|---|---|
| ≤ 0.10 | No significant drift | Keep monitoring |
| 0.10 – 0.20 | Moderate drift | Investigate, watch closely |
| > 0.20 | Significant drift | Act — retrain / refresh |

**Worked example.** Bin a feature into 4 bins. Baseline vs current proportions:

| Bin | baseline% | current% | diff | ln(cur/base) | contribution |
|---|---|---|---|---|---|
| 1 | 0.40 | 0.20 | −0.20 | ln(0.50) = −0.693 | 0.1386 |
| 2 | 0.30 | 0.30 |  0.00 | ln(1.00) =  0.000 | 0.0000 |
| 3 | 0.20 | 0.30 | +0.10 | ln(1.50) =  0.405 | 0.0405 |
| 4 | 0.10 | 0.20 | +0.10 | ln(2.00) =  0.693 | 0.0693 |
| | | | | **PSI** | **≈ 0.248** |

PSI ≈ 0.248 > 0.20 → significant drift. Note that the metric *needs every bin to be non-empty*: if a current bin is 0, `ln(0)` is `−inf`. The fix is a tiny smoothing constant (epsilon) added to every bin proportion.

```python
import math

def psi(baseline_counts, current_counts, eps=1e-6):
    """PSI from two equal-length lists of per-bin counts."""
    b_tot = sum(baseline_counts) or 1
    c_tot = sum(current_counts) or 1
    score = 0.0
    for b, c in zip(baseline_counts, current_counts):
        b_pct = b / b_tot + eps      # smoothing avoids ln(0)/divide-by-zero
        c_pct = c / c_tot + eps
        score += (c_pct - b_pct) * math.log(c_pct / b_pct)
    return score
```

### KS test (intuition)

The Kolmogorov–Smirnov statistic is the **maximum gap between the two cumulative distribution functions**. Bigger gap = more drift. It needs no binning, which makes it convenient for continuous data, but it is less interpretable than PSI's single bounded-ish score.

```
CDF
1.0│        ___________ current
   │      _/  ┊ D = max gap
   │    _/    ↕
   │  _/    _/  baseline
0.0│_/____/_______________→ value
```

---

## 4. Embedding Drift

For text, the richest drift signal lives in the **embedding space**. Track the centroid (mean vector) of a baseline batch versus a current batch; a growing cosine distance means the *semantics* of incoming queries are moving.

```
embedding space (2-D projection)

baseline cluster        current cluster
     ● ● ●                     ○ ○
    ● ●(C_b)● ─────────────► (C_c)○ ○
     ● ● ●                   ○ ○ ○
            cosine_distance(C_b, C_c) grows  → embedding drift
```

```python
import math

def cosine_distance(u, v):
    dot = sum(a * b for a, b in zip(u, v))
    nu = math.sqrt(sum(a * a for a in u))
    nv = math.sqrt(sum(b * b for b in v))
    return 1.0 - dot / (nu * nv) if nu and nv else 1.0

def centroid(vectors):
    n = len(vectors)
    dim = len(vectors[0])
    return [sum(v[i] for v in vectors) / n for i in range(dim)]
```

Embedding drift is the early-warning system for RAG: when query semantics move outside what your index covers, retrieval quality drops *before* users complain.

---

## 5. From Detection to Action: Retraining Triggers

Detecting drift is only useful if it drives a decision. Combine signals into a trigger.

```
        ┌─────────────┐   PSI > 0.2  ┌──────────────┐
inputs ─►│ drift detect │────────────►│ retrain /    │
        │ PSI, KS,    │   centroid    │ refresh KB / │──► deploy
        │ embeddings, │──── dist ────►│ update prompt │    canary
        │ quality     │   quality↓    └──────────────┘
        └─────────────┘
```

| Strategy | Type | Description |
|---|---|---|
| **Threshold trigger** | Reactive | Retrain when PSI or quality crosses a line |
| **Scheduled refresh** | Proactive | Periodic re-index / re-train on a cadence |
| **Canary deploy** | Proactive | Roll a candidate to a small % and compare |
| **Fallback model** | Reactive | Switch to a simpler/safer model on degradation |
| **Human escalation** | Reactive | Route low-confidence cases to a human |

### Online vs offline detection

| Aspect | Offline | Online |
|---|---|---|
| Timing | Batch / post-hoc | Streaming / real-time |
| Latency to alert | Hours–days | Seconds–minutes |
| Use case | Model evaluation, audits | Production guardrails |

---

## 6. Pitfalls

- **Empty bins** crash PSI/KL via `ln(0)` — always smooth with an epsilon.
- **Window size matters**: too small a current window is noisy (false positives); too large is sluggish (slow detection).
- **Blips are not drift**: a transient spike should not trigger an expensive retrain — require the signal to persist (a `for:`-style sustain window).
- **Multiple comparisons**: testing many features inflates false positives; correct thresholds or aggregate.
- **Drift ≠ degradation**: a distribution can shift while quality stays fine. Pair input-drift detection with an output-quality signal before acting.

---

## Key Takeaways

- **Drift is gradual divergence**, not a crash: inputs (`P(X)`), outputs (`P(Y)`), or the relationship (`P(Y|X)`) move away from your baseline and quietly erode quality.
- **The recipe is universal**: baseline distribution → compare current window with a divergence metric → flag past a threshold.
- **PSI is the workhorse**: `Σ (cur% − base%) · ln(cur%/base%)`; ≤ 0.1 fine, 0.1–0.2 watch, > 0.2 act. Always add an epsilon to avoid `ln(0)`.
- **Embedding drift is RAG's early warning**: a rising cosine distance between baseline and current centroids predicts retrieval-quality drops before users do.
- **Detection must drive action**: wire scores into retraining triggers, scheduled refreshes, canaries, or fallbacks — and require persistence so a blip does not trigger a retrain.
- **Pair input drift with output quality**: a shifted input distribution is only a problem if quality actually drops, so confirm before you act.
