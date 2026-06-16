# Module 2: LangChain Framework — Interview Questions

## Table of Contents
- [Beginner Questions (1-10)](#beginner-questions)
- [Intermediate Questions (11-20)](#intermediate-questions)
- [Advanced Questions (21-28)](#advanced-questions)

---

## Beginner Questions

### Q1: What is LangChain and why is it useful?

**Answer:** LangChain is an open-source framework designed to simplify the development of applications powered by Large Language Models (LLMs). It provides abstractions for common LLM operations including prompt management, chain orchestration, memory handling, and agent creation. It is useful because it reduces boilerplate code, enables modular composition of LLM workflows, and integrates with multiple model providers and external tools.

---

### Q2: What are the core components of LangChain?

**Answer:** The core components of LangChain are:

| Component | Purpose |
|-----------|---------|
| **Models** | Wrappers for LLMs (chat and text completion) |
| **Prompts** | Templates for structuring model inputs |
| **Output Parsers** | Extract structured data from model outputs |
| **Indexes** | Document loading, splitting, and retrieval |
| **Chains** | Sequences of operations |
| **Memory** | Conversation state management |
| **Agents** | LLM-driven decision-making with tools |
| **Callbacks** | Event hooks for monitoring and logging |

---

### Q3: What is the difference between an LLM and a Chat Model in LangChain?

**Answer:**

| Aspect | LLM | Chat Model |
|--------|-----|------------|
| Input | Plain text string | List of messages (System, Human, AI) |
| Output | Text string | ChatMessage object |
| Interface | `invoke("text")` | `invoke([messages])` |
| Use Case | Text completion | Conversational AI |

Example:
```python
# LLM (text completion)
from langchain_openai import OpenAI
llm = OpenAI(model="text-davinci-003")
response = llm.invoke("What is Python?")

# Chat Model
from langchain_openai import ChatOpenAI
chat_model = ChatOpenAI(model="gpt-4o-mini")
response = chat_model.invoke([HumanMessage(content="What is Python?")])
```

---

### Q4: What is a Prompt Template?

**Answer:** A Prompt Template is a parameterized way to construct prompts for LLMs. It allows you to define a prompt structure with placeholders that get filled with dynamic values at runtime.

```python
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate(
    template="Translate the following text to {language}: {text}",
    input_variables=["language", "text"],
)

formatted = prompt.format(language="French", text="Hello")
# Output: "Translate the following text to French: Hello"
```

---

### Q5: What is LCEL (LangChain Expression Language)?

**Answer:** LCEL is LangChain's declarative composition syntax using the pipe (`|`) operator. It enables chaining components together with built-in support for streaming, async execution, parallel execution, and fallbacks.

```python
chain = prompt | model | parser
result = chain.invoke({"topic": "AI"})
```

Key benefits:
- **Streaming**: Real-time token output
- **Async support**: `ainvoke()`, `astream()`
- **Parallel execution**: `RunnableParallel`
- **Fallbacks**: `.with_fallbacks()`
- **Retries**: `.with_retry()`

---

### Q6: What is a Chain in LangChain?

**Answer:** A Chain is a sequence of operations that process input and produce output. It combines components like prompts, models, and parsers into a reusable pipeline.

```python
# Using LCEL (modern approach)
chain = (
    ChatPromptTemplate.from_template("Explain {topic} simply.")
    | ChatOpenAI(model="gpt-4o-mini")
    | StrOutputParser()
)
result = chain.invoke({"topic": "machine learning"})
```

---

### Q7: What are Output Parsers and why are they needed?

**Answer:** Output Parsers transform raw LLM responses into structured formats. They are needed because LLMs return unstructured text, but applications often require structured data (JSON, lists, Pydantic objects).

Common parsers:
- `StrOutputParser`: Returns plain text
- `JsonOutputParser`: Returns parsed JSON
- `PydanticOutputParser`: Returns Pydantic model instances
- `ListOutputParser`: Returns comma-separated lists

---

### Q8: What is Memory in LangChain?

**Answer:** Memory enables LLM applications to retain context across multiple interactions. Without memory, each request is independent and the model has no awareness of previous conversations.

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(return_messages=True)
memory.save_context({"input": "Hi"}, {"output": "Hello!"})
history = memory.load_memory_variables({})
```

---

### Q9: What is the difference between `ConversationBufferMemory` and `ConversationBufferWindowMemory`?

**Answer:**

| Feature | ConversationBufferMemory | ConversationBufferWindowMemory |
|---------|-------------------------|-------------------------------|
| Storage | Stores entire conversation | Stores last N exchanges |
| Token Usage | Grows indefinitely | Bounded by window size |
| Use Case | Short conversations | Long-running conversations |
| Parameter | None | `k` (number of exchanges) |

---

### Q10: What is a Tool in LangChain?

**Answer:** A Tool is a function that an agent can invoke to perform actions beyond text generation. Tools enable agents to interact with external systems, APIs, databases, and perform computations.

```python
from langchain.tools import tool

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    return str(eval(expression))
```

---

## Intermediate Questions

### Q11: Explain the difference between `LLMChain`, `SimpleSequentialChain`, and `SequentialChain`.

**Answer:**

| Chain Type | Description | Input/Output |
|------------|-------------|--------------|
| **LLMChain** | Single prompt + model | One input, one output |
| **SimpleSequentialChain** | Multiple chains in sequence, single input/output | One input, one output |
| **SequentialChain** | Multiple chains with multiple inputs/outputs | Multiple inputs, multiple outputs |

Example of `SequentialChain`:
```python
from langchain.chains import SequentialChain

# Chain 1: Generate outline
outline_chain = LLMChain(llm=llm, prompt=outline_prompt, output_key="outline")

# Chain 2: Write essay from outline
essay_chain = LLMChain(llm=llm, prompt=essay_prompt, output_key="essay")

# Combine
seq_chain = SequentialChain(
    chains=[outline_chain, essay_chain],
    input_variables=["topic"],
    output_variables=["outline", "essay"],
)
result = seq_chain.invoke({"topic": "AI ethics"})
```

---

### Q12: How does `ConversationSummaryMemory` work?

**Answer:** `ConversationSummaryMemory` uses an LLM to generate a running summary of the conversation instead of storing raw messages. This reduces token consumption while preserving context.

```python
from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    return_messages=True,
)
```

How it works:
1. After each exchange, the memory calls the LLM to update the summary
2. The summary is passed to the model instead of raw conversation history
3. This keeps token usage bounded even for long conversations

---

### Q13: What is `ConversationSummaryBufferMemory` and when should you use it?

**Answer:** `ConversationSummaryBufferMemory` combines the benefits of buffer memory and summary memory. It keeps the most recent N tokens as raw messages and summarizes older messages.

```python
from langchain.memory import ConversationSummaryBufferMemory

memory = ConversationSummaryBufferMemory(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    max_token_limit=1000,  # Summarize when exceeding this limit
    return_messages=True,
)
```

Use when:
- You need recent context in full detail
- Older context can be summarized
- You want to balance token usage with context quality

---

### Q14: How do you create a custom tool in LangChain?

**Answer:** There are two ways to create custom tools:

**Method 1: Using the `@tool` decorator**
```python
from langchain.tools import tool

@tool
def search_database(query: str) -> str:
    """Search the internal database for information."""
    results = database.search(query)
    return format_results(results)
```

**Method 2: Inheriting from `BaseTool`**
```python
from langchain.tools import BaseTool

class CustomSearchTool(BaseTool):
    name: str = "database_search"
    description: str = "Search the internal database"

    def _run(self, query: str) -> str:
        results = database.search(query)
        return format_results(results)

    async def _arun(self, query: str) -> str:
        return await database.asearch(query)
```

---

### Q15: What is an Agent Executor and how does it work?

**Answer:** `AgentExecutor` is the runtime that runs an agent. It handles the loop of:
1. Passing input to the agent
2. Agent decides which tool to use
3. Executing the tool
4. Feeding the result back to the agent
5. Repeating until the agent produces a final answer

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,  # Prevent infinite loops
    handle_parsing_errors=True,
)
result = executor.invoke({"input": "What is 25 * 48?"})
```

---

### Q16: What is `VectorStoreRetrieverMemory`?

**Answer:** `VectorStoreRetrieverMemory` stores conversation history in a vector store and retrieves relevant past exchanges using semantic similarity. This enables long-term memory with context-aware retrieval.

```python
from langchain.memory import VectorStoreRetrieverMemory
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts([], embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

memory = VectorStoreRetrieverMemory(retriever=retriever)
memory.save_context(
    {"input": "What is the capital of France?"},
    {"output": "Paris"},
)
```

---

### Q17: How do you handle structured output with LangChain?

**Answer:** Use `with_structured_output()` or output parsers with Pydantic models:

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="Full name")
    age: int = Field(description="Age in years")

# Method 1: with_structured_output (simplest)
llm = ChatOpenAI(model="gpt-4o-mini")
structured_llm = llm.with_structured_output(Person)
result = structured_llm.invoke("John is 30 years old.")

# Method 2: JsonOutputParser with Pydantic
from langchain_core.output_parsers import JsonOutputParser
parser = JsonOutputParser(pydantic_object=Person)
chain = prompt | llm | parser
```

---

### Q18: What are Callbacks in LangChain and how do you use them?

**Answer:** Callbacks are hooks that fire during chain/agent execution for monitoring, logging, or custom behavior.

```python
from langchain_core.callbacks import BaseCallbackHandler

class MyCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"LLM starting with prompt: {prompts[0][:50]}...")

    def on_llm_end(self, response, **kwargs):
        print(f"LLM finished. Tokens: {response.llm_output.get('token_usage', {})}")

    def on_chain_start(self, serialized, inputs, **kwargs):
        print(f"Chain starting with inputs: {inputs}")

