# Exercise: PSI Drift Detector

## Background

Population Stability Index (PSI) is the workhorse metric for detecting that an input distribution has shifted away from the one you calibrated on. It bins both windows over the same edges, compares the *proportion* of data in each bin, and sums a per-bin divergence into a single score. The standard bands are: ≤ 0.10 no drift, 0.10–0.20 moderate, > 0.20 significant.

In this exercise you implement the PSI core: given a baseline window and a current window of numeric feature values (e.g. query lengths), compute PSI and flag drift when it crosses a threshold.

Everything runs offline with the Python standard library only (just `math`). The binning helpers and sample windows are provided; you implement the PSI math and the band/check logic.

## Your Task

Open `exercise.py` and complete the `DriftDetector` class:

1. **`psi(current, eps)`** — bin the `current` window with `self._bin`, convert both `self.baseline_counts` and the current counts to proportions, add `eps` to each to avoid `ln(0)`, and return `Σ (cur% − base%) · ln(cur% / base%)`.
2. **`band(psi_value)`** (static) — return `"no_drift"` for `psi ≤ NO_DRIFT`, `"moderate_drift"` for `psi ≤ MODERATE_DRIFT`, else `"significant_drift"`.
3. **`check(current)`** — return a dict with `psi`, `band`, `drift_detected` (`psi > self.threshold`), and `threshold`.

## Requirements

- Pure standard library — only `math`. No numpy/scipy/pandas, no network.
- Smooth every bin proportion with `eps` so an empty bin never produces `ln(0)` or a divide-by-zero.
- Do not modify the provided `_make_edges`, `_bin`, `BASELINE`, `STABLE_CURRENT`, or `DRIFTED_CURRENT`.
- PSI of the baseline against itself must be ~0 (only the epsilon noise).

## How to Run

```bash
python exercise.py
```

The starter raises `NotImplementedError` until you fill in the `# TODO` sections.

## Expected Output

Running `python solution.py` prints the scores and self-checks with asserts, ending with:

```
=== PSI drift detection ===
baseline vs itself  : PSI=0.0000  band=no_drift
baseline vs stable  : PSI=0.1386  band=moderate_drift  drift=False
baseline vs drifted : PSI=11.3900  band=significant_drift  drift=True

All assertions passed.
```

(The drifted window's PSI is large because every value moved into the out-of-range upper bin — exactly the signal a real detector should fire on.)
