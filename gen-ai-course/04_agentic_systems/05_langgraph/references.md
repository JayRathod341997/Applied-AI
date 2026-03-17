# References: LangGraph Framework

## Official Documentation

### LangGraph
- **Official Documentation**: https://langchain-ai.github.io/langgraph/
- **GitHub Repository**: https://github.com/langchain-ai/langgraph
- **API Reference**: https://langchain-ai.github.io/langgraph/reference/
- **Examples**: https://github.com/langchain-ai/langgraph/tree/main/examples

### LangChain
- **Official Documentation**: https://python.langchain.com/docs
- **GitHub**: https://github.com/langchain-ai/langchain

---

## Tutorials and Guides

### Getting Started
1. **LangGraph Quick Start**: https://langchain-ai.github.io/langgraph/tutorials/
2. **Introduction to LangGraph**: https://blog.langchain.dev/introducing-langgraph/
3. **Building Agents with LangGraph**: https://python.langchain.com/docs/langgraph

### Video Tutorials
1. **LangGraph Course**: https://www.youtube.com/watch?v=ivLh7W7xTzk
2. **Building AI Agents**: https://www.youtube.com/watch?v=dQw4w9WgXcQ

### Blog Posts
1. **LangGraph vs LangChain Chains**: https://blog.langchain.dev/langgraph-vs-chains/
2. **Human-in-the-Loop with LangGraph**: https://blog.langchain.dev/human-in-the-loop/

---

## Key Concepts

### Nodes and Edges
- **Documentation**: https://langchain-ai.github.io/langgraph/concepts/
- **Examples**: https://github.com/langchain-ai/langgraph/tree/main/examples/node-edge

### State Management
- **TypedDict State**: https://langchain-ai.github.io/langgraph/concepts/state/
- **Persistence**: https://langchain-ai.github.io/langgraph/concepts/persistence/

### Human-in-the-Loop
- **Interrupt Pattern**: https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/
- **Force Calling Tool**: https://langchain-ai.github.io/langgraph/how-tos/

---

## Agent Patterns

### ReAct Pattern
- **Paper**: https://arxiv.org/abs/2210.03629
- **Implementation**: https://github.com/langchain-ai/langgraph/tree/main/examples/react

### Reflection Pattern
- **Self-Reflection**: https://arxiv.org/abs/2303.11366
- **Implementation**: https://github.com/langchain-ai/langgraph/tree/main/examples/reflection

### Tool Use
- **Tool Calling**: https://python.langchain.com/docs/modules/model_io/chat/
- **Custom Tools**: https://python.langchain.com/docs/modules/agents/tools/

---

## Memory Management

### Short-term Memory
- **Message History**: https://python.langchain.com/docs/modules/memory/
- **ConversationBufferMemory**: https://python.langchain.com/api_reference/langchain/memory/langchain.memory.buffer.ChatMessageHistory.html

### Long-term Memory
- **Vector Store Retriever**: https://python.langchain.com/docs/modules/data_connection/retrievers/
- **FAISS**: https://python.langchain.com/docs/integrations/vectorstores/faiss/
- **Pinecone**: https://python.langchain.com/docs/integrations/vectorstores/pinecone/

---

## Cloud Integrations

### AWS
- **Bedrock Agent**: https://aws.amazon.com/bedrock/
- **SageMaker**: https://aws.amazon.com/sagemaker/

### Azure
- **Azure OpenAI**: https://azure.microsoft.com/services/cognitive-services/openai/
- **Azure AI Agent Service**: https://learn.microsoft.com/azure/ai-services/

### GCP
- **Vertex AI**: https://cloud.google.com/vertex-ai
- **Gemini API**: https://ai.google.dev/

---

## Community Resources

### Forums
- **LangChain Discord**: https://discord.gg/langchain
- **Reddit r/LangChain**: https://reddit.com/r/LangChain
- **Stack Overflow**: https://stackoverflow.com/questions/tagged/langchain

### GitHub
- **Awesome LangGraph**: https://github.com/ langchain-ai/awesome-langgraph
- **Example Collections**: https://github.com/langchain-ai/langgraph/tree/main/examples

---

## Research Papers

1. **ReAct: Synergizing Reasoning and Acting in Language Models**
   - https://arxiv.org/abs/2210.03629

2. **Reflexion: Language Agents with Verbal Reinforcement Learning**
   - https://arxiv.org/abs/2303.11366

3. **Toolformer: Language Models Can Teach Themselves to Use Tools**
   - https://arxiv.org/abs/2302.04761

---

## Books

1. "Building AI Agents" - Upcoming from O'Reilly
2. "Practical LangChain" - Available on Leanpub
3. "Modern AI Development" - Chapter on Agents

---

## Cheat Sheet

### Quick Commands

```bash
# Install
pip install langgraph langchain langchain-openai

# Create basic graph
from langgraph.graph import StateGraph, END

# Define state
class State(TypedDict):
    messages: list

# Create graph
graph = StateGraph(State)
graph.add_node("process", my_function)
graph.set_entry_point("process")
graph.add_edge("process", END)
app = graph.compile()
```

### Common Patterns

```python
# Conditional edge
graph.add_conditional_edges(
    "node_a",
    routing_function,
    {"path_b": "node_b", "path_c": "node_c"}
)

# With state
def should_continue(state):
    if state.get("done"):
        return END
    return "next"

# Checkpointing
app = graph.compile(checkpointer=MemorySaver())
app.invoke(state, config={"configurable": {"thread_id": "1"}})
```

---

## Additional Tools

### Visualization
- **Mermaid.js**: https://mermaid.js.org/
- **Graphviz**: https://graphviz.org/

### Testing
- **Pytest**: https://docs.pytest.org/
- **LangChain Test Utils**: https://python.langchain.com/docs/additional_modules/

### Deployment
- **FastAPI**: https://fastapi.tiangolo.com/
- **Streamlit**: https://streamlit.io/
- **Docker**: https://www.docker.com/