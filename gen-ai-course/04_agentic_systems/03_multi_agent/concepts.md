# Concepts: Multi-Agent Collaboration

---

## What are Multi-Agent Systems?

Multi-agent systems (MAS) consist of multiple autonomous AI agents that work together to achieve complex goals that would be difficult or impossible for a single agent to accomplish alone. Each agent perceives its environment, makes decisions, and acts — either independently or in coordination with other agents.

In the context of LLM-based systems, an **agent** is typically an LLM equipped with:
- A set of **tools** (web search, code execution, database access, etc.)
- A **memory** mechanism (short-term context, long-term vector store)
- A **reasoning loop** (think → act → observe → repeat)
- A **role or persona** defining its area of responsibility

Multi-agent systems extend this by connecting multiple such agents, enabling them to delegate, collaborate, critique, and synthesize work across specializations.

### Why Single Agents Fall Short

A single LLM agent struggles with:
- **Context window limits**: Long tasks require more tokens than any single context window can hold
- **Cognitive overload**: Asking one agent to plan, research, code, test, and document simultaneously degrades quality
- **Lack of checks and balances**: No mechanism for self-verification or peer review
- **Bottleneck scalability**: Everything serializes through one agent

Multi-agent architectures solve these problems through distribution, specialization, and parallelism.

---

## Benefits of Multi-Agent Systems

### 1. Specialization
Each agent is designed and prompted for a narrow domain. A **CodeAgent** knows programming idioms; a **ResearchAgent** knows how to formulate search queries and evaluate sources; a **CriticAgent** knows how to find flaws in arguments. Specialization means each agent operates at maximum effectiveness within its scope.

> **Example**: In a software engineering pipeline, a `PlannerAgent` decomposes requirements into tickets, a `CoderAgent` implements each ticket, a `ReviewerAgent` checks for bugs, and a `DocumentationAgent` writes the docs — each excelling at its role.

### 2. Parallelism and Scalability
Independent subtasks can be executed concurrently by multiple agents, dramatically reducing wall-clock time. Need to research 10 topics? Spawn 10 `ResearchAgent` instances in parallel rather than waiting for one to finish sequentially.

Horizontal scaling is architectural: you add agents, not complexity to existing ones.

### 3. Robustness and Fault Tolerance
If one agent fails, the system can retry using a different agent, fall back to a simpler strategy, or route around the failure. A well-designed orchestrator handles agent errors as recoverable exceptions rather than fatal failures.

### 4. Modularity and Maintainability
Agents are independently testable and swappable. You can upgrade the `SummarizerAgent` from GPT-4 to a fine-tuned model without touching the rest of the pipeline. This mirrors microservices architecture in traditional software.

### 5. Emergent Problem-Solving
When agents with different "perspectives" debate or critique each other's outputs, the system can arrive at solutions that no single agent would have produced — similar to how human teams outperform individuals on complex tasks.

---

## Architecture Patterns

### 1. Hierarchical (Supervisor-Worker)

```
          Supervisor Agent
         /        |        \
   Research    Analysis   Reporting
    Agent       Agent      Agent
```

**How it works**: A supervisor (orchestrator) receives a high-level goal, decomposes it into subtasks, and delegates each to a specialized worker agent. Workers report results back to the supervisor, which synthesizes a final output.

**Best for**: Structured workflows with clear task decomposition and a single source of truth for state.

**Implementation pattern**:
```python
class SupervisorAgent:
    def run(self, goal: str):
        plan = self.llm.plan(goal)               # Decompose goal
        results = {}
        for task in plan.tasks:
            agent = self.route(task)             # Select agent by task type
            results[task.id] = agent.execute(task)
        return self.llm.synthesize(results)      # Combine outputs
```

**Trade-offs**:
- The supervisor is a single point of failure
- Supervisor must have broad enough context to coordinate effectively
- Works well when subtasks are known upfront

---

### 2. Peer-to-Peer (Decentralized)

```
Agent A <──────> Agent B
   ^                 ^
   │                 │
   └──────> Agent C <┘
```

**How it works**: Agents communicate directly with each other without a central coordinator. Each agent can initiate communication, request help, or share information based on its own reasoning.

**Best for**: Dynamic, emergent workflows where the sequence of operations isn't known in advance.

**Implementation pattern**:
```python
class PeerAgent:
    def __init__(self, name, peers: dict):
        self.name = name
        self.peers = peers  # {name: AgentInterface}
    
    def handle(self, message: Message):
        if self.can_handle(message):
            return self.process(message)
        else:
            best_peer = self.select_peer(message)
            return self.peers[best_peer].handle(message)
```

