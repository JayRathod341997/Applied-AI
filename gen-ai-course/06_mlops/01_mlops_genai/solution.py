"""Solution: an in-memory model/prompt registry with stage promotion.

Implements `ModelRegistry`, which stores immutable, versioned artifacts under a
stable name and tracks which version occupies which stage. Versions move
None -> Staging -> Production; promoting a version demotes whoever currently
holds that stage (to "Archived") so exactly one version is in a stage at a time.
Rollback is just promoting a previous version back to Production.

Runs fully OFFLINE (no API keys, no network). The bottom of the file runs a demo
and asserts the expected registry behaviour.

Run with:  python solution.py
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# The artifact version record and the allowed stages.
# ---------------------------------------------------------------------------
STAGES = ("None", "Staging", "Production", "Archived")


@dataclass
class Version:
    """An immutable versioned artifact. Only `stage` is ever mutated."""

    name: str
    version: int
    artifact: object          # the model/prompt/dataset payload (any object)
    stage: str = "None"


# ---------------------------------------------------------------------------
# The registry.
# ---------------------------------------------------------------------------
class ModelRegistry:
    """A single source of truth for versioned artifacts and their stages."""

    def __init__(self) -> None:
        self._store: dict[str, list[Version]] = {}

    def register(self, name: str, artifact: object) -> int:
        versions = self._store.setdefault(name, [])
        number = len(versions) + 1
        versions.append(Version(name=name, version=number, artifact=artifact))
        return number

    def get_version(self, name: str, version: int) -> Version:
        if name not in self._store:
            raise KeyError(f"unknown artifact: {name!r}")
        for v in self._store[name]:
            if v.version == version:
                return v
        raise KeyError(f"unknown version {version} for {name!r}")

    def promote(self, name: str, version: int, stage: str) -> None:
        if stage not in STAGES:
            raise ValueError(f"invalid stage {stage!r}; allowed: {STAGES}")
        target = self.get_version(name, version)        # validates existence
        # Demote whoever currently holds this stage (skip None/Archived, which
        # may legitimately be shared by many versions).
        if stage in ("Staging", "Production"):
            for v in self._store[name]:
                if v.stage == stage and v.version != version:
                    v.stage = "Archived"
        target.stage = stage

    def get_current(self, name: str, stage: str = "Production") -> Version:
        if name not in self._store:
            raise KeyError(f"unknown artifact: {name!r}")
        for v in self._store[name]:
            if v.stage == stage:
                return v
        raise KeyError(f"no version in stage {stage!r} for {name!r}")

    def list_versions(self, name: str) -> list[Version]:
        return list(self._store.get(name, []))


# ---------------------------------------------------------------------------
# Demonstration + assertions.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    reg = ModelRegistry()

    print("=== Register versions ===")
    v1 = reg.register("support-prompt", "You are a helpful agent. v1")
    v2 = reg.register("support-prompt", "You are a helpful support agent. v2")
    v3 = reg.register("support-prompt", "You are a concise support agent. v3")
    print(f"support-prompt -> v{v1}, v{v2}, v{v3}")
    # Version numbers are monotonic and start at 1; all start in stage "None".
    assert (v1, v2, v3) == (1, 2, 3)
    assert all(v.stage == "None" for v in reg.list_versions("support-prompt"))

    print("=== Promote v2 to Staging, then v3 to Production ===")
    reg.promote("support-prompt", 2, "Staging")
    reg.promote("support-prompt", 3, "Production")
    print("Staging  ->", reg.get_current("support-prompt", "Staging").version)
    print("Production ->", reg.get_current("support-prompt", "Production").version)
    assert reg.get_current("support-prompt", "Staging").version == 2
    assert reg.get_current("support-prompt", "Production").version == 3

    print("=== Roll back: promote v2 to Production ===")
    reg.promote("support-prompt", 2, "Production")
    print("Production ->", reg.get_current("support-prompt", "Production").version,
          "(v3 demoted to Archived)")
    # v2 now holds Production; v3 was demoted to Archived (single Production holder).
    assert reg.get_current("support-prompt", "Production").version == 2
    assert reg.get_version("support-prompt", 3).stage == "Archived"
    # v2 moved from Staging to Production, so Staging is now empty.
    raised = False
    try:
        reg.get_current("support-prompt", "Staging")
    except KeyError:
        raised = True
    assert raised, "Staging should be empty after v2 moved to Production"

    print("=== Multiple artifacts are isolated ===")
    mv1 = reg.register("embedder", {"model": "text-embedding-3-small"})
    reg.promote("embedder", 1, "Production")
    assert mv1 == 1  # numbering is per-name, not global
    assert reg.get_current("embedder", "Production").version == 1
    assert reg.get_current("support-prompt", "Production").version == 2

    print("=== Validation: bad stage and unknown lookups raise ===")
    for bad in (
        lambda: reg.promote("support-prompt", 1, "Live"),     # invalid stage
        lambda: reg.get_version("support-prompt", 99),         # unknown version
        lambda: reg.get_current("nope", "Production"),         # unknown artifact
    ):
        errored = False
        try:
            bad()
        except (ValueError, KeyError):
            errored = True
        assert errored, "expected ValueError/KeyError for invalid input"

    print("\nAll assertions passed.")
