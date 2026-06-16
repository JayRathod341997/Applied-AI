# JD-Aligned Senior Deep Dives Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add JD-aligned `Senior Deep Dive` sections to seven `course-content/` modules (M2, M4, M5, M6, M7, M11, M14) and update the README + master-guide cross-references, completing senior-level coverage of the Senior AI Engineer (risk-management) job description.

**Architecture:** Pure documentation work. Each module gets one `## Senior Deep Dive: <theme>` section appended to its `interview-questions.md` (4–6 `### SQ#` Q&As) plus a `## Bonus: Senior / JD-Aligned Questions` block appended to its `quiz.md` (4–6 self-contained MCQs). Content mirrors the existing M1/M3/M10/M12 deep dives. Two final edits update `README.md` and `SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md` to link the new sections.

**Tech Stack:** Markdown only. Git for version control. No code, no tests, no build.

**Spec:** `docs/superpowers/specs/2026-06-16-jd-aligned-senior-deep-dives-design.md`

---

## House-Style Rules (apply to EVERY task)

These come from the existing M1/M3/M10/M12 deep dives — match them exactly:

1. **interview-questions.md** addition format:
   ```markdown


   ---

   ## Senior Deep Dive: <Theme>

   > *<one-line italic note on what interviewers probe with this theme>*

   ### SQ1: <question>?

   **Answer:** <prose>. **Bold** the key terms. Use tables / fenced code where they
   materially help. END every answer with an explicit trade-off + business/risk
   consequence (the senior tell).
   ```
