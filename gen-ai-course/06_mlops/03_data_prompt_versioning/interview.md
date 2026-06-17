# Data & Prompt Versioning - Interview Questions

### Q1: Why isn't versioning your code in Git enough to make a GenAI system reproducible?

**Answer:** Because in a GenAI system, behaviour is driven by more than code. A given output is a function of:

- **Code** — the pipeline logic
- **Prompt** — the exact template text
- **Data** — the eval/training/retrieval corpus
- **Model** — the specific (ideally dated) model snapshot
- **Params** — temperature, top_p, top_k, seed, etc.

Git only versions the code. If the prompt is edited in a UI, the eval set gains rows, or the vendor silently updates `gpt-4o`, your output changes with no corresponding commit. Reproducibility requires pinning *all* of these together, not just the code.

---

### Q2: What is content-addressable storage, and why is it the ideal way to identify artifacts?

**Answer:** Content-addressable storage (CAS) means an artifact's identifier **is** a hash of its own bytes (e.g. `sha256`). The address is *derived from* the content rather than assigned externally. This gives three properties for free:

| Property | Why it follows from hashing |
|---|---|
| **Immutability** | A hash maps to exactly one byte sequence, forever |
| **Deduplication** | Identical bytes hash identically -> stored once |
| **Integrity** | Re-hash on read; mismatch = corruption/tampering |

Git, IPFS, Docker image layers, and DVC all use this model. A location-based name (`prompt.txt`) can silently point at new bytes; a content address cannot lie.

---

### Q3: How does a content hash give you deduplication "for free"?

**Answer:** You key storage by the hash. On `put`, you compute the hash and insert only if that key is absent (`setdefault`/`if not exists`). Identical content always produces the same digest, so the second insert is a no-op. Two engineers independently saving the same 2 GB dataset, or re-running a pipeline 100 times on unchanged data, all collapse to a single stored copy — no manual coordination required.

---

### Q4: A junior says "let's just name our prompts v1, v2, v3 in a folder." What problems does that have, and what's better?

**Answer:** Sequential filenames are *location* addressing: the name says nothing about the content and can be edited in place without anyone noticing. Problems:

- Someone overwrites `v2.txt` and the "v2" everyone references is now silently different.
- No dedup — `v2` and `v4` may be byte-identical and you'd never know.
- No integrity check.

Better: store the content under its **content hash**, and keep a human-friendly **semantic version label** that resolves to that hash. The label is for communication and rollbacks; the hash is the immutable ground truth.

---

### Q5: Compare semantic versioning and content hashing for prompts. When do you use each?

**Answer:**

| | Semantic version (`v2.1.0`) | Content hash (`sha256:9f2c…`) |
|---|---|---|
| Assigned by | Humans | Derived from bytes |
| Readable / ordered | Yes | No |
| Catches silent edits | No | Yes |
| Use for | Release notes, rollback targets, comms | Audit, dedup, "exactly what ran?" |

Use **both together**. The semantic label is what humans and changelogs reference; the hash is what you log alongside every trace so you can later prove which exact bytes produced a result.

---

### Q6: What is a prompt registry and why deploy prompts "by reference"?

**Answer:** A prompt registry is a store (table or managed service) holding every prompt version, its content hash, metadata (author, model, params), and history. Deploying *by reference* means your application fetches a prompt by name/version/hash at runtime instead of having the text pasted inline in code.

Benefits: non-engineers can iterate on prompts without code deploys; every production trace can record the exact prompt hash used; you can roll back to a previous version instantly; and you get diffs between versions. Managed options include LangSmith, Langfuse, PromptLayer, and Helicone.

---

### Q7: How do you version a vector/embedding index, and why is it trickier than versioning a prompt?

**Answer:** An index is **derived data** — it isn't authored, it's *built* from inputs. So you version it by versioning the recipe that produced it:

```
index snapshot id = hash(docs_hash + chunking_config + embed_model + embed_dim)
```

Two index builds from the same docs but different chunk sizes, or the same chunks but a different embedder, are *different artifacts* with different retrieval behaviour. Recording all inputs lets you (a) replay an answer against the exact index it used and (b) A/B two snapshots by changing one variable at a time. A prompt, by contrast, is authored content you can hash directly.

---

### Q8: How would you hash a dataset of records so the same logical data always yields the same hash?

**Answer:** Serialize it **canonically** before hashing — sort keys, fix separators and line endings — so the byte representation is deterministic regardless of in-memory dict ordering:

