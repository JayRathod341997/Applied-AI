"""Exercise: a pluggable LLM gateway with a provider-abstraction fallback chain.

You will build an `LLMGateway` that hides multiple model providers behind a
single `complete(prompt)` interface and falls back from primary -> secondary ->
tertiary when a provider raises. The gateway also counts how many times each
provider was called.

Everything runs OFFLINE. The MockProvider classes below are fully provided.
Complete only the sections marked `# TODO`.

Run with:  python exercise.py
"""

from __future__ import annotations

from typing import Protocol


# ---------------------------------------------------------------------------
# Provided: a common provider interface + offline mock implementations.
# Do NOT modify these.
# ---------------------------------------------------------------------------
class LLMProvider(Protocol):
    """Structural interface every provider must satisfy."""

    name: str

    def complete(self, prompt: str) -> str:  # pragma: no cover - protocol
        ...


class MockProvider:
    """An offline provider that echoes the prompt.

    `fail` controls whether a call raises, so we can simulate outages.
    """

    def __init__(self, name: str, fail: bool = False) -> None:
        self.name = name
        self.fail = fail

    def complete(self, prompt: str) -> str:
        if self.fail:
            raise RuntimeError(f"{self.name} is unavailable (simulated outage)")
        return f"[{self.name}] Echo: {prompt}"


# ---------------------------------------------------------------------------
# TODO: implement the gateway.
# ---------------------------------------------------------------------------
class LLMGateway:
    """Routes completion requests through an ordered list of providers.

    The first provider is the primary; on failure the gateway tries the next
    one, and so on. It also tracks per-provider call counts.
    """

    def __init__(self, providers: list[LLMProvider]) -> None:
        """Store providers in priority order and init the call counter.

        Args:
            providers: ordered list; index 0 is the primary provider.
        """
        # TODO: save `providers` and create a dict {provider.name: 0} counter.
        raise NotImplementedError("TODO: store providers and init call counts")

    def complete(self, prompt: str) -> str:
        """Try each provider in order; return the first success.

        Increment a provider's call count before invoking it. On any Exception,
        record the error and move to the next provider. If all providers fail,
        raise RuntimeError including the last error seen.
        """
        # TODO: implement the fallback chain.
        raise NotImplementedError("TODO: implement fallback chain")

    def stats(self) -> dict[str, int]:
        """Return a COPY of the per-provider call counts."""
        # TODO: return a copy of the call-count dict.
        raise NotImplementedError("TODO: return a copy of call counts")


# ---------------------------------------------------------------------------
# Demonstration of intended usage.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Demo 1: primary succeeds ===")
    gw = LLMGateway([
        MockProvider("openai", fail=False),
        MockProvider("anthropic", fail=False),
        MockProvider("local-llama", fail=False),
    ])
    print("Result:", gw.complete("hello world"))
    print("Call counts:", gw.stats())

    print("\n=== Demo 2: primary fails, secondary succeeds ===")
    gw = LLMGateway([
        MockProvider("openai", fail=True),
        MockProvider("anthropic", fail=False),
        MockProvider("local-llama", fail=False),
    ])
    print("Result:", gw.complete("ping"))
    print("Call counts:", gw.stats())

    print("\n=== Demo 3: primary + secondary fail, tertiary succeeds ===")
    gw = LLMGateway([
        MockProvider("openai", fail=True),
        MockProvider("anthropic", fail=True),
        MockProvider("local-llama", fail=False),
    ])
    print("Result:", gw.complete("hi"))
    print("Call counts:", gw.stats())

    print()
    gw = LLMGateway([MockProvider("only", fail=True)])
    try:
        gw.complete("x")
    except RuntimeError:
        print("All providers down raises RuntimeError as expected.")
