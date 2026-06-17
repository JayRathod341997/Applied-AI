# Architecture Design — Concepts

Designing a GenAI system is mostly about *separating concerns* so that each part can scale, fail, and evolve independently. This file walks through the five core patterns you will use again and again: choosing a deployment topology, layering the system, gating the edge, decoupling with queues, and serving the model itself.

---

## 1. Monolith vs Microservices for AI

The first architectural decision is *how many deployable units* your system has. There is no universally correct answer — it depends on team size, scale, iteration speed, and operational maturity.

| Dimension | Monolith | Microservices |
|---|---|---|
| **Deployment** | Single artifact | Many independent services |
| **Scaling** | Scale everything together | Scale each component separately |
| **Latency** | In-process calls (sub-ms) | Network hops (1–10 ms each) |
| **Complexity** | Low initially | High (mesh, discovery, tracing) |
| **Fault isolation** | One crash = total outage | Blast radius contained |
| **ML lifecycle** | Model & app tightly coupled | Independent model versioning |
| **Best for** | Small teams, prototypes, <5 models | Large teams, 10+ models, regulated |

### The Modular Monolith — where most AI teams should start

A *modular monolith* is a single deployable unit that is internally organized into well-defined modules. You get the operational simplicity of one artifact while keeping clean seams you can later split into services.

```
┌─────────────────────────────────────────────────┐
│              Modular Monolith                    │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Inference │ │  Cache   │  │  Auth &  │        │
│  │  Module   │◄┤  Module  │  │  Routing │        │
│  └────┬─────┘  └──────────┘  └──────────┘        │
│       │                                          │
│  ┌────▼─────┐  ┌──────────┐  ┌──────────┐        │
│  │ Pre/Post │  │ Observ-  │  │  Config  │        │
│  │ Process  │  │ ability  │  │  Module  │        │
│  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────┘
```

**Migrate to microservices when:**

- Components have wildly different scaling needs (GPU inference vs CPU metadata).
- Teams need independent deployment cycles.
- Regulation demands isolation (PHI processing separate from general logic).
- The same model must sit behind multiple APIs with different SLAs.

---

## 2. The Layered Reference Architecture

Almost every production GenAI system can be drawn as five horizontal layers. Each layer has a single responsibility and only talks to its neighbours. This is the mental model to fall back on when a design feels tangled.

```
┌──────────────────────────────────────────────────────┐
│  PRESENTATION   Web app · mobile · chat widget · SDK  │
├──────────────────────────────────────────────────────┤
│  ORCHESTRATION  Gateway · routing · agents · prompts  │
│                 guardrails · session & memory         │
├──────────────────────────────────────────────────────┤
│  INFERENCE      LLM serving (vLLM/TGI) · embeddings   │
│                 rerankers · model registry            │
├──────────────────────────────────────────────────────┤
│  KNOWLEDGE      Vector DB · retrieval · chunking       │
│                 caches · feature store                │
├──────────────────────────────────────────────────────┤
│  DATA           Object store · OLTP/OLAP · streams    │
│                 ingestion pipelines · governance      │
└──────────────────────────────────────────────────────┘
```

| Layer | Responsibility | Typical tech | Scales on |
|---|---|---|---|
| **Presentation** | User interaction, streaming UI | React, FastAPI, WebSocket | Request rate |
| **Orchestration** | Routing, agent logic, guardrails | LangGraph, gateway, Redis | Concurrency |
| **Inference** | Run models, generate tokens | vLLM, TGI, embedding servers | GPU memory |
| **Knowledge** | Store & retrieve context | Qdrant, pgvector, Elastic | Index size |
| **Data** | Source of truth, ingestion | S3, Postgres, Kafka | Volume |

The key benefit: a change in the inference layer (swapping Llama-3 for a fine-tune) does not ripple up to presentation, because the orchestration layer hides it behind a stable interface.

---

## 3. API Gateway Patterns

The API gateway is the single front door for all client traffic. For AI systems it does far more than reverse-proxy — it authenticates, meters tokens, routes by task, and (crucially) abstracts away which model *provider* actually serves the request.