chain = prompt | model | parser
result = chain.invoke(
    {"topic": "AI"},
    config={"callbacks": [MyCallbackHandler()]}
)
```

---

### Q19: How do you implement caching in LangChain?

**Answer:** LangChain supports caching to avoid redundant API calls for identical prompts:

```python
from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache, SQLiteCache

# In-memory cache (fast, lost on restart)
set_llm_cache(InMemoryCache())

# SQLite cache (persistent across restarts)
set_llm_cache(SQLiteCache(database_path="langchain_cache.db"))

# GPTCache for semantic similarity caching
from langchain_community.cache import GPTCache
set_llm_cache(GPTCache("./gptcache_data"))
```

---

### Q20: What is `RunnableParallel` and when should you use it?

**Answer:** `RunnableParallel` executes multiple runnables concurrently and combines their results. Use it when you need to run independent operations in parallel.

```python
from langchain_core.runnables import RunnableParallel

parallel_chain = RunnableParallel({
    "summary": summary_chain,
    "keywords": keyword_chain,
    "sentiment": sentiment_chain,
    "entities": entity_chain,
})

result = parallel_chain.invoke({"text": "Your input text"})
# Returns: {"summary": "...", "keywords": [...], "sentiment": "...", "entities": [...]}
```

---

## Advanced Questions

### Q21: Explain the ReAct pattern and how LangChain implements it.

**Answer:** ReAct (Reasoning + Acting) is an agent pattern where the LLM alternates between reasoning about what to do and taking actions using tools.

The loop:
1. **Thought**: LLM reasons about the current state
2. **Action**: LLM selects a tool to invoke
3. **Observation**: Tool returns a result
4. Repeat until **Final Answer** is reached

```python
from langchain.agents import create_react_agent

