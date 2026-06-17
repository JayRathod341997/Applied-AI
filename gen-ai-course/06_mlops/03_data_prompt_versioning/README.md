# Data & Prompt Versioning

This subtopic covers how to give the *non-code* artifacts of a GenAI system — datasets, prompt templates, and embedding indexes — the same rigor that Git gives your source code. You will learn why a **content hash** (sha256 of the bytes) makes the cleanest possible artifact ID: immutable, automatically deduplicated, and trivially verifiable. You will see how *reproducibility* comes from pinning data + prompt + model + config together as one bundle, so a result can be regenerated months later. Finally you will learn the core idea behind **DVC**: Git stores a tiny `.dvc` pointer file while the heavy content lives in remote object storage. The goal is to make "which exact prompt and which exact eval set produced this score?" a question you can always answer.

## Topics

- Why datasets, prompts, and vector indexes need versioning (not just code)
- Content-addressable storage and content hashing with `hashlib` (sha256)
- Immutability, deduplication, and integrity from hash-based identity
- Prompt versioning strategies: semantic versions vs content hashes, prompt registries
- Dataset and embedding-index snapshot versioning
- Reproducibility: pinning data + prompt + model + params into one bundle
- DVC concepts: small `.dvc` pointers in Git, content in remote storage (Git vs Git-LFS vs DVC)

## Files in this subtopic

- `concepts.md` — the teaching content: ASCII diagrams, comparison tables, and focused code snippets for every topic above.
- `quiz.md` — 10 multiple-choice questions with answers and explanations to check your understanding.
- `exercise_01.md` — the brief for the hands-on coding exercise (a content-addressable "DVC-lite" version store).
- `exercise.py` — a runnable starter scaffold with helpers provided; you fill in the `# TODO` sections.
- `solution.py` — the complete, offline, fully-tested reference implementation of the store.
- `interview.md` — interview questions and model answers on versioning data, prompts, and indexes.
- `references.md` — curated links to authoritative docs and articles for deeper study.

## Start

Begin with `concepts.md`, then test yourself with `quiz.md`, and finally build the version store in `exercise.py` (checking against `solution.py`).