**Trade-offs**:
- More flexible and resilient (no central bottleneck)
- Harder to debug — conversation flows can be non-linear
- Risk of infinite loops or circular delegation without proper guards

---

### 3. Hub-and-Spoke

```
      Agent A
         |
Hub ─────┼───── Agent B
         |
      Agent C
```

**How it works**: A central hub handles all routing and message brokering. Agents never communicate directly — all messages pass through the hub. The hub acts as a message bus or event broker.

**Best for**: Systems where observability and control of all inter-agent communication is critical (e.g., compliance, auditing).

**Implementation pattern**:
```python
class MessageHub:
    def __init__(self):
        self.agents = {}
        self.message_log = []
    
    def register(self, name: str, agent):
        self.agents[name] = agent
    
    def send(self, from_agent: str, to_agent: str, message: Message):
        self.message_log.append((from_agent, to_agent, message))
        return self.agents[to_agent].receive(message)
```

**Trade-offs**:
- Full observability of all messages
- Hub becomes a bottleneck under high load
- Simpler agent logic (no routing responsibility)

---

### 4. Pipeline (Sequential Chain)

```
Input → Agent A → Agent B → Agent C → Output
```

Each agent processes the output of the previous one. This is the simplest pattern — essentially a processing chain.

**Best for**: Linear workflows like: fetch → clean → analyze → summarize → format.

---

### 5. Blackboard (Shared Memory)

```
         ┌──────────────────┐
         │   Blackboard     │
         │  (shared state)  │
         └──────────────────┘
              ↑    ↑    ↑
         Agent A  Agent B  Agent C
```

**How it works**: A shared data store (the "blackboard") holds the current problem state. Agents read from and write to the blackboard independently. Each agent activates when it detects data it can process.

**Best for**: Problems where agents contribute incrementally (e.g., document analysis where different agents annotate different aspects).

---

### 6. Debate / Critic Pattern

```
Proposer Agent → [Draft Solution]
                        ↓
               Critic Agent → [Critique]
                        ↓
               Proposer Agent → [Revised Solution]
                        ↓
               Judge Agent → [Final Decision]
```

**How it works**: One agent proposes a solution; a critic agent evaluates and challenges it; the proposer revises. This continues for N rounds or until the critic approves.

**Best for**: High-stakes outputs where accuracy matters: legal analysis, medical reasoning, complex code generation.

**Research backing**: "Constitutional AI" and "LLM-as-a-Judge" research shows adversarial agent patterns significantly improve output quality.

---

## Agent Communication

### Message Structure

A well-designed agent message is structured and machine-parseable:

```python
from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime
import uuid

@dataclass
class AgentMessage:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str           # Agent name/ID
    recipient: str        # Target agent or "broadcast"
    type: str             # "request" | "inform" | "query" | "response" | "error"
    content: Any          # The payload
    conversation_id: str  # Groups related messages
    timestamp: datetime   = field(default_factory=datetime.utcnow)
    metadata: dict        = field(default_factory=dict)
    in_reply_to: Optional[str] = None  # Message ID being replied to
```

### Message Types

| Type | Purpose | Example |
|------|---------|---------|
| **Request** | Ask another agent to perform an action | "Search for papers on RAG published in 2024" |
| **Inform** | Push information without expecting a reply | "I found 15 papers. Storing in shared context." |
| **Query** | Ask for current state or data | "What is the current status of task #3?" |
| **Response** | Reply to a Request or Query | Returns the result of the requested action |
| **Error** | Signal failure | "Tool call failed: rate limit exceeded" |
| **Broadcast** | Send to all agents | "Stopping all work — goal has been achieved" |

### Communication Protocols

#### Synchronous (Request-Response)
The calling agent **blocks** until it receives a response. Simple to reason about but can cause bottlenecks.

```python
result = await research_agent.execute(task)  # Blocks here
next_task = planner.next(result)
```

**Use when**: The next step strictly depends on the current result.

#### Asynchronous (Message Passing)
The calling agent fires a message and continues other work. Results arrive via callbacks or a message queue.

```python
# Fire and continue
await message_queue.publish("research_agent", task)
await message_queue.publish("analysis_agent", other_task)

# Later, collect results
results = await asyncio.gather(
    message_queue.consume("research_results"),
    message_queue.consume("analysis_results")
)
```

