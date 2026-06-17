# Quiz

## Question 1

In a GenAI pipeline, versioning your application code in Git is not enough to reproduce a past result. Which set of artifacts must *also* be pinned?

A) Only the prompt template
B) Prompt, dataset, model, and parameters
C) Only the model id
D) Only the random seed

---

**Answer: B**

A GenAI output is produced by code *plus* the prompt, the dataset, the model, and the sampling parameters. Pinning only the code (or only one of the others) leaves several silent variables that can change the output, so all of them must be recorded together.

---

## Question 2

What does "content-addressable storage" mean?

A) Content is stored at a path the user picks
B) The address of an artifact is derived from a hash of its own bytes
C) Content is encrypted before storage
D) Each file gets a sequential integer ID

---

**Answer: B**

In content-addressable storage the identifier *is* a fingerprint (hash) of the content. Because the address is computed from the bytes, it cannot point to different bytes without the hash changing — the basis of Git, IPFS, Docker layers, and DVC.

---

## Question 3

You compute `sha256` of a prompt, store it, then store the exact same prompt string again. What happens?

A) A second copy is stored under a new hash
B) An error is raised for a duplicate
C) The same hash is returned and no second copy is stored (deduplication)
D) The content is appended to the first entry

---

**Answer: C**

Identical bytes always produce the same SHA-256 digest. A content-addressable store keyed by that digest collapses duplicates to a single slot, so re-saving identical content returns the same hash and consumes no extra storage.

---

## Question 4

How do you verify that bytes retrieved from a content store were not corrupted or tampered with?

A) Check the file's modification timestamp
B) Re-hash the retrieved bytes and compare to the requested hash
C) Compare the file size only
D) Trust the storage layer

---

**Answer: B**

Integrity is checked by re-hashing the retrieved content and confirming the digest equals the hash you asked for. Any change to the bytes — corruption or tampering — produces a different digest, so the mismatch is detectable.

---

## Question 5

Why is it best practice to track a prompt by *both* a semantic version (`v2.1.0`) and a content hash?

A) Hashes are faster to type than version numbers
B) The semantic label is human-friendly while the hash is the immutable ground truth that catches silent edits
C) Semantic versions deduplicate storage
D) Content hashes are ordered chronologically

---

**Answer: B**

A semantic label is readable and good for comms and rollbacks, but a human can mislabel or silently edit a prompt. The content hash is derived from the bytes, so it cannot lie about what actually ran. Recording both gives readability *and* a verifiable source of truth.

---

## Question 6

When hashing a dataset of dict rows so the same logical data always produces the same hash, what step is essential?

A) Hash each row separately and add the digests
B) Serialize canonically (e.g. `json.dumps(..., sort_keys=True)`) before hashing
C) Shuffle the rows first
D) Compress the data with gzip

---

**Answer: B**

Dict/JSON key ordering can vary between runs, producing different bytes for the same logical content. Canonical serialization (sorted keys, fixed separators) makes the byte representation deterministic so equal data always yields an equal hash.

---

## Question 7

An embedding/vector index is *derived* data. Which inputs should its version (snapshot id) be a function of?

A) Only the embedding model name
B) Only the number of vectors
C) The source docs, the chunking config, and the embedding model (and dim)
D) The wall-clock time it was built

---

**Answer: C**

Re-chunking or swapping the embedder changes retrieval even if the source docs are unchanged. Deriving the snapshot id from docs + chunking config + embedding model (+ dimension) makes index versions reproducible and lets you A/B one variable at a time.

---

## Question 8

What is the purpose of hashing the full spec (data + prompt + model + params + code) into a single `run_id`?

A) To compress the run metadata
B) To give the reproducible bundle one immutable identity that resolves back to every exact input
C) To encrypt the parameters
D) To pick a random model

---

**Answer: B**

Hashing the whole spec produces a single, stable `run_id` for the bundle. "Reproduce run X" becomes well-defined: resolve each referenced hash back to its bytes and re-execute with the same model and params.

---

## Question 9

In DVC, what is actually committed to the Git repository for a 5 GB dataset?

A) The full 5 GB file
B) A small `.dvc` pointer file containing the content hash and size
C) A compressed copy of the dataset
D) Nothing; DVC bypasses Git entirely

---

**Answer: B**

DVC stores the heavy bytes in a remote (S3/GCS/Azure/SSH) and commits only a tiny text `.dvc` pointer (hash + size + path) to Git. Git history stays small and fast while `dvc pull` reconstructs the exact bytes the pointer references.

---

## Question 10

You need to version GB-to-TB datasets and model weights in your own S3 bucket, with ML pipeline stages and `repro`. Which tool fits best?

A) Plain Git
B) Git-LFS
C) DVC
D) A shared network drive with manual filenames

---

**Answer: C**

DVC is built for large datasets/models in a bring-your-own remote, deduplicates by content hash, and adds pipeline stages (`dvc.yaml`, `dvc repro`). Plain Git bloats on big binaries, and Git-LFS handles medium binaries but lacks pipeline/`repro` features and a bring-your-own bucket model.
