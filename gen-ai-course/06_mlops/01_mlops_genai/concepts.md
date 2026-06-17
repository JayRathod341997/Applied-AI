# MLOps Foundations & Lifecycle — Concepts

MLOps is the discipline of shipping and operating machine-learning systems *reliably and repeatably*. For GenAI the stakes are higher than classic ML because a "release" is no longer just code and a model file — it is a moving bundle of **code + model + prompt + retrieval index + config**, any of which can silently change a system's behaviour. This file builds the foundations: why GenAI needs MLOps at all, how MLOps relates to DevOps and LLMOps, the end-to-end lifecycle, the reference architecture, and the artifact/registry model that underpins everything else in Module 6.

---

## 1. Why MLOps for GenAI?

A clever prototype in a notebook is not a product. The gap between "it worked in the demo" and "it works for 10,000 users every day" is exactly what MLOps closes. GenAI widens that gap because its behaviour depends on artifacts that traditional software pipelines never tracked.

| Concern | Plain software | GenAI system |
|---|---|---|
| **What ships** | Code | Code + model + prompt + index + config |
| **Determinism** | Same input → same output | Same input → *varying* output (temperature, model drift) |
| **Quality signal** | Tests pass / fail | Faithfulness, relevance, hallucination rate, cost |
| **Failure mode** | Crash / 500 | Plausible-but-wrong answers (silent) |
| **Cost** | Roughly fixed per request | Variable per token, can spike 10× |
| **Source of change** | A commit | A new prompt, a re-embedded index, a model upgrade |

The practical consequences a GenAI MLOps practice must handle:

- **Multiple model artifacts** — an LLM, an embedding model, often a reranker, each versioned and swappable.
- **Prompts are code** — a one-word prompt edit can regress quality; prompts need versioning, testing, and rollback.
- **Data & index versioning** — the documents and the vector index built from them define what the system "knows".
- **Stateful, agentic workflows** — multi-step agents are harder to test and reproduce than a single call.
- **Cost & quality monitoring** — you watch *answer quality* and *spend*, not just uptime.

> The single biggest mindset shift: in GenAI, **behaviour is data-defined**, so the things you version, test, and roll back extend well beyond source code.

---

## 2. DevOps vs MLOps vs LLMOps

These three disciplines are nested layers, each adding concerns to the one below. DevOps automates software delivery; MLOps adds the model and data lifecycle; LLMOps specialises MLOps for large language models and prompts.

```
┌──────────────────────────────────────────────────────────┐
│  LLMOps   prompts · tokens · eval/judges · guardrails     │
│  ┌────────────────────────────────────────────────────┐  │
│  │  MLOps   models · datasets · experiments · drift    │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  DevOps   code · build · CI/CD · infra · logs │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

| Aspect | DevOps | MLOps | LLMOps |
|---|---|---|---|
| **Primary artifact** | Code | Code + model + data | Code + model + **prompt** + index |
| **Versioning** | Git | Git + model registry + data | + prompt registry + index snapshots |
| **Testing** | Unit / integration | + data validation, model metrics | + prompt regression, LLM-as-judge |
| **Deployment** | Rolling / blue-green | + staged model rollout | + A/B on prompts & models |
| **Monitoring** | Uptime, latency, errors | + accuracy, **drift** | + faithfulness, hallucination, **token cost** |
| **Rollback** | Revert a commit | Revert model/data version | Revert prompt or model version |

The key takeaway is *continuity*: you do not throw away DevOps when you adopt MLOps. CI/CD, infrastructure-as-code, and observability still apply — you simply add model, data, prompt, and quality concerns on top. (Module 13 covers LLMOps in depth; this module focuses on the MLOps layer.)

---

## 3. The End-to-End GenAI Lifecycle

Almost every GenAI system follows the same loop. The arrows that matter most are the *feedback* ones: monitoring feeds iteration, and iteration feeds new data and prompts back into the pipeline. MLOps is what makes that loop fast, safe, and repeatable.

```
   ┌────────────┐     ┌──────────────┐     ┌───────────────┐
   │ 1. Data    │────►│ 2. Prep &    │────►│ 3. Model /    │
   │ collection │     │   embedding  │     │   prompt dev  │
   └────────────┘     └──────────────┘     └───────┬───────┘
        ▲                                          │
        │                                          ▼
   ┌────┴───────┐     ┌──────────────┐     ┌───────────────┐
   │ 7. Iterate │◄────│ 6. Monitor   │◄────│ 4. Evaluate   │
   │  (feedback)│     │  (quality,   │     │   & validate  │
   └────────────┘     │   cost,drift)│     └───────┬───────┘
                      └──────▲───────┘             │
                             │                     ▼
                             │             ┌───────────────┐
                             └─────────────│ 5. Deploy     │
                                           │  (staged)     │
                                           └───────────────┘