```python
canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"))
h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

Without canonicalization, the same records in a different key order produce different bytes and therefore a different (misleading) hash. For very large datasets you'd hash a stable streamed serialization or a Merkle tree of chunk hashes rather than loading everything into memory.

---

### Q9: What exactly goes into a "reproducible bundle," and how do you turn it into a single id?

**Answer:** The bundle pins every driver of the output:

- `data_hash` — eval/training set
- `prompt_hash` — exact template
- `model_id` — dated model snapshot
- `params` — temperature, top_p, seed, k, …
- `code_commit` — git rev

You produce one `run_id` by hashing the canonical JSON of that spec. "Reproduce run X" then means: resolve each referenced hash back to its bytes and re-execute with the recorded model and params. For bit-identical *outputs* you also need deterministic sampling (`temperature=0` or a fixed seed) and a pinned model snapshot — a floating alias like `gpt-4o` breaks reproducibility.

---

### Q10: Explain DVC in one minute. What lives in Git and what lives elsewhere?

**Answer:** DVC (Data Version Control) keeps Git fast by separating pointers from payload. When you `dvc add data/eval.jsonl`, DVC:

1. Hashes the file and writes a tiny text **`.dvc` pointer** (hash + size + path).
2. Adds the real data to `.gitignore`.
3. Lets you commit the *pointer* to Git (a few bytes).
4. On `dvc push`, uploads the actual bytes to a **remote** (S3/GCS/Azure/SSH).

To reconstruct an exact version on another machine: `git checkout <commit>` gets the pointer, then `dvc pull` downloads the precise bytes that pointer references. Git history stays small; large content lives in object storage, deduplicated by content hash.

---

### Q11: When would you choose plain Git vs Git-LFS vs DVC?

**Answer:**

| Tool | Repo holds | Big files in | Best for |
|---|---|---|---|
| **Plain Git** | Full bytes | `.git` (forever) | Code, prompts, small configs (you want diffs) |
| **Git-LFS** | LFS pointer | LFS server | Medium binaries (MB–GB) |
| **DVC** | `.dvc` pointer | Any remote bucket | Large datasets, model weights, index snapshots; ML pipelines |

Rule of thumb: prompts and small text → plain Git (diffable, tiny); datasets, weights, and index snapshots → DVC (huge, binary, bring-your-own remote, plus `dvc.yaml`/`dvc repro` for pipeline stages). Git-LFS is the middle ground but lacks DVC's pipeline and bring-your-own-bucket model.

---

### Q12: How does content hashing let you *verify integrity* of a downloaded dataset or model?

**Answer:** Because the address is the fingerprint, you re-hash what you received and compare. After `dvc pull` (or any download), recompute the `sha256`/`md5` of the bytes and check it against the hash recorded in the `.dvc` pointer. A match proves the content is exactly what the pointer promised; a mismatch flags corruption in transit or tampering at the remote. This is the same mechanism Docker uses to verify image layers and that package managers use for checksums.

---

### Q13: Your eval score dropped from 0.81 to 0.74 between two runs. How does proper versioning let you find the cause?

**Answer:** If each run logged a reproducible bundle (data_hash, prompt_hash, model_id, params, code_commit), you diff the two bundles:

- Different `prompt_hash` → a prompt edit; `diff` the two prompt versions.
- Different `data_hash` → the eval set changed; diff the datasets.
- Different `model_id` → vendor/model change.
- Same hashes but different output → non-deterministic sampling (temperature/seed not fixed).

Without versioning, all five variables move at once and you can only guess. With it, the regression is reduced to a single changed hash you can inspect line by line.

---

### Q14: What are the limits of "reproducibility" with hosted LLMs even when you pin everything?

**Answer:** Even with a pinned bundle you face residual non-determinism:

- **Floating model aliases** — `gpt-4o`/`claude-3-5-sonnet` can be silently updated; pin a **dated snapshot** instead.
- **Sampling** — non-zero temperature/top_p makes outputs vary; set `temperature=0` or a fixed seed where supported (and even then, GPU/floating-point and batching effects can cause tiny drift).
- **Hidden server-side changes** — safety filters, system-prompt injection, or routing you can't see.
- **Tool/RAG context** — if retrieval pulls live data, the context isn't pinned unless you also version the index snapshot.

So "reproducible" for hosted LLMs usually means *reproducible inputs and configuration*, with a documented note that outputs are reproducible only up to the provider's determinism guarantees. Self-hosted models with fixed weights and seeds get you closest to bit-exact replay.
