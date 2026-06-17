"""Solution: a content-addressable version store ("DVC-lite").

Implements `VersionStore`, which gives prompt/dataset strings the same
guarantees Git gives code: content-addressed identity (sha256), automatic
deduplication, a named version history, and a line-level diff between versions.

Runs fully OFFLINE using only the standard library (hashlib, difflib). The
bottom of the file runs a demo and asserts the expected behaviour.

Run with:  python solution.py
"""

from __future__ import annotations

import difflib
import hashlib


# ---------------------------------------------------------------------------
# Helper.
# ---------------------------------------------------------------------------
def sha256_hex(content: str) -> str:
    """Return the sha256 hex digest of `content` encoded as UTF-8."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# The version store.
# ---------------------------------------------------------------------------
class VersionStore:
    """A content-addressable blob store with a named-version history layer."""

    def __init__(self) -> None:
        self._blobs: dict[str, str] = {}        # content hash -> content
        self._names: dict[str, list[str]] = {}  # name -> [hash, ...] oldest->newest

    # --- content-addressable blob layer ------------------------------------
    def put(self, content: str) -> str:
        """Store `content` keyed by its sha256 hash and return the hash.

        Deduplicates: identical content returns the same hash and is stored
        only once.
        """
        h = sha256_hex(content)
        self._blobs.setdefault(h, content)   # idempotent insert -> dedup
        return h

    def get(self, h: str) -> str:
        """Return the content for hash `h`, or raise KeyError if unknown."""
        if h not in self._blobs:
            raise KeyError(f"unknown content hash: {h}")
        return self._blobs[h]

    def exists(self, h: str) -> bool:
        """Return True if a blob with hash `h` is stored."""
        return h in self._blobs

    def blob_count(self) -> int:
        """Return the number of distinct blobs stored (for dedup checks)."""
        return len(self._blobs)

    # --- named-version (history) layer -------------------------------------
    def commit(self, name: str, content: str) -> str:
        """Record that logical `name` now points at `content`.

        Stores the content and appends its hash to the name's history.
        """
        h = self.put(content)
        self._names.setdefault(name, []).append(h)
        return h

    def history(self, name: str) -> list[str]:
        """Return the hashes for `name`, oldest -> newest ([] if unknown)."""
        return list(self._names.get(name, []))

    def latest(self, name: str) -> str:
        """Return the newest hash for `name`, or raise KeyError if none."""
        versions = self._names.get(name)
        if not versions:
            raise KeyError(f"no versions committed for name: {name}")
        return versions[-1]

    # --- diffing -----------------------------------------------------------
    def diff(self, hash_a: str, hash_b: str) -> list[str]:
        """Return a line-level unified diff between two stored contents."""
        a = self.get(hash_a).splitlines()
        b = self.get(hash_b).splitlines()
        return list(
            difflib.unified_diff(
                a,
                b,
                fromfile=f"a/{hash_a[:6]}",
                tofile=f"b/{hash_b[:6]}",
                lineterm="",
            )
        )


# ---------------------------------------------------------------------------
# Demonstration + assertions.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    store = VersionStore()

    print("=== Dedup: same content -> same hash, store size unchanged ===")
    ha = store.put("hello")
    hb = store.put("hello")
    print("hash a:", ha)
    print("hash b:", hb)
    print("blob count:", store.blob_count())
    # Same content -> same hash, and stored exactly once.
    assert ha == hb
    assert store.blob_count() == 1
    # Sanity: the hash really is the sha256 of the bytes.
    assert ha == hashlib.sha256(b"hello").hexdigest()

    print("\n=== Commit history for 'greeting_prompt' ===")
    v1 = store.commit("greeting_prompt", "Hello, {name}! Welcome.")
    v2 = store.commit("greeting_prompt", "Hello, {name}! Welcome back.")
    print("v1 hash:", v1)
    print("v2 hash:", v2)
    print("history length:", len(store.history("greeting_prompt")))
    print("latest == v2:", store.latest("greeting_prompt") == v2)
    # Two versions recorded oldest -> newest, latest points at v2.
    assert v1 != v2
    assert store.history("greeting_prompt") == [v1, v2]
    assert len(store.history("greeting_prompt")) == 2
    assert store.latest("greeting_prompt") == v2

    print("\n=== Round-trip get() ===")
    print("get(v2) ->", repr(store.get(v2)))
    # Content round-trips by hash.
    assert store.get(v1) == "Hello, {name}! Welcome."
    assert store.get(v2) == "Hello, {name}! Welcome back."
    assert store.exists(v1) and store.exists(v2)

    print("\n=== Diff v1 -> v2 ===")
    d = store.diff(v1, v2)
    for line in d:
        print(line)
    # The diff shows the old line removed and the new line added.
    assert any(line.startswith("-Hello, {name}! Welcome.") for line in d)
    assert any(line.startswith("+Hello, {name}! Welcome back.") for line in d)

    print()
    # Unknown hashes raise KeyError (never return None).
    raised = False
    try:
        store.get("deadbeef")
    except KeyError:
        raised = True
        print("get(unknown) raised KeyError as expected.")
    assert raised, "expected KeyError for an unknown hash"

    # latest() on an unknown name also raises.
    raised = False
    try:
        store.latest("nope")
    except KeyError:
        raised = True
    assert raised, "expected KeyError for an unknown name"

    # Dedup across commits: committing identical content reuses the blob.
    before = store.blob_count()
    again = store.commit("greeting_prompt", "Hello, {name}! Welcome.")
    assert again == v1                       # same content -> same hash
    assert store.blob_count() == before      # no new blob created
    assert store.history("greeting_prompt") == [v1, v2, v1]  # history still grows

    print("\nAll assertions passed.")
