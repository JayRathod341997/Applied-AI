"""Exercise: an in-memory model/prompt registry with stage promotion.

You will build a `ModelRegistry` that stores immutable, versioned artifacts
(models, prompts, datasets, ...) under a stable name and tracks which version
occupies which stage. Versions move through stages: None -> Staging ->
Production, and promoting a version demotes whoever currently holds that stage
so exactly one version is in a stage at a time.

Everything runs OFFLINE. The `Version` dataclass and `STAGES` constant below are
fully provided. Complete only the sections marked `# TODO`.

Run with:  python exercise.py
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Provided: the artifact version record and the allowed stages.
# Do NOT modify these.
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
# TODO: implement the registry.
# ---------------------------------------------------------------------------
class ModelRegistry:
    """A single source of truth for versioned artifacts and their stages."""

    def __init__(self) -> None:
        # TODO: create a store mapping name -> list[Version].
        raise NotImplementedError("TODO: init the name -> list[Version] store")

    def register(self, name: str, artifact: object) -> int:
        """Append a new immutable version under `name`; return its number.

        Version numbers start at 1 and increase by 1 per registration. The new
        version's stage is "None".
        """
        # TODO: append a new Version and return its version number.
        raise NotImplementedError("TODO: register a new version")

    def get_version(self, name: str, version: int) -> Version:
        """Return the Version object; raise KeyError if name/version unknown."""
        # TODO: look up and return the matching Version.
        raise NotImplementedError("TODO: fetch a specific version")

    def promote(self, name: str, version: int, stage: str) -> None:
        """Move `version` to `stage`, demoting any current holder of `stage`.

        Validate `stage` is in STAGES (else ValueError). Demote whoever holds
        `stage` to "Archived", then set the target version's stage.
        """
        # TODO: validate stage, demote the current holder, promote the target.
        raise NotImplementedError("TODO: implement stage promotion")

    def get_current(self, name: str, stage: str = "Production") -> Version:
        """Return the version currently in `stage`; raise KeyError if none."""
        # TODO: find and return the version whose stage == stage.
        raise NotImplementedError("TODO: fetch the current version for a stage")

    def list_versions(self, name: str) -> list[Version]:
        """Return a COPY of the version list for `name`."""
        # TODO: return a copy of the version list.
        raise NotImplementedError("TODO: list versions")


# ---------------------------------------------------------------------------
# Demonstration of intended usage.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    reg = ModelRegistry()

    print("=== Register versions ===")
    v1 = reg.register("support-prompt", "You are a helpful agent. v1")
    v2 = reg.register("support-prompt", "You are a helpful support agent. v2")
    v3 = reg.register("support-prompt", "You are a concise support agent. v3")
    print(f"support-prompt -> v{v1}, v{v2}, v{v3}")

    print("=== Promote v2 to Staging, then v3 to Production ===")
    reg.promote("support-prompt", 2, "Staging")
    reg.promote("support-prompt", 3, "Production")
    print("Staging  ->", reg.get_current("support-prompt", "Staging").version)
    print("Production ->", reg.get_current("support-prompt", "Production").version)

    print("=== Roll back: promote v2 to Production ===")
    reg.promote("support-prompt", 2, "Production")
    print("Production ->", reg.get_current("support-prompt", "Production").version)
