# Data & Prompt Versioning — Concepts

A GenAI result is never produced by code alone. It is produced by *code plus a prompt plus a dataset plus a model plus a pile of parameters*. If you only version the code, you can never explain — let alone reproduce — why last month's eval scored 0.81 and today's scores 0.74. This file walks through how to give those non-code artifacts real identities: content hashing for immutable IDs, prompt and dataset versioning strategies, reproducible bundles, and the DVC pattern that keeps Git fast while tracking gigabyte files.

---

## 1. Why Version Data, Prompts, and Indexes?

In a traditional app the only thing that changes behaviour is code, and Git versions it. In a GenAI app, behaviour is driven by four moving parts that live *outside* your `.py` files:

```
        ┌─────────────────────────────────────────────┐
        │            What drives a GenAI output        │
        │                                              │
        │   CODE  ──┐                                  │
        │   PROMPT ─┼──►  LLM / RAG pipeline ──► OUTPUT │
        │   DATA  ──┤                                  │
        │   MODEL ──┘     (+ params: temp, top_p, k)   │
        └─────────────────────────────────────────────┘
```

If any one of these drifts silently, your output drifts and you have no audit trail. Concretely:

| Artifact | What changes | Failure if unversioned |
|---|---|---|
| **Prompt template** | A reviewer "tweaks" wording in the UI | Quality regresses; nobody can point to the diff |
| **Eval dataset** | Rows added/removed/relabeled | Scores move but you can't tell if model or data changed |
| **Fine-tune / training set** | Rebuilt from a new dump | Can't reproduce the model you shipped |
| **Embedding index** | Re-chunked or re-embedded | Retrieval quality shifts; old answers can't be replayed |
| **Model** | Vendor silently updates `gpt-4o` | Same prompt, different answer, no warning |

The fix is the same idea everywhere: give every artifact a **stable, verifiable identity** and record which identities were used together.

---

## 2. Content-Addressable Storage & Content Hashing

The cleanest identity for an artifact is a **hash of its own bytes**. This is *content-addressable storage* (CAS): the address of a thing **is** a fingerprint of its content. Git, IPFS, Docker layers, and DVC all work this way.

A cryptographic hash like **SHA-256** takes any input and returns a fixed 64-hex-character digest. The same bytes always produce the same digest; a one-character change produces a completely different digest.

```python
import hashlib

def content_hash(content: str) -> str:
    """Stable sha256 hex of a string's UTF-8 bytes."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

p1 = "Summarize the email in one sentence."
p2 = "Summarize the email in one line."

print(content_hash(p1))  # e.g. 9f2c...  (64 hex chars)
print(content_hash(p2))  # totally different digest — one word changed
```

Naming vs content addressing:

```
   Location addressing            Content addressing
   ───────────────────            ──────────────────
   prompt.txt  ──► ??? bytes      sha256(bytes) ──► THE bytes
   (the name is stable, the       (the name is derived from
    content can change silently)   the content; can't lie)
```

Because the address is derived from the content, you cannot point a hash at different bytes — the hash would no longer match. That single property gives you the next three guarantees for free.

---

## 3. Immutability, Deduplication & Integrity

Content hashing buys three things at once:

- **Immutability** — a hash refers to *exactly one* sequence of bytes, forever. `sha256("v1 prompt")` will mean the same thing in 2030. You never "overwrite" a version; you create a new hash.
- **Deduplication** — store content keyed by its hash and identical content collapses to one entry automatically. Re-saving the same eval set 100 times costs one copy.
- **Integrity** — re-hash retrieved bytes and compare to the requested hash; if they differ, the data was corrupted or tampered with.

```python
class ContentStore:
    """A minimal content-addressable store (the core of 'DVC-lite')."""

    def __init__(self) -> None:
        self._blobs: dict[str, str] = {}   # hash -> content

    def put(self, content: str) -> str:
        h = hashlib.sha256(content.encode("utf-8")).hexdigest()
        self._blobs.setdefault(h, content)   # dedup: identical bytes, one slot
        return h

    def get(self, h: str) -> str:
        if h not in self._blobs:
            raise KeyError(f"unknown content hash: {h}")
        return self._blobs[h]
```

```
put("hello")  ──► 2cf24d...   stored
put("hello")  ──► 2cf24d...   SAME hash, NOT stored again  (dedup)
put("hella")  ──► 0a4d55...   new hash, new slot
                              len(store) == 2, not 3
```

