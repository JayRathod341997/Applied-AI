# GenAI Project Case Studies

Interview-ready deep dives for the **"walk me through a project you built"** round, covering
all 13 GenAI projects under [`gen-ai-course/14_ai_projects/`](../../gen-ai-course/14_ai_projects/).
Companion to the [Senior AI Engineer Interview Guide](../SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md).

## How to use these in an interview

Each case study follows the same 10-part structure so you can rehearse one flow and reuse it
for any project:

1. Problem statement → 2. Why AI/ML → 3. Dataset / knowledge corpus & eval set →
4. Prompt & context engineering (the GenAI analog of feature engineering) → 5. Model selection →
6. Training / prompt-iteration (mostly "no training, and here's why") → 7. Evaluation metrics →
8. Deployment architecture → 9. Business impact → 10. Lessons learned.

Each file opens with a **30-second pitch** and closes with **likely follow-up questions**.

> **On the numbers:** these are course/portfolio projects, not production systems with measured
> telemetry. Every figure that isn't derivable from the code (corpus size, latency, cost,
> accuracy, business impact) is explicitly tagged **`*Illustrative:*`** — representative values
> you can defend as targets, then swap for real numbers once you've run the system. The
> architecture, models, and integrations described are grounded in the actual source.

> **Senior-level tip:** the strongest answers name a trade-off and a real limitation. Several of
> these write-ups flag where the code diverges from its README (stubbed scrapers, keyword vs
> vector search, unwired conflict resolvers). Owning those gaps — "here's what's shipped, here's
> what I'd harden next behind an eval gate" — reads as senior judgment, not weakness.

## The projects

### RAG / retrieval
| # | Project | Best for showing |
|---|---------|------------------|
| 02 | [Book Recommender](02-book-recommender.md) | Embeddings + hybrid search + a cross-encoder **reranker**; retrieval metrics (hit-rate, MRR, nDCG) |
| 03 | [Customer Support Engine](03-customer-support-engine.md) | **Stateful LangGraph agent** — state machine, conversational memory/checkpointer, tool-use, escalation; grounding/faithfulness |

### Multi-agent
| # | Project | Best for showing |
|---|---------|------------------|
| 04 | [Multi-Agent Researcher](04-multi-agent-researcher.md) | **CrewAI** role decomposition (researcher → critic → writer); "why multi-agent vs one agent" |
| 05 | [Market Intelligence Agent](05-market-intelligence-agent.md) | Orchestrated retrieval → reasoning → **validation** loop as an anti-hallucination design |

### Single-agent automation
| # | Project | Best for showing |
|---|---------|------------------|
| 01 | [AI Inbox Cleaner](01-ai-inbox-cleaner.md) | LLM **classification + routing**, two-tier model choice (fast classify / strong draft), human-in-the-loop |
| 06 | [Smart Notion Sync Agent](06-smart-notion-sync-agent.md) | LLM **conflict resolution** vs deterministic rules; multi-system sync (Notion / Calendar / Slack) |
| 07 | [Schedule Parser & Calendar Sync](07-schedule-parser-calendar-sync.md) | **OCR + LLM structured extraction** (a CV angle); image→events field-level accuracy |
| 08 | [Real Estate CRM Agent](08-real-estate-crm-agent.md) | LLM **lead qualification + scoring** and generated outreach (SMS/email) |
| 09 | [VA Task Supervisor Agent](09-va-task-supervisor-agent.md) | LLM **task assignment/routing** with structured reasoning over Notion + Slack |
| 10 | [EP Job Application Agent](10-ep-job-application-agent.md) | **Two-tier pipeline** (cheap filter + strong tailoring); scrape → filter → generate |
| 12 | [Remote Job Ops Engine](12-remote-job-ops-engine.md) | **Classification + generation** in one pipeline; distinct models per stage |

### Research agent
| # | Project | Best for showing |
|---|---------|------------------|
| 11 | [Grant Funding Research Agent](11-grant-funding-research-agent.md) | Search → retrieve → **match/score** with precision/recall framing for relevance |

### Content generation
| # | Project | Best for showing |
|---|---------|------------------|
| 13 | [Tactical Affiliate Funnel](13-tactical-affiliate-funnel.md) | High-volume **content generation**, conversion tracking, and the responsible-AI/disclosure angle |

## Shared stack themes (good cross-project talking points)

- **Model tiering:** most automation agents run a cheap model (`llama-3.1-8b-instant`) for
  classify/filter and a stronger one (`llama-3.3-70b-versatile`) for generation, both via **Groq**.
  The RAG/multi-agent projects lean on **Azure OpenAI `gpt-4o`** + `text-embedding-ada-002`.
- **Structured output everywhere:** Pydantic schemas + `with_structured_output` / JSON contracts
  are the real "feature engineering" of these systems.
- **Retrieval choices:** Azure AI Search (hybrid vector+keyword) with an optional cross-encoder
  reranker — a clean story about precision vs latency/cost.
- **Orchestration spectrum:** plain LangChain chains → LangGraph state machines → CrewAI
  multi-agent — useful for "when would you reach for each?"
- **Serving:** FastAPI + Uvicorn services, Azure Container Apps / AKS for deployment.