**Use when**: Multiple agents can work in parallel; results are needed only later.

#### Event-Driven (Publish-Subscribe)
Agents publish events to named channels; other agents subscribe to channels of interest. No direct coupling between publisher and subscriber.

```python
# Publisher
event_bus.publish("research.complete", {"topic": "RAG", "papers": papers})

# Subscriber (registered at startup)
@event_bus.subscribe("research.complete")
async def on_research_complete(event):
    analysis_agent.analyze(event["papers"])
```

**Use when**: Loose coupling is desired; downstream agents should react to state changes automatically.

---

## Task Decomposition

Effective task decomposition is the core skill of an orchestrator agent. Poor decomposition leads to redundant work, missed subtasks, or subtasks too large for individual agents to complete well.

### Decomposition Strategies

#### 1. Goal Decomposition (Top-Down)
Break the high-level goal into independent subgoals.

```
Goal: "Write a technical blog post about LLM agents"
  ├── Subgoal 1: Research current state of LLM agents
  ├── Subgoal 2: Identify 5 key concepts to explain
  ├── Subgoal 3: Draft each section
  ├── Subgoal 4: Review for technical accuracy
  └── Subgoal 5: Format and finalize
```

#### 2. Data Decomposition (Parallel Fan-Out)
Split a dataset and process chunks in parallel.

```
Task: "Summarize 50 customer support tickets"
  ├── Agent 1: Tickets 1-10
  ├── Agent 2: Tickets 11-20
  ├── Agent 3: Tickets 21-30
  ├── Agent 4: Tickets 31-40
  └── Agent 5: Tickets 41-50
→ Aggregator: Combine and theme summaries
```

#### 3. Functional Decomposition (Pipeline)
Break a task into sequential processing stages.

```
Task: "Generate a competitor analysis report"
  ├── Stage 1 (ResearchAgent): Gather raw data
  ├── Stage 2 (AnalysisAgent): Extract insights
  ├── Stage 3 (WriterAgent): Draft narrative
  └── Stage 4 (EditorAgent): Polish and format
```

### The Full Decomposition Loop

```
1. ANALYZE    → Understand the goal, constraints, and available agents
2. PLAN       → Determine subtasks, dependencies, and execution order
3. ASSIGN     → Match subtasks to best-suited agents
4. EXECUTE    → Run subtasks (parallel where possible)
5. MONITOR    → Track progress, handle failures, re-plan if needed
6. COLLECT    → Gather all agent outputs
7. SYNTHESIZE → Combine outputs into a coherent final result
8. VALIDATE   → Check result against original goal; iterate if needed
```

---

## State Management in Multi-Agent Systems

One of the hardest challenges in MAS is managing shared state consistently.

### State Types

| State Type | Scope | Storage |
|------------|-------|---------|
| **Agent-local state** | Single agent's context window | In-memory |
| **Conversation state** | All messages in a session | Thread/session store |
| **Shared task state** | Current progress on a shared goal | Distributed store (Redis, DB) |
| **Long-term memory** | Persistent knowledge across sessions | Vector DB, key-value store |

### State Passing Patterns

**Pattern 1: Pass-by-Value (Message Payload)**
Each message carries all needed context. Simple but can create large messages.

```python
message = {
    "task": "analyze sentiment",
    "data": full_text,          # Entire context passed
    "prior_results": {...}
}
```

**Pattern 2: Pass-by-Reference (Shared Store)**
Messages carry only IDs; agents fetch data from a shared store.

```python
message = {
    "task": "analyze sentiment",
    "data_ref": "session:abc123:document:1",  # Reference only
}
# Agent fetches: store.get("session:abc123:document:1")
```

**Pattern 3: Event Sourcing**
All state changes are recorded as immutable events. Any agent can reconstruct current state by replaying events.

---

## Memory Architecture for Multi-Agent Systems

### Four Layers of Memory

```
┌─────────────────────────────────────┐
│  Layer 4: External Knowledge        │  ← Vector DB, web search, APIs
├─────────────────────────────────────┤
│  Layer 3: Long-Term Agent Memory    │  ← Persistent per-agent store
├─────────────────────────────────────┤
│  Layer 2: Shared Working Memory     │  ← Current session/task state
├─────────────────────────────────────┤
│  Layer 1: In-Context Memory         │  ← Current LLM context window
└─────────────────────────────────────┘
```

