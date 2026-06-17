"""Exercise: a content-addressable version store ("DVC-lite").

You will build a `VersionStore` that gives prompt/dataset strings the same
guarantees Git gives code:

  * content addressing  -- the id of an artifact is sha256 of its bytes
  * deduplication       -- identical content is stored exactly once
  * named history       -- a logical name (e.g. "greeting_prompt") tracks an
                           ordered list of content hashes over time
  * diffing             -- a line-level diff between any two stored versions

Everything runs OFFLINE using only the standard library (hashlib, difflib).
Complete only the sections marked `# TODO`.

Run with:  python exercise.py
"""

from __future__ import annotations

import difflib
import hashlib


# ---------------------------------------------------------------------------
# Provided helper. Do NOT modify.
# ---------------------------------------------------------------------------
def sha256_hex(content: str) -> str:
    """Return the sha256 hex digest of `content` encoded as UTF-8."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# TODO: implement the version store.
# ---------------------------------------------------------------------------
class VersionStore:
    """A content-addressable blob store with a named-version history layer."""

    def __init__(self) -> None:
        # blobs: content hash -> content string
        self._blobs: dict[str, str] = {}
        # names: logical name -> list of hashes (oldest -> newest)
        self._names: dict[str, list[str]] = {}

    # --- content-addressable blob layer ------------------------------------
    def put(self, content: str) -> str:
        """Store `content` keyed by its sha256 hash and return the hash.

        Putting identical content twice must return the SAME hash and must NOT
        create a second copy (deduplication).
        """
        # TODO: hash content with sha256_hex, store it if new, return the hash.
        raise NotImplementedError("TODO: hash, dedup-store, and return the hash")

    def get(self, h: str) -> str:
        """Return the content for hash `h`, or raise KeyError if unknown."""
        # TODO: look up the blob; raise KeyError when missing.
        raise NotImplementedError("TODO: return blob or raise KeyError")

    def exists(self, h: str) -> bool:
        """Return True if a blob with hash `h` is stored."""
        # TODO: return whether the hash is present.
        raise NotImplementedError("TODO: membership check")

    def blob_count(self) -> int:
        """Return the number of distinct blobs stored (for dedup checks)."""
        return len(self._blobs)

    # --- named-version (history) layer -------------------------------------
    def commit(self, name: str, content: str) -> str:
        """Record that logical `name` now points at `content`.

        Stores the content (via put) and appends its hash to the name's
        history. Returns the content hash.
        """
        # TODO: put content, append hash to self._names[name] history, return it.
        raise NotImplementedError("TODO: commit content under a name")

    def history(self, name: str) -> list[str]:
        """Return the list of hashes for `name`, oldest -> newest ([] if none)."""
        # TODO: return a copy of the history list (empty list if name unknown).
        raise NotImplementedError("TODO: return history list")

    def latest(self, name: str) -> str:
        """Return the newest hash for `name`, or raise KeyError if none."""
        # TODO: return the last hash in the name's history; raise KeyError if empty.
        raise NotImplementedError("TODO: return latest hash or raise KeyError")

    # --- diffing -----------------------------------------------------------
    def diff(self, hash_a: str, hash_b: str) -> list[str]:
        """Return a line-level unified diff between two stored contents.

        Use difflib.unified_diff over the splitlines() of each content.
        """
        # TODO: fetch both blobs and return list(difflib.unified_diff(...)).
        raise NotImplementedError("TODO: produce a unified diff list")


# ---------------------------------------------------------------------------
# Demonstration of intended usage.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    store = VersionStore()

    print("=== Dedup: same content -> same hash, store size unchanged ===")
    ha = store.put("hello")
    hb = store.put("hello")
    print("hash a:", ha)
    print("hash b:", hb)
    print("blob count:", store.blob_count())

    print("\n=== Commit history for 'greeting_prompt' ===")
    v1 = store.commit("greeting_prompt", "Hello, {name}! Welcome.")
    v2 = store.commit("greeting_prompt", "Hello, {name}! Welcome back.")
    print("v1 hash:", v1)
    print("v2 hash:", v2)
    print("history length:", len(store.history("greeting_prompt")))
    print("latest == v2:", store.latest("greeting_prompt") == v2)

    print("\n=== Round-trip get() ===")
    print("get(v2) ->", repr(store.get(v2)))

    print("\n=== Diff v1 -> v2 ===")
    for line in store.diff(v1, v2):
        print(line)

    print()
    try:
        store.get("deadbeef")
    except KeyError:
        print("get(unknown) raised KeyError as expected.")
