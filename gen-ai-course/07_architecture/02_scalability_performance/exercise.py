"""Semantic Response Cache — STARTER.

Build a semantic cache that returns a stored LLM response when a new query is
*semantically similar* (cosine similarity >= threshold) to a previously seen
query, with TTL-based expiry.

Everything runs OFFLINE: a deterministic hash-based bag-of-words `MockEmbedder`
stands in for a real embedding model, so there are no API keys or network calls.

Run:
    py -3 exercise.py
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

import numpy as np


# --------------------------------------------------------------------------- #
# Mock embedder (FULLY PROVIDED — do not modify)
# --------------------------------------------------------------------------- #
class MockEmbedder:
    """Deterministic, offline bag-of-words hashing embedder.

    Each token is hashed into one of `dim` buckets; the vector counts token
    occurrences per bucket and is L2-normalized. Queries that share words map
    to nearby vectors, which is enough to exercise semantic-cache logic without
    a real model or network access.
    """

    _WORD = re.compile(r"[a-z0-9']+")

    def __init__(self, dim: int = 256, seed: int = 7):
        self.dim = dim
        self.seed = seed

    def _tokens(self, text: str) -> list[str]:
        return self._WORD.findall(text.lower())

    def _bucket(self, token: str) -> int:
        # Stable, deterministic hash -> bucket index.
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
# SemanticCache — IMPLEMENT THE TODOs
# --------------------------------------------------------------------------- #
class SemanticCache:
    """A semantic response cache with cosine-similarity lookup and TTL expiry."""

    def __init__(self, embedder: MockEmbedder, threshold: float = 0.8, ttl: float = 60.0):
        self.embedder = embedder
        self.threshold = threshold
        self.ttl = ttl
        self.entries: list[CacheEntry] = []
        self.stats = {"hits": 0, "misses": 0}

    # Indirection so tests can monkeypatch the clock.
    def _now(self) -> float:
        return time.monotonic()

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        """Return cosine similarity between two vectors.

        TODO:
          - compute dot(a, b) / (||a|| * ||b||)
          - if either norm is 0, return 0.0 (avoid divide-by-zero)
        """
        raise NotImplementedError("TODO: implement _cosine")

    def set(self, query: str, response: str) -> None:
        """Embed `query` and store (embedding, response, expires_at).

        TODO:
          - embed the query
          - compute expires_at = self._now() + self.ttl
          - append a CacheEntry to self.entries
        """
        raise NotImplementedError("TODO: implement set")

    def purge_expired(self) -> int:
        """Remove expired entries; return how many were removed.

        TODO:
          - keep only entries whose expires_at > now
          - return the number removed
        """
        raise NotImplementedError("TODO: implement purge_expired")

    def get(self, query: str) -> str | None:
        """Return the cached response for the best match >= threshold, else None.

        TODO:
          - purge expired entries first
          - embed the query
          - find the stored entry with the highest cosine similarity
          - if best similarity >= self.threshold: record a hit, return its response
          - else: record a miss, return None
        """
        raise NotImplementedError("TODO: implement get")


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    embedder = MockEmbedder()
    cache = SemanticCache(embedder, threshold=0.8, ttl=2.0)

    cache.set("how do i reset my password?", "Go to Settings > Security > Reset Password.")
    print("[set] cached the password-reset answer")

    hit = cache.get("i forgot my password, how can i change it")
    print("[get] paraphrase ->", hit)

    miss = cache.get("what is the capital of france")
    print("[get] unrelated ->", miss)

    print("stats:", cache.stats)