```

| Stage | What happens | Artifacts produced | MLOps practice |
|---|---|---|---|
| **1. Data collection** | Gather documents, logs, labels | Raw dataset version | Data versioning |
| **2. Prep & embedding** | Clean, chunk, embed, index | Processed dataset, vector index | Index snapshots, content hashing |
| **3. Model/prompt dev** | Pick models, write & tune prompts | Prompt versions, fine-tunes | Prompt registry, experiment tracking |
| **4. Evaluate & validate** | Score on a golden set, run judges | Eval reports, metrics | Quality gates, regression tests |
| **5. Deploy** | Stage → production rollout | Released bundle | Registry promotion, canary |
| **6. Monitor** | Watch quality, cost, drift | Telemetry, alerts | Observability, drift detection |
| **7. Iterate** | Feed findings back in | New data/prompts | Retraining triggers, automation |

Each downstream subtopic in Module 6 zooms into part of this loop: [experiment tracking](../02_experiment_tracking/) for stage 3–4, [data & prompt versioning](../03_data_prompt_versioning/) for stages 1–3, and [pipeline orchestration](../04_pipeline_orchestration/) for automating the whole thing.

---

## 4. The MLOps Reference Architecture

A production GenAI platform separates the *control plane* (how you build, version, and govern artifacts) from the *runtime plane* (how requests are served). Drawing these as layers keeps responsibilities clean.

```
┌──────────────────────────────────────────────────────────────┐
│  EXPERIMENTATION   notebooks · experiment tracking · evals     │
├──────────────────────────────────────────────────────────────┤
│  ARTIFACT / REGISTRY   model registry · prompt registry        │
│                        dataset & index versions · stages       │
├──────────────────────────────────────────────────────────────┤
│  PIPELINE / ORCH.   build · train/fine-tune · embed · deploy   │
│                     DAG orchestration · retraining triggers    │
├──────────────────────────────────────────────────────────────┤
│  SERVING / RUNTIME   gateway · LLM serving · retrieval · cache │
├──────────────────────────────────────────────────────────────┤
│  OBSERVABILITY   metrics · logs · traces · drift · cost        │
└──────────────────────────────────────────────────────────────┘
```

| Layer | Responsibility | Typical tooling |
|---|---|---|
| **Experimentation** | Try ideas, log runs, compare results | MLflow, W&B, Jupyter |
| **Artifact / Registry** | Single source of truth for versioned artifacts + their stage | MLflow Registry, DVC, Git |
| **Pipeline / Orchestration** | Automate repeatable workflows | Airflow, Prefect, Dagster, Kubeflow |
| **Serving / Runtime** | Answer live requests | vLLM/TGI, API gateway, vector DB |
| **Observability** | Know what's happening in prod | OpenTelemetry, LangSmith, Grafana |

The **registry is the hinge** of the architecture: experimentation produces candidate artifacts, the registry decides which are promoted to Staging/Production, pipelines deploy the promoted versions, and observability feeds quality data back to experimentation.

---

## 5. Artifacts, Versions, and Stage Promotion

In GenAI, an *artifact* is anything whose change alters system behaviour: a model, a prompt template, a dataset, an index. The registry stores **versioned, immutable** artifacts and tracks which *version* of each occupies each *stage*.

```
Artifact: "support-prompt"
   v1 ─ stage: Archived
   v2 ─ stage: None          ┌─────────────────────────────┐
   v3 ─ stage: Staging  ◄────┤ promote(v3, "Staging")      │
   v4 ─ stage: Production◄────┤ promote(v4, "Production")   │
                             └─────────────────────────────┘
   get_production() ─► v4
```

The canonical promotion flow moves a version through stages, demoting whatever held the target stage before it:

```
   None ──promote──► Staging ──promote──► Production
     ▲                                       │
     └──────────────── Archived ◄────────────┘
                    (demoted on replacement)
```

A minimal in-memory registry — the shape you will build in the exercise:

```python
from dataclasses import dataclass, field

@dataclass
class Version:
    version: int
    artifact: object          # the model/prompt payload
    stage: str = "None"       # None | Staging | Production | Archived

class Registry:
    def __init__(self) -> None:
        self._store: dict[str, list[Version]] = {}

    def register(self, name: str, artifact: object) -> int:
        versions = self._store.setdefault(name, [])
        v = Version(version=len(versions) + 1, artifact=artifact)
        versions.append(v)
        return v.version           # immutable, monotonically increasing

    def promote(self, name: str, version: int, stage: str) -> None:
        # demote whoever currently holds this stage, then promote the target
        for v in self._store[name]:
            if v.stage == stage:
                v.stage = "Archived"
        self._get(name, version).stage = stage

    def get_production(self, name: str):
        for v in self._store[name]:
            if v.stage == "Production":
                return v
        raise KeyError(f"no Production version for {name!r}")
```

Why this matters: a stable name (`"support-prompt"`) plus a stage (`Production`) gives the *runtime* a fixed address, while the *version* underneath can change safely. Rollback becomes "promote the previous version back to Production" — a metadata change, not a redeploy.

| Concept | Definition | Why it matters |
|---|---|---|
| **Artifact name** | Stable logical identifier | Runtime depends on the name, not a version |
| **Version** | Immutable numbered snapshot | Reproducibility & rollback |
| **Stage** | None / Staging / Production / Archived | Controlled, auditable promotion |
| **Promotion** | Move a version to a stage (demote the old one) | Safe release without code changes |

---

## Key Takeaways

- **GenAI behaviour is data-defined**, so MLOps must version code *and* models, prompts, datasets, and indexes — not just source code.
- **DevOps ⊂ MLOps ⊂ LLMOps**: each layer keeps the practices below it and adds new artifacts, tests, and metrics on top.
- **The lifecycle is a loop** — data → prep → model/prompt → evaluate → deploy → monitor → iterate — and MLOps is what makes that loop fast, safe, and repeatable.
- **The registry is the hinge** of the reference architecture: it holds immutable versioned artifacts and tracks which version sits in each stage.
- **Promotion (None → Staging → Production) decouples release from redeploy**: pointing a stable name at a new version — or rolling back to the previous one — is a metadata change, which is exactly what you implement in the [exercise](./exercise_01.md).
