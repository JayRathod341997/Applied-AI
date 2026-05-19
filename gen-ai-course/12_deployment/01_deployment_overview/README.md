# Module 12.1 — Deployment Overview

A complete guide to deploying Generative AI systems in production: from your first API call to enterprise-grade, multi-region infrastructure.

---

## Table of Contents

1. [What Does "Deploying a GenAI Model" Mean?](#what-does-deploying-a-genai-model-mean)
2. [The Deployment Spectrum](#the-deployment-spectrum)
3. [Deployment Options Deep Dive](#deployment-options-deep-dive)
4. [Decision Framework](#decision-framework)
5. [Deployment Patterns](#deployment-patterns)
6. [Latency, Cost & Scalability Trade-offs](#latency-cost--scalability-trade-offs)
7. [Real-World Scenario Walkthroughs](#real-world-scenario-walkthroughs)
8. [Architecture Diagrams](#architecture-diagrams)
9. [Hands-On: Your First Production Deployment](#hands-on-your-first-production-deployment)

---

## What Does "Deploying a GenAI Model" Mean?

Deployment is the act of making a trained or fine-tuned model available for real users or systems to call in real time (or batch). For GenAI this is more complex than classical ML because:

- Models are **enormous** (1 B – 700 B parameters).
- Inference is **stateful** for multi-turn conversations.
- Outputs are **probabilistic** — you need quality gates.
- Latency expectations are **sub-second** for interactive UX.
- Regulatory requirements around **data privacy** differ by region.

```
Developer laptop
      │
      │  "I trained / chose a model, now what?"
      ▼
┌─────────────────────────────────────────────────────┐
│                  DEPLOYMENT PIPELINE                │
│                                                     │
│  Model  →  Optimize  →  Package  →  Serve  →  Monitor │
│  (weights)  (quant/    (Docker/    (API/     (metrics/  │
│             distil)    ONNX)       gRPC)      alerts)   │
└─────────────────────────────────────────────────────┘
      │
      ▼
  End Users / Downstream Services
```

---

## The Deployment Spectrum

Think of deployment as a dial between **control** and **convenience**:

```
◄─────────────────────────────────────────────────────────────►
 Full Control                                    Full Convenience

 Self-hosted        Managed Cloud      Third-party      Cloud API
 on bare metal      (SageMaker,        (Replicate,      (OpenAI,
 or own GPU         Azure ML,          Modal,           Anthropic,
 cluster            Vertex AI)         RunPod)          Gemini)

 ▲                                                         ▲
 Lower cost at scale                          Fastest time-to-market
 Full data sovereignty                        Zero infra ops
 Total customization                          Per-token pricing
```

---

## Deployment Options Deep Dive

### 1. Cloud APIs (Managed Third-Party Inference)

**What it is:** You call an HTTPS endpoint. The provider hosts the model entirely.

**Providers:** OpenAI, Anthropic, Google Gemini, Cohere, Mistral AI, Azure OpenAI Service

**Architecture:**
```
Your App ──HTTPS──► Provider API Gateway ──► Model Cluster ──► Response
              (API Key auth)           (load balanced)
```

**When to use:**
- Prototyping or early product stages
- Traffic is unpredictable or low-volume
- You need state-of-the-art models without training
- No strict data residency requirements

**Cost model:** Per-token (input + output). Example: GPT-4o at ~$5/1M input tokens.

**Pros:**
- Zero infrastructure overhead
- Automatic model updates
- High availability SLAs (99.9%+)

**Cons:**
- Data leaves your environment
- Vendor lock-in risk
- Cost grows linearly with usage (no economies of scale)
- Rate limits can block scaling spikes

**Code example — minimal production-ready client:**
```python
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def call_llm(prompt: str, system: str = "") -> str:
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


# Usage
response = call_llm(
    prompt="Summarize the quarterly earnings report.",
    system="You are a financial analyst. Be concise.",
)
```

---

### 2. Self-Hosted on Own Infrastructure

**What it is:** You run model weights on servers you own or lease (bare metal, colocation, or cloud VMs with dedicated GPUs).

**Common stacks:**
- `vLLM` (PagedAttention, continuous batching) — production standard
- `Ollama` — developer-friendly local inference
- `llama.cpp` — CPU/Apple Silicon inference
- `TensorRT-LLM` — NVIDIA-optimized high-throughput

**Architecture:**
```
                  ┌──────────────────────────────────┐
Load Balancer     │         Inference Cluster         │
     │            │  ┌──────────┐  ┌──────────┐      │
     ├────────────►  │ Worker 0 │  │ Worker 1 │  ... │
     │            │  │ (A100)   │  │ (A100)   │      │
     │            │  └──────────┘  └──────────┘      │
     │            └──────────────────────────────────┘
     │
Model Registry (S3/GCS/Azure Blob)
     └──► Workers pull weights on startup
```

**When to use:**
- High traffic volume where per-token costs exceed infra costs
- Strict data sovereignty / air-gapped environments
- Need fine-tuned private model weights
- Ultra-low latency requirements (co-location with app servers)

**vLLM production server setup:**
```bash
# Install
pip install vllm

# Launch OpenAI-compatible server
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --tensor-parallel-size 2 \           # split across 2 GPUs
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --served-model-name llama3-8b \
  --port 8000
```

```python
# Client code — identical to OpenAI SDK
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="not-needed")

response = client.chat.completions.create(
    model="llama3-8b",
    messages=[{"role": "user", "content": "Explain transformer attention."}],
    temperature=0.7,
    stream=True,
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

### 3. Managed Cloud ML Platforms

**What it is:** Cloud providers host your model weights and handle scaling, monitoring, and serving infrastructure. You bring the model; they run the cluster.

**Platforms:**
| Platform | Provider | Key Strength |
|---|---|---|
| SageMaker Endpoints | AWS | Deep AWS integration, JumpStart models |
| Azure ML Endpoints | Azure | Azure OpenAI + custom models |
| Vertex AI Endpoints | GCP | Tight BigQuery/data integration |
| Hugging Face Inference Endpoints | HF | One-click OSS model deployment |

**Architecture (SageMaker example):**
```
Developer
   │
   │  sagemaker.deploy(model, instance_type="ml.g5.2xlarge")
   ▼
SageMaker Control Plane
   │
   ├── Creates Endpoint Config
   ├── Provisions EC2 GPU instances
   ├── Pulls model from S3
   └── Starts inference container
           │
           ▼
   SageMaker Endpoint (HTTPS)
   ┌──────────────────────────┐
   │  Instance 0 (ml.g5.2xl) │  ◄── Auto Scaling Group
   │  Instance 1 (ml.g5.2xl) │
   └──────────────────────────┘
```

**Code example — deploy custom model to SageMaker:**
```python
import sagemaker
from sagemaker.huggingface import HuggingFaceModel

role = sagemaker.get_execution_role()

hub = {
    "HF_MODEL_ID": "mistralai/Mistral-7B-Instruct-v0.2",
    "HF_TASK": "text-generation",
    "SM_NUM_GPUS": "1",
}

model = HuggingFaceModel(
    env=hub,
    role=role,
    transformers_version="4.37",
    pytorch_version="2.1",
    py_version="py310",
)

predictor = model.deploy(
    initial_instance_count=1,
    instance_type="ml.g5.2xlarge",
    endpoint_name="mistral-7b-prod",
)

# Invoke
output = predictor.predict({
    "inputs": "What is the capital of France?",
    "parameters": {"max_new_tokens": 100, "temperature": 0.1},
})
print(output[0]["generated_text"])
```

---

### 4. Serverless Inference

**What it is:** Functions-as-a-Service (FaaS) that spin up on demand and shut down when idle. You pay only for invocation time.

**Options for GenAI:**
- AWS Lambda + SageMaker Serverless Inference
- Azure Functions + Azure Container Apps (scale-to-zero)
- Google Cloud Run
- Modal (GPU serverless, purpose-built for ML)
- Replicate (hosted OSS models, pay-per-second GPU)

**Architecture:**
```
Request ──► API Gateway
                │
                │  Cold start: ~2-30s (model load)
                │  Warm: <100ms overhead
                ▼
         Serverless Function
         ┌──────────────────┐
         │  Load model      │ ◄── Model cached in /tmp or
         │  Run inference   │     pre-loaded container
         │  Return response │
         └──────────────────┘
                │
                ▼
           Scale to zero when idle
```

**Modal example — GPU serverless endpoint:**
```python
import modal

app = modal.App("genai-inference")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("transformers", "torch", "accelerate")
)

@app.cls(
    image=image,
    gpu="A10G",              # request GPU only when needed
    container_idle_timeout=300,  # keep warm 5 min after last request
)
class Inference:
    @modal.enter()
    def load_model(self):
        from transformers import pipeline
        self.pipe = pipeline(
            "text-generation",
            model="mistralai/Mistral-7B-Instruct-v0.2",
            device_map="auto",
        )

    @modal.method()
    def generate(self, prompt: str) -> str:
        result = self.pipe(prompt, max_new_tokens=200, temperature=0.7)
        return result[0]["generated_text"]


@app.local_entrypoint()
def main():
    model = Inference()
    print(model.generate.remote("Explain quantum entanglement simply."))
```

**When to use serverless:**
- Highly variable or unpredictable traffic
- Development / internal tools with low usage
- Cost-sensitive workloads where idle time dominates

**Limitations to plan for:**
- Cold start latency (10–60s for large models)
- Memory limits (Lambda max: 10 GB RAM, no GPU natively)
- Execution time limits (Lambda: 15 min max)

---

### 5. Edge Deployment

**What it is:** Running quantized, distilled model weights directly on end-user devices (mobile, browser, IoT).

**Runtimes:**
- `llama.cpp` — CPU/Metal inference for GGUF quantized models
- `MLC LLM` — WebGPU / iOS / Android deployment
- `ONNX Runtime` — cross-platform, browser-compatible
- `TensorFlow Lite` / `CoreML` — mobile-optimized

**Architecture:**
```
Cloud (optional for initial download)
        │
        │  One-time model download (GGUF, 4-bit ≈ 4 GB)
        ▼
   User Device
  ┌──────────────────────────────────┐
  │  App                            │
  │   └── llama.cpp / MLC runtime   │
  │         └── Model Weights (local)│
  │               └── Inference      │
  └──────────────────────────────────┘
        │
        No network call needed for inference
```

**Python: local inference with llama.cpp Python bindings:**
```python
from llama_cpp import Llama

# Load 4-bit quantized Mistral 7B (~4 GB)
llm = Llama(
    model_path="./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
    n_ctx=4096,        # context window
    n_gpu_layers=35,   # offload layers to GPU if available
    verbose=False,
)

response = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is machine learning?"},
    ],
    max_tokens=256,
    temperature=0.7,
)

print(response["choices"][0]["message"]["content"])
```

**When to use edge:**
- Offline-first applications
- Privacy-critical use cases (medical, legal notes)
- Low latency with no network dependency
- Devices without reliable internet

---

### 6. Hybrid Deployment

**What it is:** Combine cloud and on-premise/edge in a unified serving architecture with intelligent routing.

**Common patterns:**

**Pattern A — Tier by query complexity:**
```
User Request
     │
     ▼
Query Router (classifier or rule-based)
     │
     ├──── Simple query ──────► Small model (on-prem / edge)
     │                          - Llama 3 8B on own GPU
     │                          - Fast, cheap
     │
     └──── Complex query ─────► Large model (cloud API)
                                - GPT-4o / Claude Sonnet
                                - Accurate, slower
```

**Pattern B — Privacy-sensitive routing:**
```
Request
   │
   ├── Contains PII? ──Yes──► On-premise model (data stays)
   │
   └── No PII? ────────────► Cloud API (better quality)
```

**Pattern C — Active-passive failover:**
```
Primary: Cloud API
   │
   └── Fallback: Self-hosted model (if cloud is down/rate-limited)
```

**Router implementation:**
```python
from enum import Enum

class RouteTarget(Enum):
    LOCAL = "local"
    CLOUD = "cloud"

def route_request(prompt: str, pii_detected: bool, token_count: int) -> RouteTarget:
    if pii_detected:
        return RouteTarget.LOCAL
    if token_count > 4000:       # long context: use capable cloud model
        return RouteTarget.CLOUD
    if token_count < 500:        # short simple query: use local
        return RouteTarget.LOCAL
    return RouteTarget.CLOUD     # default


def hybrid_generate(prompt: str) -> str:
    pii = detect_pii(prompt)
    tokens = count_tokens(prompt)
    target = route_request(prompt, pii, tokens)

    if target == RouteTarget.LOCAL:
        return local_model.generate(prompt)
    else:
        return cloud_api.generate(prompt)
```

---

## Decision Framework

Use this flowchart to pick your deployment option:

```
Start: What are your primary constraints?
│
├──► Data must stay on-premise?
│         └── YES ──► Self-hosted or Edge
│
├──► Need <500ms P95 latency?
│         └── YES ──► Self-hosted (vLLM) or Cloud Managed Endpoint
│
├──► Traffic very spiky / unpredictable?
│         └── YES ──► Serverless (Modal, Cloud Run) or Cloud API
│
├──► Small team, no MLOps resources?
│         └── YES ──► Cloud API (OpenAI/Anthropic) or Managed Platform
│
├──► Cost at scale is the #1 concern?
│         └── YES ──► Self-hosted on owned GPU hardware
│
└──► Need custom fine-tuned model?
          └── YES ──► Managed Platform (SageMaker/Vertex) or Self-hosted
```

### Quick Reference Table

| Dimension | Cloud API | Managed Platform | Self-hosted | Serverless | Edge |
|---|---|---|---|---|---|
| Setup time | Minutes | Hours | Days | Hours | Days |
| Data privacy | Low | Medium | High | Medium | Very High |
| Cost at low traffic | Low | Medium | High | Very Low | Zero (runtime) |
| Cost at high traffic | Very High | Medium | Low | Medium | Zero (runtime) |
| Latency | 200–2000ms | 100–500ms | 50–300ms | 500ms–60s | 50–500ms |
| Model flexibility | Low | High | Full | Medium | Limited |
| Ops burden | None | Low | High | Low | Medium |
| Max model size | Unlimited | Unlimited | GPU VRAM limited | ~13B | ~7B (4-bit) |

---

## Deployment Patterns

### 1. API-First Pattern

The most common pattern: expose model inference as a REST or gRPC API.

```
Client ──HTTP──► FastAPI/Flask App
                      │
                      ├── Auth middleware
                      ├── Rate limiting
                      ├── Request validation
                      ▼
                 Model inference
                      │
                      ▼
                 Response + metadata
```

**FastAPI production-ready inference server:**
```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import anthropic
import time

app = FastAPI(title="GenAI API", version="1.0")
security = HTTPBearer()
client = anthropic.Anthropic()


class GenerateRequest(BaseModel):
    prompt: str
    system: str = ""
    max_tokens: int = 1024
    temperature: float = 0.7


class GenerateResponse(BaseModel):
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "your-api-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


@app.post("/v1/generate", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    _: str = Depends(verify_token),
):
    start = time.time()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=request.max_tokens,
        system=request.system,
        messages=[{"role": "user", "content": request.prompt}],
    )
    latency = (time.time() - start) * 1000

    return GenerateResponse(
        text=message.content[0].text,
        model=message.model,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
        latency_ms=round(latency, 2),
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

### 2. Streaming Pattern

Stream tokens to the client as they are generated — critical for interactive UX.

```
Client ◄──Server-Sent Events (SSE)──── Streaming Inference
  │                                          │
  │  data: {"token": "The"}                 │
  │  data: {"token": " answer"}             │
  │  data: {"token": " is"}                 │
  │  data: [DONE]                           │
```

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import anthropic
import json

app = FastAPI()
client = anthropic.Anthropic()


@app.post("/v1/stream")
async def stream_generate(prompt: str):
    def event_stream():
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'token': text})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

---

### 3. Batch Processing Pattern

For high-throughput offline workloads: process thousands of documents overnight.

```
Input Queue (SQS/Kafka)
      │
      ├── Batch Worker 0 ──► Model Inference ──► Output Store (S3/DB)
      ├── Batch Worker 1 ──► Model Inference ──►
      └── Batch Worker N ──► Model Inference ──►
```

```python
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator

client = anthropic.Anthropic()


def process_single(item: dict) -> dict:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",   # fast + cheap for batch
        max_tokens=512,
        messages=[{"role": "user", "content": item["prompt"]}],
    )
    return {"id": item["id"], "result": response.content[0].text}


def batch_process(items: list[dict], max_workers: int = 10) -> Iterator[dict]:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single, item): item for item in items}
        for future in as_completed(futures):
            yield future.result()


# Usage
documents = [
    {"id": "doc_001", "prompt": "Summarize: ...long text..."},
    {"id": "doc_002", "prompt": "Extract entities from: ..."},
    # ... thousands more
]

results = list(batch_process(documents, max_workers=20))
```

---

### 4. Agentic / Async Pattern

For autonomous workflows where the model takes multiple steps over time.

```
User Request ──► Task Queue ──► Agent Worker
                                    │
                              ┌─────▼──────┐
                              │   LLM      │◄──── Tool Calls
                              │  Reasoning │         │
                              └─────┬──────┘    (web search,
                                    │            code exec,
                              Next step?         DB lookup)
                                    │
                              ┌─────▼──────┐
                              │  Done?     │──YES──► Return result
                              └─────┬──────┘         to user
                                    │
                                   NO ──► Loop back
```

---

## Latency, Cost & Scalability Trade-offs

### Latency breakdown for a typical API call

```
User          DNS       API GW     Auth      LLM        Response
  │─────────────────────────────────────────────────────────►│
  │           │5ms       │10ms      │15ms      │500-2000ms │ │
  │           └──────────┴──────────┴──────────┴───────────┘ │
  │◄──────────────────────────────────────────────────────────│
  Total: ~550–2050ms for cloud API
```

**Optimization levers:**
1. **Reduce input tokens** — shorter, focused prompts
2. **Reduce output tokens** — constrain `max_tokens`
3. **Choose smaller model** — Haiku vs Sonnet vs Opus
4. **Enable streaming** — time-to-first-token feels faster
5. **Caching** — semantic cache or exact-match cache for repeated prompts
6. **Regional deployment** — deploy closer to users

### Cost estimation model

```
Monthly Cost = Daily_Requests × Avg_Input_Tokens × Input_Price_per_1M
             + Daily_Requests × Avg_Output_Tokens × Output_Price_per_1M
             + Infrastructure_Cost

Example (Claude Sonnet, 10K req/day, 500 input + 200 output tokens avg):
  Input:  10,000 × 30 × 500 / 1,000,000 × $3.00  = $45/month
  Output: 10,000 × 30 × 200 / 1,000,000 × $15.00 = $90/month
  Total:  ~$135/month
```

---

## Real-World Scenario Walkthroughs

### Scenario 1: Customer Support Chatbot (SaaS Company)

**Requirements:**
- 5,000 concurrent users at peak
- <3s response time
- PII in conversations (customer data)
- 24/7 availability

**Solution: Cloud API + PII Scrubbing Layer**
```
User ──► PII Scrubber ──► Claude API ──► Response ──► PII Re-injection ──► User
         (replace names,               (anonymized)    (restore names)
          account nums                 processed
          with tokens)
```

**Stack:** FastAPI + Anthropic SDK + Azure Key Vault (secrets) + Redis (session state)

---

### Scenario 2: Legal Document Analysis (Law Firm)

**Requirements:**
- Strict data sovereignty (documents cannot leave EU data center)
- Large context (50-page contracts)
- No GPU expertise in-house

**Solution: Azure ML Managed Endpoint**
```
Law firm's Azure tenant (EU West region)
├── Azure Blob Storage (contract PDFs)
├── Azure ML Endpoint (Mistral-7B fine-tuned on legal docs)
└── Private Link (no public internet exposure)
```

---

### Scenario 3: AI Writing Assistant (Consumer App)

**Requirements:**
- 10M users, mostly idle
- Cost sensitive
- Feature: offline mode

**Solution: Hybrid — Cloud + Edge**
```
User Device
├── Small GGUF model (offline, 4B params, 2.5 GB)
│   └── Used for: grammar correction, short completions
│
└── Cloud API (when online + complex tasks)
    └── Used for: full drafts, research, long-form
```

---

## Architecture Diagrams

### Full Production Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Production GenAI System                       │
│                                                                      │
│  ┌─────────┐     ┌──────────┐     ┌──────────────────────────────┐  │
│  │ Client  │────►│  CDN /   │────►│      API Gateway              │  │
│  │ (Web/   │     │  WAF     │     │  (Rate limiting, Auth, TLS)   │  │
│  │  Mobile)│     └──────────┘     └───────────┬──────────────────┘  │
│  └─────────┘                                  │                      │
│                                               ▼                      │
│                              ┌────────────────────────────┐          │
│                              │     Application Layer       │          │
│                              │  FastAPI / LangServe        │          │
│                              │  ┌──────────┐ ┌──────────┐ │          │
│                              │  │ Prompt   │ │ Output   │ │          │
│                              │  │ Pipeline │ │ Guardrails│ │          │
│                              │  └────┬─────┘ └──────────┘ │          │
│                              └───────┼────────────────────┘          │
│                                      │                               │
│              ┌───────────────────────┼──────────────────────┐        │
│              │                       ▼                       │        │
│              │          ┌────────────────────────┐           │        │
│              │          │    Model Router         │           │        │
│              │          └──┬──────────┬──────────┘           │        │
│              │             │          │                        │        │
│              │    ┌────────▼──┐   ┌───▼─────────┐            │        │
│              │    │ Local LLM │   │  Cloud API  │            │        │
│              │    │ (vLLM)    │   │  (Anthropic)│            │        │
│              │    └───────────┘   └─────────────┘            │        │
│              │                                                │        │
│              │     Observability Stack                        │        │
│              │  ┌──────────┐ ┌──────────┐ ┌──────────┐       │        │
│              │  │ Metrics  │ │  Traces  │ │  Logs    │       │        │
│              │  │(Prometheus│ │ (Jaeger) │ │(Elastic) │       │        │
│              │  └──────────┘ └──────────┘ └──────────┘       │        │
│              └────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Hands-On: Your First Production Deployment

Follow this step-by-step to get a production API live in 30 minutes using cloud API + Docker.

**Step 1: Project structure**
```
genai-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── config.py        # Settings via pydantic-settings
│   └── models.py        # Pydantic request/response models
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

**Step 2: `app/main.py`**
```python
from fastapi import FastAPI
from app.models import GenerateRequest, GenerateResponse
from app.config import settings
import anthropic
import time

app = FastAPI()
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    t0 = time.time()
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=req.max_tokens,
        messages=[{"role": "user", "content": req.prompt}],
    )
    return GenerateResponse(
        text=msg.content[0].text,
        latency_ms=(time.time() - t0) * 1000,
    )
```

**Step 3: `Dockerfile`**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Step 4: `docker-compose.yml`**
```yaml
version: "3.9"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Step 5: Run**
```bash
cp .env.example .env
# Edit .env: ANTHROPIC_API_KEY=sk-ant-...
docker compose up -d
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!", "max_tokens": 100}'
```

---

## Key Takeaways

1. **Match deployment to constraints** — data privacy, latency, cost, and team size all point to different options.
2. **Cloud APIs for speed to market** — move to self-hosted when monthly API costs exceed infrastructure costs.
3. **Self-hosted vLLM is the production standard** for teams running their own GPU clusters.
4. **Streaming is non-negotiable** for interactive user-facing applications.
5. **Hybrid routing** unlocks the best of both worlds: privacy and quality.
6. **Observability from day one** — you cannot optimize what you cannot measure.

---

*Next: [02 Deployment Techniques →](../02_deployment_techniques/README.md)*
