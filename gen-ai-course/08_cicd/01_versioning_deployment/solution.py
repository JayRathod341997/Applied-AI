"""Solution: an artifact version registry with rollback.

Implements `ArtifactRegistry`: registers immutable versioned artifacts, deploys
a chosen version, rolls back to the previous deployed version, and keeps a
deployment-history audit trail.

Runs fully OFFLINE (no API keys, no network). A monotonic timestamp counter
keeps output deterministic. The bottom runs a demo and asserts behaviour.

Run with:  python solution.py
"""

from __future__ import annotations

from typing import Any, Optional


class ArtifactRegistry:
    """In-memory registry of immutable artifact versions with rollback."""

    def __init__(self) -> None:
        self._artifacts: dict[str, Any] = {}
        self._history: list[dict[str, Any]] = []
        self._stack: list[str] = []          # distinct deploy sequence (rewind)
        self._current: Optional[str] = None
        self._clock = 0

    def _tick(self) -> int:
        self._clock += 1
        return self._clock

    def register(self, version: str, payload: Any) -> None:
        if version in self._artifacts:
            raise ValueError(f"version {version!r} already registered (immutable)")
        self._artifacts[version] = payload

    def deploy(self, version: str) -> None:
        if version not in self._artifacts:
            raise KeyError(f"version {version!r} is not registered")
        self._history.append({
            "version": version,
            "action": "deploy",
            "from_version": self._current,
            "timestamp": self._tick(),
        })
        # Track the distinct deploy sequence so rollback can rewind one step.
        if not self._stack or self._stack[-1] != version:
            self._stack.append(version)
        self._current = version

    def rollback(self) -> None:
        if len(self._stack) < 2:
            raise RuntimeError("no prior version to roll back to")
        self._stack.pop()                    # drop the current version
        previous = self._stack[-1]           # the one deployed before it
        self._history.append({
            "version": previous,
            "action": "rollback",
            "from_version": self._current,
            "timestamp": self._tick(),
        })
        self._current = previous

    def current_version(self) -> Optional[str]:
        return self._current

    def history(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self._history]


# ---------------------------------------------------------------------------
# Demonstration + assertions.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    reg = ArtifactRegistry()
    reg.register("v1", {"prompt": "summarize v1"})
    reg.register("v2", {"prompt": "summarize v2"})
    reg.register("v3", {"prompt": "summarize v3"})
    print("Registered:", ["v1", "v2", "v3"])

    # Immutability: re-registering raises.
    raised = False
    try:
        reg.register("v1", {"prompt": "x"})
    except ValueError:
        raised = True
    assert raised, "re-registering an existing version must raise ValueError"

    # Deploying an unregistered version raises.
    raised = False
    try:
        reg.deploy("v9")
    except KeyError:
        raised = True
    assert raised, "deploying an unregistered version must raise KeyError"

    reg.deploy("v1")
    print("Deployed v1 -> current =", reg.current_version())
    assert reg.current_version() == "v1"
    assert reg.history()[-1] == {
        "version": "v1", "action": "deploy", "from_version": None, "timestamp": 1
    }

    reg.deploy("v2")
    print("Deployed v2 -> current =", reg.current_version())
    reg.deploy("v3")
    print("Deployed v3 -> current =", reg.current_version())
    assert reg.current_version() == "v3"

    reg.rollback()
    print("Rolled back -> current =", reg.current_version())
    assert reg.current_version() == "v2"
    assert reg.history()[-1]["action"] == "rollback"
    assert reg.history()[-1]["from_version"] == "v3"

    reg.rollback()
    print("Rolled back -> current =", reg.current_version())
    assert reg.current_version() == "v1"

    actions = [r["action"] for r in reg.history()]
    print("History actions:", actions)
    assert actions == ["deploy", "deploy", "deploy", "rollback", "rollback"]

    # history() returns a copy: mutating it must not affect internal state.
    h = reg.history()
    h.append({"tampered": True})
    assert len(reg.history()) == 5, "history() must return a defensive copy"

    # Rolling back with no prior distinct version raises.
    fresh = ArtifactRegistry()
    fresh.register("only", 1)
    fresh.deploy("only")
    raised = False
    try:
        fresh.rollback()
    except RuntimeError:
        raised = True
    assert raised, "rollback with no prior version must raise RuntimeError"

    print("All assertions passed.")
