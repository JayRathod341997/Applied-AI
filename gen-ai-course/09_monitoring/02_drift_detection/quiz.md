# Quiz

## Question 1

What type of drift occurs when the embedding model is updated and vector representations change?

A) Data drift
B) Concept drift
C) Embedding drift
D) Target drift

---

**Answer: C**

Embedding drift specifically refers to changes in vector representations — caused by a new embedding model version, tokenizer change, or fine-tune. Previously-similar items can become dissimilar, silently degrading retrieval.

---

## Question 2

Which statistical method is the common workhorse for measuring distribution shift in feature drift detection?

A) Chi-Squared Test
B) Population Stability Index (PSI)
C) T-Test
D) ANOVA

---

**Answer: B**

PSI bins both windows over the same edges and sums a per-bin divergence into one interpretable score (≤0.1 fine, 0.1–0.2 watch, >0.2 act). It originated in credit-risk monitoring and is now standard across ML drift detection.

---

## Question 3

What is "sudden drift" in concept drift?

A) Gradual changes over months
B) Abrupt, immediate changes
C) Periodic seasonal patterns
D) A temporary anomaly that reverts

---

**Answer: B**

Sudden drift is an abrupt shift in behaviour, often triggered by a discrete event — a policy change, a product launch, or a news event. It contrasts with gradual (slow slide), recurring (seasonal), and blip (transient) shapes.

---

## Question 4

Which symptom most directly indicates knowledge base staleness in a RAG system?

A) Increased CPU usage
B) Higher GPU temperature
C) Retrieval returning irrelevant or outdated documents
D) Longer container start times

---

**Answer: C**

When the indexed content no longer covers what users ask, retrieval surfaces irrelevant or outdated chunks, average similarity scores fall, and zero-result rates rise. That is the staleness signal — unrelated to infrastructure metrics like CPU.

---

## Question 5

The PSI formula is `Σ (current% − baseline%) × ln(current% / baseline%)`. Why must you add a small epsilon to each bin proportion?

A) To make PSI larger on purpose
B) To avoid `ln(0)` and divide-by-zero when a bin is empty in one window
C) Because PSI must always be negative
D) Epsilon converts PSI to a p-value

---

**Answer: B**

If a bin has zero observations in the current (or baseline) window, the proportion is 0, and `ln(0)` is `−inf` (and `cur%/base%` may divide by zero). A tiny smoothing constant on every proportion keeps the logarithm finite without materially changing a real score.

---

## Question 6

A feature's PSI between baseline and the current window is 0.27. Using the standard bands, what should you do?

A) Nothing — this is within normal variation
B) Watch it closely but take no action
C) Treat it as significant drift and act (investigate / retrain / refresh)
D) Immediately roll back all infrastructure

---

**Answer: C**

PSI > 0.20 is the "significant drift" band, signalling the distribution has materially shifted. The right response is to investigate and act — retrain, refresh the knowledge base, or update the prompt — typically behind a canary.

---

## Question 7

What is concept drift, as distinct from data drift?

A) The input distribution `P(X)` changes
B) The relationship `P(Y|X)` between input and the correct output changes
C) The server's clock drifts
D) The embedding dimensionality changes

---

**Answer: B**

Data (feature) drift is a change in the inputs themselves, `P(X)`. Concept drift is subtler: the same input now maps to a different correct answer — `P(Y|X)` has changed — for example when user expectations or ground truth evolve. It is detected via quality-metric trends and change-point tests rather than input statistics alone.

---

## Question 8

How is embedding drift typically quantified between a baseline batch and a current batch of texts?

A) By counting the number of tokens
B) By the cosine distance between the two batches' centroid (mean) vectors
C) By measuring GPU memory usage
D) By the HTTP status code distribution

---

**Answer: B**

You compute each batch's centroid (mean embedding) and track the cosine distance between them over time. A growing distance means incoming queries are moving semantically — RAG's early warning that the index may no longer cover them.

---

## Question 9

Why should a single transient spike ("blip") usually NOT trigger an expensive model retrain?

A) Blips never affect users
B) Retraining is free, so it does not matter
C) A blip is a temporary anomaly that reverts; requiring the signal to persist avoids wasteful, churny retrains
D) PSI cannot detect blips

---

**Answer: C**

Blips are transient and self-correct. Reacting to every spike causes alert fatigue and pointless, risky retrains. A robust trigger requires the drift signal to persist over a sustain window before acting — the same principle as a `for:` duration on an alert.

---

## Question 10

Why should input-drift detection be paired with an output-quality signal before triggering action?

A) Quality signals are cheaper than drift detection
B) A distribution can shift while output quality stays fine — drift is not the same as degradation
C) Output quality replaces the need for any drift detection
D) Regulators require exactly two signals

---

**Answer: B**

Detecting that inputs moved does not prove the system got worse; the model may handle the new distribution well. Confirming with an output-quality metric (e.g. relevance, faithfulness, or user satisfaction) prevents acting on harmless shifts and reduces false-positive retrains.
