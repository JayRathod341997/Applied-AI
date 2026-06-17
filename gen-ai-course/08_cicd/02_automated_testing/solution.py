"""Solution: a prompt regression test runner.

Implements `RegressionRunner`: runs a (mock) prompt function against a golden
set, scores each output by keyword presence, computes an overall pass-rate, and
produces a build pass/fail decision (the regression gate).

Runs fully OFFLINE (no API keys, no network). The bottom runs a demo and
asserts the gate behaviour.

Run with:  python solution.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


# ---------------------------------------------------------------------------
# Golden set + mock prompt functions.
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


def partial_prompt_fn(text: str) -> str:
    """A 'partial' mock: keeps only the first number found, for a mid score."""
    import re
    m = re.search(r"\$?\d[\d.]*[%A-Za-z]*", text)
    return f"Summary: {m.group(0) if m else 'n/a'}"


# ---------------------------------------------------------------------------
# Result containers.
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
# The runner.
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
        if not keywords:
            return 1.0
        hits = sum(1 for k in keywords if k in output)
        return hits / len(keywords)

    def score_case(self, output: str, case: dict) -> CaseResult:
        score = self.keyword_score(output, case["expected_keywords"])
        return CaseResult(
            input=case["input"],
            score=score,
            passed=score >= self.case_pass_threshold,
        )

    def run(self, prompt_fn: Callable[[str], str]) -> RunReport:
        results = [
            self.score_case(prompt_fn(case["input"]), case)
            for case in self.golden_set
        ]
        passed = sum(1 for r in results if r.passed)
        pass_rate = passed / len(results) if results else 0.0
        return RunReport(results=results, pass_rate=pass_rate)

    def gate(self, report: RunReport) -> bool:
        return report.pass_rate >= self.build_threshold


# ---------------------------------------------------------------------------
# Demonstration + assertions.
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
    # The good prompt echoes the input, so every keyword is present.
    assert all(r.score == 1.0 for r in good.results)
    assert good.pass_rate == 1.0
    assert runner.gate(good) is True

    print()
    bad = runner.run(regressed_prompt_fn)
    _print_report("Regressed prompt (fails the gate)", runner, bad)
    # The regressed prompt drops all numbers -> zero keyword hits everywhere.
    assert all(r.score == 0.0 for r in bad.results)
    assert bad.pass_rate == 0.0
    assert runner.gate(bad) is False

    # keyword_score edge cases.
    assert runner.keyword_score("anything", []) == 1.0
    assert runner.keyword_score("has 15% only", ["15%", "28%"]) == 0.5

    # A partial prompt: keeps one number per case -> below per-case threshold
    # for the multi-keyword cases, so the build still fails.
    partial = runner.run(partial_prompt_fn)
    assert partial.pass_rate < 1.0
    assert runner.gate(partial) is False

    # run() must not mutate the golden set.
    assert len(GOLDEN_SET) == 3 and GOLDEN_SET[0]["expected_keywords"] == [
        "$4.2B", "15%", "28%"
    ]

    print("\nAll assertions passed.")
