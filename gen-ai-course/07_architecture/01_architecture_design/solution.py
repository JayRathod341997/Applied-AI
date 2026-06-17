"""Solution: a pluggable LLM gateway with a provider-abstraction fallback chain.

Implements `LLMGateway`, which hides multiple model providers behind a single
`complete(prompt)` interface, falls back primary -> secondary -> tertiary on
failure, and counts per-provider calls.

Runs fully OFFLINE (no API keys, no network). The bottom of the file runs a
demo and asserts the expected fallback behaviour.

Run with:  python solution.py
"""

from __future__ import annotations

from typing import Protocol


# ---------------------------------------------------------------------------
# Common provider interface + offline mock implementations.
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
# The gateway.
# ---------------------------------------------------------------------------
class LLMGateway:
    """Routes completion requests through an ordered list of providers.

    The first provider is the primary; on failure the gateway tries the next
    one, and so on. It also tracks per-provider call counts.
    """

    def __init__(self, providers: list[LLMProvider]) -> None:
        if not providers:
            raise ValueError("LLMGateway requires at least one provider")
        self.providers = list(providers)
        self.call_counts: dict[str, int] = {p.name: 0 for p in self.providers}

    def complete(self, prompt: str) -> str:
        """Try each provider in priority order; return the first success.

        Raises:
            RuntimeError: if every provider fails. The message includes the
                last error encountered.
        """
        last_error: Exception | None = None
        for provider in self.providers:
            self.call_counts[provider.name] += 1
            try:
                return provider.complete(prompt)
            except Exception as err:  # noqa: BLE001 - intentional broad catch
                last_error = err
                continue
        raise RuntimeError(f"all providers failed; last error: {last_error}")

    def stats(self) -> dict[str, int]:
        """Return a copy of the per-provider call counts."""
        return dict(self.call_counts)


# ---------------------------------------------------------------------------
# Demonstration + assertions.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Demo 1: primary succeeds ===")
    gw = LLMGateway([
        MockProvider("openai", fail=False),
        MockProvider("anthropic", fail=False),
        MockProvider("local-llama", fail=False),
    ])
    result = gw.complete("hello world")
    print("Result:", result)
    print("Call counts:", gw.stats())
    # Primary served it; secondary and tertiary were never called.
    assert result == "[openai] Echo: hello world"
    assert gw.stats() == {"openai": 1, "anthropic": 0, "local-llama": 0}

    print("\n=== Demo 2: primary fails, secondary succeeds ===")
    gw = LLMGateway([
        MockProvider("openai", fail=True),
        MockProvider("anthropic", fail=False),
        MockProvider("local-llama", fail=False),
    ])
    result = gw.complete("ping")
    print("Result:", result)
    print("Call counts:", gw.stats())
    # Primary raised, so the secondary handled it; tertiary untouched.
    assert result == "[anthropic] Echo: ping"
    assert gw.stats() == {"openai": 1, "anthropic": 1, "local-llama": 0}

    print("\n=== Demo 3: primary + secondary fail, tertiary succeeds ===")
    gw = LLMGateway([
        MockProvider("openai", fail=True),
        MockProvider("anthropic", fail=True),
        MockProvider("local-llama", fail=False),
    ])
    result = gw.complete("hi")
    print("Result:", result)
    print("Call counts:", gw.stats())
    assert result == "[local-llama] Echo: hi"
    assert gw.stats() == {"openai": 1, "anthropic": 1, "local-llama": 1}

    print("\n=== Demo 4: all providers down ===")
    gw = LLMGateway([
        MockProvider("openai", fail=True),
        MockProvider("anthropic", fail=True),
    ])
    raised = False
    try:
        gw.complete("x")
    except RuntimeError as e:
        raised = True
        print("Raised RuntimeError as expected:", e)
    assert raised, "expected RuntimeError when every provider fails"
    # Every provider was attempted exactly once.
    assert gw.stats() == {"openai": 1, "anthropic": 1}

    print("\n=== Demo 5: provider-agnostic - works with any duck-typed object ===")
    class CountingStub:
        name = "stub"

        def __init__(self) -> None:
            self.seen: list[str] = []

        def complete(self, prompt: str) -> str:
            self.seen.append(prompt)
            return f"[stub] {prompt.upper()}"

    stub = CountingStub()
    gw = LLMGateway([stub])
    assert gw.complete("ok") == "[stub] OK"
    assert stub.seen == ["ok"]

    print("\nAll assertions passed.")