```
                    ┌──────────────┐
   Clients ────────►│  API Gateway │
                    │              │
                    │  • Auth      │
                    │  • Rate limit│
                    │  • Route     │
                    │  • Provider  │
                    │    abstract  │
                    └──┬───┬───┬───┘
                       │   │   │
              ┌────────┘   │   └────────┐
              ▼            ▼            ▼
         ┌─────────┐ ┌─────────┐ ┌─────────┐
         │ Model A │ │ Model B │ │ Model C │
         │ (OpenAI)│ │(Claude) │ │ (Llama) │
         └─────────┘ └─────────┘ └─────────┘
```

### Core gateway functions for AI

| Function | What it does | Example |
|---|---|---|
| **Auth** | Verify caller identity & scope | API key → org & quota |
| **Rate limiting** | Protect backends from spikes | 100 req/min per key |
| **Model routing** | Pick a model by task/complexity | simple → small model, hard → large |
| **Provider abstraction** | Hide vendor specifics behind one schema | one `/chat` for OpenAI + Claude + Llama |
| **Fallback** | Retry on a different provider on failure | primary 5xx → secondary |
| **Token metering** | Track & cap spend per tenant | 1M tokens/day per org |

### Provider abstraction — the heart of a portable AI system

A provider abstraction layer means your application code calls *one* interface, and a swap of vendor is a config change, not a rewrite. This is exactly what you will build in the exercise.

```python
class LLMProvider:
    """Common interface every provider implements."""
    name: str
    def complete(self, prompt: str) -> str: ...

class Gateway:
    def __init__(self, providers: list[LLMProvider]):
        self.providers = providers  # ordered: primary, secondary, ...

    def complete(self, prompt: str) -> str:
        last_err = None
        for p in self.providers:        # fallback chain
            try:
                return p.complete(prompt)
            except Exception as e:
                last_err = e              # try the next provider
        raise RuntimeError(f"all providers failed: {last_err}")
```

Popular off-the-shelf gateways: **Kong** and **AWS API Gateway** (general purpose), **Envoy** (service mesh / gRPC), and AI-native ones like **LiteLLM** and **Portkey** that add multi-LLM routing, caching, and fallbacks out of the box.

---

## 4. Async Processing: Message Queues & Event-Driven Ingestion

Synchronous request/response breaks down for compute-heavy AI work (long generations, batch embedding, document parsing). Async processing *decouples* the request from the result so the client is never blocked.

| Pattern | Latency tolerance | Throughput | Complexity | Use case |
|---|---|---|---|---|
| **Sync** | < 5 s | Low | Low | Chat, real-time Q&A |
| **Queue-based** | seconds–hours | High | Medium | Batch inference, doc processing |
| **Event-driven** | variable | Very high | High | Multi-step / agentic pipelines |

### Queue-based architecture

The API server accepts the job, returns a `job_id` immediately, and a worker pool consumes the queue. The client polls or receives a callback.

```
┌──────────┐    ┌───────────────┐    ┌──────────────┐    ┌──────────┐
│  Client  │───►│  API Server   │───►│ Message Queue│───►│  Worker  │
│          │    │ (returns      │    │  • SQS       │    │  Pool    │
│          │◄───│  job_id)      │    │  • RabbitMQ  │    │  • GPU   │
│          │    └───────────────┘    │  • Redis     │    │  • CPU   │
│          │    ┌───────────────┐    │  • Kafka     │    │          │
│          │◄───│ Poll/Callback │◄───│              │    │          │
└──────────┘    └───────────────┘    └──────────────┘    └──────────┘
```

```python
# Worker side (Celery) — retries and rate-limits are first-class
from celery import Celery

app = Celery("ai_tasks", broker="redis://localhost:6379/0")

@app.task(bind=True, max_retries=3, rate_limit="10/m")
def generate_report(self, prompt: str):
    try:
        return run_inference(prompt)        # heavy, long-running
    except Exception as exc:
        self.retry(exc=exc, countdown=60)   # automatic backoff
```

### Event-driven ingestion

For document ingestion, an upload emits an *event* (e.g. "object created" on S3) that triggers a chain: parse → chunk → embed → index. Each stage is a consumer, so stages scale independently and a slow embedder cannot stall the uploader.

