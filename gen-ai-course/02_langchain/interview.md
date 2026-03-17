# LangChain - Interview Questions

This document contains interview questions and answers covering Module 2: LangChain Framework and Tooling.

---

## 1. LangChain Overview

### Q1: What is LangChain and why would you use it?

**Answer:** LangChain is an open-source framework for building applications with large language models. It provides:

- **Abstraction:** Simplified interfaces for LLM interactions
- **Composability:** Chain components together
- **Tool Ecosystem:** Built-in integrations for tools, vector databases
- **Memory:** Built-in conversation memory
- **Agents:** Autonomous agents with tool usage
- **Production Features:** Debugging, monitoring, evaluation

---

### Q2: What is the difference between LangChain and LangGraph?

**Answer:**

| Aspect | LangChain | LangGraph |
|--------|-----------|-----------|
| Structure | Linear chains | Cyclic graphs |
| Use Case | Simple workflows | Complex, stateful agents |
| Control Flow | Sequential | Conditional, branching |
| State Management | Basic | Sophisticated |
| Production | Good for prototypes | Better for agents |

LangGraph is built on LangChain for building agentic workflows.

---

### Q3: What are the core components of LangChain?

**Answer:** Core components:

- **LLMs/Chat Models:** Interface to language models
- **Prompts:** Prompt templates and management
- **Chains:** Sequential LLM operations
- **Memory:** Conversation history storage
- **Tools:** External capabilities (search, APIs)
- **Agents:** Autonomous decision makers
- **Indexes:** Document loaders and retrievers

---

## 2. Building Blocks

### Q4: How do Chat Models work in LangChain?

**Answer:** Chat models:

- **Message Types:** System, Human, AI messages
- **Providers:** OpenAI, Anthropic, Azure OpenAI, etc.
- **Parameters:** temperature, max_tokens, streaming
- **Usage Tracking:** Token counting, costs
- **Function Calling:** Structured output support

Example:
```python
from langchain_openai import ChatOpenAI
chat = ChatOpenAI(model="gpt-4")
response = chat.invoke([{"role": "user", "content": "Hello"}])
```

---

### Q5: What are Prompt Templates in LangChain?

**Answer:** Prompt templates:

- **String PromptTemplate:** Simple string substitution
- **ChatPromptTemplate:** Structured chat messages
- **PipelinePrompt:** Chain multiple prompts
- **FewShotPromptTemplate:** With examples

Benefits: Reusability, parameterized prompts, cleaner code

---

### Q6: How do Output Parsers work?

**Answer:** Output parsers:

- **PydanticOutputParser:** Parse into Pydantic models
- **JSON Parser:** Extract JSON from responses
- **CSV Parser:** Extract CSV data
- **Structured Output:** Function calling support

```python
from langchain.output_parsers import PydanticOutputParser
parser = PydanticOutputParser(pydantic_object=MyModel)
```

---

### Q7: What is caching in LangChain and why use it?

**Answer:** Caching types:

- **In-Memory Cache:** Simple, same process
- **SQLite Cache:** Persistent, file-based
- **Redis Cache:** Distributed, high performance
- **LLM Cache:** Cache full LLM responses

Benefits: Cost reduction, latency improvement, consistency

---

### Q8: What is response streaming in LangChain?

**Answer:** Streaming:

- **Use Case:** Real-time response display
- **Implementation:** Use `.stream()` method
- **Token-by-Token:** Faster perceived latency
- **Compatible with Chains:** Works in most components

```python
for chunk in chat.stream("Tell me a story"):
    print(chunk.content, end="")
```

---

## 3. Chains

### Q9: What are the different types of chains in LangChain?

**Answer:** Chain types:

- **LLMChain:** Basic prompt → LLM → output
- **SequentialChain:** Multiple chains in sequence
- **RouterChain:** Route to different chains
- **TransformationChain:** Transform inputs/outputs
- **ConversationChain:** With memory
- **RetrievalQA:** RAG chain

---

### Q10: How do you compose prompts in LangChain?

**Answer:** Composition methods:

- **PipelinePrompt:** Chain prompts together
- **String Concatenation:** Simple joining
- **ChatPrompt Compositions:** Multiple message types

```python
from langchain.prompts.pipeline import PipelinePrompt
```

---

### Q11: What is FewShotPromptTemplate and Example Selectors?

**Answer:** Few-shot learning:

- **FewShotPromptTemplate:** Include examples in prompt
- **Example Selector:** Choose which examples to include
  - Length-based: Fit within token limit
  - Similarity-based: Select relevant examples
  - Semantic kernel: ML-based selection

---

### Q12: How do you use ConversationChain?

**Answer:** ConversationChain:

```python
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

conversation = ConversationChain(
    llm=chat,
    memory=ConversationBufferMemory()
)
response = conversation.predict(input="Hi!")
```

---

### Q13: How do you implement tool calling in LangChain?

**Answer:** Tool calling:

```python
from langchain.tools import tool
from langchain.agents import AgentType

@tool
def calculate(expression: str) -> str:
    """Evaluate math expression."""
    return str(eval(expression))

tools = [calculate]
agent = initialize_agent(tools, llm, AgentType.ZERO_SHOT_REACT_DESCRIPTION)
```

---

## 4. Memory, Tools, and Agents

### Q14: What are the different memory types in LangChain?

**Answer:** Memory types:

- **BufferMemory:** Raw message history
- **BufferWindowMemory:** Last K messages
- **ConversationTokenBufferMemory:** By token limit
- **ConversationSummaryMemory:** Summarized history
- **VectorStore Memory:** Semantic retrieval from history
- **Entity Memory:** Track entities and facts

---

### Q15: How do you manage memory in a conversation?

