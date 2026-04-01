# Applied AI — From Prompts to Production

## Course Overview

A comprehensive curriculum for developers and engineers who want to build production-grade AI systems using LLMs, agents, RAG, and cloud deployment.

**Prerequisites:** Basic Python, REST APIs, and familiarity with cloud concepts.

---

## Part 1: Foundations

### Module 1 — Generative AI & Prompting
**Folder:** [`gen-ai-course/01_generative_ai/`](gen-ai-course/01_generative_ai/)

- 1.1 What is Generative AI? — LLM capabilities and limitations
- 1.2 Prompt Engineering — Techniques and patterns
- 1.3 Data Analysis with LLM prompts
- 1.4 Ethics, considerations, and the future of AI

### Module 2 — LangChain Framework
**Folder:** [`gen-ai-course/02_langchain/`](gen-ai-course/02_langchain/)

- 2.1 LangChain overview and architecture
- 2.2 Building blocks: chains, prompts, parsers
- 2.3 Chat models and chains
- 2.4 Memory, tools, and agents
- 2.5 Patterns and best practices
- 2.6 Mini-projects: Chatbot, Summarizer, Q&A System, Waiter Bot, Travel Planner

---

## Part 2: Retrieval & Knowledge Systems

### Module 3 — RAG & Vector Databases
**Folder:** [`gen-ai-course/03_rag_vectordb/`](gen-ai-course/03_rag_vectordb/)

- 3.1 What is RAG? — Overview and use cases
- 3.2 Embeddings and chunking strategies
- 3.3 Vector databases — Setup, integration, and migration
- 3.4 Building a RAG pipeline end-to-end
- 3.5 Advanced retrieval techniques (hybrid search, re-ranking)
- 3.6 RAG evaluation and metrics
- 3.7 Production challenges and common fixes

---

## Part 3: Agentic AI

### Module 4 — Agentic Systems
**Folder:** [`gen-ai-course/04_agentic_systems/`](gen-ai-course/04_agentic_systems/)

- 4.1 Introduction to Agentic AI
- 4.2 Agent design patterns — ReAct, Plan-and-Execute, and more
- 4.3 Multi-agent systems and coordination
- 4.4 Agent-to-Agent (A2A) protocol
- 4.5 Building agents with LangGraph

### Module 5 — Model Context Protocol (MCP)
**Folder:** [`gen-ai-course/05_mcp/`](gen-ai-course/05_mcp/)

- 5.1 MCP overview and motivation
- 5.2 Building MCP servers
- 5.3 Building MCP clients
- 5.4 Enterprise MCP integration project

### Module 6 — LangGraph Deep Dive
**Folder:** [`gen-ai-course/06_langgraph/`](gen-ai-course/06_langgraph/)

- 6.1 LangGraph overview and core concepts
- 6.2 Building blocks: nodes, edges, state management
- 6.3 Cyclic vs. DAG graphs — Human-in-the-loop patterns

---

## Part 4: Production Engineering

### Module 7 — Architecture Design
**Folder:** [`gen-ai-course/07_architecture/`](gen-ai-course/07_architecture/)

- 7.1 AI system architecture patterns
- 7.2 Scaling, reliability, and cost trade-offs

### Module 8 — CI/CD for AI
**Folder:** [`gen-ai-course/08_cicd/`](gen-ai-course/08_cicd/)

- 8.1 Versioning AI models and prompts
- 8.2 Automated deployment pipelines for LLM apps

### Module 9 — Monitoring & Observability
**Folder:** [`gen-ai-course/09_monitoring/`](gen-ai-course/09_monitoring/)

- 9.1 Observability fundamentals for LLM systems
- 9.2 Drift detection and model performance tracking
- 9.3 Logging strategies and distributed tracing

### Module 10 — AI Governance & Compliance
**Folder:** [`gen-ai-course/10_governance/`](gen-ai-course/10_governance/)

- 10.1 Risks and guardrails in production AI
- 10.2 Responsible AI principles
- 10.3 Regulatory compliance (GDPR, HIPAA, EU AI Act)

---

## Part 5: Fine-Tuning & Deployment

### Module 11 — Fine-Tuning LLMs
**Folder:** [`gen-ai-course/11_fine-tuning/`](gen-ai-course/11_fine-tuning/)

- 11.1 When and why to fine-tune vs. prompt engineering
- 11.2 Fine-tuning techniques: LoRA, QLoRA, PEFT
- 11.3 Fine-tuning implementation walkthrough

### Module 12 — Deployment Strategies
**Folder:** [`gen-ai-course/12_deployment/`](gen-ai-course/12_deployment/)

- 12.1 Deployment overview: containers, serverless, APIs
- 12.2 Deployment techniques and patterns
- 12.3 Azure-based deployment with Container Apps

### Module 13 — LLMOps
**Folder:** [`gen-ai-course/13_LLMops/`](gen-ai-course/13_LLMops/)

- 13.1 LLMOps overview and the AI lifecycle
- 13.2 Infrastructure setup (Azure and cloud-agnostic)
- 13.3 Deployment strategies at scale
- 13.4 Monitoring and observability in LLMOps
- 13.5 Security and compliance for AI systems
- 13.6 Cost optimization strategies

---

## Part 6: Capstone Projects

### Module 14 — Production AI Projects
**Folder:** [`gen-ai-course/14_ai_projects/`](gen-ai-course/14_ai_projects/)

Each project includes a full architecture walkthrough, Azure infrastructure (Bicep IaC), deployment guide, and interview prep.

| Project | Stack | Highlights |
|---------|-------|------------|
| **Book Recommender** | RAG + Embeddings + Azure AI Search | Semantic search, personalization |
| **Customer Support Engine** | LangGraph + WebSockets + React | Real-time streaming, stateful agents |
| **Market Intelligence Agent** | LangChain + RAG + Blob Storage | Web scraping, summarization pipeline |
| **Multi-Agent Researcher** | CrewAI + LangChain + Cosmos DB | Collaborative agents, persistent memory |

---

## Learning Path Summary

```
Fundamentals → Retrieval → Agentic AI → Production Engineering → Fine-Tuning & Deployment → Capstone
  (M1–M2)       (M3)        (M4–M6)           (M7–M10)               (M11–M13)               (M14)
```

**Total Modules:** 14 | **Capstone Projects:** 4
