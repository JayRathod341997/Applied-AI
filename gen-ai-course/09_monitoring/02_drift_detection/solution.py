"""Solution: a Population Stability Index (PSI) drift detector.

Implements `DriftDetector`, which bins a baseline window and a current window
over fixed bin edges, computes PSI between them, and flags drift when PSI
exceeds a threshold (default 0.2).

Pure standard library (math only). Runs fully OFFLINE. The bottom of the file
runs a demo over fixed windows and asserts the expected PSI bands.

Run with:  python solution.py
"""

from __future__ import annotations

import math

# Standard PSI interpretation bands.
NO_DRIFT = 0.10
MODERATE_DRIFT = 0.20


# ---------------------------------------------------------------------------
# Fixed offline sample windows (no numpy / no randomness in the assertions).
# Baseline query lengths cluster low; the drifted window shifts higher.
# ---------------------------------------------------------------------------
BASELINE = [
    10, 12, 14, 15, 16, 18, 19, 20, 21, 22,
    23, 24, 25, 26, 27, 28, 29, 30, 31, 32,
]
# Same shape, just shifted later in time (no drift) — copy with tiny jitter.
STABLE_CURRENT = [
    11, 13, 14, 15, 17, 18, 19, 20, 21, 22,
    23, 24, 25, 26, 27, 28, 29, 30, 31, 33,
]
# Clearly shifted distribution (drift).
DRIFTED_CURRENT = [
    40, 42, 44, 45, 46, 48, 49, 50, 51, 52,
    53, 54, 55, 56, 57, 58, 59, 60, 61, 62,
]


class DriftDetector:
    """PSI-based drift detector over fixed bin edges.

    Bin edges are derived from the baseline window so that PSI compares like
    for like. Counts are smoothed with an epsilon to avoid ln(0)/divide-by-zero
    when a bin is empty in one window.
    """

    def __init__(self, baseline: list[float], bins: int = 10, threshold: float = MODERATE_DRIFT):
        if len(baseline) < bins:
            raise ValueError("baseline needs at least `bins` samples")
        self.baseline = list(baseline)
        self.bins = bins
        self.threshold = threshold
        self.bin_edges = self._make_edges(self.baseline, bins)
        self.baseline_counts = self._bin(self.baseline)

    @staticmethod
    def _make_edges(values: list[float], bins: int) -> list[float]:
        """Equal-width bin edges spanning the baseline range.

        Returns `bins + 1` edges. The outer edges are pushed to +/- inf so
        out-of-range current values still land in the first/last bin.
        """
        lo, hi = min(values), max(values)
        if hi == lo:  # degenerate: widen so we still have a span
            hi = lo + 1.0
        width = (hi - lo) / bins
        edges = [lo + i * width for i in range(bins + 1)]
        edges[0] = -math.inf
        edges[-1] = math.inf
        return edges

    def _bin(self, values: list[float]) -> list[int]:
        """Count how many values fall into each bin defined by bin_edges."""
        counts = [0] * self.bins
        for v in values:
            placed = False
            for i in range(self.bins):
                # bin i covers [edge_i, edge_{i+1}); last bin is inclusive.
                if self.bin_edges[i] <= v < self.bin_edges[i + 1]:
                    counts[i] += 1
                    placed = True
                    break
            if not placed:  # equals the +inf upper edge -> last bin
                counts[-1] += 1
        return counts

    def psi(self, current: list[float], eps: float = 1e-6) -> float:
        """PSI between the stored baseline and a current window."""
        cur_counts = self._bin(current)
        b_tot = sum(self.baseline_counts) or 1
        c_tot = sum(cur_counts) or 1
        score = 0.0
        for b, c in zip(self.baseline_counts, cur_counts):
            b_pct = b / b_tot + eps
            c_pct = c / c_tot + eps
            score += (c_pct - b_pct) * math.log(c_pct / b_pct)
        return score

    @staticmethod
    def band(psi_value: float) -> str:
        """Map a PSI score to its standard interpretation band."""
        if psi_value <= NO_DRIFT:
            return "no_drift"
        if psi_value <= MODERATE_DRIFT:
            return "moderate_drift"
        return "significant_drift"

    def check(self, current: list[float]) -> dict:
        """Return the PSI, its band, and whether it exceeds the threshold."""
        value = self.psi(current)
        return {
            "psi": value,
            "band": self.band(value),
            "drift_detected": value > self.threshold,
            "threshold": self.threshold,
        }


# ---------------------------------------------------------------------------
# Demonstration + assertions.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    detector = DriftDetector(BASELINE, bins=10, threshold=0.2)

    stable = detector.check(STABLE_CURRENT)
    drifted = detector.check(DRIFTED_CURRENT)
    same = detector.check(BASELINE)  # comparing baseline to itself

    print("=== PSI drift detection ===")
    print(f"baseline vs itself  : PSI={same['psi']:.4f}  band={same['band']}")
    print(f"baseline vs stable  : PSI={stable['psi']:.4f}  band={stable['band']}  "
          f"drift={stable['drift_detected']}")
    print(f"baseline vs drifted : PSI={drifted['psi']:.4f}  band={drifted['band']}  "
          f"drift={drifted['drift_detected']}")

    # --- assertions ---
    # Baseline vs itself: PSI is ~0 (only the epsilon smoothing).
    assert same["psi"] < NO_DRIFT
    assert same["band"] == "no_drift"
    assert same["drift_detected"] is False

    # A nearly-identical window should not flag drift.
    assert stable["drift_detected"] is False
    assert stable["psi"] <= MODERATE_DRIFT

    # A clearly shifted window must flag significant drift.
    assert drifted["drift_detected"] is True
    assert drifted["band"] == "significant_drift"
    assert drifted["psi"] > MODERATE_DRIFT

    # PSI is non-negative and the drifted score dwarfs the stable one.
    assert drifted["psi"] > stable["psi"]

    # Band mapping is correct at the boundaries.
    assert DriftDetector.band(0.05) == "no_drift"
    assert DriftDetector.band(0.15) == "moderate_drift"
    assert DriftDetector.band(0.30) == "significant_drift"

    print("\nAll assertions passed.")
