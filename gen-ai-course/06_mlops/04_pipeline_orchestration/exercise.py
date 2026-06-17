"""Exercise: a mini DAG runner with topological ordering, retries, and skips.

You will build a `DAGRunner` that models a GenAI ingestion pipeline
(ingest -> chunk -> embed -> index, plus a parallel build_synonyms branch) as a
DAG. It must:

  * compute a valid topological order (Kahn's algorithm) and raise ValueError
    on a cycle,
  * run each stage only after its dependencies succeed,
  * retry a failing stage up to its configured `retries` count
    (total attempts = retries + 1),
  * skip stages whose dependency failed.

Everything runs OFFLINE with deterministic mock stages. The mock stage helpers
below are fully provided. Complete only the sections marked `# TODO`.

Run with:  python exercise.py
"""

from __future__ import annotations

from collections import deque
from typing import Callable

SUCCESS = "SUCCESS"
FAILED = "FAILED"
SKIPPED = "SKIPPED"


# ---------------------------------------------------------------------------
# Provided: deterministic, offline mock stage functions. Do NOT modify these.
# ---------------------------------------------------------------------------
def make_stage(label: str) -> Callable[[], str]:
    """Return a zero-arg stage that always succeeds, returning a result string."""

    def _stage() -> str:
        return f"{label}-ok"

    return _stage


def make_flaky_stage(label: str, fail_times: int) -> Callable[[], str]:
    """Return a stage that raises `fail_times` times, then succeeds.

    Deterministic via a closure counter -- no randomness, fully offline.
    """
    state = {"calls": 0}

    def _stage() -> str:
        state["calls"] += 1
        if state["calls"] <= fail_times:
            raise RuntimeError(f"{label} transient failure #{state['calls']}")
        return f"{label}-ok"

    return _stage


def make_failing_stage(label: str) -> Callable[[], str]:
    """Return a stage that always raises."""

    def _stage() -> str:
        raise RuntimeError(f"{label} permanent failure")

    return _stage


# ---------------------------------------------------------------------------
# TODO: implement the DAG runner.
# ---------------------------------------------------------------------------
class DAGRunner:
    """Registers stages with dependencies and runs them in topological order."""

    def __init__(self) -> None:
        # TODO: initialize storage for stages. For each stage track:
        #   func, depends_on (list[str]), retries (int).
        raise NotImplementedError("TODO: init stage storage")

    def add_stage(
        self,
        name: str,
        func: Callable[[], object],
        depends_on: list[str] | tuple[str, ...] = (),
        retries: int = 0,
    ) -> None:
        """Register a stage with its dependencies and retry count."""
        # TODO: store the stage definition.
        raise NotImplementedError("TODO: register stage")

    def topological_order(self) -> list[str]:
        """Return stage names in a valid topological order.

        Use Kahn's algorithm. Raise ValueError if the graph has a cycle.
        """
        # TODO: build in-degree map + child map, run Kahn's algorithm,
        #       and raise ValueError("cycle detected in DAG") if not all
        #       nodes were emitted.
        raise NotImplementedError("TODO: topological sort with cycle detection")

    def run(self) -> dict:
        """Execute stages in topological order with retries and skips.

        Returns a dict: {stage_name: {"status": ..., "attempts": int,
        "output": ...}}.
        """
        # TODO:
        #   * order = self.topological_order()
        #   * for each stage in order:
        #       - if any dependency's status != SUCCESS -> SKIPPED, attempts=0
        #       - else attempt func() up to retries+1 times; first success ->
        #         SUCCESS with that output; otherwise FAILED.
        #   * record status, attempts, output per stage and return it.
        raise NotImplementedError("TODO: run the DAG")


# ---------------------------------------------------------------------------
# Demonstration of intended usage.
# ---------------------------------------------------------------------------
def build_pipeline(embed_func: Callable[[], object], embed_retries: int) -> DAGRunner:
    dag = DAGRunner()
    dag.add_stage("ingest", make_stage("ingest"))
    dag.add_stage("chunk", make_stage("chunk"), depends_on=["ingest"])
    dag.add_stage("embed", embed_func, depends_on=["chunk"], retries=embed_retries)
    dag.add_stage("build_synonyms", make_stage("build_synonyms"), depends_on=["chunk"])
    dag.add_stage("index", make_stage("index"), depends_on=["embed", "build_synonyms"])
    return dag


if __name__ == "__main__":
    dag = build_pipeline(make_stage("embed"), embed_retries=0)
    print("Topological order:", dag.topological_order())

    print("--- Run 1: all stages succeed ---")
    result = dag.run()
    for name, info in result.items():
        print(f"{name}: {info['status']} (attempts={info['attempts']})")

    print("--- Run 2: flaky embed (fails twice, retries=2) ---")
    dag = build_pipeline(make_flaky_stage("embed", fail_times=2), embed_retries=2)
    result = dag.run()
    print(f"embed: {result['embed']['status']} (attempts={result['embed']['attempts']})")

    print("--- Run 3: embed always fails (retries=1); index skipped ---")
    dag = build_pipeline(make_failing_stage("embed"), embed_retries=1)
    result = dag.run()
    print(f"embed: {result['embed']['status']} (attempts={result['embed']['attempts']})")
    print(f"index: {result['index']['status']} (attempts={result['index']['attempts']})")

    cyclic = DAGRunner()
    cyclic.add_stage("a", make_stage("a"), depends_on=["c"])
    cyclic.add_stage("b", make_stage("b"), depends_on=["a"])
    cyclic.add_stage("c", make_stage("c"), depends_on=["b"])
    try:
        cyclic.topological_order()
    except ValueError as e:
        print("Cycle correctly detected:", e)
