"""Exercise: a Population Stability Index (PSI) drift detector.

You will build a `DriftDetector` that bins a baseline window and a current
window over fixed bin edges, computes PSI between them, and flags drift when
PSI exceeds a threshold (default 0.2).

Pure standard library (math only). Everything runs OFFLINE. The sample windows
and helper constants are provided. Complete only the `# TODO` sections.

Run with:  python exercise.py
"""

from __future__ import annotations

import math

# Standard PSI interpretation bands.
NO_DRIFT = 0.10
MODERATE_DRIFT = 0.20


# ---------------------------------------------------------------------------
# Provided: fixed offline sample windows. Do NOT modify these.
# ---------------------------------------------------------------------------
BASELINE = [
    10, 12, 14, 15, 16, 18, 19, 20, 21, 22,
    23, 24, 25, 26, 27, 28, 29, 30, 31, 32,
]
STABLE_CURRENT = [
    11, 13, 14, 15, 17, 18, 19, 20, 21, 22,
    23, 24, 25, 26, 27, 28, 29, 30, 31, 33,
]
DRIFTED_CURRENT = [
    40, 42, 44, 45, 46, 48, 49, 50, 51, 52,
    53, 54, 55, 56, 57, 58, 59, 60, 61, 62,
]


class DriftDetector:
    """PSI-based drift detector over fixed bin edges."""

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

        Return `bins + 1` edges; push the outer edges to -inf / +inf so that
        out-of-range current values still land in the first/last bin.
        """
        lo, hi = min(values), max(values)
        if hi == lo:
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
                if self.bin_edges[i] <= v < self.bin_edges[i + 1]:
                    counts[i] += 1
                    placed = True
                    break
            if not placed:  # equals the +inf upper edge -> last bin
                counts[-1] += 1
        return counts

    def psi(self, current: list[float], eps: float = 1e-6) -> float:
        """PSI between the stored baseline and a current window.

        PSI = sum over bins of (cur% - base%) * ln(cur% / base%).
        Add `eps` to every proportion to avoid ln(0) / divide-by-zero.
        """
        # TODO: bin `current`, convert counts to smoothed proportions, sum PSI.
        raise NotImplementedError("TODO: compute PSI between baseline and current")

    @staticmethod
    def band(psi_value: float) -> str:
        """Map a PSI score to 'no_drift' / 'moderate_drift' / 'significant_drift'."""
        # TODO: return the band using NO_DRIFT and MODERATE_DRIFT thresholds.
        raise NotImplementedError("TODO: map a PSI score to its band")

    def check(self, current: list[float]) -> dict:
        """Return {psi, band, drift_detected, threshold}."""
        # TODO: compute psi, band, and whether psi exceeds self.threshold.
        raise NotImplementedError("TODO: assemble the drift check result")


# ---------------------------------------------------------------------------
# Demonstration of intended usage.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    detector = DriftDetector(BASELINE, bins=10, threshold=0.2)

    stable = detector.check(STABLE_CURRENT)
    drifted = detector.check(DRIFTED_CURRENT)

    print("=== PSI drift detection ===")
    print(f"baseline vs stable  : PSI={stable['psi']:.4f}  band={stable['band']}  "
          f"drift={stable['drift_detected']}")
    print(f"baseline vs drifted : PSI={drifted['psi']:.4f}  band={drifted['band']}  "
          f"drift={drifted['drift_detected']}")