This is why two engineers who independently save the same 2 GB dataset never double the storage bill, and why a tampered blob is detectable on read.

---

## 4. Prompt Versioning Strategies

Prompts are code-like (they decide behaviour) but are often edited by non-engineers. You need a versioning scheme. Two complementary ones:

| Strategy | Identity | Human-friendly? | Catches silent edits? | Good for |
|---|---|---|---|---|
| **Semantic version** (`v1.4.0`) | A label humans assign | Yes — readable, ordered | No — label can lie | Release notes, comms, rollback targets |
| **Content hash** (`sha256:9f2c…`) | Derived from the bytes | No — opaque | Yes — bytes can't lie | Audit, dedup, "what exactly ran?" |

Best practice is to use **both**: a friendly semantic label *and* the content hash it resolves to, recorded together. The label is what people talk about; the hash is the ground truth.

```
prompt registry entry
─────────────────────
name:    email_summary
version: v2.1.0            ◄── human label (semver)
hash:    sha256:9f2c1a…    ◄── content hash (immutable truth)
model:   claude-haiku
params:  {temperature: 0.2}
author:  gaurang@…   created: 2026-06-17
```

### Prompt registry

A *prompt registry* is a small service/table that stores every prompt version, its hash, metadata, and history — so prompts are deployed by **reference**, not pasted inline.

```python
class PromptRegistry:
    def __init__(self) -> None:
        self._versions: dict[str, list[str]] = {}   # name -> [hash, ...]
        self._store = ContentStore()

    def register(self, name: str, template: str) -> str:
        h = self._store.put(template)
        self._versions.setdefault(name, []).append(h)
        return h

    def latest(self, name: str) -> str:
        return self._versions[name][-1]             # newest hash

    def get(self, h: str) -> str:
        return self._store.get(h)
```

Managed tools that do this for you: **LangSmith**, **Langfuse**, **PromptLayer**, and **Helicone** all offer prompt versioning, diffing, and "which prompt produced this trace?" lookups.

---

## 5. Dataset & Embedding-Index Versioning

The same hashing idea extends to bulk artifacts, with one wrinkle: you usually want a stable hash of a *whole collection*, not a single string.

**Datasets (eval sets, fine-tune data).** Hash the *canonical serialization* — sort keys, fix line endings, then hash — so the same logical data always hashes the same regardless of dict ordering.

```python
import hashlib, json

def dataset_hash(rows: list[dict]) -> str:
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

**Embedding indexes (vector DB snapshots).** A vector index is derived data: it depends on the source docs, the chunking config, *and* the embedding model. Re-chunk or swap the embedder and retrieval changes. Version an index by recording the inputs that built it (a "recipe"), plus a snapshot:

```
index snapshot id  =  hash(
      docs_hash       (which corpus) +
      chunking_config (size, overlap) +
      embed_model     (e.g. text-embedding-3-large) +
      embed_dim
)
```

```
docs v3  +  chunk{512,50}  +  embedder=te3-large  ─► index snapshot  idx_a1b2…
docs v3  +  chunk{256,25}  +  embedder=te3-large  ─► DIFFERENT snapshot idx_77ef…
```

This lets you pin retrieval: an answer generated against `idx_a1b2…` can be replayed exactly, and you can A/B two index snapshots fairly because everything but the one variable is held constant.

---

## 6. Reproducibility: Pin Everything as One Bundle

Reproducibility = the ability to regenerate a result from recorded inputs. In GenAI that means pinning **all four** drivers together. Pinning the code alone is not enough; pinning the prompt alone is not enough.

```
┌──────────────── Reproducible Bundle ────────────────┐
│  data_hash    : sha256 of the eval/training set     │
│  prompt_hash  : sha256 of the exact template        │
│  model_id     : claude-haiku-2026-03  (pinned ver)  │
│  params       : {temperature:0, top_p:1, seed:7}    │
│  code_commit  : git rev a1b2c3d                      │
│  ──────────────────────────────────────────────     │
│  run_id       : hash(all of the above)              │
│  result       : score=0.81, outputs=…               │
└─────────────────────────────────────────────────────┘
```

```python
import hashlib, json

