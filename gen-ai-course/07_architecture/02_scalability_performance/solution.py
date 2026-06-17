"""Semantic Response Cache — SOLUTION (offline, no API keys).

Implements a semantic cache that returns a stored LLM response when a new query
is semantically similar (cosine similarity >= threshold) to a previously seen
query, with TTL-based expiry.

A deterministic hash-based bag-of-words `MockEmbedder` stands in for a real
embedding model so the whole thing runs OFFLINE.

Run:
    py -3 solution.py
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass

import numpy as np


# --------------------------------------------------------------------------- #
# Mock embedder (offline, deterministic)
# --------------------------------------------------------------------------- #
class MockEmbedder:
    """Deterministic, offline bag-of-words hashing embedder.

    Each token is hashed into one of `dim` buckets; the vector counts token
    occurrences per bucket and is L2-normalized. Queries sharing words land
    near each other, which is enough to exercise semantic-cache logic.
    """

    _WORD = re.compile(r"[a-z0-9']+")

    def __init__(self, dim: int = 256, seed: int = 7):
        self.dim = dim
        self.seed = seed

    def _tokens(self, text: str) -> list[str]:
        return self._WORD.findall(text.lower())

    def _bucket(self, token: str) -> int:
        h = 0
        for ch in token:
            h = (h * 131 + ord(ch) + self.seed) & 0xFFFFFFFF
        return h % self.dim

    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float64)
        for tok in self._tokens(text):
            vec[self._bucket(tok)] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec


# --------------------------------------------------------------------------- #
# Cache entry
# --------------------------------------------------------------------------- #
@dataclass
class CacheEntry:
    query: str
    embedding: np.ndarray
    response: str
    expires_at: float


# --------------------------------------------------------------------------- #
# SemanticCache
# --------------------------------------------------------------------------- #
class SemanticCache:
    """A semantic response cache with cosine-similarity lookup and TTL expiry."""

    def __init__(self, embedder: MockEmbedder, threshold: float = 0.8, ttl: float = 60.0):
        self.embedder = embedder
        self.threshold = threshold
        self.ttl = ttl
        self.entries: list[CacheEntry] = []
        self.stats = {"hits": 0, "misses": 0}

    # Indirection so tests / demos can monkeypatch the clock.
    def _now(self) -> float:
        return time.monotonic()

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        na = float(np.linalg.norm(a))
        nb = float(np.linalg.norm(b))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    def set(self, query: str, response: str) -> None:
        embedding = self.embedder.embed(query)
        expires_at = self._now() + self.ttl
        self.entries.append(
            CacheEntry(query=query, embedding=embedding, response=response, expires_at=expires_at)
        )

    def purge_expired(self) -> int:
        now = self._now()
        before = len(self.entries)
        self.entries = [e for e in self.entries if e.expires_at > now]
        return before - len(self.entries)

    def get(self, query: str) -> str | None:
        self.purge_expired()
        q = self.embedder.embed(query)

        best_entry: CacheEntry | None = None
        best_sim = -1.0
        for entry in self.entries:
            sim = self._cosine(q, entry.embedding)
            if sim > best_sim:
                best_sim, best_entry = sim, entry

        if best_entry is not None and best_sim >= self.threshold:
            self.stats["hits"] += 1
            return best_entry.response

        self.stats["misses"] += 1
        return None


# --------------------------------------------------------------------------- #
# Demo + assertions
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    embedder = MockEmbedder()

    # Mutable clock so we can simulate TTL expiry deterministically.
    clock = {"t": 1000.0}

    cache = SemanticCache(embedder, threshold=0.7, ttl=5.0)
    cache._now = lambda: clock["t"]  # type: ignore[assignment]

    # 1) Store a response.
    cache.set("how do i reset my password?", "Go to Settings > Security > Reset Password.")
    print("[set] cached: 'how do i reset my password?'")

    # 2) Paraphrase that shares key words -> expect a HIT.
    paraphrase = "how do i reset my account password please"
    sim = cache._cosine(embedder.embed(paraphrase), cache.entries[0].embedding)
    hit = cache.get(paraphrase)
    print(f"[get] HIT  (sim={sim:.2f}) for '{paraphrase}'" if hit else f"[get] MISS for '{paraphrase}'")
    assert hit is not None, "expected a cache hit on the paraphrase"

    # 3) Unrelated query -> expect a MISS (below threshold).
    unrelated = "what is the capital of france"
    miss = cache.get(unrelated)
    print(f"[get] MISS for '{unrelated}'")
    assert miss is None, "expected a cache miss on the unrelated query"

    # 4) Advance the clock past the TTL -> the entry expires -> MISS.
    clock["t"] += 10.0  # 10s later, ttl was 5s
    expired = cache.get(paraphrase)
    print("[expiry] entry expired after TTL -> MISS")
    assert expired is None, "expected a miss after TTL expiry"
    assert len(cache.entries) == 0, "expired entry should have been purged"

    # 5) Zero-norm safety: empty text embeds to a zero vector -> cosine 0.0.
    assert cache._cosine(embedder.embed(""), embedder.embed("")) == 0.0

    print("stats:", cache.stats)
    assert cache.stats == {"hits": 1, "misses": 2}, cache.stats
    print("All assertions passed.")