prompt = ChatPromptTemplate.from_template("""Answer the following questions as best you can.

You have access to the following tools: {tools}

Use the following format:
Question: the input question
Thought: your reasoning
Action: tool name
Action Input: tool input
Observation: tool result
... (repeat Thought/Action/Observation)
Thought: I now know the final answer
Final Answer: the final answer

Question: {input}
Thought: {agent_scratchpad}
""")

agent = create_react_agent(llm, tools, prompt)
```

---

### Q22: How do you implement fallbacks and retries in LangChain chains?

**Answer:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

# Fallbacks: Try alternative chains if primary fails
primary_chain = prompt | ChatOpenAI(model="gpt-4o") | parser
fallback_chain = prompt | ChatOpenAI(model="gpt-4o-mini") | parser

robust_chain = primary_chain.with_fallbacks([fallback_chain])

# Retries: Retry the same chain on failure
retry_chain = primary_chain.with_retry(
    retry_if_exception_type=(RateLimitError, APIError),
    wait_exponential_jitter=True,
    stop_after_attempt=3,
)

# Combined
robust_retry_chain = primary_chain.with_fallbacks([fallback_chain]).with_retry(
    stop_after_attempt=3
)
```

---

### Q23: How do you handle streaming responses in LangChain?

**Answer:**

```python
# Synchronous streaming
chain = prompt | ChatOpenAI(model="gpt-4o-mini", streaming=True) | StrOutputParser()

for chunk in chain.stream({"topic": "AI"}):
    print(chunk, end="", flush=True)

# Async streaming
async for chunk in chain.astream({"topic": "AI"}):
    print(chunk, end="", flush=True)

# With callbacks for events
from langchain_core.callbacks import StreamingStdOutCallbackHandler

chain = prompt | model | parser
chain.invoke(
    {"topic": "AI"},
    config={"callbacks": [StreamingStdOutCallbackHandler()]}
)
```