- **In-context**: The LLM's current prompt — fast but ephemeral and size-limited
- **Shared working memory**: A key-value store all agents in a session can read/write (Redis, in-memory dict)
- **Long-term agent memory**: Each agent's accumulated knowledge across sessions (vector DB with agent-scoped namespacing)
- **External knowledge**: Retrieval-augmented data fetched on demand from the web, databases, or document stores

---

## Orchestration with LLMs

Modern multi-agent frameworks use LLMs not just as workers but as **orchestrators** — the LLM itself decides which agents to call, in what order, and with what inputs.

### LLM-as-Orchestrator Pattern

```python
ORCHESTRATOR_PROMPT = """
You are a coordinator managing a team of specialized agents:
- research_agent: Finds information on any topic
- code_agent: Writes and executes Python code
- math_agent: Solves mathematical problems
- writer_agent: Drafts natural language content

Given the user's goal, decide which agents to invoke and in what order.
Output a JSON plan: {{"steps": [{{"agent": "...", "task": "..."}}]}}
"""

class LLMOrchestrator:
    def run(self, goal: str):
        plan = self.llm.complete(ORCHESTRATOR_PROMPT + f"\nGoal: {goal}")
        plan = json.loads(plan)
        
        context = {}
        for step in plan["steps"]:
            agent = self.agents[step["agent"]]
            result = agent.execute(step["task"], context)
            context[step["agent"]] = result
        
        return self.llm.synthesize(goal, context)
```

### Tool-Calling as Agent Invocation

In frameworks like LangGraph and AutoGen, agent invocation is modeled as **tool use** — the orchestrator LLM calls agents the same way it would call a function:

```python
tools = [
    {
        "name": "research_agent",
        "description": "Search the web and synthesize information on a topic",
        "parameters": {"topic": "string", "depth": "shallow|deep"}
    },
    {
        "name": "code_agent", 
        "description": "Write and execute Python code to solve a problem",
        "parameters": {"problem": "string", "language": "python"}
    }
]

# LLM decides to call research_agent, then passes result to code_agent
```

---

## Practical Example: Research Assistant Pipeline

A complete, production-grade research assistant using multi-agent architecture:

```python
import asyncio
from typing import List
from anthropic import Anthropic

client = Anthropic()

class PlannerAgent:
    """Decomposes a research topic into focused subtopics."""
    
    def create_plan(self, topic: str) -> List[str]:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""Break the research topic "{topic}" into 3-5 focused subtopics.
                Return as a JSON array of strings. Example: ["subtopic1", "subtopic2"]"""
            }]
        )
        return json.loads(response.content[0].text)


class SearchAgent:
    """Performs web search and returns raw results for a subtopic."""
    
    def search(self, subtopic: str) -> str:
        # In production: integrate with Tavily, SerpAPI, or Bing Search
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": f"Provide a detailed factual overview of: {subtopic}"
            }]
        )
        return response.content[0].text


class SummarizerAgent:
    """Synthesizes multiple research findings into a coherent report."""
    
    def summarize(self, topic: str, findings: dict) -> str:
        findings_text = "\n\n".join([
            f"### {subtopic}\n{content}" 
            for subtopic, content in findings.items()
        ])
        
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": f"""Synthesize these research findings on "{topic}" into a 
                comprehensive, well-structured report:\n\n{findings_text}"""
            }]
        )
        return response.content[0].text


class CriticAgent:
    """Reviews the final report for gaps, inaccuracies, or missing context."""
    
    def critique(self, topic: str, report: str) -> str:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""Review this research report on "{topic}". 
                Identify: (1) factual gaps, (2) missing perspectives, (3) areas needing deeper analysis.
                Be specific and constructive.\n\nReport:\n{report}"""
            }]
        )
        return response.content[0].text


class ResearchTeam:
    def __init__(self):
        self.planner = PlannerAgent()
        self.searcher = SearchAgent()
        self.summarizer = SummarizerAgent()
        self.critic = CriticAgent()
    
    async def research(self, topic: str, iterations: int = 2) -> str:
        # Step 1: Plan
        subtopics = self.planner.create_plan(topic)
        print(f"Plan: {subtopics}")
        
        # Step 2: Parallel search across all subtopics
        search_tasks = [
            asyncio.to_thread(self.searcher.search, subtopic)
            for subtopic in subtopics
        ]
        results = await asyncio.gather(*search_tasks)
        findings = dict(zip(subtopics, results))
        
        # Step 3: Synthesize
        report = self.summarizer.summarize(topic, findings)
        
        # Step 4: Critique and refine (debate loop)
        for i in range(iterations):
            critique = self.critic.critique(topic, report)
            print(f"Critique round {i+1}: {critique[:200]}...")
            
            # Re-synthesize with critique as additional context
            findings["critique_feedback"] = critique
            report = self.summarizer.summarize(topic, findings)
        
        return report


# Usage
async def main():
    team = ResearchTeam()
    report = await team.research("The impact of LLM agents on software development")
    print(report)

asyncio.run(main())
```

