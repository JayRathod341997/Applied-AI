"""Exercise: an artifact version registry with rollback.

You will build an `ArtifactRegistry` that registers immutable versioned
artifacts, deploys a chosen version, rolls back to the previous deployed
version, and keeps a deployment-history audit trail.

Everything runs OFFLINE (Python standard library only). A monotonic timestamp
counter is provided so output is deterministic. Complete only the `# TODO`
sections.

Run with:  python exercise.py
"""

from __future__ import annotations

from typing import Any, Optional


class ArtifactRegistry:
    """In-memory registry of immutable artifact versions with rollback.

    - register(version, payload): store a new immutable version.
    - deploy(version): make a registered version the current deployment.
    - rollback(): re-point current to the previous distinct deployed version.
    - current_version(): the currently deployed version (or None).
    - history(): the deployment-history audit trail.
    """

    def __init__(self) -> None:
        self._artifacts: dict[str, Any] = {}      # version -> payload (immutable)
        self._history: list[dict[str, Any]] = []  # deployment records
        self._current: Optional[str] = None
        self._clock = 0                           # monotonic timestamp source

    def _tick(self) -> int:
        """Return a monotonically increasing timestamp (deterministic)."""
        self._clock += 1
        return self._clock

    def register(self, version: str, payload: Any) -> None:
        """Store a new immutable version.

        Raises:
            ValueError: if `version` is already registered (immutability).
        """
        # TODO: reject duplicates, then store payload under `version`.
        raise NotImplementedError("TODO: implement register")

    def deploy(self, version: str) -> None:
        """Make `version` the current deployment and record it in history.

        Append {"version", "action": "deploy", "from_version", "timestamp"}.

        Raises:
            KeyError: if `version` was never registered.
        """
        # TODO: validate, append a 'deploy' history record, update current.
        raise NotImplementedError("TODO: implement deploy")

    def rollback(self) -> None:
        """Re-point current to the previous DISTINCT deployed version.

        Append a record with "action": "rollback".

        Raises:
            RuntimeError: if there is no prior version to roll back to.
        """
        # TODO: find the previous distinct version from history, record, update.
        raise NotImplementedError("TODO: implement rollback")

    def current_version(self) -> Optional[str]:
        """Return the currently deployed version (or None)."""
        # TODO: return the current version.
        raise NotImplementedError("TODO: implement current_version")

    def history(self) -> list[dict[str, Any]]:
        """Return a COPY of the deployment-history list."""
        # TODO: return a copy so callers can't mutate internal state.
        raise NotImplementedError("TODO: implement history")


# ---------------------------------------------------------------------------
# Demonstration of intended usage.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    reg = ArtifactRegistry()
    reg.register("v1", {"prompt": "summarize v1"})
    reg.register("v2", {"prompt": "summarize v2"})
    reg.register("v3", {"prompt": "summarize v3"})
    print("Registered:", ["v1", "v2", "v3"])

    reg.deploy("v1")
    print("Deployed v1 -> current =", reg.current_version())
    reg.deploy("v2")
    print("Deployed v2 -> current =", reg.current_version())
    reg.deploy("v3")
    print("Deployed v3 -> current =", reg.current_version())

    reg.rollback()
    print("Rolled back -> current =", reg.current_version())
    reg.rollback()
    print("Rolled back -> current =", reg.current_version())

    print("History actions:", [r["action"] for r in reg.history()])