---

### Q24: Explain how to build a multi-agent system with LangChain.

**Answer:** LangGraph (part of the LangChain ecosystem) enables multi-agent orchestration:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class AgentState(TypedDict):
    messages: list
    current_agent: str

# Define agent nodes
def researcher_node(state):
    # Research agent logic
    return {"messages": [...]}

def writer_node(state):
    # Writer agent logic
    return {"messages": [...]}

def reviewer_node(state):
    # Reviewer agent logic
    return {"messages": [...]}

# Build graph
graph = StateGraph(AgentState)
graph.add_node("researcher", researcher_node)
graph.add_node("writer", writer_node)
graph.add_node("reviewer", reviewer_node)

graph.add_edge("researcher", "writer")
graph.add_edge("writer", "reviewer")
graph.add_edge("reviewer", END)

graph.set_entry_point("researcher")
app = graph.compile()
```

---

### Q25: How do you optimize token usage in LangChain applications?

**Answer:**

1. **Use appropriate memory types:**
   - `ConversationSummaryMemory` for long conversations
   - `ConversationBufferWindowMemory` with limited `k`

2. **Efficient document chunking:**
   ```python
   splitter = RecursiveCharacterTextSplitter(
       chunk_size=500,
       chunk_overlap=50,
   )
   ```

3. **Prompt optimization:**
   - Remove redundant instructions
   - Use concise system prompts
   - Avoid unnecessary few-shot examples

4. **Model selection:**
   - Use smaller models for simpler tasks
   - Use `gpt-4o-mini` instead of `gpt-4o` when possible

5. **Caching:**
   ```python
   set_llm_cache(SQLiteCache(database_path="cache.db"))
   ```

6. **Response length control:**
   ```python
   llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=200)
   ```

---

### Q26: What is the difference between `create_tool_calling_agent` and `create_react_agent`?

**Answer:**

| Feature | `create_tool_calling_agent` | `create_react_agent` |
|---------|----------------------------|---------------------|
| Mechanism | Uses native function calling | Uses ReAct prompt pattern |
| LLM Support | Requires tool-calling capable LLMs | Works with any LLM |
| Reliability | More reliable, structured | More flexible, prompt-dependent |
| Performance | Faster (native support) | Slower (text parsing) |
| Best For | Modern LLMs (GPT-4, Claude 3) | Legacy or open-source LLMs |

---

### Q27: How do you implement error handling and graceful degradation in LangChain?

**Answer:**

```python
from langchain_core.runnables import RunnableLambda
from langchain_core.exceptions import OutputParserException

# Custom error handler
def safe_invoke(chain, inputs, fallback_value="I couldn't process that request."):
    try:
        return chain.invoke(inputs)
    except OutputParserException as e:
        print(f"Parse error: {e}")
        return fallback_value
    except Exception as e:
        print(f"Unexpected error: {e}")
        return fallback_value

# Using with_fallbacks for graceful degradation
primary = prompt | ChatOpenAI(model="gpt-4o") | parser
fallback = prompt | ChatOpenAI(model="gpt-3.5-turbo") | parser
final_fallback = RunnableLambda(lambda x: "Service temporarily unavailable.")

robust_chain = primary.with_fallbacks([fallback, final_fallback])
```

---

### Q28: How would you design a production-ready LangChain application?

**Answer:** A production-ready LangChain application should include:

1. **Environment management:**
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   ```

2. **Configuration management:**
   ```python
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       openai_api_key: str
       model_name: str = "gpt-4o-mini"
       max_tokens: int = 500
       temperature: float = 0.7
   ```