---

## Common Frameworks for Multi-Agent Systems

### LangGraph
Graph-based orchestration where agents are nodes and transitions are edges. Supports cycles (loops), conditionals, and human-in-the-loop checkpoints.

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(ResearchState)
workflow.add_node("planner", planner_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("critic", critic_node)

workflow.add_edge("planner", "researcher")
workflow.add_conditional_edges(
    "critic",
    should_continue,          # Returns "researcher" or END
    {"researcher": "researcher", "end": END}
)
```

### AutoGen (Microsoft)
Agents are defined with roles and engage in multi-turn conversations to solve problems. Supports `GroupChat` for multi-agent round-table discussion.

```python
from autogen import AssistantAgent, UserProxyAgent, GroupChat

planner = AssistantAgent("Planner", system_message="You decompose tasks...")
coder = AssistantAgent("Coder", system_message="You write Python code...")
critic = AssistantAgent("Critic", system_message="You review code for bugs...")

group_chat = GroupChat(agents=[planner, coder, critic], messages=[], max_round=10)
```

### CrewAI
Role-based agents with explicit crews, tasks, and processes (sequential or hierarchical).

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(role="Researcher", goal="Find accurate information", ...)
writer = Agent(role="Writer", goal="Write compelling content", ...)

research_task = Task(description="Research LLM agents", agent=researcher)
write_task = Task(description="Write blog post", agent=writer)

crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task],
            process=Process.sequential)
```

---

## Failure Modes and Mitigation

### 1. Agent Loops
Agents enter infinite cycles of calling each other without progress.

**Mitigation**: Implement a step counter; abort after N steps. Use a supervisor to detect stalled progress.

### 2. Context Poisoning
One agent produces incorrect output that cascades as false context for downstream agents.

**Mitigation**: Use critic/validator agents at checkpoints. Never pass raw unvalidated output to downstream agents.

### 3. Tool Overuse
Agents repeatedly call expensive tools (web search, code execution) when the answer is already available in context.

**Mitigation**: Inject a "check context first" instruction. Cache tool results within a session.

### 4. Conflicting Instructions
Two agents given overlapping responsibilities produce contradictory outputs.

**Mitigation**: Clear role boundaries in system prompts. Use a final arbiter agent to resolve conflicts.

### 5. Latency Amplification
Sequential chains of slow agents accumulate latency multiplicatively.

**Mitigation**: Maximize parallel execution. Profile the critical path and optimize the slowest agent first.

---

## Design Principles for Production Multi-Agent Systems

1. **Single Responsibility**: Each agent does one thing well. Resist the urge to give agents multiple roles.
2. **Explicit Contracts**: Define the exact input/output schema for each agent. Validate at boundaries.
3. **Idempotency**: Agents should produce the same output given the same input — enables safe retries.
4. **Observability First**: Log every message, every tool call, every agent decision. You cannot debug what you cannot observe.
5. **Graceful Degradation**: If a specialist agent fails, the system should fall back to a generalist rather than crashing.
6. **Human-in-the-Loop**: For high-stakes decisions, route through a human approval step before acting.
7. **Cost Awareness**: Each LLM call costs money and time. Cheap models for routing/classification; expensive models for reasoning.

---

## Summary

Multi-agent systems represent a paradigm shift from single-model pipelines to collaborative AI architectures. The key ideas are:

| Concept | Core Insight |
|--------|-------------|
| **Specialization** | Narrow-scope agents outperform generalist agents on specific tasks |
| **Orchestration** | An LLM or rule-based system routes tasks to the right agent |
| **Communication** | Structured messages with types, IDs, and conversation threading |
| **State management** | Shared stores decouple agents while maintaining coherent task state |
| **Debate patterns** | Adversarial critic loops improve output quality significantly |
| **Parallel execution** | Independent subtasks should always run concurrently |
| **Observability** | Full message logging is non-negotiable in production |

The field is evolving rapidly — today's best practice (LangGraph, AutoGen, CrewAI) will be superseded, but the underlying principles of specialization, decomposition, and structured communication will remain foundational.
