# Modules 6 (MLOps), 8 (CI/CD), 9 (Monitoring) — Content Design Spec

**Date:** 2026-06-17
**Target:** `gen-ai-course/06_mlops/`, `gen-ai-course/08_cicd/`, `gen-ai-course/09_monitoring/`
**Goal:** Build these three underdeveloped modules up to the depth and consistency of the freshly-built Module 7 (`gen-ai-course/07_architecture/`), using the full 8-file-per-subtopic template.

## Background

| Module | Current state | Rich source in `course-content`? |
|---|---|---|
| `06_mlops` | 1 subtopic `01_mlops_genai` with only `interview.md` (172 lines) | ❌ none |
| `08_cicd` | 1 subtopic `01_versioning_deployment` with only `interview.md` (114 lines) | ✅ `course-content/part-4-production/module-8-cicd/` (concepts 1377, interview 553, quiz 339) |
| `09_monitoring` | 3 subtopics; `interview.md` solid, `02`'s `concepts.md` decent; everything else stub/placeholder | ✅ `course-content/part-4-production/module-9-monitoring/` (concepts 1136, interview 424, quiz 389) |

The **gold-standard template** to match exactly (depth, tone, file set) is:
`gen-ai-course/07_architecture/01_architecture_design/` — read every file there before writing.

The `course-content` copies are a **source to adapt from, not a target to modify.**

## Per-subtopic file set (the 8-file template)

| File | Purpose | Depth target |
|---|---|---|
| `README.md` | Short intro + topic list + "files in this subtopic" + start pointer | ~20–30 lines |
| `concepts.md` | Main teaching content: ASCII diagrams, comparison tables, focused code snippets, "Key Takeaways" | 150–300 lines |
| `quiz.md` | Multiple-choice Q&A with answer + explanation per question | 8–12 questions |
| `exercise_01.md` | Brief: background, task, requirements, how-to-run, expected output | ~40–60 lines |
| `exercise.py` | Runnable starter scaffold; provided mocks + `# TODO` sections that raise `NotImplementedError`; `__main__` demo | — |
| `solution.py` | Complete reference impl; ends with `__main__` demo + `assert`-based checks; **runs fully offline** | — |
| `interview.md` | Interview Q&A with model answers | 10–20 questions |
| `references.md` | Curated external links with one-line descriptions | curated |

## Module structure

### 06_mlops (no source — design from scratch; avoid overlap with `13_LLMops`)
- `01_mlops_genai` — **upgrade** existing. Foundations & lifecycle: why MLOps for GenAI, DevOps vs MLOps vs LLMOps, the end-to-end lifecycle, reference architecture. **Preserve** the existing `interview.md` content (expand it, don't delete good material).
  - Exercise: an in-memory **model/prompt registry** — register versioned artifacts, promote across stages (None→Staging→Production), fetch the current Production version.
- `02_experiment_tracking` — **new**. Experiment tracking (MLflow/W&B concepts), logging params/metrics/artifacts, comparing runs, picking the best run, model registry hand-off.
  - Exercise: an **experiment tracker** — log runs with params+metrics, query the best run by a target metric.
- `03_data_prompt_versioning` — **new**. Versioning datasets, prompts, and embeddings/indexes; content-hash identity; reproducibility; DVC concepts.
  - Exercise: a **content-addressable version store** (DVC-lite) — hash content, store versions, retrieve by hash, diff two versions.
- `04_pipeline_orchestration` — **new**. Training/inference pipelines, DAG orchestration (Airflow/Prefect concepts), retraining triggers, automation.
  - Exercise: a **mini DAG runner** — topologically order stages, run them, support a stage retry on failure.

### 08_cicd (source: `module-8-cicd`)
- `01_versioning_deployment` — **upgrade** existing. Versioning AI models & prompts (Git+DVC, model registry/MLflow, prompt versioning strategies), promotion flows, rollback. Adapt source §8.1.1–8.1.3, §8.2.6. **Preserve** existing `interview.md` content.
  - Exercise: an **artifact version registry with rollback** — register versions, deploy one, roll back to a prior version, track history.
- `02_automated_testing` — **new**. Automated testing for LLM apps: prompt unit tests, golden/reference sets, regression gates, LLM-as-judge, CI pipelines (GitHub Actions/Azure DevOps). Adapt source §8.1.4, §8.2.1–8.2.2.
  - Exercise: a **prompt regression test runner** — run a (mock) prompt against a golden set, score outputs, fail the build if pass-rate drops below a threshold.
- `03_deployment_strategies` — **new**. Containerization (Docker), IaC (Terraform/Bicep concepts), blue-green & canary deployments, environment management, automated rollback. Adapt source §8.2.3–8.2.5, §8.2.7.
  - Exercise: a **canary release controller** — shift traffic in increments, monitor a (mock) error rate, auto-promote on success or auto-rollback when errors exceed a threshold.

### 09_monitoring (source: `module-9-monitoring`; keep existing 3 subtopics)
- `01_observability` — **fill stubs**. Three pillars (metrics/logs/traces), LLM-specific metrics, latency percentiles, cost metrics, alerting, dashboards, LangSmith/Langfuse. Adapt source §9.1.
  - Exercise: a **metrics collector** — record per-request latency+tokens+cost, compute P50/P95/P99, total/avg cost, error rate.
- `02_drift_detection` — **fill stubs** (concepts.md is decent — refine/expand, don't gut it). Types of drift, PSI/KS/KL methods, embedding drift, retraining triggers. Adapt source §9.2.
  - Exercise: a **drift detector** — compute PSI (and a simple distribution comparison) between a baseline window and a current window; flag when drift exceeds a threshold.
- `03_logging_strategies` — **fill stubs**. Structured logging, log levels, PII redaction, distributed tracing (OpenTelemetry), log aggregation, retention. Adapt source §9.3.
  - Exercise: a **structured logger with PII redaction** — emit JSON log records, redact emails/phones/keys, support correlation IDs.

## Content & exercise principles

- **Source reuse:** adapt heavily from the matching `course-content` module (08, 09). Match the Module-7 style — ASCII diagrams, comparison tables, focused code snippets. Don't reinvent material that already exists.
- **Self-contained exercises:** every `exercise.py`/`solution.py` runs **offline** with no API keys / network — use mock/stub LLM clients and mock embedders. Each `solution.py` ends with a `__main__` demo and `assert`-based checks so it self-verifies.
- **No new dependencies:** rely only on the Python standard library (and whatever `gen-ai-course/requirements.txt` already provides). Prefer stdlib + mocks.
- **Consistency:** all subtopics across all three modules follow this one shared template so the modules read uniformly with Module 7.
- **Root READMEs:** rewrite each module's root `README.md` to list and link every subtopic with objectives and prerequisites.

## Out of scope (YAGNI)
- Do not modify the `course-content` copies or any `.pptx`.
- No new external dependencies.
- No security/compliance subtopic in any module (covered by Module 10 governance / 13 LLMops).
- Don't touch other modules.

## Success criteria
- 06_mlops: 4 subtopics, 08_cicd: 3 subtopics, 09_monitoring: 3 subtopics — each with the complete 8-file set, consistent in depth/style with Module 7.
- Each module's root `README.md` lists and links all its subtopics.
- Every `solution.py` runs offline (`python solution.py`) and self-verifies via `__main__` + asserts.
- Existing strong `interview.md` content in 06/08/09 is preserved (expanded, not deleted).