3. **Error handling and retries:**
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   def call_chain(inputs):
       return chain.invoke(inputs)
   ```

4. **Monitoring and logging:**
   ```python
   from langchain_core.callbacks import BaseCallbackHandler

   class MonitoringCallback(BaseCallbackHandler):
       def on_llm_end(self, response, **kwargs):
           log_token_usage(response.llm_output)
   ```

5. **Security:**
   - Input validation and sanitization
   - Rate limiting
   - API key management
   - Prompt injection protection

6. **Testing:**
   - Unit tests for individual components
   - Integration tests for chains
   - Mock LLM responses for deterministic testing

7. **Deployment:**
   - Containerization (Docker)
   - CI/CD pipelines
   - Health checks and monitoring
   - Scalable infrastructure

---

## Quick Reference Table

| Topic | Key Classes/Functions |
|-------|----------------------|
| Prompt Templates | `PromptTemplate`, `ChatPromptTemplate`, `FewShotPromptTemplate` |
| Output Parsers | `StrOutputParser`, `JsonOutputParser`, `PydanticOutputParser` |
| Memory | `ConversationBufferMemory`, `ConversationSummaryMemory`, `VectorStoreRetrieverMemory` |
| Chains | LCEL (`\|`), `RunnableParallel`, `RunnablePassthrough` |
| Tools | `@tool` decorator, `BaseTool` class |
| Agents | `create_tool_calling_agent`, `create_react_agent`, `AgentExecutor` |
| Caching | `InMemoryCache`, `SQLiteCache`, `set_llm_cache()` |
| Callbacks | `BaseCallbackHandler`, `StreamingStdOutCallbackHandler` |
| Error Handling | `.with_fallbacks()`, `.with_retry()` |

---

## Senior Deep Dive: LlamaIndex vs LangChain & When to Drop the Framework

> *The course teaches LangChain, but the JD also lists LlamaIndex. Interviewers want to hear that you choose a framework for the job — and can leave it when it stops paying for itself.*

### SQ1: When would you reach for LlamaIndex instead of LangChain — and when neither?

**Answer:** The choice turns on what sits at the centre of your problem. **LlamaIndex** is a data- and retrieval-first framework: its primary abstractions are **document loaders**, **node parsers** (chunking), **indices** (VectorStoreIndex, SummaryIndex, KnowledgeGraphIndex), **retrievers**, **node postprocessors**, **response synthesizers**, and **query engines**. Every abstraction in its stack exists to answer one question — *how do I get the right information out of private data?* — making it the natural fit when ingest → index → retrieve is the core problem, such as document Q&A, enterprise search, or a RAG pipeline over hundreds of thousands of policy documents. **LangChain**, by contrast, is a general **orchestration** framework: its strength is chains, agents, tool integrations, and the glue needed to wire LLM calls into broader workflows that go well beyond retrieval. A multi-step agent that queries APIs, runs calculations, writes reports, and caches results is squarely in LangChain territory. The two are not mutually exclusive — a common production pattern uses LlamaIndex for the retrieval layer inside a LangChain or LangGraph agent, giving you specialised retrieval quality plus general orchestration breadth. The answer is *neither* when the framework overhead stops paying for itself: a **latency-critical hot path** with a single LLM call, a regulated pipeline where you must audit every token sent and received, or a simple script that calls one model once. In those cases the raw **provider SDK** — `openai`, `anthropic`, `boto3` — is simpler, faster, and far easier to audit. The trade-off to name explicitly: a framework buys integrations and battle-tested patterns but costs a dependency, frequent version churn, and **leaky abstractions** that can obscure what is actually being sent to the model — a real risk in regulated environments where the prompt and token budget must be fully visible.

### SQ2: When do you drop the framework and call the model SDK directly?

**Answer:** The signal to reach for the raw SDK is when the framework is adding cost — in latency, opacity, or operational complexity — without adding enough value in return. The clearest cases are **latency-critical hot paths**: if you are targeting sub-200 ms response times on a synchronous API, every extra middleware layer matters, and a direct `client.chat.completions.create()` call with a hand-crafted prompt is simply faster than the same call routed through several layers of LCEL or LlamaIndex plumbing. The second signal is **audit and cost control**: in a regulated organisation, you must be able to prove *exactly* what prompt was sent, how many tokens were consumed, and what response was received. Frameworks that build and modify prompts internally — injecting context, system messages, or chain-of-thought scaffolding behind convenience methods — make that audit harder. The third signal is **debugging cost**: when a bug in your pipeline requires stepping through four layers of framework callback handlers and abstract base classes to find the actual prompt, the framework is now slowing down development rather than accelerating it. Keep frameworks for **prototyping**, **breadth of integrations** (you need to swap three different vector databases without rewriting retrieval logic), and **standard patterns** that would otherwise be boilerplate. The **senior framing** that interviewers are listening for: frameworks are accelerators, not architecture. A competent senior engineer should be able to re-implement any chain in roughly fifty lines of SDK calls from memory. The trade-off is **development speed vs control and transparency** — and in a production risk-management system, transparency often wins.

### SQ3: What does LangChain's LCEL give you, and what's the cost?

**Answer:** **LCEL** (LangChain Expression Language) is a declarative **pipe composition** system expressed with the `|` operator: `prompt | model | parser`. The moment you wire components this way, you gain several cross-cutting capabilities for free — true **streaming** (tokens flow through every stage as they arrive), **async execution** via `ainvoke` and `astream`, **batching** of multiple inputs, configurable **retries** via `.with_retry()`, **fallbacks** to alternative chains via `.with_fallbacks()`, and **parallelism** via `RunnableParallel`. These are not trivial to implement correctly from scratch, particularly async streaming through a multi-step pipeline, so LCEL's main return on investment is eliminating that boilerplate. The **cost** is two-fold. First, there is a genuine **learning curve**: understanding how `RunnablePassthrough`, `RunnableLambda`, and `RunnableParallel` compose, how context is threaded through, and how `config` propagates requires time. Second, and more important for production, **introspection degrades**: when something goes wrong, stack traces run through multiple framework layers and error messages can be cryptic. Debugging a mis-routed input or a parser mismatch often means adding `callbacks` and carefully reading intermediate state rather than simply reading your own code. The trade-off is explicit: LCEL buys **less boilerplate and a lot of free infrastructure**, and costs **harder introspection when things go wrong** — a cost that compounds if your team is not already fluent in the framework's internals.

### SQ4: Map LlamaIndex's core abstractions onto a RAG pipeline.

**Answer:** LlamaIndex names and wires the exact stages you would build by hand in a RAG pipeline, which is what makes it ergonomic for retrieval-heavy work. The flow runs as follows. Raw files and data sources are loaded as **Documents** — the framework's top-level unit of text. Documents are then parsed into **Nodes** (the equivalent of chunks), where the **node parser** controls chunking strategy, overlap, and metadata inheritance. Nodes are passed into an **Index** — most commonly `VectorStoreIndex`, which embeds each node and persists embeddings to a backing store, but SummaryIndex (for summarisation) or KnowledgeGraphIndex (for graph-structured retrieval) are swappable alternatives. From the index you derive a **Retriever**, which executes the similarity or keyword search against that index and returns the most relevant nodes. Those nodes then pass through **node postprocessors** — pluggable components for **re-ranking** (e.g., a cross-encoder), **similarity score cutoffs**, or **keyword filtering** — which prune and reorder the candidate set. The refined nodes reach the **response synthesizer**, which takes the query and the node list, constructs the final prompt, calls the LLM, and produces a structured response. All of this is exposed through a **query engine**, the single object your application calls at inference time. Each stage is independently swappable without touching the others, which is exactly the ports-and-adapters pattern you would implement by hand. The trade-off between convention and control applies here: you gain a named, tested pipeline in very few lines of code, but any customisation that falls outside the framework's expected shapes requires understanding and subclassing the right abstract base class, and the framework still decides the final prompt format unless you override the response synthesizer explicitly.

### SQ5: How do you manage framework version churn and lock-in in production?

**Answer:** Both LangChain and LlamaIndex have historically shipped breaking API changes at high frequency — a real operational hazard in a production risk-management system where upgrades must be tested, approved, and documented. The first line of defence is **pinning versions** explicitly in your dependency manifest (`langchain==0.2.x`, `llama-index-core==0.10.x`) and reviewing the full changelog before any upgrade. That alone is insufficient, however, because what you really need is the **option to swap or drop the framework without rewriting business logic**. The architectural answer is wrapping the framework behind **your own interface** — a retrieval abstraction, an LLM gateway class, a document-ingestion protocol — so that your domain code calls `retriever.search(query)` and does not know or care whether that is backed by LlamaIndex, LangChain, a raw SDK call, or a future framework you have not chosen yet. This is the **ports-and-adapters** (hexagonal architecture) pattern applied to AI tooling. When LangChain ships a breaking change, you update one adapter class rather than touching every file that builds a chain. The third practice is **maintaining your own benchmark suite** — a small set of representative queries with known expected outputs — and running it against every candidate upgrade before promoting it to production. This catches regressions that the framework's own test suite never sees because it does not know your documents or your query distribution. The trade-off to name clearly: building and maintaining the adapter layer is **upfront cost** — perhaps a day or two of engineering — but it buys you **the option to migrate, swap, or drop the framework on your own schedule**, rather than being forced into emergency upgrades when a dependency breaks. In a regulated context where every change to a production system requires a change-management ticket, that optionality is not a nicety; it is cheap insurance against a dependency that ships breaking changes monthly.
