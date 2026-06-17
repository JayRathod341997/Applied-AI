"""Token-cost estimator + tiered router (STARTER).

Goal
----
Given a query, (1) estimate the token cost using a pricing table and
(2) route the query to a model TIER based on a simple complexity heuristic,
then report the chosen tier and estimated cost.

This file MUST run fully offline. Token counting uses `tiktoken` when it is
installed but falls back to a simple word-count tokenizer otherwise.

Fill in every function marked with `# TODO` and remove the
NotImplementedError once done. Compare with solution.py when finished.
"""

from __future__ import annotations

# --- Optional tiktoken with graceful offline fallback ------------------------
try:
    import tiktoken
    try:
        _ENC = tiktoken.get_encoding("cl100k_base")
        _TOKENIZER = "tiktoken (cl100k_base)"
    except Exception:
        _ENC = None
        _TOKENIZER = "word-count fallback (encoding unavailable)"
except Exception:
    tiktoken = None
    _ENC = None
    _TOKENIZER = "word-count fallback (tiktoken missing)"


# --- Pricing table: dollars per 1,000 tokens --------------------------------
# Representative tiers; prices move constantly, see references.md.
PRICING = {
    "small":    {"input_per_1k": 0.00015, "output_per_1k": 0.00060},
    "mid":      {"input_per_1k": 0.00050, "output_per_1k": 0.00150},
    "frontier": {"input_per_1k": 0.00250, "output_per_1k": 0.01000},
}

TIERS = ["small", "mid", "frontier"]

# Keywords that signal a harder, reasoning-heavy task.
HARD_KEYWORDS = (
    "prove", "derive", "design", "architect", "debug", "optimize",
    "analyze", "refactor", "algorithm", "trade-off", "tradeoff",
)


def count_tokens(text: str) -> int:
    """Return an estimated token count for `text`.

    Use tiktoken when `_ENC` is available; otherwise estimate from the
    whitespace word count (a word is roughly 1.3 tokens). Must not raise
    when tiktoken is missing.
    """
    # TODO: if _ENC is not None, return len(_ENC.encode(text))
    # TODO: else estimate from len(text.split()) * 1.3, at least 1 for non-empty
    raise NotImplementedError("TODO: implement count_tokens")


def estimate_cost(in_tokens: int, out_tokens: int, tier: str) -> float:
    """Return the dollar cost of a call given token counts and a tier.

    Look the tier up in PRICING and apply input_per_1k / output_per_1k.
    """
    # TODO: look up PRICING[tier], compute
    #   (in_tokens/1000)*input_per_1k + (out_tokens/1000)*output_per_1k
    raise NotImplementedError("TODO: implement estimate_cost")


def route_query(query: str) -> str:
    """Pick a model tier from a simple complexity heuristic.

    Suggested scoring:
      - words > 60  -> +2 ; words > 20 -> +1
      - any HARD_KEYWORDS present -> +2
      - more than one '?' -> +1
    Map score 0->small, 1->mid, 2+->frontier (clamp into TIERS).
    """
    # TODO: compute a complexity score and map it to a tier name
    raise NotImplementedError("TODO: implement route_query")


def analyze(query: str, expected_output_tokens: int = 200) -> dict:
    """Combine counting, routing and costing into one report dict.

    Returns: {query, tier, in_tokens, out_tokens, cost_usd}
    """
    # TODO: count input tokens, route, estimate cost, build the dict
    raise NotImplementedError("TODO: implement analyze")


if __name__ == "__main__":
    SAMPLES = [
        ("What time is it?", 20),
        ("Summarize this paragraph for me.", 60),
        ("Design and prove correct a distributed lock that is fault tolerant "
         "and debug the race condition in the current implementation.", 400),
    ]

    print(f"TOKENIZER: {_TOKENIZER}\n")
    print(f"{'QUERY':<50} {'TIER':<9} {'IN':>4} {'OUT':>4} {'COST $':>10}")
    print("-" * 80)
    for q, out in SAMPLES:
        r = analyze(q, out)
        q_short = (q[:47] + "...") if len(q) > 50 else q
        print(f"{q_short:<50} {r['tier']:<9} {r['in_tokens']:>4} "
              f"{r['out_tokens']:>4} {r['cost_usd']:>10.6f}")
