# Module 12 — Deployment

Everything you need to take a GenAI system from a working prototype on your laptop to a production service that handles real users, real traffic, and real failure modes.

---

## What You Will Learn

By the end of this module you will be able to:

- Choose the right deployment option (cloud API, self-hosted, serverless, edge, hybrid) based on latency, cost, and data-privacy constraints
- Containerize a GenAI inference server with Docker and orchestrate it with Kubernetes
- Apply blue-green, canary, and rolling deployment strategies safely
- Optimize models with quantization and continuous batching before going live
- Deploy to **Azure** (Container Apps, AKS, Azure OpenAI, Azure ML) and **AWS** (Bedrock, SageMaker)
- Build a full CI/CD pipeline with automated smoke tests and rollback
- Monitor latency, token spend, and error rates using Prometheus + Grafana or Azure Monitor

---

## Module Map

```
12_deployment/
│
├── 01_deployment_overview/          ← Start here
│   └── README.md                    Options, trade-offs, patterns, decision framework
│
├── 02_deployment_techniques/        ← The how-to
│   └── README.md                    Docker, K8s, serverless, optimization, CI/CD,
│                                    monitoring, security, cost, load testing
│
├── 03_deployment_implementation_with_azure/   ← Azure deep-dive
│   └── README.md                    Azure OpenAI, Container Apps, AKS, ML Endpoints,
│                                    Managed Identity, Private Link, App Insights
│
│   └── 04_deployment_with_aws_mlops/          ← AWS deep-dive
│       └── README.md                Bedrock, SageMaker endpoints, Lambda, MLOps pipelines
│
├── 05_production_operations/        ← Conceptual glue (diagram-driven)
│   └── README.md                    Request lifecycle, scaling, releases,
│                                    observability & cost — visualized
│
└── interview.md                     ← Interview prep Q&A
```

---

## Learning Path

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1 — 01_deployment_overview                                │
│  "What are my options and how do I choose?"                     │
│  Read the decision framework + run the hands-on Docker example  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  Step 2 — 02_deployment_techniques                              │
│  "How do I actually build this?"                                │
│  Follow the Docker → K8s → CI/CD → monitoring progression      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  Step 2.5 — 05_production_operations                            │
│  "How does this behave under real traffic?"                     │
│  Visual mental models: request flow, scaling, releases, cost    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
┌─────────────▼───────────────┐  ┌─────────────▼───────────────┐
│  Step 3a — Azure            │  │  Step 3b — AWS              │
│  03_deployment_impl_azure   │  │  04_deployment_aws_mlops    │
│  Azure OpenAI, ACA, AKS,    │  │  Bedrock, SageMaker,        │
│  Managed Identity           │  │  Lambda, MLOps pipelines    │
└─────────────────────────────┘  └─────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────┐
│  Step 4 — interview.md                                          │
│  Review all key concepts with Q&A practice                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference — Deployment Option Cheatsheet

| Situation | Recommended Option |
|---|---|
| Prototyping / early product | Cloud API (OpenAI, Anthropic, Azure OpenAI) |
| Variable / unpredictable traffic | Serverless (Modal, Cloud Run, Lambda) |
| High traffic, cost at scale | Self-hosted vLLM on GPU cluster |
| Strict EU data residency | Azure OpenAI + Private Endpoints |
| Custom fine-tuned model | Azure ML / SageMaker Managed Endpoint |
| Offline / privacy-critical app | Edge (llama.cpp + GGUF) |
| Need both cost and compliance | Hybrid routing (local + cloud) |

---

## Prerequisites

Before starting this module, make sure you are comfortable with:

- **Python** — async functions, FastAPI basics, environment variables
- **Docker** — building images, writing Dockerfiles, `docker compose up`
- **REST APIs** — HTTP methods, status codes, JSON request/response
- **LLM basics** — tokens, prompts, temperature (covered in Module 01)

Cloud accounts (at least one):
- [Azure free account](https://azure.microsoft.com/free/) — $200 credit for 30 days
- [AWS free tier](https://aws.amazon.com/free/) — includes SageMaker Studio Lab

---

## Estimated Time

| Section | Time |
|---|---|
| 01 Deployment Overview | 1–2 hours |
| 02 Deployment Techniques | 3–4 hours |
| 02.5 Production Operations | 1.5–2 hours |
| 03 Azure Implementation | 2–3 hours |
| 04 AWS & MLOps | 2–3 hours |
| Interview Prep | 1 hour |
| **Total** | **~12 hours** |

---

*Previous module: [11 Fine-tuning →](../11_fine-tuning/README.md)*
*Next module: [13 LLMops →](../13_LLMops/README.md)*
