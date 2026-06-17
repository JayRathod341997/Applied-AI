# Versioning & Deployment — Interview Questions

Interview questions and model answers on versioning GenAI artifacts, promotion flows, and rollback. (Expanded from the original Module 8 set; the original questions are preserved below.)

---

## 1. What do you version in GenAI systems?

**Answer:** Far more than code. The interdependent artifacts are:

- **Code** — application logic, pipelines, agents
- **Models** — LLM weights, LoRA adapters, fine-tunes
- **Prompts** — system and user templates (treated as first-class assets)
- **Embeddings** — vector-database indexes (they change whenever you re-embed)
- **Agent graphs** — LangGraph / LangChain workflow definitions
- **Configuration** — model name, temperature, thresholds
- **Data** — training data, source documents

They must be versioned *together* because a change in any one can change overall system behaviour, and reproducing a result requires the exact combination.

---

## 2. How does CI/CD differ for software vs ML vs GenAI systems?

**Answer:**

| Aspect | Software | ML | GenAI |
|---|---|---|---|
| Build | Compile | Train | Prompt + build |
| Test | Unit tests | Quality metrics | Behaviour / eval tests |
| Artifacts | Binary | Model weights | Prompts + indexes + weights |
| Rollback | Easy (redeploy) | Hard (retrain) | Re-point prompt/model version |

GenAI adds an **evaluation gate** (quality on a golden set) that has no equivalent in standard software pipelines, and its outputs are probabilistic rather than deterministic.

---

## 3. How do you design promotion flows for GenAI?

**Answer:** A gated ladder:

```
Dev → Staging → Production
```

1. **Dev** — test new prompts/models locally against a small eval set.
2. **Staging** — integration tests, the full eval gate, and A/B against a small slice of traffic.
3. **Production** — gradual rollout (canary) with live monitoring; promotion to Production usually requires explicit approval.

Each arrow is a *gate*: a version only advances when it passes that environment's checks.

---

## 4. What are rollback strategies for GenAI?

**Answer:** Rollback target depends on what regressed:

- **Prompt rollback** — revert to the previous prompt version (Git revert / registry re-point).
- **Model rollback** — transition the registry stage back to the prior model version.
- **Embedding rollback** — restore the previous vector index from its manifest.
- **Agent rollback** — revert to the previous workflow graph.
- **Code/infra rollback** — roll back the container image or re-apply previous IaC state.

All of them rely on **immutable versions** plus a **deployment-history audit trail** so you know exactly what the previous stable version was.

---

## 5. How do you manage changes to agent logic?

**Answer:**

1. **Version control** — store agent graphs in Git.
2. **Testing** — exercise the new agent behaviour against golden traces.
3. **Canary** — deploy to a small subset of traffic first.
4. **Monitoring** — watch for tool-call failures, loops, and quality drops.
5. **Rollback plan** — always keep the previous graph one switch away.

---

## 6. What CI/CD tools work well with GenAI?

**Answer:**

- **GitHub Actions** — workflow automation, GitHub-native.
- **GitLab CI** — pipeline management.
- **Jenkins** — custom/self-hosted pipelines.
- **AWS CodePipeline** — cloud-native on AWS.
- **Azure DevOps** — Microsoft ecosystem, variable groups + Key Vault.
- **MLflow / Weights & Biases** — experiment tracking and model registry hand-off.

---

## 7. How do you test prompts in CI/CD?

**Answer:**

1. **Unit tests** — prompt builders, parsers, validators (deterministic).
2. **Golden sets** — curated input → expected-content pairs.
3. **Regression tests** — ensure quality does not degrade across prompt changes.
4. **Quality checks** — hallucination detection, guardrail/safety validation.

The regression suite runs as an **eval gate** that blocks deployment if the pass-rate drops below a threshold.

---

## 8. Why isn't Git alone enough to version models and datasets?

**Answer:** Git is built for line-based text. Multi-GB binary weights or datasets bloat history, produce meaningless diffs, and make clones painfully slow. The standard fix keeps a small **pointer** in Git and stores the **bytes** elsewhere: **Git LFS** for medium in-repo binaries, **DVC** for large datasets/models plus pipeline reproducibility. DVC's `.dvc` file holds a content hash; `dvc push` sends the bytes to a remote (S3/Blob/GCS).

---

## 9. When would you choose Git LFS vs DVC?

**Answer:**

- **Git LFS** — for small/medium binaries you genuinely want in Git history (an ONNX export, an image asset). Simple `git lfs track`.
- **DVC** — for large datasets and models, *and* when you need reproducible pipelines (`dvc.yaml`, `dvc repro`) and lineage between data, params, and outputs.

Many teams use both: LFS for in-repo binaries, DVC for the heavy data/model artifacts.

---

## 10. What does a model registry give you beyond DVC?

**Answer:** Lifecycle **stages** (None → Staging → Production → Archived), governance/approval workflows, a UI + API, and **run lineage** — the params, metrics, and data that produced each version. DVC answers "what bytes did this commit reference?"; the registry answers "which version is Production right now, and how did it get there?"

---

## 11. Why must registered model versions be immutable?

**Answer:** Immutability is what makes rollback trustworthy. If you can edit a registered version in place, the thing you roll back to is no longer what it was — destroying reproducibility and the audit trail. The correct response to a needed change is to register a *new* version, never mutate an existing one.

---

## 12. How do you version prompts as first-class artifacts?

**Answer:** Store them as versioned YAML files (or registry entries) carrying their own metadata and eval contract (model target, version, eval metric + threshold). Start with **Git-based** files (simple, diff-able, auditable). Graduate to a **registry-backed** store when you need programmatic access and A/B testing, or **feature flags** when you need gradual rollout and kill switches. Avoid hardcoding prompts as string literals in app code.

---

## 13. How does feature-flag A/B routing assign users to prompt variants?

**Answer:** By hashing a stable identifier: `hash(user_id) % 100 < rollout_pct`. This buckets each user *deterministically*, so the same user consistently sees the same variant — essential for a clean experiment. Random per-request routing would flip users between control and treatment and contaminate the results.

---

## 14. What triggers should drive an automated rollback for a GenAI service?

**Answer:** A mix of generic and AI-specific signals:

- **Error-rate spike** (> 5% over 5 min) — 5xx / total.
- **P99 latency** (> 3000 ms) — from APM.
- **Quality drop** (< threshold on a golden set) — *AI-specific*, caught by a live regression eval.
- **Cost anomaly** (> 2× baseline) — token/cost tracking.

The quality and cost triggers are what make GenAI rollback different — a change can pass code tests yet degrade output quality or blow up token spend.

---

## 15. What is the minimal data you need to support fast rollback?

**Answer:** Two things: (1) **immutable versions** so the rollback target is byte-identical to what it was, and (2) a **deployment-history audit trail** — records of `(version, action, from_version, timestamp)` — so you know what the previous stable version was and can re-point to it in one step. Without the history, "roll back to the last good version" is a guess.

---

## Summary

Key topics: **what to version** (everything, together), **how** (Git for pointers, DVC/LFS for bytes, a registry for stages + lineage), **prompt versioning** (first-class, Git → registry → flags), and **promotion + rollback** (gated up, fast back, backed by immutability and a deployment-history trail).
