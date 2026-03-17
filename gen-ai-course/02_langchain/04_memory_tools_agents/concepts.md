# Memory, Tools, and Agents Concepts

## Memory Types

### 1. ConversationBufferMemory
```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    return_messages=True,
    output_key="text",
    input_key="input"
)
```

### 2. ConversationSummaryMemory
```python
from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(llm=llm)
```

### 3. BufferWindowMemory
```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(k=5)
```

## Tools

### Creating Tools
```python
from langchain.tools import tool

@tool
def search(query: str) -> str:
    """Search for information."""
    return search_results
```

### Using Tools with Agents
```python
from langchain.agents import AgentType, initialize_agent

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)
```

## Agent Types

1. **ZERO_SHOT_REACT_DESCRIPTION**: Use reasoning + tools
2. **CONVERSATIONAL**: With memory
3. **STRUCTURED_CHAT**: Complex inputs
4. **SELF_ASK_WITH_SEARCH**: Use search tool
