"""Solution: a mini DAG runner with topological ordering, retries, and skips.

Implements `DAGRunner`, the core of any orchestrator:

  * `add_stage(name, func, depends_on, retries)` registers a task,
  * `topological_order()` returns a valid run order via Kahn's algorithm and
    raises ValueError on a cycle,
  * `run()` executes stages in order, retrying failures (total attempts =
    retries + 1) and skipping stages whose dependency failed.

Runs fully OFFLINE (no network, no third-party deps). The bottom of the file
runs a demo and asserts the expected behaviour.

Run with:  python solution.py
"""

from __future__ import annotations

from collections import deque
from typing import Callable

SUCCESS = "SUCCESS"
FAILED = "FAILED"
SKIPPED = "SKIPPED"


# ---------------------------------------------------------------------------
# Deterministic, offline mock stage functions.
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
# The DAG runner.
# ---------------------------------------------------------------------------
class _Stage:
    __slots__ = ("name", "func", "depends_on", "retries")

    def __init__(self, name, func, depends_on, retries):
        self.name = name
        self.func = func
        self.depends_on = list(depends_on)
        self.retries = retries


class DAGRunner:
    """Registers stages with dependencies and runs them in topological order."""

    def __init__(self) -> None:
        self.stages: dict[str, _Stage] = {}

    def add_stage(
        self,
        name: str,
        func: Callable[[], object],
        depends_on: list[str] | tuple[str, ...] = (),
        retries: int = 0,
    ) -> None:
        """Register a stage with its dependencies and retry count."""
        if name in self.stages:
            raise ValueError(f"duplicate stage name: {name}")
        if retries < 0:
            raise ValueError("retries must be >= 0")
        self.stages[name] = _Stage(name, func, depends_on, retries)

    def topological_order(self) -> list[str]:
        """Return stage names in a valid topological order (Kahn's algorithm).

        Raises:
            ValueError: if a dependency is unknown, or the graph has a cycle.
        """
        indegree: dict[str, int] = {n: 0 for n in self.stages}
        children: dict[str, list[str]] = {n: [] for n in self.stages}
        for name, stage in self.stages.items():
            for dep in stage.depends_on:
                if dep not in self.stages:
                    raise ValueError(f"stage '{name}' depends on unknown '{dep}'")
                indegree[name] += 1
                children[dep].append(name)

        # Use sorted seeding for a deterministic order across runs.
        ready = deque(sorted(n for n, d in indegree.items() if d == 0))
        order: list[str] = []
        while ready:
            node = ready.popleft()
            order.append(node)
            for child in sorted(children[node]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)

        if len(order) != len(self.stages):
            raise ValueError("cycle detected in DAG")
        return order

    def run(self) -> dict:
        """Execute stages in topological order with retries and skips.

        Returns:
            dict mapping stage name -> {"status", "attempts", "output"}.
        """
        order = self.topological_order()
        results: dict[str, dict] = {}

        for name in order:
            stage = self.stages[name]

            # Skip if any dependency did not succeed.
            dep_failed = any(
                results[dep]["status"] != SUCCESS for dep in stage.depends_on
            )
            if dep_failed:
                results[name] = {"status": SKIPPED, "attempts": 0, "output": None}
                continue

            attempts = 0
            output = None
            status = FAILED
            max_attempts = stage.retries + 1
            while attempts < max_attempts:
                attempts += 1
                try:
                    output = stage.func()
                    status = SUCCESS
                    break
                except Exception:  # noqa: BLE001 - intentional broad catch
                    continue  # retry until attempts exhausted

            results[name] = {"status": status, "attempts": attempts, "output": output}

        return results


# ---------------------------------------------------------------------------
# Demonstration + assertions.
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
    # --- Topological order respects dependencies -------------------------
    dag = build_pipeline(make_stage("embed"), embed_retries=0)
    order = dag.topological_order()
    print("Topological order:", order)

    def before(a: str, b: str) -> bool:
        return order.index(a) < order.index(b)

    assert before("ingest", "chunk")
    assert before("chunk", "embed")
    assert before("chunk", "build_synonyms")
    assert before("embed", "index")
    assert before("build_synonyms", "index")
    assert order[-1] == "index"  # index depends on two upstreams, always last

    # --- Run 1: all stages succeed --------------------------------------
    print("--- Run 1: all stages succeed ---")
    result = dag.run()
    for name, info in result.items():
        print(f"{name}: {info['status']} (attempts={info['attempts']})")
    assert all(info["status"] == SUCCESS for info in result.values())
    assert all(info["attempts"] == 1 for info in result.values())
    assert result["index"]["output"] == "index-ok"

    # --- Run 2: flaky embed fails twice then succeeds (retries=2) -------
    print("--- Run 2: flaky embed (fails twice, retries=2) ---")
    dag = build_pipeline(make_flaky_stage("embed", fail_times=2), embed_retries=2)
    result = dag.run()
    print(f"embed: {result['embed']['status']} (attempts={result['embed']['attempts']})")
    assert result["embed"]["status"] == SUCCESS
    assert result["embed"]["attempts"] == 3  # 2 failures + 1 success
    assert result["index"]["status"] == SUCCESS  # downstream still runs

    # --- Run 3: embed always fails (retries=1); index is skipped --------
    print("--- Run 3: embed always fails (retries=1); index skipped ---")
    dag = build_pipeline(make_failing_stage("embed"), embed_retries=1)
    result = dag.run()
    print(f"embed: {result['embed']['status']} (attempts={result['embed']['attempts']})")
    print(f"index: {result['index']['status']} (attempts={result['index']['attempts']})")
    assert result["embed"]["status"] == FAILED
    assert result["embed"]["attempts"] == 2  # 1 initial + 1 retry
    assert result["index"]["status"] == SKIPPED
    assert result["index"]["attempts"] == 0
    assert result["index"]["output"] is None
    # Unrelated branch still succeeded.
    assert result["build_synonyms"]["status"] == SUCCESS

    # --- Cycle detection -------------------------------------------------
    cyclic = DAGRunner()
    cyclic.add_stage("a", make_stage("a"), depends_on=["c"])
    cyclic.add_stage("b", make_stage("b"), depends_on=["a"])
    cyclic.add_stage("c", make_stage("c"), depends_on=["b"])
    raised = False
    try:
        cyclic.topological_order()
    except ValueError as e:
        raised = True
        print("Cycle correctly detected:", e)
    assert raised, "expected ValueError on a cyclic graph"

    print("\nAll assertions passed.")