2. **quiz.md** addition format (self-contained, answer after each question):
   ```markdown


   ---

   ## Bonus: Senior / JD-Aligned Questions (<Theme>)

   > Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

   ### BQ1. <question>

   A) ...  
   B) ...  
   C) ...  
   D) ...  

   **Answer: <X>** — <one-line justification>.
   ```
   (Note the **two trailing spaces** after each option for the markdown line break, exactly as M3's quiz does.)
3. Append to the **end of the file** in every case — do not insert mid-file.
4. **Risk/regulated lens** throughout (fraud, credit, MRM, audit, EU AI Act).
5. **Claude/Anthropic** treated as a first-class LLM alongside GPT/Gemini/Mistral. If you make any model-specific factual claim (pricing, context window, model ID), verify it via the `claude-api` skill first.
6. Before appending, **skim the module's existing questions** so a new SQ does not duplicate one already there.
7. One commit per task with the message shown in that task's final step.

---

### Task 1: M2 — LangChain → "LlamaIndex vs LangChain & framework exit"

**Files:**
- Modify (append): `course-content/part-1-foundations/module-2-langchain/interview-questions.md` (currently 697 lines)
- Modify (append): `course-content/part-1-foundations/module-2-langchain/quiz.md` (currently 447 lines)

- [ ] **Step 1: Append the deep-dive section to interview-questions.md**

Append this to the end of the file (theme note + 5 SQ&As). Write each answer in the house prose style, bolding the key terms and closing each with a trade-off:

```markdown


---

## Senior Deep Dive: LlamaIndex vs LangChain & When to Drop the Framework

> *The course teaches LangChain, but the JD also lists LlamaIndex. Interviewers want to hear that you choose a framework for the job — and can leave it when it stops paying for itself.*

### SQ1: When would you reach for LlamaIndex instead of LangChain — and when neither?

**Answer:** Cover these points:
- **LlamaIndex** is a *data / retrieval-first* framework: document loaders, node parsers, indices (`VectorStoreIndex`, summary, knowledge-graph), retrievers, response synthesizers, query engines. Best when the core problem is **ingest → index → retrieve** over private data (RAG, document Q&A).
- **LangChain** is a *general orchestration* framework: chains, agents, tools, broad integrations, LCEL. Best when you need **agent/tool orchestration and workflow glue** beyond retrieval.
- **Both together** is common: LlamaIndex retrieval inside a LangChain/LangGraph agent.
- **Trade-off to close on:** a framework buys integrations and standard patterns but costs a dependency, version churn, and leaky abstractions; for a latency-critical hot path the raw provider SDK can be simpler, faster, and easier to audit.

### SQ2: When do you drop the framework and call the model SDK directly?

**Answer:** Cover: latency/cost-critical paths; when abstractions hide the actual prompt and token usage (a problem for cost control and auditability in regulated systems); when debugging through framework layers costs more than it saves; when you need full control of retries/streaming/timeouts. Keep frameworks for prototyping, breadth of integrations, and standard patterns. **Senior framing:** frameworks are accelerators, not architecture — you should be able to re-implement a given chain in ~50 lines of SDK calls, and that knowledge is what lets you decide. Trade-off: development speed vs control/transparency.

### SQ3: What does LangChain's LCEL give you, and what's the cost?

**Answer:** LCEL (LangChain Expression Language) is **declarative pipe composition** (`prompt | model | parser`) that provides streaming, async, batching, retries, **fallbacks**, and parallelism for free across the pipeline. Cost: a learning curve and reduced transparency when debugging — stack traces run through the framework, not your code. Trade-off: less boilerplate vs harder introspection.

### SQ4: Map LlamaIndex's core abstractions onto a RAG pipeline.

**Answer:** Present the chain: **Documents → Nodes** (chunks) **→ Index** (e.g. `VectorStoreIndex`) **→ Retriever → Node postprocessors** (re-ranking, similarity cutoff) **→ Response synthesizer → Query engine**. Note that each stage is swappable, and that this is the same pipeline you'd otherwise hand-build — the framework just names and wires the parts. Trade-off: convention/speed vs hand-rolled control.

### SQ5: How do you manage framework version churn and lock-in in production?

**Answer:** Cover: **pin versions**; **wrap the framework behind your own interface** (ports/adapters) so retrieval/LLM calls can be swapped without touching business logic; evaluate new framework versions against **your own benchmarks** before upgrading; avoid deep coupling to fast-moving APIs. Trade-off: an abstraction layer is upfront cost but buys you the option to migrate or drop the framework later — cheap insurance against a dependency that breaks monthly.
```

- [ ] **Step 2: Append the bonus quiz block to quiz.md**

Append to the end of the file:

```markdown


---

## Bonus: Senior / JD-Aligned Questions (LlamaIndex vs LangChain)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. Your core problem is ingesting, indexing, and retrieving over a large private document set with minimal orchestration glue. Which framework is the most natural fit?

A) LangChain — for its agent abstractions  
B) LlamaIndex — a data/retrieval-first framework  
C) Neither; you must use raw SDK calls  
D) A general web framework like FastAPI  

**Answer: B** — LlamaIndex is built around ingest→index→retrieve; LangChain shines when you also need general agent/tool orchestration.

### BQ2. What is the strongest reason to drop a framework and use the provider SDK directly?

A) Frameworks can never stream responses  
B) A latency/cost-critical hot path where abstraction overhead and opacity hurt control and auditability  
C) The SDK is always fewer lines of code  
D) Frameworks cannot call external tools  

**Answer: B** — on hot paths you often want full control of prompts, tokens, retries, and streaming, and transparent behavior for audit.

### BQ3. What does LangChain's LCEL primarily provide?

A) A vector database  
B) Declarative composition with streaming, async, batching, and fallbacks  
C) A fine-tuning service  
D) A replacement for Python itself  

**Answer: B** — LCEL composes pipeline steps declaratively and adds cross-cutting features for free.

### BQ4. Which ordering correctly describes a LlamaIndex RAG pipeline?

A) Index → Documents → Query engine → Nodes  
B) Documents → Nodes → Index → Retriever → Postprocessor → Response synthesizer  
C) Retriever → Documents → Index → Nodes  
D) Query engine → Index → Documents  

**Answer: B** — documents are parsed into nodes, indexed, retrieved, post-processed (e.g. re-ranked), then synthesized into a response.

### BQ5. What is the best practice for limiting framework lock-in?

A) Never pin versions so you always get the latest  
B) Wrap the framework behind your own interface, pin versions, and evaluate upgrades against your own benchmarks  
C) Fork the framework and maintain it yourself  
D) Avoid frameworks entirely in all cases  

**Answer: B** — an adapter layer plus pinned versions keeps you able to upgrade, swap, or drop the framework on your terms.
```

- [ ] **Step 3: Verify both sections were added and render cleanly**

Run:
```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
grep -n "Senior Deep Dive: LlamaIndex" course-content/part-1-foundations/module-2-langchain/interview-questions.md
grep -n "Bonus: Senior / JD-Aligned Questions (LlamaIndex" course-content/part-1-foundations/module-2-langchain/quiz.md
```
Expected: one line number returned from each (the new headings exist).

- [ ] **Step 4: Commit**

```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
git add course-content/part-1-foundations/module-2-langchain/interview-questions.md course-content/part-1-foundations/module-2-langchain/quiz.md
git commit -m "docs(m2): add Senior Deep Dive on LlamaIndex vs LangChain"
```

---

### Task 2: M4 — Agentic Systems → "Multi-agent systems & autonomous workflows"

**Files:**
- Modify (append): `course-content/part-3-agentic-ai/module-4-agentic-systems/interview-questions.md` (currently 672 lines)
- Modify (append): `course-content/part-3-agentic-ai/module-4-agentic-systems/quiz.md` (currently 192 lines)

- [ ] **Step 1: Append the deep-dive section to interview-questions.md**

Append to the end of the file:

```markdown


---

## Senior Deep Dive: Multi-Agent Systems, Autonomous Workflows & Conversational AI

> *The JD explicitly calls for multi-agent systems, autonomous workflows, and conversational AI. Interviewers probe whether you add autonomy deliberately — and constrain it for a regulated context.*

### SQ1: When is a multi-agent system the right design, and when is one agent enough?

**Answer:** Cover: choose **multi-agent** when the task decomposes into **specialized roles** (researcher/coder/critic), parallelizable subtasks, or needs separation of concerns/permissions. Common patterns: **supervisor / orchestrator-worker**, hierarchical, and network. Choose a **single agent** when coordination overhead outweighs the benefit. **Trade-off:** more agents buy flexibility and specialization but cost latency, token spend, a larger failure surface, and harder debugging/evaluation — in a regulated system that also means more to audit.

### SQ2: How do you keep an autonomous agent reliable and safe in a regulated (risk) context?

**Answer:** **Bounded autonomy** is the theme: tool **allow-lists**, **human-in-the-loop approval** for high-risk/state-changing actions, max-step and budget caps, sandboxing, output schema validation, and a **full audit log** of every tool call and the reasoning behind it. Prefer determinism where the path is known. **Trade-off:** autonomy speeds work but trades away control and auditability — you tier the autonomy by the risk of the action.

### SQ3: Agent vs simple chain — what's your decision criterion?

**Answer:** Use an **agent only when the path is genuinely dynamic and tool-dependent** and cannot be pre-defined. **Chains/graphs** are cheaper, faster, and predictable. Most things called "agents" should be chains. **Trade-off:** flexibility vs cost/latency/predictability — default to the least dynamic design that solves the problem.

### SQ4: How do agents coordinate and share state in a multi-agent system?

**Answer:** Mechanisms: a **supervisor** routing subtasks, **message passing** between agents, a shared **scratchpad/blackboard**, and shared memory. Risks: **context bloat** (every agent dragging the full history) and **conflicting actions**. Mitigate with scoped context per agent, typed hand-offs, and a single writer for shared state. Trade-off: richer coordination vs context cost and race conditions.

### SQ5: What does production conversational AI need beyond the LLM call?

**Answer:** Session/state management, **memory** (short-term window + long-term summarization/retrieval), guardrails, **fallback and escalation to a human**, intent routing, **RAG grounding**, streaming for latency, and analytics. For risk/customer-facing use, add content safety and logging. **Trade-off:** each capability adds latency and cost — you add them where the conversation's risk and value justify it.
```

- [ ] **Step 2: Append the bonus quiz block to quiz.md**

Append to the end of the file:

```markdown


---

## Bonus: Senior / JD-Aligned Questions (Multi-Agent & Autonomous Workflows)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. What is the strongest justification for a multi-agent design over a single agent?

A) It always runs faster  
B) The task decomposes into specialized roles or parallelizable subtasks needing separation of concerns  
C) It uses fewer tokens  
D) It removes the need for evaluation  

**Answer: B** — multi-agent pays off when specialization or parallelism is real; otherwise the coordination overhead is pure cost.

### BQ2. For an autonomous agent that can take consequential actions in a regulated domain, which control matters most?

A) A larger context window  
B) Bounded autonomy: tool allow-lists, human-in-the-loop approval, and a full audit log  
C) A higher temperature  
D) More agents  

**Answer: B** — consequential actions require approval gates, least-privilege tools, and auditability.

### BQ3. When is a deterministic chain preferable to an agent?

A) Never  
B) When the path is known and static — it is cheaper, faster, and predictable  
C) Only when there are no tools  
D) Only for image tasks  

**Answer: B** — if you can pre-define the flow, a chain beats an agent on cost, latency, and predictability.

### BQ4. A coordinator that delegates subtasks to specialist agents is which pattern?

A) Bag-of-words  
B) Supervisor / orchestrator-worker  
C) Map-reduce only  
D) Single-shot prompting  

**Answer: B** — a supervisor routes work to specialized workers and aggregates results.

### BQ5. Which metric set best evaluates an agent?

A) Accuracy alone  
B) Task success rate, tool-call correctness, trajectory/steps, and cost  
C) Token count only  
D) Lines of code  

**Answer: B** — agents need outcome *and* process metrics, including how efficiently they got there.
```

- [ ] **Step 3: Verify both sections render**

Run:
```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
grep -n "Senior Deep Dive: Multi-Agent" course-content/part-3-agentic-ai/module-4-agentic-systems/interview-questions.md
grep -n "Bonus: Senior / JD-Aligned Questions (Multi-Agent" course-content/part-3-agentic-ai/module-4-agentic-systems/quiz.md
```
Expected: one line number from each.

- [ ] **Step 4: Commit**

```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
git add course-content/part-3-agentic-ai/module-4-agentic-systems/interview-questions.md course-content/part-3-agentic-ai/module-4-agentic-systems/quiz.md
git commit -m "docs(m4): add Senior Deep Dive on multi-agent systems & autonomous workflows"
```

---

### Task 3: M5 — MCP → "Tool/data integration, copilots & Claude/Anthropic"

**Files:**
- Modify (append): `course-content/part-3-agentic-ai/module-5-mcp/interview-questions.md` (currently 641 lines)
- Modify (append): `course-content/part-3-agentic-ai/module-5-mcp/quiz.md` (currently 229 lines)

- [ ] **Step 1: Append the deep-dive section to interview-questions.md**

Append to the end of the file:

```markdown


---

## Senior Deep Dive: MCP for Enterprise Tool/Data Integration & AI Copilots

> *The JD emphasizes Claude/Anthropic and AI copilots. MCP is Anthropic's open standard for connecting models to tools and data — interviewers probe whether you can integrate and secure it at enterprise scale.*

### SQ1: What problem does MCP solve, and why does it matter for enterprise copilots?

**Answer:** **MCP (Model Context Protocol)** is an open standard from **Anthropic** that standardizes how an LLM application connects to tools and data sources through **MCP servers** — often described as "USB-C for AI tools." It **decouples** the host/model from integrations: build a server once and reuse it across many clients (Claude Desktop, IDEs, custom hosts), avoiding **N×M** bespoke integrations. **Trade-off:** adopting an emerging standard buys reuse and portability but is less mature than hand-rolled glue — worth it when many AI clients must share the same integrations.

### SQ2: Describe MCP's architecture.

**Answer:** **Host** (the LLM application) connects via one **Client** per server to an **MCP Server** that exposes three primitives: **resources** (read-only data/context), **tools** (callable actions), and **prompts** (reusable templates). Transport is typically **stdio** (local) or **HTTP + SSE** (remote). Note the clean separation: the host never embeds integration code — it speaks MCP. Trade-off: a protocol hop adds indirection but standardizes everything behind it.

### SQ3: How do you secure MCP tool access in a regulated environment?

**Answer:** **Least-privilege, scoped servers**; per-server authentication/credentials; **tool allow-lists**; **human approval** for state-changing tools; **audit every invocation**; network isolation; and — critically — **validate/sanitize tool outputs**, because tool results are a **prompt-injection** vector (a malicious document returned by a tool can hijack the model). **Trade-off:** tighter controls reduce agent flexibility but are mandatory where actions touch money or PII.

### SQ4: MCP vs traditional function/tool calling — what's the difference, and when do you use each?

**Answer:** **Function/tool calling** is in-app and model-specific — you define schemas the model can call within one application. **MCP** standardizes and **decouples** the integration into a separate server reachable over a transport, **reusable across hosts**. Use **MCP** when integrations should be shared/reused across multiple AI clients or teams; use plain tool calling for a single app's bespoke, tightly-coupled tools. Trade-off: reusability/portability vs the simplicity of an in-process call.

### SQ5: Where do Claude and Anthropic fit in this picture?

**Answer:** MCP is **Anthropic's** open standard, and **Claude** is a strong tool-use/agentic model — directly relevant to the JD's Claude emphasis. The payoff: build an MCP server once and it works across Claude and other MCP-capable hosts, so your enterprise integrations aren't locked to a single vendor's tool-calling format. Trade-off: betting on an open standard vs a single-vendor SDK — the standard wins on portability as the ecosystem grows.
```

- [ ] **Step 2: Append the bonus quiz block to quiz.md**

Append to the end of the file:

```markdown


---

## Bonus: Senior / JD-Aligned Questions (MCP for Enterprise Integration)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. What is the primary value of MCP?

A) It fine-tunes models  
B) A standard protocol that decouples LLM hosts from tool/data integrations — build a server once, reuse across clients  
C) It is a vector database  
D) It replaces Python  

**Answer: B** — MCP avoids N×M bespoke integrations by standardizing how hosts talk to tools and data.

### BQ2. Which three primitives does an MCP server expose?

A) Tables, rows, columns  
B) Resources, tools, and prompts  
C) GET, POST, DELETE  
D) Train, validate, test  

**Answer: B** — resources (data/context), tools (actions), and prompts (templates).

### BQ3. What is the biggest security concern when MCP tool results are fed back to the model?

A) Slow networking  
B) Prompt injection via tool output — so sanitize results, use least privilege, and require human approval  
C) Excessive logging  
D) Tool results are always safe  

**Answer: B** — a tool can return attacker-controlled text that hijacks the model; treat tool output as untrusted input.

### BQ4. When should you choose MCP over plain in-app function calling?

A) When you never use tools  
B) When integrations should be reusable and shareable across multiple AI clients or teams  
C) Only for local scripts  
D) Only when using a vector DB  

**Answer: B** — MCP's decoupling pays off when the same integration must serve many hosts.

### BQ5. Who originated MCP, and what is its portability benefit?

A) A database vendor; it locks you in  
B) Anthropic; an open standard so one server works across Claude and other MCP-capable hosts  
C) It has no defined origin  
D) A single closed-source IDE  

**Answer: B** — MCP is Anthropic's open standard, giving cross-host portability rather than single-vendor lock-in.
```

- [ ] **Step 3: Verify both sections render**

Run:
```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
grep -n "Senior Deep Dive: MCP for Enterprise" course-content/part-3-agentic-ai/module-5-mcp/interview-questions.md
grep -n "Bonus: Senior / JD-Aligned Questions (MCP" course-content/part-3-agentic-ai/module-5-mcp/quiz.md
```
Expected: one line number from each.

- [ ] **Step 4: Commit**

```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
git add course-content/part-3-agentic-ai/module-5-mcp/interview-questions.md course-content/part-3-agentic-ai/module-5-mcp/quiz.md
git commit -m "docs(m5): add Senior Deep Dive on MCP for enterprise integration & copilots"
```

---

### Task 4: M6 — LangGraph → "Stateful orchestration, human-in-the-loop & durable agents"

**Files:**
- Modify (append): `course-content/part-3-agentic-ai/module-6-langgraph/interview-questions.md` (currently 744 lines)
- Modify (append): `course-content/part-3-agentic-ai/module-6-langgraph/quiz.md` (currently 246 lines)

- [ ] **Step 1: Append the deep-dive section to interview-questions.md**

Append to the end of the file:

```markdown


---

## Senior Deep Dive: Stateful Orchestration, Human-in-the-Loop & Durable Agents

> *The JD wants autonomous workflows and copilots that are controllable in production. LangGraph's value is exactly that — interviewers probe state, persistence, and human oversight.*

### SQ1: What does LangGraph add over a linear chain or a simple agent loop?

**Answer:** An explicit **graph of nodes and edges over shared state**, with **conditional and cyclic** flows, controllability, and **persistence/checkpointing**. It lets you model real workflows — branches, loops, retries, parallel fan-out — instead of a single straight line or an opaque while-loop. **Trade-off:** more expressive and controllable, but more upfront design than a chain — justified when the flow has real branching/state.

### SQ2: How do you implement human-in-the-loop with LangGraph?

**Answer:** Use a **checkpointer** plus an **interrupt** before/after a node: the graph persists its state, pauses, surfaces the proposed action to a human, and **resumes** (with optional human edits) on approval. This is essential for high-risk/state-changing actions in a regulated context. **Trade-off:** a human gate adds latency but is the control that makes autonomy acceptable for consequential decisions.

### SQ3: What does durable/resumable execution buy you, and how is it implemented?

**Answer:** A **checkpointer** (in-memory, SQLite, or **Postgres**) persists state **per thread**, enabling crash recovery, long-running workflows, **time-travel/replay**, and an audit trail. **Trade-off:** persistence adds infrastructure and a little latency, but buys reliability and auditability — usually mandatory for production risk workflows.

### SQ4: How do you manage state and avoid context bloat in a long graph?

**Answer:** Define a **typed state schema**; use **reducers** to merge updates (e.g. append vs overwrite); **trim or summarize** message history; and **store large artifacts by reference** rather than inlining them into state. **Trade-off:** aggressive trimming saves tokens/latency but risks dropping context the graph later needs — tune by task.

### SQ5: When is LangGraph the wrong tool?

**Answer:** For **simple linear flows** with no branching, looping, or persistent state — a plain chain is simpler and cheaper. Reaching for LangGraph there adds complexity with no payoff. **Trade-off:** controllability vs simplicity — match the tool to the flow's actual shape.
```

- [ ] **Step 2: Append the bonus quiz block to quiz.md**

Append to the end of the file:

```markdown


---

## Bonus: Senior / JD-Aligned Questions (Stateful Orchestration & Durable Agents)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. What is the main reason to choose LangGraph over a linear chain?

A) It is always cheaper  
B) You need branching, loops, and shared state with controllable, persistent execution  
C) It removes the need for an LLM  
D) It only does image generation  

**Answer: B** — LangGraph models stateful, branching, cyclic workflows that a linear chain cannot.

### BQ2. How is human-in-the-loop achieved in LangGraph?

A) By raising the temperature  
B) A checkpointer plus an interrupt before/after a node, resuming on human approval  
C) By disabling tools  
D) It is not possible  

**Answer: B** — the graph persists state, pauses at an interrupt, and resumes after a human approves/edits.

### BQ3. What does a checkpointer enable?

A) Faster token generation only  
B) Durable, resumable per-thread state: crash recovery, long-running workflows, and audit/replay  
C) Cheaper embeddings  
D) Automatic fine-tuning  

**Answer: B** — checkpointers persist state so workflows survive crashes and can be replayed/audited.

### BQ4. Best way to prevent state/context bloat in a long graph?

A) Inline every artifact into state  
B) Typed state + reducers + trim/summarize messages + store large artifacts by reference  
C) Never persist state  
D) Use a single global variable  

**Answer: B** — a typed schema with reducers and summarization keeps state bounded.

### BQ5. When is LangGraph overkill?

A) For a simple, static, linear pipeline with no branching or state  
B) For any workflow with loops  
C) Whenever you need persistence  
D) For human-in-the-loop flows  

**Answer: A** — a plain chain is simpler and cheaper when there is no branching, looping, or state.
```

- [ ] **Step 3: Verify both sections render**

Run:
```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
grep -n "Senior Deep Dive: Stateful Orchestration" course-content/part-3-agentic-ai/module-6-langgraph/interview-questions.md
grep -n "Bonus: Senior / JD-Aligned Questions (Stateful" course-content/part-3-agentic-ai/module-6-langgraph/quiz.md
```
Expected: one line number from each.

- [ ] **Step 4: Commit**

```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
git add course-content/part-3-agentic-ai/module-6-langgraph/interview-questions.md course-content/part-3-agentic-ai/module-6-langgraph/quiz.md
git commit -m "docs(m6): add Senior Deep Dive on stateful orchestration & durable agents"
```

---

### Task 5: M7 — Architecture → "Enterprise AI architecture & scalable pipelines on Azure"

**Files:**
- Modify (append): `course-content/part-4-production/module-7-architecture/interview-questions.md` (currently 729 lines)
- Modify (append): `course-content/part-4-production/module-7-architecture/quiz.md` (currently 339 lines)

- [ ] **Step 1: Append the deep-dive section to interview-questions.md**

Append to the end of the file:

```markdown


---

## Senior Deep Dive: Enterprise AI Architecture & Scalable Pipelines on Azure

> *The JD lists "AI Architecture" and "scalable AI pipelines" with an Azure emphasis. Interviewers want a reference architecture, a build-vs-buy stance, and answers on scale, failure, and security.*

### SQ1: Sketch a reference architecture for an enterprise GenAI platform on Azure.

**Answer:** Walk the layers:
- **Data/ingestion:** Azure Data Lake / Blob, **Azure Database for PostgreSQL (pgvector)** for vectors + metadata.
- **Index/retrieval:** embeddings (Azure OpenAI), hybrid retrieval + re-ranking.
- **Model layer:** **Azure OpenAI / Azure AI Foundry** for managed models, or self-hosted open models on **AKS** (vLLM).
- **Orchestration:** the app/agent layer (LangChain/LangGraph or SDK).
- **Edge/API:** **Azure API Management** gateway, caching, rate limiting.
- **Cross-cutting:** observability (**Application Insights**), security (**Entra ID**, **Key Vault**, **Private Link**), eval/CI gates, governance/audit.

**Trade-off to close on:** every managed Azure service trades some control and cost for speed and compliance — you choose per layer based on scale and data sensitivity.

### SQ2: Build vs buy — managed model API vs self-hosted open model?

**Answer:** **Buy (Azure OpenAI / Foundry):** fastest to production, managed scaling, compliance certifications, no infra. **Build (self-host on AKS/vLLM):** lower cost-per-token at high volume, full data control, customization, no vendor rate limits. Decide by **scale, data sensitivity, cost-per-token at volume, latency, and customization needs**. **Trade-off:** speed/compliance vs cost-at-scale/control — most teams start managed and self-host only the high-volume, sensitive workloads.

### SQ3: How do you make AI pipelines scalable and cost-controlled?

**Answer:** **Async/queue-based** ingestion, **batching**, autoscaling (**KEDA on AKS**), **provisioned throughput (PTU)** for steady load vs PAYG for burst, **caching** (semantic + exact), **model routing** (small model for easy queries), and **token budgets**. Measure **cost per resolved task**, not per call. **Trade-off:** each lever trades a bit of quality or complexity for cost/latency — tie each to its quality impact.

### SQ4: How do you design an LLM system for failure and resilience?

**Answer:** **Timeouts**, **retries with backoff**, **fallbacks** (smaller model or cached answer), **circuit breakers**, graceful degradation, **idempotency**, dead-letter queues, and multi-region / PTU failover. **Trade-off:** resilience machinery adds cost and complexity — scale it to the SLA and the cost of an outage in a risk context.

### SQ5: How do security and data residency shape the architecture in a regulated domain?

**Answer:** **Private Link / VNet** integration (no public egress), **region pinning** for data residency, **Entra ID** RBAC, **Key Vault** for secrets, PII handling/redaction, network isolation, **customer-managed keys**, and end-to-end **audit logging**. **Trade-off:** stricter isolation slows development and integration but is non-negotiable where data is regulated — bake it into the paved path so it doesn't slow every project.
```

- [ ] **Step 2: Append the bonus quiz block to quiz.md**

Append to the end of the file:

```markdown


---

## Bonus: Senior / JD-Aligned Questions (Enterprise AI Architecture on Azure)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. What is the strongest reason to choose Azure OpenAI / AI Foundry over self-hosting?

A) It is always cheaper at every scale  
B) Speed to production plus managed scaling and compliance, with no infrastructure burden  
C) It allows arbitrary weight surgery  
D) It removes the need for evaluation  

**Answer: B** — managed services win on speed, scaling, and compliance; self-hosting wins on cost-at-scale and control.

### BQ2. What is the strongest reason to self-host an open model on AKS?

A) It is simpler than a managed API  
B) Lower cost-per-token at high volume, full data control, customization, and no vendor rate limits  
C) It needs no monitoring  
D) It guarantees higher accuracy  

**Answer: B** — self-hosting pays off for high-volume, sensitive, or heavily-customized workloads.

### BQ3. Which lever gives predictable cost/latency for steady high-volume LLM traffic on Azure?

A) Always PAYG  
B) Provisioned throughput (PTU) for steady load, combined with caching and routing  
C) Disabling retries  
D) A larger context window  

**Answer: B** — PTU reserves throughput for predictable load; caching/routing cut redundant spend.

### BQ4. Which Azure control keeps AI traffic off the public internet in a regulated system?

A) A public IP  
B) Private Link / VNet integration  
C) A larger SKU  
D) Disabling TLS  

**Answer: B** — Private Link / VNet integration removes public egress for sensitive workloads.

### BQ5. What is the right primary cost metric for an LLM platform?

A) Cost per API call  
B) Cost per resolved task  
C) Number of tokens generated  
D) Number of deployed models  

**Answer: B** — cost per resolved task reflects real business value, not just per-call price.
```

- [ ] **Step 3: Verify both sections render**

Run:
```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
grep -n "Senior Deep Dive: Enterprise AI Architecture" course-content/part-4-production/module-7-architecture/interview-questions.md
grep -n "Bonus: Senior / JD-Aligned Questions (Enterprise AI Architecture" course-content/part-4-production/module-7-architecture/quiz.md
```
Expected: one line number from each.

- [ ] **Step 4: Commit**

```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
git add course-content/part-4-production/module-7-architecture/interview-questions.md course-content/part-4-production/module-7-architecture/quiz.md
git commit -m "docs(m7): add Senior Deep Dive on enterprise AI architecture on Azure"
```

---

### Task 6: M11 — Fine-tuning → "Fine-tuning vs RAG, LoRA/QLoRA & synthetic data on Azure"

**Files:**
- Modify (append): `course-content/part-5-fine-tuning-deployment/module-11-fine-tuning/interview-questions.md` (currently 230 lines)
- Modify (append): `course-content/part-5-fine-tuning-deployment/module-11-fine-tuning/quiz.md` (currently 340 lines)

- [ ] **Step 1: Append the deep-dive section to interview-questions.md**

Append to the end of the file:

```markdown


---

## Senior Deep Dive: Fine-Tuning vs RAG, LoRA/QLoRA & Synthetic Data on Azure

> *The JD lists fine-tuning, PEFT, and "synthetic information to train LLM as part of Azure" with a hallucination angle. Interviewers probe whether you fine-tune for the right reasons and guard against synthetic-data failure modes.*

### SQ1: RAG vs fine-tuning vs both — what's your decision framework?

**Answer:** **RAG** for **fresh, factual, changing knowledge** with citations and access control. **Fine-tuning** for **behavior, format, tone, and domain style**, and to cut latency/cost via shorter prompts — but **not** a reliable way to inject new facts. **Both** is common: fine-tune the behavior, RAG the facts. **Trade-off:** fine-tuning is upfront training cost + a static artifact to re-train as the domain shifts; RAG is per-query retrieval cost but always current — pick by whether the gap is *knowledge* or *behavior*.

### SQ2: Explain PEFT, LoRA, and QLoRA.

**Answer:** **Full fine-tuning** updates all weights — expensive in compute and storage. **LoRA** freezes the base model and trains small **low-rank adapter** matrices — cheap, tiny swappable artifacts, multiple adapters per base. **QLoRA** adds **4-bit (NF4) quantization** of the frozen base so you can fine-tune large models on a single GPU. **Trade-off:** PEFT trades a small quality delta for a large cost/memory saving — almost always the right default outside frontier research.

### SQ3: How do you use synthetic data to fine-tune, and what are the risks?

**Answer:** Generate or augment training data with a stronger model (**distillation**), bootstrap low-data domains, and balance classes — while keeping **real PII out**. **Risks:** **model collapse**, **bias amplification**, distribution drift, and hallucinated/incorrect labels. Mitigate with human review, diversity, **mixing in real data**, and evaluation. **Trade-off:** synthetic data unblocks low-data domains but degrades quality if it dominates — it's a supplement, not a replacement, and (per the JD) directly relevant to controlling hallucination.

### SQ4: How do you run and evaluate fine-tuning on Azure?

**Answer:** Use **Azure OpenAI fine-tuning** or **Azure ML**: prepare **JSONL** training data, train, and deploy. Gate promotion with **eval**: a hold-out set + a **golden set** + a **regression check against the base model** before any deploy. **Version data and model together.** **Trade-off:** an eval gate slows release but is what prevents a fine-tune that's better on your task yet worse everywhere else.

### SQ5: How do you prevent overfitting and catastrophic forgetting during fine-tuning?

**Answer:** Small learning rate, **few epochs**, validation-based **early stopping**, **mix in general-domain data**, and prefer **LoRA** (limited weight drift). Evaluate on a **broad benchmark**, not just the task set. **Trade-off:** stronger task specialization risks eroding general capability — you balance the two and verify with broad evals.
```

- [ ] **Step 2: Append the bonus quiz block to quiz.md**

Append to the end of the file:

```markdown


---

## Bonus: Senior / JD-Aligned Questions (Fine-Tuning, PEFT & Synthetic Data)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. You need the model to reliably cite up-to-date internal policies. Fine-tune or RAG?

A) Fine-tune — it memorizes facts best  
B) RAG — fresh facts with citations and access control  
C) Neither is possible  
D) Increase temperature  

**Answer: B** — RAG handles changing factual knowledge with citations; fine-tuning is for behavior, not fresh facts.

### BQ2. What does LoRA do?

A) Retrains all model weights  
B) Freezes the base model and trains small low-rank adapter matrices  
C) Quantizes the dataset  
D) Replaces the tokenizer  

**Answer: B** — LoRA trains compact, swappable adapters on top of a frozen base.

### BQ3. What does QLoRA add over LoRA?

A) Nothing  
B) 4-bit (NF4) quantization of the frozen base so large models fine-tune on a single GPU  
C) A larger context window  
D) Automatic RAG  

**Answer: B** — QLoRA quantizes the base to 4-bit, slashing memory needs for fine-tuning.

### BQ4. What is the biggest risk of training primarily on model-generated synthetic data?

A) It is always perfect  
B) Model collapse, bias amplification, and drift — mitigate by mixing real data, ensuring diversity, and human review  
C) It needs no evaluation  
D) It removes the need for a base model  

**Answer: B** — synthetic data that dominates the mix degrades the model; treat it as a supplement.

### BQ5. What is the right gate before promoting a fine-tuned model?

A) Deploy immediately  
B) Evaluate on a golden + hold-out set and run a regression check against the base model  
C) Check only training loss  
D) Ask the model if it improved  

**Answer: B** — eval-gated promotion catches task gains that come at the cost of general regressions.
```

- [ ] **Step 3: Verify both sections render**

Run:
```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
grep -n "Senior Deep Dive: Fine-Tuning vs RAG" course-content/part-5-fine-tuning-deployment/module-11-fine-tuning/interview-questions.md
grep -n "Bonus: Senior / JD-Aligned Questions (Fine-Tuning" course-content/part-5-fine-tuning-deployment/module-11-fine-tuning/quiz.md
```
Expected: one line number from each.

- [ ] **Step 4: Commit**

```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
git add course-content/part-5-fine-tuning-deployment/module-11-fine-tuning/interview-questions.md course-content/part-5-fine-tuning-deployment/module-11-fine-tuning/quiz.md
git commit -m "docs(m11): add Senior Deep Dive on fine-tuning, PEFT & synthetic data on Azure"
```

---

### Task 7: M14 — Capstone → "Risk-management capstone end-to-end"

**Files:**
- Modify (append): `course-content/part-6-capstone/module-14-projects/interview-questions.md` (currently 570 lines)
- Modify (append): `course-content/part-6-capstone/module-14-projects/quiz.md` (currently 238 lines)

- [ ] **Step 1: Append the deep-dive section to interview-questions.md**

Append to the end of the file:

```markdown


---

## Senior Deep Dive: A Risk-Management Capstone, End-to-End

> *The JD is for AI in risk management for global, regulated organisations, judged on business outcomes. Interviewers want one project you can walk end-to-end and tie to their success metrics.*

### SQ1: Walk through a risk-management GenAI capstone end-to-end.

**Answer:** Use a **credit-risk / fraud analyst copilot**:
- **Problem & stakeholders & success metric** (e.g. cut analyst case time, hold false-negative rate).
- **Data:** transactions, policies, KYC docs.
- **Architecture:** a **calibrated gradient-boosted tabular model** for the risk score + **RAG over policy documents** + an **LLM** for human-readable case narratives — the LLM is the *second stage*, not the classifier.
- **Eval:** faithfulness/relevance for RAG, task-success for the copilot, **calibration** for the score.
- **Rollout:** canary, **human-in-the-loop**, full audit trail.
- **Outcome:** map to the JD's success metrics.

**Trade-off to close on:** combining classic ML and GenAI adds system complexity but gives you a fast, explainable score *and* natural-language reasoning — each used where it's strongest.

### SQ2: How do you map a capstone to the JD's success metrics?

**Answer:** Tie each deliverable to a JD metric: **scalable production deployment** (it shipped and serves real traffic), **model performance/accuracy improvement** (quantified lift), **reduced deployment timeline** (via MLOps automation / paved paths), and **org adoption/impact** (active users, decisions assisted). **Quantify every one.** **Trade-off:** optimizing one metric (e.g. recall) can hurt another (false alarms/cost) — you state which you chose and why with the risk owner.

### SQ3: How do you choose between classic ML and GenAI within the capstone?

**Answer:** **Tabular prediction** (default/fraud probability) → **gradient-boosted trees** (calibrated, explainable, fast, auditable). **Unstructured reasoning** (policy Q&A, narrative, summarization) → **LLM/RAG**. Combine them; **do not** use an LLM as the primary classifier (latency, cost, determinism, auditability). **Trade-off:** the maturity signal is recommending the *simplest* model that meets the need — often classic ML for the decision and GenAI for the explanation.

### SQ4: What makes the capstone "production-ready" rather than a notebook demo?

**Answer:** An **eval harness + CI gates**, **monitoring/drift detection**, **rollback**, **security/PII** handling, an **audit trail**, **cost controls**, **human-in-the-loop** for high-risk decisions, and docs/**model card**. **Trade-off:** this scaffolding is real effort that a demo skips — but it's exactly what separates a 10-year engineer's work from a prototype, and what a regulator expects.

### SQ5: How do you present the capstone's business impact to non-technical stakeholders?

**Answer:** **Lead with the outcome and the metric** — risk reduced, dollars or analyst-hours saved, adoption — then tie the technical choices to that value, and **acknowledge limitations and governance**. **Trade-off:** depth of technical detail vs clarity for the audience — you calibrate to the room, but always anchor on business value, not architecture.
```

- [ ] **Step 2: Append the bonus quiz block to quiz.md**

Append to the end of the file:

```markdown


---

## Bonus: Senior / JD-Aligned Questions (Risk-Management Capstone)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. What is the best architecture for a credit-risk analyst copilot?

A) An LLM as the primary classifier for the risk score  
B) A calibrated gradient-boosted model for the score, plus RAG/LLM for policy Q&A and narratives  
C) A single prompt with no retrieval  
D) A rules engine only  

**Answer: B** — use classic ML for the calibrated, explainable decision and GenAI for reasoning/explanation.

### BQ2. Which capstone deliverable maps to the JD metric "reduced AI deployment timelines"?

A) A bigger model  
B) MLOps automation and paved-path CI/CD with eval gates  
C) More prompts  
D) A larger context window  

**Answer: B** — automation and paved paths are what compress idea-to-production time.

### BQ3. What makes a capstone "production-ready" versus a notebook demo?

A) A nicer chart  
B) Eval/CI gates, monitoring, rollback, audit trail, and security/cost controls  
C) More training epochs  
D) A public GitHub star count  

**Answer: B** — production readiness is operational scaffolding, not model size.

### BQ4. For predicting default probability from tabular features, the right model family is:

A) A large language model  
B) Gradient-boosted trees — calibrated, explainable, and fast  
C) A diffusion model  
D) A k-means cluster  

**Answer: B** — tabular risk prediction is GBM territory; an LLM is the wrong primary classifier.

### BQ5. What is the best way to present the capstone's impact to executives?

A) Walk through the model architecture in detail  
B) Lead with the business outcome and a quantified metric, then tie tech choices to that value  
C) Show the training loss curve  
D) List every library used  

**Answer: B** — executives buy outcomes; anchor on the metric and the value, not the architecture.
```

- [ ] **Step 3: Verify both sections render**

Run:
```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
grep -n "Senior Deep Dive: A Risk-Management Capstone" course-content/part-6-capstone/module-14-projects/interview-questions.md
grep -n "Bonus: Senior / JD-Aligned Questions (Risk-Management" course-content/part-6-capstone/module-14-projects/quiz.md
```
Expected: one line number from each.

- [ ] **Step 4: Commit**

```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
git add course-content/part-6-capstone/module-14-projects/interview-questions.md course-content/part-6-capstone/module-14-projects/quiz.md
git commit -m "docs(m14): add Senior Deep Dive on the risk-management capstone"
```

---

### Task 8: Cross-reference updates (README + master guide)

**Files:**
- Modify: `course-content/README.md` (Senior Deep Dive bullet list, around lines 83–88)
- Modify: `course-content/SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md` (JD → Module Map table, lines ~37–50)

- [ ] **Step 1: Extend the README Senior Deep Dive bullet list**

In `course-content/README.md`, find the existing list (the four bullets ending with the Module 1 hallucination link, around lines 85–88) and append these seven bullets immediately after the last existing bullet, keeping the same `- [text](path) (Module N)` format:

```markdown
- [LlamaIndex vs LangChain & framework exit](part-1-foundations/module-2-langchain/interview-questions.md) (Module 2)
- [Multi-agent systems & autonomous workflows](part-3-agentic-ai/module-4-agentic-systems/interview-questions.md) (Module 4)
- [MCP for enterprise integration & copilots](part-3-agentic-ai/module-5-mcp/interview-questions.md) (Module 5)
- [Stateful orchestration & durable agents](part-3-agentic-ai/module-6-langgraph/interview-questions.md) (Module 6)
- [Enterprise AI architecture on Azure](part-4-production/module-7-architecture/interview-questions.md) (Module 7)
- [Fine-tuning vs RAG, LoRA/QLoRA & synthetic data](part-5-fine-tuning-deployment/module-11-fine-tuning/interview-questions.md) (Module 11)
- [Risk-management capstone, end-to-end](part-6-capstone/module-14-projects/interview-questions.md) (Module 14)
```

- [ ] **Step 2: Update the master-guide JD → Module Map emphasis column**

In `course-content/SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md`, update these specific table rows so the "Senior-level emphasis" column references the new deep dives. Use Edit to change each row's third column text (keep the first two columns intact):

- Row "LangChain / LlamaIndex orchestration" → set emphasis to: `When to drop the framework; cost/latency; **M2 deep dive: LlamaIndex vs LangChain**`
- Row "AI agents, multi-agent systems, copilots" → set emphasis to: `Orchestration (LangGraph), MCP, autonomy vs control; **M4/M5/M6 deep dives**`
- Row "Prompt engineering, fine-tuning, RAG frameworks" → set emphasis to: `RAG vs fine-tuning decision, eval-gated promotion; **M11 deep dive: LoRA/QLoRA & synthetic data**`
- Row "AI architecture, scalable pipelines" → set emphasis to: `End-to-end design under constraints; **M7 deep dive: enterprise architecture on Azure**`
- Row "Risk management domain, global/regulated" → set emphasis to: `MRM, fairness, EU AI Act, fraud/credit risk; **M14 deep dive: risk capstone**`

(If a row's exact current text differs, match on the first-column JD-requirement text and replace only the emphasis cell.)

- [ ] **Step 3: Verify the cross-references**

Run:
```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
grep -c "interview-questions.md) (Module" course-content/README.md
grep -n "M2 deep dive\|M4/M5/M6 deep dives\|M11 deep dive\|M7 deep dive\|M14 deep dive" course-content/SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md
```
Expected: README count is at least 11 (4 existing + 7 new); the master-guide grep returns 5 matching lines.

- [ ] **Step 4: Commit**

```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
git add course-content/README.md course-content/SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md
git commit -m "docs(course): cross-reference new Senior Deep Dives in README & master guide"
```

---

## Final Verification (after all tasks)

- [ ] **All seven modules have both sections:**

```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
grep -rl "## Senior Deep Dive:" course-content/part-1-foundations/module-2-langchain course-content/part-3-agentic-ai/module-4-agentic-systems course-content/part-3-agentic-ai/module-5-mcp course-content/part-3-agentic-ai/module-6-langgraph course-content/part-4-production/module-7-architecture course-content/part-5-fine-tuning-deployment/module-11-fine-tuning course-content/part-6-capstone/module-14-projects
grep -rl "Bonus: Senior / JD-Aligned Questions" course-content/part-1-foundations/module-2-langchain course-content/part-3-agentic-ai/module-4-agentic-systems course-content/part-3-agentic-ai/module-5-mcp course-content/part-3-agentic-ai/module-6-langgraph course-content/part-4-production/module-7-architecture course-content/part-5-fine-tuning-deployment/module-11-fine-tuning course-content/part-6-capstone/module-14-projects
```
Expected: 7 interview-questions.md paths and 7 quiz.md paths.

- [ ] **Clean git log of the eight commits:**

```bash
cd "d:/Jay Rathod/Tutorials/Applied AI"
git log --oneline -8
```
Expected: the eight `docs(...)` commits from Tasks 1–8.

> **Note on commit granularity:** The spec mentioned a single commit; this plan uses one commit per module (plus a cross-ref commit) for cleaner review. If a single commit is preferred, run `git reset --soft HEAD~8 && git commit` to squash before sharing.

---

## Notes for the Implementing Engineer

- **Do not touch** out-of-scope files: the `gen-ai-course/` tree, `ai_inbox_cleaner` Python files, the M8/M9/M13 MLOps modules, or any diagrams.
- The working tree already has **unrelated uncommitted changes** (M1/M3/M10/M12 deep dives and `ai_inbox_cleaner` edits). **Stage only the files named in each task** — never `git add -A` / `git add .`.
- Write the SQ answers as **flowing prose in the house style**, not as the bullet outlines shown above — the bullets tell you the substance each answer must contain; convert them to prose like the existing M1/M3/M10/M12 answers.
- Keep **two trailing spaces** after each quiz option (`A) ...  `) for correct markdown line breaks.
- Line counts in the file headers are current as of plan authoring; since every change is an append, they don't need to be exact at execution time.
```
