# Versioning & Deployment — Concepts

A GenAI system is not one artifact — it is a bundle of interdependent ones: application code, model weights, prompt templates, vector indexes, and configuration. Change any one and behaviour can shift. Versioning is the discipline of making every one of those changes *named, reproducible, and reversible*. This file walks through what to version, how Git + DVC + a model registry split the job, how to version prompts, and how promotion and rollback flows give you a safety net.

---

## 1. What to Version (and Why Git Alone Falls Short)

Traditional software versioning tracks text files in Git. GenAI adds artifacts that are large, binary, or "soft" (prose), and that are produced by *other* artifacts. You must version all of them together because they are interdependent.

| Artifact | Examples | Where it lives | Why version it |
|---|---|---|---|
| **Code** | App, pipelines, agents | Git | Logic changes |
| **Models** | Fine-tuned weights, adapters | DVC / registry | Behaviour changes |
| **Prompts** | System & user templates | Git / prompt registry | Output quality shifts dramatically |
| **Embeddings** | Vector indexes | Object store + manifest | Retrieval changes when re-embedded |
| **Agent graphs** | LangGraph / chain definitions | Git | Workflow changes |
| **Config** | Model name, temperature, thresholds | Git / secrets store | Runtime behaviour |
| **Data** | Training sets, documents | DVC | Reproducibility & audit |

Git struggles with the bold rows: a 14 GB `.safetensors` file bloats the repo, diffs are meaningless, and clones become unbearable. The fix is to keep a *pointer* in Git and the *bytes* somewhere built for them.

```
        Git repo (small)                 Remote storage (big)
   ┌────────────────────────┐        ┌───────────────────────────┐
   │ model.bin.dvc  ──────────────────► s3://bucket/ab/cd1234...  │
   │ prompts/v3.yaml         │        │ (actual weights, data)    │
   │ src/, config/           │        └───────────────────────────┘
   └────────────────────────┘
     versioned by commit                addressed by content hash
```

---

## 2. Git + DVC — Pointers in Git, Bytes in Remote Storage

**DVC (Data Version Control)** extends Git for ML. `dvc add` replaces a large file with a tiny `.dvc` metadata file (containing a content hash) that Git tracks, and stores the real bytes in a remote (S3, Azure Blob, GCS). Checking out an old commit + `dvc pull` reconstructs the exact data that commit referenced.

```bash
git init && dvc init
dvc remote add -d store azure://mycontainer/dvcstore

dvc add models/llm_finetuned.safetensors   # creates models/...dvc + .gitignore
git add models/llm_finetuned.safetensors.dvc .gitignore
git commit -m "track v2.1 weights (eval f1=0.87)"
dvc push                                    # bytes -> remote; git push -> pointer
```

For binaries that *should* live in Git's own history (smaller files), use **Git LFS** instead (`git lfs track "*.onnx"`). Rule of thumb: **LFS for small/medium binaries you want in Git history; DVC for large datasets/models and for pipeline reproducibility.**

| | Git | Git LFS | DVC |
|---|---|---|---|
| **File size sweet spot** | < 1 MB text | MB–low GB binaries | GB+ datasets/models |
| **Storage** | Git history | LFS server | Any remote (S3/Blob/GCS) |
| **Stage management** | branches/tags | none | none |
| **Pipeline repro** | no | no | yes (`dvc repro`) |
| **Best for** | code, prompts, config | model files in-repo | data + large models + lineage |

---

## 3. Model Registry — Stages, Immutability, Lineage

A **model registry** (MLflow, Azure ML) is a catalog of *registered model versions* with lifecycle **stages** and lineage back to the run that produced them. Where DVC answers "what bytes did this commit reference?", the registry answers "which version is *Production* right now, and how did it get there?"

```
   register        promote          promote
  ┌────────┐      ┌─────────┐      ┌────────────┐      ┌──────────┐
  │  None  │ ───► │ Staging │ ───► │ Production │ ───► │ Archived │
  └────────┘      └─────────┘      └────────────┘      └──────────┘
   v3 (new)        v2 (tested)       v1 (serving)        v0 (old)
```

```python
from mlflow.tracking import MlflowClient
client = MlflowClient()

mv = client.create_model_version(
    name="llama3-8b-lora", source="runs:/<run_id>/model",
    description="v2.1 - improved prompt templates")

client.transition_model_version_stage(
    name="llama3-8b-lora", version=mv.version, stage="Production")
```