```
S3 upload ──► event ──► [parse] ──► [chunk] ──► [embed] ──► [index]
                          (each stage is its own consumer group)
```

---

## 5. Model-Serving Architectures

The serving layer is where trained weights meet production traffic. Framework and GPU-topology choices directly drive latency, throughput, and cost.

| Framework | Throughput | Latency | Quantization | Continuous batching | Best for |
|---|---|---|---|---|---|
| **vLLM** | Very high | Low | AWQ, GPTQ, FP8 | Yes (PagedAttention) | Production LLM serving |
| **TGI** (HuggingFace) | High | Medium | GPTQ, AWQ, EETQ | Yes | HF ecosystem |
| **TensorRT-LLM** | Highest | Lowest | INT8, INT4, FP8 | Yes | Max perf on NVIDIA |
| **Ollama** | Medium | Medium | GGUF (Q4–Q8) | No | Local dev, single user |

### vLLM and PagedAttention

vLLM's key trick is **PagedAttention**: it stores the KV cache in non-contiguous "pages" (like virtual memory), eliminating fragmentation. That lets it pack far more concurrent sequences into the same GPU memory and do **continuous batching** — adding/removing requests every step instead of waiting for a whole batch to finish.

```
┌──────────────────────────────────────────────────┐
│                   vLLM Server                     │
│  ┌────────────┐   ┌──────────────────────────┐    │
│  │   API      │──►│   Scheduler              │    │
│  │  (FastAPI) │   │  • Continuous batching   │    │
│  └────────────┘   │  • Preemption / priority │    │
│                   └───────────┬──────────────┘    │
│  ┌────────────────────────────▼──────────────┐    │
│  │          PagedAttention Engine            │    │
│  │  • KV cache in non-contiguous pages       │    │
│  │  • Near-zero memory waste → bigger batches│    │
│  └───────────────────────────────────────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  GPU 0   │  │  GPU 1   │  │  GPU N   │  ◄ tensor│
│  │ KV pages │  │ KV pages │  │ KV pages │  parallel│
│  └──────────┘  └──────────┘  └──────────┘          │
└──────────────────────────────────────────────────┘
```

### Single-GPU vs multi-GPU tensor parallelism

A model that fits in one GPU's memory should run on one GPU — network and synchronization overhead make multi-GPU *slower* for small models. When the weights don't fit (e.g. a 70B model needs ~140 GB in FP16), **tensor parallelism** splits each layer's matrices across GPUs; every GPU holds a slice and they all-reduce results each step.

| | Single GPU | Multi-GPU (tensor parallel) |
|---|---|---|
| **Model fits?** | Weights < GPU memory | Weights > one GPU |
| **`--tensor-parallel-size`** | 1 | 2, 4, 8 (power of 2, ≤ #GPUs) |
| **Inter-GPU comm** | None | All-reduce every layer (NVLink ideal) |
| **Best for** | 7B–13B models | 34B, 70B+ models |

```bash
# Single GPU — small model fits in memory
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3-8B-Instruct \
    --tensor-parallel-size 1 --port 8000

# Multi-GPU — 70B sharded across 4 GPUs
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3-70B-Instruct \
    --tensor-parallel-size 4 --quantization awq --port 8000
```

TGI offers the same idea via `--num-shard`:

```bash
docker run --gpus all -p 8000:80 \
    ghcr.io/huggingface/text-generation-inference:latest \
    --model-id meta-llama/Llama-3-70B-Instruct \
    --quantize awq --num-shard 4
```

---

## Key Takeaways

- **Start with a modular monolith.** Split into microservices only when scaling needs, team size, or regulation force it.
- **Think in five layers** — presentation, orchestration, inference, knowledge, data — and keep each layer talking only to its neighbours.
- **The API gateway is your control plane:** auth, rate limiting, routing, and (most importantly) provider abstraction with a fallback chain make the system portable and resilient.
- **Decouple heavy work with queues.** Sync for chat, queue-based for batch jobs, event-driven for multi-step ingestion and agents.
- **Match serving topology to model size.** Single GPU when the model fits; tensor parallelism (`--tensor-parallel-size`) only when it doesn't. Prefer vLLM/TGI for continuous batching and high throughput.