def bundle_id(data_hash, prompt_hash, model_id, params, code_commit) -> str:
    spec = json.dumps(
        {
            "data": data_hash,
            "prompt": prompt_hash,
            "model": model_id,
            "params": params,
            "code": code_commit,
        },
        sort_keys=True,
    )
    return hashlib.sha256(spec.encode("utf-8")).hexdigest()[:16]
```

Now "reproduce run `a1b2c3d4`" is well-defined: resolve each hash back to its bytes and re-execute. Note that true bit-for-bit reproduction of LLM *outputs* also requires fixing sampling (`temperature=0` or a seed) and pinning a **dated model snapshot** rather than a floating alias like `gpt-4o`.

---

## 7. DVC Concepts: Small Pointers in Git, Content in Remote Storage

Git is great for text and terrible for big binaries — committing a 5 GB dataset bloats the repo forever. **DVC (Data Version Control)** solves this with the content-addressable trick: Git tracks a **tiny `.dvc` pointer file** (a few lines of text containing the content's hash), while the actual bytes live in a **remote store** (S3, GCS, Azure Blob, SSH).

```
        Working dir              Git repo                Remote store
        ───────────             ─────────                ────────────
   data/eval.jsonl   ◄── points ── eval.jsonl.dvc        s3://bucket/files/
   (5 GB, gitignored)            (120 bytes, committed)    md5/a1/b2c3…  (the 5 GB)
                                  ├ md5: a1b2c3…
                                  └ size: 5_000_000_000
```

A `.dvc` file is just text — so Git diffs and history work normally, but on tiny pointers:

```yaml
# eval.jsonl.dvc  (committed to Git)
outs:
  - md5: a1b2c3d4e5f6...
    size: 5000000000
    path: eval.jsonl
```

Typical workflow:

```bash
dvc add data/eval.jsonl     # hashes the file, writes .dvc pointer, gitignores the data
git add data/eval.jsonl.dvc data/.gitignore
git commit -m "Add eval set v3"
dvc push                    # uploads the actual bytes to the remote store

# later, on another machine / CI:
git checkout v3.0           # gets the small .dvc pointer
dvc pull                    # downloads the exact bytes the pointer references
```

Because content is keyed by hash, `dvc push`/`pull` dedup and only transfer what's missing — and `git checkout <old-commit>` + `dvc pull` reconstructs the *exact* dataset that commit referenced.

### Git vs Git-LFS vs DVC

| | Plain Git | Git-LFS | DVC |
|---|---|---|---|
| **What's in the repo** | Full file bytes | LFS pointer (text) | `.dvc` pointer (text) |
| **Where big files live** | In `.git` (forever) | LFS server | Any remote (S3/GCS/Azure/SSH) |
| **Good file size** | KBs of text | MB–GB binaries | GB–TB datasets/models |
| **Storage backend** | Git host | LFS-enabled host | Bring-your-own bucket |
| **ML pipeline / stages** | No | No | Yes (`dvc.yaml`, `dvc repro`) |
| **Dedup by content hash** | Yes (objects) | Yes | Yes |
| **Best for** | Code, prompts (small) | Medium binaries | Datasets, indexes, model weights |

Rule of thumb: **prompts and small configs → plain Git** (they're text and you *want* diffs); **datasets, model weights, and index snapshots → DVC** (huge, binary, need a bring-your-own remote).

---

## Key Takeaways

- **Version the non-code artifacts too.** Prompts, eval/training data, and vector indexes drive behaviour; un-versioned, they drift silently and kill reproducibility.
- **Use the content hash as the identity.** `sha256(bytes)` gives immutability, automatic deduplication, and integrity checking for free — the address *is* the fingerprint.
- **Version prompts with both a semantic label and a hash.** The label is for humans and rollbacks; the hash is the ground truth that catches silent edits. A prompt registry deploys by reference.
- **Version an index by its recipe.** An embedding index = f(docs, chunking, embedder, dim); record all inputs so retrieval can be replayed and A/B'd fairly.
- **Reproducibility = pinning data + prompt + model + params (+ code) as one bundle.** Hash the spec to get a `run_id`; pin dated model snapshots and fix sampling for true reproduction.
- **DVC keeps Git fast:** a tiny `.dvc` pointer (hash + size) lives in Git, the real bytes live in a remote bucket. Use plain Git for small text, DVC for big datasets/models/indexes.