**Answer:** Memory management:

```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(
    k=5,  # Last 5 messages
    return_messages=True
)

# Add to chain
chain = LLMChain(llm=chat, memory=memory)
```

---

### Q16: What are Tools in LangChain and how do you create them?

**Answer:** Tools:

- **Pre-built:** Search, calculator, APIs
- **Custom:** Your own functions decorated with @tool
- **Tool Schema:** Name, description, args schema

```python
from langchain.tools import tool

@tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    # Implementation
    return weather_data
```

---

### Q17: What are Agents and how do they work?

**Answer:** Agent types:

- **Zero-shot ReACT:** Use reasoning + tools
- **Conversational:** With memory
- **Structured Tool Chat:** Complex inputs
- **Self-Ask with Search:** Use search tool
- **OpenAI Functions:** Function calling

Agent Loop:
1. Receive input
2. Decide action
3. Execute tool
4. Observe result
5. Repeat until done

---

### Q18: How do you build an intelligent agent with tool calling?

**Answer:** Building agents:

1. **Define Tools:** Create or import tools
2. **Initialize Agent:** Choose agent type
3. **Add Memory:** Optional conversation memory
4. **Execute:** Run with user input

```python
from langchain.agents import AgentExecutor

agent = create_openai_functions_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
result = executor.invoke({"input": "What's the weather?"})
```

---

## 5. Patterns and Best Practices

### Q19: How do you test and debug LangChain workflows?

**Answer:** Debugging:

- **LangSmith:** LangChain's debugging service
- **Verbose Mode:** Print all steps
- **Callbacks:** Custom logging
- **Tracing:** See prompt → LLM → output

```python
from langchain.callbacks import LangChainTracer
chain.invoke(inputs, config={"callbacks": [LangChainTracer()]})
```

---

### Q20: What are best practices for LangChain production deployment?

**Answer:** Best practices:

- **Error Handling:** Handle API failures gracefully
- **Rate Limiting:** Respect provider limits
- **Caching:** Reduce costs and latency
- **Monitoring:** Track usage and errors
- **Streaming:** For better UX
- **Token Tracking:** Monitor costs

---

### Q21: How do you optimize LangChain for cost?

**Answer:** Optimization:

- **Caching:** Cache LLM responses
- **Prompt Optimization:** Reduce tokens
- **Smaller Models:** Use cheaper models when possible
- **Batch Processing:** Group requests
- **Memory Selection:** Choose appropriate memory type

---

### Q22: What is the Runnable interface in LangChain?

**Answer:** Runnable:

- **Standard Interface:** `.invoke()`, `.batch()`, `.stream()`
- **Composability:** Chain with `|`
- **Async Support:** `.ainvoke()`, `.abatch()`
- **Parallel:** `.parallel()` for concurrent execution

```python
chain = prompt | llm | output_parser
result = chain.invoke({"topic": "AI"})
```

---

### Q23: How do you handle errors in LangChain?

**Answer:** Error handling:

- **Try/Except:** Wrap LLM calls
- **Retry Logic:** Use retry callbacks
- **Fallback Chains:** Alternate on failure
- **Timeout:** Set max execution time
- **Circuit Breaker:** Prevent cascade failures

---

## Technical Questions

### Q24: How does LangChain integrate with vector databases?

**Answer:** Integration:

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

vectorstore = Chroma.from_documents(
    documents, 
    embedding=OpenAIEmbeddings()
)

retriever = vectorstore.as_retriever()
```

---

### Q25: What is the difference between LCEL and legacy chains?

**Answer:**

| Aspect | LCEL | Legacy |
|--------|------|--------|
| Interface | Runnable | Chain class |
| Composition | `|` operator | .chain() methods |
| Async | Native | Add async methods |
| Streaming | Built-in | Limited |

LCEL (LangChain Expression Language) is the modern way.

---

## Production Questions

### Q26: How do you implement RAG with LangChain?

**Answer:** RAG Implementation:

```python
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm=chat,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)
```

---

### Q27: How would you build a multi-step agent workflow?

**Answer:** Multi-step workflow:

1. **Define State:** What data to pass between steps
2. **Define Nodes:** Each step as a function
3. **Define Edges:** Control flow between nodes
4. **Execute:** Run with initial state

---

### Q28: What are common LangChain anti-patterns?

**Answer:** Anti-patterns:

- **No Error Handling:** API failures crash app
- **Excessive Memory:** Too much history retained
- **No Caching:** Repeated expensive calls
- **Large Prompts:** Exceeding context limits
- **Synchronous Only:** Not using async when beneficial

---

## Scenario-Based Questions

### Q29: How would you build a customer service bot with LangChain?

**Answer:** Design:

1. **Intent Detection:** Classify user query
2. **RAG:** Retrieve relevant docs
3. **Generation:** Create response
4. **Memory:** Track conversation
5. **Escalation:** Human handoff when needed

---

### Q30: How do you handle sensitive data in LangChain applications?

**Answer:** Handling:

- **Input Sanitization:** Remove PII from prompts
- **Output Filtering:** Check responses
- **Memory Security:** Encrypt conversation history
- **Logging:** Don't log sensitive data
- **Access Control:** Limit data exposure

---

## Summary

Key LangChain topics:

1. **Overview:** Framework, components, ecosystem
2. **Building Blocks:** Models, prompts, parsers
3. **Chains:** Composition, sequential, router
4. **Memory:** Types, management, persistence
5. **Tools & Agents:** Tool calling, agent types
6. **Production:** Debugging, optimization, LCEL

---

## References

- [LangChain Documentation](references.md)
- [LangChain Expression Language](references.md)
- [LangSmith Debugging](references.md)
