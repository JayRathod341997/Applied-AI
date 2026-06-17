# References

- **DVC (Data Version Control) — Documentation** — versioning datasets and models with small `.dvc` pointers in Git and content in a remote store: https://dvc.org/doc
- **DVC — How DVC works (internal files & content addressing)** — the `.dvc` file format and the content-addressed cache: https://dvc.org/doc/user-guide/project-structure/internal-files
- **DVC — Pipelines (`dvc.yaml`, `dvc repro`)** — reproducible ML pipeline stages on top of versioned data: https://dvc.org/doc/user-guide/pipelines
- **Git LFS — Documentation** — replacing large binaries with text pointers tracked by Git: https://git-lfs.com/
- **Pro Git — Git Internals: Git Objects** — how Git itself is a content-addressable store keyed by SHA-1/SHA-256: https://git-scm.com/book/en/v2/Git-Internals-Git-Objects
- **Python `hashlib` — Standard Library** — `sha256` and other secure hashes used for content addressing: https://docs.python.org/3/library/hashlib.html
- **Python `difflib` — Standard Library** — `unified_diff` and sequence-diffing used to compare artifact versions: https://docs.python.org/3/library/difflib.html
- **Wikipedia — Content-addressable storage** — the general concept behind Git, IPFS, Docker layers, and DVC: https://en.wikipedia.org/wiki/Content-addressable_storage
- **LangSmith — Prompt management & versioning** — a prompt registry with versions, diffs, and trace linkage: https://docs.smith.langchain.com/prompt_engineering/concepts
- **Langfuse — Prompt Management** — open-source prompt versioning, labels, and deployment by reference: https://langfuse.com/docs/prompts/get-started
- **PromptLayer — Prompt Registry** — versioning, A/B testing, and tracking which prompt produced which output: https://docs.promptlayer.com/
- **Hugging Face Hub — Datasets versioning (Git + LFS)** — how the Hub versions large datasets and model weights with Git and LFS: https://huggingface.co/docs/hub/datasets-overview