| Property | DVC | Model Registry |
|---|---|---|
| **Stage management** | No | Yes (None/Staging/Production/Archived) |
| **Lineage** | Pipeline (`dvc.yaml`) | Run → params, metrics, data |
| **Access** | Git workflow | UI + API/SDK |
| **Best for** | data-science iteration | production governance |

**Two non-negotiable rules:** versions are **immutable** (never edit a registered version — register a new one) and **semantic** (`MAJOR.MINOR.PATCH`, with rich metadata: base model, data hash, hyperparameters, eval scores, code commit). Immutability is what makes rollback trustworthy: the version you roll back to is byte-identical to what it was.

---

## 4. Prompt Versioning Strategies

Prompts are *soft* assets — a one-word change can swing output quality. Treat them as first-class versioned artifacts, not string literals buried in code.

```
prompts/
└── chatbot/
    └── system_prompt/
        ├── v1.yaml   ← archived
        ├── v2.yaml   ← production
        └── v3.yaml   ← staging
```

A versioned prompt file carries its own metadata and eval contract:

```yaml
version: "2.0"
model_target: "gpt-4o"
eval_score: 0.87
system_prompt: |
  You are a precise summarization assistant. Max 3 sentences;
  keep specific numbers and dates; never add facts not in the source.
evaluation:
  metric: "rouge_l"
  threshold: 0.75
```

| Strategy | Pros | Cons | Best for |
|---|---|---|---|
| **Git-based (YAML files)** | Simple, diff-able, auditable | No runtime promotion | Most teams, start here |
| **Registry-backed (DB)** | Programmatic, A/B, metrics | Needs infra | Many prompts, live experiments |
| **Feature flags** | Gradual rollout, kill switch | Flag-management overhead | Risky changes, % rollout |
| **Inline in code** | Fastest prototyping | Not production-ready | Throwaway spikes |

Feature-flag A/B routing buckets users deterministically so the same user always sees the same variant:

```python
def prompt_version(user_id: str, rollout_pct: int, target: str, default: str) -> str:
    if hash(user_id) % 100 < rollout_pct:   # deterministic bucket
        return target
    return default                          # control group
```

---

## 5. Promotion Flows & Rollback

Promotion moves *one chosen version* up the environment ladder; rollback moves the active pointer *back* to a known-good version. The artifact never changes — only which version each environment points at.

```
   Dev ───────► Staging ───────► Production
   (HEAD)       (candidate)      (active)
                                   │  metric breach
                                   ▼
                              ROLLBACK ──► previous stable
```

**Promotion** is gated: a version only advances when it passes that environment's checks (eval gate in Staging, approval for Production). **Rollback** is the inverse and must be *pre-planned and fast* — for GenAI the "roll back" target depends on what changed:

| What regressed | Rollback action | Mechanism |
|---|---|---|
| Model quality | Re-point registry stage to prior version | `transition_model_version_stage` |
| Prompt | Revert prompt file / registry entry | Git revert + redeploy |
| App code | Roll back container image | revision rollback |
| Infra | Re-apply previous IaC state | `terraform apply` prior state |
| Canary errors | Shift traffic away | weight → 0% |

Automated rollback fires on triggers, not vibes:

| Trigger | Threshold | Detection |
|---|---|---|
| Error-rate spike | > 5% over 5 min | 5xx / total |
| P99 latency | > 3000 ms | APM percentile |
| Quality drop | < 80% on golden set | live regression eval |
| Cost anomaly | > 2× baseline | token/cost tracking |

The two ingredients every rollback needs: **immutable versions** (so the target is exactly what it was) and **deployment history** (so you know what the previous stable version *was*). That history — `(version, env, timestamp, action)` records — is exactly what you will build in the exercise.

```python
# A deployment-history record is the minimal audit trail for rollback.
record = {
    "version": "v2",
    "action": "deploy",        # deploy | rollback
    "timestamp": 1718600000,
    "from_version": "v1",      # what it replaced
}
```

---

## Key Takeaways

- **Version everything together** — code, models, prompts, embeddings, config, data — because they are interdependent; a change in one can change system behaviour.
- **Git for pointers, remote storage for bytes.** Use Git LFS for in-repo binaries and DVC for large datasets/models and pipeline reproducibility.
- **A model registry adds what DVC lacks: lifecycle stages, governance, and run lineage.** Keep versions **immutable** and **semantically numbered**.
- **Prompts are first-class artifacts.** Start with Git-based YAML; graduate to a registry or feature flags when you need runtime promotion and A/B testing.
- **Promotion goes up (gated), rollback goes back (fast).** Reliable rollback needs immutable versions plus a deployment-history audit trail and metric-based triggers.
