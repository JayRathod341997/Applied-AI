# Exercise: A Content-Addressable Version Store ("DVC-lite")

## Background

Datasets, prompt templates, and index recipes all need the same thing Git gives code: an immutable identity, automatic deduplication, and a history you can diff. The trick that powers Git and DVC is **content addressing** — the ID of an artifact is the `sha256` of its bytes, so identical content is stored once and any change produces a new ID.

In this exercise you will build a small, offline `VersionStore` that does exactly this for prompt and dataset strings:

1. A content-addressable blob store: `put` content and get back its hash; `get` it back by hash; identical content deduplicates.
2. A named-version layer: `commit` a logical name (e.g. `greeting_prompt`) to new content, keeping a **history** of hashes over time.
3. A simple line-level `diff` between any two stored versions, so you can see what changed.

Everything runs offline using only the Python standard library (`hashlib`, `difflib`).

## Your Task

Open `exercise.py` and complete the `VersionStore` class:

1. **`put(content)`** — compute the `sha256` hex of `content` (UTF-8), store the content keyed by that hash, and return the hash. Putting identical content twice must return the **same** hash and must **not** add a second copy.
2. **`get(hash)`** — return the stored content, or raise `KeyError` if the hash is unknown.
3. **`exists(hash)`** — return `True`/`False`.
4. **`commit(name, content)`** — `put` the content, append its hash to that name's history, and return the hash.
5. **`history(name)`** — return the list of hashes for `name`, oldest → newest (empty list if unknown).
6. **`latest(name)`** — return the newest hash for `name` (raise `KeyError` if none).
7. **`diff(hash_a, hash_b)`** — return a `list[str]` line-level unified diff between the two stored contents (use `difflib.unified_diff`).

## Requirements

- Standard library only (`hashlib`, `difflib`); fully offline, no network, no installs.
- Deduplication must be real: storing the same content N times keeps the blob store size at 1 for that content.
- `get`/`latest` on an unknown key must raise `KeyError` (not return `None`).
- Do not change the provided helper `sha256_hex`.

## How to Run

```bash
python exercise.py
```

The starter raises `NotImplementedError` until you fill in the `# TODO` sections, so it imports cleanly but the demo will fail until complete.

## Expected Output

When finished, running the demo should look something like:

```text
=== Dedup: same content -> same hash, store size unchanged ===
hash a: 2cf24dba5fb0a30e...
hash b: 2cf24dba5fb0a30e...
blob count: 1

=== Commit history for 'greeting_prompt' ===
v1 hash: 5e8b9a...
v2 hash: 7c1f02...
history length: 2
latest == v2: True

=== Round-trip get() ===
get(v2) -> 'Hello, {name}! Welcome back.'

=== Diff v1 -> v2 ===
--- a/5e8b9a
+++ b/7c1f02
@@ -1 +1 @@
-Hello, {name}! Welcome.
+Hello, {name}! Welcome back.

get(unknown) raised KeyError as expected.
```
