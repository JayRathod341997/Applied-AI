"""Exercise: a prompt regression test runner.

You will build a `RegressionRunner` that runs a (mock) prompt function against a
golden set, scores each output by keyword presence, computes an overall
pass-rate, and produces a build pass/fail decision (the regression gate).

Everything runs OFFLINE (Python standard library only). The mock prompt
functions and the golden set are provided. Complete only the `# TODO` sections.

Run with:  python exercise.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


# ---------------------------------------------------------------------------
# Provided: golden set + mock prompt functions. Do NOT modify these.
# ---------------------------------------------------------------------------
GOLDEN_SET = [
    {
        "input": "Q3 revenue was $4.2B, up 15% YoY. Margin improved to 28%.",
        "expected_keywords": ["$4.2B", "15%", "28%"],
    },
    {
        "input": "Model v2.1 cut hallucination from 12% to 3.4%.",
        "expected_keywords": ["12%", "3.4%"],
    },
    {
        "input": "Latency dropped from 800ms to 210ms after caching.",
        "expected_keywords": ["800ms", "210ms"],
    },
]


def good_prompt_fn(text: str) -> str:
    """A 'good' summarizer mock: echoes the input, so all keywords survive."""
    return f"Summary: {text}"


def regressed_prompt_fn(text: str) -> str:
    """A 'regressed' mock: drops all the numbers, so keyword checks fail."""
    return "Summary: numbers omitted."


# ---------------------------------------------------------------------------
# Result containers (provided).
# ---------------------------------------------------------------------------
@dataclass
class CaseResult:
    input: str
    score: float
    passed: bool


@dataclass
class RunReport:
    results: list[CaseResult]
    pass_rate: float


# ---------------------------------------------------------------------------
# TODO: implement the runner.
# ---------------------------------------------------------------------------
class RegressionRunner:
    """Runs a prompt function against a golden set and gates on pass-rate."""

    def __init__(
        self,
        golden_set: list[dict],
        build_threshold: float = 0.8,
        case_pass_threshold: float = 0.5,
    ) -> None:
        self.golden_set = golden_set
        self.build_threshold = build_threshold
        self.case_pass_threshold = case_pass_threshold

    def keyword_score(self, output: str, keywords: list[str]) -> float:
        """Fraction (0.0-1.0) of `keywords` present as substrings of `output`.

        Empty `keywords` -> 1.0.
        """
        # TODO: count keyword hits and divide by len(keywords).
        raise NotImplementedError("TODO: implement keyword_score")

    def score_case(self, output: str, case: dict) -> CaseResult:
        """Score one output against one golden case."""
        # TODO: compute score; passed = score >= self.case_pass_threshold.
        raise NotImplementedError("TODO: implement score_case")

    def run(self, prompt_fn: Callable[[str], str]) -> RunReport:
        """Run prompt_fn over the whole golden set and build a RunReport."""
        # TODO: loop the golden set, score each case, compute pass_rate.
        raise NotImplementedError("TODO: implement run")

    def gate(self, report: RunReport) -> bool:
        """Build decision: True if pass_rate >= build_threshold."""
        # TODO: return the gate decision.
        raise NotImplementedError("TODO: implement gate")


# ---------------------------------------------------------------------------
# Demonstration of intended usage.
# ---------------------------------------------------------------------------
def _print_report(title: str, runner: RegressionRunner, report: RunReport) -> None:
    print(f"=== {title} ===")
    for r in report.results:
        tag = "PASS" if r.passed else "FAIL"
        print(f"  {tag}  score={r.score:.2f}  input='{r.input[:34]}...'")
    decision = "BUILD PASSES" if runner.gate(report) else "BUILD FAILS"
    print(
        f"pass-rate={report.pass_rate:.0%} "
        f"threshold={runner.build_threshold:.0%} -> {decision}"
    )


if __name__ == "__main__":
    runner = RegressionRunner(GOLDEN_SET, build_threshold=0.8)

    good = runner.run(good_prompt_fn)
    _print_report("Good prompt (passes the gate)", runner, good)

    print()
    bad = runner.run(regressed_prompt_fn)
    _print_report("Regressed prompt (fails the gate)", runner, bad)
