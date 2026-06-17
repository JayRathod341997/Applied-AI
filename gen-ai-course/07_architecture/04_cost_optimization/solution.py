"""Token-cost estimator + tiered router (SOLUTION).

Runs fully offline: no API keys, no network. Uses `tiktoken` when available,
falls back to a word-count tokenizer otherwise.

Run:
    python solution.py
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

HARD_KEYWORDS = (
    "prove", "derive", "design", "architect", "debug", "optimize",
    "analyze", "refactor", "algorithm", "trade-off", "tradeoff",
)


def count_tokens(text: str) -> int:
    """Estimated token count; tiktoken if available, else word-count fallback."""
    if not text:
        return 0
    if _ENC is not None:
        return len(_ENC.encode(text))
    # Fallback: a whitespace word is roughly 1.3 tokens in English.
    words = len(text.split())
    return max(1, round(words * 1.3))


def estimate_cost(in_tokens: int, out_tokens: int, tier: str) -> float:
    """Dollar cost of a call given token counts and a pricing tier."""
    if tier not in PRICING:
        raise ValueError(f"unknown tier: {tier!r}")
    p = PRICING[tier]
    return (in_tokens / 1000) * p["input_per_1k"] + \
           (out_tokens / 1000) * p["output_per_1k"]


def route_query(query: str) -> str:
    """Pick a model tier from a simple complexity heuristic."""
    q = query.lower()
    words = len(query.split())
    score = 0
    if words > 60:
        score += 2
    elif words > 20:
        score += 1
    if any(k in q for k in HARD_KEYWORDS):
        score += 2
    if query.count("?") > 1:
        score += 1
    return TIERS[min(score, len(TIERS) - 1)]


def analyze(query: str, expected_output_tokens: int = 200) -> dict:
    """Count input tokens, route to a tier, and estimate cost."""
    in_tokens = count_tokens(query)
    tier = route_query(query)
    out_tokens = expected_output_tokens
    cost = estimate_cost(in_tokens, out_tokens, tier)
    return {
        "query": query,
        "tier": tier,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "cost_usd": cost,
    }


def _print_table(rows: list[dict]) -> None:
    print(f"{'QUERY':<50} {'TIER':<9} {'IN':>4} {'OUT':>4} {'COST $':>10}")
    print("-" * 80)
    for r in rows:
        q = r["query"]
        q_short = (q[:47] + "...") if len(q) > 50 else q
        print(f"{q_short:<50} {r['tier']:<9} {r['in_tokens']:>4} "
              f"{r['out_tokens']:>4} {r['cost_usd']:>10.6f}")


if __name__ == "__main__":
    SAMPLES = [
        ("What time is it?", 20),
        ("Summarize this paragraph for me.", 60),
        ("List three fruits.", 30),
        ("Design and prove correct a distributed lock that is fault tolerant "
         "and debug the race condition in the current implementation. "
         "Analyze the trade-offs and optimize for low latency under "
         "high contention across multiple regions and many concurrent "
         "clients while preserving strict linearizability guarantees.", 400),
    ]

    print(f"TOKENIZER: {_TOKENIZER}\n")
    rows = [analyze(q, out) for q, out in SAMPLES]
    _print_table(rows)

    # ---- Assertions -------------------------------------------------------
    trivial = analyze("What time is it?", 20)
    complex_q = analyze(SAMPLES[-1][0], 400)

    # A long/complex query routes to a higher tier than a trivial one.
    assert TIERS.index(complex_q["tier"]) > TIERS.index(trivial["tier"]), \
        "complex query should route to a higher tier than a trivial one"
    assert trivial["tier"] == "small", "trivial query should be 'small'"
    assert complex_q["tier"] == "frontier", "complex query should be 'frontier'"

    # Cost is computed correctly for a known token count.
    # 1000 input + 1000 output on 'frontier' = 0.00250 + 0.01000 = 0.01250
    known = estimate_cost(1000, 1000, "frontier")
    assert abs(known - 0.01250) < 1e-9, f"expected 0.01250, got {known}"

    # 2000 input + 500 output on 'frontier' = 0.005 + 0.005 = 0.010
    known2 = estimate_cost(2000, 500, "frontier")
    assert abs(known2 - 0.010) < 1e-9, f"expected 0.010, got {known2}"

    # Tier ordering must make 'small' cheaper than 'frontier' for same tokens.
    assert estimate_cost(1000, 1000, "small") < \
        estimate_cost(1000, 1000, "frontier")

    print("\nAll assertions passed.")
